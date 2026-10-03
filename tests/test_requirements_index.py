"""Integrity tests for the normative Markdown and the requirements index.

These tests pin the normative text of the reference package rather than a
behaviour of the platform: ``spec/requirements_index.json`` must hold exactly
the 63 requirements PL-001..PL-063, the ten ADRs and the eighteen sources of
specification v0.2, verbatim and reproducibly, and the Markdown must carry the
same text without page furniture (specification section 28: "The source
Markdown is the normative specification"; Appendix C: "63 indexed
requirements").

Requirement markers on these tests therefore name the requirements whose
*text* a test pins (for example the ten requirements that sit next to a page
boundary in the PDF), not requirements whose behaviour is enforced.
"""

from __future__ import annotations

import importlib.util
import json
import re
import subprocess
import sys
from pathlib import Path
from types import ModuleType

import pytest

from plumb.contracts.common import (
    BuildState,
    BuildStepState,
    CollectorState,
    DatasetState,
    EffectState,
    ReleaseState,
    TrainingState,
)
from tests.conftest import REPO_ROOT

SPEC_DIR = REPO_ROOT / "spec"
SCRIPT = SPEC_DIR / "build_requirements_index.py"
INDEX_PATH = SPEC_DIR / "requirements_index.json"
MARKDOWN_PATH = SPEC_DIR / "Plumb_Autonomous_Implementation_Specification_v0.2.md"
RAW_PATH = REPO_ROOT / "docs" / "_spec_extracted_raw.txt"
LAYOUT_PATH = REPO_ROOT / "docs" / "_spec_extracted_layout.txt"

EXPECTED_IDS = [f"PL-{n:03d}" for n in range(1, 64)]
EXPECTED_ADR_IDS = [f"ADR-{n:03d}" for n in range(1, 11)]
EXPECTED_SOURCE_IDS = [f"S{n:02d}" for n in range(1, 19)]
PAGE_BOUNDARY_IDS = (
    "PL-011", "PL-012", "PL-016", "PL-025", "PL-030",
    "PL-039", "PL-044", "PL-047", "PL-050", "PL-056",
)
CONVERSION_NOTE = (
    "*Converted from the delivered PDF (Plumb_Agentic_Implementation_Specification.pdf, "
    "30 pages). This Markdown is the normative text of the reference package.*"
)
FURNITURE = re.compile(
    r"^(PLUMB / AUTONOMOUS IMPLEMENTATION|October 2, 2026 \| Proposed system design)"
)


# ---------------------------------------------------------------------------
# Fixtures and helpers
# ---------------------------------------------------------------------------


@pytest.fixture(scope="module")
def builder() -> ModuleType:
    spec = importlib.util.spec_from_file_location("build_requirements_index", SCRIPT)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module  # dataclasses resolve postponed annotations via sys.modules
    spec.loader.exec_module(module)
    return module


@pytest.fixture(scope="module")
def index() -> dict:
    with INDEX_PATH.open("r", encoding="utf-8") as handle:
        return json.load(handle)


@pytest.fixture(scope="module")
def markdown() -> str:
    return MARKDOWN_PATH.read_text(encoding="utf-8")


@pytest.fixture(scope="module")
def layout_paragraphs() -> dict[str, str]:
    """PL / ADR paragraphs re-derived from the layout extraction, independently.

    A paragraph is a run of non-blank lines; the layout file separates body
    paragraphs with blank lines. Running headers and footers end a run, so a
    requirement that had been cut at a page break would show up here as a
    paragraph that stops mid-sentence and the comparison below would fail.
    """
    paragraphs: dict[str, str] = {}
    run: list[str] = []

    def flush() -> None:
        for k, line in enumerate(run):
            match = re.match(r"^(PL-\d{3}|ADR-\d{3})[.:] ", line)
            if match:
                end = k + 1
                while end < len(run) and not re.match(r"^(PL-\d{3}|ADR-\d{3})[.:] ", run[end]):
                    end += 1
                paragraphs[match.group(1)] = " ".join(run[k:end])
        run.clear()

    for raw_line in LAYOUT_PATH.read_text(encoding="utf-8").split("\n"):
        text = raw_line.replace("\f", "").strip()
        if not text or FURNITURE.match(text):
            flush()
            continue
        run.append(text)
    flush()
    return paragraphs


