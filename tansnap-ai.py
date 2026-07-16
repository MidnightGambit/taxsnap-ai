"""
TaxSnap AI — US tax document assistant.
ZIP → city/state • Occupation • Federal / State scope
"""
import re
from datetime import datetime

import cv2
import numpy as np
import pandas as pd
import streamlit as st
from PIL import Image

try:
    import zipcodes
except ImportError:
    zipcodes = None

try:
    import requests
except ImportError:
    requests = None

US_STATES = [
    "Alabama", "Alaska", "Arizona", "Arkansas", "California", "Colorado",
    "Connecticut", "Delaware", "Florida", "Georgia", "Hawaii", "Idaho",
    "Illinois", "Indiana", "Iowa", "Kansas", "Kentucky", "Louisiana", "Maine",
    "Maryland", "Massachusetts", "Michigan", "Minnesota", "Mississippi",
    "Missouri", "Montana", "Nebraska", "Nevada", "New Hampshire", "New Jersey",
    "New Mexico", "New York", "North Carolina", "North Dakota", "Ohio",
    "Oklahoma", "Oregon", "Pennsylvania", "Rhode Island", "South Carolina",
    "South Dakota", "Tennessee", "Texas", "Utah", "Vermont", "Virginia",
    "Washington", "West Virginia", "Wisconsin", "Wyoming",
]

STATE_ABBR_TO_NAME = {
    "AL": "Alabama", "AK": "Alaska", "AZ": "Arizona", "AR": "Arkansas",
    "CA": "California", "CO": "Colorado", "CT": "Connecticut", "DE": "Delaware",
    "FL": "Florida", "GA": "Georgia", "HI": "Hawaii", "ID": "Idaho",
    "IL": "Illinois", "IN": "Indiana", "IA": "Iowa", "KS": "Kansas",
    "KY": "Kentucky", "LA": "Louisiana", "ME": "Maine", "MD": "Maryland",
    "MA": "Massachusetts", "MI": "Michigan", "MN": "Minnesota", "MS": "Mississippi",
    "MO": "Missouri", "MT": "Montana", "NE": "Nebraska", "NV": "Nevada",
    "NH": "New Hampshire", "NJ": "New Jersey", "NM": "New Mexico", "NY": "New York",
    "NC": "North Carolina", "ND": "North Dakota", "OH": "Ohio", "OK": "Oklahoma",
    "OR": "Oregon", "PA": "Pennsylvania", "RI": "Rhode Island", "SC": "South Carolina",
    "SD": "South Dakota", "TN": "Tennessee", "TX": "Texas", "UT": "Utah",
    "VT": "Vermont", "VA": "Virginia", "WA": "Washington", "WV": "West Virginia",
    "WI": "Wisconsin", "WY": "Wyoming", "DC": "District of Columbia",
}

def normalize_zip(zip_input):
    digits = re.sub(r"\D", "", (zip_input or "").strip())
    if len(digits) < 5:
        return None
    return digits[:5]

def lookup_location_from_zip(zip_input):
    zip5 = normalize_zip(zip_input)
    if not zip5:
        return None, None, None

    if zipcodes:
        try:
            matches = zipcodes.matching(zip5)
            if matches:
                m = matches[0]
                abbr = (m.get("state") or "").upper()
                city = m.get("city") or m.get("default_city")
                state_name = STATE_ABBR_TO_NAME.get(abbr, abbr)
                return city, state_name, zip5
        except Exception:
            pass

    if requests:
        try:
            r = requests.get(f"https://api.zippopotam.us/us/{zip5}", timeout=8)
            if r.ok:
                data = r.json()
                places = data.get("places") or []
                if places:
                    p = places[0]
                    abbr = (data.get("state abbreviation") or "").upper()
                    city = p.get("place name")
                    state_name = STATE_ABBR_TO_NAME.get(abbr, data.get("state") or abbr)
                    return city, state_name, zip5
        except Exception:
            pass

    return None, None, zip5

def extract_dollar_amounts(text):
    if not text:
        return []
    amounts = []
    for m in re.finditer(r"\$?\s*(\d{1,3}(?:,\d{3})*(?:\.\d{2})?|\d+\.\d{2})", text):
        raw = m.group(1).replace(",", "")
        try:
            val = float(raw)
            if 0.01 <= val <= 9_999_999:
                amounts.append(val)
        except ValueError:
            continue
    return amounts

def guess_category(text):
    lower = text.lower()
    if any(w in lower for w in ("w-2", "w2", "wages", "withholding")):
        return "Wages / W-2"
    if any(w in lower for w in ("1099", "nec", "misc")):
        return "1099 / Other income"
    if any(w in lower for w in ("medical", "doctor", "pharmacy", "hospital")):
        return "Medical"
    if any(w in lower for w in ("charity", "donation", "church")):
        return "Charitable"
    if any(w in lower for w in ("rent", "utilities", "internet", "office")):
        return "Home office / utilities"
    return "Business / general expense"

def run_ocr(image):
    try:
        import pytesseract
    except ImportError:
        return ""
    try:
        img_cv = cv2.cvtColor(np.array(image.convert("RGB")), cv2.COLOR_RGB2BGR)
        gray = cv2.cvtColor(img_cv, cv2.COLOR_BGR2GRAY)
        enhanced = cv2.adaptiveThreshold(
            gray, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY, 11, 2
        )
        return pytesseract.image_to_string(enhanced, config="--psm 6") or ""
    except Exception:
        return ""

