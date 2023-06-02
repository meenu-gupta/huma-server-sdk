import unittest

from extensions.appointment.models.appointment import Appointment
from sdk.common.utils.convertible import ConvertibleClassValidationError


class AppointmentToDictTestCase(unittest.TestCase):
    def test_failure_not_valid_object_id_manager_id(self):
        with self.assertRaises(ConvertibleClassValidationError):
            Appointment.from_dict({Appointment.MANAGER_ID: "ID"})

    def test_failure_not_valid_object_id_note_id(self):
        with self.assertRaises(ConvertibleClassValidationError):
            Appointment.from_dict({Appointment.NOTE_ID: "ID"})

    def test_failure_not_valid_object_id_call_id(self):
        with self.assertRaises(ConvertibleClassValidationError):
            Appointment.from_dict({Appointment.CALL_ID: "ID"})
