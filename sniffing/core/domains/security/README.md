# Security Domain

The security domain provides comprehensive security testing capabilities for code analysis, including vulnerability detection, compliance checking, and attack simulation.

## Features

### Vulnerability Detection
- SQL injection detection
- Cross-site scripting (XSS) detection
- Command injection detection
- Other common web vulnerabilities

### Compliance Checking
- Password security requirements
- Logging requirements
- Encryption requirements
- OWASP ASVS compliance

### Attack Simulation
- Path traversal attacks
- Insecure deserialization
- File upload vulnerabilities
- MITRE ATT&CK framework integration

### AI-Powered Analysis
- CodeBERT-based code analysis
- Confidence scoring
- Risk assessment
- Automated fix suggestions

### Comprehensive Reporting
- HTML reports
- PDF reports
- CSV exports
- Risk scoring
- Recommendations

## Installation

1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. Configure the domain:
- Copy `config.yaml.example` to `config.yaml`
- Adjust settings as needed

## Usage

### Basic Usage

```python
from sniffing.core.domains.security import SecuritySniffer, SecurityAnalyzer, SecurityReporter
from sniffing.utils.config import SnifferConfig

# Initialize components
config = SnifferConfig("path/to/config.yaml")
sniffer = SecuritySniffer(config)
analyzer = SecurityAnalyzer(config)
reporter = SecurityReporter(config)

# Run security testing
async def run_security_testing(files):
    # Run sniffing
    results = await sniffer.sniff_files(files)

    # Analyze results
    analysis = await analyzer.analyze_results(results)

    # Generate report
    report = await reporter.generate_report(results, analysis)

    return report
```

### Configuration

The security domain is configured through `config.yaml`:

```yaml
# Global settings
global:
  enabled: true
  parallel_jobs: 4
  cache_ttl: 3600
  workspace_path: "./workspace"
  report_path: "./reports/security"

# Vulnerability patterns
vulnerability_patterns:
  sql_injection:
    name: "SQL Injection"
    severity: "critical"
    description: "Potential SQL injection vulnerability"
    regex: "..."
    cwe: "CWE-89"
    cvss: 9.8

# Compliance rules
compliance_rules:
  password_storage:
    name: "Insecure Password Storage"
    severity: "high"
    description: "Password security requirements"
    regex: "..."
    standard: "OWASP ASVS"
    requirement: "V2.4"

# Attack patterns
attack_patterns:
  path_traversal:
    name: "Path Traversal"
    severity: "high"
    description: "Path traversal vulnerability"
    regex: "..."
    technique: "Directory traversal"
    mitre: "T1083"
```

## Components

### SecuritySniffer

The `SecuritySniffer` class performs the actual security testing:
- Scans for vulnerabilities
- Checks compliance rules
- Simulates attacks
- Calculates coverage

### SecurityAnalyzer

The `SecurityAnalyzer` class analyzes the results:
- Uses AI to analyze code
- Calculates confidence scores
- Assesses risks
- Generates findings

### SecurityReporter

The `SecurityReporter` class generates reports:
- Creates HTML/PDF/CSV reports
- Includes executive summaries
- Provides detailed findings
- Suggests remediation steps

## Testing

Run tests with pytest:
```bash
pytest test_security.py -v
```

## Metrics

The security domain collects various metrics:
- Number of issues found
- Coverage percentage
- Risk scores
- Analysis confidence
- Performance metrics

Access metrics through Prometheus:
```python
from sniffing.utils.metrics import get_metrics

metrics = get_metrics("security")
```

## Logging

Logs are written to the configured log file:
```yaml
logging:
  level: "INFO"
  format: "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
  file: "./logs/security/{name}.log"
```

## Contributing

1. Follow the code style (black, flake8, mypy)
2. Add tests for new features
3. Update documentation
4. Submit pull requests

## License

MIT License - See LICENSE file for details
