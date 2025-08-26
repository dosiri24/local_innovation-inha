import json
import os
from functools import lru_cache
from typing import Any, Dict, Optional

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
I18N_DIR = os.path.join(BASE_DIR, '..', 'data', 'i18n')

SUPPORTED_LANGS = ['ko', 'en', 'zh', 'ja']

@lru_cache(maxsize=16)
def _load_lang(lang: str) -> Dict[str, Any]:
    path = os.path.join(I18N_DIR, f"{lang}.json")
    if not os.path.exists(path):
        return {}
    try:
        with open(path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception:
        return {}

def _get(data: Dict[str, Any], key: str) -> Optional[str]:
    cur: Any = data
    for part in key.split('.'):
        if isinstance(cur, dict) and part in cur:
            cur = cur[part]
        else:
            return None
    return cur if isinstance(cur, str) else None

def translate(lang: str, key: str, default: Optional[str] = None) -> str:
    """Translate a dot-notated key with fallback to Korean and default/key.

    - lang: current language code
    - key: dot path (e.g., 'index.title')
    - default: optional default string to use if not found
    """
    lang = (lang or 'ko').lower()
    # Primary language
    val = _get(_load_lang(lang), key)
    if val:
        return val
    # Fallback to Korean dictionary
    if lang != 'ko':
        val = _get(_load_lang('ko'), key)
        if val:
            return val
    # Fallback to provided default or the key itself
    return default if default is not None else key

