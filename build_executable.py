#!/usr/bin/env python3
"""
Build script to create executable for Resume Screener
Creates a single-file executable that non-technical users can run
"""

import os
import sys
import subprocess
import shutil
from pathlib import Path

def install_pyinstaller():
    """Install PyInstaller if not available"""
    try:
        import PyInstaller
        print("✅ PyInstaller already installed")
    except ImportError:
        print("📦 Installing PyInstaller...")
        subprocess.check_call([sys.executable, "-m", "pip", "install", "pyinstaller"])

def create_launcher_script():
    """Create a simple launcher script for the Streamlit app"""
    launcher_content = '''
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
'''

    with open("launcher.py", "w") as f:
        f.write(launcher_content)
    print("✅ Created launcher.py")

def build_executable():
    """Build the executable using PyInstaller"""
    print("🔨 Building executable...")

    # Determine the correct separator for --add-data (Windows uses ; others use :)
    separator = ";" if sys.platform == "win32" else ":"

    # PyInstaller command
    cmd = [
        "pyinstaller",
        "--onefile",                              # Single file
        "--name=ResumeScreener",                 # Output name
        f"--add-data=ui{separator}ui",           # Include UI package
        f"--add-data=src{separator}src",         # Include src package
        f"--add-data=data{separator}data",       # Include sample data
        f"--add-data=app.py{separator}.",        # Include main app
        "--hidden-import=streamlit",
        "--hidden-import=openai",
        "--hidden-import=PyPDF2",
        "--hidden-import=docx",
        "--hidden-import=sklearn",
        "--hidden-import=nltk",
        "--hidden-import=pandas",
        "--hidden-import=tqdm",
        "--collect-all=streamlit",               # Collect all streamlit files
        "launcher.py"
    ]

    # Add icon if it exists
    if os.path.exists("icon.ico"):
        cmd.insert(-1, "--icon=icon.ico")

    # Don't use --windowed for Streamlit apps as we need console output
    # cmd.append("--windowed")

    try:
        subprocess.check_call(cmd)
        print("✅ Executable built successfully!")
        print(f"📁 Find your executable in: dist/ResumeScreener{'.exe' if sys.platform == 'win32' else ''}")
    except subprocess.CalledProcessError as e:
        print(f"❌ Build failed: {e}")
        return False

    return True

def create_distribution_package():
    """Create a distribution package with executable and required files"""
    # Create distribution directory in parent folder
    parent_dir = Path("..").resolve()
    dist_dir = parent_dir / "ResumeScreener_Distribution"

    # Clean and create distribution directory
    if dist_dir.exists():
        shutil.rmtree(dist_dir)
    dist_dir.mkdir()

    # Copy executable
    exe_name = "ResumeScreener.exe" if sys.platform == "win32" else "ResumeScreener"
    exe_source = Path("dist") / exe_name

    if exe_source.exists():
        shutil.copy2(exe_source, dist_dir / exe_name)
        print(f"✅ Copied executable to {dist_dir}")

    # Copy sample files
    shutil.copytree("data", dist_dir / "data")

    # Create README for users
    readme_content = """# Resume Screener - Ready to Use!

## How to Run:
1. Double-click the ResumeScreener executable
2. Your browser will open automatically
3. Follow the on-screen instructions

## What You Need:
- OpenAI API key (you can enter this in the app)
- Resume files (PDF, DOCX, or TXT)
- Job description text
- Scoring rubric

## Sample Files:
- data/jd_sample.txt - Example job description
- data/rubric_sample.txt - Example scoring rubric
- data/resumes/ - Sample resume files

## Troubleshooting:
- If the app doesn't open, check your firewall settings
- Make sure you have an internet connection for the OpenAI API
- On macOS, you may need to right-click → "Open" the first time

Need help? Check the full documentation in the original repository.
"""

    with open(dist_dir / "README.txt", "w") as f:
        f.write(readme_content)

    print(f"✅ Distribution package created: {dist_dir}")
    return dist_dir

def main():
    print("🚀 Building Resume Screener Executable")
    print("=" * 50)

    # Check if we're in the right directory
    if not os.path.exists("app.py"):
        print("❌ app.py not found. Please run this script from the project root directory.")
        return

    # Install PyInstaller
    install_pyinstaller()

    # Create launcher script
    create_launcher_script()

    # Build executable
    if build_executable():
        # Create distribution package
        dist_dir = create_distribution_package()

        print("\n🎉 SUCCESS!")
        print(f"📦 Your executable is ready in: {dist_dir}")
        print("\n📋 Next steps:")
        print("1. Test the executable on your machine")
        print("2. Zip the distribution folder")
        print("3. Share with your team!")
        print("\n💡 Users just need to:")
        print("- Unzip the folder")
        print("- Double-click the executable")
        print("- Enter their OpenAI API key when prompted")

if __name__ == "__main__":
    main()