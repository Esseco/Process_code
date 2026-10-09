"""Create a directory; no file deletion or movement."""
from pathlib import Path
from Process_folder.Handle_File import ensure_dir
OUTPUT_DIR = Path("E:/results/new_task")
def main():
    print(ensure_dir(OUTPUT_DIR))
if __name__ == "__main__":
    main()
