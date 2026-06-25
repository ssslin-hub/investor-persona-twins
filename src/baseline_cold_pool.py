"""No-persona cold-pool baseline on 2026-Q1 holdout (B4 evaluator).

Pipeline:
  1. Read `data_auto/test.json`; strip `[Q&A SO FAR]` from management context.
  2. For each model in MODELS:
       a. Generate a single pool of EXACTLY 12 unbranded analyst questions
          (no analyst name, no persona) via `prompts/baseline_cold_pool.md`.
       b. Run the B4 set-level evaluator (`prompts/evaluator_b4.md`) once: it
          returns the bidirectional coverage / precision / per-pair scores
          for the full pool-vs-actuals matrix in one shot.
       c. Compute sentence-BLEU-2 and BLEU-4 of each actual against the pool
          (auxiliary literal-similarity metric).
  3. Write artifacts under `data_baseline/{model_slug}/...` and render
     `reports/baseline_cold_pool_2026q1.md`.

Naming convention: B4 (set-level) is the right framework here because our
predictions have no analyst identity — we cannot run a B2-style per-analyst
1x1 matching.
"""

from __future__ import annotations

import json
import math
import os
import random
import re
import sys
from collections import Counter
from typing import Any

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, HERE)

from llm_client import call_llm, parse_json_strict  # noqa: E402
from run_pipeline import build_judge_prompt  # noqa: E402

PROMPTS = os.path.join(ROOT, "prompts")
DATA_AUTO = os.path.join(ROOT, "data_auto")
TEST_PATH = os.path.join(DATA_AUTO, "test.json")
POOL_PROMPT = os.path.join(PROMPTS, "baseline_cold_pool.md")
POOL_PROMPT_K110 = os.path.join(PROMPTS, "baseline_cold_pool_k110.md")
EVAL_PROMPT = os.path.join(PROMPTS, "evaluator_b4.md")
JUDGE_PROMPT = os.path.join(PROMPTS, "judge_match.md")
B2_PROMPT = os.path.join(PROMPTS, "evaluator_b2.md")
OUT_BASE = os.path.join(ROOT, "data_baseline")
REPORT_PATH = os.path.join(ROOT, "reports", "baseline_cold_pool_2026q1.md")

# V1 judge_match for the auxiliary exact/partial/miss hit-rate axis.
JUDGE_MODEL = "gpt-5-mini"

# V1 returning subset = 9 analysts (cold-start excluded) → for apples-to-apples
# vs auto_discovery TEST hit = 0.600.
TEST_RETURNING = {
    "matthew boss", "steven wieczynski", "brandt montour", "james hardiman",
    "lizzie dove", "robin farley", "vince ciepiel", "sharon zackfia",
    "andrew didora",
}

# Models for the GENERATOR. Evaluator is fixed (see EVAL_MODEL) so the rubric
# is applied identically across models.
MODELS = [
    ("gpt-5-mini", "gpt-5-mini"),
    ("gpt-5", "gpt-5"),
]
EVAL_MODEL = "gpt-5"  # B4 evaluator — fixed to the stronger model so the
                      # judging axis is held constant when comparing
                      # generators.

POOL_SIZE = 12

# ------------------------------------------------------------------------
# Vendored BLEU (modified-precision + smoothing.method1) — no nltk dep.
# ------------------------------------------------------------------------


def _tokens(text: str) -> list[str]:
    return re.findall(r"[A-Za-z0-9']+", text.lower())


def _ngrams(tokens: list[str], n: int) -> Counter:
    return Counter(tuple(tokens[i:i + n]) for i in range(len(tokens) - n + 1))


def _modified_precision(hyp_tokens: list[str], refs_tokens: list[list[str]], n: int) -> tuple[int, int]:
    hyp_ng = _ngrams(hyp_tokens, n)
    if not hyp_ng:
        return 0, 0
    max_ref: Counter = Counter()
    for rt in refs_tokens:
        rn = _ngrams(rt, n)
        for ng, cnt in rn.items():
            if cnt > max_ref[ng]:
                max_ref[ng] = cnt
    clipped = 0
    total = 0
    for ng, cnt in hyp_ng.items():
        clipped += min(cnt, max_ref.get(ng, 0))
        total += cnt
    return clipped, total


def _brevity_penalty(hyp_len: int, refs_lens: list[int]) -> float:
    if hyp_len == 0:
        return 0.0
    closest = min(refs_lens, key=lambda r: (abs(r - hyp_len), r))
    if hyp_len > closest:
        return 1.0
    return math.exp(1.0 - closest / hyp_len)


def sentence_bleu(hyp: str, refs: list[str], max_n: int) -> float:
    hyp_tokens = _tokens(hyp)
    refs_tokens = [_tokens(r) for r in refs if r]
    if not hyp_tokens or not refs_tokens:
        return 0.0
    log_precisions: list[float] = []
    for n in range(1, max_n + 1):
        clipped, total = _modified_precision(hyp_tokens, refs_tokens, n)
        if total == 0:
            return 0.0
        if clipped == 0 and n >= 2:
            clipped, total = 1, total + 1
        if clipped == 0:
            return 0.0
        log_precisions.append(math.log(clipped / total))
    weight = 1.0 / max_n
    geo = math.exp(sum(weight * lp for lp in log_precisions))
    bp = _brevity_penalty(len(hyp_tokens), [len(r) for r in refs_tokens])
    return bp * geo


# ------------------------------------------------------------------------
# Anti-leakage helpers.
# ------------------------------------------------------------------------


def _all_4grams(text: str) -> set[tuple[str, ...]]:
    toks = _tokens(text)
    return {tuple(toks[i:i + 4]) for i in range(len(toks) - 3)}


def _test_actual_4grams(test: dict) -> set[tuple[str, ...]]:
    grams: set[tuple[str, ...]] = set()
    for _name, actuals in test["per_analyst_actual_questions"].items():
        for a in actuals:
            grams |= _all_4grams(a["question"])
    return grams


# ------------------------------------------------------------------------
# Actuals flattening.
# ------------------------------------------------------------------------


def flatten_actuals(test: dict) -> list[dict]:
    out: list[dict] = []
    i = 1
    for name in sorted(test["per_analyst_actual_questions"].keys()):
        for a in test["per_analyst_actual_questions"][name]:
            out.append({
                "actual_id": f"a{i:02d}",
                "analyst": name,
                "question": a["question"],
            })
            i += 1
    return out


# ------------------------------------------------------------------------
# Pool + evaluator runners.
# ------------------------------------------------------------------------


def _slug(model: str) -> str:
    return model.replace(".", "_").replace("/", "_")


def _strip_qa(mgmt: str) -> str:
    if "[Q&A SO FAR]" in mgmt:
        mgmt = mgmt.split("[Q&A SO FAR]", 1)[0].rstrip()
    return mgmt


