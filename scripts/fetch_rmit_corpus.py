#!/usr/bin/env python3
"""Build the fixed nine-document RMIT Library corpus used by group B3_HKT.

This is a deliberately bounded fetcher, not a general crawler: it requests only
the nine public URLs listed below and extracts the page's main AEM content area.
The generated Markdown keeps headings and lists because they are meaningful
boundaries for the chunking benchmark.
"""

from __future__ import annotations

import csv
import re
from dataclasses import dataclass
from pathlib import Path

import requests
from bs4 import BeautifulSoup, Tag


ROOT = Path(__file__).resolve().parents[1]
OUTPUT_DIR = ROOT / "data" / "rmit-library"
USER_AGENT = "B3-HKT-Lab7/1.0 (+educational corpus; nine public pages only)"


@dataclass(frozen=True)
class Source:
    doc_id: str
    title: str
    url: str
    audience: str
    category: str
    section: str | None = None


SOURCES = (
    Source(
        "rmit-accessibility-resources",
        "Resources for students with a disability",
        "https://www.rmit.edu.vn/libraryvn/student-support/resources-for-students-with-a-disability",
        "student",
        "accessibility",
    ),
    Source(
        "rmit-borrowing-returning",
        "Borrowing and returning",
        "https://www.rmit.edu.vn/libraryvn/borrowing-and-resources/borrowing-and-returning",
        "all",
        "borrowing-policy",
    ),
    Source(
        "rmit-develop-course-content",
        "Develop course content",
        "https://www.rmit.edu.vn/libraryvn/teacher-support/developing-course-content",
        "faculty",
        "teacher-support",
    ),
    Source(
        "rmit-library-hours-locations",
        "Library hours and locations",
        "https://www.rmit.edu.vn/libraryvn/about-us/hours-and-locations",
        "all",
        "opening-hours",
    ),
    Source(
        "rmit-library-resources",
        "Library resources and collections",
        "https://www.rmit.edu.vn/libraryvn/borrowing-and-resources/library-resources",
        "all",
        "library-resources",
    ),
    Source(
        "rmit-library-rules",
        "RMIT Vietnam Library rules",
        "https://www.rmit.edu.vn/libraryvn/about-us",
        "all",
        "library-rules",
        section="Library rules",
    ),
    Source(
        "rmit-study-faq",
        "Study FAQs",
        "https://www.rmit.edu.vn/libraryvn/student-support/study-faq",
        "student",
        "student-support",
    ),
    Source(
        "rmit-study-room-booking",
        "Book a study room",
        "https://www.rmit.edu.vn/libraryvn/student-support/book-a-study-room",
        "student",
        "room-booking",
    ),
    Source(
        "rmit-workshops-consultations",
        "Workshops and consultations for students",
        "https://www.rmit.edu.vn/libraryvn/teacher-support/organise-workshops-and-consultations-for-your-students",
        "faculty",
        "teacher-support",
    ),
)


def _normalize(value: str) -> str:
    return re.sub(r"\s+", " ", value).strip()


def _main_content(soup: BeautifulSoup) -> Tag:
    body_grid = soup.select_one(".body-gridcontent")
    if body_grid is not None and len(body_grid.get_text(" ", strip=True)) >= 80:
        return body_grid

    # Study FAQs is loaded in a sibling AEM fragment, so choose the root with
    # the richest heading structure instead of a navigation/footer root.
    roots = soup.select(".root")
    if not roots:
        raise ValueError("RMIT page does not contain an AEM .root element")
    return max(
        roots,
        key=lambda element: (
            len(element.select("h2")),
            len(element.get_text(" ", strip=True)),
        ),
    )


def _render_markdown(root: Tag, source: Source) -> str:
    blocks: list[str] = []
    in_requested_section = source.section is None

    for element in root.find_all(["h1", "h2", "h3", "h4", "h5", "h6", "p", "li"]):
        if element.find_parent(class_="modal") is not None:
            continue  # hidden video transcript duplicates visible content
        if element.name == "li" and element.get("role") == "presentation":
            continue  # tab navigation, not article content
        if any(parent.name in {"p", "li"} for parent in element.parents if parent is not root):
            continue  # avoid nested text being emitted twice

        text = _normalize(element.get_text(" ", strip=True))
        if not text:
            continue

        if source.section is not None:
            if element.name == "h2" and text == source.section:
                in_requested_section = True
            elif in_requested_section and element.name == "h2":
                break
            if not in_requested_section:
                continue

        if element.name.startswith("h"):
            blocks.append(f"{'#' * int(element.name[1])} {text}")
        elif element.name == "li":
            blocks.append(f"- {text}")
        else:
            blocks.append(text)

    if not blocks:
        raise ValueError(f"no article content extracted from {source.url}")
    return f"# {source.title}\n\n" + "\n\n".join(blocks) + "\n"


def _front_matter(source: Source) -> str:
    fields = {
        "doc_id": source.doc_id,
        "title": source.title,
        "source_url": source.url,
        "retrieved_at": "2026-08-03",
        "document_version": "not-stated",
        "audience": source.audience,
        "department": "library",
        "category": source.category,
        "language": "en",
    }
    rows = ["---", *(f'{key}: "{value}"' for key, value in fields.items()), "---", ""]
    return "\n".join(rows)


def main() -> int:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    manifest_rows: list[dict[str, str]] = []

    session = requests.Session()
    session.headers.update({"User-Agent": USER_AGENT, "Accept": "text/html"})
    for source in SOURCES:
        response = session.get(source.url, timeout=30)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, "html.parser")
        body = _render_markdown(_main_content(soup), source)
        path = OUTPUT_DIR / f"{source.doc_id}.md"
        path.write_text(_front_matter(source) + body, encoding="utf-8")
        manifest_rows.append(
            {
                "doc_id": source.doc_id,
                "file_path": str(path.relative_to(ROOT)),
                "title": source.title,
                "source_url": source.url,
                "retrieved_at": "2026-08-03",
                "document_version": "not-stated",
                "license_or_permission": "public-source",
            }
        )
        print(f"Saved {path.relative_to(ROOT)} ({len(body)} body characters)")

    with (OUTPUT_DIR / "sources.csv").open("w", encoding="utf-8", newline="") as target:
        writer = csv.DictWriter(target, fieldnames=manifest_rows[0].keys())
        writer.writeheader()
        writer.writerows(manifest_rows)
    print(f"Saved {OUTPUT_DIR.relative_to(ROOT) / 'sources.csv'} ({len(manifest_rows)} rows)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
