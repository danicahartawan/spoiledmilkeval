"""
Claude (LLM) baseline implementation.

Uses LLM to generate recommendations and synthetic search results for deprecated technologies.
"""

import time
import json
import hashlib
import re
from pathlib import Path
from typing import List, Optional, Dict, Any
import requests
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type

from .result import Result
from ..utils import authority_score


class ClaudeBaseline:
    """
    LLM-based baseline using Claude API.
    
    Generates search results by asking Claude to provide recommendations
    and alternatives for deprecated technologies, then formats them as
    search results for comparison.
    """
    
    BASE_URL = "https://api.anthropic.com/v1"
    
    def __init__(
        self,
        api_key: Optional[str] = None,
        model: str = "claude-3-haiku-20240307",
        cache_dir: str = ".cache"
    ):
        """
        Initialize Claude baseline.
        
        Args:
            api_key: Anthropic API key (defaults to ANTHROPIC_API_KEY env var)
            model: Claude model to use
            cache_dir: Directory for cache storage
        """
        import os
        from dotenv import load_dotenv
        load_dotenv()
        
        # Try both environment variable names
        self.api_key = api_key or os.getenv("CLAUDE_API_KEY") or os.getenv("ANTHROPIC_API_KEY")
        self.model = model
        self.session = requests.Session()
        
        # Set up cache directory
        self.cache_dir = Path(cache_dir) / "claude"
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        
        # Validate required credentials
        if not self.api_key or self.api_key.startswith("your_") or self.api_key.startswith("<"):
            raise ValueError(
                "Claude API requires CLAUDE_API_KEY or ANTHROPIC_API_KEY. "
                "Please set this environment variable with a real API key or pass it as a parameter."
            )
        
        self.session.headers.update({
            "x-api-key": self.api_key,
            "Content-Type": "application/json",
            "anthropic-version": "2023-06-01"
        })
    
    def _get_cache_key(self, query: str, k: int) -> str:
        """Generate cache key from query and result count."""
        cache_input = f"{query}|k={k}"
        return hashlib.md5(cache_input.encode()).hexdigest()
    
    def _get_cache_path(self, cache_key: str) -> Path:
        """Get file path for cache key."""
        return self.cache_dir / f"{cache_key}.json"
    
    def _load_from_cache(self, cache_key: str) -> Optional[List[Result]]:
        """Load results from cache if available."""
        cache_path = self._get_cache_path(cache_key)
        
        if not cache_path.exists():
            return None
        
        try:
            with open(cache_path, 'r', encoding='utf-8') as f:
                cached_data = json.load(f)
            
            # Convert cached data back to Result objects
            results = [Result.from_dict(item) for item in cached_data['results']]
            
            print(f"📁 Cache hit: {cache_key[:8]}... ({len(results)} results)")
            return results
            
        except (json.JSONDecodeError, KeyError, FileNotFoundError) as e:
            print(f"⚠️  Cache read error for {cache_key[:8]}...: {e}")
            # Remove corrupted cache file
            cache_path.unlink(missing_ok=True)
            return None
    
    def _save_to_cache(self, cache_key: str, results: List[Result], query: str, k: int) -> None:
        """Save results to cache."""
        cache_path = self._get_cache_path(cache_key)
        
        cache_data = {
            'query': query,
            'k': k,
            'timestamp': time.time(),
            'results_count': len(results),
            'results': [result.to_dict() for result in results]
        }
        
        try:
            with open(cache_path, 'w', encoding='utf-8') as f:
                json.dump(cache_data, f, indent=2, ensure_ascii=False)
            
            print(f"💾 Cached: {cache_key[:8]}... ({len(results)} results)")
            
        except (OSError, TypeError) as e:
            print(f"⚠️  Cache write error for {cache_key[:8]}...: {e}")
    
    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=4, max=10),
        retry=retry_if_exception_type((requests.exceptions.ConnectionError, requests.exceptions.Timeout))
    )
    def _make_request(self, messages: List[Dict[str, str]], max_tokens: int = 2000) -> str:
        """
        Make request to Claude API.
        
        Args:
            messages: List of message objects
            max_tokens: Maximum tokens in response
            
        Returns:
            Claude's response text
        """
        payload = {
            "model": self.model,
            "max_tokens": max_tokens,
            "messages": messages
        }
        
        response = self.session.post(f"{self.BASE_URL}/messages", json=payload)
        
        # Handle auth errors - don't retry these
        if response.status_code in [401, 403]:
            raise ValueError(f"Authentication failed (HTTP {response.status_code}): Check your API key and permissions")
        
        # Handle rate limiting - let tenacity retry these
        if response.status_code == 429:
            raise requests.exceptions.ConnectionError(f"Rate limited (HTTP 429)")
        
        # Handle server errors - let tenacity retry these  
        if response.status_code >= 500:
            raise requests.exceptions.ConnectionError(f"Server error (HTTP {response.status_code})")
        
        response.raise_for_status()
        
        response_data = response.json()
        return response_data["content"][0]["text"]
    
    def ask_claude(self, query: str) -> str:
        """
        Ask Claude about deprecation alternatives.
        
        Args:
            query: Deprecation query
            
        Returns:
            Claude's response text
        """
        # Strict system prompt that REQUIRES authoritative URLs
        system_prompt = """You are a software deprecation expert. You MUST include 1-3 authoritative URLs in your response.

CRITICAL REQUIREMENTS:
1. ALWAYS include at least 1 authoritative URL (official docs, vendor GitHub repos, etc.)
2. URLs MUST be real and authoritative (no generic sites, forums, or blogs)
3. Prefer: official documentation, GitHub repos/issues, vendor websites
4. If you cannot find authoritative URLs, respond EXACTLY: "no reliable source"
5. Keep response concise but include practical migration advice with each URL

Focus on official sources like:
- nextjs.org/docs, reactjs.org, vuejs.org, etc.
- github.com/[vendor]/[project]/docs or /issues
- developer.mozilla.org, docs.microsoft.com, etc."""
        
        user_prompt = f"""What replaces {query}? Cite official docs if possible."""
        
        messages = [
            {"role": "user", "content": f"{system_prompt}\n\n{user_prompt}"}
        ]
        
        try:
            response_text = self._make_request(messages)
            return response_text
        except Exception as e:
            print(f"Warning: Claude request failed: {e}")
            return ""
    
    def extract_citations(self, text: str) -> List[str]:
        """
        Extract URLs from Claude's response text.
        
        Args:
            text: Claude's response text
            
        Returns:
            List of extracted URLs
        """
        # URL regex pattern
        url_pattern = r'https?://[^\s<>"{}|\\^`\[\]]+'
        urls = re.findall(url_pattern, text)
        
        # Clean up URLs (remove trailing punctuation)
        cleaned_urls = []
        for url in urls:
            # Remove trailing punctuation
            url = re.sub(r'[.,;:!?]+$', '', url)
            # Remove trailing parentheses
            url = re.sub(r'\)+$', '', url)
            cleaned_urls.append(url)
        
        return list(set(cleaned_urls))  # Remove duplicates
    
    def run(self, query: str, k: int = 10) -> List[Result]:
        """
        Generate deprecation recommendations using Claude.
        
        Args:
            query: Deprecation query
            k: Number of recommendations to generate
            
        Returns:
            List of search results
        """
        # Generate cache key
        cache_key = self._get_cache_key(query, k)
        
        # Try to load from cache first
        cached_results = self._load_from_cache(cache_key)
        if cached_results is not None:
            return cached_results
        
        # Ask Claude for recommendations
        claude_response = self.ask_claude(query)
        
        if not claude_response:
            print("Warning: No response from Claude")
            return []
        
        # Check if Claude said "no reliable source" - drop this response
        if "no reliable source" in claude_response.lower():
            print("Info: Claude found no reliable sources for this query")
            return []
        
        # Extract citations from the response
        cited_urls = self.extract_citations(claude_response)
        
        if not cited_urls:
            print("Warning: No authoritative citations found in Claude response - dropping answer")
            return []
        
        # Filter URLs to only include authoritative ones (tier 2-3)
        authoritative_urls = []
        for url in cited_urls:
            auth_tier = authority_score(url)
            if auth_tier >= 2:  # Only tier 2-3 are considered authoritative
                authoritative_urls.append(url)
        
        if not authoritative_urls:
            print("Warning: No authoritative URLs found in Claude response - dropping answer")
            return []
        
        # Create synthetic Result objects using authoritative links only
        results = []
        for i, url in enumerate(authoritative_urls[:k]):
            # Create a synthetic title and snippet based on the URL and response
            title = f"Claude Recommendation {i+1}"
            snippet = claude_response[:200] + "..." if len(claude_response) > 200 else claude_response
            
            result = Result(
                title=title,
                url=url,
                snippet=snippet,
                score=1.0 - i * 0.1,  # Decreasing score
                authority_tier=authority_score(url)
            )
            results.append(result)
        
        # Cache the results
        self._save_to_cache(cache_key, results, query, k)
        
        print(f"✅ Claude API Success: {len(results)} results retrieved")
        return results