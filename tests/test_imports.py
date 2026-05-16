import unittest
from langguard import LangGuardPipeline

class TestImports(unittest.TestCase):
    def test_pipeline_import(self):
        """Test that the main pipeline class can be imported."""
        self.assertIsNotNone(LangGuardPipeline)

    def test_package_version(self):
        """Test that we can access metadata (if we add it later)."""
        pass

if __name__ == '__main__':
    unittest.main()
