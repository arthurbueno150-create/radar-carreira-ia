"""Execute: python app.py --open. O processamento e o ML são feitos em Python."""
import argparse
import json
import os
from pathlib import Path
from threading import Timer
import webbrowser

from flask import Flask, jsonify, render_template, request, Response
from waitress import serve

from radar.analytics import overview, select_indices
from radar.data import load_snapshot, ROOT
from radar.model import CareerModel
from radar.skills import SKILLS


def create_app(snapshot=None):
    app = Flask(__name__)
    app.config['MAX_CONTENT_LENGTH'] = 32 * 1024
    app.json.ensure_ascii = False
    app.json.sort_keys = False
    snapshot = snapshot or load_snapshot()
    model = CareerModel(snapshot['jobs'])
    app.extensions['career_model'] = model

    def indices():
        return select_indices(model.jobs, request.args.get('category', ''),
                              request.args.get('q', ''), request.args.get('location', ''))

    @app.after_request
    def headers(response):
        response.headers['X-Content-Type-Options'] = 'nosniff'
        response.headers['X-Frame-Options'] = 'DENY'
        response.headers['Referrer-Policy'] = 'no-referrer'
        response.headers['Content-Security-Policy'] = (
            "default-src 'self'; script-src 'self'; style-src 'self' 'unsafe-inline'; "
            "img-src 'self' data:; connect-src 'self'; frame-ancestors 'none'; base-uri 'self'; form-action 'self'")
        response.headers['Cache-Control'] = 'no-store'
        return response

    @app.get('/')
    def index():
        return render_template('index.html')

    @app.get('/health')
    def health():
        return jsonify(status='ok', jobs=len(model.jobs), model='tfidf-kmeans', version='1.0.0')

    @app.get('/api/overview')
    def stats():
        return jsonify(overview(snapshot, model, indices()))

    @app.get('/api/options')
    def options():
        return jsonify(skills=list(SKILLS), categories=sorted({j['category'] for j in model.jobs}),
                       locations=sorted({j['location'] for j in model.jobs}))

    def analyze_payload():
        payload = request.get_json(silent=True)
        if not isinstance(payload, dict):
            return None, ('Envie um objeto JSON válido.', 400)
        profile = payload.get('profile', '')
        if not isinstance(profile, str) or not profile.strip():
            return None, ('Descreva suas competências antes de analisar.', 400)
        if len(profile) > 6000:
            return None, ('Use no máximo 6.000 caracteres.', 400)
        extra = payload.get('extra_skills', [])
        if not isinstance(extra, list) or any(not isinstance(s, str) or s not in SKILLS for s in extra):
            return None, ('A simulação contém uma competência desconhecida.', 400)
        return model.recommend(profile, indices(), list(dict.fromkeys(extra))), None

    @app.post('/api/recommend')
    def recommend():
        result, error = analyze_payload()
        if error:
            return jsonify(error=error[0]), error[1]
        return jsonify(result)

    @app.post('/api/export')
    def export_plan():
        result, error = analyze_payload()
        if error:
            return jsonify(error=error[0]), error[1]
        # O texto digitado não é persistido nem incluído na exportação.
        result['data_source'] = snapshot['metadata']
        result['note'] = 'Índices de afinidade e cobertura não são probabilidades de contratação.'
        return Response(json.dumps(result, ensure_ascii=False, indent=2), mimetype='application/json',
                        headers={'Content-Disposition': 'attachment; filename="meu-plano-radar.json"'})

    @app.get('/api/methodology')
    def methodology():
        report_path = ROOT / 'reports' / 'model_report.json'
        report = json.loads(report_path.read_text(encoding='utf-8')) if report_path.exists() else {}
        # Nunca mostrar métricas antigas como se pertencessem a uma base atualizada.
        if report.get('data_sha256') != snapshot['metadata']['sha256']:
            report = {'status': 'Execute python train.py para avaliar esta versão da base.'}
        return jsonify(report=report, trials=model.cluster_trials, silhouette=model.silhouette,
                       clusters=model.cluster_info, projection_variance=model.projection_variance,
                       vocabulary=len(model.vectorizer.vocabulary_), skills=len(SKILLS),
                       metadata=snapshot['metadata'])

    @app.errorhandler(413)
    def large_payload(error):
        return jsonify(error='Conteúdo muito grande. Limite: 32 KB.'), 413

    return app


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--open', action='store_true', help='Abre o navegador local')
    parser.add_argument('--port', type=int, default=int(os.environ.get('PORT', 8765)))
    args = parser.parse_args()
    application = create_app()
    if args.open:
        Timer(1.5, lambda: webbrowser.open(f'http://127.0.0.1:{args.port}')).start()
    print(f'Radar de Carreira IA pronto em http://127.0.0.1:{args.port}', flush=True)
    serve(application, host=os.environ.get('RADAR_HOST', '127.0.0.1'), port=args.port, threads=4)
