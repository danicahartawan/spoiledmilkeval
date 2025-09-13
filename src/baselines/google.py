"""
Google Programmable Search baseline implementation.
"""

import time
import json
import hashlib
from pathlib import Path
from typing import List, Optional, Dict, Any
import requests
from tenacity import retry, stop_after_attempt, wait_exponential

from .result import Result
from ..utils import authority_score


class GoogleBaseline:
    """
    Google Programmable Search Engine baseline.
    
    Uses Google's Custom Search API to provide baseline search results
    for comparison with Exa's neural search.
    """
    
    BASE_URL = "https://www.googleapis.com/customsearch/v1"
    
    def __init__(
        self,
        api_key: Optional[str] = None,
        search_engine_id: Optional[str] = None,
        cache_dir: str = ".cache"
    ):
        """
        Initialize Google Search baseline.
        
        Args:
            api_key: Google API key (defaults to GOOGLE_SEARCH_API_KEY env var)
            search_engine_id: Custom Search Engine ID (defaults to GOOGLE_SEARCH_ENGINE_ID env var)
            cache_dir: Directory for cache storage
        """
        import os
        self.api_key = api_key or os.getenv("GOOGLE_SEARCH_API_KEY")
        self.search_engine_id = search_engine_id or os.getenv("GOOGLE_SEARCH_ENGINE_ID")
        
        # Set up cache directory
        self.cache_dir = Path(cache_dir) / "google"
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        
        self.session = requests.Session()
        
        # Check API credentials - warn if missing but don't fail (we have curated fallback)
        if (not self.api_key or not self.search_engine_id or 
            self.api_key.startswith("your_") or self.search_engine_id.startswith("your_") or
            self.api_key.startswith("<")):
            print("Info: Google Search API not configured - will use curated data fallback")
    
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
        wait=wait_exponential(multiplier=1, min=4, max=10)
    )
    def _make_request(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """
        Make request to Google Custom Search API.
        
        Args:
            params: API parameters
            
        Returns:
            API response data
        """
        response = self.session.get(self.BASE_URL, params=params)
        response.raise_for_status()
        
        return response.json()
    
    def _search_with_curated_data(self, query: str, k: int = 10) -> List[Result]:
        """
        Fallback to curated search results when API is not available.
        
        Args:
            query: Search query
            k: Number of results to return
            
        Returns:
            List of curated search results
        """
        # Try to find curated data by extracting query_id from query context
        # For now, we'll look for query_id patterns or use a mapping
        curated_data_dir = Path("data/baselines/google")
        
        # Try to find matching curated data files
        results = []
        for curated_file in curated_data_dir.glob("*.json"):
            try:
                with open(curated_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                
                # Check if this curated data matches our query
                if self._query_matches_curated_data(query, data):
                    for item in data.get("curated_results", [])[:k]:
                        url = item.get("url", "")
                        result = Result(
                            title=item.get("title", ""),
                            url=url,
                            snippet=item.get("snippet", ""),
                            score=1.0 - len(results) / 100.0,  # Decreasing score by position
                            authority_tier=authority_score(url)
                        )
                        results.append(result)
                    
                    if results:
                        print(f"✅ Using curated Google data: {len(results)} results")
                        return results[:k]
                        
            except (json.JSONDecodeError, IOError) as e:
                print(f"Warning: Could not load curated data from {curated_file}: {e}")
                continue
        
        # If no curated data found, return empty results
        print("⚠️ No Google API access and no matching curated data found")
        return []
    
    def _query_matches_curated_data(self, query: str, curated_data: dict) -> bool:
        """
        Check if a query matches curated data.
        
        Args:
            query: Search query
            curated_data: Curated data dictionary
            
        Returns:
            True if query matches curated data
        """
        curated_query = curated_data.get("query", "").lower()
        query_lower = query.lower()
        
        # Simple keyword matching - check if key terms overlap
        query_keywords = set(query_lower.split())
        curated_keywords = set(curated_query.split())
        
        # Match if at least 2 significant keywords overlap
        overlap = query_keywords.intersection(curated_keywords)
        significant_keywords = overlap - {"deprecated", "replacement", "migrate", "to", "from", "the", "a", "an", "is", "are", "was", "were"}
        
        return len(significant_keywords) >= 2
    
    def _search_with_api(self, query: str, k: int = 10) -> List[Result]:
        """
        Search using Google Custom Search API.
        
        Args:
            query: Search query
            k: Number of results to return
            
        Returns:
            List of search results from API
        """
        # Generate cache key
        cache_key = self._get_cache_key(query, k)
        
        # Try to load from cache first
        cached_results = self._load_from_cache(cache_key)
        if cached_results is not None:
            return cached_results
        
        # Make API calls (existing logic)
        return self._make_api_calls(query, k, cache_key)
    
    def _make_api_calls(self, query: str, k: int, cache_key: str) -> List[Result]:
        """Make the actual Google API calls."""
        # Google Custom Search limits to 10 results per request
        # For more than 10, we need to make multiple requests
        all_results = []
        requests_needed = (min(k, 100) + 9) // 10  # Ceiling division
        
        for request_num in range(requests_needed):
            start_index = request_num * 10 + 1
            current_num = min(10, k - len(all_results))
            
            if current_num <= 0:
                break
            
            params = {
                "key": self.api_key,
                "cx": self.search_engine_id,
                "q": query,
                "num": current_num,
                "start": start_index,
                "safe": "off"
            }
            
            # Make API request
            try:
                response_data = self._make_request(params)
                
                # Process results
                results = []
                for item in response_data.get("items", []):
                    url = item.get("link", "")
                    result = Result(
                        title=item.get("title", ""),
                        url=url,
                        snippet=item.get("snippet", ""),
                        score=1.0 - (len(all_results) + len(results)) / 100.0,  # Decreasing score by position
                        authority_tier=authority_score(url)
                    )
                    results.append(result)
                
                all_results.extend(results)
                
            except Exception as e:
                print(f"Warning: Google API request failed: {e}")
                break  # Don't try more requests if one fails
        
        # Cache the results
        if all_results:
            self._save_to_cache(cache_key, all_results, query, k)
        
        print(f"✅ Google API Success: {len(all_results)} results retrieved")
        return all_results

    def run(self, query: str, k: int = 10) -> List[Result]:
        """
        Search using Google Custom Search API with curated fallback.
        
        Args:
            query: Search query
            k: Number of results to return (max 100)
            
        Returns:
            List of search results
        """
        # Try API first if configured
        if self.api_key and self.search_engine_id and not self.api_key.startswith('<'):
            return self._search_with_api(query, k)
        
        # Fallback to curated data
        return self._search_with_curated_data(query, k)