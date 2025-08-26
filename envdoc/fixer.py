"""
Enhanced Environment Variable Fixer
Applies fixes to code files and environment configuration with system integration
"""

import ast
import os
import re
import shutil
import tempfile
from pathlib import Path
from typing import Dict, List, Set, Tuple, Optional, Any
from dataclasses import dataclass
import platform
import subprocess

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

from .analyzer import EnhancedMismatch, EnhancedAnalysisResult
from .scanner import EnvUsage

@dataclass
class FixAction:
    """Represents a fixing action"""
    mismatch: EnhancedMismatch
    action_type: str  # 'rename_in_code', 'add_to_env', 'use_system_var', 'create_new'
    old_name: str
    new_name: str
    target_files: List[str]
    env_files_to_update: List[str]
    system_command: Optional[str] = None
    value_to_set: Optional[str] = None
    backup_created: bool = False

@dataclass
class FixResult:
    """Result of applying fixes"""
    actions_applied: List[FixAction]
    files_modified: List[str]
    backups_created: List[str]
    errors: List[str]
    success_count: int
    total_count: int

class EnhancedEnvFixer:
    """
    Enhanced Environment Variable Fixer
    Provides comprehensive fixing capabilities including system environment integration
    """
    
    def __init__(self, project_root: str, dry_run: bool = False):
        self.project_root = Path(project_root)
        self.dry_run = dry_run
        self.console = Console() if INTERACTIVE_AVAILABLE else None
        self.backups_dir = self.project_root / ".envdoctor_backups"
        
    def interactive_fix(self, analysis_result: EnhancedAnalysisResult) -> FixResult:
        """Interactive fixing with user choices for each issue"""
        
        if not INTERACTIVE_AVAILABLE:
            rprint("[red]❌ Interactive mode requires 'rich' and 'questionary' packages[/red]")
            return FixResult([], [], [], ["Interactive mode not available"], 0, 0)
        
        rprint(f"[bold blue]🔧 EnvDoctor Interactive Fix Mode[/bold blue]")
        rprint(f"Project: {self.project_root}")
        rprint(f"Dry Run: {'Yes' if self.dry_run else 'No'}")
        
        if not analysis_result.mismatches:
            rprint("[green]🎉 No issues found to fix![/green]")
            return FixResult([], [], [], [], 0, 0)
        
        actions_to_apply = []
        
        rprint(f"\n[yellow]Found {len(analysis_result.mismatches)} issues to resolve[/yellow]")
        
        for i, mismatch in enumerate(analysis_result.mismatches, 1):
            rprint(f"\n[cyan]Issue {i}/{len(analysis_result.mismatches)}[/cyan]")
            
            action = self._get_user_action_for_mismatch(mismatch)
            if action:
                actions_to_apply.append(action)
        
        # Summary and confirmation
        if actions_to_apply:
            rprint(f"\n[yellow]📋 Summary: {len(actions_to_apply)} actions planned[/yellow]")
            
            for action in actions_to_apply:
                rprint(f"   • {action.action_type}: {action.old_name} → {action.new_name}")
            
            if not self.dry_run:
                confirm = questionary.confirm("Apply these changes?").ask()
                if not confirm:
                    rprint("[yellow]⏹️ Operation cancelled by user[/yellow]")
                    return FixResult([], [], [], [], 0, len(actions_to_apply))
            
            # Apply actions
            return self._apply_actions(actions_to_apply)
        
        else:
            rprint("[yellow]⏹️ No actions selected[/yellow]")
            return FixResult([], [], [], [], 0, 0)
    
    def _get_user_action_for_mismatch(self, mismatch: EnhancedMismatch) -> Optional[FixAction]:
        """Get user's preferred action for a specific mismatch"""
        
        rprint(f"[red]❌ Variable: {mismatch.used_name}[/red]")
        rprint(f"   Issue: {mismatch.issue_type}")
        rprint(f"   Used in {len(mismatch.usages)} location(s)")
        
        # Show usage locations
        for usage in mismatch.usages[:3]:  # Show first 3
            file_path = Path(usage.file_path).relative_to(self.project_root)
            rprint(f"     📄 {file_path}:{usage.line_number}")
        if len(mismatch.usages) > 3:
            rprint(f"     ... and {len(mismatch.usages) - 3} more locations")
        
        # Build options based on available suggestions
        choices = []
        
        # Option 1: Use suggestions (if any)
        if mismatch.suggested_matches:
            for i, (suggestion, confidence) in enumerate(zip(mismatch.suggested_matches[:3], mismatch.confidence_scores[:3])):
                source_info = "🖥️ system" if mismatch.system_available else "📄 file"
                confidence_str = f"{confidence:.0%}"
                choices.append(f"Rename to '{suggestion}' (confidence: {confidence_str}, {source_info})")
        
        # Option 2: Add to .env file
        choices.append(f"Add '{mismatch.used_name}' to .env file")
        
        # Option 3: Set as system environment variable
        if platform.system() in ['Windows', 'Linux', 'Darwin']:
            choices.append(f"Set '{mismatch.used_name}' as system environment variable")
        
        # Option 4: Manual rename
        choices.append(f"Rename to custom name")
        
        # Option 5: Skip
        choices.append("Skip this issue")
        
        # Get user choice
        choice = questionary.select(
            f"How would you like to resolve '{mismatch.used_name}'?",
            choices=choices
        ).ask()
        
        if choice.startswith("Skip"):
            return None
        
        # Process the choice
        if choice.startswith("Rename to '") and "'" in choice:
            # Extract suggested name
            new_name = choice.split("'")[1]
            return FixAction(
                mismatch=mismatch,
                action_type='rename_in_code',
                old_name=mismatch.used_name,
                new_name=new_name,
                target_files=[usage.file_path for usage in mismatch.usages],
                env_files_to_update=[]
            )
        
        elif choice.startswith("Add"):
            # Add to .env file
            value = questionary.text(
                f"Value for {mismatch.used_name}:",
                default=""
            ).ask()
            
            return FixAction(
                mismatch=mismatch,
                action_type='add_to_env',
                old_name=mismatch.used_name,
                new_name=mismatch.used_name,
                target_files=[],
                env_files_to_update=[str(self.project_root / ".env")],
                value_to_set=value
            )
        
        elif choice.startswith("Set") and "system" in choice:
            # Set as system environment variable
            value = questionary.text(
                f"System value for {mismatch.used_name}:",
                default=""
            ).ask()
            
            return FixAction(
                mismatch=mismatch,
                action_type='use_system_var',
                old_name=mismatch.used_name,
                new_name=mismatch.used_name,
                target_files=[],
                env_files_to_update=[],
                system_command=self._get_system_set_command(mismatch.used_name, value),
                value_to_set=value
            )
        
        elif choice.startswith("Rename to custom"):
            # Manual rename
            new_name = questionary.text(
                f"New name for '{mismatch.used_name}':",
                validate=lambda x: len(x.strip()) > 0 and x.strip().isupper()
            ).ask()
            
            if new_name:
                return FixAction(
                    mismatch=mismatch,
                    action_type='rename_in_code',
                    old_name=mismatch.used_name,
                    new_name=new_name.strip(),
                    target_files=[usage.file_path for usage in mismatch.usages],
                    env_files_to_update=[]
                )
        
        return None
    
    def _get_system_set_command(self, var_name: str, value: str) -> str:
        """Get the command to set system environment variable"""
        
        if platform.system() == "Windows":
            # Windows setx command (persistent)
            return f'setx {var_name} "{value}"'
        else:
            # Unix-like systems - this would go in shell profile
            return f'export {var_name}="{value}"'
    
    def _apply_actions(self, actions: List[FixAction]) -> FixResult:
        """Apply the list of fix actions"""
        
        rprint(f"\n[cyan]🔧 Applying {len(actions)} fix actions...[/cyan]")
        
        applied_actions = []
        modified_files = []
        backups_created = []
        errors = []
        
        # Ensure backups directory exists
        if not self.dry_run:
            self.backups_dir.mkdir(exist_ok=True)
        
        for i, action in enumerate(actions, 1):
            rprint(f"\n[dim]Action {i}/{len(actions)}:[/dim] {action.action_type}: {action.old_name} → {action.new_name}")
            
            try:
                success = self._apply_single_action(action)
                if success:
                    applied_actions.append(action)
                    if action.target_files:
                        modified_files.extend(action.target_files)
                    if action.env_files_to_update:
                        modified_files.extend(action.env_files_to_update)
                    if action.backup_created:
                        backups_created.extend(self._get_backup_files_for_action(action))
                    rprint(f"   [green]✅ Success[/green]")
                else:
                    errors.append(f"Failed to apply action: {action.action_type} for {action.old_name}")
                    rprint(f"   [red]❌ Failed[/red]")
            
            except Exception as e:
                error_msg = f"Error applying {action.action_type} for {action.old_name}: {str(e)}"
                errors.append(error_msg)
                rprint(f"   [red]❌ Error: {str(e)}[/red]")
        
        # Remove duplicates
        modified_files = list(set(modified_files))
        backups_created = list(set(backups_created))
        
        success_count = len(applied_actions)
        total_count = len(actions)
        
        # Summary
        rprint(f"\n[cyan]📊 Fix Results:[/cyan]")
        rprint(f"   ✅ Successful: {success_count}/{total_count}")
        rprint(f"   📝 Files Modified: {len(modified_files)}")
        rprint(f"   💾 Backups Created: {len(backups_created)}")
        if errors:
            rprint(f"   ❌ Errors: {len(errors)}")
            for error in errors[:3]:  # Show first 3 errors
                rprint(f"      • {error}")
            if len(errors) > 3:
                rprint(f"      ... and {len(errors) - 3} more")
        
        return FixResult(
            actions_applied=applied_actions,
            files_modified=modified_files,
            backups_created=backups_created,
            errors=errors,
            success_count=success_count,
            total_count=total_count
        )
    
    def _apply_single_action(self, action: FixAction) -> bool:
        """Apply a single fix action"""
        
        if self.dry_run:
            rprint(f"   [dim](DRY RUN) Would apply: {action.action_type}[/dim]")
            return True
        
        try:
            if action.action_type == 'rename_in_code':
                return self._rename_in_code_files(action)
            elif action.action_type == 'add_to_env':
                return self._add_to_env_file(action)
            elif action.action_type == 'use_system_var':
                return self._set_system_variable(action)
            else:
                rprint(f"   [red]Unknown action type: {action.action_type}[/red]")
                return False
        
        except Exception as e:
            rprint(f"   [red]Exception in {action.action_type}: {str(e)}[/red]")
            return False
    
    def _rename_in_code_files(self, action: FixAction) -> bool:
        """Rename variable in code files"""
        success = True
        
        # Get unique files to modify
        files_to_modify = list(set(action.target_files))
        
        for file_path in files_to_modify:
            try:
                # Create backup
                backup_path = self._create_backup(file_path)
                if backup_path:
                    action.backup_created = True
                
                # Modify the file
                if self._rename_variable_in_file(file_path, action.old_name, action.new_name):
                    rprint(f"      📝 Modified: {Path(file_path).relative_to(self.project_root)}")
                else:
                    success = False
                    rprint(f"      ⚠️ No changes made to: {Path(file_path).relative_to(self.project_root)}")
            
            except Exception as e:
                rprint(f"      ❌ Error modifying {file_path}: {str(e)}")
                success = False
        
        return success
    
    def _add_to_env_file(self, action: FixAction) -> bool:
        """Add variable to .env file"""
        
        env_file = self.project_root / ".env"
        
        # Create backup
        if env_file.exists():
            backup_path = self._create_backup(str(env_file))
            if backup_path:
                action.backup_created = True
        
        # Add variable to .env file
        try:
            with open(env_file, 'a', encoding='utf-8') as f:
                f.write(f"\n# Added by EnvDoctor\n")
                f.write(f"{action.new_name}={action.value_to_set or ''}\n")
            
            rprint(f"      📄 Added to .env: {action.new_name}")
            return True
        
        except Exception as e:
            rprint(f"      ❌ Error writing to .env file: {str(e)}")
            return False
    
    def _set_system_variable(self, action: FixAction) -> bool:
        """Set system environment variable"""
        
        if not action.system_command:
            rprint(f"      ⚠️ No system command for {action.new_name}")
            return False
        
        try:
            if platform.system() == "Windows":
                # Use setx for persistent variables on Windows
                result = subprocess.run(
                    action.system_command,
                    shell=True,
                    capture_output=True,
                    text=True,
                    timeout=10
                )
                
                if result.returncode == 0:
                    rprint(f"      🖥️ Set system variable: {action.new_name}")
                    rprint(f"      ⚠️ Note: Restart your terminal for changes to take effect")
                    return True
                else:
                    rprint(f"      ❌ Failed to set system variable: {result.stderr}")
                    return False
            
            else:
                # Unix-like systems - add to current process and suggest shell profile update
                os.environ[action.new_name] = action.value_to_set or ''
                rprint(f"      🖥️ Set in current session: {action.new_name}")
                rprint(f"      💡 Consider adding '{action.system_command}' to your shell profile")
                return True
        
        except subprocess.TimeoutExpired:
            rprint(f"      ⚠️ Timeout setting system variable: {action.new_name}")
            return False
        except Exception as e:
            rprint(f"      ❌ Error setting system variable: {str(e)}")
            return False
    
    def _rename_variable_in_file(self, file_path: str, old_name: str, new_name: str) -> bool:
        """Rename environment variable in a specific file"""
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            original_content = content
            
            # Python files: Try AST-based replacement first
            if file_path.endswith('.py'):
                content = self._rename_with_ast(content, old_name, new_name, file_path)
            
            # Fallback to regex replacement for all files
            if content == original_content:
                content = self._rename_with_regex(content, old_name, new_name)
            
            # Only write if changes were made
            if content != original_content:
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(content)
                return True
            
            return False
        
        except Exception as e:
            rprint(f"      ❌ Error processing {file_path}: {str(e)}")
            return False
    
    def _rename_with_ast(self, content: str, old_name: str, new_name: str, file_path: str) -> str:
        """Use AST to rename variables in Python files"""
        
        try:
            tree = ast.parse(content)
            transformer = VariableRenameTransformer(old_name, new_name)
            new_tree = transformer.visit(tree)
            
            if transformer.changes_made:
                # Convert back to code
                import ast
                try:
                    # Try to use astunparse if available
                    import astunparse
                    return astunparse.unparse(new_tree)
                except ImportError:
                    # Fallback: use regex replacement
                    return self._rename_with_regex(content, old_name, new_name)
        
        except SyntaxError:
            # If AST parsing fails, fall back to regex
            pass
        
        return content
    
    def _rename_with_regex(self, content: str, old_name: str, new_name: str) -> str:
        """Use regex to rename variables"""
        
        # Patterns for different usage contexts
        patterns = [
            # os.getenv('OLD_NAME') -> os.getenv('NEW_NAME')
            (rf"(os\.getenv\s*\(\s*['\"])({re.escape(old_name)})(['\"])", rf"\1{new_name}\3"),
            
            # os.environ['OLD_NAME'] -> os.environ['NEW_NAME']
            (rf"(os\.environ\s*\[\s*['\"])({re.escape(old_name)})(['\"])", rf"\1{new_name}\3"),
            
            # os.environ.get('OLD_NAME') -> os.environ.get('NEW_NAME')
            (rf"(os\.environ\.get\s*\(\s*['\"])({re.escape(old_name)})(['\"])", rf"\1{new_name}\3"),
            
            # getenv('OLD_NAME') -> getenv('NEW_NAME') (when imported directly)
            (rf"(getenv\s*\(\s*['\"])({re.escape(old_name)})(['\"])", rf"\1{new_name}\3"),
            
            # environ['OLD_NAME'] -> environ['NEW_NAME'] (when imported directly)
            (rf"(environ\s*\[\s*['\"])({re.escape(old_name)})(['\"])", rf"\1{new_name}\3"),
            
            # Custom env functions
            (rf"(get_env\s*\(\s*['\"])({re.escape(old_name)})(['\"])", rf"\1{new_name}\3"),
            (rf"(env_var\s*\(\s*['\"])({re.escape(old_name)})(['\"])", rf"\1{new_name}\3"),
        ]
        
        modified_content = content
        
        for pattern, replacement in patterns:
            modified_content = re.sub(pattern, replacement, modified_content)
        
        return modified_content
    
    def _create_backup(self, file_path: str) -> Optional[str]:
        """Create backup of a file"""
        
        try:
            source_path = Path(file_path)
            if not source_path.exists():
                return None
            
            # Create backup filename with timestamp
            from datetime import datetime
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_name = f"{source_path.name}.backup_{timestamp}"
            backup_path = self.backups_dir / backup_name
            
            # Copy the file
            shutil.copy2(source_path, backup_path)
            return str(backup_path)
        
        except Exception as e:
            rprint(f"      ⚠️ Could not create backup for {file_path}: {str(e)}")
            return None
    
    def _get_backup_files_for_action(self, action: FixAction) -> List[str]:
        """Get list of backup files that might have been created for an action"""
        
        # This is a simplified implementation
        # In practice, you'd track which backups were actually created
        backup_files = []
        
        if action.backup_created:
            from datetime import datetime
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            
            # Add potential backup files
            for file_path in action.target_files + action.env_files_to_update:
                source_path = Path(file_path)
                backup_name = f"{source_path.name}.backup_{timestamp}"
                backup_files.append(str(self.backups_dir / backup_name))
        
        return backup_files
    
    def batch_fix(self, analysis_result: EnhancedAnalysisResult, 
                  auto_apply_confidence_threshold: float = 0.9) -> FixResult:
        """Automatically fix issues with high confidence"""
        
        rprint(f"[bold blue]🤖 EnvDoctor Batch Fix Mode[/bold blue]")
        rprint(f"Confidence threshold: {auto_apply_confidence_threshold:.0%}")
        
        auto_actions = []
        
        for mismatch in analysis_result.mismatches:
            # Only auto-fix high-confidence issues
            if (mismatch.confidence_scores and 
                max(mismatch.confidence_scores) >= auto_apply_confidence_threshold):
                
                # Use the highest-confidence suggestion
                best_suggestion = mismatch.suggested_matches[0]
                
                action = FixAction(
                    mismatch=mismatch,
                    action_type='rename_in_code',
                    old_name=mismatch.used_name,
                    new_name=best_suggestion,
                    target_files=[usage.file_path for usage in mismatch.usages],
                    env_files_to_update=[]
                )
                auto_actions.append(action)
                
                rprint(f"   🎯 Auto-fix: {mismatch.used_name} → {best_suggestion}")
        
        if auto_actions:
            rprint(f"\n[yellow]Applying {len(auto_actions)} automatic fixes...[/yellow]")
            return self._apply_actions(auto_actions)
        else:
            rprint("[yellow]⚠️ No high-confidence fixes found for automatic application[/yellow]")
            return FixResult([], [], [], [], 0, 0)


