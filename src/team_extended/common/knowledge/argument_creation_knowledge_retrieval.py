"""
Knowledge retrieval module for argument creation with evidence enhancement.

This module handles knowledge retrieval when the evaluator identifies arguments
with insufficient evidence that need to be strengthened.
"""

import logging
import uuid
from typing import List
from langchain_core.runnables import RunnableConfig

from .knowledge_retrieval_workflow import create_knowledge_retrieval_workflow
from .model import KnowledgeRetrievalState, SearchContext
from .vector_db_manager import VectorDBManager

logger = logging.getLogger(__name__)


class ArgumentCreationKnowledgeRetriever:
    """
    Handles knowledge retrieval for argument creation with member and team awareness.
    
    This class is responsible for:
    - Detecting when arguments need additional evidence
    - Creating member-adaptive search contexts
    - Filtering knowledge based on member expertise
    - Combining new and existing knowledge
    """

    def __init__(
        self,
        llm,
        vector_db: VectorDBManager,
        tavily_tool=None,
        store=None,
        use_personalization: bool = True,
    ):
        self.llm = llm
        self.vector_db = vector_db
        self.tavily_tool = tavily_tool
        self.store = store
        self.use_personalization = use_personalization
        logger.info(f"[KNOWLEDGE RETRIEVER] Initialized with use_personalization={use_personalization}")

    def retrieve_knowledge_for_argument(
        self, state, config: RunnableConfig
    ):
        """
        Retrieve knowledge considering member's expertise and preferences.

        This method checks if new knowledge is needed based on reviewer feedback
        and retrieves additional evidence when required.

        Args:
            state: ArgumentCreatorState with context and existing knowledge
            config: RunnableConfig for the workflow execution

        Returns:
            Updated state with retrieved knowledge
        """
        logger.info(f"[KNOWLEDGE RETRIEVER] Starting knowledge retrieval for topic: {state.context.topic}")

        # Check if we need new knowledge based on member profile and feedback
        needs_new_knowledge = self._should_retrieve_new_knowledge(state)
        logger.info(f"[KNOWLEDGE RETRIEVER] Needs new knowledge: {needs_new_knowledge}")

        if needs_new_knowledge:
            # Create search context adapted to member and team
            logger.info(f"[KNOWLEDGE RETRIEVER] Creating search context - use_personalization={self.use_personalization}")
            search_context = self._create_member_adaptive_search_context(state)

            # Add existing sources to excluded list to avoid duplicates
            existing_sources = [
                doc.source
                for doc in state.retrieved_knowledge
                if hasattr(doc, "source")
            ]
            search_context.excluded_sources.extend(existing_sources)

            # Execute knowledge retrieval workflow
            logger.info(f"[KNOWLEDGE RETRIEVER] Executing knowledge retrieval workflow")
            retrieved_docs = self._execute_knowledge_retrieval(
                search_context, config
            )
            logger.info(f"[KNOWLEDGE RETRIEVER] Retrieved {len(retrieved_docs)} documents")

            # Filter and combine knowledge
            if self.use_personalization:
                logger.info(f"[KNOWLEDGE RETRIEVER] Combining knowledge with member-specific filtering")
                state.retrieved_knowledge = self._combine_knowledge(
                    state.retrieved_knowledge,
                    retrieved_docs,
                    state.context.member_profile,
                )
            else:
                logger.info(f"[KNOWLEDGE RETRIEVER] Combining knowledge without member-specific filtering")
                # Without personalization, just combine without member-specific filtering
                state.retrieved_knowledge = self._combine_knowledge_non_personalized(
                    state.retrieved_knowledge,
                    retrieved_docs,
                )
            logger.info(f"[KNOWLEDGE RETRIEVER] Total knowledge documents: {len(state.retrieved_knowledge)}")

        logger.info(f"[KNOWLEDGE RETRIEVER] Completed knowledge retrieval")
        return state

    def _should_retrieve_new_knowledge(self, state) -> bool:
        """Determine if new knowledge retrieval is needed based on feedback"""
        if not state.context.reviewer_feedback:
            return False

        feedback_keywords = ["evidence", "research", "data", "source"]
        return any(
            keyword in state.context.reviewer_feedback.lower()
            for keyword in feedback_keywords
        )

    def _execute_knowledge_retrieval(
        self, search_context: SearchContext, config
    ) -> List:
        """Execute the knowledge retrieval workflow and return documents"""
        knowledge_retrieval_workflow = create_knowledge_retrieval_workflow(
            llm=self.llm,
            vector_db=self.vector_db,
            tavily_tool=self.tavily_tool,
            store=self.store,
            use_web_search=(self.tavily_tool is not None),
        )

        # Ensure session_id is set
        if not search_context.session_id:
            search_context.session_id = str(uuid.uuid4())

        initial_state = KnowledgeRetrievalState(
            context=search_context, session_id=search_context.session_id
        )

        config = {"configurable": {"session_id": search_context.session_id}}

        result = knowledge_retrieval_workflow.invoke(initial_state, config)
        return result.retrieved_documents

    def _combine_knowledge(
        self, existing_knowledge: List, new_documents: List, member_profile
    ) -> List:
        """Combine existing and new knowledge, filtering and deduplicating"""
        # Filter new knowledge for member relevance
        new_filtered_knowledge = self._filter_knowledge_for_member(
            new_documents, member_profile
        )

        # Combine and deduplicate based on source/content
        combined_knowledge = list(existing_knowledge)  # Start with existing
        existing_sources = {
            doc.source for doc in combined_knowledge if hasattr(doc, "source")
        }

        for new_doc in new_filtered_knowledge:
            if not hasattr(new_doc, "source") or new_doc.source not in existing_sources:
                combined_knowledge.append(new_doc)

        return combined_knowledge

    def _combine_knowledge_non_personalized(
        self, existing_knowledge: List, new_documents: List
    ) -> List:
        """Combine existing and new knowledge without member-specific filtering"""
        # Combine and deduplicate based on source/content only
        combined_knowledge = list(existing_knowledge)  # Start with existing
        existing_sources = {
            doc.source for doc in combined_knowledge if hasattr(doc, "source")
        }

        for new_doc in new_documents:
            if not hasattr(new_doc, "source") or new_doc.source not in existing_sources:
                combined_knowledge.append(new_doc)

        return combined_knowledge

    def _create_member_adaptive_search_context(self, state) -> SearchContext:
        """Create search context adapted for the specific member's profile and team focus"""
        base_topic = state.context.topic
        base_perspective = state.context.team_focus.perspective_description
        feedback = state.context.reviewer_feedback or ""
        iteration = state.context.iteration_count
        member = state.context.member_profile
        team_focus = state.context.team_focus

        if self.use_personalization:
            perspective_informed_perspective = SearchContextAdapter.get_team_stance_perspective(
                team_focus, member, base_perspective
            )
            perspective_informed_topic = SearchContextAdapter.adapt_topic_for_team_stance(
                base_topic, team_focus, member
            )
        else:
            # Without personalization, use team-only perspective
            perspective_informed_perspective = SearchContextAdapter.get_team_only_perspective(
                team_focus, base_perspective
            )
            perspective_informed_topic = SearchContextAdapter.adapt_topic_for_team_only(
                base_topic, team_focus
            )

        # Collect previously retrieved sources to exclude them
        excluded_sources = []
        if hasattr(state, "retrieved_knowledge") and state.retrieved_knowledge:
            excluded_sources = [doc.source for doc in state.retrieved_knowledge]

        # Analyze feedback with team perspective and member considerations
        modified_topic = perspective_informed_topic
        modified_perspective = perspective_informed_perspective

        feedback_lower = feedback.lower()

        if "counterargument" in feedback_lower or "opposing" in feedback_lower:
            modified_topic, modified_perspective = self._adapt_for_counterargument(
                feedback_lower, team_focus, perspective_informed_perspective, base_topic
            )

        elif "evidence" in feedback_lower and "weak" in feedback_lower:
            modified_topic, modified_perspective = self._adapt_for_weak_evidence(
                team_focus, perspective_informed_perspective, base_topic
            )

        elif "specific" in feedback_lower or "example" in feedback_lower:
            modified_topic, modified_perspective = self._adapt_for_examples(
                team_focus, perspective_informed_perspective, base_topic
            )

        elif any(aspect in feedback_lower for aspect in team_focus.priority_aspects):
            modified_topic, modified_perspective = self._adapt_for_priority_aspects(
                feedback_lower, team_focus, perspective_informed_perspective, base_topic
            )

        elif any(
            concern in feedback_lower for concern in team_focus.interests_and_concerns
        ):
            modified_topic, modified_perspective = self._adapt_for_concerns(
                feedback_lower, team_focus, perspective_informed_perspective, base_topic
            )

        elif iteration > 1:
            if self.use_personalization:
                iteration_perspectives = SearchContextAdapter.get_team_iteration_perspectives(
                    team_focus, member, iteration
                )
            else:
                iteration_perspectives = SearchContextAdapter.get_team_only_iteration_perspectives(
                    team_focus, iteration
                )
            modified_perspective = iteration_perspectives
            modified_topic = f"{modified_perspective} {base_topic}"

        return SearchContext(
            topic=modified_topic,
            domains=state.context.domains,
            goals=state.context.goals,
            perspective=modified_perspective,
            iteration_count=state.context.iteration_count,
            previous_arguments=state.context.previous_arguments,
            session_id=state.context.session_id,
            excluded_sources=excluded_sources,
        )

    def _adapt_for_counterargument(
        self, feedback_lower, team_focus, perspective, base_topic
    ):
        """Adapt search for counterargument-related feedback"""
        if "defensive" in team_focus.counterargument_strategy.lower():
            modified_perspective = f"defensive {perspective} addressing challenges"
            modified_topic = (
                f"evidence supporting {team_focus.team_type} concerns about {base_topic}"
            )
        elif "aggressive" in team_focus.counterargument_strategy.lower():
            modified_perspective = f"counter-attack {perspective} exposing problems"
            modified_topic = f"evidence contradicting opposing views on {base_topic}"
        else:
            modified_perspective = f"balanced {perspective} addressing opposition"
            modified_topic = (
                f"{team_focus.team_type} response to challenges about {base_topic}"
            )
        return modified_topic, modified_perspective

    def _adapt_for_weak_evidence(self, team_focus, perspective, base_topic):
        """Adapt search for weak evidence feedback"""
        team_evidence_type = (
            team_focus.evidence_preferences[0]
            if team_focus.evidence_preferences
            else "research"
        )
        modified_perspective = f"{team_evidence_type} focused {perspective}"
        modifier = SearchContextAdapter.get_perspective_topic_modifier(
            team_focus.viewpoint_orientation
        )
        modified_topic = f"{team_evidence_type} evidence {modifier} {base_topic}"
        return modified_topic, modified_perspective

    def _adapt_for_examples(self, team_focus, perspective, base_topic):
        """Adapt search for specific examples feedback"""
        primary_concern = (
            team_focus.interests_and_concerns[0]
            if team_focus.interests_and_concerns
            else "concerns"
        )
        modified_perspective = f"case study focused {perspective}"
        modified_topic = f"examples of {primary_concern} in {base_topic}"
        return modified_topic, modified_perspective

    def _adapt_for_priority_aspects(
        self, feedback_lower, team_focus, perspective, base_topic
    ):
        """Adapt search for priority aspects mentioned in feedback"""
        mentioned_aspect = next(
            aspect for aspect in team_focus.priority_aspects if aspect in feedback_lower
        )
        modified_perspective = f"{mentioned_aspect} focused {perspective}"
        modified_topic = f"{mentioned_aspect} aspects of {base_topic} from {team_focus.team_type} perspective"
        return modified_topic, modified_perspective

    def _adapt_for_concerns(self, feedback_lower, team_focus, perspective, base_topic):
        """Adapt search for concerns mentioned in feedback"""
        mentioned_concern = next(
            concern
            for concern in team_focus.interests_and_concerns
            if concern in feedback_lower
        )
        modified_perspective = f"{mentioned_concern} focused {perspective}"
        modified_topic = f"{mentioned_concern} implications of {base_topic}"
        return modified_topic, modified_perspective

    def _filter_knowledge_for_member(self, documents, member_profile):
        """Filter and prioritize retrieved documents based on member's expertise and preferences"""
        if not documents:
            return documents

        # Score documents based on member relevance
        scored_docs = []
        for doc in documents:
            score = MemberRelevanceScorer.calculate_score(doc, member_profile)
            scored_docs.append((doc, score))

        # Sort by relevance score (highest first)
        scored_docs.sort(key=lambda x: x[1], reverse=True)

        # Return documents in order of member relevance
        return [doc for doc, score in scored_docs]


