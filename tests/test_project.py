import json
import sys
from pathlib import Path

import numpy as np
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from app import create_app
from radar.analytics import select_indices
from radar.data import build_snapshot, plain_text, load_snapshot, valid_source_url
from radar.skills import extract_skills


@pytest.fixture(scope='module')
def app():
    application = create_app()
    application.config['TESTING'] = True
    return application


@pytest.fixture()
def client(app):
    return app.test_client()


def test_html_is_cleaned_and_script_removed():
    assert plain_text('<p>SQL &amp; Python</p><script>alert(1)</script>') == 'SQL & Python'
    assert not valid_source_url('https://jobicy.com.evil.test/jobs/1')
    assert not valid_source_url('javascript:alert(1)')


def test_skill_boundaries_and_portuguese():
    skills = extract_skills('JavaScript, análises estatísticas? Estatística, visualização de dados e PostgreSQL; RAG.')
    assert 'JavaScript' in skills and 'Java' not in skills
    assert {'Estatística', 'Visualização', 'SQL', 'RAG'} <= set(skills)
    assert 'RAG' not in extract_skills('fragmentation')
    assert 'C++' in extract_skills('C++ and C#')


def test_ingestion_deduplicates_and_rejects_bad_urls():
    raw = {'id': 1, 'jobTitle': 'Data scientist', 'companyName': 'Example',
           'jobDescription': '<p>Python SQL</p>', 'url': 'https://jobicy.com/jobs/1'}
    snapshot = build_snapshot([{'jobs': [raw, raw, {**raw, 'id': 2}, {**raw, 'url': 'javascript:bad'}]}])
    assert snapshot['metadata']['count'] == 1
    assert snapshot['metadata']['duplicates_removed'] == 2
    assert snapshot['metadata']['rejected'] == 1


def test_snapshot_integrity():
    snapshot = load_snapshot()
    assert snapshot['metadata']['count'] == len(snapshot['jobs'])
    assert len({j['id'] for j in snapshot['jobs']}) == len(snapshot['jobs'])
    assert all(valid_source_url(j['url']) for j in snapshot['jobs'])


def test_data_filter_is_consistent(client):
    response = client.get('/api/overview?category=Dados%20e%20analytics')
    data = response.get_json()
    assert response.status_code == 200
    assert set(data['categories']) == {'Dados e analytics'}
    assert data['count'] == len(data['points'])
    assert all(s['count'] <= data['count'] for s in data['skills'])
    assert client.get('/api/overview?q=zzzz-no-match-0000').get_json()['count'] == 0


def test_recommendation_bounds_and_explanation(client):
    result = client.post('/api/recommend', json={'profile': 'Python SQL Pandas'}).get_json()
    scores = [j['score'] for j in result['matches']]
    assert scores == sorted(scores, reverse=True)
    assert all(0 <= score <= 100 for score in scores)
    for job in result['matches']:
        assert set(job['matched']) <= {'Python', 'SQL', 'Pandas'}
        assert set(job['matched']).isdisjoint(job['missing'])
        assert abs(job['score'] - (.65 * job['coverage'] + .35 * job['text_similarity'])) < .11


def test_what_if_improves_coverage_without_changing_population(client):
    before = client.post('/api/recommend', json={'profile': 'Python SQL'}).get_json()
    after = client.post('/api/recommend', json={'profile': 'Python SQL', 'extra_skills': ['AWS', 'Docker']}).get_json()
    assert after['assessed'] == before['assessed']
    assert after['simulation']['after'] >= before['simulation']['after']
    assert after['simulation']['above80_after'] >= before['simulation']['above80_after']
    assert after['simulation']['before'] == before['simulation']['before']


def test_same_skill_twice_does_not_inflate_results(client):
    once = client.post('/api/recommend', json={'profile': 'Python', 'extra_skills': ['AWS']}).get_json()
    twice = client.post('/api/recommend', json={'profile': 'Python', 'extra_skills': ['AWS', 'AWS', 'Python']}).get_json()
    assert once['simulation'] == twice['simulation']


@pytest.mark.parametrize('payload', [None, [], {'profile': ''}, {'profile': 2}, {'profile': 'x'*6001},
                                     {'profile': 'SQL', 'extra_skills': ['fake skill']},
                                     {'profile': 'SQL', 'extra_skills': [{}]}])
def test_input_validation(client, payload):
    assert client.post('/api/recommend', json=payload).status_code == 400


def test_no_matches_and_unknown_profile(client):
    data = client.post('/api/recommend?q=no-match-00000', json={'profile': 'Python'}).get_json()
    assert data['matches'] == [] and data['plan'] == [] and data['simulation']['after'] == 0
    data = client.post('/api/recommend', json={'profile': 'zzzzzzzzzzzzz'}).get_json()
    assert not data['has_text_signal']
    assert all(j['score'] == 0 for j in data['matches'])


def test_export_does_not_include_raw_profile(client):
    profile = 'UNIQUE_PRIVATE_TEXT_12345 Python SQL'
    response = client.post('/api/export', json={'profile': profile})
    assert response.status_code == 200
    assert 'attachment' in response.headers['Content-Disposition']
    assert profile not in response.get_data(as_text=True)
    assert response.get_json()['data_source']['source'] == 'Jobicy'


def test_app_and_security_headers(client):
    response = client.get('/')
    assert response.status_code == 200
    assert response.headers['X-Content-Type-Options'] == 'nosniff'
    assert "default-src 'self'" in response.headers['Content-Security-Policy']
    assert client.post('/api/recommend', data='x'*40000, content_type='application/json').status_code == 413
    assert client.get('/health').get_json()['status'] == 'ok'


def test_report_has_no_company_leakage(client):
    report = client.get('/api/methodology').get_json()['report']
    assert report['data_sha256'] == load_snapshot()['metadata']['sha256']
    assert report['supervised']['company_overlap'] == 0
    assert report['supervised']['train_rows'] + report['supervised']['test_rows'] == report['rows']
    assert sum(map(sum, report['supervised']['confusion_matrix'])) == report['supervised']['test_rows']
