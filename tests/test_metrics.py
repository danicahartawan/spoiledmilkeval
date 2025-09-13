"""
Comprehensive tests for metrics module.

Tests all four metrics with various edge cases, positive cases, and overfiring prevention.
"""

import pytest
import math
from src.metrics import (
    deprecation_notice_at_k,
    replacement_coverage,
    authority_at_k,
    time_to_solution,
    evaluate_baseline
)
from src.baselines.result import Result


class TestDeprecationNoticeAtK:
    """Test cases for DeprecationNotice@k metric."""
    
    def test_empty_results(self):
        """Test with empty results list."""
        assert deprecation_notice_at_k([], k=5) == 0.0
    
    def test_zero_k(self):
        """Test with k=0."""
        results = [Result("Test", "http://test.com", "deprecated API", authority_tier=1)]
        assert deprecation_notice_at_k(results, k=0) == 0.0
    
    def test_no_deprecation_language(self):
        """Test with results that don't contain deprecation language."""
        results = [
            Result("How to use React", "https://reactjs.org", "React is a great library", authority_tier=3),
            Result("JavaScript tutorial", "https://mdn.org", "Learn JavaScript basics", authority_tier=3)
        ]
        assert deprecation_notice_at_k(results, k=5) == 0.0
    
    def test_deprecation_in_title(self):
        """Test detection of deprecation language in title."""
        results = [
            Result("API is deprecated", "https://example.com", "Use new API instead", authority_tier=2),
            Result("Regular title", "https://example.com", "Regular content", authority_tier=2)
        ]
        assert deprecation_notice_at_k(results, k=5) == 1.0
    
    def test_deprecation_in_snippet(self):
        """Test detection of deprecation language in snippet."""
        results = [
            Result("Regular title", "https://example.com", "This function has been deprecated", authority_tier=2)
        ]
        assert deprecation_notice_at_k(results, k=5) == 1.0
    
    def test_all_deprecation_patterns(self):
        """Test all supported deprecation patterns."""
        test_cases = [
            "This API is deprecated",
            "Feature was removed in v2.0", 
            "Function was replaced with newFunction",
            "See migration guide for details",
            "Use React hooks instead of class components"
        ]
        
        for text in test_cases:
            results = [Result("Test", "https://example.com", text, authority_tier=2)]
            assert deprecation_notice_at_k(results, k=5) == 1.0, f"Should detect: {text}"
    
    def test_case_insensitive(self):
        """Test that matching is case insensitive."""
        results = [
            Result("API is DEPRECATED", "https://example.com", "Use NEW API instead", authority_tier=2)
        ]
        assert deprecation_notice_at_k(results, k=5) == 1.0
    
    def test_word_boundaries_prevent_overfiring(self):
        """Test that word boundaries prevent false matches."""
        # These should NOT match (overfiring prevention)
        false_positives = [
            "undeprecated code",  # "deprecated" is part of larger word
            "deprecate-something",  # hyphenated, not word boundary  
            "This is not deprecated but deprecated-like",  # Second one should match
        ]
        
        results = [Result("Test", "https://example.com", false_positives[0], authority_tier=2)]
        assert deprecation_notice_at_k(results, k=5) == 0.0
        
        results = [Result("Test", "https://example.com", false_positives[1], authority_tier=2)]
        assert deprecation_notice_at_k(results, k=5) == 0.0
        
        # This one should match because "deprecated" appears as a full word
        results = [Result("Test", "https://example.com", false_positives[2], authority_tier=2)]
        assert deprecation_notice_at_k(results, k=5) == 1.0
    
    def test_k_limit(self):
        """Test that only top-k results are considered."""
        results = [
            Result("Regular title", "https://example.com", "Regular content", authority_tier=2),
            Result("Regular title", "https://example.com", "Regular content", authority_tier=2),
            Result("Deprecated API", "https://example.com", "This is deprecated", authority_tier=2),
        ]
        
        # With k=2, should not find deprecation (it's in position 3)
        assert deprecation_notice_at_k(results, k=2) == 0.0
        
        # With k=3, should find deprecation
        assert deprecation_notice_at_k(results, k=3) == 1.0


