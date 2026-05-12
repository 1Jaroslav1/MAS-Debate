from typing import List, Optional
from langgraph.graph import StateGraph, START, END
from langgraph.store.memory import InMemoryStore
from langchain_core.runnables import RunnableConfig
from langchain_openai import OpenAIEmbeddings

from src.team_extended.common.metrics.token_tracking import NodeTokenTracker

from .vector_db_manager import VectorDBManager
from .knowledge_retrieval_manager import KnowledgeRetrievalManager
from .model import KnowledgeRetrievalState
from .search_tools import retrieve_from_memory, save_to_memory, rag_search, web_search


class KnowledgeRetrievalWorkflowBuilder:
    """Builder class for creating knowledge retrieval workflows with clean separation of concerns"""

    def __init__(
        self,
        llm,
        vector_db: VectorDBManager,
        tavily_tool,
        retrieval_manager: KnowledgeRetrievalManager,
        use_rag: bool = True,
        use_web_search: bool = True,
    ):
        self.llm = llm
        self.vector_db = vector_db
        self.tavily_tool = tavily_tool
        self.retrieval_manager = retrieval_manager
        self.use_rag = use_rag
        self.use_web_search = use_web_search

    def retrieve_memories_node(
        self, state: KnowledgeRetrievalState, config: RunnableConfig
    ) -> KnowledgeRetrievalState:
        """Retrieve relevant memories from store with team context"""
        memories = retrieve_from_memory(state, config)
        state.memory_items = memories

        # Log team context for debugging
        if state.context.member_profile:
            print(
                f"Retrieving memories for member: {state.context.member_profile.name}"
            )
        if state.context.team_focus:
            print(f"Retrieving memories for team: {state.context.team_focus.team_type}")

        return state

    def generate_queries_node(
        self, state: KnowledgeRetrievalState
    ) -> KnowledgeRetrievalState:
        """Generate search queries based on context, memories, and team integration"""
        queries = self.retrieval_manager.generate_search_queries(
            state.context, state.memory_items
        )
        state.search_queries = queries

        # Store member-adapted queries separately for tracking
        member_adapted = [q for q in queries if q.member_expertise_focus]
        state.member_adapted_queries = member_adapted

        # Initialize expertise coverage tracking
        if state.context.member_profile:
            state.expertise_coverage = {
                expertise: 0
                for expertise in state.context.member_profile.expertise_domains
            }

        print(
            f"Generated {len(queries)} queries ({len(member_adapted)} member-adapted)"
        )
        return state

    def search_node(self, state: KnowledgeRetrievalState) -> KnowledgeRetrievalState:
        """Execute searches iteratively with team context"""
        if state.current_query_index < len(state.search_queries):
            query = state.search_queries[state.current_query_index]

            print(
                f"Executing query {state.current_query_index + 1}/{len(state.search_queries)}: {query.query}"
            )

            documents = []

            # Execute RAG search with team context (CONDITIONAL)
            if self.use_rag:
                documents = rag_search(query, self.vector_db, state, limit=5)
                print(f"RAG search returned {len(documents)} documents")
            else:
                print("RAG search disabled, skipping")

            # Track expertise coverage
            if query.member_expertise_focus and state.context.member_profile:
                if query.member_expertise_focus in state.expertise_coverage:
                    state.expertise_coverage[query.member_expertise_focus] += len(
                        documents
                    )

            if self.use_web_search and len(documents) < 3:
                web_docs = web_search(
                    query, self.vector_db, self.tavily_tool, state, limit=5
                )
                print(f"Web search returned {len(web_docs)} additional documents")
                documents.extend(web_docs)
            elif self.use_web_search:
                print("Web search skipped (sufficient RAG results)")
            else:
                print("Web search disabled, skipping")

            state.retrieved_documents.extend(documents)
            state.current_query_index += 1

        return state

    def team_filtering_node(
        self, state: KnowledgeRetrievalState
    ) -> KnowledgeRetrievalState:
        """Apply team-specific filtering and ranking to retrieved documents"""
        if not state.retrieved_documents:
            return state

        print(f"Applying team filtering to {len(state.retrieved_documents)} documents")

        # Apply team-specific filtering and ranking
        filtered_docs = []

        for doc in state.retrieved_documents:
            # Calculate combined relevance score
            combined_score = (
                doc.relevance_score
                + doc.member_expertise_score
                + doc.team_perspective_score
            )

            # Apply team perspective thresholds
            keep_document = True

            if state.context.team_focus:
                # Minimum team perspective score requirement
                if (
                    doc.team_perspective_score < 0.1
                    and state.context.team_focus.avoid_keywords
                ):
                    # Check if document contains avoid keywords
                    doc_text = f"{doc.title} {doc.content}".lower()
                    if any(
                        keyword.lower() in doc_text
                        for keyword in state.context.team_focus.avoid_keywords
                    ):
                        keep_document = False

            # Prefer documents that match member's evidence preferences
            if state.context.member_profile and doc.evidence_type_match:
                combined_score += 0.5

            if keep_document:
                doc.relevance_score = combined_score  # Update with combined score
                filtered_docs.append(doc)

        state.team_filtered_documents = filtered_docs

        # Sort by combined relevance score
        state.team_filtered_documents.sort(
            key=lambda x: x.relevance_score, reverse=True
        )

        print(
            f"Team filtering resulted in {len(state.team_filtered_documents)} documents"
        )

        return state

    def consolidate_node(
        self, state: KnowledgeRetrievalState, config: RunnableConfig
    ) -> KnowledgeRetrievalState:
        """Consolidate results with team context and save to memory"""
        # Use team-filtered documents if available, otherwise use all retrieved documents
        documents = (
            state.team_filtered_documents
            if state.team_filtered_documents
            else state.retrieved_documents
        )

        # Remove duplicates
        seen_sources = set()
        unique_documents = []
        for doc in documents:
            if doc.source not in seen_sources:
                seen_sources.add(doc.source)
                unique_documents.append(doc)

        final_documents = _ensure_team_diversity(unique_documents, state)

        state.retrieved_documents = final_documents[:20]

        if state.context.member_profile:
            expertise_summary = {
                k: v for k, v in state.expertise_coverage.items() if v > 0
            }
            print(
                f"Expertise coverage for {state.context.member_profile.name}: {expertise_summary}"
            )

        if state.context.team_focus:
            team_relevant = sum(
                1
                for doc in state.retrieved_documents
                if doc.team_perspective_score > 0.3
            )
            print(
                f"Team-relevant documents for {state.context.team_focus.team_type}: {team_relevant}/{len(state.retrieved_documents)}"
            )

        if state.retrieved_documents:
            save_to_memory(state, config)

        return state

    @staticmethod
    def should_continue_search(state: KnowledgeRetrievalState) -> str:
        """Determine if more searches are needed"""
        if state.current_query_index < len(state.search_queries):
            return "search"
        else:
            return "team_filtering"

    def build(self) -> StateGraph:
        """Build and return the compiled workflow"""
        workflow = StateGraph(KnowledgeRetrievalState)

        # Add all nodes
        workflow.add_node("retrieve_memories", self.retrieve_memories_node)
        workflow.add_node("generate_queries", self.generate_queries_node)
        workflow.add_node("search", self.search_node)
        workflow.add_node("team_filtering", self.team_filtering_node)
        workflow.add_node("consolidate", self.consolidate_node)

        # Add edges
        workflow.add_edge(START, "retrieve_memories")
        workflow.add_edge("retrieve_memories", "generate_queries")
        workflow.add_edge("generate_queries", "search")

        # Add conditional edges
        workflow.add_conditional_edges(
            "search", self.should_continue_search, ["search", "team_filtering"]
        )
        workflow.add_edge("team_filtering", "consolidate")
        workflow.add_edge("consolidate", END)

        return workflow


