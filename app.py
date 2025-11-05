# Age Eligibility Calculator — Web App (Streamlit) v3.8
# No logical change from desktop version; UI adapted to web (two-panel layout).
# Features preserved:
# - Age calc vs cutoff
# - Class ranges (KG-1..Grade 12)
# - Submitted vs Not Submitted docs (PDF)
# - PDF exports with reportlab
# - Login page (Operator, School, Password @9852; admin ELDHOJACOB always works; others 3‑month trial)
# - "copyright@eldhojacobsby2025" on UI header; PDF footer only
#
# Run locally:
#   pip install -r requirements.txt
#   streamlit run app.py

from __future__ import annotations
import os
import json
from dataclasses import dataclass
from datetime import date, datetime, timedelta
from pathlib import Path
from typing import Dict, Tuple

import streamlit as st

# PDF
try:
    from reportlab.lib.pagesizes import A4
    from reportlab.pdfgen import canvas
    from reportlab.lib import colors as reportlab_colors
    from reportlab.lib.units import mm
except Exception as e:
    st.session_state.setdefault("_pdf_error", str(e))

# -----------------------------
# Constants / Config
# -----------------------------
CONFIG_FILE = Path(".age_eligibility_config.json")  # local to app working dir (persists on local; ephemeral on cloud)
ADMIN_USERNAME = "ELDHOJACOB"
UNIVERSAL_PASSWORD = "@9852"
TRIAL_DAYS = 90

DEVELOPER_TAG = "copyright@eldhojacobsby2025"

COLORS = {
    "bg": "#eff6ff",
    "card": "#fefce8",
    "text": "#1e3a8a",
    "muted": "#6b7280",
    "ok": "#22c55e",
    "bad": "#ef4444",
    "badge_idle": "#a1b2c3",
    "blink1": "#15803d",
    "blink2": "#34d399",
    "border": "#bfdbfe",
    "accent": "#1e3a8a",
}

@dataclass(frozen=True)
class Age:
    years: int
    months: int
    days: int

@dataclass(frozen=True)
class Range:
    min: Age
    max: Age

ClassKey = str

DEFAULT_CUTOFF_MONTH = 9
DEFAULT_CUTOFF_DAY = 30

DEFAULT_RANGES: Dict[ClassKey, Range] = {
    "KG-1":    Range(Age(3, 0, 0),  Age(4, 11, 29)),
    "KG-2":    Range(Age(4, 0, 0),  Age(5, 11, 29)),
    "Grade 1": Range(Age(5, 0, 0),  Age(7, 11, 29)),
    "Grade 2": Range(Age(6, 0, 0),  Age(8, 11, 29)),
    "Grade 3": Range(Age(7, 0, 0),  Age(9, 11, 29)),
    "Grade 4": Range(Age(8, 0, 0),  Age(10, 11, 29)),
    "Grade 5": Range(Age(9, 0, 0),  Age(11, 11, 29)),
    "Grade 6": Range(Age(10, 0, 0), Age(12, 11, 29)),
    "Grade 7": Range(Age(11, 0, 0), Age(14, 11, 29)),
    "Grade 8": Range(Age(12, 0, 0), Age(15, 11, 29)),
    "Grade 9": Range(Age(13, 0, 0), Age(16, 11, 29)),
    "Grade 10":Range(Age(14, 0, 0), Age(17, 11, 29)),
    "Grade 11":Range(Age(15, 0, 0), Age(18, 11, 29)),
    "Grade 12":Range(Age(16, 0, 0), Age(19, 11, 29)),
}

def class_list():
    return list(DEFAULT_RANGES.keys())

def last_day_of_month(year: int, month: int) -> int:
    if month == 12:
        next_month = date(year + 1, 1, 1)
    else:
        next_month = date(year, month + 1, 1)
    return (next_month - date(year, month, 1)).days

def make_valid_date(y: int, m: int, d: int) -> date:
    m = min(max(m, 1), 12)
    d = min(max(d, 1), last_day_of_month(y, m))
    return date(y, m, d)

