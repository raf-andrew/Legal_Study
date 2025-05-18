"""
Script to set up AI components for sniffing infrastructure.
"""
import logging
import os
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional

import torch
import yaml
from transformers import AutoModelForSequenceClassification, AutoTokenizer

logger = logging.getLogger("setup_ai")

def main() -> int:
    """Main entry point for AI setup."""
    try:
        # Set up logging
        setup_logging()

        # Load configuration
        config = load_config()
        if not config:
            logger.error("Failed to load configuration")
            return 1

        # Set up AI components
        if not setup_ai(config):
            logger.error("Failed to set up AI components")
            return 1

        logger.info("AI components set up successfully")
        return 0

    except Exception as e:
        logger.error(f"Error setting up AI components: {e}")
        return 1

def setup_logging() -> None:
    """Set up logging configuration."""
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )

def load_config() -> Optional[Dict[str, Any]]:
    """Load sniffing configuration."""
    try:
        config_path = Path("sniffing/config/sniffing_config.yaml")
        if not config_path.exists():
            logger.error(f"Configuration file not found: {config_path}")
            return None

        with open(config_path, "r") as f:
            config = yaml.safe_load(f)

        return config

    except Exception as e:
        logger.error(f"Error loading configuration: {e}")
        return None

def setup_ai(config: Dict[str, Any]) -> bool:
    """Set up AI components."""
    try:
        # Get AI configuration
        ai_config = config.get("ai", {})
        if not ai_config.get("enabled", False):
            logger.info("AI components disabled in configuration")
            return True

        # Create directories
        if not create_directories(ai_config):
            return False

        # Download models
        if not download_models(ai_config):
            return False

        # Set up features
        if not setup_features(ai_config):
            return False

        return True

    except Exception as e:
        logger.error(f"Error setting up AI components: {e}")
        return False

def create_directories(config: Dict[str, Any]) -> bool:
    """Create AI directories."""
    try:
        # Create model directories
        model_path = Path(config.get("model_path", "models"))
        model_path.mkdir(parents=True, exist_ok=True)

        # Create feature directories
        features = config.get("features", {})
        for feature in features:
            feature_path = model_path / feature
            feature_path.mkdir(exist_ok=True)
            logger.info(f"Created directory: {feature_path}")

        return True

    except Exception as e:
        logger.error(f"Error creating directories: {e}")
        return False

def download_models(config: Dict[str, Any]) -> bool:
    """Download AI models."""
    try:
        # Get model configuration
        model_name = config.get("model", "microsoft/codebert-base")
        model_path = Path(config.get("model_path", "models"))

        # Download tokenizer
        logger.info(f"Downloading tokenizer: {model_name}")
        tokenizer = AutoTokenizer.from_pretrained(model_name)
        tokenizer.save_pretrained(model_path / "tokenizer")

        # Download model
        logger.info(f"Downloading model: {model_name}")
        model = AutoModelForSequenceClassification.from_pretrained(
            model_name,
            num_labels=len(config.get("features", {}))
        )
        model.save_pretrained(model_path / "model")

        return True

    except Exception as e:
        logger.error(f"Error downloading models: {e}")
        return False

def setup_features(config: Dict[str, Any]) -> bool:
    """Set up AI features."""
    try:
        features = config.get("features", {})
        if not features:
            logger.warning("No AI features configured")
            return True

        # Set up each feature
        for feature, enabled in features.items():
            if enabled:
                if not setup_feature(feature, config):
                    return False

        return True

    except Exception as e:
        logger.error(f"Error setting up features: {e}")
        return False

def setup_feature(feature: str, config: Dict[str, Any]) -> bool:
    """Set up a specific AI feature."""
    try:
        logger.info(f"Setting up feature: {feature}")

        if feature == "code_analysis":
            return setup_code_analysis(config)
        elif feature == "vulnerability_detection":
            return setup_vulnerability_detection(config)
        elif feature == "documentation_generation":
            return setup_documentation_generation(config)
        elif feature == "test_generation":
            return setup_test_generation(config)
        elif feature == "code_review":
            return setup_code_review(config)
        else:
            logger.warning(f"Unknown feature: {feature}")
            return True

    except Exception as e:
        logger.error(f"Error setting up feature {feature}: {e}")
        return False

def setup_code_analysis(config: Dict[str, Any]) -> bool:
    """Set up code analysis feature."""
    try:
        # Create configuration
        analysis_config = {
            "model": config.get("model", "microsoft/codebert-base"),
            "max_tokens": config.get("max_tokens", 512),
            "temperature": config.get("temperature", 0.7),
            "metrics": [
                "complexity",
                "maintainability",
                "reliability",
                "security"
            ]
        }

        # Save configuration
        config_path = Path("models/code_analysis/config.yml")
        config_path.parent.mkdir(parents=True, exist_ok=True)

        with open(config_path, "w") as f:
            yaml.dump(analysis_config, f)

        return True

    except Exception as e:
        logger.error(f"Error setting up code analysis: {e}")
        return False

