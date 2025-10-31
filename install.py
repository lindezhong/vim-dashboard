#!/usr/bin/env python3
"""
vim-dashboard installation script
This script sets up the virtual environment and installs dependencies
"""

import os
import sys
import subprocess
import platform
from pathlib import Path


def get_script_dir():
    """Get the directory where this script is located."""
    return Path(__file__).parent.absolute()


def get_venv_path():
    """Get the virtual environment path."""
    return get_script_dir() / 'venv'


def get_python_executable():
    """Get the appropriate Python executable."""
    # Try python3 first, then python
    for cmd in ['python3', 'python']:
        try:
            result = subprocess.run([cmd, '--version'], 
                                  capture_output=True, text=True, check=True)
            if 'Python 3' in result.stdout:
                return cmd
        except (subprocess.CalledProcessError, FileNotFoundError):
            continue
    
    raise RuntimeError("Python 3 not found. Please install Python 3.7 or later.")


def create_venv():
    """Create virtual environment."""
    venv_path = get_venv_path()
    python_cmd = get_python_executable()
    
    print(f"Creating virtual environment at {venv_path}...")
    
    try:
        subprocess.run([python_cmd, '-m', 'venv', str(venv_path)], check=True)
        print("✓ Virtual environment created successfully")
    except subprocess.CalledProcessError as e:
        raise RuntimeError(f"Failed to create virtual environment: {e}")


def get_venv_python():
    """Get the Python executable in the virtual environment."""
    venv_path = get_venv_path()
    
    if platform.system() == 'Windows':
        return venv_path / 'Scripts' / 'python.exe'
    else:
        return venv_path / 'bin' / 'python'


def install_dependencies():
    """Install Python dependencies."""
    venv_python = get_venv_python()
    requirements_file = get_script_dir() / 'requirements.txt'
    
    if not requirements_file.exists():
        raise RuntimeError(f"Requirements file not found: {requirements_file}")
    
    print("Installing dependencies...")
    
    try:
        # Upgrade pip first
        subprocess.run([str(venv_python), '-m', 'pip', 'install', '--upgrade', 'pip'], 
                      check=True)
        
        # Install requirements
        subprocess.run([str(venv_python), '-m', 'pip', 'install', '-r', str(requirements_file)], 
                      check=True)
        print("✓ Dependencies installed successfully")
    except subprocess.CalledProcessError as e:
        raise RuntimeError(f"Failed to install dependencies: {e}")


def verify_installation():
    """Verify that the installation was successful."""
    venv_python = get_venv_python()
    
    print("Verifying installation...")
    
    # Test imports
    test_imports = [
        'rich',
        'yaml',
        'dashboard'
    ]
    
    for module in test_imports:
        try:
            result = subprocess.run([str(venv_python), '-c', f'import {module}'], 
                                  capture_output=True, text=True, check=True)
            print(f"✓ {module} imported successfully")
        except subprocess.CalledProcessError:
            print(f"✗ Failed to import {module}")
            return False
    
    return True


def print_usage_instructions():
    """Print usage instructions."""
    print("\n" + "="*60)
    print("🎉 vim-dashboard installation completed successfully!")
    print("="*60)
    print("\nUsage:")
    print("1. Make sure vim-dashboard is in your vim plugin path")
    print("2. Create a config file in ~/dashboard/ directory")
    print("3. Use the following commands in vim:")
    print("   :DashboardStart <config_file>  - Start dashboard")
    print("   :DashboardRestart              - Restart current dashboard")
    print("   :DashboardStop                 - Stop dashboard")
    print("   :DashboardList                 - List running dashboards")
    print("   :Dashboard                     - Browse config files")
    print("\nExample config file (~/dashboard/example.yaml):")
    print("""
database:
  type: sqlite
  url: sqlite:///example.db
query: "SELECT 'Hello' as message, 'World' as target"
interval: 30s
show:
  type: table
  column_list:
    - column: message
      alias: Message
    - column: target
      alias: Target
""")
    print("\nFor more information, check the documentation.")


def main():
    """Main installation function."""
    try:
        print("vim-dashboard Installation Script")
        print("=" * 40)
        
        # Check if virtual environment already exists
        venv_path = get_venv_path()
        if venv_path.exists():
            print(f"Virtual environment already exists at {venv_path}")
            response = input("Do you want to recreate it? (y/N): ").strip().lower()
            if response in ['y', 'yes']:
                import shutil
                shutil.rmtree(venv_path)
                print("Removed existing virtual environment")
            else:
                print("Using existing virtual environment")
        
        # Create virtual environment if it doesn't exist
        if not venv_path.exists():
            create_venv()
        
        # Install dependencies
        install_dependencies()
        
        # Verify installation
        if verify_installation():
            print_usage_instructions()
        else:
            print("\n❌ Installation verification failed!")
            print("Please check the error messages above and try again.")
            sys.exit(1)
            
    except Exception as e:
        print(f"\n❌ Installation failed: {e}")
        sys.exit(1)


if __name__ == '__main__':
    main()