"""Regression tests for causal UI wiring in app/main.py."""

from __future__ import annotations

from pathlib import Path


def test_causal_view_mode_option_and_route_present() -> None:
    """Main app includes Causal Inference mode and dispatch route."""
    source = Path("app/main.py").read_text(encoding="utf-8")

    assert '"Causal Inference"' in source
    assert 'elif view_mode == "Causal Inference":' in source
    assert "render_causal_analysis()" in source


def test_causal_payload_key_validation_present() -> None:
    """Main app validates expected keys from causal pipeline output."""
    source = Path("app/main.py").read_text(encoding="utf-8")

    assert 'required_keys = {' in source
    assert '"covariate_balance"' in source
    assert '"matched_data"' in source
    assert '"ps_data"' in source
    assert 'missing_keys = sorted(required_keys - set(causal_results))' in source
