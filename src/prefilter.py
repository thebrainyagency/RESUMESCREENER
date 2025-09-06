# src/prefilter.py
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import numpy as np

def prefilter_resumes(resumes, jd_text, top_k=100):
    """
    Prefilter resumes using TF-IDF similarity against the job description.
    
    Args:
        resumes (list of dict): [{"filename": str, "text": str}, ...]
        jd_text (str): Job description text
        top_k (int): Number of resumes to shortlist

    Returns:
        list of dict: Shortlisted resumes with added prefilter_score
    """
    texts = [jd_text] + [r["text"] for r in resumes]
    vectorizer = TfidfVectorizer(stop_words="english")
    tfidf = vectorizer.fit_transform(texts)

    # First vector is JD, rest are resumes
    jd_vec = tfidf[0:1]
    resume_vecs = tfidf[1:]
    sims = cosine_similarity(jd_vec, resume_vecs).flatten()

    # Attach scores
    for i, r in enumerate(resumes):
        r["prefilter_score"] = float(sims[i])

    # Sort by score
    ranked = sorted(resumes, key=lambda x: x["prefilter_score"], reverse=True)

    return ranked[:top_k]
