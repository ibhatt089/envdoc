# PyPI Publishing Guide for EnvDoc

This document outlines the complete process for packaging and publishing EnvDoc to PyPI.

## Prerequisites

### 1. Install Required Tools

```bash
# Install build and publishing tools
pip install --upgrade pip
pip install --upgrade build twine check-manifest

# Verify installation
python -m build --version
twine --version
check-manifest --version
```

### 2. Create PyPI Accounts

1. **PyPI Production**: Create account at `https://pypi.org/account/register/`
2. **PyPI Test**: Create account at `https://test.pypi.org/account/register/`
3. **Generate API Tokens**:
   - Go to Account Settings → API tokens
   - Create token with "Entire account" scope
   - Save tokens securely

## Automated 3-Phase Security Pipeline

EnvDoc implements a comprehensive **3-Phase Security Pipeline** for maximum safety:

### Pipeline Features

- **Phase 1: Build** - Artifact creation with integrity verification
- **Phase 2A: Test Prep** - Dynamic security test scenario generation  
- **Phase 2B: Safety Testing** - Comprehensive security validation
- **Phase 3: Publish** - Only after ALL security gates pass
- **Multi-platform**: Tests on Windows, macOS, Linux
- **Python Compatibility**: Tests Python 3.8-3.12
- **Security-first**: File protection and unauthorized modification prevention
- **PyPI Trusted Publishing**: No manual API tokens required

### Security Validation

The pipeline creates dynamic test scenarios to verify:

- No unauthorized file modifications
- Sensitive file protection (production configs, API keys)
- Boundary condition handling
- User system safety
- Permission respect and rollback capabilities

### Usage Options

1. **Release Publishing** (Recommended):

   ```bash
   # Create and push a git tag
   git tag v1.0.0
   git push origin v1.0.0
   ```

2. **Manual Workflow Dispatch**:
   - Go to GitHub Actions tab
   - Select "Publish EnvDoc to PyPI" workflow
   - Click "Run workflow"
   - Choose target: `testpypi` or `pypi`

### Setup Required

1. **Configure PyPI Trusted Publishing**:
   - Go to PyPI → Account Settings → Publishing
   - Add GitHub repository as trusted publisher
   - No API tokens needed!

2. **GitHub Environments**:
   - Create `pypi` and `testpypi` environments
   - Configure protection rules as needed

## Manual Publishing (Alternative)

If you prefer manual publishing or need to troubleshoot:

## Pre-Publication Checklist

### 1. Version Management

Ensure version consistency across all files:

```bash
# Check version in setup.py
grep "version=" setup.py

# Check version in __init__.py  
grep "__version__" envdoc/__init__.py

# Check version in CHANGELOG.md
head -20 CHANGELOG.md
```

### 2. Documentation Review

```bash
# Verify README renders correctly
python -c "import setuptools; print('Setup tools ready')"

# Check all required files exist
ls -la README.md LICENSE CHANGELOG.md MANIFEST.in requirements.txt
```

### 3. Code Quality Checks

```bash
# Run tests
python -m pytest

# Check code formatting
black --check .
flake8 .

# Test package installation locally
pip install -e .
envdoc --version
```

## Building the Package

### 1. Clean Previous Builds

```bash
# Remove previous build artifacts
rm -rf build/
rm -rf dist/
rm -rf *.egg-info/
```

### 2. Build Distribution Packages

```bash
# Build source distribution and wheel
python -m build

# Verify build artifacts
ls -la dist/
```

Expected output:

```md
dist/
├── envdoc-1.0.0-py3-none-any.whl
└── envdoc-1.0.0.tar.gz
```

### 3. Verify Package Contents

```bash
# Check wheel contents
python -m zipfile -l dist/python_envdoc-1.0.0-py3-none-any.whl

# Check source distribution
tar -tzf dist/envdoc-1.0.0.tar.gz
```

## Testing the Package

### 1. Test on PyPI Test Server

```bash
# Upload to PyPI test server
twine upload --repository testpypi dist/*

# Install from test server
pip install --index-url https://test.pypi.org/simple/ --extra-index-url https://pypi.org/simple/ envdoc

# Test installation
envdoc --version
envdoc health
```

### 2. Test in Clean Environment

```bash
# Create fresh virtual environment
python -m venv test_env
source test_env/bin/activate  # Linux/Mac
test_env\Scripts\activate     # Windows

# Install and test
pip install --index-url https://test.pypi.org/simple/ --extra-index-url https://pypi.org/simple/ envdoc
envdoc --version

# Clean up
deactivate
rm -rf test_env
```

## Publishing to PyPI

### 1. Upload to Production PyPI