def generate_pool(model: str, mgmt: str, out_dir: str) -> dict:
    tpl = open(POOL_PROMPT).read()
    prompt = tpl.replace("{management_presentation}", mgmt)
    log_path = os.path.join(out_dir, "logs", "pool_prompt.txt")
    raw = call_llm(
        prompt, model=model, expect_json=True,
        temperature=0.0, log_to=log_path,
    )
    pool = parse_json_strict(raw)
    qs = pool.get("predicted_questions", [])
    # normalise candidate_id
    for i, q in enumerate(qs):
        if not q.get("candidate_id"):
            q["candidate_id"] = f"p{i+1:02d}"
    pool["predicted_questions"] = qs
    if len(qs) != POOL_SIZE:
        print(f"  ! WARN: pool for {model} returned {len(qs)} (expected {POOL_SIZE}); proceeding")
    with open(os.path.join(out_dir, "pool.json"), "w") as f:
        json.dump({"model": model, "pool": pool, "raw_response": raw}, f, indent=2)
    return pool


def run_b4_evaluator(pool: dict, actuals: list[dict], out_dir: str) -> dict:
    tpl = open(EVAL_PROMPT).read()
    pred_block = json.dumps(pool["predicted_questions"], indent=2)
    actual_block = json.dumps([{"actual_id": a["actual_id"],
                                "analyst": a["analyst"],
                                "question": a["question"]} for a in actuals], indent=2)
    prompt = tpl.replace("{predicted_block}", pred_block).replace("{actual_block}", actual_block)
    log_path = os.path.join(out_dir, "logs", "evaluator_prompt.txt")
    raw = call_llm(
        prompt, model=EVAL_MODEL, expect_json=True,
        temperature=0.0, log_to=log_path,
    )
    verdict = parse_json_strict(raw)
    with open(os.path.join(out_dir, "set_evaluation.json"), "w") as f:
        json.dump(verdict, f, indent=2)
    return verdict


def _recompute_set_metrics(verdict: dict) -> dict:
    """Defensive recompute: trust per-row 0-4 scores but recompute set-level
    aggregates locally so we never depend on the LLM's arithmetic."""
    cov = verdict.get("actual_coverage", [])
    prec = verdict.get("predicted_precision", [])
    cov_scores = [r.get("match_score_0_to_4", 0) for r in cov]
    prec_scores = [r.get("match_score_0_to_4", 0) for r in prec]
    n_act = len(cov)
    n_pred = len(prec)
    cov_count = sum(1 for s in cov_scores if s >= 3)
    use_count = sum(1 for s in prec_scores if s >= 3)
    return {
        "coverage_count": cov_count,
        "coverage_rate": cov_count / n_act if n_act else 0.0,
        "useful_prediction_count": use_count,
        "precision_rate": use_count / n_pred if n_pred else 0.0,
        "average_actual_best_score": (sum(cov_scores) / n_act) if n_act else 0.0,
        "average_predicted_best_score": (sum(prec_scores) / n_pred) if n_pred else 0.0,
    }


def run_hit_rate_judge(pool: dict, test: dict, out_dir: str) -> dict:
    """Reuse the V1 judge_match.md (exact / partial / miss) per analyst, with
    the cold pool as the predicted set. This gives the V1-style hit rate
    directly comparable to auto_discovery TEST = 0.600 and V0 baseline 0.500.
    """
    judge_tpl = open(JUDGE_PROMPT).read()
    actuals_by_name = test["per_analyst_actual_questions"]
    pool_qs = pool["predicted_questions"]
    os.makedirs(os.path.join(out_dir, "judgments"), exist_ok=True)
    per_analyst: dict[str, dict] = {}
    tot_actual = tot_exact = tot_partial = tot_miss = 0
    for analyst in sorted(actuals_by_name.keys()):
        actuals = actuals_by_name[analyst]
        prompt = build_judge_prompt(judge_tpl, analyst, pool_qs, actuals)
        log_path = os.path.join(out_dir, "logs", f"judge_{analyst.replace(' ', '_')}.txt")
        raw = call_llm(prompt, model=JUDGE_MODEL, expect_json=True,
                       temperature=0.0, log_to=log_path)
        verdict = parse_json_strict(raw)
        s = verdict.get("summary", {})
        n_actual = int(s.get("n_actual", len(actuals)))
        n_exact = int(s.get("n_exact", 0))
        n_partial = int(s.get("n_partial", 0))
        n_miss = int(s.get("n_miss", n_actual - n_exact - n_partial))
        hit = (n_exact + n_partial) / n_actual if n_actual else 0.0
        per_analyst[analyst] = {
            "n_actual": n_actual, "n_exact": n_exact,
            "n_partial": n_partial, "n_miss": n_miss, "hit": hit,
            "in_returning_subset": analyst in TEST_RETURNING,
        }
        tot_actual += n_actual
        tot_exact += n_exact
        tot_partial += n_partial
        tot_miss += n_miss
        with open(os.path.join(out_dir, "judgments", f"{analyst.replace(' ', '_')}.json"), "w") as f:
            json.dump(verdict, f, indent=2)

    all_hit = (tot_exact + tot_partial) / tot_actual if tot_actual else 0.0

    ret = {k: v for k, v in per_analyst.items() if v["in_returning_subset"]}
    r_actual = sum(v["n_actual"] for v in ret.values())
    r_exact = sum(v["n_exact"] for v in ret.values())
    r_partial = sum(v["n_partial"] for v in ret.values())
    r_miss = sum(v["n_miss"] for v in ret.values())
    r_hit = (r_exact + r_partial) / r_actual if r_actual else 0.0

    return {
        "per_analyst": per_analyst,
        "all_analysts": {
            "n_analysts": len(per_analyst),
            "n_actual": tot_actual, "n_exact": tot_exact,
            "n_partial": tot_partial, "n_miss": tot_miss, "hit": all_hit,
        },
        "returning_subset": {
            "n_analysts": len(ret),
            "n_actual": r_actual, "n_exact": r_exact,
            "n_partial": r_partial, "n_miss": r_miss, "hit": r_hit,
        },
    }


