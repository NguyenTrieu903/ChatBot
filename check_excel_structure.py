import pandas as pd
from pathlib import Path

# Check traning.xlsx
excel1 = Path("data/traning.xlsx")
if excel1.exists():
    print("=== traning.xlsx ===")
    df1 = pd.read_excel(excel1)
    print(f"Columns: {df1.columns.tolist()}")
    print(f"Shape: {df1.shape}")
    print("\nFirst few rows:")
    print(df1.head())
    print("\n")
else:
    print(f"File not found: {excel1}")

# Check traning_new.xlsx
excel2 = Path("data/traning_new.xlsx")
if excel2.exists():
    print("=== traning_new.xlsx ===")
    df2 = pd.read_excel(excel2)
    print(f"Columns: {df2.columns.tolist()}")
    print(f"Shape: {df2.shape}")
    print("\nFirst few rows:")
    print(df2.head())
else:
    print(f"File not found: {excel2}")


