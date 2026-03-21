import asyncio
import unittest

from analyzers.onpage_seo import analyze_onpage
from analyzers.semantic_seo import analyze_semantic
from analyzers.technical_seo import analyze_technical
from analyzers.ux_signals import analyze_ux


FIXTURE_PAGES = [
    {
        "url": "https://example.com/",
        "title": "Example Home",
        "meta_description": "Example description for homepage",
        "canonical": "https://example.com/",
        "h1": ["Example Home"],
        "images": [{"src": "https://example.com/a.jpg", "alt": "image", "has_alt": True}],
        "internal_links": ["https://example.com/about"],
        "schema_markup": ["Organization"],
        "text_content": "Example Brand offers SEO and digital marketing solutions. Learn more today.",
        "word_count": 80,
        "response_time_ms": 120,
        "status_code": 200,
        "is_https": True,
        "redirect_chain": ["https://example.com/"],
        "viewport": True,
        "has_nav": True,
        "has_list": True,
        "has_table": False,
        "paragraphs": 5,
    },
    {
        "url": "https://example.com/about",
        "title": "",
        "meta_description": "",
        "canonical": "",
        "h1": [],
        "images": [{"src": "https://example.com/b.jpg", "alt": "", "has_alt": False}],
        "internal_links": [],
        "schema_markup": [],
        "text_content": "About Example Brand? Contact us for support.",
        "word_count": 20,
        "response_time_ms": 640,
        "status_code": 404,
        "is_https": True,
        "redirect_chain": ["https://example.com/old", "https://example.com/mid", "https://example.com/new", "https://example.com/about"],
        "viewport": False,
        "has_nav": False,
        "has_list": False,
        "has_table": False,
        "paragraphs": 1,
    },
]


class AnalyzerTests(unittest.TestCase):
    def test_analyzers_return_scores(self):
        technical = asyncio.run(analyze_technical(FIXTURE_PAGES, "https://example.com", {"robots_found": True, "sitemap_found": True, "sitemap_urls": []}))
        onpage = asyncio.run(analyze_onpage(FIXTURE_PAGES))
        semantic = asyncio.run(analyze_semantic(FIXTURE_PAGES))
        ux = asyncio.run(analyze_ux(FIXTURE_PAGES))

        self.assertIn("score", technical)
        self.assertIn("score", onpage)
        self.assertIn("score", semantic)
        self.assertIn("score", ux)

        self.assertGreaterEqual(technical["score"], 0)
        self.assertLessEqual(technical["score"], 100)


if __name__ == "__main__":
    unittest.main()
