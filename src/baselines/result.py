"""
Abstract Result dataclass for baseline search results.
"""

from dataclasses import dataclass
from typing import Optional


@dataclass
class Result:
    """Abstract result dataclass for search results."""
    title: str
    url: str
    snippet: str
    score: Optional[float] = None
    authority_tier: Optional[int] = None
    
    def to_dict(self) -> dict:
        """Convert to dictionary for serialization."""
        return {
            'title': self.title,
            'url': self.url,
            'snippet': self.snippet,
            'score': self.score,
            'authority_tier': self.authority_tier
        }
    
    @classmethod
    def from_dict(cls, data: dict) -> 'Result':
        """Create Result from dictionary."""
        return cls(
            title=data.get('title', ''),
            url=data.get('url', ''),
            snippet=data.get('snippet', ''),
            score=data.get('score'),
            authority_tier=data.get('authority_tier')
        )

