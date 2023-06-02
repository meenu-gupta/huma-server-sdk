import unittest

from extensions.common.exceptions import InvalidIdentityReportNameException
from extensions.deployment.boarding.consent_module import ConsentModule
from extensions.deployment.boarding.econsent_module import EConsentModule
from extensions.deployment.boarding.helper_agreement_module import HelperAgreementModule
from extensions.identity_verification.models.identity_verification import (
    OnfidoReportNameType,
)
from extensions.identity_verification.modules import IdentityVerificationModule
from extensions.module_result.boarding.az_screening_module import AZPScreeningModule
from sdk.common.exceptions.exceptions import InvalidModuleConfigBody


class EconsentModuleTestCase(unittest.TestCase):
    def test_success_validate_config_body(self):
        config_body = {}
        res = EConsentModule.validate_config_body(config_body)
        self.assertIsNone(res)

    def test_failure_not_empty_body(self):
        config_body = {"a": 1}
        with self.assertRaises(InvalidModuleConfigBody):
            EConsentModule.validate_config_body(config_body)


class ConsentModuleTestCase(unittest.TestCase):
    def test_success_validate_config_body(self):
        config_body = {}
        res = ConsentModule.validate_config_body(config_body)
        self.assertIsNone(res)

    def test_failure_not_empty_body(self):
        config_body = {"a": 1}
        with self.assertRaises(InvalidModuleConfigBody):
            ConsentModule.validate_config_body(config_body)


class IdentityVerificationModuleTestCase(unittest.TestCase):
    def test_success_validate_config_body(self):
        config_body = {
            IdentityVerificationModule.REQUIRED_REPORTS: [
                OnfidoReportNameType.DOCUMENT.value
            ]
        }
        res = IdentityVerificationModule.validate_config_body(config_body)
        self.assertIsNone(res)

    def test_failure_validate_config_body_with_invalid_data(self):
        config_body = {IdentityVerificationModule.REQUIRED_REPORTS: ["invalid one"]}
        with self.assertRaises(InvalidIdentityReportNameException):
            IdentityVerificationModule.validate_config_body(config_body)

    def test_success_validate_config_body_with_no_require_reports(self):
        config_body = {"aa": "aa"}
        res = IdentityVerificationModule.validate_config_body(config_body)
        self.assertIsNone(res)


class AZScreeningModuleTestCase(unittest.TestCase):
    def test_success_validate_config_body(self):
        config_body = {}
        res = AZPScreeningModule.validate_config_body(config_body)
        self.assertIsNone(res)

    def test_failure_not_empty_body(self):
        config_body = {"a": 1}
        with self.assertRaises(InvalidModuleConfigBody):
            AZPScreeningModule.validate_config_body(config_body)


class HelperAgreementModuleTestCase(unittest.TestCase):
    def test_success_validate_config_body(self):
        config_body = {}
        res = HelperAgreementModule.validate_config_body(config_body)
        self.assertIsNone(res)

    def test_failure_not_empty_body(self):
        config_body = {"a": 1}
        with self.assertRaises(InvalidModuleConfigBody):
            HelperAgreementModule.validate_config_body(config_body)


if __name__ == "__main__":
    unittest.main()
