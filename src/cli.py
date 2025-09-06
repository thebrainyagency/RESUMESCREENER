import argparse, os, json
import pandas as pd
from tqdm import tqdm

from src.parser import parse_resumes
from src.prefilter import prefilter_resumes
from src.scorer import score_with_llm
from src.ranker import aggregate_and_rank
from src.utils import sha256_text

def main():
    ap = argparse.ArgumentParser(description="Resume Screener (incremental)")
    ap.add_argument("--resumes", required=True, help="Folder with resumes")
    ap.add_argument("--jd", required=True, help="Path to job description .txt")
    ap.add_argument("--out", default="./out", help="Output folder")
    ap.add_argument("--k", type=int, default=100, help="Shortlist size for LLM")
    ap.add_argument("--force-llm", action="store_true",
                    help="(No-op in Option B) Scorer handles its own cache")
    args = ap.parse_args()

    os.makedirs(args.out, exist_ok=True)

    # 1) Parse resumes (compute res_sha)
    resumes = parse_resumes(args.resumes)

    # 2) Load JD + JD hash (JD hash is informational now)
    with open(args.jd, "r", encoding="utf-8") as f:
        jd_text = f.read()
    jd_sha = sha256_text(jd_text)[:16]

    # 3) Prefilter on ALL parsed resumes, then shortlist
    shortlisted = prefilter_resumes(resumes, jd_text, top_k=args.k)

    # 4) LLM scoring — always call; scorer will return cached fast if present
    results = []
    for res in tqdm(shortlisted, desc="LLM scoring"):
        scored = score_with_llm(res, jd_text, out_root=args.out)
        results.append(scored)

    # 5) Write JSONL
    jsonl_path = os.path.join(args.out, "details.jsonl")
    with open(jsonl_path, "w", encoding="utf-8") as f:
        for r in results:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")

    # 6) Final aggregation + ranking
    ranked = aggregate_and_rank(results)
    df = pd.DataFrame(ranked)
    csv_path = os.path.join(args.out, "results.csv")
    df.to_csv(csv_path, index=False)

    print(f"Done.\n- Saved details: {jsonl_path}\n- Saved ranked CSV: {csv_path}\n- Scored (incl. cache hits): {len(results)}")

if __name__ == "__main__":
    main()
