import pandas as pd
import os
import time

TEST_FILE = "TEST_AUTOSAVE.csv"

def verify_autosave_logic():
    print(f"Testing autosave logic on {TEST_FILE}...")
    
    # 1. Cleanup previous test
    if os.path.exists(TEST_FILE):
        os.remove(TEST_FILE)
        
    # 2. Initialize File (App startup logic)
    print("Step 1: Initializing file...")
    pd.DataFrame(columns=["col1", "col2"]).to_csv(TEST_FILE, index=False)
    
    # 3. Simulate Loop (App loop logic)
    test_data = [
        {"col1": "Row 1", "col2": "Data A"},
        {"col1": "Row 2", "col2": "Data B"},
        {"col1": "Row 3", "col2": "Data C"},
    ]
    
    print("Step 2: Appending rows...")
    for i, data in enumerate(test_data):
        # The exact logic used in app.py
        pd.DataFrame([data])[["col1", "col2"]].to_csv(
            TEST_FILE, mode='a', header=False, index=False
        )
        print(f"  - Appended row {i+1}")
        
    # 4. Verify Content
    print("Step 3: Verifying content...")
    df_read = pd.read_csv(TEST_FILE)
    print("Read DataFrame:")
    print(df_read)
    
    if len(df_read) == 3 and df_read.iloc[2]['col2'] == "Data C":
        print("✅ SUCCESS: Autosave logic works as expected.")
    else:
        print("❌ FAILURE: Content mismatch.")

if __name__ == "__main__":
    verify_autosave_logic()
