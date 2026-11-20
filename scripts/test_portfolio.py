"""Public-data and deployment-path checks for the portfolio builder."""

from html.parser import HTMLParser
import json
from pathlib import Path
import tempfile
import unittest
from urllib.parse import unquote, urlsplit

import build_portfolio as portfolio


class Links(HTMLParser):
    def __init__(self):
        super().__init__()
        self.links = []
        self.ids = set()
        self.control_targets = set()
        self.scripts = 0

    def handle_starttag(self, tag, attributes):
        attributes = dict(attributes)
        if tag == "script":
            self.scripts += 1
        if attributes.get("id"):
            self.ids.add(attributes["id"])
        if attributes.get("aria-controls"):
            self.control_targets.update(attributes["aria-controls"].split())
        for key in ("href", "src"):
            if attributes.get(key):
                self.links.append(attributes[key])


class Portfolio(unittest.TestCase):
    def test_private_records_and_html_in_metadata_are_not_published_as_markup(self):
        records = [
            {"name": "public-fixture", "owner": portfolio.OWNER, "private": False, "fork": False,
             "archived": False, "stars": 0, "language": "Python", "updated": "2026-11-17T00:00:00Z",
             "description": '<script>alert("metadata")</script>'},
            {"name": "private-fixture", "owner": portfolio.OWNER, "private": True},
            {"name": "other-owner", "owner": "someone-else", "private": False},
        ]
        snapshot = {"schema": 1, "owner": portfolio.OWNER, "captured_at": "2026-11-18T00:00:00Z",
                    "repositories": records, "research_commits": {}}
        with tempfile.TemporaryDirectory() as temporary:
            output = Path(temporary) / "site"
            portfolio.build_site(snapshot, output)
            html = (output / "index.html").read_text()
            published = json.loads((output / "assets/repositories.json").read_text())
        self.assertNotIn("private-fixture", html)
        self.assertNotIn("other-owner", html)
        self.assertEqual([repo["name"] for repo in published["repositories"]], ["public-fixture"])
        parsed = Links()
        parsed.feed(html)
        self.assertEqual(parsed.scripts, 1)  # the local app.js, never metadata
        self.assertIn("&lt;script&gt;", html)

    def test_feature_pages_and_local_links_work_below_a_project_subdirectory(self):
        snapshot = portfolio.read_json(portfolio.SNAPSHOT)
        with tempfile.TemporaryDirectory() as temporary:
            output = Path(temporary) / "billyrdavis1985-bot"
            result = portfolio.build_site(snapshot, output)
            self.assertEqual(result["featured"], 7)
            pages = list(output.rglob("*.html"))
            parsed = {}
            for path in pages:
                parser = Links()
                parser.feed(path.read_text())
                self.assertLessEqual(parser.control_targets, parser.ids, path)
                parsed[path.resolve()] = parser
            for path, parser in parsed.items():
                for link in parser.links:
                    url = urlsplit(link)
                    if url.scheme or url.netloc:
                        continue
                    target = (path.parent / unquote(url.path)).resolve() if url.path else path
                    if target.is_dir():
                        target /= "index.html"
                    self.assertTrue(target.is_relative_to(output.resolve()), (path, link))
                    self.assertTrue(target.is_file(), (path, link))
                    if url.fragment and target.suffix == ".html":
                        self.assertIn(url.fragment, parsed[target].ids, (path, link))

    def test_builder_refuses_to_replace_an_unowned_directory(self):
        with tempfile.TemporaryDirectory() as temporary:
            output = Path(temporary)
            sentinel = output / "README.md"
            sentinel.write_text("Existing project")
            with self.assertRaises(ValueError):
                portfolio.build_site(portfolio.read_json(portfolio.SNAPSHOT), output)
            self.assertEqual(sentinel.read_text(), "Existing project")


if __name__ == "__main__":
    unittest.main()
