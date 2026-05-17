# Re-export the entry point so callers can `from webview import run`.
from .app import run

__all__ = ["run"]
