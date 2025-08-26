"""
Enhanced Environment Variable Scanner
Finds all environment variable usage patterns in Python code
and compares against system and file-based environment sources
"""

import ast
import re
import os
from pathlib import Path
from typing import Dict, List, Set, Tuple, Optional, Any
from dataclasses import dataclass
import fnmatch

@dataclass
class EnvUsage:
    """Represents a usage of an environment variable in code"""
    file_path: str
    line_number: int
    column: int
    variable_name: str
    access_method: str  # 'os.getenv', 'os.environ', 'dotenv', etc.
    has_default: bool
    default_value: Optional[str]
    context_line: str
    function_name: Optional[str] = None  # Function/method where it's used
    class_name: Optional[str] = None     # Class where it's used

@dataclass
class EnvDefinition:
    """Represents a definition of an environment variable"""
    file_path: str
    line_number: int
    variable_name: str
    value: str
    source_type: str  # 'file', 'system', 'shell'
    is_example: bool = False
    is_sensitive: bool = False  # Contains secrets/passwords

@dataclass
class ScanResult:
    """Complete scan results"""
    usages: List[EnvUsage]
    definitions: List[EnvDefinition]
    system_variables: Dict[str, str]
    file_variables: Dict[str, Dict[str, str]]  # filename -> variables
    usage_stats: Dict[str, Any]

