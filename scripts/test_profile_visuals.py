"""Checks for incomplete public data, pagination and private-data exclusion."""

from datetime import date
import unittest
from unittest.mock import patch
import xml.etree.ElementTree as ET

import render_contributions as calendar
import update_project_feed as feed


def cell(day, count=0, level=0):
    count_text = "No contributions" if count == 0 else f"{count:,} contributions"
    return (f'<td data-date="{day}" data-level="{level}" id="day-{day}"></td>'
            f'<tool-tip for="day-{day}">{count_text} on November 17th.</tool-tip>')


class CalendarIntegrity(unittest.TestCase):
    def test_counts_come_from_tooltips_not_activity_levels(self):
        html = cell("2026-11-16") + cell("2026-11-17", 1234, 4)
        days = calendar.parse_calendar(html, date(2026, 11, 16), date(2026, 11, 17))
        self.assertEqual([day.count for day in days], [0, 1234])

    def test_missing_or_malformed_days_fail_instead_of_showing_zero(self):
        for html in (cell("2026-11-16"), cell("2026-11-16") + cell("2026-11-17", 10, 0),
                     cell("2026-11-16") + '<td data-date="2026-11-17" data-level="1" id="unknown"></td>'):
            with self.subTest(html=html), self.assertRaises(ValueError):
                calendar.parse_calendar(html, date(2026, 11, 16), date(2026, 11, 17))

    def test_zero_activity_and_reduced_motion_render(self):
        days = [calendar.Day("2026-11-17", 0, 0)]
        for animated in (True, False):
            svg = calendar.render_skyline(days, date(2026, 11, 17), animated)
            ET.fromstring(svg)
            self.assertNotIn("<script", svg)
            self.assertEqual("@keyframes" in svg, animated)
        self.assertIn("prefers-reduced-motion", calendar.render_skyline(days, "2026-11-17", True))


class RepositoryInventory(unittest.TestCase):
    def test_paginated_inventory_separates_forks_and_excludes_nonpublic_repositories(self):
        def repo(name, **changes):
            value = dict(name=name, private=False, owner={"login": feed.OWNER}, language=None,
                         stargazers_count=0, fork=False, archived=False)
            value.update(changes)
            return value
        first = [repo(f"public-{n}") for n in range(100)]
        second = [repo("a-fork", fork=True), repo("archived", archived=True),
                  repo("secret-project", private=True), repo("internal", visibility="internal"),
                  repo("someone-elses", owner={"login": "another-owner"})]
        with patch.object(feed, "github_json", side_effect=[first, second]) as api:
            stats = feed.public_repository_stats()
        self.assertEqual(len(stats), 102)
        self.assertIn("page=2", api.call_args_list[1].args[0])
        markdown = feed.render_markdown([], stats, "2026-11-17")
        for hidden in ("secret-project", "internal", "someone-elses"):
            self.assertNotIn(hidden, markdown)
        self.assertIn("101 originals", markdown)
        self.assertIn("1 forks", markdown)
        self.assertIn("Unspecified", markdown)
        self.assertTrue(next(item for item in stats if item.repository == "archived").archived)

    def test_fork_stars_do_not_inflate_original_project_total(self):
        stats = [feed.RepositoryStats("original", "Python", 2, False, False),
                 feed.RepositoryStats("fork", "HTML", 999, True, False)]
        svg = feed.render_stats_card(stats, "2026-11-17")
        ET.fromstring(svg)
        self.assertIn("2 stars on originals", svg)
        self.assertNotIn("999", svg)
        self.assertNotIn("HTML", svg)


if __name__ == "__main__":
    unittest.main()
