"""Debug geometric features for specific profiles."""
import cv2
import numpy as np
from src.services.geometric_extractor import GeometricFeatureExtractor

ge = GeometricFeatureExtractor()

# Test LR5201 (küçük çıkıntılı)
file1 = r'C:\Users\yunus.hezer\Desktop\YENİ BENZERLİK\YENİPNGLER-20251030T075723Z-1-001\YENİPNGLER\LR5201.png'
with open(file1, 'rb') as f:
    img1 = cv2.imdecode(np.frombuffer(f.read(), dtype=np.uint8), cv2.IMREAD_COLOR)

features1 = ge.extract_features(img1)

# Test GLR33-39 (büyük kare boşluklu)
file2 = r'C:\Users\yunus.hezer\Desktop\YENİ BENZERLİK\YENİPNGLER-20251030T075723Z-1-001\YENİPNGLER\GLR33-39.png'
with open(file2, 'rb') as f:
    img2 = cv2.imdecode(np.frombuffer(f.read(), dtype=np.uint8), cv2.IMREAD_COLOR)

features2 = ge.extract_features(img2)

print("=" * 60)
print("LR5201 (küçük çıkıntılı) Features:")
print("=" * 60)
print(f"Outer contour features (0-9): {features1[:10]}")
print(f"Inner contour features (10-22): {features1[10:23]}")
print(f"  - Number of inner contours: {features1[10]}")
print(f"  - Total inner area: {features1[11]}")
print(f"  - Largest inner area: {features1[12]}")
print(f"  - Inner area ratio: {features1[15]}")

print("\n" + "=" * 60)
print("GLR33-39 (büyük kare boşluklu) Features:")
print("=" * 60)
print(f"Outer contour features (0-9): {features2[:10]}")
print(f"Inner contour features (10-22): {features2[10:23]}")
print(f"  - Number of inner contours: {features2[10]}")
print(f"  - Total inner area: {features2[11]}")
print(f"  - Largest inner area: {features2[12]}")
print(f"  - Inner area ratio: {features2[15]}")

print("\n" + "=" * 60)
print("Inner Contour Feature Differences:")
print("=" * 60)
inner_diff = np.abs(features1[10:23] - features2[10:23])
print(f"Absolute differences: {inner_diff}")
print(f"Mean difference: {inner_diff.mean():.4f}")
print(f"Max difference: {inner_diff.max():.4f}")
