"""Inicializador portátil: cria ambiente isolado apenas na primeira execução."""
from pathlib import Path
import os
import subprocess
import sys

ROOT = Path(__file__).resolve().parent
ENV = ROOT / '.venv'
PYTHON = ENV / ('Scripts/python.exe' if os.name == 'nt' else 'bin/python')


def main():
    if sys.version_info < (3, 12):
        raise SystemExit('Instale Python 3.12 ou superior em https://www.python.org/downloads/')
    if not PYTHON.exists():
        print('Preparando o ambiente Python isolado...', flush=True)
        subprocess.run([sys.executable, '-m', 'venv', str(ENV)], check=True)
    stamp = ENV / '.radar-installed'
    requirements = (ROOT / 'requirements.txt').read_text(encoding='utf-8')
    if not stamp.exists() or stamp.read_text(encoding='utf-8') != requirements:
        print('Instalando dependências. Esta etapa usa internet e só é necessária na primeira execução.', flush=True)
        subprocess.run([str(PYTHON), '-m', 'pip', 'install', '-r', str(ROOT / 'requirements.txt')], check=True)
        stamp.write_text(requirements, encoding='utf-8')
    subprocess.run([str(PYTHON), str(ROOT / 'app.py'), '--open'], cwd=ROOT, check=True)


if __name__ == '__main__':
    try:
        main()
    except subprocess.CalledProcessError as error:
        print(f'Não foi possível iniciar (código {error.returncode}). Confira a conexão e se a porta 8765 está livre.')
        raise SystemExit(1)
