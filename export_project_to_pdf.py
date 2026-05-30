from __future__ import annotations

import datetime as dt
from pathlib import Path
from typing import Iterable, List, Optional, Tuple

from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, PageBreak, Preformatted
from reportlab.lib.units import inch


# =========================
# CONFIGURATION
# =========================
REPO_ROOT = Path(__file__).resolve().parent

INCLUDE_EXTENSIONS = {".py", ".md", ".txt", ".json"}

EXCLUDE_DIRS = {
    ".venv",
    "venv",
    "__pycache__",
    ".pytest_cache",
    ".git",
    ".idea",
    ".vscode",
    "node_modules",
    "dist",
    "build",
    ".mypy_cache",
    ".ruff_cache",
}

MAX_CHARS_PER_CHUNK = 12000  # split big files so ReportLab stays stable

STAMP = dt.datetime.now().strftime("%Y%m%d_%H%M%S")
OUTPUT_PDF = REPO_ROOT / f"Full_Project_Source_{STAMP}.pdf"


# =========================
# STYLES
# =========================
styles = getSampleStyleSheet()

TITLE_STYLE = ParagraphStyle("TitleStyle", parent=styles["Title"], alignment=1, spaceAfter=18)
SECTION_STYLE = ParagraphStyle("SectionStyle", parent=styles["Heading2"], spaceBefore=12, spaceAfter=6)
FILE_STYLE = ParagraphStyle("FileStyle", parent=styles["Heading3"], spaceBefore=10, spaceAfter=6)

CODE_STYLE = ParagraphStyle(
    "CodeStyle",
    parent=styles["Normal"],
    fontName="Courier",
    fontSize=8,
    leading=10,
)


# =========================
# HELPERS
# =========================
def is_excluded(path: Path) -> bool:
    return any(part in EXCLUDE_DIRS for part in path.parts)


def chunk_text(text: str, chunk_size: int) -> Iterable[str]:
    for i in range(0, len(text), chunk_size):
        yield text[i : i + chunk_size]


def safe_read_text(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8")
    except Exception:
        return path.read_text(encoding="utf-8", errors="ignore")


def find_project_root(repo_root: Path) -> Path:
    """
    Auto-detect the actual project folder.
    Looks for a folder that contains typical project markers.
    """
    # First: if repo_root itself has markers, use it
    markers = ["app.py", "agent.py", "tools.py", "requirements.txt", "README.md"]
    marker_hits = sum((repo_root / m).exists() for m in markers)
    if marker_hits >= 2:
        return repo_root

    # Second: search immediate child dirs
    candidates: List[Tuple[int, Path]] = []
    for p in repo_root.iterdir():
        if not p.is_dir() or is_excluded(p):
            continue

        score = 0
        for m in markers:
            if (p / m).exists():
                score += 2
        if (p / "data").exists():
            score += 2
        if (p / "src").exists():
            score += 1
        if (p / "tests").exists():
            score += 1

        if score > 0:
            candidates.append((score, p))

    if candidates:
        candidates.sort(reverse=True, key=lambda x: x[0])
        return candidates[0][1]

    # Third: deep search (limit: avoid scanning .venv etc)
    best_score = -1
    best_path: Optional[Path] = None
    for p in repo_root.rglob("*"):
        if not p.is_dir() or is_excluded(p):
            continue
        score = 0
        for m in markers:
            if (p / m).exists():
                score += 2
        if (p / "data").exists():
            score += 2
        if (p / "src").exists():
            score += 1
        if (p / "tests").exists():
            score += 1
        if score > best_score:
            best_score = score
            best_path = p

    if best_path and best_score > 0:
        return best_path

    raise FileNotFoundError(
        f"Could not auto-detect project root inside: {repo_root}\n"
        f"project folder contains app.py/agent.py/tools.py or data/."
    )


def iter_project_files(root: Path) -> List[Path]:
    files: List[Path] = []
    for p in root.rglob("*"):
        if not p.is_file():
            continue
        if is_excluded(p):
            continue
        if p.suffix.lower() in INCLUDE_EXTENSIONS:
            files.append(p)
    return sorted(files)


# =========================
# MAIN
# =========================
def export_project_to_pdf() -> Tuple[Path, int, Path]:
    project_root = find_project_root(REPO_ROOT)
    files = iter_project_files(project_root)

    doc = SimpleDocTemplate(
        str(OUTPUT_PDF),
        pagesize=A4,
        rightMargin=36,
        leftMargin=36,
        topMargin=36,
        bottomMargin=36,
    )

    story = []
    story.append(Paragraph("Full Project Source Code Export", TITLE_STYLE))
    story.append(Paragraph(f"Repo root: {REPO_ROOT}", styles["Normal"]))
    story.append(Paragraph(f"Detected project root: {project_root}", styles["Normal"]))
    story.append(Paragraph(f"Included extensions: {', '.join(sorted(INCLUDE_EXTENSIONS))}", styles["Normal"]))
    story.append(Paragraph(f"Excluded dirs: {', '.join(sorted(EXCLUDE_DIRS))}", styles["Normal"]))
    story.append(Spacer(1, 0.2 * inch))

    if not files:
        story.append(Paragraph("⚠️ No files matched. Check INCLUDE_EXTENSIONS.", SECTION_STYLE))
        doc.build(story)
        return OUTPUT_PDF, 0, project_root

    story.append(Paragraph(f"Files included: {len(files)}", SECTION_STYLE))
    story.append(PageBreak())

    for i, path in enumerate(files, start=1):
        rel = path.relative_to(project_root)
        story.append(Paragraph(f"{i}. {rel}", FILE_STYLE))
        story.append(Spacer(1, 0.1 * inch))

        content = safe_read_text(path)
        if not content.strip():
            story.append(Paragraph("(Empty file)", styles["Italic"]))
        else:
            for part_no, chunk in enumerate(chunk_text(content, MAX_CHARS_PER_CHUNK), start=1):
                if part_no > 1:
                    story.append(Paragraph(f"(continued… part {part_no})", styles["Italic"]))
                story.append(Preformatted(chunk, CODE_STYLE))
                story.append(Spacer(1, 0.1 * inch))

        if i != len(files):
            story.append(PageBreak())

    doc.build(story)
    return OUTPUT_PDF, len(files), project_root


if __name__ == "__main__":
    out_pdf, count, detected_root = export_project_to_pdf()
    print(f"✅ Detected project root: {detected_root}")
    print(f"✅ Files exported: {count}")
    print(f"✅ PDF generated: {out_pdf}")
