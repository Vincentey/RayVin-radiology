from radio_assistance.config.settings import settings
from pathlib import Path
import pydicom
from pydicom.errors import InvalidDicomError
import numpy as np
from PIL import Image
import torch
import torchvision.transforms as T
from typing import List, Union, Sequence, Optional, Tuple

# CT Window presets: (Window Level/Center, Window Width)
CT_WINDOWS = {
    "lung": (-600, 1500),
    "bone": (400, 1800),
    "soft_tissue": (40, 400),
    "brain": (40, 80),
    "liver": (60, 150),
    "mediastinum": (40, 350),
    "abdomen": (40, 400),
}

# Mapping from DICOM BodyPartExamined to appropriate default window
BODY_PART_TO_WINDOW = {
    "CHEST": "lung",
    "LUNG": "lung",
    "THORAX": "lung",
    "HEAD": "brain",
    "BRAIN": "brain",
    "SKULL": "bone",
    "SPINE": "bone",
    "CSPINE": "bone",
    "TSPINE": "bone",
    "LSPINE": "bone",
    "PELVIS": "soft_tissue",
    "ABDOMEN": "abdomen",
    "LIVER": "liver",
    "KIDNEY": "abdomen",
    "EXTREMITY": "bone",
    "LEG": "bone",
    "ARM": "bone",
    "HAND": "bone",
    "FOOT": "bone",
    "KNEE": "bone",
    "HIP": "bone",
    "SHOULDER": "bone",
}


