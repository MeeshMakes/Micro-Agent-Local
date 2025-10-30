import os

def analyze_folders(start_path):
    script_name = os.path.basename(__file__)  # Get the script file name
    analyze_file = os.path.join(start_path, "analyze.txt")  # Output file path

    with open(analyze_file, "w", encoding="utf-8") as file:
        file.write(f"Folder Analysis Report\n")
        file.write(f"{'='*50}\n\n")
        file.write(f"Root Directory: {start_path}\n\n")

        for root, dirs, files in os.walk(start_path):
            # Ensure only directories below the script's location are analyzed
            if not root.startswith(start_path):
                continue  # Skip any directory outside the scope

            level = root.replace(start_path, "").count(os.sep)
            indent = "|   " * level  # Tree structure formatting
            file.write(f"{indent}|-- {os.path.basename(root)}/\n")

            # Filter out the script and analyze.txt from files list
            filtered_files = [f for f in files if f not in {script_name, "analyze.txt"}]

            # List files in the directory
            for f in filtered_files:
                file_indent = "|   " * (level + 1)
                file_path = os.path.join(root, f)
                file.write(f"{file_indent}|-- {f}\n")

                # Capture file content
                try:
                    with open(file_path, "r", encoding="utf-8", errors="ignore") as f_content:
                        file_data = f_content.read()
                        file.write(f"\n{file_indent}    --- File Content ---\n")
                        file.write(f"{file_data}\n")
                        file.write(f"{file_indent}    -------------------\n\n")
                except Exception as e:
                    file.write(f"{file_indent}    [Error reading file: {str(e)}]\n\n")

    print(f"Analysis complete. Results saved in {analyze_file}")

if __name__ == "__main__":
    script_directory = os.path.abspath(os.path.dirname(__file__))  # Get the script's location
    analyze_folders(script_directory)  # Analyze only from script's directory downward
