import streamlit as st
import pandas as pd
from typing import List, Dict, Any

def show_progress_indicator(current_step: int):
    """Display progress indicator for the workflow"""
    progress_steps = ["Setup", "Upload", "Process", "Results"]

    cols = st.columns(4)
    for i, step_name in enumerate(progress_steps, 1):
        with cols[i-1]:
            if i < current_step:
                st.success(f"✅ {step_name}")
            elif i == current_step:
                st.info(f"⏳ {step_name}")
            else:
                st.write(f"⭕ {step_name}")

def show_file_upload(accept_multiple: bool = True) -> List:
    """Reusable file upload component"""
    uploaded_files = st.file_uploader(
        "Choose resume files",
        accept_multiple_files=accept_multiple,
        type=['pdf', 'docx', 'txt'],
        help="Upload PDF, DOCX, or TXT resume files"
    )

    if uploaded_files:
        file_count = len(uploaded_files) if accept_multiple else 1
        st.success(f"✅ {file_count} file{'s' if file_count > 1 else ''} uploaded")

        with st.expander("View uploaded files"):
            files = uploaded_files if accept_multiple else [uploaded_files]
            for file in files:
                st.write(f"📄 {file.name} ({file.size} bytes)")

    return uploaded_files

def show_cost_estimation(k_value: int, model: str):
    """Display cost estimation"""
    cost_per_resume = 0.0005 if model == "gpt-4o-mini" else 0.005
    estimated_cost = k_value * cost_per_resume

    st.metric("Estimated Cost", f"${estimated_cost:.3f}")

    if model == "gpt-4o-mini":
        st.info("💰 Cost-effective option")
    else:
        st.info("🎯 Higher accuracy option")

def show_summary_stats(results: List[Dict[str, Any]]):
    """Display summary statistics"""
    if not results:
        return

    df = pd.DataFrame(results)

    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.metric("Total Scored", len(results))
    with col2:
        avg_score = df['total_score'].mean()
        st.metric("Average Score", f"{avg_score:.1f}")
    with col3:
        top_score = df['total_score'].max()
        st.metric("Top Score", f"{top_score}")
    with col4:
        score_range = f"{df['total_score'].min()}-{df['total_score'].max()}"
        st.metric("Score Range", score_range)

def show_results_table(results: List[Dict[str, Any]]):
    """Display sortable results table"""
    if not results:
        return

    df = pd.DataFrame(results)

    # Select columns to display
    display_columns = [
        'resume_file_name', 'total_score', 'applicant_name',
        'email', 'phone', 'prefilter_score'
    ]
    available_columns = [col for col in display_columns if col in df.columns]

    # Format and display table
    display_df = df[available_columns].copy()
    display_df = display_df.round(2)

    st.dataframe(
        display_df,
        width="stretch",
        hide_index=True
    )

def show_navigation_buttons(current_step: int, can_proceed: bool = True):
    """Show navigation buttons for steps"""
    col1, col2 = st.columns(2)

    with col1:
        if current_step > 1:
            if st.button("← Back"):
                st.session_state.step = current_step - 1
                st.rerun()

    with col2:
        if current_step < 4:
            button_text = {
                1: "Next: Upload Files",
                2: "Next: Review & Process",
                3: "🚀 Start Screening"
            }.get(current_step, "Next")

            if st.button(button_text, disabled=not can_proceed, type="primary" if current_step == 3 else "secondary"):
                st.session_state.step = current_step + 1
                st.rerun()