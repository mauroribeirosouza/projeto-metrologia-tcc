#!/usr/bin/env python3
import csv
import os
import sys
from pathlib import Path

def check_csv_file(file_path):
    """Check if all rows in a CSV file have the same number of columns as the header."""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            # Read first few lines to detect dialect
            sample = f.read(1024)
            f.seek(0)
            
            # Try to detect the dialect
            try:
                dialect = csv.Sniffer().sniff(sample)
            except csv.Error:
                dialect = 'excel'  # Default to standard CSV
            
            reader = csv.reader(f, dialect)
            
            # Read header
            try:
                header = next(reader)
                expected_columns = len(header)
                
                print(f"\nChecking {file_path}")
                print(f"Header has {expected_columns} columns: {', '.join(header)}")
                
                for line_num, row in enumerate(reader, start=2):
                    actual_columns = len(row)
                    if actual_columns != expected_columns:
                        print(f"ERROR: Line {line_num} has {actual_columns} columns (expected {expected_columns})")
                        print(f"Line content: {row}")
                        return False
                    
                    # Check for empty or whitespace-only fields
                    for col_num, field in enumerate(row):
                        if not field.strip():
                            print(f"WARNING: Empty field at line {line_num}, column {col_num + 1} (header: {header[col_num]})")
                
                print("✓ All rows have correct number of columns")
                return True
                
            except StopIteration:
                print(f"WARNING: File {file_path} is empty")
                return True
                
    except Exception as e:
        print(f"ERROR processing {file_path}: {str(e)}")
        return False

def main():
    """Find and check all CSV files in the project."""
    module_path = Path('addons/metrology_management')
    csv_files = []
    
    # Find all .csv files
    for root, dirs, files in os.walk(module_path):
        for file in files:
            if file.endswith('.csv'):
                csv_files.append(Path(root) / file)
    
    if not csv_files:
        print("No CSV files found in the module")
        return
    
    print(f"Found {len(csv_files)} CSV files to check")
    
    all_valid = True
    for csv_file in csv_files:
        if not check_csv_file(csv_file):
            all_valid = False
    
    if all_valid:
        print("\n✓ All CSV files are valid!")
        sys.exit(0)
    else:
        print("\n✗ Some CSV files have problems!")
        sys.exit(1)

if __name__ == '__main__':
    main()