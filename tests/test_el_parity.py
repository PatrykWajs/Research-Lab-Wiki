# -*- coding: utf-8 -*-
"""unittest wrapper: one test per EN/EL page pair plus the hub.

python3 -m unittest tests.test_el_parity -v            (all pages)
RLW_PAGE=ginger python3 -m unittest tests.test_el_parity  (one page: the Sunday deploy gate)
"""
import os
import unittest

try:
    from . import el_parity as P
except ImportError:  # run as a plain script from tests/
    import el_parity as P


class ElParity(unittest.TestCase):
    pass


def _make(slug, el_name):
    def test(self):
        fails = P.check_pair(slug, el_name)
        self.assertFalse(fails, "\n".join(f"{c}: {m}" for c, m in fails))
    return test


_only = os.environ.get("RLW_PAGE")
for _slug, _el in sorted(P.page_map().items()):
    if _only and _slug != _only:
        continue
    setattr(ElParity, f"test_{_slug.replace('-', '_')}", _make(_slug, _el))


class Hub(unittest.TestCase):
    def test_hub_cards(self):
        fails = P.check_hub()
        self.assertFalse(fails, "\n".join(f"{c}: {m}" for c, m in fails))


if __name__ == "__main__":
    unittest.main()
