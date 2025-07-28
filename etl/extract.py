import os
from pathlib import Path
from dotenv import load_dotenv
import shutil
import pandas as pd
from datetime import datetime

load_dotenv()

LOCAL_INPUT_PATH = Path(os.getenv("LOCAL_INPUT_PATH"))
LOCAL_OUTPUT_PATH = Path(os.getenv("LOCAL_OUTPUT_PATH"))
INPUT_DIR = Path(os.getenv("INPUT_DIR"))
LOG_DIR = Path(os.getenv("LOG_DIR"))

FILE_MASK = os.getenv("FILE_MASK")
EXTRACT_LOGFILE = os.getenv("EXTRACT_LOGFILE")
REQUIRED_COLUMNS = [col.strip() for col in os.getenv("REQUIRED_COLUMNS").split(",")]
log_file = LOG_DIR / EXTRACT_LOGFILE

# create dirs if not exist
INPUT_DIR.mkdir(parents=True, exist_ok=True)
LOG_DIR.mkdir(parents=True, exist_ok=True)
LOCAL_OUTPUT_PATH.mkdir(parents=True, exist_ok=True)

def log_extract(original_filename, archive_filename, status, error, extract_date):
    header = "original_filename,archive_filename,status,error,extract_date\n"
    write_header = not log_file.exists() or log_file.stat().st_size == 0
    with open(log_file, "a", encoding="utf-8") as f:
        if write_header:
            f.write(header)
        error_str = "" if not error else str(error).replace(",", ";").replace("\n", " ")
        f.write(f"{original_filename},{archive_filename},{status},{error_str},{extract_date}\n")

def main():
    files = list(LOCAL_INPUT_PATH.glob(FILE_MASK))
    if not files:
        print("No files found for mask:", FILE_MASK)
        return

    for file in files:
        dt = datetime.now()
        extract_date = dt.strftime("%Y-%m-%d %H:%M:%S")
        postfix = dt.strftime("%Y%m%d")
        archive_name = file.name.replace('.csv', f'_{postfix}.csv')
        try:
            # header check
            df = pd.read_csv(file, nrows=1) 
            missing = [col for col in REQUIRED_COLUMNS if col not in df.columns]
            if missing:
                raise ValueError(f"Missing required columns: {', '.join(missing)}")

            # copy to input
            dest_file = INPUT_DIR / file.name
            shutil.copy2(file, dest_file)

            # move to archive
            archive_dest = LOCAL_OUTPUT_PATH / archive_name
            shutil.move(str(file), archive_dest)

            log_extract(file.name, archive_name, "success", None, extract_date)

        except Exception as e:
            log_extract(file.name, archive_name, "fail", e, extract_date)

if __name__ == "__main__":
    main()