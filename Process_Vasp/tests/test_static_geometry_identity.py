import hashlib
import json
from copy import deepcopy
from unittest.mock import patch
import pytest
from pymatgen.core import Structure,Lattice
from Process_Vasp.workflows import atomate_runner as runner


def test_geometry_ignores_site_metadata_and_periodic_wrapping():
    initial=Structure(Lattice.cubic(4),['Na','O'],[[0,0,0],[.5,.5,.5]])
    final=deepcopy(initial)
    final.add_site_property('magmom',[.6,.6])
    final.translate_sites([0],[1,0,0],to_unit_cell=False)
    assert initial != final
    assert runner._same_structure(initial,final)


@pytest.mark.parametrize('change',['motion','lattice','species','order'])
def test_geometry_rejects_actual_change(change):
    left=Structure(Lattice.cubic(4),['Na','O'],[[0,0,0],[.5,.5,.5]])
    right=deepcopy(left)
    if change=='motion':right.translate_sites([0],[.02,0,0])
    elif change=='lattice':right.scale_lattice(66)
    elif change=='species':right.replace(0,'Li')
    else:right=Structure(left.lattice,['O','Na'],[[.5,.5,.5],[0,0,0]])
    assert not runner._same_structure(left,right)


def test_existing_static_with_output_properties_reused_without_execution(tmp_path):
    initial=Structure(Lattice.cubic(4),['Na','O'],[[0,0,0],[.5,.5,.5]])
    initial.to(filename=tmp_path/'initial.vasp',fmt='poscar')
    config={'calculation':'static','structure_file':'initial.vasp','incar_settings':{'static':{}},'kpoints_settings':{},'resume_from':{'static':'runs/static/attempt_001'}}
    (tmp_path/'workflow.json').write_text(json.dumps(config))
    dependency=hashlib.sha256((tmp_path/'initial.vasp').read_bytes()).hexdigest()
    fingerprint=hashlib.sha256(json.dumps({'runner_version':1,'dependency':dependency,'stage':'static','incar':{},'kpoints':{}},sort_keys=True).encode()).hexdigest()
    folder=tmp_path/'runs/static/attempt_001'
    folder.mkdir(parents=True)
    (folder/'vasprun.xml').write_text('validated parser is mocked')
    (tmp_path/'workflow_state.json').write_text(json.dumps({'version':1,'stages':{'static':{'status':'failed','directory':'runs/static/attempt_001','fingerprint':'different','attempt':1,'error':'static unexpectedly changed the structure'}}}))
    final=deepcopy(initial)
    final.add_site_property('magmom',[.6,.6])
    with patch.object(runner,'_validate',return_value=final),patch.object(runner,'_job',side_effect=AssertionError('VASP must not be generated')),patch('jobflow.run_locally',side_effect=AssertionError('VASP must not run')):
        result=runner.run_workflow(tmp_path)
    assert result['stages']['static']['status']=='completed'
    assert result['stages']['static']['imported'] is True
