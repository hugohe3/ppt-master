#!/usr/bin/env python3
"""Focused tests for Confirm UI Design Spec depth validation."""

from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path


SCRIPTS_DIR = Path(__file__).resolve().parents[1]
if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))

from confirm_ui import server  # noqa: E402


def _recommendations(
    depth: object = 'brief',
    *,
    generation_mode: str = 'continuous',
    refine_spec: bool = False,
) -> dict:
    data = {
        'recommend': {'generation_mode': generation_mode},
        'refine_spec': {'value': refine_spec},
    }
    if depth is not None:
        data['design_spec_depth'] = {'value': depth}
    return data


def _result(
    *,
    generation_mode: str = 'continuous',
    refine_spec: bool = False,
    depth: str = 'brief',
) -> dict:
    return {
        'generation_mode': generation_mode,
        'refine_spec': refine_spec,
        'design_spec_depth': depth,
    }


class ConfirmUiDesignSpecDepthTests(unittest.TestCase):
    def test_missing_recommendation_field_is_rejected(self) -> None:
        error = server._stage2_production_recommendations_error(
            _recommendations(None)
        )

        self.assertIn('design_spec_depth.value', error or '')

    def test_invalid_recommendation_value_is_rejected(self) -> None:
        error = server._stage2_production_recommendations_error(
            _recommendations(['brief'])
        )

        self.assertIn('"brief" or "complete"', error or '')

    def test_brief_is_accepted_without_coupling_conditions(self) -> None:
        self.assertIsNone(
            server._stage2_production_recommendations_error(_recommendations())
        )
        self.assertIsNone(server._stage2_production_result_error(_result()))

    def test_split_mode_rejects_brief(self) -> None:
        recommendation_error = server._stage2_production_recommendations_error(
            _recommendations(generation_mode='split')
        )
        error = server._stage2_production_result_error(
            _result(generation_mode='split')
        )

        self.assertIn('design_spec_depth.value to "complete"', recommendation_error or '')
        self.assertIn('design_spec_depth to "complete"', error or '')

    def test_refinement_rejects_brief(self) -> None:
        recommendation_error = server._stage2_production_recommendations_error(
            _recommendations(refine_spec=True)
        )
        error = server._stage2_production_result_error(
            _result(refine_spec=True)
        )

        self.assertIn('design_spec_depth.value to "complete"', recommendation_error or '')
        self.assertIn('design_spec_depth to "complete"', error or '')

    def test_legacy_result_defaults_to_complete(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            result_path = Path(temp_dir) / 'result.json'
            result_path.write_text(
                json.dumps({'stage': 'final', 'status': 'confirmed'}),
                encoding='utf-8',
            )

            result = server._read_result_object(result_path)

        self.assertEqual(result['design_spec_depth'], 'complete')


if __name__ == '__main__':
    unittest.main()
