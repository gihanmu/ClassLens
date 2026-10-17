"""Evidence-grounded pedagogical recommendation blueprints catalog.

Maps diagnosed mathematical misconceptions to topic-specific instructional interventions
with exact student evidence citations and zero fabricated student counts.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional
from services.worker.agents.contracts import DifferentiatedAction
from services.worker.math_verifier.task_router import TaskType


BLUEPRINT_CATALOG: Dict[str, Dict[str, Any]] = {
    # -------------------------------------------------------------------------
    # FRACTION DIVISION INTERVENTIONS
    # -------------------------------------------------------------------------
    f"{TaskType.FRACTION_DIVISION.value}:FRAC-DIV-WRONG-GROUP-SIZE": {
        "title": "Fraction Bar Partitioning & Measurement Grouping",
        "action_type": "concrete_manipulative",
        "instructional_steps": [
            "Use fraction strips or tape models to represent dividend 8/9 partitioned into 9 equal units.",
            "Physically group 4/9 blocks together to demonstrate that exactly two groups of 4/9 fit inside 8/9.",
            "Emphasize that the divisor defines the measurement group size, not the number of partitions.",
        ],
        "rationale": "Addresses misunderstanding of fraction division as measurement/grouping.",
        "status": "verified_misconception",
    },
    f"{TaskType.FRACTION_DIVISION.value}:FRAC-DIV-RECIPROCAL-INVERSION": {
        "title": "Reciprocal Inversion & Divisor Meaning",
        "action_type": "worked_example",
        "instructional_steps": [
            "Demonstrate why dividing by 4/9 is mathematically equivalent to multiplying by 9/4 (the reciprocal).",
            "Highlight that only the divisor fraction is inverted, while the dividend remains unchanged.",
            "Verify the symbolic computation: (8/9) * (9/4) = 72/36 = 2.",
        ],
        "rationale": "Corrects incorrect reciprocal operation or confusion over which term to invert.",
        "status": "verified_misconception",
    },
    f"{TaskType.FRACTION_DIVISION.value}:FRAC-DIV-UNIT-FORM-DISCONNECT": {
        "title": "Connecting Unit Form to Conceptual Tape Models",
        "action_type": "guided_inquiry",
        "instructional_steps": [
            "Express 8/9 as '8 ninths' and 4/9 as '4 ninths' in explicit verbal unit form.",
            "Ask: 'How many groups of 4 ninths are in 8 ninths?' -> '8 ninths ÷ 4 ninths = 2'.",
            "Align each written unit-form phrase directly above its corresponding visual tape partition.",
        ],
        "rationale": "Bridges symbolic unit-form notation with visual fraction representations.",
        "status": "verified_misconception",
    },
    f"{TaskType.FRACTION_DIVISION.value}:REPRESENTATION-MISSING": {
        "title": "Visual Representation Follow-Up: Tape Diagram Construction",
        "action_type": "guided_inquiry",
        "instructional_steps": [
            "Acknowledge the student's correct numeric calculation (8/9 ÷ 4/9 = 2).",
            "Guide the student to draw the requested visual model: a tape divided into 9 equal parts with 8 shaded.",
            "Prompt student to bracket groups of 4/9 on the tape to visually substantiate the quotient 2.",
        ],
        "rationale": "Prompts student to construct required visual evidence without falsely diagnosing an arithmetic error.",
        "status": "representation_followup",
    },
    f"{TaskType.FRACTION_DIVISION.value}:VISUAL-MODEL-INCOMPLETE": {
        "title": "Visual Representation Follow-Up: Tape Diagram Construction",
        "action_type": "guided_inquiry",
        "instructional_steps": [
            "Acknowledge the student's correct numeric calculation (8/9 ÷ 4/9 = 2).",
            "Guide the student to draw the requested visual model: a tape divided into 9 equal parts with 8 shaded.",
            "Prompt student to bracket groups of 4/9 on the tape to visually substantiate the quotient 2.",
        ],
        "rationale": "Prompts student to construct required visual evidence without falsely diagnosing an arithmetic error.",
        "status": "representation_followup",
    },

    # -------------------------------------------------------------------------
    # INTEGER NUMBER LINE INTERVENTIONS
    # -------------------------------------------------------------------------
    f"{TaskType.INTEGER_NUMBER_LINE.value}:MISC-ARITH-OFF-BY-ONE": {
        "title": "Number Line Bead String & Interval Spacing",
        "action_type": "concrete_manipulative",
        "instructional_steps": [
            "Distribute 20-bead strings to students with off-by-one errors.",
            "Demonstrate counting spaces between beads rather than physical bead dividers.",
            "Model transition from -6 through 0 to +6, emphasizing the 12-unit span.",
        ],
        "rationale": "Resolves tick-mark counting errors by focusing on unit interval lengths.",
        "status": "verified_misconception",
    },
    f"{TaskType.INTEGER_NUMBER_LINE.value}:MISC-LINE-INTERVAL-MISLABEL": {
        "title": "Interval Tick-Mark vs Unit Space Calibration",
        "action_type": "worked_example",
        "instructional_steps": [
            "Present side-by-side number line with tick labels vs interval steps.",
            "Highlight that jump distance corresponds to the gap traversed, not the landing index mark.",
            "Practice counting unit gaps on grid paper.",
        ],
        "rationale": "Clarifies coordinate label positioning vs interval jump distance.",
        "status": "verified_misconception",
    },
    f"{TaskType.INTEGER_NUMBER_LINE.value}:MISC-DIR-INV": {
        "title": "Contrasting Cases: Directional Sign Vectors",
        "action_type": "worked_example",
        "instructional_steps": [
            "Present side-by-side student work: correct rightward hop vs. inverted leftward jump.",
            "Have pairs color-code positive additions in green (right) and subtractions in orange (left).",
            "Conduct mini-whiteboard check on -4 + 8 vs -4 - 8.",
        ],
        "rationale": "Remediates vector direction errors when adding or subtracting signed numbers.",
        "status": "verified_misconception",
    },
    f"{TaskType.INTEGER_NUMBER_LINE.value}:MISC-NUM-DIR-REVERSE": {
        "title": "Contrasting Cases: Directional Sign Vectors",
        "action_type": "worked_example",
        "instructional_steps": [
            "Present side-by-side student work: correct rightward hop vs. inverted leftward jump.",
            "Have pairs color-code positive additions in green (right) and subtractions in orange (left).",
            "Conduct mini-whiteboard check on -4 + 8 vs -4 - 8.",
        ],
        "rationale": "Remediates vector direction errors when adding or subtracting signed numbers.",
        "status": "verified_misconception",
    },
    f"{TaskType.INTEGER_NUMBER_LINE.value}:DIRECTION_SIGN_CONFUSION": {
        "title": "Contrasting Cases: Directional Sign Vectors",
        "action_type": "worked_example",
        "instructional_steps": [
            "Present side-by-side student work: correct rightward hop vs. inverted leftward jump.",
            "Have pairs color-code positive additions in green (right) and subtractions in orange (left).",
            "Conduct mini-whiteboard check on -4 + 8 vs -4 - 8.",
        ],
        "rationale": "Remediates vector direction errors when adding or subtracting signed numbers.",
        "status": "verified_misconception",
    },
    f"{TaskType.INTEGER_NUMBER_LINE.value}:MISC-MAG-COUNT": {
        "title": "Direct Jump Magnitude Verification Routine",
        "action_type": "guided_inquiry",
        "instructional_steps": [
            "Establish a mandatory mental check: 'start + distance = landing point'.",
            "Verify -6 + 12 = 6 before proceeding to the third step (- 4).",
            "Pair students to audit peer number line hops for exact interval lengths.",
        ],
        "rationale": "Instills verification checkpoints for multi-step integer hop traversal.",
        "status": "verified_misconception",
    },
    f"{TaskType.INTEGER_NUMBER_LINE.value}:INCORRECT_INTERVAL_MAGNITUDE": {
        "title": "Direct Jump Magnitude Verification Routine",
        "action_type": "guided_inquiry",
        "instructional_steps": [
            "Establish a mandatory mental check: 'start + distance = landing point'.",
            "Verify -6 + 12 = 6 before proceeding to the third step (- 4).",
            "Pair students to audit peer number line hops for exact interval lengths.",
        ],
        "rationale": "Instills verification checkpoints for multi-step integer hop traversal.",
        "status": "verified_misconception",
    },
    f"{TaskType.INTEGER_NUMBER_LINE.value}:START_POINT_ZERO_MISUNDERSTANDING": {
        "title": "Origin Anchor & Initial Coordinate Walkway",
        "action_type": "concrete_manipulative",
        "instructional_steps": [
            "Lay number line on floor from -10 to +10.",
            "Ask student to physically stand at 0 as home base before moving to initial term.",
            "Emphasize whether problem begins from origin or starts directly at first operand.",
        ],
        "rationale": "Clarifies number-line coordinate conventions.",
        "status": "verified_misconception",
    },
    f"{TaskType.INTEGER_NUMBER_LINE.value}:COMPENSATORY_ARITHMETIC_ERROR": {
        "title": "Reasoning vs. Answer Audit Routine",
        "action_type": "guided_inquiry",
        "instructional_steps": [
            "Examine student work where incorrect hops serendipitously reached the correct final answer.",
            "Guide peer discussion on why valid mathematical process matters beyond just the final number.",
            "Re-verify each hop step-by-step with SymPy rational rules.",
        ],
        "rationale": "Emphasizes process validity over accidental correct answers.",
        "status": "verified_misconception",
    },
    f"{TaskType.INTEGER_NUMBER_LINE.value}:REASONING_INCOMPLETE": {
        "title": "Multi-Step Working & Number Line Documentation",
        "action_type": "guided_inquiry",
        "instructional_steps": [
            "Provide students with number line templates requiring drawn hops for every term.",
            "Require students to label start point, hop distance, and intermediate landings.",
            "Review student work where answer was written without supporting visual proof.",
        ],
        "rationale": "Addresses incomplete working on integer operations.",
        "status": "representation_followup",
    },

    # -------------------------------------------------------------------------
    # DECIMAL OPERATIONS INTERVENTIONS
    # -------------------------------------------------------------------------
    f"{TaskType.DECIMAL_OPERATIONS.value}:DEC-EST-MAGNITUDE-SLIP": {
        "title": "Decimal Place Magnitude & Benchmark Estimation",
        "action_type": "worked_example",
        "instructional_steps": [
            "Round decimal factors to single-digit leading integers to establish upper and lower bounds.",
            "Check product decimal position against estimated order of magnitude before finalizing.",
            "Use 10x10 grids to visualize decimal scaling.",
        ],
        "rationale": "Grounds decimal place-value position in rough order-of-magnitude estimation.",
        "status": "verified_misconception",
    },

    # -------------------------------------------------------------------------
    # PLACE VALUE INTERVENTIONS
    # -------------------------------------------------------------------------
    f"{TaskType.PLACE_VALUE.value}:PLACE-VALUE-COLUMN-MISALIGN": {
        "title": "Place Value Disks & Base-Ten Column Bundling",
        "action_type": "concrete_manipulative",
        "instructional_steps": [
            "Use place value disks to represent hundreds, tens, and ones in physical columns.",
            "Demonstrate bundling 10 tens into 1 hundred disk.",
            "Map physical disk counts directly into expanded standard form.",
        ],
        "rationale": "Reinforces unit grouping and place-value column alignment.",
        "status": "verified_misconception",
    },
}


class RecommendationCatalog:
    """Retrieves and constructs strictly evidence-grounded DifferentiatedAction objects."""

    @classmethod
    def get_action_for_cluster(
        cls,
        task_type: TaskType,
        taxonomy_id: str,
        student_count: int,
        supporting_response_ids: List[str],
        assessment_id: Optional[str] = None,
        is_mock: bool = False,
    ) -> Optional[DifferentiatedAction]:
        """Builds a DifferentiatedAction strictly if student_count > 0 and blueprint matches."""
        if student_count <= 0 or not supporting_response_ids:
            return None

        # Look up key by task_type:taxonomy_id
        key = f"{task_type.value}:{taxonomy_id}"
        blueprint = BLUEPRINT_CATALOG.get(key)

        if not blueprint:
            # Check if any blueprint matches taxonomy across same topic
            prefix = f"{task_type.value}:"
            for k, b in BLUEPRINT_CATALOG.items():
                if k.startswith(prefix) and taxonomy_id in k:
                    blueprint = b
                    break

        if not blueprint:
            return None

        return DifferentiatedAction(
            target_misconception_id=taxonomy_id,
            action_type=blueprint["action_type"],
            title=blueprint["title"],
            instructional_steps=blueprint["instructional_steps"],
            student_count_affected=student_count,
            assessment_id=assessment_id,
            task_type=task_type.value,
            supporting_response_ids=supporting_response_ids,
            evidence_sufficiency="sufficient",
            status=blueprint.get("status", "verified_misconception"),
            rationale=blueprint.get("rationale"),
            is_mock=is_mock,
        )
