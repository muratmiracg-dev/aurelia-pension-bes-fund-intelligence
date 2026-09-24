"""CLI contract: read-only validation and safe handling of explicit input."""
import contextlib
import hashlib
import io
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from aurelia_pension.__main__ import main
from aurelia_pension.data import generate


class CommandTests(unittest.TestCase):
    def test_validation_does_not_write_or_rebuild(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            data = root / "data/demo"
            generate(data)
            def snapshot():
                return {str(p.relative_to(root)): hashlib.sha256(p.read_bytes()).hexdigest()
                        for p in root.rglob("*") if p.is_file()}
            before = snapshot()
            output = io.StringIO()
            with contextlib.redirect_stdout(output):
                main(["validate", "--root", str(root), "--json"])
            result = json.loads(output.getvalue())
            self.assertEqual(result["status"], "PASS")
            self.assertEqual(result["price_observations"], 36900)
            self.assertEqual(result["checks_passed"], 10)
            self.assertEqual(before, snapshot())
            self.assertFalse((root / "artifacts").exists())

    def test_missing_input_has_machine_readable_failure(self):
        with tempfile.TemporaryDirectory() as directory:
            output = io.StringIO()
            with contextlib.redirect_stdout(output), self.assertRaises(SystemExit) as error:
                main(["validate", "--data-dir", directory, "--json"])
            self.assertEqual(error.exception.code, 2)
            result = json.loads(output.getvalue())
            self.assertEqual(result["status"], "FAIL")
            self.assertIn("funds.csv", result["error"])

    def test_explicit_invalid_data_never_serves_existing_report(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "artifacts").mkdir()
            report = root / "artifacts/Aurelia_Pension_BES_Dashboard.html"
            report.write_text("old snapshot", encoding="utf-8")
            with patch("aurelia_pension.__main__.http.server.ThreadingHTTPServer") as server:
                with contextlib.redirect_stderr(io.StringIO()), self.assertRaises(SystemExit) as error:
                    main(["serve", "--root", str(root), "--data-dir", str(root / "missing")])
                self.assertEqual(error.exception.code, 2)
                server.assert_not_called()
            self.assertEqual(report.read_text(encoding="utf-8"), "old snapshot")


if __name__ == "__main__":
    unittest.main()
