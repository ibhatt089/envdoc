# EnvDoc - Smart Environment Variable Management

[![Python Version](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![PyPI version](https://badge.fury.io/py/envdoc.svg)](https://badge.fury.io/py/envdoc)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Cross-Platform](https://img.shields.io/badge/platform-Windows%20%7C%20macOS%20%7C%20Linux-lightgrey)](https://github.com/ibhatt089/envdoc)

**Automatically detect, analyze, and fix environment variable issues across your entire codebase.**

EnvDoc is a comprehensive tool that scans your project for environment variable usage, compares it against system and file-based configuration, and provides intelligent fixing capabilities with multiple action options.

## Why EnvDoc?

Environment variable mismatches are a common source of application failures that can be difficult to debug. They cause:

- **Silent failures** in production environments
- **Hard-to-debug issues** across different environments  
- **Inconsistent configurations** between team members
- **Time-consuming troubleshooting** sessions

## **EnvDoc solves this by providing:**

- Intelligent detection of naming inconsistencies
- Smart suggestions with confidence scoring
- Multiple fix options (interactive, batch, dry-run)
- System environment integration for complete visibility
- Health scoring to track configuration improvements

## Installation

Install from PyPI (recommended):

```bash
pip install envdoc
```

Install with optional interactive dependencies:

```bash
pip install envdoc[interactive]
```

Verify installation:

```bash
envdoc --version
```

## Complete Package Structure

```tree
envdoc/ (Ready for GitHub)
├── .github/workflows/
│   └── build-test-publish.yml      # 🔒 3-Phase Security Pipeline
├── tests/                          # 🧪 Comprehensive test suite
│   ├── test_scanner.py             # Scanner validation
│   ├── test_analyzer.py            # Analyzer testing  
│   └── test_cli.py                 # CLI interface tests
├── envdoc/                         # 🐍 Core package
│   ├── __init__.py                 # v1.0.0
│   ├── cli.py                      # Command interface
│   ├── analyzer.py                 # Environment analysis
│   ├── scanner.py                  # Code scanning  
│   ├── fixer.py                    # Safe fixing
│   └── manager.py                  # Environment management
├── SECURITY_PIPELINE.md            # 🛡️ Security documentation
├── pyproject.toml                  # 🏗️ Modern packaging
├── pytest.ini                     # 🧪 Test configuration
├── run_tests.py                    # 🔍 Local test runner
├── README.md                       # 📚 Professional docs
├── CHANGELOG.md                    # 📋 Enhanced with security info
├── PUBLISHING.md                   # 🚀 Updated pipeline guide
├── LICENSE                         # ⚖️ MIT license
└── MANIFEST.in                     # 📁 Complete file manifest
```

## Quick Start

```bash
# Quick health check
envdoc health

# Comprehensive analysis  
envdoc analyze --detailed

# Interactive fixing
envdoc fix

# Smart .env setup
envdoc setup

# Complete diagnostic
envdoc doctor --fix-suggestions
```

## Core Features

### Comprehensive Detection

- **Multi-format Support**: Detects variables in `.env`, `docker-compose.yml`, `Dockerfile`, YAML configs
- **Code Pattern Recognition**: Finds `os.getenv()`, `os.environ[]`, and custom environment functions
- **Framework Integration**: Works with Django, Flask, FastAPI, and other frameworks
- **System Environment**: Detects system-level environment variables

### Intelligent Analysis

- **Pattern Matching**: Uses advanced algorithms to detect common naming patterns
- **Issue Categorization**: Classifies problems as typos, missing variables, or naming inconsistencies
- **Cross-Source Comparison**: Analyzes system vs file vs code usage
- **Sensitive Variable Detection**: Automatically identifies secrets and passwords

### Flexible Fixing

- **Interactive Mode**: Provides guided fixing with multiple options for each issue
- **Batch Mode**: Automatically fixes high-confidence issues
- **Dry-Run Support**: Preview changes before applying them
- **Safe Operations**: Creates automatic backups before modifications

### Professional Reporting

- **Health Scoring**: Tracks configuration quality over time
- **Detailed Analytics**: Provides comprehensive issue breakdown
- **Export Options**: Supports JSON, YAML, and text output formats

## Command Reference

### Health and Analysis

```bash
# Quick health check
envdoc health

# Show only numeric score (useful for CI/CD)
envdoc health --score-only

# Detailed analysis with suggestions
envdoc analyze --detailed

# Save analysis report to file
envdoc analyze --report health-report.txt
```

### Fixing Issues

```bash
# Interactive fixing (recommended for first-time users)
envdoc fix

# Batch fixing with high confidence threshold (90%+)
envdoc fix --batch

# Batch fixing with medium confidence threshold (80%+)
envdoc fix --batch --confidence 0.8
```

### Environment Management

```bash
# Smart .env file creation from .env.example
envdoc setup

# Complete environment overview
envdoc manage --show-system --show-files

# Show sensitive variables (use with caution)
envdoc manage --show-sensitive
```

### Scanning and Diagnostics

```bash
# Scan specific directory
envdoc scan /path/to/project

# Export scan results as JSON
envdoc scan --output-format json --save-results results.json

# Comprehensive diagnostic with fix suggestions
envdoc doctor --fix-suggestions
```

### Global Options

```bash
# Specify project root directory
envdoc --project-root /path/to/project health

# Enable verbose output for debugging
envdoc --verbose analyze

# Preview changes without applying them
envdoc --dry-run fix --batch
```

## Usage Examples

### Basic Workflow

1. **Initial Setup**: Create `.env` file from template

   ```bash
   envdoc setup
   ```

2. **Health Check**: Assess current configuration

   ```bash
   envdoc health
   ```

3. **Analysis**: Get detailed issue breakdown

   ```bash
   envdoc analyze --detailed
   ```

4. **Fix Issues**: Apply corrections

   ```bash
   envdoc fix --batch --confidence 0.9
   ```

### CI/CD Integration

**GitHub Actions Example:**

```yaml
name: Environment Variable Health Check
on: [push, pull_request]

jobs:
  env-check:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - name: Set up Python
        uses: actions/setup-python@v2
        with:
          python-version: 3.9
      - name: Install EnvDoctor
        run: pip install envdoc
      - name: Run health check
        run: |
          score=$(envdoc health --score-only)
          echo "Environment health score: $score%"
          if [ $(echo "$score < 70" | bc) -eq 1 ]; then
            echo "Environment health too low"
            envdoc analyze --detailed
            exit 1
          fi
```

**Docker Integration:**

```dockerfile
FROM python:3.11-alpine
RUN pip install envdoc
COPY . /app
WORKDIR /app
RUN envdoc setup && \
    envdoc fix --batch --confidence 0.9 && \
    envdoc health
```

## Cross-Platform Support

### Supported Platforms

- **Windows**: Windows 10, 11 and later
- **macOS**: macOS 10.14 and later
- **Linux**: Ubuntu, CentOS, Debian, Alpine, and other distributions

### Python Compatibility

- **Python 3.8+**: Full support and testing
- **PyPy 3.8+**: Compatible

### Framework Support

- **Web Frameworks**: Django, Flask, FastAPI, Tornado
- **Data Science**: Pandas, NumPy, Jupyter notebooks
- **Cloud Platforms**: AWS, Azure, GCP integrations
- **Containers**: Docker, Kubernetes
- **CI/CD**: GitHub Actions, GitLab CI, Jenkins

## Advanced Features

### Pattern Recognition

EnvDoctor automatically detects common environment variable naming patterns:

```python
# These variations are automatically recognized:
DATABASE_HOST     <-> DB_HOST <-> POSTGRES_HOST
DATABASE_USER     <-> DB_USER <-> POSTGRES_USER  
DATABASE_PASSWORD <-> DB_PASSWORD <-> DB_PASS
API_KEY          <-> API_TOKEN <-> API_SECRET
REDIS_URL        <-> REDIS_ENDPOINT <-> REDIS_URI
```

### Confidence Scoring

Issues are ranked by confidence level for intelligent processing:

- **90-100%**: Obvious typos and naming mistakes (auto-fixable)
- **70-89%**: High-confidence suggestions (recommended for batch fixing)
- **50-69%**: Medium-confidence alternatives (manual review recommended)
- **Below 50%**: Low-confidence suggestions (manual review required)

### Health Scoring

The health score is calculated using the following formula:

```md
Health Score = (Perfect Matches + Available Variables) / Total Variables Used × 100%

Factors considered:
✓ Perfect matches between code and environment
✓ Variables available in system or files
✗ Missing variables
✗ Naming inconsistencies
✗ Unused definitions
```

## Development Pipeline

### Current Release (v1.0.0)

- Complete environment variable detection and analysis
- Interactive and batch fixing capabilities
- Smart .env file management
- Cross-platform CLI interface
- Health scoring and reporting

### Upcoming Features (v1.1.0)

- Enhanced pattern recognition with machine learning
- Performance optimizations for large codebases
- Extended configuration file format support
- Improved error reporting and logging

### Future Roadmap (v1.2.0+)

- Web-based dashboard for team collaboration
- IDE extensions for popular editors (VS Code, PyCharm)
- Multi-language support (JavaScript, Go, Java, .NET)
- Cloud service integrations (AWS Secrets Manager, Azure Key Vault)
- Advanced analytics and historical trending

## Contributing

We welcome contributions! Here's how to get started:

### Modern Build System & Security

EnvDoc uses modern Python packaging standards with comprehensive security:

- **pyproject.toml**: All package configuration in one file
- **3-Phase Security Pipeline**: Build → Test → Publish with safety validation
- **Cross-platform**: Automated testing on Windows, macOS, and Linux  
- **Multi-version**: Testing across Python 3.8-3.12
- **Security-first**: Comprehensive safety testing before any release
- **File Protection**: Advanced validation to prevent unauthorized modifications

See [SECURITY_PIPELINE.md](SECURITY_PIPELINE.md) for detailed security information.

### Development Setup

```bash
# Clone the repository
git clone https://github.com/ibhatt089/envdoc.git
cd envdoc

# Create virtual environment
python -m venv venv
source venv/bin/activate  # Linux/Mac
venv\Scripts\activate     # Windows

# Install development dependencies
pip install -e ".[dev]"

# Run tests
pytest

# Format code
black .
flake8 .
```

### Contribution Guidelines

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/feature-name`)
3. Make your changes with appropriate tests
4. Ensure code passes all checks (`pytest`, `black`, `flake8`)
5. Commit changes with clear messages
6. Push to your fork and create a Pull Request

## Troubleshooting

### Common Issues

## **ModuleNotFoundError**

```bash
# Reinstall the package
pip uninstall python-envdoc
pip install python-envdoc
```

## **Permission Issues on Windows**

```bash
# Install with user flag
pip install --user python-envdoc
```

## **Rich Output Issues**

```bash
# Install with interactive dependencies
pip install python-envdoc[interactive]
```

## **No Issues Detected**

```bash
# Verify you're in the correct directory
envdoc --verbose --project-root /correct/path health
```

## Support

- **Documentation**: [GitHub Wiki](https://github.com/ibhatt089/envdoc/wiki)
- **Bug Reports**: [GitHub Issues](https://github.com/ibhatt089/envdoc/issues)
- **Feature Requests**: [GitHub Discussions](https://github.com/ibhatt089/envdoc/discussions)
- **Email**: [ibhatt89@outlook.com](mailto:ibhatt89@outlook.com)

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Author

**Ishan Bhatt** - Software Engineer with expertise in DevOps automation and developer tooling.

- GitHub: [@ibhatt089](https://github.com/ibhatt089)
- Email: [ibhatt89@outlook.com](mailto:ibhatt89@outlook.com)

---

### **Made with Python • Cross-Platform • Open Source**

---