def markdown_tables(markdown: str) -> list[tuple[list[str], list[list[str]]]]:
    """Return (header, rows) for every pipe table in the document."""
    tables: list[tuple[list[str], list[list[str]]]] = []
    lines = markdown.split("\n")
    i = 0
    while i < len(lines):
        if lines[i].startswith("|") and i + 1 < len(lines) and re.match(r"^\|(-+\|)+$", lines[i + 1]):
            header = [c.strip() for c in lines[i].strip("|").split("|")]
            rows: list[list[str]] = []
            i += 2
            while i < len(lines) and lines[i].startswith("|"):
                rows.append([c.strip() for c in lines[i].strip("|").split("|")])
                i += 1
            tables.append((header, rows))
            continue
        i += 1
    return tables


def table_by_header(markdown: str, header: list[str]) -> list[list[str]]:
    matches = [rows for hdr, rows in markdown_tables(markdown) if hdr == header]
    assert len(matches) == 1, f"expected exactly one table with header {header}, found {len(matches)}"
    return matches[0]


def mutated_copies(tmp_path: Path, transform) -> tuple[Path, Path]:
    """Write copies of both extractions with ``transform(text)`` applied."""
    raw_copy = tmp_path / "raw.txt"
    layout_copy = tmp_path / "layout.txt"
    raw_copy.write_text(transform(RAW_PATH.read_text(encoding="utf-8")), encoding="utf-8")
    layout_copy.write_text(transform(LAYOUT_PATH.read_text(encoding="utf-8")), encoding="utf-8")
    return raw_copy, layout_copy


# ---------------------------------------------------------------------------
# Index structure
# ---------------------------------------------------------------------------


@pytest.mark.requirements("PL-001", "PL-063")
def test_exactly_63_requirements_with_contiguous_ids(index: dict) -> None:
    ids = [r["id"] for r in index["requirements"]]
    assert ids == EXPECTED_IDS
    assert index["counts"]["requirements"] == 63
    assert index["spec_version"] == "0.2"
    assert index["spec_date"] == "2026-10-02"
    for requirement in index["requirements"]:
        assert set(requirement) == {"id", "section", "section_title", "text", "keywords"}
        assert requirement["text"] == " ".join(requirement["text"].split()), requirement["id"]
        assert not requirement["text"].startswith("PL-"), requirement["id"]
        assert requirement["text"].endswith("."), requirement["id"]


@pytest.mark.requirements("PL-001", "PL-004", "PL-063")
def test_requirement_sections_are_numbered_and_titled(index: dict) -> None:
    sections = {s["number"]: s["title"] for s in index["sections"]}
    assert [s["number"] for s in index["sections"]] == [str(n) for n in range(1, 30)]
    assert sections["1"] == "Product contract: Plumb performs the implementation"
    assert sections["29"] == "Primary sources and evidence boundaries"
    for requirement in index["requirements"]:
        assert requirement["section"] in sections, requirement["id"]
        assert requirement["section_title"] == sections[requirement["section"]], requirement["id"]
    by_id = {r["id"]: r for r in index["requirements"]}
    assert by_id["PL-001"]["section"] == "1"
    assert by_id["PL-004"]["section"] == "4"
    assert by_id["PL-057"]["section"] == "23"
    assert by_id["PL-063"]["section"] == "26"
    # Sections 2, 3, 27, 28 and 29 carry no PL requirement.
    assert {r["section"] for r in index["requirements"]} == {
        str(n) for n in range(1, 27) if n not in (2, 3)
    }


@pytest.mark.requirements("PL-001", "PL-051")
def test_every_requirement_contains_must_or_must_not(index: dict, builder: ModuleType) -> None:
    only_must_not: list[str] = []
    for requirement in index["requirements"]:
        text = requirement["text"]
        has_must = re.search(r"\bMUST\b(?! NOT\b)", text) is not None
        has_must_not = re.search(r"\bMUST NOT\b", text) is not None
        assert has_must or has_must_not, f"{requirement['id']} carries neither MUST nor MUST NOT"
        assert requirement["keywords"] == builder.keywords_of(text), requirement["id"]
        assert ("MUST" in requirement["keywords"]) is has_must, requirement["id"]
        assert ("MUST NOT" in requirement["keywords"]) is has_must_not, requirement["id"]
        if has_must_not and not has_must:
            only_must_not.append(requirement["id"])
    # PL-051 (hostile inputs) is the one requirement phrased purely as a prohibition.
    assert only_must_not == ["PL-051"]
    assert not any("SHOULD" in r["keywords"] or "MAY" in r["keywords"] for r in index["requirements"])


