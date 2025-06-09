import streamlit as st
import pandas as pd

# --- App Configuration ---
st.set_page_config(layout="centered", page_title="Snowflake Workload Calculator")

# --- Data ---
# Credits consumed per hour for each standard warehouse size.
CREDITS_PER_HOUR = {
    'X-Small': 1,
    'Small': 2,
    'Medium': 4,
    'Large': 8,
    'X-Large': 16,
    '2X-Large': 32,
    '3X-Large': 64,
    '4X-Large': 128,
    '5X-Large': 256,
    '6X-Large': 512,
}
WEEKS_PER_MONTH = 52 / 12 # Average weeks in a month for calculation

# --- Session State Initialization ---
# This preserves the list of workloads as users interact with the app.
if 'workloads' not in st.session_state:
    st.session_state.workloads = [
        {'name': 'Workload 1', 'size': 'Medium', 'count': 1, 'uptime': 8.0, 'days_per_week': 5} 
    ]
else:
    # Ensures older session data is compatible by adding new keys if missing.
    for i, workload in enumerate(st.session_state.workloads):
        if 'name' not in workload:
            workload['name'] = f"Workload {i + 1}"
        if 'days_per_week' not in workload:
            workload['days_per_week'] = 7 # Default to 7 for older workloads

# --- UI ---
st.title("❄️ Snowflake Workload Calculator")

st.write(
    "This Streamlit app helps estimate your workloads and their monthly Snowflake credit usage. "
    "Add, remove, and configure your workloads below."
)

st.divider()

# --- Workload Management ---
total_daily_credits = 0
total_monthly_credits = 0
workload_summary_data = [] # Holds data for the final summary table.

# Loop through and display each workload configuration section.
for i, workload in enumerate(st.session_state.workloads):
    with st.container(border=True):
        st.session_state.workloads[i]['name'] = st.text_input(
            "Workload Name",
            value=workload['name'],
            key=f"name_{i}"
        )

        col1, col2, col3 = st.columns([2,2,1])

        with col1:
            st.session_state.workloads[i]['size'] = st.selectbox(
                "Warehouse Size:",
                options=list(CREDITS_PER_HOUR.keys()),
                index=list(CREDITS_PER_HOUR.keys()).index(workload['size']),
                key=f"size_{i}"
            )

        with col2:
            st.session_state.workloads[i]['count'] = st.number_input(
                "Number of Warehouses:",
                min_value=1,
                value=workload['count'],
                step=1,
                key=f"count_{i}"
            )
        
        with col3:
            st.write("") 
            st.write("")
            # "Remove" button for the current workload.
            if st.button("Remove", key=f"remove_{i}"):
                st.session_state.workloads.pop(i)
                st.rerun()

        uptime_col, days_col = st.columns(2)
        with uptime_col:
            st.session_state.workloads[i]['uptime'] = st.slider(
                "Average Daily Uptime (Hours):",
                min_value=0.0,
                max_value=24.0,
                value=workload['uptime'],
                step=0.5,
                key=f"uptime_{i}"
            )
        
        with days_col:
            st.session_state.workloads[i]['days_per_week'] = st.slider(
                "Active Days per Week:",
                min_value=1,
                max_value=7,
                value=workload['days_per_week'],
                step=1,
                key=f"days_{i}"
            )

        # --- Workload Calculation ---
        credits_for_size = CREDITS_PER_HOUR[st.session_state.workloads[i]['size']]
        workload_daily_credits = credits_for_size * st.session_state.workloads[i]['uptime'] * st.session_state.workloads[i]['count']
        workload_monthly_credits = workload_daily_credits * st.session_state.workloads[i]['days_per_week'] * WEEKS_PER_MONTH
        
        total_daily_credits += workload_daily_credits
        total_monthly_credits += workload_monthly_credits

        # Add this workload's calculated data to the summary list.
        workload_summary_data.append({
            "Workload": st.session_state.workloads[i]['name'],
            "Size": st.session_state.workloads[i]['size'],
            "# Warehouses": st.session_state.workloads[i]['count'],
            "Daily Uptime": st.session_state.workloads[i]['uptime'],
            "Active Days/Week": st.session_state.workloads[i]['days_per_week'],
            "Est. Daily Credits": workload_daily_credits,
            "Est. Monthly Credits": workload_monthly_credits
        })
        
        st.info(f"Estimated daily credits for this workload (on an active day): **{workload_daily_credits:,.2f}**")

# Button to add a new workload.
if st.button("Add New Workload"):
    new_workload_name = f"Workload {len(st.session_state.workloads) + 1}"
    st.session_state.workloads.append({'name': new_workload_name, 'size': 'X-Small', 'count': 4, 'uptime': 8.0, 'days_per_week': 5})
    st.rerun()

st.divider()

# --- Summary Table ---
if workload_summary_data:
    st.header("Workload Summary")
    summary_df = pd.DataFrame(workload_summary_data)
    # Set the DataFrame index to start at 1 instead of 0.
    summary_df.index = summary_df.index + 1
    
    st.dataframe(
        summary_df.style.format({
            'Est. Daily Credits': '{:,.2f}',
            'Est. Monthly Credits': '{:,.2f}'
        }),
        use_container_width=True
    )

# --- Aggregate Results ---
st.header("Total Estimated Consumption")
res_col1, res_col2, res_col3 = st.columns(3)

with res_col1:
    st.metric(
        label="Total Daily Credits",
        value=f"{total_daily_credits:,.2f}",
        help="Represents the total credits consumed on a day when all workloads are active."
    )

with res_col2:
    st.metric(
        label="Total Monthly Credits",
        value=f"{total_monthly_credits:,.2f}",
        help=f"Calculated based on the active days per week for each workload over an average of {WEEKS_PER_MONTH:.2f} weeks per month."
    )

with res_col3:
    st.metric(
        label="Total Annual Credits",
        value=f"{total_monthly_credits * 12:,.2f}",
        help="An estimate calculated by multiplying the total monthly credits by 12."
    )


# --- Disclaimer ---
st.info(
    "**Disclaimer:** This is an estimate for standard warehouses. "
    "Actual costs may vary based on your Snowflake contract's credit price, "
    "per-second billing (with a 60-second minimum), auto-suspension settings, "
    "and usage of other services like Cloud Services or Serverless features."
)