def setup_vulnerability_detection(config: Dict[str, Any]) -> bool:
    """Set up vulnerability detection feature."""
    try:
        # Create configuration
        vuln_config = {
            "model": config.get("model", "microsoft/codebert-base"),
            "confidence_threshold": config.get("confidence_threshold", 0.8),
            "vulnerability_types": [
                "sql_injection",
                "xss",
                "file_inclusion",
                "command_injection",
                "authentication_bypass"
            ],
            "severity_levels": [
                "high",
                "medium",
                "low"
            ]
        }

        # Save configuration
        config_path = Path("models/vulnerability_detection/config.yml")
        config_path.parent.mkdir(parents=True, exist_ok=True)

        with open(config_path, "w") as f:
            yaml.dump(vuln_config, f)

        return True

    except Exception as e:
        logger.error(f"Error setting up vulnerability detection: {e}")
        return False

def setup_documentation_generation(config: Dict[str, Any]) -> bool:
    """Set up documentation generation feature."""
    try:
        # Create configuration
        doc_config = {
            "model": config.get("model", "microsoft/codebert-base"),
            "max_tokens": config.get("max_tokens", 512),
            "temperature": config.get("temperature", 0.7),
            "style_guide": "google",
            "sections": [
                "description",
                "parameters",
                "returns",
                "examples"
            ]
        }

        # Save configuration
        config_path = Path("models/documentation_generation/config.yml")
        config_path.parent.mkdir(parents=True, exist_ok=True)

        with open(config_path, "w") as f:
            yaml.dump(doc_config, f)

        return True

    except Exception as e:
        logger.error(f"Error setting up documentation generation: {e}")
        return False

def setup_test_generation(config: Dict[str, Any]) -> bool:
    """Set up test generation feature."""
    try:
        # Create configuration
        test_config = {
            "model": config.get("model", "microsoft/codebert-base"),
            "max_tokens": config.get("max_tokens", 512),
            "temperature": config.get("temperature", 0.7),
            "test_frameworks": {
                "python": "pytest",
                "javascript": "jest",
                "typescript": "jest"
            },
            "coverage_threshold": 90
        }

        # Save configuration
        config_path = Path("models/test_generation/config.yml")
        config_path.parent.mkdir(parents=True, exist_ok=True)

        with open(config_path, "w") as f:
            yaml.dump(test_config, f)

        return True

    except Exception as e:
        logger.error(f"Error setting up test generation: {e}")
        return False

def setup_code_review(config: Dict[str, Any]) -> bool:
    """Set up code review feature."""
    try:
        # Create configuration
        review_config = {
            "model": config.get("model", "microsoft/codebert-base"),
            "max_tokens": config.get("max_tokens", 512),
            "temperature": config.get("temperature", 0.7),
            "review_aspects": [
                "style",
                "performance",
                "security",
                "maintainability"
            ],
            "severity_levels": [
                "critical",
                "major",
                "minor",
                "suggestion"
            ]
        }

        # Save configuration
        config_path = Path("models/code_review/config.yml")
        config_path.parent.mkdir(parents=True, exist_ok=True)

        with open(config_path, "w") as f:
            yaml.dump(review_config, f)

        return True

    except Exception as e:
        logger.error(f"Error setting up code review: {e}")
        return False

def verify_setup() -> bool:
    """Verify AI setup."""
    try:
        # Check directories
        required_dirs = [
            "models/code_analysis",
            "models/vulnerability_detection",
            "models/documentation_generation",
            "models/test_generation",
            "models/code_review"
        ]

        for directory in required_dirs:
            path = Path(directory)
            if not path.exists():
                logger.error(f"Required directory not found: {directory}")
                return False

        # Check configurations
        required_configs = [
            "models/code_analysis/config.yml",
            "models/vulnerability_detection/config.yml",
            "models/documentation_generation/config.yml",
            "models/test_generation/config.yml",
            "models/code_review/config.yml"
        ]

        for config_file in required_configs:
            path = Path(config_file)
            if not path.exists():
                logger.error(f"Configuration file not found: {config_file}")
                return False

        # Check model files
        model_files = [
            "models/model/pytorch_model.bin",
            "models/tokenizer/vocab.json"
        ]

        for model_file in model_files:
            path = Path(model_file)
            if not path.exists():
                logger.error(f"Model file not found: {model_file}")
                return False

        # Check CUDA availability
        if torch.cuda.is_available():
            logger.info("CUDA is available")
            logger.info(f"Using device: {torch.cuda.get_device_name(0)}")
        else:
            logger.warning("CUDA not available, using CPU")

        return True

    except Exception as e:
        logger.error(f"Error verifying setup: {e}")
        return False

def cleanup_old_files() -> bool:
    """Clean up old AI files."""
    try:
        # Clean up old files
        old_files = [
            "models/code_analysis/config.yml.old",
            "models/vulnerability_detection/config.yml.old",
            "models/documentation_generation/config.yml.old",
            "models/test_generation/config.yml.old",
            "models/code_review/config.yml.old"
        ]

        for file in old_files:
            path = Path(file)
            if path.exists():
                path.unlink()
                logger.info(f"Removed old file: {file}")

        return True

    except Exception as e:
        logger.error(f"Error cleaning up old files: {e}")
        return False

if __name__ == "__main__":
    sys.exit(main())
