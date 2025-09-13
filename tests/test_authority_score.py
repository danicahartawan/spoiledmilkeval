"""
Unit tests for the 3-tier authority scoring system.

Run with: python -m pytest tests/test_authority_score.py -v
"""

import pytest
import sys
from pathlib import Path

# Add src to path for imports
sys.path.append(str(Path(__file__).parent.parent))

from src.utils import authority_score


class TestAuthorityScore:
    """Test cases for the authority_score function."""

    def test_tier_3_official_docs(self):
        """Test Tier 3: Official documentation sites."""
        tier3_urls = [
            'https://nextjs.org/docs/getting-started',
            'https://pytorch.org/docs/stable/index.html',
            'https://www.tensorflow.org/guide/migrate',
            'https://docs.python.org/3/whatsnew/3.12.html',
            'https://docs.djangoproject.com/en/4.2/releases/',
            'https://pytorch.readthedocs.io/en/stable/',
            'https://vercel.com/docs/concepts/next.js',
            'https://developer.mozilla.org/en-US/docs/Web/API',
        ]
        
        for url in tier3_urls:
            assert authority_score(url) == 3, f"Expected Tier 3 for {url}"

    def test_tier_3_official_github(self):
        """Test Tier 3: Official GitHub organization repositories.""" 
        tier3_github_urls = [
            'https://github.com/vercel/next.js',
            'https://github.com/pytorch/pytorch',
            'https://github.com/tensorflow/tensorflow',
            'https://github.com/vercel/next.js/tree/canary/docs',
            'https://github.com/pytorch/pytorch/releases/tag/v2.0.0',
        ]
        
        for url in tier3_github_urls:
            assert authority_score(url) == 3, f"Expected Tier 3 for {url}"

    def test_tier_2_github_issues(self):
        """Test Tier 2: GitHub issues and discussions."""
        tier2_github_urls = [
            'https://github.com/vercel/next.js/issues/12345',
            'https://github.com/pytorch/pytorch/issues/98765', 
            'https://github.com/tensorflow/tensorflow/discussions/54321',
            'https://github.com/someuser/somerepo/issues/123',
        ]
        
        for url in tier2_github_urls:
            assert authority_score(url) == 2, f"Expected Tier 2 for {url}"

    def test_tier_2_reputable_sources(self):
        """Test Tier 2: Reputable company blogs and sources."""
        tier2_urls = [
            'https://stackoverflow.com/questions/12345/next-js-question',
            'https://blog.vercel.com/next-js-13-app-directory', 
            'https://engineering.fb.com/2023/ml/pytorch-2-0/',
            'https://medium.com/@vercel/next-js-migration-guide',
            'https://dev.to/microsoft/azure-updates',
        ]
        
        for url in tier2_urls:
            assert authority_score(url) == 2, f"Expected Tier 2 for {url}"

    def test_tier_1_general_content(self):
        """Test Tier 1: General blogs, SEO sites, forums."""
        tier1_urls = [
            'https://johnsmith.dev/nextjs-tips',
            'https://tutorialspoint.com/nextjs/guide',
            'https://medium.com/@randomdev/my-experience',
            'https://dev.to/coder123/tips-and-tricks',
            'https://reddit.com/r/nextjs/comments/abc123',
            'https://gist.github.com/user/abc123',
        ]
        
        for url in tier1_urls:
            assert authority_score(url) == 1, f"Expected Tier 1 for {url}"

    def test_edge_cases(self):
        """Test edge cases and error handling."""
        assert authority_score('') == 1
        assert authority_score(None) == 1
        assert authority_score('not-a-url') == 1
        assert authority_score('https://malformed-url') == 1
        
        # www. prefix handling
        assert authority_score('https://www.nextjs.org/docs') == 3
        assert authority_score('https://www.stackoverflow.com/questions/123') == 2
        
        # Case insensitivity
        assert authority_score('https://NEXTJS.ORG/docs') == 3
        assert authority_score('https://STACKOVERFLOW.COM/questions/456') == 2


if __name__ == '__main__':
    pytest.main([__file__, '-v'])