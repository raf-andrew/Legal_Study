#!/usr/bin/env python3

import os
import sys
import json
import logging
import datetime
from pathlib import Path
from typing import Dict, List, Any
import cv2
import numpy as np
from PIL import Image
import pytesseract

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('wireframe_analysis.log'),
        logging.StreamHandler(sys.stdout)
    ]
)

logger = logging.getLogger(__name__)

class WireframeAnalyzer:
    def __init__(self):
        self.results = {
            'timestamp': datetime.datetime.now().isoformat(),
            'analysis': {},
            'recommendations': []
        }

    def analyze_layout(self, image_path: str) -> Dict[str, Any]:
        """Analyze wireframe layout and composition."""
        try:
            # Read image
            img = cv2.imread(image_path)
            gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

            # Edge detection
            edges = cv2.Canny(gray, 50, 150)

            # Find contours
            contours, _ = cv2.findContours(edges, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

            # Analyze layout
            layout_analysis = {
                'total_elements': len(contours),
                'image_size': {
                    'width': img.shape[1],
                    'height': img.shape[0]
                },
                'element_distribution': self.analyze_element_distribution(contours, img.shape)
            }

            return {
                'status': 'passed',
                'details': layout_analysis
            }
        except Exception as e:
            return {
                'status': 'failed',
                'details': {'error': str(e)}
            }

    def analyze_element_distribution(self, contours: List, image_shape: tuple) -> Dict[str, Any]:
        """Analyze the distribution of elements in the wireframe."""
        # Calculate element positions and sizes
        elements = []
        for contour in contours:
            x, y, w, h = cv2.boundingRect(contour)
            elements.append({
                'position': {'x': x, 'y': y},
                'size': {'width': w, 'height': h},
                'area': w * h
            })

        # Analyze distribution
        total_area = image_shape[0] * image_shape[1]
        element_areas = [e['area'] for e in elements]

        return {
            'element_count': len(elements),
            'total_area_covered': sum(element_areas),
            'coverage_percentage': (sum(element_areas) / total_area) * 100,
            'average_element_size': sum(element_areas) / len(elements) if elements else 0
        }

    def analyze_text_content(self, image_path: str) -> Dict[str, Any]:
        """Analyze text content in the wireframe."""
        try:
            # Extract text using OCR
            text = pytesseract.image_to_string(Image.open(image_path))

            # Analyze text content
            lines = text.split('\n')
            words = text.split()

            return {
                'status': 'passed',
                'details': {
                    'total_lines': len(lines),
                    'total_words': len(words),
                    'average_line_length': sum(len(line) for line in lines) / len(lines) if lines else 0,
                    'text_content': text
                }
            }
        except Exception as e:
            return {
                'status': 'failed',
                'details': {'error': str(e)}
            }

    def analyze_color_scheme(self, image_path: str) -> Dict[str, Any]:
        """Analyze color scheme and contrast."""
        try:
            # Read image
            img = cv2.imread(image_path)

            # Convert to RGB
            rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)

            # Get dominant colors
            pixels = rgb.reshape(-1, 3)
            from sklearn.cluster import KMeans
            kmeans = KMeans(n_clusters=5, random_state=0).fit(pixels)
            colors = kmeans.cluster_centers_

            return {
                'status': 'passed',
                'details': {
                    'dominant_colors': colors.tolist(),
                    'color_count': len(np.unique(pixels, axis=0))
                }
            }
        except Exception as e:
            return {
                'status': 'failed',
                'details': {'error': str(e)}
            }

    def generate_recommendations(self, analysis_results: Dict[str, Any]) -> List[str]:
        """Generate recommendations based on analysis results."""
        recommendations = []

        # Layout recommendations
        layout = analysis_results.get('layout', {}).get('details', {})
        if layout.get('element_distribution', {}).get('coverage_percentage', 0) < 30:
            recommendations.append("Consider increasing content density for better space utilization")

        # Text content recommendations
        text = analysis_results.get('text_content', {}).get('details', {})
        if text.get('average_line_length', 0) > 100:
            recommendations.append("Consider breaking down long text into more digestible chunks")

        # Color scheme recommendations
        colors = analysis_results.get('color_scheme', {}).get('details', {})
        if colors.get('color_count', 0) > 10:
            recommendations.append("Consider simplifying the color palette for better visual consistency")

        return recommendations

    def analyze_wireframe(self, image_path: str) -> Dict[str, Any]:
        """Analyze a wireframe image and generate recommendations."""
        analysis = {
            'layout': self.analyze_layout(image_path),
            'text_content': self.analyze_text_content(image_path),
            'color_scheme': self.analyze_color_scheme(image_path)
        }

        self.results['analysis'] = analysis
        self.results['recommendations'] = self.generate_recommendations(analysis)

        return self.results

    def save_results(self, output_path: str):
        """Save analysis results to a JSON file."""
        try:
            with open(output_path, 'w') as f:
                json.dump(self.results, f, indent=2)
            logger.info(f"Results saved to {output_path}")
        except Exception as e:
            logger.error(f"Failed to save results: {e}")

def main():
    # Create output directory
    output_dir = Path('.wireframe/testing/analysis')
    output_dir.mkdir(parents=True, exist_ok=True)

    # Get all wireframe images
    wireframe_dir = Path('.wireframe/testing/output')
    image_files = list(wireframe_dir.rglob('*.png'))

    for image_file in image_files:
        logger.info(f"Analyzing wireframe: {image_file}")

        # Create output directory for this wireframe
        wireframe_output_dir = output_dir / image_file.parent.name
        wireframe_output_dir.mkdir(exist_ok=True)

        # Analyze wireframe
        analyzer = WireframeAnalyzer()
        results = analyzer.analyze_wireframe(str(image_file))

        # Save results
        results_file = wireframe_output_dir / f'analysis_{datetime.datetime.now().strftime("%Y%m%d_%H%M%S")}.json'
        analyzer.save_results(str(results_file))

        # Print recommendations
        print(f"\nWireframe Analysis for {image_file.name}:")
        print("\nRecommendations:")
        for rec in results['recommendations']:
            print(f"- {rec}")

if __name__ == '__main__':
    main()
