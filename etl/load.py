import os
from pathlib import Path
from dotenv import load_dotenv
from datetime import datetime
import pandas as pd
import sqlite3
import sys

load_dotenv()

OUTPUT_DIR = Path(os.getenv("OUTPUT_DIR"))
LOG_DIR = Path(os.getenv("LOG_DIR"))
DB_DIR = Path(os.getenv("DB_DIR"))
DB = os.getenv("DB")
DB_PATH = Path(DB_DIR) / DB

LOAD_LOGFILE = os.getenv("LOAD_LOGFILE")
TRANSFORM_LOGFILE = os.getenv("TRANSFORM_LOGFILE")
TABLE = os.getenv("TABLE")
log_file = LOG_DIR / LOAD_LOGFILE

# create dirs if not exist
LOG_DIR.mkdir(parents=True, exist_ok=True)
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
Path(DB_DIR).mkdir(parents=True, exist_ok=True)

# logging fc
def log_error(agg_file, error, load_date):
    with open(log_file, "a", encoding="utf-8") as logf:
        logf.write(f"{agg_file},fail,{error},{load_date}\n")

# read transform log
log_df = pd.read_csv(LOG_DIR / TRANSFORM_LOGFILE)
success_files = log_df[log_df["status"]=="success"]

if success_files.empty:
    print("there is no data to load")
    sys.exit()

load_date = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

# connect to SQLite with error handling
try:
    con = sqlite3.connect(DB_PATH)
except Exception as e:
    print(f"DB connect error: {e}")
    for _, row in success_files.iterrows():
        agg_file = row["agg_filename"]
        log_error(agg_file, e, load_date)
    sys.exit()

# load each file
for _, row in success_files.iterrows():
    agg_file = row["agg_filename"]
    orig_file = row["original_filename"]
    csv_path = OUTPUT_DIR / agg_file

    if not csv_path.exists():
        print(f"cant find {csv_path}, skipping")
        log_error(agg_file, "file_not_found", load_date)
        continue

    try:
        df = pd.read_csv(csv_path)
        df["original_filename"] = orig_file
        df["agg_filename"] = agg_file
        df["load_date"] = load_date

        df.to_sql(TABLE, con, if_exists='append', index=False)
        
        # logging
        with open(log_file, "a", encoding="utf-8") as logf:
            logf.write(f"{agg_file},success,{load_date}\n")
    except Exception as e:
        log_error(agg_file, e, load_date)
        print(f"{agg_file} load fail with error: {e}")

con.close()