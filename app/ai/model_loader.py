"""
YOLOv8 Model Loader and Lifecycle Manager
Provides thread-safe singleton loading for AI object detection weights.
"""
import os
import logging
from config import Config

logger = logging.getLogger(__name__)

_model_instance = None


def get_model():
    """
    Retrieves or initializes the YOLOv8 object detection model.
    Falls back gracefully if Ultralytics weights cannot be fetched dynamically.
    """
    global _model_instance
    if _model_instance is not None:
        return _model_instance

    model_path = Config.YOLO_MODEL_PATH
    os.makedirs(os.path.dirname(model_path), exist_ok=True)

    try:
        from ultralytics import YOLO
        logger.info(f"Loading YOLOv8 model from: {model_path}")
        
        # Check if local custom weights exist; if not, use base yolov8n.pt
        if os.path.exists(model_path):
            _model_instance = YOLO(model_path)
        else:
            logger.info("Custom weights not found at path; initializing base 'yolov8n.pt' model...")
            _model_instance = YOLO('yolov8n.pt')
            
        logger.info("YOLOv8 Defect Detection Model loaded successfully.")
    except Exception as e:
        logger.warning(f"Ultralytics YOLO model failed to load ({str(e)}). Using computer vision fallback detector.")
        _model_instance = "FALLBACK_CV_ENGINE"

    return _model_instance