```bash
# Upload to production PyPI
twine upload dist/*

# Enter your PyPI username and API token when prompted
# Username: __token__
# Password: <your-api-token>
```

### 2. Verify Publication

```bash
# Check package on PyPI
open https://pypi.org/project/envdoc/

# Install from production PyPI
pip install envdoc

# Verify installation
envdoc --version
```

## Post-Publication Steps

### 1. GitHub Release

```bash
# Tag the release
git tag v1.0.0
git push origin v1.0.0

# Create GitHub release with changelog
# Go to: https://github.com/ibhatt089/envdoc/releases/new
```

### 2. Documentation Updates

- Update GitHub Wiki with installation instructions
- Update repository README with PyPI badge
- Announce release in relevant communities

### 3. Monitoring

- Monitor PyPI download statistics
- Watch for user issues and feedback
- Prepare for next version development

## Authentication Methods

### Method 1: API Tokens (Recommended)

```bash
# Create ~/.pypirc file
cat > ~/.pypirc << EOF
[distutils]
index-servers = 
    pypi
    testpypi

[pypi]
  username = __token__
  password = <your-production-token>

[testpypi]
  repository = https://test.pypi.org/legacy/
  username = __token__
  password = <your-test-token>
EOF

# Set secure permissions
chmod 600 ~/.pypirc
```

### Method 2: Environment Variables

```bash
# Set environment variables
export TWINE_USERNAME=__token__
export TWINE_PASSWORD=<your-api-token>

# Upload without interactive prompt
twine upload dist/*
```

### Method 3: Keyring (Most Secure)

```bash
# Install keyring
pip install keyring

# Store token in keyring
keyring set https://upload.pypi.org/legacy/ __token__

# Upload (will use stored token)
twine upload dist/*
```

## Automation with GitHub Actions

Create `.github/workflows/publish.yml`:

```yaml
name: Publish to PyPI

on:
  release:
    types: [published]

jobs:
  publish:
    runs-on: ubuntu-latest
    
    steps:
    - uses: actions/checkout@v3
    
    - name: Set up Python
      uses: actions/setup-python@v4
      with:
        python-version: '3.11'
    
    - name: Install dependencies
      run: |
        python -m pip install --upgrade pip
        pip install build twine
    
    - name: Build package
      run: python -m build
    
    - name: Publish to PyPI
      env:
        TWINE_USERNAME: __token__
        TWINE_PASSWORD: ${{ secrets.PYPI_API_TOKEN }}
      run: twine upload dist/*
```

## Troubleshooting

### Common Issues

## **Build Fails**

```bash
# Check setup.py syntax
python setup.py check

# Verify all imports work
python -c "import envdoc; print('Import successful')"
```

## **Upload Fails**

```bash
# Check network connectivity
ping pypi.org

# Verify credentials
twine check dist/*
```

## **Package Not Found After Upload**

```bash
# Wait 5-10 minutes for PyPI indexing
# Check package URL directly
curl -I https://pypi.org/project/envdoc/
```

### Version Conflicts

If you need to update a version:

```bash
# Increment version in setup.py and __init__.py
# Rebuild and upload
python -m build
twine upload dist/*
```

**Note**: You cannot re-upload the same version number to PyPI.

## Security Best Practices

1. **Use API tokens** instead of passwords
2. **Enable 2FA** on PyPI account
3. **Store tokens securely** (use keyring or environment variables)
4. **Never commit tokens** to version control
5. **Use separate tokens** for different projects
6. **Regularly rotate tokens**

## Version Management Strategy

```bash
# Development versions
1.0.0.dev1, 1.0.0.dev2, ...

# Release candidates  
1.0.0rc1, 1.0.0rc2, ...

# Production releases
1.0.0, 1.0.1, 1.1.0, 2.0.0
```

## Final Checklist

Before publishing:

- [ ] Version numbers match across all files
- [ ] README.md is professional and complete
- [ ] CHANGELOG.md is updated
- [ ] All tests pass
- [ ] Package builds without errors
- [ ] Test installation works
- [ ] Documentation is accurate
- [ ] License file is included
- [ ] API tokens are ready
- [ ] Git repository is clean and pushed

After publishing:

- [ ] Package appears on PyPI
- [ ] Installation from PyPI works
- [ ] GitHub release is created
- [ ] Documentation is updated
- [ ] Community is notified

---

**Ready to publish? Run the complete workflow:**

```bash
# 1. Final checks
python -m pytest
black --check .
flake8 .

# 2. Build
rm -rf build dist *.egg-info
python -m build

# 3. Test
twine upload --repository testpypi dist/*

# 4. Publish
twine upload dist/*

# 5. Verify
pip install envdoc
envdoc --version
```
