"""
Utility functions for deprecation search evaluation.

Includes authority scoring for determining the reliability of search results.
"""

import re
from urllib.parse import urlparse
from typing import Optional


def authority_score(url: str) -> int:
    """
    Score the authority of a URL based on domain heuristics.
    
    Uses a 3-tier scoring system:
    - Tier 3 (highest): Official documentation, GitHub repos/docs, authoritative sources
    - Tier 2 (medium): Reputable blogs, dev platforms
    - Tier 1 (lowest): Forums, SEO sites, other sources
    
    Args:
        url: The URL to score
        
    Returns:
        Authority tier (1-3), where 3 is highest authority
    """
    if not url or not isinstance(url, str):
        return 1
    
    try:
        parsed = urlparse(url.lower().strip())
        domain = parsed.netloc
        path = parsed.path
        
        # Remove www. prefix for consistency
        if domain.startswith('www.'):
            domain = domain[4:]
        
        # Tier 3: Highest authority - Official docs and authoritative sources
        tier_3_patterns = [
            # Framework and library official sites
            r'nextjs\.org',
            r'pytorch\.org', 
            r'tensorflow\.org',
            r'reactjs\.org',
            r'vuejs\.org',
            r'angular\.io',
            r'svelte\.dev',
            r'nuxtjs\.org',
            r'gatsbyjs\.org',
            r'nodejs\.org',
            r'python\.org',
            r'golang\.org',
            r'rust-lang\.org',
            
            # Documentation platforms
            r'.*\.readthedocs\.io',
            r'docs\..*',
            r'documentation\..*',
            
            # Cloud providers and major tech companies
            r'.*\.vercel\.com',
            r'.*\.netlify\.com', 
            r'docs\.aws\.amazon\.com',
            r'cloud\.google\.com',
            r'docs\.microsoft\.com',
            r'developer\.mozilla\.org',
            r'developer\.apple\.com',
            
            # Package managers and registries
            r'npmjs\.com',
            r'pypi\.org',
            r'crates\.io',
            r'packagist\.org',
            
            # Version control platforms (docs/issues/releases only)
            r'github\.com/.+/(docs|issues|pull|discussions|releases|wiki)',
            r'gitlab\.com/.+/(docs|issues|merge_requests|wiki)',
        ]
        
        for pattern in tier_3_patterns:
            if re.search(pattern, domain) or re.search(pattern, f"{domain}{path}"):
                return 3
        
        # Tier 2: Medium authority - Reputable blogs and dev platforms  
        tier_2_patterns = [
            # Developer platforms
            r'dev\.to',
            r'medium\.com',
            r'hashnode\.com',
            r'substack\.com',
            
            # Company engineering blogs (but not generic blog platforms)
            r'engineering\..*',
            r'tech\..*', 
            r'blog\.(netflix|google|microsoft|facebook|meta|amazon|stripe|shopify|github|gitlab|vercel|netlify)\.com',
            r'developers\..*',
            
            # Educational platforms
            r'freecodecamp\.org',
            r'codecademy\.com',
            r'udemy\.com',
            r'coursera\.org',
            r'edx\.org',
            
            # News and tutorial sites
            r'css-tricks\.com',
            r'smashingmagazine\.com',
            r'a11yproject\.com',
            r'webdev\.com',
            r'web\.dev',
            
            # Popular tech blogs
            r'overreacted\.io',
            r'kentcdodds\.com', 
            r'joshwcomeau\.com',
            r'dan\.luu',
            
            # General GitHub (not docs/issues)
            r'github\.com/[^/]+/[^/]+$',
            r'github\.com/[^/]+/[^/]+/blob',
            r'github\.com/[^/]+/[^/]+/tree',
        ]
        
        for pattern in tier_2_patterns:
            if re.search(pattern, domain) or re.search(pattern, f"{domain}{path}"):
                return 2
        
        # Tier 1: Lowest authority - Everything else
        # Forums, Q&A sites, random blogs, SEO content farms
        tier_1_indicators = [
            r'stackoverflow\.com',
            r'stackexchange\.com',
            r'reddit\.com',
            r'quora\.com',
            r'.*forum.*',
            r'.*\.wordpress\.com',
            r'.*\.blogspot\.com',
            r'.*\.wix\.com',
            r'.*\.squarespace\.com',
        ]
        
        # Check for explicit tier 1 indicators
        for pattern in tier_1_indicators:
            if re.search(pattern, domain):
                return 1
        
        # Default to tier 1 for unknown domains
        return 1
        
    except Exception:
        # If URL parsing fails, default to lowest tier
        return 1


def get_domain_info(url: str) -> Optional[dict]:
    """
    Extract domain information from a URL for debugging authority scores.
    
    Args:
        url: The URL to analyze
        
    Returns:
        Dictionary with domain, path, and authority score info
    """
    if not url or not isinstance(url, str):
        return None
    
    try:
        parsed = urlparse(url.lower().strip())
        domain = parsed.netloc
        
        # If no domain is found, it's not a valid URL
        if not domain:
            return None
            
        if domain.startswith('www.'):
            domain = domain[4:]
            
        return {
            'url': url,
            'domain': domain,
            'path': parsed.path,
            'authority_score': authority_score(url)
        }
    except Exception:
        return None