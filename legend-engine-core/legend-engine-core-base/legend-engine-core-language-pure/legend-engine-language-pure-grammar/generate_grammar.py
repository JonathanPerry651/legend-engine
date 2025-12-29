import os
import sys
import subprocess
import shutil

def main():
    tool_path = sys.argv[1]
    output_jar = sys.argv[2]
    source_files = sys.argv[3:]

    # Base directory for package calculation
    base_dir = "src/main/antlr4"
    
    # Temp dirs
    work_dir = "antlr_work"
    gen_dir = "antlr_gen"
    os.makedirs(work_dir, exist_ok=True)
    os.makedirs(gen_dir, exist_ok=True)

    # Copy files to work_dir to have a clean structure for -lib potentially
    # But actually, we can just use the original paths if we set -lib correctly
    # The problem is -lib might need to be a list or a single dir.
    # We will assume that using base_dir as lib is enough? 
    # Or we can copy everything to a flat dir for lib like legend-pure does?
    # flattening allows "import CoreParserGrammar" to work without package prefix if the file is CoreParserGrammar.g4
    
    flat_lib = os.path.join(work_dir, "lib")
    os.makedirs(flat_lib, exist_ok=True)
    
    # Map of filename to full path
    file_map = {}

    print(f"Processing {len(source_files)} grammar files...")

    # Sort source files to process Lexers first
    def sort_key(f):
        if "Lexer" in os.path.basename(f):
            return 0
        return 1
    
    source_files.sort(key=sort_key)

    for f in source_files:
        filename = os.path.basename(f)
        file_map[f] = filename
        # Copy to flat lib
        shutil.copy(f, os.path.join(flat_lib, filename))

    for f in source_files:
        # Calculate package
        if base_dir in f:
            rel_path = f.split(base_dir)[1].lstrip("/")
        else:
            print(f"Warning: {f} does not contain {base_dir}")
            continue
            
        dir_path = os.path.dirname(rel_path)
        package_name = dir_path.replace("/", ".")
        
        # Exclude core grammars from compilation as per POM
        if "/core/" in f or f.endswith("CoreParserGrammar.g4"): # Robust check
             print(f"Skipping compilation of excluded file: {f}")
             continue

        # Prepare output dir
        # Antlr tool with -package and -o works well
        # We want output in gen_dir/org/finos/...
        out_path = os.path.join(gen_dir, dir_path)
        os.makedirs(out_path, exist_ok=True)

        print(f"Compiling {f} to package {package_name}")
        
        if "Parser" in filename:
             print(f"Checking flat_lib before compiling {filename}: {os.listdir(flat_lib)}")
             # Check specific token file if likely needed
             token_file = os.path.join(flat_lib, filename.replace("Parser", "Lexer").replace(".g4", ".tokens"))
             if os.path.exists(token_file):
                 print(f"Token file {token_file} exists. Size: {os.path.getsize(token_file)}")
                 # with open(token_file, 'r') as tf:
                 #    print(f"Content: {tf.read()}")
             else:
                 print(f"Token file {token_file} DOES NOT exist")

        cmd = [
            tool_path,
            "-package", package_name,
            "-visitor",
            "-listener",
            "-lib", os.path.abspath(flat_lib),
            "-o", out_path,
            os.path.join(flat_lib, os.path.basename(f))
        ]
        
        try:
            subprocess.check_call(cmd)
            
            print(f"Contents of out_path ({out_path}): {os.listdir(out_path)}")
            # Also check if there are subdirectories
            for root, dirs, files in os.walk(out_path):
                 print(f"  Walking {root}: {files}")

            # Copy generated tokens back to lib
            found_tokens = False
            # We might need to walk to find tokens if they are in subdirs
            for root, dirs, files in os.walk(out_path):
                for generated in files:
                    if generated.endswith(".tokens"):
                        shutil.copy(os.path.join(root, generated), flat_lib)
                        found_tokens = True
            
            if not found_tokens:
                print(f"Warning: No tokens generated for {filename}")
            else:
                print(f"Copied tokens for {filename}")

            # print(f"Lib contents: {os.listdir(flat_lib)}")

        except subprocess.CalledProcessError as e:
            print(f"Error compiling {f}: {e}")
            sys.exit(1)

    # Zip results
    # We zip the contents of gen_dir
    subprocess.check_call(["jar", "cf", output_jar, "-C", gen_dir, "."])

if __name__ == "__main__":
    main()
