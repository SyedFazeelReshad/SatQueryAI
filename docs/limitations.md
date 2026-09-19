# SatQuery AI — System Status & Limitations

## Stage 2 Status (Current)

### Vision-Language Capabilities (Stage 2)
- **Primary VLM:** `Qwen2-VL-2B-Instruct` with LoRA adapter fine-tuned on BigEarthNet.
- **Dynamic Resolution:** Preserves high-resolution satellite imagery details (up to 1280×1280 pixels) without square resizing distortion.
- **Single-Image VQA:** Real remote-sensing visual question answering guided by deterministic measurements.
- **Scene Captioning:** Generates comprehensive remote-sensing descriptions of land cover and terrain.
- **Change Reasoning:** Explains bi-temporal changes in natural language based on Change Vector Analysis (CVA) raster evidence.
- **Graceful Fallback:** If adapter weights are not yet present in `models/trained/rs_vlm_lora/`, the backend safely operates in stub mode with informative instructions rather than crashing.

### Object Detection & Grounding (Stage 2 Upgraded)
- **Grounding DINO 1.5 Edge:** Integrated for text-guided zero-shot object detection in satellite scenes (runways, reservoirs, industrial complexes).
- **MobileSAM v2:** 40× faster promptable segmentation generating polygon masks from Grounding DINO boxes on CPU or GPU.

### Deterministic Scientific Engine (Active)
- All physical measurements ($km^2$, pixel counts, percentages, NDVI, NDWI, Built-Up proxies) are computed deterministically from raster data.
- The VLM interprets and explains measurements, but **never fabricates numerical values**.

---

## Known Current Constraints

### Registration
- ORB + RANSAC is optimized for optical-to-optical bi-temporal alignment.
- For optical-SAR cross-modal alignment, severe radiometric differences may require feature-level or GCP alignment.

### Area Calculations
- Physical area calculations assume projected CRS (UTM / Web Mercator in meters).
- Geographic CRS (degrees) uses WGS84 haversine ellipsoid approximation at scene centroid.

---

## Scientific Honesty Statement

This system never fabricates:
- Satellite imagery
- Geographical coordinates
- Measurements or percentages
- Detections or segmentation masks
- Confidence metrics