def run_b2_evaluator(pool: dict, test: dict, out_dir: str) -> dict:
    """V2 B2 per-analyst evaluator: 0-4 score + 4-axis breakdown, one score
    per analyst. Same cold pool is reused as each analyst's predicted set
    (per the user's assumption: 'each analyst answered 12 questions').
    """
    tpl = open(B2_PROMPT).read()
    actuals_by_name = test["per_analyst_actual_questions"]
    pool_qs = pool["predicted_questions"]
    pred_block = json.dumps(
        [{"candidate_id": q.get("candidate_id", f"p{i+1:02d}"),
          "topic_label": q.get("topic_label", "?"),
          "question_text": q.get("question_text", "")}
         for i, q in enumerate(pool_qs)],
        indent=2,
    )
    os.makedirs(os.path.join(out_dir, "b2"), exist_ok=True)
    per_analyst: dict[str, dict] = {}
    for analyst in sorted(actuals_by_name.keys()):
        actuals = actuals_by_name[analyst]
        actual_block = json.dumps(
            [{"index": i, "question": a["question"]} for i, a in enumerate(actuals)],
            indent=2,
        )
        prompt = (tpl.replace("{analyst_name}", analyst)
                     .replace("{predicted_block}", pred_block)
                     .replace("{actual_block}", actual_block))
        log_path = os.path.join(out_dir, "logs", f"b2_{analyst.replace(' ', '_')}.txt")
        raw = call_llm(prompt, model=EVAL_MODEL, expect_json=True,
                       temperature=0.0, log_to=log_path)
        verdict = parse_json_strict(raw)
        with open(os.path.join(out_dir, "b2", f"{analyst.replace(' ', '_')}.json"), "w") as f:
            json.dump(verdict, f, indent=2)
        per_analyst[analyst] = verdict

    scores = [int(v.get("match_score_0_to_4", 0)) for v in per_analyst.values()]
    binary = [bool(v.get("binary_match", s >= 3)) for v, s in zip(per_analyst.values(), scores)]
    n = len(per_analyst)
    return {
        "per_analyst": per_analyst,
        "n_analysts": n,
        "binary_match_count": sum(1 for b in binary if b),
        "binary_match_rate": sum(1 for b in binary if b) / n if n else 0.0,
        "average_match_score": sum(scores) / n if n else 0.0,
    }


def compute_bleu(pool: dict, actuals: list[dict]) -> dict:
    pool_texts = [q.get("question_text", "") for q in pool["predicted_questions"]]
    rows: list[dict] = []
    for a in actuals:
        b2 = sentence_bleu(a["question"], pool_texts, max_n=2)
        b4 = sentence_bleu(a["question"], pool_texts, max_n=4)
        rows.append({"actual_id": a["actual_id"], "analyst": a["analyst"],
                     "B2": b2, "B4": b4})
    mean_b2 = sum(r["B2"] for r in rows) / len(rows) if rows else 0.0
    mean_b4 = sum(r["B4"] for r in rows) / len(rows) if rows else 0.0
    return {"per_actual": rows, "mean_B2": mean_b2, "mean_B4": mean_b4}


# ============================================================================
# K=110 + sample-of-10 experiment
# ============================================================================


def _jaccard(a: list[str], b: list[str]) -> float:
    sa, sb = set(a), set(b)
    if not sa and not sb:
        return 1.0
    return len(sa & sb) / max(1, len(sa | sb))


def _dedup_pool(qs: list[dict], jaccard_thresh: float = 0.85) -> tuple[list[dict], list[dict]]:
    """Drop exact text duplicates + near-duplicates (Jaccard >= threshold on
    lowercased word-tokens). Returns (kept, dropped)."""
    kept: list[dict] = []
    kept_tokens: list[list[str]] = []
    seen_text: set[str] = set()
    dropped: list[dict] = []
    for q in qs:
        text = q.get("question_text", "").strip()
        key = text.lower()
        if not text or key in seen_text:
            dropped.append({**q, "drop_reason": "exact-duplicate"})
            continue
        toks = _tokens(text)
        near = False
        for kt in kept_tokens:
            if _jaccard(toks, kt) >= jaccard_thresh:
                near = True
                break
        if near:
            dropped.append({**q, "drop_reason": f"near-duplicate-jaccard>={jaccard_thresh}"})
            continue
        kept.append(q)
        kept_tokens.append(toks)
        seen_text.add(key)
    return kept, dropped


def generate_pool_n(model: str, mgmt: str, K: int, temperature: float,
                    prompt_path: str, out_dir: str) -> dict:
    tpl = open(prompt_path).read()
    prompt = tpl.replace("{management_presentation}", mgmt)
    log_path = os.path.join(out_dir, "logs", "pool_prompt.txt")
    raw = call_llm(
        prompt, model=model, expect_json=True,
        temperature=temperature, log_to=log_path,
    )
    pool = parse_json_strict(raw)
    raw_qs = pool.get("predicted_questions", [])
    kept, dropped = _dedup_pool(raw_qs)
    K_eff = len(kept)
    for i, q in enumerate(kept):
        q["candidate_id"] = f"p{i+1:03d}"
    pool_record = {
        "model": model,
        "K_requested": K,
        "K_returned": len(raw_qs),
        "K_eff_after_dedup": K_eff,
        "n_dropped": len(dropped),
        "temperature": temperature,
        "pool": {"predicted_questions": kept},
        "dropped": dropped,
        "raw_response": raw,
    }
    with open(os.path.join(out_dir, "pool.json"), "w") as f:
        json.dump(pool_record, f, indent=2)
    print(f"  pool: requested {K}, returned {len(raw_qs)}, kept {K_eff} after dedup (dropped {len(dropped)})")
    if K_eff < 60:
        raise RuntimeError(f"Pool too small after dedup: K_eff={K_eff} < 60")
    return pool_record


def run_b4_on(predicted_qs: list[dict], actuals: list[dict],
              out_dir: str, tag: str) -> dict:
    tpl = open(EVAL_PROMPT).read()
    pred_block = json.dumps(predicted_qs, indent=2)
    actual_block = json.dumps([{"actual_id": a["actual_id"],
                                "analyst": a["analyst"],
                                "question": a["question"]} for a in actuals], indent=2)
    prompt = tpl.replace("{predicted_block}", pred_block).replace("{actual_block}", actual_block)
    log_path = os.path.join(out_dir, "logs", f"b4_{tag}_prompt.txt")
    raw = call_llm(prompt, model=EVAL_MODEL, expect_json=True,
                   temperature=0.0, log_to=log_path)
    verdict = parse_json_strict(raw)
    with open(os.path.join(out_dir, f"b4_{tag}.json"), "w") as f:
        json.dump(verdict, f, indent=2)
    return verdict


