"""
Decision Engine package for Jal-Saathi.
Handles water balance, pest/disease protection, and soil nourishment advisories.
"""

from .engine import DecisionEngine, decide
from .handler import handler

__all__ = ["DecisionEngine", "decide", "handler"]
