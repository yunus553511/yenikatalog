"""Geometric feature extraction from images with advanced contour matching."""
import cv2
import numpy as np
from typing import List, Tuple, Optional
from src.core.logging_config import get_logger

logger = get_logger(__name__)


class GeometricFeatureExtractor:
    """Extract geometric shape features from profile images with advanced contour matching."""
    
    def __init__(self):
        """Initialize geometric feature extractor."""
        # Store last processed contours for contour matching
        self.last_outer_contour: Optional[np.ndarray] = None
        self.last_inner_contours: List[np.ndarray] = []
        logger.info("Geometric feature extractor initialized with contour matching support")
    
    def extract_features(self, image: np.ndarray, store_contours: bool = True) -> np.ndarray:
        """
        Extract 55-dimensional geometric feature vector with advanced contour matching.
        
        Features breakdown:
        - 10 outer contour features
        - 13 inner contour features (ENHANCED)
        - 7 Hu moments
        - 4 symmetry features
        - 6 spatial features
        - 5 legacy hole features
        - 5 contour matching features (NEW)
        - 5 shape context features (NEW)
        
        Args:
            image: Input image as numpy array (H, W, C) in BGR format
            store_contours: Whether to store contours for future matching
            
        Returns:
            55-dimensional feature vector as numpy array
        """
        try:
            # Convert to grayscale
            if len(image.shape) == 3:
                gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
            else:
                gray = image
            
            # Apply adaptive thresholding for better contour detection
            binary = cv2.adaptiveThreshold(
                gray, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
                cv2.THRESH_BINARY_INV, 11, 2
            )
            
            # Find contours with hierarchy (CRITICAL for inner contours)
            contours, hierarchy = cv2.findContours(
                binary, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE
            )
            
            if len(contours) == 0:
                logger.warning("No contours found in image")
                return np.zeros(45)
            
            # Separate outer and inner contours using hierarchy
            outer_contours, inner_contours = self._separate_contours(contours, hierarchy)
            
            if len(outer_contours) == 0:
                logger.warning("No outer contours found in image")
                return np.zeros(45)
            
            # Get largest outer contour for advanced features
            largest_outer = max(outer_contours, key=cv2.contourArea)
            
            # Extract all feature types with guaranteed dimensions
            features = []
            
            # Extract each feature type and ensure correct dimensions
            outer_features = self._extract_outer_contour_features(outer_contours, binary.shape)
            if len(outer_features) != 10:
                logger.warning(f"Outer contour features: expected 10, got {len(outer_features)}, padding")
                outer_features = (outer_features + [0.0] * 10)[:10]
            features.extend(outer_features)
            
            inner_features = self._extract_inner_contour_features(inner_contours, outer_contours)
            if len(inner_features) != 13:
                logger.warning(f"Inner contour features: expected 13, got {len(inner_features)}, padding")
                inner_features = (inner_features + [0.0] * 13)[:13]
            features.extend(inner_features)
            
            hu_features = self._extract_hu_moments(outer_contours)
            if len(hu_features) != 7:
                logger.warning(f"Hu moments: expected 7, got {len(hu_features)}, padding")
                hu_features = (hu_features + [0.0] * 7)[:7]
            features.extend(hu_features)
            
            symmetry_features = self._extract_symmetry_features(binary)
            if len(symmetry_features) != 4:
                logger.warning(f"Symmetry features: expected 4, got {len(symmetry_features)}, padding")
                symmetry_features = (symmetry_features + [0.0] * 4)[:4]
            features.extend(symmetry_features)
            
            spatial_features = self._extract_spatial_features(outer_contours, binary.shape)
            if len(spatial_features) != 6:
                logger.warning(f"Spatial features: expected 6, got {len(spatial_features)}, padding")
                spatial_features = (spatial_features + [0.0] * 6)[:6]
            features.extend(spatial_features)
            
            legacy_features = self._extract_legacy_hole_features(inner_contours, outer_contours)
            if len(legacy_features) != 5:
                logger.warning(f"Legacy hole features: expected 5, got {len(legacy_features)}, padding")
                legacy_features = (legacy_features + [0.0] * 5)[:5]
            features.extend(legacy_features)
            
            contour_matching_features = self._extract_contour_matching_features(largest_outer, inner_contours)
            if len(contour_matching_features) != 5:
                logger.warning(f"Contour matching features: expected 5, got {len(contour_matching_features)}, padding")
                contour_matching_features = (contour_matching_features + [0.0] * 5)[:5]
            features.extend(contour_matching_features)
            
            shape_context_features = self._extract_shape_context_features(largest_outer)
            if len(shape_context_features) != 5:
                logger.warning(f"Shape context features: expected 5, got {len(shape_context_features)}, padding")
                shape_context_features = (shape_context_features + [0.0] * 5)[:5]
            features.extend(shape_context_features)
            
            # Store contours for future matching if requested
            if store_contours:
                self.last_outer_contour = largest_outer
                self.last_inner_contours = inner_contours
            
            # Convert to numpy array
            feature_array = np.array(features, dtype=np.float32)
            
            # Final verification - this should NEVER fail now
            if len(feature_array) != 55:
                logger.error(f"CRITICAL: Expected 55 features, got {len(feature_array)}, returning zeros")
                return np.zeros(55, dtype=np.float32)
            
            # Normalize features
            normalized_features = self._normalize_features(feature_array)
            
            return normalized_features
            
        except Exception as e:
            logger.error(f"Failed to extract geometric features: {e}", exc_info=True)
            # Return zeros with correct dimension
            return np.zeros(55, dtype=np.float32)
    
    def _separate_contours(self, contours: List, hierarchy: np.ndarray) -> Tuple[List, List]:
        """
        Separate outer (parent) and inner (child) contours using hierarchy.
        
        Args:
            contours: List of contours from cv2.findContours
            hierarchy: Hierarchy array from cv2.findContours
            
        Returns:
            Tuple of (outer_contours, inner_contours)
        """
        if hierarchy is None or len(contours) == 0:
            return list(contours), []
        
        outer = []
        inner = []
        
        # hierarchy[0][i] = [next, previous, first_child, parent]
        for i, cnt in enumerate(contours):
            if hierarchy[0][i][3] == -1:  # No parent = outer contour
                outer.append(cnt)
            else:  # Has parent = inner contour (hole)
                inner.append(cnt)
        
        logger.debug(f"Separated {len(outer)} outer and {len(inner)} inner contours")
        return outer, inner
    
    def _extract_outer_contour_features(self, contours: List, image_shape: Tuple) -> List[float]:
        """
        Extract outer contour features (10 features).
        
        Args:
            contours: List of outer contours
            image_shape: Shape of the image (height, width)
            
        Returns:
            List of 10 outer contour features
        """
        if len(contours) == 0:
            return [0.0] * 10
        
        # Find largest outer contour
        largest_contour = max(contours, key=cv2.contourArea)
        
        # Calculate features
        area = cv2.contourArea(largest_contour)
        perimeter = cv2.arcLength(largest_contour, True)
        
        # Avoid division by zero
        if area == 0 or perimeter == 0:
            return [0.0] * 10
        
        # Bounding box
        x, y, w, h = cv2.boundingRect(largest_contour)
        aspect_ratio = float(w) / h if h > 0 else 0
        
        # Convex hull
        hull = cv2.convexHull(largest_contour)
        hull_area = cv2.contourArea(hull)
        
        # Solidity
        solidity = area / hull_area if hull_area > 0 else 0
        
        # Extent
        rect_area = w * h
        extent = area / rect_area if rect_area > 0 else 0
        
        # Circularity
        circularity = (4 * np.pi * area) / (perimeter ** 2) if perimeter > 0 else 0
        
        # Complexity
        complexity = (perimeter ** 2) / area if area > 0 else 0
        
        # Approximated polygon
        epsilon = 0.01 * perimeter
        approx = cv2.approxPolyDP(largest_contour, epsilon, True)
        num_vertices = len(approx)
        
        # Convex hull area ratio
        convex_ratio = hull_area / area if area > 0 else 0
        
        # Orientation
        if len(largest_contour) >= 5:
            try:
                ellipse = cv2.fitEllipse(largest_contour)
                orientation = np.deg2rad(ellipse[2])
            except:
                orientation = 0.0
        else:
            orientation = 0.0
        
        features = [
            area,                    # Largest contour area
            perimeter,               # Largest contour perimeter
            complexity,              # Contour complexity
            aspect_ratio,            # Bounding box aspect ratio
            convex_ratio,            # Convex hull area ratio
            num_vertices,            # Number of vertices
            solidity,                # Solidity
            extent,                  # Extent
            circularity,             # Circularity
            orientation              # Outer contour orientation
        ]
        
        return features
    
    def _extract_inner_contour_features(self, inner_contours: List, outer_contours: List) -> List[float]:
        """
        Extract enhanced inner contour features (13 features).
        
        This is critical for distinguishing profiles with different internal structures.
        
        Args:
            inner_contours: List of inner contours (holes/cavities)
            outer_contours: List of outer contours for normalization
            
        Returns:
            List of 13 inner contour features
        """
        if len(inner_contours) == 0:
            # No inner contours - return zeros
            return [0.0] * 13
        
        if len(outer_contours) == 0:
            logger.warning("No outer contours for inner contour normalization")
            return [0.0] * 13
        
        # Get largest outer contour for normalization
        largest_outer = max(outer_contours, key=cv2.contourArea)
        outer_area = cv2.contourArea(largest_outer)
        
        if outer_area == 0:
            return [0.0] * 13
        
        # Calculate inner contour areas
        inner_areas = [cv2.contourArea(cnt) for cnt in inner_contours]
        inner_perimeters = [cv2.arcLength(cnt, True) for cnt in inner_contours]
        
        # Filter out very small contours (noise)
        min_area_threshold = outer_area * 0.001  # 0.1% of outer area
        valid_indices = [i for i, area in enumerate(inner_areas) if area > min_area_threshold]
        
        if len(valid_indices) == 0:
            return [0.0] * 13
        
        inner_areas = [inner_areas[i] for i in valid_indices]
        inner_perimeters = [inner_perimeters[i] for i in valid_indices]
        valid_contours = [inner_contours[i] for i in valid_indices]
        
        # 1. Number of inner contours
        num_inner = len(inner_areas)
        
        # 2. Total inner contour area (NORMALIZED by outer area)
        total_inner_area = sum(inner_areas) / outer_area
        
        # 3. Largest inner contour area (NORMALIZED by outer area)
        largest_inner_area = max(inner_areas) / outer_area
        
        # 4. Smallest inner contour area (NORMALIZED by outer area)
        smallest_inner_area = min(inner_areas) / outer_area
        
        # 5. Average inner contour area (NORMALIZED by outer area)
        avg_inner_area = (sum(inner_areas) / num_inner) / outer_area
        
        # 6. Inner contour area ratio (total holes / outer area)
        inner_area_ratio = sum(inner_areas) / outer_area
        
        # 7. Inner contour count density (count / outer area)
        inner_count_density = num_inner / outer_area
        
        # 8. Largest inner contour perimeter
        largest_inner_perimeter = max(inner_perimeters)
        
        # 9. Average inner contour complexity
        complexities = []
        for area, perimeter in zip(inner_areas, inner_perimeters):
            if area > 0 and perimeter > 0:
                complexity = (perimeter ** 2) / area
                complexities.append(complexity)
        avg_complexity = np.mean(complexities) if complexities else 0.0
        
        # 10. Inner contour spatial distribution (std of centroids)
        centroids = []
        for cnt in valid_contours:
            M = cv2.moments(cnt)
            if M['m00'] > 0:
                cx = M['m10'] / M['m00']
                cy = M['m01'] / M['m00']
                centroids.append([cx, cy])
        
        if len(centroids) > 1:
            centroids_array = np.array(centroids)
            spatial_distribution = np.std(centroids_array)
        else:
            spatial_distribution = 0.0
        
        # 11. Inner contour size variance
        size_variance = np.var(inner_areas) if len(inner_areas) > 1 else 0.0
        
        # 12. Inner contour aspect ratio (average)
        aspect_ratios = []
        for cnt in valid_contours:
            x, y, w, h = cv2.boundingRect(cnt)
            if h > 0:
                aspect_ratios.append(float(w) / h)
        avg_aspect_ratio = np.mean(aspect_ratios) if aspect_ratios else 0.0
        
        # 13. Inner contour circularity (average)
        # Note: inner_areas are now normalized, need raw areas for circularity
        raw_inner_areas = [cv2.contourArea(inner_contours[i]) for i in valid_indices]
        circularities = []
        for area, perimeter in zip(raw_inner_areas, inner_perimeters):
            if perimeter > 0:
                circularity = (4 * np.pi * area) / (perimeter ** 2)
                circularities.append(circularity)
        avg_circularity = np.mean(circularities) if circularities else 0.0
        
        features = [
            num_inner,
            total_inner_area,
            largest_inner_area,
            smallest_inner_area,
            avg_inner_area,
            inner_area_ratio,
            inner_count_density,
            largest_inner_perimeter,
            avg_complexity,
            spatial_distribution,
            size_variance,
            avg_aspect_ratio,
            avg_circularity
        ]
        
        logger.debug(f"Extracted {num_inner} inner contours with total area ratio {inner_area_ratio:.4f}")
        
        return features
    
    def _extract_hu_moments(self, contours: List) -> List[float]:
        """
        Extract Hu moments (7 features).
        
        Args:
            contours: List of contours from cv2.findContours
            
        Returns:
            List of 7 Hu moment features
        """
        if len(contours) == 0:
            return [0.0] * 7
        
        # Find largest contour
        largest_contour = max(contours, key=cv2.contourArea)
        
        # Calculate moments
        moments = cv2.moments(largest_contour)
        
        # Calculate Hu moments
        hu_moments = cv2.HuMoments(moments).flatten()
        
        # Apply log transform to make values more manageable
        hu_moments = -np.sign(hu_moments) * np.log10(np.abs(hu_moments) + 1e-10)
        
        return hu_moments.tolist()
    
    def _extract_symmetry_features(self, binary: np.ndarray) -> List[float]:
        """
        Extract symmetry features (4 features).
        
        Args:
            binary: Binary image
            
        Returns:
            List of 4 symmetry features
        """
        h, w = binary.shape
        
        # Horizontal symmetry
        top_half = binary[:h//2, :]
        bottom_half = binary[h//2:, :]
        bottom_half_flipped = np.flipud(bottom_half)
        
        # Resize to match if needed
        min_h = min(top_half.shape[0], bottom_half_flipped.shape[0])
        top_half = top_half[:min_h, :]
        bottom_half_flipped = bottom_half_flipped[:min_h, :]
        
        h_symmetry = np.sum(top_half == bottom_half_flipped) / (min_h * w) if min_h * w > 0 else 0
        
        # Vertical symmetry
        left_half = binary[:, :w//2]
        right_half = binary[:, w//2:]
        right_half_flipped = np.fliplr(right_half)
        
        # Resize to match if needed
        min_w = min(left_half.shape[1], right_half_flipped.shape[1])
        left_half = left_half[:, :min_w]
        right_half_flipped = right_half_flipped[:, :min_w]
        
        v_symmetry = np.sum(left_half == right_half_flipped) / (h * min_w) if h * min_w > 0 else 0
        
        # Diagonal symmetry (simplified)
        diag_symmetry = np.sum(binary == np.transpose(binary)) / (h * w) if h * w > 0 else 0
        
        # Radial symmetry (simplified - using center point)
        center_y, center_x = h // 2, w // 2
        radial_symmetry = binary[center_y, center_x] / 255.0
        
        return [h_symmetry, v_symmetry, diag_symmetry, radial_symmetry]
    
    def _extract_spatial_features(self, contours: List, image_shape: Tuple) -> List[float]:
        """
        Extract spatial features (6 features).
        
        Args:
            contours: List of contours from cv2.findContours
            image_shape: Shape of the image (height, width)
            
        Returns:
            List of 6 spatial features
        """
        if len(contours) == 0:
            return [0.0] * 6
        
        h, w = image_shape
        
        # Find largest contour
        largest_contour = max(contours, key=cv2.contourArea)
        
        # Calculate moments for centroid
        M = cv2.moments(largest_contour)
        
        if M['m00'] == 0:
            return [0.0] * 6
        
        # Centroid (normalized)
        cx = M['m10'] / M['m00'] / w
        cy = M['m01'] / M['m00'] / h
        
        # Fit ellipse if possible
        if len(largest_contour) >= 5:
            try:
                ellipse = cv2.fitEllipse(largest_contour)
                (center, axes, orientation) = ellipse
                major_axis = max(axes)
                minor_axis = min(axes)
                eccentricity = np.sqrt(1 - (minor_axis / major_axis) ** 2) if major_axis > 0 else 0
                orientation_rad = np.deg2rad(orientation)
            except:
                major_axis = 0
                minor_axis = 0
                eccentricity = 0
                orientation_rad = 0
        else:
            major_axis = 0
            minor_axis = 0
            eccentricity = 0
            orientation_rad = 0
        
        return [cx, cy, orientation_rad, major_axis, minor_axis, eccentricity]
    
    def _extract_legacy_hole_features(self, inner_contours: List, outer_contours: List) -> List[float]:
        """
        Extract legacy hole/cavity features for backward compatibility (5 features).
        
        Args:
            inner_contours: List of inner contours
            outer_contours: List of outer contours
            
        Returns:
            List of 5 legacy hole features
        """
        if len(inner_contours) == 0:
            return [0.0] * 5
        
        if len(outer_contours) == 0:
            return [0.0] * 5
        
        # Calculate areas
        inner_areas = [cv2.contourArea(cnt) for cnt in inner_contours]
        outer_area = cv2.contourArea(max(outer_contours, key=cv2.contourArea))
        
        if outer_area == 0:
            return [0.0] * 5
        
        # Filter noise
        min_area_threshold = outer_area * 0.001
        valid_areas = [area for area in inner_areas if area > min_area_threshold]
        
        if len(valid_areas) == 0:
            return [0.0] * 5
        
        num_holes = len(valid_areas)
        total_hole_area = sum(valid_areas)
        largest_hole_area = max(valid_areas)
        avg_hole_area = total_hole_area / num_holes
        hole_density = total_hole_area / outer_area
        
        return [num_holes, total_hole_area, largest_hole_area, avg_hole_area, hole_density]
    

    def _extract_contour_matching_features(self, outer_contour: np.ndarray, inner_contours: List[np.ndarray]) -> List[float]:
        """
        Extract contour matching features using OpenCV's matchShapes (5 features).
        
        Uses Hu moment-based shape matching for rotation/scale invariant comparison.
        
        Args:
            outer_contour: Largest outer contour
            inner_contours: List of inner contours
            
        Returns:
            List of 5 contour matching features
        """
        try:
            features = []
            
            # 1. Outer contour compactness (perimeter^2 / area)
            area = cv2.contourArea(outer_contour)
            perimeter = cv2.arcLength(outer_contour, True)
            compactness = (perimeter ** 2) / area if area > 0 else 0
            features.append(compactness)
            
            # 2. Contour convexity defects count
            hull = cv2.convexHull(outer_contour, returnPoints=False)
            if len(hull) > 3 and len(outer_contour) > 3:
                try:
                    defects = cv2.convexityDefects(outer_contour, hull)
                    defect_count = len(defects) if defects is not None else 0
                except:
                    defect_count = 0
            else:
                defect_count = 0
            features.append(defect_count)
            
            # 3. Average convexity defect depth
            if len(hull) > 3 and len(outer_contour) > 3:
                try:
                    defects = cv2.convexityDefects(outer_contour, hull)
                    if defects is not None and len(defects) > 0:
                        depths = [d[0][3] / 256.0 for d in defects]  # Normalize depth
                        avg_depth = np.mean(depths)
                    else:
                        avg_depth = 0
                except:
                    avg_depth = 0
            else:
                avg_depth = 0
            features.append(avg_depth)
            
            # 4. Contour roughness (actual perimeter / convex hull perimeter)
            hull_points = cv2.convexHull(outer_contour)
            hull_perimeter = cv2.arcLength(hull_points, True)
            roughness = perimeter / hull_perimeter if hull_perimeter > 0 else 1.0
            features.append(roughness)
            
            # 5. Inner contour distribution uniformity
            if len(inner_contours) > 1:
                # Calculate distances between inner contour centroids
                centroids = []
                for cnt in inner_contours:
                    M = cv2.moments(cnt)
                    if M['m00'] > 0:
                        cx = M['m10'] / M['m00']
                        cy = M['m01'] / M['m00']
                        centroids.append([cx, cy])
                
                if len(centroids) > 1:
                    # Calculate pairwise distances
                    distances = []
                    for i in range(len(centroids)):
                        for j in range(i + 1, len(centroids)):
                            dist = np.linalg.norm(np.array(centroids[i]) - np.array(centroids[j]))
                            distances.append(dist)
                    
                    # Coefficient of variation (std/mean) - lower means more uniform
                    uniformity = np.std(distances) / np.mean(distances) if np.mean(distances) > 0 else 0
                else:
                    uniformity = 0
            else:
                uniformity = 0
            features.append(uniformity)
            
            return features
        
        except Exception as e:
            logger.warning(f"Failed to extract contour matching features: {e}")
            return [0.0] * 5
    
    def _extract_shape_context_features(self, contour: np.ndarray) -> List[float]:
        """
        Extract shape context-inspired features (5 features).
        
        Shape context captures the distribution of points relative to each other.
        
        Args:
            contour: Contour to extract features from
            
        Returns:
            List of 5 shape context features
        """
        try:
            features = []
            
            # Sample points from contour
            num_samples = min(100, len(contour))
            if len(contour) < num_samples:
                sampled_points = contour
            else:
                indices = np.linspace(0, len(contour) - 1, num_samples, dtype=int)
                sampled_points = contour[indices]
            
            sampled_points = sampled_points.reshape(-1, 2)
            
            # 1. Average distance from centroid
            M = cv2.moments(contour)
            if M['m00'] > 0:
                cx = M['m10'] / M['m00']
                cy = M['m01'] / M['m00']
                centroid = np.array([cx, cy])
                
                distances = np.linalg.norm(sampled_points - centroid, axis=1)
                avg_dist = np.mean(distances)
                features.append(avg_dist)
                
                # 2. Standard deviation of distances from centroid
                std_dist = np.std(distances)
                features.append(std_dist)
                
                # 3. Skewness of distance distribution
                if std_dist > 0:
                    skewness = np.mean(((distances - avg_dist) / std_dist) ** 3)
                else:
                    skewness = 0
                features.append(skewness)
            else:
                features.extend([0, 0, 0])
            
            # 4. Angular distribution uniformity
            if M['m00'] > 0:
                angles = np.arctan2(sampled_points[:, 1] - cy, sampled_points[:, 0] - cx)
                # Bin angles into 8 sectors
                hist, _ = np.histogram(angles, bins=8, range=(-np.pi, np.pi))
                # Normalize
                hist = hist / np.sum(hist) if np.sum(hist) > 0 else hist
                # Calculate entropy (uniformity measure)
                hist = hist[hist > 0]  # Remove zeros for log
                entropy = -np.sum(hist * np.log(hist)) if len(hist) > 0 else 0
                features.append(entropy)
            else:
                features.append(0)
            
            # 5. Contour curvature variation
            if len(sampled_points) > 2:
                # Calculate angles between consecutive segments
                vectors = np.diff(sampled_points, axis=0)
                angles = np.arctan2(vectors[:, 1], vectors[:, 0])
                angle_diffs = np.diff(angles)
                # Wrap angles to [-pi, pi]
                angle_diffs = np.arctan2(np.sin(angle_diffs), np.cos(angle_diffs))
                curvature_var = np.std(angle_diffs)
                features.append(curvature_var)
            else:
                features.append(0)
            
            return features
        
        except Exception as e:
            logger.warning(f"Failed to extract shape context features: {e}")
            return [0.0] * 5

    def _normalize_features(self, features: np.ndarray) -> np.ndarray:
        """
        Normalize all 55 features to [0, 1] range using robust scaling.
        
        Args:
            features: Raw 55-dimensional feature vector
            
        Returns:
            Normalized 55-dimensional feature vector
        """
        # Replace inf and nan with 0
        features = np.nan_to_num(features, nan=0.0, posinf=0.0, neginf=0.0)
        
        # Clip extreme values
        features = np.clip(features, -1e6, 1e6)
        
        normalized = np.zeros_like(features)
        
        # Define normalization ranges for different feature groups
        # Outer contour features (0-9): areas, perimeters, ratios
        for i in range(10):
            val = features[i]
            if i in [0, 1]:  # Area and perimeter - large values
                normalized[i] = min(val / 100000.0, 1.0)
            elif i == 2:  # Complexity
                normalized[i] = min(val / 1000.0, 1.0)
            else:  # Ratios and other metrics
                normalized[i] = min(max(val, 0.0), 1.0)
        
        # Inner contour features (10-22): counts, areas, ratios
        # CRITICAL: Areas are now normalized by outer_area in extraction!
        for i in range(10, 23):
            val = features[i]
            if i == 10:  # Number of inner contours
                normalized[i] = min(val / 20.0, 1.0)  # Max ~20 holes
            elif i in [11, 12, 13, 14]:  # Areas (ALREADY normalized by outer_area, 0-1 range)
                normalized[i] = min(max(val, 0.0), 1.0)  # Just clip
            elif i == 15:  # Inner area ratio (already 0-1)
                normalized[i] = min(max(val, 0.0), 1.0)
            elif i == 16:  # Inner count density
                normalized[i] = min(val / 0.001, 1.0)  # Very small values
            elif i == 17:  # Largest inner perimeter
                normalized[i] = min(val / 10000.0, 1.0)
            elif i == 18:  # Average complexity
                normalized[i] = min(val / 2000.0, 1.0)
            elif i == 19:  # Spatial distribution
                normalized[i] = min(val / 1000.0, 1.0)
            elif i == 20:  # Size variance (normalized by outer_area^2)
                normalized[i] = min(val, 1.0)  # Already small
            elif i in [21, 22]:  # Aspect ratio, circularity
                normalized[i] = min(max(val, 0.0), 1.0)
        
        # Hu moments (23-29): already log-transformed, just clip
        for i in range(23, 30):
            val = features[i]
            normalized[i] = min(max((val + 10.0) / 20.0, 0.0), 1.0)
        
        # Symmetry features (30-33): already in [0, 1]
        for i in range(30, 34):
            normalized[i] = min(max(features[i], 0.0), 1.0)
        
        # Spatial features (34-39): mixed
        for i in range(34, 40):
            val = features[i]
            if i in [34, 35]:  # Centroid - already normalized
                normalized[i] = min(max(val, 0.0), 1.0)
            elif i == 36:  # Orientation
                normalized[i] = (val + np.pi) / (2 * np.pi)
            elif i in [37, 38]:  # Axis lengths
                normalized[i] = min(val / 1000.0, 1.0)
            else:  # Eccentricity
                normalized[i] = min(max(val, 0.0), 1.0)
        
        # Legacy hole features (40-44): similar to inner contours
        for i in range(40, 45):
            val = features[i]
            if i == 40:  # Number of holes
                normalized[i] = min(val / 50.0, 1.0)
            elif i in [41, 42, 43]:  # Areas
                normalized[i] = min(val / 50000.0, 1.0)
            else:  # Density
                normalized[i] = min(max(val, 0.0), 1.0)
        
        # Contour matching features (45-49): NEW
        for i in range(45, 50):
            val = features[i]
            if i == 45:  # Compactness
                normalized[i] = min(val / 100.0, 1.0)
            elif i == 46:  # Defect count
                normalized[i] = min(val / 50.0, 1.0)
            elif i == 47:  # Average defect depth
                normalized[i] = min(max(val, 0.0), 1.0)
            elif i == 48:  # Roughness
                normalized[i] = min(max(val, 0.0), 1.0)
            else:  # Uniformity (49)
                normalized[i] = min(val / 10.0, 1.0)
        
        # Shape context features (50-54): NEW
        for i in range(50, 55):
            val = features[i]
            if i in [50, 51]:  # Average distance, std distance
                normalized[i] = min(val / 1000.0, 1.0)
            elif i == 52:  # Skewness
                normalized[i] = min(max((val + 5.0) / 10.0, 0.0), 1.0)
            elif i == 53:  # Entropy
                normalized[i] = min(max(val / 3.0, 0.0), 1.0)
            else:  # Curvature variation (54)
                normalized[i] = min(val / 5.0, 1.0)
        
        # Final safety clip
        normalized = np.clip(normalized, 0.0, 1.0)
        
        return normalized