def run_b2_subset(per_analyst_subset: dict[str, list[dict]],
                  test: dict, out_dir: str) -> dict:
    """B2 evaluator where each analyst has their OWN predicted subset."""
    tpl = open(B2_PROMPT).read()
    actuals_by_name = test["per_analyst_actual_questions"]
    os.makedirs(os.path.join(out_dir, "b2"), exist_ok=True)
    per_analyst: dict[str, dict] = {}
    for analyst in sorted(actuals_by_name.keys()):
        actuals = actuals_by_name[analyst]
        subset = per_analyst_subset[analyst]
        pred_block = json.dumps(subset, indent=2)
        actual_block = json.dumps(
            [{"index": i, "question": a["question"]} for i, a in enumerate(actuals)],
            indent=2,
        )
        prompt = (tpl.replace("{analyst_name}", analyst)
                     .replace("{predicted_block}", pred_block)
                     .replace("{actual_block}", actual_block))
        log_path = os.path.join(out_dir, "logs", f"b2_{analyst.replace(' ', '_')}.txt")
        raw = call_llm(prompt, model=EVAL_MODEL, expect_json=True,
                       temperature=0.0, log_to=log_path)
        verdict = parse_json_strict(raw)
        with open(os.path.join(out_dir, "b2", f"{analyst.replace(' ', '_')}.json"), "w") as f:
            json.dump(verdict, f, indent=2)
        per_analyst[analyst] = verdict
    scores = [int(v.get("match_score_0_to_4", 0)) for v in per_analyst.values()]
    binary = [bool(v.get("binary_match", s >= 3)) for v, s in zip(per_analyst.values(), scores)]
    n = len(per_analyst)
    return {
        "per_analyst": per_analyst,
        "n_analysts": n,
        "binary_match_count": sum(1 for b in binary if b),
        "binary_match_rate": sum(1 for b in binary if b) / n if n else 0.0,
        "average_match_score": sum(scores) / n if n else 0.0,
    }


def run_hit_subset(per_analyst_subset: dict[str, list[dict]],
                   test: dict, out_dir: str) -> dict:
    """V1 judge_match where each analyst has their OWN predicted subset."""
    judge_tpl = open(JUDGE_PROMPT).read()
    actuals_by_name = test["per_analyst_actual_questions"]
    os.makedirs(os.path.join(out_dir, "judgments"), exist_ok=True)
    per_analyst: dict[str, dict] = {}
    tot_actual = tot_exact = tot_partial = tot_miss = 0
    for analyst in sorted(actuals_by_name.keys()):
        actuals = actuals_by_name[analyst]
        subset = per_analyst_subset[analyst]
        prompt = build_judge_prompt(judge_tpl, analyst, subset, actuals)
        log_path = os.path.join(out_dir, "logs", f"judge_{analyst.replace(' ', '_')}.txt")
        raw = call_llm(prompt, model=JUDGE_MODEL, expect_json=True,
                       temperature=0.0, log_to=log_path)
        verdict = parse_json_strict(raw)
        s = verdict.get("summary", {})
        n_actual = int(s.get("n_actual", len(actuals)))
        n_exact = int(s.get("n_exact", 0))
        n_partial = int(s.get("n_partial", 0))
        n_miss = int(s.get("n_miss", n_actual - n_exact - n_partial))
        hit = (n_exact + n_partial) / n_actual if n_actual else 0.0
        per_analyst[analyst] = {
            "n_actual": n_actual, "n_exact": n_exact,
            "n_partial": n_partial, "n_miss": n_miss, "hit": hit,
            "in_returning_subset": analyst in TEST_RETURNING,
        }
        tot_actual += n_actual
        tot_exact += n_exact
        tot_partial += n_partial
        tot_miss += n_miss
        with open(os.path.join(out_dir, "judgments", f"{analyst.replace(' ', '_')}.json"), "w") as f:
            json.dump(verdict, f, indent=2)
    all_hit = (tot_exact + tot_partial) / tot_actual if tot_actual else 0.0
    ret = {k: v for k, v in per_analyst.items() if v["in_returning_subset"]}
    r_actual = sum(v["n_actual"] for v in ret.values())
    r_exact = sum(v["n_exact"] for v in ret.values())
    r_partial = sum(v["n_partial"] for v in ret.values())
    r_miss = sum(v["n_miss"] for v in ret.values())
    r_hit = (r_exact + r_partial) / r_actual if r_actual else 0.0
    return {
        "per_analyst": per_analyst,
        "all_analysts": {"n_analysts": len(per_analyst),
                         "n_actual": tot_actual, "n_exact": tot_exact,
                         "n_partial": tot_partial, "n_miss": tot_miss, "hit": all_hit},
        "returning_subset": {"n_analysts": len(ret),
                             "n_actual": r_actual, "n_exact": r_exact,
                             "n_partial": r_partial, "n_miss": r_miss, "hit": r_hit},
    }


