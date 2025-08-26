"""
EnvDoctor Command Line Interface
Comprehensive environment variable management suite
"""

import sys
import argparse
import os
from pathlib import Path

try:
    from rich.console import Console
    from rich.panel import Panel
    from rich import print as rprint
    from rich.progress import Progress, SpinnerColumn, TextColumn
    from rich.table import Table
    RICH_AVAILABLE = True
except ImportError:
    RICH_AVAILABLE = False
    Console = None

from . import __version__
from .manager import EnvManager
from .scanner import EnhancedEnvScanner
from .analyzer import EnhancedEnvAnalyzer
from .fixer import EnhancedEnvFixer

class EnvDoctorCLI:
    """Main CLI handler for EnvDoctor"""
    
    def __init__(self):
        self.console = Console() if RICH_AVAILABLE else None
        
    def print_banner(self):
        """Print the EnvDoctor banner"""
        if RICH_AVAILABLE:
            banner = """
🏥 EnvDoctor v{version} - Complete Environment Variable Management Suite

   Detect • Analyze • Fix • Manage
   System Environment • File Configuration • Code Usage
            """.format(version=__version__)
            
            rprint(Panel(banner, border_style="blue", padding=(1, 2)))
        else:
            print(f"EnvDoctor v{__version__} - Environment Variable Management Suite")
            print("=" * 60)
    
    def run(self):
        """Main CLI entry point"""
        parser = self.create_parser()
        args = parser.parse_args()
        
        # Handle help and version first
        if hasattr(args, 'func'):
            try:
                return args.func(args)
            except KeyboardInterrupt:
                if RICH_AVAILABLE:
                    rprint("\n[yellow]⏹️ Operation interrupted by user[/yellow]")
                else:
                    print("\nOperation interrupted by user")
                return 1
            except Exception as e:
                if args.verbose:
                    import traceback
                    traceback.print_exc()
                else:
                    if RICH_AVAILABLE:
                        rprint(f"[red]❌ Error: {str(e)}[/red]")
                    else:
                        print(f"Error: {str(e)}")
                return 1
        else:
            parser.print_help()
            return 0
    
    def create_parser(self) -> argparse.ArgumentParser:
        """Create the argument parser"""
        
        parser = argparse.ArgumentParser(
            prog='envdoctor',
            description='Complete Environment Variable Management Suite',
            formatter_class=argparse.RawDescriptionHelpFormatter,
            epilog="""
Examples:
  envdoctor scan                    # Scan current directory
  envdoctor scan /path/to/project   # Scan specific project
  envdoctor analyze                 # Analyze environment issues
  envdoctor fix                     # Interactive fix mode
  envdoctor fix --batch --confidence 0.9  # Auto-fix high confidence issues
  envdoctor setup                   # Smart .env setup
  envdoctor manage                  # Complete environment overview
  envdoctor health                  # Quick health check
  
For more information: https://github.com/trackergenai/envdoctor
            """
        )
        
        parser.add_argument(
            '--version',
            action='version',
            version=f'EnvDoctor {__version__}'
        )
        
        parser.add_argument(
            '--verbose', '-v',
            action='store_true',
            help='Enable verbose output and error details'
        )
        
        parser.add_argument(
            '--project-root', '-p',
            type=str,
            default='.',
            help='Project root directory (default: current directory)'
        )
        
        parser.add_argument(
            '--dry-run', '-n',
            action='store_true',
            help='Show what would be done without making changes'
        )
        
        # Subcommands
        subparsers = parser.add_subparsers(dest='command', help='Available commands')
        
        # Scan command
        scan_parser = subparsers.add_parser(
            'scan',
            help='Scan project for environment variable usage'
        )
        scan_parser.add_argument(
            '--output-format', '-f',
            choices=['text', 'json', 'yaml'],
            default='text',
            help='Output format'
        )
        scan_parser.add_argument(
            '--save-results', '-s',
            type=str,
            help='Save scan results to file'
        )
        scan_parser.set_defaults(func=self.cmd_scan)
        
        # Analyze command
        analyze_parser = subparsers.add_parser(
            'analyze',
            help='Analyze environment variable configuration'
        )
        analyze_parser.add_argument(
            '--detailed', '-d',
            action='store_true',
            help='Show detailed analysis including suggestions'
        )
        analyze_parser.add_argument(
            '--report',
            type=str,
            help='Save analysis report to file'
        )
        analyze_parser.set_defaults(func=self.cmd_analyze)
        
        # Fix command
        fix_parser = subparsers.add_parser(
            'fix',
            help='Fix environment variable issues'
        )
        fix_parser.add_argument(
            '--batch', '-b',
            action='store_true',
            help='Batch fix mode (automatic for high confidence issues)'
        )
        fix_parser.add_argument(
            '--confidence', '-c',
            type=float,
            default=0.9,
            help='Minimum confidence for batch fixes (default: 0.9)'
        )
        fix_parser.add_argument(
            '--backup-dir',
            type=str,
            help='Custom backup directory'
        )
        fix_parser.set_defaults(func=self.cmd_fix)
        
        # Setup command
        setup_parser = subparsers.add_parser(
            'setup',
            help='Smart .env file setup and management'
        )
        setup_parser.add_argument(
            '--force',
            action='store_true',
            help='Force recreate .env file even if it exists'
        )
        setup_parser.set_defaults(func=self.cmd_setup)
        
        # Manage command
        manage_parser = subparsers.add_parser(
            'manage',
            help='Complete environment variable overview and management'
        )
        manage_parser.add_argument(
            '--show-system',
            action='store_true',
            help='Show system environment variables'
        )
        manage_parser.add_argument(
            '--show-files',
            action='store_true',
            help='Show file-based variables'
        )
        manage_parser.add_argument(
            '--show-sensitive',
            action='store_true',
            help='Show sensitive variables (use with caution)'
        )
        manage_parser.set_defaults(func=self.cmd_manage)
        
        # Health command
        health_parser = subparsers.add_parser(
            'health',
            help='Quick environment health check'
        )
        health_parser.add_argument(
            '--score-only',
            action='store_true',
            help='Show only the health score'
        )
        health_parser.set_defaults(func=self.cmd_health)
        
        # Doctor command (comprehensive check)
        doctor_parser = subparsers.add_parser(
            'doctor',
            help='Comprehensive environment checkup (scan + analyze + recommendations)'
        )
        doctor_parser.add_argument(
            '--fix-suggestions',
            action='store_true',
            help='Include fix suggestions in the checkup'
        )
        doctor_parser.set_defaults(func=self.cmd_doctor)
        
        return parser
    
    def cmd_scan(self, args) -> int:
        """Scan command implementation"""
        self.print_banner()
        
        if RICH_AVAILABLE:
            rprint(f"[cyan]🔍 Scanning project: {Path(args.project_root).resolve()}[/cyan]")
        
        scanner = EnhancedEnvScanner(args.project_root)
        
        with self._progress_context("Scanning project files..."):
            result = scanner.scan_everything()
        
        # Display results
        if args.output_format == 'json':
            import json
            output = {
                'statistics': result.usage_stats,
                'variables_used': list(set(usage.variable_name for usage in result.usages)),
                'system_variables_count': len(result.system_variables),
                'file_variables': {k: list(v.keys()) for k, v in result.file_variables.items()},
            }
            print(json.dumps(output, indent=2))
        
        elif args.output_format == 'yaml':
            try:
                import yaml
                output = {
                    'statistics': result.usage_stats,
                    'variables_used': list(set(usage.variable_name for usage in result.usages)),
                    'system_variables_count': len(result.system_variables),
                    'file_variables': {k: list(v.keys()) for k, v in result.file_variables.items()},
                }
                print(yaml.dump(output, default_flow_style=False))
            except ImportError:
                if RICH_AVAILABLE:
                    rprint("[red]❌ PyYAML not installed. Use 'pip install pyyaml' for YAML output.[/red]")
                else:
                    print("PyYAML not installed. Use 'pip install pyyaml' for YAML output.")
                return 1
        
        else:  # text format
            self._display_scan_results_text(result)
        
        # Save results if requested
        if args.save_results:
            try:
                self._save_scan_results(result, args.save_results, args.output_format)
                if RICH_AVAILABLE:
                    rprint(f"[green]💾 Results saved to: {args.save_results}[/green]")
                else:
                    print(f"Results saved to: {args.save_results}")
            except Exception as e:
                if RICH_AVAILABLE:
                    rprint(f"[red]❌ Failed to save results: {str(e)}[/red]")
                else:
                    print(f"Failed to save results: {str(e)}")
        
        return 0
    
    def cmd_analyze(self, args) -> int:
        """Analyze command implementation"""
        self.print_banner()
        
        # First scan
        scanner = EnhancedEnvScanner(args.project_root)
        with self._progress_context("Scanning project..."):
            scan_result = scanner.scan_everything()
        
        # Then analyze
        analyzer = EnhancedEnvAnalyzer()
        with self._progress_context("Analyzing environment configuration..."):
            analysis_result = analyzer.analyze_enhanced(scan_result)
        
        # Display results
        report = analyzer.generate_enhanced_report(analysis_result)
        
        if RICH_AVAILABLE:
            rprint(report)
        else:
            print(report)
        
        # Save report if requested
        if args.report:
            try:
                with open(args.report, 'w', encoding='utf-8') as f:
                    f.write(report)
                if RICH_AVAILABLE:
                    rprint(f"\n[green]📄 Report saved to: {args.report}[/green]")
                else:
                    print(f"\nReport saved to: {args.report}")
            except Exception as e:
                if RICH_AVAILABLE:
                    rprint(f"[red]❌ Failed to save report: {str(e)}[/red]")
                else:
                    print(f"Failed to save report: {str(e)}")
        
        # Return exit code based on health
        health_score = analysis_result.statistics.get('overall_health_score', 0)
        if health_score >= 90:
            return 0  # Excellent
        elif health_score >= 70:
            return 1  # Good but has issues
        else:
            return 2  # Poor health
    
    def cmd_fix(self, args) -> int:
        """Fix command implementation"""
        self.print_banner()
        
        # Get analysis first
        scanner = EnhancedEnvScanner(args.project_root)
        with self._progress_context("Scanning and analyzing..."):
            scan_result = scanner.scan_everything()
            
            analyzer = EnhancedEnvAnalyzer()
            analysis_result = analyzer.analyze_enhanced(scan_result)
        
        if not analysis_result.mismatches:
            if RICH_AVAILABLE:
                rprint("[green]🎉 No issues found to fix![/green]")
            else:
                print("No issues found to fix!")
            return 0
        
        # Initialize fixer
        fixer = EnhancedEnvFixer(args.project_root, dry_run=args.dry_run)
        
        # Apply fixes
        if args.batch:
            if RICH_AVAILABLE:
                rprint(f"[yellow]🤖 Batch fixing with confidence threshold: {args.confidence:.0%}[/yellow]")
            fix_result = fixer.batch_fix(analysis_result, args.confidence)
        else:
            if RICH_AVAILABLE:
                rprint("[cyan]🔧 Interactive fix mode[/cyan]")
            fix_result = fixer.interactive_fix(analysis_result)
        
        # Return appropriate exit code
        if fix_result.success_count == fix_result.total_count:
            return 0  # All fixes succeeded
        elif fix_result.success_count > 0:
            return 1  # Some fixes succeeded
        else:
            return 2  # No fixes succeeded
    
    def cmd_setup(self, args) -> int:
        """Setup command implementation"""
        self.print_banner()
        
        manager = EnvManager(args.project_root)
        success = manager.smart_env_setup()
        
        return 0 if success else 1
    
    def cmd_manage(self, args) -> int:
        """Manage command implementation"""
        self.print_banner()
        
        manager = EnvManager(args.project_root)
        
        with self._progress_context("Discovering environment sources..."):
            sources = manager.show_complete_environment_view()
        
        # Additional detailed views if requested
        if args.show_system or args.show_files or args.show_sensitive:
            if RICH_AVAILABLE:
                rprint("\n[cyan]🔍 Detailed View[/cyan]")
            
            if args.show_system:
                self._show_system_variables()
            
            if args.show_files:
                self._show_file_variables(sources)
            
            if args.show_sensitive:
                self._show_sensitive_variables()
        
        return 0
    
    def cmd_health(self, args) -> int:
        """Health command implementation"""
        
        if not args.score_only:
            self.print_banner()
        
        # Quick health check
        scanner = EnhancedEnvScanner(args.project_root)
        with self._progress_context("Quick health scan..."):
            scan_result = scanner.scan_everything()
            
            analyzer = EnhancedEnvAnalyzer()
            analysis_result = analyzer.analyze_enhanced(scan_result)
        
        health_score = analysis_result.statistics.get('overall_health_score', 0)
        
        if args.score_only:
            print(f"{health_score:.1f}")
            return 0
        
        # Display health summary
        if RICH_AVAILABLE:
            if health_score >= 90:
                rprint(f"[green]🎉 Health Score: {health_score:.1f}% - Excellent![/green]")
            elif health_score >= 70:
                rprint(f"[yellow]👍 Health Score: {health_score:.1f}% - Good[/yellow]")
            else:
                rprint(f"[red]⚠️ Health Score: {health_score:.1f}% - Needs Attention[/red]")
        else:
            print(f"Health Score: {health_score:.1f}%")
        
        # Quick summary
        stats = analysis_result.statistics
        if RICH_AVAILABLE:
            rprint(f"   Variables Used: {stats.get('total_variables_used', 0)}")
            rprint(f"   Perfect Matches: {stats.get('perfect_matches', 0)}")
            rprint(f"   Issues Found: {stats.get('mismatches', 0)}")
        
        if health_score < 70:
            if RICH_AVAILABLE:
                rprint(f"\n[dim]💡 Run 'envdoctor analyze' for details or 'envdoctor fix' to resolve issues[/dim]")
        
        return 0 if health_score >= 70 else 1
    
    def cmd_doctor(self, args) -> int:
        """Doctor command - comprehensive checkup"""
        self.print_banner()
        
        if RICH_AVAILABLE:
            rprint("[bold cyan]🩺 Comprehensive Environment Checkup[/bold cyan]")
        
        # Full pipeline
        scanner = EnhancedEnvScanner(args.project_root)
        with self._progress_context("Comprehensive scan..."):
            scan_result = scanner.scan_everything()
        
        analyzer = EnhancedEnvAnalyzer()
        with self._progress_context("Deep analysis..."):
            analysis_result = analyzer.analyze_enhanced(scan_result)
        
        # Show full report
        report = analyzer.generate_enhanced_report(analysis_result)
        if RICH_AVAILABLE:
            rprint(report)
        else:
            print(report)
        
        # Show fix suggestions if requested
        if args.fix_suggestions and analysis_result.mismatches:
            if RICH_AVAILABLE:
                rprint(f"\n[cyan]🔧 Fix Suggestions[/cyan]")
                rprint(f"Run one of these commands to fix the issues:")
                rprint(f"   • envdoctor fix                     # Interactive fixes")
                rprint(f"   • envdoctor fix --batch             # Auto-fix high confidence issues")
                rprint(f"   • envdoctor fix --batch -c 0.8      # Auto-fix medium+ confidence issues")
        
        # Return based on health
        health_score = analysis_result.statistics.get('overall_health_score', 0)
        return 0 if health_score >= 90 else (1 if health_score >= 70 else 2)
    
    def _progress_context(self, description: str):
        """Create a progress context manager"""
        if RICH_AVAILABLE:
            class ProgressContext:
                def __init__(self, desc, console):
                    self.desc = desc
                    self.console = console
                    self.progress = None
                
                def __enter__(self):
                    self.progress = Progress(
                        SpinnerColumn(),
                        TextColumn("[progress.description]{task.description}"),
                        console=self.console,
                        transient=True
                    )
                    self.progress.start()
                    self.progress.add_task(self.desc)
                    return self
                
                def __exit__(self, *args):
                    if self.progress:
                        self.progress.stop()
            
            return ProgressContext(description, self.console)
        else:
            # Fallback context manager that just prints the description
            class SimpleProgress:
                def __init__(self, desc):
                    self.desc = desc
                def __enter__(self):
                    print(f"{self.desc}")
                    return self
                def __exit__(self, *args):
                    pass
            
            return SimpleProgress(description)
    
    def _display_scan_results_text(self, result):
        """Display scan results in text format"""
        
        if RICH_AVAILABLE:
            rprint(f"\n[cyan]📊 Scan Results[/cyan]")
            
            stats_table = Table(title="Statistics")
            stats_table.add_column("Metric", style="cyan")
            stats_table.add_column("Count", style="green")
            
            for key, value in result.usage_stats.items():
                readable_key = key.replace('_', ' ').title()
                stats_table.add_row(readable_key, str(value))
            
            self.console.print(stats_table)
            
            # Show used variables
            used_vars = sorted(set(usage.variable_name for usage in result.usages))
            if used_vars:
                rprint(f"\n[cyan]🔍 Variables Used in Code ({len(used_vars)}):[/cyan]")
                for var in used_vars[:20]:  # Show first 20
                    rprint(f"   - {var}")
                if len(used_vars) > 20:
                    rprint(f"   ... and {len(used_vars) - 20} more")
            
            # Show file variables
            if result.file_variables:
                rprint(f"\n[cyan]📄 File-based Variables:[/cyan]")
                for filename, variables in result.file_variables.items():
                    rprint(f"   {filename}: {len(variables)} variables")
                    for var in list(variables.keys())[:5]:  # Show first 5
                        rprint(f"      - {var}")
                    if len(variables) > 5:
                        rprint(f"      ... and {len(variables) - 5} more")
        
        else:
            print(f"\nScan Results:")
            print("-" * 30)
            for key, value in result.usage_stats.items():
                readable_key = key.replace('_', ' ').title()
                print(f"{readable_key}: {value}")
    
    def _save_scan_results(self, result, filename: str, format_type: str):
        """Save scan results to file"""
        
        output_data = {
            'statistics': result.usage_stats,
            'variables_used': list(set(usage.variable_name for usage in result.usages)),
            'system_variables_count': len(result.system_variables),
            'file_variables': {k: list(v.keys()) for k, v in result.file_variables.items()},
            'usage_details': [
                {
                    'variable': usage.variable_name,
                    'file': usage.file_path,
                    'line': usage.line_number,
                    'method': usage.access_method
                }
                for usage in result.usages
            ]
        }
        
        if format_type == 'json':
            import json
            with open(filename, 'w') as f:
                json.dump(output_data, f, indent=2)
        
        elif format_type == 'yaml':
            import yaml
            with open(filename, 'w') as f:
                yaml.dump(output_data, f, default_flow_style=False)
        
        else:  # text
            with open(filename, 'w') as f:
                f.write("EnvDoctor Scan Results\n")
                f.write("=" * 30 + "\n\n")
                
                f.write("Statistics:\n")
                for key, value in result.usage_stats.items():
                    f.write(f"  {key.replace('_', ' ').title()}: {value}\n")
                
                f.write(f"\nVariables Used ({len(set(usage.variable_name for usage in result.usages))}):\n")
                for var in sorted(set(usage.variable_name for usage in result.usages)):
                    f.write(f"  - {var}\n")
    
    def _show_system_variables(self):
        """Show system environment variables"""
        system_vars = dict(os.environ)
        
        if RICH_AVAILABLE:
            rprint(f"\n[green]🖥️ System Environment Variables ({len(system_vars)}):[/green]")
            
            # Show a sample of system variables  
            sample_vars = list(system_vars.items())[:20]
            for name, value in sample_vars:
                preview = value[:50] + "..." if len(value) > 50 else value
                rprint(f"   {name}: {preview}")
            
            if len(system_vars) > 20:
                rprint(f"   ... and {len(system_vars) - 20} more")
        else:
            print(f"\nSystem Environment Variables ({len(system_vars)}):")
            sample_vars = list(system_vars.items())[:10]
            for name, value in sample_vars:
                preview = value[:50] + "..." if len(value) > 50 else value
                print(f"   {name}: {preview}")
    
    def _show_file_variables(self, sources):
        """Show file-based variables"""
        file_sources = [s for s in sources if s.type == 'file']
        
        if RICH_AVAILABLE:
            rprint(f"\n[yellow]📄 File-based Variables:[/yellow]")
            for source in file_sources:
                rprint(f"   {source.name}: {len(source.variables)} variables")
        else:
            print(f"\nFile-based Variables:")
            for source in file_sources:
                print(f"   {source.name}: {len(source.variables)} variables")
    
    def _show_sensitive_variables(self):
        """Show sensitive variables (with warning)"""
        if RICH_AVAILABLE:
            rprint(f"\n[red]🔒 Warning: Sensitive variables detected[/red]")
            rprint(f"[dim]Use this information carefully and ensure proper security[/dim]")
        else:
            print(f"\nWarning: Sensitive variables detected")
            print("Use this information carefully and ensure proper security")


def main():
    """CLI entry point"""
    cli = EnvDoctorCLI()
    sys.exit(cli.run())


if __name__ == "__main__":
    main()
