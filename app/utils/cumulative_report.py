"""
Cumulative report: one student's last 2-3 big tests, side by side.

Built only from the student's `student_quiz_reports_v2` docs (one per test), so
no extra data source is needed. `build_cumulative_report(items)` picks the tests
and returns everything the template prints, including the plain-English
comments; it returns None when the student has fewer than MIN_TESTS big tests.

Wording rules follow the approved "AIAT student report" spec (JEE and NEET).
Ranks and mentor names from that spec are not shown yet.
"""

import re
from datetime import date

from markupsafe import Markup

BIG_TEST_FORMATS = {"major_test", "full_syllabus_test", "mock_test", "part_test"}
MAX_TESTS = 3
MIN_TESTS = 2
MAX_CHAPTER_ROWS = 8  # per subject table, including the "N other chapters" row
SUBJECT_ORDER = ["Physics", "Chemistry", "Maths", "Mathematics", "Biology"]
COUNT_FIELDS = ("num_correct", "num_wrong", "num_partially_correct", "num_skipped")

# "AIET-01-G12-PCM", "JNV-G12-MT-02-...", "G12-Baseline Test" -> 12
_GRADE_IN_NAME = re.compile(r"(?:^|[^A-Za-z0-9])G(9|1[0-2])(?!\d)")
# Old question system names chapters "12C20 - Electrochemistry"; the new one
# says "Electrochemistry". Dropping the code lets same-named chapters merge and
# take the current priority. Never match on the code itself: it was renumbered.
_OLD_CHAPTER_CODE = re.compile(r"^\s*\d+[A-Z]+\d+\s*-\s*")
# "JNV-G12-MT-02-JEE Main (AIAT-02)" -> "AIAT-02"
_SHORT_NAME = re.compile(r"\b(AI[AE]T)[-\s]?(\d+)\b", re.IGNORECASE)


def _num(value) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return 0.0


def _fmt(value: float) -> str:
    """Marks as printed: 49, 49.5, -3."""
    value = round(value, 1)
    return str(int(value)) if value == int(value) else str(value)


def _plural(count, word: str, plural: str = None) -> str:
    return f"{_fmt(count)} {word if count == 1 else (plural or word + 's')}"


def _counts(row: dict) -> dict:
    """Right/wrong/skipped of a subject or chapter row. Partially-correct
    answers count as right here (only JEE Advanced has them, and those papers
    are not picked)."""
    right = int(_num(row.get("num_correct")) + _num(row.get("num_partially_correct")))
    wrong = int(_num(row.get("num_wrong")))
    skipped = int(_num(row.get("num_skipped")))
    # `total_questions` on v2 subject rows is the whole paper's count, so sum instead.
    return {"r": right, "w": wrong, "s": skipped, "n": right + wrong + skipped}


def _grade_from_name(name: str):
    match = _GRADE_IN_NAME.search(name or "")
    return match.group(1) if match else None


def select_tests(items: list) -> list:
    """The student's last MAX_TESTS big tests, oldest first.

    Big = major/full-syllabus/mock/part test, submitted, not a Baseline or a
    JEE Advanced paper, written for the student's grade (when the name says),
    and in the stream of the student's latest big test. A test name taken twice
    keeps only the later sitting.
    """
    candidates = []
    for item in items:
        header = item.get("report_header") or {}
        overall = item.get("overall_performance") or {}
        name = header.get("test_name") or ""
        lname = name.lower()
        if header.get("test_format") not in BIG_TEST_FORMATS:
            continue
        if "baseline" in lname or "advance" in lname:
            continue
        if overall.get("has_quiz_ended") is False or not header.get("test_date"):
            continue
        if not item.get("subject_performance"):
            continue
        name_grade = _grade_from_name(name)
        student_grade = str(header.get("grade") or "").strip()
        if name_grade and student_grade and name_grade != student_grade:
            continue
        candidates.append(item)

    if not candidates:
        return []
    candidates.sort(key=lambda i: str(i["report_header"]["test_date"]))
    stream = candidates[-1]["report_header"].get("stream")

    by_name = {}
    for item in candidates:
        if item["report_header"].get("stream") == stream:
            by_name[item["report_header"]["test_name"]] = item  # later wins
    picked = sorted(
        by_name.values(), key=lambda i: str(i["report_header"]["test_date"])
    )
    return picked[-MAX_TESTS:]


