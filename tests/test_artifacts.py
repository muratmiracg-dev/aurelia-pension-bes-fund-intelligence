"""Committed report artifacts must match a fresh build of the current code."""
import re
import shutil
import tempfile
import unittest
from pathlib import Path

from aurelia_pension.pipeline import build

REPO = Path(__file__).resolve().parent.parent

# Floating-point sums can differ in the last binary digit between NumPy builds
# (for example -0.047 vs -0.04699999999999999). Compare numbers at 10 significant
# digits so the check is portable across the CI matrix but still catches stale content.
_FLOAT = re.compile(r"-?\d+\.\d+(?:[eE][-+]?\d+)?")


def normalized(path: Path) -> str:
    text = path.read_text(encoding="utf-8")
    return _FLOAT.sub(lambda m: format(float(m.group()), ".10g"), text)


# The SQLite file is rebuilt with the same rows but is not byte-identical between
# runs, so it is excluded here.
TEXT_ARTIFACTS = (
    "Aurelia_Pension_BES_Dashboard.html",
    "dashboard_data.json",
    "data_quality.csv",
    "fund_metrics.csv",
    "manifest.json",
    "portfolio_metrics.csv",
)


class CommittedArtifactTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls._tmp = tempfile.TemporaryDirectory()
        cls.root = Path(cls._tmp.name)
        # The build reads its HTML/JS template and SQL views from the project root.
        for folder in ("web", "sql"):
            shutil.copytree(REPO / folder, cls.root / folder)
        build(cls.root)

    @classmethod
    def tearDownClass(cls):
        cls._tmp.cleanup()

    def test_demo_inputs_match_committed_inputs(self):
        for path in sorted((REPO / "data/demo").glob("*.csv")):
            with self.subTest(path=path.name):
                self.assertEqual(
                    (self.root / "data/demo" / path.name).read_bytes(),
                    path.read_bytes(),
                    f"data/demo/{path.name} is stale; run `python -m aurelia_pension build`",
                )

    def test_text_artifacts_match_fresh_build(self):
        for name in TEXT_ARTIFACTS:
            with self.subTest(artifact=name):
                self.assertEqual(
                    normalized(self.root / "artifacts" / name),
                    normalized(REPO / "artifacts" / name),
                    f"artifacts/{name} is stale; run `python -m aurelia_pension build` "
                    "and commit the regenerated artifacts",
                )


if __name__ == "__main__":
    unittest.main()
