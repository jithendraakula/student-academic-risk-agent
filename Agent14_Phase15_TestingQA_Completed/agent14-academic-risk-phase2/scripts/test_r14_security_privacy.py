"""R14 security/privacy gate for production-facing defaults and AI data boundaries."""
from __future__ import annotations

import os
import re
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def assert_true(cond: bool, msg: str) -> None:
    if not cond:
        raise AssertionError(msg)


def test_config_defaults() -> None:
    text = (ROOT / "backend/app/core/config.py").read_text(encoding="utf-8")
    assert_true('"false" if ENVIRONMENT == "production" else "true"' in text, "production docs should default off")
    assert_true('AI_INCLUDE_STUDENT_IDENTIFIERS = os.getenv("AI_INCLUDE_STUDENT_IDENTIFIERS", "false")' in text, "AI identifier sharing must default off")
    assert_true('AI_ALLOWED_EXTERNAL_DATA = os.getenv("AI_ALLOWED_EXTERNAL_DATA", "false")' in text, "AI data policy flag missing")


def test_gitignore() -> None:
    text = (ROOT / ".gitignore").read_text(encoding="utf-8")
    for required in [".env\n", "*.db\n", "__pycache__/", "node_modules/"]:
        assert_true(required in text, f"missing gitignore rule: {required!r}")
    assert_true("!.env.example" in text, ".env.example must remain shareable")


def test_ai_deidentification() -> None:
    text = (ROOT / "backend/app/services/ai.py").read_text(encoding="utf-8")
    assert_true("if AI_INCLUDE_STUDENT_IDENTIFIERS:" in text, "AI identifier gate missing")
    assert_true('"student_identifiers_sent_to_provider": AI_INCLUDE_STUDENT_IDENTIFIERS' in text, "AI privacy telemetry missing")
    assert_true('"case_reference"' in text, "de-identified case reference missing")


def test_no_obvious_secrets() -> None:
    patterns = [re.compile(r"AIza[0-9A-Za-z_-]{20,}"), re.compile(r"xai-[A-Za-z0-9_-]{20,}"), re.compile(r"sk-[A-Za-z0-9_-]{20,}")]
    excluded = {"package-lock.json"}
    hits = []
    for base in [ROOT / "backend", ROOT / "frontend", ROOT / "ml", ROOT / "scripts"]:
        for path in base.rglob("*"):
            if not path.is_file() or path.name in excluded or path.suffix not in {".py", ".ts", ".tsx", ".js", ".jsx", ".json", ".md", ".yml", ".yaml", ".env.example"}:
                continue
            try:
                text = path.read_text(encoding="utf-8", errors="ignore")
            except OSError:
                continue
            for pattern in patterns:
                if pattern.search(text):
                    hits.append(str(path))
                    break
    assert_true(not hits, f"possible API-key material found: {hits}")



def test_production_policy():
    env = os.environ.copy()
    env.update({
        "ENVIRONMENT": "production",
        "JWT_SECRET": "a-very-long-test-secret-for-r14-production-policy",
        "ALLOWED_ORIGINS": "https://example.test",
        "TRUSTED_HOSTS": "example.test",
        "JWT_EXPIRE_MINUTES": "60",
        "AI_INCLUDE_STUDENT_IDENTIFIERS": "false",
        "AI_ALLOWED_EXTERNAL_DATA": "false",
        "DATABASE_URL": "postgresql+psycopg://user:password@localhost:5432/agent14",
    })
    code = "from app.core.config import ENABLE_DOCS, AI_INCLUDE_STUDENT_IDENTIFIERS; assert ENABLE_DOCS is False; assert AI_INCLUDE_STUDENT_IDENTIFIERS is False; print('production policy ok')"
    result = subprocess.run(["python", "-c", code], cwd=ROOT / "backend", env=env, capture_output=True, text=True)
    assert_true(result.returncode == 0, result.stderr or "production config import failed")

    env["AI_INCLUDE_STUDENT_IDENTIFIERS"] = "true"
    result = subprocess.run(["python", "-c", "import app.core.config"], cwd=ROOT / "backend", env=env, capture_output=True, text=True)
    assert_true(result.returncode != 0 and "AI_INCLUDE_STUDENT_IDENTIFIERS" in result.stderr, "production AI identifier sharing must require explicit external-data approval")

def test_python_compile() -> None:
    result = subprocess.run(["python", "-m", "compileall", "-q", "backend/app", "scripts", "ml"], cwd=ROOT, capture_output=True, text=True)
    assert_true(result.returncode == 0, result.stderr or "compileall failed")


if __name__ == "__main__":
    for fn in [test_config_defaults, test_gitignore, test_ai_deidentification, test_no_obvious_secrets, test_production_policy, test_python_compile]:
        fn()
        print(f"PASS: {fn.__name__}")
    print("R14 security/privacy gate passed")
