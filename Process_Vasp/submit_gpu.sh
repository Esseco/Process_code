#!/bin/bash
#SBATCH --job-name=test
#SBATCH -N 1
#SBATCH -n 2
#SBATCH --ntasks-per-node=2
#SBATCH --mem=64G
#SBATCH --gres=gpu:1
#SBATCH --partition=v100m3
#SBATCH --output=out
#SBATCH --error=err
export cuda_path="/data/app/cuda/cuda-12.8" 
export PATH=${cuda_path}/bin:$PATH
export LD_LIBRARY_PATH=${cuda_path}/lib64:$LD_LIBRARY_PATH
export CUDA_HOME=${cuda_path}:$CUDA_HOME

module load gcc/12.2.0
export vasp_path="/data/app/vasp/6.5.1-nvhpc"
module use /data/app/nvhpc/22.5_cuda12.9/modulefiles/
module load nvhpc-hpcx fftw/3.3.10-nvhpc
export PATH=${vasp_path}/bin:$PATH
ulimit -s unlimited
ulimit -l unlimited

source /data/app/anaconda3/2024.10-1/bin/activate
conda activate python
python3 workflow.py
