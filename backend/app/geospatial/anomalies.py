import numpy as np

def detect_statistical_anomalies(array: np.ndarray, threshold_sigma: float = 3.0) -> dict:
    warnings = []
    h, w, c = array.shape
    anomalies_mask = np.zeros((h, w), dtype=bool)
    
    band_stats = []
    for i in range(c):
        band = array[:, :, i]
        mean = np.nanmean(band)
        std = np.nanstd(band)
        if std > 0:
            z_score = np.abs((band - mean) / std)
            band_anomalies = z_score > threshold_sigma
            anomalies_mask |= band_anomalies
        else:
            warnings.append(f"Band {i} has 0 standard deviation, skipping anomaly check.")
            
        band_stats.append({
            'mean': float(mean),
            'std': float(std),
            'anomalies_count': int(np.sum(band_anomalies)) if std > 0 else 0
        })
        
    return {
        'anomalies_mask': anomalies_mask,
        'total_anomalies': int(np.sum(anomalies_mask)),
        'band_stats': band_stats,
        'warnings': warnings
    }