def run_k110_sample_experiment(test: dict, mgmt: str, actuals: list[dict],
                               K: int = 110, k_sample: int = 10,
                               seed: int = 42,
                               generator_model: str = "gpt-5-mini") -> dict:
    out_dir = os.path.join(OUT_BASE, f"{_slug(generator_model)}_k{K}")
    os.makedirs(os.path.join(out_dir, "logs"), exist_ok=True)
    print(f"\n=== K={K} sample-{k_sample} | Generator: {generator_model} t=1.0 | Evaluator: {EVAL_MODEL} | seed={seed} ===")

    pool_record = generate_pool_n(generator_model, mgmt, K, 1.0,
                                  POOL_PROMPT_K110, out_dir)
    pool_qs = pool_record["pool"]["predicted_questions"]
    K_eff = len(pool_qs)

    # Sampling
    rng = random.Random(seed)
    per_analyst_idx: dict[str, list[int]] = {}
    for analyst in sorted(test["per_analyst_actual_questions"].keys()):
        per_analyst_idx[analyst] = rng.sample(range(K_eff), k_sample)
    b4_slate_idx = rng.sample(range(K_eff), k_sample)

    per_analyst_subset = {
        analyst: [pool_qs[i] for i in idxs]
        for analyst, idxs in per_analyst_idx.items()
    }
    b4_slate = [pool_qs[i] for i in b4_slate_idx]
    with open(os.path.join(out_dir, "samples.json"), "w") as f:
        json.dump({
            "seed": seed,
            "k_sample": k_sample,
            "K_eff": K_eff,
            "per_analyst": {a: [pool_qs[i]["candidate_id"] for i in idxs]
                             for a, idxs in per_analyst_idx.items()},
            "b4_slate": [pool_qs[i]["candidate_id"] for i in b4_slate_idx],
        }, f, indent=2)

    # Anti-leakage (on full pool)
    test_grams = _test_actual_4grams(test)
    pool_grams: set[tuple[str, ...]] = set()
    for q in pool_qs:
        pool_grams |= _all_4grams(q.get("question_text", ""))
    leaked = pool_grams & test_grams
    leak = {"n_leaked_4grams": len(leaked),
            "examples": [" ".join(g) for g in list(leaked)[:5]]}

    # V1 hit + B2 (per-analyst sampled-10)
    hit_rate = run_hit_subset(per_analyst_subset, test, out_dir)
    b2 = run_b2_subset(per_analyst_subset, test, out_dir)

    # B4 sampled-slate
    b4_sampled_verdict = run_b4_on(b4_slate, actuals, out_dir, tag="sampled")
    b4_sampled_metrics = _recompute_set_metrics(b4_sampled_verdict)

    # B4 oracle (full pool)
    b4_oracle_verdict = run_b4_on(pool_qs, actuals, out_dir, tag="oracle")
    b4_oracle_metrics = _recompute_set_metrics(b4_oracle_verdict)

    # BLEU
    bleu_full = compute_bleu({"predicted_questions": pool_qs}, actuals)
    bleu_slate = compute_bleu({"predicted_questions": b4_slate}, actuals)
    with open(os.path.join(out_dir, "bleu.json"), "w") as f:
        json.dump({"full_pool": bleu_full, "slate_10": bleu_slate}, f, indent=2)

    summary = {
        "experiment": f"K={K} sample-{k_sample}",
        "generator_model": generator_model,
        "evaluator_model": EVAL_MODEL,
        "judge_model": JUDGE_MODEL,
        "seed": seed,
        "K_requested": K,
        "K_eff": K_eff,
        "k_sample": k_sample,
        "actual_count": len(actuals),
        "hit_rate": hit_rate,
        "b2": b2,
        "b4_sampled": {"metrics": b4_sampled_metrics,
                       "summary": b4_sampled_verdict.get("summary", "")},
        "b4_oracle": {"metrics": b4_oracle_metrics,
                      "summary": b4_oracle_verdict.get("summary", "")},
        "bleu_full_pool": {"mean_B2": bleu_full["mean_B2"], "mean_B4": bleu_full["mean_B4"]},
        "bleu_slate_10": {"mean_B2": bleu_slate["mean_B2"], "mean_B4": bleu_slate["mean_B4"]},
        "anti_leakage": leak,
    }
    with open(os.path.join(out_dir, "summary.json"), "w") as f:
        json.dump(summary, f, indent=2)

    # Console summary
    a = hit_rate["all_analysts"]
    r = hit_rate["returning_subset"]
    print(f"  V1 hit (returning 9 ana / {r['n_actual']} actuals) = {r['hit']:.3f}  (E={r['n_exact']} P={r['n_partial']} M={r['n_miss']})")
    print(f"  V1 hit (all 11 ana / {a['n_actual']} actuals)     = {a['hit']:.3f}  (E={a['n_exact']} P={a['n_partial']} M={a['n_miss']})")
    print(f"  B2 binary_match = {b2['binary_match_count']}/{b2['n_analysts']} = {b2['binary_match_rate']:.3f}   avg = {b2['average_match_score']:.2f}/4")
    print(f"  B4 sampled-slate ({k_sample} preds): cov {b4_sampled_metrics['coverage_count']}/{len(actuals)}={b4_sampled_metrics['coverage_rate']:.3f}  prec {b4_sampled_metrics['useful_prediction_count']}/{k_sample}={b4_sampled_metrics['precision_rate']:.3f}  avg_actual_best={b4_sampled_metrics['average_actual_best_score']:.2f}  avg_pred_best={b4_sampled_metrics['average_predicted_best_score']:.2f}")
    print(f"  B4 oracle ({K_eff} preds):       cov {b4_oracle_metrics['coverage_count']}/{len(actuals)}={b4_oracle_metrics['coverage_rate']:.3f}  prec {b4_oracle_metrics['useful_prediction_count']}/{K_eff}={b4_oracle_metrics['precision_rate']:.3f}  avg_actual_best={b4_oracle_metrics['average_actual_best_score']:.2f}  avg_pred_best={b4_oracle_metrics['average_predicted_best_score']:.2f}")
    print(f"  BLEU full pool: B2={bleu_full['mean_B2']:.4f}  B4={bleu_full['mean_B4']:.4f}")
    print(f"  BLEU slate-10:  B2={bleu_slate['mean_B2']:.4f}  B4={bleu_slate['mean_B4']:.4f}")
    if leak["n_leaked_4grams"]:
        print(f"  !! leaked 4-grams: {leak['n_leaked_4grams']}  e.g. {leak['examples']}")
    return summary


def run_one_model(model_slug: str, model_id: str, test: dict, mgmt: str, actuals: list[dict]) -> dict:
    out_dir = os.path.join(OUT_BASE, _slug(model_slug))
    os.makedirs(os.path.join(out_dir, "logs"), exist_ok=True)
    print(f"\n=== Generator: {model_id}   |   Evaluator: {EVAL_MODEL} ===")

    pool = generate_pool(model_id, mgmt, out_dir)

    # Anti-leakage
    test_grams = _test_actual_4grams(test)
    pool_grams: set[tuple[str, ...]] = set()
    for q in pool["predicted_questions"]:
        pool_grams |= _all_4grams(q.get("question_text", ""))
    leaked = pool_grams & test_grams
    leak = {"n_leaked_4grams": len(leaked), "examples": [" ".join(g) for g in list(leaked)[:5]]}

    verdict = run_b4_evaluator(pool, actuals, out_dir)
    set_metrics = _recompute_set_metrics(verdict)

    hit_rate = run_hit_rate_judge(pool, test, out_dir)
    b2 = run_b2_evaluator(pool, test, out_dir)

    bleu = compute_bleu(pool, actuals)
    with open(os.path.join(out_dir, "bleu.json"), "w") as f:
        json.dump(bleu, f, indent=2)

    summary = {
        "generator_model": model_id,
        "evaluator_model": EVAL_MODEL,
        "judge_model": JUDGE_MODEL,
        "pool_size": len(pool["predicted_questions"]),
        "actual_count": len(actuals),
        "set_metrics_recomputed": set_metrics,
        "set_metrics_from_llm": verdict.get("set_metrics", {}),
        "hit_rate": hit_rate,
        "b2": b2,
        "mean_B2": bleu["mean_B2"],
        "mean_B4": bleu["mean_B4"],
        "missed_actual_themes": verdict.get("missed_actual_themes", []),
        "overpredicted_themes": verdict.get("overpredicted_themes", []),
        "anti_leakage": leak,
        "summary": verdict.get("summary", ""),
        "B4_reference_v2": {"coverage_rate": 0.667, "precision_rate": 0.667,
                            "avg_actual_best": 2.92, "avg_predicted_best": 2.50},
    }
    with open(os.path.join(out_dir, "summary.json"), "w") as f:
        json.dump(summary, f, indent=2)

    print(f"  coverage  = {set_metrics['coverage_count']}/{len(actuals)} = {set_metrics['coverage_rate']:.3f}")
    print(f"  precision = {set_metrics['useful_prediction_count']}/{len(pool['predicted_questions'])} = {set_metrics['precision_rate']:.3f}")
    print(f"  avg actual best    = {set_metrics['average_actual_best_score']:.2f} / 4")
    print(f"  avg predicted best = {set_metrics['average_predicted_best_score']:.2f} / 4")
    r = hit_rate["returning_subset"]
    a = hit_rate["all_analysts"]
    print(f"  V1 hit (returning 9 ana / {r['n_actual']} actuals) = {r['hit']:.3f}  (exact={r['n_exact']} partial={r['n_partial']} miss={r['n_miss']})")
    print(f"  V1 hit (all 11 ana / {a['n_actual']} actuals)     = {a['hit']:.3f}  (exact={a['n_exact']} partial={a['n_partial']} miss={a['n_miss']})")
    print(f"  B2 binary_match_rate = {b2['binary_match_count']}/{b2['n_analysts']} = {b2['binary_match_rate']:.3f}   avg score = {b2['average_match_score']:.2f} / 4")
    print(f"  BLEU-2 mean = {bleu['mean_B2']:.4f}   BLEU-4 mean = {bleu['mean_B4']:.4f}")
    if leak["n_leaked_4grams"]:
        print(f"  !! leaked 4-grams: {leak['n_leaked_4grams']}  e.g. {leak['examples']}")
    else:
        print("  anti-leakage: 0 4-gram overlap with TEST actuals")
    return summary


