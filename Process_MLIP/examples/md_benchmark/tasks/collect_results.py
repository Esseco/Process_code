"""Summarize eight task reports; does not run any calculations."""
import csv
import json
from pathlib import Path
import sys

writer = csv.writer(sys.stdout)
writer.writerow(['case', 'structure', 'status', 'steps', 'steps_per_second', 'msd_csv'])
for folder in sorted(Path(__file__).resolve().parent.glob('[0-9][0-9]_*')):
    for structure in ('LCO', 'NVP'):
        report_path = folder / 'results' / structure / 'run_report.json'
        msd = report_path.parent / 'msd.csv'
        if not report_path.is_file():
            writer.writerow([folder.name, structure, 'not_run', '', '', ''])
            continue
        report = json.loads(report_path.read_text(encoding='utf-8'))
        writer.writerow([folder.name, structure, report['status'], report.get('total_steps', ''),
                         report.get('steps_per_second', ''), str(msd) if msd.is_file() else ''])