class EnhancedEnvScanner:
    """
    Enhanced Environment Variable Scanner
    Scans code, system environment, and configuration files
    """
    
    # Enhanced patterns for environment variable detection
    ENV_PATTERNS = [
        # Standard os.getenv patterns
        r'os\.getenv\s*\(\s*[\'"]([^\'"\)]+)[\'"]',
        r'getenv\s*\(\s*[\'"]([^\'"\)]+)[\'"]',
        
        # os.environ patterns  
        r'os\.environ\s*\[\s*[\'"]([^\'"\]]+)[\'"]',
        r'environ\s*\[\s*[\'"]([^\'"\]]+)[\'"]',
        r'os\.environ\.get\s*\(\s*[\'"]([^\'"\)]+)[\'"]',
        r'environ\.get\s*\(\s*[\'"]([^\'"\)]+)[\'"]',
        
        # Custom environment functions
        r'get_env\s*\(\s*[\'"]([^\'"\)]+)[\'"]',
        r'env_var\s*\(\s*[\'"]([^\'"\)]+)[\'"]',
        r'get_setting\s*\(\s*[\'"]([^\'"\)]+)[\'"]',
        r'config\.get\s*\(\s*[\'"]([^\'"\)]+)[\'"]',
        r'get_config\s*\(\s*[\'"]([^\'"\)]+)[\'"]',
        
        # Framework-specific patterns
        # Django
        r'settings\.[A-Z_][A-Z_0-9]*',
        # Flask
        r'app\.config\[[\'"]([^\'"\]]+)[\'"]\]',
        r'config\[[\'"]([^\'"\]]+)[\'"]\]',
        # FastAPI/Pydantic
        r'Field\(.*env=[\'"]([^\'"\)]+)[\'"]',
        # Config classes
        r'Config\.[A-Z_][A-Z_0-9]*',
        
        # Docker and container patterns
        r'ENV\s+([A-Z_][A-Z_0-9]*)',
        
        # Shell script patterns in Python strings
        r'\$\{([A-Z_][A-Z_0-9]*)\}',
        r'\$([A-Z_][A-Z_0-9]*)',
        
        # String interpolation patterns
        r'f[\'"][^\'\"]*\{[^}]*([A-Z_][A-Z_0-9]*)[^}]*\}',
        
        # Direct uppercase string references (less reliable but common)
        r'[\'"]([A-Z][A-Z_0-9]{2,})[\'"]',
    ]
    
    # File patterns to include/exclude
    INCLUDE_PATTERNS = [
        '*.py', '*.pyx', '*.pyi',
        '*.yml', '*.yaml',  # Docker compose, CI/CD
        'Dockerfile', 'Dockerfile.*',
        '*.sh', '*.bash', '*.zsh',  # Shell scripts
        '*.json',  # Config files
    ]
    
    EXCLUDE_PATTERNS = [
        '__pycache__/*', '.git/*', '.svn/*', '*.pyc', '*.pyo',
        'build/*', 'dist/*', '.tox/*', '.pytest_cache/*',
        'node_modules/*', '.env', '.env.*', 'venv/*', 'env/*', '.venv/*',
        '*.min.js', '*.bundle.js',  # Minified files
    ]
    
    ENV_FILE_PATTERNS = [
        '.env*', 'env.*', '*.env',
        'docker-compose.yml', 'docker-compose.yaml',
        'docker-compose.*.yml', 'docker-compose.*.yaml',
        '.github/workflows/*.yml', '.github/workflows/*.yaml',
        '.gitlab-ci.yml', 'azure-pipelines.yml',
        'Dockerfile*', '*.Dockerfile',
    ]
    
    # Sensitive variable patterns
    SENSITIVE_PATTERNS = [
        'password', 'passwd', 'pwd', 'secret', 'key', 'token', 'auth',
        'credential', 'private', 'cert', 'ssl', 'api_key', 'access_key'
    ]
    
    def __init__(self, project_root: str):
        self.project_root = Path(project_root)
        self.usages: List[EnvUsage] = []
        self.definitions: List[EnvDefinition] = []
        self.system_vars = dict(os.environ)
        
    def scan_everything(self) -> ScanResult:
        """Scan everything: code, files, and system environment"""
        print(f"🔍 Enhanced scanning of project: {self.project_root}")
        
        # 1. Scan Python files for usage
        code_usages = self._scan_code_files()
        
        # 2. Scan configuration files for definitions
        file_definitions = self._scan_config_files()
        
        # 3. Get system environment variables
        system_definitions = self._get_system_definitions()
        
        # 4. Combine all definitions
        all_definitions = file_definitions + system_definitions
        
        # 5. Calculate usage statistics
        stats = self._calculate_usage_stats(code_usages, all_definitions)
        
        # 6. Build file variables mapping
        file_vars = self._build_file_variables_mapping(file_definitions)
        
        self.usages = code_usages
        self.definitions = all_definitions
        
        return ScanResult(
            usages=code_usages,
            definitions=all_definitions,
            system_variables=self.system_vars,
            file_variables=file_vars,
            usage_stats=stats
        )
    
    def _scan_code_files(self) -> List[EnvUsage]:
        """Scan all code files for environment variable usage"""
        usages = []
        
        # Find all code files
        code_files = []
        for pattern in self.INCLUDE_PATTERNS:
            if pattern.startswith('*'):
                code_files.extend(self.project_root.rglob(pattern))
            else:
                code_files.extend(self.project_root.glob(f"**/{pattern}"))
        
        # Filter files
        filtered_files = []
        for file_path in code_files:
            if file_path.is_file() and self._should_scan_file(file_path):
                filtered_files.append(file_path)
        
        print(f"📁 Found {len(filtered_files)} code files to scan")
        
        # Scan each file
        for file_path in filtered_files:
            try:
                file_usages = self._scan_single_file(file_path)
                usages.extend(file_usages)
            except Exception as e:
                print(f"⚠️ Error scanning {file_path}: {e}")
        
        print(f"🔍 Found {len(usages)} environment variable usages")
        return usages
    
    def _should_scan_file(self, file_path: Path) -> bool:
        """Check if file should be scanned"""
        rel_path = str(file_path.relative_to(self.project_root))
        
        # Check exclude patterns
        for pattern in self.EXCLUDE_PATTERNS:
            if fnmatch.fnmatch(rel_path, pattern):
                return False
        
        return True
    
    def _scan_single_file(self, file_path: Path) -> List[EnvUsage]:
        """Scan a single file for environment variable usage"""
        usages = []
        
        try:
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()
                lines = content.splitlines()
        except Exception as e:
            print(f"⚠️ Cannot read {file_path}: {e}")
            return usages
        
        # Try AST parsing for Python files
        if file_path.suffix == '.py':
            try:
                tree = ast.parse(content)
                visitor = EnhancedEnvVariableVisitor(str(file_path), lines)
                visitor.visit(tree)
                usages.extend(visitor.usages)
            except SyntaxError:
                # Fallback to regex for invalid Python syntax
                usages.extend(self._scan_with_regex(file_path, content, lines))
        else:
            # Use regex for non-Python files
            usages.extend(self._scan_with_regex(file_path, content, lines))
        
        return usages
    
    def _scan_with_regex(self, file_path: Path, content: str, lines: List[str]) -> List[EnvUsage]:
        """Scan using regex patterns"""
        usages = []
        
        for pattern in self.ENV_PATTERNS:
            for match in re.finditer(pattern, content, re.MULTILINE):
                groups = match.groups()
                if groups:
                    var_name = groups[0]
                    
                    # Skip if it's obviously not an environment variable
                    if not self._looks_like_env_var(var_name):
                        continue
                    
                    line_num = content[:match.start()].count('\n') + 1
                    col_offset = match.start() - content.rfind('\n', 0, match.start()) - 1
                    
                    usage = EnvUsage(
                        file_path=str(file_path),
                        line_number=line_num,
                        column=col_offset,
                        variable_name=var_name,
                        access_method='regex_detected',
                        has_default=False,
                        default_value=None,
                        context_line=lines[line_num - 1] if line_num <= len(lines) else ""
                    )
                    usages.append(usage)
        
        return usages
    
    def _looks_like_env_var(self, var_name: str) -> bool:
        """Check if string looks like an environment variable name"""
        # Must be uppercase with underscores, at least 2 characters
        if len(var_name) < 2:
            return False
        
        if not re.match(r'^[A-Z][A-Z0-9_]*$', var_name):
            return False
        
        # Skip common non-env patterns
        exclude_patterns = [
            'HTTP_', 'HTTPS_', 'GET', 'POST', 'PUT', 'DELETE',  # HTTP methods
            'SQL', 'SELECT', 'INSERT', 'UPDATE', 'DELETE',      # SQL keywords
            'TRUE', 'FALSE', 'NULL', 'NONE',                    # Constants
        ]
        
        if any(var_name.startswith(pattern) for pattern in exclude_patterns):
            return False
        
        return True
    
    def _scan_config_files(self) -> List[EnvDefinition]:
        """Scan configuration files for environment variable definitions"""
        definitions = []
        
        # Find config files
        config_files = []
        for pattern in self.ENV_FILE_PATTERNS:
            config_files.extend(self.project_root.rglob(pattern))
        
        print(f"📄 Found {len(config_files)} configuration files")
        
        for file_path in config_files:
            if file_path.is_file():
                try:
                    file_definitions = self._parse_config_file(file_path)
                    definitions.extend(file_definitions)
                except Exception as e:
                    print(f"⚠️ Error parsing {file_path}: {e}")
        
        print(f"📄 Found {len(definitions)} file-based variable definitions")
        return definitions
    
    def _parse_config_file(self, file_path: Path) -> List[EnvDefinition]:
        """Parse configuration file for environment variable definitions"""
        definitions = []
        
        if file_path.name.startswith('.env') or file_path.name.endswith('.env'):
            # .env file format
            definitions = self._parse_env_file(file_path)
        elif file_path.name.startswith('docker-compose'):
            # Docker compose file
            definitions = self._parse_docker_compose(file_path)
        elif file_path.name.startswith('Dockerfile'):
            # Dockerfile
            definitions = self._parse_dockerfile(file_path)
        elif file_path.suffix in ['.yml', '.yaml']:
            # YAML files (CI/CD configs)
            definitions = self._parse_yaml_env_vars(file_path)
        
        return definitions
    
    def _parse_env_file(self, file_path: Path) -> List[EnvDefinition]:
        """Parse .env file format"""
        definitions = []
        is_example = 'example' in file_path.name or 'sample' in file_path.name
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                lines = f.readlines()
            
            for line_num, line in enumerate(lines, 1):
                line = line.strip()
                
                if not line or line.startswith('#'):
                    continue
                
                if '=' in line:
                    key, value = line.split('=', 1)
                    key = key.strip()
                    value = value.strip().strip('"').strip("'")
                    
                    is_sensitive = any(pattern in key.lower() for pattern in self.SENSITIVE_PATTERNS)
                    
                    definition = EnvDefinition(
                        file_path=str(file_path),
                        line_number=line_num,
                        variable_name=key,
                        value=value,
                        source_type='file',
                        is_example=is_example,
                        is_sensitive=is_sensitive
                    )
                    definitions.append(definition)
        
        except Exception as e:
            print(f"⚠️ Error parsing env file {file_path}: {e}")
        
        return definitions
    
    def _parse_docker_compose(self, file_path: Path) -> List[EnvDefinition]:
        """Parse Docker Compose file for environment variables"""
        definitions = []
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Simple regex to find environment variables
            # This is a basic implementation - would need yaml parsing for full accuracy
            env_patterns = [
                r'environment:\s*\n((?:\s+-\s+[A-Z_][A-Z0-9_]*=.*\n)*)',
                r'-\s+([A-Z_][A-Z0-9_]*=[^\n]*)',
            ]
            
            for pattern in env_patterns:
                for match in re.finditer(pattern, content, re.MULTILINE):
                    # Extract environment variables from match
                    # This is simplified - real implementation would be more robust
                    pass
        
        except Exception as e:
            print(f"⚠️ Error parsing docker-compose {file_path}: {e}")
        
        return definitions
    
    def _parse_dockerfile(self, file_path: Path) -> List[EnvDefinition]:
        """Parse Dockerfile for ENV declarations"""
        definitions = []
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                lines = f.readlines()
            
            for line_num, line in enumerate(lines, 1):
                line = line.strip()
                
                if line.startswith('ENV '):
                    # Parse ENV KEY=value or ENV KEY value
                    env_part = line[4:].strip()
                    
                    if '=' in env_part:
                        key, value = env_part.split('=', 1)
                    else:
                        parts = env_part.split(None, 1)
                        if len(parts) == 2:
                            key, value = parts
                        else:
                            continue
                    
                    key = key.strip()
                    value = value.strip().strip('"').strip("'")
                    
                    is_sensitive = any(pattern in key.lower() for pattern in self.SENSITIVE_PATTERNS)
                    
                    definition = EnvDefinition(
                        file_path=str(file_path),
                        line_number=line_num,
                        variable_name=key,
                        value=value,
                        source_type='file',
                        is_example=False,
                        is_sensitive=is_sensitive
                    )
                    definitions.append(definition)
        
        except Exception as e:
            print(f"⚠️ Error parsing Dockerfile {file_path}: {e}")
        
        return definitions
    
    def _parse_yaml_env_vars(self, file_path: Path) -> List[EnvDefinition]:
        """Parse YAML files for environment variable references"""
        definitions = []
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Look for environment variable patterns in YAML
            env_patterns = [
                r'\$\{([A-Z_][A-Z0-9_]*)\}',  # ${VAR_NAME}
                r'\$([A-Z_][A-Z0-9_]*)',       # $VAR_NAME
                r'env:\s*([A-Z_][A-Z0-9_]*)', # env: VAR_NAME
            ]
            
            for pattern in env_patterns:
                for match in re.finditer(pattern, content):
                    var_name = match.group(1)
                    line_num = content[:match.start()].count('\n') + 1
                    
                    # This creates a "reference" definition, not a value definition
                    definition = EnvDefinition(
                        file_path=str(file_path),
                        line_number=line_num,
                        variable_name=var_name,
                        value="",  # No value in reference
                        source_type='file',
                        is_example=False,
                        is_sensitive=False
                    )
                    definitions.append(definition)
        
        except Exception as e:
            print(f"⚠️ Error parsing YAML {file_path}: {e}")
        
        return definitions
    
    def _get_system_definitions(self) -> List[EnvDefinition]:
        """Get system environment variable definitions"""
        definitions = []
        
        for var_name, var_value in self.system_vars.items():
            is_sensitive = any(pattern in var_name.lower() for pattern in self.SENSITIVE_PATTERNS)
            
            definition = EnvDefinition(
                file_path="<system>",
                line_number=0,
                variable_name=var_name,
                value=var_value,
                source_type='system',
                is_example=False,
                is_sensitive=is_sensitive
            )
            definitions.append(definition)
        
        print(f"🖥️ Found {len(definitions)} system environment variables")
        return definitions
    
    def _calculate_usage_stats(self, usages: List[EnvUsage], definitions: List[EnvDefinition]) -> Dict[str, Any]:
        """Calculate comprehensive usage statistics"""
        used_vars = set(usage.variable_name for usage in usages)
        defined_vars = set(defn.variable_name for defn in definitions)
        system_vars = set(defn.variable_name for defn in definitions if defn.source_type == 'system')
        file_vars = set(defn.variable_name for defn in definitions if defn.source_type == 'file')
        
        return {
            'total_usages': len(usages),
            'unique_variables_used': len(used_vars),
            'total_definitions': len(definitions),
            'unique_variables_defined': len(defined_vars),
            'system_variables': len(system_vars),
            'file_variables': len(file_vars),
            'perfect_matches': len(used_vars & defined_vars),
            'missing_definitions': len(used_vars - defined_vars),
            'unused_definitions': len(defined_vars - used_vars),
            'files_with_usage': len(set(usage.file_path for usage in usages)),
            'config_files_found': len(set(defn.file_path for defn in definitions if defn.source_type == 'file')),
        }
    
    def _build_file_variables_mapping(self, definitions: List[EnvDefinition]) -> Dict[str, Dict[str, str]]:
        """Build mapping of files to their variables"""
        file_vars = {}
        
        for defn in definitions:
            if defn.source_type == 'file':
                filename = Path(defn.file_path).name
                if filename not in file_vars:
                    file_vars[filename] = {}
                file_vars[filename][defn.variable_name] = defn.value
        
        return file_vars


