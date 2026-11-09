"""Inspect actual cl100k_base token IDs and raw token bytes.

Optional dependency: python3 -m pip install tiktoken==0.14.0
"""

import json
import sys

try:
    import tiktoken
except ImportError as error:
    raise SystemExit('Установите tiktoken: python3 -m pip install tiktoken==0.14.0') from error


encoding = tiktoken.get_encoding('cl100k_base')
samples = sys.argv[1:] or [
    'Сколько оплаченных заказов было 1 марта 2025 года?',
    'How many paid orders were there on March 1, 2025?',
    'аромадиффузор',
]

for sample in samples:
    token_ids = encoding.encode(sample)
    pieces = []
    for token_id in token_ids:
        raw = encoding.decode_single_token_bytes(token_id)
        pieces.append({
            'id': token_id,
            'bytes_hex': raw.hex(),
            'utf8_piece': raw.decode('utf-8', errors='replace'),
        })
    print(json.dumps({
        'text': sample,
        'encoding': encoding.name,
        'token_count': len(token_ids),
        'pieces': pieces,
        'round_trip_exact': encoding.decode(token_ids) == sample,
    }, ensure_ascii=False, indent=2))
