"""Exa Search API client with caching and retry functionality."""
import hashlib
import json
import os
from pathlib import Path
from typing import Any, Dict, List, Optional
import requests
from tenacity import retry, stop_after_attempt, wait_exponential


class ExaClient:
    """Client for Exa Search API with JSON caching and retry functionality."""
    
    def __init__(self, api_key: str, cache_dir: str = ".cache/exa") -> None:
        """Initialize ExaClient.
        
        Args:
            api_key: Exa API key
            cache_dir: Directory for caching search results
        """
        self.api_key = api_key
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self.base_url = "https://api.exa.ai/search"
    
    def _get_cache_key(self, query: str, k: int) -> str:
        """Generate cache key for query and k combination."""
        content = f"{query}:{k}"
        return hashlib.md5(content.encode()).hexdigest()
    
    def _get_cache_path(self, cache_key: str) -> Path:
        """Get cache file path for given cache key."""
        return self.cache_dir / f"{cache_key}.json"
    
    def _load_from_cache(self, cache_key: str) -> Optional[List[Dict[str, Any]]]:
        """Load search results from cache."""
        cache_path = self._get_cache_path(cache_key)
        if cache_path.exists():
            try:
                with open(cache_path, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except (json.JSONDecodeError, IOError):
                # Remove corrupted cache file
                cache_path.unlink(missing_ok=True)
        return None
    
    def _save_to_cache(self, cache_key: str, results: List[Dict[str, Any]]) -> None:
        """Save search results to cache."""
        cache_path = self._get_cache_path(cache_key)
        try:
            with open(cache_path, 'w', encoding='utf-8') as f:
                json.dump(results, f, indent=2, ensure_ascii=False)
        except IOError as e:
            print(f"Warning: Failed to save to cache: {e}")
    
    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=4, max=10)
    )
    def _call_exa_api(self, query: str, k: int) -> List[Dict[str, Any]]:
        """Make API call to Exa Search with retries."""
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        
        payload = {
            "query": query,
            "numResults": k,
            "contents": {
                "text": True
            }
        }
        
        response = requests.post(
            self.base_url,
            headers=headers,
            json=payload,
            timeout=30
        )
        response.raise_for_status()
        
        data = response.json()
        return self._normalize_results(data.get("results", []))
    
    def _normalize_results(self, raw_results: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Normalize raw API results to consistent format."""
        normalized = []
        
        for result in raw_results:
            normalized_result = {
                "title": result.get("title", "").strip(),
                "url": result.get("url", "").strip(),
                "snippet": result.get("text", "").strip()[:500]  # Limit snippet length
            }
            
            # Only add results with valid URL and title
            if normalized_result["url"] and normalized_result["title"]:
                normalized.append(normalized_result)
        
        return normalized
    
    def search(self, query: str, k: int = 10) -> List[Dict[str, Any]]:
        """Search using Exa API with caching.
        
        Args:
            query: Search query string
            k: Number of results to return
            
        Returns:
            List of normalized search results with title, url, snippet fields
        """
        if not query or not query.strip():
            return []
            
        cache_key = self._get_cache_key(query, k)
        
        # Try cache first
        cached_results = self._load_from_cache(cache_key)
        if cached_results is not None:
            return cached_results
        
        # Cache miss - call API
        try:
            results = self._call_exa_api(query, k)
            self._save_to_cache(cache_key, results)
            return results
        except Exception as e:
            print(f"Error calling Exa API for query '{query}': {e}")
            return []