def _subject_order(names) -> list:
    rank = {s: i for i, s in enumerate(SUBJECT_ORDER)}
    return sorted(names, key=lambda s: (rank.get(s, len(rank)), s))


def _short_test_name(name: str) -> str:
    match = _SHORT_NAME.search(name or "")
    if match:
        return f"{match.group(1).upper()}-{match.group(2)}"
    return name


def _parse_date(value):
    try:
        return date.fromisoformat(str(value)[:10])
    except ValueError:
        return None


def _month_span(dates) -> str:
    dates = [d for d in dates if d]
    if not dates:
        return ""
    first, last = dates[0], dates[-1]
    if first.year != last.year:
        return f"{first:%b %Y}–{last:%b %Y}"
    if first.month == last.month:
        return f"{last:%b %Y}"
    return f"{first:%b}–{last:%b %Y}"


def _change(prev, last):
    """Change line under a marks chart: (css class, text)."""
    if prev is None or last is None:
        return "", "—"
    diff = round(last - prev, 1)
    if diff > 0:
        return "up", f"▲ {_plural(diff, 'mark')} more"
    if diff < 0:
        return "down", f"▼ {_plural(-diff, 'mark')} less"
    return "", "same"


def _chart(name, out_of, marks, labels, is_total=False) -> dict:
    cols = []
    for i, (label, value) in enumerate(zip(labels, marks)):
        pct = (
            0
            if value is None or out_of <= 0
            else max(0, min(100, value / out_of * 100))
        )
        cols.append(
            {
                "label": label,
                "marks": None if value is None else _fmt(value),
                "pct": round(pct, 1),
                "last": i == len(labels) - 1,
            }
        )
    cls, text = _change(marks[-2], marks[-1])
    return {
        "name": name,
        "out_of": _fmt(out_of),
        "cols": cols,
        "total": is_total,
        "change_from": f"{labels[-2]} → {labels[-1]}",
        "change_cls": cls,
        "change_text": text,
    }


def _paper_line(subjects: list) -> str:
    """'Each subject has 25 questions and 100 marks, so the full paper is 300 marks.'"""
    total = sum(s["max"] for s in subjects)
    shapes = {(s["n"], s["max"]) for s in subjects}
    if len(shapes) == 1:
        n, mx = shapes.pop()
        return (
            f"Each subject has {n} questions and {_fmt(mx)} marks, "
            f"so the full paper is {_fmt(total)} marks."
        )
    parts = [
        f"{s['name']} has {s['n']} questions ({_fmt(s['max'])} marks)" for s in subjects
    ]
    return f"{'. '.join(parts)}. The full paper is {_fmt(total)} marks."


def _subject_comment(subj, last, prev, L, P, is_neet) -> str:
    """One plain sentence (or two) under a subject in Part 2, about the latest test."""
    r, w, s, n = last["r"], last["w"], last["s"], last["n"]
    tried = r + w
    x = None if prev is None else prev["marks"]
    y = last["marks"]

    if tried == 0:
        return (
            f"In {L} you did not answer any question. Every skipped question is 0 marks. "
            "Try the questions you know."
        )

    many_skipped = s >= (0.4 * n if is_neet else 0.6 * n)
    if many_skipped:
        lead = ""
        if tried >= 3 and r >= 2 * w:
            lead = f"When you answer, you are often right: {r} of {tried} in {L}. "
        if is_neet and prev is not None and prev["s"] - s >= 5:
            return lead + (
                f"You skipped fewer questions than in {P} ({prev['s']} → {s}), which is good. "
                f"But {s} of {n} is still a lot. Try more questions."
            )
        start = f"But in {L}" if lead else f"In {L}"
        before = f" ({P}: {prev['s']})" if prev is not None else ""
        return lead + (
            f"{start} you skipped {s} of {n} questions{before}. "
            "Every skipped question is 0 marks. Try more questions."
        )

    if w > r:
        return (
            f"In {L} you had {w} wrong and {r} right. Each wrong answer takes away 1 mark. "
            "Answer only when you are sure."
        )

    if x is not None and y > x:
        if not is_neet:
            return f"Your marks went up: {_fmt(x)} → {_fmt(y)}. Keep going."
        if w < prev["w"]:
            return (
                f"Very good. Wrong answers went down from {prev['w']} to {w}, "
                f"and your marks went up from {_fmt(x)} to {_fmt(y)}."
            )
        return f"Your marks went up from {_fmt(x)} to {_fmt(y)}. Keep going."

    if x is not None and x - y >= 0.05 * subj["max"]:
        text = f"Your marks went down from {_fmt(x)} to {_fmt(y)}."
        if not is_neet:
            return (
                text + f" In {L} you had {_plural(w, 'wrong answer')} and skipped {s}."
            )
        if r < prev["r"]:
            text += f" Right answers went down from {prev['r']} to {r}."
        if w > prev["w"]:
            text += f" Wrong answers went up from {prev['w']} to {w}."
        if s > prev["s"]:
            text += f" Skipped questions went up from {prev['s']} to {s}."
        return text

    return f"In {L} you got {r} right, {w} wrong and skipped {s}."


