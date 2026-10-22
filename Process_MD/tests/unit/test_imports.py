import subprocess
import sys


def test_package_import_does_not_load_optional_backends():
    subprocess.run([sys.executable, "-c",
                    "import process_md, sys; "
                    "assert 'torch' not in sys.modules; assert 'chgnet' not in sys.modules; "
                    "assert 'Process_MLIP' not in sys.modules; "
                    "assert 'pymatgen.analysis.diffusion.analyzer' not in sys.modules"],
                   check=True, capture_output=True, text=True)
