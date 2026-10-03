#!/usr/bin/env python3
"""Build ``spec/requirements_index.json`` from the extracted specification text.

The index is the machine-readable companion of the normative Markdown
(``spec/Plumb_Autonomous_Implementation_Specification_v0.2.md``). It lists the
63 requirements PL-001..PL-063 with their section, verbatim text and RFC-style
keywords, the ten architectural decisions ADR-001..ADR-010 of section 27 and
the eighteen primary sources [S01]..[S18] of section 29. ``scripts/validate.py``
and the test suite use it to build the requirement coverage matrix
(REFERENCE_PACKAGE_DESIGN.md section 10; specification section 28: "The source
Markdown is the normative specification").

Inputs
------
``docs/_spec_extracted_raw.txt``
    Reading-order text of the delivered PDF. It is the source of every
    character in the index. It carries no blank lines between body paragraphs,
    so on its own it cannot say where a requirement paragraph ends and the
    following prose begins.
``docs/_spec_extracted_layout.txt``
    Layout-preserving extraction of the same PDF. It separates paragraphs with
    blank lines and is used only to delimit the PL / ADR paragraphs. Every line
    taken from the reading-order file is cross-checked against the layout file;
    a mismatch is a hard error, so the two extractions cannot drift apart
    silently.

Page furniture (running headers, footers and page numbers) is removed, line
wraps are rejoined and whitespace is normalised to single spaces. A paragraph
that stops mid-sentence at a page break is continued on the next page.

Usage
-----
::

    python3 spec/build_requirements_index.py            # write spec/requirements_index.json
    python3 spec/build_requirements_index.py --output - # print the JSON to stdout
    python3 spec/build_requirements_index.py --check    # rebuild and compare with the committed file

The output is deterministic: running the script twice yields byte-identical
files.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Iterable, Sequence

REPO_ROOT = Path(__file__).resolve().parent.parent
DEFAULT_SOURCE = REPO_ROOT / "docs" / "_spec_extracted_raw.txt"
DEFAULT_LAYOUT = REPO_ROOT / "docs" / "_spec_extracted_layout.txt"
DEFAULT_OUTPUT = REPO_ROOT / "spec" / "requirements_index.json"

SPEC_TITLE = "Autonomous Implementation System"
SPEC_VERSION = "0.2"
SPEC_DATE = "2026-10-02"
SPEC_DATE_TEXT = "October 2, 2026"
TITLE_PAGE_VERSION_LINE = f"Version {SPEC_VERSION} | {SPEC_DATE_TEXT}"

EXPECTED_REQUIREMENTS = 63
EXPECTED_ADRS = 10
EXPECTED_SOURCES = 18
EXPECTED_SECTIONS = 29
EXPECTED_APPENDICES = ("A", "B", "C")

RUNNING_HEADER = "PLUMB / AUTONOMOUS IMPLEMENTATION"
RUNNING_SUBHEADER = f"ENGINEERING SPECIFICATION {SPEC_VERSION}"
RUNNING_FOOTER = f"{SPEC_DATE_TEXT} | Proposed system design"

REQUIREMENT_MARKER = re.compile(r"^(PL-\d{3})\. (.*)$")
ADR_MARKER = re.compile(r"^(ADR-\d{3}): (.*)$")
SOURCE_MARKER = re.compile(r"^\[(S\d{2})\] (.*)$")
SECTION_HEADING = re.compile(r"^(\d{1,2})\. (\S.*)$")
APPENDIX_HEADING = re.compile(r"^Appendix ([A-Z])\. (\S.*)$")
PAGE_NUMBER = re.compile(r"^\d{1,2}$")
URL = re.compile(r"https?://\S+")
SENTENCE_END = re.compile(r"[.!?]['\")\]]*$")
FIRST_SENTENCE = re.compile(r"^(.*?)\. (?=[A-Z])")

KEYWORD_PATTERNS: tuple[tuple[str, re.Pattern[str]], ...] = (
    ("MUST", re.compile(r"\bMUST\b(?! NOT\b)")),
    ("MUST NOT", re.compile(r"\bMUST NOT\b")),
    ("SHOULD", re.compile(r"\bSHOULD\b")),
    ("MAY", re.compile(r"\bMAY\b")),
)


class SpecParseError(ValueError):
    """The extracted text does not have the structure the index relies on."""


@dataclass(frozen=True)
class Section:
    number: str
    title: str

    @property
    def heading(self) -> str:
        return f"{self.number}. {self.title}"


@dataclass(frozen=True)
class Appendix:
    letter: str
    title: str

    @property
    def heading(self) -> str:
        return f"Appendix {self.letter}. {self.title}"


@dataclass(frozen=True)
class Requirement:
    id: str
    section: str
    section_title: str
    text: str
    keywords: list[str]


@dataclass(frozen=True)
class Adr:
    id: str
    title: str
    rationale: str


@dataclass(frozen=True)
class Source:
    id: str
    citation: str
    title: str
    annotation: str
    url: str
    urls: list[str]


# ---------------------------------------------------------------------------
# Text helpers
# ---------------------------------------------------------------------------


def normalise(text: str) -> str:
    """Collapse all whitespace runs to single spaces and trim."""
    return " ".join(text.split())


def join_wrapped(lines: Iterable[str]) -> str:
    """Rejoin lines that the PDF wrapped mid-sentence."""
    return normalise(" ".join(lines))


def ends_sentence(line: str) -> bool:
    return bool(SENTENCE_END.search(line))


def keywords_of(text: str) -> list[str]:
    """Which of MUST, MUST NOT, SHOULD, MAY occur in ``text`` (canonical order)."""
    return [name for name, pattern in KEYWORD_PATTERNS if pattern.search(text)]


def is_furniture(text: str) -> bool:
    """Running header / footer lines in either extraction (page numbers excluded)."""
    return (
        text.startswith(RUNNING_HEADER)
        or text == RUNNING_SUBHEADER
        or text.startswith(RUNNING_FOOTER)
    )


# ---------------------------------------------------------------------------
# Reading-order extraction
# ---------------------------------------------------------------------------


def read_text_lines(path: Path) -> list[str]:
    return path.read_text(encoding="utf-8").split("\n")


def strip_furniture(lines: Sequence[str]) -> list[str]:
    """Drop headers, footers, page numbers and blank lines; keep reading order.

    A page number is only recognised directly after the footer so that a
    standalone number inside a table can never be mistaken for one.
    """
    content: list[str] = []
    expect_page_number = False
    for raw in lines:
        text = raw.replace("\f", "").strip()
        if not text:
            continue
        if text.startswith(RUNNING_FOOTER):
            expect_page_number = True
            continue
        if expect_page_number and PAGE_NUMBER.match(text):
            expect_page_number = False
            continue
        expect_page_number = False
        if is_furniture(text):
            continue
        content.append(text)
    return content


def parse_contents(content: list[str]) -> tuple[list[Section], list[Appendix], int]:
    """Read the table of contents.

    Returns the numbered sections, the appendices and the index of the first
    content line after the contents block (the second "Architecture at a
    glance" occurrence, which opens the body).
    """
    try:
        start = content.index("Contents")
    except ValueError as exc:
        raise SpecParseError("contents block not found") from exc
    sections: list[Section] = []
    appendices: list[Appendix] = []
    i = start + 1
    while i < len(content):
        text = content[i]
        if PAGE_NUMBER.match(text):
            i += 1
            continue
        if text == "Architecture at a glance":
            if sections:
                break
            i += 1
            continue
        section = SECTION_HEADING.match(text)
        appendix = APPENDIX_HEADING.match(text)
        if section:
            sections.append(Section(section.group(1), section.group(2)))
        elif appendix:
            appendices.append(Appendix(appendix.group(1), appendix.group(2)))
        else:
            raise SpecParseError(f"unexpected line in contents: {text!r}")
        i += 1
    if len(sections) != EXPECTED_SECTIONS:
        raise SpecParseError(f"expected {EXPECTED_SECTIONS} sections, found {len(sections)}")
    if [a.letter for a in appendices] != list(EXPECTED_APPENDICES):
        raise SpecParseError(f"unexpected appendices: {[a.letter for a in appendices]}")
    if [s.number for s in sections] != [str(n) for n in range(1, EXPECTED_SECTIONS + 1)]:
        raise SpecParseError("section numbers are not 1..29 in order")
    return sections, appendices, i


def match_heading(content: list[str], index: int, headings: dict[str, str]) -> tuple[str, int] | None:
    """Recognise a (possibly two-line) heading at ``index``.

    Returns the heading key and the number of lines it occupies, or ``None``.
    """
    one = content[index]
    if one in headings:
        return headings[one], 1
    if index + 1 < len(content):
        two = f"{one} {content[index + 1]}"
        if two in headings:
            return headings[two], 2
    return None


# ---------------------------------------------------------------------------
# Layout extraction: paragraph extents
# ---------------------------------------------------------------------------


def layout_runs(lines: Sequence[str]) -> list[list[str]]:
    """Runs of consecutive non-blank, non-furniture lines of the layout file."""
    runs: list[list[str]] = []
    current: list[str] = []
    for raw in lines:
        text = raw.replace("\f", "").strip()
        if not text or is_furniture(text):
            if current:
                runs.append(current)
                current = []
            continue
        current.append(text)
    if current:
        runs.append(current)
    return runs


def _is_marker(text: str) -> bool:
    return bool(REQUIREMENT_MARKER.match(text) or ADR_MARKER.match(text))


def paragraph_extents(layout_lines: Sequence[str]) -> dict[str, list[str]]:
    """Map each PL-xxx / ADR-xxx marker to the full lines of its paragraph.

    A paragraph is the marker line and the lines that follow it inside the
    same blank-line delimited run. When the run stops without sentence-final
    punctuation the paragraph was split by a page break and continues in the
    next run.
    """
    runs = layout_runs(layout_lines)
    extents: dict[str, list[str]] = {}
    for run_index, run in enumerate(runs):
        for k, line in enumerate(run):
            if not _is_marker(line):
                continue
            end = k + 1
            while end < len(run) and not _is_marker(run[end]):
                end += 1
            paragraph = run[k:end]
            follow = run_index + 1
            while end == len(run) and not ends_sentence(paragraph[-1]) and follow < len(runs):
                continuation = runs[follow]
                cut = 0
                while cut < len(continuation) and not _is_marker(continuation[cut]):
                    cut += 1
                paragraph = paragraph + continuation[:cut]
                if cut < len(continuation):
                    break
                follow += 1
            marker = line.split(" ", 1)[0].rstrip(".:")
            if marker in extents:
                raise SpecParseError(f"duplicate marker in layout text: {marker}")
            extents[marker] = paragraph
    return extents


# ---------------------------------------------------------------------------
# Index construction
# ---------------------------------------------------------------------------


def _take_paragraph(content: list[str], index: int, expected: list[str], marker: str) -> list[str]:
    """Take ``len(expected)`` reading-order lines and cross-check them."""
    lines = content[index : index + len(expected)]
    if lines != expected:
        raise SpecParseError(
            f"{marker}: reading-order text disagrees with layout text\n"
            f"  reading-order: {lines}\n  layout:        {expected}"
        )
    if not ends_sentence(lines[-1]):
        raise SpecParseError(f"{marker}: paragraph does not end a sentence: {lines[-1]!r}")
    return lines


def parse_adr(lines: list[str]) -> Adr:
    match = ADR_MARKER.match(lines[0])
    assert match is not None
    body = join_wrapped([match.group(2), *lines[1:]])
    title, separator, rationale = body.partition(" Rationale: ")
    if not separator or not rationale:
        raise SpecParseError(f"{match.group(1)}: missing 'Rationale:' clause")
    return Adr(id=match.group(1), title=title.rstrip("."), rationale=rationale)


def parse_source(lines: list[str]) -> Source:
    match = SOURCE_MARKER.match(lines[0])
    assert match is not None
    body = join_wrapped([match.group(2), *lines[1:]])
    urls = URL.findall(body)
    if not urls:
        raise SpecParseError(f"[{match.group(1)}]: no URL")
    description = normalise(body[: body.index(urls[0])])
    first = FIRST_SENTENCE.match(description)
    if first is None:
        raise SpecParseError(f"[{match.group(1)}]: cannot split title from annotation: {description!r}")
    title = first.group(1)
    annotation = description[first.end() :]
    return Source(
        id=match.group(1),
        citation=f"[{match.group(1)}]",
        title=title,
        annotation=annotation,
        url=urls[0],
        urls=urls,
    )


def build_index(source_path: Path = DEFAULT_SOURCE, layout_path: Path = DEFAULT_LAYOUT) -> dict:
    """Parse both extractions and return the index as a JSON-ready dict."""
    content = strip_furniture(read_text_lines(source_path))
    if TITLE_PAGE_VERSION_LINE not in content:
        raise SpecParseError(f"title page line {TITLE_PAGE_VERSION_LINE!r} not found")
    sections, appendices, body_start = parse_contents(content)
    extents = paragraph_extents(read_text_lines(layout_path))

    headings = {s.heading: s.number for s in sections}
    headings.update({a.heading: a.letter for a in appendices})
    section_by_number = {s.number: s for s in sections}

    requirements: list[Requirement] = []
    adrs: list[Adr] = []
    sources: list[Source] = []
    current_section: Section | None = None

    i = body_start
    while i < len(content):
        heading = match_heading(content, i, headings)
        if heading is not None:
            key, used = heading
            current_section = section_by_number.get(key)
            i += used
            continue
        line = content[i]
        requirement = REQUIREMENT_MARKER.match(line)
        adr = ADR_MARKER.match(line)
        source = SOURCE_MARKER.match(line)
        if requirement:
            marker = requirement.group(1)
            if marker not in extents:
                raise SpecParseError(f"{marker}: not found in layout text")
            lines = _take_paragraph(content, i, extents[marker], marker)
            if current_section is None:
                raise SpecParseError(f"{marker}: appears before any numbered section")
            text = join_wrapped([requirement.group(2), *lines[1:]])
            requirements.append(
                Requirement(
                    id=marker,
                    section=current_section.number,
                    section_title=current_section.title,
                    text=text,
                    keywords=keywords_of(text),
                )
            )
            i += len(lines)
            continue
        if adr:
            marker = adr.group(1)
            if marker not in extents:
                raise SpecParseError(f"{marker}: not found in layout text")
            lines = _take_paragraph(content, i, extents[marker], marker)
            adrs.append(parse_adr(lines))
            i += len(lines)
            continue
        if source:
            end = i
            while end < len(content) and not URL.search(content[end]):
                end += 1
            if end == len(content):
                raise SpecParseError(f"[{source.group(1)}]: no URL line")
            sources.append(parse_source(content[i : end + 1]))
            i = end + 1
            continue
        i += 1

    _validate(requirements, adrs, sources)
    return {
        "spec_title": SPEC_TITLE,
        "spec_version": SPEC_VERSION,
        "spec_date": SPEC_DATE,
        "generated_by": "spec/build_requirements_index.py",
        "source_files": [_display_path(source_path), _display_path(layout_path)],
        "counts": {
            "sections": len(sections),
            "requirements": len(requirements),
            "adrs": len(adrs),
            "sources": len(sources),
        },
        "sections": [asdict(s) for s in sections],
        "appendices": [asdict(a) for a in appendices],
        "requirements": [asdict(r) for r in requirements],
        "adrs": [asdict(a) for a in adrs],
        "sources": [asdict(s) for s in sources],
    }


def _display_path(path: Path) -> str:
    """Repository-relative path when the file lives in the repository."""
    resolved = path.resolve()
    if resolved.is_relative_to(REPO_ROOT):
        return resolved.relative_to(REPO_ROOT).as_posix()
    return str(path)


def _validate(requirements: list[Requirement], adrs: list[Adr], sources: list[Source]) -> None:
    ids = [r.id for r in requirements]
    expected_ids = [f"PL-{n:03d}" for n in range(1, EXPECTED_REQUIREMENTS + 1)]
    if ids != expected_ids:
        raise SpecParseError(
            f"expected requirements {expected_ids[0]}..{expected_ids[-1]} in order, found {len(ids)}: {ids}"
        )
    for requirement in requirements:
        if not any(k.startswith("MUST") for k in requirement.keywords):
            raise SpecParseError(f"{requirement.id}: contains neither MUST nor MUST NOT")
    adr_ids = [a.id for a in adrs]
    if adr_ids != [f"ADR-{n:03d}" for n in range(1, EXPECTED_ADRS + 1)]:
        raise SpecParseError(f"expected {EXPECTED_ADRS} ADRs in order, found {adr_ids}")
    source_ids = [s.id for s in sources]
    if source_ids != [f"S{n:02d}" for n in range(1, EXPECTED_SOURCES + 1)]:
        raise SpecParseError(f"expected {EXPECTED_SOURCES} sources in order, found {source_ids}")


def render_index(index: dict) -> str:
    """Serialise deterministically (UTF-8, two-space indent, trailing newline)."""
    return json.dumps(index, indent=2, ensure_ascii=False) + "\n"


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n\n", 1)[0])
    parser.add_argument("--source", type=Path, default=DEFAULT_SOURCE, help="reading-order extraction")
    parser.add_argument("--layout", type=Path, default=DEFAULT_LAYOUT, help="layout-preserving extraction")
    parser.add_argument(
        "--output",
        type=str,
        default=str(DEFAULT_OUTPUT),
        help="where to write the JSON ('-' for stdout)",
    )
    parser.add_argument(
        "--check",
        action="store_true",
        help="do not write; exit 1 if the rebuilt index differs from --output",
    )
    args = parser.parse_args(argv)

    try:
        rendered = render_index(build_index(args.source, args.layout))
    except SpecParseError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2

    if args.check:
        committed = Path(args.output)
        if not committed.exists():
            print(f"error: {committed} does not exist", file=sys.stderr)
            return 1
        if committed.read_text(encoding="utf-8") != rendered:
            print(f"error: {committed} is out of date; rerun without --check", file=sys.stderr)
            return 1
        print(f"ok: {committed} is up to date")
        return 0

    if args.output == "-":
        sys.stdout.write(rendered)
        return 0
    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(rendered, encoding="utf-8")
    print(f"wrote {output}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