def render_report(summaries: list[dict], actuals: list[dict]) -> None:
    os.makedirs(os.path.dirname(REPORT_PATH), exist_ok=True)
    lines: list[str] = []
    lines.append("# No-Persona Cold-Pool Baseline — 2026-Q1 holdout (B4 evaluator)")
    lines.append("")
    lines.append(f"**Setup.** A single LLM call per generator produces an unbranded pool of **{POOL_SIZE} questions** from only the Q1 2026 prepared remarks (no analyst names, no persona, no history). The same 0–4 set-level evaluator rubric used by V2 `run_llm_set_pipeline.mjs` then judges the pool against the {len(actuals)} actuals in both directions:")
    lines.append("")
    lines.append("- **Coverage**: each actual → best predicted match; score ≥ 3 counts as covered.")
    lines.append("- **Precision**: each predicted question → best actual match; score ≥ 3 counts as useful.")
    lines.append("- **Average best score** (continuous) on each side.")
    lines.append("")
    lines.append(f"Generator: gpt-5-mini and gpt-5 (temperature 0). Evaluator: fixed to **{EVAL_MODEL}** so the rubric is held constant when comparing generators.")
    lines.append("")
    lines.append("BLEU-2 / BLEU-4 are smoothed sentence-BLEU (method1) with all pool questions as references — a literal-similarity sanity check, distinct from the semantic B4 metric.")
    lines.append("")
    lines.append("**Reference points.** V2 `run_llm_set_pipeline.mjs` B4 numbers on the same holdout: coverage 8/12 = 66.7 %, precision 8/12 = 66.7 %, avg actual best 2.92, avg predicted best 2.50.")
    lines.append("")

    lines.append("## Headline — V1 hit + B2 per-analyst + B4 set-level, no persona")
    lines.append("")
    lines.append("| Generator | V1 hit (all 11/12) | **B2** binary match (11 ana) | B2 avg score | B4 coverage | B4 precision | avg actual best | avg pred best | BLEU-2 | BLEU-4 |")
    lines.append("|---|---|---|---:|---|---|---:|---:|---:|---:|")
    for s in summaries:
        m = s["set_metrics_recomputed"]
        hr = s["hit_rate"]
        a = hr["all_analysts"]
        b2 = s["b2"]
        lines.append(
            f"| {s['generator_model']} "
            f"| {a['n_exact']+a['n_partial']}/{a['n_actual']} = **{a['hit']:.3f}** "
            f"| {b2['binary_match_count']}/{b2['n_analysts']} = **{b2['binary_match_rate']:.3f}** "
            f"| {b2['average_match_score']:.2f} "
            f"| {m['coverage_count']}/{s['actual_count']} = **{m['coverage_rate']:.3f}** "
            f"| {m['useful_prediction_count']}/{s['pool_size']} = **{m['precision_rate']:.3f}** "
            f"| {m['average_actual_best_score']:.2f} "
            f"| {m['average_predicted_best_score']:.2f} "
            f"| {s['mean_B2']:.4f} "
            f"| {s['mean_B4']:.4f} |"
        )
    lines.append("")
    lines.append("**Reference points** on the same 2026-Q1 holdout:")
    lines.append("- V0 baseline (per-analyst, no peer): V1 hit 0.500")
    lines.append("- V1 `auto_discovery` TEST (per-analyst persona, peer-augmented): V1 hit **0.600** (9 returning / 10 actuals)")
    lines.append("- V2 `run_llm_persona_pipeline.mjs` **B2** (per-analyst Extractor → Simulator → Evaluator, 11 analysts): binary_match_rate **3/11 = 0.273**, avg score **1.45 / 4**")
    lines.append("- V2 `run_llm_set_pipeline.mjs` **B4** (19-persona panel + selector slate of 12): coverage 0.667, precision 0.667, avg actual best 2.92, avg pred. best 2.50")
    lines.append("")

    # Rubric explanation
    lines.append("## Scoring rubrics")
    lines.append("")
    lines.append("Two complementary semantic judges are run on every (generator, pool) pair:")
    lines.append("")
    lines.append("### V1 `judge_match.md` — three-level per-analyst (the **hit rate** column)")
    lines.append("")
    lines.append("For each actual question asked by a given analyst, the judge looks at the entire pool and assigns one label, then sums per analyst:")
    lines.append("")
    lines.append("- **EXACT** — same topic, same direction of inquiry, comparable specificity (e.g. both ask about yield decomposition at the bps level).")
    lines.append("- **PARTIAL** — same topic and similar direction, but one side is broader/narrower in specificity (e.g. predicted asks generally about yield drivers; actual asks specifically about new-hardware contribution).")
    lines.append("- **MISS** — no question in the pool addresses the same substantive concern.")
    lines.append("")
    lines.append("`hit = (n_exact + n_partial) / n_actual` per analyst, then summed. This is the same judge V1 `auto_discovery` reports as `hit_rate_exact_or_partial`. Judge model: `gpt-5-mini`, temperature 0.")
    lines.append("")
    lines.append("### V2 B2 per-analyst evaluator (the **B2 binary match** column)")
    lines.append("")
    lines.append("For each analyst, the evaluator receives the cold pool (treated as the analyst's predicted set — the user's \"assume each analyst answered 12 questions\" stipulation) and that analyst's actual question(s). It returns one overall match score 0–4 plus a 4-axis alignment breakdown (topic / trigger / question form / granularity, each ∈ {none, weak, partial, strong}). `binary_match = score >= 3`.")
    lines.append("")
    lines.append("Aggregates: `binary_match_rate = n_binary_hit / 11`, `average_match_score = mean(score) / 4`.")
    lines.append("")
    lines.append("Same 0–4 rubric as B4 (see below). B2 differs from B4 only in scope: B2 fixes analyst identity, B4 ignores identity.")
    lines.append("")
    lines.append("### V2 B4 set-level rubric (the **0–4 score** used for coverage / precision)")
    lines.append("")
    lines.append("Same rubric is applied in **both directions** (each actual → best pool match; each pool item → best actual match):")
    lines.append("")
    lines.append("| score | meaning |")
    lines.append("|:-:|---|")
    lines.append("| **0** | No meaningful relation — the predicted question and the actual question are about different things entirely. |")
    lines.append("| **1** | Same broad business area only (e.g. both touch \"costs\" but one is fuel hedging and the other is labour inflation). |")
    lines.append("| **2** | Partial theme match but wrong trigger or different ask — overlapping topic, but the specific uncertainty being probed differs. |")
    lines.append("| **3** | Substantially similar question target — both questions would elicit substantially the same management answer. |")
    lines.append("| **4** | Very close substitute — the predicted question is essentially the actual question reworded; same trigger, same ask, same expected answer shape. |")
    lines.append("")
    lines.append("Aggregates:")
    lines.append("- **coverage_rate** = fraction of actuals whose best-matching pool item scores ≥ 3.")
    lines.append("- **precision_rate** = fraction of pool items whose best-matching actual scores ≥ 3.")
    lines.append("- **avg actual best** = mean over actuals of `max_pool match_score_0_to_4`.")
    lines.append("- **avg pred. best**  = mean over pool of `max_actual match_score_0_to_4`.")
    lines.append("")
    lines.append("Evaluator model: `gpt-5`, temperature 0. Held constant so that the difference between gpt-5-mini and gpt-5 in the headline isolates **generator** quality, not judge quality.")
    lines.append("")
    lines.append("### BLEU-2 / BLEU-4 (literal similarity, auxiliary)")
    lines.append("")
    lines.append("Smoothed sentence BLEU (Papineni 2002, modified n-gram precision; smoothing = NLTK `SmoothingFunction.method1`). For each actual question:")
    lines.append("")
    lines.append("- hypothesis = the actual question text")
    lines.append("- references = all 12 pool questions")
    lines.append("- BLEU-2 truncates at n = 2 (1-gram + 2-gram geometric mean × brevity penalty)")
    lines.append("- BLEU-4 truncates at n = 4 (up through 4-gram)")
    lines.append("")
    lines.append("Then averaged across actuals. These are **string-overlap** metrics, not semantic; they answer \"how close is the predicted *wording* to the actual *wording*\", which is intentionally separate from the 0–4 semantic axis. They will always be low when the pool generates the analyst's *concern* but not the analyst's *phrasing* — exactly the regime we are in.")
    lines.append("")

    # Per-analyst V1 hit + B2 breakdown
    for s in summaries:
        lines.append(f"## {s['generator_model']} — per-analyst V1 judge & B2 evaluator")
        lines.append("")
        lines.append("| Analyst | V1 (exact/partial/miss) | V1 hit | **B2 score 0-4** | B2 binary | topic | trigger | form | gran |")
        lines.append("|---|---|---:|:-:|:-:|:-:|:-:|:-:|:-:|")
        b2_map = s["b2"]["per_analyst"]
        for name in sorted(s["hit_rate"]["per_analyst"].keys()):
            v = s["hit_rate"]["per_analyst"][name]
            b = b2_map.get(name, {})
            bs = b.get("match_score_0_to_4", "-")
            bm = "Y" if b.get("binary_match") else "N"
            tm = b.get("topic_match", "-")
            tr = b.get("trigger_alignment", "-")
            fm = b.get("question_form_alignment", "-")
            gr = b.get("granularity_alignment", "-")
            lines.append(f"| {name} | {v['n_exact']}/{v['n_partial']}/{v['n_miss']} | {v['hit']:.2f} | **{bs}** | {bm} | {tm} | {tr} | {fm} | {gr} |")
        lines.append("")

    # Missed / overpredicted themes
    for s in summaries:
        lines.append(f"## {s['generator_model']} — qualitative")
        lines.append("")
        if s.get("summary"):
            lines.append(f"_Evaluator summary:_ {s['summary']}")
            lines.append("")
        if s.get("missed_actual_themes"):
            lines.append("**Missed actual themes:** " + "; ".join(s["missed_actual_themes"]))
            lines.append("")
        if s.get("overpredicted_themes"):
            lines.append("**Overpredicted themes:** " + "; ".join(s["overpredicted_themes"]))
            lines.append("")

    # Anti-leakage
    lines.append("## Anti-leakage")
    lines.append("")
    lines.append("| Generator | # leaked 4-grams | examples |")
    lines.append("|---|---:|---|")
    for s in summaries:
        lk = s["anti_leakage"]
        ex = "; ".join(lk["examples"]) if lk["examples"] else "—"
        lines.append(f"| {s['generator_model']} | {lk['n_leaked_4grams']} | {ex} |")
    lines.append("")

    lines.append("## Artifacts")
    lines.append("")
    for s in summaries:
        sl = _slug(s["generator_model"])
        lines.append(f"- `data_baseline/{sl}/pool.json` — 12 generated questions + raw LLM response")
        lines.append(f"- `data_baseline/{sl}/set_evaluation.json` — bidirectional B4 verdict (full rubric)")
        lines.append(f"- `data_baseline/{sl}/summary.json`, `bleu.json`")
    lines.append("")

    with open(REPORT_PATH, "w") as f:
        f.write("\n".join(lines))
    print(f"\nWrote report -> {REPORT_PATH}")


