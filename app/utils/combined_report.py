"""
Combined-report generation core.

Reads per-student AIET v2.0 docs from DynamoDB, filters them to a school's
roster via a 3-way id match, renders each through reporting's OWN v2 print
template + the html_to_pdf service, and merges them into one PDF. No BigQuery —
the v2 docs already hold the content.

Renders with `student_quiz_report_v2_print.html` — the SAME template the
single-report endpoint uses for v2 docs (student_quiz_reports.py:render_v2_report)
— so each page of the combined PDF is byte-identical to the per-student PDF the
reporting site already serves. (The etl-data-flow aiet_report_template.html was
built for the older generate_aiet_reports.py JSON schema, whose field names
differ from the stored v2 doc — total_marks vs marks_scored, etc. — so it left
fields blank. Verified against real data, 2026-06-23.)

The merge loop is condensed from combine_pdfs_by_school.py, with WeasyPrint
swapped for the html_to_pdf service and the metadata.school string-filter
swapped for the roster id-match.
"""

import io
import os
from decimal import Decimal

import requests
from jinja2 import Environment, FileSystemLoader
from pypdf import PdfReader, PdfWriter

TEMPLATE_DIR = "templates"
TEMPLATE_NAME = "student_quiz_report_v2_print.html"


def _safe_format(fmt, *args, **kwargs):
    """Null-safe `format` filter. The AIET template applies `"%.2f"|format(x)`
    to numeric metrics, but stored v2 docs can carry null where a metric is
    undefined (e.g. accuracy for a subject with 0 attempts). Treat None as 0
    so a single sparse student doesn't crash the whole combined report. The
    manual etl-data-flow run never hit this because it formatted freshly
    computed numbers, not the stored doc."""
    safe_args = tuple(0 if a is None else a for a in args)
    safe_kwargs = {k: (0 if v is None else v) for k, v in kwargs.items()}
    return fmt % (safe_kwargs or safe_args)


def _finalize(value):
    """Render None as empty string rather than the literal "None" for direct
    `{{ ... }}` outputs (e.g. a null priority tag)."""
    return "" if value is None else value


_env = Environment(loader=FileSystemLoader(TEMPLATE_DIR), finalize=_finalize)
_env.filters["format"] = _safe_format


def _decimalize(obj):
    """Recursively convert DynamoDB Decimals to int/float so Jinja renders them
    cleanly (98 not Decimal('98'), 98.33 not Decimal('98.33'))."""
    if isinstance(obj, Decimal):
        return int(obj) if obj % 1 == 0 else float(obj)
    if isinstance(obj, list):
        return [_decimalize(v) for v in obj]
    if isinstance(obj, dict):
        return {k: _decimalize(v) for k, v in obj.items()}
    return obj


def _roster_index(students):
    """Build lookup sets of the three id kinds from the af_lms roster.
    All compared as strings; empty apaar_id is ignored (many records store "")."""
    user_ids, student_ids, apaar_ids = set(), set(), set()
    for s in students:
        if s.get("user_id") not in (None, ""):
            user_ids.add(str(s["user_id"]))
        if s.get("student_id") not in (None, ""):
            student_ids.add(str(s["student_id"]))
        if s.get("apaar_id") not in (None, ""):
            apaar_ids.add(str(s["apaar_id"]))
    return user_ids, student_ids, apaar_ids


def filter_docs_to_roster(v2_docs, students):
    """Keep only the session's v2 docs that belong to this school's roster.

    A doc matches if its user_id, student_id, or (non-empty) apaar_id is in the
    roster — the same forgiving 3-way match the BigQuery enrollment join and the
    af_lms perf-tab deep-dive use, because test_responses.user_id is not reliably
    the Postgres user.id.

    Returns (matched_docs, missing_count) where missing = roster students with no
    matching v2 doc (e.g. didn't sit the test).
    """
    user_ids, student_ids, apaar_ids = _roster_index(students)
    matched = []
    matched_keys = set()  # which roster identities we satisfied, for missing count

    for doc in v2_docs:
        d_user = str(doc.get("user_id")) if doc.get("user_id") not in (None, "") else None
        d_student = (
            str(doc.get("student_id")) if doc.get("student_id") not in (None, "") else None
        )
        d_apaar = str(doc.get("apaar_id")) if doc.get("apaar_id") not in (None, "") else None

        if (
            (d_user and d_user in user_ids)
            or (d_student and d_student in student_ids)
            or (d_apaar and d_apaar in apaar_ids)
        ):
            matched.append(doc)
            if d_user:
                matched_keys.add(("u", d_user))
            if d_student:
                matched_keys.add(("s", d_student))
            if d_apaar:
                matched_keys.add(("a", d_apaar))

    # A roster student is "missing" if none of its ids were matched by any doc.
    missing = 0
    for s in students:
        ids = []
        if s.get("user_id") not in (None, ""):
            ids.append(("u", str(s["user_id"])))
        if s.get("student_id") not in (None, ""):
            ids.append(("s", str(s["student_id"])))
        if s.get("apaar_id") not in (None, ""):
            ids.append(("a", str(s["apaar_id"])))
        if not any(k in matched_keys for k in ids):
            missing += 1

    return matched, missing


def _student_sort_key(doc):
    header = doc.get("report_header") or {}
    return str(header.get("student_name", "")).lower()


def render_student_html(doc):
    """Render one AIET v2.0 doc to HTML via the v2 print template.

    Mirrors render_v2_report's prep: the template reads
    report_header.student_id, but the authoritative student_id lives at the
    doc's top level, so copy it down before rendering.
    """
    doc = _decimalize(doc)
    if isinstance(doc.get("report_header"), dict) and "student_id" in doc:
        doc["report_header"]["student_id"] = doc["student_id"]
    template = _env.get_template(TEMPLATE_NAME)
    return template.render(report=doc)


def html_to_pdf_bytes(html, timeout=60):
    """POST HTML to the html_to_pdf service and return raw PDF bytes.

    The AIET template is self-contained (system fonts, no external CSS/images/
    MathJax), so the default {html} call is sufficient — verified pixel-identical
    to WeasyPrint in the fidelity spike.
    """
    url = os.getenv("HTML_TO_PDF_SERVER_URL")
    if not url:
        raise RuntimeError("HTML_TO_PDF_SERVER_URL is not set")
    response = requests.post(url, json={"html": html}, timeout=timeout)
    if response.status_code != 200:
        raise RuntimeError(
            f"html_to_pdf service error {response.status_code}: {response.text[:200]}"
        )
    return response.content


def build_combined_pdf(matched_docs):
    """Render every matched student and merge into one PDF (sorted by name).

    Returns (pdf_bytes, rendered_count). Renders are sequential to stay gentle on
    the single shared Chromium behind html_to_pdf.
    """
    writer = PdfWriter()
    rendered = 0
    for doc in sorted(matched_docs, key=_student_sort_key):
        html = render_student_html(doc)
        pdf_bytes = html_to_pdf_bytes(html)
        reader = PdfReader(io.BytesIO(pdf_bytes))
        for page in reader.pages:
            writer.add_page(page)
        rendered += 1

    out = io.BytesIO()
    writer.write(out)
    return out.getvalue(), rendered