class VariableRenameTransformer(ast.NodeTransformer):
    """AST transformer to rename environment variables in Python code"""
    
    def __init__(self, old_name: str, new_name: str):
        self.old_name = old_name
        self.new_name = new_name
        self.changes_made = False
    
    def visit_Call(self, node: ast.Call) -> ast.Call:
        """Transform function calls that access environment variables"""
        
        # Handle os.getenv(), os.environ.get()
        if (isinstance(node.func, ast.Attribute) and
            node.args and isinstance(node.args[0], ast.Constant) and
            node.args[0].value == self.old_name):
            
            node.args[0] = ast.Constant(value=self.new_name)
            self.changes_made = True
        
        return self.generic_visit(node)
    
    def visit_Subscript(self, node: ast.Subscript) -> ast.Subscript:
        """Transform subscript access like os.environ['KEY']"""
        
        if (isinstance(node.slice, ast.Constant) and
            node.slice.value == self.old_name):
            
            node.slice = ast.Constant(value=self.new_name)
            self.changes_made = True
        
        return self.generic_visit(node)


if __name__ == "__main__":
    # Test the enhanced fixer
    from .scanner import EnhancedEnvScanner
    from .analyzer import EnhancedEnvAnalyzer
    import sys
    
    if len(sys.argv) > 1:
        project_path = sys.argv[1]
    else:
        project_path = "."
    
    # Run complete pipeline
    scanner = EnhancedEnvScanner(project_path)
    scan_result = scanner.scan_everything()
    
    analyzer = EnhancedEnvAnalyzer()
    analysis_result = analyzer.analyze_enhanced(scan_result)
    
    fixer = EnhancedEnvFixer(project_path, dry_run=True)
    
    print(f"\n🔧 Fixer Test (Dry Run)")
    
    if analysis_result.mismatches:
        print(f"Found {len(analysis_result.mismatches)} issues that could be fixed")
        for mismatch in analysis_result.mismatches[:3]:
            print(f"   - {mismatch.used_name}: {mismatch.issue_type}")
    else:
        print("No issues to fix!")
    
    # Test batch fix
    fix_result = fixer.batch_fix(analysis_result)
    print(f"Batch fix would apply {fix_result.success_count}/{fix_result.total_count} fixes")
