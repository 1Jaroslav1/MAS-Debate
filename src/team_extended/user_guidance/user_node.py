from typing import Optional
from dataclasses import dataclass
from src.reasoning.godsaf.godsaf_service import CandidateArgument
from src.team_extended.user_guidance.user_guidance_service import UserGuidanceService


@dataclass
class UserInteractionState:
    """State to track user interaction progress across interrupts."""
    step: int = 0
    want_guidance: Optional[str] = None
    guidance_shown: bool = False
    argument_text: Optional[str] = None
    llm_draft_generated: bool = False
    llm_choice: Optional[str] = None
    final_argument: Optional[str] = None
    evaluation_shown: bool = False
    commit_choice: Optional[str] = None


class UserInteractionService:
    """
    Service that handles all user interaction logic using LangGraph interrupts.
    """
    
    def __init__(self, guidance_service: UserGuidanceService):
        self.guidance_service = guidance_service
        
    def run_user_interaction(self, user_team: str, topic: str, 
                           interaction_state: Optional[UserInteractionState] = None) -> tuple[str, UserInteractionState]:
        """
        Complete user interaction flow using interrupts.
        
        Returns:
            Tuple of (final argument text, interaction state)
        """
        if interaction_state is None:
            interaction_state = UserInteractionState()
        
        # Step 1: Ask if user wants guidance
        if interaction_state.step == 0:
            if interaction_state.want_guidance is None:
                interaction_state.want_guidance = input(
                    "🎓 Would you like strategic guidance using GoDsAF analysis? (y/n): "
                )
            interaction_state.step = 1
        
        # Step 2: Show guidance if requested
        if interaction_state.step == 1:
            guidance = None
            if interaction_state.want_guidance.lower() == 'y' and not interaction_state.guidance_shown:
                guidance = self.guidance_service.get_strategic_guidance(user_team)
                self._show_guidance(guidance)
                interaction_state.guidance_shown = True
            interaction_state.step = 2
            # Store guidance for later use
            self._current_guidance = guidance if interaction_state.want_guidance.lower() == 'y' else None
        
        # Step 3: Get user's argument
        if interaction_state.step == 2:
            if interaction_state.argument_text is None:
                prompt = self._build_argument_prompt(self._current_guidance)
                interaction_state.argument_text = input(prompt)
            interaction_state.step = 3
        
        # Step 4: Handle LLM assistance if requested
        if interaction_state.step == 3:
            if (interaction_state.argument_text.lower() in ['help', 'llm', 'draft'] and 
                not interaction_state.llm_draft_generated):
                
                if self._current_guidance and self.guidance_service.llm:
                    print("\n🤖 Generating argument draft based on strategic guidance...")
                    draft_info = self._generate_and_show_llm_draft(self._current_guidance, user_team, topic)
                    interaction_state.llm_draft_generated = True
                    
                    if interaction_state.llm_choice is None:
                        interaction_state.llm_choice = input(
                            "Choose: (1) Use this draft (2) Modify it (3) Create your own: "
                        )
                    
                    # Process LLM choice
                    interaction_state.final_argument = self._process_llm_choice(
                        interaction_state.llm_choice, draft_info
                    )
                else:
                    print("\n❌ LLM assistance not available.")
                    if interaction_state.final_argument is None:
                        interaction_state.final_argument = input("Please enter your argument manually: \n --> YOUR ARGUMENT: ")
            else:
                interaction_state.final_argument = interaction_state.argument_text
            
            interaction_state.step = 4
        
        # Step 5: Parse, evaluate and show results
        if interaction_state.step == 4:
            if interaction_state.final_argument and not interaction_state.evaluation_shown:
                suggestion = self.guidance_service.parse_and_evaluate_argument(
                    interaction_state.final_argument, user_team, topic
                )
                self._show_evaluation(interaction_state.final_argument, suggestion)
                interaction_state.evaluation_shown = True
                # Store for commit step
                self._current_suggestion = suggestion
            interaction_state.step = 5
        
        # Step 6: Ask about committing to framework
        if interaction_state.step == 5:
            if interaction_state.commit_choice is None:
                interaction_state.commit_choice = input(
                    "💾 Add this argument to the debate framework? (y/n): "
                )
            
            if interaction_state.commit_choice.lower() == 'y':
                self._commit_argument(interaction_state.final_argument, self._current_suggestion, user_team)
            
            interaction_state.step = 6
        
        return interaction_state.final_argument or "No argument provided", interaction_state
    
    def _build_argument_prompt(self, guidance) -> str:
        """Build the argument input prompt."""
        prompt_parts = [
            "📝 CREATE YOUR ARGUMENT:",
            "Write your argument naturally - AI will detect structure automatically!"
        ]
        
        if guidance:
            prompt_parts.append("(Consider the strategic guidance above)")
        
        prompt_parts.append("💡 Type 'help' if you need AI assistance: ")
        
        return "\n".join(prompt_parts)
    
    def _show_guidance(self, guidance):
        """Display strategic guidance to user."""
        print("\n" + "="*60)
        print("🎯 STRATEGIC GUIDANCE")
        print("="*60)
        
        print(f"\n📊 Priority Level: {guidance.priority_level.upper()}")
        
        if guidance.recommended_domains:
            print(f"\n🎯 Recommended Domains:")
            for domain in guidance.recommended_domains:
                print(f"   • {domain.name}: {domain.description} (salience: {domain.salience})")
        
        if guidance.recommended_goals:
            print(f"\n🎯 Recommended Goals:")
            for goal in guidance.recommended_goals:
                print(f"   • {goal.name}: {goal.description}")
        
        print(f"\n💡 Strategic Explanation:")
        print(guidance.strategic_explanation)
        
        if guidance.examples:
            print(f"\n📝 Argument Examples:")
            for i, example in enumerate(guidance.examples, 1):
                print(f"   {i}. {example}")
        
        print(f"\n📈 Current Situation:")
        print(guidance.current_situation_analysis)
        
        print(f"\n🎭 Opponent Analysis:")
        print(guidance.opponent_analysis)
        
        print("="*60)
    
    def _generate_and_show_llm_draft(self, guidance, team_name: str, topic: str) -> dict:
        """Generate and display LLM argument draft."""
        try:
            strategy = self.guidance_service.generate_argument_draft(guidance, team_name, topic)
            
            print("\n" + "="*60)
            print("🤖 AI-GENERATED ARGUMENT DRAFT")
            print("="*60)
            
            print(f"\n📝 Draft Argument:")
            print(f'"{strategy["argument_text"]}"')
            
            print(f"\n🧠 AI's Reasoning:")
            print(strategy["reasoning"])
            
            print(f"\n🎯 Strategic Rationale:")
            print(strategy["strategic_rationale"])
            
            targets_domains = strategy["targets_domains"]
            if targets_domains:
                print(f"\n🎯 Targets Domains: {', '.join(targets_domains)}")
            
            supports_goals = strategy["supports_goals"]
            if supports_goals:
                print(f"\n🎯 Supports Goals: {', '.join(supports_goals)}")
            
            print("="*60)
            
            return {
                "strategy": strategy,
                "success": True
            }
            
        except Exception as e:
            print(f"\n❌ Error generating argument draft: {e}")
            return {
                "error": str(e),
                "success": False
            }
    
    def _process_llm_choice(self, choice: str, draft_info: dict) -> Optional[str]:
        """Process user's choice regarding LLM draft."""
        if not draft_info.get("success"):
            return input("Please enter your argument manually: ")
        
        strategy = draft_info["strategy"]
        
        if choice == "1":
            return strategy["argument_text"]
        elif choice == "2":
            print(f"\nCurrent draft: {strategy["argument_text"]}")
            modified = input("Enter your modified version: ")
            return modified if modified.strip() else strategy["argument_text"]
        else:  # choice == "3" or anything else
            return input("Enter your own argument: ")
    
    def _show_evaluation(self, argument_text: str, suggestion):
        """Show argument evaluation results."""
        print(f"\n📊 ARGUMENT ANALYSIS:")
        print(f"Argument: \"{argument_text}\"")
        print(f"AI detected: {', '.join(suggestion.target_domains)} domains, {', '.join(suggestion.target_goals)} goals")
        print(f"Assessment: {suggestion.reasoning}")
        print(f"Expected impact: {suggestion.expected_impact}")
    
    def _commit_argument(self, argument_text: str, suggestion, team_name: str):
        """Commit argument to the debate framework."""
        af_service = self.guidance_service.service
        candidate = CandidateArgument(
            name=f"user_arg_{len(af_service.arguments)}",
            text=argument_text,
            team=team_name,
            domains=set(suggestion.target_domains),
            goals={goal: suggestion.target_domains for goal in suggestion.target_goals},
            attacks=set()
        )
        
        candidate_id = f"user_candidate_{len(af_service.candidate_arguments)}"
        af_service.set_candidate_argument(candidate_id, candidate)
        af_service.apply_candidate_argument(candidate_id)
        print(f"✅ Argument added as '{candidate.name}' to the framework")



