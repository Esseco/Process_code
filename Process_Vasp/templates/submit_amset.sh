#!/bin/bash
#SBATCH --job-name=amset_post
#SBATCH --nodes=1
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=2
#SBATCH --mem=32G
#SBATCH --partition=v100m3
#SBATCH --output=amset-%j.out
#SBATCH --error=amset-%j.err

set -euo pipefail
cd "${SLURM_SUBMIT_DIR:-$(dirname "$0")}"
# Partition copied from the existing task. Set an available CPU partition if needed.
# AMSET uses CPUs; no VASP, CUDA or GPU modules are needed.
source /data/app/anaconda3/2024.10-1/bin/activate
conda activate python
command -v amset >/dev/null || { echo "Activate an environment with AMSET installed." >&2; exit 1; }
export OMP_NUM_THREADS=1
export OPENBLAS_NUM_THREADS=1
export MKL_NUM_THREADS=1
python postprocess.py