@pytest.mark.requirements("PL-001")
def test_keyword_detection_is_case_sensitive_and_token_based(builder: ModuleType) -> None:
    assert builder.keywords_of("Plumb MUST discover work. It MUST NOT stop.") == ["MUST", "MUST NOT"]
    assert builder.keywords_of("Untrusted documents MUST NOT change authority.") == ["MUST NOT"]
    assert builder.keywords_of("It must not. It should. It may.") == []
    assert builder.keywords_of("SHOULD denotes a default; MAY denotes a choice.") == ["SHOULD", "MAY"]
    assert builder.keywords_of("MUSTARD and MAYBE are not keywords.") == []


@pytest.mark.requirements("PL-006", "PL-017", "PL-038", "PL-062")
def test_exactly_10_adrs_with_title_and_rationale(index: dict) -> None:
    assert [a["id"] for a in index["adrs"]] == EXPECTED_ADR_IDS
    assert index["counts"]["adrs"] == 10
    for adr in index["adrs"]:
        assert set(adr) == {"id", "title", "rationale"}
        assert adr["title"] and not adr["title"].endswith("."), adr["id"]
        assert "Rationale" not in adr["title"], adr["id"]
        assert adr["rationale"].endswith("."), adr["id"]
    by_id = {a["id"]: a for a in index["adrs"]}
    assert by_id["ADR-001"]["title"] == "Separate engineering and runtime credentials"
    assert by_id["ADR-009"] == {
        "id": "ADR-009",
        "title": "Use explicit UNKNOWN for uncertain effects",
        "rationale": "automatic retries can duplicate irreversible actions.",
    }
    assert by_id["ADR-010"]["title"] == "Measure implementation autonomy separately from runtime autonomy"


@pytest.mark.requirements("PL-052", "PL-060")
def test_exactly_18_sources_with_urls(index: dict) -> None:
    assert [s["id"] for s in index["sources"]] == EXPECTED_SOURCE_IDS
    assert index["counts"]["sources"] == 18
    for source in index["sources"]:
        assert set(source) == {"id", "citation", "title", "annotation", "url", "urls"}
        assert source["citation"] == f"[{source['id']}]"
        assert source["url"].startswith("https://"), source["id"]
        assert source["urls"][0] == source["url"]
        assert all(u.startswith("https://") for u in source["urls"]), source["id"]
        assert source["title"] and source["annotation"].endswith("."), source["id"]
    by_id = {s["id"]: s for s in index["sources"]}
    assert by_id["S14"]["title"] == "PostgreSQL, Row Security Policies"
    assert by_id["S17"]["url"] == "https://opentelemetry.io/docs/specs/semconv/"
    assert by_id["S16"]["title"] == "OpenAPI Specification 3.1.1"
    assert by_id["S18"]["urls"] == [
        "https://docs.temporal.io/ai",
        "https://docs.temporal.io/activity-execution",
    ]
    # Requirements that cite a source cite one that exists.
    cited = {c for r in index["requirements"] for c in re.findall(r"\[(S\d{2})\]", r["text"])}
    assert cited == {"S14", "S17"}


# ---------------------------------------------------------------------------
# Verbatim text: layout cross-check and page boundaries
# ---------------------------------------------------------------------------


@pytest.mark.requirements(*PAGE_BOUNDARY_IDS)
def test_requirement_text_matches_layout_extraction(index: dict, layout_paragraphs: dict[str, str]) -> None:
    for requirement in index["requirements"]:
        paragraph = layout_paragraphs[requirement["id"]]
        expected = " ".join(paragraph.split(" ", 1)[1].split())
        assert requirement["text"] == expected, requirement["id"]


