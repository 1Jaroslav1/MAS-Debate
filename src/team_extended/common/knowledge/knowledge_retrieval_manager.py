from typing import List, Dict, Any, Optional
import json

from langchain_core.prompts import PromptTemplate

from src.team_extended.common.metrics.token_tracking import NodeTokenTracker

from .model import SearchQuery, SearchContext


class KnowledgeRetrievalManager:
    def __init__(self, llm, token_tracker: Optional[NodeTokenTracker] = None):
        self.llm = llm
        self.token_tracker = token_tracker
        self.search_query_prompt = PromptTemplate(
            template="""
            You are a Knowledge Retrieval Manager generating search queries for a specific team member.
            
            TOPIC & CONTEXT:
            Topic: {topic}
            Domains: {domains}
            Goals: {goals}
            Domain-Goal Connections: {domain_goal_connections}
            Previous Arguments: {previous_arguments}
            Current Perspective: {perspective}
            Iteration: {iteration}
            
            TEAM MEMBER PROFILE:
            Member Name: {member_name}
            Expertise Areas: {member_expertise}
            Preferred Evidence Types: {member_evidence_preferences}
            Communication Style: {member_communication_style}
            Industry Background: {member_industry}
            
            TEAM FOCUS CONTEXT:
            Team Type: {team_type}
            Team Perspective: {team_perspective_description}
            Team Orientation: {team_viewpoint_orientation}
            Priority Aspects: {team_priority_aspects}
            Evidence Preferences: {team_evidence_preferences}
            Focus Keywords: {team_focus_keywords}
            Interests/Concerns: {team_interests_concerns}
            
            SEARCH CONSTRAINTS:
            Previously Retrieved Sources (AVOID): {excluded_sources}
            Relevant Memories: {memories}
            
            Generate search queries that:
            1. ALIGN WITH MEMBER EXPERTISE: Leverage {member_name}'s knowledge in {member_expertise}
            2. SUPPORT TEAM PERSPECTIVE: Find evidence that supports the {team_type} viewpoint
            3. MATCH EVIDENCE PREFERENCES: Prioritize {member_evidence_preferences} and {team_evidence_preferences}
            4. COVER PRIORITY ASPECTS: Address {team_priority_aspects}
            5. SERVE TEAM INTERESTS: Consider {team_interests_concerns}
            6. FOCUS ON DOMAIN-GOAL CONNECTIONS: Prioritize evidence that connects specific domains to specific goals as shown in the connections
            7. AVOID DUPLICATION: Exclude sources already retrieved
            
            Create queries that would naturally appeal to {member_name} and support the {team_type} perspective.
            Each query should be 1-6 words of actual search terms that {member_name} would use.
            Generate max 3 queries sorted by impact and need.

            Return ONLY a valid JSON object (no other text) in this exact format:
            {{
                "queries": [
                    {{
                        "query": "search terms here",
                        "domain": "domain_name",
                        "search_type": "exploratory",
                        "priority": 1.0,
                        "perspective_modifier": "team perspective modifier",
                        "target_goal": "exact goal from the goals list",
                        "member_expertise_focus": "expertise area this targets",
                        "team_perspective_alignment": "how this supports team viewpoint",
                        "evidence_type_preference": "preferred evidence type"
                    }}
                ]
            }}
            
            Example for a technical lead on stakeholder team:
            {{
                "queries": [
                    {{
                        "query": "ROI metrics implementation costs",
                        "domain": "technology",
                        "search_type": "supporting",
                        "priority": 1.0,
                        "perspective_modifier": "analytical business perspective",
                        "target_goal": "g_costs",
                        "member_expertise_focus": "technical architecture",
                        "team_perspective_alignment": "supports stakeholder ROI concerns",
                        "evidence_type_preference": "performance metrics"
                    }}
                ]
            }}
            """,
            input_variables=[
                "topic",
                "domains",
                "goals",
                "domain_goal_connections",
                "previous_arguments",
                "perspective",
                "iteration",
                "member_name",
                "member_expertise",
                "member_evidence_preferences",
                "member_communication_style",
                "member_industry",
                "team_type",
                "team_perspective_description",
                "team_viewpoint_orientation",
                "team_priority_aspects",
                "team_evidence_preferences",
                "team_focus_keywords",
                "team_interests_concerns",
                "excluded_sources",
                "memories",
            ],
        )

    def generate_search_queries(self, context: SearchContext, memories: List[Dict[str, Any]]) -> List[SearchQuery]:
        """Generate search queries based on context, memories, and team integration"""

        # Extract member and team information
        member_info = (
            self._extract_member_info(context.member_profile)
            if context.member_profile
            else {}
        )
        team_info = (
            self._extract_team_info(context.team_focus) if context.team_focus else {}
        )

        # Format memories for prompt
        memory_text = ""
        excluded_sources = set()

        if memories:
            for mem in memories:
                memory_text += f"- Query: {mem.get('query', '')}\n"
                memory_text += f"  Domains: {', '.join(mem.get('domains', []))}\n"
                memory_text += f"  Goals: {', '.join(mem.get('goals', []))}\n"
                memory_text += f"  Perspective: {mem.get('perspective', 'N/A')}\n"
                memory_text += f"  Member: {mem.get('member_name', 'N/A')}\n"
                memory_text += f"  Team: {mem.get('team_type', 'N/A')}\n"
                memory_text += (
                    f"  Key findings: {len(mem.get('documents', []))} documents\n\n"
                )

                for source in mem.get("retrieved_sources", []):
                    excluded_sources.add(source)

        # Combine with excluded sources from context
        all_excluded_sources = list(
            excluded_sources.union(set(context.excluded_sources))
        )

        # Clean goal descriptions
        clean_goals = []
        for goal in context.goals:
            clean_goals.append(goal)

        # Format domain-goal connections
        domain_goal_text = ""
        if context.domain_goal_connections:
            for domain, goal in context.domain_goal_connections:
                domain_goal_text += f"• {domain} → {goal}\n"
        else:
            domain_goal_text = "None specified"

        # Prepare input with team integration
        input_data = {
            "topic": context.topic,
            "domains": ", ".join(context.domains),
            "goals": ", ".join(clean_goals),
            "domain_goal_connections": domain_goal_text,
            "previous_arguments": (
                ", ".join(context.previous_arguments)
                if context.previous_arguments
                else "None"
            ),
            "perspective": context.perspective or "neutral",
            "iteration": context.iteration_count,
            "memories": memory_text or "No relevant memories found",
            "excluded_sources": (
                ", ".join(all_excluded_sources[:10]) if all_excluded_sources else "None"
            ),
            **member_info,  # Include member profile information
            **team_info,  # Include team focus information
        }

        # Generate queries using LLM
        chain = self.search_query_prompt | self.llm

        try:
            # Invoke chain - result is an AIMessage with usage_metadata
            result = chain.invoke(input_data)

            # Track token usage - wrap AIMessage in dict format for StructuredOutputTokenExtractor
            if self.token_tracker:
                # Wrap in dict format that extractor expects: {"raw": AIMessage}
                wrapped_result = {"raw": result, "parsed": None}
                self.token_tracker.record_llm_call(wrapped_result, phase_name="search_query_generation")

            # Extract content from AIMessage
            response_text = (
                result.content if hasattr(result, "content") else str(result)
            )

            # Try to find JSON in the response
            import re

            json_match = re.search(r"\{.*\}", response_text, re.DOTALL)
            if json_match:
                json_str = json_match.group()
            else:
                print(f"No JSON found in response: {response_text[:200]}...")
                return self._create_fallback_queries(context)

            # Parse JSON
            queries_data = json.loads(json_str)
            queries = []

            for q in queries_data.get("queries", []):
                # Clean up the query text
                query_text = q.get("query", "")
                for goal in context.goals:
                    query_text = query_text.replace(goal, "").strip()

                if not query_text or not q.get("domain"):
                    continue

                # Validate target_goal
                target_goal = q.get("target_goal")
                if target_goal and target_goal not in context.goals:
                    for goal in context.goals:
                        if (
                            target_goal.lower() in goal.lower()
                            or goal.lower() in target_goal.lower()
                        ):
                            target_goal = goal
                            break
                    else:
                        target_goal = context.goals[0] if context.goals else None

                query = SearchQuery(
                    query=query_text,
                    domain=q.get(
                        "domain", context.domains[0] if context.domains else "general"
                    ),
                    search_type=q.get("search_type", "exploratory"),
                    priority=float(q.get("priority", 1.0)),
                    perspective_modifier=q.get("perspective_modifier"),
                    target_goal=target_goal,
                    # NEW: Team-specific fields
                    member_expertise_focus=q.get("member_expertise_focus"),
                    team_perspective_alignment=q.get("team_perspective_alignment"),
                    evidence_type_preference=q.get("evidence_type_preference"),
                )
                queries.append(query)

            if not queries:
                print("No valid queries generated, using fallback")
                return self._create_fallback_queries(context)

            # Ensure expertise coverage and team perspective alignment
            queries = self._enhance_queries_for_team_context(queries, context)

            queries.sort(key=lambda x: x.priority, reverse=True)
            return queries

        except Exception as e:
            print(f"Error in generate_search_queries: {e}")
            import traceback

            traceback.print_exc()
            return self._create_fallback_queries(context)

    def _extract_member_info(self, member_profile) -> Dict[str, str]:
        """Extract member profile information for prompt formatting"""
        if not member_profile:
            return {
                "member_name": "Unknown Member",
                "member_expertise": "General",
                "member_evidence_preferences": "Research",
                "member_communication_style": "Professional",
                "member_industry": "General",
            }

        return {
            "member_name": member_profile.name,
            "member_expertise": ", ".join(member_profile.expertise_domains),
            "member_evidence_preferences": ", ".join(
                member_profile.preferred_evidence_types
            ),
            "member_communication_style": member_profile.communication_style,
            "member_industry": member_profile.industry_background or "General",
        }

    def _extract_team_info(self, team_focus) -> Dict[str, str]:
        """Extract team focus information for prompt formatting"""
        if not team_focus:
            return {
                "team_type": "General Team",
                "team_perspective_description": "Balanced perspective",
                "team_viewpoint_orientation": "Neutral",
                "team_priority_aspects": "General considerations",
                "team_evidence_preferences": "Research",
                "team_focus_keywords": "None",
                "team_interests_concerns": "General concerns",
            }

        return {
            "team_type": team_focus.team_type,
            "team_perspective_description": team_focus.perspective_description,
            "team_viewpoint_orientation": team_focus.viewpoint_orientation,
            "team_priority_aspects": ", ".join(team_focus.priority_aspects),
            "team_evidence_preferences": ", ".join(team_focus.evidence_preferences),
            "team_focus_keywords": (
                ", ".join(team_focus.focus_keywords)
                if team_focus.focus_keywords
                else "None"
            ),
            "team_interests_concerns": ", ".join(team_focus.interests_and_concerns),
        }

    def _enhance_queries_for_team_context(self, queries: List[SearchQuery], context: SearchContext) -> List[SearchQuery]:
        """Enhance queries to ensure team context coverage"""
        enhanced_queries = queries.copy()

        # Ensure all member expertise areas are covered
        if context.member_profile and context.member_profile.expertise_domains:
            covered_expertise = {
                q.member_expertise_focus
                for q in enhanced_queries
                if q.member_expertise_focus
            }

            for expertise in context.member_profile.expertise_domains:
                if expertise not in covered_expertise:
                    # Create additional query for uncovered expertise
                    enhanced_queries.append(
                        SearchQuery(
                            query=f"{context.topic} {expertise}",
                            domain=context.domains[0] if context.domains else "general",
                            search_type="exploratory",
                            priority=0.7,
                            perspective_modifier=context.perspective,
                            target_goal=context.goals[0] if context.goals else None,
                            member_expertise_focus=expertise,
                            team_perspective_alignment="expertise coverage",
                            evidence_type_preference=(
                                context.member_profile.preferred_evidence_types[0]
                                if context.member_profile.preferred_evidence_types
                                else "research"
                            ),
                        )
                    )

        # Ensure team priority aspects are covered
        if context.team_focus and context.team_focus.priority_aspects:
            covered_aspects = {
                q.team_perspective_alignment
                for q in enhanced_queries
                if q.team_perspective_alignment
            }

            for aspect in context.team_focus.priority_aspects[
                :3
            ]:  # Top 3 priority aspects
                if not any(
                    aspect.lower() in str(covered).lower()
                    for covered in covered_aspects
                ):
                    # Create additional query for uncovered aspect
                    enhanced_queries.append(
                        SearchQuery(
                            query=f"{context.topic} {aspect}",
                            domain=context.domains[0] if context.domains else "general",
                            search_type="supporting",
                            priority=0.8,
                            perspective_modifier=f"{context.team_focus.viewpoint_orientation} {aspect}",
                            target_goal=context.goals[0] if context.goals else None,
                            member_expertise_focus="general",
                            team_perspective_alignment=f"covers {aspect}",
                            evidence_type_preference=(
                                context.team_focus.evidence_preferences[0]
                                if context.team_focus.evidence_preferences
                                else "research"
                            ),
                        )
                    )

        return enhanced_queries

    def _extract_goal_keywords(self, goal: str) -> str:
        """Extract meaningful keywords from goal, excluding IDs"""
        words = []
        for word in goal.split():
            if not word.startswith("g_"):
                words.append(word)
        return " ".join(words[-2:]) if words else ""

    def _create_fallback_queries(self, context: SearchContext) -> List[SearchQuery]:
        """Create fallback queries with team context consideration"""
        queries = []

        for i, goal in enumerate(context.goals):
            goal_keywords = goal.lower().split()[-2:]
            query_text = f"{context.topic} {' '.join(goal_keywords)}"

            if context.perspective:
                query_text += f" {context.perspective}"

            # Add member expertise if available
            member_focus = None
            evidence_pref = "research"
            if context.member_profile:
                if context.member_profile.expertise_domains:
                    member_focus = context.member_profile.expertise_domains[
                        i % len(context.member_profile.expertise_domains)
                    ]
                    query_text += f" {member_focus}"
                if context.member_profile.preferred_evidence_types:
                    evidence_pref = context.member_profile.preferred_evidence_types[0]

            # Add team perspective if available
            team_alignment = "general perspective"
            if context.team_focus:
                team_alignment = f"supports {context.team_focus.team_type} {context.team_focus.viewpoint_orientation}"
                if context.team_focus.priority_aspects:
                    priority_aspect = context.team_focus.priority_aspects[
                        i % len(context.team_focus.priority_aspects)
                    ]
                    query_text += f" {priority_aspect}"

            queries.append(
                SearchQuery(
                    query=query_text,
                    domain=(
                        context.domains[i % len(context.domains)]
                        if context.domains
                        else "general"
                    ),
                    search_type="exploratory",
                    priority=1.0 - (i * 0.1),
                    perspective_modifier=context.perspective,
                    target_goal=goal,
                    member_expertise_focus=member_focus,
                    team_perspective_alignment=team_alignment,
                    evidence_type_preference=evidence_pref,
                )
            )

        return queries
