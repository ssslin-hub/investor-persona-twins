"""One-shot evaluator: given (in-summary, out-dir, model, n_runs, do_chunked),
run B2+B4 (+chunked) n_runs times. Cached-skip per run. For batch parallelism.
"""
import argparse, json, os, subprocess, sys
HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
EVAL = os.path.join(HERE, "eval_gpt5_generic.py")
CHUNK = os.path.join(HERE, "b4_chunked_precision.py")


def run_once(in_summary, out_dir, model, do_chunked):
    os.makedirs(out_dir, exist_ok=True)
    env = os.environ.copy(); env["EVAL_MODEL"] = model
    for sub in ("pool", "b2", "b4"):
        cmd = ["python3", EVAL, sub, "--in-summary", in_summary, "--out-dir", out_dir]
        with open(os.path.join(out_dir, f"{sub}.log"), "w") as fp:
            subprocess.run(cmd, stdout=fp, stderr=subprocess.STDOUT, env=env, cwd=ROOT, check=False)
    if do_chunked:
        cmd = ["python3", CHUNK, "--in-summary", in_summary, "--out-dir", out_dir, "--chunk-size", "50"]
        with open(os.path.join(out_dir, "chunked.log"), "w") as fp:
            subprocess.run(cmd, stdout=fp, stderr=subprocess.STDOUT, env=env, cwd=ROOT, check=False)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--in-summary", required=True)
    ap.add_argument("--out-base", required=True, help="dir containing run_1, run_2, ...")
    ap.add_argument("--model", required=True)
    ap.add_argument("--n-runs", type=int, default=5)
    ap.add_argument("--chunked", action="store_true")
    args = ap.parse_args()
    for i in range(1, args.n_runs+1):
        out_dir = os.path.join(args.out_base, f"run_{i}")
        cached = os.path.exists(os.path.join(out_dir, "b4.json"))
        if args.chunked:
            cached = cached and os.path.exists(os.path.join(out_dir, "b4_precision_chunked.json"))
        if cached:
            print(f"  {args.model} run {i}: cached"); continue
        print(f"  {args.model} run {i}: running")
        run_once(args.in_summary, out_dir, args.model, args.chunked)


if __name__ == "__main__":
    main()
