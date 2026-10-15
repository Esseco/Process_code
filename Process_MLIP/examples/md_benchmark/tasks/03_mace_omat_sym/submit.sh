#!/bin/bash
#SBATCH --job-name=03_mace_omat_sym
#SBATCH -N 1
#SBATCH -n 2
#SBATCH --ntasks-per-node=2
#SBATCH --mem=32G
#SBATCH --gres=gpu:1
#SBATCH --partition=v100m3
#SBATCH --output=out-%j
#SBATCH --error=err-%j

set -eo pipefail
cd "${SLURM_SUBMIT_DIR:-$(dirname "$(readlink -f "$0")")}"
export cuda_path="/data/app/cuda/cuda-12.8"
export PATH="${cuda_path}/bin:$PATH"
export LD_LIBRARY_PATH="${cuda_path}/lib64:${LD_LIBRARY_PATH:-}"
export CUDA_HOME="${cuda_path}"
export OMP_NUM_THREADS=2
export MKL_NUM_THREADS=2

source /data/app/anaconda3/2024.10-1/bin/activate
conda activate mace_cueq
# Python flags select the requested SevenNet backend; avoid environment overrides.
unset SEVENNET_ENABLE_CUEQ SEVENNET_ENABLE_OEQ SEVENNET_ENABLE_FLASH
python -u run_md.py
