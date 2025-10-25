#!/usr/bin/env python3
"""
Setup script for Vapi-Haptik Voice Bot
Initializes environment, installs dependencies, and configures services
"""

import os
import sys
import subprocess
import shutil
from pathlib import Path


def print_header(text):
    """Print formatted header"""
    print("\n" + "="*60)
    print(f"  {text}")
    print("="*60 + "\n")


def check_python_version():
    """Check if Python version is 3.9+"""
    print("🐍 Checking Python version...")
    version = sys.version_info
    if version.major < 3 or (version.major == 3 and version.minor < 9):
        print("❌ Python 3.9+ is required")
        sys.exit(1)
    print(f"✅ Python {version.major}.{version.minor}.{version.micro}")


def check_node_version():
    """Check if Node.js is installed"""
    print("\n📦 Checking Node.js...")
    try:
        result = subprocess.run(
            ["node", "--version"],
            capture_output=True,
            text=True
        )
        print(f"✅ Node.js {result.stdout.strip()}")
        return True
    except FileNotFoundError:
        print("⚠️  Node.js not found (optional)")
        return False


def create_directories():
    """Create necessary directories"""
    print("\n📁 Creating directories...")
    directories = [
        "logs",
        "data",
        "tests/__pycache__",
        "vapi/__pycache__",
        "haptik/__pycache__",
        "backend/__pycache__",
        "integration/__pycache__"
    ]
    
    for directory in directories:
        Path(directory).mkdir(parents=True, exist_ok=True)
    
    print("✅ Directories created")


def install_python_dependencies():
    """Install Python dependencies"""
    print("\n📦 Installing Python dependencies...")
    try:
        subprocess.run(
            [sys.executable, "-m", "pip", "install", "--upgrade", "pip"],
            check=True
        )
        subprocess.run(
            [sys.executable, "-m", "pip", "install", "-r", "requirements.txt"],
            check=True
        )
        print("✅ Python dependencies installed")
    except subprocess.CalledProcessError as e:
        print(f"❌ Error installing Python dependencies: {e}")
        sys.exit(1)


def install_node_dependencies():
    """Install Node.js dependencies"""
    if not os.path.exists("package.json"):
        print("⚠️  No package.json found, skipping Node dependencies")
        return
    
    print("\n📦 Installing Node.js dependencies...")
    try:
        subprocess.run(["npm", "install"], check=True)
        print("✅ Node.js dependencies installed")
    except (subprocess.CalledProcessError, FileNotFoundError) as e:
        print(f"⚠️  Skipping Node dependencies: {e}")


def setup_environment():
    """Setup environment file"""
    print("\n⚙️  Setting up environment...")
    
    env_example = "config/env.example"
    env_file = "config/.env"
    
    if not os.path.exists(env_file):
        if os.path.exists(env_example):
            shutil.copy(env_example, env_file)
            print(f"✅ Created {env_file} from template")
            print("⚠️  Please edit config/.env with your API keys")
        else:
            print("⚠️  No env.example found")
    else:
        print(f"✅ {env_file} already exists")


def initialize_database():
    """Initialize database"""
    print("\n🗄️  Initializing database...")
    try:
        sys.path.append(os.path.dirname(os.path.dirname(__file__)))
        from backend.booking_service import BookingService
        
        service = BookingService()
        print("✅ Database initialized")
    except Exception as e:
        print(f"⚠️  Database initialization warning: {e}")


def run_tests():
    """Run basic tests"""
    print("\n🧪 Running basic tests...")
    try:
        subprocess.run(
            [sys.executable, "-m", "pytest", "tests/", "-v"],
            check=False  # Don't fail setup if tests fail
        )
    except Exception as e:
        print(f"⚠️  Tests skipped: {e}")


def display_next_steps():
    """Display next steps"""
    print_header("🎉 Setup Complete!")
    
    print("""
Next Steps:
    
1. Configure your environment:
   $ nano config/.env
   
   Add your API keys:
   - VAPI_API_KEY
   - HAPTIK_API_KEY
   - FLIGHT_API_KEY
   - HOTEL_API_KEY

2. Create Vapi assistant:
   $ python vapi/voice_agent.py

3. Start the backend server:
   $ python backend/server.py
   
   Or use the start script:
   $ ./scripts/start_services.sh

4. Test the integration:
   $ python integration/connector.py

5. View API documentation:
   http://localhost:8080/docs

6. Make a test call:
   $ python scripts/test_call.py

For more information, see:
- README.md
- docs/SETUP.md
- docs/API_REFERENCE.md

Need help? Contact: support@mytrip.ai
""")


def main():
    """Main setup function"""
    print_header("🎙️  Travel.ai Voice Bot Setup")
    
    # Change to project directory
    os.chdir(Path(__file__).parent.parent)
    
    # Run setup steps
    check_python_version()
    check_node_version()
    create_directories()
    install_python_dependencies()
    install_node_dependencies()
    setup_environment()
    initialize_database()
    
    # Optional: run tests
    response = input("\n🧪 Run tests? (y/N): ").lower()
    if response == 'y':
        run_tests()
    
    display_next_steps()


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n⚠️  Setup cancelled by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n\n❌ Setup failed: {e}")
        sys.exit(1)

