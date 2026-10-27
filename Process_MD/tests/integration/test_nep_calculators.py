from unittest.mock import Mock, patch

from process_md import create_nep_calculator


def test_nep_adapter_forwards_backend_options():
    expected = object()
    with patch("Process_MLIP.calculators.create_nep_calculator", return_value=expected) as factory:
        result = create_nep_calculator(
            "nep.txt", backend="gpu", gpumd_command="gpumd", directory="run"
        )
    assert result is expected
    factory.assert_called_once_with(
        "nep.txt", backend="gpu", gpumd_command="gpumd", directory="run"
    )
