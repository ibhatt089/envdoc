"""
EnvDoctor - Complete Environment Variable Management Suite

Automatically detects, analyzes, and fixes environment variable issues across:
- System environment variables
- .env and configuration files  
- Python code usage patterns
- Cross-platform compatibility

Features:
- Smart .env file creation and management
- System vs file environment variable comparison
- Interactive fixing with multiple action options
- Complete environment variable lifecycle management

Author: Ishan Bhatt
License: MIT
"""

__version__ = "1.0.0"
__author__ = "Ishan Bhatt"
__email__ = "bhatt.ish89@gmail.com"

from .scanner import EnhancedEnvScanner
from .analyzer import EnhancedEnvAnalyzer
from .fixer import EnhancedEnvFixer
from .manager import EnvManager
from .cli import main

__all__ = [
    "EnhancedEnvScanner",
    "EnhancedEnvAnalyzer", 
    "EnhancedEnvFixer",
    "EnvManager",
    "main"
]
