import os
import pandas as pd
from datetime import timedelta
from dotenv import load_dotenv
from pathlib import Path

load_dotenv()

INPUT_DIR = Path(os.getenv("INPUT_DIR"))
OUTPUT_DIR = Path(os.getenv("OUTPUT_DIR"))
LOG_DIR = Path(os.getenv("LOG_DIR"))
FILE_MASK = os.getenv("FILE_MASK")
REQUIRED_COLUMNS = [col.strip() for col in os.getenv("REQUIRED_COLUMNS").split(',')]
log_file = LOG_DIR / "transform.log"

# create dirs if not exist
INPUT_DIR.mkdir(parents=True, exist_ok=True)
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
LOG_DIR.mkdir(parents=True, exist_ok=True)

with open(log_file, "w") as f:
    f.write("original_filename,agg_filename,status,error\n")

    for filename in os.listdir(INPUT_DIR):
        if not filename.startswith(FILE_MASK.replace("*", "")):
            continue

        input_path = INPUT_DIR / filename
        try:
            df = pd.read_csv(input_path)

            # if all columns exist
            missing = [col for col in REQUIRED_COLUMNS if col not in df.columns]
            if missing:
                raise ValueError(f"Missing required columns: {', '.join(missing)}")

            # convert timestamp
            df['timestamp'] = pd.to_datetime(df['timestamp'], errors='coerce')
            df = df.dropna(subset=['timestamp'])

            # quantity and price in num, side to lower
            df['quantity'] = pd.to_numeric(df['quantity'], errors='coerce')
            df['price'] = pd.to_numeric(df['price'], errors='coerce')
            df = df.dropna(subset=['quantity', 'price', 'side'])
            df['side'] = df['side'].astype(str).str.lower()

            # pnl
            df['pnl'] = df.apply(
                lambda row: row['quantity'] * row['price'] * (1 if row['side'] == 'sell' else -1),
                axis=1
            )

            # create week_start_date monday with 00 time
            df['week_start_date'] = df['timestamp'].apply(lambda x: (x - timedelta(days=x.weekday())).normalize())

            # agg
            agg_df = df.groupby(
                ['week_start_date', 'client_type', 'user_id', 'symbol']
            ).agg(
                total_volume=('quantity', 'sum'),
                total_pnl=('pnl', 'sum'),
                trade_count=('symbol', 'count')
            ).reset_index()

            agg_filename = f"agg_{filename}"
            output_path = OUTPUT_DIR / agg_filename
            agg_df.to_csv(output_path, index=False)

            f.write(f"{filename},{agg_filename},success,\n")

        except Exception as e:
            agg_filename = f"agg_{filename}"
            error_msg = str(e).replace(",", ";").replace("\n", " ")
            f.write(f"{filename},{agg_filename},fail,{error_msg}\n")
