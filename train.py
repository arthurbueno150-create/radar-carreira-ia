"""Reproduz os experimentos e salva métricas vinculadas ao hash dos dados."""
import json
from datetime import datetime, timezone
import importlib.metadata

from radar.data import load_snapshot, ROOT
from radar.model import CareerModel
from radar.evaluation import evaluate_categories


def main():
    snapshot = load_snapshot()
    model = CareerModel(snapshot['jobs'])
    report = {
        'generated_at': datetime.now(timezone.utc).isoformat(),
        'data_sha256': snapshot['metadata']['sha256'], 'random_state': 42,
        'rows': len(model.jobs), 'text_vocabulary': len(model.vectorizer.vocabulary_),
        'versions': {p: importlib.metadata.version(p) for p in ['scikit-learn', 'numpy', 'pandas']},
        'clustering': {'silhouette': model.silhouette, 'metric': 'cosine',
                       'trials': model.cluster_trials, 'clusters': model.cluster_info,
                       'projection_variance': round(model.projection_variance, 4),
                       'note': 'Silhouette é diagnóstico interno usado para escolher k; não é acurácia em teste.'},
        'supervised': evaluate_categories(model.jobs),
    }
    destination = ROOT / 'reports' / 'model_report.json'
    destination.parent.mkdir(exist_ok=True)
    destination.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding='utf-8')
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return report


if __name__ == '__main__':
    main()
