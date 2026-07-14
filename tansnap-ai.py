import streamlit as st
from PIL import Image
import pytesseract
import cv2
import numpy as np
import pandas as pd
from datetime import datetime

st.set_page_config(page_title="TaxSnap AI", page_icon="📸", layout="wide")

# Header
st.markdown("""
<style>
    .big-font {font-size: 48px !important; font-weight: bold;}
</style>
""", unsafe_allow_html=True)

st.title("📸 TaxSnap AI")
st.subheader("Smart Document → Tax Insights")

st.sidebar.title("Settings")
year = st.sidebar.selectbox("Tax Year", [2025, 2026])
user_type = st.sidebar.selectbox("User Type", ["Individual", "Freelancer", "Small Business Owner"])

st.markdown("---")

uploaded_files = st.file_uploader(
    "Upload your receipts, W-2s, 1099s, invoices, or statements", 
    type=["jpg", "jpeg", "png"], 
    accept_multiple_files=True,
    help="Supports multiple files"
)

all_records = []

if uploaded_files:
    st.success(f"✅ {len(uploaded_files)} document(s) uploaded")
    
    for file in uploaded_files:
        col1, col2 = st.columns([1, 2])
        with col1:
            img = Image.open(file)
            st.image(img, caption=file.name, use_column_width=True)

        with col2:
            # Improved OCR
            img_cv = cv2.cvtColor(np.array(img), cv2.COLOR_RGB2BGR)
            gray = cv2.cvtColor(img_cv, cv2.COLOR_BGR2GRAY)
            text = pytesseract.image_to_string(gray, config='--psm 6')

            st.subheader("AI Analysis")
            st.text_area("Extracted Text", text[:600] + "..." if len(text) > 600 else text, height=180)

            # Smart Categorization
            category = "Business Expense"
            if any(word in text.lower() for word in ["medical", "doctor", "pharmacy"]):
                category = "Medical"
            elif any(word in text.lower() for word in ["charity", "donation"]):
                category = "Charitable"
            elif any(word in text.lower() for word in ["office", "rent", "utilities"]):
                category = "Home Office / Utilities"

            record = {
                "File": file.name,
                "Date": datetime.now().strftime("%Y-%m-%d"),
                "Category": category,
                "Deductible": "High",
                "Notes": "AI categorized"
            }
            all_records.append(record)

    if all_records:
        df = pd.DataFrame(all_records)
        st.subheader("📋 AI Processed Documents")
        st.dataframe(df, use_container_width=True)

# Tax Estimator
st.subheader("Quick Tax Estimate")
c1, c2, c3 = st.columns(3)
with c1:
    income = st.number_input("Total Income", value=65000, step=1000)
with c2:
    expenses = st.number_input("Deductible Expenses", value=12000, step=500)
with c3:
    st.metric("Est. Taxable Income", f"${max(0, income - expenses):,}")

st.caption("TaxSnap AI — Simple tax document assistant for individuals, freelancers & small businesses.")

st.success("✅ Improved general version loaded!")
