# Dataset Curation & Inspection Plan — ClassLens

**Document ID:** EVL-CUR-002
**Version:** 1.1.0
**Date:** 2026-10-11

---

### Changelog (v1.1.0)
- Formally confirmed that `problem_1065658` is the sole verified local problem directory containing the $-6 + 12 - 4 = 2$ task (13 student responses in `dataset/problem_1065658/`).
- Documented that problem ID `712487` does not exist in the local filesystem.
- Formalized strict metadata isolation: human teacher descriptions, synthetic LLM QA, and provisional curated labels are stored in separate, unpolluted schema fields.

---

## 1. Local Dataset Structure & Provenance

The local repository contains the complete DrawEduMath dataset extracted under:
```
./dataset/
├── problem_1065658/
│   ├── 04255753-0b36-495d-87eb-1e3cd0c97634.jpeg
│   ├── ... (13 total student image files)
│   └── problem_metadata.json
├── problem_1066525/
└── ... (188 problem folders total, containing 2,030 images)
```

### 1.1 Non-Destructive Integrity Policy
In strict compliance with Section 0 of `ClassLens_Master_Prompt.md`:
- **Zero In-Place Mutation**: No image, JSON file, or folder in `./dataset/` will be renamed, modified, deleted, or relocated.
- **No Uncontrolled Bulk Ingestion**: The application will **never** open or transmit all 2,030 images simultaneously to any AI model or external API.
- **Metadata-First Inspection**: The backend indexes problem metadata through a lightweight indexer that reads JSON keys on demand without loading bulk image binaries into memory.

---

## 2. Primary Vertical Slice Verification: Problem #1065658

### 2.1 Resolution of Problem ID Ambiguity
- The Master Prompt tentatively referenced Problem `#712487 (if confirmed in local data)`.
- A programmatic audit across all 188 folders confirmed that **`712487` does not exist** anywhere in `./dataset/`.
- Folder **`dataset/problem_1065658/`** is the exact, verified problem containing the $-6 + 12 - 4 = 2$ number line challenge, comprising:
  - 13 real student responses (7 JPEGs of hand-drawn paper work, 6 PNGs of digital whiteboard work).
  - Complete `problem_metadata.json` with teacher descriptions and single-rater teacher QA pairs.

### 2.2 Pedagogical Variance in Problem #1065658
This verified problem encompasses diverse pedagogical representations:
1. **Canonical Number Line Model**: Starting at 0, hopping left 6 to $-6$, right 12 to $+6$, left 4 to $+2$ (Rows 0, 1, 10).
2. **Alternative Commutative Order**: Rearranging to $12 - 4 - 6 = 2$ (Row 9).
3. **Magnitude Off-by-One Errors**: Hopping 11 units instead of 12 (Rows 4, 5).
4. **Terminal Marker Mismatch**: Circled +3 instead of +2 (Row 6).
5. **Interval Scale Mislabeled**: Irregular tick numbering skipping values (Row 8).
6. **Incomplete Submissions**: Circled final answer 2 with zero working shown (Row 11); blank number line with no arrows (Row 12).

---

## 3. Metadata Parsing & Provenance Isolation

The metadata schema extracted by our loader strictly isolates annotation provenance:

```python
class ParsedStudentAnswerMetadata(BaseModel):
    problem_id: str
    row_index: int
    image_name: str
    relative_path: str
    # Human single-rater annotations (Descriptive Evidence)
    teacher_description: Optional[str] = None
    teacher_qa_pairs: List[dict] = []
    # Synthetic annotations (Isolated / Excluded from Ground Truth)
    synthetic_qa_gpt4o: List[dict] = []
    synthetic_qa_claude: List[dict] = []
    # Adjudicated Verification Layer (ClassLens Golden Benchmark)
    curated_benchmark_status: Optional[str] = "provisional"
    curated_first_error_step: Optional[int] = None
    adjudication_notes: Optional[str] = None
```

All synthetic fields are explicitly sequestered from evaluation scoring logic.
