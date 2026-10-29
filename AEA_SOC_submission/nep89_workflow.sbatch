#!/bin/bash
#SBATCH --job-name=aea_nep89_wf
#SBATCH --partition=v100m3
#SBATCH --nodes=1
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=6
#SBATCH --gres=gpu:1
#SBATCH --mem=64G
#SBATCH --time=72:00:00
#SBATCH --output=/data/home/lichaoyue/26-7-AEA/MLIP_SOC_MD/jobs/nep89_workflow-%j.out
#SBATCH --error=/data/home/lichaoyue/26-7-AEA/MLIP_SOC_MD/jobs/nep89_workflow-%j.err
set -euo pipefail
export PYTHONPATH=/data/home/lichaoyue/Process_code/MD_Screening_Workflow:/data/home/lichaoyue/Process_code/Process_MD:/data/home/lichaoyue/Process_code:/data/home/lichaoyue/.conda/envs/mace_cueq/lib/python3.11/site-packages
export MLIP_MODEL_ID=nep89
export OMP_NUM_THREADS=2
export MKL_NUM_THREADS=2
module load gpumd/5.9.1-cuda129
exec /data/home/lichaoyue/.venvs/nep-speed/bin/python -u /data/home/lichaoyue/Process_code/AEA_SOC_submission/run_soc_workflow.py
