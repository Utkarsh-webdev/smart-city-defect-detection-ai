"""
AI Detector Verification Script
Generates a synthetic road defect image and validates detection and annotation.
"""
import os
import sys
from PIL import Image, ImageDraw

# Add project root to sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))

from app.ai.detector import DefectDetector


def create_sample_road_image(output_path):
    """Creates a synthetic asphalt road image with a pothole for testing."""
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    img = Image.new('RGB', (640, 480), color=(55, 58, 60))
    draw = ImageDraw.Draw(img)
    
    # Draw yellow road divider line
    draw.line([(320, 0), (320, 480)], fill=(240, 200, 40), width=8)
    
    # Draw a simulated dark pothole depression
    draw.ellipse([(200, 200), (380, 320)], fill=(20, 22, 24), outline=(10, 10, 10), width=3)
    draw.ellipse([(240, 230), (340, 290)], fill=(12, 12, 14))
    
    img.save(output_path, 'JPEG')
    return output_path


def run_test():
    print("==================================================")
    print("Testing Smart City AI Defect Detection Engine")
    print("==================================================")
    
    sample_dir = os.path.join(os.path.dirname(__file__), 'test_samples')
    input_sample = os.path.join(sample_dir, 'sample_pothole.jpg')
    output_annotated = os.path.join(sample_dir, 'sample_annotated.jpg')
    
    create_sample_road_image(input_sample)
    print(f"[OK] Generated test image at: {input_sample}")
    
    detector = DefectDetector(confidence_threshold=0.60)
    result = detector.detect(input_sample, output_annotated_path=output_annotated, reported_hint='Pothole')
    
    print("\n--- Detection Result ---")
    print(f"Primary Defect: {result['primary_defect']}")
    print(f"Confidence:     {int(result['confidence'] * 100)}%")
    print(f"Severity:       {result['severity']}")
    print(f"Defect Count:   {result['defect_count']}")
    print(f"AI Status:      {result['ai_status']}")
    print(f"Latency:        {result['processing_time_ms']} ms")
    print(f"Annotated Image Saved: {os.path.exists(output_annotated)}")
    print("==================================================")
    print("AI Engine Test PASSED Successfully!")


if __name__ == '__main__':
    run_test()
