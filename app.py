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
</style>
""", unsafe_allow_html=True)

# 1) Build the blank template for days 1–31
df = pd.DataFrame({
    "Date": list(range(1, 32)),
    "গ্রহণের পরিমাণ (D)": np.nan,
    "বাকিতে নেওয়া (E)": np.nan,
    "G (চাল ব্যবহার)": np.nan,
    "I (Mon/Thu)": np.nan,
    "J (Tue/Fri)": np.nan,
    "K (Wed/Sat)": np.nan,
})

# 2) Configure AgGrid
gb = GridOptionsBuilder.from_dataframe(df)
# Prevent adding or removing rows
gb.configure_grid_options(suppressRowDrag=True)

# Date column – read-only, pinned left, light grey
gb.configure_column(
    "Date",
    editable=False,
    pinned='left',
    width=80,
    headerClass="header-dark",
    cellStyle={"backgroundColor": "#f2f2f2"}
)
# D column – editable, light cyan
gb.configure_column(
    "গ্রহণের পরিমাণ (D)", editable=True, width=140,
    headerClass="header-blue",
    cellStyle={"backgroundColor": "#e0f7fa"}
)
# E column – editable, light green
gb.configure_column(
    "বাকিতে নেওয়া (E)", editable=True, width=140,
    headerClass="header-green",
    cellStyle={"backgroundColor": "#e8f5e9"}
)
# G, I, J, K columns – read-only with pastel backgrounds
gb.configure_column(
    "G (চাল ব্যবহার)", editable=False, width=130,
    cellStyle={"backgroundColor": "#fff9c4"}
)
gb.configure_column(
    "I (Mon/Thu)", editable=False, width=130,
    cellStyle={"backgroundColor": "#ffe0b2"}
)
gb.configure_column(
    "J (Tue/Fri)", editable=False, width=130,
    cellStyle={"backgroundColor": "#f3e5f5"}
)
gb.configure_column(
    "K (Wed/Sat)", editable=False, width=130,
    cellStyle={"backgroundColor": "#fce4ec"}
)

grid_opts = gb.build()

# 3) Display editable grid
st.markdown("### 1) Enter D & E values in the table below:")
response = AgGrid(
    df,
    gridOptions=grid_opts,
    data_return_mode=DataReturnMode.FILTERED_AND_SORTED,
    update_mode=GridUpdateMode.MODEL_CHANGED,
    fit_columns_on_grid_load=True,
    enable_enterprise_modules=False,
    height=500,
    theme='alpine'
)

edited_df = pd.DataFrame(response["data"])

# 4) Baseline G₂ input
initial_G = st.number_input(
    "Baseline চাল ব্যবহার (G₂, Day 1)",
    min_value=0.0, step=0.1, format="%.2f"
)

# 5) Compute button
if st.button("Compute All G, I, J, K"):
    df2 = edited_df.copy()
    # Reset Date to 1–31 to ensure it's fixed
    df2["Date"] = list(range(1, 32))

    # Fill blanks with zeros
    df2["গ্রহণের পরিমাণ (D)"].fillna(0, inplace=True)
    df2["বাকিতে নেওয়া (E)"].fillna(0, inplace=True)

    # Compute G: G[0]=initial_G; G[n]=G[n-1] - F[n] + E[n-1]
    G = [initial_G]
    F_col = df2.get("চাল প্রাপ্তি", pd.Series(0, index=df2.index))
    for i in range(1, len(df2)):
        prev = G[-1]
        F_i = F_col.iloc[i]
        E_prev = df2["বাকিতে নেওয়া (E)"].iloc[i-1]
        G.append(prev - F_i + E_prev)
    df2["G (চাল ব্যবহার)"] = G

    # Compute weekly sums for D
    Dcol = df2["গ্রহণের পরিমাণ (D)"]
    df2["I (Mon/Thu)"] = [Dcol[i::7].sum() for i in df2.index]
    df2["J (Tue/Fri)"] = [Dcol[i+1::7].sum() for i in df2.index]
    df2["K (Wed/Sat)"] = [Dcol[i+2::7].sum() for i in df2.index]

    # 6) Show results in a second grid
    st.markdown("### Results Table:")
    AgGrid(
        df2,
        gridOptions=grid_opts,
        fit_columns_on_grid_load=True,
        height=500,
        theme='alpine'
    )
