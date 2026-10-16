from pathlib import Path
import re

desktop=Path('C:/Users/Esseco/Desktop/1/2')
root=Path('Process_MLIP/examples/sym_md_scan')
root.mkdir(exist_ok=True)
template=(desktop/'03_mace_omat_sym'/'run_md.py').read_text(encoding='utf-8-sig')
submit=(desktop/'03_mace_omat_sym'/'submit.sh').read_text(encoding='utf-8-sig')
cases=[(500,30),(700,30),(900,30),(700,10),(700,50),(700,70)]
for temperature,duration in cases:
    name=f'sym_{temperature}K_{duration}ps'
    folder=root/name
    folder.mkdir(exist_ok=True)
    text=template.replace('Full relaxation -> 5000-step NVT -> MSD. Edit paths/parameters below.',
                          f'OMat+Symmetrix: FIRE all relaxation -> {temperature} K / {duration} ps NVT -> MSD.')
    text=text.replace('MD = dict(ensemble="nvt", temperature_K=600, steps=5000,',
                      f'TEMPERATURE_K = {temperature}\nDURATION_PS = {duration}\nTIMESTEP_FS = 2.0\nMD = dict(ensemble="nvt", temperature_K=TEMPERATURE_K,\n'
                      '          steps=int(DURATION_PS * 1000 / TIMESTEP_FS), timestep_fs=TIMESTEP_FS,')
    compile(text,str(folder/'run_md.py'),'exec')
    (folder/'run_md.py').write_text(text,encoding='utf-8',newline='\n')
    shell=submit.replace('--job-name=03_mace_omat_sym',f'--job-name={name}')
    shell=shell.replace('# Python flags select the requested SevenNet backend; avoid environment overrides.\n','')
    shell=shell.replace('unset SEVENNET_ENABLE_CUEQ SEVENNET_ENABLE_OEQ SEVENNET_ENABLE_FLASH\n','')
    (folder/'submit.sh').write_text(shell,encoding='utf-8',newline='\n')
    (folder/'README.md').write_text(f'# {name}\n\n每个结构先 FIRE 全弛豫，再运行 {temperature} K、{duration} ps NVT（2 fs，{duration*500} 步），最后导出 MSD。\n从上级读取 LCO.vasp / NVP.vasp，分别统计 Li / Na。\n结果在本文件夹 results/LCO/ 和 results/NVP/。检查 run_md.py 路径后执行 sbatch submit.sh，使用 mace_cueq 环境。\n',encoding='utf-8')
print('Generated 6 unique cases, 12 structure trajectories')
