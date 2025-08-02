import streamlit as st
import pandas as pd
import numpy as np

st.set_page_config(page_title="Rice‐Flow Table", layout="wide")
st.title("Monthly Rice‐Flow Calculator")

# 1) Prepare an empty template for days 1–31
template = pd.DataFrame({
    "Date": list(range(1, 32)),
    "গ্রহণের পরিমাণ (D)": np.nan,
    "বাকিতে নেওয়া (E)": np.nan,
})

st.markdown("### 1) Enter your daily inputs (columns D & E)")
# 2) Let the user edit that template in a table 📝
#    (requires Streamlit >= 1.18.0)
edited = st.data_editor(
    template,
    num_rows="fixed",        # don't let them add/delete rows
    hide_index=True,
    key="daily_inputs",
)

# 3) Ask for the baseline G₂ value
initial_G = st.number_input(
    "Baseline চাল ব্যবহার (G₂, the starting G on Day 1)",
    min_value=0.0, value=0.0, format="%.2f"
)

# 4) Once they’ve filled it, hit “Compute”
if st.button("Compute G, I, J, K for all days"):
    df = edited.copy()

    # sanity-check: fill any blank D/E with zeros
    df["গ্রহণের পরিমাণ (D)"].fillna(0, inplace=True)
    df["বাকিতে নেওয়া (E)"].fillna(0, inplace=True)

    # 5) compute G exactly like your Excel
    G = [initial_G]
    for i in range(1, len(df)):
        prev = G[i-1]
        F_i    = df.loc[i, "চাল প্রাপ্তি"]     if "চাল প্রাপ্তি"     in df else 0
        E_prev = df.loc[i-1, "বাকিতে নেওয়া (E)"]
        # replace F_i line with your actual column if needed
        G.append(prev - F_i + E_prev)
    df["G (চাল ব্যবহার)"] = G

    # 6) compute the 7-day offsets I, J, K
    D = df["গ্রহণের পরিমাণ (D)"]
    df["I (Mon/Thu)"] = [D[i::7].sum() for i in df.index]
    df["J (Tue/Fri)"] = [D[i+1::7].sum() for i in df.index]
    df["K (Wed/Sat)"] = [D[i+2::7].sum() for i in df.index]

    # 7) show the full table
    st.markdown("### Results Table")
    st.dataframe(df, use_container_width=True)
