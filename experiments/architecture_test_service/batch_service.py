"""
Batch processing service for architecture testing.

Orchestrates running multiple configs and generating summaries.
"""

import json
import time
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

from .config_generator import generate_configs
from .debate_runner import run_single_debate
from .models import BatchSummary, DebateRunResult


class ArchitectureTestService:
    """Service for running architecture comparison tests."""

    def __init__(self, output_root: str | Path = "architecture_tests"):
        """
        Initialize the service.

        Args:
            output_root: Root directory for test outputs
        """
        self.output_root = Path(output_root)

    def _extract_architecture_details(self, result_file: str) -> Optional[Dict[str, Any]]:
        """
        Extract architecture details from a result file.

        Args:
            result_file: Path to the result JSON file

        Returns:
            Dictionary with architecture details or None if extraction fails
        """
        try:
            result_path = Path(result_file)
            if not result_path.exists():
                return None

            with open(result_path, "r", encoding="utf-8") as f:
                results = json.load(f)

            # Extract team architectures if present
            team_architectures = results.get("team_architectures", {})
            if not team_architectures:
                return None

            # Summarize architecture details for easy analysis
            details = {}
            for team_name, arch_info in team_architectures.items():
                team_summary = {
                    "architecture": arch_info.get("architecture"),
                    "team_type": arch_info.get("team_type"),
                }

                # Add ToT config if present
                if "tot_config" in arch_info:
                    team_summary["tot_config"] = arch_info["tot_config"]

                # Summarize member features
                members = arch_info.get("members", [])
                if members:
                    # Check if any member has knowledge or evaluation active
                    has_knowledge = any(m.get("knowledge_active", False) for m in members)
                    has_rag = any(m.get("knowledge_use_rag", False) for m in members)
                    has_web_search = any(m.get("knowledge_use_web_search", False) for m in members)
                    has_evaluation = any(m.get("evaluation_active", False) for m in members)

                    team_summary["features"] = {
                        "knowledge_active": has_knowledge,
                        "rag_enabled": has_rag,
                        "web_search_enabled": has_web_search,
                        "evaluation_active": has_evaluation,
                        "num_members": len(members),
                    }

                details[team_name] = team_summary

            return details

        except Exception as e:
            print(f"  ⚠️  Could not extract architecture details from {result_file}: {e}")
            return None

    def _make_batch_dir(self, base_config_id: str) -> Path:
        """
        Create batch directory with timestamp.

        Args:
            base_config_id: ID of base config

        Returns:
            Path to batch directory
        """
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        batch_dir = self.output_root / f"{base_config_id}_{timestamp}"
        batch_dir.mkdir(parents=True, exist_ok=True)
        return batch_dir

    def run_single_config(
        self,
        config_path: str | Path,
    ) -> BatchSummary:
        """
        Run architecture tests for a single base config.

        Process:
        1. Generate 40 config variations
        2. Create batch directory
        3. Run all 40 debates sequentially
        4. Generate batch summary

        Args:
            config_path: Path to base configuration file

        Returns:
            BatchSummary with results and errors
        """
        config_path = Path(config_path)
        started_at = datetime.now()

        # Load config to get ID
        with open(config_path, "r", encoding="utf-8") as f:
            base_config = json.load(f)

        base_config_id = base_config.get("id", config_path.stem)

        # Create batch directory
        batch_dir = self._make_batch_dir(base_config_id)

        print(f"\n{'='*80}")
        print(f"Starting architecture tests for: {base_config_id}")
        print(f"Batch directory: {batch_dir}")
        print(f"{'='*80}\n")

        # Generate configs
        try:
            configs = generate_configs(config_path, batch_dir)
        except Exception as e:
            print(f"❌ Failed to generate configs: {e}")
            raise

        print(f"Generated {len(configs)} config variations\n")

        # Run debates
        results: List[DebateRunResult] = []
        successful = 0
        failed = 0

        for idx, (config, team1_arch, team2_arch, team1_role, team2_role) in enumerate(configs, 1):
            print(f"[{idx}/{len(configs)}] Running: {team1_arch} vs {team2_arch} ({team1_role} first)")

            result = run_single_debate(
                config,
                team1_arch,
                team2_arch,
                team1_role,
                team2_role,
            )

            results.append(result)

            if result.status == "success":
                successful += 1
                winner_str = f"Winner: {result.winner}" if result.winner else "Winner: N/A"
                margin_str = f"(margin: {result.vote_margin})" if result.vote_margin is not None else ""
                print(f"  ✅ Success - {winner_str} {margin_str}")
            else:
                failed += 1
                print(f"  ❌ Failed - {result.error}")

            # Wait 10 seconds between simulations (except after the last one)
            if idx < len(configs):
                print(f"  ⏳ Waiting 60 seconds before next simulation...")
                time.sleep(60)

        # Create summary
        finished_at = datetime.now()

        results_matrix = []
        errors = []

        for result in results:
            result_dict = {
                "team1_arch": result.team1_arch,
                "team2_arch": result.team2_arch,
                "team1_role": result.team1_role,
                "team2_role": result.team2_role,
                "status": result.status,
                "output_file": result.output_file,
            }

            if result.winner is not None:
                result_dict["winner"] = result.winner
            if result.vote_margin is not None:
                result_dict["vote_margin"] = result.vote_margin

            # Extract architecture details from result file if successful
            if result.status == "success" and result.output_file:
                arch_details = self._extract_architecture_details(result.output_file)
                if arch_details:
                    result_dict["architecture_details"] = arch_details

            results_matrix.append(result_dict)

            if result.status == "failed":
                errors.append({
                    "config": f"{result.team1_arch} vs {result.team2_arch} ({result.team1_role} first)",
                    "error": result.error,
                })

        summary = BatchSummary(
            base_config_id=base_config_id,
            base_config_path=str(config_path.resolve()),
            started_at=started_at.isoformat(),
            finished_at=finished_at.isoformat(),
            total_runs=len(configs),
            successful_runs=successful,
            failed_runs=failed,
            results_matrix=results_matrix,
            errors=errors,
        )

        # Write summary to file
        summary_file = batch_dir / "batch_summary.json"
        with open(summary_file, "w", encoding="utf-8") as f:
            json.dump(
                {
                    "base_config_id": summary.base_config_id,
                    "base_config_path": summary.base_config_path,
                    "started_at": summary.started_at,
                    "finished_at": summary.finished_at,
                    "total_runs": summary.total_runs,
                    "successful_runs": summary.successful_runs,
                    "failed_runs": summary.failed_runs,
                    "results_matrix": summary.results_matrix,
                    "errors": summary.errors,
                },
                f,
                indent=2,
                ensure_ascii=False,
            )

        print(f"\n{'='*80}")
        print(f"Batch complete: {successful}/{len(configs)} successful")
        print(f"Summary saved to: {summary_file}")
        print(f"{'='*80}\n")

        return summary

    def run_batch(
        self,
        config_paths: List[str | Path],
    ) -> List[Optional[BatchSummary]]:
        """
        Run architecture tests for multiple base configs.

        Each config is processed independently. If one fails, others continue.

        Args:
            config_paths: List of paths to base configuration files

        Returns:
            List of BatchSummary objects (or None for failed configs)
        """
        summaries = []

        for idx, config_path in enumerate(config_paths, 1):
            print(f"\n{'#'*80}")
            print(f"Processing config {idx}/{len(config_paths)}: {config_path}")
            print(f"{'#'*80}")

            try:
                summary = self.run_single_config(config_path)
                summaries.append(summary)
            except Exception as e:
                print(f"\n❌ Failed to process {config_path}: {e}\n")
                summaries.append(None)

        # Print final summary
        successful_batches = sum(1 for s in summaries if s is not None)
        print(f"\n{'#'*80}")
        print(f"All batches complete: {successful_batches}/{len(config_paths)} configs processed successfully")
        print(f"{'#'*80}\n")

        return summaries
