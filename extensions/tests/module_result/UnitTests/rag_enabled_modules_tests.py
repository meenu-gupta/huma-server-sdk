import unittest

from extensions.module_result.modules import rag_enabled_module_ids, default_modules


class RagEnabledModulesTestCase(unittest.TestCase):
    def test_retrieve_rag_enabled_module_ids(self):
        res = rag_enabled_module_ids
        for module in default_modules:
            if module.ragEnabled:
                self.assertIn(module.moduleId, res)


if __name__ == "__main__":
    unittest.main()