def looks_like_document(text):
    if len(text.strip()) < 15:
        return False
    lower = text.lower()
    hints = (
        "total", "tax", "receipt", "invoice", "amount", "w-2", "1099",
        "subtotal", "date", "payment", "balance", "wage", "employer",
    )
    return any(h in lower for h in hints) or sum(c.isdigit() for c in text) > 8

# --- UI ---
st.set_page_config(page_title="TaxSnap AI", page_icon="🎮", layout="wide")

st.title("🎮 TaxSnap AI")
st.caption("ZIP finds your city • Upload docs • Federal & state-aware estimates")

st.sidebar.header("📍 Location")
tax_year = st.sidebar.selectbox("Tax year", [2025, 2026], index=1)
zip_code = st.sidebar.text_input("ZIP code", placeholder="e.g. 10001", max_chars=10)

zip_city, zip_state, zip5 = lookup_location_from_zip(zip_code)
if zip_city and zip_state:
    st.sidebar.success(f"📌 {zip_city}, {zip_state} ({zip5})")
elif zip5 and zip_code.strip():
    st.sidebar.warning("ZIP not found — pick state below.")

state_override = st.sidebar.selectbox(
    "State (override if needed)",
    US_STATES,
    index=US_STATES.index(zip_state) if zip_state in US_STATES else 0,
)
effective_state = zip_state or state_override
effective_city = zip_city or st.sidebar.text_input("City (if no ZIP)", placeholder="Any city")

st.sidebar.header("👤 You")
occupation = st.sidebar.selectbox(
    "Occupation",
    [
        "Salaried employee",
        "Freelancer / gig worker",
        "Small business owner",
        "Student",
        "Retired",
        "Investor",
        "Other",
    ],
)

tax_scope = st.sidebar.radio("Tax scope", ["Federal only", "Federal + state"])

st.sidebar.markdown("---")
st.sidebar.caption(f"**{occupation}** • {effective_city or '—'}, {effective_state}")

st.markdown("---")

uploaded_files = st.file_uploader(
    "Upload receipts, W-2s, 1099s, or invoices (JPG/PNG)",
    type=["jpg", "jpeg", "png"],
    accept_multiple_files=True,
)

records = []
upload_expense_total = 0.0

if uploaded_files:
    st.success(f"🎯 {len(uploaded_files)} file(s) — analyzing…")
    progress = st.progress(0)

    for i, file in enumerate(uploaded_files):
        progress.progress((i + 1) / len(uploaded_files))
        col_img, col_data = st.columns([1, 1.6])

        with col_img:
            try:
                image = Image.open(file)
                st.image(image, caption=file.name, use_container_width=True)
            except Exception:
                st.error(f"Could not open {file.name}")
                continue

        with col_data:
            text = run_ocr(image)
            if not text.strip():
                st.info("OCR unavailable or no text — use manual amounts below.")
                is_doc = False
            elif not looks_like_document(text):
                st.warning("Doesn’t look like a tax document (e.g. a selfie). Use a receipt or form.")
                is_doc = False
            else:
                is_doc = True
                st.text_area("Extracted text", text[:900] + ("…" if len(text) > 900 else ""), height=160)

            amounts = extract_dollar_amounts(text) if text else []
            est_amount = max(amounts) if amounts else 0.0
            if is_doc and est_amount:
                upload_expense_total += est_amount

            category = guess_category(text) if text else "Unknown"
            records.append({
                "File": file.name,
                "Category": category,
                "Est. amount": f"${est_amount:,.2f}" if est_amount else "—",
                "State": effective_state,
            })

    progress.empty()

    if records:
        st.subheader("📋 Document summary")
        st.dataframe(pd.DataFrame(records), use_container_width=True, hide_index=True)
        if upload_expense_total > 0:
            st.metric("Total from uploads (estimated)", f"${upload_expense_total:,.2f}")

st.subheader("💰 Tax estimate")
c1, c2, c3 = st.columns(3)
with c1:
    income = st.number_input("Total income", min_value=0, value=65000, step=1000)
with c2:
    default_exp = int(upload_expense_total) if upload_expense_total else 12000
    expenses = st.number_input("Deductible expenses", min_value=0, value=default_exp, step=500)
with c3:
    federal_rate = st.slider("Rough federal rate %", 10, 37, 22)

if st.button("🚀 Calculate my estimate", type="primary", use_container_width=True):
    taxable = max(0, income - expenses)
    federal_est = taxable * (federal_rate / 100)
    st.success(f"**Estimated taxable income:** ${taxable:,.0f}")
    st.metric("Rough federal tax (estimate)", f"${federal_est:,.0f}")

    if tax_scope == "Federal + state":
        st.warning(
            f"**{effective_state}** (near {effective_city or 'your ZIP'}) has its own rules — "
            "use this for planning, not filing."
        )
    else:
        st.info("Federal only — state not included.")

    st.balloons()

st.caption(
    f"TaxSnap AI • Year {tax_year} • {tax_scope} • Not tax advice."
)
