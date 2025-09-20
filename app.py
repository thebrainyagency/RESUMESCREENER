import streamlit as st
from ui.steps import step1_setup, step2_uploads, step3_process, step4_results
from ui.components import show_progress_indicator
from ui.utils import init_session_state

st.set_page_config(
    page_title="Resume Screener",
    page_icon="📄",
    layout="wide"
)

def main():
    """Main Streamlit app entry point"""
    # Initialize session state
    init_session_state()

    # Header
    st.title("📄 Resume Screener")
    st.markdown("AI-powered resume screening with custom rubrics")

    # Show progress indicator
    show_progress_indicator(st.session_state.step)

    st.divider()

    # Route to appropriate step
    if st.session_state.step == 1:
        step1_setup()
    elif st.session_state.step == 2:
        step2_uploads()
    elif st.session_state.step == 3:
        step3_process()
    elif st.session_state.step == 4:
        step4_results()

if __name__ == "__main__":
    main()