class EnhancedEnvVariableVisitor(ast.NodeVisitor):
    """Enhanced AST visitor for finding environment variable usage"""
    
    def __init__(self, file_path: str, lines: List[str]):
        self.file_path = file_path
        self.lines = lines
        self.usages: List[EnvUsage] = []
        self.current_function = None
        self.current_class = None
    
    def visit_FunctionDef(self, node: ast.FunctionDef):
        """Track current function context"""
        old_function = self.current_function
        self.current_function = node.name
        self.generic_visit(node)
        self.current_function = old_function
    
    def visit_ClassDef(self, node: ast.ClassDef):
        """Track current class context"""
        old_class = self.current_class
        self.current_class = node.name
        self.generic_visit(node)
        self.current_class = old_class
    
    def visit_Call(self, node: ast.Call):
        """Visit function calls to detect env var access"""
        
        # Handle os.getenv(), os.environ.get(), etc.
        if isinstance(node.func, ast.Attribute):
            if isinstance(node.func.value, ast.Attribute):
                # os.environ.get()
                if (isinstance(node.func.value.value, ast.Name) and
                    node.func.value.value.id == 'os' and
                    node.func.value.attr == 'environ' and
                    node.func.attr == 'get'):
                    self._extract_env_usage(node, 'os.environ.get')
            elif isinstance(node.func.value, ast.Name):
                # os.getenv()
                if (node.func.value.id == 'os' and 
                    node.func.attr == 'getenv'):
                    self._extract_env_usage(node, 'os.getenv')
                # environ.get() (if imported directly)
                elif (node.func.value.id == 'environ' and 
                      node.func.attr == 'get'):
                    self._extract_env_usage(node, 'environ.get')
        
        # Handle direct function calls
        elif isinstance(node.func, ast.Name):
            if node.func.id in ['getenv', 'get_env', 'env_var', 'get_setting', 'get_config']:
                self._extract_env_usage(node, node.func.id)
        
        self.generic_visit(node)
    
    def visit_Subscript(self, node: ast.Subscript):
        """Visit subscript access like os.environ['KEY']"""
        
        if isinstance(node.value, ast.Attribute):
            # os.environ['KEY']
            if (isinstance(node.value.value, ast.Name) and
                node.value.value.id == 'os' and
                node.value.attr == 'environ'):
                self._extract_env_usage_subscript(node, 'os.environ[]')
        elif isinstance(node.value, ast.Name):
            # environ['KEY'] (if imported directly)  
            if node.value.id == 'environ':
                self._extract_env_usage_subscript(node, 'environ[]')
        
        self.generic_visit(node)
    
    def _extract_env_usage(self, node: ast.Call, method: str):
        """Extract environment variable name from function call"""
        if node.args and isinstance(node.args[0], ast.Constant):
            var_name = node.args[0].value
            if isinstance(var_name, str):
                has_default = len(node.args) > 1
                default_value = None
                
                if has_default and isinstance(node.args[1], ast.Constant):
                    default_value = str(node.args[1].value)
                
                usage = EnvUsage(
                    file_path=self.file_path,
                    line_number=node.lineno,
                    column=node.col_offset,
                    variable_name=var_name,
                    access_method=method,
                    has_default=has_default,
                    default_value=default_value,
                    context_line=self.lines[node.lineno - 1] if node.lineno <= len(self.lines) else "",
                    function_name=self.current_function,
                    class_name=self.current_class
                )
                self.usages.append(usage)
    
    def _extract_env_usage_subscript(self, node: ast.Subscript, method: str):
        """Extract environment variable name from subscript access"""
        if isinstance(node.slice, ast.Constant) and isinstance(node.slice.value, str):
            var_name = node.slice.value
            
            usage = EnvUsage(
                file_path=self.file_path,
                line_number=node.lineno,
                column=node.col_offset,
                variable_name=var_name,
                access_method=method,
                has_default=False,
                default_value=None,
                context_line=self.lines[node.lineno - 1] if node.lineno <= len(self.lines) else "",
                function_name=self.current_function,
                class_name=self.current_class
            )
            self.usages.append(usage)


if __name__ == "__main__":
    # Test the enhanced scanner
    import sys
    
    if len(sys.argv) > 1:
        project_path = sys.argv[1]
    else:
        project_path = "."
    
    scanner = EnhancedEnvScanner(project_path)
    result = scanner.scan_everything()
    
    print(f"\n📊 Enhanced Scan Results:")
    for key, value in result.usage_stats.items():
        print(f"   {key}: {value}")
    
    print(f"\n🔍 Environment Variables Used:")
    used_vars = set(usage.variable_name for usage in result.usages)
    for var in sorted(used_vars):
        print(f"   - {var}")
    
    print(f"\n🖥️ System Variables (sample):")
    system_sample = list(result.system_variables.keys())[:10]
    for var in system_sample:
        print(f"   - {var}")
    
    print(f"\n📄 File Variables:")
    for filename, variables in result.file_variables.items():
        print(f"   {filename}: {len(variables)} variables")
