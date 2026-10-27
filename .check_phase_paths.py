from pathlib import Path
import tempfile
for p in [Path(r'E:\0-PhaseDiagram\NaCoO2-phase'),Path(r'E:\0-PhaseDiagram\NaNiO2-phase'),Path(r'E:\0-PhaseDiagram')]:
 print('\n',p)
 try:
  with tempfile.NamedTemporaryFile(prefix='.writecheck-',dir=p,delete=False) as f: name=Path(f.name)
  name.unlink()
  print('writable=True')
 except Exception as e: print('writable=False',type(e).__name__,str(e))
