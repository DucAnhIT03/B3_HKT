#!/usr/bin/env python3
"""Clean the RMIT HTML-to-Markdown corpus produced by fetch_public_pages.py.

The generic crawler intentionally keeps visible text. RMIT pages render part
of their navigation as ordinary divs, so those labels survive the initial
HTML extraction. This script keeps the YAML front matter and source wording,
then removes that repeated interface text and restores useful Markdown
structure for chunking experiments.
"""

from __future__ import annotations

import argparse
import re
from pathlib import Path


RULES = {
    "rmit-accessibility-resources.md": {
        "start": "If you are an RMIT student with a disability, the library is here to help, with a dedicated librarian and multiple resources.",
        "start_occurrence": "last",
        "end": "Helpful links",
        "h2": {"Wheelchair access", "Equitable Learning and Accessibility"},
        "h3": {"Meet our ELA librarian"},
        "bullets": {
            "Text digitisation",
            "Helping to obtain digital resources",
            "Converting documents from PDF to text",
        },
        "drop": {"Email Thi"},
    },
    "rmit-borrowing-returning.md": {
        "start": "Learn how to borrow, renew and return library items with ease.",
        "start_occurrence": "last",
        "end": "Helpful links",
        "h2": {
            "Borrowing for students, staff and alumni",
            "Returns",
            "Lost or damaged items",
            "Damage fees",
            "Disputes",
        },
        "h3": {"Student", "Staff", "Alumni"},
        "h4": {
            "English students",
            "Undergraduate and postgraduate students",
            "Academic staff",
            "Professional staff",
            "Major damages will be charged a replacement fee",
            "Minor damages will be charged a repair fee",
            "Audio-visual materials (CDs-DVDs)",
            "If you disagree with the library fine",
            "We will not accept the following reasons",
        },
        "drop": {
            "Details on how to log in to your account and check on your borrowing details are located on Borrowing and resources.",
        },
        "bullets": {
            "The cover is noticeably damaged or missing.",
            "Or pages are stained, missing, illegible, or otherwise warped.",
            "Or there is heavy writing and/ or highlighting throughout the book.",
            "Or any other conditions that make the book unusable, including exposure to chemicals, cleaning agents, perfumes or tobacco smoke, etc. that causes a noticeable odour.",
            "Lack of knowledge of library polices",
            "Unwillingness to take responsibility for material loaned to a third party",
            "Forgetting the due date",
            "Not receiving library reminders, either via email or in the mail",
            "Email inbox was full",
            "Unable to visit the library often or distance from the library",
            "Disagreement with the library fine policy",
            "Not being on campus",
            "Semester breaks, summer vacation",
            "Changed opening hours",
        },
    },
    "rmit-course-content-support.md": {
        "start": "Lecturers are provided with a wide range of credible academic resources and expert support in sourcing, scanning, linking and embedding these in course content.",
        "end": "Helpful links",
        "h2": {
            "The eReserve service",
            "Reading list assistance",
            "Library collections",
            "Add library resources to Canvas",
            "Purchasing books",
        },
    },
    "rmit-library-hours.md": {
        "start": "RMIT Vietnam has two locations, The Beanland library and The Hanoi library.",
        "start_occurrence": "last",
        "end": "Helpful links",
        "h2": {"Saigon South campus", "Hanoi campus"},
        "h3": {
            "During semester",
            "Semester break",
            "Address",
            "Contacts",
            "Wheelchair access",
            "Take the Saigon South campus library virtual tour",
            "Take the Hanoi campus library virtual tour",
        },
        "drop": {"Take a virtual tour"},
    },
    "rmit-library-resources.md": {
        "start": "The library provides online resources, assistance with how to use the information and showcases Vietnam-only archives and collections.",
        "end": "Helpful links",
        "h2": {
            "Online resources",
            "Digital Vietnamese art collection and archive",
            "Copyright advice",
        },
        "h3": {
            "Library databases",
            "Google Scholar",
            "Library subject guides",
            "Research repository",
            "Statista",
            "Open Educational Resources",
            "Video and audio collection",
            "Not sure where to start?",
            "Can’t find it in the library?",
            "Access problems?",
            "Using assistive technology?",
            "ProQuest",
            "EBSCO",
            "Other databases",
            "Urban archive of Ho Chi Minh City",
            "Typography in Vietnam",
        },
    },
    "rmit-library-rules.md": {
        "start": "Find your liaison librarian, library rules and discover the library locations.",
        "start_occurrence": "last",
        "end": "What's on",
        "h2": {"Meet the library team", "Hours and locations", "Library rules"},
        "bullets": {
            "The library can only be used by RMIT University staff, students and alumni",
            "Photocopied books are not allowed on campus",
            "The IT rules of use are enforced and no computer games are allowed",
            "Users can bring beverages but not food into the library",
            "Students who disrupt the use of facilities, collections or services shall be requested to leave",
            "English is the only language to be used in the library",
        },
    },
    "rmit-study-faq.md": {
        "start": "Evaluating sources",
        "end": "Helpful links",
        "h2": {
            "Evaluating sources",
            "Citing and referencing (RMIT Harvard style)",
            "Search strategy",
            "Databases",
            "Google Scholar",
        },
        "h4": {
            "Works in the original language (non-English)",
            "For film titles",
            "For other types",
            "Market vs. Industry Reports",
            "Market Reports",
            "Industry Reports",
            "Sources:",
            "References:",
        },
    },
    "rmit-study-room-booking.md": {
        "start": "The Library offers bookable study rooms that give you a place to learn, collaborate and prepare for your assignments.",
        "start_occurrence": "last",
        "end": "Helpful links",
        "h2": {"Check for availability", "How to book a room", "Booking policy", "Equipment in the meeting room"},
        "h3": {"General", "Booking quotas and how to check-in"},
        "drop": {"Transcript", "Back to Video", "Study room booking instructions (PDF)"},
        "dedupe": {
            "How to book a Library study room",
            "Simply log in with your RMIT account, choose your campus, select a room and time and confirm your booking.",
        },
        "bullets": {
            "All study rooms at the Library are available for use on a first-come, first-served basis. Students are advised to plan their bookings prior to the meeting time 2 weeks ahead",
            "Students must check-in at the library front desk within 15 minutes prior to their scheduled bookings. Or else, bookings will be canceled, and slots will become available for other students to book",
            "The system only allows booking during the Library operation hours",
            "Students must clean up after using the meeting room",
            "Table and chairs",
        },
    },
    "rmit-teacher-workshops.md": {
        "start": "The library offers a wide range of library workshops to teach students research skills for general research purposes and for specific assignment requirements.",
        "end": "Helpful links",
        "h2": {"Tailored workshops for specific courses", "Library tutorials", "Research consultations"},
        "h3": {"Set up a research consultation"},
        "drop": {"Make the most of the library", "Find a liaison librarian"},
        "bullets": {
            "Commerce, Management",
            "Economics, Finance, Marketing, Accountancy",
            "Professional Communication, Design, Fashion",
            "IT, Engineering",
            "MBA",
            "English",
            "Research advice for a student's research assignment",
            "Instruction on how to search the library online databases",
            "Instruction on how to evaluate and reference your sources",
        },
    },
}


