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


if __name__ == "__main__":
    unittest.main()