def diff_ymd(birth: date, cutoff: date) -> Age:
    if cutoff < birth:
        return Age(0, 0, 0)
    y = cutoff.year - birth.year
    m = cutoff.month - birth.month
    d = cutoff.day - birth.day
    if d < 0:
        pm = cutoff.month - 1 or 12
        py = cutoff.year if cutoff.month > 1 else cutoff.year - 1
        d += last_day_of_month(py, pm)
        m -= 1
    if m < 0:
        m += 12
        y -= 1
    return Age(y, m, d)

def cmp_age(a: Age, b: Age) -> int:
    if a.years != b.years: return a.years - b.years
    if a.months != b.months: return a.months - b.months
    return a.days - b.days

def sub_ymd(base: date, y: int, m: int, d: int) -> date:
    Y = base.year - y
    M = base.month - m
    D = base.day - d
    while M <= 0:
        Y -= 1; M += 12
    maxd = last_day_of_month(Y, M)
    if D > maxd: D = maxd
    if D <= 0:
        M -= 1
        if M == 0:
            M = 12; Y -= 1
        D += last_day_of_month(Y, M)
    return date(Y, M, D)

def dob_window_for_range(cutoff: date, r: Range) -> Tuple[date, date]:
    latest = sub_ymd(cutoff, r.min.years, r.min.months, r.min.days)
    earliest = sub_ymd(cutoff, r.max.years, r.max.months, r.max.days)
    return earliest, latest

# -----------------------------
# Trial / Login helpers
# -----------------------------
def _get_installation_date() -> date:
    if CONFIG_FILE.exists():
        try:
            with open(CONFIG_FILE, "r") as f:
                config = json.load(f)
                return datetime.fromisoformat(config.get("install_date")).date()
        except Exception:
            pass
    install_date = date.today()
    try:
        with open(CONFIG_FILE, "w") as f:
            json.dump({"install_date": install_date.isoformat()}, f)
    except Exception:
        pass
    return install_date

def login_view():
    st.markdown(
        f"<div style='background:{COLORS['bg']};padding:1rem;border-radius:12px;border:1px solid {COLORS['border']};'>"
        f"<h2 style='margin:0;color:{COLORS['text']}'>Age Eligibility Calculator</h2>"
        f"<div style='color:{COLORS['muted']};font-style:italic'>{DEVELOPER_TAG}</div>"
        f"</div>", unsafe_allow_html=True
    )

    with st.form("login_form", clear_on_submit=False):
        colA, colB = st.columns(2)
        operator = colA.text_input("Operator/Incharge Name")
        school = colB.text_input("School Name")
        password = st.text_input("Password", type="password")
        submitted = st.form_submit_button("Login", use_container_width=True)
        if submitted:
            if not operator or not school or not password:
                st.error("Please fill in all fields.")
                return False
            if password != UNIVERSAL_PASSWORD:
                st.error("Incorrect password. Please use the correct password.")
                return False
            if operator == ADMIN_USERNAME:
                st.session_state["logged_in"] = True
                st.session_state["operator"] = operator
                st.session_state["school"] = school
                return True
            # Trial for non-admin
            install_date = _get_installation_date()
            current_date = date.today()
            trial_end = install_date + timedelta(days=TRIAL_DAYS)
            if current_date > trial_end:
                st.error("Your trial period is over, please contact the administrator.")
                return False
            st.session_state["logged_in"] = True
            st.session_state["operator"] = operator
            st.session_state["school"] = school
            return True
    return False

