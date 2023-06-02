from unittest import TestCase

from extensions.deployment.models.consent.consent import Consent


class ConsentTestCase(TestCase):
    def test_consent_bump_revision_from_empty(self):
        consent = Consent()
        consent.bump_revision()
        self.assertEqual(Consent.FIRST_VERSION, consent.revision)

    def test_consent_bump_revision(self):
        test_revision = 5
        consent = Consent()
        consent.bump_revision(test_revision)
        self.assertEqual(test_revision + 1, consent.revision)
