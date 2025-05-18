import os
import re
import yaml
from pathlib import Path
from typing import Dict, List, Optional, Union

class TestConverter:
    def __init__(self):
        self.tests_dir = Path(".tests")
        self.converted_dir = Path(".tests/converted")
        self.converted_dir.mkdir(exist_ok=True)
        
    def clean_yaml_content(self, content: str) -> str:
        """Clean YAML content to make it parseable"""
        # Remove references and citations
        content = re.sub(r'^\s*(Reference|Citation):.+$', '', content, flags=re.MULTILINE)
        
        # Fix list items that might break YAML parsing
        content = re.sub(r'^\s*-\s+"([^"]+)"\s+by\s+(.+)$', 
                        r'  - title: "\1"\n    author: "\2"', 
                        content, 
                        flags=re.MULTILINE)
        
        return content
        
    def extract_yaml_block(self, content: str) -> Optional[Dict]:
        """Extract and parse a YAML block from markdown content"""
        yaml_match = re.search(r'```yaml\n(.*?)\n```', content, re.DOTALL)
        if not yaml_match:
            return None
            
        try:
            yaml_content = self.clean_yaml_content(yaml_match.group(1))
            return yaml.safe_load(yaml_content)
        except yaml.YAMLError as e:
            print(f"YAML parsing error: {e}")
            return None
            
    def format_value(self, value: Union[str, List, Dict]) -> str:
        """Format a value for markdown output"""
        if isinstance(value, (list, dict)):
            return str(value)
        return str(value)
        
    def convert_test_file(self, test_file: Path) -> Path:
        """Convert a YAML-in-markdown test file to the expected format"""
        with open(test_file, 'r', encoding='utf-8') as f:
            content = f.read()
            
        # Extract test metadata
        metadata = self.extract_yaml_block(content)
        converted_content = []
        
        if metadata:
            converted_content.append("# Test Configuration")
            for key, value in metadata.items():
                if isinstance(value, (str, int, float)):
                    converted_content.append(f"{key}: {value}")
            converted_content.append("")
            
        # Process each section
        sections = re.split(r'^##\s+', content, flags=re.MULTILINE)
        for section in sections:
            if not section.strip():
                continue
                
            # Extract section title and content
            title_match = re.match(r'^([^\n]+)\n', section)
            if not title_match:
                continue
                
            section_title = title_match.group(1)
            section_content = section[len(title_match.group(0)):]
            
            # Add section header
            converted_content.append(f"## {section_title}")
            converted_content.append("")
            
            # Process questions in the section
            questions = re.finditer(r'^###\s+([^\n]+)\n(.*?)(?=^###|\Z)', 
                                 section_content, 
                                 re.DOTALL | re.MULTILINE)
            
            for question in questions:
                title = question.group(1)
                question_content = question.group(2)
                
                # Extract question data
                question_data = self.extract_yaml_block(question_content)
                if question_data:
                    # Format the question with metadata
                    converted_content.append(f"### {title}")
                    
                    # Add metadata fields
                    metadata_fields = ['Topic', 'Difficulty', 'Points']
                    for field in metadata_fields:
                        if field in question_data:
                            converted_content.append(f"{field}: {question_data[field]}")
                    
                    # Add question content
                    if 'Question' in question_data:
                        converted_content.append("")
                        question_text = question_data['Question']
                        if isinstance(question_text, str):
                            # Ensure question ends with question mark
                            if not question_text.strip().endswith('?'):
                                question_text = question_text.strip() + '?'
                            converted_content.append(question_text)
                    
                    # Add options for multiple choice
                    if 'Options' in question_data:
                        converted_content.append("\nOptions:")
                        for key, value in question_data['Options'].items():
                            converted_content.append(f"{key}: {value}")
                    
                    # Add grading rubric
                    if 'Grading Rubric' in question_data:
                        converted_content.append("\nGrading Rubric:")
                        rubric = question_data['Grading Rubric']
                        if isinstance(rubric, dict):
                            for key, value in rubric.items():
                                if isinstance(value, (int, float)):
                                    converted_content.append(f"- {key}: {value} points")
                                else:
                                    converted_content.append(f"- {key}: {value}")
                        elif isinstance(rubric, str):
                            converted_content.append(rubric)
                        elif isinstance(rubric, list):
                            for item in rubric:
                                converted_content.append(f"- {item}")
                    
                    converted_content.append("")
                    
        # Write converted file
        converted_file = self.converted_dir / test_file.name
        with open(converted_file, 'w', encoding='utf-8') as f:
            f.write('\n'.join(str(line) for line in converted_content))
            
        return converted_file
        
    def convert_all_tests(self) -> List[Path]:
        """Convert all test files in the .tests directory"""
        converted_files = []
        
        # Clear existing converted files
        for file in self.converted_dir.glob('*.md'):
            file.unlink()
            
        # Convert each test file
        for root, _, files in os.walk(self.tests_dir):
            for file in files:
                if file.endswith('_test.md'):
                    test_file = Path(root) / file
                    if test_file.parent != self.converted_dir:  # Skip already converted files
                        try:
                            converted_file = self.convert_test_file(test_file)
                            converted_files.append(converted_file)
                            print(f"Converted {test_file} -> {converted_file}")
                        except Exception as e:
                            print(f"Error converting {test_file}: {e}")
                    
        return converted_files

if __name__ == "__main__":
    converter = TestConverter()
    converted_files = converter.convert_all_tests()
    
    print("\nConverted Test Files:")
    for file in converted_files:
        print(f"- {file}") 