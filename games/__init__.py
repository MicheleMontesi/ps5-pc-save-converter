"""
Games module package.
Automatically registers all supported game converters into GameRegistry.
"""

from core.registry import GameRegistry
from .hogwarts_legacy import HogwartsLegacyConverter

# Register Hogwarts Legacy
GameRegistry.register(HogwartsLegacyConverter())

__all__ = ['GameRegistry']
