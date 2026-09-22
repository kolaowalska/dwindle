from __future__ import annotations

import importlib.util


def test_visualize_enabled_when_visualizer_importable():
    """the flag used to be False in both branches of the try/except."""
    import src.demo as demo

    expected = importlib.util.find_spec("matplotlib") is not None
    assert demo.VISUALIZE is expected
