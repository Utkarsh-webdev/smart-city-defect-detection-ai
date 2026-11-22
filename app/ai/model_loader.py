"""
YOLOv8 Model Loader and Lifecycle Manager
Provides thread-safe singleton loading for AI object detection weights.
"""
import os
import logging
from config import Config, basedir

logger = logging.getLogger(__name__)

# Ensure Ultralytics writes configuration inside the project directory
# rather than system/user directories which might have permission restrictions.
os.environ.setdefault('YOLO_CONFIG_DIR', os.path.abspath(os.path.join(basedir, '.yolo')))

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
    root_model_path = os.path.join(basedir, 'yolov8n.pt')
    os.makedirs(os.path.dirname(model_path), exist_ok=True)

    try:
        from ultralytics import YOLO
        
        # Check custom weights path first, then root path, then base 'yolov8n.pt'
        if os.path.exists(model_path):
            target_path = model_path
        elif os.path.exists(root_model_path):
            target_path = root_model_path
        else:
            target_path = 'yolov8n.pt'

        logger.info(f"Loading YOLOv8 model from: {target_path}")
        _model_instance = YOLO(target_path)
        logger.info("YOLOv8 Defect Detection Model loaded successfully.")
    except Exception as e:
        logger.warning(f"Ultralytics YOLO model failed to load ({str(e)}). Using computer vision fallback detector.")
        _model_instance = "FALLBACK_CV_ENGINE"

    return _model_instance
