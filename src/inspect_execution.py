import os
import sqlite3
import json

# Detect database path dynamically (Docker vs Windows Host)
db_path = '/root/.n8n/database.sqlite'
if not os.path.exists(db_path):
    local_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '../.n8n/.n8n/database.sqlite'))
    if os.path.exists(local_path):
        db_path = local_path
    else:
        db_path = '../.n8n/.n8n/database.sqlite'

conn = sqlite3.connect(db_path)
cursor = conn.cursor()

# Get the latest execution data
cursor.execute("SELECT executionId, data FROM execution_data ORDER BY executionId DESC LIMIT 1")
row = cursor.fetchone()
conn.close()

if not row:
    print("No execution data found.")
    exit(1)

exec_id, data_str = row
print(f"--- Execution ID: {exec_id} ---")

try:
    exec_data = json.loads(data_str)
    if isinstance(exec_data, list) and len(exec_data) > 0:
        exec_data = exec_data[0]
except Exception as e:
    print("Failed to parse execution JSON:", e)
    exit(1)

# Parse nested resultData if it is string-encoded JSON
result_data = exec_data.get("resultData", {})
if isinstance(result_data, str):
    try:
        result_data = json.loads(result_data)
    except:
        pass

run_data = result_data.get("runData", {}) if isinstance(result_data, dict) else {}

print("Executed Nodes:")
for node_name, runs in run_data.items():
    for i, run in enumerate(runs):
        output_data = run.get("data", {})
        # Output data itself might be string-encoded
        if isinstance(output_data, str):
            try: output_data = json.loads(output_data)
            except: pass
        main_outputs = output_data.get("main", []) if isinstance(output_data, dict) else []
        
        # Count total items in output
        item_count = 0
        if main_outputs and len(main_outputs) > 0:
            for output in main_outputs:
                if output:
                    item_count += len(output)
                    
        print(f"- {node_name} (Run {i+1}): {item_count} items output")
        if "error" in run:
            print(f"  [ERROR]: {run['error']}")