class TestReplacementCoverage:
    """Test cases for ReplacementCoverage metric."""
    
    def test_empty_results(self):
        """Test with empty results list."""
        assert replacement_coverage([], k=5) == 0.0
    
    def test_no_replacement_language(self):
        """Test with results that don't contain replacement language."""
        results = [
            Result("How to use React", "https://reactjs.org", "React is a great library", authority_tier=3)
        ]
        assert replacement_coverage(results, k=5) == 0.0
    
    def test_default_heuristic_patterns(self):
        """Test detection with default heuristic replacement patterns."""
        test_cases = [
            "use hooks instead of class components",
            "switch to the new API instead of old one",
            "this is an alternative to the deprecated method",
            "replacement for the old function",
            "migrate to the new version",
            "switch to the newer approach", 
            "this is recommended over the old way",
            "the preferred method is now"
        ]
        
        for text in test_cases:
            results = [Result("Test", "https://example.com", text, authority_tier=2)]
            assert replacement_coverage(results, k=5) == 1.0, f"Should detect: {text}"
    
    def test_custom_expected_replacements(self):
        """Test with custom expected replacement terms."""
        expected = ["getServerSideProps", "Next.js 13"]
        
        results = [
            Result("Migration guide", "https://nextjs.org", "Use getServerSideProps for server-side rendering", authority_tier=3)
        ]
        assert replacement_coverage(results, expected_replacements=expected, k=5) == 1.0
        
        # Should not match with different expected replacements
        expected = ["Vue.js", "Angular"]
        assert replacement_coverage(results, expected_replacements=expected, k=5) == 0.0
    
    def test_k_limit(self):
        """Test that only top-k results are considered."""
        results = [
            Result("Regular", "https://example.com", "Regular content", authority_tier=2),
            Result("Regular", "https://example.com", "Regular content", authority_tier=2),
            Result("Migration", "https://example.com", "Use instead of the old method", authority_tier=2),
        ]
        
        # With k=2, should not find replacement language
        assert replacement_coverage(results, k=2) == 0.0
        
        # With k=3, should find replacement language
        assert replacement_coverage(results, k=3) == 1.0


class TestAuthorityAtK:
    """Test cases for Authority@k metric."""
    
    def test_empty_results(self):
        """Test with empty results list."""
        assert authority_at_k([], k=5) == 0
    
    def test_mixed_authority_levels(self):
        """Test with mixed authority tiers."""
        results = [
            Result("StackOverflow", "https://stackoverflow.com/q/123", "Question", authority_tier=1),
            Result("Blog post", "https://dev.to/user/post", "Article", authority_tier=2),
            Result("Official docs", "https://nextjs.org/docs", "Documentation", authority_tier=3),
        ]
        
        # Should return maximum authority (3)
        assert authority_at_k(results, k=5) == 3
    
    def test_k_limit_affects_max(self):
        """Test that k limit affects which results are considered."""
        results = [
            Result("Low authority", "https://stackoverflow.com/q/123", "Question", authority_tier=1),
            Result("Medium authority", "https://dev.to/user/post", "Article", authority_tier=2),
            Result("High authority", "https://nextjs.org/docs", "Documentation", authority_tier=3),
        ]
        
        # With k=1, only consider first result (authority 1)
        assert authority_at_k(results, k=1) == 1
        
        # With k=2, consider first two results (max authority 2)
        assert authority_at_k(results, k=2) == 2
        
        # With k=3, consider all results (max authority 3)
        assert authority_at_k(results, k=3) == 3
    
    def test_none_authority_ignored(self):
        """Test that None authority values are ignored."""
        results = [
            Result("No authority", "https://example.com", "Content", authority_tier=None),
            Result("Has authority", "https://nextjs.org", "Content", authority_tier=2),
        ]
        
        assert authority_at_k(results, k=5) == 2


