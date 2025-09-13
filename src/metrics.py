"""
Metrics for evaluating baseline search systems.

Implements four key metrics for deprecation search evaluation:
- DeprecationNotice@k: Detection of deprecation language
- ReplacementCoverage: Coverage of known replacement tokens
- Authority@k: Maximum authority score among top-k results
- Time-to-Solution: Rank of first result satisfying notice + replacement + authority
"""

import re
from typing import List, Optional, Union
try:
    from .baselines.result import Result
except ImportError:
    from baselines.result import Result


def deprecation_notice_at_k(results: List[Result], k: int = 5) -> float:
    """
    DeprecationNotice@k: Check if any result in top-k contains deprecation language.
    
    Uses regex pattern to detect deprecation-related terms:
    - deprecated
    - removed  
    - replaced
    - migration guide
    
    Args:
        results: List of search results
        k: Number of top results to consider (default: 10)
        
    Returns:
        1.0 if any top-k result contains deprecation language, 0.0 otherwise
    """
    if not results or k <= 0:
        return 0.0
    
    # Strict regex pattern for deprecation language (case-insensitive)
    # Matches deprecation terms in proper contexts only
    deprecation_pattern = re.compile(
        r'(?:\(|:|\[|^|\s)(?:is |was |has been |will be |now |been )?deprecated(?:\)|:|\]|\.|!|,|;|\s|$)|' +
        r'\b(?:was |has been |will be |been )?removed(?:\.|!|,|;|\s|$)|' +
        r'\b(?:was |has been |will be |been )?replaced(?:\.|!|,|;|\s|$)|' +
        r'\bmigration guide\b|\bmigration doc\b|' +
        r'\buse .* instead\b',
        re.IGNORECASE
    )
    
    # Check top-k results
    top_k_results = results[:k]
    
    for result in top_k_results:
        # Check title and snippet for deprecation language
        text_to_check = f"{result.title} {result.snippet}".lower()
        if deprecation_pattern.search(text_to_check):
            return 1.0
    
    return 0.0


def replacement_coverage(
    results: List[Result], 
    expected_replacements: Optional[List[str]] = None,
    k: int = 5
) -> float:
    """
    ReplacementCoverage: Check if any result contains known replacement tokens.
    
    Args:
        results: List of search results
        expected_replacements: List of expected replacement terms/phrases
        k: Number of top results to consider (default: 10)
        
    Returns:
        1.0 if any top-k result contains a replacement token, 0.0 otherwise
    """
    if not results or k <= 0:
        return 0.0
    
    # If no expected replacements provided, use balanced heuristic phrases
    if expected_replacements is None:
        expected_replacements = [
            "use .* instead",  # regex pattern for "use X instead"
            "use instead",  # exact phrase for "use instead Y"
            "instead of",
            "alternative to",
            "replacement for", 
            "migrate to",
            "switch to",
            "recommended",
            "preferred"
        ]
    
    # Check top-k results
    top_k_results = results[:k]
    
    for result in top_k_results:
        # Check title and snippet for replacement language
        text_to_check = f"{result.title} {result.snippet}".lower()
        
        for replacement in expected_replacements:
            # Handle regex patterns (those containing .*)
            if '.*' in replacement:
                pattern = re.compile(replacement, re.IGNORECASE)
                if pattern.search(text_to_check):
                    return 1.0
            else:
                # Simple substring match for exact phrases
                if replacement.lower() in text_to_check:
                    return 1.0
    
    return 0.0


def authority_at_k(results: List[Result], k: int = 5) -> int:
    """
    Authority@k: Maximum authority tier among top-k results.
    
    Args:
        results: List of search results
        k: Number of top results to consider (default: 10)
        
    Returns:
        Maximum authority tier (1-3) among top-k results, or 0.0 if no results
    """
    if not results or k <= 0:
        return 0.0
    
    # Check top-k results
    top_k_results = results[:k]
    
    max_authority = 0
    for result in top_k_results:
        if result.authority_tier is not None:
            max_authority = max(max_authority, result.authority_tier)
    
    return max_authority


def time_to_solution(
    results: List[Result],
    expected_replacements: Optional[List[str]] = None,
    k: int = 5,
    min_authority: int = 2
) -> Union[int, float]:
    """
    Time-to-Solution (TTS): Rank of first result that satisfies:
    1. Contains deprecation language (DeprecationNotice@k)
    2. Contains replacement information (ReplacementCoverage)  
    3. Has authority tier >= min_authority (using authority_tier field)
    
    Args:
        results: List of search results
        expected_replacements: List of expected replacement terms/phrases
        k: Number of top results to consider (default: 10)
        min_authority: Minimum authority tier required (default: 2)
        
    Returns:
        Rank (1-indexed) of first satisfying result, or float('inf') if none found
    """
    if not results or k <= 0:
        return float('inf')
    
    # If no expected replacements provided, use balanced heuristic phrases
    if expected_replacements is None:
        expected_replacements = [
            "use .* instead",  # regex pattern for "use X instead"
            "use instead",  # exact phrase for "use instead Y"
            "instead of",
            "alternative to",
            "replacement for", 
            "migrate to",
            "switch to",
            "recommended",
            "preferred"
        ]
    
    # Strict regex pattern for deprecation language (same as deprecation_notice_at_k)
    deprecation_pattern = re.compile(
        r'(?:\(|:|\[|^|\s)(?:is |was |has been |will be |now |been )?deprecated(?:\)|:|\]|\.|!|,|;|\s|$)|' +
        r'\b(?:was |has been |will be |been )?removed(?:\.|!|,|;|\s|$)|' +
        r'\b(?:was |has been |will be |been )?replaced(?:\.|!|,|;|\s|$)|' +
        r'\bmigration guide\b|\bmigration doc\b|' +
        r'\buse .* instead\b',
        re.IGNORECASE
    )
    
    # Check top-k results
    top_k_results = results[:k]
    
    for rank, result in enumerate(top_k_results, 1):
        # Check if result has sufficient authority (tier >= min_authority)
        if result.authority_tier is None or result.authority_tier < min_authority:
            continue
        
        # Check for deprecation language
        text_to_check = f"{result.title} {result.snippet}".lower()
        has_deprecation = bool(deprecation_pattern.search(text_to_check))
        
        if not has_deprecation:
            continue
        
        # Check for replacement information
        has_replacement = False
        for replacement in expected_replacements:
            # Handle regex patterns (those containing .*)
            if '.*' in replacement:
                pattern = re.compile(replacement, re.IGNORECASE)
                if pattern.search(text_to_check):
                    has_replacement = True
                    break
            else:
                # Simple substring match for exact phrases
                if replacement.lower() in text_to_check:
                    has_replacement = True
                    break
        
        if has_replacement:
            return rank
    
    return float('inf')


def evaluate_baseline(
    results: List[Result],
    expected_replacements: Optional[List[str]] = None,
    k: int = 5
) -> dict:
    """
    Evaluate a baseline using all four metrics.
    
    Args:
        results: List of search results
        expected_replacements: List of expected replacement terms/phrases
        k: Number of top results to consider (default: 10)
        
    Returns:
        Dictionary with all metric scores
    """
    return {
        "deprecation_notice_at_k": deprecation_notice_at_k(results, k),
        "replacement_coverage": replacement_coverage(results, expected_replacements, k),
        "authority_at_k": authority_at_k(results, k),
        "time_to_solution": time_to_solution(results, expected_replacements, k)
    }
