def aggregate_and_rank(results, *, use_total=True):
    """
    Aggregate -> final_score; sort; add rank. Keeps all fields intact.
    - If use_total=True (default), use 'total_score' from LLM scoring.
    - Fallback to 'prefilter_score' when total_score is missing.
    """
    ranked = []
    for r in results:
        if use_total and isinstance(r.get("total_score"), (int, float)):
            final = float(r["total_score"])
        else:
            final = float(r.get("prefilter_score", 0.0))
        r["final_score"] = final
        ranked.append(r)

    ranked.sort(key=lambda x: x["final_score"], reverse=True)
    for i, r in enumerate(ranked, 1):
        r["rank"] = i
    return ranked
