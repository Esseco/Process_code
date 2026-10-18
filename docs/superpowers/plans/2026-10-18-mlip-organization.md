# Process_MLIP organization implementation plan

**Goal:** tests move to tests/, duplicate scaffolding/optimizer code is consolidated, public calls remain compatible.

**Architecture:** keep existing runtime module paths; consolidate public exports in __init__.py. Extract MD support into a private module shared by md/pre_relax/workflow. Model-specific single-structure adapters share MLIPRelaxer through a private result adapter. Ten test modules group behavior; a non-discoverable support module owns fixtures.

**Execution:** primary agent inline, using executing-plans; no model/environment changes, no forced worktree/commits or delegated review (user preferences).

## Constraints and review focus

- Preserve package exports, old module imports and Process_AL_MC compatibility, signatures, default units/seeds/step counts and output semantics.
- Keep pre-relax defaults separate from historical single-structure defaults (FIRE/0.05 vs LBFGS/ASE default); do not merge their scientific settings.
- Test discovery must execute each original test exactly once, without cross-imported TestCases.
- Temporary paths and example-relative paths must remain valid after tests move.
- Preserve unrelated VASP changes and user files; default py1; no dependencies or model loads.

## Tasks

- [x] Capture existing public signatures/test inventory and run baseline suite.
- [x] Move tests into tests/ and group model/relax/timing/example tests; extract NoStress/ZeroCalculator/temporary-directory and example fixtures. Retain original test methods except proven duplicate fixtures; eliminate test-to-test imports.
- [x] Extract _md_support.py and _relaxation.py; keep existing public modules/patchable aliases and consolidate __init__.py exports. Use one ASE optimization implementation without changing outputs/defaults.
- [x] Add API/architecture compatibility checks, document module responsibilities and test commands. Regenerate catalog without test symbols in the public API.
- [x] Run py1/py-mace suites, compare original test IDs/signatures, check model-free imports/example compilation and targeted diffs. Record evidence/limits.

## Verification ledger

- Baseline: 95 distinct tests, 14 public signatures. Final: all original methods retained once; 4 added checks; 10 test modules.
- py1: 99 tests OK (1 existing missing-full-MTK skip). Existing py-mace: 99 tests OK.
- AST audit: all MD/support function bodies identical after extraction; fixed/full-cell EMT old/new single-structure reports match at 1e-12.
- Public imports/defaults and Process_AL_MC compatibility preserved; fresh import does not import model libraries. Model/GPU performance and scientific accuracy not revalidated.
- User VASP changes preserved. No installed packages, weight files, cached results or desktop task scripts changed.
