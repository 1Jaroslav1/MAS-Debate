from dataclasses import dataclass
from typing import List, Tuple

from src.reasoning.godsaf.godsaf_service import GoDsAFService, UGNEntry

@dataclass
class GoDsAFAnalysisNodeResult:
    team: str
    primary_ugns: List[UGNEntry]
    secondary_ugns: List[UGNEntry]
    analysis_summary: str

class GoDsAFAnalysisNode:
    """
    Analysis node for GoDsAF that recommends strategy based on UGN analysis.

    The node analyzes a team's Unmet Goal Needs and recommends up to 2 domains
    and 2 goals for new argument development based on the 90% rule:
    - If UGN2/UGN1 > 90% (where UGN1 >= UGN2), include both
    - Otherwise focus on the top UGN only
    """

    def __init__(self, godsaf_service: GoDsAFService):
        self.service = godsaf_service

    def analyze_team_strategy(self, team_name: str) -> GoDsAFAnalysisNodeResult:
        ugn_entries = self.service.get_ugn_for_team(team_name)

        if not ugn_entries:
            return GoDsAFAnalysisNodeResult(
                team=team_name,
                primary_ugns=[],
                secondary_ugns=[],
                analysis_summary=f"No unmet goal needs found for team {team_name}. Team has sufficient coverage.",
            )

        primary_ugns, secondary_ugns = self._apply_acceptence_rule(ugn_entries)

        analysis_summary = self._generate_analysis_summary(
            team_name,
            primary_ugns,
            secondary_ugns,
        )

        return GoDsAFAnalysisNodeResult(
            team=team_name,
            primary_ugns=primary_ugns,
            secondary_ugns=secondary_ugns,
            analysis_summary=analysis_summary,
        )

    def _apply_acceptence_rule(self, ugn_entries: List[UGNEntry], acceptence_coef: float = 0.9) -> Tuple[List[UGNEntry], List[UGNEntry]]:
        if not ugn_entries:
            return [], []

        if len(ugn_entries) == 1:
            return [ugn_entries[0]], []

        # Get top two UGNs
        ugn1 = ugn_entries[0]
        ugn2 = ugn_entries[1]

        # Apply acceptence rule: if ugn2/ugn1 > acceptence_coef, include both
        if ugn1.value > 0 and (ugn2.value / ugn1.value) > acceptence_coef:
            # Include both as primary concerns
            primary_ugns = [ugn1, ugn2]
            secondary_ugns = []
        else:
            # Focus only on the top UGN
            primary_ugns = [ugn1]
            secondary_ugns = [ugn2]

        return primary_ugns, secondary_ugns



    def _generate_analysis_summary(
        self,
        team_name: str,
        primary_ugns: List[UGNEntry],
        secondary_ugns: List[UGNEntry],
    ) -> str:
        """Generate a human-readable analysis summary."""

        summary_parts = []
        summary_parts.append(f"Strategy Analysis for Team {team_name}")
        summary_parts.append("=" * 40)

        if primary_ugns:
            if len(primary_ugns) == 1:
                ugn = primary_ugns[0]
                summary_parts.append(
                    f"Primary Focus: {ugn.goal} in {ugn.domain} (UGN: {ugn.value})"
                )
            else:
                ugn1, ugn2 = primary_ugns[0], primary_ugns[1]
                ratio = ugn2.value / ugn1.value if ugn1.value > 0 else 0
                summary_parts.append(
                    f"Dual Priority Strategy (90% rule applied - ratio: {ratio:.1%}):"
                )
                summary_parts.append(
                    f"  • {ugn1.goal} in {ugn1.domain} (UGN: {ugn1.value})"
                )
                summary_parts.append(
                    f"  • {ugn2.goal} in {ugn2.domain} (UGN: {ugn2.value})"
                )

        if secondary_ugns:
            summary_parts.append(
                f"Secondary Concern: {secondary_ugns[0].goal} in {secondary_ugns[0].domain} (UGN: {secondary_ugns[0].value})"
            )

        summary_parts.append("")
        summary_parts.append("Recommended New Argument Strategy:")
        
        # Extract unique domains and goals from UGNs
        all_ugns = primary_ugns + secondary_ugns
        unique_domains = list(set(ugn.domain.name for ugn in all_ugns))
        unique_goals = list(set(ugn.goal.name for ugn in all_ugns))
        
        summary_parts.append(f"  Domains: {', '.join(sorted(unique_domains))}")
        summary_parts.append(f"  Goals: {', '.join(sorted(unique_goals))}")
        
        # Show domain-goal connections
        summary_parts.append("  Domain-Goal Connections:")
        for ugn in all_ugns:
            summary_parts.append(f"    • {ugn.domain.name} → {ugn.goal.name} (UGN: {ugn.value})")

        # Add strategic advice
        summary_parts.append("")
        summary_parts.append("Strategic Advice:")
        if len(primary_ugns) == 2:
            summary_parts.append(
                "  • Consider arguments that address both priority areas"
            )
            summary_parts.append(
                "  • High correlation between top unmet needs suggests systematic gap"
            )
        else:
            summary_parts.append("  • Focus arguments on the primary unmet need")
            summary_parts.append(
                "  • Consider how addressing this gap affects overall team position"
            )

        return "\n".join(summary_parts)

    def compare_team_strategies(self, team1: str, team2: str) -> str:
        """Compare strategy recommendations between two teams."""

        rec1 = self.analyze_team_strategy(team1)
        rec2 = self.analyze_team_strategy(team2)
        domain_names1 = {domain.name for domain in rec1.recommended_domains}
        domain_names2 = {domain.name for domain in rec2.recommended_domains}
        goal_names1 = {goal.name for goal in rec1.recommended_goals}
        goal_names2 = {goal.name for goal in rec2.recommended_goals}

        comparison = []
        comparison.append(f"Strategy Comparison: {team1} vs {team2}")
        comparison.append("=" * 50)

        comparison.append(f"\n{team1} Strategy:")
        comparison.append(
            f"  Domains: {', '.join(domain_names1) if domain_names1 else 'None'}"
        )
        comparison.append(
            f"  Goals: {', '.join(goal_names1) if goal_names1 else 'None'}"
        )

        comparison.append(f"\n{team2} Strategy:")
        comparison.append(
            f"  Domains: {', '.join(domain_names2) if domain_names2 else 'None'}"
        )
        comparison.append(
            f"  Goals: {', '.join(goal_names2) if goal_names2 else 'None'}"
        )
        
        domain_overlap = domain_names1.intersection(domain_names2)
        goal_overlap = goal_names1.intersection(goal_names2)

        comparison.append(f"\nStrategic Overlaps:")
        comparison.append(
            f"  Competing Domains: {', '.join(domain_overlap) if domain_overlap else 'None'}"
        )
        comparison.append(
            f"  Competing Goals: {', '.join(goal_overlap) if goal_overlap else 'None'}"
        )

        if domain_overlap or goal_overlap:
            comparison.append(
                f"\n⚠️  Teams have overlapping strategic priorities - expect increased competition"
            )

        return "\n".join(comparison)

    def get_detailed_ugn_analysis(self, team_name: str, top_n: int = 5) -> str:
        """Get detailed UGN analysis for a team."""

        ugn_entries = self.service.get_ugn_for_team(team_name)

        if not ugn_entries:
            return f"No unmet goal needs found for team {team_name}"

        analysis = []
        analysis.append(f"Detailed UGN Analysis for Team {team_name}")
        analysis.append("=" * 50)

        for i, ugn in enumerate(ugn_entries[:top_n], 1):
            analysis.append(f"{i}. {ugn.goal} in {ugn.domain}: {ugn.value}")

            # Add percentage if this is not the first entry
            if i > 1:
                ratio = (
                    ugn.value / ugn_entries[0].value if ugn_entries[0].value > 0 else 0
                )
                analysis.append(f"   ({ratio:.1%} of top priority)")

        # Add 90% rule analysis
        if len(ugn_entries) >= 2:
            ratio = (
                ugn_entries[1].value / ugn_entries[0].value
                if ugn_entries[0].value > 0
                else 0
            )
            analysis.append(f"\n90% Rule Analysis:")
            analysis.append(f"  Second priority ratio: {ratio:.1%}")
            if ratio > 0.9:
                analysis.append(f"  ✓ Dual priority strategy recommended")
            else:
                analysis.append(f"  → Single priority strategy recommended")

        return "\n".join(analysis)
