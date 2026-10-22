import pytest
from ase.build import bulk


@pytest.fixture
def crystal():
    return bulk("LiF", "rocksalt", a=5.3, cubic=True)
