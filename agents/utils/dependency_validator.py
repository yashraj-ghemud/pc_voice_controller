"""
Dependency validation utility for the Kypzer AI agent system.

This module provides functions to validate that all required dependencies
are properly installed and compatible.
"""

import sys
from typing import List, Tuple


def check_required_packages() -> Tuple[bool, List[str]]:
    """
    Check if all required packages for the agent system are installed.
    
    Returns:
        Tuple of (all_installed: bool, missing_packages: List[str])
    """
    required_packages = [
        # Agent system core
        ("langgraph", "0.0.30"),
        ("langchain", "0.1.0"),
        ("langchain_core", "0.1.0"),
        ("langchain_google_genai", "0.0.5"),
        ("pyautogen", "0.2.0"),
        # Existing dependencies
        ("google.genai", None),
        ("speech_recognition", None),
        ("chromadb", None),
        ("dotenv", None),
    ]
    
    missing = []
    
    for package_name, min_version in required_packages:
        try:
            if "." in package_name:
                # Handle nested imports
                __import__(package_name)
            else:
                __import__(package_name)
        except ImportError:
            missing.append(f"{package_name}>={min_version}" if min_version else package_name)
    
    return len(missing) == 0, missing


def validate_environment() -> bool:
    """
    Validate that the environment is ready for the agent system.
    
    Returns:
        True if environment is valid, False otherwise
    """
    all_installed, missing = check_required_packages()
    
    if not all_installed:
        print("❌ Missing required packages:")
        for pkg in missing:
            print(f"   - {pkg}")
        print("\nInstall missing packages with:")
        print("   pip install -r requirements.txt")
        return False
    
    print("✅ All required packages are installed")
    return True


if __name__ == "__main__":
    success = validate_environment()
    sys.exit(0 if success else 1)
