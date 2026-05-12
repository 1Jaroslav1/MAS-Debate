from typing import Any, Dict
from src.debate_extended.state import DebateState


class DebateResultsService:
    def build_results(self, final_state: DebateState) -> Dict[str, Any]:
        af = final_state["af"]
        godsaf_results = af.solve()

        metrics_summary = None
        if "metrics_aggregator" in final_state:
            metrics_aggregator = final_state["metrics_aggregator"]
            metrics_summary = metrics_aggregator.get_full_summary()

        # Extract architecture information for each team
        team_architectures = self._extract_team_architectures(final_state)

        return {
            "config_id": final_state.get("config_id"),
            "topic": final_state["topic"],
            "max_rounds": final_state["max_rounds"],
            "rounds_completed": final_state["round"],
            "teams": [team["team_name"] for team in final_state["teams"]],
            "team_architectures": team_architectures,
            "audience_initial_votes": final_state.get("audience_initial_votes", []),
            "audience_final_votes": final_state.get("audience_final_votes", []),
            # Initial voting metrics (with initial_ prefix)
            "initial_vote_counts": final_state.get("initial_vote_counts"),
            "initial_winning_team": final_state.get("initial_winning_team"),
            "initial_margin_of_victory": final_state.get("initial_margin_of_victory"),
            # Final voting metrics (with final_ prefix)
            "final_vote_counts": final_state.get("final_vote_counts"),
            "final_winning_team": final_state.get("final_winning_team"),
            "final_margin_of_victory": final_state.get("final_margin_of_victory"),
            "final_vote_changes": final_state.get("final_vote_changes"),
            # Deprecated fields (backwards compatibility - prefer final_ prefixed versions)
            "winning_team": final_state.get("final_winning_team") or final_state.get("winning_team"),
            "vote_counts": final_state.get("final_vote_counts") or final_state.get("vote_counts"),
            "margin_of_victory": final_state.get("final_margin_of_victory") or final_state.get("margin_of_victory"),
            "domain_goal_pairs": final_state.get("domain_goal_pairs", []),
            "arguments": final_state.get("argument_log", []),
            "tgs_snapshots": final_state.get("tgs_snapshots", []),
            "final_tgs": {
                team: {f"{g}-{d}": v for (g, d), v in pairs.items()}
                for team, pairs in godsaf_results.get("tgs", {}).items()
            },
            "execution_metrics": metrics_summary,
        }

    def _extract_team_architectures(self, final_state: DebateState) -> Dict[str, Any]:
        """Extract architecture information for each team."""
        team_architectures = {}

        for team in final_state.get("teams", []):
            team_name = team["team_name"]
            team_focus = team.get("team_focus")

            # Extract team-level architecture info
            architecture_info = {
                "architecture": team.get("architecture", "godsaf"),
                "team_type": team_focus.team_type if team_focus else None,
            }

            # Add ToT config if present
            if "tot_config" in team and team["tot_config"]:
                tot_cfg = team["tot_config"]
                architecture_info["tot_config"] = {
                    "num_analysis_branches": getattr(tot_cfg, "num_analysis_branches", None),
                    "num_argument_variations": getattr(tot_cfg, "num_argument_variations", None),
                    "pruning_strategy": getattr(tot_cfg, "pruning_strategy", None),
                    "analysis_pruning_k": getattr(tot_cfg, "analysis_pruning_k", None),
                    "argument_pruning_k": getattr(tot_cfg, "argument_pruning_k", None),
                    "search_algorithm": getattr(tot_cfg, "search_algorithm", None),
                    "enable_fast_scoring": getattr(tot_cfg, "enable_fast_scoring", None),
                    "diversity_weight": getattr(tot_cfg, "diversity_weight", None),
                }

            # Extract member-level architecture features
            members_config = []
            for member in team.get("team_members", []):
                member_info = {
                    "name": member["name"],
                }

                # Extract knowledge node config if present
                if "knowledge_retrival_context" in member:
                    knowledge_ctx = member["knowledge_retrival_context"]
                    member_info["knowledge_active"] = getattr(knowledge_ctx, "knowledge_active", False)
                    member_info["knowledge_use_rag"] = getattr(knowledge_ctx, "knowledge_use_rag", False)
                    member_info["knowledge_use_web_search"] = getattr(knowledge_ctx, "knowledge_use_web_search", False)

                # Extract evaluation config if present
                eval_config = team.get("evaluation_config")
                if eval_config:
                    member_info["evaluation_active"] = getattr(eval_config, "active", False)

                # Extract other member settings
                member_profile = member.get("member_profile")
                if member_profile:
                    member_info["max_iterations"] = getattr(member_profile, "max_iterations", 3)
                    member_info["use_personalization"] = getattr(member_profile, "use_personalization", True)
                    member_info["use_context_analysis"] = getattr(member_profile, "use_context_analysis", True)

                members_config.append(member_info)

            architecture_info["members"] = members_config
            team_architectures[team_name] = architecture_info

        return team_architectures

