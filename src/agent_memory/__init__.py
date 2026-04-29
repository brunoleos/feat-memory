"""agent-memory: persistent memory methodology for LLM agents."""

from importlib.metadata import PackageNotFoundError, version

try:
    __version__ = version("agent-memory")
except PackageNotFoundError:
    __version__ = "unknown"
