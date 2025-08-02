import streamlit as st
import pandas as pd
import numpy as np
from st_aggrid import AgGrid, GridOptionsBuilder, DataReturnMode, GridUpdateMode

# Page configuration
st.set_page_config(page_title="Rice-Flow Table", layout="wide")
st.title("📊 Monthly Rice-Flow Calculator")

# Custom CSS for header styling
st.markdown("""
<style>
  .header-dark .ag-header-cell-label { background-color: #424242 !important; color: white; }
  .header-blue .ag-header-cell-label { background-color: #0288d1 !important; color: white; }
  .header-green .ag-header-cell-label { background-color: #43a047 !important; color: white; }
  .header-day .ag-header-cell-label { background-color: #6a1b9a !important; color: white; }
</style>
""", unsafe_allow_html=True)

# Ask user for the weekday of the 1st of the month
weekdays = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
first_day = st.selectbox("Select the weekday of the 1st of the month:", weekdays, index=0)
first_index = weekdays.index(first_day)

# Build blank template for days 1–31, default numeric to 0
dates = list(range(1, 32))
days = [weekdays[(first_index + d - 1) % 7] for d in dates]
RATE = 0.12  # Fixed rate for চাল প্রাপ্তি calculation

df_template = pd.DataFrame({
    "Date": dates,
    "Day": days,
    "গ্রহণের পরিমাণ (D)": 0.0,
    # F will be calculated as D * RATE, so show initial zeros but non-editable
    "চাল প্রাপ্তি (F)": 0.0,
    "বাকিতে নেওয়া (E)": 0.0,
    "G (চাল ব্যবহার)": 0.0,
})

# Configure AgGrid options for input grid
gb = GridOptionsBuilder.from_dataframe(df_template)
gb.configure_grid_options(suppressRowDrag=True)
for col, opts in {
    "Date": {"editable": False, "width": 80,  "headerClass": "header-dark", "bg": "#f2f2f2", "pinned": 'left'},
    "Day": {"editable": False, "width": 100, "headerClass": "header-day",  "bg": "#ede7f6", "pinned": 'left'},
    "গ্রহণের পরিমাণ (D)": {"editable": True,  "width": 140, "headerClass": "header-blue", "bg": "#e0f7fa"},
    "চাল প্রাপ্তি (F)": {"editable": False, "width": 130, "headerClass": "header-dark", "bg": "#fffde7"},
    "বাকিতে নেওয়া (E)": {"editable": True,  "width": 140, "headerClass": "header-green", "bg": "#e8f5e9"},
    "G (চাল ব্যবহার)": {"editable": False, "width": 130, "headerClass": "header-dark", "bg": "#fff9c4"},
}.items():
    gb.configure_column(
        col,
        editable=opts["editable"],
        width=opts["width"],
        headerClass=opts["headerClass"],
        pinned=opts.get("pinned"),
        cellStyle={"backgroundColor": opts["bg"]}
    )
grid_opts_input = gb.build()

# Display input grid
st.markdown("### 1) Enter D & E values in the table below (F is auto-calculated):")
response = AgGrid(
    df_template,
    gridOptions=grid_opts_input,
    data_return_mode=DataReturnMode.FILTERED_AND_SORTED,
    update_mode=GridUpdateMode.MODEL_CHANGED,
    fit_columns_on_grid_load=True,
    height=400,
    theme='alpine'
)
edited_df = pd.DataFrame(response["data"])

# Baseline G₂ input
initial_G = st.number_input("Baseline চাল ব্যবহার (G₂, Day 1)", min_value=0.0, step=0.1, format="%.2f")

# Compute button
if st.button("Compute All G"):
    # Prepare working copy and reset index for sequential access
    df2 = edited_df.copy().reset_index(drop=True)
    df2["Date"] = dates
    df2["Day"] = days

    # Coerce D & E to numeric, treat blanks as 0
    df2["গ্রহণের পরিমাণ (D)"] = pd.to_numeric(df2["গ্রহণের পরিমাণ (D)"], errors="coerce").fillna(0)
    df2["বাকিতে নেওয়া (E)"   ] = pd.to_numeric(df2["বাকিতে নেওয়া (E)"   ], errors="coerce").fillna(0)

    # Calculate F = D * RATE
    df2["চাল প্রাপ্তি (F)"] = df2["গ্রহণের পরিমাণ (D)"] * RATE

    # Calculate G sequentially
    G_vals = [initial_G]
    for i in range(1, len(df2)):
        prev = G_vals[-1]
        received = df2.iloc[i]["চাল প্রাপ্তি (F)"]
        carried = df2.iloc[i-1]["বাকিতে নেওয়া (E)"]
        G_vals.append(prev - received + carried)
    df2["G (চাল ব্যবহার)"] = G_vals

    # Compute weekly totals
    total_I = df2.loc[df2["Day"].isin(["Monday", "Thursday"]), "গ্রহণের পরিমাণ (D)"].sum()
    total_J = df2.loc[df2["Day"].isin(["Tuesday", "Friday"]),   "গ্রহণের পরিমাণ (D)"].sum()
    total_K = df2.loc[df2["Day"].isin(["Wednesday", "Saturday"]), "গ্রহণের পরিমাণ (D)"].sum()

    st.markdown("### Weekly Totals from গ্রহণের পরিমাণ (D):")
    st.write(f"**Mon/Thu (I)**: {total_I:.2f}")
    st.write(f"**Tue/Fri (J)**: {total_J:.2f}")
    st.write(f"**Wed/Sat (K)**: {total_K:.2f}")

    # Display results in read-only grid
    st.markdown("### Results Table:")
    gb2 = GridOptionsBuilder.from_dataframe(df2)
    gb2.configure_default_column(editable=False)
    AgGrid(
        df2,
        gridOptions=gb2.build(),
        fit_columns_on_grid_load=True,
        height=400,
        theme='alpine'
    )
