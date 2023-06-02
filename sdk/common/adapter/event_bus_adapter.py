import functools
import logging
import traceback
from abc import ABC
from collections import defaultdict
from typing import Union, Callable

from sdk.common.utils import inject

logger = logging.getLogger(__name__)


class BaseEvent(ABC):
    pass


class EventBusAdapter:
    def __init__(self):
        self._handlers = defaultdict(list)

    def subscribe(self, event: type, handler: Union[tuple[Callable], Callable]) -> None:
        if isinstance(handler, (tuple, list)):
            [self._subscribe(event, func) for func in handler]
        else:
            self._subscribe(event, handler)

    def _subscribe(self, event: type, handler: Callable) -> None:
        if not isinstance(event, type):
            raise Exception(
                f"subscribe() first argument must be a type, got '{type(event)}"
            )
        if not callable(handler):
            raise Exception(
                f"subscribe() second argument must be a callable, got '{type(handler)}"
            )
        self._handlers[event].append(handler)

    def emit(
        self, event: BaseEvent, raise_error: bool = False, async_: bool = False
    ) -> list:
        if not isinstance(event, BaseEvent):
            raise Exception("Can not emit event not of type BaseEvent")
        _cls = event.__class__
        if not self.has_subscribers_for(_cls):
            return []
        if async_:
            result = self._emit_async(event, raise_error)
        else:
            result = []
            for handler in self._get_handler_chain_for(_cls):
                try:
                    result.append(handler(event))
                except Exception as error:
                    logger.warning(
                        f"Event handler error for class {_cls}. Error: {error}.\n"
                        f"More details {traceback.format_exc()}"
                    )
                    if raise_error:
                        raise error
        return result

    def _emit_async(self, event: BaseEvent, raise_error: bool = False):
        raise NotImplementedError

    def has_subscribers_for(self, message_class):
        return message_class in self._handlers

    def _get_handler_chain_for(self, message_class: type):
        return self._handlers[message_class]


def emit_event(event_type: type):
    def wrapper(f):
        def _wrapper(*args, **kwargs):
            result = f(*args, **kwargs)
            event_bus = inject.instance(EventBusAdapter)
            event_bus.emit(event_type(result))
            return result

        return _wrapper

    return wrapper


def check_event_before_call(event: type):
    def wrapper(func: Callable):
        @functools.wraps(func)
        def inner_wrapper(*args, **kwargs):
            event_bus = inject.instance(EventBusAdapter)
            event_bus.emit(event(), raise_error=True)
            return func(*args, **kwargs)

        return inner_wrapper

    return wrapper
