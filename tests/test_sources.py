import json
import unittest

from jobbot.sources import common, greenhouse, lever
from tests.helpers import FIX


class Sources(unittest.TestCase):
    def test_greenhouse_parse_and_filter(self):
        data = json.loads((FIX / "greenhouse.json").read_text())
        jobs = greenhouse.fetch("acme", getter=lambda url: data)
        self.assertEqual(len(jobs), 2)
        self.assertEqual(jobs[0]["description"], "Work with VNA and antennas.")
        hits = [j for j in jobs if common.matches(j, ["rf"], exclude=["senior"])]
        self.assertEqual([j["title"] for j in hits], ["RF Student Engineer"])

    def test_greenhouse_board_name_is_url_quoted(self):
        seen = []
        greenhouse.fetch("a/../b", getter=lambda url: seen.append(url) or {"jobs": []})
        self.assertIn("a%2F..%2Fb", seen[0])

    def test_lever_parse(self):
        data = json.loads((FIX / "lever.json").read_text())
        jobs = lever.fetch("acme", getter=lambda url: data)
        self.assertEqual(jobs[0]["apply_url"], "https://example.com/lever/abc/apply")
        self.assertEqual(jobs[0]["employment"], "Part-time")
        self.assertEqual(jobs[0]["posted"], "2025-10-01")
        self.assertTrue(common.matches(jobs[0], ["rf"], ["ashdod"]))


class SearchRegions(unittest.TestCase):
    def test_search_uses_profile_regions_when_no_location_given(self):
        import contextlib
        import io
        import json as _json
        from unittest import mock

        from jobbot import cli
        data = _json.loads((FIX / "lever.json").read_text())
        prof = _json.loads((FIX / "profile.json").read_text())
        out = io.StringIO()
        with mock.patch.object(lever, "fetch", return_value=lever.parse("acme", data)), \
             mock.patch.object(cli, "load_profile", return_value={**prof, "preferences": {"regions": ["Haifa"]}}), \
             contextlib.redirect_stdout(out):
            cli.main(["search", "--lever", "acme", "--profile", "p.json"])
        self.assertEqual(_json.loads(out.getvalue()), [])
        out = io.StringIO()
        with mock.patch.object(lever, "fetch", return_value=lever.parse("acme", data)), \
             mock.patch.object(cli, "load_profile", return_value={**prof, "preferences": {"regions": ["Ashdod"]}}), \
             contextlib.redirect_stdout(out):
            cli.main(["search", "--lever", "acme", "--profile", "p.json"])
        self.assertEqual(len(_json.loads(out.getvalue())), 1)


if __name__ == "__main__":
    unittest.main()