# def quick_guidance_node(state: DebateState) -> DebateState:
#     """Quick guidance without argument creation."""
#     team_name = state["user"]["team_name"]
#     all_teams = [team["team_name"] for team in state["teams"]]
    
#     guidance_service = UserGuidanceService(state["af"])
#     guidance = guidance_service.get_strategic_guidance(team_name, all_teams)
    
#     print("\n🎯 QUICK STRATEGIC TIPS")
#     print("="*40)
    
#     tips = guidance_service.get_quick_tips(team_name)
#     for tip in tips:
#         print(f"   {tip}")
    
#     print(f"\nPriority: {guidance.priority_level}")
#     if guidance.recommended_domains:
#         domain_names = [d.name for d in guidance.recommended_domains[:2]]
#         print(f"Focus domains: {', '.join(domain_names)}")
    
#     return state


# # Helper function for simple argument creation without full guidance
# def simple_argument_node(state: DebateState) -> DebateState:
#     """Simple argument creation with just parsing, no guidance."""
#     team_name = state["user"]["team_name"]
#     topic = state["topic"]
    
#     # Single interrupt for argument
#     argument_text = interrupt("📝 Enter your argument (AI will auto-parse structure)")
    
#     if argument_text:
#         guidance_service = UserGuidanceService(state["af"])
#         suggestion = guidance_service.parse_and_evaluate_argument(argument_text, team_name, topic)
        
#         print(f"\n🤖 AI detected: {', '.join(suggestion.target_domains)} domains, {', '.join(suggestion.target_goals)} goals")
#         print(f"📊 Expected impact: {suggestion.expected_impact}")
        
#         # Ask to commit
#         commit = interrupt("💾 Add to framework? (y/n)")
#         if commit.lower() == 'y':
#             af_service = guidance_service.service
#             candidate = CandidateArgument(
#                 name=f"user_arg_{len(af_service.arguments)}",
#                 text=argument_text,
#                 team=team_name,
#                 domains=set(suggestion.target_domains),
#                 goals={goal: suggestion.target_domains for goal in suggestion.target_goals},
#                 attacks=set()
#             )
            
#             candidate_id = f"user_simple_{len(af_service.candidate_arguments)}"
#             af_service.set_candidate_argument(candidate_id, candidate)
#             af_service.apply_candidate_argument(candidate_id)
#             print(f"✅ Argument added to framework")
    
#     return state
