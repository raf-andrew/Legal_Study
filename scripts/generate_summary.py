#!/usr/bin/env python3

import argparse
import json
import os
from datetime import datetime
from jinja2 import Template

def load_verification_reports(verification_dir):
    """Load all verification reports from the directory."""
    reports = []

    for filename in os.listdir(verification_dir):
        if filename.endswith('_verification_') and filename.endswith('.json'):
            filepath = os.path.join(verification_dir, filename)
            with open(filepath, 'r', encoding='utf-8') as f:
                report = json.load(f)
                report['filename'] = filename
                reports.append(report)

    return reports

def generate_html_summary(reports, output_file):
    """Generate HTML summary of verification results."""
    template_str = """
    <!DOCTYPE html>
    <html>
    <head>
        <title>Verification Summary</title>
        <style>
            body { font-family: Arial, sans-serif; margin: 20px; }
            .summary { margin-bottom: 20px; }
            .report { border: 1px solid #ddd; padding: 10px; margin-bottom: 10px; }
            .passed { color: green; }
            .failed { color: red; }
            table { border-collapse: collapse; width: 100%; }
            th, td { border: 1px solid #ddd; padding: 8px; text-align: left; }
            th { background-color: #f2f2f2; }
        </style>
    </head>
    <body>
        <h1>Verification Summary</h1>
        <p>Generated: {{ timestamp }}</p>

        <div class="summary">
            <h2>Overall Summary</h2>
            <table>
                <tr>
                    <th>Metric</th>
                    <th>Value</th>
                </tr>
                <tr>
                    <td>Total Reports</td>
                    <td>{{ reports|length }}</td>
                </tr>
                <tr>
                    <td>Passed Verifications</td>
                    <td>{{ passed_count }}</td>
                </tr>
                <tr>
                    <td>Failed Verifications</td>
                    <td>{{ failed_count }}</td>
                </tr>
                <tr>
                    <td>Average Coverage</td>
                    <td>{{ avg_coverage }}%</td>
                </tr>
            </table>
        </div>

        <h2>Detailed Reports</h2>
        {% for report in reports %}
        <div class="report">
            <h3>Report: {{ report.filename }}</h3>
            <p>Timestamp: {{ report.timestamp }}</p>

            <h4>Test Results</h4>
            <table>
                <tr>
                    <th>Metric</th>
                    <th>Value</th>
                </tr>
                <tr>
                    <td>Total Tests</td>
                    <td>{{ report.test_results.total_tests }}</td>
                </tr>
                <tr>
                    <td>Passed</td>
                    <td class="{{ 'passed' if report.test_results.passed > 0 else 'failed' }}">
                        {{ report.test_results.passed }}
                    </td>
                </tr>
                <tr>
                    <td>Failed</td>
                    <td class="{{ 'failed' if report.test_results.failed > 0 else 'passed' }}">
                        {{ report.test_results.failed }}
                    </td>
                </tr>
                <tr>
                    <td>Skipped</td>
                    <td>{{ report.test_results.skipped }}</td>
                </tr>
                <tr>
                    <td>Pass Rate</td>
                    <td>{{ "%.2f"|format(report.test_results.pass_rate) }}%</td>
                </tr>
            </table>

            <h4>Coverage</h4>
            <table>
                <tr>
                    <th>Metric</th>
                    <th>Value</th>
                </tr>
                <tr>
                    <td>Line Coverage</td>
                    <td class="{{ 'passed' if report.coverage_data.line_coverage >= 90 else 'failed' }}">
                        {{ "%.2f"|format(report.coverage_data.line_coverage) }}%
                    </td>
                </tr>
            </table>

            <h4>Verification Status</h4>
            <table>
                <tr>
                    <th>Requirement</th>
                    <th>Status</th>
                </tr>
                {% for key, value in report.requirements_met.items() %}
                <tr>
                    <td>{{ key }}</td>
                    <td class="{{ 'passed' if value else 'failed' }}">
                        {{ 'PASSED' if value else 'FAILED' }}
                    </td>
                </tr>
                {% endfor %}
            </table>
        </div>
        {% endfor %}
    </body>
    </html>
    """

    # Calculate summary statistics
    passed_count = sum(1 for r in reports if r['verification_status']['passed'])
    failed_count = len(reports) - passed_count
    avg_coverage = sum(r['coverage_data']['line_coverage'] for r in reports) / len(reports) if reports else 0

    # Render template
    template = Template(template_str)
    html_content = template.render(
        timestamp=datetime.now().isoformat(),
        reports=reports,
        passed_count=passed_count,
        failed_count=failed_count,
        avg_coverage=avg_coverage
    )

    # Write HTML file
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(html_content)

def main():
    parser = argparse.ArgumentParser(description='Generate verification summary report')
    parser.add_argument('--verification-dir', required=True, help='Directory containing verification reports')
    parser.add_argument('--output', required=True, help='Output HTML file path')

    args = parser.parse_args()

    try:
        # Load verification reports
        reports = load_verification_reports(args.verification_dir)

        if not reports:
            print("No verification reports found")
            return

        # Generate HTML summary
        generate_html_summary(reports, args.output)
        print(f"Summary report generated: {args.output}")

    except Exception as e:
        print(f"Error generating summary: {str(e)}", file=sys.stderr)
        sys.exit(1)

if __name__ == '__main__':
    main()