class SearchContextAdapter:
    """Adapter for creating search contexts based on team and member profiles"""

    @staticmethod
    def get_team_only_perspective(team_focus, base_perspective: str) -> str:
        """Generate a team perspective-informed viewpoint without member-specific information"""
        orientation_modifier = team_focus.viewpoint_orientation
        primary_aspect = (
            team_focus.priority_aspects[0]
            if team_focus.priority_aspects
            else "general"
        )
        team_type = team_focus.team_type

        return f"{orientation_modifier} perspective emphasizing {primary_aspect} from {team_type} viewpoint"

    @staticmethod
    def adapt_topic_for_team_only(topic: str, team_focus) -> str:
        """Adapt the search topic to reflect team perspective without member expertise"""
        orientation_modifier = team_focus.viewpoint_orientation
        primary_aspect = (
            team_focus.priority_aspects[0]
            if team_focus.priority_aspects
            else "general"
        )
        team_type = team_focus.team_type

        return f"{orientation_modifier} {primary_aspect} aspects of {topic} from {team_type} perspective"

    @staticmethod
    def get_team_only_iteration_perspectives(team_focus, iteration: int) -> str:
        """Get iteration-specific perspectives based on team focus only (no member profile)"""
        orientation_modifier = team_focus.viewpoint_orientation
        team_type = team_focus.team_type

        # Base perspectives that adapt to different team orientations
        perspectives = SearchContextAdapter._get_base_perspectives(orientation_modifier)

        # Select perspective based on iteration
        selected_perspective = perspectives[(iteration - 2) % len(perspectives)]

        return f"{orientation_modifier} analysis of {selected_perspective} from {team_type} perspective"

    @staticmethod
    def get_team_stance_perspective(team_focus, member, base_perspective: str) -> str:
        """Generate a team perspective-informed viewpoint based on member background and team focus"""
        # Combine member's expertise with team perspective requirements
        expertise_focus = (
            member.expertise_domains[0] if member.expertise_domains else "professional"
        )
        thinking_approach = member.thinking_style.lower()
        orientation_modifier = team_focus.viewpoint_orientation

        # Incorporate priority aspects from team focus
        primary_aspect = (
            team_focus.priority_aspects[0]
            if team_focus.priority_aspects
            else "general"
        )
        team_type = team_focus.team_type

        if "analytical" in thinking_approach:
            return f"analytical {expertise_focus} {orientation_modifier} perspective emphasizing {primary_aspect} from {team_type} viewpoint"
        elif "creative" in thinking_approach:
            return f"innovative {expertise_focus} {orientation_modifier} approach highlighting {primary_aspect} for {team_type}"
        elif "systematic" in thinking_approach:
            return f"systematic {expertise_focus} {orientation_modifier} analysis of {primary_aspect} from {team_type} perspective"
        else:
            return f"{expertise_focus} {orientation_modifier} perspective on {primary_aspect} representing {team_type}"

    @staticmethod
    def adapt_topic_for_team_stance(topic: str, team_focus, member) -> str:
        """Adapt the search topic to reflect team perspective and member expertise"""
        orientation_modifier = team_focus.viewpoint_orientation
        primary_expertise = (
            member.expertise_domains[0] if member.expertise_domains else "professional"
        )
        primary_aspect = (
            team_focus.priority_aspects[0]
            if team_focus.priority_aspects
            else "general"
        )
        team_type = team_focus.team_type

        return f"{primary_expertise} analysis of {orientation_modifier} {primary_aspect} aspects of {topic} from {team_type} perspective"

    @staticmethod
    def get_perspective_topic_modifier(viewpoint_orientation: str) -> str:
        """Get topic modifier based on team viewpoint orientation"""
        if "supportive" in viewpoint_orientation.lower():
            return "supporting"
        elif "critical" in viewpoint_orientation.lower():
            return "challenging"
        elif "protective" in viewpoint_orientation.lower():
            return "protecting against"
        elif "analytical" in viewpoint_orientation.lower():
            return "analyzing"
        else:
            return "regarding"

    @staticmethod
    def get_team_iteration_perspectives(team_focus, member, iteration: int) -> str:
        """Get iteration-specific perspectives based on team focus and member profile"""
        orientation_modifier = team_focus.viewpoint_orientation
        team_type = team_focus.team_type

        # Base perspectives that adapt to different team orientations
        perspectives = SearchContextAdapter._get_base_perspectives(orientation_modifier)

        # Add member's risk tolerance flavor
        perspectives = SearchContextAdapter._adjust_for_risk_tolerance(
            perspectives, member.risk_tolerance, orientation_modifier
        )

        # Add member's expertise and team type flavor
        selected_perspective = perspectives[(iteration - 2) % len(perspectives)]
        expertise = (
            member.expertise_domains[0] if member.expertise_domains else "professional"
        )

        return f"{expertise} {orientation_modifier} analysis of {selected_perspective} from {team_type} perspective"

    @staticmethod
    def _get_base_perspectives(orientation_modifier: str) -> List[str]:
        """Get base perspectives based on orientation"""
        if "supportive" in orientation_modifier.lower():
            return [
                "implementation benefits",
                "positive outcomes",
                "long-term value",
                "stakeholder advantages",
            ]
        elif "critical" in orientation_modifier.lower():
            return [
                "implementation risks",
                "potential drawbacks",
                "long-term costs",
                "stakeholder concerns",
            ]
        elif "protective" in orientation_modifier.lower():
            return [
                "security implications",
                "risk mitigation",
                "defensive measures",
                "safety considerations",
            ]
        elif "analytical" in orientation_modifier.lower():
            return [
                "data analysis",
                "systematic evaluation",
                "evidence assessment",
                "objective comparison",
            ]
        else:
            return [
                "practical considerations",
                "stakeholder impact",
                "implementation factors",
                "outcome analysis",
            ]

    @staticmethod
    def _adjust_for_risk_tolerance(
        perspectives: List[str], risk_tolerance: str, orientation_modifier: str
    ) -> List[str]:
        """Adjust perspectives based on member's risk tolerance"""
        if "conservative" in risk_tolerance.lower():
            if "supportive" in orientation_modifier.lower():
                return [
                    "proven benefits",
                    "low-risk advantages",
                    "established value",
                    "stable outcomes",
                ]
            elif "critical" in orientation_modifier.lower():
                return [
                    "proven risks",
                    "established problems",
                    "documented failures",
                    "known challenges",
                ]
            else:
                return [
                    "conservative approach",
                    "risk-averse analysis",
                    "proven methods",
                    "stable considerations",
                ]
        elif "aggressive" in risk_tolerance.lower():
            if "supportive" in orientation_modifier.lower():
                return [
                    "innovative potential",
                    "breakthrough opportunities",
                    "disruptive advantages",
                    "transformative benefits",
                ]
            elif "critical" in orientation_modifier.lower():
                return [
                    "emerging risks",
                    "potential disruptions",
                    "unforeseen consequences",
                    "systemic problems",
                ]
            else:
                return [
                    "bold initiatives",
                    "aggressive strategies",
                    "innovative approaches",
                    "transformative potential",
                ]

        return perspectives


class MemberRelevanceScorer:
    """Scorer for calculating document relevance to specific members"""

    @staticmethod
    def calculate_score(doc, member_profile) -> float:
        """Calculate how relevant a document is to the specific member"""
        score = 0.0
        content_lower = doc.content.lower()

        # Score based on expertise domains
        for domain in member_profile.expertise_domains:
            if domain.lower() in content_lower:
                score += 3.0

        # Score based on preferred evidence types
        for evidence_type in member_profile.preferred_evidence_types:
            if evidence_type.lower() in content_lower:
                score += 2.0

        # Score based on industry background
        if (
            member_profile.industry_background
            and member_profile.industry_background.lower() in content_lower
        ):
            score += 2.0

        # Score based on core values (concepts that matter to them)
        for value in member_profile.core_values:
            if value.lower() in content_lower:
                score += 1.0

        return score