@pytest.mark.requirements(*PAGE_BOUNDARY_IDS)
def test_page_boundary_requirements_are_complete(index: dict, layout_paragraphs: dict[str, str]) -> None:
    by_id = {r["id"]: r["text"] for r in index["requirements"]}
    for pl_id in PAGE_BOUNDARY_IDS:
        text = by_id[pl_id]
        assert text.endswith("."), pl_id
        assert text == " ".join(layout_paragraphs[pl_id].split(" ", 1)[1].split()), pl_id
    assert by_id["PL-011"].endswith("revalidates dependent facts, datasets and plans.")
    assert by_id["PL-012"].endswith("review cost and a prospective measurement plan.")
    assert by_id["PL-016"].endswith("MUST NOT consume a failed or unverified prerequisite.")
    assert by_id["PL-025"].endswith("appear satisfied or unsatisfied by default.")
    assert by_id["PL-030"].endswith("mark it unavailable rather than falsifying reproducibility.")
    assert by_id["PL-039"].endswith("satisfying the same obligation with duplicate actions.")
    assert by_id["PL-044"].endswith("they do not establish business performance by themselves.")
    assert by_id["PL-047"].endswith("while preserving visibility and recovery.")
    assert by_id["PL-050"].endswith("latency, data terms or failure rates worsen.")
    assert by_id["PL-056"].endswith("stable opaque cursors with bounded page sizes.")


@pytest.mark.requirements("PL-006", "PL-062")
def test_adr_text_matches_layout_extraction(index: dict, layout_paragraphs: dict[str, str]) -> None:
    for adr in index["adrs"]:
        paragraph = " ".join(layout_paragraphs[adr["id"]].split())
        assert paragraph == f"{adr['id']}: {adr['title']}. Rationale: {adr['rationale']}"


@pytest.mark.requirements("PL-016", "PL-025")
def test_builder_rejoins_a_paragraph_split_by_a_page_break(builder: ModuleType) -> None:
    layout = [
        "PL-001. Alpha MUST hold while the page",
        "",
        "October 2, 2026 | Proposed system design              7",
        "\fPLUMB / AUTONOMOUS IMPLEMENTATION          ENGINEERING SPECIFICATION 0.2",
        "",
        "ends; beta follows.",
        "",
        "Unrelated prose that starts a new paragraph.",
        "",
        "PL-002. Gamma MUST end here.",
        "",
    ]
    extents = builder.paragraph_extents(layout)
    assert extents["PL-001"] == ["PL-001. Alpha MUST hold while the page", "ends; beta follows."]
    assert extents["PL-002"] == ["PL-002. Gamma MUST end here."]
    content = builder.strip_furniture(
        [
            "PL-001. Alpha MUST hold while the page",
            "October 2, 2026 | Proposed system design",
            "",
            "7",
            "",
            "\fPLUMB / AUTONOMOUS IMPLEMENTATION",
            "ENGINEERING SPECIFICATION 0.2",
            "ends; beta follows.",
        ]
    )
    assert content == ["PL-001. Alpha MUST hold while the page", "ends; beta follows."]


@pytest.mark.requirements("PL-057")
def test_strip_furniture_keeps_numbers_that_are_not_page_numbers(builder: ModuleType) -> None:
    content = builder.strip_furniture(["Count", "7", "October 2, 2026 | Proposed system design", "8", "Next"])
    assert content == ["Count", "7", "Next"]


# ---------------------------------------------------------------------------
# Negative tests: a damaged extraction is refused, never indexed silently
# ---------------------------------------------------------------------------


@pytest.mark.requirements("PL-030")
def test_truncated_requirement_is_rejected(builder: ModuleType, tmp_path: Path) -> None:
    dropped = "than falsifying reproducibility.\n"
    raw_copy = tmp_path / "raw.txt"
    raw_copy.write_text(RAW_PATH.read_text(encoding="utf-8").replace(dropped, ""), encoding="utf-8")
    with pytest.raises(builder.SpecParseError, match="PL-030"):
        builder.build_index(raw_copy, LAYOUT_PATH)


@pytest.mark.requirements("PL-047")
def test_layout_cut_at_page_break_without_continuation_is_rejected(builder: ModuleType, tmp_path: Path) -> None:
    # Remove PL-047's last line from the layout copy only: the reading-order
    # text then disagrees with the layout extents and the build must fail.
    last = "validated. Pausing an intervention blocks new external effects while preserving visibility and recovery.\n"
    layout_copy = tmp_path / "layout.txt"
    layout_copy.write_text(LAYOUT_PATH.read_text(encoding="utf-8").replace(last, ""), encoding="utf-8")
    with pytest.raises(builder.SpecParseError, match="PL-047"):
        builder.build_index(RAW_PATH, layout_copy)


