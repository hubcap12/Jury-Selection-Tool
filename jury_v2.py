#!/usr/bin/env python3
"""Jury Selection Tool — webview UI entry point.

Run with:  python jury_v2.py
"""
import os

# Use Qt (PySide6) backend — avoids .NET dependency entirely.
os.environ.setdefault("PYWEBVIEW_GUI", "qt")

if __name__ == "__main__":
    from jury_ui import run
    run()
1