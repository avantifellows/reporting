import os
import sys

# The app uses imports relative to app/ (it is run from inside that folder).
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "app"))
