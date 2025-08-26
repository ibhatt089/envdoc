"""
Enhanced Environment Variable Analyzer
Analyzes scan results with system environment integration
"""

from typing import Dict, List, Set, Tuple, Optional
from dataclasses import dataclass
from difflib import get_close_matches

from .scanner import EnvUsage, ScanResult

@dataclass
class EnhancedMismatch:
    """Enhanced mismatch with system environment awareness"""
    used_name: str
    usages: List[EnvUsage]
    suggested_matches: List[str]
    confidence_scores: List[float]
    issue_type: str  # 'missing', 'typo', 'inconsistent_naming', 'system_available'
    system_available: bool
    file_available: List[str]  # Files where it's available
    recommended_action: str
    
@dataclass 
class EnhancedAnalysisResult:
    """Enhanced analysis result with system integration"""
    mismatches: List[EnhancedMismatch]
    perfect_matches: List[str]
    system_only_matches: List[str]  # Available in system but not files
    file_only_matches: List[str]    # Available in files but not system
    unused_definitions: List[str]
    sensitive_variables: List[str]
    statistics: Dict[str, any]

class EnhancedEnvAnalyzer:
    """
    Enhanced Environment Variable Analyzer
    Provides comprehensive analysis with system environment integration
    """
    
    # Enhanced naming pattern variations - (pattern, suffix1, suffix2)
    NAMING_PATTERNS = [
        # Database patterns
        ('HOST', 'HOSTNAME'),
        ('USER', 'USERNAME'), 
        ('PASS', 'PASSWORD'),
        ('PASSWD', 'PASSWORD'),
        ('DB', 'DATABASE'),
        
        # URL/Endpoint patterns
        ('URL', 'ENDPOINT'),
        ('BASE_URL', 'URL'),
        ('URI', 'URL'),
        
        # Key/Token patterns  
        ('KEY', 'TOKEN'),
        ('API_KEY', 'KEY'),
        ('SECRET', 'KEY'),
        ('SECRET_KEY', 'SECRET'),
        ('ACCESS_KEY', 'KEY'),
        
        # Enable/Disable patterns
        ('ENABLED', 'ENABLE'),
        ('DISABLED', 'DISABLE'),
        
        # Count/Size patterns
        ('COUNT', 'SIZE'),
        ('LIMIT', 'MAX'),
        ('MIN', 'MINIMUM'),
        ('MAX', 'MAXIMUM'),
        
        # Timeout/Duration patterns
        ('TIMEOUT', 'DURATION'),
        ('TTL', 'TIMEOUT'),
        ('EXPIRY', 'TIMEOUT'),
        ('EXPIRE', 'EXPIRY'),
        
        # Port patterns
        ('PORT', 'PORT_NUMBER'),
    ]
    
    # Enhanced prefix/suffix variations
    COMMON_PREFIXES = [
        # Application specific
        'APP_', 'APPLICATION_', 'SERVICE_', 'PROJECT_',
        
        # Framework specific
        'DJANGO_', 'FLASK_', 'FASTAPI_', 'EXPRESS_',
        
        # Database specific
        'DB_', 'DATABASE_', 'POSTGRES_', 'POSTGRESQL_', 'MYSQL_',
        'REDIS_', 'CACHE_', 'MONGODB_', 'MONGO_',
        'QDRANT_', 'VECTOR_', 'SEARCH_', 'ELASTIC_',
        'NEO4J_', 'GRAPH_', 'CYPHER_',
        
        # Cloud/Infrastructure  
        'AWS_', 'AZURE_', 'GCP_', 'CLOUD_', 'DOCKER_',
        'KUBERNETES_', 'K8S_', 'HELM_',
        
        # API/Network
        'API_', 'HTTP_', 'HTTPS_', 'SERVER_', 'CLIENT_',
        'WEBHOOK_', 'ENDPOINT_', 'PROXY_',
        
        # Authentication/Security
        'JWT_', 'AUTH_', 'OAUTH_', 'SECURITY_', 'SSL_', 'TLS_',
        
        # Monitoring/Logging
        'LOG_', 'LOGGING_', 'DEBUG_', 'MONITOR_', 'METRICS_',
        'SENTRY_', 'ELASTIC_', 'PROMETHEUS_',
        
        # Development/Environment  
        'DEV_', 'DEVELOPMENT_', 'PROD_', 'PRODUCTION_',
        'TEST_', 'TESTING_', 'STAGE_', 'STAGING_',
        
        # Custom project prefixes (can be detected)
        'TRACKERGENAI_', 'TRACKER_',
    ]
    
    def __init__(self):
        self.scan_result: Optional[ScanResult] = None
        self.used_vars: Set[str] = set()
        self.system_vars: Set[str] = set()
        self.file_vars: Set[str] = set()
        
    def analyze_enhanced(self, scan_result: ScanResult) -> EnhancedAnalysisResult:
        """Perform enhanced analysis with system environment integration"""
        
        self.scan_result = scan_result
        self.used_vars = {usage.variable_name for usage in scan_result.usages}
        self.system_vars = set(scan_result.system_variables.keys())
        
        # Get all file-based variables
        all_file_vars = set()
        for file_vars in scan_result.file_variables.values():
            all_file_vars.update(file_vars.keys())
        self.file_vars = all_file_vars
        
        print(f"🔍 Enhanced analysis: {len(self.used_vars)} used, {len(self.system_vars)} system, {len(self.file_vars)} file")
        
        # Find mismatches with system awareness
        mismatches = self._find_enhanced_mismatches()
        
        # Categorize matches
        perfect_matches = list(self.used_vars & (self.system_vars | self.file_vars))
        system_only_matches = list(self.used_vars & self.system_vars - self.file_vars)
        file_only_matches = list(self.used_vars & self.file_vars - self.system_vars)
        
        # Find unused definitions
        all_defined = self.system_vars | self.file_vars
        unused_definitions = list(all_defined - self.used_vars)
        
        # Find sensitive variables
        sensitive_vars = self._find_sensitive_variables()
        
        # Calculate enhanced statistics
        statistics = self._calculate_enhanced_statistics(
            mismatches, perfect_matches, system_only_matches, 
            file_only_matches, unused_definitions, sensitive_vars
        )
        
        return EnhancedAnalysisResult(
            mismatches=mismatches,
            perfect_matches=perfect_matches,
            system_only_matches=system_only_matches,
            file_only_matches=file_only_matches,
            unused_definitions=unused_definitions,
            sensitive_variables=sensitive_vars,
            statistics=statistics
        )
    
    def _find_enhanced_mismatches(self) -> List[EnhancedMismatch]:
        """Find mismatches with enhanced system environment awareness"""
        mismatches = []
        
        all_available = self.system_vars | self.file_vars
        
        for used_var in self.used_vars:
            if used_var not in all_available:
                # Find potential matches from both system and files
                system_suggestions = self._find_suggestions_in_set(used_var, self.system_vars)
                file_suggestions = self._find_suggestions_in_set(used_var, self.file_vars)
                
                # Combine and rank suggestions
                all_suggestions = self._combine_suggestions(system_suggestions, file_suggestions)
                
                # Determine issue type and recommended action
                issue_type, recommended_action = self._classify_enhanced_issue(
                    used_var, system_suggestions, file_suggestions
                )
                
                # Find which files have potential matches
                file_availability = self._find_file_availability(used_var)
                
                # Get all usages for this variable
                var_usages = [usage for usage in self.scan_result.usages 
                             if usage.variable_name == used_var]
                
                mismatch = EnhancedMismatch(
                    used_name=used_var,
                    usages=var_usages,
                    suggested_matches=[s[0] for s in all_suggestions],
                    confidence_scores=[s[1] for s in all_suggestions],
                    issue_type=issue_type,
                    system_available=len(system_suggestions) > 0,
                    file_available=file_availability,
                    recommended_action=recommended_action
                )
                mismatches.append(mismatch)
        
        return mismatches
    
    def _find_suggestions_in_set(self, used_var: str, variable_set: Set[str]) -> List[Tuple[str, float]]:
        """Find suggestions in a specific set of variables"""
        suggestions = []
        var_list = list(variable_set)
        
        # 1. Exact fuzzy matching
        fuzzy_matches = get_close_matches(used_var, var_list, n=5, cutoff=0.6)
        for match in fuzzy_matches:
            similarity = self._calculate_similarity(used_var, match)
            suggestions.append((match, similarity))
        
        # 2. Pattern-based matching
        pattern_matches = self._find_pattern_matches(used_var, var_list)
        suggestions.extend(pattern_matches)
        
        # 3. Prefix/suffix matching
        prefix_suffix_matches = self._find_prefix_suffix_matches(used_var, var_list)
        suggestions.extend(prefix_suffix_matches)
        
        # Remove duplicates and sort by confidence
        suggestions = list(set(suggestions))
        suggestions.sort(key=lambda x: x[1], reverse=True)
        
        return suggestions[:3]  # Return top 3 suggestions per set
    
    def _combine_suggestions(self, system_suggestions: List[Tuple[str, float]], 
                           file_suggestions: List[Tuple[str, float]]) -> List[Tuple[str, float]]:
        """Combine and rank suggestions from system and files"""
        
        # Boost system suggestions slightly (they're immediately available)
        boosted_system = [(var, score * 1.1) for var, score in system_suggestions]
        
        # Combine all suggestions
        all_suggestions = boosted_system + file_suggestions
        
        # Remove duplicates and sort
        unique_suggestions = {}
        for var, score in all_suggestions:
            if var not in unique_suggestions or unique_suggestions[var] < score:
                unique_suggestions[var] = score
        
        # Convert back to list and sort
        result = list(unique_suggestions.items())
        result.sort(key=lambda x: x[1], reverse=True)
        
        return result[:5]  # Return top 5 overall
    
    def _classify_enhanced_issue(self, used_var: str, system_suggestions: List[Tuple[str, float]], 
                                file_suggestions: List[Tuple[str, float]]) -> Tuple[str, str]:
        """Classify issue type and recommend action with system awareness"""
        
        best_system_score = system_suggestions[0][1] if system_suggestions else 0
        best_file_score = file_suggestions[0][1] if file_suggestions else 0
        best_overall_score = max(best_system_score, best_file_score)
        
        if best_overall_score >= 0.9:
            issue_type = 'typo'
            if best_system_score > best_file_score:
                recommended_action = 'use_system_variable'
            else:
                recommended_action = 'use_file_variable'
        elif best_overall_score >= 0.7:
            issue_type = 'inconsistent_naming'
            if system_suggestions and file_suggestions:
                recommended_action = 'choose_source'
            elif system_suggestions:
                recommended_action = 'use_system_variable'
            else:
                recommended_action = 'use_file_variable'
        elif system_suggestions or file_suggestions:
            issue_type = 'similar_available'
            recommended_action = 'review_suggestions'
        else:
            issue_type = 'missing'
            recommended_action = 'create_variable'
        
        return issue_type, recommended_action
    
    def _find_file_availability(self, used_var: str) -> List[str]:
        """Find which files have variables similar to the used variable"""
        file_availability = []
        
        for filename, variables in self.scan_result.file_variables.items():
            # Check for exact matches or close matches in this file
            if used_var in variables:
                file_availability.append(f"{filename} (exact)")
            else:
                # Check for close matches
                close_matches = get_close_matches(used_var, list(variables.keys()), n=1, cutoff=0.8)
                if close_matches:
                    file_availability.append(f"{filename} (similar: {close_matches[0]})")
        
        return file_availability
    
    def _calculate_similarity(self, str1: str, str2: str) -> float:
        """Enhanced similarity calculation"""
        if str1 == str2:
            return 1.0
        
        # Normalize strings
        s1 = str1.lower().replace('_', '').replace('-', '')
        s2 = str2.lower().replace('_', '').replace('-', '')
        
        if s1 == s2:
            return 0.95  # Very high but not perfect (different formatting)
        
        # Multiple similarity metrics
        
        # 1. Character overlap
        common_chars = set(s1) & set(s2)
        total_chars = set(s1) | set(s2)
        char_similarity = len(common_chars) / len(total_chars) if total_chars else 0
        
        # 2. Length similarity
        len_diff = abs(len(s1) - len(s2))
        max_len = max(len(s1), len(s2))
        len_similarity = 1.0 - (len_diff / max_len) if max_len > 0 else 1.0
        
        # 3. Substring similarity
        substr_similarity = 0
        if s1 in s2 or s2 in s1:
            substr_similarity = 0.8
        elif any(part in s2 for part in s1.split('_') if len(part) > 2):
            substr_similarity = 0.6
        
        # 4. Prefix/suffix similarity
        prefix_suffix_sim = 0
        if s1.startswith(s2) or s2.startswith(s1):
            prefix_suffix_sim = 0.7
        elif s1.endswith(s2) or s2.endswith(s1):
            prefix_suffix_sim = 0.6
        
        # Weighted combination
        similarity = (
            char_similarity * 0.3 +
            len_similarity * 0.2 +
            substr_similarity * 0.3 +
            prefix_suffix_sim * 0.2
        )
        
        return min(similarity, 0.95)  # Cap at 0.95 for non-exact matches
    
    def _find_pattern_matches(self, used_var: str, available_vars: List[str]) -> List[Tuple[str, float]]:
        """Find matches based on common naming patterns"""
        pattern_matches = []
        
        for suffix1, suffix2 in self.NAMING_PATTERNS:
            # Check if used_var ends with suffix1
            if used_var.endswith('_' + suffix1):
                prefix = used_var[:-len(suffix1)-1]
                expected = prefix + '_' + suffix2
                if expected in available_vars and expected != used_var:
                    pattern_matches.append((expected, 0.9))
            elif used_var.endswith(suffix1) and not used_var.endswith('_' + suffix1):
                prefix = used_var[:-len(suffix1)]
                expected = prefix + suffix2
                if expected in available_vars and expected != used_var:
                    pattern_matches.append((expected, 0.9))
            
            # Check reverse direction (suffix2 -> suffix1)
            if used_var.endswith('_' + suffix2):
                prefix = used_var[:-len(suffix2)-1] 
                expected = prefix + '_' + suffix1
                if expected in available_vars and expected != used_var:
                    pattern_matches.append((expected, 0.9))
            elif used_var.endswith(suffix2) and not used_var.endswith('_' + suffix2):
                prefix = used_var[:-len(suffix2)]
                expected = prefix + suffix1
                if expected in available_vars and expected != used_var:
                    pattern_matches.append((expected, 0.9))
        
        return pattern_matches
    
    def _find_prefix_suffix_matches(self, used_var: str, available_vars: List[str]) -> List[Tuple[str, float]]:
        """Find matches based on prefix/suffix variations"""
        matches = []
        
        # Try removing common prefixes from used_var
        for prefix in self.COMMON_PREFIXES:
            if used_var.startswith(prefix):
                base_name = used_var[len(prefix):]
                # Look for the base name with other prefixes
                for available_var in available_vars:
                    for other_prefix in self.COMMON_PREFIXES:
                        if available_var.startswith(other_prefix):
                            other_base = available_var[len(other_prefix):]
                            if base_name == other_base:
                                matches.append((available_var, 0.85))
                    
                    # Also check for base name without prefix
                    if available_var == base_name:
                        matches.append((available_var, 0.8))
        
        # Try adding common prefixes to used_var  
        for prefix in self.COMMON_PREFIXES:
            candidate = prefix + used_var
            if candidate in available_vars:
                matches.append((candidate, 0.85))
        
        # Try removing suffixes
        common_suffixes = ['_URL', '_KEY', '_HOST', '_PORT', '_USER', '_PASSWORD']
        for suffix in common_suffixes:
            if used_var.endswith(suffix):
                base_name = used_var[:-len(suffix)]
                for other_suffix in common_suffixes:
                    candidate = base_name + other_suffix
                    if candidate in available_vars:
                        matches.append((candidate, 0.8))
        
        return matches
    
    def _find_sensitive_variables(self) -> List[str]:
        """Find variables that contain sensitive information"""
        sensitive_vars = []
        
        sensitive_patterns = [
            'password', 'passwd', 'pwd', 'secret', 'key', 'token',
            'auth', 'credential', 'private', 'cert', 'ssl', 'api_key',
            'access_key', 'private_key', 'client_secret'
        ]
        
        all_vars = self.used_vars | self.system_vars | self.file_vars
        
        for var in all_vars:
            if any(pattern in var.lower() for pattern in sensitive_patterns):
                sensitive_vars.append(var)
        
        return sensitive_vars
    
    def _calculate_enhanced_statistics(self, mismatches: List[EnhancedMismatch], 
                                     perfect_matches: List[str],
                                     system_only_matches: List[str],
                                     file_only_matches: List[str],
                                     unused_definitions: List[str],
                                     sensitive_vars: List[str]) -> Dict[str, any]:
        """Calculate enhanced analysis statistics"""
        
        total_used = len(self.used_vars)
        total_system = len(self.system_vars)
        total_file = len(self.file_vars)
        
        # Categorize mismatches by type
        mismatch_types = {}
        action_types = {}
        for mismatch in mismatches:
            issue_type = mismatch.issue_type
            action_type = mismatch.recommended_action
            
            mismatch_types[issue_type] = mismatch_types.get(issue_type, 0) + 1
            action_types[action_type] = action_types.get(action_type, 0) + 1
        
        # Calculate enhanced health scores
        perfect_score = len(perfect_matches) / total_used * 100 if total_used > 0 else 100
        system_coverage = len(self.used_vars & self.system_vars) / total_used * 100 if total_used > 0 else 0
        file_coverage = len(self.used_vars & self.file_vars) / total_used * 100 if total_used > 0 else 0
        
        # Overall health considers both perfect matches and availability
        overall_health = (len(perfect_matches) + len(system_only_matches) + len(file_only_matches)) / total_used * 100 if total_used > 0 else 100
        
        return {
            # Basic counts
            'total_variables_used': total_used,
            'total_system_variables': total_system,
            'total_file_variables': total_file,
            
            # Match categories
            'perfect_matches': len(perfect_matches),
            'system_only_matches': len(system_only_matches),
            'file_only_matches': len(file_only_matches),
            'mismatches': len(mismatches),
            'unused_definitions': len(unused_definitions),
            'sensitive_variables': len(sensitive_vars),
            
            # Issue breakdown
            'mismatch_types': mismatch_types,
            'recommended_actions': action_types,
            
            # Health scores
            'perfect_match_score': round(perfect_score, 2),
            'system_coverage_score': round(system_coverage, 2),
            'file_coverage_score': round(file_coverage, 2),
            'overall_health_score': round(overall_health, 2),
            
            # Analysis flags
            'has_system_integration': total_system > 0,
            'has_file_config': total_file > 0,
            'has_sensitive_vars': len(sensitive_vars) > 0,
            'issues_found': len(mismatches) > 0,
        }
    
    def generate_enhanced_report(self, result: EnhancedAnalysisResult) -> str:
        """Generate comprehensive analysis report"""
        report = []
        
        report.append("🏥 EnvDoctor Enhanced Analysis Report")
        report.append("=" * 60)
        
        stats = result.statistics
        
        # Health overview
        report.append(f"📊 Overall Health Score: {stats['overall_health_score']}%")
        report.append(f"   Perfect Matches: {stats['perfect_matches']} ({stats['perfect_match_score']}%)")
        report.append(f"   System Coverage: {stats['system_coverage_score']}%")
        report.append(f"   File Coverage: {stats['file_coverage_score']}%")
        
        # Environment overview
        report.append(f"\n🌍 Environment Overview:")
        report.append(f"   Variables Used in Code: {stats['total_variables_used']}")
        report.append(f"   System Environment Variables: {stats['total_system_variables']}")
        report.append(f"   File-based Variables: {stats['total_file_variables']}")
        
        # Match breakdown
        if result.system_only_matches:
            report.append(f"\n🖥️ Available in System Only ({len(result.system_only_matches)}):")
            for var in sorted(result.system_only_matches)[:10]:
                report.append(f"   - {var}")
            if len(result.system_only_matches) > 10:
                report.append(f"   ... and {len(result.system_only_matches) - 10} more")
        
        if result.file_only_matches:
            report.append(f"\n📄 Available in Files Only ({len(result.file_only_matches)}):")
            for var in sorted(result.file_only_matches)[:10]:
                report.append(f"   - {var}")
            if len(result.file_only_matches) > 10:
                report.append(f"   ... and {len(result.file_only_matches) - 10} more")
        
        # Issues
        if result.mismatches:
            report.append(f"\n❌ Issues Found ({len(result.mismatches)}):")
            
            # Group by issue type
            for issue_type, count in stats['mismatch_types'].items():
                report.append(f"   {issue_type}: {count}")
            
            report.append(f"\n🔧 Recommended Actions:")
            for action_type, count in stats['recommended_actions'].items():
                report.append(f"   {action_type.replace('_', ' ').title()}: {count}")
            
            report.append(f"\n📋 Detailed Issues:")
            for i, mismatch in enumerate(result.mismatches[:5], 1):  # Show first 5
                report.append(f"\n{i}. Variable: {mismatch.used_name}")
                report.append(f"   Issue: {mismatch.issue_type}")
                report.append(f"   Used in {len(mismatch.usages)} location(s)")
                report.append(f"   Recommended: {mismatch.recommended_action}")
                
                if mismatch.system_available:
                    report.append(f"   💡 Available in system environment")
                
                if mismatch.file_available:
                    report.append(f"   📄 Available in files: {', '.join(mismatch.file_available)}")
                
                if mismatch.suggested_matches:
                    report.append(f"   Suggestions:")
                    for j, (suggestion, confidence) in enumerate(zip(mismatch.suggested_matches[:3], mismatch.confidence_scores[:3]), 1):
                        source = "🖥️ system" if suggestion in self.system_vars else "📄 file"
                        report.append(f"     {j}. {suggestion} (confidence: {confidence:.0%}, {source})")
            
            if len(result.mismatches) > 5:
                report.append(f"\n   ... and {len(result.mismatches) - 5} more issues")
        
        # Security notice
        if result.sensitive_variables:
            report.append(f"\n🔒 Sensitive Variables Detected ({len(result.sensitive_variables)}):")
            report.append(f"   Please ensure these are properly secured and not committed to version control.")
            for var in sorted(result.sensitive_variables)[:5]:
                source = "🖥️" if var in self.system_vars else "📄"
                report.append(f"   {source} {var}")
            if len(result.sensitive_variables) > 5:
                report.append(f"   ... and {len(result.sensitive_variables) - 5} more")
        
        # Recommendations
        if stats['overall_health_score'] >= 90:
            report.append(f"\n🎉 Excellent! Your environment configuration is very well organized.")
        elif stats['overall_health_score'] >= 70:
            report.append(f"\n👍 Good configuration with minor issues that are easy to fix.")
            report.append(f"💡 Consider running 'envdoctor --fix' for interactive resolution.")
        else:
            report.append(f"\n⚠️ Several configuration issues found.")
            report.append(f"🔧 Run 'envdoctor --fix' for guided resolution, or 'envdoctor --batch-fix' for automatic fixes.")
        
        return "\n".join(report)


if __name__ == "__main__":
    # Test the enhanced analyzer
    from .scanner import EnhancedEnvScanner
    import sys
    
    if len(sys.argv) > 1:
        project_path = sys.argv[1]
    else:
        project_path = "."
    
    scanner = EnhancedEnvScanner(project_path)
    scan_result = scanner.scan_everything()
    
    analyzer = EnhancedEnvAnalyzer()
    analysis_result = analyzer.analyze_enhanced(scan_result)
    
    print(analyzer.generate_enhanced_report(analysis_result))
