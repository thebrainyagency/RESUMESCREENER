import streamlit as st
import tempfile
import os
import time
import logging
from src.parser import parse_resumes
from src.prefilter import prefilter_resumes
from src.scorer import score_with_llm
from src.ranker import aggregate_and_rank
from ui.utils import calculate_k_value

# Set up logging to show in Streamlit
logging.basicConfig(level=logging.INFO)

def process_resumes():
    """Process the resumes and show progress"""
    st.header("⏳ Processing...")

    # Add warning about browser refresh
    st.warning("⚠️ **Important**: Do not refresh the browser or close this tab during processing - you'll lose all progress and have to start over!")

    # Create temporary directory for uploaded files
    with tempfile.TemporaryDirectory() as temp_dir:
        progress_bar = st.progress(0)
        status_text = st.empty()

        try:
            # Step 1: Save uploaded files
            status_text.text("📁 Saving uploaded files...")
            st.write(f"💾 Saving {len(st.session_state.uploaded_resumes)} files...")
            for i, uploaded_file in enumerate(st.session_state.uploaded_resumes):
                file_path = os.path.join(temp_dir, uploaded_file.name)
                with open(file_path, "wb") as f:
                    f.write(uploaded_file.getvalue())
                progress_bar.progress((i + 1) / len(st.session_state.uploaded_resumes) * 0.2)
                st.write(f"✅ Saved: {uploaded_file.name}")

            # Step 2: Parse resumes
            status_text.text("📄 Parsing resumes...")
            st.write("🔍 Starting resume parsing...")
            resumes = parse_resumes(temp_dir)
            st.write(f"✅ Successfully parsed {len(resumes)} resumes")

            # Show parsing results
            successful_parses = [r for r in resumes if not r['text'].startswith('ERROR')]
            failed_parses = [r for r in resumes if r['text'].startswith('ERROR')]

            if failed_parses:
                st.warning(f"⚠️ {len(failed_parses)} PDFs had parsing issues but will still be processed:")
                for failed in failed_parses:
                    st.write(f"   - {failed['filename']}")

            progress_bar.progress(0.3)

            # Step 3: Prefilter
            status_text.text("🔍 Prefiltering with TF-IDF...")
            k_value = calculate_k_value(
                len(resumes),
                st.session_state.prefilter_percent
            )
            st.write(f"🎯 Prefiltering to top {k_value} resumes...")
            shortlisted = prefilter_resumes(resumes, st.session_state.jd_text, top_k=k_value)
            st.write(f"✅ Shortlisted {len(shortlisted)} resumes for LLM scoring")
            progress_bar.progress(0.4)

            # Step 4: Parse rubric (save rubric temporarily and set path)
            status_text.text("📊 Parsing rubric...")
            st.write("📊 Parsing scoring rubric with LLM...")
            rubric_path = os.path.join(temp_dir, "rubric.txt")
            with open(rubric_path, "w") as f:
                f.write(st.session_state.rubric_text)
            os.environ["RUBRIC_PATH"] = rubric_path
            st.write("✅ Rubric parsed successfully")
            progress_bar.progress(0.5)

            # Step 5: Score with LLM
            status_text.text("🤖 Scoring with LLM...")
            st.write("🤖 Starting LLM scoring (this may take a few minutes)...")
            results = []
            for i, resume in enumerate(shortlisted):
                st.write(f"   🔄 Scoring: {resume['filename']} ({i + 1}/{len(shortlisted)})")
                scored = score_with_llm(resume, st.session_state.jd_text)
                results.append(scored)
                progress = 0.5 + (i + 1) / len(shortlisted) * 0.4
                progress_bar.progress(progress)
                status_text.text(f"🤖 Scoring with LLM... ({i + 1}/{len(shortlisted)})")
                st.write(f"   ✅ Completed: {resume['filename']}")

            # Step 6: Rank results
            status_text.text("📈 Ranking results...")
            st.write("📈 Ranking and aggregating results...")
            ranked_results = aggregate_and_rank(results)
            st.write(f"✅ Final ranking complete! {len(ranked_results)} resumes scored.")
            progress_bar.progress(1.0)

            # Store results
            st.session_state.results = ranked_results
            status_text.text("✅ Processing complete!")

            # Move to results step
            time.sleep(2)
            st.session_state.step = 4
            st.rerun()

        except Exception as e:
            st.error(f"❌ Error during processing: {str(e)}")
            st.write("🔍 **Debug Information:**")
            st.write(f"Error type: {type(e).__name__}")
            st.write(f"Error details: {str(e)}")
            if "PDF" in str(e) or "startxref" in str(e):
                st.write("💡 **Suggestion**: This looks like a PDF parsing error. Some PDFs may be corrupted or have unusual formatting.")
            status_text.text("❌ Processing failed")
            st.stop()