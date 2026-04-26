import importlib
import sys
import traceback
import io

# Force UTF-8 encoding for stdout to prevent cp1252 charmap errors with emojis on Windows
if sys.stdout.encoding.lower() != 'utf-8':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

def main():
    # List of modules to run in sequence
    cells = [
        "specsense_cell1",
        "specsense_cell2",
        "specsense_cell3",
        "specsense_cell4",
        "specsense_cell5",
        "specsense_cell6",
        "specsense_cell7",
        "specsense_cell8",
        "specsense_cell9",
    ]

    print("[*] Starting SpecSense Execution Pipeline...")
    
    for cell_name in cells:
        print("\n" + "="*50)
        print(f"[>] Executing {cell_name}...")
        print("="*50)
        
        try:
            # Import the module dynamically
            module = importlib.import_module(cell_name)
            
            # Check for a run() or main() function and execute it if found
            if hasattr(module, 'run') and callable(module.run):
                print(f"[{cell_name}] Found run() function. Executing...")
                module.run()
            elif hasattr(module, 'main') and callable(module.main):
                print(f"[{cell_name}] Found main() function. Executing...")
                module.main()
            else:
                print(f"[{cell_name}] No main() or run() function found. Module level code executed on import.")
                
        except Exception as e:
            print(f"\n[X] Error executing {cell_name}:")
            traceback.print_exc()
            print("\n[!] Pipeline execution stopped due to an error.")
            sys.exit(1)
            
    print("\n[+] All SpecSense cells executed successfully!")

if __name__ == "__main__":
    main()
