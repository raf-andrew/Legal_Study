#!/usr/bin/env python3
"""
HTML Guide Generator
This script generates HTML guides from our documentation templates.
"""

import argparse
import logging
import os
import sys
from pathlib import Path
from typing import Dict, List, Optional

import jinja2
import yaml
from jinja2 import Environment, FileSystemLoader

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class HTMLGuideGenerator:
    def __init__(self, config_path: str, template_dir: str, output_dir: str):
        self.config_path = config_path
        self.template_dir = Path(template_dir)
        self.output_dir = Path(output_dir)
        self.config = self.load_config()
        self.env = self.setup_jinja()

    def load_config(self) -> Dict:
        """Load configuration from YAML file."""
        try:
            with open(self.config_path, 'r') as f:
                return yaml.safe_load(f)
        except Exception as e:
            logger.error(f"Failed to load config: {str(e)}")
            sys.exit(1)

    def setup_jinja(self) -> Environment:
        """Set up Jinja2 environment."""
        return Environment(
            loader=FileSystemLoader(self.template_dir),
            autoescape=True
        )

    def generate_guide(self, template_name: str, output_name: str) -> None:
        """Generate HTML guide from template."""
        try:
            template = self.env.get_template(template_name)
            output = template.render(
                config=self.config,
                last_updated=time.strftime("%Y-%m-%d %H:%M:%S")
            )

            output_path = self.output_dir / output_name
            output_path.parent.mkdir(parents=True, exist_ok=True)

            with open(output_path, 'w') as f:
                f.write(output)

            logger.info(f"Generated guide: {output_path}")
        except Exception as e:
            logger.error(f"Failed to generate guide: {str(e)}")

    def generate_all_guides(self) -> None:
        """Generate all HTML guides."""
        guides = {
            'security.md.j2': 'guides/security_setup.html',
            'workflows.md.j2': 'guides/workflow_setup.html',
            'environments.md.j2': 'guides/environment_setup.html',
            'analytics.md.j2': 'guides/analytics_setup.html',
            'community.md.j2': 'guides/community_setup.html',
            'dependabot.md.j2': 'guides/dependabot_setup.html',
            'projects.md.j2': 'guides/project_setup.html',
            'governance.md.j2': 'guides/governance_setup.html'
        }

        for template, output in guides.items():
            self.generate_guide(template, output)

def main():
    parser = argparse.ArgumentParser(description='Generate HTML guides from templates')
    parser.add_argument('--config', default='docs/github/config.yaml', help='Path to configuration file')
    parser.add_argument('--template-dir', default='docs/github/templates', help='Template directory')
    parser.add_argument('--output-dir', default='docs/github', help='Output directory')
    args = parser.parse_args()

    generator = HTMLGuideGenerator(args.config, args.template_dir, args.output_dir)
    generator.generate_all_guides()

if __name__ == '__main__':
    main()
