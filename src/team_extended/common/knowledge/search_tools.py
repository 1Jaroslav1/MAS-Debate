from typing import List, Dict, Any
from datetime import datetime

from langgraph.config import get_store
from langchain_core.runnables import RunnableConfig

from .model import (
    SearchQuery,
    KnowledgeRetrievalState,
    KnowledgeMemory,
    RetrievedDocument,
)
from .vector_db_manager import VectorDBManager


def retrieve_from_memory(
    state: KnowledgeRetrievalState, config: RunnableConfig
) -> List[Dict[str, Any]]:
    """Retrieve relevant memories from the store with team context consideration"""
    store = get_store()
    session_id = state.context.session_id

    namespace = (session_id, "knowledge_memories")

    try:
        search_parts = [state.context.topic]

        if state.context.domains:
            search_parts.append(f"domains: {', '.join(state.context.domains)}")

        if state.context.goals:
            search_parts.append(f"goals: {', '.join(state.context.goals)}")

        if state.context.perspective:
            search_parts.append(f"perspective: {state.context.perspective}")

        if state.context.member_profile:
            search_parts.append(f"member: {state.context.member_profile.name}")
            search_parts.append(
                f"expertise: {', '.join(state.context.member_profile.expertise_domains)}"
            )

        if state.context.team_focus:
            search_parts.append(f"team: {state.context.team_focus.team_type}")
            search_parts.append(
                f"team_perspective: {state.context.team_focus.perspective_description}"
            )

        search_query = " ".join(search_parts)

        items = store.search(namespace, query=search_query, limit=5)

        memories = []
        for item in items:
            if item.value:
                memories.append(item.value)

        return memories
    except Exception as e:
        print(f"Semantic search failed: {e}, using fallback")
        memories = []

        for i in range(20):
            try:
                item = store.get(namespace, str(i))
                if item and item.value:
                    memory = item.value
                    # Check if goals overlap
                    if any(
                        goal in memory.get("goals", []) for goal in state.context.goals
                    ):
                        # NEW: Also check team context if available
                        if state.context.team_focus:
                            if (
                                memory.get("team_type")
                                == state.context.team_focus.team_type
                            ):
                                memories.append(memory)
                        else:
                            memories.append(memory)
            except:
                continue

        return memories[-5:]


def save_to_memory(state: KnowledgeRetrievalState, config: RunnableConfig) -> None:
    """Save retrieved knowledge to memory with team context"""
    store = get_store()
    session_id = state.context.session_id

    retrieved_sources = [doc.source for doc in state.retrieved_documents]

    member_name = (
        state.context.member_profile.name if state.context.member_profile else None
    )
    team_type = state.context.team_focus.team_type if state.context.team_focus else None

    # Track search adaptations made for team/member
    search_adaptations = []
    for query in state.search_queries:
        if query.member_expertise_focus:
            search_adaptations.append(
                f"member_expertise: {query.member_expertise_focus}"
            )
        if query.team_perspective_alignment:
            search_adaptations.append(
                f"team_alignment: {query.team_perspective_alignment}"
            )

    # Create memory item with team context
    memory_item: KnowledgeMemory = {
        "query": state.context.topic,
        "documents": [
            {
                "title": doc.title,
                "source": doc.source,
                "content": doc.content[:500],
                "relevance_score": doc.relevance_score,
                "goal": doc.goal,
                # NEW: Include team-specific scores
                "member_expertise_score": doc.member_expertise_score,
                "team_perspective_score": doc.team_perspective_score,
                "evidence_type_match": doc.evidence_type_match,
            }
            for doc in state.retrieved_documents[:5]
        ],
        "timestamp": datetime.now().isoformat(),
        "domains": state.context.domains,
        "goals": state.context.goals,
        "perspective": state.context.perspective,
        "session_id": session_id,
        "retrieved_sources": retrieved_sources,
        # NEW: Team context in memory
        "member_name": member_name,
        "team_type": team_type,
        "search_adaptations": search_adaptations,
    }

    # Save to store
    namespace = (session_id, "knowledge_memories")
    memory_id = str(int(datetime.now().timestamp()))
    store.put(namespace, memory_id, memory_item)

    # Update state directly
    state.memory_items.append(memory_item)
    state.context.excluded_sources.extend(retrieved_sources)


