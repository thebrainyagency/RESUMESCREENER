
import streamlit.web.cli as stcli
import sys
import os

# Add the current directory to Python path so we can import our modules
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, current_dir)

if __name__ == "__main__":
    # Run streamlit app
    sys.argv = ["streamlit", "run", os.path.join(current_dir, "app.py"), "--server.headless", "true"]
    sys.exit(stcli.main())
