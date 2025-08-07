#!/usr/bin/env python3
"""
Quick installation script to bypass compilation issues
"""

import subprocess
import sys
import os

def quick_install():
    """Quick installation that bypasses problematic packages"""
    print("🔧 Quick installation for ECHR Respondent Scraper...")
    
    try:
        # Install only Playwright with specific options
        print("Installing Playwright...")
        subprocess.check_call([
            sys.executable, "-m", "pip", "install", 
            "playwright==1.40.0",
            "--only-binary=all",
            "--no-deps",  # Don't install dependencies that might need compilation
            "--force-reinstall"
        ])
        
        # Install Playwright browsers
        print("Installing Playwright browsers...")
        subprocess.check_call([sys.executable, "-m", "playwright", "install"])
        
        print("✅ Quick installation completed!")
        return True
        
    except subprocess.CalledProcessError as e:
        print(f"❌ Quick installation failed: {e}")
        return False

def test_installation():
    """Test if the installation works"""
    try:
        import playwright
        from playwright.async_api import async_playwright
        print("✅ Installation test successful!")
        return True
    except ImportError as e:
        print(f"❌ Installation test failed: {e}")
        return False

def main():
    print("="*50)
    print("Quick Installation for ECHR Respondent Scraper")
    print("="*50)
    
    if quick_install():
        if test_installation():
            print("\n🎉 Installation successful!")
            print("You can now run: python echr_respondent_scraper.py")
        else:
            print("\n❌ Installation test failed. Try the Windows-specific installer.")
    else:
        print("\n❌ Quick installation failed. Try the Windows-specific installer.")

if __name__ == "__main__":
    main() 