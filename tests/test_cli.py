from __future__ import annotations

import io
import json
from contextlib import redirect_stdout
import unittest

from chaser.cli import main


class CLITests(unittest.TestCase):
    def test_cli_list(self) -> None:
        buf = io.StringIO()
        with redirect_stdout(buf):
            code = main(["list"])
        self.assertEqual(code, 0)
        output = buf.getvalue()
        self.assertIn("red_goal", output)
        self.assertIn("dual_chaser", output)

    def test_cli_simulate_default(self) -> None:
        buf = io.StringIO()
        with redirect_stdout(buf):
            code = main(["simulate"])
        self.assertEqual(code, 0)
        data = json.loads(buf.getvalue())
        self.assertEqual(data["outcome"], "blue_intercepted")

    def test_cli_simulate_dual_chaser(self) -> None:
        buf = io.StringIO()
        with redirect_stdout(buf):
            code = main(["simulate", "--scenario", "dual_chaser"])
        self.assertEqual(code, 0)
        data = json.loads(buf.getvalue())
        self.assertIn(data["outcome"], {"blue_1_intercepted", "blue_2_intercepted"})

    def test_cli_compare(self) -> None:
        buf = io.StringIO()
        with redirect_stdout(buf):
            code = main(["compare"])
        self.assertEqual(code, 0)
        data = json.loads(buf.getvalue())
        self.assertEqual(data["total_positions_tested"], 5)


if __name__ == "__main__":
    unittest.main()
