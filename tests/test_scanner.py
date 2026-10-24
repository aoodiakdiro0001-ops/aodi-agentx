"""Aodı-AgentX — unit tests (stdlib unittest، بلا تبعيات وبدون أي وصول شبكة)."""
import sys, unittest
from pathlib import Path

CORE = Path(__file__).resolve().parent.parent / "core"
sys.path.insert(0, str(CORE))

import scanner  # noqa: E402


class ScannerTests(unittest.TestCase):
    def test_detects_hardcoded_secret(self):
        p = Path("/tmp/") / "ax_t1.py"
        p.write_text('password = "VerySecret1234"\n', encoding="utf-8")
        out = scanner.scan_file(p, "t1.py")
        self.assertTrue(any(f.rule == "AX-S01" for f in out))

    def test_detects_eval_and_sql(self):
        p = Path("/tmp/") / "ax_t2.py"
        p.write_text('eval(input())\ncursor.execute(f"SELECT {x}")\n', encoding="utf-8")
        rules = {f.rule for f in scanner.scan_file(p, "t2.py")}
        self.assertIn("AX-S02", rules)
        self.assertIn("AX-S05", rules)

    def test_clean_file_no_findings(self):
        p = Path("/tmp/") / "ax_t3.py"
        p.write_text("x = 1 + 2\nprint(sum([1, 2, 3]))\n", encoding="utf-8")
        self.assertEqual([], scanner.scan_file(p, "t3.py"))

    def test_rule_count(self):
        self.assertEqual(len(scanner.RULES), 10)
        self.assertEqual(len(scanner.RULES_BY_ID), 10)

    def test_detects_sql_fstring_and_cors_and_dom(self):
        p = Path("/tmp/") / "ax_t4.py"
        p.write_text(
            'query = f"SELECT * FROM users WHERE id = {uid}"\n'
            'resp["Access-Control-Allow-Origin"] = "*"\n', encoding="utf-8")
        rules = {f.rule for f in scanner.scan_file(p, "t4.py")}
        self.assertIn("AX-S05", rules)
        self.assertIn("AX-S09", rules)


class ConfigTests(unittest.TestCase):
    def test_paths_exist_dir(self):
        import config
        self.assertTrue(config.HOME.exists())
        self.assertIn("aodix", str(config.HOME).lower())


if __name__ == "__main__":
    unittest.main(verbosity=2)
