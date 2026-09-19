"""
SatQuery AI — BigEarthNet Preparation Pipeline
Stage 2: Prepares, filters, formats, and splits BigEarthNet for VLM adaptation.

Pipeline:
1. Validates directory structure & patch integrity.
2. Filters out cloudy, corrupted, nodata, or uniform uninformative tiles.
3. Formats multi-label remote sensing metadata into Qwen2-VL conversational dialogues.
4. Generates stratified train/val/test splits with reproducibility hashes.
5. Saves manifests to data/manifests/ for Google Colab / local training.
"""

import argparse
import json
import logging
from pathlib import Path
from typing import Any, Dict, List

from training.preprocessing.filtering import filter_patch_by_metadata, filter_dataset_manifest
from training.preprocessing.formatting import generate_multiturn_conversations
from training.preprocessing.splitting import split_dataset

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)


def prepare_pipeline(
    data_dir: Path,
    output_manifest_dir: Path,
    target_sample_size: int = 10000,
    train_ratio: float = 0.8,
    val_ratio: float = 0.1,
    test_ratio: float = 0.1
) -> Dict[str, Any]:
    output_manifest_dir.mkdir(parents=True, exist_ok=True)
    
    logger.info(f"Scanning raw patches in {data_dir}...")
    raw_manifest: List[Dict[str, Any]] = []
    
    if data_dir.exists():
        for patch_folder in data_dir.iterdir():
            if patch_folder.is_dir():
                json_meta_file = patch_folder / f"{patch_folder.name}_labels_metadata.json"
                labels = []
                metadata = {}
                if json_meta_file.exists():
                    try:
                        with open(json_meta_file, "r", encoding="utf-8") as f:
                            meta_content = json.load(f)
                            labels = meta_content.get("labels", [])
                            metadata = meta_content
                    except Exception as e:
                        logger.warning(f"Could not read metadata for {patch_folder.name}: {e}")
                
                raw_manifest.append({
                    "patch_id": patch_folder.name,
                    "image_path": str(patch_folder),
                    "labels": labels,
                    "metadata": metadata
                })
    else:
        logger.warning(f"Data directory {data_dir} does not exist yet. Generating template manifest structure.")
        
    logger.info(f"Found {len(raw_manifest)} total patches. Applying filtering rules...")
    
    # 1. Apply Filtering
    filtered_manifest, filter_stats = filter_dataset_manifest(
        raw_manifest,
        target_sample_size=target_sample_size,
        balance_classes=True
    )
    
    # 2. Apply Instruction Formatting
    logger.info("Generating multi-query Vision-Language instruction dialogues...")
    formatted_manifest = []
    for item in filtered_manifest:
        conversations = generate_multiturn_conversations(
            patch_id=item["patch_id"],
            image_path=item["image_path"],
            labels=item["labels"],
            metadata=item.get("metadata", {})
        )
        item_formatted = dict(item)
        item_formatted["conversations"] = conversations
        formatted_manifest.append(item_formatted)
        
    # 3. Apply Splitting
    logger.info("Partitioning into deterministic train/validation/test splits...")
    train_set, val_set, test_set, split_meta = split_dataset(
        formatted_manifest,
        train_ratio=train_ratio,
        val_ratio=val_ratio,
        test_ratio=test_ratio
    )
    
    # 4. Save Manifests
    train_path = output_manifest_dir / "bigearthnet_train.json"
    val_path = output_manifest_dir / "bigearthnet_val.json"
    test_path = output_manifest_dir / "bigearthnet_test.json"
    meta_path = output_manifest_dir / "dataset_summary.json"
    
    with open(train_path, "w", encoding="utf-8") as f:
        json.dump(train_set, f, indent=2)
    with open(val_path, "w", encoding="utf-8") as f:
        json.dump(val_set, f, indent=2)
    with open(test_path, "w", encoding="utf-8") as f:
        json.dump(test_set, f, indent=2)
        
    summary = {
        "filter_statistics": filter_stats,
        "split_metadata": split_meta,
        "paths": {
            "train": str(train_path),
            "val": str(val_path),
            "test": str(test_path)
        }
    }
    with open(meta_path, "w", encoding="utf-8") as f:
        json.dump(summary, f, indent=2)
        
    logger.info(f"Dataset preparation complete! Manifests saved to {output_manifest_dir}")
    return summary


def main():
    parser = argparse.ArgumentParser(description="Prepare BigEarthNet dataset for SatQuery AI VLM fine-tuning")
    parser.add_argument("--data_dir", type=Path, default=Path("data/raw/bigearthnet"), help="Raw BigEarthNet directory")
    parser.add_argument("--output_dir", type=Path, default=Path("data/manifests"), help="Output manifest directory")
    parser.add_argument("--sample_size", type=int, default=10000, help="Target filtered sample size")
    args = parser.parse_args()
    
    summary = prepare_pipeline(args.data_dir, args.output_dir, target_sample_size=args.sample_size)
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
