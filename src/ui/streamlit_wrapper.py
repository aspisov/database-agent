"""
Streamlit wrapper that handles imports properly.

This script ensures that imports work correctly by adding the project root to sys.path.
"""

import os
import sys

# Add the project root to sys.path
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "../.."))
sys.path.insert(0, project_root)

# Now import and run the streamlit app
from src.ui.streamlit_app import main

if __name__ == "__main__":
    main()
