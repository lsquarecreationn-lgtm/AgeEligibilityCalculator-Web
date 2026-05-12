# Age Eligibility Calculator + School ERP Modules — Streamlit Web App

This Streamlit application includes two authenticated work areas:

1. **Age Eligibility Calculator** — Calculates age on a configured cut-off date, validates class eligibility, tracks mandatory documents, and keeps the original two-panel workflow.
2. **School ERP Modules** — A full school ERP module blueprint covering student records, admissions, fees, transport, attendance, exams, academics, HR, payroll, portals, library, inventory, hostel, discipline, certificates, documents, communication, visitors, health, alumni, roles, reports, and settings.

## School ERP Coverage

The ERP area includes:

- Dashboard cards for all 25 modules.
- Search across module names, sections, and fields.
- Module explorer with expandable field groups.
- Prototype quick-entry forms for validating fields before database/workflow integration.

## Login

- Password: `@9852`
- Admin username: `ELDHOJACOB`
- Non-admin users have a 90-day trial based on `.age_eligibility_config.json`.

## Local Run (Windows/Mac/Linux)

```bash
python -m venv .venv
. .venv/Scripts/activate   # Windows
# or
source .venv/bin/activate  # macOS/Linux

pip install -r requirements.txt
streamlit run app.py
```

## Deploy on Streamlit Cloud

1. Push `app.py`, `requirements.txt`, and `README.md` to a GitHub repo.
2. Go to https://share.streamlit.io/ → New app → Connect your repo.
3. Select branch + `app.py` as the entry file → Deploy.
4. Add secrets or a database later if you want persistent ERP records.

## Persistence Note

The ERP quick-entry screen is a prototype and keeps values only in Streamlit session state. For production use, connect forms to a database and add role-based workflows per module.
