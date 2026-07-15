import streamlit as st
from PIL import Image
import pytesseract
import cv2
import numpy as np
import pandas as pd
from datetime import datetime

st.set_page_config(page_title="TaxSnap AI", page_icon="🎮", layout="wide")

st.title("🎮 TaxSnap AI")
st.caption("Upload documents • Get smart tax insights for any US state")

# Sidebar - Full State & City
st.sidebar.header("Your Location")
year = st.sidebar.selectbox("Tax Year", [2025, 2026])

# Full list of US States
states = ["Alabama", "Alaska", "Arizona", "Arkansas", "California", "Colorado", "Connecticut", "Delaware", 
          "Florida", "Georgia", "Hawaii", "Idaho", "Illinois", "Indiana", "Iowa", "Kansas", "Kentucky", 
          "Louisiana", "Maine", "Maryland", "Massachusetts", "Michigan", "Minnesota", "Mississippi", 
          "Missouri", "Montana", "Nebraska", "Nevada", "New Hampshire", "New Jersey", "New Mexico", 
          "New York", "North Carolina", "North Dakota", "Ohio", "Oklahoma", "Oregon", "Pennsylvania", 
          "Rhode Island", "South Carolina", "South Dakota", "Tennessee", "Texas", "Utah", "Vermont", 
          "Virginia", "Washington", "West Virginia", "Wisconsin", "Wyoming"]

state = st.sidebar.selectbox("State", states)
city = st.sidebar.text_input("City", placeholder="e.g. New York, Los Angeles, Chicago, Austin...")

occupation = st.sidebar.selectbox("Occupation", 
    ["Salaried Employee", "Freelancer / Gig Worker", "Small Business Owner", 
     "Student", "Retired", "Investor", "Other"])

tax_scope = st.sidebar.radio("Calculate", ["Federal Only", "Federal + State"])

st.markdown("---")

uploaded_files = st.file_uploader(
    "Upload receipts, W-2s, 1099s, or invoices", 
    type=["jpg", "jpeg", "png"], 
    accept_multiple_files=True
)

if uploaded_files:
    st.success(f"✅ {len(uploaded_files)} document(s) uploaded")
    for file in uploaded_files:
        col1, col2 = st.columns([1, 2])
        with col1:
            image = Image.open(file)
            st.image(image, caption=file.name, use_column_width=True)

        with col2:
            st.subheader("Document Analysis")
            img_cv = cv2.cvtColor(np.array(image), cv2.COLOR_RGB2BGR)
            gray = cv2.cvtColor(img_cv, cv2.COLOR_BGR2GRAY)
            text = pytesseract.image_to_string(gray, config='--psm 6')
            st.text_area("Extracted Text", text[:700] + "..." if len(text) > 700 else text, height=200)

st.subheader("💰 Quick Tax Estimate")
col1, col2 = st.columns(2)
with col1:
    income = st.number_input("Total Income", value=65000, step=1000)
with col2:
    expenses = st.number_input("Deductible Expenses", value=15000, step=500)

if st.button("Calculate Estimate", type="primary"):
    taxable = max(0, income - expenses)
    st.success(f"**Estimated Taxable Income:** ${taxable:,.0f}")
    st.info(f"Note: This is a rough estimate for {state}. State taxes vary significantly.")

st.caption("TaxSnap AI — Works for any city and state in the US")