def rag_search(
    query: SearchQuery,
    vector_db: VectorDBManager,
    state: KnowledgeRetrievalState,
    limit: int = 10,
) -> List[RetrievedDocument]:
    """Execute RAG search with team context consideration"""
    # Build query without goal IDs
    base_query = query.query
    for goal in state.context.goals:
        base_query = base_query.replace(goal, "").strip()

    # Enhance query with domain, perspective, and team context
    enhanced_query = f"{query.domain}: {base_query}"
    if query.perspective_modifier:
        enhanced_query += f" {query.perspective_modifier}"

    # NEW: Add member expertise context
    if query.member_expertise_focus:
        enhanced_query += f" {query.member_expertise_focus}"

    # Get excluded sources from state
    excluded_sources = state.context.excluded_sources

    # NEW: Consider team focus for filtering
    filter_preferences = []
    if state.context.team_focus and state.context.team_focus.evidence_preferences:
        filter_preferences = state.context.team_focus.evidence_preferences

    # Search with team-aware filtering
    documents = vector_db.search(
        enhanced_query,
        limit=limit * 2,
        filter_domains=[query.domain] if query.domain else None,
        filter_goals=None,
        exclude_sources=excluded_sources,
        # NEW: Team-specific filtering
        filter_evidence_types=filter_preferences if filter_preferences else None,
        member_expertise=query.member_expertise_focus,
    )

    print(
        f"RAG search for '{enhanced_query}' found {len(documents)} documents before team scoring"
    )

    # NEW: Apply team-specific scoring
    for doc in documents:
        doc = _apply_team_scoring(doc, query, state)

    # Sort by combined relevance (original + team scoring)
    documents.sort(
        key=lambda x: x.relevance_score
        + x.member_expertise_score
        + x.team_perspective_score,
        reverse=True,
    )

    # If we have a target goal, prefer documents with that goal
    if query.target_goal and documents:
        goal_matched = [doc for doc in documents if doc.goal == query.target_goal]
        no_goal = [doc for doc in documents if not doc.goal]
        other_goal = [
            doc for doc in documents if doc.goal and doc.goal != query.target_goal
        ]

        documents = goal_matched + no_goal + other_goal
        documents = documents[:limit]
    else:
        documents = documents[:limit]

    # Adjust relevance scores based on search type
    for doc in documents:
        if query.search_type == "supporting":
            doc.relevance_score *= 1.2
        elif query.search_type == "contradicting":
            doc.relevance_score *= 0.8

        # Assign goal if not set
        if not doc.goal:
            if query.target_goal:
                doc.goal = query.target_goal
            elif state.context.goals:
                doc.goal = assign_document_goal(doc, state, query)

    return documents


def _apply_team_scoring(
    doc: RetrievedDocument, query: SearchQuery, state: KnowledgeRetrievalState
) -> RetrievedDocument:
    """Apply team-specific scoring to documents"""
    doc_text = f"{doc.title} {doc.content}".lower()

    # Score based on member expertise
    if state.context.member_profile and state.context.member_profile.expertise_domains:
        expertise_score = 0
        for expertise in state.context.member_profile.expertise_domains:
            if expertise.lower() in doc_text:
                expertise_score += 0.3
        doc.member_expertise_score = min(expertise_score, 1.0)

    # Score based on team perspective
    if state.context.team_focus:
        perspective_score = 0

        # Check for team focus keywords
        for keyword in state.context.team_focus.focus_keywords:
            if keyword.lower() in doc_text:
                perspective_score += 0.2

        # Check for team priority aspects
        for aspect in state.context.team_focus.priority_aspects:
            if aspect.lower() in doc_text:
                perspective_score += 0.3

        # Check for team interests/concerns
        for concern in state.context.team_focus.interests_and_concerns:
            if concern.lower() in doc_text:
                perspective_score += 0.2

        # Penalize avoid keywords
        for avoid_keyword in state.context.team_focus.avoid_keywords:
            if avoid_keyword.lower() in doc_text:
                perspective_score -= 0.3

        doc.team_perspective_score = max(min(perspective_score, 1.0), 0.0)

    # Check evidence type match
    if (
        state.context.member_profile
        and state.context.member_profile.preferred_evidence_types
    ):
        for evidence_type in state.context.member_profile.preferred_evidence_types:
            if evidence_type.lower() in doc_text:
                doc.evidence_type_match = True
                break

    return doc


