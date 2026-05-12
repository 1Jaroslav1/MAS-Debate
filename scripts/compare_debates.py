import json
import sys
import io
from pathlib import Path
from typing import List, Dict
from scripts.analyse_debate_results import DebateResultsAnalyser, DebateAnalysis

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')


class DebateComparator:
    def __init__(self, result_files: List[str]):
        self.analyses: List[DebateAnalysis] = []
        self.files = result_files

        for file in result_files:
            try:
                analyser = DebateResultsAnalyser(file)
                analysis = analyser.analyse()
                self.analyses.append(analysis)
                print(f"✓ Loaded: {Path(file).name}")
            except Exception as e:
                print(f"✗ Error loading {file}: {e}")

    def compare(self):
        if not self.analyses:
            print("No valid analyses to compare")
            return

        print("\n" + "="*120)
        print("DEBATE COMPARISON")
        print("="*120)

        print(f"\n{len(self.analyses)} debates loaded\n")

        self._print_comparison_table()
        self._print_vote_dynamics()
        self._print_iteration_comparison()
        self._print_evaluation_comparison()
        self._print_strategic_comparison()

    def _print_comparison_table(self):
        print("-"*120)
        print("OVERVIEW")
        print("-"*120)

        header = f"{'Config ID':<60} {'Winner':<25} {'Margin':>8} {'Win %':>8}"
        print(header)
        print("-"*120)

        for analysis in self.analyses:
            config_short = analysis.config_id[:57] + "..." if len(analysis.config_id) > 60 else analysis.config_id
            winner_short = "Proposition" if "Proposition" in analysis.winner else "Opposition"
            print(f"{config_short:<60} {winner_short:<25} {analysis.win_margin:>8} {analysis.win_percentage:>7.1f}%")

    def _print_vote_dynamics(self):
        print("\n" + "-"*120)
        print("VOTE DYNAMICS")
        print("-"*120)

        header = f"{'Config ID':<60} {'Initial A/D':>12} {'Final A/D':>12} {'Delta A/D':>12} {'Swing':>8}"
        print(header)
        print("-"*120)

        for analysis in self.analyses:
            config_short = analysis.config_id[:57] + "..." if len(analysis.config_id) > 60 else analysis.config_id
            initial = f"{analysis.initial_agree}/{analysis.initial_disagree}"
            final = f"{analysis.final_agree}/{analysis.final_disagree}"
            delta_a = f"{analysis.vote_delta_agree:+d}" if analysis.vote_delta_agree != 0 else "0"
            delta_d = f"{analysis.vote_delta_disagree:+d}" if analysis.vote_delta_disagree != 0 else "0"
            delta = f"{delta_a}/{delta_d}"
            swing = len(analysis.swing_voters)

            print(f"{config_short:<60} {initial:>12} {final:>12} {delta:>12} {swing:>8}")

    def _print_iteration_comparison(self):
        print("\n" + "-"*120)
        print("ITERATION STATISTICS")
        print("-"*120)

        header = f"{'Config ID':<60} {'Avg Iter':>10} {'1st Try':>10} {'Rejected':>10}"
        print(header)
        print("-"*120)

        for analysis in self.analyses:
            config_short = analysis.config_id[:57] + "..." if len(analysis.config_id) > 60 else analysis.config_id
            its = analysis.iteration_stats

            avg_iter = f"{its['avg_iterations_per_argument']:.2f}"
            first_try = f"{its['accepted_on_first_try']}/{its['total_arguments']}"
            rejected = its['rejected_iterations']

            print(f"{config_short:<60} {avg_iter:>10} {first_try:>10} {rejected:>10}")

    def _print_evaluation_comparison(self):
        print("\n" + "-"*120)
        print("EVALUATION SCORES")
        print("-"*120)

        header = f"{'Config ID':<60} {'Overall':>10} {'Strategic':>10} {'UGN Cov':>10}"
        print(header)
        print("-"*120)

        for analysis in self.analyses:
            config_short = analysis.config_id[:57] + "..." if len(analysis.config_id) > 60 else analysis.config_id
            evs = analysis.evaluation_stats

            overall = f"{evs['overall_score']['mean']:.1f}"
            strategic = f"{evs['strategic_alignment_score']['mean']:.1f}"
            ugn = f"{evs['ugn_coverage_score']['mean']:.1f}"

            print(f"{config_short:<60} {overall:>10} {strategic:>10} {ugn:>10}")

    def _print_strategic_comparison(self):
        print("\n" + "-"*120)
        print("STRATEGIC ALIGNMENT")
        print("-"*120)

        header = f"{'Config ID':<60} {'Primary':>10} {'Both':>10} {'Neither':>10}"
        print(header)
        print("-"*120)

        for analysis in self.analyses:
            config_short = analysis.config_id[:57] + "..." if len(analysis.config_id) > 60 else analysis.config_id
            sas = analysis.strategic_alignment_stats

            primary = sas['primary_ugn_addressed']
            both = sas['both_ugn_addressed']
            neither = sas['neither_ugn_addressed']

            print(f"{config_short:<60} {primary:>10} {both:>10} {neither:>10}")

        print("\n" + "="*120 + "\n")

    def export_comparison(self, output_file: str):
        comparison_data = {
            "debates_compared": len(self.analyses),
            "debates": [
                {
                    "config_id": analysis.config_id,
                    "topic": analysis.topic,
                    "winner": analysis.winner,
                    "win_margin": analysis.win_margin,
                    "win_percentage": analysis.win_percentage,
                    "vote_delta": {
                        "agree": analysis.vote_delta_agree,
                        "disagree": analysis.vote_delta_disagree
                    },
                    "swing_voters_count": len(analysis.swing_voters),
                    "iteration_stats": analysis.iteration_stats,
                    "evaluation_stats": analysis.evaluation_stats,
                    "strategic_alignment_stats": analysis.strategic_alignment_stats
                }
                for analysis in self.analyses
            ]
        }

        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(comparison_data, f, indent=2, ensure_ascii=False)

        print(f"Comparison exported to: {output_file}")


def main():
    if len(sys.argv) < 3:
        print("Usage: python compare_debates.py <results_file1.json> <results_file2.json> [...] [--export <output_file.json>]")
        print("\nExample:")
        print("  python compare_debates.py results/debate1.json results/debate2.json results/debate3.json")
        print("  python compare_debates.py results/*.json --export comparison.json")
        sys.exit(1)

    export_file = None
    result_files = []

    for i, arg in enumerate(sys.argv[1:]):
        if arg == "--export":
            if i + 2 < len(sys.argv):
                export_file = sys.argv[i + 2]
            break
        elif not arg.endswith('.json'):
            continue
        else:
            result_files.append(arg)

    if not result_files:
        print("Error: No valid result files specified")
        sys.exit(1)

    try:
        comparator = DebateComparator(result_files)
        comparator.compare()

        if export_file:
            comparator.export_comparison(export_file)

    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
