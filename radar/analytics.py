from collections import Counter
from datetime import datetime, timezone
import pandas as pd

from .skills import normalize


def select_indices(jobs, category='', query='', location=''):
    needle, region = normalize(query), normalize(location)
    return [i for i, j in enumerate(jobs)
            if (not category or j['category'] == category)
            and (not needle or needle in normalize(j['title'] + ' ' + j['company'] + ' ' + ' '.join(j['skills'])))
            and (not region or region in normalize(j['location']))]


def overview(snapshot, model, indices):
    jobs = [model.jobs[i] for i in indices]
    count = len(jobs)
    frequencies = Counter(s for j in jobs for s in j['skills'])
    weekly = []
    if jobs:
        dates = pd.to_datetime(pd.Series([j['published_at'] for j in jobs]), utc=True, errors='coerce')
        frame = pd.DataFrame({'week': dates.dt.strftime('%G-W%V')}).dropna()
        weekly = [{'week': k, 'count': int(v)} for k, v in frame.groupby('week').size().items()]
    ai_skills = {'Machine Learning', 'Deep Learning', 'LLMs', 'IA generativa', 'NLP', 'RAG'}
    ai_count = sum(bool(ai_skills.intersection(j['skills'])) for j in jobs)
    latest = max((j['published_at'] or '' for j in jobs), default='')
    oldest = min((j['published_at'] for j in jobs if j['published_at']), default='')
    age_days = (datetime.now(timezone.utc) - datetime.fromisoformat(snapshot['metadata']['fetched_at'])).days
    return {
        'metadata': snapshot['metadata'], 'age_days': max(0, age_days),
        'count': count, 'companies': len({j['company'] for j in jobs}),
        'skill_count': len(frequencies), 'ai_count': ai_count,
        'ai_share': round(100 * ai_count / count, 1) if count else 0,
        'skills': [{'name': s, 'count': n, 'share': round(n / count * 100, 1)} for s, n in frequencies.most_common(16)],
        'weekly': weekly, 'latest': latest, 'oldest': oldest,
        'categories': dict(Counter(j['category'] for j in jobs)),
        'levels': dict(Counter(j['level'] for j in jobs)),
        'locations': dict(Counter(j['location'] for j in jobs).most_common(8)),
        'no_skills': sum(not j['skills'] for j in jobs),
        'salary_missing': sum(j['salary_min'] is None for j in jobs),
        'clusters': model.cluster_info,
        'points': [{'id': model.jobs[i]['id'], 'title': model.jobs[i]['title'],
                    'company': model.jobs[i]['company'], 'cluster': int(model.labels[i]),
                    'x': round(float(model.coordinates[i, 0]), 4),
                    'y': round(float(model.coordinates[i, 1]), 4)} for i in indices],
    }
