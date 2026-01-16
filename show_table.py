import pandas as pd
import os

file_path = "TRANSLATION_RESULTS_V2.csv"
if os.path.exists(file_path):
    try:
        df = pd.read_csv(file_path)
        # Display first 20 rows
        with open("table_output_utf8.txt", "w", encoding="utf-8") as f:
            f.write(df.head(20).to_markdown(index=False))
            f.write(f"\n... (Total rows: {len(df)})")
        print("Table saved to table_output_utf8.txt")
    except Exception as e:
        print(f"Error reading CSV: {e}")
else:
    print("File not found.")
