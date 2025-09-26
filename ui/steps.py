import streamlit as st
import pandas as pd
from ui.components import (
    show_file_upload, show_cost_estimation, show_navigation_buttons,
    show_summary_stats, show_results_table
)
from ui.utils import (
    validate_api_key, set_environment_variables, calculate_k_value,
    load_sample_rubric, reset_to_step_one
)
from ui.processor import process_resumes

def step1_setup():
    """Step 1: API Key and Model Selection"""
    st.header("🔧 Setup & Configuration")

    col1, col2 = st.columns(2)

    with col1:
        # Check if API key already exists in environment
        if st.session_state.api_key and validate_api_key(st.session_state.api_key):
            st.success("✅ Using API key from environment")
            st.text_input(
                "OpenAI API Key",
                value="sk-***" + st.session_state.api_key[-4:],
                disabled=True,
                help="API key loaded from environment variable"
            )
            api_key = st.session_state.api_key

            # Option to override
            if st.checkbox("Override with different API key"):
                api_key = st.text_input(
                    "Enter new API Key",
                    type="password",
                    help="Enter a different OpenAI API key"
                )
                if api_key:
                    if validate_api_key(api_key):
                        st.success("✅ Valid API key format")
                        st.session_state.api_key = api_key
                        set_environment_variables(api_key, st.session_state.model_choice)
                    else:
                        st.error("❌ Invalid API key format")
        else:
            api_key = st.text_input(
                "OpenAI API Key",
                type="password",
                value=st.session_state.api_key,
                help="Enter your OpenAI API key (starts with sk-)"
            )

            if api_key:
                if validate_api_key(api_key):
                    st.success("✅ Valid API key format")
                    st.session_state.api_key = api_key
                    set_environment_variables(api_key, st.session_state.model_choice)
                else:
                    st.error("❌ Invalid API key format")

    with col2:
        model = st.selectbox(
            "LLM Model",
            ["gpt-4o", "gpt-4o-mini"],
            index=0 if st.session_state.model_choice == "gpt-4o" else 1,
            help="gpt-4o is more accurate, gpt-4o-mini is cheaper"
        )
        st.session_state.model_choice = model

        if api_key and validate_api_key(api_key):
            set_environment_variables(api_key, model)

        show_cost_estimation(100, model)  # Show cost for 100 resumes as example

    # Navigation
    show_navigation_buttons(1, validate_api_key(api_key))

def step2_uploads():
    """Step 2: File Uploads and Inputs"""
    st.header("📁 Upload Inputs")

    # Resume upload
    st.subheader("1. Upload Resumes")
    uploaded_files = show_file_upload()
    if uploaded_files:
        st.session_state.uploaded_resumes = uploaded_files

    # Job Description
    st.subheader("2. Job Description")
    jd_text = st.text_area(
        "Enter the job description",
        value=st.session_state.jd_text,
        height=200,
        help="Paste the full job description here"
    )
    st.session_state.jd_text = jd_text

    # Rubric
    st.subheader("3. Scoring Rubric")

    col1, col2 = st.columns([3, 1])
    with col2:
        if st.button("Load Sample"):
            sample_rubric = load_sample_rubric()
            if sample_rubric:
                st.session_state.rubric_text = sample_rubric
                st.rerun()
            else:
                st.error("Sample rubric not found")

    with col1:
        rubric_text = st.text_area(
            "Enter the scoring rubric",
            value=st.session_state.rubric_text,
            height=300,
            help="Define your scoring criteria and point allocations"
        )
        st.session_state.rubric_text = rubric_text

    # Prefilter settings
    if uploaded_files:
        st.subheader("4. Prefiltering Settings")
        col1, col2 = st.columns(2)

        with col1:
            total_resumes = len(uploaded_files)
            prefilter_percent = st.slider(
                "Percentage of resumes to score with LLM",
                min_value=10,
                max_value=100,
                value=st.session_state.prefilter_percent,
                step=5,
                help="Higher percentage = more accurate but more expensive"
            )
            st.session_state.prefilter_percent = prefilter_percent

            k_value = calculate_k_value(total_resumes, prefilter_percent)
            st.info(f"Will score top {k_value} resumes out of {total_resumes} total")

        with col2:
            show_cost_estimation(k_value, st.session_state.model_choice)

    # Navigation
    can_proceed = (
        uploaded_files and
        len(jd_text.strip()) > 0 and
        len(rubric_text.strip()) > 0
    )
    show_navigation_buttons(2, can_proceed)

