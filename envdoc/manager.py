"""
Environment Variable Manager
Handles complete environment variable lifecycle management including:
- Smart .env file creation and management
- System environment variable detection
- Cross-source environment variable comparison
- Interactive management options
"""

import os
import sys
import shutil
from pathlib import Path
from typing import Dict, List, Set, Optional, Any, Tuple
from dataclasses import dataclass
import subprocess
import platform

try:
    from rich.console import Console
    from rich.table import Table
    from rich.panel import Panel
    from rich import print as rprint
    import questionary
    INTERACTIVE_AVAILABLE = True
except ImportError:
    INTERACTIVE_AVAILABLE = False
    Console = None

from dotenv import load_dotenv

@dataclass
class EnvSource:
    """Represents a source of environment variables"""
    name: str
    type: str  # 'system', 'file', 'shell'
    path: Optional[str]
    variables: Dict[str, str]
    priority: int  # Higher = more important
    writable: bool

@dataclass
class EnvVariable:
    """Complete information about an environment variable"""
    name: str
    sources: List[EnvSource]
    current_value: Optional[str]
    recommended_source: Optional[str]
    usage_count: int
    is_system_critical: bool

class EnvManager:
    """
    Complete Environment Variable Management System
    Provides smart .env management and system integration
    """
    
    # Critical system variables that should not be modified
    SYSTEM_CRITICAL_VARS = {
        'PATH', 'HOME', 'USER', 'USERNAME', 'USERPROFILE', 'SYSTEMROOT',
        'PROGRAMFILES', 'PROGRAMDATA', 'TEMP', 'TMP', 'WINDIR', 'APPDATA',
        'LOCALAPPDATA', 'COMMONPROGRAMFILES', 'PYTHONPATH', 'JAVA_HOME',
        'NODE_PATH', 'SHELL', 'TERM', 'DISPLAY', 'PWD', 'OLDPWD'
    }
    
    # Common .env file names in order of preference
    ENV_FILE_NAMES = [
        '.env',
        '.env.local',
        '.env.development',
        '.env.production',
        '.env.test'
    ]
    
    ENV_EXAMPLE_NAMES = [
        '.env.example',
        '.env.sample',
        '.env.template',
        'env.example'
    ]
    
    def __init__(self, project_root: str):
        self.project_root = Path(project_root)
        self.console = Console() if INTERACTIVE_AVAILABLE else None
        self.env_sources: List[EnvSource] = []
        self.all_variables: Dict[str, EnvVariable] = {}
        
    def discover_all_sources(self) -> List[EnvSource]:
        """Discover all environment variable sources"""
        sources = []
        
        # 1. System environment variables
        system_vars = dict(os.environ)
        sources.append(EnvSource(
            name="System Environment",
            type="system",
            path=None,
            variables=system_vars,
            priority=100,
            writable=True  # Can be modified via os.environ
        ))
        
        # 2. Shell-specific variables (if detectable)
        shell_vars = self._detect_shell_variables()
        if shell_vars:
            sources.append(EnvSource(
                name="Shell Environment",
                type="shell", 
                path=self._get_shell_profile_path(),
                variables=shell_vars,
                priority=90,
                writable=True
            ))
        
        # 3. .env files in project
        for env_file in self.ENV_FILE_NAMES + self.ENV_EXAMPLE_NAMES:
            env_path = self.project_root / env_file
            if env_path.exists():
                env_vars = self._parse_env_file(env_path)
                is_example = any(example in env_file for example in ['example', 'sample', 'template'])
                
                sources.append(EnvSource(
                    name=f"File: {env_file}",
                    type="file",
                    path=str(env_path),
                    variables=env_vars,
                    priority=80 if not is_example else 70,
                    writable=True
                ))
        
        # 4. Look for .env files in parent directories (for monorepos)
        parent_env_files = self._find_parent_env_files()
        for env_file, env_vars in parent_env_files:
            sources.append(EnvSource(
                name=f"Parent: {env_file.name}",
                type="file",
                path=str(env_file),
                variables=env_vars,
                priority=60,
                writable=True
            ))
        
        self.env_sources = sources
        return sources
    
    def smart_env_setup(self) -> bool:
        """
        Smart .env file setup (enhanced version of main.py logic)
        Creates .env from .env.example or provides helpful guidance
        """
        
        rprint("[bold blue]🏥 EnvDoctor Smart Environment Setup[/bold blue]")
        
        env_path = self.project_root / ".env"
        env_example_path = self._find_best_example_file()
        
        # Check current state
        if env_path.exists():
            rprint(f"[green]✅ .env file already exists: {env_path}[/green]")
            
            if INTERACTIVE_AVAILABLE:
                action = questionary.select(
                    "What would you like to do?",
                    choices=[
                        "Analyze existing .env file",
                        "Compare with .env.example", 
                        "Backup and recreate from example",
                        "Skip .env setup"
                    ]
                ).ask()
                
                if action == "Analyze existing .env file":
                    return self._analyze_existing_env(env_path)
                elif action == "Compare with .env.example":
                    return self._compare_env_files(env_path, env_example_path)
                elif action == "Backup and recreate from example":
                    return self._backup_and_recreate_env(env_path, env_example_path)
            
            return True
        
        elif env_example_path:
            rprint(f"[yellow]⚠️ .env not found, but found: {env_example_path.name}[/yellow]")
            rprint("[cyan]🔧 Creating .env file from example...[/cyan]")
            
            try:
                # Create .env from example
                shutil.copy2(env_example_path, env_path)
                
                # Load and analyze the new .env file
                load_dotenv(env_path)
                rprint(f"[green]✅ Created .env file: {env_path}[/green]")
                
                # Show what was created
                env_vars = self._parse_env_file(env_path)
                rprint(f"[dim]📝 Created with {len(env_vars)} environment variables[/dim]")
                
                # Provide next steps
                rprint("[yellow]💡 Next steps:[/yellow]")
                rprint("   1. Review and update values in the new .env file")
                rprint("   2. Run 'envdoctor --analyze' to check for issues")
                rprint("   3. Never commit .env files to version control")
                
                return True
                
            except Exception as e:
                rprint(f"[red]❌ Failed to create .env from example: {e}[/red]")
                rprint("[yellow]⚠️ You may need to create .env file manually[/yellow]")
                return False
        
        else:
            # No .env or .env.example found
            rprint("[red]❌ CRITICAL: Neither .env nor .env.example file found![/red]")
            rprint(f"[dim]📁 Searched in: {self.project_root}[/dim]")
            rprint("[yellow]🔧 Recommendations:[/yellow]")
            
            if INTERACTIVE_AVAILABLE:
                action = questionary.select(
                    "What would you like to do?",
                    choices=[
                        "Create basic .env.example template",
                        "Search for .env files in parent directories",
                        "Show detected system variables",
                        "Exit and create manually"
                    ]
                ).ask()
                
                if action == "Create basic .env.example template":
                    return self._create_env_example_template()
                elif action == "Search for .env files in parent directories":
                    return self._search_parent_env_files()
                elif action == "Show detected system variables":
                    return self._show_relevant_system_vars()
            
            else:
                rprint("   1. Create .env.example file with your project's environment variables")
                rprint("   2. Copy .env.example to .env and update values")
                rprint("   3. Run 'envdoctor --setup' again")
                
            return False
    
    def _find_best_example_file(self) -> Optional[Path]:
        """Find the best .env.example file"""
        for example_name in self.ENV_EXAMPLE_NAMES:
            example_path = self.project_root / example_name
            if example_path.exists():
                return example_path
        return None
    
    def _analyze_existing_env(self, env_path: Path) -> bool:
        """Analyze existing .env file"""
        env_vars = self._parse_env_file(env_path)
        
        rprint(f"[cyan]📊 .env File Analysis: {env_path.name}[/cyan]")
        
        table = Table(title="Environment Variables", show_header=True)
        table.add_column("Variable", style="cyan")
        table.add_column("Value Length", style="green")
        table.add_column("Type", style="yellow")
        
        for name, value in env_vars.items():
            value_len = len(value) if value else 0
            var_type = "Empty" if not value else "Secret" if any(secret in name.lower() for secret in ['key', 'secret', 'password', 'token']) else "Config"
            
            table.add_row(name, str(value_len), var_type)
        
        if self.console:
            self.console.print(table)
        
        return True
    
    def _compare_env_files(self, env_path: Path, example_path: Optional[Path]) -> bool:
        """Compare .env with .env.example"""
        if not example_path:
            rprint("[yellow]⚠️ No .env.example file found for comparison[/yellow]")
            return False
        
        env_vars = self._parse_env_file(env_path)
        example_vars = self._parse_env_file(example_path)
        
        # Find differences
        missing_in_env = set(example_vars.keys()) - set(env_vars.keys())
        extra_in_env = set(env_vars.keys()) - set(example_vars.keys())
        common_vars = set(env_vars.keys()) & set(example_vars.keys())
        
        rprint("[cyan]📊 .env vs .env.example Comparison[/cyan]")
        
        if missing_in_env:
            rprint(f"[red]❌ Missing in .env ({len(missing_in_env)}):[/red]")
            for var in sorted(missing_in_env):
                rprint(f"   - {var}")
        
        if extra_in_env:
            rprint(f"[yellow]⚠️ Extra in .env ({len(extra_in_env)}):[/yellow]")
            for var in sorted(extra_in_env):
                rprint(f"   + {var}")
        
        rprint(f"[green]✅ Common variables: {len(common_vars)}[/green]")
        
        return True
    
    def _backup_and_recreate_env(self, env_path: Path, example_path: Optional[Path]) -> bool:
        """Backup existing .env and recreate from example"""
        if not example_path:
            rprint("[red]❌ No .env.example found to recreate from[/red]")
            return False
        
        # Create backup
        backup_path = env_path.with_suffix('.env.backup')
        try:
            shutil.copy2(env_path, backup_path)
            rprint(f"[green]✅ Backup created: {backup_path}[/green]")
            
            # Recreate from example
            shutil.copy2(example_path, env_path)
            rprint(f"[green]✅ Recreated .env from {example_path.name}[/green]")
            
            return True
            
        except Exception as e:
            rprint(f"[red]❌ Failed to backup and recreate: {e}[/red]")
            return False
    
    def _create_env_example_template(self) -> bool:
        """Create a basic .env.example template"""
        
        # Detect what kind of project this might be
        project_type = self._detect_project_type()
        
        template_vars = self._get_template_vars_for_project(project_type)
        
        example_path = self.project_root / ".env.example"
        
        try:
            with open(example_path, 'w') as f:
                f.write(f"# Environment Variables for {project_type} Project\n")
                f.write("# Copy this file to .env and update the values\n\n")
                
                for section, vars_dict in template_vars.items():
                    f.write(f"# {section}\n")
                    for var_name, description in vars_dict.items():
                        f.write(f"{var_name}=  # {description}\n")
                    f.write("\n")
            
            rprint(f"[green]✅ Created .env.example template: {example_path}[/green]")
            rprint("[yellow]💡 Please review and customize the template, then copy to .env[/yellow]")
            
            return True
            
        except Exception as e:
            rprint(f"[red]❌ Failed to create .env.example: {e}[/red]")
            return False
    
    def _detect_project_type(self) -> str:
        """Detect what type of project this is"""
        
        if (self.project_root / "requirements.txt").exists() or (self.project_root / "pyproject.toml").exists():
            if any((self.project_root / file).exists() for file in ["app.py", "main.py", "manage.py"]):
                return "Python Web Application"
            return "Python Application"
        
        if (self.project_root / "package.json").exists():
            return "Node.js Application"
        
        if (self.project_root / "Dockerfile").exists():
            return "Containerized Application"
        
        return "General Application"
    
    def _get_template_vars_for_project(self, project_type: str) -> Dict[str, Dict[str, str]]:
        """Get template environment variables based on project type"""
        
        common_vars = {
            "Application Settings": {
                "APP_NAME": "Application name",
                "APP_VERSION": "Application version",
                "ENVIRONMENT": "Environment (development, staging, production)",
                "DEBUG": "Enable debug mode (true/false)"
            },
            "Server Configuration": {
                "HOST": "Server host address",
                "PORT": "Server port number"
            }
        }
        
        if "Python" in project_type:
            common_vars.update({
                "Database Configuration": {
                    "DATABASE_URL": "Database connection string",
                    "DB_HOST": "Database host",
                    "DB_PORT": "Database port",
                    "DB_NAME": "Database name", 
                    "DB_USER": "Database username",
                    "DB_PASSWORD": "Database password"
                },
                "Security": {
                    "SECRET_KEY": "Application secret key",
                    "JWT_SECRET": "JWT signing secret"
                }
            })
        
        return common_vars
    
    def _search_parent_env_files(self) -> bool:
        """Search for .env files in parent directories"""
        
        current_path = self.project_root.parent
        found_files = []
        
        # Search up to 3 levels up
        for _ in range(3):
            if current_path == current_path.parent:  # Reached root
                break
            
            for env_name in self.ENV_FILE_NAMES + self.ENV_EXAMPLE_NAMES:
                env_file = current_path / env_name
                if env_file.exists():
                    found_files.append(env_file)
            
            current_path = current_path.parent
        
        if found_files:
            rprint(f"[green]📁 Found {len(found_files)} .env file(s) in parent directories:[/green]")
            
            for i, env_file in enumerate(found_files, 1):
                rel_path = os.path.relpath(env_file, self.project_root)
                rprint(f"   {i}. {rel_path}")
            
            if INTERACTIVE_AVAILABLE:
                choices = [f"{os.path.relpath(f, self.project_root)} - Copy to current project" for f in found_files]
                choices.append("None of these")
                
                selection = questionary.select(
                    "Which file would you like to use as a template?",
                    choices=choices
                ).ask()
                
                if selection != "None of these":
                    selected_file = found_files[choices.index(selection)]
                    target_path = self.project_root / ".env.example"
                    
                    try:
                        shutil.copy2(selected_file, target_path)
                        rprint(f"[green]✅ Copied to .env.example[/green]")
                        return True
                    except Exception as e:
                        rprint(f"[red]❌ Failed to copy: {e}[/red]")
            
            return True
        else:
            rprint("[yellow]⚠️ No .env files found in parent directories[/yellow]")
            return False
    
    def _show_relevant_system_vars(self) -> bool:
        """Show system environment variables that might be relevant"""
        
        relevant_patterns = [
            'DATABASE', 'DB_', 'POSTGRES', 'MYSQL', 'MONGO',
            'REDIS', 'CACHE',
            'API_', 'SECRET', 'KEY', 'TOKEN',
            'AWS_', 'AZURE_', 'GCP_',
            'NODE_', 'PYTHON', 'JAVA_',
            'PORT', 'HOST', 'URL', 'URI'
        ]
        
        system_vars = dict(os.environ)
        relevant_vars = {}
        
        for var_name, var_value in system_vars.items():
            if any(pattern in var_name.upper() for pattern in relevant_patterns):
                if var_name not in self.SYSTEM_CRITICAL_VARS:
                    relevant_vars[var_name] = var_value
        
        if relevant_vars:
            rprint(f"[cyan]🖥️ Found {len(relevant_vars)} potentially relevant system variables:[/cyan]")
            
            table = Table(show_header=True, header_style="bold magenta")
            table.add_column("Variable", style="cyan")
            table.add_column("Value Preview", style="green")
            
            for var_name, var_value in list(relevant_vars.items())[:20]:  # Show first 20
                preview = var_value[:50] + "..." if len(var_value) > 50 else var_value
                table.add_row(var_name, preview)
            
            if self.console:
                self.console.print(table)
            
            if len(relevant_vars) > 20:
                rprint(f"[dim]... and {len(relevant_vars) - 20} more[/dim]")
        else:
            rprint("[yellow]⚠️ No obviously relevant system environment variables found[/yellow]")
        
        return True
    
    def _detect_shell_variables(self) -> Dict[str, str]:
        """Detect shell-specific environment variables"""
        # This is platform-specific and complex to implement fully
        # For now, return empty dict
        return {}
    
    def _get_shell_profile_path(self) -> Optional[str]:
        """Get path to shell profile file"""
        home = Path.home()
        
        if platform.system() == "Windows":
            # Windows doesn't have traditional shell profiles
            return None
        else:
            # Unix-like systems
            shell = os.environ.get('SHELL', '')
            if 'bash' in shell:
                for profile in ['.bashrc', '.bash_profile', '.profile']:
                    if (home / profile).exists():
                        return str(home / profile)
            elif 'zsh' in shell:
                for profile in ['.zshrc', '.zprofile']:
                    if (home / profile).exists():
                        return str(home / profile)
        
        return None
    
    def _parse_env_file(self, env_file: Path) -> Dict[str, str]:
        """Parse environment file and return variables"""
        variables = {}
        
        try:
            with open(env_file, 'r', encoding='utf-8') as f:
                for line_num, line in enumerate(f, 1):
                    line = line.strip()
                    
                    # Skip empty lines and comments
                    if not line or line.startswith('#'):
                        continue
                    
                    # Parse KEY=VALUE
                    if '=' in line:
                        key, value = line.split('=', 1)
                        key = key.strip()
                        value = value.strip().strip('"').strip("'")
                        variables[key] = value
                        
        except Exception as e:
            print(f"Warning: Error parsing {env_file}: {e}")
        
        return variables
    
    def _find_parent_env_files(self) -> List[Tuple[Path, Dict[str, str]]]:
        """Find .env files in parent directories"""
        parent_files = []
        current_path = self.project_root.parent
        
        # Search up to 3 levels
        for _ in range(3):
            if current_path == current_path.parent:
                break
            
            for env_name in self.ENV_FILE_NAMES + self.ENV_EXAMPLE_NAMES:
                env_file = current_path / env_name
                if env_file.exists():
                    env_vars = self._parse_env_file(env_file)
                    parent_files.append((env_file, env_vars))
            
            current_path = current_path.parent
        
        return parent_files
    
    def show_complete_environment_view(self):
        """Show complete view of all environment sources"""
        
        if not self.env_sources:
            self.discover_all_sources()
        
        rprint("[bold blue]🌍 Complete Environment Overview[/bold blue]")
        
        # Show sources
        sources_table = Table(title="Environment Sources", show_header=True)
        sources_table.add_column("Source", style="cyan")
        sources_table.add_column("Type", style="yellow")
        sources_table.add_column("Variables", style="green")
        sources_table.add_column("Priority", style="magenta")
        sources_table.add_column("Writable", style="red")
        
        for source in sorted(self.env_sources, key=lambda x: x.priority, reverse=True):
            sources_table.add_row(
                source.name,
                source.type,
                str(len(source.variables)),
                str(source.priority),
                "Yes" if source.writable else "No"
            )
        
        if self.console:
            self.console.print(sources_table)
        
        return self.env_sources


if __name__ == "__main__":
    # Test the manager
    import sys
    
    if len(sys.argv) > 1:
        project_path = sys.argv[1]
    else:
        project_path = "."
    
    manager = EnvManager(project_path)
    
    print("🏥 EnvDoctor Environment Manager Test")
    print("=" * 40)
    
    # Test smart setup
    manager.smart_env_setup()
    
    # Show complete environment view
    sources = manager.show_complete_environment_view()
