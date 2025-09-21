#!/bin/bash

# Resume Screener Launcher Script for macOS/Linux
echo "=========================================="
echo "       Resume Screener - Starting..."
echo "=========================================="
echo

# Check if Python is installed
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 is not installed"
    echo
    echo "Please install Python 3.12+ from https://python.org"
    echo "Or using Homebrew: brew install python"
    echo
    read -p "Press any key to exit..."
    exit 1
fi

echo "✅ Python found: $(python3 --version)"
echo

# Check if we're in the right directory
if [ ! -f "app.py" ]; then
    echo "❌ app.py not found"
    echo "Please make sure you're running this from the ResumeScreener folder"
    echo
    read -p "Press any key to exit..."
    exit 1
fi

# Install/update dependencies
echo "📦 Installing dependencies..."
pip3 install -r requirements.txt
if [ $? -ne 0 ]; then
    echo "❌ Failed to install dependencies"
    echo "You might need to install pip: python3 -m ensurepip --upgrade"
    read -p "Press any key to exit..."
    exit 1
fi

echo "✅ Dependencies installed"
echo

# Start the Streamlit app
echo "🚀 Starting Resume Screener..."
echo "🌐 Your browser should open automatically"
echo "📋 If not, open: http://localhost:8501"
echo
echo "⚠️  To stop the app, close this terminal or press Ctrl+C"
echo

streamlit run app.py --server.headless false --server.port 8501