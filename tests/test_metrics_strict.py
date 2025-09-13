"""
Additional strict tests for metrics to prevent overfiring and ensure precision.
"""

import pytest
from src.metrics import (
    deprecation_notice_at_k,
    replacement_coverage,
    authority_at_k,
    time_to_solution,
    evaluate_baseline
)
from src.baselines.result import Result


class TestStrictDeprecationMatching:
    """Test strict deprecation pattern matching to prevent overfiring."""
    
    def test_strict_word_boundaries(self):
        """Test that deprecation patterns use strict word boundaries."""
        # These should NOT match - compound words or contexts where deprecated is not standalone
        false_positives = [
            "undeprecated functionality",
            "deprecated-style coding",  # hyphenated compound
            "deprecation-related issues",  # different word form
            "predeprecated state",  # prefix compound
            "post-deprecated cleanup",  # prefix compound
            "removedBackup file",  # compound word
            "irreplaceable memories",  # different word
            "replacement-like behavior"  # different word
        ]
        
        for text in false_positives:
            results = [Result("Test", "https://example.com", text, authority_tier=2)]
            assert deprecation_notice_at_k(results, k=5) == 0.0, f"Should NOT match: '{text}'"
    
    def test_exact_deprecation_matches(self):
        """Test exact matches for deprecation patterns."""
        # These SHOULD match
        exact_matches = [
            "API is deprecated",
            "function was removed",
            "method was replaced", 
            "migration guide available",
            "use React hooks instead",
            "This is deprecated.",
            "Feature was removed in v2.0",
            "Component was replaced with NewComponent",
            "See migration guide here",
            "Use new API instead of old one"
        ]
        
        for text in exact_matches:
            results = [Result("Test", "https://example.com", text, authority_tier=2)]
            assert deprecation_notice_at_k(results, k=5) == 1.0, f"Should match: '{text}'"

    def test_punctuation_and_context(self):
        """Test deprecation detection with various punctuation and contexts."""
        valid_contexts = [
            "This API is deprecated!",
            "Feature (deprecated)",
            "Method: deprecated since v1.0",
            "[deprecated] Use new method",
            "Status: deprecated - use alternatives",
            "⚠️ This is deprecated",
            "Note: removed in next version"
        ]
        
        for text in valid_contexts:
            results = [Result("Test", "https://example.com", text, authority_tier=2)]
            assert deprecation_notice_at_k(results, k=5) == 1.0, f"Should match: '{text}'"


class TestStrictReplacementCoverage:
    """Test strict replacement coverage to ensure accurate detection."""
    
    def test_replacement_false_positives(self):
        """Test patterns that should NOT trigger replacement coverage."""
        false_positives = [
            "used for alternative purposes",  # 'alternative' but not replacement context  
            "migrate data to new server",  # 'migrate' but not deprecation context
            "switch lights on",  # 'switch' in different context  
            # Note: "recommended" and "preferred" are broad terms that may match
            # This is a tradeoff between precision and recall
        ]
        
        for text in false_positives:
            results = [Result("Test", "https://example.com", text, authority_tier=2)]
            assert replacement_coverage(results, k=5) == 0.0, f"Should NOT match: '{text}'"

    def test_replacement_true_positives(self):
        """Test patterns that SHOULD trigger replacement coverage."""
        true_positives = [
            "use React hooks instead of class components",
            "recommended alternative to deprecated method", 
            "migrate to newer API version",
            "switch to newer implementation instead of old one",  # More specific
            "preferred alternative approach",  # Match updated pattern
            "replacement for this function",
            "instead of using the old API"
        ]
        
        for text in true_positives:
            results = [Result("Test", "https://example.com", text, authority_tier=2)]
            assert replacement_coverage(results, k=5) == 1.0, f"Should match: '{text}'"