def create_knowledge_retrieval_workflow(
    llm,
    vector_db: VectorDBManager,
    tavily_tool,
    store=None,
    use_rag: bool = True,
    use_web_search: bool = True,
    token_tracker: Optional[NodeTokenTracker] = None
) -> StateGraph:
    """Create the knowledge retrieval workflow with team integration and memory management"""

    if store is None:
        embeddings = OpenAIEmbeddings(model="text-embedding-3-small")
        store = InMemoryStore(
            index={
                "embed": embeddings,
                "dims": 1536,
            }
        )

    retrieval_manager = KnowledgeRetrievalManager(llm, token_tracker=token_tracker)

    builder = KnowledgeRetrievalWorkflowBuilder(
        llm=llm,
        vector_db=vector_db,
        tavily_tool=tavily_tool,
        retrieval_manager=retrieval_manager,
        use_rag=use_rag,
        use_web_search=use_web_search,
    )

    workflow = builder.build()
    return workflow.compile(store=store)


def _ensure_team_diversity(documents: List, state: KnowledgeRetrievalState) -> List:
    """Ensure diversity across team interests and member expertise"""
    if not documents:
        return documents

    diverse_docs = []
    covered_aspects = set()
    covered_expertise = set()

    sorted_docs = sorted(documents, key=lambda x: x.relevance_score, reverse=True)

    if state.context.team_focus and state.context.team_focus.priority_aspects:
        for doc in sorted_docs:
            doc_text = f"{doc.title} {doc.content}".lower()

            doc_aspects = []
            for aspect in state.context.team_focus.priority_aspects:
                if aspect.lower() in doc_text:
                    doc_aspects.append(aspect)

            if doc_aspects or doc.relevance_score > 0.8:
                diverse_docs.append(doc)
                covered_aspects.update(doc_aspects)

                if len(diverse_docs) >= 15:
                    break

    if state.context.member_profile and state.context.member_profile.expertise_domains:
        remaining_docs = [doc for doc in sorted_docs if doc not in diverse_docs]

        for doc in remaining_docs:
            doc_text = f"{doc.title} {doc.content}".lower()

            doc_expertise = []
            for expertise in state.context.member_profile.expertise_domains:
                if expertise.lower() in doc_text:
                    doc_expertise.append(expertise)

            if doc_expertise or doc.member_expertise_score > 0.5:
                diverse_docs.append(doc)
                covered_expertise.update(doc_expertise)

                if len(diverse_docs) >= 20:
                    break

    if len(diverse_docs) < 20:
        remaining_docs = [doc for doc in sorted_docs if doc not in diverse_docs]
        diverse_docs.extend(remaining_docs[: 20 - len(diverse_docs)])

    return diverse_docs
