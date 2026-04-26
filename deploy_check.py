import os
import sys

# Force UTF-8 encoding for standard output
sys.stdout.reconfigure(encoding='utf-8')

def check_files():
    print("="*50)
    print("🚀 SPECSENSE DEPLOYMENT CHECKLIST")
    print("="*50)
    print("\n[1] Checking Required Files...")
    
    required_files = [
        "Dockerfile",
        "requirements.txt",
        "README.md",
        "app.py",
        ".gitignore",
        "specsense_cell1.py",
        "specsense_cell2.py",
        "specsense_cell3.py",
        "specsense_cell4.py",
        "specsense_cell5.py",
        "specsense_cell6.py",
        "specsense_cell7.py",
        "specsense_cell8.py"
    ]
    
    missing_files = []
    for f in required_files:
        if os.path.exists(f):
            print(f"  ✅ {f} found")
        else:
            print(f"  ❌ {f} MISSING")
            missing_files.append(f)
            
    if missing_files:
        print("\n❌ FAILED: Missing required files.")
        return False
        
    print("\n[2] Checking Imports (Ensuring cells don't execute on import)...")
    
    cells = [f"specsense_cell{i}" for i in range(1, 9)]
    cells.append("app")
    
    all_imports_passed = True
    for module_name in cells:
        try:
            # We use __import__ to dynamically import the module
            __import__(module_name)
            print(f"  ✅ {module_name}.py imported successfully")
        except Exception as e:
            print(f"  ❌ {module_name}.py failed to import: {e}")
            all_imports_passed = False
            
    if not all_imports_passed:
        print("\n❌ FAILED: One or more modules have import errors. Ensure all testing code is wrapped in if __name__ == '__main__':")
        return False
        
    print("\n" + "="*50)
    print("✅ ALL CHECKS PASSED!")
    print("="*50)
    print("\nNext steps for HuggingFace Spaces Deployment:")
    print("1. Go to huggingface.co/spaces and create a new Docker Space.")
    print("2. Clone the space locally: git clone https://huggingface.co/spaces/YOUR_USERNAME/SPACE_NAME")
    print("3. Copy all these files into the cloned repository.")
    print("4. git add . && git commit -m 'Deploy SpecSense' && git push")
    print("5. HuggingFace will automatically build your Docker container.")
    
    return True

if __name__ == "__main__":
    success = check_files()
    sys.exit(0 if success else 1)
