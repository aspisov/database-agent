#!/usr/bin/env python
"""
Launcher script for the Streamlit web interface.

This script launches the Streamlit web interface for the Conversational Database Agent.
"""

import subprocess
import os
import sys


def main():
    """Launch the Streamlit web interface."""
    print("🚀 Launching Streamlit Web Interface for Database Agent")

    # Get the directory of this script
    script_dir = os.path.dirname(os.path.abspath(__file__))

    # Path to the Streamlit wrapper script
    wrapper_path = os.path.join(script_dir, "ui", "streamlit_wrapper.py")

    # Check if the file exists
    if not os.path.exists(wrapper_path):
        print(f"❌ Error: Could not find Streamlit wrapper at {wrapper_path}")
        sys.exit(1)

    try:
        # Set PYTHONPATH environment variable to include the project root
        env = os.environ.copy()

        # Add the project root to PYTHONPATH
        if "PYTHONPATH" in env:
            env["PYTHONPATH"] = f"{script_dir}:{env['PYTHONPATH']}"
        else:
            env["PYTHONPATH"] = script_dir

        print(f"📌 Setting PYTHONPATH to include: {script_dir}")

        # Run streamlit command with the wrapper path
        subprocess.run(
            [
                "streamlit",
                "run",
                wrapper_path,
                "--server.headless",
                "true",
            ],
            check=True,
            env=env,
        )
    except subprocess.CalledProcessError as e:
        print(f"❌ Error: Failed to launch Streamlit app: {e}")
        sys.exit(1)
    except FileNotFoundError:
        print("❌ Error: Streamlit not found. Please make sure it's installed.")
        print("Try running: pip install streamlit")
        sys.exit(1)


if __name__ == "__main__":
    main()
