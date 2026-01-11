"""
Installation Verification Script
Checks if all required packages are installed and working
"""

import sys

def check_import(module_name, package_name=None, optional=False):
    """Check if a module can be imported"""
    try:
        __import__(module_name)
        status = "✅ INSTALLED"
        return True
    except ImportError:
        if optional:
            status = "⚠️  OPTIONAL (not installed)"
        else:
            status = "❌ MISSING"
        package = package_name or module_name
        print(f"{status}: {package}")
        return optional  # Return True for optional packages


def main():
    print("=" * 60)
    print("🔍 Livestock Health System - Dependency Check")
    print("=" * 60)
    
    all_good = True
    
    # Required packages
    print("\n📦 Required Packages:")
    print("-" * 60)
    all_good &= check_import("cv2", "opencv-python")
    all_good &= check_import("numpy")
    all_good &= check_import("fastapi")
    all_good &= check_import("uvicorn")
    all_good &= check_import("PIL", "pillow")
    all_good &= check_import("pydantic")
    
    # QR code support
    print("\n📱 QR Code Detection:")
    print("-" * 60)
    pyzbar_ok = check_import("pyzbar")
    all_good &= pyzbar_ok
    
    # ML model support (optional)
    print("\n🤖 Machine Learning (Optional):")
    print("-" * 60)
    tf_ok = check_import("tensorflow", optional=True)
    
    # Database (built-in)
    print("\n💾 Database:")
    print("-" * 60)
    check_import("sqlite3")
    print("✅ INSTALLED: sqlite3 (built-in)")
    
    # Additional packages
    print("\n📊 Additional Packages:")
    print("-" * 60)
    check_import("pandas", optional=True)
    check_import("sklearn", "scikit-learn", optional=True)
    
    print("\n" + "=" * 60)
    
    if all_good:
        print("✅ ALL REQUIRED PACKAGES INSTALLED!")
        print("\n🚀 Ready to run:")
        print("   python server_enhanced.py")
        
        if not tf_ok:
            print("\n⚠️  Note: TensorFlow not installed")
            print("   System will use fallback heuristic analysis")
            print("   To install: pip install tensorflow")
        
        return 0
    else:
        print("❌ SOME REQUIRED PACKAGES ARE MISSING!")
        print("\n📥 To install missing packages:")
        print("   pip install -r requirements.txt")
        print("\n⚠️  Windows pyzbar issue?")
        print("   Download: https://aka.ms/vs/17/release/vc_redist.x64.exe")
        return 1


if __name__ == "__main__":
    sys.exit(main())
