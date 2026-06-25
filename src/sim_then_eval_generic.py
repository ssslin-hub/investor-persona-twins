"""Generic fresh-sim + 5-run gpt-5 eval driver.
Supports source ∈ {v1, auto, v5} and writes to
  data_auto/final_eval_<K>q_<source>_<label>/{summary.json, variance/run_*/...}

Usage: python3 src/sim_then_eval_generic.py --source v5 --K 16 --label s2 --n-eval-runs 5
"""
import argparse, json, os, subprocess, sys
HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, HERE)
from llm_client import call_llm, parse_json_strict  # noqa: E402
from run_pipeline import build_simulator_prompt, stub_predictions, load_text  # noqa: E402

ALL_11 = ['matthew boss','steven wieczynski','brandt montour','james hardiman','lizzie dove','robin farley','vince ciepiel','sharon zackfia','andrew didora','xian siew','kevin kopelman']
COLD = ['xian siew','kevin kopelman']
EVAL_SCRIPT = os.path.join(HERE, 'eval_gpt5_generic.py')

PERSONA_ROOTS = {
    'v1':   os.path.join(ROOT, 'data', 'personas'),
    'v5':   os.path.join(ROOT, 'data', 'personas_v5'),
    'auto': os.path.join(ROOT, 'data_auto', 'final_personas'),
}
FALLBACK = os.path.join(ROOT, 'data_auto', 'final_personas', '_fallback.json')


def load_persona(name, source):
    if name in COLD:
        return json.load(open(FALLBACK))
    p = os.path.join(PERSONA_ROOTS[source], f"{name.replace(' ','_')}.json")
    return json.load(open(p)) if os.path.exists(p) else None


def simulate(out_dir, K, source):
    log_dir = os.path.join(out_dir, 'logs'); os.makedirs(log_dir, exist_ok=True)
    test = json.load(open(os.path.join(ROOT, 'data_auto', 'test.json')))
    mgmt = test['management_context']; actuals_by = test['per_analyst_actual_questions']
    sim_tpl = load_text(os.path.join(ROOT, 'prompts', f'simulate_questions_{K}q.md'))
    per_analyst = {}
    total = 0
    for name in ALL_11:
        actuals = actuals_by.get(name, [])
        if not actuals: continue
        persona = load_persona(name, source)
        if persona is None: print(f"  ! {name}: no persona"); continue
        prompt = build_simulator_prompt(sim_tpl, persona, mgmt)
        try:
            out = call_llm(prompt, expect_json=True, dry_run_stub=stub_predictions(name),
                           log_to=f"{log_dir}/sim_{name.replace(' ','_')}.txt")
            pred = parse_json_strict(out)
        except Exception as e:
            print(f"  ! {name}: {e}"); pred = stub_predictions(name)
        pq = pred.get('predicted_questions', [])
        if len(pq) > K: pred['predicted_questions'] = pq[:K]
        per_analyst[name] = {'n_actual': len(actuals), 'predictions': pred,
                              'persona_source': source if name not in COLD else 'auto-fallback'}
        total += len(pred.get('predicted_questions', []))
        print(f"  {name:25s} K={len(pq)}")
    summary = {'K': K, 'source': source, 'n_analysts_scored': len(per_analyst),
               'total_predicted_questions': total, 'per_analyst': per_analyst}
    with open(os.path.join(out_dir, 'summary.json'), 'w') as f:
        json.dump(summary, f, indent=2)


def run_eval(in_summary, out_dir, model='gpt-5'):
    os.makedirs(out_dir, exist_ok=True)
    env = os.environ.copy(); env['EVAL_MODEL'] = model
    for sub in ('pool','b2','b4'):
        cmd = ['python3', EVAL_SCRIPT, sub, '--in-summary', in_summary, '--out-dir', out_dir]
        log = os.path.join(out_dir, f'{sub}.log')
        with open(log, 'w') as fp:
            subprocess.run(cmd, stdout=fp, stderr=subprocess.STDOUT, env=env, cwd=ROOT, check=False)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--source', choices=['v1','auto','v5'], required=True)
    ap.add_argument('--K', type=int, required=True)
    ap.add_argument('--label', required=True)
    ap.add_argument('--n-eval-runs', type=int, default=5)
    args = ap.parse_args()
    out_dir = os.path.join(ROOT, 'data_auto', f'final_eval_{args.K}q_{args.source}_{args.label}')
    os.makedirs(out_dir, exist_ok=True)
    summary_path = os.path.join(out_dir, 'summary.json')
    if not os.path.exists(summary_path):
        print(f"=== SIM {args.source} K={args.K} {args.label} ===")
        simulate(out_dir, args.K, args.source)
    else:
        print(f"=== SIM cached: {args.source} K={args.K} {args.label} ===")
    var_dir = os.path.join(out_dir, 'variance'); os.makedirs(var_dir, exist_ok=True)
    for i in range(1, args.n_eval_runs+1):
        run_d = os.path.join(var_dir, f'run_{i}')
        if os.path.exists(os.path.join(run_d, 'b4.json')):
            print(f"  eval run {i}: cached"); continue
        print(f"  eval run {i}: running")
        run_eval(summary_path, run_d)


if __name__ == '__main__':
    main()
