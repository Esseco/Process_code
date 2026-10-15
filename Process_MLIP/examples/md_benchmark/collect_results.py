"""Collect completed benchmark throughput; never loads models or reruns MD."""
import csv
import json
import sys
from benchmark_config import OUTPUT_ROOT
from benchmark_runner import CASES

writer = csv.writer(sys.stdout)
writer.writerow(['case','status','steps','steps_per_second','device'])
for case in CASES:
    path = OUTPUT_ROOT / case / 'run_report.json'
    if not path.is_file():
        writer.writerow([case,'missing','','',''])
        continue
    report = json.loads(path.read_text(encoding='utf-8'))
    writer.writerow([case,report['status'],report.get('total_steps',''),
                     report.get('steps_per_second',''),report['model'].get('device','')])
