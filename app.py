import streamlit as st
import pandas as pd
import numpy as np
from st_aggrid import AgGrid, GridOptionsBuilder, DataReturnMode, GridUpdateMode

st.set_page_config(page_title="Rice-Flow Table", layout="wide")
st.title("📊 Monthly Rice-Flow Calculator")

# 1) Build the blank template for days 1–31
df = pd.DataFrame({
    "Date": list(range(1, 32)),
    "গ্রহণের পরিমাণ (D)": np.nan,
    "বাকিতে নেওয়া (E)":    np.nan,
    "G (চাল ব্যবহার)":    np.nan,
    "I (Mon/Thu)":        np.nan,
    "J (Tue/Fri)":        np.nan,
    "K (Wed/Sat)":        np.nan,
})

# 2) Configure AgGrid
gb = GridOptionsBuilder.from_dataframe(df)
# Make Date read-only, D & E editable, others read-only
gb.configure_column("Date", editable=False, width=80)
gb.configure_column("গ্রহণের পরিমাণ (D)", editable=True, width=140)
gb.configure_column("বাকিতে নেওয়া (E)",    editable=True, width=140)
for c in ["G (চাল ব্যবহার)", "I (Mon/Thu)", "J (Tue/Fri)", "K (Wed/Sat)"]:
    gb.configure_column(c, editable=False, width=130, cellStyle={"backgroundColor":"#F5F5F5"})

# Freeze the header and Date column
gb.configure_grid_options(domLayout="normal")
gb.configure_grid_options(suppressRowClickSelection=True)
gb.configure_grid_options(rowSelection="single")
gb.configure_grid_options(floatingFilter=True)
grid_opts = gb.build()

# 3) Show the grid
st.markdown("### 1) Enter D & E values in the table below:")
grid_response = AgGrid(
    df,
    gridOptions=grid_opts,
    data_return_mode=DataReturnMode.FILTERED_AND_SORTED,
    update_mode=GridUpdateMode.MODEL_CHANGED,
    fit_columns_on_grid_load=True,
    enable_enterprise_modules=False,
    height=500,
)

edited_df = pd.DataFrame(grid_response["data"])

# 4) Baseline G₂
initial_G = st.number_input(
    "Baseline চাল ব্যবহার (G₂, Day 1)",
    min_value=0.0, step=0.1, format="%.2f"
)

# 5) Compute when user clicks
if st.button("Compute All G, I, J, K"):
    df2 = edited_df.copy()
    df2["গ্রহণের পরিমাণ (D)"].fillna(0, inplace=True)
    df2["বাকিতে নেওয়া (E)"].fillna(0, inplace=True)

    # G formula: G[0] = initial_G; G[n]=G[n-1] - F[n] + E[n-1]
    G = [initial_G]
    for i in range(1, len(df2)):
        prev = G[-1]
        # assume F = some fixed “চাল প্রাপ্তি” column? If absent use 0:
        F_i    = df2.get("চাল প্রাপ্তি", pd.Series(0)).iloc[i]
        E_prev = df2["বাকিতে নেওয়া (E)"].iloc[i-1]
        G.append(prev - F_i + E_prev)
    df2["G (চাল ব্যবহার)"] = G

    # Weekly sums
    Dcol = df2["গ্রহণের পরিমাণ (D)"]
    df2["I (Mon/Thu)"] = [Dcol[i::7].sum() for i in df2.index]
    df2["J (Tue/Fri)"] = [Dcol[i+1::7].sum() for i in df2.index]
    df2["K (Wed/Sat)"] = [Dcol[i+2::7].sum() for i in df2.index]

    # 6) Redisplay with formulas filled
    st.markdown("### Results (formulas applied):")
    AgGrid(
        df2,
        gridOptions=gb.build(),
        fit_columns_on_grid_load=True,
        height=500
    )
