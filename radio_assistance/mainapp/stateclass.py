from typing import TypedDict, List, Dict, Any
from langchain_core.messages import BaseMessage
import torch
import numpy as np
from pathlib import Path


class AgentState(TypedDict):
    study_id: str
    user_id: int
    user_role: str

    dicom_path: List[Path]|None
    modality: str|None
    is_relevant: bool|None
    dicom_metadata: dict | None
    clinical_context: dict | None
    image_findings: dict | None
    case_summary: str | None
    
    draft_findings: str | None
    draft_impression: str | None
    final_report: str| None
    image_tensor: List[torch.Tensor]|None
    volume_tensor: torch.Tensor|None
    stop_reason: str|None
    
    # Vision model outputs
    model_predictions: List[Dict[str, Any]] | None  # Predictions from vision models
    gradcam_heatmaps: List[Dict[str, np.ndarray]] | None  # Grad-CAM heatmaps per image
    
    # RAG recommendations
    clinical_recommendations: Dict[str, Any] | None  # Generated recommendations from RAG pipeline
    
    # Error handling
    preprocessing_error: str | None  # Error during image preprocessing
    error: str | None  # General error message


