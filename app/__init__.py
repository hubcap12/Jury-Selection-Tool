__all__ = ['JuryApp']

def __getattr__(name: str):
    if name == 'JuryApp':
        from .main import JuryApp
        return JuryApp
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
