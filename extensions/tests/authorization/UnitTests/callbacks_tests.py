from unittest.mock import MagicMock

from extensions.authorization.callbacks import get_unread_messages_badge
from extensions.export_deployment.callbacks import get_async_export_badges


def test_get_messages_badge():
    repo = MagicMock()
    repo.retrieve_user_unread_messages_count.return_value = 5
    result = get_unread_messages_badge(MagicMock(), repo)
    assert "messages" in result
    assert result["messages"] == 5


def test_get_downloads_badge():
    repo = MagicMock()
    repo.retrieve_unseen_export_process_count.return_value = 3
    result = get_async_export_badges(MagicMock(), repo)
    assert "downloads" in result
    assert result["downloads"] == 3
