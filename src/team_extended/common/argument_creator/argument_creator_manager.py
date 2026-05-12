import logging
from typing import Dict, Optional

from langchain_core.prompts import PromptTemplate

from .model import (
    ArgumentStrategy,
    ArgumentDraft,
    ArgumentCreatorState,
    MemberProfile,
    TeamFocusContext,
)
from src.team_extended.common.metrics.token_tracking import NodeTokenTracker

logger = logging.getLogger(__name__)


class ArgumentCreatorManager:
    def __init__(self, llm, use_personalization: bool = True, token_tracker: Optional[NodeTokenTracker] = None):
        self.llm = llm
        self.use_personalization = use_personalization
        self.token_tracker = token_tracker
        logger.info(f"[ARGUMENT CREATOR MANAGER] Initialized with use_personalization={use_personalization}")

        # Context analysis prompt WITH personalization (original version)
        self.context_analysis_prompt_personalized = PromptTemplate(
            template="""
            Analyze the argument creation context and determine the optimal approach for this specific team member.
            
            TOPIC & CONTEXT:
            Topic: {topic}
            Domain-Goal Connections: {domain_goal_connections}
            Iteration: {iteration_count}/{max_iterations}
            
            TEAM FOCUS CONTEXT:
            Team Type: {team_type}
            Team Perspective: {perspective_description}
            Viewpoint Orientation: {viewpoint_orientation}
            Primary Interests/Concerns: {interests_and_concerns}
            Priority Aspects: {priority_aspects}
            Evidence Preferences: {evidence_preferences}
            Counterargument Strategy: {counterargument_strategy}
            Rhetorical Emphasis: {rhetorical_emphasis}
            Focus Keywords: {focus_keywords}
            Avoid Keywords: {avoid_keywords}
            Typical Arguments: {typical_arguments}
            
            TEAM MEMBER PROFILE:
            Name: {member_name}
            Education: {member_education}
            Experience: {member_experience}
            Expertise: {member_expertise}
            Role: {member_role}
            
            MEMBER'S COGNITIVE & COMMUNICATION STYLE:
            Thinking Style: {thinking_style}
            Communication Style: {communication_style}
            Argumentation Preference: {argumentation_preference}
            Decision Making: {decision_making_style}
            
            MEMBER'S VALUES & BELIEFS:
            Core Values: {core_values}
            Philosophical Stance: {philosophical_stance}
            Risk Tolerance: {risk_tolerance}
            
            MEMBER'S PREFERENCES:
            Preferred Evidence: {preferred_evidence}
            Counterargument Approach: {counterargument_approach}
            Notable Biases: {notable_biases}
            
            CONTEXT:
            Previous Arguments: {previous_arguments}
            Reviewer Feedback: {reviewer_feedback}
            Available Knowledge: {knowledge_summary}
            
            Create a strategy that:
            1. SERVES THE TEAM PERSPECTIVE: Must represent the {team_type} viewpoint on {topic}
            2. EMPHASIZES PRIORITY ASPECTS: Focus on {priority_aspects}
            3. REFLECTS MEMBER AUTHENTICITY: Maintains {member_name}'s unique voice and expertise
            4. ALIGNS WITH TEAM ORIENTATION: Uses {viewpoint_orientation} approach with {evidence_preferences}
            5. ADDRESSES TEAM CONCERNS: Considers {interests_and_concerns}
            6. HANDLES OPPOSITION: Uses {counterargument_strategy} approach
            7. TARGETS SPECIFIC DOMAIN-GOAL PAIRS: Must address {domain_goal_connections}
            
            The strategy must balance team perspective requirements with the member's authentic voice.
            The argument should feel like {member_name} genuinely represents the {team_type} perspective.
            
            You MUST return a JSON object with ALL of the following fields:
            {{
                "approach": "Strategic approach that serves team perspective while matching member's style",
                "rhetorical_focus": "Primary rhetorical strategy aligned with team emphasis and member preference",
                "logical_structure": "Argument structure that fits member's thinking style and team needs",
                "evidence_priorities": ["Evidence types that support team perspective and match member preferences"],
                "counterargument_handling": "Strategy that reflects both team approach and member's style",
                "personalization_notes": "How this strategy reflects the member's unique profile",
                "perspective_alignment": "How the strategy specifically serves the {team_type} perspective",
                "focus_emphasis": ["Priority aspects from team focus that will be emphasized"],
                "evidence_perspective_filter": "How evidence selection will support the {team_type} viewpoint"
            }}
            """,
            input_variables=[
                "topic",
                "domain_goal_connections",
                "iteration_count",
                "max_iterations",
                "team_type",
                "perspective_description",
                "viewpoint_orientation",
                "interests_and_concerns",
                "priority_aspects",
                "evidence_preferences",
                "counterargument_strategy",
                "rhetorical_emphasis",
                "focus_keywords",
                "avoid_keywords",
                "typical_arguments",
                "member_name",
                "member_education",
                "member_experience",
                "member_expertise",
                "member_role",
                "thinking_style",
                "communication_style",
                "argumentation_preference",
                "decision_making_style",
                "core_values",
                "philosophical_stance",
                "risk_tolerance",
                "preferred_evidence",
                "counterargument_approach",
                "notable_biases",
                "previous_arguments",
                "reviewer_feedback",
                "knowledge_summary",
            ],
        )

        # Context analysis prompt WITHOUT personalization (no member profile data)
        self.context_analysis_prompt_non_personalized = PromptTemplate(
            template="""
            Analyze the argument creation context and determine the optimal approach for this team member.

            TOPIC & CONTEXT:
            Topic: {topic}
            Domain-Goal Connections: {domain_goal_connections}
            Iteration: {iteration_count}/{max_iterations}

            TEAM FOCUS CONTEXT:
            Team Type: {team_type}
            Team Perspective: {perspective_description}
            Viewpoint Orientation: {viewpoint_orientation}
            Primary Interests/Concerns: {interests_and_concerns}
            Priority Aspects: {priority_aspects}
            Evidence Preferences: {evidence_preferences}
            Counterargument Strategy: {counterargument_strategy}
            Rhetorical Emphasis: {rhetorical_emphasis}
            Focus Keywords: {focus_keywords}
            Avoid Keywords: {avoid_keywords}
            Typical Arguments: {typical_arguments}

            CONTEXT:
            Previous Arguments: {previous_arguments}
            Reviewer Feedback: {reviewer_feedback}
            Available Knowledge: {knowledge_summary}

            Create a strategy that:
            1. SERVES THE TEAM PERSPECTIVE: Must represent the {team_type} viewpoint on {topic}
            2. EMPHASIZES PRIORITY ASPECTS: Focus on {priority_aspects}
            3. ALIGNS WITH TEAM ORIENTATION: Uses {viewpoint_orientation} approach with {evidence_preferences}
            4. ADDRESSES TEAM CONCERNS: Considers {interests_and_concerns}
            5. HANDLES OPPOSITION: Uses {counterargument_strategy} approach
            6. TARGETS SPECIFIC DOMAIN-GOAL PAIRS: Must address {domain_goal_connections}

            The strategy must focus on team perspective requirements without relying on individual member characteristics.

            You MUST return a JSON object with ALL of the following fields:
            {{
                "approach": "Strategic approach that serves team perspective",
                "rhetorical_focus": "Primary rhetorical strategy aligned with team emphasis",
                "logical_structure": "Argument structure that fits team needs",
                "evidence_priorities": ["Evidence types that support team perspective"],
                "counterargument_handling": "Strategy that reflects team approach",
                "personalization_notes": "N/A - Non-personalized mode",
                "perspective_alignment": "How the strategy specifically serves the {team_type} perspective",
                "focus_emphasis": ["Priority aspects from team focus that will be emphasized"],
                "evidence_perspective_filter": "How evidence selection will support the {team_type} viewpoint"
            }}
            """,
            input_variables=[
                "topic",
                "domain_goal_connections",
                "iteration_count",
                "max_iterations",
                "team_type",
                "perspective_description",
                "viewpoint_orientation",
                "interests_and_concerns",
                "priority_aspects",
                "evidence_preferences",
                "counterargument_strategy",
                "rhetorical_emphasis",
                "focus_keywords",
                "avoid_keywords",
                "typical_arguments",
                "previous_arguments",
                "reviewer_feedback",
                "knowledge_summary",
            ],
        )

        # Argument construction prompt WITH personalization (original version)
        self.argument_construction_prompt_personalized = PromptTemplate(
            template="""
            ###
            STRATEGIC REQUIREMENTS - YOUR PRIMARY OBJECTIVE
            ###

            Topic: {topic}
            Your Perspective: {team_type} ({viewpoint_orientation})

            {domain_goal_connections}

            CRITICAL INSTRUCTIONS:
            1. Your argument MUST demonstrate how the specified domain(s) advance the specified goal(s)
            2. Use terminology from BOTH the goal description AND domain description
            3. Frame your entire argument through the domain lens (not generic arguments)
            4. Include domain-specific keywords 10-15 times throughout
            5. Opening sentence must reference the domain explicitly
            6. Closing sentence must reinforce the domain-goal connection

            ###
            YOUR PROFILE
            ###

            Name: {member_name}
            Role: {member_role}
            Expertise: {member_expertise}
            Communication Style: {communication_style}
            Argumentation Preference: {argumentation_preference}

            ###
            ADDITIONAL CONTEXT
            ###

            Team Concerns: {interests_and_concerns}
            Must Emphasize: {priority_aspects}
            Evidence Types: {evidence_preferences}

            Available Evidence: {evidence_summary}
            Previous Feedback: {reviewer_feedback}
            Avoid repeating: {previous_arguments}

            ###
            TASK
            ###

            Create a {team_type} argument that:
            1. Focuses on the specified domain-goal pairs (use exact terminology from descriptions)
            2. Represents your expertise and communication style
            3. Uses {argumentation_preference} approach
            4. Addresses the {team_type} perspective concerns

            STRUCTURE:
            - Opening: "From a [domain] perspective, [topic] raises questions about [goal]..."
            - Body: Demonstrate how domain relates to goal (use domain keywords extensively)
            - Closing: "These [domain] considerations show that [goal] is affected by..."

            You MUST return a JSON object with ALL fields:
            {{
                "main_thesis": "Thesis mentioning both domain and goal explicitly",
                "supporting_points": ["3-4 points using domain-specific terminology"],
                "evidence_integration": "How evidence supports the domain-goal connection",
                "counterargument_responses": ["Responses from the {team_type} perspective"],
                "conclusion": "Conclusion reinforcing domain-goal relationship",
                "full_argument": "Complete argument (focus on domain, not generic policy/tech)",
                "member_voice_notes": "Brief note on your style",
                "domain_alignment_check": "List the domain IDs you addressed (e.g., 'd_environment, d_public_policy')"
            }}
            """,
            input_variables=[
                "topic",
                "team_type",
                "viewpoint_orientation",
                "domain_goal_connections",
                "member_name",
                "member_role",
                "member_expertise",
                "communication_style",
                "argumentation_preference",
                "interests_and_concerns",
                "priority_aspects",
                "evidence_preferences",
                "evidence_summary",
                "reviewer_feedback",
                "previous_arguments",
            ],
        )

        # Argument construction prompt WITHOUT personalization (no member profile data)
        self.argument_construction_prompt_non_personalized = PromptTemplate(
            template="""
            ###
            STRATEGIC REQUIREMENTS - YOUR PRIMARY OBJECTIVE
            ###

            Topic: {topic}
            Your Perspective: {team_type} ({viewpoint_orientation})

            {domain_goal_connections}

            CRITICAL INSTRUCTIONS:
            1. Your argument MUST demonstrate how the specified domain(s) advance the specified goal(s)
            2. Use terminology from BOTH the goal description AND domain description
            3. Frame your entire argument through the domain lens (not generic arguments)
            4. Include domain-specific keywords 10-15 times throughout
            5. Opening sentence must reference the domain explicitly
            6. Closing sentence must reinforce the domain-goal connection

            ###
            TEAM CONTEXT
            ###

            Team Concerns: {interests_and_concerns}
            Must Emphasize: {priority_aspects}
            Evidence Types: {evidence_preferences}

            Available Evidence: {evidence_summary}
            Previous Feedback: {reviewer_feedback}
            Avoid repeating: {previous_arguments}

            ###
            TASK
            ###

            Create a {team_type} argument that:
            1. Focuses on the specified domain-goal pairs (use exact terminology from descriptions)
            2. Uses team's preferred approach and evidence
            3. Addresses the {team_type} perspective concerns

            STRUCTURE:
            - Opening: "From a [domain] perspective, [topic] raises questions about [goal]..."
            - Body: Demonstrate how domain relates to goal (use domain keywords extensively)
            - Closing: "These [domain] considerations show that [goal] is affected by..."

            You MUST return a JSON object with ALL fields:
            {{
                "main_thesis": "Thesis mentioning both domain and goal explicitly",
                "supporting_points": ["3-4 points using domain-specific terminology"],
                "evidence_integration": "How evidence supports the domain-goal connection",
                "counterargument_responses": ["Responses from the {team_type} perspective"],
                "conclusion": "Conclusion reinforcing domain-goal relationship",
                "full_argument": "Complete argument (focus on domain, not generic policy/tech)",
                "member_voice_notes": "N/A - Non-personalized mode",
                "domain_alignment_check": "List the domain IDs you addressed (e.g., 'd_environment, d_public_policy')"
            }}
            """,
            input_variables=[
                "topic",
                "team_type",
                "viewpoint_orientation",
                "domain_goal_connections",
                "interests_and_concerns",
                "priority_aspects",
                "evidence_preferences",
                "evidence_summary",
                "reviewer_feedback",
                "previous_arguments",
            ],
        )

    def _extract_team_focus_info(self, focus: TeamFocusContext) -> Dict[str, str]:
        """Extract team focus information for prompt formatting"""
        return {
            "team_type": focus.team_type,
            "perspective_descriptor": focus.get_perspective_descriptor(),
            "perspective_description": focus.perspective_description,
            "viewpoint_orientation": focus.viewpoint_orientation,
            "priority_aspects": ", ".join(focus.priority_aspects),
            "evidence_preferences": ", ".join(focus.evidence_preferences),
            "counterargument_strategy": focus.counterargument_strategy,
            "rhetorical_emphasis": focus.rhetorical_emphasis,
            "focus_keywords": (
                ", ".join(focus.focus_keywords)
                if focus.focus_keywords
                else "None specified"
            ),
            "avoid_keywords": (
                ", ".join(focus.avoid_keywords)
                if focus.avoid_keywords
                else "None specified"
            ),
            "interests_and_concerns": ", ".join(focus.interests_and_concerns),
            "typical_arguments": (
                ", ".join(focus.typical_arguments)
                if focus.typical_arguments
                else "Standard arguments for this perspective"
            ),
        }

    def _extract_member_info(self, profile: MemberProfile) -> Dict[str, str]:
        """Extract member profile information for prompt formatting"""
        return {
            "member_name": profile.name,
            "member_education": ", ".join(profile.education),
            "member_experience": ", ".join(profile.experience),
            "member_expertise": ", ".join(profile.expertise_domains),
            "member_role": profile.current_role,
            "thinking_style": profile.thinking_style,
            "communication_style": profile.communication_style,
            "argumentation_preference": profile.argumentation_preference,
            "decision_making_style": profile.decision_making_style,
            "core_values": ", ".join(profile.core_values),
            "philosophical_stance": profile.philosophical_stance,
            "risk_tolerance": profile.risk_tolerance,
            "preferred_evidence": ", ".join(profile.preferred_evidence_types),
            "counterargument_approach": profile.typical_counterargument_approach,
            "notable_biases": (
                ", ".join(profile.notable_biases)
                if profile.notable_biases
                else "None identified"
            ),
            "member_background": f"{profile.current_role} with expertise in {', '.join(profile.expertise_domains)}",
            "member_style": f"{profile.communication_style} communication, {profile.thinking_style} thinking",
        }

    def analyze_feedback_for_search(
        self, feedback: str, member_profile: MemberProfile, team_focus: TeamFocusContext
    ) -> Dict[str, str]:
        """Analyze reviewer feedback considering member's profile and team focus"""
        if not feedback:
            return {"search_modification": "none"}

        feedback_lower = feedback.lower()

        # Consider member's expertise and team orientation when interpreting feedback
        member_domains = [domain.lower() for domain in member_profile.expertise_domains]
        orientation_modifier = (
            team_focus.viewpoint_orientation
        )  # e.g., "supportive", "critical", "analytical", "protective"
        team_type = team_focus.team_type

        # Adjust search strategy based on member's background and team perspective
        if any(domain in feedback_lower for domain in member_domains):
            # Feedback relates to member's expertise area
            primary_expertise = member_profile.expertise_domains[0]
            return {
                "search_modification": f"expert_{orientation_modifier}_focus",
                "perspective_shift": f"expert {primary_expertise} {orientation_modifier} analysis from {team_type} perspective",
                "topic_modifier": f"{primary_expertise} {orientation_modifier} perspective on",
            }

        # Team perspective-aware feedback analysis
        if any(
            word in feedback_lower
            for word in ["counterargument", "opposing", "challenge"]
        ):
            # Handle challenges based on team's typical approach
            if "defensive" in team_focus.counterargument_strategy.lower():
                return {
                    "search_modification": "defensive_evidence",
                    "perspective_shift": f"defensive {team_type} analysis addressing challenges to {team_focus.priority_aspects[0] if team_focus.priority_aspects else 'concerns'}",
                    "topic_modifier": f"evidence supporting {team_type} concerns about",
                }
            elif "aggressive" in team_focus.counterargument_strategy.lower():
                return {
                    "search_modification": "counter_evidence",
                    "perspective_shift": f"counter-analysis from {team_type} perspective challenging {team_focus.avoid_keywords[0] if team_focus.avoid_keywords else 'opposing views'}",
                    "topic_modifier": f"evidence contradicting",
                }
            else:
                return {
                    "search_modification": "perspective_evidence",
                    "perspective_shift": f"{team_type} response to challenges regarding {team_focus.priority_aspects[0] if team_focus.priority_aspects else 'concerns'}",
                    "topic_modifier": f"{team_type} perspective on challenges to",
                }

        elif any(word in feedback_lower for word in ["evidence", "data", "research"]):
            # Focus on evidence that supports team perspective
            preferred_evidence = (
                member_profile.preferred_evidence_types[0]
                if member_profile.preferred_evidence_types
                else "research"
            )
            team_evidence = f"{team_type} {preferred_evidence}"
            return {
                "search_modification": "perspective_aligned_evidence",
                "perspective_shift": f"{team_evidence} focus from {orientation_modifier} viewpoint",
                "topic_modifier": f"{team_evidence} evidence",
            }

        elif any(word in feedback_lower for word in ["specific", "example", "case"]):
            # Look for examples that support team perspective
            primary_concern = (
                team_focus.interests_and_concerns[0]
                if team_focus.interests_and_concerns
                else "concerns"
            )
            if "supportive" in orientation_modifier.lower():
                return {
                    "search_modification": "success_cases",
                    "perspective_shift": f"success story focused on {primary_concern}",
                    "topic_modifier": f"successful examples addressing {primary_concern}",
                }
            elif "critical" in orientation_modifier.lower():
                return {
                    "search_modification": "failure_cases",
                    "perspective_shift": f"failure case focused on {primary_concern}",
                    "topic_modifier": f"problematic examples of {primary_concern}",
                }
            else:
                return {
                    "search_modification": "case_studies",
                    "perspective_shift": f"case study focused on {primary_concern}",
                    "topic_modifier": f"case studies of {primary_concern}",
                }

        # Check if feedback mentions team-specific concerns
        for concern in team_focus.interests_and_concerns:
            if concern.lower() in feedback_lower:
                return {
                    "search_modification": "concern_focused",
                    "perspective_shift": f"{team_type} analysis of {concern}",
                    "topic_modifier": f"{concern} implications of",
                }

        # Default to team-oriented alternative perspective
        return {
            "search_modification": f"{orientation_modifier}_alternative",
            "perspective_shift": f"{team_type} {orientation_modifier} alternative perspective",
            "topic_modifier": f"{team_type} {orientation_modifier} aspects of",
        }

    def analyze_context(self, state: ArgumentCreatorState) -> ArgumentCreatorState:
        """Analyze context and determine member-specific strategy with team focus"""
        logger.info(f"[MANAGER - ANALYZE CONTEXT] Starting - use_personalization={self.use_personalization}")

        member_info = self._extract_member_info(state.context.member_profile)
        team_focus_info = self._extract_team_focus_info(state.context.team_focus)

        # Analyze feedback with member profile and team focus consideration
        feedback_analysis = self.analyze_feedback_for_search(
            state.context.reviewer_feedback,
            state.context.member_profile,
            state.context.team_focus,
        )

        # Enhanced knowledge summary considering member's expertise and team stance
        knowledge_summary = ""
        if state.retrieved_knowledge:
            knowledge_summary = (
                f"Retrieved {len(state.retrieved_knowledge)} relevant documents"
            )

            # Check alignment with member's expertise and team stance
            member_domains = [
                d.lower() for d in state.context.member_profile.expertise_domains
            ]
            focus_keywords = [
                k.lower() for k in state.context.team_focus.focus_keywords
            ]

            relevant_docs = [
                doc
                for doc in state.retrieved_knowledge
                if any(domain in doc.content.lower() for domain in member_domains)
            ]
            stance_aligned_docs = [
                doc
                for doc in state.retrieved_knowledge
                if any(keyword in doc.content.lower() for keyword in focus_keywords)
            ]

            if relevant_docs:
                knowledge_summary += f" ({len(relevant_docs)} aligned with {state.context.member_profile.name}'s expertise)"
            if stance_aligned_docs:
                knowledge_summary += f" ({len(stance_aligned_docs)} supporting {state.context.team_focus.team_type})"

            if feedback_analysis["search_modification"] != "none":
                knowledge_summary += (
                    f"\nSearch adapted for {feedback_analysis['search_modification']}"
                )
        else:
            knowledge_summary = f"No knowledge retrieved yet for {state.context.member_profile.name}'s analysis"

        # Format domain-goal connections with full context
        domain_goal_text = ""
        if state.context.domain_goal_connections:
            domain_goal_text = "Your argument should focus on these strategic domain-goal pairs:\n\n"

            for idx, item in enumerate(state.context.domain_goal_connections, 1):
                if isinstance(item, dict):
                    # Enriched format with full descriptions
                    priority = "PRIMARY" if item.get('priority') == 'PRIMARY' else "SECONDARY"
                    domain_goal_text += f"{idx}. {priority} Strategic Target (UGN Value: {item.get('ugn_value', 0)}):\n"
                    domain_goal_text += f"   GOAL: '{item['goal_id']}'\n"
                    domain_goal_text += f"   Description: {item['goal_desc']}\n"
                    domain_goal_text += f"   DOMAIN: '{item['domain_id']}'\n"
                    domain_goal_text += f"   Description: {item['domain_desc']}\n"
                    domain_goal_text += f"   → Your argument MUST show how '{item['domain_id']}' advances '{item['goal_id']}'\n"
                    domain_goal_text += f"   → Use terminology from both descriptions above\n\n"
                elif isinstance(item, tuple):
                    # Legacy tuple format
                    domain, goal = item
                    domain_goal_text += f"{idx}. Domain '{domain}' → Goal '{goal}'\n"
                else:
                    domain_goal_text += f"{idx}. {item}\n"
        else:
            domain_goal_text = "No specific domain-goal targets specified."

        # Prepare strategy input based on personalization mode
        if self.use_personalization:
            # Include member profile information for personalized mode
            strategy_input = {
                "topic": state.context.topic,
                "domain_goal_connections": domain_goal_text,
                "iteration_count": state.context.iteration_count,
                "max_iterations": state.context.max_iterations,
                "previous_arguments": "\n".join(
                    f"- {arg}" for arg in state.context.previous_arguments
                ),
                "reviewer_feedback": state.context.reviewer_feedback
                or "No previous feedback",
                "knowledge_summary": knowledge_summary,
                **member_info,  # Include all member profile information
                **team_focus_info,  # Include all team focus information
            }
            # Use personalized prompt
            prompt = self.context_analysis_prompt_personalized
        else:
            # Exclude member profile information for non-personalized mode
            strategy_input = {
                "topic": state.context.topic,
                "domain_goal_connections": domain_goal_text,
                "iteration_count": state.context.iteration_count,
                "max_iterations": state.context.max_iterations,
                "previous_arguments": "\n".join(
                    f"- {arg}" for arg in state.context.previous_arguments
                ),
                "reviewer_feedback": state.context.reviewer_feedback
                or "No previous feedback",
                "knowledge_summary": knowledge_summary,
                **team_focus_info,
            }
            prompt = self.context_analysis_prompt_non_personalized

        logger.info(f"[MANAGER - ANALYZE CONTEXT] Using {'personalized' if self.use_personalization else 'non-personalized'} prompt")
        chain = prompt | self.llm.with_structured_output(
            ArgumentStrategy,
            include_raw=True
        )
        logger.info(f"[MANAGER - ANALYZE CONTEXT] Invoking LLM for strategy generation")
        result = chain.invoke(strategy_input)

        strategy = result["parsed"]
 
        if self.token_tracker:
            self.token_tracker.record_llm_call(result, phase_name="context_analysis")

        state.strategy = strategy
        logger.info(f"[MANAGER - ANALYZE CONTEXT] Completed - Generated strategy: {strategy.approach}")
        return state

    def construct_argument(self, state: ArgumentCreatorState) -> ArgumentCreatorState:
        """Construct argument focused on domain-goal pairs"""
        logger.info(f"[MANAGER - CONSTRUCT ARGUMENT] Starting - use_personalization={self.use_personalization}")

        member_info = self._extract_member_info(state.context.member_profile)
        team_focus_info = self._extract_team_focus_info(state.context.team_focus)

        # Prepare evidence summary
        evidence_summary = ""
        if state.retrieved_knowledge:
            logger.info(f"[MANAGER - CONSTRUCT ARGUMENT] Sorting {len(state.retrieved_knowledge)} retrieved documents")
            if self.use_personalization:
                sorted_docs = sorted(
                    state.retrieved_knowledge,
                    key=lambda doc: self._evidence_relevance_score(
                        doc, state.context.member_profile, state.context.team_focus
                    ),
                    reverse=True,
                )
            else:
                sorted_docs = sorted(
                    state.retrieved_knowledge,
                    key=lambda doc: self._evidence_relevance_score_team_only(
                        doc, state.context.team_focus
                    ),
                    reverse=True,
                )
            for doc in sorted_docs[:5]:
                evidence_summary += f"- {doc.title}: {doc.content[:200]}...\n"
        else:
            evidence_summary = "No evidence available"

        # Format domain-goal connections (reuse from analyze_context)
        domain_goal_text = ""
        if state.context.domain_goal_connections:
            domain_goal_text = "Your argument should focus on these strategic domain-goal pairs:\n\n"
            for idx, item in enumerate(state.context.domain_goal_connections, 1):
                if isinstance(item, dict):
                    priority = "PRIMARY" if item.get('priority') == 'PRIMARY' else "SECONDARY"
                    domain_goal_text += f"{idx}. {priority} Strategic Target (UGN Value: {item.get('ugn_value', 0)}):\n"
                    domain_goal_text += f"   GOAL: '{item['goal_id']}'\n"
                    domain_goal_text += f"   Description: {item['goal_desc']}\n"
                    domain_goal_text += f"   DOMAIN: '{item['domain_id']}'\n"
                    domain_goal_text += f"   Description: {item['domain_desc']}\n"
                    domain_goal_text += f"   → Your argument MUST show how '{item['domain_id']}' advances '{item['goal_id']}'\n"
                    domain_goal_text += f"   → Use terminology from both descriptions above\n\n"
                elif isinstance(item, tuple):
                    domain, goal = item
                    domain_goal_text += f"{idx}. Domain '{domain}' → Goal '{goal}'\n"
        else:
            domain_goal_text = "No specific domain-goal targets specified."

        # Prepare construction input based on personalization mode
        if self.use_personalization:
            # Include member profile information for personalized mode
            construction_input = {
                "topic": state.context.topic,
                "team_type": team_focus_info["team_type"],
                "viewpoint_orientation": team_focus_info["viewpoint_orientation"],
                "domain_goal_connections": domain_goal_text,
                "member_name": member_info["member_name"],
                "member_role": member_info["member_role"],
                "member_expertise": member_info["member_expertise"],
                "communication_style": member_info["communication_style"],
                "argumentation_preference": member_info["argumentation_preference"],
                "interests_and_concerns": team_focus_info["interests_and_concerns"],
                "priority_aspects": team_focus_info["priority_aspects"],
                "evidence_preferences": team_focus_info["evidence_preferences"],
                "evidence_summary": evidence_summary,
                "reviewer_feedback": state.context.reviewer_feedback or "No previous feedback",
                "previous_arguments": "\n".join(f"- {arg}" for arg in state.context.previous_arguments) or "None",
            }
            # Use personalized prompt
            prompt = self.argument_construction_prompt_personalized
        else:
            # Exclude member profile information for non-personalized mode
            construction_input = {
                "topic": state.context.topic,
                "team_type": team_focus_info["team_type"],
                "viewpoint_orientation": team_focus_info["viewpoint_orientation"],
                "domain_goal_connections": domain_goal_text,
                "interests_and_concerns": team_focus_info["interests_and_concerns"],
                "priority_aspects": team_focus_info["priority_aspects"],
                "evidence_preferences": team_focus_info["evidence_preferences"],
                "evidence_summary": evidence_summary,
                "reviewer_feedback": state.context.reviewer_feedback or "No previous feedback",
                "previous_arguments": "\n".join(f"- {arg}" for arg in state.context.previous_arguments) or "None",
            }
            # Use non-personalized prompt
            prompt = self.argument_construction_prompt_non_personalized

        # Generate argument with appropriate prompt
        logger.info(f"[MANAGER - CONSTRUCT ARGUMENT] Using {'personalized' if self.use_personalization else 'non-personalized'} prompt")
        chain = prompt | self.llm.with_structured_output(
            ArgumentDraft,
            include_raw=True  # Include raw response to get token usage
        )
        logger.info(f"[MANAGER - CONSTRUCT ARGUMENT] Invoking LLM for argument generation")
        result = chain.invoke(construction_input)

        draft = result["parsed"]

        if self.token_tracker:
            self.token_tracker.record_llm_call(result, phase_name="argument_construction")

        state.draft = draft
        logger.info(f"[MANAGER - CONSTRUCT ARGUMENT] Completed - Generated {len(draft.full_argument)} character argument")
        return state

    def _evidence_relevance_score(
        self, doc, member_profile: MemberProfile, team_focus: TeamFocusContext
    ):
        """Score document relevance based on member's preferences and team focus"""
        score = 0
        content_lower = doc.content.lower()

        # Score based on member's preferred evidence types
        for evidence_type in member_profile.preferred_evidence_types:
            if evidence_type.lower() in content_lower:
                score += 2

        # Score based on member's expertise domains
        for domain in member_profile.expertise_domains:
            if domain.lower() in content_lower:
                score += 3

        # Score based on team focus keywords (perspective support)
        for keyword in team_focus.focus_keywords:
            if keyword.lower() in content_lower:
                score += 4  # Higher weight for perspective alignment

        # Penalize content with avoid keywords (opposing perspective indicators)
        for avoid_keyword in team_focus.avoid_keywords:
            if avoid_keyword.lower() in content_lower:
                score -= 2

        # Score based on team's evidence preferences
        for evidence_pref in team_focus.evidence_preferences:
            if evidence_pref.lower() in content_lower:
                score += 3

        # Score based on team's priority aspects
        for aspect in team_focus.priority_aspects:
            if aspect.lower() in content_lower:
                score += 3

        # Score based on team's interests and concerns
        for concern in team_focus.interests_and_concerns:
            if concern.lower() in content_lower:
                score += 2

        return score

    def _evidence_relevance_score_team_only(
        self, doc, team_focus: TeamFocusContext
    ):
        """Score document relevance based only on team focus (no member profile)"""
        score = 0
        content_lower = doc.content.lower()

        # Score based on team focus keywords (perspective support)
        for keyword in team_focus.focus_keywords:
            if keyword.lower() in content_lower:
                score += 4  # Higher weight for perspective alignment

        # Penalize content with avoid keywords (opposing perspective indicators)
        for avoid_keyword in team_focus.avoid_keywords:
            if avoid_keyword.lower() in content_lower:
                score -= 2

        # Score based on team's evidence preferences
        for evidence_pref in team_focus.evidence_preferences:
            if evidence_pref.lower() in content_lower:
                score += 3

        # Score based on team's priority aspects
        for aspect in team_focus.priority_aspects:
            if aspect.lower() in content_lower:
                score += 3

        # Score based on team's interests and concerns
        for concern in team_focus.interests_and_concerns:
            if concern.lower() in content_lower:
                score += 2

        return score