@pytest.mark.requirements("PL-012")
def test_requirement_without_must_is_rejected(builder: ModuleType, tmp_path: Path) -> None:
    raw_copy, layout_copy = mutated_copies(
        tmp_path, lambda text: text.replace("PL-012. Every OpportunitySpec MUST state", "PL-012. Every OpportunitySpec must state")
    )
    with pytest.raises(builder.SpecParseError, match="PL-012: contains neither MUST nor MUST NOT"):
        builder.build_index(raw_copy, layout_copy)


@pytest.mark.requirements("PL-001", "PL-063")
def test_missing_requirement_breaks_contiguity_and_is_rejected(builder: ModuleType, tmp_path: Path) -> None:
    raw_copy, layout_copy = mutated_copies(tmp_path, lambda text: text.replace("PL-063. ", "PL-064. "))
    with pytest.raises(builder.SpecParseError, match="expected requirements PL-001..PL-063"):
        builder.build_index(raw_copy, layout_copy)


@pytest.mark.requirements("PL-001")
def test_duplicate_requirement_id_is_rejected(builder: ModuleType, tmp_path: Path) -> None:
    raw_copy, layout_copy = mutated_copies(tmp_path, lambda text: text.replace("PL-002. ", "PL-001. "))
    with pytest.raises(builder.SpecParseError):
        builder.build_index(raw_copy, layout_copy)


@pytest.mark.requirements("PL-038")
def test_adr_without_rationale_is_rejected(builder: ModuleType, tmp_path: Path) -> None:
    raw_copy, layout_copy = mutated_copies(
        tmp_path, lambda text: text.replace("uncertain effects. Rationale: automatic", "uncertain effects. Because automatic")
    )
    with pytest.raises(builder.SpecParseError, match="ADR-009: missing 'Rationale:'"):
        builder.build_index(raw_copy, layout_copy)


@pytest.mark.requirements("PL-052")
def test_source_without_url_is_rejected(builder: ModuleType, tmp_path: Path) -> None:
    raw_copy, layout_copy = mutated_copies(
        tmp_path, lambda text: text.replace("https://www.postgresql.org/docs/current/ddl-rowsecurity.html", "(link withheld)")
    )
    with pytest.raises(builder.SpecParseError):
        builder.build_index(raw_copy, layout_copy)


# ---------------------------------------------------------------------------
# Reproducibility and CLI
# ---------------------------------------------------------------------------


