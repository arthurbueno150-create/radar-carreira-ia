"""Leitura, limpeza e coleta manual de uma amostra pública do Jobicy."""
from datetime import datetime, timezone, timedelta
from html import unescape
from html.parser import HTMLParser
from pathlib import Path
import hashlib
import json
import re
from urllib.parse import urlparse
from urllib.request import Request, urlopen

from .skills import extract_skills, normalize

ROOT = Path(__file__).resolve().parents[1]
DATA_PATH = ROOT / 'data' / 'jobs.json'
FEEDS = [f'https://jobicy.com/api/v2/remote-jobs?count=200&industry={category}'
         for category in ['data-science', 'engineering']]


class TextExtractor(HTMLParser):
    def __init__(self):
        super().__init__()
        self.parts = []
        self.hidden = 0

    def handle_starttag(self, tag, attrs):
        if tag in {'script', 'style'}:
            self.hidden += 1
        if tag in {'p', 'div', 'li', 'br', 'h1', 'h2', 'h3'}:
            self.parts.append('\n')

    def handle_endtag(self, tag):
        if tag in {'script', 'style'}:
            self.hidden = max(0, self.hidden - 1)

    def handle_data(self, data):
        if not self.hidden:
            self.parts.append(data)


def plain_text(value) -> str:
    parser = TextExtractor()
    parser.feed(str(value or ''))
    return re.sub(r'\s+', ' ', unescape(' '.join(parser.parts))).strip()


def valid_source_url(value: str) -> bool:
    parsed = urlparse(value)
    return parsed.scheme == 'https' and parsed.hostname in {'jobicy.com', 'www.jobicy.com'}


def build_snapshot(payloads: list[dict], fetched_at: str | None = None) -> dict:
    jobs, seen_ids, seen_texts = [], set(), set()
    raw_count = duplicates = rejected = 0
    for payload in payloads:
        for raw in payload.get('jobs', []):
            raw_count += 1
            title = plain_text(raw.get('jobTitle'))
            description = plain_text(raw.get('jobDescription'))
            company = plain_text(raw.get('companyName'))
            url = raw.get('url', '')
            if not title or not description or not valid_source_url(url):
                rejected += 1
                continue
            job_id = str(raw.get('id', ''))
            fingerprint = hashlib.sha256(normalize(company + ' ' + title + ' ' + description).encode()).hexdigest()
            if job_id in seen_ids or fingerprint in seen_texts:
                duplicates += 1
                continue
            seen_ids.add(job_id)
            seen_texts.add(fingerprint)
            industries = raw.get('jobIndustry') or []
            category = 'Dados e analytics' if any('Data Science' in x for x in industries) else 'Engenharia de software'
            jobs.append({
                'id': job_id, 'title': title, 'company': company, 'url': url,
                'category': category, 'source_category': ', '.join(industries),
                'location': plain_text(raw.get('jobGeo')) or 'Não informada',
                'level': plain_text(raw.get('jobLevel')) or 'Não informado',
                'published_at': raw.get('pubDate'), 'description': description,
                'skills': extract_skills(title + ' ' + description),
                'salary_min': raw.get('salaryMin'), 'salary_max': raw.get('salaryMax'),
                'salary_currency': raw.get('salaryCurrency'), 'salary_period': raw.get('salaryPeriod'),
                'source': 'Jobicy',
            })
    jobs.sort(key=lambda j: (j['published_at'] or '', j['id']), reverse=True)
    content_hash = hashlib.sha256(json.dumps(jobs, sort_keys=True, ensure_ascii=False).encode()).hexdigest()
    return {'metadata': {
        'source': 'Jobicy', 'source_url': 'https://jobicy.com/jobs-rss-feed',
        'fetched_at': fetched_at or datetime.now(timezone.utc).isoformat(),
        'endpoints': FEEDS, 'raw_count': raw_count, 'count': len(jobs),
        'duplicates_removed': duplicates, 'rejected': rejected, 'sha256': content_hash,
        'sampling': 'Até 200 vagas recentes por categoria: Data Science & Analytics e Software Engineering. Amostra de conveniência, sem representatividade do Brasil ou do mercado total.',
    }, 'jobs': jobs}


def load_snapshot(path: Path = DATA_PATH) -> dict:
    return json.loads(path.read_text(encoding='utf-8'))


def refresh_snapshot(path: Path = DATA_PATH) -> dict:
    if path.exists():
        old = load_snapshot(path)
        age = datetime.now(timezone.utc) - datetime.fromisoformat(old['metadata']['fetched_at'])
        if age < timedelta(hours=6):
            raise ValueError('A coleta mais recente tem menos de 6 horas. Use a cópia local.')
    payloads = []
    for url in FEEDS:
        request = Request(url, headers={'User-Agent': 'RadarCarreiraIA/1.0 (educational research)'})
        with urlopen(request, timeout=45) as response:
            payload = json.load(response)
        if not isinstance(payload.get('jobs'), list) or not payload['jobs']:
            raise ValueError('A fonte retornou uma lista vazia ou inválida. A base anterior foi preservada.')
        payloads.append(payload)
    snapshot = build_snapshot(payloads)
    if len(snapshot['jobs']) < 10:
        raise ValueError('Amostra insuficiente. A base anterior foi preservada.')
    path.parent.mkdir(parents=True, exist_ok=True)
    temp = path.with_suffix('.tmp')
    temp.write_text(json.dumps(snapshot, ensure_ascii=False, indent=2), encoding='utf-8')
    temp.replace(path)
    return snapshot
