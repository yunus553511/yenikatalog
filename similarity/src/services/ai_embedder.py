"""AI-based image embedding extraction using ResNet50."""
import numpy as np
import torch
import torch.nn as nn
import torchvision.models as models
import torchvision.transforms as transforms
from PIL import Image
from typing import List
from src.core.logging_config import get_logger

logger = get_logger(__name__)


class AIEmbedder:
    """Extract deep learning embeddings from images using ensemble of models."""
    
    def __init__(self, model_name: str = "ensemble", device: str = "cpu"):
        """
        Initialize AI embedder with pre-trained model(s).
        
        Args:
            model_name: Name of the model to use ('resnet50', 'efficientnet', 'ensemble')
            device: Device to run inference on ('cpu' or 'cuda')
        """
        self.model_name = model_name
        self.device = torch.device(device)
        
        logger.info(f"Initializing {model_name} on {device}")
        
        if model_name == "ensemble":
            # Load multiple models for ensemble
            self.models = []
            self.embedding_dims = []
            
            # Model 1: ResNet50 (2048 dims)
            logger.info("Loading ResNet50...")
            resnet = models.resnet50(pretrained=True)
            resnet_features = nn.Sequential(*list(resnet.children())[:-1])
            self.models.append(resnet_features)
            self.embedding_dims.append(2048)
            
            # Model 2: EfficientNet-B0 (1280 dims)
            logger.info("Loading EfficientNet-B0...")
            try:
                efficientnet = models.efficientnet_b0(pretrained=True)
                efficientnet_features = nn.Sequential(*list(efficientnet.children())[:-1])
                self.models.append(efficientnet_features)
                self.embedding_dims.append(1280)
            except Exception as e:
                logger.warning(f"Failed to load EfficientNet: {e}")
            
            # Model 3: MobileNetV3 (960 dims) - lightweight alternative
            logger.info("Loading MobileNetV3...")
            try:
                mobilenet = models.mobilenet_v3_large(pretrained=True)
                mobilenet_features = nn.Sequential(*list(mobilenet.children())[:-1])
                self.models.append(mobilenet_features)
                self.embedding_dims.append(960)
            except Exception as e:
                logger.warning(f"Failed to load MobileNetV3: {e}")
            
            # Move all models to device and set to eval
            for model in self.models:
                model.to(self.device)
                model.eval()
            
            self.total_dims = sum(self.embedding_dims)
            logger.info(f"Ensemble initialized with {len(self.models)} models, total dims: {self.total_dims}")
            
        elif model_name == "resnet50":
            base_model = models.resnet50(pretrained=True)
            self.model = nn.Sequential(*list(base_model.children())[:-1])
            self.model.to(self.device)
            self.model.eval()
            self.models = [self.model]
            self.embedding_dims = [2048]
            self.total_dims = 2048
        else:
            raise ValueError(f"Unsupported model: {model_name}")
        
        # Define image preprocessing transforms
        self.transform = transforms.Compose([
            transforms.Resize(256),
            transforms.CenterCrop(224),
            transforms.ToTensor(),
            transforms.Normalize(
                mean=[0.485, 0.456, 0.406],  # ImageNet mean
                std=[0.229, 0.224, 0.225]     # ImageNet std
            )
        ])
        
        logger.info(f"{model_name} initialized successfully")
    
    def extract_embedding(self, image: np.ndarray) -> np.ndarray:
        """
        Extract embedding from a single image (ensemble or single model).
        
        Args:
            image: Input image as numpy array (H, W, C) in BGR format (OpenCV format)
            
        Returns:
            Embedding as numpy array (dims depend on model)
        """
        try:
            # Convert BGR to RGB
            if len(image.shape) == 3 and image.shape[2] == 3:
                image_rgb = image[:, :, ::-1]  # BGR to RGB
            else:
                # Handle grayscale
                image_rgb = image
            
            # Convert to PIL Image
            pil_image = Image.fromarray(image_rgb)
            
            # Apply transforms
            input_tensor = self.transform(pil_image)
            input_batch = input_tensor.unsqueeze(0)  # Add batch dimension
            
            # Move to device
            input_batch = input_batch.to(self.device)
            
            # Extract features from all models
            embeddings = []
            with torch.no_grad():
                for model in self.models:
                    embedding = model(input_batch)
                    embedding = embedding.squeeze().cpu().numpy()
                    
                    # Ensure 1D
                    if len(embedding.shape) > 1:
                        embedding = embedding.flatten()
                    
                    embeddings.append(embedding)
            
            # Concatenate all embeddings
            if len(embeddings) > 1:
                combined_embedding = np.concatenate(embeddings)
            else:
                combined_embedding = embeddings[0]
            
            return combined_embedding
            
        except Exception as e:
            logger.error(f"Failed to extract embedding: {e}")
            raise
    
    def batch_extract_embeddings(self, images: List[np.ndarray], batch_size: int = 32) -> np.ndarray:
        """
        Extract embeddings from multiple images in batches.
        
        Args:
            images: List of images as numpy arrays (H, W, C) in BGR format
            batch_size: Number of images to process in each batch
            
        Returns:
            Array of embeddings with shape (num_images, 2048)
        """
        num_images = len(images)
        embeddings = []
        
        logger.info(f"Extracting embeddings for {num_images} images in batches of {batch_size}")
        
        for i in range(0, num_images, batch_size):
            batch_images = images[i:i + batch_size]
            batch_tensors = []
            
            # Preprocess all images in batch
            for image in batch_images:
                try:
                    # Convert BGR to RGB
                    if len(image.shape) == 3 and image.shape[2] == 3:
                        image_rgb = image[:, :, ::-1]
                    else:
                        image_rgb = image
                    
                    # Convert to PIL and apply transforms
                    pil_image = Image.fromarray(image_rgb)
                    input_tensor = self.transform(pil_image)
                    batch_tensors.append(input_tensor)
                    
                except Exception as e:
                    logger.warning(f"Failed to preprocess image in batch: {e}")
                    # Add zero tensor as placeholder
                    batch_tensors.append(torch.zeros(3, 224, 224))
            
            # Stack into batch
            batch_tensor = torch.stack(batch_tensors).to(self.device)
            
            # Extract features
            with torch.no_grad():
                batch_embeddings = self.model(batch_tensor)
            
            # Convert to numpy and add to results
            batch_embeddings = batch_embeddings.squeeze().cpu().numpy()
            
            # Handle single image case (squeeze removes all dimensions)
            if len(batch_tensors) == 1:
                batch_embeddings = batch_embeddings.reshape(1, -1)
            
            embeddings.append(batch_embeddings)
            
            # Log progress
            processed = min(i + batch_size, num_images)
            logger.debug(f"Processed {processed}/{num_images} images")
        
        # Concatenate all batches
        all_embeddings = np.vstack(embeddings)
        
        logger.info(f"Extracted embeddings with shape {all_embeddings.shape}")
        
        return all_embeddings
