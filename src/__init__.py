"""
Exa Spoiled Milk Evaluation Package

A comprehensive evaluation framework for comparing search systems on deprecated technology queries.
"""

__version__ = "0.1.0"
__author__ = "Your Name"

from .exa_client import ExaClient
from .eval_runner import EvalRunner

__all__ = [
    "ExaClient",
    "EvalRunner",
]