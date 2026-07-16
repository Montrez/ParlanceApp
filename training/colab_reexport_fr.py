#!/usr/bin/env python3
"""Deprecated shim — use `colab_reexport.py --lang fr` instead."""
import runpy
import sys

sys.argv = ["colab_reexport.py", "--lang", "fr"]
runpy.run_path("colab_reexport.py", run_name="__main__")
