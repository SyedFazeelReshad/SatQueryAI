import numpy as np
from sklearn.cluster import MiniBatchKMeans
import cv2
from app.geospatial.area import area_summary
from app.geospatial.raster import RasterMetadata
from app.geospatial.indices import calculate_ndvi, calculate_ndwi

def extract_spectral_features(array: np.ndarray, nodata: float | None = None) -> np.ndarray:
    h, w, c = array.shape
    features = array.reshape(-1, c).astype(np.float32)
    # Basic normalization per band
    for i in range(c):
        band_min = np.nanmin(features[:, i])
        band_max = np.nanmax(features[:, i])
        if band_max > band_min:
            features[:, i] = (features[:, i] - band_min) / (band_max - band_min)
    
    if nodata is not None:
        features[features == nodata] = 0.0
    
    return np.nan_to_num(features)

def extract_texture_features(array: np.ndarray) -> np.ndarray:
    h, w, c = array.shape
    gray = np.mean(array, axis=2).astype(np.float32)
    gray = cv2.normalize(gray, None, 0, 255, cv2.NORM_MINMAX).astype(np.uint8)
    
    # Use Scharr gradient magnitude as simple texture
    grad_x = cv2.Scharr(gray, cv2.CV_32F, 1, 0)
    grad_y = cv2.Scharr(gray, cv2.CV_32F, 0, 1)
    mag = cv2.magnitude(grad_x, grad_y)
    
    return mag.reshape(-1, 1)

def cluster_image(features: np.ndarray, n_clusters: int = 5) -> np.ndarray:
    kmeans = MiniBatchKMeans(n_clusters=n_clusters, random_state=42, batch_size=4096, n_init='auto')
    labels = kmeans.fit_predict(features)
    return labels