# -----------------------------
# Main App
# -----------------------------
def main_app():
    # Header
    st.markdown(
        f"<div style='background:{COLORS['bg']};padding:1rem 1rem;border-radius:12px;border:1px solid {COLORS['border']};display:flex;justify-content:space-between;align-items:center;'>"
        f"<div><span style='font-size:22px;font-weight:800;color:{COLORS['text']}'>Age Eligibility Calculator</span></div>"
        f"<div style='color:{COLORS['muted']}'>{DEVELOPER_TAG}</div>"
        f"</div>",
        unsafe_allow_html=True
    )

    # Two columns
    left, right = st.columns([1, 1.2], gap="large")

    # Defaults
    today = date.today()
    default_year = today.year if today.month >= 9 else today.year - 1

    # Session state defaults
    for k, v in {
        "selected_class": class_list()[0],
        "dob_day": 1,
        "dob_month": 1,
        "dob_year": today.year - 5,
        "academic_year": default_year,
        "cutoff_month": DEFAULT_CUTOFF_MONTH,
        "cutoff_day": DEFAULT_CUTOFF_DAY,
        "student_name": "",
        "qid": "",
        "session": "Morning",
        "nationality": "India",
    }.items():
        st.session_state.setdefault(k, v)

    with left:
        with st.container(border=True):
            st.subheader("Input Panel")
            st.selectbox("Class", class_list(), key="selected_class")

            c1, c2, c3 = st.columns(3)
            c1.number_input("DOB Day", 1, 31, key="dob_day")
            c2.number_input("DOB Month", 1, 12, key="dob_month")
            c3.number_input("DOB Year", 1990, 2100, key="dob_year")

            c4, c5 = st.columns(2)
            c4.number_input("Academic Start Year", 1990, 2100, key="academic_year")
            c5.write("")

            st.text_input("Student Name (optional)", key="student_name")
            st.text_input("QID (optional)", key="qid")

            c6, c7 = st.columns(2)
            c6.number_input("Cut-off Month (1–12)", 1, 12, key="cutoff_month")
            # Adjust cutoff day max based on month/year
            max_day = last_day_of_month(st.session_state["academic_year"], st.session_state["cutoff_month"])
            c7.number_input("Cut-off Day (1–31)", 1, max_day, key="cutoff_day")

            st.selectbox("Admission Session", ["Morning", "Evening"], key="session")
            if st.session_state["session"] == "Morning":
                st.markdown(f"**Nationality:** India")
                st.session_state["nationality"] = "India"
            else:
                st.selectbox("Nationality", ["India", "Pakistan", "Nepal", "Bangladesh", "Sri Lanka"], key="nationality")

            st.markdown("---")
            st.markdown("**Mandatory Documents Submitted**")

            # Documents (same list)
            docs = {
                "doc_qid_student": "QID (Student)",
                "doc_qid_parents": "QID Parents (Both)",
                "doc_passport_student": "Passport Student",
                "doc_passport_parents": "Passport Parents",
                "doc_immunization": "Immunization Records",
                "doc_mofa": "MOFA Attested",
                "doc_tc": "TC Original",
                "doc_marklist": "Marklist",
                "doc_national_address": "National Address",
                "doc_employment": "Employment Letter",
                "doc_birth_certificate": "Birth Certificate",
            }
            for key, label in docs.items():
                st.session_state.setdefault(key, False)

            cols = st.columns(2)
            for i, (key, label) in enumerate(docs.items()):
                with cols[i % 2]:
                    st.checkbox(label, key=key)

            # Extra checkbox for Grade 10/12
            if st.session_state["selected_class"] in ["Grade 10", "Grade 12"]:
                st.session_state.setdefault("doc_edu_authority_tc", False)
                st.checkbox("Educational Authority Signed TC", key="doc_edu_authority_tc")
            else:
                st.session_state["doc_edu_authority_tc"] = False

            st.markdown("---")
            btn_cols = st.columns(3)
            with btn_cols[0]:
                st.button("Calculate", key="btn_calc", type="primary",
                          disabled=(not bool(st.session_state.get("nationality"))))
            with btn_cols[1]:
                if st.button("Reset"):
                    for key in list(st.session_state.keys()):
                        if key not in ["logged_in", "operator", "school"]:
                            del st.session_state[key]
                    st.rerun()
            with btn_cols[2]:
                st.button("Download PDF", key="btn_pdf",
                          disabled=("reportlab" in (st.session_state.get("_pdf_error") or "").lower()))

    # Compute if requested or if values changed and button pressed
    result = {}
    if st.session_state.get("btn_calc"):
        try:
            ay = int(st.session_state["academic_year"])
            cm = int(st.session_state["cutoff_month"])
            cd = int(st.session_state["cutoff_day"])
            cutoff = make_valid_date(ay, cm, cd)
            by = int(st.session_state["dob_year"])
            bm = int(st.session_state["dob_month"])
            bd = int(st.session_state["dob_day"])
            birth = make_valid_date(by, bm, bd)
        except Exception:
            st.error("Please enter valid dates.")
            return

        cls = st.session_state["selected_class"]
        r = DEFAULT_RANGES.get(cls)
        if not r:
            st.error(f"No age range configured for class '{cls}'.")
            return

        age = diff_ymd(birth, cutoff)
        within = (cmp_age(age, r.min) >= 0) and (cmp_age(age, r.max) <= 0)
        earliest, latest = dob_window_for_range(cutoff, r)

        result = {
            "age": age,
            "range_min": r.min,
            "range_max": r.max,
            "dob_earliest": earliest,
            "dob_latest": latest,
            "within": within,
            "cutoff": cutoff,
        }
        st.session_state["_last_result"] = result

    # Right panel (show last result if exists)
    with right:
        with st.container(border=True):
            st.subheader("Result & Eligibility")
            res = st.session_state.get("_last_result")
            if not res:
                st.info("Run **Calculate** to see eligibility details.")
            else:
                age = res["age"]
                rmin = res["range_min"]
                rmax = res["range_max"]
                earliest = res["dob_earliest"]
                latest = res["dob_latest"]
                within = res["within"]
                cutoff = res["cutoff"]

                # Age lines
                st.metric("Age on Cut-off", f"{age.years}y {age.months}m {age.days}d",
                          help=cutoff.strftime("Age as on %d/%m/%Y"))
                c1, c2 = st.columns(2)
                c1.write(f"**Allowed Min**: {rmin.years}y {rmin.months}m {rmin.days}d")
                c2.write(f"**Allowed Max**: {rmax.years}y {rmax.months}m {rmax.days}d")
                c3, c4 = st.columns(2)
                c3.write(f"**Valid DOB Earliest**: {earliest.isoformat()}")
                c4.write(f"**Valid DOB Latest**: {latest.isoformat()}")

                # Eligibility badge
                bg = COLORS["ok"] if within else COLORS["bad"]
                text = f"Eligible for Class {st.session_state['selected_class']}" if within else (
                    "Not Eligible: Too Young" if cmp_age(age, rmin) < 0 else "Not Eligible: Too Old"
                )
                st.markdown(
                    f"<div style='margin-top:1rem;background:{bg};color:white;padding:12px 16px;border-radius:10px;font-weight:700;text-align:center'>{text}</div>",
                    unsafe_allow_html=True
                )
                st.caption(f"Age as on {cutoff.strftime('%d/%m/%Y')} : {age.years}y {age.months}m {age.days}d")

                # Limits label (for PDF parity)
                st.session_state["_limits_label"] = f"Limits for {st.session_state['selected_class']}: Min {rmin.years}y {rmin.months}m {rmin.days}d  —  Max {rmax.years}y {rmax.months}m {rmax.days}d"

            # PDF generation
            if st.session_state.get("btn_pdf"):
                err = st.session_state.get("_pdf_error")
                if err:
                    st.error(f"PDF export requires reportlab. ({err})")
                else:
                    path = export_report_pdf_streamlit()
                    if path:
                        with open(path, "rb") as f:
                            st.download_button(
                                "Download PDF", f, file_name=os.path.basename(path), mime="application/pdf"
                            )
                    else:
                        st.error("PDF could not be created. Please calculate first.")

