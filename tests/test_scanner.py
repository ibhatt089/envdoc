"""
Unit tests for EnvDoc Scanner module
Tests environment variable detection in code files
"""

import pytest
import tempfile
import os
from pathlib import Path
from envdoc.scanner import EnhancedEnvScanner


class TestEnvScanner:
    
    def setup_method(self):
        """Set up test fixtures before each test method"""
        self.scanner = EnhancedEnvScanner()
        self.test_dir = tempfile.mkdtemp()
        
    def teardown_method(self):
        """Clean up after each test method"""
        import shutil
        shutil.rmtree(self.test_dir, ignore_errors=True)
    
    def create_test_file(self, filename: str, content: str) -> str:
        """Helper method to create test files"""
        file_path = Path(self.test_dir) / filename
        file_path.parent.mkdir(parents=True, exist_ok=True)
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(content)
        return str(file_path)
    
    def test_scan_simple_os_getenv(self):
        """Test detection of os.getenv() calls"""
        content = '''
import os

database_url = os.getenv('DATABASE_URL', 'localhost')
api_key = os.getenv('API_KEY')
debug = os.getenv('DEBUG', False)
        '''
        file_path = self.create_test_file('test.py', content)
        
        results = self.scanner.scan_file(file_path)
        
        assert len(results) == 3
        env_vars = [r['variable'] for r in results]
        assert 'DATABASE_URL' in env_vars
        assert 'API_KEY' in env_vars
        assert 'DEBUG' in env_vars
    
    def test_scan_os_environ_access(self):
        """Test detection of os.environ[] access"""
        content = '''
import os

host = os.environ['HOST']
port = os.environ.get('PORT', 8080)
secret = os.environ.get('SECRET_KEY')
        '''
        file_path = self.create_test_file('config.py', content)
        
        results = self.scanner.scan_file(file_path)
        
        assert len(results) == 3
        env_vars = [r['variable'] for r in results]
        assert 'HOST' in env_vars
        assert 'PORT' in env_vars
        assert 'SECRET_KEY' in env_vars
    
    def test_scan_mixed_patterns(self):
        """Test detection of mixed environment variable patterns"""
        content = '''
import os
from os import getenv

# Different patterns
db_host = os.getenv('DB_HOST')
db_port = os.environ['DB_PORT']
db_name = os.environ.get('DB_NAME', 'mydb')
redis_url = getenv('REDIS_URL')
        '''
        file_path = self.create_test_file('mixed.py', content)
        
        results = self.scanner.scan_file(file_path)
        
        assert len(results) == 4
        env_vars = [r['variable'] for r in results]
        assert 'DB_HOST' in env_vars
        assert 'DB_PORT' in env_vars
        assert 'DB_NAME' in env_vars
        assert 'REDIS_URL' in env_vars
    
    def test_scan_docker_compose(self):
        """Test detection in docker-compose.yml files"""
        content = '''
version: '3.8'
services:
  web:
    environment:
      - DATABASE_URL=${DATABASE_URL}
      - API_KEY=${API_KEY:-default_key}
      - DEBUG=${DEBUG}
    env_file:
      - .env
        '''
        file_path = self.create_test_file('docker-compose.yml', content)
        
        results = self.scanner.scan_file(file_path)
        
        assert len(results) >= 3
        env_vars = [r['variable'] for r in results]
        assert 'DATABASE_URL' in env_vars
        assert 'API_KEY' in env_vars
        assert 'DEBUG' in env_vars
    
    def test_scan_directory(self):
        """Test scanning entire directory"""
        # Create multiple test files
        self.create_test_file('app.py', 'import os\ndb = os.getenv("DATABASE_URL")')
        self.create_test_file('config.py', 'import os\nkey = os.environ["API_KEY"]')
        self.create_test_file('utils.py', 'import os\ndebug = os.getenv("DEBUG")')
        
        results = self.scanner.scan_directory(self.test_dir)
        
        assert len(results) >= 3
        all_vars = []
        for file_results in results.values():
            all_vars.extend([r['variable'] for r in file_results])
        
        assert 'DATABASE_URL' in all_vars
        assert 'API_KEY' in all_vars
        assert 'DEBUG' in all_vars
    
    def test_ignore_comments(self):
        """Test that commented code is ignored"""
        content = '''
import os

# This should be ignored
# api_key = os.getenv('COMMENTED_VAR')

active_var = os.getenv('ACTIVE_VAR')
        '''
        file_path = self.create_test_file('comments.py', content)
        
        results = self.scanner.scan_file(file_path)
        
        assert len(results) == 1
        assert results[0]['variable'] == 'ACTIVE_VAR'
    
    def test_ignore_strings(self):
        """Test that strings containing env var patterns are handled correctly"""
        content = '''
import os

# This should not be detected as env var usage
help_text = "Use os.getenv('YOUR_VAR') to access environment variables"

# This should be detected
real_var = os.getenv('REAL_VAR')
        '''
        file_path = self.create_test_file('strings.py', content)
        
        results = self.scanner.scan_file(file_path)
        
        # Should only detect the actual function call, not the string
        assert len(results) == 1
        assert results[0]['variable'] == 'REAL_VAR'
    
    def test_invalid_file(self):
        """Test handling of invalid/non-existent files"""
        results = self.scanner.scan_file('/nonexistent/file.py')
        assert results == []
    
    def test_empty_file(self):
        """Test handling of empty files"""
        file_path = self.create_test_file('empty.py', '')
        results = self.scanner.scan_file(file_path)
        assert results == []


if __name__ == '__main__':
    pytest.main([__file__])
