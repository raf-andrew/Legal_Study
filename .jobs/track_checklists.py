import os
import re
import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class ChecklistTracker:
    def __init__(self, checklists_dir: str = ".jobs"):
        self.checklists_dir = checklists_dir
        self.results = {}
        
    def scan_checklists(self) -> Dict:
        """Scan all markdown checklists and analyze their completion status."""
        checklist_files = Path(self.checklists_dir).glob("*_checklist.md")
        results = {
            "timestamp": datetime.now().isoformat(),
            "checklists": {},
            "summary": {
                "total_checklists": 0,
                "total_items": 0,
                "completed_items": 0
            }
        }
        
        for file_path in checklist_files:
            try:
                with open(file_path, 'r') as f:
                    content = f.read()
                
                # Parse checklist items
                checklist_items = re.findall(r'- \[([ x])\].*', content)
                total_items = len(checklist_items)
                completed_items = sum(1 for item in checklist_items if item == 'x')
                
                # Parse sections
                sections = {}
                current_section = "General"
                for line in content.split('\n'):
                    if line.startswith('## '):
                        current_section = line[3:].strip()
                        sections[current_section] = {"total": 0, "completed": 0}
                    elif line.startswith('- ['):
                        if current_section not in sections:
                            sections[current_section] = {"total": 0, "completed": 0}
                        sections[current_section]["total"] += 1
                        if line.startswith('- [x]'):
                            sections[current_section]["completed"] += 1
                
                checklist_name = file_path.stem.replace('_checklist', '').title()
                results["checklists"][checklist_name] = {
                    "file": str(file_path),
                    "total_items": total_items,
                    "completed_items": completed_items,
                    "completion_percentage": (completed_items / total_items * 100) if total_items > 0 else 0,
                    "sections": sections
                }
                
                # Update summary
                results["summary"]["total_checklists"] += 1
                results["summary"]["total_items"] += total_items
                results["summary"]["completed_items"] += completed_items
                
            except Exception as e:
                logger.error(f"Error processing {file_path}: {str(e)}")
        
        if results["summary"]["total_items"] > 0:
            results["summary"]["overall_completion"] = (
                results["summary"]["completed_items"] / results["summary"]["total_items"] * 100
            )
        else:
            results["summary"]["overall_completion"] = 0
            
        self.results = results
        return results

    def generate_report(self, output_format: str = "text") -> str:
        """Generate a report of checklist status."""
        if not self.results:
            self.scan_checklists()
            
        if output_format == "json":
            return json.dumps(self.results, indent=2)
            
        elif output_format == "text":
            report = []
            report.append("Checklist Progress Report")
            report.append(f"Generated: {self.results['timestamp']}")
            report.append(f"\nOverall Progress: {self.results['summary']['overall_completion']:.1f}%")
            report.append(f"Total Checklists: {self.results['summary']['total_checklists']}")
            report.append(f"Total Items: {self.results['summary']['total_items']}")
            report.append(f"Completed Items: {self.results['summary']['completed_items']}")
            
            for checklist_name, checklist_data in self.results["checklists"].items():
                report.append(f"\n{checklist_name} Checklist")
                report.append(f"Progress: {checklist_data['completion_percentage']:.1f}%")
                report.append(f"Items: {checklist_data['completed_items']}/{checklist_data['total_items']}")
                
                report.append("\nSection Progress:")
                for section, section_data in checklist_data["sections"].items():
                    completion = (section_data["completed"] / section_data["total"] * 100) if section_data["total"] > 0 else 0
                    report.append(f"  {section}: {completion:.1f}% ({section_data['completed']}/{section_data['total']})")
            
            return "\n".join(report)
            
        elif output_format == "html":
            html = [
                "<html>",
                "<head>",
                "<style>",
                "body { font-family: Arial, sans-serif; margin: 20px; }",
                ".progress { width: 200px; height: 20px; background-color: #f0f0f0; border-radius: 10px; }",
                ".progress-bar { height: 100%; background-color: #4CAF50; border-radius: 10px; }",
                ".checklist { margin: 20px 0; padding: 10px; border: 1px solid #ccc; }",
                ".section { margin: 10px 0; }",
                "</style>",
                "</head>",
                "<body>",
                "<h1>Checklist Progress Report</h1>",
                f"<p>Generated: {self.results['timestamp']}</p>"
            ]
            
            # Overall progress
            overall = self.results['summary']['overall_completion']
            html.append(f"<h2>Overall Progress: {overall:.1f}%</h2>")
            html.append(f'<div class="progress"><div class="progress-bar" style="width: {overall}%"></div></div>')
            
            # Summary
            html.append("<h3>Summary</h3>")
            html.append("<ul>")
            html.append(f"<li>Total Checklists: {self.results['summary']['total_checklists']}</li>")
            html.append(f"<li>Total Items: {self.results['summary']['total_items']}</li>")
            html.append(f"<li>Completed Items: {self.results['summary']['completed_items']}</li>")
            html.append("</ul>")
            
            # Individual checklists
            for checklist_name, checklist_data in self.results["checklists"].items():
                html.append(f'<div class="checklist">')
                html.append(f"<h3>{checklist_name} Checklist</h3>")
                completion = checklist_data['completion_percentage']
                html.append(f'<div class="progress"><div class="progress-bar" style="width: {completion}%"></div></div>')
                html.append(f"<p>Progress: {completion:.1f}%</p>")
                html.append(f"<p>Items: {checklist_data['completed_items']}/{checklist_data['total_items']}</p>")
                
                html.append("<h4>Section Progress:</h4>")
                for section, section_data in checklist_data["sections"].items():
                    section_completion = (section_data["completed"] / section_data["total"] * 100) if section_data["total"] > 0 else 0
                    html.append(f'<div class="section">')
                    html.append(f"<p>{section}: {section_completion:.1f}% ({section_data['completed']}/{section_data['total']})</p>")
                    html.append(f'<div class="progress"><div class="progress-bar" style="width: {section_completion}%"></div></div>')
                    html.append("</div>")
                
                html.append("</div>")
            
            html.extend(["</body>", "</html>"])
            return "\n".join(html)
        else:
            raise ValueError(f"Unsupported output format: {output_format}")

    def save_report(self, output_dir: str = "reports") -> None:
        """Save reports in multiple formats."""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        os.makedirs(output_dir, exist_ok=True)
        
        # Save JSON report
        with open(f"{output_dir}/checklist_progress_{timestamp}.json", "w") as f:
            json.dump(self.results, f, indent=2)
        
        # Save text report
        with open(f"{output_dir}/checklist_progress_{timestamp}.txt", "w") as f:
            f.write(self.generate_report("text"))
        
        # Save HTML report
        with open(f"{output_dir}/checklist_progress_{timestamp}.html", "w") as f:
            f.write(self.generate_report("html"))

def main():
    tracker = ChecklistTracker()
    
    # Generate and print text report
    print(tracker.generate_report("text"))
    
    # Save reports in all formats
    tracker.save_report()

if __name__ == "__main__":
    main() 