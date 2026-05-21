"""
Renderers for the Caleidoscope project.

This module provides different renderers for converting geometric patterns
into various output formats.
"""
from .base import Renderer
from .tikz import TikzRenderer

__all__ = ["Renderer", "TikzRenderer"]
