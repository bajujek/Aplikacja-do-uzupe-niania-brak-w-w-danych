import pandas as pd

def detect_csv_separator(file_path):
    with open(file_path, 'r', encoding='utf-8') as f:
        first_line = f.readline()
        if first_line.count(';') > first_line.count(','):
            return ';'
        else:
            return ','

def load_file(file_path):
    if file_path.endswith(".csv"):
        sep = detect_csv_separator(file_path)
        return pd.read_csv(file_path, sep=sep)
    else:
        return pd.read_excel(file_path)
