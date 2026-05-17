"""Additional Info module — catch-all for RFC drivers that don't fit the 5 primary modules.

Install with: pip install 'rfc-plugins[additional_info]'
"""
from rfc_plugins._deps import require


def validate_dependencies() -> None:
    """Verify this module's optional dependencies are installed.

    Called by each driver's ``__init__`` so missing deps surface as an
    actionable ImportError at use time rather than at module import.
    """
    require([], extra="additional_info")