def _chapter_tables(tests, subjects, show_all) -> list:
    """Chapter counts added together across the picked tests, one table per subject."""
    chapters = {}
    for item in tests:  # oldest first, so a later test's priority wins
        for ch in item.get("chapter_performance") or []:
            name = _OLD_CHAPTER_CODE.sub("", ch.get("chapter_name") or "").strip()
            key = (ch.get("subject"), name)
            if not key[0] or not key[1]:
                continue
            row = chapters.setdefault(
                key, {"name": key[1], "priority": None, "q": 0, "r": 0, "w": 0, "s": 0}
            )
            c = _counts(ch)
            row["q"] += c["n"]
            row["r"] += c["r"]
            row["w"] += c["w"]
            row["s"] += c["s"]
            if ch.get("priority"):
                row["priority"] = ch["priority"]

    order = {"High": 0, "Medium": 1, "Low": 2}
    tables = []
    for subj in subjects:
        rows = [
            row
            for (sname, _), row in chapters.items()
            if sname == subj["name"] and row["q"] > 0
        ]
        if not show_all:
            rows = [row for row in rows if row["priority"] == "High"]
        rows.sort(key=lambda c: (order.get(c["priority"], 3), -c["q"], c["name"]))
        total = {k: sum(row[k] for row in rows) for k in ("q", "r", "w", "s")}
        shown = rows
        if len(rows) > MAX_CHAPTER_ROWS:  # keep page 2 on one A4 sheet
            rest = rows[MAX_CHAPTER_ROWS - 1 :]
            other = {k: sum(row[k] for row in rest) for k in ("q", "r", "w", "s")}
            other.update(name=f"{len(rest)} other chapters", priority=None, other=True)
            shown = rows[: MAX_CHAPTER_ROWS - 1] + [other]
        tables.append(
            {"subject": subj["name"], "rows": rows, "shown": shown, "total": total}
        )
    return tables


def _chapter_detail(ch) -> str:
    parts = []
    if ch["s"]:
        parts.append(
            f"all {ch['s']} skipped"
            if ch["s"] == ch["q"]
            else f"{ch['s']} of {ch['q']} skipped"
        )
    if ch["w"]:
        parts.append(
            f"all {ch['w']} wrong" if ch["w"] == ch["q"] else f"{ch['w']} wrong"
        )
    return ", ".join(parts)


def _todo_item(table, fallback) -> Markup:
    """One 'What to do next' line for a subject."""
    name = table["subject"]
    totals = table["total"] if table["rows"] else fallback
    q, r, w, s = totals["q"], totals["r"], totals["w"], totals["s"]

    if q and w == 0 and s == 0:
        return Markup("<b>{}: very good.</b> You got all {} questions right.").format(
            name, q
        )
    if s >= q / 2:
        title, verb = "try more questions.", "Start with"
    elif w > r:
        title, verb = "check your answers.", "Start with"
    elif r >= 0.6 * q:
        title, verb = "good work, keep going.", "Revise"
    else:
        title, verb = "practise these chapters.", "Start with"

    weak = sorted(
        (c for c in table["rows"] if c["w"] + c["s"] > 0),
        key=lambda c: (c["priority"] != "High", -(c["w"] + c["s"]), -c["q"], c["name"]),
    )[:2]
    text = Markup("<b>{}: {}</b>").format(name, title)
    if weak:
        named = [
            Markup("<b>{}</b> ({})").format(c["name"], _chapter_detail(c)) for c in weak
        ]
        text += Markup(" {} {}.").format(verb, Markup(" and ").join(named))
    return text


