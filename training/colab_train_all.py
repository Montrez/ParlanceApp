#!/usr/bin/env python3
"""Deprecated shim — use `colab_train.py --lang both` instead."""
import runpy
import sys

sys.argv = ["colab_train.py", "--lang", "both"]
runpy.run_path("colab_train.py", run_name="__main__")
