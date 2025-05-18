#!/usr/bin/env python3

import os
import json
import random
from datetime import datetime
from pathlib import Path

class TestDataGenerator:
    def __init__(self, output_dir=".wireframe/testing/test_data"):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)

    def generate_test_report(self, report_id=None):
        """Generate a test report with random but consistent data."""
        if report_id is None:
            report_id = f"test_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}"

        report_data = {
            "report_id": report_id,
            "timestamp": datetime.now().isoformat(),
            "version": "1.0.0",
            "metadata": {
                "title": f"Test Report {report_id}",
                "description": "Generated test report for wireframe refinement testing",
                "author": "Test System",
                "generated_at": datetime.now().isoformat()
            },
            "content": {
                "sections": self._generate_sections(),
                "options": self._generate_options(),
                "metrics": self._generate_metrics()
            }
        }

        # Save as JSON
        json_path = self.output_dir / f"{report_id}.json"
        with open(json_path, 'w') as f:
            json.dump(report_data, f, indent=2)

        # Generate HTML version
        html_path = self.output_dir / f"{report_id}.html"
        self._generate_html_report(report_data, html_path)

        return {
            "json_path": str(json_path),
            "html_path": str(html_path),
            "data": report_data
        }

    def _generate_sections(self):
        """Generate random sections for the report."""
        sections = []
        for i in range(random.randint(3, 6)):
            section = {
                "id": f"section_{i+1}",
                "title": f"Section {i+1}",
                "content": f"This is test content for section {i+1}",
                "order": i,
                "type": random.choice(["text", "image", "code", "table"])
            }
            sections.append(section)
        return sections

    def _generate_options(self):
        """Generate random options for the report."""
        options = []
        for i in range(random.randint(2, 4)):
            option = {
                "id": f"option_{i+1}",
                "title": f"Option {i+1}",
                "description": f"Description for option {i+1}",
                "selected": False,
                "order": i
            }
            options.append(option)
        return options

    def _generate_metrics(self):
        """Generate random metrics for the report."""
        return {
            "performance": {
                "load_time": random.uniform(0.1, 2.0),
                "render_time": random.uniform(0.05, 1.0),
                "interaction_time": random.uniform(0.01, 0.5)
            },
            "accessibility": {
                "score": random.randint(80, 100),
                "issues": random.randint(0, 5)
            },
            "responsiveness": {
                "desktop": random.randint(90, 100),
                "tablet": random.randint(85, 100),
                "mobile": random.randint(80, 100)
            }
        }

    def _generate_html_report(self, report_data, output_path):
        """Generate HTML report from the report data."""
        html_content = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{report_data['metadata']['title']}</title>
    <style>
        body {{
            font-family: Arial, sans-serif;
            line-height: 1.6;
            margin: 0;
            padding: 20px;
            max-width: 1200px;
            margin: 0 auto;
        }}
        .section {{
            margin-bottom: 30px;
            padding: 20px;
            border: 1px solid #ddd;
            border-radius: 5px;
        }}
        .option {{
            padding: 10px;
            margin: 5px 0;
            border: 1px solid #eee;
            border-radius: 3px;
            cursor: pointer;
        }}
        .option.selected {{
            background-color: #e3f2fd;
            border-color: #2196f3;
        }}
        .metric-card {{
            padding: 15px;
            margin: 10px 0;
            background-color: #f8f9fa;
            border-radius: 5px;
        }}
        .version-info {{
            position: fixed;
            top: 10px;
            right: 10px;
            padding: 5px 10px;
            background-color: #f8f9fa;
            border-radius: 3px;
            font-size: 0.9em;
            color: #666;
        }}
    </style>
</head>
<body>
    <div class="version-info">Version: {report_data['version']}</div>
    <h1>{report_data['metadata']['title']}</h1>
    <p>{report_data['metadata']['description']}</p>

    {self._generate_sections_html(report_data['content']['sections'])}
    {self._generate_options_html(report_data['content']['options'])}
    {self._generate_metrics_html(report_data['content']['metrics'])}

    <script>
        document.querySelectorAll('.option').forEach(option => {{
            option.addEventListener('click', function() {{
                // Remove selected class from all options
                document.querySelectorAll('.option').forEach(opt => {{
                    opt.classList.remove('selected');
                }});
                // Add selected class to clicked option
                this.classList.add('selected');
            }});
        }});
    </script>
</body>
</html>"""

        with open(output_path, 'w') as f:
            f.write(html_content)

    def _generate_sections_html(self, sections):
        """Generate HTML for sections."""
        sections_html = ""
        for section in sections:
            sections_html += f"""
            <div class="section" id="{section['id']}">
                <h2>{section['title']}</h2>
                <p>{section['content']}</p>
            </div>"""
        return sections_html

    def _generate_options_html(self, options):
        """Generate HTML for options."""
        options_html = """
        <div class="options">
            <h2>Options</h2>"""
        for option in options:
            options_html += f"""
            <div class="option" data-option-id="{option['id']}" role="button" tabindex="0">
                <h3>{option['title']}</h3>
                <p>{option['description']}</p>
            </div>"""
        options_html += "</div>"
        return options_html

    def _generate_metrics_html(self, metrics):
        """Generate HTML for metrics."""
        metrics_html = """
        <div class="metrics">
            <h2>Metrics</h2>"""

        # Performance metrics
        metrics_html += f"""
            <div class="metric-card">
                <h3>Performance</h3>
                <p>Load Time: {metrics['performance']['load_time']:.2f}s</p>
                <p>Render Time: {metrics['performance']['render_time']:.2f}s</p>
                <p>Interaction Time: {metrics['performance']['interaction_time']:.2f}s</p>
            </div>"""

        # Accessibility metrics
        metrics_html += f"""
            <div class="metric-card">
                <h3>Accessibility</h3>
                <p>Score: {metrics['accessibility']['score']}/100</p>
                <p>Issues: {metrics['accessibility']['issues']}</p>
            </div>"""

        # Responsiveness metrics
        metrics_html += f"""
            <div class="metric-card">
                <h3>Responsiveness</h3>
                <p>Desktop: {metrics['responsiveness']['desktop']}%</p>
                <p>Tablet: {metrics['responsiveness']['tablet']}%</p>
                <p>Mobile: {metrics['responsiveness']['mobile']}%</p>
            </div>"""

        metrics_html += "</div>"
        return metrics_html

if __name__ == "__main__":
    generator = TestDataGenerator()
    report = generator.generate_test_report()
    print(f"Generated test report at: {report['html_path']}")
