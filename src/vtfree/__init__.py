"""
vtfree – Thin, polite wrapper around VirusTotal PublicAPIv3.
"""
from importlib.metadata import version
from .client import VTClient
from .exceptions import VTClientError

__all__ = ["VTClient", "VTClientError"]
__version__ = version(__package__ or "vtfree")
