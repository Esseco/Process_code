"""Summarize eight task reports; does not run any calculations."""
import csv
import json
from pathlib import Path
import sys

writer = csv.writer(sys.stdout)
writer.writerow(['case', 'status', 'steps', 'steps_per_second', 'msd_csv'])
for folder in sorted(Path(__file__).resolve().parent.glob('[0-9][0-9]_*')):
    report_path = folder / 'results' / 'run_report.json'
    msd = folder / 'results' / 'msd.csv'
    if not report_path.is_file():
        writer.writerow([folder.name, 'not_run', '', '', ''])
        continue
    report = json.loads(report_path.read_text(encoding='utf-8'))
    writer.writerow([folder.name, report['status'], report.get('total_steps', ''),
                     report.get('steps_per_second', ''), str(msd) if msd.is_file() else ''])
