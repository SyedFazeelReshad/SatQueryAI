"""
SatQuery AI — Dataset Validation Script
Validates that a dataset directory has the expected structure.
"""

import argparse
import json
import logging
from pathlib import Path

logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
logger = logging.getLogger(__name__)


def validate_bigearthnet(data_dir: Path) -> dict:
    """Validate BigEarthNet dataset."""
    result = {"dataset": "BigEarthNet", "valid": False, "issues": [], "stats": {}}
    
    if not data_dir.exists():
        result["issues"].append(f"Directory not found: {data_dir}")
        return result
    
    patches = list(data_dir.iterdir())
    result["stats"]["total_patches"] = len(patches)
    
    if len(patches) == 0:
        result["issues"].append("No patches found")
        return result
    
    result["valid"] = True
    logger.info(f"BigEarthNet: {len(patches)} patches found at {data_dir}")
    return result


def main():
    parser = argparse.ArgumentParser(description="Validate SatQuery AI training datasets")
    parser.add_argument("--dataset", choices=["bigearthnet", "vrsbench", "rsvqa", "cdvqa"], required=True)
    parser.add_argument("--data_dir", type=Path, required=True)
    args = parser.parse_args()
    
    if args.dataset == "bigearthnet":
        result = validate_bigearthnet(args.data_dir)
    else:
        logger.info(f"Validation for {args.dataset} not yet implemented (Stage 2)")
        return 0
    
    print(json.dumps(result, indent=2))
    return 0 if result["valid"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