class TestTimeToSolution:
    """Test cases for Time-to-Solution metric."""
    
    def test_empty_results(self):
        """Test with empty results list."""
        assert time_to_solution([], k=5) == float('inf')
    
    def test_no_qualifying_results(self):
        """Test when no results meet all criteria."""
        results = [
            # Has deprecation but low authority
            Result("Deprecated API", "https://stackoverflow.com/q/123", "This API is deprecated", authority_tier=1),
            # Has authority but no deprecation
            Result("Regular docs", "https://nextjs.org/docs", "How to use the API", authority_tier=3),
        ]
        
        assert time_to_solution(results, k=5) == float('inf')
    
    def test_perfect_result_first_position(self):
        """Test result that meets all criteria in first position."""
        results = [
            Result(
                "Migration Guide", 
                "https://nextjs.org/docs/migration", 
                "getInitialProps is deprecated. Use instead getServerSideProps for server-side rendering.",
                authority_tier=3
            )
        ]
        
        assert time_to_solution(results, k=5) == 1
    
    def test_perfect_result_later_position(self):
        """Test result that meets all criteria in later position."""
        results = [
            Result("Bad result", "https://example.com", "Regular content", authority_tier=1),
            Result("Another bad result", "https://stackoverflow.com/q/123", "Some question", authority_tier=1),
            Result(
                "Migration Guide", 
                "https://nextjs.org/docs/migration", 
                "getInitialProps is deprecated. Use instead getServerSideProps.",
                authority_tier=3
            )
        ]
        
        assert time_to_solution(results, k=5) == 3
    
    def test_custom_expected_replacements(self):
        """Test with custom expected replacements."""
        expected = ["getServerSideProps"]
        results = [
            Result(
                "Migration Guide",
                "https://nextjs.org/docs", 
                "getInitialProps is deprecated. Migrate to getServerSideProps.",
                authority_tier=3
            )
        ]
        
        assert time_to_solution(results, expected_replacements=expected, k=5) == 1
    
    def test_min_authority_parameter(self):
        """Test min_authority parameter."""
        results = [
            Result(
                "Blog post",
                "https://dev.to/user/post",
                "API is deprecated. Use new API instead of old one.",
                authority_tier=2
            )
        ]
        
        # With min_authority=2, should find result
        assert time_to_solution(results, k=5, min_authority=2) == 1
        
        # With min_authority=3, should not find result
        assert time_to_solution(results, k=5, min_authority=3) == float('inf')
    
    def test_all_three_criteria_required(self):
        """Test that all three criteria (deprecation, replacement, authority) are required."""
        
        # Has deprecation and authority but no replacement
        results = [
            Result("Docs", "https://nextjs.org/docs", "API is deprecated", authority_tier=3)
        ]
        assert time_to_solution(results, k=5) == float('inf')
        
        # Has replacement and authority but no deprecation  
        results = [
            Result("Docs", "https://nextjs.org/docs", "The recommended approach is now newAPI", authority_tier=3)
        ]
        assert time_to_solution(results, k=5) == float('inf')
        
        # Has deprecation and replacement but insufficient authority
        results = [
            Result("Forum", "https://stackoverflow.com/q/123", "API deprecated. Use instead new one.", authority_tier=1)
        ]
        assert time_to_solution(results, k=5) == float('inf')


class TestEvaluateBaseline:
    """Test cases for evaluate_baseline function."""
    
    def test_complete_evaluation(self):
        """Test complete baseline evaluation with all metrics."""
        results = [
            Result(
                "Migration Guide",
                "https://nextjs.org/docs/migration",
                "getInitialProps is deprecated. Use instead getServerSideProps.",
                authority_tier=3
            ),
            Result(
                "Blog Post", 
                "https://dev.to/author/post",
                "Alternative to old approach with examples",
                authority_tier=2
            ),
            Result(
                "Forum Discussion",
                "https://stackoverflow.com/q/123",
                "Discussion about the deprecated feature",
                authority_tier=1
            )
        ]
        
        metrics = evaluate_baseline(results, k=5)
        
        # Should detect deprecation
        assert metrics["deprecation_notice_at_k"] == 1.0
        
        # Should detect replacement language
        assert metrics["replacement_coverage"] == 1.0
        
        # Should return max authority (3)
        assert metrics["authority_at_k"] == 3
        
        # Should find time to solution (first result meets all criteria)
        assert metrics["time_to_solution"] == 1
    
    def test_no_qualifying_results(self):
        """Test evaluation when no results meet criteria."""
        results = [
            Result("Regular content", "https://example.com", "Just regular content", authority_tier=1)
        ]
        
        metrics = evaluate_baseline(results, k=5)
        
        assert metrics["deprecation_notice_at_k"] == 0.0
        assert metrics["replacement_coverage"] == 0.0
        assert metrics["authority_at_k"] == 1  # Still reports authority
        assert metrics["time_to_solution"] == float('inf')


class TestEdgeCases:
    """Test edge cases and error conditions."""
    
    def test_special_characters_in_text(self):
        """Test handling of special characters that might break regex."""
        results = [
            Result("Test", "https://example.com", "API is deprecated (use instead the new one)", authority_tier=3)
        ]
        
        # Should handle parentheses and other special characters
        assert deprecation_notice_at_k(results, k=5) == 1.0
        assert replacement_coverage(results, k=5) == 1.0
    
    def test_very_long_text(self):
        """Test handling of very long text snippets."""
        long_text = "This is a very long snippet. " * 100 + "The API is deprecated. Use instead the new API."
        results = [
            Result("Test", "https://nextjs.org/docs", long_text, authority_tier=3)
        ]
        
        assert deprecation_notice_at_k(results, k=5) == 1.0
        assert replacement_coverage(results, k=5) == 1.0
    
    def test_unicode_text(self):
        """Test handling of Unicode text."""
        results = [
            Result("Test", "https://example.com", "API är deprecated. Use instead nya API.", authority_tier=3)
        ]
        
        # Should still detect English keywords
        assert deprecation_notice_at_k(results, k=5) == 1.0
        assert replacement_coverage(results, k=5) == 1.0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])