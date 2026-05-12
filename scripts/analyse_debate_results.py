import json
import sys
import io
from pathlib import Path
from typing import Dict, List, Any
from collections import defaultdict, Counter
from dataclasses import dataclass
import statistics

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')


@dataclass
class VoteChange:
    name: str
    initial: str
    final: str
    changed: bool
    direction: str


@dataclass
class DebateAnalysis:
    config_id: str
    topic: str
    max_rounds: int

    initial_agree: int
    initial_disagree: int
    final_agree: int
    final_disagree: int

    vote_delta_agree: int
    vote_delta_disagree: int
    swing_voters: List[VoteChange]

    winner: str
    win_margin: int
    win_percentage: float

    teams: List[Dict]
    arguments: List[Dict]

    iteration_stats: Dict[str, Any]
    evaluation_stats: Dict[str, Any]
    strategic_alignment_stats: Dict[str, Any]


class DebateResultsAnalyser:
    def __init__(self, results_file: str):
        self.results_file = Path(results_file)
        if not self.results_file.exists():
            raise FileNotFoundError(f"Results file not found: {results_file}")

        with open(self.results_file, 'r', encoding='utf-8') as f:
            self.data = json.load(f)

    def analyse(self) -> DebateAnalysis:
        initial_votes = self._parse_votes(self.data.get("audience_initial_votes", []))
        final_votes = self._parse_votes(self.data.get("audience_final_votes", []))

        vote_changes = self._calculate_vote_changes(initial_votes, final_votes)
        swing_voters = [vc for vc in vote_changes if vc.changed]

        initial_agree = sum(1 for v in initial_votes.values() if v == "agree")
        initial_disagree = sum(1 for v in initial_votes.values() if v == "disagree")
        final_agree = sum(1 for v in final_votes.values() if v == "agree")
        final_disagree = sum(1 for v in final_votes.values() if v == "disagree")

        vote_delta_agree = final_agree - initial_agree
        vote_delta_disagree = final_disagree - initial_disagree

        total_votes = final_agree + final_disagree
        if final_agree > final_disagree:
            winner = "Proposition (Agree)"
            win_margin = final_agree - final_disagree
            win_percentage = (final_agree / total_votes * 100) if total_votes > 0 else 0
        else:
            winner = "Opposition (Disagree)"
            win_margin = final_disagree - final_agree
            win_percentage = (final_disagree / total_votes * 100) if total_votes > 0 else 0

        teams = self.data.get("teams", [])
        arguments = self.data.get("argument_log", [])

        iteration_stats = self._analyse_iterations(arguments)
        evaluation_stats = self._analyse_evaluations(arguments)
        strategic_stats = self._analyse_strategic_alignment(arguments)

        return DebateAnalysis(
            config_id=self.data.get("config_id", "unknown"),
            topic=self.data.get("topic", "unknown"),
            max_rounds=self.data.get("max_rounds", 0),
            initial_agree=initial_agree,
            initial_disagree=initial_disagree,
            final_agree=final_agree,
            final_disagree=final_disagree,
            vote_delta_agree=vote_delta_agree,
            vote_delta_disagree=vote_delta_disagree,
            swing_voters=swing_voters,
            winner=winner,
            win_margin=win_margin,
            win_percentage=win_percentage,
            teams=teams,
            arguments=arguments,
            iteration_stats=iteration_stats,
            evaluation_stats=evaluation_stats,
            strategic_alignment_stats=strategic_stats
        )

    def _parse_votes(self, votes: List[Dict]) -> Dict[str, str]:
        return {vote["name"]: vote["decision"] for vote in votes}

    def _calculate_vote_changes(self, initial: Dict, final: Dict) -> List[VoteChange]:
        changes = []
        for name in initial.keys():
            initial_vote = initial.get(name, "unknown")
            final_vote = final.get(name, "unknown")
            changed = initial_vote != final_vote

            if changed:
                if initial_vote == "agree" and final_vote == "disagree":
                    direction = "Agree → Disagree"
                elif initial_vote == "disagree" and final_vote == "agree":
                    direction = "Disagree → Agree"
                else:
                    direction = f"{initial_vote} → {final_vote}"
            else:
                direction = "No change"

            changes.append(VoteChange(
                name=name,
                initial=initial_vote,
                final=final_vote,
                changed=changed,
                direction=direction
            ))

        return changes

    def _analyse_iterations(self, arguments: List[Dict]) -> Dict[str, Any]:
        iteration_counts = []
        total_iterations = 0
        rejected_iterations = 0
        accepted_on_first = 0

        for arg in arguments:
            if "iteration_history" in arg:
                history = arg["iteration_history"]
                iteration_counts.append(len(history))
                total_iterations += len(history)
                rejected_iterations += sum(1 for h in history if not h.get("accepted", False))
                if len(history) == 1 and history[0].get("accepted", False):
                    accepted_on_first += 1

        return {
            "total_arguments": len(arguments),
            "arguments_with_iterations": len(iteration_counts),
            "total_iterations": total_iterations,
            "rejected_iterations": rejected_iterations,
            "accepted_on_first_try": accepted_on_first,
            "avg_iterations_per_argument": statistics.mean(iteration_counts) if iteration_counts else 0,
            "max_iterations": max(iteration_counts) if iteration_counts else 0,
            "min_iterations": min(iteration_counts) if iteration_counts else 0
        }

    def _analyse_evaluations(self, arguments: List[Dict]) -> Dict[str, Any]:
        overall_scores = []
        strategic_scores = []
        ugn_scores = []
        results_counter = Counter()

        for arg in arguments:
            eval_log = arg.get("evaluation_log", {})

            if "overall_score" in eval_log:
                overall_scores.append(eval_log["overall_score"])

            if "final_result" in eval_log:
                results_counter[eval_log["final_result"]] += 1

            if "iteration_history" in arg:
                for iteration in arg["iteration_history"]:
                    eval_results = iteration.get("evaluation_results", {})

                    if "strategic_alignment_score" in eval_results and eval_results["strategic_alignment_score"] is not None:
                        strategic_scores.append(eval_results["strategic_alignment_score"])

                    if "ugn_coverage_score" in eval_results and eval_results["ugn_coverage_score"] is not None:
                        ugn_scores.append(eval_results["ugn_coverage_score"])

        return {
            "total_arguments_evaluated": len(arguments),
            "result_distribution": dict(results_counter),
            "overall_score": {
                "mean": statistics.mean(overall_scores) if overall_scores else 0,
                "median": statistics.median(overall_scores) if overall_scores else 0,
                "min": min(overall_scores) if overall_scores else 0,
                "max": max(overall_scores) if overall_scores else 0,
                "stdev": statistics.stdev(overall_scores) if len(overall_scores) > 1 else 0
            },
            "strategic_alignment_score": {
                "mean": statistics.mean(strategic_scores) if strategic_scores else 0,
                "median": statistics.median(strategic_scores) if strategic_scores else 0,
                "min": min(strategic_scores) if strategic_scores else 0,
                "max": max(strategic_scores) if strategic_scores else 0
            },
            "ugn_coverage_score": {
                "mean": statistics.mean(ugn_scores) if ugn_scores else 0,
                "median": statistics.median(ugn_scores) if ugn_scores else 0,
                "min": min(ugn_scores) if ugn_scores else 0,
                "max": max(ugn_scores) if ugn_scores else 0
            }
        }

    def _analyse_strategic_alignment(self, arguments: List[Dict]) -> Dict[str, Any]:
        primary_ugn_addressed = 0
        secondary_ugn_addressed = 0
        both_ugn_addressed = 0
        neither_ugn_addressed = 0

        domain_goal_pairs = defaultdict(int)

        for arg in arguments:
            if "iteration_history" in arg:
                for iteration in arg["iteration_history"]:
                    eval_results = iteration.get("evaluation_results", {})

                    primary = eval_results.get("addresses_primary_ugn", False)
                    secondary = eval_results.get("addresses_secondary_ugn", False)

                    if primary and secondary:
                        both_ugn_addressed += 1
                    elif primary:
                        primary_ugn_addressed += 1
                    elif secondary:
                        secondary_ugn_addressed += 1
                    else:
                        neither_ugn_addressed += 1

            domains = arg.get("domains", [])
            goals = arg.get("goals", {})

            for goal, goal_domains in goals.items():
                for domain in goal_domains:
                    pair = f"{domain} × {goal}"
                    domain_goal_pairs[pair] += 1

        return {
            "primary_ugn_addressed": primary_ugn_addressed,
            "secondary_ugn_addressed": secondary_ugn_addressed,
            "both_ugn_addressed": both_ugn_addressed,
            "neither_ugn_addressed": neither_ugn_addressed,
            "domain_goal_pairs": dict(domain_goal_pairs),
            "unique_domain_goal_pairs": len(domain_goal_pairs)
        }

    def print_analysis(self, analysis: DebateAnalysis):
        print("\n" + "="*100)
        print("DEBATE RESULTS ANALYSIS")
        print("="*100)

        print(f"\nTopic: {analysis.topic}")
        print(f"Config ID: {analysis.config_id}")
        print(f"Rounds: {analysis.max_rounds}")

        print("\n" + "-"*100)
        print("VOTE ANALYSIS")
        print("-"*100)

        print(f"\nInitial Votes:")
        print(f"  Agree:    {analysis.initial_agree:3d} ({analysis.initial_agree/(analysis.initial_agree+analysis.initial_disagree)*100:.1f}%)")
        print(f"  Disagree: {analysis.initial_disagree:3d} ({analysis.initial_disagree/(analysis.initial_agree+analysis.initial_disagree)*100:.1f}%)")

        print(f"\nFinal Votes:")
        print(f"  Agree:    {analysis.final_agree:3d} ({analysis.final_agree/(analysis.final_agree+analysis.final_disagree)*100:.1f}%)")
        print(f"  Disagree: {analysis.final_disagree:3d} ({analysis.final_disagree/(analysis.final_agree+analysis.final_disagree)*100:.1f}%)")

        print(f"\nVote Delta:")
        delta_sign_agree = "+" if analysis.vote_delta_agree >= 0 else ""
        delta_sign_disagree = "+" if analysis.vote_delta_disagree >= 0 else ""
        print(f"  Agree:    {delta_sign_agree}{analysis.vote_delta_agree:3d}")
        print(f"  Disagree: {delta_sign_disagree}{analysis.vote_delta_disagree:3d}")

        print(f"\n🏆 WINNER: {analysis.winner}")
        print(f"   Margin: {analysis.win_margin} votes")
        print(f"   Win %:  {analysis.win_percentage:.1f}%")

        print(f"\nSwing Voters: {len(analysis.swing_voters)}")
        if analysis.swing_voters:
            agree_to_disagree = [sv for sv in analysis.swing_voters if sv.initial == "agree" and sv.final == "disagree"]
            disagree_to_agree = [sv for sv in analysis.swing_voters if sv.initial == "disagree" and sv.final == "agree"]

            if agree_to_disagree:
                print(f"\n  Agree → Disagree ({len(agree_to_disagree)}):")
                for sv in agree_to_disagree[:5]:
                    print(f"    - {sv.name}")
                if len(agree_to_disagree) > 5:
                    print(f"    ... and {len(agree_to_disagree) - 5} more")

            if disagree_to_agree:
                print(f"\n  Disagree → Agree ({len(disagree_to_agree)}):")
                for sv in disagree_to_agree[:5]:
                    print(f"    - {sv.name}")
                if len(disagree_to_agree) > 5:
                    print(f"    ... and {len(disagree_to_agree) - 5} more")

        print("\n" + "-"*100)
        print("ITERATION ANALYSIS")
        print("-"*100)

        its = analysis.iteration_stats
        print(f"\nTotal Arguments: {its['total_arguments']}")
        print(f"Arguments with Iteration Data: {its['arguments_with_iterations']}")
        print(f"Total Iterations Performed: {its['total_iterations']}")
        print(f"Rejected Iterations: {its['rejected_iterations']}")
        print(f"Accepted on First Try: {its['accepted_on_first_try']}")
        print(f"\nAverage Iterations per Argument: {its['avg_iterations_per_argument']:.2f}")
        print(f"Max Iterations: {its['max_iterations']}")
        print(f"Min Iterations: {its['min_iterations']}")

        print("\n" + "-"*100)
        print("EVALUATION SCORES ANALYSIS")
        print("-"*100)

        evs = analysis.evaluation_stats
        print(f"\nTotal Arguments Evaluated: {evs['total_arguments_evaluated']}")
        print(f"\nResult Distribution:")
        for result, count in evs['result_distribution'].items():
            print(f"  {result.capitalize():10s}: {count:3d}")

        print(f"\nOverall Scores:")
        print(f"  Mean:   {evs['overall_score']['mean']:.1f}/100")
        print(f"  Median: {evs['overall_score']['median']:.1f}/100")
        print(f"  Min:    {evs['overall_score']['min']:.1f}/100")
        print(f"  Max:    {evs['overall_score']['max']:.1f}/100")
        print(f"  StdDev: {evs['overall_score']['stdev']:.1f}")

        print(f"\nStrategic Alignment Scores:")
        print(f"  Mean:   {evs['strategic_alignment_score']['mean']:.1f}/100")
        print(f"  Median: {evs['strategic_alignment_score']['median']:.1f}/100")
        print(f"  Min:    {evs['strategic_alignment_score']['min']:.1f}/100")
        print(f"  Max:    {evs['strategic_alignment_score']['max']:.1f}/100")

        print(f"\nUGN Coverage Scores:")
        print(f"  Mean:   {evs['ugn_coverage_score']['mean']:.1f}/100")
        print(f"  Median: {evs['ugn_coverage_score']['median']:.1f}/100")
        print(f"  Min:    {evs['ugn_coverage_score']['min']:.1f}/100")
        print(f"  Max:    {evs['ugn_coverage_score']['max']:.1f}/100")

        print("\n" + "-"*100)
        print("STRATEGIC ALIGNMENT ANALYSIS")
        print("-"*100)

        sas = analysis.strategic_alignment_stats
        print(f"\nUGN Addressing:")
        print(f"  Primary UGN Only:     {sas['primary_ugn_addressed']}")
        print(f"  Secondary UGN Only:   {sas['secondary_ugn_addressed']}")
        print(f"  Both UGNs:            {sas['both_ugn_addressed']}")
        print(f"  Neither UGN:          {sas['neither_ugn_addressed']}")

        print(f"\nDomain-Goal Pairs Used:")
        print(f"  Unique Pairs: {sas['unique_domain_goal_pairs']}")

        if sas['domain_goal_pairs']:
            print(f"\n  Top 5 Most Used Pairs:")
            sorted_pairs = sorted(sas['domain_goal_pairs'].items(), key=lambda x: x[1], reverse=True)
            for pair, count in sorted_pairs[:5]:
                print(f"    {pair}: {count}")

        print("\n" + "-"*100)
        print("TEAM ANALYSIS")
        print("-"*100)

        for team in analysis.teams:
            print(f"\nTeam: {team.get('team_name', 'Unknown')}")
            print(f"  Architecture: {team.get('architecture', 'godsaf')}")
            print(f"  Members: {len(team.get('team_members', []))}")

            team_args = [arg for arg in analysis.arguments if any(
                member.get('name') == arg.get('member_name')
                for member in team.get('team_members', [])
            )]

            if team_args:
                team_scores = [arg.get('evaluation_log', {}).get('overall_score', 0) for arg in team_args]
                print(f"  Arguments Created: {len(team_args)}")
                print(f"  Average Score: {statistics.mean(team_scores):.1f}/100" if team_scores else "  Average Score: N/A")

        print("\n" + "="*100 + "\n")

    def export_to_json(self, analysis: DebateAnalysis, output_file: str):
        output_data = {
            "metadata": {
                "config_id": analysis.config_id,
                "topic": analysis.topic,
                "max_rounds": analysis.max_rounds,
                "source_file": str(self.results_file)
            },
            "vote_analysis": {
                "initial": {
                    "agree": analysis.initial_agree,
                    "disagree": analysis.initial_disagree
                },
                "final": {
                    "agree": analysis.final_agree,
                    "disagree": analysis.final_disagree
                },
                "delta": {
                    "agree": analysis.vote_delta_agree,
                    "disagree": analysis.vote_delta_disagree
                },
                "swing_voters": [
                    {
                        "name": sv.name,
                        "initial": sv.initial,
                        "final": sv.final,
                        "direction": sv.direction
                    }
                    for sv in analysis.swing_voters
                ],
                "winner": {
                    "side": analysis.winner,
                    "margin": analysis.win_margin,
                    "percentage": analysis.win_percentage
                }
            },
            "iteration_stats": analysis.iteration_stats,
            "evaluation_stats": analysis.evaluation_stats,
            "strategic_alignment_stats": analysis.strategic_alignment_stats
        }

        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(output_data, f, indent=2, ensure_ascii=False)

        print(f"Analysis exported to: {output_file}")


def main():
    if len(sys.argv) < 2:
        print("Usage: python analyse_debate_results.py <results_file.json> [--export <output_file.json>]")
        print("\nExample:")
        print("  python analyse_debate_results.py results/debate_results.json")
        print("  python analyse_debate_results.py results/debate_results.json --export analysis.json")
        sys.exit(1)

    results_file = sys.argv[1]

    export_file = None
    if "--export" in sys.argv:
        export_idx = sys.argv.index("--export")
        if len(sys.argv) > export_idx + 1:
            export_file = sys.argv[export_idx + 1]

    try:
        analyser = DebateResultsAnalyser(results_file)
        analysis = analyser.analyse()
        analyser.print_analysis(analysis)

        if export_file:
            analyser.export_to_json(analysis, export_file)

    except FileNotFoundError as e:
        print(f"Error: {e}")
        sys.exit(1)
    except json.JSONDecodeError as e:
        print(f"Error: Invalid JSON file - {e}")
        sys.exit(1)
    except Exception as e:
        print(f"Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
