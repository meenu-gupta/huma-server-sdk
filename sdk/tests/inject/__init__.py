from unittest import TestCase

from sdk.common.utils import inject


class BaseTestInject(TestCase):
    def tearDown(self):
        inject.clear()
