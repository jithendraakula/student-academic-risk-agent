from __future__ import annotations

import os
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def main() -> None:
    req = (ROOT / 'backend' / 'requirements.txt').read_text()
    assert 'psycopg[binary]' in req, 'PostgreSQL driver missing from backend requirements'

    env_example = (ROOT / 'backend' / '.env.example').read_text()
    assert 'JWT_SECRET=replace-with-a-long-random-secret' in env_example
    assert 'AI_API_KEY=' in env_example
    assert 'SMTP_PASSWORD=' in env_example

    fe_example = ROOT / 'frontend' / '.env.example'
    assert fe_example.exists(), 'frontend/.env.example missing'
    assert 'VITE_API_BASE_URL=' in fe_example.read_text()

    gitignore = (ROOT / '.gitignore').read_text()
    for entry in ['.env', '.venv', 'venv', 'node_modules', '__pycache__']:
        assert entry in gitignore, f'missing gitignore protection: {entry}'
    assert '*.py[cod]' in gitignore or '*.pyc' in gitignore, 'missing Python bytecode protection'

    vite = (ROOT / 'frontend' / 'vite.config.ts').read_text()
    assert 'VITE_API_BASE_URL must be configured for production builds' in vite

    config = (ROOT / 'backend' / 'app' / 'core' / 'config.py').read_text()
    assert 'DATABASE_URL must use PostgreSQL with psycopg in production' in config
    assert 'JWT_SECRET must be configured in production' in config
    assert 'ENABLE_DOCS' in config

    readme = (ROOT / 'README.md').read_text()
    assert 'demo password: `demo`' in readme
    assert 'Remediation R15' in readme

    # Syntax smoke checks for the deployment-sensitive config files.
    subprocess.run(['python', '-m', 'py_compile', str(ROOT / 'backend' / 'app' / 'core' / 'config.py')], check=True)

    # Ensure production config fails closed without touching the user's environment.
    env = os.environ.copy()
    env.update({
        'ENVIRONMENT': 'production',
        'JWT_SECRET': 'changeme-in-production',
        'DATABASE_URL': 'sqlite:///forbidden.db',
        'ALLOWED_ORIGINS': 'https://example.edu',
        'TRUSTED_HOSTS': 'api.example.edu',
    })
    cmd = [
        'python', '-c',
        'import sys; sys.path.insert(0, "backend"); import app.core.config',
    ]
    result = subprocess.run(cmd, cwd=ROOT, env=env, capture_output=True, text=True)
    assert result.returncode != 0, 'production config did not fail closed for SQLite/default secret'

    print('R15 deployment readiness gate: PASS')


if __name__ == '__main__':
    main()
