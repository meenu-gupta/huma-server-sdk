import logging

from extensions.autocomplete.models.autocomplete_manager import (
    AutocompleteModulesManager,
)
from extensions.autocomplete.repository.autocomplete_repository import (
    AutoCompleteRepository,
)
from extensions.autocomplete.repository.mongo_autocomplete_repository import (
    MongoAutoCompleteRepository,
)

logger = logging.getLogger(__name__)


def bind_autocomplete_manager(binder):
    binder.bind(AutocompleteModulesManager, AutocompleteModulesManager())
    logger.debug(f"AutocompleteManager bind to AutocompleteManager")


def bind_autocomplete_repository(binder):
    binder.bind_to_provider(
        AutoCompleteRepository, lambda: MongoAutoCompleteRepository()
    )
    logger.debug(f"AutoCompleteRepository bind to MongoAutoCompleteRepository")
