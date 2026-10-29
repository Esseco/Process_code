#!/bin/bash
#SBATCH --job-name=aea_orbv3_wf
#SBATCH --partition=v100m3
#SBATCH --nodes=1
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=6
#SBATCH --gres=gpu:1
#SBATCH --mem=64G
#SBATCH --time=72:00:00
#SBATCH --output=/data/home/lichaoyue/26-7-AEA/MLIP_SOC_MD/jobs/orbv3_workflow-%j.out
#SBATCH --error=/data/home/lichaoyue/26-7-AEA/MLIP_SOC_MD/jobs/orbv3_workflow-%j.err
set -euo pipefail
export PYTHONPATH=/data/home/lichaoyue/Process_code/MD_Screening_Workflow:/data/home/lichaoyue/Process_code/Process_MD:/data/home/lichaoyue/Process_code
export MLIP_MODEL_ID=orbv3_direct
export OMP_NUM_THREADS=2
export MKL_NUM_THREADS=2
module load cuda/12.8
exec /data/home/lichaoyue/.conda/envs/python/bin/python -u /data/home/lichaoyue/26-7-AEA/MLIP_SOC_MD/run_soc_workflow.py