def step3_process():
    """Step 3: Review and Process"""
    st.header("🔍 Review & Process")

    # Summary
    st.subheader("Input Summary")
    total_resumes = len(st.session_state.uploaded_resumes)
    k_value = calculate_k_value(total_resumes, st.session_state.prefilter_percent)

    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Resumes", total_resumes)
    with col2:
        st.metric("Will Score", k_value)
    with col3:
        st.metric("Model", st.session_state.model_choice)
    with col4:
        show_cost_estimation(k_value, st.session_state.model_choice)

    # Preview inputs
    with st.expander("📋 Job Description Preview"):
        preview_text = st.session_state.jd_text[:500]
        if len(st.session_state.jd_text) > 500:
            preview_text += "..."
        st.text_area("Preview", value=preview_text, height=100, disabled=True, label_visibility="hidden", key="jd_preview")

    with st.expander("📊 Rubric Preview"):
        preview_text = st.session_state.rubric_text[:500]
        if len(st.session_state.rubric_text) > 500:
            preview_text += "..."
        st.text_area("Preview", value=preview_text, height=100, disabled=True, label_visibility="hidden", key="rubric_preview")

    # Navigation and process
    col1, col2 = st.columns(2)
    with col1:
        if st.button("← Back"):
            st.session_state.step = 2
            st.rerun()

    with col2:
        if st.button("🚀 Start Screening", type="primary"):
            # Process resumes and move to results
            process_resumes()

def step4_results():
    """Step 4: Display Results"""
    st.header("📊 Results")

    if st.session_state.results is None:
        st.error("No results available")
        return

    results = st.session_state.results

    # Summary statistics
    st.subheader("📈 Summary Statistics")
    show_summary_stats(results)

    # Results table
    st.subheader("🏆 Ranking Table")
    show_results_table(results)

    # Individual resume details
    st.subheader("📋 Individual Resume Details")
    df = pd.DataFrame(results)

    selected_resume = st.selectbox(
        "Select a resume to view details",
        options=df['resume_file_name'].tolist(),
        key="selected_resume"
    )

    if selected_resume:
        resume_data = df[df['resume_file_name'] == selected_resume].iloc[0]

        col1, col2 = st.columns(2)

        with col1:
            st.write("**Basic Information:**")
            st.write(f"**Name:** {resume_data.get('applicant_name', 'N/A')}")
            st.write(f"**Email:** {resume_data.get('email', 'N/A')}")
            st.write(f"**Phone:** {resume_data.get('phone', 'N/A')}")
            st.write(f"**Total Score:** {resume_data.get('total_score', 'N/A')}")

        with col2:
            st.write("**Dimension Scores:**")
            score_columns = [
                col for col in df.columns
                if col.endswith('_score') and col not in ['total_score', 'prefilter_score']
            ]
            for col in score_columns:
                dimension_name = col.replace('_score', '').replace('_', ' ').title()
                st.write(f"**{dimension_name}:** {resume_data.get(col, 'N/A')}")

    # Navigation and downloads
    col1, col2 = st.columns(2)

    with col1:
        if st.button("← Start New"):
            reset_to_step_one()
            st.rerun()

    with col2:
        # Download CSV
        csv = df.to_csv(index=False)
        st.download_button(
            label="📥 Download Results CSV",
            data=csv,
            file_name="resume_screening_results.csv",
            mime="text/csv"
        )