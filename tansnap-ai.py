import streamlit as st
from PIL import Image
import pandas as pd
from datetime import datetime
import requests

st.set_page_config(page_title="TaxSnap AI", layout="wide")
st.title("🎮 TaxSnap AI")
st.caption("Vision AI + Auto Tax Insights • Any US State")

st.sidebar.header("Your Info")
year = st.sidebar.selectbox("Tax Year", [2025, 2026])
state = st.sidebar.selectbox("State", ["California", "New York", "Texas", "Florida", "Other"])
city = st.sidebar.text_input("City", "")

uploaded_files = st.file_uploader("Upload documents", type=["jpg", "jpeg", "png"], accept_multiple_files=True)

total_amount = 0.0
records = []

if uploaded_files:
    st.success(f"Processing {len(uploaded_files)} document(s)...")
    for file in uploaded_files:
        image = Image.open(file)
        st.image(image, caption=file.name, use_column_width=True)

        # Vision LLM Call
        try:
            response = requests.post(
                "http://localhost:11434/api/chat",
                json={
                    "model": "llava",
                    "messages": [{
                        "role": "user",
                        "content": "Extract tax-related info. Return only JSON: date, amount (number), vendor, category, deductible (yes/no).",
                        "images": [image.tobytes().hex()]
                    }]
                },
                timeout=30
            )
            ai_result = response.json()['message']['content']
        except:
            ai_result = "Could not analyze with Vision LLM."

        st.text_area("AI Analysis", ai_result, height=150)

        # Rough total extraction (for demo)
        try:
            amount = 150.0  # Placeholder - can improve with regex
            total_amount += amount
            records.append({"File": file.name, "Est Amount": amount, "Analysis": ai_result[:100]})
        except:
            pass

    st.metric("Total Estimated Amount from Documents", f"${total_amount:,.2f}")

# Estimator
st.subheader("Tax Estimate")
col1, col2 = st.columns(2)
with col1:
    income = st.number_input("Your Total Income", value=65000, step=1000)
with col2:
    expenses = st.number_input("Deductible Expenses (from uploads)", value=int(total_amount), step=500)

if st.button("Calculate Full Estimate"):
    taxable = max(0, income - expenses)
    st.success(f"**Estimated Taxable Income:** ${taxable:,.0f}")

st.caption("TaxSnap AI - For all 50 states")
