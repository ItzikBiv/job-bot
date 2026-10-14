import unittest

from jobbot import truth
from tests.helpers import profile, tailoring


class TruthGate(unittest.TestCase):
    def check(self, t):
        return truth.validate(profile(), t)

    def test_faithful_tailoring_passes(self):
        errors, warnings = self.check(tailoring())
        self.assertEqual(errors, [])

    def test_invented_number_in_bullet_is_rejected(self):
        t = tailoring()
        t["experience"][0]["bullets"][1] = {"text": "Maintained 40 test setups.", "from": ["b-new-2"]}
        errors, _ = self.check(t)
        self.assertTrue(any("number '40'" in e for e in errors), errors)

    def test_invented_technology_is_rejected(self):
        t = tailoring()
        t["experience"][0]["bullets"][1] = {"text": "Maintained test setups in Python and FPGA.", "from": ["b-new-2"]}
        errors, _ = self.check(t)
        self.assertTrue(any("'python'" in e for e in errors), errors)
        self.assertTrue(any("'fpga'" in e for e in errors), errors)

    def test_invented_number_in_summary_is_rejected(self):
        t = tailoring(summary={"text": "EE student with 9 years of lab work.", "from": ["f-years"]})
        errors, _ = self.check(t)
        self.assertTrue(any("number '9'" in e for e in errors), errors)

    def test_free_text_without_sources_is_rejected(self):
        t = tailoring()
        t["experience"][0]["bullets"][1] = {"text": "Maintained test setups."}
        errors, _ = self.check(t)
        self.assertTrue(any("must cite" in e for e in errors), errors)

    def test_unknown_id_is_rejected(self):
        errors, _ = self.check(tailoring(skills=["s-rf", "s-made-up"]))
        self.assertTrue(any("unknown id 's-made-up'" in e for e in errors), errors)

    def test_bullet_moved_to_another_role_is_rejected(self):
        t = tailoring()
        t["experience"][1]["bullets"] = [{"ref": "b-new-1"}]
        errors, _ = self.check(t)
        self.assertTrue(any("belongs to 'x-new'" in e for e in errors), errors)

    def test_reordered_timeline_is_rejected(self):
        t = tailoring()
        t["experience"].reverse()
        errors, _ = self.check(t)
        self.assertTrue(any("chronological" in e for e in errors), errors)

    def test_unconfirmed_claim_and_gap_warn(self):
        t = tailoring(skills=["s-rf", "s-vna"])
        t["experience"] = t["experience"][:1]
        errors, warnings = self.check(t)
        self.assertEqual(errors, [])
        self.assertTrue(any("s-vna" in w for w in warnings), warnings)
        self.assertTrue(any("omitted x-old" in w for w in warnings), warnings)

    def test_cover_note_may_name_the_job_but_not_new_tech(self):
        t = tailoring()
        t["job"]["company"] = "Gizmo ASIC Labs"
        t["packet"]["cover_note"] = "I am applying to Gizmo ASIC Labs."
        errors, _ = self.check(t)
        self.assertEqual(errors, [])
        t["packet"]["cover_note"] = "I have strong Verilog experience."
        errors, _ = self.check(t)
        self.assertTrue(any("'verilog'" in e for e in errors), errors)

    def test_email_body_is_checked_and_cv_is_not_a_claim(self):
        t = tailoring()
        t["packet"]["email"] = {"to": "x@example.com", "subject": "Application", "body": "My CV is attached."}
        self.assertEqual(self.check(t)[0], [])
        t["packet"]["email"]["body"] = "I hold a PMP certification."
        errors, _ = self.check(t)
        self.assertTrue(any("packet.email.body" in e and "'pmp'" in e for e in errors), errors)

    def test_job_title_cannot_launder_claims(self):
        t = tailoring()
        t["job"]["title"] = "Senior Verilog FPGA Engineer"
        t["packet"]["cover_note"] = "I have 12 years of Verilog and FPGA experience."
        errors, _ = self.check(t)
        self.assertTrue(any("'verilog'" in e for e in errors), errors)
        t["packet"]["cover_note"] = "I am applying for the Senior Verilog FPGA Engineer role."
        self.assertEqual(self.check(t)[0], [])

    def test_number_words_and_credentials_are_claims(self):
        t = tailoring()
        t["experience"][0]["bullets"][1] = {"text": "Led twelve engineers; Ph.D. candidate.", "from": ["b-new-2"]}
        errors, _ = self.check(t)
        self.assertTrue(any("'twelve'" in e for e in errors), errors)
        self.assertTrue(any("'ph.d'" in e for e in errors), errors)

    def test_hebrew_script_technology_is_checked(self):
        t = tailoring(lang="he")
        t["experience"][0]["bullets"][1] = {"text": "פיתוח בפייתון ובוורילוג.", "from": ["b-new-2"]}
        errors, _ = self.check(t)
        self.assertTrue(errors, "Hebrew-script technology words must be checked")

    def test_term_must_come_from_cited_sources_not_whole_profile(self):
        t = tailoring()
        t["experience"][1]["bullets"] = [{"text": "Assembled cable harnesses and ran MATLAB analyses.", "from": ["b-old-1"]}]
        errors, _ = self.check(t)
        self.assertTrue(any("'matlab'" in e for e in errors), errors)

    def test_claim_resting_on_unconfirmed_item_warns(self):
        t = tailoring(summary={"text": "Hands-on VNA user.", "from": ["s-vna"]})
        errors, warnings = self.check(t)
        self.assertEqual(errors, [])
        self.assertTrue(any("not confirmed" in w for w in warnings), warnings)

    def test_ref_and_text_together_is_rejected(self):
        t = tailoring()
        t["experience"][0]["bullets"][0] = {"ref": "b-new-1", "text": "Invented things", "from": ["b-new-1"]}
        errors, _ = self.check(t)
        self.assertTrue(any("not both" in e for e in errors), errors)

    def test_everyday_words_are_not_tech_claims(self):
        t = tailoring(summary={"text": "Ready to go further in RF measurements.", "from": ["s-rf"]})
        self.assertEqual(self.check(t)[0], [])

    def test_missing_job_is_an_error_not_a_crash(self):
        t = tailoring()
        del t["job"]
        errors, _ = self.check(t)
        self.assertTrue(any("job:" in e for e in errors), errors)

    def test_hebrew_bullet_keeps_source_number(self):
        t = tailoring(lang="he", summary={"text": "סטודנטית עם 4 שנות עבודת מעבדה.", "from": ["f-years"]})
        errors, _ = self.check(t)
        self.assertEqual(errors, [])


if __name__ == "__main__":
    unittest.main()
