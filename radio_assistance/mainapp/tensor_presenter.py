"""
Tensor Presenter Module

This module contains classes for presenting preprocessed medical image tensors
to vision models for inference and interpretability analysis.
Uses TorchXRayVision for verified, well-trained chest X-ray models.
"""

import torch
import torch.nn as nn
import torch.nn.functional as F
import torchxrayvision as xrv
import numpy as np
import matplotlib.pyplot as plt
from PIL import Image
from typing import List, Dict, Optional, Tuple, Union
from pathlib import Path


class GradCAM:
    """
    Gradient-weighted Class Activation Mapping (Grad-CAM) implementation.
    Generates visual explanations for CNN predictions.
    """
    
    def __init__(self, model: nn.Module, target_layer: nn.Module):
        """
        Initialize Grad-CAM.
        
        Args:
            model: The neural network model
            target_layer: The convolutional layer to use for Grad-CAM
        """
        self.model = model
        self.target_layer = target_layer
        self.gradients = None
        self.activations = None
        
        # Register hooks
        self._register_hooks()
    
    def _register_hooks(self):
        """Register forward and backward hooks on the target layer."""
        
        def forward_hook(module, input, output):
            self.activations = output.detach()
        
        def backward_hook(module, grad_input, grad_output):
            self.gradients = grad_output[0].detach()
        
        self.target_layer.register_forward_hook(forward_hook)
        self.target_layer.register_full_backward_hook(backward_hook)
    
    def generate(
        self, 
        input_tensor: torch.Tensor, 
        target_class: Optional[int] = None
    ) -> Tuple[np.ndarray, int, float]:
        """
        Generate Grad-CAM heatmap for the input tensor.
        
        Args:
            input_tensor: Input image tensor of shape (1, C, H, W)
            target_class: Target class index for Grad-CAM. If None, uses predicted class.
            
        Returns:
            Tuple of (heatmap, predicted_class, confidence):
                - heatmap: numpy array of shape (H, W) with values in [0, 1]
                - predicted_class: the class index used for Grad-CAM
                - confidence: model confidence for that class
        """
        self.model.eval()
        
        # Forward pass
        output = self.model(input_tensor)
        
        # Get prediction info
        probabilities = torch.sigmoid(output) if output.min() < 0 else output
        
        if target_class is None:
            target_class = output.argmax(dim=1).item()
        
        confidence = probabilities[0, target_class].item()
        
        # Backward pass for target class
        self.model.zero_grad()
        one_hot = torch.zeros_like(output)
        one_hot[0, target_class] = 1
        output.backward(gradient=one_hot, retain_graph=True)
        
        # Generate heatmap
        # Global average pooling of gradients
        weights = self.gradients.mean(dim=(2, 3), keepdim=True)
        
        # Weighted combination of activation maps
        cam = (weights * self.activations).sum(dim=1, keepdim=True)
        
        # ReLU to keep only positive contributions
        cam = F.relu(cam)
        
        # Resize to input size
        cam = F.interpolate(
            cam, 
            size=(input_tensor.shape[2], input_tensor.shape[3]), 
            mode='bilinear', 
            align_corners=False
        )
        
        # Normalize to [0, 1]
        cam = cam.squeeze().cpu().numpy()
        if cam.max() > 0:
            cam = (cam - cam.min()) / (cam.max() - cam.min())
        
        return cam, target_class, confidence


