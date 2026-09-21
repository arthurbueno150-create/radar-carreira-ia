"""Experimento supervisionado auxiliar, com teste separado por empresa."""
from collections import Counter
import numpy as np
from sklearn.dummy import DummyClassifier
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score, f1_score, confusion_matrix, classification_report
from sklearn.model_selection import GroupShuffleSplit
from sklearn.pipeline import Pipeline
from threadpoolctl import threadpool_limits


def evaluate_categories(jobs):
    texts = [j['title'] + ' ' + j['description'] for j in jobs]
    labels = np.array([j['category'] for j in jobs])
    groups = np.array([j['company'].casefold().strip() for j in jobs])
    train, test = next(GroupShuffleSplit(n_splits=1, test_size=.25, random_state=42).split(texts, labels, groups))
    train_companies, test_companies = set(groups[train]), set(groups[test])
    if len(set(labels[train])) < 2 or len(set(labels[test])) < 2:
        return {'status': 'Amostra insuficiente para avaliar ambas as categorias neste particionamento.'}
    classifier = Pipeline([
        ('tfidf', TfidfVectorizer(stop_words='english', ngram_range=(1, 2), min_df=2,
                                  max_features=12000, sublinear_tf=True)),
        ('classifier', LogisticRegression(C=2, class_weight='balanced', max_iter=1000, random_state=42)),
    ])
    with threadpool_limits(limits=1):
        classifier.fit([texts[i] for i in train], labels[train])
        prediction = classifier.predict([texts[i] for i in test])
    baseline = DummyClassifier(strategy='most_frequent').fit(np.zeros((len(train), 1)), labels[train])
    dummy_prediction = baseline.predict(np.zeros((len(test), 1)))
    classes = sorted(set(labels))
    def measures(pred):
        return {'accuracy': round(float(accuracy_score(labels[test], pred)), 4),
                'macro_f1': round(float(f1_score(labels[test], pred, average='macro', zero_division=0)), 4)}
    return {
        'task': 'Prever a categoria atribuída pelo Jobicy a partir do título e da descrição.',
        'split': 'GroupShuffleSplit: 25% das empresas no teste, random_state=42.',
        'train_rows': len(train), 'test_rows': len(test),
        'train_companies': len(train_companies), 'test_companies': len(test_companies),
        'company_overlap': len(train_companies & test_companies),
        'train_distribution': dict(Counter(labels[train])), 'test_distribution': dict(Counter(labels[test])),
        'model': measures(prediction), 'baseline': measures(dummy_prediction),
        'classes': classes, 'confusion_matrix': confusion_matrix(labels[test], prediction, labels=classes).tolist(),
        'classification_report': classification_report(labels[test], prediction, labels=classes, output_dict=True, zero_division=0),
        'limitations': 'Experimento auxiliar em um único split. As métricas medem reprodução das categorias da fonte, não qualidade das recomendações ou probabilidade de contratação. O vocabulário TF-IDF é ajustado somente no treino deste experimento.',
    }
