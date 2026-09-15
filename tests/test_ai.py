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
        self.assertEqual(
            set(snapshot),
            {"jobs", "gallery", "keyframes", "personas", "campaigns", "ai"},
        )
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

    def test_character_dna_reaches_both_ai_prompts(self):
        dna = "Maya, wavy dark brown hair, sage green ribbed cardigan."
        write_request = app.AIWriteRequest(product_name="Sola", character_dna=dna)
        improve_request = app.AIImproveRequest(
            product_name="Sola",
            character_dna=dna,
            base_prompts=["A valid base render prompt for variant one."],
        )
        calls = []

        def capture(system, user, max_tokens):
            calls.append((system, user))
            return {"prompts": ["A refined continuous smartphone UGC take."]}

        with patch.object(app, "_run_ai", side_effect=capture):
            app.ai_write(write_request)
            app.ai_improve_prompts(improve_request)
        for system, user in calls:
            self.assertIn("character_dna", system)
            self.assertIn(dna, user)
        self.assertIn("verbatim", calls[1][0])

    def test_ugc_style_block_describes_phone_imperfection(self):
        self.assertIn("micro-shake", app.UGC_STYLE_BLOCK)
        self.assertIn("visible pores", app.UGC_STYLE_BLOCK)
        self.assertIn("off-center", app.UGC_STYLE_BLOCK)

    def test_persona_round_trip_and_delete(self):
        with TemporaryDirectory() as directory:
            personas = Path(directory) / "personas"
            keyframes = Path(directory) / "keyframes"
            personas.mkdir()
            keyframes.mkdir()
            with patch.object(app, "PERSONAS", personas), \
                    patch.object(app, "KEYFRAMES", keyframes):
                saved = app.save_persona(app.PersonaRequest(
                    name="Maya Kitchen",
                    dna="Maya, wavy dark brown hair, sage green ribbed cardigan.",
                ))
                self.assertEqual(saved["slug"], "maya-kitchen")
                (keyframes / "persona-maya-kitchen-1.png").write_bytes(b"png")
                listed = app.list_personas()
                self.assertEqual(len(listed), 1)
                self.assertEqual(listed[0]["stills"], ["persona-maya-kitchen-1.png"])
                app.delete_persona("maya-kitchen")
                self.assertEqual(app.list_personas(), [])
                self.assertFalse((keyframes / "persona-maya-kitchen-1.png").exists())

    def test_persona_slug_rejects_traversal(self):
        with self.assertRaises(HTTPException) as raised:
            app.safe_persona("../evil")
        self.assertEqual(raised.exception.status_code, 404)

    def test_still_command_uses_zimage_venv(self):
        job = {"prompt": "portrait", "outfile": "/tmp/x.png",
               "width": 704, "height": 1280, "seed": 5}
        cmd = app.still_command(job)
        self.assertIn(str(app.ZIMAGE_SCRIPT), cmd)
        self.assertIn("--seed", cmd)

    def test_render_prompt_contains_style_dna_and_hook_swap(self):
        ctx = app.CreativeContext(
            product_name="Sola",
            script="Sola made my routine feel easier. I use one drop daily.",
            character_dna="Maya, wavy dark brown hair, sage green ribbed cardigan.",
            duration_seconds=8,
        )
        prompt = app.build_render_prompt(ctx, "hot_take", 1)
        self.assertIn(app.UGC_STYLE_BLOCK, prompt)
        self.assertIn(ctx.character_dna, prompt)
        self.assertIn("Hot take:", prompt)
        self.assertIn("I use one drop daily.", prompt)
        self.assertIn(app.PROMPT_TEXT_GUARD, prompt)

    def test_campaign_expands_hook_matrix(self):
        recorded = []

        def fake_enqueue(gen, images):
            recorded.append((gen, images))
            return {"id": f"j{len(recorded)}", "seed": 1, "file": f"f{len(recorded)}.mp4"}

        with TemporaryDirectory() as directory:
            campaigns = Path(directory)
            (campaigns / "abc123.json").write_text('{"id": "abc123", "cells": []}')
            req = app.CampaignRequest(
                context=app.CreativeContext(product_name="Sola", script="A steady script."),
                hooks=["discovery", "problem", "proof"],
                variants_per_hook=2,
                refine=False,
            )
            with patch.object(app, "CAMPAIGNS", campaigns), \
                    patch.object(app, "_enqueue_video", side_effect=fake_enqueue):
                app._build_campaign("abc123", req)
            campaign = app.json.loads((campaigns / "abc123.json").read_text())
        self.assertEqual(len(recorded), 6)
        self.assertEqual(campaign["status"], "queued")
        self.assertEqual({cell["hook"] for cell in campaign["cells"]},
                         {"discovery", "problem", "proof"})
        self.assertTrue(all(cell.get("job_id") for cell in campaign["cells"]))

    def test_sidecar_round_trip_preserves_rating(self):
        with TemporaryDirectory() as directory:
            outputs = Path(directory)
            with patch.object(app, "OUTPUTS", outputs):
                job = {"kind": "video", "file": "clip.mp4", "prompt": "p" * 20,
                       "width": 704, "height": 1280, "num_frames": 121,
                       "frame_rate": 24.0, "seed": 3, "images": [],
                       "status": "queued", "created": 1.0}
                app.write_sidecar(job)
                app.sidecar_path("clip.mp4").write_text(
                    app.json.dumps({**app.read_sidecar("clip.mp4"), "rating": 4}))
                job["status"] = "done"
                app.write_sidecar(job)
                sidecar = app.read_sidecar("clip.mp4")
        self.assertEqual(sidecar["rating"], 4)
        self.assertEqual(sidecar["status"], "done")

    def test_leftover_jobs_requeue_on_startup(self):
        with TemporaryDirectory() as directory:
            data = Path(directory)
            (data / "jobs.json").write_text(app.json.dumps([
                {"id": "resume1", "status": "running", "kind": "video",
                 "prompt": "p" * 20, "file": "a.mp4", "outfile": "/tmp/a.mp4"},
                {"id": "done1", "status": "done", "kind": "video",
                 "prompt": "p" * 20, "file": "b.mp4", "outfile": "/tmp/b.mp4"},
            ]))
            fake_jobs, fake_order, queued = {}, [], []

            class FakeQueue:
                def put(self, item):
                    queued.append(item)

            with patch.object(app, "DATA", data), \
                    patch.object(app, "jobs", fake_jobs), \
                    patch.object(app, "job_order", fake_order), \
                    patch.object(app, "queue", FakeQueue()):
                app.requeue_leftover_jobs()
        self.assertEqual(queued, ["resume1"])
        self.assertEqual(fake_jobs["resume1"]["status"], "queued")

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
