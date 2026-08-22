"""
AI Defect Detection Package for Smart City Infrastructure
"""
from .model_loader import get_model
from .detector import DefectDetector

__all__ = ['get_model', 'DefectDetector']
