from unittest import TestCase
from unittest.mock import MagicMock

from sdk.common.adapter.event_bus_adapter import BaseEvent, EventBusAdapter


class TestEvent(BaseEvent):
    pass


class AnotherTestEvent(BaseEvent):
    pass


class TestException(Exception):
    pass


class EventBusAdapterTestCase(TestCase):
    def test_event_subscription(self):
        event_bus = EventBusAdapter()
        event_bus.subscribe(TestEvent, lambda x: x)

        self.assertIn(TestEvent, event_bus._handlers)

    def test_event_emit(self):
        test_func = MagicMock()
        event_bus = EventBusAdapter()
        event_bus.subscribe(TestEvent, test_func)

        event_bus.emit(TestEvent())

        test_func.assert_called_once()

    def test_event_emit_wrong_event_type(self):
        test_func = MagicMock()
        event_bus = EventBusAdapter()
        event_bus.subscribe(TestEvent, test_func)

        with self.assertRaises(Exception):
            event_bus.emit("test")

        test_func.assert_not_called()

    def test_event_raises_error(self):
        test_func = MagicMock()
        test_func.side_effect = TestException
        event_bus = EventBusAdapter()
        event_bus.subscribe(TestEvent, test_func)

        with self.assertRaises(TestException):
            event_bus.emit(TestEvent(), raise_error=True)

        test_func.assert_called_once()

    def test_event_mute_error(self):
        test_func = MagicMock()
        test_func.side_effect = TestException
        event_bus = EventBusAdapter()
        event_bus.subscribe(TestEvent, test_func)

        event_bus.emit(TestEvent(), raise_error=False)
        test_func.assert_called_once()

    def test_multiple_subscribers(self):
        test_func_one = MagicMock()
        test_func_two = MagicMock()
        test_func_three = MagicMock()

        event_bus = EventBusAdapter()

        event_bus.subscribe(TestEvent, test_func_one)
        event_bus.subscribe(TestEvent, test_func_two)
        event_bus.subscribe(TestEvent, test_func_three)

        event_bus.emit(TestEvent())

        test_func_one.assert_called_once()
        test_func_two.assert_called_once()
        test_func_three.assert_called_once()

    def test_multiple_subscribers_one_raises_error(self):
        test_func_one = MagicMock()
        test_func_two = MagicMock()
        test_func_two.side_effect = TestException
        test_func_three = MagicMock()

        event_bus = EventBusAdapter()

        event_bus.subscribe(TestEvent, test_func_one)
        event_bus.subscribe(TestEvent, test_func_two)
        event_bus.subscribe(TestEvent, test_func_three)

        with self.assertRaises(TestException):
            event_bus.emit(TestEvent(), raise_error=True)

        test_func_one.assert_called_once()
        test_func_two.assert_called_once()
        test_func_three.assert_not_called()

    def test_multiple_subscribers_one_raises_error_muted(self):
        test_func_one = MagicMock()
        test_func_two = MagicMock()
        test_func_two.side_effect = TestException
        test_func_three = MagicMock()

        event_bus = EventBusAdapter()

        event_bus.subscribe(TestEvent, test_func_one)
        event_bus.subscribe(TestEvent, test_func_two)
        event_bus.subscribe(TestEvent, test_func_three)

        event_bus.emit(TestEvent())

        test_func_one.assert_called_once()
        test_func_two.assert_called_once()
        test_func_three.assert_called_once()

    def test_has_subscribers_for(self):
        event_bus = EventBusAdapter()
        event_bus.subscribe(TestEvent, lambda x: x)

        self.assertTrue(event_bus.has_subscribers_for(TestEvent))
        self.assertFalse(event_bus.has_subscribers_for(AnotherTestEvent))
