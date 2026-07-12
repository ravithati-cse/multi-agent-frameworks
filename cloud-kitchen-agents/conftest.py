"""Make the repo root importable and keep sim timing fast during tests."""
import os
import sys

sys.path.insert(0, os.path.dirname(__file__))
os.environ.setdefault("CKA_TIME_SCALE", "0.02")
