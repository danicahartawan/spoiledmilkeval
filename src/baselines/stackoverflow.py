"""
StackOverflow API baseline implementation.
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


class StackOverflowBaseline:
    """
    StackOverflow API baseline search system.
    
    Uses the StackOverflow API to search for questions and answers
    related to deprecated technologies and their alternatives.
    """
    
    BASE_URL = "https://api.stackexchange.com/2.3"
    
    def __init__(
        self,
        api_key: Optional[str] = None,
        cache_dir: str = ".cache",
        site: str = "stackoverflow"
    ):
        """
        Initialize StackOverflow baseline.
        
        Args:
            api_key: StackOverflow API key (optional, for higher rate limits)
            cache_dir: Directory for cache storage
            site: StackExchange site to search (default: "stackoverflow")
        """
        import os
        self.api_key = api_key or os.getenv("STACKOVERFLOW_API_KEY")
        self.site = site
        self.session = requests.Session()
        
        # Set up cache directory
        self.cache_dir = Path(cache_dir) / "stackoverflow"
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        
        # Set up compression and user agent
        self.session.headers.update({
            "Accept-Encoding": "gzip",
            "User-Agent": "ExaSpoiledMilkEval/1.0"
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
        wait=wait_exponential(multiplier=1, min=4, max=10)
    )
    def _make_request(self, endpoint: str, params: Dict[str, Any]) -> Dict[str, Any]:
        """
        Make request to StackOverflow API.
        
        Args:
            endpoint: API endpoint
            params: Request parameters
            
        Returns:
            API response data
        """
        url = f"{self.BASE_URL}/{endpoint}"
        
        # Add API key if available
        if self.api_key:
            params["key"] = self.api_key
        
        response = self.session.get(url, params=params)
        response.raise_for_status()
        
        return response.json()
    
    def run(self, query: str, k: int = 10) -> List[Result]:
        """
        Search StackOverflow questions and answers.
        
        Args:
            query: Search query
            k: Number of results to return (max 100)
            
        Returns:
            List of search results
        """
        # Generate cache key
        cache_key = self._get_cache_key(query, k)
        
        # Try to load from cache first
        cached_results = self._load_from_cache(cache_key)
        if cached_results is not None:
            return cached_results
        
        all_results = []
        
        # Search questions
        try:
            question_params = {
                "site": self.site,
                "intitle": query,  # Search in question titles
                "pagesize": min(k, 100),
                "sort": "relevance",
                "order": "desc",
                "filter": "withbody"  # Include question body text
            }
            
            response_data = self._make_request("search", question_params)
            
            # Process question results
            for item in response_data.get("items", []):
                # Create snippet from question body
                body = item.get("body_markdown", item.get("body", ""))
                snippet = (body[:200] + "...") if len(body) > 200 else body
                
                url = item.get("link", "")
                result = Result(
                    title=item.get("title", ""),
                    url=url,
                    snippet=snippet,
                    score=min(1.0, item.get("score", 0) / 100.0),  # Normalize score
                    authority_tier=authority_score(url)
                )
                all_results.append(result)
                
        except Exception as e:
            print(f"Warning: Question search failed: {e}")
        
        # If we need more results, search answers
        if len(all_results) < k:
            try:
                answer_params = {
                    "site": self.site,
                    "q": query,
                    "pagesize": min(k - len(all_results), 100),
                    "sort": "votes",
                    "order": "desc",
                    "filter": "withbody"
                }
                
                response_data = self._make_request("answers", answer_params)
                
                # Process answer results
                for item in response_data.get("items", []):
                    # Create snippet from answer body
                    body = item.get("body_markdown", item.get("body", ""))
                    snippet = (body[:200] + "...") if len(body) > 200 else body
                    
                    url = f"https://stackoverflow.com/a/{item.get('answer_id')}"
                    result = Result(
                        title=f"Answer to: {item.get('title', 'Question')}",
                        url=url,
                        snippet=snippet,
                        score=min(1.0, item.get("score", 0) / 50.0),  # Normalize answer score
                        authority_tier=authority_score(url)
                    )
                    all_results.append(result)
                    
            except Exception as e:
                print(f"Warning: Answer search failed: {e}")
        
        # Limit to requested number of results
        all_results = all_results[:k]
        
        # Cache the results
        self._save_to_cache(cache_key, all_results, query, k)
        
        print(f"✅ StackOverflow API Success: {len(all_results)} results retrieved")
        return all_results