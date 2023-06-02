from unittest.mock import MagicMock

from extensions.appointment.callbacks import get_appointment_badge


def test_get_appointment_badge():
    repo = MagicMock()
    repo.retrieve_pending_appointment_count.return_value = 3
    result = get_appointment_badge(MagicMock(), repo)
    assert "appointments" in result
    assert result["appointments"] == 3
