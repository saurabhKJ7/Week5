#!/usr/bin/env python3
"""
Setup script for Excel Sheets Agent
"""

import os
import sys
import subprocess
import platform
from pathlib import Path


def check_python_version():
    """Check if Python version is compatible"""
    if sys.version_info < (3, 8):
        print("❌ Python 3.8 or higher is required")
        print(f"Current version: {sys.version}")
        return False
    print(f"✅ Python version: {sys.version}")
    return True


def create_virtual_environment():
    """Create and activate virtual environment"""
    print("🔧 Creating virtual environment...")
    
    try:
        subprocess.run([sys.executable, "-m", "venv", "venv"], check=True)
        print("✅ Virtual environment created successfully")
        return True
    except subprocess.CalledProcessError:
        print("❌ Failed to create virtual environment")
        return False


def get_pip_command():
    """Get the appropriate pip command for the platform"""
    if platform.system() == "Windows":
        return "venv\\Scripts\\pip"
    else:
        return "venv/bin/pip"


def install_dependencies():
    """Install required packages"""
    print("📦 Installing dependencies...")
    
    pip_cmd = get_pip_command()
    
    try:
        # Upgrade pip first
        subprocess.run([pip_cmd, "install", "--upgrade", "pip"], check=True)
        
        # Install requirements
        subprocess.run([pip_cmd, "install", "-r", "requirements.txt"], check=True)
        
        print("✅ Dependencies installed successfully")
        return True
    except subprocess.CalledProcessError:
        print("❌ Failed to install dependencies")
        return False


def create_directories():
    """Create necessary directories"""
    print("📁 Creating directories...")
    
    directories = [
        "temp",
        "output", 
        "data",
        "sample_data"
    ]
    
    for directory in directories:
        Path(directory).mkdir(exist_ok=True)
        print(f"   Created: {directory}/")
    
    print("✅ Directories created successfully")


def create_env_file():
    """Create .env file template"""
    print("🔐 Creating .env file template...")
    
    env_template = """# LLM API Keys (uncomment and add your key)
# OPENAI_API_KEY=your_openai_key_here
# ANTHROPIC_API_KEY=your_anthropic_key_here

# Database Configuration
DATABASE_PATH=data/excel_agent.db

# Processing Configuration
CHUNK_SIZE=5000
MAX_FILE_SIZE_MB=200
FUZZY_THRESHOLD=80

# Cache Configuration
CACHE_ENABLED=true
CACHE_TTL=3600
"""
    
    with open(".env", "w") as f:
        f.write(env_template)
    
    print("✅ .env file created successfully")
    print("   Please add your API keys to the .env file")


def create_sample_data():
    """Generate sample Excel files"""
    print("📊 Creating sample Excel files...")
    
    try:
        subprocess.run([sys.executable, "create_sample_data.py"], check=True)
        print("✅ Sample data created successfully")
        return True
    except subprocess.CalledProcessError:
        print("❌ Failed to create sample data")
        return False


def print_next_steps():
    """Print next steps for the user"""
    print("\n🎉 Setup completed successfully!")
    print("\n📋 Next steps:")
    print("1. Add your API key to the .env file:")
    print("   - For OpenAI: OPENAI_API_KEY=your_key_here")
    print("   - For Anthropic: ANTHROPIC_API_KEY=your_key_here")
    print("\n2. Activate the virtual environment:")
    
    if platform.system() == "Windows":
        print("   venv\\Scripts\\activate")
    else:
        print("   source venv/bin/activate")
    
    print("\n3. Run the application:")
    print("   streamlit run app.py")
    print("\n4. Open your browser to: http://localhost:8501")
    print("\n📖 For more information, check the README.md file")


def main():
    """Main setup function"""
    print("🚀 Excel Sheets Agent Setup")
    print("=" * 40)
    
    # Check Python version
    if not check_python_version():
        sys.exit(1)
    
    # Create virtual environment
    if not create_virtual_environment():
        sys.exit(1)
    
    # Install dependencies
    if not install_dependencies():
        sys.exit(1)
    
    # Create directories
    create_directories()
    
    # Create .env file
    create_env_file()
    
    # Create sample data
    create_sample_data()
    
    # Print next steps
    print_next_steps()


if __name__ == "__main__":
    main() 