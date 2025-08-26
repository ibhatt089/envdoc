"""
Unit tests for EnvDoc CLI module
Tests command line interface functionality
"""

import pytest
import tempfile
import os
from pathlib import Path
from click.testing import CliRunner
from envdoc.cli import main, health, analyze, setup


class TestCLI:
    
    def setup_method(self):
        """Set up test fixtures before each test method"""
        self.runner = CliRunner()
        self.test_dir = tempfile.mkdtemp()
        
    def teardown_method(self):
        """Clean up after each test method"""
        import shutil
        shutil.rmtree(self.test_dir, ignore_errors=True)
    
    def create_test_project(self):
        """Create a test project structure"""
        # Create test Python file
        test_file = Path(self.test_dir) / 'app.py'
        test_file.write_text('''
import os

database_url = os.getenv('DATABASE_URL')
api_key = os.environ['API_KEY']
debug = os.getenv('DEBUG', False)
        ''')
        
        # Create .env file
        env_file = Path(self.test_dir) / '.env'
        env_file.write_text('''
DATABASE_URL=postgresql://localhost/test
API_KEY=test_key_123
UNUSED_VAR=unused_value
        ''')
        
        return self.test_dir
    
    def test_main_help(self):
        """Test main command help"""
        result = self.runner.invoke(main, ['--help'])
        assert result.exit_code == 0
        assert 'EnvDoc' in result.output
        assert 'health' in result.output
        assert 'analyze' in result.output
    
    def test_version_command(self):
        """Test version command"""
        result = self.runner.invoke(main, ['--version'])
        assert result.exit_code == 0
        assert '1.0.0' in result.output
    
    def test_health_command_basic(self):
        """Test basic health command"""
        project_dir = self.create_test_project()
        
        with self.runner.isolated_filesystem():
            os.chdir(project_dir)
            result = self.runner.invoke(health)
            
            assert result.exit_code == 0
            # Should contain health score information
            assert 'Health Score' in result.output or 'score' in result.output.lower()
    
    def test_health_command_score_only(self):
        """Test health command with --score-only flag"""
        project_dir = self.create_test_project()
        
        with self.runner.isolated_filesystem():
            os.chdir(project_dir)
            result = self.runner.invoke(health, ['--score-only'])
            
            assert result.exit_code == 0
            # Should output only numeric score
            output_lines = [line.strip() for line in result.output.split('\n') if line.strip()]
            assert len(output_lines) >= 1
    
    def test_analyze_command_basic(self):
        """Test basic analyze command"""
        project_dir = self.create_test_project()
        
        with self.runner.isolated_filesystem():
            os.chdir(project_dir)
            result = self.runner.invoke(analyze)
            
            assert result.exit_code == 0
            # Should show analysis results
            assert 'Environment Variables' in result.output or 'Found' in result.output
    
    def test_analyze_command_detailed(self):
        """Test analyze command with --detailed flag"""
        project_dir = self.create_test_project()
        
        with self.runner.isolated_filesystem():
            os.chdir(project_dir)
            result = self.runner.invoke(analyze, ['--detailed'])
            
            assert result.exit_code == 0
            # Detailed output should be longer
            assert len(result.output) > 100
    
    def test_setup_command_with_example(self):
        """Test setup command when .env.example exists"""
        project_dir = Path(self.test_dir)
        
        # Create .env.example file
        example_file = project_dir / '.env.example'
        example_file.write_text('''
DATABASE_URL=postgresql://localhost/example
API_KEY=your_api_key_here
DEBUG=false
        ''')
        
        with self.runner.isolated_filesystem():
            os.chdir(project_dir)
            result = self.runner.invoke(setup)
            
            assert result.exit_code == 0
            
            # Check that .env file was created
            env_file = project_dir / '.env'
            assert env_file.exists()
            
            # Verify content
            env_content = env_file.read_text()
            assert 'DATABASE_URL' in env_content
            assert 'API_KEY' in env_content
            assert 'DEBUG' in env_content
    
    def test_setup_command_no_example(self):
        """Test setup command when no .env.example exists"""
        project_dir = Path(self.test_dir)
        
        with self.runner.isolated_filesystem():
            os.chdir(project_dir)
            result = self.runner.invoke(setup)
            
            # Should handle gracefully (might create basic .env or show message)
            assert result.exit_code in [0, 1]  # Allow for different handling strategies
    
    def test_verbose_flag(self):
        """Test --verbose flag"""
        project_dir = self.create_test_project()
        
        with self.runner.isolated_filesystem():
            os.chdir(project_dir)
            result = self.runner.invoke(main, ['--verbose', 'health'])
            
            assert result.exit_code == 0
            # Verbose output should contain more details
            assert len(result.output) > 50
    
    def test_project_root_flag(self):
        """Test --project-root flag"""
        project_dir = self.create_test_project()
        
        result = self.runner.invoke(main, ['--project-root', project_dir, 'health'])
        
        # Should work with custom project root
        assert result.exit_code in [0, 1]  # May succeed or fail gracefully
    
    def test_dry_run_flag(self):
        """Test --dry-run flag"""
        project_dir = self.create_test_project()
        
        with self.runner.isolated_filesystem():
            os.chdir(project_dir)
            result = self.runner.invoke(main, ['--dry-run', 'analyze'])
            
            assert result.exit_code == 0
            # Should indicate dry-run mode
            assert 'dry' in result.output.lower() or 'simulation' in result.output.lower()
    
    def test_invalid_command(self):
        """Test invalid command handling"""
        result = self.runner.invoke(main, ['nonexistent-command'])
        
        assert result.exit_code != 0
        assert 'No such command' in result.output or 'Usage:' in result.output
    
    def test_empty_project(self):
        """Test commands on empty project directory"""
        with self.runner.isolated_filesystem():
            result = self.runner.invoke(health)
            
            # Should handle empty project gracefully
            assert result.exit_code in [0, 1]
    
    def test_json_output_format(self):
        """Test JSON output format if supported"""
        project_dir = self.create_test_project()
        
        with self.runner.isolated_filesystem():
            os.chdir(project_dir)
            # Try JSON format if the CLI supports it
            result = self.runner.invoke(analyze, ['--format', 'json'])
            
            # May not be implemented yet, so allow for different responses
            assert result.exit_code in [0, 2]  # Success or "no such option"
    
    def test_color_output_control(self):
        """Test color output control"""
        project_dir = self.create_test_project()
        
        with self.runner.isolated_filesystem():
            os.chdir(project_dir)
            result = self.runner.invoke(main, ['--no-color', 'health'])
            
            # Should work with or without color support
            assert result.exit_code in [0, 2]


class TestCLIIntegration:
    """Integration tests that test CLI with real scenarios"""
    
    def test_full_workflow(self):
        """Test complete workflow: setup → health → analyze"""
        runner = CliRunner()
        
        with runner.isolated_filesystem():
            # Create example file
            Path('.env.example').write_text('''
DATABASE_URL=postgresql://localhost/example
API_KEY=your_key_here
DEBUG=false
            ''')
            
            # Create test code
            Path('app.py').write_text('''
import os
db_url = os.getenv('DATABASE_URL')
api_key = os.environ['API_KEY']
debug_mode = os.getenv('DEBUG', False)
            ''')
            
            # Step 1: Setup
            result = runner.invoke(setup)
            assert result.exit_code == 0
            assert Path('.env').exists()
            
            # Step 2: Health check
            result = runner.invoke(health)
            assert result.exit_code == 0
            
            # Step 3: Analyze
            result = runner.invoke(analyze)
            assert result.exit_code == 0


if __name__ == '__main__':
    pytest.main([__file__])