@pytest.mark.requirements("PL-030", "PL-046")
def test_build_script_reproduces_committed_json_byte_for_byte(tmp_path: Path) -> None:
    output = tmp_path / "requirements_index.json"
    result = subprocess.run(
        [sys.executable, str(SCRIPT), "--output", str(output)],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 0, result.stderr
    assert output.read_bytes() == INDEX_PATH.read_bytes()
    assert INDEX_PATH.read_text(encoding="utf-8").endswith("}\n")


@pytest.mark.requirements("PL-030", "PL-046")
def test_check_mode_passes_for_committed_file_and_fails_for_stale_file(tmp_path: Path) -> None:
    ok = subprocess.run(
        [sys.executable, str(SCRIPT), "--check"], cwd=REPO_ROOT, capture_output=True, text=True, check=False
    )
    assert ok.returncode == 0, ok.stderr
    assert "up to date" in ok.stdout

    stale = tmp_path / "stale.json"
    stale.write_text(INDEX_PATH.read_text(encoding="utf-8").replace('"spec_version": "0.2"', '"spec_version": "0.1"'))
    bad = subprocess.run(
        [sys.executable, str(SCRIPT), "--check", "--output", str(stale)],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
        check=False,
    )
    assert bad.returncode == 1
    assert "out of date" in bad.stderr


@pytest.mark.requirements("PL-030")
def test_stdout_mode_prints_the_same_json(index: dict) -> None:
    result = subprocess.run(
        [sys.executable, str(SCRIPT), "--output", "-"], cwd=REPO_ROOT, capture_output=True, text=True, check=False
    )
    assert result.returncode == 0, result.stderr
    assert json.loads(result.stdout) == index


# ---------------------------------------------------------------------------
# Normative Markdown
# ---------------------------------------------------------------------------


@pytest.mark.requirements("PL-001", "PL-063")
def test_markdown_contains_every_requirement_once_as_bold_token(markdown: str, index: dict) -> None:
    bold = re.findall(r"^\*\*(PL-\d{3})\.\*\* ", markdown, flags=re.M)
    assert bold == EXPECTED_IDS
    for pl_id in EXPECTED_IDS:
        assert len(re.findall(rf"\b{pl_id}\b", markdown)) == 1, pl_id
    paragraphs = dict(re.findall(r"^\*\*(PL-\d{3})\.\*\* (.+)$", markdown, flags=re.M))
    for requirement in index["requirements"]:
        assert paragraphs[requirement["id"]] == requirement["text"], requirement["id"]


@pytest.mark.requirements("PL-001", "PL-004", "PL-063")
def test_markdown_has_the_29_section_headings_and_appendices(markdown: str, index: dict) -> None:
    lines = markdown.split("\n")
    level_two = [line for line in lines if line.startswith("## ")]
    numbered = [line for line in level_two if re.match(r"^## \d{1,2}\. ", line)]
    assert len(numbered) == 29
    for section in index["sections"]:
        assert f"## {section['number']}. {section['title']}" in lines, section["number"]
    assert level_two[0] == "## Architecture at a glance"
    assert "## Appendix A. Agent execution protocol" in lines
    assert "## Appendix B. First complete customer trace" in lines
    assert "## Appendix C. Delivered reference package and verification" in lines
    assert sum(1 for line in lines if line.startswith("# ")) == 1
    # Headings follow the table of contents of the PDF, in order.
    raw = RAW_PATH.read_text(encoding="utf-8")
    contents = raw[raw.index("\nContents\n") : raw.index("Architecture at a glance\nAn agent")]
    toc_headings = re.findall(r"^(\d{1,2}\. .+|Appendix [A-C]\. .+)$", contents, flags=re.M)
    assert [h[3:] for h in level_two[1:]] == toc_headings
    appendix_a = [line for line in lines if re.match(r"^### \d\. ", line)]
    assert appendix_a == [
        "### 1. The unit of agent work",
        "### 2. Scheduler and step protocol",
        "### 3. Worker result contract and repair",
        "### 4. Model selection inside engineering work",
        "### 5. How useful automation accumulates",
        "### 6. Product surfaces the customer actually needs",
        "### 7. Staffing and sequencing assumptions",
    ]
    assert "### Goal and authority" in lines and "### Success and its denominator" in lines


@pytest.mark.requirements("PL-001")
def test_markdown_starts_with_conversion_note_and_title_block(markdown: str) -> None:
    lines = markdown.split("\n")
    assert lines[0] == CONVERSION_NOTE
    assert "# Autonomous Implementation System" in lines
    assert "Version 0.2 | October 2, 2026" in lines
    assert any(line.startswith("Prepared for ") for line in lines)
    assert any(line.startswith("Scope: normative system design") for line in lines)
    counts = [row for hdr, rows in markdown_tables(markdown) if hdr == ["63 requirements", "17 typed contracts"] for row in rows]
    assert counts == [["24 API operations", "56 passing local tests"]]
    assert "**Version 0.2 | Normative engineering specification | October 2, 2026**" in lines


@pytest.mark.requirements("PL-001")
def test_markdown_has_no_page_furniture(markdown: str) -> None:
    assert "ENGINEERING SPECIFICATION 0.2" not in markdown
    assert "PLUMB / AUTONOMOUS IMPLEMENTATION" not in markdown
    assert "Proposed system design" not in markdown
    assert re.search(r"^\d{1,2}$", markdown, flags=re.M) is None
    assert "\f" not in markdown
    assert "Contents" not in [line.strip() for line in markdown.split("\n")]
    # No hard-wrapped prose after the title block: every body line is a whole
    # paragraph, heading, table row or list item.
    body = markdown[markdown.index("## Architecture at a glance") :]
    for line in body.split("\n"):
        if line and not line.startswith(("|", "#", "-", "*", "1", "2", "3", "4", "5", "6", "7", "8")):
            assert line.rstrip().endswith((".", ":")), line


@pytest.mark.requirements("PL-057")
def test_markdown_aggregate_table_matches_shared_state_enums(markdown: str) -> None:
    rows = table_by_header(markdown, ["Aggregate", "Allowed lifecycle"])
    lifecycles = {row[0]: [s.strip() for s in row[1].split(",")] for row in rows}
    assert list(lifecycles) == ["Build", "Build step", "Collector", "Dataset", "Training", "Release", "Effect"]
    enums = {
        "Build": BuildState,
        "Build step": BuildStepState,
        "Collector": CollectorState,
        "Dataset": DatasetState,
        "Training": TrainingState,
        "Release": ReleaseState,
        "Effect": EffectState,
    }
    for aggregate, enum in enums.items():
        assert lifecycles[aggregate] == [member.value for member in enum], aggregate


@pytest.mark.requirements("PL-061", "PL-063")
def test_markdown_tables_are_rebuilt_and_page_split_tables_merged(markdown: str) -> None:
    design = table_by_header(markdown, ["Design question", "Decision"])
    assert [row[0] for row in design] == [
        "Who connects applications?",
        "Who establishes training data?",
        "Who chooses the model?",
        "Who deploys?",
        "Who fixes failures?",
        "Who decides that work is complete?",
    ]
    domains = table_by_header(markdown, ["Domain", "Owns", "Initial technology decision"])
    assert [row[0] for row in domains] == [
        "Control service",
        "Evidence workers",
        "Engineering workers",
        "Business workers",
        "Policy and action gateway",
        "Artifact and learning services",
        "Product interface",
    ]
    scenarios = table_by_header(markdown, ["Scenario", "Automatic implementation work", "Production boundary"])
    assert [row[0] for row in scenarios] == [
        "Accounting evidence preparation",
        "Industrial RFQ preparation",
        "Laundry route preparation",
    ]
    milestones = table_by_header(markdown, ["Milestone", "Required deliverable", "Evidence before proceeding"])
    assert [row[0].split(":")[0] for row in milestones] == ["M0", "M1", "M2", "M3", "M4", "M5", "M6"]
    tools = table_by_header(markdown, ["Proposed tool family", "What it may do", "What it cannot decide"])
    assert [row[0] for row in tools][:2] == ["artifact.read / artifact.propose", "source.describe / source.sample"]
    assert [row[0] for row in tools][-1] == "dependency.raise"
    assert len(tools) == 9
    failures = table_by_header(markdown, ["Failure class", "Automatic behavior", "Stop condition"])
    assert [row[0] for row in failures] == [
        "Transient provider/infrastructure failure",
        "Implementation defect",
        "Source schema/semantic change",
        "Missing authorization",
        "Missing business decision",
        "Unsupported capability",
        "Poor model quality",
    ]
    checks = table_by_header(markdown, ["Check", "Executed result"])
    assert len(checks) == 8
    assert ["Normative requirements", "63 indexed requirements"] in checks
    # Every table has consistent column counts and no repeated header rows.
    for header, rows in markdown_tables(markdown):
        assert all(len(row) == len(header) for row in rows), header
        assert header not in rows, header


@pytest.mark.requirements("PL-006", "PL-052", "PL-062")
def test_markdown_lists_adrs_and_sources_with_links(markdown: str, index: dict) -> None:
    lines = markdown.split("\n")
    for adr in index["adrs"]:
        assert f"- **{adr['id']}:** {adr['title']}. Rationale: {adr['rationale']}" in lines, adr["id"]
    for source in index["sources"]:
        matching = [line for line in lines if line.startswith(f"- **[{source['id']}]** ")]
        assert len(matching) == 1, source["id"]
        assert matching[0].startswith(f"- **[{source['id']}]** {source['title']}. {source['annotation']} ")
        for url in source["urls"]:
            assert f"<{url}>" in matching[0], source["id"]
    assert len(re.findall(r"^- \*\*\[S\d{2}\]\*\* ", markdown, flags=re.M)) == 18
    assert len(re.findall(r"^- \*\*ADR-\d{3}:\*\* ", markdown, flags=re.M)) == 10
