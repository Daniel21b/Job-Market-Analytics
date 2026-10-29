"""Legacy entry point: the results frontend has moved to Next.js."""

import streamlit as st

st.set_page_config(page_title="Job Market Observatory — moved", page_icon="↗")
st.title("Job Market Observatory")
st.write("The interactive results dashboard has moved to a dedicated web application.")
st.link_button(
    "Explore the results", "https://danielberhane.vercel.app/en/analytics", type="primary"
)
st.caption("The new dashboard displays a dated, verified analysis snapshot with source evidence.")
