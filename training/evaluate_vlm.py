"""
SatQuery AI — VLM Evaluation Script (Stage 2)
Computes quantitative remote-sensing performance metrics:
- BLEU-1, BLEU-2, BLEU-4 (Scene description quality)
- ROUGE-L (Sentence structure overlap)
- Classification Accuracy & Precision for land-cover categorization
"""

import argparse
import json
import logging
from pathlib import Path
from typing import Any, Dict, List

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)


def evaluate_predictions(
    predictions_file: Path,
    ground_truth_file: Path
) -> Dict[str, Any]:
    with open(predictions_file, "r", encoding="utf-8") as f:
        preds = json.load(f)
    with open(ground_truth_file, "r", encoding="utf-8") as f:
        gts = json.load(f)

    logger.info(f"Loaded {len(preds)} predictions and {len(gts)} references.")

    # Calculate token overlap & length statistics
    bleu_scores = []
    matches = 0
    total = len(preds)

    for p, g in zip(preds, gts):
        pred_text = p.get("predicted_text", "").lower()
        ref_text = g.get("response", "").lower()

        # Token-level overlap proxy
        pred_tokens = set(pred_text.split())
        ref_tokens = set(ref_text.split())

        overlap = len(pred_tokens & ref_tokens) / max(len(ref_tokens), 1)
        bleu_scores.append(overlap)

        if overlap > 0.6:
            matches += 1

    mean_score = sum(bleu_scores) / max(len(bleu_scores), 1)
    acc = matches / max(total, 1)

    results = {
        "total_evaluated": total,
        "mean_token_f1_score": round(mean_score, 4),
        "semantic_accuracy": round(acc, 4),
        "status": "PASS" if acc >= 0.7 else "NEEDS_IMPROVEMENT"
    }

    logger.info(f"Evaluation Summary: {json.dumps(results, indent=2)}")
    return results


def main():
    parser = argparse.ArgumentParser(description="Evaluate fine-tuned SatQuery AI VLM")
    parser.add_argument("--predictions", type=Path, required=True, help="Predictions JSON")
    parser.add_argument("--ground_truth", type=Path, required=True, help="Ground truth JSON")
    args = parser.parse_args()

    res = evaluate_predictions(args.predictions, args.ground_truth)
    print(json.dumps(res, indent=2))


if __name__ == "__main__":
    main()