class TensorPresenter:
    """
    Handles presentation of preprocessed medical image tensors to vision models.
    Uses TorchXRayVision for verified, well-trained models.
    """
    
    def __init__(
        self, 
        device: Optional[str] = None,
        model_name: str = "densenet121-res224-all"
    ):
        """
        Initialize TensorPresenter with TorchXRayVision model.
        
        Args:
            device: Device to use ('cuda', 'cpu', or None for auto-detect)
            model_name: TorchXRayVision model name. Options:
                - "densenet121-res224-all" (default, trained on multiple datasets)
                - "densenet121-res224-nih" (trained on NIH ChestX-ray14)
                - "densenet121-res224-chex" (trained on CheXpert)
                - "densenet121-res224-mimic_ch" (trained on MIMIC-CXR)
                - "densenet121-res224-mimic_nb" (MIMIC with no uncertain)
                - "densenet121-res224-pc" (trained on PadChest)
        """
        if device is None:
            self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        else:
            self.device = torch.device(device)
        
        self.model_name = model_name
        
        # Lazy loading - models initialized on first use
        self._model = None
        self._gradcam = None
    
    def _load_model(self) -> nn.Module:
        """
        Load TorchXRayVision model with verified pretrained weights.
        
        Returns:
            Loaded model
        """
        print(f"Loading TorchXRayVision model: {self.model_name}")
        
        # Load the model - weights are downloaded automatically
        model = xrv.models.DenseNet(weights=self.model_name)
        model = model.to(self.device)
        model.eval()
        
        print(f"Model loaded successfully. Pathologies: {model.pathologies}")
        
        return model
    
    def _get_model_and_gradcam(self) -> Tuple[nn.Module, GradCAM]:
        """Get or initialize model and Grad-CAM."""
        if self._model is None:
            self._model = self._load_model()
            # Target the last dense block for Grad-CAM
            target_layer = self._model.features.denseblock4
            self._gradcam = GradCAM(self._model, target_layer)
        
        return self._model, self._gradcam
    
    def _preprocess_for_xrv(self, tensor: torch.Tensor) -> torch.Tensor:
        """
        Preprocess tensor for TorchXRayVision models.
        XRV expects: single channel, 224x224, normalized to [-1024, 1024] range
        
        Args:
            tensor: Input tensor from DicomProcessor (3, 224, 224) normalized with ImageNet stats
            
        Returns:
            Tensor ready for XRV model (1, 1, 224, 224)
        """
        # If tensor has batch dimension, work with it
        if tensor.dim() == 4:
            tensor = tensor.squeeze(0)  # Remove batch dim temporarily
        
        # Convert from ImageNet normalized RGB back to [0, 1] grayscale
        # Reverse ImageNet normalization
        mean = torch.tensor([0.485, 0.456, 0.406]).view(3, 1, 1).to(tensor.device)
        std = torch.tensor([0.229, 0.224, 0.225]).view(3, 1, 1).to(tensor.device)
        tensor_denorm = tensor * std + mean
        
        # Convert RGB to grayscale (take mean across channels)
        gray = tensor_denorm.mean(dim=0, keepdim=True)  # (1, 224, 224)
        
        # XRV expects values in [-1024, 1024] range (like Hounsfield units)
        # Scale from [0, 1] to [-1024, 1024]
        xrv_tensor = (gray - 0.5) * 2048  # Maps [0,1] to [-1024, 1024]
        
        # Add batch dimension
        xrv_tensor = xrv_tensor.unsqueeze(0)  # (1, 1, 224, 224)
        
        return xrv_tensor
    
    def xray_densenet_gradcam(
        self,
        image_tensors: List[torch.Tensor],
        threshold: float = 0.5,
        top_k: Optional[int] = 5,
        generate_heatmaps: bool = True
    ) -> Dict:
        """
        Present X-ray tensors to TorchXRayVision DenseNet and generate Grad-CAM heatmaps.
        
        Args:
            image_tensors: List of image tensors from DicomProcessor.Image_extractor().
                          Each tensor should be of shape (1, 3, 224, 224).
            threshold: Probability threshold for positive predictions (default 0.5)
            top_k: Return top K predictions per image. If None, returns all above threshold.
            generate_heatmaps: Whether to generate Grad-CAM heatmaps (default True)
            
        Returns:
            Dictionary containing:
                - 'predictions': List of prediction dicts per image
                - 'heatmaps': List of dicts per image (if generate_heatmaps=True)
                - 'device': Device used for inference
                - 'model': Model name used
        """
        model, gradcam = self._get_model_and_gradcam()
        pathology_labels = model.pathologies
        
        all_predictions = []
        all_heatmaps = []
        
        for tensor in image_tensors:
            # Ensure tensor is on correct device
            if tensor.dim() == 3:
                tensor = tensor.unsqueeze(0)
            tensor = tensor.to(self.device)
            
            # Preprocess for TorchXRayVision
            xrv_tensor = self._preprocess_for_xrv(tensor)
            
            # Forward pass
            with torch.no_grad():
                output = model(xrv_tensor)
            
            # XRV outputs logits, apply sigmoid for probabilities
            probabilities = torch.sigmoid(output).squeeze().cpu().numpy()
            
            # Build probability dict
            prob_dict = {
                label: float(prob) 
                for label, prob in zip(pathology_labels, probabilities)
            }
            
            # Find positive findings (above threshold)
            positive_findings = [
                label for label, prob in prob_dict.items() 
                if prob >= threshold
            ]
            
            # Get top K predictions
            sorted_predictions = sorted(
                prob_dict.items(), 
                key=lambda x: x[1], 
                reverse=True
            )
            
            if top_k is not None:
                top_predictions = sorted_predictions[:top_k]
            else:
                top_predictions = [p for p in sorted_predictions if p[1] >= threshold]
            
            prediction_result = {
                'probabilities': prob_dict,
                'positive_findings': positive_findings,
                'top_predictions': top_predictions
            }
            all_predictions.append(prediction_result)
            
            # Generate Grad-CAM heatmaps for positive findings
            if generate_heatmaps:
                heatmap_dict = {}
                
                # Generate heatmaps for top predictions
                findings_for_heatmap = [label for label, _ in top_predictions[:5]]
                
                for finding in findings_for_heatmap:
                    if finding in pathology_labels:
                        class_idx = list(pathology_labels).index(finding)
                        
                        # Need gradient computation for Grad-CAM
                        xrv_tensor_grad = xrv_tensor.clone().requires_grad_(True)
                        heatmap, _, _ = gradcam.generate(xrv_tensor_grad, target_class=class_idx)
                        heatmap_dict[finding] = heatmap
                
                all_heatmaps.append(heatmap_dict)
        
        result = {
            'predictions': all_predictions,
            'device': str(self.device),
            'model': self.model_name
        }
        
        if generate_heatmaps:
            result['heatmaps'] = all_heatmaps
        
        return result
    
    def overlay_heatmap(
        self,
        original_image: np.ndarray,
        heatmap: np.ndarray,
        alpha: float = 0.4,
        colormap: str = 'jet'
    ) -> np.ndarray:
        """
        Overlay Grad-CAM heatmap on the original image.
        
        Args:
            original_image: Original image as numpy array (H, W) or (H, W, 3)
            heatmap: Grad-CAM heatmap as numpy array (H, W) with values in [0, 1]
            alpha: Transparency of heatmap overlay (default 0.4)
            colormap: Matplotlib colormap name (default 'jet')
            
        Returns:
            Overlay image as numpy array (H, W, 3) with values in [0, 255]
        """
        # Ensure original is RGB
        if original_image.ndim == 2:
            original_rgb = np.stack([original_image] * 3, axis=-1)
        else:
            original_rgb = original_image
        
        # Normalize original to [0, 255]
        if original_rgb.max() <= 1.0:
            original_rgb = (original_rgb * 255).astype(np.uint8)
        
        # Resize heatmap to match original
        if heatmap.shape != original_rgb.shape[:2]:
            heatmap_pil = Image.fromarray((heatmap * 255).astype(np.uint8))
            heatmap_pil = heatmap_pil.resize(
                (original_rgb.shape[1], original_rgb.shape[0]), 
                Image.BILINEAR
            )
            heatmap = np.array(heatmap_pil) / 255.0
        
        # Apply colormap
        cmap = plt.get_cmap(colormap)
        heatmap_colored = cmap(heatmap)[:, :, :3]  # Remove alpha channel
        heatmap_colored = (heatmap_colored * 255).astype(np.uint8)
        
        # Blend images
        overlay = (
            (1 - alpha) * original_rgb.astype(np.float32) + 
            alpha * heatmap_colored.astype(np.float32)
        )
        overlay = np.clip(overlay, 0, 255).astype(np.uint8)
        
        return overlay
