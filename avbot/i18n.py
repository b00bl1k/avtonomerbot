import gettext
import logging
import os
import threading

from babel.support import LazyProxy

logger = logging.getLogger(__name__)
translations = {}
tls = threading.local()


def gettext_translate(s):
    return tls.translate(s)


def lazy_gettext(s):
    return LazyProxy(gettext_translate, s=s, enable_cache=False)


_ = gettext_translate
__ = lazy_gettext


def gettext_getfunc(lang):
    def tr(message):
        if lang not in translations:
            return message
        return translations[lang].gettext(message)
    return tr


def load_translations(path, domain="avbot"):
    for name in os.listdir(path):
        if not os.path.isdir(os.path.join(path, name)):
            continue
        mo_path = os.path.join(path, name, "LC_MESSAGES", domain + ".mo")
        if os.path.exists(mo_path):
            with open(mo_path, "rb") as fp:
                translations[name] = gettext.GNUTranslations(fp)
                logger.info(f"Loaded translation '{name}'")


def setup_locale(lang="en"):
    tls.translate = gettext_getfunc(lang)
    tls.lang = lang


def get_current_lang():
    return tls.lang
