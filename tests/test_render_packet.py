import json
import tempfile
import unittest
from pathlib import Path

from jobbot import packet, render, review
from tests.helpers import profile, tailoring


class RenderAndPacket(unittest.TestCase):
    def test_html_is_escaped(self):
        t = tailoring()
        t["experience"][0]["bullets"][1] = {"text": "Maintained <script>alert(1)</script> test setups.", "from": ["b-new-2"]}
        html = render.render_html(profile(), t)
        self.assertNotIn("<script>alert", html)
        self.assertIn("&lt;script&gt;", html)

    def test_hebrew_is_rtl_and_english_ltr(self):
        self.assertIn('dir="rtl"', render.render_html(profile(), tailoring(lang="he", summary={})))
        self.assertIn('dir="ltr"', render.render_html(profile(), tailoring()))

    def test_hebrew_isolates_latin_runs_and_main_comes_first(self):
        t = tailoring(lang="he", summary={})
        t["experience"][0]["bullets"][1] = {"text": "תחזוקת עמדות בדיקה <b> RF", "from": ["b-new-2"]}
        html = render.render_html(profile(), t)
        self.assertIn('<span dir="ltr">RF</span>', html)
        self.assertNotIn("<b>", html.split("<body>")[1].split("<aside")[0])
        self.assertIn("&lt;", html)
        self.assertIn('<span dir="ltr">dana@example.com</span>', html)
        self.assertLess(html.index('<main class="main">'), html.index('<aside class="side">'))

    def test_review_page_drops_unsafe_links_and_sandboxes_preview(self):
        with tempfile.TemporaryDirectory() as d:
            t = tailoring(slug="../../escape")
            t["job"]["apply_url"] = "javascript:alert(1)"
            t["job"]["url"] = "data:text/html,hi"
            t["fit"] = {"score": None}
            folder, _ = packet.build(profile(), t, d, make_pdf=False)
            self.assertEqual(folder.parent, Path(d))
            page = review.build_page([folder], leads=[{"name": "x", "url": "javascript:alert(2)", "note": "n"}])
            self.assertNotIn("javascript:", page)
            self.assertNotIn('href="data:', page)
            self.assertIn('sandbox=""', page)

    def test_stale_pdf_is_removed_when_no_browser(self):
        import os
        with tempfile.TemporaryDirectory() as d:
            html = Path(d) / "cv.html"
            html.write_text("<p>x</p>")
            pdf = Path(d) / "cv.pdf"
            pdf.write_bytes(b"old")
            old = os.environ.get("PATH")
            os.environ["PATH"] = ""
            os.environ["JOBBOT_CHROMIUM"] = "/nonexistent"
            orig = render.find_chromium
            render.find_chromium = lambda: None
            try:
                self.assertFalse(render.render_pdf(html, pdf))
            finally:
                render.find_chromium = orig
                os.environ["PATH"] = old or ""
                os.environ.pop("JOBBOT_CHROMIUM")
            self.assertFalse(pdf.exists())

    def test_undated_education_has_no_date(self):
        prof = profile()
        prof["education"].append({"id": "e-lic", "title": {"en": "Licence", "he": "רישיון"}, "org": {"en": "Gov", "he": "ממשלה"},
                                  "start": None, "end": None, "note": None})
        html = render.render_html(prof, tailoring(education=["e-1", "e-lic"]))
        self.assertIn('<span class="title">Licence</span><span class="date"></span>', html)

    def test_hebrew_sentence_punctuation_stays_outside_latin_run(self):
        t = tailoring(lang="he", summary={"text": "מתכנת ב-Python ו-MATLAB. עובד עם B.Sc, VNA.", "from": ["s-matlab"]})
        html = render.render_html(profile(), t)
        self.assertIn('<span dir="ltr">MATLAB</span>. ', html)
        self.assertIn('<span dir="ltr">B.Sc, VNA</span>.', html)

    def test_hebrew_keeps_english_lists_in_one_run(self):
        t = tailoring(lang="he", summary={"text": "מכשור מעבדה (Scope, VNA), מטוסי C-130H, C-130J ו-Boeing 707.", "from": ["s-rf"]})
        html = render.render_html(profile(), t)
        self.assertIn('<span dir="ltr">Scope, VNA</span>)', html)
        self.assertIn('<span dir="ltr">C-130H, C-130J</span> ו-<span dir="ltr">Boeing 707</span>.', html)

    def test_download_name_is_person_and_job(self):
        self.assertEqual(packet.download_name(profile(), {"file_label": "KLA Yavne"}, "x"), "Dana_Example_CV_KLA_Yavne.pdf")
        self.assertEqual(packet.download_name(profile(), {}, "acme-rf-student"), "Dana_Example_CV_Acme_Rf_Student.pdf")

    def test_single_column_layout_has_no_sidebar(self):
        html = render.render_html(profile(), tailoring(layout="single"))
        self.assertNotIn('<aside class="side">', html)
        self.assertIn('class="contact-line"', html)
        self.assertIn("<b>Software:</b> MATLAB", html)
        self.assertLess(html.index("contact-line"), html.index('class="summary"'))

    def test_design_stats_tiles_and_emphasis(self):
        t = tailoring(design={"stats": ["st-years", "st-lines"], "emphasis": ["4 years of lab work"], "palette": "teal"})
        html = render.render_html(profile(), t)
        self.assertIn('<div class="n">12</div>', html)
        self.assertIn("<b>4 years of lab work</b>", html)
        self.assertIn("--accent:#0f8b8d", html)
        self.assertIn("repeat(2,1fr)", html)

    def test_design_defaults_keep_original_look(self):
        html = render.render_html(profile(), tailoring())
        self.assertNotIn('<div class="stats">', html)
        self.assertIn("--accent:#2f6bff", html)

    def test_skills_as_list(self):
        html = render.render_html(profile(), tailoring(design={"skills_style": "list"}))
        self.assertIn('class="skills-list"', html)
        self.assertNotIn('<span class="chip">', html)

    def test_minimal_theme_two_columns_and_fonts(self):
        html = render.render_html(profile(), tailoring(design={"theme": "minimal", "stats": ["st-years"]}))
        self.assertIn("@font-face{font-family:'Libre Bodoni'", html)
        self.assertIn('class="cols"', html)
        self.assertIn("Jan 2023 – Present", html)
        self.assertIn('<div class="n">4</div>', html)
        self.assertLess(html.index('class="right"'), html.index('class="left"'))
        self.assertNotIn("<script", html)

    def test_minimal_theme_single_and_hebrew(self):
        html = render.render_html(profile(), tailoring(lang="he", summary={}, layout="single", design={"theme": "minimal"}))
        self.assertIn('dir="rtl"', html)
        self.assertIn('class="page single"', html)
        self.assertNotIn('class="cols"', html)
        self.assertIn("01.2023", html)

    def test_dates_and_present(self):
        html = render.render_html(profile(), tailoring())
        self.assertIn("01.2023 – Present", html)
        self.assertIn("01.2020 – 12.2022", html)

    def test_rejected_tailoring_builds_nothing(self):
        t = tailoring(summary={"text": "Has 99 patents.", "from": ["f-years"]})
        with tempfile.TemporaryDirectory() as d:
            with self.assertRaises(packet.TailoringRejected):
                packet.build(profile(), t, d, make_pdf=False)
            self.assertEqual(list(Path(d).iterdir()), [])

    def test_packet_and_review_page(self):
        with tempfile.TemporaryDirectory() as d:
            folder, p = packet.build(profile(), tailoring(), d, make_pdf=False)
            saved = json.loads((folder / "packet.json").read_text(encoding="utf-8"))
            self.assertEqual(saved["fields"]["email"], "dana@example.com")
            self.assertTrue(any("Reworded" in c for c in saved["changes"]))
            page = review.build_page([folder], leads=[{"name": "Lead", "url": "https://example.com", "note": "check"}])
            self.assertTrue(page.startswith("<title>"))
            self.assertIn("srcdoc=", page)
            self.assertNotIn("<html", page.split("srcdoc=")[0])
            self.assertIn("Lead", page)


if __name__ == "__main__":
    unittest.main()
