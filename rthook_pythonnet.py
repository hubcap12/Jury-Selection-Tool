"""PyInstaller runtime hook for pythonnet.

Default on Windows is netfx (.NET Framework 4.x, always present).
Only force coreclr if netfx initialization fails — e.g. on machines where the
.NET Framework host can't resolve Python.Runtime.Loader.Initialize.
"""
import os

# Leave PYTHONNET_RUNTIME unset so pythonnet defaults to netfx on Windows.
# If the user's environment already has it set, respect that.
