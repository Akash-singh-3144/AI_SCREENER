import streamlit as st
import pandas as pd
import os
from parser import extract_text
from utils import analyze_resume, get_gemini_api_key

st.set_page_config(page_title="AI Resume Screener", page_icon="📄", layout="wide")

# Hide Streamlit Default UI
hide_st_style = """
<style>
#MainMenu {visibility: hidden;}
footer {visibility: hidden;}
header {visibility: hidden;}
.stAppDeployButton {display:none;}
[data-testid="stAppDeployButton"] {display: none;}
</style>
"""
st.markdown(hide_st_style, unsafe_allow_html=True)

st.title("📄 AI Resume Screening System")
st.markdown("Upload a Job Description and multiple Resumes to automatically rank candidates based on fit.")

api_key = get_gemini_api_key()
if not api_key:
    st.warning("⚠️ Please provide your Gemini API key in the .env file to proceed.")

# Main Layout
col1, col2 = st.columns(2)

with col1:
    st.subheader("1. Job Description")
    jd_text_input = st.text_area("Paste JD here", height=200, key="jd")

with col2:
    st.subheader("2. Upload Resumes")
    resume_files = st.file_uploader("Upload Resumes (.txt, .pdf, .docx)", type=["txt", "pdf", "docx"], accept_multiple_files=True, key="resumes")

if st.button("🚀 Run Screening", type="primary"):
    if not api_key:
        st.error("Gemini API Key is missing. Please add it to your .env file.")
    elif not jd_text_input.strip():
        st.error("Please enter a Job Description.")
    elif not resume_files:
        st.error("Please upload at least one Resume.")
    else:
        with st.spinner("Analyzing candidates..."):
            jd_text = jd_text_input.strip()
            
            results = []
            
            # Progress bar
            progress_bar = st.progress(0)
            total_files = len(resume_files)
            
            for i, resume_file in enumerate(resume_files):
                resume_text = extract_text(resume_file, resume_file.name)
                
                if not resume_text.strip():
                    results.append({
                        "Name": resume_file.name,
                        "Score": 0,
                        "Strengths": "Could not extract text",
                        "Gaps": "",
                        "Recommendation": "Not Fit"
                    })
                    continue
                    
                analysis = analyze_resume(jd_text, resume_text, api_key)
                
                # Format lists as bullet points for the dataframe
                strengths_str = "\n".join([f"• {s}" for s in analysis.get("strengths", [])])
                gaps_str = "\n".join([f"• {g}" for g in analysis.get("gaps", [])])
                
                results.append({
                    "Name": resume_file.name,
                    "Score": analysis.get("score", 0),
                    "Strengths": strengths_str,
                    "Gaps": gaps_str,
                    "Recommendation": analysis.get("recommendation", "Not Fit")
                })
                
                progress_bar.progress((i + 1) / total_files)
                
            st.success("Analysis Complete!")
            
            # Display Results
            df = pd.DataFrame(results)
            df = df.sort_values(by="Score", ascending=False).reset_index(drop=True)
            
            st.subheader("📊 Screening Results")
            st.dataframe(
                df,
                column_config={
                    "Score": st.column_config.ProgressColumn("Match Score", help="0-100", format="%d", min_value=0, max_value=100),
                },
                use_container_width=True,
                hide_index=True
            )
            
            # CSV Download
            csv = df.to_csv(index=False).encode('utf-8-sig')
            st.download_button(
                label="📥 Download Results as CSV",
                data=csv,
                file_name='resume_screening_results.csv',
                mime='text/csv',
            )
