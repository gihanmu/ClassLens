# ClassLens — Project Owner Handwriting Collection Checklist

**Document:** Gate 6.1 Checkpoint B Operational Guide  
**Audience:** Repository Owner / Test Administrator  
**Status:** READY FOR PHYSICAL WORKSHEET CREATION  

---

## 1. Overview

Before authorized live multimodal evaluation (Phase B) can begin, 5 physical handwritten samples must be created, photographed/scanned, and deposited in the evaluation dataset folder.

This checklist gives the exact steps and drawing scripts to produce the **5 prioritized blind evaluation cases**.

---

## 2. Preparation Steps

1. **Locate the Blank Worksheet Template:**
   The template is pre-generated and stored in the repository at:
   `evaluation/datasets/templates/blank_worksheet_template.png`
2. **Print or Digital Pen Setup:**
   - **Option A (Physical Paper - Preferred):** Print 5 copies on standard A4 paper. Use a normal 2B or HB pencil or ballpoint pen.
   - **Option B (Tablet / iPad Stylus):** Open the PNG in a drawing application (e.g. GoodNotes, Notability, Procreate, Apple Pencil) and hand-draw directly using a realistic pen or pencil brush (100% opacity, dark gray/black).
3. **Target Destination Directory:**
   Create the directory if not already created:
   `evaluation/datasets/images/`

---

## 3. Drawing Scripts for the 5 Prioritized Cases

### Sample 1: Canonical Correct Solution
* **Target Filename:** `evaluation/datasets/images/blind_eval_01_canonical_correct.png`
* **Sample ID on header:** `BLIND-01`
* **Handwriting Script:**
  1. Draw an arc starting at `0` going left and landing on `-6`. Label above the arc: `-6`.
  2. Draw an arc starting at `-6` going right and landing on `+6`. Label above the arc: `+12`.
  3. Draw an arc starting at `+6` going left and landing on `+2`. Label above the arc: `-4`.
  4. In the "Final Answer:" box, clearly write: `2`.

---

### Sample 2: Off-By-One Interval Counting Error
* **Target Filename:** `evaluation/datasets/images/blind_eval_02_off_by_one.png`
* **Sample ID on header:** `BLIND-02`
* **Handwriting Script:**
  1. Draw an arc from `0` going left to `-6`. Label: `-6`.
  2. Draw an arc from `-6` going right, but stop at `+5` (student undercounted 12 ticks by 1). Label: `+12`.
  3. Draw an arc from `+5` going left by 4 ticks, landing on `+1`. Label: `-4`.
  4. In the "Final Answer:" box, write: `1`.

---

### Sample 3: Direction / Sign Error
* **Target Filename:** `evaluation/datasets/images/blind_eval_03_direction_reversal.png`
* **Sample ID on header:** `BLIND-03`
* **Handwriting Script:**
  1. Draw an arc from `0` to `-6`. Label: `-6`.
  2. Draw an arc from `-6` going **left** (wrong direction for `+12`), landing at `-18` (or arrow pointing past `-10` off the scale). Alternatively, if constrained by the $-10$ axis: draw arc from `-6` going left 4 units to `-10`. Label: `+12`.
  3. In the "Final Answer:" box, write: `-14`.

---

### Sample 4: Compensatory Lucky Answer
* **Target Filename:** `evaluation/datasets/images/blind_eval_04_compensatory.png`
* **Sample ID on header:** `BLIND-04`
* **Handwriting Script:**
  1. Draw an arc from `0` to `-6`. Label: `-6`.
  2. Draw an arc from `-6` going right, but undercounting and landing on `+5`. Label: `+12`.
  3. Draw an arc from `+5` going left to `+2` (span is only 3 units, but falsely labeled `-4`). Label: `-4`.
  4. In the "Final Answer:" box, write: `2`.
  * *Note: The final answer is mathematically correct (2), but the geometric reasoning contains compensating errors.*

---

### Sample 5: Ambiguous / Incomplete Worksheet
* **Target Filename:** `evaluation/datasets/images/blind_eval_05_ambiguous_incomplete.png`
* **Sample ID on header:** `BLIND-05`
* **Handwriting Script:**
  1. Draw only the first arc from `0` to `-6`. Label: `-6`.
  2. Leave the rest of the number line completely blank (no second or third arc).
  3. Leave the "Final Answer:" box completely blank.
  * *Note: Tests the pipeline's ability to abstain from hallucinating full diagnoses when evidence is incomplete.*

---

## 4. Quality & Formatting Verification

Before placing images in `evaluation/datasets/images/`:
- [ ] Image format is `.png` or `.jpg`.
- [ ] Filenames match exactly (`blind_eval_01_canonical_correct.png`, etc.).
- [ ] Images are oriented right-side up (not rotated 90° or 180°).
- [ ] Resolution is at least $1200 \times 800$ px (under 5 MB per file).
- [ ] No real student names or identifying information are present.

---

## 5. Verification Command

Once the 5 files are placed in `evaluation/datasets/images/`, verify them safely using dry-run mode ($0.00 spend):

```bash
python -m evaluation.runner --dataset evaluation/datasets/blind_eval_specification.json --dry-run
```

If all 5 images are present, the dry-run will report:
`Prerequisites Verified: 5/5 images present on disk.`
