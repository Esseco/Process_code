"""使用 ASE 从轨迹导出指定帧结构，不加载模型。"""
from numbers import Integral
from pathlib import Path

from ase.io import write
from ase.io.trajectory import Trajectory

def export_traj_frames(trajectory, output_dir=None, frames=-1, *, format="vasp", overwrite=False):
    """按保存帧索引导出结构，返回 frame_indices、structure_files 和 frame_count。

    frames: 整数/整数列表/slice；0 为首帧，-1 为末帧，None 为全部。
    output_dir=None: 输出到输入轨迹所在目录。
    format: vasp（默认）/ cif / xyz / extxyz / traj；文件名 frame_000000.格式。
    索引对应 MSD 的 frame_index，不一定是 MD 步号。负索引转为实际索引。
    原子顺序保持不变；不弛豫、不加载模型、不修改源轨迹，默认不覆盖文件。
    VASP 使用分数坐标；需完整晶胞。保留 ASE 动量等信息请用 traj。
    """
    if type(overwrite) is not bool:
        raise TypeError("overwrite must be bool")
    if format not in ("vasp", "cif", "xyz", "extxyz", "traj"):
        raise ValueError("format must be vasp, cif, xyz, extxyz or traj")
    source = Path(trajectory).resolve()
    root = source.parent if output_dir is None else Path(output_dir)
    if root.is_symlink() or (root.exists() and not root.is_dir()):
        raise FileExistsError(root)
    root = root.resolve()
    with Trajectory(str(source), "r") as reader:
        count = len(reader)
        if frames is None:
            requested = range(count)
        elif isinstance(frames, slice):
            requested = range(count)[frames]
        elif isinstance(frames, Integral) and not isinstance(frames, bool):
            requested = [frames]
        elif isinstance(frames, (list, tuple)):
            requested = frames
        else:
            raise TypeError("frames must be an integer, integer list/tuple, slice, or None")
        indices = []
        for index in requested:
            if isinstance(index, bool) or not isinstance(index, Integral):
                raise TypeError("Each frame index must be an integer")
            index = int(index)
            index = index + count if index < 0 else index
            if not 0 <= index < count:
                raise IndexError(f"Frame index outside trajectory with {count} frames")
            if index in indices:
                raise ValueError("Duplicate frame indices")
            indices.append(index)
        if not indices:
            raise ValueError("No frames selected")
        paths = [root / f"frame_{index:06d}.{format}" for index in indices]
        for path in paths:
            if path == source:
                raise ValueError("Cannot overwrite the input trajectory")
            if path.is_symlink() or path.is_dir() or (path.exists() and not overwrite):
                raise FileExistsError(path)
        images = [reader[index] for index in indices]
        if format in ("vasp", "cif") and any(image.cell.rank != 3 for image in images):
            raise ValueError(f"{format} export requires a complete 3D cell")
    root.mkdir(parents=True, exist_ok=True)
    for image, path in zip(images, paths):
        options = dict(direct=True, sort=False, vasp5=True) if format == "vasp" else {}
        write(str(path), image, format=format, **options)
    return dict(trajectory_file=str(source), frame_count=count, frame_indices=indices,
                structure_files=[str(path) for path in paths], format=format)