class DicomProcessor():
    
    def __init__(self, dicom_path:Union[str, Path, Sequence[Union[str, Path]]]):

        if isinstance(dicom_path, (str, Path)):
            self.dicom_path = [Path(dicom_path)]
        else:
            self.dicom_path = [Path(p)for p in dicom_path]

    def ModalityRelevance (self)-> dict:

        """This function extracts the modality from each of the dicom_path in the list
        and check if all the dicom_paths point to the same modality.  
        """
        modality_set: List[str] = []
        for path in self.dicom_path:
            try:
                dicom_data= pydicom.dcmread(path, stop_before_pixels=True)
                modality= getattr(dicom_data, 'Modality', None)
            except InvalidDicomError:
                return {"is_relevant": False, "error": "Invalid DICOM file"}
            except Exception as e:
                return {"is_relevant": False, "error": f"Error reading DICOM: {e}"}
            
            modality_set.append(modality)

        print(modality_set)
        unique_modality= set(modality_set)
        print(unique_modality)

        if len(unique_modality) != 1 or None in unique_modality: 
            return {"is_relevant": False, "modality": "MIXED"}
        
        unique = unique_modality.pop()
        if str(unique).upper() in settings.approved_modality:
            return {"is_relevant": True, "modality": unique}
        else:
            return {"is_relevant": False, "modality": "MIXED"}
        
    def ExtractMetadata(self):

        metadata= pydicom.dcmread(self.dicom_path[0], stop_before_pixels=True)

        def get_data(attribute:str):
            return getattr(metadata, attribute, None)
            
        patient_name= get_data("PatientName")
        diagnosis= get_data("AdmittingDiagnosesDescription")
        patient_age= get_data("PatientAge")
        study_id= get_data("StudyID")

        required_data= {
            "patient_name": str(patient_name),
            "diagnosis": str(diagnosis),
            "patient_age": str(patient_age),
            "study_id": str(study_id)
        }

        return {"dicom_metadata": required_data}
    
    def ExtractCTWindowSettings(self) -> dict:
        """
        Extract CT window settings from DICOM metadata.
        
        Returns a dict with:
            - 'dicom_window': (center, width) tuple if stored in DICOM, else None
            - 'body_part': The body part examined (e.g., "CHEST", "HEAD")
            - 'suggested_window': Suggested window preset name based on body part
            - 'study_description': Study/Series description (may contain hints)
        """
        try:
            dcm = pydicom.dcmread(self.dicom_path[0], stop_before_pixels=True)
        except Exception as e:
            return {"error": f"Could not read DICOM: {e}"}
        
        # Try to get window values stored in DICOM
        dicom_window = None
        window_center = getattr(dcm, "WindowCenter", None)
        window_width = getattr(dcm, "WindowWidth", None)
        
        if window_center is not None and window_width is not None:
            # These can be single values or lists (multiple windows)
            if hasattr(window_center, '__iter__') and not isinstance(window_center, str):
                # Multiple windows stored - take the first one
                window_center = float(window_center[0])
                window_width = float(window_width[0])
            else:
                window_center = float(window_center)
                window_width = float(window_width)
            dicom_window = (window_center, window_width)
        
        # Get body part examined
        body_part = getattr(dcm, "BodyPartExamined", None)
        if body_part:
            body_part = str(body_part).upper().strip()
        
        # Get study/series description (may contain useful keywords)
        study_desc = getattr(dcm, "StudyDescription", "") or ""
        series_desc = getattr(dcm, "SeriesDescription", "") or ""
        description = f"{study_desc} {series_desc}".upper()
        
        # Determine suggested window from body part
        suggested_window = None
        if body_part and body_part in BODY_PART_TO_WINDOW:
            suggested_window = BODY_PART_TO_WINDOW[body_part]
        else:
            # Try to infer from description keywords
            if any(kw in description for kw in ["LUNG", "CHEST", "THORAX", "PULMONARY"]):
                suggested_window = "lung"
            elif any(kw in description for kw in ["BRAIN", "HEAD", "CRANIAL"]):
                suggested_window = "brain"
            elif any(kw in description for kw in ["BONE", "SPINE", "SKELETAL", "FRACTURE"]):
                suggested_window = "bone"
            elif any(kw in description for kw in ["LIVER", "HEPATIC"]):
                suggested_window = "liver"
            elif any(kw in description for kw in ["ABDOMEN", "ABDOMINAL"]):
                suggested_window = "abdomen"
            else:
                suggested_window = "soft_tissue"  # Safe default
        
        return {
            "dicom_window": dicom_window,
            "body_part": body_part,
            "suggested_window": suggested_window,
            "study_description": f"{study_desc} | {series_desc}".strip(" |")
        }
    
    def Image_extractor(self): 
        try:
            pixel_set = []
            for path in self.dicom_path:
                image = pydicom.dcmread(path)
                if not hasattr(image, "PixelData"):
                    return {"error": f"DICOM file has no pixel data: {path}"}
                
                # Get rescale parameters
                slope = float(getattr(image, "RescaleSlope", 1.0))
                intercept = float(getattr(image, "RescaleIntercept", 0.0))
                
                # Apply rescaling
                pixels = image.pixel_array.astype("float32") * slope + intercept
                
                # Handle photometric interpretation (invert if MONOCHROME1)
                photometric = getattr(image, "PhotometricInterpretation", "MONOCHROME2")
                if photometric == "MONOCHROME1":
                    pixels = pixels.max() - pixels  # Invert
                
                pixel_set.append(pixels)

        except InvalidDicomError:
            return {"error": "Invalid DICOM file. Cannot read image pixels."}
        except Exception as e:
            return {"error": f"Unexpected error while reading DICOM image: {e}"}
        
        tensor_list = []

        transform = T.Compose([
            T.Resize((224, 224)),
            T.ToTensor(),                       # → tensor in [0,1]
            T.Normalize(mean=[0.485, 0.456, 0.406],
                        std=[0.229, 0.224, 0.225]),
        ])
        
        for pixel_array in pixel_set: 
            # Use percentile-based normalization for robustness
            p1, p99 = np.percentile(pixel_array, [1, 99])
            if p99 > p1:
                pixel_norm = np.clip((pixel_array - p1) / (p99 - p1), 0, 1)
            else:
                pixel_norm = pixel_array * 0.0

            pixels_uint8 = (pixel_norm * 255).astype("uint8")
            img = Image.fromarray(pixels_uint8).convert("RGB")
            
            tensor = transform(img)  # shape: (3, 224, 224)
            tensor_list.append(tensor.unsqueeze(0))
            
        return {"image_tensor": tensor_list}

    def _apply_ct_window(self, volume: np.ndarray, window_center: float, window_width: float) -> np.ndarray:
        """
        Apply CT windowing to convert Hounsfield Units to display range [0, 1].
        
        Args:
            volume: 3D numpy array in Hounsfield Units
            window_center: Center of the window (Window Level)
            window_width: Width of the window
            
        Returns:
            Windowed volume normalized to [0, 1]
        """
        min_hu = window_center - (window_width / 2)
        max_hu = window_center + (window_width / 2)
        
        # Clip values outside the window
        volume_windowed = np.clip(volume, min_hu, max_hu)
        
        # Normalize to [0, 1]
        volume_normalized = (volume_windowed - min_hu) / (max_hu - min_hu)
        
        return volume_normalized

    def _apply_mri_normalization(self, volume: np.ndarray, 
                                  lower_percentile: float = 1.0, 
                                  upper_percentile: float = 99.0) -> np.ndarray:
        """
        Apply percentile-based normalization for MRI volumes.
        MRI has arbitrary intensity values, so we clip outliers and normalize.
        
        Args:
            volume: 3D numpy array
            lower_percentile: Lower percentile for clipping (default 1%)
            upper_percentile: Upper percentile for clipping (default 99%)
            
        Returns:
            Normalized volume in range [0, 1]
        """
        # Calculate percentile values
        p_low = np.percentile(volume, lower_percentile)
        p_high = np.percentile(volume, upper_percentile)
        
        # Clip outliers
        volume_clipped = np.clip(volume, p_low, p_high)
        
        # Normalize to [0, 1]
        if p_high > p_low:
            volume_normalized = (volume_clipped - p_low) / (p_high - p_low)
        else:
            volume_normalized = volume_clipped * 0.0
            
        return volume_normalized

    def Image_extractor_3D(
        self, 
        target_depth: int = 64, 
        target_size: int = 224,
        ct_window: Optional[str] = None,
        custom_window: Optional[Tuple[float, float]] = None,
        mri_percentiles: Tuple[float, float] = (1.0, 99.0),
        auto_window: bool = True
    ):
        """
        Preprocess DICOM slices for 3D vision models (CT/MRI volumes).
        Automatically detects modality and applies appropriate normalization.
        
        Args:
            target_depth: Number of slices in the output volume (default 64)
            target_size: Height and width of each slice (default 224)
            ct_window: Preset CT window name ("lung", "bone", "soft_tissue", "brain", 
                       "liver", "mediastinum", "abdomen"). Only used for CT.
            custom_window: Custom (window_center, window_width) tuple. Overrides ct_window.
            mri_percentiles: (lower, upper) percentiles for MRI normalization (default 1%, 99%)
            auto_window: If True (default), automatically detect window from DICOM metadata
                         when ct_window and custom_window are not specified.
            
        Returns:
            dict with 'volume_tensor' of shape (1, 1, D, H, W), 'modality', and 
            'window_used' (for CT), or error tuple
        """
        try:
            slices_data = []
            detected_modality = None
            rescale_slope = 1.0
            rescale_intercept = 0.0
            
            for path in self.dicom_path:
                dcm = pydicom.dcmread(path)
                if not hasattr(dcm, "PixelData"):
                    return {"error": f"DICOM file has no pixel data: {path}"}
                
                # Detect modality from first slice
                if detected_modality is None:
                    detected_modality = getattr(dcm, "Modality", "UNKNOWN")
                    # Get rescale parameters for CT (to convert to Hounsfield Units)
                    rescale_slope = float(getattr(dcm, "RescaleSlope", 1.0))
                    rescale_intercept = float(getattr(dcm, "RescaleIntercept", 0.0))
                
                # Get slice position for sorting (use InstanceNumber as fallback)
                if hasattr(dcm, "ImagePositionPatient"):
                    slice_position = float(dcm.ImagePositionPatient[2])
                elif hasattr(dcm, "SliceLocation"):
                    slice_position = float(dcm.SliceLocation)
                elif hasattr(dcm, "InstanceNumber"):
                    slice_position = float(dcm.InstanceNumber)
                else:
                    slice_position = len(slices_data)  # fallback to order received
                    
                slices_data.append((slice_position, dcm.pixel_array))

        except InvalidDicomError:
            return {"error": "Invalid DICOM file. Cannot read image pixels."}
        except Exception as e:
            return {"error": f"Unexpected error while reading DICOM image: {e}"}

        # Sort slices by position to ensure correct anatomical order
        slices_data.sort(key=lambda x: x[0])
        pixel_arrays = [s[1] for s in slices_data]

        # Stack into 3D volume: (D, H, W)
        volume = np.stack(pixel_arrays, axis=0).astype("float32")

        # Apply modality-specific normalization
        window_used = None
        if detected_modality == "CT":
            # Convert to Hounsfield Units
            volume_hu = volume * rescale_slope + rescale_intercept
            
            # Determine window parameters (priority: custom_window > ct_window > auto-detect > default)
            if custom_window is not None:
                window_center, window_width = custom_window
                window_used = {"type": "custom", "center": window_center, "width": window_width}
            elif ct_window is not None and ct_window in CT_WINDOWS:
                window_center, window_width = CT_WINDOWS[ct_window]
                window_used = {"type": "preset", "name": ct_window, "center": window_center, "width": window_width}
            elif auto_window:
                # Auto-detect from DICOM metadata
                window_settings = self.ExtractCTWindowSettings()
                
                if window_settings.get("dicom_window"):
                    # Use window values stored in DICOM file
                    window_center, window_width = window_settings["dicom_window"]
                    window_used = {"type": "dicom", "center": window_center, "width": window_width,
                                   "body_part": window_settings.get("body_part")}
                elif window_settings.get("suggested_window"):
                    # Use suggested window based on body part
                    suggested = window_settings["suggested_window"]
                    window_center, window_width = CT_WINDOWS[suggested]
                    window_used = {"type": "inferred", "name": suggested, "center": window_center, 
                                   "width": window_width, "body_part": window_settings.get("body_part")}
                else:
                    # Fallback to soft tissue
                    window_center, window_width = CT_WINDOWS["soft_tissue"]
                    window_used = {"type": "default", "name": "soft_tissue", "center": window_center, "width": window_width}
            else:
                # auto_window=False and no window specified, use soft tissue
                window_center, window_width = CT_WINDOWS["soft_tissue"]
                window_used = {"type": "default", "name": "soft_tissue", "center": window_center, "width": window_width}
            
            volume_normalized = self._apply_ct_window(volume_hu, window_center, window_width)
            
        elif detected_modality == "MR":
            # MRI uses percentile-based normalization
            volume_normalized = self._apply_mri_normalization(
                volume, 
                lower_percentile=mri_percentiles[0],
                upper_percentile=mri_percentiles[1]
            )
        else:
            # Fallback: simple min-max normalization for unknown modalities
            min_val = np.min(volume)
            max_val = np.max(volume)
            if max_val > min_val:
                volume_normalized = (volume - min_val) / (max_val - min_val)
            else:
                volume_normalized = volume * 0.0

        # Resize volume to target dimensions (D, H, W) -> (target_depth, target_size, target_size)
        # First resize each slice spatially
        resized_slices = []
        for i in range(volume_normalized.shape[0]):
            slice_img = Image.fromarray((volume_normalized[i] * 255).astype("uint8"))
            slice_resized = slice_img.resize((target_size, target_size), Image.BILINEAR)
            resized_slices.append(np.array(slice_resized).astype("float32") / 255.0)
        
        volume_resized = np.stack(resized_slices, axis=0)  # (D, H, W)

        # Resample depth dimension using linear interpolation
        current_depth = volume_resized.shape[0]
        if current_depth != target_depth:
            # Create depth indices for interpolation
            original_indices = np.linspace(0, current_depth - 1, current_depth)
            target_indices = np.linspace(0, current_depth - 1, target_depth)
            
            # Interpolate along depth axis
            volume_resampled = np.zeros((target_depth, target_size, target_size), dtype="float32")
            for h in range(target_size):
                for w in range(target_size):
                    volume_resampled[:, h, w] = np.interp(
                        target_indices, original_indices, volume_resized[:, h, w]
                    )
        else:
            volume_resampled = volume_resized

        # Final normalization with mean and std (common for 3D medical imaging models)
        mean = 0.5
        std = 0.5
        volume_final = (volume_resampled - mean) / std

        # Convert to tensor: (1, 1, D, H, W) - batch, channel, depth, height, width
        volume_tensor = torch.from_numpy(volume_final).float()
        volume_tensor = volume_tensor.unsqueeze(0).unsqueeze(0)  # Add batch and channel dims

        result = {"volume_tensor": volume_tensor, "modality": detected_modality}
        if window_used:
            result["window_used"] = window_used
        return result

    def guardrail(self):
        """
        Validate CT/MRI series for 3D processing.
        
        Requirements:
        - All slices must belong to the same series (SeriesInstanceUID)
        - Minimum 5 slices for meaningful 3D analysis
        """
        slice_count = len(self.dicom_path)

        if slice_count < 5:
            return {
                "is_relevant": False,
                "stop_reason": f"Insufficient slices for 3D analysis. Got {slice_count}, need at least 5."
            }

        series_uids = []
        for path in self.dicom_path:
            try:
                metadata = pydicom.dcmread(path, stop_before_pixels=True)
                instance_uid = getattr(metadata, "SeriesInstanceUID", None)
                series_uids.append(instance_uid)
            except Exception as e:
                return {
                    "is_relevant": False,
                    "stop_reason": f"Error reading DICOM metadata: {e}"
                }
        
        unique_uids = set(series_uids)

        if None in unique_uids:
            return {
                "is_relevant": False,
                "stop_reason": "Missing SeriesInstanceUID in one or more DICOM files."
            }
        
        if len(unique_uids) != 1:
            return {
                "is_relevant": False,
                "stop_reason": f"Multiple series detected ({len(unique_uids)}). Please upload slices from a single series."
            }

        return {"is_relevant": True, "slice_count": slice_count}
            
        

  








        
    

        

        
        





    
        

    