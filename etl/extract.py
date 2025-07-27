import os
from pathlib import Path
from dotenv import load_dotenv
import shutil
from datetime import datetime

# load env vars
load_dotenv()

LOCAL_INPUT_PATH = Path(os.getenv("LOCAL_INPUT_PATH"))
LOCAL_OUTPUT_PATH = Path(os.getenv("LOCAL_OUTPUT_PATH"))
INPUT_DIR = Path(os.getenv("INPUT_DIR"))
LOG_DIR = Path(os.getenv("LOG_DIR"))

FILE_MASK = os.getenv("FILE_MASK")
POSTFIX = datetime.now().strftime("%Y%m%d")
EXTRACT_LOGFILE = os.getenv("EXTRACT_LOGFILE")
log_file = LOG_DIR / EXTRACT_LOGFILE

# create dirs if not exist
INPUT_DIR.mkdir(parents=True, exist_ok=True)
LOG_DIR.mkdir(parents=True, exist_ok=True)
LOCAL_OUTPUT_PATH.mkdir(parents=True, exist_ok=True)

def log_extract(filename, new_filename):
    if not log_file.exists() or log_file.stat().st_size == 0:
        with open(log_file, "w", encoding="utf-8") as f:
            f.write("original_filename,archive_filename\n")
    with open(log_file, "a", encoding="utf-8") as f:
        f.write(f"{filename},{new_filename}\n")

def main():
    files = list(LOCAL_INPUT_PATH.glob(FILE_MASK))
    if not files:
        print("No files found for mask:", FILE_MASK)
        return

    for file in files:
        # Copy to INPUT_DIR
        dest_file = INPUT_DIR / file.name
        shutil.copy2(file, dest_file)

        # Move original to archive with postfix
        archive_name = file.name.replace('.csv', f'_{POSTFIX}.csv')
        archive_dest = LOCAL_OUTPUT_PATH / archive_name

        shutil.move(str(file), archive_dest)

        # Log
        log_extract(file.name, archive_name)

if __name__ == "__main__":
    main()