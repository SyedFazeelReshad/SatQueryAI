"""
SatQuery AI — VLM Inference Test Script (Stage 2)
Tests the adapted VLM on sample remote-sensing images.
"""

import argparse
import logging
from pathlib import Path

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def main():
    parser = argparse.ArgumentParser(description="Test SatQuery AI VLM inference")
    parser.add_argument("--adapter_path", type=Path, default=Path("../models/trained/rs_vlm_lora/"))
    parser.add_argument("--image", type=Path, required=True, help="Test image path")
    parser.add_argument("--question", type=str, default="Describe this satellite image.")
    args = parser.parse_args()
    
    logger.info("=== SatQuery AI VLM Inference Test ===")
    logger.info(f"Adapter path: {args.adapter_path}")
    logger.info(f"Image: {args.image}")
    logger.info(f"Question: {args.question}")
    
    if not args.adapter_path.exists():
        logger.warning("Adapter not found — training has not been completed yet.")
        logger.warning("Run train_vlm.py first to produce the adapter.")
        return 1
    
    logger.info("Stage 2 inference implementation pending adapter training.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