def assign_document_goal(
    doc: RetrievedDocument, state: KnowledgeRetrievalState, query: SearchQuery
) -> str:
    """Assign the most relevant goal to a document based on content, query, and team context"""
    if query.target_goal:
        return query.target_goal

    if not state.context.goals:
        return ""

    goal_scores = {}
    doc_text = f"{doc.title} {doc.content}".lower()

    for goal in state.context.goals:
        score = 0
        goal_keywords = goal.lower().split()
        score += sum(1 for keyword in goal_keywords if keyword in doc_text)

        # Boost score based on search type
        if query.search_type == "supporting" and "support" in goal.lower():
            score += 2
        elif query.search_type == "contradicting" and (
            "counter" in goal.lower() or "challenge" in goal.lower()
        ):
            score += 2

        # NEW: Boost score based on team context
        if state.context.team_focus:
            # If goal aligns with team priority aspects
            for aspect in state.context.team_focus.priority_aspects:
                if aspect.lower() in goal.lower():
                    score += 3

            # If goal aligns with team interests
            for concern in state.context.team_focus.interests_and_concerns:
                if concern.lower() in goal.lower():
                    score += 2

        goal_scores[goal] = score

    return max(goal_scores.items(), key=lambda x: x[1])[0]


def web_search(
    query: SearchQuery,
    vector_db: VectorDBManager,
    tavily_tool,
    state: KnowledgeRetrievalState,
    limit: int = 10,
) -> List[RetrievedDocument]:
    """Execute web search with team context consideration and store results in vector DB"""
    # # Build enhanced query with team perspective
    # perspective_part = (
    #     f" {query.perspective_modifier}" if query.perspective_modifier else ""
    # )

    # # NEW: Add team-specific search terms
    # team_modifier = ""
    # if state.context.team_focus:
    #     # Add team perspective keywords
    #     if state.context.team_focus.focus_keywords:
    #         team_modifier += f" {state.context.team_focus.focus_keywords[0]}"

    #     # Add priority aspect
    #     if state.context.team_focus.priority_aspects:
    #         team_modifier += f" {state.context.team_focus.priority_aspects[0]}"

    # # Add member expertise context
    # member_modifier = ""
    # if query.member_expertise_focus:
    #     member_modifier = f" {query.member_expertise_focus}"

    # enhanced_query = f"{query.query}{perspective_part}{team_modifier}{member_modifier}"

    # Execute web search
    search_results = None
    try:
        search_results = tavily_tool.invoke({"query": query.query})
    except Exception as e:
        print(f"Error executing web search: {e}")
        return []

    if "HTTPError" in str(search_results):
        print("Error in web search result: ", search_results)
        return []

    # Get excluded sources from state
    excluded_sources = set(state.context.excluded_sources)

    documents = []
    for idx, result in enumerate(search_results):
        # Skip if source was already retrieved
        if result.get("url", "") in excluded_sources:
            continue

        # Create document
        doc = RetrievedDocument(
            content=result.get("content", ""),
            title=result.get("title", ""),
            source=result.get("url", ""),
            relevance_score=1.0 - (idx * 0.1),
            domain=query.domain,
            goal=state.context.goals[0] if state.context.goals else "",
        )

        # NEW: Apply team scoring to web search results
        doc = _apply_team_scoring(doc, query, state)

        # Store in vector database for future use with team context
        doc.embedding_id = vector_db.add_document(doc)
        documents.append(doc)

        if len(documents) >= limit:
            break

    return documents
