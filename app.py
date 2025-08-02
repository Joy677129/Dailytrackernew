from st_aggrid import GridOptionsBuilder

# … after you’ve built your initial df …

# 2) Configure AgGrid with per-column styling
gb = GridOptionsBuilder.from_dataframe(df)

# Date column – dark header, light grey cells
gb.configure_column(
    "Date",
    editable=False,
    width=80,
    headerClass="header-dark",
    cellStyle={"backgroundColor": "#f2f2f2"}
)

# D column – tinted light blue
gb.configure_column(
    "গ্রহণের পরিমাণ (D)",
    editable=True,
    width=140,
    headerClass="header-blue",
    cellStyle={"backgroundColor": "#e0f7fa"}  # light cyan
)

# E column – tinted light green
gb.configure_column(
    "বাকিতে নেওয়া (E)",
    editable=True,
    width=140,
    headerClass="header-green",
    cellStyle={"backgroundColor": "#e8f5e9"}  # light green
)

# G column – tinted light yellow
gb.configure_column(
    "G (চাল ব্যবহার)",
    editable=False,
    width=130,
    cellStyle={"backgroundColor": "#fff9c4"}  # light yellow
)

# I column – tinted light orange
gb.configure_column(
    "I (Mon/Thu)",
    editable=False,
    width=130,
    cellStyle={"backgroundColor": "#ffe0b2"}  # light orange
)

# J column – tinted light purple
gb.configure_column(
    "J (Tue/Fri)",
    editable=False,
    width=130,
    cellStyle={"backgroundColor": "#f3e5f5"}  # light purple
)

# K column – tinted light pink
gb.configure_column(
    "K (Wed/Sat)",
    editable=False,
    width=130,
    cellStyle={"backgroundColor": "#fce4ec"}  # light pink
)

grid_opts = gb.build()
