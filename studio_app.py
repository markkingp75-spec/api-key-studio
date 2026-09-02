import streamlit as st
import requests

st.title("🔑 Custom API Key Studio")
st.markdown("Generate and manage your API keys to power your automation and social marketing projects.")

email_input = st.text_input("Enter your email address")
tier_selection = st.selectbox("Choose API Tier", ["free", "pro (Paid Standard)"])

if st.button("Generate API Key"):
    if email_input:
        tier_val = "pro" if "pro" in tier_selection else "free"
        try:
            response = requests.post(
                "http://127.0.0.1:8000/studio/api/v1/register",
                json={"email": email_input, "requested_tier": tier_val}
            )
            if response.status_code == 200:
                data = response.json()
                st.success(f"Success! Assigned Tier: **{data['tier'].upper()}**")
                st.code(data["api_key"], language="text")
                st.info("Copy your API key safely. Use it in your project headers under `X-API-Key`.")
            else:
                st.error("Failed to generate key.")
        except Exception as e:
            st.error(f"Could not connect to Studio backend: {e}")
    else:
        st.warning("Please provide a valid email.")