def render_k110_section(s: dict) -> str:
    """Markdown section for the K=110 sample-10 experiment."""
    lines: list[str] = []
    K = s["K_eff"]
    k = s["k_sample"]
    a = s["hit_rate"]["all_analysts"]
    r = s["hit_rate"]["returning_subset"]
    b2 = s["b2"]
    bs = s["b4_sampled"]["metrics"]
    bo = s["b4_oracle"]["metrics"]

    lines.append(f"## K=110 + sample-{k} experiment (generator: {s['generator_model']}, seed={s['seed']})")
    lines.append("")
    lines.append(f"**Setup.** gpt-5-mini was asked once (temperature=1) to generate 110 distinct Q&A questions from the prepared remarks. After dedup K_eff = **{K}**. A fixed RNG (seed=42) then drew **10 random candidates per analyst** as that analyst's predicted set (B2 / V1 inputs) and a **single 10-question slate** for B4 sampled. B4 oracle uses the full {K}-pool.")
    lines.append("")
    lines.append("| Metric | Value | Upstream reference |")
    lines.append("|---|---|---|")
    lines.append(f"| K (post-dedup) | {K} | — |")
    lines.append(f"| k_sample (per analyst & B4 slate) | {k} | — |")
    lines.append(f"| **V1 hit (returning 9 / {r['n_actual']})** | {r['n_exact']+r['n_partial']}/{r['n_actual']} = **{r['hit']:.3f}** | V1 auto_discovery 0.600 |")
    lines.append(f"| V1 hit (all 11 / {a['n_actual']}) | {a['n_exact']+a['n_partial']}/{a['n_actual']} = **{a['hit']:.3f}** | — |")
    lines.append(f"| **B2 binary match** | {b2['binary_match_count']}/{b2['n_analysts']} = **{b2['binary_match_rate']:.3f}** | V2 B2 0.273 |")
    lines.append(f"| B2 avg score | **{b2['average_match_score']:.2f}** / 4 | V2 B2 1.45 |")
    lines.append(f"| **B4 sampled coverage** | {bs['coverage_count']}/{s['actual_count']} = **{bs['coverage_rate']:.3f}** | V2 B4 0.667 |")
    lines.append(f"| B4 sampled precision | {bs['useful_prediction_count']}/{k} = **{bs['precision_rate']:.3f}** | V2 B4 0.667 |")
    lines.append(f"| B4 sampled avg actual best | {bs['average_actual_best_score']:.2f} | V2 B4 2.92 |")
    lines.append(f"| B4 sampled avg pred best | {bs['average_predicted_best_score']:.2f} | V2 B4 2.50 |")
    lines.append(f"| **B4 oracle coverage** ({K} preds) | {bo['coverage_count']}/{s['actual_count']} = **{bo['coverage_rate']:.3f}** | (upper bound) |")
    lines.append(f"| B4 oracle precision | {bo['useful_prediction_count']}/{K} = {bo['precision_rate']:.3f} | — |")
    lines.append(f"| B4 oracle avg actual best | {bo['average_actual_best_score']:.2f} | (upper bound) |")
    lines.append(f"| BLEU-2 / BLEU-4 (full pool refs) | {s['bleu_full_pool']['mean_B2']:.4f} / {s['bleu_full_pool']['mean_B4']:.4f} | — |")
    lines.append(f"| BLEU-2 / BLEU-4 (slate-10 refs) | {s['bleu_slate_10']['mean_B2']:.4f} / {s['bleu_slate_10']['mean_B4']:.4f} | — |")
    lines.append(f"| 4-gram leak count | {s['anti_leakage']['n_leaked_4grams']} | — |")
    lines.append("")

    # Per-analyst breakdown
    lines.append(f"### Per-analyst V1 + B2 on the seeded sample of {k}")
    lines.append("")
    lines.append("| Analyst | V1 (E/P/M) | V1 hit | B2 score 0-4 | B2 binary | topic | trigger | form | gran |")
    lines.append("|---|---|---:|:-:|:-:|:-:|:-:|:-:|:-:|")
    b2_map = b2["per_analyst"]
    for name in sorted(s["hit_rate"]["per_analyst"].keys()):
        v = s["hit_rate"]["per_analyst"][name]
        b = b2_map.get(name, {})
        bs_score = b.get("match_score_0_to_4", "-")
        bm = "Y" if b.get("binary_match") else "N"
        tm = b.get("topic_match", "-")
        tr = b.get("trigger_alignment", "-")
        fm = b.get("question_form_alignment", "-")
        gr = b.get("granularity_alignment", "-")
        lines.append(f"| {name} | {v['n_exact']}/{v['n_partial']}/{v['n_miss']} | {v['hit']:.2f} | **{bs_score}** | {bm} | {tm} | {tr} | {fm} | {gr} |")
    lines.append("")

    lines.append("### Artifacts")
    lines.append("")
    slug = f"{_slug(s['generator_model'])}_k{s['K_requested']}"
    lines.append(f"- `data_baseline/{slug}/pool.json` — raw 110-pool + dedup log + K_eff")
    lines.append(f"- `data_baseline/{slug}/samples.json` — per-analyst sampled candidate_ids + B4 slate ids + seed")
    lines.append(f"- `data_baseline/{slug}/judgments/*.json` — V1 verdicts (sampled-10)")
    lines.append(f"- `data_baseline/{slug}/b2/*.json` — B2 evaluator verdicts (sampled-10)")
    lines.append(f"- `data_baseline/{slug}/b4_sampled.json` — B4 verdict on the 10-slate")
    lines.append(f"- `data_baseline/{slug}/b4_oracle.json` — B4 verdict on full {K}-pool")
    lines.append(f"- `data_baseline/{slug}/bleu.json`, `summary.json`")
    lines.append("")
    return "\n".join(lines)


