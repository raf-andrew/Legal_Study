# Master Control Program (MCP)

The Master Control Program (MCP) is a comprehensive code analysis and testing infrastructure that provides centralized orchestration, test scheduling, and quality assurance capabilities.

## Features

### Core Infrastructure

1. **Test Orchestration**
   - File-level test isolation
   - Domain-specific test scheduling
   - Resource allocation and management
   - Result aggregation and analysis
   - Fix generation and validation

2. **API Integration**
   - Endpoint registration and discovery
   - Contract validation
   - Performance testing
   - Security scanning
   - Documentation generation

3. **Git Integration**
   - Pre-commit hooks
   - Branch protection
   - CI/CD pipeline coupling
   - Automated fix commits
   - Version tracking

### Domain Coverage

1. **Security Domain**
   - Vulnerability detection
   - Compliance checking
   - Attack simulation
   - AI-powered analysis
   - Automated fixes

2. **Browser Domain**
   - Cross-browser testing
   - Performance analysis
   - UI/UX validation
   - Accessibility checking
   - Mobile compatibility

3. **Functional Domain**
   - Integration testing
   - E2E testing
   - API validation
   - Performance testing
   - User flow analysis

4. **Unit Domain**
   - Code coverage
   - Dependency analysis
   - Mock integration
   - Test generation
   - Performance profiling

5. **Documentation Domain**
   - Quality checking
   - Completeness validation
   - Style enforcement
   - Reference verification
   - AI-powered improvements

## Installation

1. Create virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # or `venv\Scripts\activate` on Windows
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Configure MCP:
```bash
cp config.yaml.example config.yaml
# Edit config.yaml with your settings
```

## Usage

### Basic Usage

```python
from mcp.server.orchestrator import MCPOrchestrator
from mcp.utils.config import MCPConfig

# Initialize MCP
config = MCPConfig("path/to/config.yaml")
orchestrator = MCPOrchestrator(config)

# Start MCP
await orchestrator.start()

# Schedule job
job_id = await orchestrator.schedule_job(
    "sniff",
    files=["file1.py", "file2.py"],
    domains=["security", "functional"],
    priority=1
)

# Get job status
status = await orchestrator.get_job_status(job_id)

# Stop MCP
await orchestrator.stop()
```

### Configuration

The MCP is configured through `config.yaml`:

```yaml
# Global settings
global:
  workspace_path: "./workspace"
  job_path: "./jobs"
  isolation_path: "./isolations"
  analysis_path: "./analysis"
  fix_path: "./fixes"
  report_path: "./reports"
  parallel_jobs: 4
  cache_ttl: 3600

# Domain settings
domains:
  security:
    enabled: true
    sniffer:
      patterns_path: "./patterns/security"
      rules_path: "./rules/security"
      simulations_path: "./simulations/security"
    analyzer:
      model_name: "microsoft/codebert-base"
      confidence_threshold: 0.8
    fixer:
      model_name: "microsoft/codebert-base"
      confidence_threshold: 0.9
```

## Components

### MCPOrchestrator

The `MCPOrchestrator` class handles:
- Test scheduling and management
- Resource allocation
- Result processing
- Fix generation
- Health monitoring

### MCPIsolator

The `MCPIsolator` class provides:
- File isolation
- Environment setup
- Resource cleanup
- Test isolation
- Result collection

### MCPAnalyzer

The `MCPAnalyzer` class performs:
- Result analysis
- Pattern detection
- Risk assessment
- Fix suggestion
- Report generation

### MCPFixer

The `MCPFixer` class manages:
- Fix generation
- Code modification
- Validation
- Rollback
- Documentation

## Integration

### Git Integration

```python
from mcp.utils.git import GitIntegration

# Initialize Git integration
git = GitIntegration(config)

# Get changed files
files = git.get_changed_files()

# Create branch
git.create_branch("feature/new-feature")

# Commit changes
git.commit_changes("Fix security issues", files=files)
```

### API Integration

```python
from mcp.utils.api import APIIntegration

# Initialize API integration
api = APIIntegration(config)

# Test endpoint
results = await api.test_endpoint(
    "GET",
    "https://api.example.com/users",
    expected_status=200
)

# Validate contract
contract = await api.load_contract("api.yaml")
validation = await api.validate_contract(contract, "https://api.example.com")
```

### CI/CD Integration

```python
from mcp.utils.ci_cd import CICDIntegration

# Initialize CI/CD integration
ci_cd = CICDIntegration(config)

# Run pipeline
results = await ci_cd.run_pipeline(
    pipeline={"stages": {...}},
    context={"files": files}
)
```

## Development

1. Install development dependencies:
```bash
pip install -r requirements-dev.txt
```

2. Run tests:
```bash
pytest tests/
```

3. Check code style:
```bash
black .
flake8 .
mypy .
```

4. Generate documentation:
```bash
mkdocs serve
```

## Contributing

1. Fork the repository
2. Create feature branch
3. Make changes
4. Run tests
5. Submit pull request

## License

MIT License - See LICENSE file for details
