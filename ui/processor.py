import streamlit as st
import tempfile
import os
import time
from src.parser import parse_resumes
from src.prefilter import prefilter_resumes
from src.scorer import score_with_llm
from src.ranker import aggregate_and_rank
from ui.utils import calculate_k_value

def process_resumes():
    """Process the resumes and show progress"""
    st.header("⏳ Processing...")

    # Create temporary directory for uploaded files
    with tempfile.TemporaryDirectory() as temp_dir:
        progress_bar = st.progress(0)
        status_text = st.empty()

        try:
            # Step 1: Save uploaded files
            status_text.text("📁 Saving uploaded files...")
            for i, uploaded_file in enumerate(st.session_state.uploaded_resumes):
                file_path = os.path.join(temp_dir, uploaded_file.name)
                with open(file_path, "wb") as f:
                    f.write(uploaded_file.getvalue())
                progress_bar.progress((i + 1) / len(st.session_state.uploaded_resumes) * 0.2)

            # Step 2: Parse resumes
            status_text.text("📄 Parsing resumes...")
            resumes = parse_resumes(temp_dir)
            progress_bar.progress(0.3)

            # Step 3: Prefilter
            status_text.text("🔍 Prefiltering with TF-IDF...")
            k_value = calculate_k_value(
                len(resumes),
                st.session_state.prefilter_percent
            )
            shortlisted = prefilter_resumes(resumes, st.session_state.jd_text, top_k=k_value)
            progress_bar.progress(0.4)

            # Step 4: Parse rubric (save rubric temporarily and set path)
            status_text.text("📊 Parsing rubric...")
            rubric_path = os.path.join(temp_dir, "rubric.txt")
            with open(rubric_path, "w") as f:
                f.write(st.session_state.rubric_text)
            os.environ["RUBRIC_PATH"] = rubric_path
            progress_bar.progress(0.5)

            # Step 5: Score with LLM
            status_text.text("🤖 Scoring with LLM...")
            results = []
            for i, resume in enumerate(shortlisted):
                scored = score_with_llm(resume, st.session_state.jd_text)
                results.append(scored)
                progress = 0.5 + (i + 1) / len(shortlisted) * 0.4
                progress_bar.progress(progress)
                status_text.text(f"🤖 Scoring with LLM... ({i + 1}/{len(shortlisted)})")

            # Step 6: Rank results
            status_text.text("📈 Ranking results...")
            ranked_results = aggregate_and_rank(results)
            progress_bar.progress(1.0)

            # Store results
            st.session_state.results = ranked_results
            status_text.text("✅ Processing complete!")

            # Move to results step
            time.sleep(1)
            st.session_state.step = 4
            st.rerun()

        except Exception as e:
            st.error(f"❌ Error during processing: {str(e)}")
            status_text.text("❌ Processing failed")
            st.stop()