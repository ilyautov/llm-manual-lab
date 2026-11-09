"""Remove ReportLab's unused Helvetica selections from the final PDF.

ReportLab emits empty ``BT /F... 10 Tf 12 TL ET`` operations while drawing
tables and the table of contents. They add an unembedded Helvetica resource,
although every visible glyph is set in the embedded project fonts. Refuse to
remove the resource if Helvetica ever appears in a real text operation.
"""

from __future__ import annotations

import re
from pathlib import Path

from pypdf import PdfReader, PdfWriter
from pypdf.generic import DecodedStreamObject, NameObject


def remove_unused_helvetica(path: Path) -> None:
    reader = PdfReader(path)
    writer = PdfWriter()
    writer.clone_document_from_reader(reader)
    helvetica_keys = {
        key
        for page in writer.pages
        for key, font_ref in page['/Resources']['/Font'].get_object().items()
        if str(font_ref.get_object().get('/BaseFont')) == '/Helvetica'
    }
    removed = 0
    for page in writer.pages:
        fonts = page['/Resources']['/Font'].get_object()
        content = page.get_contents().get_data()
        for key in helvetica_keys:
            token = str(key).encode('ascii')
            empty_selection = b'BT ' + token + b' 10 Tf 12 TL ET'
            uses = len(re.findall(re.escape(token) + rb'(?![+\w])', content))
            empty_uses = content.count(empty_selection)
            if uses != empty_uses:
                raise ValueError(f'Helvetica has visible or unexpected uses: {path}')
            content = content.replace(empty_selection, b'')
            fonts.pop(key, None)
            removed += empty_uses
        stream = DecodedStreamObject()
        stream.set_data(content)
        page[NameObject('/Contents')] = writer._add_object(stream)
    if not removed:
        raise ValueError(f'No unused Helvetica selections found: {path}')
    temporary = path.with_suffix('.cleaned.pdf')
    try:
        with temporary.open('wb') as target:
            writer.write(target)
        temporary.replace(path)
    finally:
        temporary.unlink(missing_ok=True)
