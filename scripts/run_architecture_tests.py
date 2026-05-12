"""
CLI entry point for architecture testing service.

Usage:
    python run_architecture_tests.py --config path/to/config.json
    python run_architecture_tests.py --folder path/to/configs/
    python run_architecture_tests.py --folder path/to/configs/ --output-dir custom_results/
"""

import argparse
import sys
from pathlib import Path

from architecture_test_service.batch_service import ArchitectureTestService


def main() -> int:
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(
        description="Run architecture comparison tests for debate configurations",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Test a single config
  python run_architecture_tests.py --config configs/basic/debate1.json

  # Test all configs in a folder
  python run_architecture_tests.py --folder configs/basic/

  # Use custom output directory
  python run_architecture_tests.py --folder configs/basic/ --output-dir my_tests/
        """,
    )

    # Input: config or folder (mutually exclusive)
    input_group = parser.add_mutually_exclusive_group(required=True)
    input_group.add_argument(
        "--config",
        type=str,
        help="Path to a single config file to test",
    )
    input_group.add_argument(
        "--folder",
        type=str,
        help="Path to a folder containing config files to test",
    )

    # Output directory
    parser.add_argument(
        "--output-dir",
        type=str,
        default="architecture_tests_2",
        help="Output directory for test results (default: architecture_tests_2/)",
    )

    args = parser.parse_args()

    # Create service
    service = ArchitectureTestService(output_root=args.output_dir)

    # Collect config paths
    config_paths = []

    if args.config:
        config_path = Path(args.config)
        if not config_path.exists():
            print(f"❌ Error: Config file not found: {config_path}")
            return 1
        if not config_path.is_file():
            print(f"❌ Error: Not a file: {config_path}")
            return 1
        config_paths.append(config_path)

    elif args.folder:
        folder_path = Path(args.folder)
        if not folder_path.exists():
            print(f"❌ Error: Folder not found: {folder_path}")
            return 1
        if not folder_path.is_dir():
            print(f"❌ Error: Not a directory: {folder_path}")
            return 1

        # Find all JSON files
        config_paths = sorted(folder_path.glob("*.json"))
        if not config_paths:
            print(f"❌ Error: No JSON files found in {folder_path}")
            return 1

    # Run tests
    print(f"Running architecture tests for {len(config_paths)} config(s)")
    print(f"Output directory: {Path(args.output_dir).resolve()}\n")

    try:
        if len(config_paths) == 1:
            service.run_single_config(config_paths[0])
        else:
            service.run_batch(config_paths)

        print("✅ All tests complete!")
        return 0

    except KeyboardInterrupt:
        print("\n\n⚠️  Interrupted by user")
        return 130

    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
