#!/usr/bin/env python3
"""
Startup script for the Streamlit Admin Interface
Checks dependencies and launches the application.
"""

import sys
import subprocess
import importlib.util
from pathlib import Path


def check_module(module_name):
    """Check if a module is available."""
    spec = importlib.util.find_spec(module_name)
    return spec is not None


def check_required_modules():
    """Check if all required modules are available."""
    required_modules = [
        'streamlit',
        'plotly',
        'pandas',
        'elasticsearch',
        'pydantic'
    ]
    
    missing_modules = []
    for module in required_modules:
        if not check_module(module):
            missing_modules.append(module)
    
    return missing_modules


def check_elasticsearch_connection():
    """Check if Elasticsearch is accessible."""
    try:
        from helpdesk_elasticsearch import HelpdeskElasticsearchManager
        es_manager = HelpdeskElasticsearchManager()
        es_manager.connect()
        es_manager.close()
        return True
    except Exception as e:
        print(f"❌ Elasticsearch connection failed: {e}")
        return False


def install_requirements():
    """Install required packages."""
    print("📦 Installing required packages...")
    try:
        subprocess.check_call([
            sys.executable, "-m", "pip", "install", "-r", "streamlit_requirements.txt"
        ])
        print("✅ Requirements installed successfully!")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ Failed to install requirements: {e}")
        return False


def main():
    """Main startup function."""
    print("🚀 Streamlit Admin Interface - Startup")
    print("=" * 50)
    
    # Check if we're in the right directory
    if not Path("streamlit_admin.py").exists():
        print("❌ streamlit_admin.py not found in current directory")
        print("Please run this script from the project root directory")
        return False
    
    # Check required modules
    print("🔍 Checking required modules...")
    missing_modules = check_required_modules()
    
    if missing_modules:
        print(f"❌ Missing modules: {', '.join(missing_modules)}")
        print("Installing requirements...")
        
        if not install_requirements():
            print("❌ Failed to install requirements")
            print("Please install manually: pip install -r streamlit_requirements.txt")
            return False
        
        # Check again after installation
        missing_modules = check_required_modules()
        if missing_modules:
            print(f"❌ Still missing modules: {', '.join(missing_modules)}")
            return False
    
    print("✅ All required modules are available")
    
    # Check Elasticsearch connection
    print("🔍 Checking Elasticsearch connection...")
    if not check_elasticsearch_connection():
        print("⚠️  Elasticsearch is not accessible")
        print("Please ensure Elasticsearch is running before starting the admin interface")
        print("You can still start the app, but some features may not work")
    
    # Launch Streamlit
    print("🚀 Starting Streamlit Admin Interface...")
    print("The application will open in your browser at http://localhost:8501")
    print("Press Ctrl+C to stop the application")
    print("-" * 50)
    
    try:
        subprocess.run([
            sys.executable, "-m", "streamlit", "run", "streamlit_admin.py"
        ])
    except KeyboardInterrupt:
        print("\n👋 Streamlit Admin Interface stopped")
    except Exception as e:
        print(f"❌ Failed to start Streamlit: {e}")
        return False
    
    return True


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
