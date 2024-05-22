import os
import re
import csv
from typing import List, Tuple

def find_files(directory: str, extensions: List[str], exclude_dirs: List[str]) -> List[str]:
    """Recursively find all files in a directory with specified extensions, excluding specified directories."""
    print(f"Searching for files in directory: {directory}")
    matched_files = []
    for root, dirs, files in os.walk(directory):
        # Exclude specified directories
        dirs[:] = [d for d in dirs if d not in exclude_dirs]
        for file in files:
            if any(file.endswith(ext) for ext in extensions):
                matched_files.append(os.path.join(root, file))
    print(f"Found {len(matched_files)} files with extensions {extensions}")
    return matched_files

def extract_ids_and_labels(file_path: str) -> List[Tuple[str, str, str]]:
    """Extract all id and label pairs from a given file."""
    print(f"Extracting id and label pairs from file: {file_path}")
    id_pattern = re.compile(r"id:\s*'([^']+)'")
    label_pattern = re.compile(r"label:\s*'([^']+)'")
    
    matches = []
    with open(file_path, 'r', encoding='utf-8') as file:
        content = file.read()
        ids = id_pattern.findall(content)
        labels = label_pattern.findall(content)
        
        id_label_pairs = []
        label_index = 0
        for id in ids:
            if label_index < len(labels):
                id_label_pairs.append((id, labels[label_index]))
                label_index += 1
            else:
                id_label_pairs.append((id, 'none'))
                
        matches = [(id, label, file_path) for id, label in id_label_pairs]
    
    print(f"Found {len(matches)} id-label pairs in file: {file_path}")
    return matches

def write_to_csv(data: List[Tuple[str, str, str]], output_path: str):
    """Write extracted data to a CSV file."""
    print(f"Writing data to CSV file: {output_path}")
    with open(output_path, 'w', newline='', encoding='utf-8') as csvfile:
        writer = csv.writer(csvfile)
        writer.writerow(['ID', 'Label', 'Path'])
        writer.writerows(data)
    print(f"Total count of id-label pairs: {len(data)}")

def main():
    directory = r'D:\Make-Print-Dev\jsketcher'
    output_path = r'D:\Make-Print-Dev\jsketcher\skunkworks\actions.csv'
    extensions = ['.js', '.ts']
    exclude_dirs = ['node_modules', 'dist']  # Add directories you want to exclude
    
    print("Starting the file search and extraction process...")
    
    all_matches = []
    files = find_files(directory, extensions, exclude_dirs)
    
    for file in files:
        matches = extract_ids_and_labels(file)
        all_matches.extend(matches)
    
    write_to_csv(all_matches, output_path)
    
    print("Process completed successfully.")

if __name__ == "__main__":
    main()
