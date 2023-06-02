import unittest

from extensions.identity_verification.models.identity_verification_log import (
    VerificationLog,
    Document,
)


class VerificationLogTestCase(unittest.TestCase):
    def test_success_verification_log_documents_creation(self):
        documents = ["603df5fc65e41764f9fe5345", "603df5fc65e41764f9fe5346"]
        verification_log = VerificationLog.from_dict(
            {VerificationLog.DOCUMENTS: documents}
        )
        log_documents = verification_log.documents
        for document in log_documents:
            self.assertTrue(isinstance(document, Document))
            self.assertIsNotNone(document.id)
            self.assertIsNotNone(document.isActive)


if __name__ == "__main__":
    unittest.main()
