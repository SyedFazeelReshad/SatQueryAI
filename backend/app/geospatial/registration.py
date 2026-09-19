import cv2
import numpy as np
from app.geospatial.raster import RasterMetadata

def check_compatibility(meta_a: RasterMetadata, meta_b: RasterMetadata) -> tuple[bool, list[str]]:
    issues = []
    if meta_a.count != meta_b.count:
        issues.append(f"Band count mismatch: {meta_a.count} vs {meta_b.count}")
    if meta_a.crs != meta_b.crs:
        issues.append(f"CRS mismatch: {meta_a.crs} vs {meta_b.crs}")
    if abs(meta_a.resolution_x - meta_b.resolution_x) > 1e-4:
        issues.append("Resolution mismatch")
    return len(issues) == 0, issues

def register_images(reference: np.ndarray, target: np.ndarray) -> dict:
    warnings = []
    
    ref_gray = cv2.normalize(np.mean(reference, axis=2), None, 0, 255, cv2.NORM_MINMAX).astype(np.uint8)
    tgt_gray = cv2.normalize(np.mean(target, axis=2), None, 0, 255, cv2.NORM_MINMAX).astype(np.uint8)
    
    orb = cv2.ORB_create(5000)
    kp1, des1 = orb.detectAndCompute(ref_gray, None)
    kp2, des2 = orb.detectAndCompute(tgt_gray, None)
    
    if des1 is None or des2 is None or len(des1) < 10 or len(des2) < 10:
        warnings.append("Insufficient keypoints found.")
        return {
            'registered': target,
            'homography': None,
            'n_matches': 0,
            'quality_score': 0.0,
            'method': "ORB + RANSAC",
            'warnings': warnings,
            'success': False
        }
        
    matcher = cv2.BFMatcher(cv2.NORM_HAMMING, crossCheck=True)
    matches = matcher.match(des2, des1) # target to reference
    matches = sorted(matches, key=lambda x: x.distance)
    
    n_matches = len(matches)
    if n_matches < 10:
        warnings.append("Insufficient matches found.")
        return {
            'registered': target,
            'homography': None,
            'n_matches': n_matches,
            'quality_score': 0.0,
            'method': "ORB + RANSAC",
            'warnings': warnings,
            'success': False
        }
        
    src_pts = np.float32([kp2[m.queryIdx].pt for m in matches]).reshape(-1, 1, 2)
    dst_pts = np.float32([kp1[m.trainIdx].pt for m in matches]).reshape(-1, 1, 2)
    
    H, mask = cv2.findHomography(src_pts, dst_pts, cv2.RANSAC, 5.0)
    
    if H is None:
        warnings.append("Homography computation failed.")
        return {
            'registered': target,
            'homography': None,
            'n_matches': n_matches,
            'quality_score': 0.0,
            'method': "ORB + RANSAC",
            'warnings': warnings,
            'success': False
        }
        
    h, w, c = reference.shape
    registered = cv2.warpPerspective(target, H, (w, h))
    
    inliers = np.sum(mask) if mask is not None else 0
    quality_score = float(inliers / len(matches))
    
    return {
        'registered': registered,
        'homography': H.tolist(),
        'n_matches': int(inliers),
        'quality_score': quality_score,
        'method': "ORB + RANSAC",
        'warnings': warnings,
        'success': True
    }
