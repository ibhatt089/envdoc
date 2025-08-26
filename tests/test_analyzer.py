"""
Unit tests for EnvDoc Analyzer module
Tests environment variable analysis and mismatch detection
"""

import pytest
import tempfile
import os
from pathlib import Path
from envdoc.analyzer import EnhancedEnvAnalyzer


class TestEnvAnalyzer:
    
    def setup_method(self):
        """Set up test fixtures before each test method"""
        self.analyzer = EnhancedEnvAnalyzer()
        self.test_dir = tempfile.mkdtemp()
        
    def teardown_method(self):
        """Clean up after each test method"""
        import shutil
        shutil.rmtree(self.test_dir, ignore_errors=True)
    
    def create_env_file(self, filename: str, content: str) -> str:
        """Helper method to create .env files"""
        file_path = Path(self.test_dir) / filename
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(content)
        return str(file_path)
    
    def test_load_env_file(self):
        """Test loading environment variables from .env file"""
        env_content = '''
DATABASE_URL=postgresql://localhost/mydb
API_KEY=secret123
DEBUG=true
# Comment should be ignored
REDIS_URL=redis://localhost
        '''
        env_path = self.create_env_file('.env', env_content)
        
        env_vars = self.analyzer.load_env_file(env_path)
        
        assert len(env_vars) == 4
        assert env_vars['DATABASE_URL'] == 'postgresql://localhost/mydb'
        assert env_vars['API_KEY'] == 'secret123'
        assert env_vars['DEBUG'] == 'true'
        assert env_vars['REDIS_URL'] == 'redis://localhost'
    
    def test_compare_exact_matches(self):
        """Test comparison with exact matches"""
        code_usage = [
            {'variable': 'DATABASE_URL', 'file': 'app.py', 'line': 10},
            {'variable': 'API_KEY', 'file': 'config.py', 'line': 5},
            {'variable': 'DEBUG', 'file': 'app.py', 'line': 15}
        ]
        
        env_vars = {
            'DATABASE_URL': 'postgresql://localhost/mydb',
            'API_KEY': 'secret123',
            'DEBUG': 'true'
        }
        
        analysis = self.analyzer.analyze_usage(code_usage, env_vars)
        
        assert analysis['matches'] == 3
        assert analysis['missing_in_env'] == 0
        assert analysis['unused_in_env'] == 0
        assert len(analysis['issues']) == 0
    
    def test_missing_variables(self):
        """Test detection of missing environment variables"""
        code_usage = [
            {'variable': 'DATABASE_URL', 'file': 'app.py', 'line': 10},
            {'variable': 'MISSING_VAR', 'file': 'config.py', 'line': 5},
            {'variable': 'ANOTHER_MISSING', 'file': 'app.py', 'line': 15}
        ]
        
        env_vars = {
            'DATABASE_URL': 'postgresql://localhost/mydb',
        }
        
        analysis = self.analyzer.analyze_usage(code_usage, env_vars)
        
        assert analysis['matches'] == 1
        assert analysis['missing_in_env'] == 2
        assert len(analysis['issues']) == 2
        
        issue_vars = [issue['variable'] for issue in analysis['issues'] if issue['type'] == 'missing']
        assert 'MISSING_VAR' in issue_vars
        assert 'ANOTHER_MISSING' in issue_vars
    
    def test_unused_variables(self):
        """Test detection of unused environment variables"""
        code_usage = [
            {'variable': 'DATABASE_URL', 'file': 'app.py', 'line': 10},
        ]
        
        env_vars = {
            'DATABASE_URL': 'postgresql://localhost/mydb',
            'UNUSED_VAR1': 'value1',
            'UNUSED_VAR2': 'value2'
        }
        
        analysis = self.analyzer.analyze_usage(code_usage, env_vars)
        
        assert analysis['matches'] == 1
        assert analysis['unused_in_env'] == 2
        assert len(analysis['issues']) == 2
        
        issue_vars = [issue['variable'] for issue in analysis['issues'] if issue['type'] == 'unused']
        assert 'UNUSED_VAR1' in issue_vars
        assert 'UNUSED_VAR2' in issue_vars
    
    def test_pattern_suggestions(self):
        """Test pattern-based suggestions for similar variables"""
        code_usage = [
            {'variable': 'DB_HOST', 'file': 'app.py', 'line': 10},
            {'variable': 'CACHE_HOST', 'file': 'app.py', 'line': 12},
        ]
        
        env_vars = {
            'DB_HOSTNAME': 'localhost',
            'CACHE_HOSTNAME': 'redis-server'
        }
        
        analysis = self.analyzer.analyze_usage(code_usage, env_vars)
        
        # Should detect pattern and suggest corrections
        assert analysis['missing_in_env'] == 2
        suggestions = []
        for issue in analysis['issues']:
            if 'suggestions' in issue and issue['suggestions']:
                suggestions.extend(issue['suggestions'])
        
        # Should suggest DB_HOSTNAME for DB_HOST
        assert any('DB_HOSTNAME' in str(s) for s in suggestions)
        assert any('CACHE_HOSTNAME' in str(s) for s in suggestions)
    
    def test_fuzzy_matching(self):
        """Test fuzzy string matching for suggestions"""
        code_usage = [
            {'variable': 'DATABASE_URl', 'file': 'app.py', 'line': 10},  # Typo: l instead of L
            {'variable': 'API_KEy', 'file': 'config.py', 'line': 5},      # Typo: y instead of Y
        ]
        
        env_vars = {
            'DATABASE_URL': 'postgresql://localhost/mydb',
            'API_KEY': 'secret123'
        }
        
        analysis = self.analyzer.analyze_usage(code_usage, env_vars)
        
        # Should suggest corrections for typos
        suggestions = []
        for issue in analysis['issues']:
            if 'suggestions' in issue and issue['suggestions']:
                suggestions.extend([s['suggested'] for s in issue['suggestions']])
        
        assert 'DATABASE_URL' in suggestions
        assert 'API_KEY' in suggestions
    
    def test_confidence_scoring(self):
        """Test confidence scoring for suggestions"""
        code_usage = [
            {'variable': 'DB_URL', 'file': 'app.py', 'line': 10},
        ]
        
        env_vars = {
            'DATABASE_URL': 'postgresql://localhost/mydb',
            'REDIS_URL': 'redis://localhost',
            'COMPLETELY_DIFFERENT': 'value'
        }
        
        analysis = self.analyzer.analyze_usage(code_usage, env_vars)
        
        # Find suggestions for DB_URL
        suggestions = []
        for issue in analysis['issues']:
            if issue['variable'] == 'DB_URL' and 'suggestions' in issue:
                suggestions = issue['suggestions']
        
        assert len(suggestions) > 0
        
        # DATABASE_URL should have higher confidence than COMPLETELY_DIFFERENT
        db_confidence = next((s['confidence'] for s in suggestions if s['suggested'] == 'DATABASE_URL'), 0)
        different_confidence = next((s['confidence'] for s in suggestions if s['suggested'] == 'COMPLETELY_DIFFERENT'), 1)
        
        assert db_confidence > different_confidence
    
    def test_health_score_calculation(self):
        """Test health score calculation"""
        # Perfect score scenario
        code_usage = [
            {'variable': 'VAR1', 'file': 'app.py', 'line': 10},
            {'variable': 'VAR2', 'file': 'app.py', 'line': 11},
        ]
        
        env_vars = {
            'VAR1': 'value1',
            'VAR2': 'value2'
        }
        
        analysis = self.analyzer.analyze_usage(code_usage, env_vars)
        health_score = self.analyzer.calculate_health_score(analysis)
        
        assert health_score == 100.0
        
        # Partial score scenario
        code_usage = [
            {'variable': 'VAR1', 'file': 'app.py', 'line': 10},
            {'variable': 'VAR2', 'file': 'app.py', 'line': 11},
            {'variable': 'MISSING', 'file': 'app.py', 'line': 12},
        ]
        
        env_vars = {
            'VAR1': 'value1',
            'VAR2': 'value2',
            'UNUSED': 'unused_value'
        }
        
        analysis = self.analyzer.analyze_usage(code_usage, env_vars)
        health_score = self.analyzer.calculate_health_score(analysis)
        
        # Should be less than 100 due to missing and unused variables
        assert 0 < health_score < 100
    
    def test_empty_analysis(self):
        """Test analysis with empty inputs"""
        analysis = self.analyzer.analyze_usage([], {})
        health_score = self.analyzer.calculate_health_score(analysis)
        
        assert analysis['matches'] == 0
        assert analysis['missing_in_env'] == 0
        assert analysis['unused_in_env'] == 0
        assert health_score == 100.0  # Perfect score for empty (no issues)
    
    def test_invalid_env_file(self):
        """Test handling of invalid .env files"""
        env_vars = self.analyzer.load_env_file('/nonexistent/.env')
        assert env_vars == {}


if __name__ == '__main__':
    pytest.main([__file__])
