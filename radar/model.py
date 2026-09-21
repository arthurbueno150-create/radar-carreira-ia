"""Modelos treinados localmente: TF-IDF, K-means e projeção SVD."""
from collections import Counter
import numpy as np
from sklearn.cluster import KMeans
from sklearn.decomposition import TruncatedSVD
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics import silhouette_score
from sklearn.preprocessing import MultiLabelBinarizer, normalize as unit_norm
from threadpoolctl import threadpool_limits

from .skills import SKILLS, canonical_text, extract_skills, learning_item


class CareerModel:
    def __init__(self, jobs: list[dict]):
        if len(jobs) < 3:
            raise ValueError('São necessárias pelo menos três vagas para treinar o modelo.')
        self.jobs = jobs
        self.vectorizer = TfidfVectorizer(stop_words='english', ngram_range=(1, 2),
                                        max_features=14000, min_df=1, sublinear_tf=True)
        self.text_matrix = self.vectorizer.fit_transform([
            canonical_text(job['title'] + ' ' + job['description']) for job in jobs])
        self.encoder = MultiLabelBinarizer(classes=list(SKILLS))
        self.binary = self.encoder.fit_transform([j['skills'] for j in jobs]).astype(float)
        self.idf = np.log((1 + len(jobs)) / (1 + self.binary.sum(axis=0))) + 1
        self.weighted = self.binary * self.idf
        self.normalized = unit_norm(self.weighted)
        self.denominators = self.weighted.sum(axis=1)
        self._fit_clusters()

    def _fit_clusters(self):
        # Vagas sem competências reconhecidas ficam fora do agrupamento.
        eligible = self.denominators > 0
        points = self.normalized[eligible]
        distinct = len(np.unique(points, axis=0))
        self.labels = np.full(len(self.jobs), -1, dtype=int)
        self.cluster_trials = []
        best = None
        with threadpool_limits(limits=1):
            for k in range(2, min(6, len(points) - 1, distinct) + 1):
                estimator = KMeans(n_clusters=k, random_state=42, n_init=10)
                labels = estimator.fit_predict(points)
                if 1 < len(set(labels)) < len(points):
                    score = float(silhouette_score(points, labels, metric='cosine'))
                    self.cluster_trials.append({'k': k, 'silhouette': round(score, 4)})
                    if best is None or score > best[0]:
                        best = (score, estimator, labels)
        if best:
            self.cluster_model = best[1]
            self.labels[eligible] = best[2]
            self.silhouette = round(best[0], 4)
        else:
            self.cluster_model = None
            self.labels[eligible] = 0
            self.silhouette = None
        self.cluster_info = []
        for label in sorted(set(self.labels)):
            selected = np.flatnonzero(self.labels == label)
            terms = Counter(s for i in selected for s in self.jobs[i]['skills']).most_common(3)
            self.cluster_info.append({'id': int(label), 'count': len(selected),
                                      'name': ' · '.join(s for s, _ in terms) if terms else 'Sem competências extraídas'})
        with threadpool_limits(limits=1):
            svd = TruncatedSVD(n_components=2, random_state=42)
            coords = svd.fit_transform(self.normalized)
        self.projection_variance = float(np.nan_to_num(svd.explained_variance_ratio_).sum())
        self.coordinates = coords

    def _coverage(self, skills: list[str]):
        present = np.array([s in skills for s in self.encoder.classes_], dtype=float)
        return np.divide(self.weighted @ present, self.denominators,
                         out=np.zeros(len(self.jobs)), where=self.denominators > 0)

    def recommend(self, profile: str, indices: list[int], extra_skills: list[str] | None = None,
                  limit: int = 12) -> dict:
        detected = extract_skills(profile)
        extras = [s for s in (extra_skills or []) if s not in detected]
        all_skills = list(dict.fromkeys(detected + extras))
        q = self.vectorizer.transform([canonical_text(profile)])
        similarity = np.asarray((self.text_matrix @ q.T).toarray()).ravel()
        before = self._coverage(detected)
        after = self._coverage(all_skills)
        # A simulação altera apenas a cobertura; mantém o texto do perfil constante.
        scores = (0.65 * after + 0.35 * similarity) * 100
        ranked = sorted(indices, key=lambda i: (-scores[i], self.jobs[i]['id']))
        matches = []
        for i in ranked[:limit]:
            job = self.jobs[i]
            matches.append({**job, 'description': job['description'][:1200],
                'score': round(float(scores[i]), 1), 'coverage': round(float(after[i]) * 100, 1),
                'text_similarity': round(float(similarity[i]) * 100, 1),
                'matched': [s for s in job['skills'] if s in all_skills],
                'missing': [s for s in job['skills'] if s not in all_skills],
                'cluster': int(self.labels[i])})
        candidates = []
        # Mesma população antes/depois. Somente vagas com skills extraídas entram na média.
        assessed = [i for i in indices if self.denominators[i] > 0]
        for skill in SKILLS:
            if skill in all_skills:
                continue
            relevant = [i for i in assessed if skill in self.jobs[i]['skills']]
            if not relevant:
                continue
            potential = self._coverage(all_skills + [skill])
            gain = float(np.mean(potential[assessed] - after[assessed])) * 100
            candidates.append({'skill': skill, 'jobs': len(relevant), 'gain': round(gain, 2), **learning_item(skill)})
        candidates.sort(key=lambda item: (-item['gain'], -item['jobs'], item['skill']))
        return {'detected_skills': detected, 'extra_skills': extras, 'matches': matches,
                'total': len(indices), 'assessed': len(assessed), 'has_text_signal': bool(q.nnz),
                'plan': candidates[:6], 'simulation': {
                    'before': round(float(np.mean(before[assessed])) * 100, 1) if assessed else 0,
                    'after': round(float(np.mean(after[assessed])) * 100, 1) if assessed else 0,
                    'above80_before': int(np.sum(before[assessed] >= .8)),
                    'above80_after': int(np.sum(after[assessed] >= .8)),
                }}
