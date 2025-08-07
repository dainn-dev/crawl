#!/usr/bin/env python3
"""
Windows-specific installation script for ECHR Respondent Scraper
Handles compilation issues and provides alternative installation methods
"""

import subprocess
import sys
import os
import platform

def check_python_version():
    """Check if Python version is compatible"""
    version = sys.version_info
    if version.major < 3 or (version.major == 3 and version.minor < 8):
        print("❌ Python 3.8 or higher is required")
        return False
    print(f"✅ Python {version.major}.{version.minor}.{version.micro} is compatible")
    return True

def install_visual_cpp_tools():
    """Provide instructions for installing Visual C++ Build Tools"""
    print("\n" + "="*60)
    print("VISUAL C++ BUILD TOOLS REQUIRED")
    print("="*60)
    print("To fix the compilation error, you need to install Microsoft Visual C++ Build Tools:")
    print("\n1. Download from: https://visualstudio.microsoft.com/visual-cpp-build-tools/")
    print("2. Run the installer")
    print("3. Select 'C++ build tools' workload")
    print("4. Install")
    print("\nAlternatively, try the pre-compiled wheel installation below.")
    print("="*60)

def install_with_precompiled_wheels():
    """Install using pre-compiled wheels to avoid compilation"""
    print("\n🔧 Installing with pre-compiled wheels...")
    
    try:
        # Upgrade pip first
        subprocess.check_call([sys.executable, "-m", "pip", "install", "--upgrade", "pip"])
        
        # Install wheel and setuptools
        subprocess.check_call([sys.executable, "-m", "pip", "install", "wheel", "setuptools"])
        
        # Install Playwright with specific options
        subprocess.check_call([
            sys.executable, "-m", "pip", "install", 
            "playwright==1.40.0",
            "--only-binary=all",  # Use only pre-compiled wheels
            "--no-cache-dir"      # Don't use cached wheels
        ])
        
        # Install Playwright browsers
        subprocess.check_call([sys.executable, "-m", "playwright", "install"])
        
        print("✅ Playwright installed successfully with pre-compiled wheels!")
        return True
        
    except subprocess.CalledProcessError as e:
        print(f"❌ Failed to install with pre-compiled wheels: {e}")
        return False

def install_with_conda():
    """Alternative installation using conda (if available)"""
    print("\n🔧 Trying conda installation...")
    
    try:
        # Check if conda is available
        subprocess.check_call(["conda", "--version"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        
        # Install with conda
        subprocess.check_call(["conda", "install", "-c", "conda-forge", "playwright", "-y"])
        subprocess.check_call([sys.executable, "-m", "playwright", "install"])
        
        print("✅ Playwright installed successfully with conda!")
        return True
        
    except (subprocess.CalledProcessError, FileNotFoundError):
        print("❌ Conda not available or installation failed")
        return False

def install_individual_packages():
    """Install packages individually to identify problematic ones"""
    print("\n🔧 Installing packages individually...")
    
    packages = [
        "playwright==1.40.0",
        "asyncio",
        "typing"
    ]
    
    for package in packages:
        try:
            print(f"Installing {package}...")
            subprocess.check_call([
                sys.executable, "-m", "pip", "install", 
                package,
                "--only-binary=all",
                "--no-cache-dir"
            ])
            print(f"✅ {package} installed successfully")
        except subprocess.CalledProcessError as e:
            print(f"❌ Failed to install {package}: {e}")
            return False
    
    # Install Playwright browsers
    try:
        subprocess.check_call([sys.executable, "-m", "playwright", "install"])
        print("✅ Playwright browsers installed successfully")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ Failed to install Playwright browsers: {e}")
        return False

def main():
    """Main installation function"""
    print("="*60)
    print("ECHR Respondent Scraper - Windows Installation")
    print("="*60)
    
    # Check Python version
    if not check_python_version():
        return
    
    # Check if we're on Windows
    if platform.system() != "Windows":
        print("This script is designed for Windows. Use the regular installation on other platforms.")
        return
    
    print(f"Platform: {platform.system()} {platform.release()}")
    
    # Try different installation methods
    methods = [
        ("Pre-compiled wheels", install_with_precompiled_wheels),
        ("Individual packages", install_individual_packages),
        ("Conda installation", install_with_conda)
    ]
    
    for method_name, method_func in methods:
        print(f"\n🔄 Trying {method_name}...")
        if method_func():
            print(f"✅ Installation successful using {method_name}!")
            
            # Test the installation
            try:
                import playwright
                print("✅ Playwright import test successful!")
                
                # Run a simple test
                from playwright.async_api import async_playwright
                print("✅ Playwright async API test successful!")
                
                print("\n🎉 Installation completed successfully!")
                print("You can now run the scraper with: python echr_respondent_scraper.py")
                return
                
            except ImportError as e:
                print(f"❌ Import test failed: {e}")
                continue
    
    # If all methods failed, provide manual instructions
    print("\n❌ All installation methods failed.")
    install_visual_cpp_tools()
    
    print("\nAlternative manual installation steps:")
    print("1. Install Visual C++ Build Tools (see above)")
    print("2. Run: pip install playwright==1.40.0")
    print("3. Run: playwright install")
    print("4. Test with: python -c 'import playwright'")

if __name__ == "__main__":
    main() 