def export_report_pdf_streamlit() -> str | None:
    # Require existing result
    res = st.session_state.get("_last_result")
    if not res:
        return None

    name = (st.session_state.get("student_name") or "Not Provided").strip()
    qid = (st.session_state.get("qid") or "Not Provided").strip()
    cls = (st.session_state.get("selected_class") or "Not Selected").strip()
    session = st.session_state.get("session")
    nationality = st.session_state.get("nationality")
    cutoff = res["cutoff"]
    age = res["age"]
    age_line = f"Age as on {cutoff.strftime('%d/%m/%Y')} : {age.years}y {age.months}m {age.days}d"
    limits = st.session_state.get("_limits_label", "Not Calculated")
    generated_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    checked_date = datetime.now().strftime("%Y-%m-%d")

    # doc flags
    all_doc_items = [
        ("QID (Student)", st.session_state.get("doc_qid_student", False)),
        ("QID Parents (Both)", st.session_state.get("doc_qid_parents", False)),
        ("Passport Student", st.session_state.get("doc_passport_student", False)),
        ("Passport Parents", st.session_state.get("doc_passport_parents", False)),
        ("Immunization Records", st.session_state.get("doc_immunization", False)),
        ("MOFA Attested", st.session_state.get("doc_mofa", False)),
        ("TC Original", st.session_state.get("doc_tc", False)),
        ("Marklist", st.session_state.get("doc_marklist", False)),
        ("National Address", st.session_state.get("doc_national_address", False)),
        ("Employment Letter", st.session_state.get("doc_employment", False)),
        ("Birth Certificate", st.session_state.get("doc_birth_certificate", False)),
    ]
    if cls in ["Grade 10", "Grade 12"]:
        all_doc_items.append(("Educational Authority Signed TC", st.session_state.get("doc_edu_authority_tc", False)))

    submitted_docs = [label for (label, flag) in all_doc_items if flag]
    pending_docs   = [label for (label, flag) in all_doc_items if not flag]

    # Prepare output path
    def _safe(s: str) -> str:
        return "".join(ch for ch in s if ch not in r'\/:*?"<>|').strip() or "Student"
    first = name.split()[0] if name and name != "Not Provided" else "Student"
    outdir = Path(".")
    base = f"{_safe(first)}_{_safe(qid if qid != 'Not Provided' else 'QID')}.pdf"
    path = outdir / base
    i = 1
    while path.exists():
        path = outdir / f"{path.stem}_{i}.pdf"
        i += 1

    # Colors
    NAVY = reportlab_colors.HexColor("#1e3a8a")
    CREAM = reportlab_colors.HexColor("#fefce8")
    BORDER = reportlab_colors.HexColor("#bfdbfe")
    OK = reportlab_colors.HexColor("#22c55e")
    BAD = reportlab_colors.HexColor("#ef4444")
    BLACK = reportlab_colors.black
    MUTED = reportlab_colors.HexColor("#6b7280")

    # PDF setup
    PAGE_W, PAGE_H = A4
    margin = 18 * mm
    c = canvas.Canvas(str(path), pagesize=A4)

    # Header bar
    header_h = 30 * mm
    c.setFillColor(NAVY)
    c.rect(0, PAGE_H - header_h, PAGE_W, header_h, fill=1, stroke=0)
    c.setFillColor(reportlab_colors.white)
    c.setFont("Helvetica-Bold", 20)
    c.drawCentredString(PAGE_W / 2, PAGE_H - header_h + 10 * mm, "ADMISSION AGE ELIGIBILITY REPORT")

    # Card container
    card_h = PAGE_H - (2 * margin) - header_h
    card_x = margin
    card_y = margin
    card_w = PAGE_W - 2 * margin
    c.setFillColor(CREAM)
    c.setStrokeColor(BORDER)
    c.setLineWidth(1)
    c.roundRect(card_x, card_y, card_w, card_h, 8, fill=1, stroke=1)

    # Helpers
    ROW_GAP = 24
    SECTION_GAP = 18

    def draw_divider(y_pos):
        c.setStrokeColor(BORDER)
        c.setLineWidth(0.8)
        c.line(card_x + 12, y_pos, card_x + card_w - 12, y_pos)

    def draw_row(y_pos, label, value, label_font="Helvetica-Bold", value_font="Helvetica", font_size=12):
        c.setFillColor(BLACK)
        c.setFont(label_font, font_size)
        c.drawString(card_x + 16, y_pos, label)
        c.setFont(value_font, font_size)
        text_w = c.stringWidth(value, value_font, font_size)
        if text_w > card_w - 32:
            avg = max(1, int((card_w - 32) / c.stringWidth("M", value_font, font_size)))
            value = (value[:avg] + "...") if len(value) > avg else value
        c.drawRightString(card_x + card_w - 16, y_pos, value)

    def draw_doc_list_as_lines(items, start_y, font_name="Helvetica", font_size=12, line_gap=24):
        c.setFont(font_name, font_size)
        lines = []
        if not items:
            lines = ["None"]
        else:
            current = ""
            for item in items:
                candidate = (current + ", " + item) if current else item
                if c.stringWidth(candidate, font_name, font_size) <= (card_w - 32):
                    current = candidate
                else:
                    lines.append(current)
                    current = item
            if current:
                lines.append(current)
        yy = start_y
        for line in lines:
            c.drawString(card_x + 16, yy, line)
            yy -= line_gap
        return yy

    def wrap_text(text, font_name, font_size, max_width):
        c.setFont(font_name, font_size)
        words = text.split()
        lines = []
        current_line = ""
        for word in words:
            test_line = current_line + (" " + word if current_line else word)
            if c.stringWidth(test_line, font_name, font_size) <= max_width:
                current_line = test_line
            else:
                if current_line:
                    lines.append(current_line)
                current_line = word
        if current_line:
            lines.append(current_line)
        return lines

    # Draw content
    y = PAGE_H - header_h - 16 * mm
    c.setFont("Helvetica-Bold", 16)
    c.setFillColor(BLACK)
    c.drawCentredString(PAGE_W / 2, y, "Student Eligibility Details")
    y -= SECTION_GAP
    draw_divider(y)
    y -= ROW_GAP

    # Student details
    draw_row(y, "Student Name", name, font_size=14); y -= ROW_GAP
    draw_row(y, "QID", qid); y -= ROW_GAP
    draw_row(y, "Selected Class", cls); y -= ROW_GAP
    draw_row(y, "Admission Session", session); y -= ROW_GAP
    draw_row(y, "Nationality", nationality); y -= ROW_GAP
    age_text = age_line.split("Age as on ",1)[-1] if age_line.lower().startswith("age as on") else age_line
    draw_row(y, "Age as on", age_text); y -= ROW_GAP
    draw_row(y, "Age Limits", limits); y -= SECTION_GAP
    draw_divider(y); y -= ROW_GAP

    # Submitted
    c.setFont("Helvetica-Bold", 12); c.setFillColor(BLACK)
    c.drawString(card_x + 16, y, "Submitted Documents")
    y -= ROW_GAP
    y = draw_doc_list_as_lines(submitted_docs, y)

    # Pending
    y -= 6
    c.setFont("Helvetica-Bold", 12)
    c.drawString(card_x + 16, y, "Not Submitted (Pending)")
    y -= ROW_GAP
    y = draw_doc_list_as_lines(pending_docs, y)

    # Red note
    y -= 6
    note_text = "PLEASE NOTE: Without submitting the required above documents, the admission process cannot be finalized."
    c.setFont("Helvetica-BoldOblique", 11)
    c.setFillColor(BAD)
    wrapped_lines = wrap_text(note_text, "Helvetica-BoldOblique", 11, card_w - 32)
    for line in wrapped_lines:
        c.drawString(card_x + 16, y, line)
        y -= ROW_GAP
    c.setFillColor(BLACK)

    # Divider
    y -= 6
    draw_divider(y)
    y -= ROW_GAP

    # Signatures
    c.setFont("Helvetica-Bold", 12); c.setFillColor(BLACK)
    c.drawString(card_x + 16, y, "Checked By:")
    c.drawString(card_x + 16, y - 12, "___________________________")
    c.setFont("Helvetica", 10)
    c.drawString(card_x + 16, y - 24, f"Date: {checked_date}")

    c.setFont("Helvetica-Bold", 12)
    c.drawRightString(card_x + card_w - 16, y, "Parent Signature:")
    c.drawRightString(card_x + card_w - 16, y - 12, "___________________________")
    c.setFont("Helvetica", 10)
    c.drawRightString(card_x + card_w - 16, y - 24, "Date: _______________")

    # Footer
    c.setFont("Helvetica-Oblique", 9)
    c.setFillColor(MUTED)
    c.drawString(card_x + 16, card_y + 12, f"Generated by Age Eligibility Calculator — Offline (v3.8) on {generated_at}")
    c.drawRightString(card_x + card_w - 16, card_y + 12, DEVELOPER_TAG)

    c.showPage()
    c.save()
    return str(path)

# -----------------------------
# App Entrypoint
# -----------------------------
def main():
    st.set_page_config(page_title="Age Eligibility Calculator", layout="wide", page_icon="🧮")
    st.markdown("<style> .stApp {background: #ffffff;} </style>", unsafe_allow_html=True)

    if not st.session_state.get("logged_in"):
        ok = login_view()
        if not ok and not st.session_state.get("logged_in"):
            st.stop()

    main_app()

if __name__ == "__main__":
    main()