def build_cumulative_report(items: list, today: date = None):
    tests = select_tests(items)
    if len(tests) < MIN_TESTS:
        return None

    labels = [f"Test {i + 1}" for i in range(len(tests))]
    L, P = labels[-1], labels[-2]
    latest = tests[-1]
    header = latest.get("report_header") or {}
    is_neet = header.get("stream") == "medical"
    exam = "NEET" if is_neet else "JEE Main"
    grade = str(header.get("grade") or "").strip()

    # Per test: subject name -> counts + marks
    per_test = []
    for item in tests:
        subjects = {}
        for row in item.get("subject_performance") or []:
            c = _counts(row)
            c["marks"] = _num(row.get("marks_scored"))
            c["max"] = _num(row.get("max_marks_possible"))
            subjects[row.get("subject")] = c
        per_test.append(subjects)

    subjects = []
    for name in _subject_order(per_test[-1].keys()):
        last = per_test[-1][name]
        subjects.append({"name": name, "n": last["n"], "max": last["max"]})

    # Part 1: marks charts
    totals = [
        _num((t.get("overall_performance") or {}).get("marks_scored")) for t in tests
    ]
    out_of = _num((latest.get("overall_performance") or {}).get("max_marks_possible"))
    out_of = out_of or sum(s["max"] for s in subjects)
    charts = [_chart("Total", out_of, totals, labels, is_total=True)]
    for subj in subjects:
        marks = [
            t[subj["name"]]["marks"] if subj["name"] in t else None for t in per_test
        ]
        charts.append(_chart(subj["name"], subj["max"], marks, labels))

    # Part 2: right / wrong / skipped per test, plus one comment per subject
    widest = max(s["n"] for s in subjects) or 1
    use_boxes = widest <= 30
    part2 = []
    for subj in subjects:
        rows = []
        for label, t in zip(labels, per_test):
            c = t.get(subj["name"])
            if c is None:
                rows.append({"label": label, "missing": True})
                continue
            n = c["n"] or 1
            rows.append(
                {
                    "label": label,
                    "r": c["r"],
                    "w": c["w"],
                    "s": c["s"],
                    "n": c["n"],
                    "tried": c["r"] + c["w"],
                    "boxes": "r" * c["r"] + "w" * c["w"] + "s" * c["s"],
                    "width": round(c["n"] / widest * 100, 1),
                    "pr": round(c["r"] / n * 100, 1),
                    "pw": round(c["w"] / n * 100, 1),
                    "ps": round(c["s"] / n * 100, 1),
                }
            )
        prev = per_test[-2].get(subj["name"])
        comment = _subject_comment(
            subj, per_test[-1][subj["name"]], prev, L, P, is_neet
        )
        part2.append({"name": subj["name"], "rows": rows, "comment": comment})

    # Part 3: chapters. Grade 11 JEE has few High chapters early on, so list all.
    show_all = not is_neet and grade == "11"
    tables = _chapter_tables(tests, subjects, show_all)
    fallback = {}
    for subj in subjects:
        f = {"q": 0, "r": 0, "w": 0, "s": 0}
        for t in per_test:
            c = t.get(subj["name"])
            if c:
                f["q"] += c["n"]
                f["r"] += c["r"]
                f["w"] += c["w"]
                f["s"] += c["s"]
        fallback[subj["name"]] = f

    def right_share(table):
        tot = table["total"] if table["rows"] else fallback[table["subject"]]
        return tot["r"] / tot["q"] if tot["q"] else 1

    todo = [
        _todo_item(t, fallback[t["subject"]]) for t in sorted(tables, key=right_share)
    ]

    dates = [_parse_date(t["report_header"].get("test_date")) for t in tests]
    test_list = []
    for label, item, d in zip(labels, tests, dates):
        test_list.append(
            {
                "label": label,
                "name": _short_test_name(item["report_header"].get("test_name", "")),
                "date": f"{d.day} {d:%b}" if d else "",
            }
        )

    today = today or date.today()
    return {
        "student_name": header.get("student_name") or "",
        "student_id": latest.get("student_id") or header.get("student_id") or "",
        "school": latest.get("school") or "",
        "grade": grade,
        "exam": exam,
        "is_neet": is_neet,
        "num_tests": len(tests),
        "months": _month_span(dates),
        "tests": test_list,
        "paper_line": _paper_line(subjects),
        "charts": charts,
        "use_boxes": use_boxes,
        "part2": part2,
        "show_all_chapters": show_all,
        "chapter_tables": tables,
        "todo": todo,
        "as_of": f"{today.day} {today:%b %Y}",
    }
