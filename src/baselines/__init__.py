"""
Baseline search systems for comparison with Exa.

Includes Google Programmable Search, StackOverflow API, and LLM-based baselines.
All baselines implement the same interface: run(query: str, k: int=10) -> list[Result]
"""

from .result import Result
from .google import GoogleBaseline
from .stackoverflow import StackOverflowBaseline  
from .claude import ClaudeBaseline

__all__ = [
    "Result",
    "GoogleBaseline",
    "StackOverflowBaseline", 
    "ClaudeBaseline",
]