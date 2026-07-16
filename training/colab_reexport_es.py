#!/usr/bin/env python3
"""Deprecated shim — use `colab_reexport.py --lang es` instead."""
import runpy
import sys

sys.argv = ["colab_reexport.py", "--lang", "es"]
runpy.run_path("colab_reexport.py", run_name="__main__")
