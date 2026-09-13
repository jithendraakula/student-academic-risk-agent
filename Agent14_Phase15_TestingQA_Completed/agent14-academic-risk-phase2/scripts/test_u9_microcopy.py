from pathlib import Path

ROOT = Path(__file__).resolve().parents[1] / 'frontend' / 'src'
FILES = list(ROOT.rglob('*.tsx')) + list(ROOT.rglob('*.ts'))
TEXT = '\n'.join(p.read_text(encoding='utf-8', errors='ignore') for p in FILES)
FORBIDDEN = [
    'risk_predictions', 'canonical alert policy', 'Backend provider',
    'Faculty-only · academic support workflow', 'grounded in canonical data',
    'canonical ML', 'ML Predict', 'Priority Act', 'Mentor Support',
    'Current academic cycle', 'No factor supplied', 'Swipe horizontally',
    'Recommended:',
]
for needle in FORBIDDEN:
    assert needle not in TEXT, f'Unwanted UI copy remains: {needle}'
mentor = (ROOT / 'pages' / 'mentor' / 'Dashboard.tsx').read_text(encoding='utf-8')
for needle in ['need attention', 'Open case', 'Risk', 'Priority', 'Next step']:
    assert needle in mentor, f'Core faculty wording missing: {needle}'
print(f'U9 microcopy gate PASS ({len(FILES)} TS/TSX files)')
