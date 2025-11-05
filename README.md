# Age Eligibility Calculator — Streamlit Web App (v3.8)

**No logical changes** from your Tkinter desktop app. This is a faithful web conversion with the **same 2‑panel layout**.

## Features
- Age as on cutoff; valid DOB window
- Class ranges KG‑1 to Grade 12 (min/max ages)
- Submitted vs Not Submitted documents
- PDF export (ReportLab), footer contains `copyright@eldhojacobsby2025`
- Login page with Operator, School, Password `@9852`; admin `ELDHOJACOB` always works; others have a 90‑day trial
- GUI header shows the developer tag

## Local Run (Windows/Mac/Linux)

```bash
python -m venv .venv
. .venv/Scripts/activate   # Windows
# or
source .venv/bin/activate  # macOS/Linux

pip install -r requirements.txt
streamlit run app.py
```

## Deploy on Streamlit Cloud (Option 2)

1. Push these 3 files to a GitHub repo: `app.py`, `requirements.txt`, `README.md`.
2. Go to https://share.streamlit.io/ → New app → Connect your repo.
3. Select branch + `app.py` as the entry file → Deploy.
4. (Optional) Add a **secrets** key/value in Streamlit Cloud for branding (not required).

**Note on Trial File:** The trial date is stored in a local file `.age_eligibility_config.json`.
- On Streamlit Cloud the filesystem resets on redeploys; for real persistence, you can swap to a small database (Deta/Firestore). Logic left unchanged here.

## LAN Tip
If you run locally on a school PC: others can open `http://<YOUR_PC_IP>:8501` on the same LAN.

## Buttons Behavior
- **Calculate** is enabled when a nationality exists (same behavior).
- **Download PDF** requires `reportlab` (already in requirements).

## Support Fonts and Colors
Design mirrors your desktop palette. Animations (blink) are approximated as static badges to keep logic unchanged and ensure stability on the web.
