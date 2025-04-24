#!/usr/bin/env python3
"""
Script to check the structure of a Lambda layer ZIP file
"""
import os
import sys
import zipfile
import tempfile


def analyze_zip_structure(zip_path):
    """Analyze the structure of a ZIP file and print its contents"""
    if not os.path.exists(zip_path):
        print(f"Error: File {zip_path} does not exist")
        return False

    print(f"Analyzing ZIP file: {zip_path}")

    # Create a temporary directory to extract the ZIP
    with tempfile.TemporaryDirectory() as temp_dir:
        # Extract the ZIP
        with zipfile.ZipFile(zip_path, "r") as zip_ref:
            zip_ref.extractall(temp_dir)

        # Print the directory structure
        print("\nDirectory structure:")
        for root, dirs, files in os.walk(temp_dir):
            level = root.replace(temp_dir, "").count(os.sep)
            indent = " " * 4 * level
            print(f"{indent}{os.path.basename(root)}/")
            subindent = " " * 4 * (level + 1)
            for f in files:
                print(f"{subindent}{f}")

        # Check for Python packages
        print("\nChecking for Python packages:")
        python_paths = []
        for root, dirs, files in os.walk(temp_dir):
            if "site-packages" in root:
                python_paths.append(root)

        if python_paths:
            for path in python_paths:
                print(f"Found site-packages directory: {path.replace(temp_dir, '')}")
                # Check for WeasyPrint
                weasyprint_path = os.path.join(path, "weasyprint")
                if os.path.exists(weasyprint_path):
                    print(
                        f"WeasyPrint found at: {weasyprint_path.replace(temp_dir, '')}"
                    )
                    print(f"WeasyPrint files: {os.listdir(weasyprint_path)}")
                else:
                    print(f"WeasyPrint NOT found in {path.replace(temp_dir, '')}")
        else:
            print("No Python site-packages directory found")

        # Check for library files
        print("\nChecking for library files:")
        lib_paths = []
        for root, dirs, files in os.walk(temp_dir):
            if os.path.basename(root) == "lib":
                lib_paths.append(root)

        if lib_paths:
            for path in lib_paths:
                print(f"Found lib directory: {path.replace(temp_dir, '')}")
                # List shared libraries
                so_files = [
                    f for f in os.listdir(path) if f.endswith(".so") or ".so." in f
                ]
                if so_files:
                    print(f"Shared libraries in {path.replace(temp_dir, '')}:")
                    for lib in so_files:
                        print(f"  - {lib}")
                else:
                    print(f"No shared libraries found in {path.replace(temp_dir, '')}")
        else:
            print("No lib directory found")

    return True


def main():
    """Main function"""
    if len(sys.argv) < 2:
        print("Usage: python check_layer_structure.py <path_to_layer.zip>")
        return 1

    zip_path = sys.argv[1]
    if analyze_zip_structure(zip_path):
        return 0
    return 1


if __name__ == "__main__":
    sys.exit(main())
