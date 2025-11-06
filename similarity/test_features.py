from src.services.geometric_extractor import GeometricFeatureExtractor
import cv2
import numpy as np

ge = GeometricFeatureExtractor()

# Use numpy to handle Turkish characters
file_path = r'C:\Users\yunus.hezer\Desktop\YENİ BENZERLİK\YENİPNGLER-20251030T075723Z-1-001\YENİPNGLER\AP0001.png'
with open(file_path, 'rb') as f:
    file_bytes = np.frombuffer(f.read(), dtype=np.uint8)
    img = cv2.imdecode(file_bytes, cv2.IMREAD_COLOR)

if img is not None:
    print(f'Image shape: {img.shape}')
    features = ge.extract_features(img)
    print(f'Feature dimensions: {len(features)}')
    print(f'Feature range: [{features.min():.4f}, {features.max():.4f}]')
    print(f'Non-zero features: {np.count_nonzero(features)}')
    print(f'\nFirst 10 outer contour features: {features[:10]}')
    print(f'Inner contour features (10-22): {features[10:23]}')
else:
    print('Failed to load image')
