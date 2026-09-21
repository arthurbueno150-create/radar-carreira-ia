"""Coleta manual; preserva a última base válida em caso de falha."""
from radar.data import refresh_snapshot

if __name__ == '__main__':
    try:
        result = refresh_snapshot()
    except Exception as error:
        raise SystemExit(f'Coleta não concluída: {error}')
    print(f"Coletadas {result['metadata']['count']} vagas. Execute python train.py e reinicie o app.")
