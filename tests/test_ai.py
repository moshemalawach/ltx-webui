import unittest
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch

from fastapi import HTTPException
from starlette.requests import Request

import app


class AICoWriterTests(unittest.TestCase):
    def test_index_is_not_cached(self):
        response = app.index()
        self.assertEqual(response.headers["cache-control"], "no-store")

    def test_application_state_combines_startup_data(self):
        response = app.Response()
        snapshot = app.application_state(response)
        self.assertEqual(set(snapshot), {"jobs", "gallery", "keyframes", "ai"})
        self.assertEqual(response.headers["cache-control"], "no-store")

    def test_preview_range_is_capped(self):
        with patch.object(app, "PREVIEW_CHUNK_BYTES", 4):
            self.assertEqual(app.preview_range("bytes=2-", 20), (2, 5))
            self.assertEqual(app.preview_range("bytes=-3", 20), (17, 19))

    def test_preview_response_returns_only_the_capped_range(self):
        with TemporaryDirectory() as directory:
            output = Path(directory)
            (output / "clip.mp4").write_bytes(b"0123456789")
            request = Request({
                "type": "http",
                "method": "GET",
                "path": "/preview/clip.mp4",
                "headers": [(b"range", b"bytes=2-")],
                "query_string": b"",
                "server": ("test", 80),
                "client": ("test", 1234),
                "scheme": "http",
            })
            with patch.object(app, "OUTPUTS", output), \
                    patch.object(app, "PREVIEW_CHUNK_BYTES", 4):
                response = app.preview_video("clip.mp4", request)
        self.assertEqual(response.status_code, 206)
        self.assertEqual(response.body, b"2345")
        self.assertEqual(response.headers["content-range"], "bytes 2-5/10")

    def test_model_json_accepts_fenced_json(self):
        self.assertEqual(
            app._model_json('```json\n{"script":"hello"}\n```'),
            {"script": "hello"},
        )

    def test_missing_key_fails_before_network_access(self):
        with patch.object(app, "LIBERTAI_API_KEY", ""):
            with self.assertRaises(HTTPException) as raised:
                app._libertai_chat("system", "user", 100)
        self.assertEqual(raised.exception.status_code, 503)

    def test_campaign_result_is_allowlisted_and_bounded(self):
        request = app.AIWriteRequest(
            product_name="Sola",
            product_type="Face serum",
            duration_seconds=8,
        )
        model_result = {
            "product_name": "Sola",
            "concept": "routine",
            "hook": "proof",
            "script": "A concise spoken script.",
            "unknown": "must not escape",
            "notes": ["Audience inferred from product type."],
        }
        with patch.object(app, "_run_ai", return_value=model_result):
            result = app.ai_write(request)
        self.assertEqual(result["model"], app.LIBERTAI_MODEL)
        self.assertEqual(result["fields"]["concept"], "routine")
        self.assertNotIn("unknown", result["fields"])

    def test_prompt_refinement_preserves_variant_count(self):
        request = app.AIImproveRequest(
            product_name="Sola",
            product_type="Face serum",
            base_prompts=["A valid base render prompt for variant one."],
        )
        refined = "A coherent continuous smartphone UGC take with natural speech."
        with patch.object(app, "_run_ai", return_value={"prompts": [refined]}):
            result = app.ai_improve_prompts(request)
        self.assertTrue(result["prompts"][0].startswith(refined))
        self.assertIn("Spoken words are audio only", result["prompts"][0])

    def test_prompt_refinement_rejects_wrong_variant_count(self):
        request = app.AIImproveRequest(
            product_name="Sola",
            base_prompts=["A valid base render prompt for variant one."],
        )
        with patch.object(app, "_run_ai", return_value={"prompts": []}):
            with self.assertRaises(HTTPException) as raised:
                app.ai_improve_prompts(request)
        self.assertEqual(raised.exception.status_code, 502)

    def test_speech_budget_leaves_an_end_buffer(self):
        self.assertEqual(app.speech_word_budget(8), 15)
        self.assertEqual(app.speech_word_budget(4), 6)

    def test_write_result_is_shortened_to_duration_budget(self):
        fields = {
            "script": "One two three four five six seven eight. Nine ten eleven twelve.",
            "notes": [],
        }
        result = app._enforce_write_budget(fields, 8)
        self.assertEqual(result["script"], "One two three four five six seven eight.")
        self.assertLessEqual(app._word_count(result["script"]), 8)
        self.assertIn("Script shortened", result["notes"][0])

    def test_prompt_refinement_rejects_dialogue_that_cannot_fit(self):
        request = app.AIImproveRequest(
            duration_seconds=4,
            base_prompts=[
                'The creator says exactly: "one two three four five six seven"'
            ],
        )
        with self.assertRaises(HTTPException) as raised:
            app.ai_improve_prompts(request)
        self.assertEqual(raised.exception.status_code, 400)
        self.assertIn("6", raised.exception.detail)

    def test_render_rejects_overlong_quoted_dialogue(self):
        request = app.GenRequest(
            prompt=(
                'The creator says exactly: "one two three four five six seven eight '
                'nine ten eleven twelve thirteen fourteen fifteen sixteen"'
            ),
            num_frames=193,
            frame_rate=25,
        )
        with self.assertRaises(HTTPException) as raised:
            app.generate(request)
        self.assertEqual(raised.exception.status_code, 400)
        self.assertIn("14", raised.exception.detail)


if __name__ == "__main__":
    unittest.main()
