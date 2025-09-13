"""
Tests for utility functions including authority scoring.
"""

import pytest
from src.utils import authority_score, get_domain_info


class TestAuthorityScore:
    """Test cases for authority_score function."""
    
    def test_tier_3_official_docs(self):
        """Test Tier 3: Official documentation sites."""
        tier_3_urls = [
            "https://nextjs.org/docs/getting-started",
            "https://pytorch.org/tutorials/", 
            "https://tensorflow.org/guide",
            "https://reactjs.org/docs",
            "https://vuejs.org/guide/",
            "https://angular.io/guide",
            "https://svelte.dev/docs",
            "https://docs.python.org/3/",
            "https://golang.org/doc/",
            "https://rust-lang.org/learn"
        ]
        
        for url in tier_3_urls:
            assert authority_score(url) == 3, f"URL should be tier 3: {url}"
    
    def test_tier_3_documentation_platforms(self):
        """Test Tier 3: Documentation platforms."""
        tier_3_urls = [
            "https://readthedocs.io/projects/docs/",
            "https://my-project.readthedocs.io/en/latest/",
            "https://docs.aws.amazon.com/",
            "https://docs.microsoft.com/azure/",
            "https://developer.mozilla.org/en-US/docs/",
            "https://cloud.google.com/docs/"
        ]
        
        for url in tier_3_urls:
            assert authority_score(url) == 3, f"URL should be tier 3: {url}"
    
    def test_tier_3_vercel_netlify(self):
        """Test Tier 3: Vercel and Netlify domains."""
        tier_3_urls = [
            "https://my-app.vercel.com/",
            "https://awesome-project.netlify.com/docs",
            "https://subdomain.vercel.com/guide"
        ]
        
        for url in tier_3_urls:
            assert authority_score(url) == 3, f"URL should be tier 3: {url}"
    
    def test_tier_3_github_docs_issues(self):
        """Test Tier 3: GitHub docs, issues, releases."""
        tier_3_urls = [
            "https://github.com/facebook/react/issues/12345",
            "https://github.com/vercel/next.js/discussions/54321", 
            "https://github.com/microsoft/typescript/releases/tag/v4.9.0",
            "https://github.com/nodejs/node/pull/98765",
            "https://github.com/python/cpython/wiki",
            "https://github.com/rust-lang/rust/docs"
        ]
        
        for url in tier_3_urls:
            assert authority_score(url) == 3, f"URL should be tier 3: {url}"
    
    def test_tier_2_dev_platforms(self):
        """Test Tier 2: Developer platforms and reputable blogs."""
        tier_2_urls = [
            "https://dev.to/some-author/post-title",
            "https://medium.com/@author/article",
            "https://hashnode.com/post/my-article",
            "https://author.substack.com/p/post",
            "https://css-tricks.com/snippets/",
            "https://web.dev/performance/",
            "https://smashingmagazine.com/2023/01/article/"
        ]
        
        for url in tier_2_urls:
            assert authority_score(url) == 2, f"URL should be tier 2: {url}"
    
    def test_tier_2_company_blogs(self):
        """Test Tier 2: Company engineering blogs."""
        tier_2_urls = [
            "https://engineering.facebook.com/2023/post/",
            "https://tech.company.com/blog/post",
            "https://blog.netflix.com/engineering/",
            "https://developers.google.com/web/",
        ]
        
        for url in tier_2_urls:
            assert authority_score(url) == 2, f"URL should be tier 2: {url}"
    
    def test_tier_2_github_code(self):
        """Test Tier 2: GitHub code repositories (not docs/issues)."""
        tier_2_urls = [
            "https://github.com/facebook/react",
            "https://github.com/microsoft/typescript/blob/main/src/file.ts",
            "https://github.com/vercel/next.js/tree/canary/packages"
        ]
        
        for url in tier_2_urls:
            assert authority_score(url) == 2, f"URL should be tier 2: {url}"
    
    def test_tier_1_forums_qa(self):
        """Test Tier 1: Forums and Q&A sites."""
        tier_1_urls = [
            "https://stackoverflow.com/questions/12345/how-to-do-x",
            "https://superuser.stackexchange.com/q/67890",
            "https://www.reddit.com/r/programming/comments/abc123/",
            "https://quora.com/What-is-the-best-way-to",
            "https://forum.example.com/topic/123"
        ]
        
        for url in tier_1_urls:
            assert authority_score(url) == 1, f"URL should be tier 1: {url}"
    
    def test_tier_1_blog_platforms(self):
        """Test Tier 1: Generic blog platforms."""
        tier_1_urls = [
            "https://myblog.wordpress.com/2023/01/post/",
            "https://author.blogspot.com/2023/01/title.html",
            "https://mysite.wix.com/blog/post",
            "https://company.squarespace.com/articles/"
        ]
        
        for url in tier_1_urls:
            assert authority_score(url) == 1, f"URL should be tier 1: {url}"
    
    def test_tier_1_unknown_domains(self):
        """Test Tier 1: Unknown or random domains."""
        tier_1_urls = [
            "https://random-seo-site.com/article",
            "https://unknown-domain.net/blog/post",
            "https://affiliate-site.info/reviews/",
            "https://content-farm.biz/how-to-guide"
        ]
        
        for url in tier_1_urls:
            assert authority_score(url) == 1, f"URL should be tier 1: {url}"
    
    def test_www_prefix_handling(self):
        """Test that www. prefix is handled correctly."""
        assert authority_score("https://www.nextjs.org/docs") == 3
        assert authority_score("https://nextjs.org/docs") == 3
        assert authority_score("https://www.dev.to/author/post") == 2
        assert authority_score("https://dev.to/author/post") == 2
    
    def test_case_insensitive(self):
        """Test that URL matching is case insensitive."""
        assert authority_score("https://NextJS.org/docs") == 3
        assert authority_score("https://GITHUB.com/facebook/react/issues/123") == 3
        assert authority_score("https://DEV.to/author/post") == 2
    
    def test_invalid_urls(self):
        """Test handling of invalid or malformed URLs."""
        invalid_urls = [
            "",
            None,
            "not-a-url",
            "ftp://invalid-protocol.com",
            "https://",
            123,  # Non-string input
            []     # Non-string input
        ]
        
        for url in invalid_urls:
            assert authority_score(url) == 1, f"Invalid URL should default to tier 1: {url}"
    
    def test_edge_cases(self):
        """Test edge cases and special scenarios."""
        # URLs with query parameters and fragments
        assert authority_score("https://nextjs.org/docs/api?version=13#section") == 3
        assert authority_score("https://dev.to/author/post?utm_source=twitter") == 2
        
        # Very long URLs
        long_url = "https://nextjs.org/docs/" + "a" * 1000
        assert authority_score(long_url) == 3
        
        # URLs with special characters
        assert authority_score("https://docs.python.org/3/library/urllib.parse.html") == 3


class TestGetDomainInfo:
    """Test cases for get_domain_info helper function."""
    
    def test_valid_url(self):
        """Test domain info extraction from valid URL."""
        info = get_domain_info("https://www.nextjs.org/docs/getting-started")
        assert info is not None
        assert info['domain'] == 'nextjs.org'
        assert info['path'] == '/docs/getting-started'
        assert info['authority_score'] == 3
    
    def test_invalid_url(self):
        """Test domain info extraction from invalid URL."""
        invalid_urls = [None, "", "not-a-url", 123]
        for url in invalid_urls:
            assert get_domain_info(url) is None
    
    def test_www_removal(self):
        """Test that www. prefix is removed from domain."""
        info = get_domain_info("https://www.example.com/path")
        assert info['domain'] == 'example.com'


if __name__ == "__main__":
    pytest.main([__file__])