def assign_class_labels(cluster_labels: np.ndarray, features: np.ndarray, array: np.ndarray, metadata: RasterMetadata) -> dict:
    h, w, c = array.shape
    labels_2d = cluster_labels.reshape(h, w)
    
    # Simple rule-based assignment if we have enough bands
    has_indices = c >= 4
    ndvi_map = calculate_ndvi(array, 2, 3).get('ndvi', np.zeros((h, w))) if has_indices else np.zeros((h, w))
    ndwi_map = calculate_ndwi(array, 1, 3).get('ndwi', np.zeros((h, w))) if has_indices else np.zeros((h, w))
    
    classes = ["water", "vegetation", "built_up", "bare_soil", "other"]
    class_map = np.full((h, w), 4, dtype=np.uint8) # default 'other'
    
    n_clusters = len(np.unique(cluster_labels))
    class_areas = {}
    class_percentages = {}
    
    for i in range(n_clusters):
        mask = labels_2d == i
        if has_indices:
            mean_ndvi = np.mean(ndvi_map[mask])
            mean_ndwi = np.mean(ndwi_map[mask])
            if mean_ndwi > 0.1:
                cls_idx = 0 # water
            elif mean_ndvi > 0.3:
                cls_idx = 1 # vegetation
            elif mean_ndvi < 0.1 and np.mean(array[mask]) > 0.3:
                cls_idx = 2 # built up
            elif mean_ndvi < 0.15:
                cls_idx = 3 # bare soil
            else:
                cls_idx = 4
        elif c >= 3:
            pass  # Handled below via pixel-level spectral analysis for 3-band imagery
        else:
            class_map[mask] = 4

    # For 3-band RGB imagery, compute robust pixel-level classification using remote-sensing indices
    if not has_indices and c >= 3:
        r = array[:, :, 0].astype(np.float32)
        g = array[:, :, 1].astype(np.float32)
        b = array[:, :, 2].astype(np.float32)

        # Normalize to 0-1 if in 0-255 range
        if np.max(r) > 1.0 or np.max(g) > 1.0 or np.max(b) > 1.0:
            r = r / 255.0
            g = g / 255.0
            b = b / 255.0

        brightness = (r + g + b) / 3.0

        # Convert to HSV for accurate perceptual separation
        img_uint8 = np.clip(np.dstack([r, g, b]) * 255.0, 0, 255).astype(np.uint8)
        hsv = cv2.cvtColor(img_uint8, cv2.COLOR_RGB2HSV)
        h_channel = hsv[:, :, 0]             # 0 to 180 in OpenCV
        s_channel = hsv[:, :, 1] / 255.0     # 0 to 1.0
        v_channel = hsv[:, :, 2] / 255.0     # 0 to 1.0

        # 1. WATER (Hierarchical: coastal/lagoon and inland water bodies):
        ndwi_br = (b - r) / np.maximum(b + r, 0.01)
        ndwi_gr = (g - r) / np.maximum(g + r, 0.01)
        
        total_px = h * w
        lagoon_candidate = (
            (r < 0.35) & 
            (ndwi_gr > 0.08) & 
            (h_channel >= 62) & (h_channel <= 145) & 
            (s_channel >= 0.12) & (v_channel <= 0.65)
        )
        nb_w, out_w, stats_w, _ = cv2.connectedComponentsWithStats(lagoon_candidate.astype(np.uint8), connectivity=8)
        has_large_water = any(stats_w[i, cv2.CC_STAT_AREA] / total_px >= 0.10 for i in range(1, nb_w))
        
        if has_large_water:
            is_water = np.zeros_like(lagoon_candidate, dtype=bool)
            for i in range(1, nb_w):
                if stats_w[i, cv2.CC_STAT_AREA] >= 30:
                    is_water[out_w == i] = True
        else:
            pond_mask = (
                (ndwi_br > 0.22) & 
                (ndwi_gr > 0.15) & 
                (b >= g * 1.04) & 
                (h_channel >= 88) & (h_channel <= 135) & 
                (s_channel >= 0.20) & (s_channel <= 0.60) & 
                (v_channel >= 0.20) & (v_channel <= 0.52)
            )
            nb_p, out_p, stats_p, _ = cv2.connectedComponentsWithStats(pond_mask.astype(np.uint8), connectivity=8)
            is_water = np.zeros_like(pond_mask, dtype=bool)
            for i in range(1, nb_p):
                if stats_p[i, cv2.CC_STAT_AREA] >= 60:
                    is_water[out_p == i] = True

        # 2. VEGETATION:
        # Terrestrial plants (grass, trees): Green is higher than Red AND Blue.
        # Blue is strongly absorbed by chlorophyll: b < r * 1.25 and b < g * 0.90.
        is_veg = (
            ~is_water &
            (g > r * 1.05) & 
            (g > b * 1.15) & 
            (b < r * 1.25) & 
            (h_channel >= 25) & (h_channel <= 85) & 
            (s_channel > 0.12)
        )

        # 3. BARE SOIL:
        # Open unpaved reddish-brown earth. Must be distinct from terracotta / tile roofs.
        is_soil = (
            ~is_water & ~is_veg &
            (h_channel >= 10) & (h_channel < 25) & 
            (s_channel > 0.45) & (r > g * 1.25) & (r > b * 1.60) & 
            (brightness < 0.45)
        )

        # 4. BLACK / ROTATION MARGINS:
        is_margin = (brightness < 0.03)

        # 5. BUILT-UP / URBAN:
        # Roads, terracotta/shingle roofs, concrete, asphalt, buildings
        is_built = ~is_water & ~is_veg & ~is_soil & ~is_margin

        # Assign class indices
        # 0: water, 1: vegetation, 2: built_up, 3: bare_soil, 4: other
        class_map = np.full((h, w), 2, dtype=np.uint8)  # default built-up
        class_map[is_veg] = 1
        class_map[is_water] = 0
        class_map[is_soil] = 3
        class_map[is_margin] = 4



    for idx, cls_name in enumerate(classes):
        mask = class_map == idx
        summary = area_summary(mask, metadata, cls_name)
        class_areas[cls_name] = summary
        class_percentages[cls_name] = summary['percentage']

    return {
        'class_map': class_map,
        'classes': classes,
        'class_areas': class_areas,
        'class_percentages': class_percentages,
        'warnings': ["Rule-based classification without full indices"] if not has_indices else [],
        'method_description': "Unsupervised clustering with rule-based cluster assignment based on spectral indices."
    }

def perform_landcover_analysis(array: np.ndarray, metadata: RasterMetadata, n_clusters: int = 5) -> dict:
    spectral = extract_spectral_features(array, metadata.nodata)
    texture = extract_texture_features(array)
    features = np.hstack([spectral, texture])
    
    labels = cluster_image(features, n_clusters)
    result = assign_class_labels(labels, features, array, metadata)
    return result