def main() -> None:
    test = json.load(open(TEST_PATH))
    mgmt = _strip_qa(test["management_context"])
    actuals = flatten_actuals(test)
    print(f"Loaded {len(actuals)} actual questions across {len({a['analyst'] for a in actuals})} analysts")

    only = os.environ.get("BCP_ONLY", "").strip()  # "k12", "k110", or ""

    summaries: list[dict] = []
    if only != "k110":
        for slug, model in MODELS:
            summaries.append(run_one_model(slug, model, test, mgmt, actuals))
        render_report(summaries, actuals)

    if only != "k12":
        K = int(os.environ.get("BCP_K", "110"))
        k_sample = int(os.environ.get("BCP_KSAMPLE", "10"))
        seed = int(os.environ.get("BCP_SEED", "42"))
        k110 = run_k110_sample_experiment(test, mgmt, actuals,
                                          K=K, k_sample=k_sample, seed=seed,
                                          generator_model="gpt-5-mini")
        # Append K=110 section to the existing report (if present) or write a
        # standalone report.
        section = render_k110_section(k110)
        try:
            existing = open(REPORT_PATH).read()
        except FileNotFoundError:
            existing = ""
        if "K=110 + sample-" in existing:
            # Replace existing K=110 section (everything from the K=110 header
            # to the next top-level "## " header or EOF).
            marker = "## K=110 + sample-"
            head = existing[: existing.index(marker)]
            tail = existing[existing.index(marker):]
            # find next top-level section after this one
            rest_idx = tail.find("\n## ", 4)  # skip its own header
            tail_after = tail[rest_idx:] if rest_idx > 0 else ""
            existing = head.rstrip() + "\n\n" + section + "\n" + tail_after.lstrip()
        else:
            existing = existing.rstrip() + "\n\n" + section + "\n"
        with open(REPORT_PATH, "w") as f:
            f.write(existing)
        print(f"  Wrote K=110 section -> {REPORT_PATH}")


if __name__ == "__main__":
    main()
