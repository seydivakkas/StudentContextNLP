"""Full synthetic smoke run; demo results NEVER count as scientific evidence."""
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from scripts.create_synthetic_fixture import build
from train_lexical import run
from compare_experiments import report
from plot_comparison import make_plot


def main():
    data = ROOT / 'data/demo'
    out = ROOT / 'results/demo/lexical'
    build(data, repeats=4)
    result = run(data, out, allow_warnings=True)
    summary = report(out / 'baseline_results.json', ROOT / 'results/demo/semantic/semantic_results.json', ROOT / 'results/demo/combined')
    make_plot(ROOT / 'results/demo/combined/model_comparison.csv', ROOT / 'results/demo/figures/test_uq_macro_f1.png', synthetic=True)
    print('SYNTHETIC SMOKE ONLY — NOT SCIENTIFIC RESULTS')
    print('B1:', result['metrics']['test_uq']['B1']['macro_f1'])
    print('B2:', result['metrics']['test_uq']['B2']['macro_f1'])
    print('Summary:', summary)


if __name__ == '__main__':
    main()
