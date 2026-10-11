"""Structured mock fixtures for the 13 DrawEduMath Problem #1065658 student cases.

PROVENANCE:
These fixtures are strictly synthetic mock observation structures for offline
local development. They are isolated from raw dataset files and explicitly tagged
as mock objects.
"""

from __future__ import annotations

import json
import os
from typing import Any, Dict

MOCK_FIXTURES: Dict[str, Dict[str, Any]] = {
    # Row 0: Clean standard hops 0 -> -6 -> 6 -> 2, circled 2
    "resp_04255753": {
        "response_id": "resp_04255753",
        "row_index": 0,
        "quality_status": "clear",
        "confidence": 0.98,
        "has_number_line": True,
        "final_answer_marked": "2",
        "observations": [
            {"kind": "number_line", "value": "Number line intervals of 2 from -12 to 12", "confidence": 0.99},
            {"kind": "arrow_jump", "value": "Jump from 0 to -6", "confidence": 0.98, "start_pos": 0.0, "end_pos": -6.0, "direction": "left"},
            {"kind": "arrow_jump", "value": "Jump from -6 to 6", "confidence": 0.98, "start_pos": -6.0, "end_pos": 6.0, "direction": "right"},
            {"kind": "arrow_jump", "value": "Jump from 6 to 2", "confidence": 0.97, "start_pos": 6.0, "end_pos": 2.0, "direction": "left"},
            {"kind": "circled_result", "value": "2", "confidence": 0.99},
        ],
    },
    # Row 1: Clean standard hops 0 -> -6 -> 6 -> 2, circled 2
    "resp_0a70eabf": {
        "response_id": "resp_0a70eabf",
        "row_index": 1,
        "quality_status": "clear",
        "confidence": 0.97,
        "has_number_line": True,
        "final_answer_marked": "2",
        "observations": [
            {"kind": "number_line", "value": "Horizontal line -9 to 10", "confidence": 0.98},
            {"kind": "arrow_jump", "value": "Jump 0 to -6", "confidence": 0.97, "start_pos": 0.0, "end_pos": -6.0, "direction": "left"},
            {"kind": "arrow_jump", "value": "Jump -6 to 6", "confidence": 0.97, "start_pos": -6.0, "end_pos": 6.0, "direction": "right"},
            {"kind": "arrow_jump", "value": "Jump 6 to 2", "confidence": 0.96, "start_pos": 6.0, "end_pos": 2.0, "direction": "left"},
            {"kind": "circled_result", "value": "2", "confidence": 0.99},
        ],
    },
    # Row 2: Clean standard hops, terminal at 2, final answer inferred
    "resp_2292f546": {
        "response_id": "resp_2292f546",
        "row_index": 2,
        "quality_status": "clear",
        "confidence": 0.95,
        "has_number_line": True,
        "final_answer_marked": None,
        "observations": [
            {"kind": "number_line", "value": "Graph paper line -7 to 10", "confidence": 0.96},
            {"kind": "arrow_jump", "value": "Jump 0 to -6", "confidence": 0.95, "start_pos": 0.0, "end_pos": -6.0, "direction": "left"},
            {"kind": "arrow_jump", "value": "Jump -6 to 6", "confidence": 0.95, "start_pos": -6.0, "end_pos": 6.0, "direction": "right"},
            {"kind": "arrow_jump", "value": "Jump 6 to 2", "confidence": 0.95, "start_pos": 6.0, "end_pos": 2.0, "direction": "left"},
        ],
    },
    # Row 3: Digitally drawn bracket curves 0 -> -6 -> 6 -> 2, circled 2
    "resp_2b804ad7": {
        "response_id": "resp_2b804ad7",
        "row_index": 3,
        "quality_status": "clear",
        "confidence": 0.96,
        "has_number_line": True,
        "final_answer_marked": "2",
        "observations": [
            {"kind": "number_line", "value": "Digital canvas", "confidence": 0.99},
            {"kind": "bracket_curve", "value": "Bracket curve 0 to -6", "confidence": 0.96, "start_pos": 0.0, "end_pos": -6.0, "direction": "left"},
            {"kind": "bracket_curve", "value": "Bracket curve -6 to 6", "confidence": 0.96, "start_pos": -6.0, "end_pos": 6.0, "direction": "right"},
            {"kind": "bracket_curve", "value": "Bracket curve 6 to 2", "confidence": 0.95, "start_pos": 6.0, "end_pos": 2.0, "direction": "left"},
            {"kind": "circled_result", "value": "2", "confidence": 0.99},
        ],
    },
    # Row 4: Compensatory error: 0 -> -6 -> 5 -> 2, answer: 2
    "resp_56005c1c": {
        "response_id": "resp_56005c1c",
        "row_index": 4,
        "quality_status": "clear",
        "confidence": 0.95,
        "has_number_line": True,
        "final_answer_marked": "2",
        "observations": [
            {"kind": "number_line", "value": "Line -10 to 10", "confidence": 0.98},
            {"kind": "arrow_jump", "value": "Jump 0 to -6", "confidence": 0.96, "start_pos": 0.0, "end_pos": -6.0, "direction": "left"},
            {"kind": "arrow_jump", "value": "Jump -6 to 5 (mag 11)", "confidence": 0.94, "start_pos": -6.0, "end_pos": 5.0, "direction": "right"},
            {"kind": "arrow_jump", "value": "Jump 5 to 2 (mag -3)", "confidence": 0.94, "start_pos": 5.0, "end_pos": 2.0, "direction": "left"},
            {"kind": "circled_result", "value": "2", "confidence": 0.98},
        ],
    },
    # Row 5: Off-by-one magnitude error: 0 -> -6 -> 5 -> 1, answer: 1
    "resp_80545ef3": {
        "response_id": "resp_80545ef3",
        "row_index": 5,
        "quality_status": "clear",
        "confidence": 0.94,
        "has_number_line": True,
        "final_answer_marked": "1",
        "observations": [
            {"kind": "number_line", "value": "Lined paper number line", "confidence": 0.97},
            {"kind": "arrow_jump", "value": "Jump 0 to -6", "confidence": 0.95, "start_pos": 0.0, "end_pos": -6.0, "direction": "left"},
            {"kind": "arrow_jump", "value": "Jump -6 to 5 (mag 11)", "confidence": 0.93, "start_pos": -6.0, "end_pos": 5.0, "direction": "right"},
            {"kind": "arrow_jump", "value": "Jump 5 to 1 (mag -4)", "confidence": 0.93, "start_pos": 5.0, "end_pos": 1.0, "direction": "left"},
            {"kind": "circled_result", "value": "1", "confidence": 0.97},
        ],
    },
    # Row 6: Correct number line 0 -> -6 -> 6 -> 2, but circled answer 3
    "resp_8cbadb4e": {
        "response_id": "resp_8cbadb4e",
        "row_index": 6,
        "quality_status": "clear",
        "confidence": 0.96,
        "has_number_line": True,
        "final_answer_marked": "3",
        "observations": [
            {"kind": "number_line", "value": "Standard number line", "confidence": 0.98},
            {"kind": "arrow_jump", "value": "Jump 0 to -6", "confidence": 0.96, "start_pos": 0.0, "end_pos": -6.0, "direction": "left"},
            {"kind": "arrow_jump", "value": "Jump -6 to 6", "confidence": 0.96, "start_pos": -6.0, "end_pos": 6.0, "direction": "right"},
            {"kind": "arrow_jump", "value": "Jump 6 to 2", "confidence": 0.95, "start_pos": 6.0, "end_pos": 2.0, "direction": "left"},
            {"kind": "circled_result", "value": "3", "confidence": 0.98},
        ],
    },
    # Row 7: Digital drawing standard pass 0 -> -6 -> 6 -> 2, circled 2
    "resp_8ef9d302": {
        "response_id": "resp_8ef9d302",
        "row_index": 7,
        "quality_status": "clear",
        "confidence": 0.98,
        "has_number_line": True,
        "final_answer_marked": "2",
        "observations": [
            {"kind": "number_line", "value": "Digital tablet drawing", "confidence": 0.99},
            {"kind": "arrow_jump", "value": "Jump 0 to -6", "confidence": 0.98, "start_pos": 0.0, "end_pos": -6.0, "direction": "left"},
            {"kind": "arrow_jump", "value": "Jump -6 to 6", "confidence": 0.98, "start_pos": -6.0, "end_pos": 6.0, "direction": "right"},
            {"kind": "arrow_jump", "value": "Jump 6 to 2", "confidence": 0.97, "start_pos": 6.0, "end_pos": 2.0, "direction": "left"},
            {"kind": "circled_result", "value": "2", "confidence": 0.99},
        ],
    },
    # Row 8: Number line interval mislabeled: stated magnitude 12 from -6 to 5
    "resp_a5c95313": {
        "response_id": "resp_a5c95313",
        "row_index": 8,
        "quality_status": "clear",
        "confidence": 0.93,
        "has_number_line": True,
        "final_answer_marked": "1",
        "observations": [
            {"kind": "number_line", "value": "Mislabeled intervals skipping 3", "confidence": 0.92},
            {"kind": "arrow_jump", "value": "Jump 0 to -6", "confidence": 0.95, "start_pos": 0.0, "end_pos": -6.0, "direction": "left", "stated_magnitude": 6.0},
            {"kind": "arrow_jump", "value": "Jump -6 to 5 with label +12", "confidence": 0.92, "start_pos": -6.0, "end_pos": 5.0, "direction": "right", "stated_magnitude": 12.0},
            {"kind": "arrow_jump", "value": "Jump 5 to 1 with label -4", "confidence": 0.92, "start_pos": 5.0, "end_pos": 1.0, "direction": "left", "stated_magnitude": 4.0},
            {"kind": "circled_result", "value": "1", "confidence": 0.96},
        ],
    },
    # Row 9: Commutative rearrangement 12 -> 8 -> 2 (12 - 4 - 6 = 2), answer: 2
    "resp_b4214e02": {
        "response_id": "resp_b4214e02",
        "row_index": 9,
        "quality_status": "clear",
        "confidence": 0.97,
        "has_number_line": True,
        "final_answer_marked": "2",
        "observations": [
            {"kind": "equation", "value": "12 - 4 - 6 = 2", "confidence": 0.99},
            {"kind": "number_line", "value": "Number line starting at 12", "confidence": 0.98},
            {"kind": "arrow_jump", "value": "Jump 12 to 8 (-4)", "confidence": 0.97, "start_pos": 12.0, "end_pos": 8.0, "direction": "left"},
            {"kind": "arrow_jump", "value": "Jump 8 to 2 (-6)", "confidence": 0.97, "start_pos": 8.0, "end_pos": 2.0, "direction": "left"},
            {"kind": "circled_result", "value": "2", "confidence": 0.99},
        ],
    },
    # Row 10: Pre-printed paper, standard hop pass 0 -> -6 -> 6 -> 2, answer: 2
    "resp_d3e07e18": {
        "response_id": "resp_d3e07e18",
        "row_index": 10,
        "quality_status": "clear",
        "confidence": 0.97,
        "has_number_line": True,
        "final_answer_marked": "2",
        "observations": [
            {"kind": "number_line", "value": "Pre-printed worksheet", "confidence": 0.99},
            {"kind": "arrow_jump", "value": "Curved arrow 0 to -6", "confidence": 0.97, "start_pos": 0.0, "end_pos": -6.0, "direction": "left"},
            {"kind": "arrow_jump", "value": "Curved arrow -6 to 6", "confidence": 0.97, "start_pos": -6.0, "end_pos": 6.0, "direction": "right"},
            {"kind": "arrow_jump", "value": "Curved arrow 6 to 2", "confidence": 0.96, "start_pos": 6.0, "end_pos": 2.0, "direction": "left"},
            {"kind": "circled_result", "value": "2", "confidence": 0.99},
        ],
    },
    # Row 11: Circled 2, but zero working or arrows shown
    "resp_e33295ea": {
        "response_id": "resp_e33295ea",
        "row_index": 11,
        "quality_status": "clear",
        "confidence": 0.95,
        "has_number_line": True,
        "final_answer_marked": "2",
        "observations": [
            {"kind": "number_line", "value": "Number line present with zero marks/hops", "confidence": 0.96},
            {"kind": "circled_result", "value": "2", "confidence": 0.98},
        ],
    },
    # Row 12: Incomplete/unreadable: no working, no arrows, no final answer
    "resp_f0738571": {
        "response_id": "resp_f0738571",
        "row_index": 12,
        "quality_status": "unreadable",
        "confidence": 0.50,
        "has_number_line": False,
        "final_answer_marked": None,
        "observations": [],
    },
}


def dump_json_fixtures(target_dir: str) -> None:
    """Serializes all mock fixtures as standalone JSON files for external inspections."""
    os.makedirs(target_dir, exist_ok=True)
    for resp_id, fixture_data in MOCK_FIXTURES.items():
        file_path = os.path.join(target_dir, f"{resp_id}.json")
        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(fixture_data, f, indent=2)
