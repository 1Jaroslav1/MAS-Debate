from typing import Dict, List, Optional
from langchain_core.prompts import PromptTemplate
from src.reasoning.godsaf.godsaf_service import GoDsAFService, Domain, Goal, CandidateArgument
from src.reasoning.miner.argument_miner import argument_parser_node
from src.team_extended.common.analyser.godsaf_analyser import GoDsAFAnalysisNode
from src.team_extended.common.team_member import StrategyRecommendation
from src.team_extended.user_guidance.user_types import ArgumentStrategy, ArgumentSuggestion, UserGuidance


class UserGuidanceService:
    """
    Service that provides strategic guidance to users for argument creation.
    Handles multiple opponent teams and LLM integration for argument drafts.
    """

    def __init__(self, godsaf_service: GoDsAFService, llm=None):
        self.service = godsaf_service
        self.analyzer = GoDsAFAnalysisNode(godsaf_service)
        self.parser = argument_parser_node()
        self.llm = llm
        self.argument_generation_prompt = PromptTemplate(
            input_variables=["strategic_context", "topic", "team_name", "opponent_teams", "guidance_summary"],
            template="""
            You are an expert debate strategist helping a user create a strategic argument.
            Based on the following strategic analysis, create an argument that addresses the user's highest priority unmet goal needs.

            STRATEGIC CONTEXT:
            {strategic_context}

            CURRENT DEBATE TOPIC: {topic}

            USER'S TEAM: {team_name}

            OPPONENT TEAMS: {opponent_teams}

            GUIDANCE SUMMARY:
            {guidance_summary}

            CREATE AN ARGUMENT that:
            1. Targets the recommended domains and goals
            2. Addresses the strategic gaps identified
            3. Is persuasive and well-reasoned
            4. Takes advantage of opponent weaknesses

            Provide your response in the following format:
            - argument_text: The complete argument text
            - reasoning: Why this argument is strategically optimal
            - strategic_rationale: How it addresses the identified gaps
            - targets_domains: List of domains this argument targets
            - supports_goals: List of goals this argument supports
        """
        )

    def get_strategic_guidance(self, team_name: str) -> UserGuidance:
        """
        Provide comprehensive strategic guidance considering all opponent teams.
        
        Args:
            team_name: Name of the user's team
            all_teams: List of all team names in the debate
            
        Returns:
            UserGuidance with recommendations and multi-opponent analysis
        """
        # Get strategy recommendation from analyzer
        strategy_rec = self.analyzer.analyze_team_strategy(team_name)
        
        all_teams = self.service.list_team_names()

        opponent_teams = [team for team in all_teams if team != team_name]
        
        # Analyze current debate state with multiple opponents
        situation_analysis = self._analyze_current_situation(team_name, opponent_teams)
        
        # Generate strategic explanation
        explanation = self._generate_strategic_explanation(strategy_rec, situation_analysis)
        
        # Create examples
        examples = self._generate_argument_examples(strategy_rec)
        
        # Determine priority level
        priority = self._determine_priority_level(strategy_rec)
        
        # Analyze all opponents
        opponent_analysis = self._analyze_all_opponents(team_name, opponent_teams)
        
        return UserGuidance(
            recommended_domains=strategy_rec.recommended_domains,
            recommended_goals=strategy_rec.recommended_goals,
            primary_ugns=strategy_rec.primary_ugns,
            secondary_ugns=strategy_rec.secondary_ugns,
            strategic_explanation=explanation,
            current_situation_analysis=situation_analysis,
            examples=examples,
            priority_level=priority,
            opponent_analysis=opponent_analysis
        )

    def parse_and_evaluate_argument(self,
                                  argument_text: str,
                                  team_name: str,
                                  topic: str = "General Debate",
                                  attacks: Optional[List[str]] = None) -> ArgumentSuggestion:
        """Parse argument text and evaluate strategic alignment using the argument parser."""
        # Use centralized parser utility
        from src.reasoning.miner.parser_utils import parse_argument

        domains = self.service.list_domains()
        goals = self.service.list_goals()
        existing_arguments = list(self.service.get_argument_names())

        parsed_dict = parse_argument(
            topic=topic,
            argument=argument_text,
            domains=domains,
            goals=goals,
            existing_arguments=existing_arguments,
            domain_lookup=lambda d: self.service.get_domain(d)
        )

        # Extract parsed structure
        target_domains = parsed_dict.get("domains", [])
        target_goals_dict = parsed_dict.get("goals", {})
        target_goals = list(target_goals_dict.keys())
        
        # Create candidate argument for evaluation
        candidate = CandidateArgument(
            name=parsed_dict.get("name", "user_argument"),
            text=argument_text,
            team=team_name,
            domains=set(target_domains),
            goals=target_goals_dict,
            attacks=set(attacks) if attacks else set()
        )

        # Evaluate the candidate
        evaluation = self.service.evaluate_new_argument(candidate)

        # Get strategic analysis
        strategy_rec = self.analyzer.analyze_team_strategy(team_name)

        # Generate reasoning
        reasoning = self._evaluate_argument_alignment(
            target_domains, target_goals, strategy_rec, evaluation, parsed_dict
        )
        
        # Suggest potential attacks
        potential_attacks = self._suggest_potential_attacks(team_name, target_domains)
        
        # Calculate expected impact
        expected_impact = self._calculate_expected_impact(evaluation, strategy_rec)
        
        return ArgumentSuggestion(
            target_domains=target_domains,
            target_goals=target_goals,
            reasoning=reasoning,
            potential_attacks=potential_attacks,
            expected_impact=expected_impact
        )

    def generate_argument_draft(self, guidance: UserGuidance, team_name: str, topic: str) -> ArgumentStrategy:
        """
        Generate an argument draft using LLM based on strategic guidance.
        
        Args:
            guidance: Strategic guidance from GoDsAF analysis
            team_name: User's team name
            topic: Debate topic
            
        Returns:
            ArgumentStrategy with LLM-generated argument and reasoning
        """
        if not self.llm:
            raise ValueError("LLM not configured for argument generation")
        
        # Prepare context for LLM
        strategic_context = self._format_strategic_context(guidance)
        opponent_teams = guidance.opponent_analysis
        guidance_summary = self._format_guidance_summary(guidance)
        
        strategy_input = {
            "strategic_context": strategic_context,
            "topic": topic,
            "team_name": team_name,
            "opponent_teams": opponent_teams,
            "guidance_summary": guidance_summary
        }
        
        # Generate argument using LLM
        chain = self.argument_generation_prompt | self.llm.with_structured_output(ArgumentStrategy)
        strategy = chain.invoke(strategy_input)
        
        return strategy

    def _analyze_all_opponents(self, team_name: str, opponent_teams: List[str]) -> str:
        """Analyze all opponent teams for strategic insights."""
        if not opponent_teams:
            return "No opponent teams identified."
        
        analysis_parts = []
        analysis_parts.append(f"Multi-Team Opponent Analysis ({len(opponent_teams)} opponents):")
        
        for i, opponent in enumerate(opponent_teams, 1):
            opponent_ugns = self.service.get_ugn_for_team(opponent)
            if opponent_ugns:
                top_ugn = opponent_ugns[0]
                analysis_parts.append(f"{i}. {opponent}: Weakness in {top_ugn.goal.name}/{top_ugn.domain.name} (UGN: {top_ugn.value})")
            else:
                analysis_parts.append(f"{i}. {opponent}: Strong coverage, no major gaps identified")
        
        return "\n".join(analysis_parts)

    def _analyze_current_situation(self, team_name: str, opponent_teams: List[str]) -> str:
        """Analyze the current debate situation with multiple opponents."""
        analysis_parts = []
        
        # Get UGN analysis for user's team
        ugn_analysis = self.analyzer.get_detailed_ugn_analysis(team_name, top_n=3)
        analysis_parts.append("Your Team Position:")
        analysis_parts.append(ugn_analysis)
        
        # Add multi-opponent analysis
        if opponent_teams:
            analysis_parts.append(f"\nCompeting Against {len(opponent_teams)} Teams:")
            for opponent in opponent_teams:
                comparison = self.analyzer.compare_team_strategies(team_name, opponent)
                analysis_parts.append(f"\nvs {opponent}:")
                # Extract just the strategic overlaps section
                lines = comparison.split('\n')
                for line in lines:
                    if 'Strategic Overlaps:' in line or 'Competing' in line or '⚠️' in line:
                        analysis_parts.append(f"  {line}")
        
        return "\n".join(analysis_parts)

    def _format_strategic_context(self, guidance: UserGuidance) -> str:
        """Format strategic context for LLM input."""
        context_parts = []
        
        context_parts.append(f"Priority Level: {guidance.priority_level.upper()}")
        
        if guidance.recommended_domains:
            domain_info = []
            for domain in guidance.recommended_domains:
                domain_info.append(f"{domain.name} (salience: {domain.salience})")
            context_parts.append(f"Recommended Domains: {', '.join(domain_info)}")
        
        if guidance.recommended_goals:
            goal_info = [goal.name for goal in guidance.recommended_goals]
            context_parts.append(f"Recommended Goals: {', '.join(goal_info)}")
        
        context_parts.append(f"Current Situation: {guidance.current_situation_analysis}")
        
        return "\n".join(context_parts)

    def _format_guidance_summary(self, guidance: UserGuidance) -> str:
        """Format guidance summary for LLM."""
        summary_parts = []
        
        summary_parts.append(guidance.strategic_explanation)
        
        if guidance.examples:
            summary_parts.append("\nExample Argument Types:")
            for example in guidance.examples:
                summary_parts.append(f"• {example}")
        
        summary_parts.append(f"\nOpponent Analysis:")
        summary_parts.append(guidance.opponent_analysis)
        
        return "\n".join(summary_parts)

    def _generate_strategic_explanation(self, 
                                      strategy_rec: StrategyRecommendation,
                                      situation_analysis: str) -> str:
        """Generate explanation for why these domains and goals are recommended."""
        explanation_parts = []
        
        explanation_parts.append("🎯 **Strategic Recommendations Explained:**")
        
        if strategy_rec.recommended_domains:
            explanation_parts.append("\n**Focus Domains:**")
            for domain in strategy_rec.recommended_domains:
                impact_level = "High" if domain.salience > 50 else "Medium" if domain.salience > 25 else "Low"
                explanation_parts.append(f"• {domain.name}: {impact_level} impact potential (salience: {domain.salience})")
        
        if strategy_rec.recommended_goals:
            explanation_parts.append("\n**Target Goals:**")
            for goal in strategy_rec.recommended_goals:
                explanation_parts.append(f"• {goal.name}: {goal.description}")
        
        # Add strategic reasoning based on UGN analysis
        if strategy_rec.primary_ugns:
            explanation_parts.append(f"\n**Why These Recommendations:**")
            if len(strategy_rec.primary_ugns) == 1:
                ugn = strategy_rec.primary_ugns[0]
                explanation_parts.append(f"Your largest strategic gap is in {ugn.goal.name}/{ugn.domain.name} (deficit: {ugn.value})")
                explanation_parts.append("Targeting this gap will provide maximum competitive advantage.")
            else:
                explanation_parts.append("Multiple high-priority gaps detected (90% rule applied)")
                explanation_parts.append("Arguments addressing either area will significantly strengthen your position.")
        
        return "\n".join(explanation_parts)

    def _generate_argument_examples(self, strategy_rec: StrategyRecommendation) -> List[str]:
        """Generate example arguments based on recommendations."""
        examples = []
        
        if not strategy_rec.recommended_domains or not strategy_rec.recommended_goals:
            return ["Focus on addressing your team's highest unmet goal needs."]
        
        # Generate examples combining domains and goals
        for goal in strategy_rec.recommended_goals[:2]:
            for domain in strategy_rec.recommended_domains[:2]:
                example = f"Argument advancing {goal.name} through {domain.name} considerations"
                examples.append(example)
        
        return examples[:3]

    def _determine_priority_level(self, strategy_rec: StrategyRecommendation) -> str:
        """Determine the priority level of the recommendations."""
        if not strategy_rec.primary_ugns:
            return "low"
        
        if len(strategy_rec.primary_ugns) == 2:
            return "high"
        
        primary_ugn_value = strategy_rec.primary_ugns[0].value
        if primary_ugn_value > 50:
            return "high"
        elif primary_ugn_value > 20:
            return "medium"
        else:
            return "low"

    def _evaluate_argument_alignment(self,
                                   target_domains: List[str],
                                   target_goals: List[str],
                                   strategy_rec: StrategyRecommendation,
                                   evaluation: Dict,
                                   parsed_info=None) -> str:
        """Evaluate how well the argument aligns with strategy."""
        reasoning_parts = []
        
        if parsed_info:
            reasoning_parts.append(f"🤖 **AI Parsed as**: '{parsed_info.name}'")
        
        # Check alignment
        recommended_domain_names = [d.name for d in strategy_rec.recommended_domains]
        recommended_goal_names = [g.name for g in strategy_rec.recommended_goals]
        
        domain_alignment = set(target_domains).intersection(set(recommended_domain_names))
        goal_alignment = set(target_goals).intersection(set(recommended_goal_names))
        
        if domain_alignment:
            reasoning_parts.append(f"✅ **Domain Alignment**: Targets recommended {', '.join(domain_alignment)}")
        else:
            reasoning_parts.append(f"⚠️ **Domain Gap**: Consider {', '.join(recommended_domain_names[:2])}")
        
        if goal_alignment:
            reasoning_parts.append(f"✅ **Goal Alignment**: Supports {', '.join(goal_alignment)}")
        else:
            reasoning_parts.append(f"⚠️ **Goal Gap**: Priority goals are {', '.join(recommended_goal_names[:2])}")
        
        # APS evaluation
        estimated_aps = evaluation.get('estimated_aps', 0)
        if estimated_aps > 100:
            reasoning_parts.append(f"💪 **High Impact**: Estimated APS {estimated_aps}")
        elif estimated_aps > 50:
            reasoning_parts.append(f"👍 **Moderate Impact**: APS {estimated_aps}")
        else:
            reasoning_parts.append(f"🤔 **Limited Impact**: APS {estimated_aps}")
        
        return "\n".join(reasoning_parts)

    def _suggest_potential_attacks(self, team_name: str, target_domains: List[str]) -> List[str]:
        """Suggest potential attacks the argument could make."""
        attacks = []
        
        for arg_name, arg in self.service.arguments.items():
            if arg.team != team_name:
                if set(arg.domains).intersection(set(target_domains)):
                    attacks.append(f"Attack {arg_name} (domain overlap)")
        
        return attacks[:3]

    def _calculate_expected_impact(self, evaluation: Dict, strategy_rec: StrategyRecommendation) -> str:
        """Calculate and describe expected impact of the argument."""
        estimated_aps = evaluation.get('estimated_aps', 0)
        defeats = evaluation.get('defeats', [])
        
        impact_parts = []
        
        if estimated_aps > 100:
            impact_parts.append("High strategic impact")
        elif estimated_aps > 50:
            impact_parts.append("Moderate impact")
        else:
            impact_parts.append("Limited impact")
        
        if defeats:
            impact_parts.append(f"Defeats {len(defeats)} arguments")
        
        if strategy_rec.primary_ugns:
            primary_gap = strategy_rec.primary_ugns[0].value
            if estimated_aps >= primary_gap * 0.5:
                impact_parts.append("Significantly reduces strategic gap")
        
        return " | ".join(impact_parts) if impact_parts else "Minimal impact"

    def get_quick_tips(self, team_name: str) -> List[str]:
        """Get quick tips for argument creation."""
        strategy_rec = self.analyzer.analyze_team_strategy(team_name)
        
        tips = []
        
        if strategy_rec.primary_ugns:
            primary_ugn = strategy_rec.primary_ugns[0]
            tips.append(f"🎯 Priority: Target {primary_ugn.goal.name} in {primary_ugn.domain.name}")
        
        if len(strategy_rec.primary_ugns) == 2:
            tips.append("⚖️ Dual focus recommended (90% rule)")
        
        if strategy_rec.recommended_domains:
            high_salience_domains = [d for d in strategy_rec.recommended_domains if d.salience > 50]
            if high_salience_domains:
                tips.append(f"💡 High impact domain: {high_salience_domains[0].name}")
        
        tips.append("🤖 AI will auto-parse your argument structure")
        tips.append("🆘 Ask for LLM help if you need argument draft")
        
        return tips[:5]
