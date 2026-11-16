"""Prevent publishing stale or incomplete build payloads."""

from pathlib import Path
import tempfile
import unittest

from tools.check_dist import check_checkout_payload


class PackagingTests(unittest.TestCase):
    def test_release_payload_must_match_all_checkout_modules(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "terminal_cells").mkdir()
            (root / "cells.py").write_bytes(b"entry point\n")
            (root / "terminal_cells" / "interaction.py").write_bytes(b"new footer\n")
            payload = {
                "cells.py": b"entry point\n",
                "terminal_cells/interaction.py": b"new footer\n",
            }
            check_checkout_payload(root, payload)
            for broken in (
                payload | {"terminal_cells/interaction.py": b"old toolbar\n"},
                {"cells.py": b"entry point\n"},
                payload | {"terminal_cells/deleted.py": b"obsolete module\n"},
            ):
                with self.subTest(files=tuple(broken)):
                    with self.assertRaisesRegex(ValueError, "rebuild before release"):
                        check_checkout_payload(root, broken)


if __name__ == "__main__":
    unittest.main()
