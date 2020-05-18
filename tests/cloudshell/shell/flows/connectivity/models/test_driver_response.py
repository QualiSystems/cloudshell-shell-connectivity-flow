from unittest import TestCase

from cloudshell.shell.flows.connectivity.models.driver_response import DriverResponse


class TestDriverResponse(TestCase):
    def test_driver_request(self):
        inst = DriverResponse()
        self.assertEqual([], inst.actionResults)
