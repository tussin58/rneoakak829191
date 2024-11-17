import re

async def escape_md(text) -> str:
    if not text:
        return ''

    escape_chars = r'_*`'
    return re.sub(r'([{}])'.format(re.escape(escape_chars)), r'\\\1', text)