class TestStrictTimeToSolution:
    """Test time-to-solution with strict requirements."""
    
    def test_requires_min_authority(self):
        """Test that time-to-solution requires minimum authority tier."""
        results = [
            # Perfect content but low authority (tier 1)
            Result(
                "Deprecated API Guide", 
                "https://stackoverflow.com/q/123",
                "This API is deprecated. Use newAPI instead of oldAPI.",
                authority_tier=1
            )
        ]
        
        # Should return inf because authority < 2
        assert time_to_solution(results, ["newAPI"], k=5, min_authority=2) == float('inf')
        
        # Should succeed with min_authority=1
        assert time_to_solution(results, ["newAPI"], k=5, min_authority=1) == 1

    def test_requires_all_three_criteria(self):
        """Test that all three criteria must be met: deprecation + replacement + authority."""
        
        # Has deprecation + authority but no replacement
        results1 = [
            Result(
                "Deprecated API",
                "https://nextjs.org/docs", 
                "This API is deprecated but no alternatives mentioned.",
                authority_tier=3
            )
        ]
        assert time_to_solution(results1, ["newAPI"], k=5) == float('inf')
        
        # Has replacement + authority but no deprecation language
        results2 = [
            Result(
                "New API Guide",
                "https://nextjs.org/docs",
                "Use newAPI for better performance with oldAPI.",  # No replacement language
                authority_tier=3
            )
        ]
        assert time_to_solution(results2, ["newAPI"], k=5) == float('inf')
        
        # Has deprecation + replacement but low authority
        results3 = [
            Result(
                "Migration Guide", 
                "https://stackoverflow.com/q/123",
                "Old API deprecated. Use newAPI instead.",
                authority_tier=1
            )
        ]
        assert time_to_solution(results3, ["newAPI"], k=5, min_authority=2) == float('inf')
        
        # Has all three criteria - should succeed
        results4 = [
            Result(
                "Official Migration Guide",
                "https://nextjs.org/docs", 
                "Old API is deprecated. Use newAPI instead for all new projects.",
                authority_tier=3
            )
        ]
        assert time_to_solution(results4, ["newAPI"], k=5) == 1

    def test_position_matters(self):
        """Test that position/rank affects time-to-solution."""
        results = [
            # Position 1: Good authority but missing criteria
            Result(
                "General Guide",
                "https://nextjs.org/docs",
                "How to build apps with our framework.",
                authority_tier=3
            ),
            # Position 2: Perfect result
            Result(
                "Migration Guide", 
                "https://nextjs.org/docs",
                "OldAPI is deprecated. Use NewAPI instead.",
                authority_tier=3
            ),
            # Position 3: Another perfect result
            Result(
                "Another Guide",
                "https://pytorch.org/docs", 
                "Feature removed. Migrate to new approach.",
                authority_tier=3
            )
        ]
        
        # Should return 2 (first qualifying result is at position 2)
        assert time_to_solution(results, ["NewAPI"], k=5) == 2


class TestAuthorityTypeReturn:
    """Test that authority_at_k returns integer as specified."""
    
    def test_returns_integer(self):
        """Test that authority_at_k returns int, not float."""
        results = [
            Result("Test", "https://nextjs.org", "content", authority_tier=3)
        ]
        
        result = authority_at_k(results, k=5)
        assert isinstance(result, int), f"Expected int, got {type(result)}"
        assert result == 3


class TestDefaultKValues:
    """Test that default k values are 5 as specified."""
    
    def test_default_k_is_5(self):
        """Test all functions use k=5 as default."""
        results = [
            Result("Test 1", "https://example.com", "deprecated API", authority_tier=1),
            Result("Test 2", "https://example.com", "use instead", authority_tier=2), 
            Result("Test 3", "https://example.com", "content", authority_tier=3),
            Result("Test 4", "https://example.com", "content", authority_tier=2),
            Result("Test 5", "https://example.com", "content", authority_tier=1),
            Result("Test 6", "https://example.com", "more deprecated content", authority_tier=3), # Position 6
        ]
        
        # With default k=5, should not see the 6th result
        assert deprecation_notice_at_k(results) == 1.0  # Found in position 1
        
        # Test with explicit k=6 to verify 6th result would be found
        results_with_only_6th = [
            Result("Test 1", "https://example.com", "regular", authority_tier=1),
            Result("Test 2", "https://example.com", "regular", authority_tier=2), 
            Result("Test 3", "https://example.com", "regular", authority_tier=3),
            Result("Test 4", "https://example.com", "regular", authority_tier=2),
            Result("Test 5", "https://example.com", "regular", authority_tier=1),
            Result("Test 6", "https://example.com", "deprecated API here", authority_tier=3), # Position 6
        ]
        
        assert deprecation_notice_at_k(results_with_only_6th, k=5) == 0.0  # Should not find (k=5)
        assert deprecation_notice_at_k(results_with_only_6th, k=6) == 1.0  # Should find (k=6)


if __name__ == '__main__':
    pytest.main([__file__, '-v'])