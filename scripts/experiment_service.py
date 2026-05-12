"""
Experiment Service: Run multiple debate configs in a single batch.

Features:
- Creates a timestamped batch folder under results/ (or custom root)
- Overrides each config's output_file into that folder
- Runs each config via create_debate_from_config
- Skips configs that error out, recording failure reason
- Writes batch_summary.json with per-config status and paths
"""

import json
import sys
import time
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Any

# Ensure project root is on path if invoked directly
PROJECT_ROOT = Path(__file__).parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.append(str(PROJECT_ROOT))

from src.debate_extended.debate_config import create_debate_from_config


@dataclass
class ExperimentResult:
    config_path: str
    status: str  # "success" | "skipped" | "failed"
    output_file: str | None
    error: str | None
    architecture_summary: Dict[str, Any] | None = None


class ExperimentService:
    def __init__(self, batch_root: str | Path = "results"):
        self.batch_root = Path(batch_root)

    def _extract_architecture_summary(self, result_file: str) -> Dict[str, Any] | None:
        """
        Extract architecture summary from a result file.

        Args:
            result_file: Path to the result JSON file

        Returns:
            Dictionary with architecture summary or None if extraction fails
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

            # Create summary for easy analysis
            summary = {}
            for team_name, arch_info in team_architectures.items():
                team_summary = {
                    "architecture": arch_info.get("architecture", "unknown"),
                    "team_type": arch_info.get("team_type", "unknown"),
                }

                # Add feature flags
                members = arch_info.get("members", [])
                if members:
                    has_knowledge = any(m.get("knowledge_active", False) for m in members)
                    has_rag = any(m.get("knowledge_use_rag", False) for m in members)
                    has_web_search = any(m.get("knowledge_use_web_search", False) for m in members)
                    has_evaluation = any(m.get("evaluation_active", False) for m in members)

                    team_summary["features"] = {
                        "knowledge": has_knowledge,
                        "rag": has_rag,
                        "web_search": has_web_search,
                        "evaluation": has_evaluation,
                    }

                summary[team_name] = team_summary

            return summary

        except Exception as e:
            print(f"  ⚠️  Could not extract architecture summary: {e}")
            return None

    def _make_batch_dir(self, name: str | None = None) -> Path:
        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        if not name:
            name = f"batch_{ts}"
        batch_dir = self.batch_root / name
        batch_dir.mkdir(parents=True, exist_ok=True)
        return batch_dir

    def _load_config_json(self, path: Path) -> Dict[str, Any]:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)

    def _write_config_json(self, path: Path, data: Dict[str, Any]) -> None:
        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)

    def run_batch(self, config_paths: List[str], batch_name: str | None = None) -> Dict[str, Any]:
        batch_dir = self._make_batch_dir(batch_name)
        summary: Dict[str, Any] = {
            "batch_name": batch_dir.name,
            "batch_dir": str(batch_dir.resolve()),
            "started_at": datetime.now().isoformat(),
            "results": [],
        }

        for idx, cfg in enumerate(config_paths, start=1):
            cfg_path = Path(cfg)
            result_rec: ExperimentResult = ExperimentResult(
                config_path=str(cfg_path), status="skipped", output_file=None, error=None
            )

            print(f"[Batch {batch_dir.name}] {idx}/{len(config_paths)} → {cfg_path}")

            if not cfg_path.exists():
                result_rec.status = "failed"
                result_rec.error = "Config file not found"
                summary["results"].append(result_rec.__dict__)
                print(f"  ❌ Missing: {cfg_path}")
                continue

            try:
                # Load, override output_file, write to temp config copy inside batch
                original = self._load_config_json(cfg_path)
                output_filename = cfg_path.stem + "_results.json"
                overridden = dict(original)
                overridden["output_file"] = str(batch_dir / output_filename)

                temp_cfg = batch_dir / (cfg_path.stem + "_overridden.json")
                self._write_config_json(temp_cfg, overridden)

                # Run
                _ = create_debate_from_config(str(temp_cfg))

                result_rec.status = "success"
                result_rec.output_file = overridden["output_file"]

                # Extract architecture summary
                arch_summary = self._extract_architecture_summary(result_rec.output_file)
                if arch_summary:
                    result_rec.architecture_summary = arch_summary

                print(f"  ✅ Saved → {result_rec.output_file}")

            except Exception as e:
                result_rec.status = "failed"
                result_rec.error = str(e)
                print(f"  ❌ Error: {e}")

            summary["results"].append(result_rec.__dict__)

            # Wait 10 seconds between simulations (except after the last one)
            if idx < len(config_paths):
                print(f"  ⏳ Waiting 10 seconds before next simulation...")
                time.sleep(10)

        summary["finished_at"] = datetime.now().isoformat()

        # Write batch summary
        summary_file = batch_dir / "batch_summary.json"
        with open(summary_file, "w", encoding="utf-8") as f:
            json.dump(summary, f, indent=2, ensure_ascii=False)

        print(f"\n📦 Batch summary saved to: {summary_file.resolve()}")
        return summary


def main() -> int:
    # Directory containing JSON config files to run
    config_dir = Path("configs/large_debate")  # Change to desired folder (e.g., "configs/advanced")
    config_paths: List[str] = sorted(str(p) for p in config_dir.glob("*.json") if p.is_file())

    svc = ExperimentService(batch_root="experiments")
    batch_name = f"large_debate_{config_dir.name}_{datetime.now().strftime("%Y%m%d_%H%M%S")}"
    _ = svc.run_batch(config_paths=config_paths, batch_name=batch_name)
    return 0


if __name__ == "__main__":
    sys.exit(main())


