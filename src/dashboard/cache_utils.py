"""Cache configuration and utilities for Streamlit dashboard."""

from __future__ import annotations

import streamlit as st

# Cache TTL (time-to-live) in seconds
# Loaders are cached for 1 hour (3600 seconds) by default,
# providing incremental refresh on dashboard reopens
DEFAULT_CACHE_TTL = 3600

# Short-lived cache for frequently accessed data (15 minutes)
SHORT_CACHE_TTL = 900

# Medium-lived cache for moderately fresh data (30 minutes)
MEDIUM_CACHE_TTL = 1800

# Long-lived cache for reference data (2 hours)
LONG_CACHE_TTL = 7200


def clear_dashboard_cache() -> None:
    """Clear all dashboard data caches.
    
    Useful when data has been updated or for manual refresh.
    Call this from Streamlit UI with a button:
    
        if st.button("Clear cache and refresh"):
            clear_dashboard_cache()
            st.rerun()
    """
    st.cache_data.clear()


def get_cache_status() -> dict[str, object]:
    """Get current cache statistics.
    
    Returns metadata about cached data loaders.
    Can be used for debugging or displaying cache info to users.
    """
    # Note: Streamlit cache doesn't directly expose stats,
    # but this function provides a placeholder for future enhancements
    return {
        "cache_type": "streamlit.cache_data",
        "default_ttl": DEFAULT_CACHE_TTL,
        "status": "All data loaders are cached with configurable TTL",
    }


def configure_cache_ttl(ttl_seconds: int) -> None:
    """Reconfigure cache TTL at runtime (for testing/development).
    
    Args:
        ttl_seconds: New TTL in seconds. Use 0 to disable caching.
    
    Note: This is a documentation helper. TTL is currently hardcoded
    in @st.cache_data decorator. To change TTL, modify the decorator
    parameters in phase10.py and drilldown.py.
    """
    # This function serves as documentation for now.
    # In a future enhancement, TTL could be loaded from environment variables
    # or configuration files and injected into decorators dynamically.
    pass
