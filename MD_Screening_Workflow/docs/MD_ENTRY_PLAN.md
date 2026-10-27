# Direct MD entry and readable outputs

## User requirements
- Caller supplies the supercell: direct entry does not expand atoms or cell.
- Reuse cell LBFGS relaxation, 5 ps precheck, 10 ps production checks, max 200 ps.
- Keep mandatory full-site reference and existing scientific stopping rules.
- GPU MACE-OMat / Symmetrix; 2 fs integration and 20 fs saved frames.
- One editable script, reusable Python API, clear final results and progress log.
- Preserve existing detailed run/trajectory/check paths and no-overwrite behavior.

## Design
Add md_screening/presets.py (screening_preset), runner.py (run_md facade),
and reporting.py (human output index, progress log and concise results).
ScreeningConfig accepts target_atoms=None; its legacy default stays 200.
New preset uses target_atoms=None and GPU Symmetrix.
run_md resolves paths/model and mobile species, then calls run_screening once.
run_md.py keeps only input paths, editable parameters, argument parsing and printing.
Core run_screening writes additional outputs so existing callers benefit too:
README.md, parameters.json, run.log, results/summary.json, results/summary.csv.
After MD, results/ also contains final_structure.extxyz and the latest msd.csv.
Detailed prepared/, relaxation/, md/, checks/, run.json and summary.csv stay in place.
Summary keeps unresolved estimates null and separates run status from transport status.
No duplicate trajectory, new integrator, automatic heating, or fake restart.

## Execution
- [x] Allow target_atoms=None; add direct preset and facade with lightweight imports.
- [x] Add progress/result outputs for success, early stop and failure.
- [x] Simplify script and document inputs, outputs and package structure.
- [x] Test atom/cell preservation, model/species resolution, no-overwrite, summaries,
  unresolved/precheck-only results and exceptions. Run short ASE MD, not long MLIP.
- [x] Run tools/verify.py --package; clean temporary artifacts; report limits.

Routine design and implementation are preauthorized by the user's AGENTS preferences.
Existing VASP conversion work is unrelated and must be preserved.

## Verification (2026-10-23)
- py1 tools/verify.py --package: 151 passed, 1 skipped (GEMDAT absent in py1).
- Dedicated analysis environment: native GEMDAT integration test passed (1).
- Disposable wheels/import and installed short ASE MD demo passed; temporary directories removed.
- Added coverage for caller cell/atom preservation, script import modes, missing reference,
  unknown transport, per-run directory uniqueness and failure-safe final export.
- One read-only review identified the standalone installed-import case; fallback/test added.
- No new MLIP/GPU run, no model/environment changes, no job submission or Git push.
