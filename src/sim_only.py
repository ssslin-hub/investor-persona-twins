"""Sim-only driver (no eval). For batch-eval workflow."""
import argparse, json, os, sys
HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, HERE)
from llm_client import call_llm, parse_json_strict
from run_pipeline import build_simulator_prompt, stub_predictions, load_text

ALL_11 = ['matthew boss','steven wieczynski','brandt montour','james hardiman','lizzie dove','robin farley','vince ciepiel','sharon zackfia','andrew didora','xian siew','kevin kopelman']
COLD = ['xian siew','kevin kopelman']
PERSONA_ROOTS = {
    'v1':   os.path.join(ROOT, 'data', 'personas'),
    'v5':   os.path.join(ROOT, 'data', 'personas_v5'),
    'auto': os.path.join(ROOT, 'data_auto', 'final_personas'),
}
FALLBACK = os.path.join(ROOT, 'data_auto', 'final_personas', '_fallback.json')


def load_persona(name, source):
    if name in COLD: return json.load(open(FALLBACK))
    p = os.path.join(PERSONA_ROOTS[source], f"{name.replace(' ','_')}.json")
    return json.load(open(p)) if os.path.exists(p) else None


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--source', required=True)
    ap.add_argument('--K', type=int, required=True)
    ap.add_argument('--label', required=True)
    args = ap.parse_args()
    out_dir = os.path.join(ROOT, 'data_auto', f'final_eval_{args.K}q_{args.source}_{args.label}')
    os.makedirs(out_dir, exist_ok=True)
    log_dir = os.path.join(out_dir, 'logs'); os.makedirs(log_dir, exist_ok=True)
    sp_path = os.path.join(ROOT, 'data_auto', f'final_eval_{args.K}q_{args.source}_{args.label}', 'summary.json')
    if os.path.exists(sp_path):
        print(f"cached: {args.K}q_{args.source}_{args.label}"); return
    test = json.load(open(os.path.join(ROOT, 'data_auto', 'test.json')))
    mgmt = test['management_context']; actuals_by = test['per_analyst_actual_questions']
    sim_tpl = load_text(os.path.join(ROOT, 'prompts', f'simulate_questions_{args.K}q.md'))
    per_analyst = {}; total = 0
    for name in ALL_11:
        actuals = actuals_by.get(name, [])
        if not actuals: continue
        persona = load_persona(name, args.source)
        if persona is None: continue
        prompt = build_simulator_prompt(sim_tpl, persona, mgmt)
        try:
            out = call_llm(prompt, expect_json=True, dry_run_stub=stub_predictions(name),
                           log_to=f"{log_dir}/sim_{name.replace(' ','_')}.txt")
            pred = parse_json_strict(out)
        except Exception as e:
            print(f"  ! {name}: {e}"); pred = stub_predictions(name)
        pq = pred.get('predicted_questions', [])
        if len(pq) > args.K: pred['predicted_questions'] = pq[:args.K]
        per_analyst[name] = {'n_actual': len(actuals), 'predictions': pred,
                              'persona_source': args.source if name not in COLD else 'auto-fallback'}
        total += len(pred.get('predicted_questions', []))
    summary = {'K': args.K, 'source': args.source, 'label': args.label,
               'n_analysts_scored': len(per_analyst), 'total_predicted_questions': total,
               'per_analyst': per_analyst}
    with open(sp_path, 'w') as f:
        json.dump(summary, f, indent=2)
    print(f"DONE {args.K}q_{args.source}_{args.label} (n={total})")


if __name__ == '__main__':
    main()
