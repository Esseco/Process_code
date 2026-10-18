"""Scientific validation must not depend on unused restart artifacts."""
import hashlib
import json
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

import pytest
from pymatgen.core import Lattice, Structure
from Process_Vasp.workflows import atomate_runner as runner


def outputs(root, *, converged=True):
    root.mkdir(parents=True,exist_ok=True)
    structure=Structure(Lattice.cubic(4),['Si'],[[0,0,0]])
    for name in ['vasprun.xml','OUTCAR','CONTCAR']:
        (root/name).write_text('fake verified output')
    parsed=SimpleNamespace(converged_electronic=converged,converged_ionic=True,
                           parameters={'NSW':0},final_structure=structure)
    return structure,parsed


def test_static_without_unused_wave_or_charge_passes(tmp_path):
    structure,parsed=outputs(tmp_path)
    with patch('pymatgen.io.vasp.outputs.Vasprun',return_value=parsed):
        assert runner._validate(tmp_path,'static')==structure
    assert not (tmp_path/'WAVECAR').exists() and not (tmp_path/'CHGCAR').exists()


@pytest.mark.parametrize('defect',['unconverged','missing_outcar','wrong_nsw'])
def test_static_scientific_failures_still_rejected(tmp_path,defect):
    _,parsed=outputs(tmp_path,converged=defect!='unconverged')
    if defect=='missing_outcar':(tmp_path/'OUTCAR').unlink()
    if defect=='wrong_nsw':parsed.parameters['NSW']=99
    with patch('pymatgen.io.vasp.outputs.Vasprun',return_value=parsed):
        with pytest.raises(ValueError):runner._validate(tmp_path,'static')


@pytest.mark.parametrize('stage',['dos','band'])
def test_properties_check_charge_before_new_job(tmp_path,stage):
    structure,_=outputs(tmp_path)
    with patch('atomate2.vasp.jobs.core.NonSCFMaker') as maker:
        with pytest.raises(ValueError,match='CHGCAR'):
            runner._job(stage,structure,tmp_path,{})
        maker.assert_not_called()


def test_failed_checkpoint_with_valid_static_reused_without_any_execution(tmp_path):
    directory=tmp_path/'runs/static/attempt_001'
    structure,parsed=outputs(directory)
    structure.to(filename=tmp_path/'initial.vasp',fmt='poscar')
    config={'calculation':'static','structure_file':'initial.vasp',
            'incar_settings':{'static':{'LWAVE':False}},'kpoints_settings':{}}
    (tmp_path/'workflow.json').write_text(json.dumps(config))
    dependency=hashlib.sha256((tmp_path/'initial.vasp').read_bytes()).hexdigest()
    fingerprint=hashlib.sha256(json.dumps({'runner_version':1,'dependency':dependency,
        'stage':'static','incar':config['incar_settings']['static'],'kpoints':{}},sort_keys=True).encode()).hexdigest()
    (tmp_path/'workflow_state.json').write_text(json.dumps({'version':1,'stages':{'static':{
        'status':'failed','directory':'runs/static/attempt_001','fingerprint':fingerprint,
        'attempt':1,'error':'Static output needs WAVECAR for subsequent calculations'}}}))
    before=(directory/'vasprun.xml').read_bytes()
    with patch('pymatgen.io.vasp.outputs.Vasprun',return_value=parsed), \
         patch('jobflow.run_locally',side_effect=AssertionError('must not run VASP')), \
         patch.object(runner,'_job',side_effect=AssertionError('must not prepare VASP')):
        state=runner.run_workflow(tmp_path)
    assert state['stages']['static']['status']=='completed'
    assert state['stages']['static']['attempt']==1
    assert 'error' not in state['stages']['static']
    assert 'WAVECAR' in state['stages']['static']['validation_recovery']['error']
    assert not (tmp_path/'runs/static/attempt_002').exists()
    assert (directory/'vasprun.xml').read_bytes()==before


@pytest.mark.parametrize('project',['O3-1ele-NaCoO2','O3-1ele-NaCrO2','O3-2ele-NaFeMn'])
def test_actual_project_plain_static_contract(tmp_path,project):
    from atomate2.vasp.sets.core import StaticSetGenerator
    from phase_agent.science.dft.prepare_pycode_relax import prepare_pycode_relax
    root=Path('E:/0-PhaseDiagram')/project
    if not (root/'workflow_state/state.json').is_file():
        pytest.skip('read-only actual project fixture unavailable')
    state=json.loads((root/'workflow_state/state.json').read_text(encoding='utf-8'))
    ledger=json.loads((root/'workflow_state/ledgers/phase_data.json').read_text(encoding='utf-8'))
    sid,record=next((sid,r) for sid,r in ledger['structures'].items() if Path(r.get('source_path','')).is_file())
    received={}
    def generator(directory,source,**kwargs):
        directory.mkdir()
        received.update(kwargs)
        (directory/'workflow.py').write_text('pass')
    task={'stage':'dft_single_point','structure_id':sid,'work_directory':str(tmp_path/'input'),
          'parameters':state['confirmed_config']['dft'].get('parameters') or {}}
    prepare_pycode_relax(task,manager=SimpleNamespace(data=ledger),generator=generator)
    geometry=Structure.from_file(record['source_path'])
    incar=StaticSetGenerator(user_incar_settings=received['incar_settings']['static']).get_input_set(geometry,potcar_spec=True)['INCAR']
    assert incar['LWAVE'] is False
    assert incar['NSW']==0 and incar['IBRION']==-1
    _,parsed=outputs(tmp_path/'result')
    parsed.final_structure=geometry
    with patch('pymatgen.io.vasp.outputs.Vasprun',return_value=parsed):
        assert runner._validate(tmp_path/'result','static')==geometry