GLOBAL_DROP = {
    "Expand all sections",
    "Collapse all sections",
    "Expand all sectionsCollapse all sections",
}


def split_front_matter(raw: str) -> tuple[str, str]:
    if not raw.startswith("---\n"):
        raise ValueError("missing YAML front matter")
    boundary = raw.find("\n---\n", 4)
    if boundary < 0:
        raise ValueError("unterminated YAML front matter")
    front_matter = raw[: boundary + 5].rstrip()
    body = raw[boundary + 5 :].lstrip("\n")
    return front_matter, body


def normalize_line(line: str) -> str:
    return re.sub(r"[\t \u00a0\u202f]+", " ", line).strip()


def find_boundary(lines: list[str], marker: str, occurrence: str = "first") -> int:
    matches = [index for index, line in enumerate(lines) if line == marker]
    if not matches:
        raise ValueError(f"content marker not found: {marker!r}")
    return matches[-1] if occurrence == "last" else matches[0]


def should_be_bullet(line: str, explicit: set[str]) -> bool:
    if line in explicit:
        return True
    prefixes = (
        "Loan quota -",
        "Loan period -",
        "Renewals -",
        "Repair fee:",
        "Replacement fee =",
        "Monday to Friday",
        "Saturday and Sunday:",
        "Exam Time ",
        "Email:",
        "Phone:",
        "May book up to ",
        "1 hour maximum/",
        "2 bookings maximum/",
        "1 representative from ",
        "1 whiteboard",
        "1 TV screen",
        "On request:",
    )
    return line.startswith(prefixes)


def clean_document(path: Path, rule: dict) -> None:
    raw = path.read_text(encoding="utf-8")
    front_matter, body = split_front_matter(raw)
    body_lines = [normalize_line(line) for line in body.splitlines()]

    start = find_boundary(body_lines, rule["start"], rule.get("start_occurrence", "first"))
    end = find_boundary(body_lines[start + 1 :], rule["end"]) + start + 1
    content = body_lines[start:end]

    title_match = re.search(r'^title:\s*"?(.*?)"?\s*$', front_matter, re.MULTILINE)
    if not title_match:
        raise ValueError("front matter has no title")
    title = title_match.group(1)

    h2 = rule.get("h2", set())
    h3 = rule.get("h3", set())
    h4 = rule.get("h4", set())
    bullets = rule.get("bullets", set())
    drop = GLOBAL_DROP | rule.get("drop", set())
    dedupe = rule.get("dedupe", set())
    seen_dedupe: set[str] = set()

    blocks = [f"# {title}"]
    previous = ""
    for line in content:
        if not line or line in drop:
            continue
        if line == previous:
            continue
        if line in dedupe:
            if line in seen_dedupe:
                continue
            seen_dedupe.add(line)

        if line in h2:
            rendered = f"## {line}"
        elif line in h3:
            rendered = f"### {line}"
        elif line in h4:
            rendered = f"#### {line}"
        elif path.name == "rmit-study-faq.md" and line.endswith("?"):
            rendered = f"### {line}"
        elif should_be_bullet(line, bullets):
            rendered = f"- {line}"
        else:
            rendered = line

        blocks.append(rendered)
        previous = line

    # RMIT accordion/tab labels are emitted before their real content. They
    # appear as a heading followed immediately by another heading at the same
    # or a higher level. Remove those empty labels while preserving a parent
    # heading followed by a genuine child section.
    compact: list[str] = []
    for index, block in enumerate(blocks):
        current = re.match(r"^(#+)\s", block)
        following = re.match(r"^(#+)\s", blocks[index + 1]) if index + 1 < len(blocks) else None
        if current and following and len(following.group(1)) <= len(current.group(1)):
            continue
        compact.append(block)

    cleaned = front_matter + "\n\n" + "\n\n".join(compact).rstrip() + "\n"
    path.write_text(cleaned, encoding="utf-8")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Clean the RMIT corpus after crawling.")
    parser.add_argument("data_dir", nargs="?", type=Path, default=Path("data/rmit-library"))
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    for filename, rule in RULES.items():
        path = args.data_dir / filename
        if not path.is_file():
            raise FileNotFoundError(path)
        clean_document(path, rule)
        print(f"Cleaned {path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
