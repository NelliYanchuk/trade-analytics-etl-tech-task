import os
import pandas as pd
from datetime import timedelta
from dotenv import load_dotenv
from pathlib import Path

load_dotenv()

INPUT_DIR = Path(os.getenv("INPUT_DIR"))
OUTPUT_DIR = Path(os.getenv("OUTPUT_DIR"))
LOG_DIR = Path(os.getenv("LOG_DIR"))

REQUIRED_COLUMNS = [col.strip() for col in os.getenv("REQUIRED_COLUMNS").split(',')]
TRANSFORM_LOGFILE = os.getenv("TRANSFORM_LOGFILE")
EXTRACT_LOGFILE = os.getenv("EXTRACT_LOGFILE")
log_file = LOG_DIR / TRANSFORM_LOGFILE

# create dirs if not exist
INPUT_DIR.mkdir(parents=True, exist_ok=True)
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
LOG_DIR.mkdir(parents=True, exist_ok=True)

# read extract log
extract_log_path = LOG_DIR / EXTRACT_LOGFILE

extract_log = pd.read_csv(extract_log_path)
files_to_process = extract_log[extract_log["status"] == "success"]["original_filename"].unique()

with open(log_file, "w", encoding="utf-8") as f:
    f.write("original_filename,agg_filename,status,error\n")

    for filename in files_to_process:
        input_path = INPUT_DIR / filename
        agg_filename = f"agg_{filename}"
        try:
            df = pd.read_csv(input_path)

            # check date, number, nan, side
            df['timestamp'] = pd.to_datetime(df['timestamp'], errors='coerce')
            df = df.dropna(subset=['timestamp'])

            df['quantity'] = pd.to_numeric(df['quantity'], errors='coerce')
            df['price'] = pd.to_numeric(df['price'], errors='coerce')
            df = df.dropna(subset=['quantity', 'price', 'side'])
            df['side'] = df['side'].astype(str).str.lower()

            df['pnl'] = df.apply(
                lambda row: row['quantity'] * row['price'] * (1 if row['side'] == 'sell' else -1),
                axis=1
            )

            # create monday
            df['week_start_date'] = df['timestamp'].apply(lambda x: (x - timedelta(days=x.weekday())).normalize())

            # agg
            agg_df = df.groupby(
                ['week_start_date', 'client_type', 'user_id', 'symbol']
            ).agg(
                total_volume=('quantity', 'sum'),
                total_pnl=('pnl', 'sum'),
                trade_count=('symbol', 'count')
            ).reset_index()

            output_path = OUTPUT_DIR / agg_filename
            agg_df.to_csv(output_path, index=False)

            f.write(f"{filename},{agg_filename},success,\n")

        except Exception as e:
            error_msg = str(e).replace(",", ";").replace("\n", " ")
            f.write(f"{filename},{agg_filename},fail,{error_msg}\n")