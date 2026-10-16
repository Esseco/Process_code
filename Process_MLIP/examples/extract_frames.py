"""从仓库根目录运行：python -m Process_MLIP.examples.extract_frames"""
from pathlib import Path
from Process_MLIP import export_traj_frames

TRAJECTORY = Path("md_results/01_nvt/md.traj")
OUTPUT = Path("extracted_frames")
FRAMES = [0, 100, -1]  # 从 0 开始；-1 末帧；slice(0, None, 100) 每 100 帧；None 全部
FORMAT = "vasp"         # vasp / cif / xyz / extxyz / traj


def main():
    result = export_traj_frames(TRAJECTORY, OUTPUT, frames=FRAMES, format=FORMAT)
    for index, path in zip(result["frame_indices"], result["structure_files"]):
        print(f"Frame {index}: {path}")


if __name__ == "__main__":
    main()
