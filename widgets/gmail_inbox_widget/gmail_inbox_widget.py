"""
Gmail Inbox Widget for Imolia Desktop Customizer

Toont van meerdere Gmail-adressen tegelijk het aantal ongelezen mails en de
nieuwste ongelezen berichten. Controleert elke X minuten op nieuwe mail.
Een klik op een adres of bericht opent dat account/bericht in je
standaardbrowser. Berichten kunnen als gelezen worden gemarkeerd of naar de
prullenbak worden verplaatst.

Inloggen gaat via IMAP met een Google "app-wachtwoord" per account
(https://myaccount.google.com/apppasswords). De wachtwoorden worden met
Windows DPAPI versleuteld opgeslagen: alleen jouw Windows-gebruiker kan ze lezen.

Dependencies:
PyQt5==5.15.6

"""

import base64
import copy
import ctypes
import json
import logging
import os
import re
import socket
import sys
import threading
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime
from email import policy
from email.parser import BytesHeaderParser, BytesParser
from html import escape as html_escape, unescape as html_unescape

# html.parser staat in een met PyInstaller gebouwde app alleen als hij in de .spec bij
# hiddenimports staat. Ontbreekt hij (oudere build), dan laadt de widget gewoon en worden
# mails met opmaak als gewone tekst getoond in plaats van dat de hele widget niet start.
try:
    from html.parser import HTMLParser
    _HAS_HTML_PARSER = True
except ImportError:
    HTMLParser = object
    _HAS_HTML_PARSER = False
from email.utils import parsedate_to_datetime
from urllib.parse import quote

from PyQt5.QtCore import Qt, QObject, QPointF, QRectF, QTimer, QUrl, pyqtSignal
from PyQt5.QtGui import (QColor, QDesktopServices, QFont, QFontMetrics, QPainter)
from PyQt5.QtWidgets import (QApplication, QCheckBox, QColorDialog, QComboBox, QDialog, QDoubleSpinBox,
                             QFileDialog, QFormLayout, QGroupBox, QHBoxLayout, QLabel, QLineEdit,
                             QListWidget, QMessageBox, QPushButton, QSpinBox, QTextBrowser, QVBoxLayout)
from src.utils.draggable_widget import DraggableWidget, WidgetSettingsDialog

logger = logging.getLogger('DesktopCustomizer.GmailInboxWidget')

# Een met PyInstaller gebouwde app bevat imaplib alleen als hij in de .spec
# bij hiddenimports staat. Ontbreekt hij, dan laden we de widget toch en tonen
# we een duidelijke melding in plaats van dat de hele widget niet start.
try:
    import imaplib
except ImportError:
    imaplib = None

IMAP_HOST = 'imap.gmail.com'
IMAP_PORT = 993
APP_PASSWORD_URL = 'https://myaccount.google.com/apppasswords'

GMAIL_RED = '#ea4335'
AVATAR_COLORS = ['#2f80c0', '#2c3e50', '#2ecc71', '#9b59b6', '#3498db', '#27ae60', '#e67e22', '#8e5bb5']
MONTHS = ['jan', 'feb', 'mrt', 'apr', 'mei', 'jun', 'jul', 'aug', 'sep', 'okt', 'nov', 'dec']

HEADER_H = 44
ACCOUNT_H = 36
MAIL_H = 42
NOTE_H = 24
PAD = 10
FLASH_SECONDS = 15
READER_META_H = 40       # hoogte van het afzender/datum-blok boven een geopende mail

WINDOWS_MEDIA_DIR = os.path.join(os.environ.get('SystemRoot', r'C:\Windows'), 'Media')


def list_windows_sounds():
    """[(weergavenaam, pad)] van alle .wav-geluiden die Windows zelf meelevert."""
    try:
        names = sorted(f for f in os.listdir(WINDOWS_MEDIA_DIR) if f.lower().endswith('.wav'))
    except OSError:
        return []
    return [(os.path.splitext(f)[0], os.path.join(WINDOWS_MEDIA_DIR, f)) for f in names]


def _default_sound():
    path = os.path.join(WINDOWS_MEDIA_DIR, 'Windows Notify Email.wav')
    return path if os.path.isfile(path) else ''  # '' = gewone Windows-pieptoon


def play_notification_sound(path):
    """Speel een .wav-bestand af zonder de widget te blokkeren. Zonder (geldig)
    bestand klinkt de standaard Windows-pieptoon."""
    try:
        import winsound
        if path and path.lower().endswith('.wav') and os.path.isfile(path):
            winsound.PlaySound(path, winsound.SND_FILENAME | winsound.SND_ASYNC | winsound.SND_NODEFAULT)
        else:
            winsound.MessageBeep(winsound.MB_ICONASTERISK)
    except Exception:
        QApplication.beep()


DEFAULT_CONFIG = {
    'accounts': [],              # [{'email': ..., 'password': 'dpapi:...'}]
    'check_interval_minutes': 2,
    'max_messages': 5,           # aantal ongelezen berichten per account in de lijst
    'mark_read_on_open': True,   # een mail telt als gelezen zodra je hem opent (zoals in Gmail zelf)
    'notify_sound': True,
    'sound_file': _default_sound(),   # pad naar een .wav; leeg = Windows-pieptoon
    'muted': False,              # "niet storen": geen geluid en geen knipperen
    'color': '#ffffff',
    'bg_opacity': 100,           # procent
    'size': (360, 340),
    'position': (780, 100),
}


def config_path():
    return os.path.join(os.path.dirname(os.path.abspath(__file__)), 'gmail_inbox_widget_config.json')


# --------------------------------------------------------------------------
# Wachtwoorden versleutelen met Windows DPAPI (geen extra pakketten nodig)
# --------------------------------------------------------------------------

if sys.platform == 'win32':
    from ctypes import wintypes

    class _DataBlob(ctypes.Structure):
        _fields_ = [('cbData', wintypes.DWORD), ('pbData', ctypes.POINTER(ctypes.c_char))]

    # Eigen WinDLL-exemplaren, niet ctypes.windll.crypt32: dat object wordt door alle widgets
    # gedeeld, en elke widget zet er zijn eigen argtypes op. Zijn er twee widgets met DPAPI
    # actief (Gmail Inbox én LLM Chat), dan overschrijven ze elkaars instellingen en geeft
    # de tweede "expected LP__DataBlob instance" bij het versleutelen.
    _crypt32 = ctypes.WinDLL('crypt32')
    _kernel32 = ctypes.WinDLL('kernel32')
    _crypt32.CryptProtectData.argtypes = [
        ctypes.POINTER(_DataBlob), wintypes.LPCWSTR, ctypes.POINTER(_DataBlob),
        ctypes.c_void_p, ctypes.c_void_p, wintypes.DWORD, ctypes.POINTER(_DataBlob)]
    _crypt32.CryptProtectData.restype = wintypes.BOOL
    _crypt32.CryptUnprotectData.argtypes = [
        ctypes.POINTER(_DataBlob), ctypes.c_void_p, ctypes.POINTER(_DataBlob),
        ctypes.c_void_p, ctypes.c_void_p, wintypes.DWORD, ctypes.POINTER(_DataBlob)]
    _crypt32.CryptUnprotectData.restype = wintypes.BOOL
    _kernel32.LocalFree.argtypes = [ctypes.c_void_p]
    _kernel32.LocalFree.restype = ctypes.c_void_p

    def _blob_in(data):
        buffer = ctypes.create_string_buffer(data, len(data))
        return _DataBlob(len(data), ctypes.cast(buffer, ctypes.POINTER(ctypes.c_char))), buffer


def encrypt_password(plain):
    data = plain.encode('utf-8')
    if sys.platform != 'win32':
        # Alleen Windows heeft DPAPI. Elders valt dit terug op base64: dat is
        # géén echte beveiliging, maar de widget is gemaakt voor Windows.
        return 'b64:' + base64.b64encode(data).decode('ascii')
    blob_in, _keep_alive = _blob_in(data)
    blob_out = _DataBlob()
    if not _crypt32.CryptProtectData(ctypes.byref(blob_in), 'Imolia Gmail Widget', None, None, None, 0,
                                     ctypes.byref(blob_out)):
        raise ctypes.WinError()
    try:
        return 'dpapi:' + base64.b64encode(ctypes.string_at(blob_out.pbData, blob_out.cbData)).decode('ascii')
    finally:
        _kernel32.LocalFree(blob_out.pbData)


def decrypt_password(token):
    kind, _, payload = (token or '').partition(':')
    raw = base64.b64decode(payload)
    if kind == 'b64':
        return raw.decode('utf-8')
    if kind != 'dpapi' or sys.platform != 'win32':
        raise ValueError('Onbekend wachtwoordformaat')
    blob_in, _keep_alive = _blob_in(raw)
    blob_out = _DataBlob()
    if not _crypt32.CryptUnprotectData(ctypes.byref(blob_in), None, None, None, None, 0, ctypes.byref(blob_out)):
        raise ctypes.WinError()
    try:
        return ctypes.string_at(blob_out.pbData, blob_out.cbData).decode('utf-8')
    finally:
        _kernel32.LocalFree(blob_out.pbData)


# --------------------------------------------------------------------------
# Gmail via IMAP
# --------------------------------------------------------------------------

def account_label(account):
    """De naam waaronder een account in de widget verschijnt: de zelfgekozen naam,
    en alleen zonder naam het e-mailadres. Zo hoeft een bezoeker geen adressen te zien."""
    return (account.get('name') or '').strip() or account['email']


def gmail_url(address, thread_id_hex=None):
    """Link die Gmail opent bij het juiste account (en eventueel direct bij één gesprek)."""
    url = f"https://mail.google.com/mail/?authuser={quote(address)}"
    if thread_id_hex:
        url += f"#inbox/{thread_id_hex}"
    return url


def friendly_error(exc):
    text = str(exc)
    lowered = text.lower()
    if imaplib is not None and isinstance(exc, imaplib.IMAP4.error):
        if 'authenticationfailed' in lowered or 'invalid credentials' in lowered \
                or 'application-specific password' in lowered:
            return 'Inloggen mislukt - controleer het adres en het app-wachtwoord'
        if 'web login' in lowered:
            return 'Google vraagt een webinlog - log in via de browser en probeer opnieuw'
        return f'IMAP-fout: {text}'
    if isinstance(exc, (socket.timeout, TimeoutError)):
        return 'Geen antwoord van Gmail (time-out)'
    if isinstance(exc, OSError):
        return 'Geen verbinding met Gmail'
    return f'Fout: {text}'


_UID_RE = re.compile(rb'UID (\d+)')
_THRID_RE = re.compile(rb'X-GM-THRID (\d+)')


def _sender_name(message):
    try:
        header = message['From']
        addresses = getattr(header, 'addresses', None)
        if addresses:
            return addresses[0].display_name or addresses[0].addr_spec
        return str(header) if header else '(onbekend)'
    except Exception:
        return str(message.get('From', '(onbekend)'))


def parse_fetch_response(data):
    """Zet het antwoord van `UID FETCH (X-GM-THRID BODY.PEEK[HEADER.FIELDS (...)])` om in berichten (nieuwste eerst)."""
    messages = []
    for item in data:
        if not isinstance(item, tuple) or len(item) < 2:
            continue
        meta, header_bytes = item[0], item[1]
        uid = _UID_RE.search(meta)
        if not uid:
            continue
        thread = _THRID_RE.search(meta)
        try:
            parsed = BytesHeaderParser(policy=policy.default).parsebytes(header_bytes)
            subject = str(parsed['Subject'] or '').strip() or '(geen onderwerp)'
            sender = _sender_name(parsed)
        except Exception:
            subject, sender, parsed = '(onleesbaar onderwerp)', '(onbekend)', None
        timestamp = None
        try:
            if parsed is not None and parsed['Date']:
                timestamp = parsedate_to_datetime(str(parsed['Date'])).timestamp()
        except Exception:
            pass
        messages.append({
            'uid': uid.group(1).decode(),
            'thrid': format(int(thread.group(1)), 'x') if thread else None,
            'sender': sender,
            'subject': subject,
            'timestamp': timestamp,
        })
    messages.sort(key=lambda m: int(m['uid']), reverse=True)
    return messages


def _connect(address, password, timeout=15):
    if imaplib is None:
        raise RuntimeError('Deze versie van de app bevat de module imaplib niet - bouw de app opnieuw '
                           '(imaplib staat nu in de .spec bij hiddenimports) of start hem vanuit de broncode')
    imap = imaplib.IMAP4_SSL(IMAP_HOST, IMAP_PORT, timeout=timeout)
    try:
        imap.login(address, password.replace(' ', ''))  # Google toont app-wachtwoorden met spaties
    except Exception:
        _close(imap)
        raise
    return imap


def _close(imap):
    try:
        imap.logout()
    except Exception:
        pass


def fetch_account(address, password, max_messages=5):
    """Haal aantal ongelezen mails en de nieuwste ongelezen berichten van één account op."""
    result = {'email': address, 'ok': False, 'error': None, 'unread': 0, 'messages': []}
    imap = None
    try:
        imap = _connect(address, password)
        status, _ = imap.select('INBOX', readonly=True)
        if status != 'OK':
            raise imaplib.IMAP4.error('Kan de inbox niet openen')
        status, data = imap.uid('SEARCH', None, 'UNSEEN')
        if status != 'OK':
            raise imaplib.IMAP4.error('Zoeken naar ongelezen mail mislukt')
        uids = data[0].split() if data and data[0] else []
        result['unread'] = len(uids)
        newest = uids[-max(1, int(max_messages)):]
        if newest:
            status, data = imap.uid('FETCH', b','.join(newest),
                                    '(X-GM-THRID BODY.PEEK[HEADER.FIELDS (FROM SUBJECT DATE)])')
            if status == 'OK':
                result['messages'] = parse_fetch_response(data)
        result['ok'] = True
    except Exception as e:
        result['error'] = friendly_error(e)
        logger.warning(f"Controleren van {address} mislukt: {result['error']}")
    finally:
        if imap:
            _close(imap)
    return result


def mail_action(address, password, uid, action):
    """Voer 'read' (als gelezen markeren) of 'trash' (naar prullenbak) uit op één bericht."""
    imap = _connect(address, password)
    try:
        status, _ = imap.select('INBOX')
        if status != 'OK':
            raise imaplib.IMAP4.error('Kan de inbox niet openen')
        if action == 'read':
            status, _ = imap.uid('STORE', uid, '+FLAGS', '(\\Seen)')
        elif action == 'trash':
            # Gmail-extensie: het label \Trash toevoegen verplaatst het bericht
            # naar de prullenbak, ongeacht de taal van de mapnaam.
            status, _ = imap.uid('STORE', uid, '+X-GM-LABELS', '(\\Trash)')
        else:
            raise ValueError(f'Onbekende actie: {action}')
        if status != 'OK':
            raise imaplib.IMAP4.error('Gmail weigerde de actie')
    finally:
        _close(imap)


# --------------------------------------------------------------------------
# Een mail lezen in de widget
# --------------------------------------------------------------------------

MAX_MESSAGE_BYTES = 2_000_000   # grotere mails worden afgekapt en zo getoond
MAX_RENDER_CHARS = 300_000      # zoveel tekst tonen we maximaal; meer laat de weergave vastlopen
_SIZE_RE = re.compile(rb'RFC822\.SIZE (\d+)')
_URL_RE = re.compile(r'https?://[^\s<>"\']+')

# Van een HTML-mail blijven alleen deze tags over. Andere tags verdwijnen (hun tekst
# blijft staan); script, stijl, frames en dergelijke verdwijnen mét inhoud. Afbeeldingen
# worden nooit geladen: dat voorkomt volgpixels en houdt het snel.
_ALLOWED_TAGS = {'a', 'b', 'strong', 'i', 'em', 'u', 's', 'br', 'hr', 'p', 'div', 'span', 'ul', 'ol', 'li',
                 'table', 'thead', 'tbody', 'tfoot', 'tr', 'td', 'th', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6',
                 'blockquote', 'pre', 'code', 'font', 'center', 'small', 'big', 'sup', 'sub'}
_VOID_TAGS = {'br', 'hr'}
_DROP_WITH_CONTENT = {'script', 'style', 'head', 'title', 'iframe', 'object', 'embed', 'svg', 'noscript',
                      'template', 'select', 'textarea', 'button', 'math'}
_ALLOWED_ATTRS = {'href', 'colspan', 'rowspan', 'align', 'valign', 'width', 'height', 'bgcolor', 'color',
                  'size', 'face', 'style', 'border', 'cellpadding', 'cellspacing'}
_SAFE_LINKS = ('http://', 'https://', 'mailto:')
_UNSAFE_STYLE_RE = re.compile(r'url\s*\(|expression|javascript|behavior|@import', re.IGNORECASE)


def _clean_style(value):
    declarations = [d.strip() for d in value.split(';') if d.strip()]
    return '; '.join(d for d in declarations if not _UNSAFE_STYLE_RE.search(d))


class _HtmlSanitizer(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.out = []
        self._dropping = []  # stapel van tags waarvan de inhoud wordt weggegooid

    def handle_starttag(self, tag, attrs):
        if tag in _DROP_WITH_CONTENT:
            self._dropping.append(tag)
            return
        if self._dropping:
            return
        if tag == 'img':
            alt = (dict(attrs).get('alt') or '').strip()
            self.out.append(f"<i>[{html_escape(alt) if alt else 'afbeelding'}]</i>")
            return
        if tag not in _ALLOWED_TAGS:
            return
        parts = []
        for name, value in attrs:
            name = (name or '').lower()
            value = value or ''
            if name not in _ALLOWED_ATTRS:
                continue
            if name == 'href' and not value.strip().lower().startswith(_SAFE_LINKS):
                continue
            if name == 'style':
                value = _clean_style(value)
                if not value:
                    continue
            parts.append(f' {name}="{html_escape(value, quote=True)}"')
        self.out.append(f"<{tag}{''.join(parts)}>")

    def handle_endtag(self, tag):
        if self._dropping:
            if tag == self._dropping[-1]:
                self._dropping.pop()
            return
        if tag in _ALLOWED_TAGS and tag not in _VOID_TAGS:
            self.out.append(f"</{tag}>")

    def handle_data(self, data):
        if not self._dropping:
            self.out.append(html_escape(data))


def _html_to_text(html):
    """Noodoplossing zonder html.parser: haal de tekst uit een HTML-mail."""
    html = re.sub(r'(?is)<(script|style|head|title|iframe|object|embed|svg|noscript)\b.*?</\1\s*>', '', html)
    html = re.sub(r'(?i)<br\s*/?>|</(p|div|tr|li|h[1-6]|table|blockquote)>', '\n', html)
    text = html_unescape(re.sub(r'(?s)<[^>]*>', '', html))
    return re.sub(r'\n{3,}', '\n\n', text).strip()


def sanitize_html(html):
    """Maak van de HTML van een mail iets dat veilig in de widget getoond kan worden."""
    if not _HAS_HTML_PARSER:
        return text_to_html(_html_to_text(html))
    parser = _HtmlSanitizer()
    try:
        parser.feed(html)
        parser.close()
    except Exception:
        return f"<pre>{html_escape(html)}</pre>"
    return ''.join(parser.out)


def text_to_html(text):
    """Platte tekst netjes tonen, met aanklikbare links."""
    escaped = html_escape(text, quote=True)

    def link(match):
        url, tail = match.group(0), ''
        changed = True
        while changed:
            changed = False
            for suffix in ('&gt;', '&lt;', '&quot;', '&#x27;'):
                if url.endswith(suffix):
                    url, tail, changed = url[:-len(suffix)], suffix + tail, True
            while url and url[-1] in '.,;:!?)]}':
                url, tail, changed = url[:-1], url[-1] + tail, True
        return f'<a href="{url}">{url}</a>{tail}'

    return '<div style="white-space: pre-wrap;">' + _URL_RE.sub(link, escaped) + '</div>'


def _body_text(message, kind):
    try:
        part = message.get_body(preferencelist=(kind,))
    except Exception:
        part = None
    if part is None:
        return ''
    try:
        return part.get_content()
    except Exception:
        payload = part.get_payload(decode=True) or b''
        try:
            return payload.decode(part.get_content_charset() or 'utf-8', 'replace')
        except LookupError:
            return payload.decode('utf-8', 'replace')


def _format_full_date(value):
    try:
        moment = parsedate_to_datetime(str(value))
        if moment.tzinfo is not None:
            moment = moment.astimezone()
        return f"{moment.day} {MONTHS[moment.month - 1]} {moment.year} {moment:%H:%M}"
    except Exception:
        return ''


def parse_message(raw):
    """Zet de ruwe bytes van een mail om in wat de widget nodig heeft om hem te tonen."""
    message = BytesParser(policy=policy.default).parsebytes(raw)
    try:
        subject = str(message['subject'] or '').strip() or '(geen onderwerp)'
    except Exception:
        subject = '(onleesbaar onderwerp)'
    sender_name, sender_addr = '', ''
    try:
        addresses = getattr(message['From'], 'addresses', None)
        if addresses:
            sender_name, sender_addr = addresses[0].display_name, addresses[0].addr_spec
        elif message['From']:
            sender_name = str(message['From'])
    except Exception:
        sender_name = str(message.get('From', ''))
    attachments = []
    try:
        for part in message.iter_attachments():
            payload = part.get_payload(decode=True) or b''
            attachments.append({'name': part.get_filename() or part.get_content_type(), 'size': len(payload)})
    except Exception:
        pass
    return {
        'subject': subject,
        'sender_name': sender_name,
        'sender_addr': sender_addr,
        'date': _format_full_date(message['Date']) if message['Date'] else '',
        'text': _body_text(message, 'plain'),
        'html': _body_text(message, 'html'),
        'attachments': attachments,
    }


def fetch_message(address, password, uid, mark_read=True, max_bytes=MAX_MESSAGE_BYTES):
    """Haal één complete mail op om hem in de widget te lezen.

    BODY.PEEK haalt de mail op zonder hem als gelezen te markeren. Alleen als dat gelukt is
    en mark_read aan staat, markeren we hem daarna zelf als gelezen (net als Gmail dat doet
    zodra je een mail opent). De mail blijft gewoon in je inbox staan.
    """
    result = {'email': address, 'uid': str(uid), 'ok': False, 'error': None}
    imap = None
    try:
        imap = _connect(address, password)
        status, _ = imap.select('INBOX', readonly=not mark_read)
        if status != 'OK':
            raise imaplib.IMAP4.error('Kan de inbox niet openen')
        status, data = imap.uid('FETCH', str(uid), f'(RFC822.SIZE BODY.PEEK[]<0.{int(max_bytes)}>)')
        if status != 'OK':
            raise imaplib.IMAP4.error('Mail ophalen mislukt')
        body, size = None, None
        for item in data or []:
            if isinstance(item, tuple) and len(item) >= 2:
                body = item[1]
                found = _SIZE_RE.search(item[0])
                size = int(found.group(1)) if found else None
                break
        if body is None:
            raise imaplib.IMAP4.error('Deze mail bestaat niet meer (misschien al verwijderd)')
        result.update(parse_message(body))
        result['truncated'] = bool(size and size > len(body))
        result['size'] = size
        if mark_read:
            imap.uid('STORE', str(uid), '+FLAGS', '(\\Seen)')
        result['ok'] = True
    except Exception as e:
        result['error'] = friendly_error(e)
        logger.warning(f"Mail lezen voor {address} mislukt: {result['error']}")
    finally:
        if imap:
            _close(imap)
    return result

def format_mail_date(timestamp, now=None):
    if not timestamp:
        return ''
    moment = datetime.fromtimestamp(timestamp)
    today = (now or datetime.now()).date()
    days = (today - moment.date()).days
    if days == 0:
        return moment.strftime('%H:%M')
    if days == 1:
        return 'gisteren'
    return f"{moment.day} {MONTHS[moment.month - 1]}"


# --------------------------------------------------------------------------
# De widget
# --------------------------------------------------------------------------

class Bridge(QObject):
    result = pyqtSignal(dict)
    finished = pyqtSignal()
    action_done = pyqtSignal(str, bool, str)
    message_ready = pyqtSignal(str, str, dict)  # (adres, uid, resultaat van fetch_message)


class GmailInboxWidget(DraggableWidget):
    def __init__(self):
        super().__init__()
        self.config = self.load_config()
        self.states = {}
        self._hits = []
        self._hover = None
        self._press_global = None
        self._scroll = 0.0
        self._content_h = 0.0
        self._checking = False
        self._closing = False
        self._last_check = None
        self._message = None  # (tekst, tot-wanneer)
        self._reader = None   # de geopende mail, of None als de lijst getoond wordt
        self._sync_states()

        self.setMinimumSize(260, 120)
        self.resize(*self.config['size'])
        self.move(*self.config['position'])

        self.bridge = Bridge(self)
        self.bridge.result.connect(self._on_result)
        self.bridge.finished.connect(self._on_finished)
        self.bridge.action_done.connect(self._on_action_done)
        self.bridge.message_ready.connect(self._on_message_ready)

        # De tekst van een geopende mail staat in een echt tekstvak: dat regelt scrollen,
        # selecteren en kopieren. Links openen we zelf (en alleen http/https/mailto).
        self.reader_view = QTextBrowser(self)
        self.reader_view.setOpenLinks(False)
        self.reader_view.setFrameShape(QTextBrowser.NoFrame)
        self.reader_view.anchorClicked.connect(self._on_reader_link)
        self.reader_view.highlighted[QUrl].connect(self._on_reader_hover)
        self.reader_view.hide()

        self.check_timer = QTimer(self)
        self.check_timer.timeout.connect(self.check_all)
        self.check_timer.start(self._interval_ms())
        self.ui_timer = QTimer(self)  # ververst o.a. "bijgewerkt om ..." en het nieuwe-mail-effect
        self.ui_timer.timeout.connect(self.update)
        self.ui_timer.start(1000)
        QTimer.singleShot(1500, self.check_all)

    # -- configuratie -----------------------------------------------------

    def load_config(self):
        config = copy.deepcopy(DEFAULT_CONFIG)
        try:
            if os.path.exists(config_path()):
                with open(config_path(), 'r') as f:
                    config.update(json.load(f))
        except (OSError, ValueError) as e:
            logger.error(f"Kon configuratie van Gmail Inbox niet lezen: {e}")
        return config

    def save_config(self):
        try:
            with open(config_path(), 'w') as f:
                json.dump(self.config, f)
        except OSError as e:
            logger.error(f"Kon configuratie van Gmail Inbox niet opslaan: {e}")

    def updateConfig(self, new_config):
        self.config.update(new_config)
        self._sync_states()
        if self._reader and self._reader['key'] not in self.states:
            self._close_reader()  # het account van de geopende mail is verwijderd
        self.check_timer.setInterval(self._interval_ms())
        self.save_config()
        self.update()
        self.check_all()

    def openSettings(self):
        dialog = GmailSettingsDialog(self)
        if dialog.exec_():
            self.updateConfig(dialog.get_config())

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self.config['size'] = (self.width(), self.height())
        self.save_config()
        self._layout_reader()

    def moveEvent(self, event):
        super().moveEvent(event)
        self.config['position'] = (self.x(), self.y())
        self.save_config()

    def closeEvent(self, event):
        self._closing = True
        self.check_timer.stop()
        self.ui_timer.stop()
        super().closeEvent(event)

    def _interval_ms(self):
        return int(max(1, float(self.config.get('check_interval_minutes', 2))) * 60 * 1000)

    def _sync_states(self):
        wanted = [a['email'].lower() for a in self.config['accounts']]
        for key in list(self.states):
            if key not in wanted:
                del self.states[key]
        for key in wanted:
            self.states.setdefault(key, {'ok': None, 'error': None, 'unread': 0, 'messages': [],
                                         'expanded': False, 'last_uid': None, 'new_until': 0.0})

    # -- controleren ------------------------------------------------------

    def _emit(self, signal, *args):
        """Veilig vanuit een achtergrond-thread uitzenden, ook als de widget net is afgesloten."""
        try:
            signal.emit(*args)
        except RuntimeError:
            pass

    def _account_password(self, address):
        for account in self.config['accounts']:
            if account['email'].lower() == address.lower():
                return decrypt_password(account['password'])
        raise KeyError(address)

    def check_all(self):
        if self._checking or self._closing or not self.config['accounts']:
            return
        jobs = []
        for account in self.config['accounts']:
            try:
                jobs.append((account['email'], decrypt_password(account['password'])))
            except Exception:
                self._on_result({'email': account['email'], 'ok': False, 'unread': 0, 'messages': [],
                                 'error': 'Wachtwoord kan niet worden gelezen - voer het opnieuw in'})
        if not jobs:
            return
        self._checking = True
        threading.Thread(target=self._run_checks, args=(jobs, self.config.get('max_messages', 5)),
                         name='GmailInboxChecker', daemon=True).start()
        self.update()

    def _run_checks(self, jobs, max_messages):
        with ThreadPoolExecutor(max_workers=4) as pool:
            futures = [pool.submit(fetch_account, address, password, max_messages) for address, password in jobs]
            for future in as_completed(futures):
                self._emit(self.bridge.result, future.result())
        self._emit(self.bridge.finished)

    def _on_finished(self):
        self._checking = False
        self._last_check = datetime.now()
        self.update()

    def _on_result(self, result):
        state = self.states.get(result['email'].lower())
        if state is None:
            return
        state['ok'] = result['ok']
        state['error'] = result['error']
        if result['ok']:
            state['unread'] = result['unread']
            state['messages'] = result['messages']
            newest = max((int(m['uid']) for m in result['messages']), default=0)
            if state['last_uid'] is not None and newest > state['last_uid'] and not self.config.get('muted'):
                state['new_until'] = time.time() + FLASH_SECONDS
                self._notify_new_mail()
            if state['last_uid'] is None or newest > state['last_uid']:
                state['last_uid'] = newest
        self.update()

    def _notify_new_mail(self):
        if self.config.get('notify_sound', True) and not self.config.get('muted'):
            play_notification_sound(self.config.get('sound_file', ''))

    def _toggle_muted(self):
        self.config['muted'] = not self.config.get('muted', False)
        self.save_config()
        if self.config['muted']:
            for state in self.states.values():
                state['new_until'] = 0.0  # lopende knipper-effecten meteen stoppen
        self._show_message('Niet storen staat aan: geen geluid of knipperen' if self.config['muted']
                           else 'Niet storen staat uit')

    # -- acties op berichten ----------------------------------------------

    def _drop_from_list(self, address, uid):
        """Haal een bericht meteen uit de getoonde lijst. De controle erna corrigeert zo nodig."""
        state = self.states.get(address.lower())
        if not state:
            return
        before = len(state['messages'])
        state['messages'] = [m for m in state['messages'] if m['uid'] != uid]
        if len(state['messages']) != before:  # een al gelezen mail telt niet nog eens mee
            state['unread'] = max(0, state['unread'] - 1)

    def _do_action(self, address, uid, action):
        # Geen bevestiging bij de prullenbak: het bericht blijft 30 dagen in
        # Gmail's Prullenbak staan en is online altijd terug te halen.
        try:
            password = self._account_password(address)
        except Exception:
            self._show_message('Wachtwoord kan niet worden gelezen')
            return
        self._drop_from_list(address, uid)
        self.update()
        threading.Thread(target=self._run_action, args=(address, password, uid, action),
                         name='GmailInboxAction', daemon=True).start()

    def _run_action(self, address, password, uid, action):
        try:
            mail_action(address, password, uid, action)
            ok, text = True, 'Gemarkeerd als gelezen' if action == 'read' else 'Naar prullenbak verplaatst'
        except Exception as e:
            ok, text = False, friendly_error(e)
            logger.warning(f"Actie {action} op {address} mislukt: {text}")
        refreshed = fetch_account(address, password, self.config.get('max_messages', 5))
        self._emit(self.bridge.result, refreshed)
        self._emit(self.bridge.action_done, address, ok, text)

    def _on_action_done(self, address, ok, text):
        self._show_message(text if ok else f'Mislukt: {text}')

    def _show_message(self, text, seconds=6):
        self._message = (text, time.time() + seconds)
        self.update()

    # -- tekenen ----------------------------------------------------------

    @staticmethod
    def _font(px, bold=False, family='Segoe UI'):
        font = QFont(family)
        font.setPixelSize(int(px))
        font.setBold(bold)
        return font

    def _add_hit(self, rect, kind, payload=None, tooltip='', clip=None):
        area = rect.intersected(clip) if clip is not None else rect
        if area.width() > 0 and area.height() > 0:
            self._hits.append((area, kind, payload, tooltip))

    def _total_unread(self):
        return sum(s['unread'] for s in self.states.values() if s['ok'])

    def _row_rects(self, clip):
        rows = []
        y = clip.top() - self._scroll
        for account in self.config['accounts']:
            key = account['email'].lower()
            state = self.states[key]
            rows.append(('account', key, QRectF(clip.left(), y, clip.width(), ACCOUNT_H)))
            y += ACCOUNT_H + 4
            if not state['expanded']:
                continue
            if state['ok'] and not state['messages']:
                rows.append(('note', 'Geen ongelezen mail', QRectF(clip.left(), y, clip.width(), NOTE_H)))
                y += NOTE_H + 4
            for message in state['messages']:
                rows.append(('mail', (key, message), QRectF(clip.left() + 14, y, clip.width() - 14, MAIL_H)))
                y += MAIL_H + 3
            extra = state['unread'] - len(state['messages'])
            if state['ok'] and state['messages'] and extra > 0:
                rows.append(('more', (key, extra), QRectF(clip.left() + 14, y, clip.width() - 14, NOTE_H)))
                y += NOTE_H + 4
            y += 4
        self._content_h = y + self._scroll - clip.top()
        max_scroll = max(0.0, self._content_h - clip.height())
        self._scroll = min(max(self._scroll, 0.0), max_scroll)
        return rows

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        painter.setRenderHint(QPainter.TextAntialiasing)

        alpha = int(max(10, min(100, self.config.get('bg_opacity', 100))) / 100 * 255)
        painter.setPen(Qt.NoPen)
        painter.setBrush(QColor(20, 22, 28, alpha))
        painter.drawRoundedRect(QRectF(self.rect()), 12, 12)

        self._hits = []
        now = time.time()
        if self._reader:
            self._draw_reader(painter, now)
            painter.end()
            super().paintEvent(event)
            return
        self._draw_header(painter, now)

        clip = QRectF(PAD, HEADER_H, self.width() - 2 * PAD, self.height() - HEADER_H - PAD)
        if not self.config['accounts']:
            self._draw_empty(painter, clip)
        else:
            rows = self._row_rects(clip)
            painter.save()
            painter.setClipRect(clip)
            for kind, payload, rect in rows:
                if rect.bottom() < clip.top() or rect.top() > clip.bottom():
                    continue
                if kind == 'account':
                    self._draw_account(painter, rect, clip, payload, now)
                elif kind == 'mail':
                    self._draw_mail(painter, rect, clip, *payload)
                elif kind == 'more':
                    self._draw_note(painter, rect, f"+ {payload[1]} meer in Gmail", clip, ('open_inbox', payload[0]))
                else:
                    self._draw_note(painter, rect, payload, clip, None)
            painter.restore()
        painter.end()
        super().paintEvent(event)  # tekent het greepje rechtsonder om te schalen

    def _text_color(self, alpha=255):
        color = QColor(self.config.get('color', '#ffffff'))
        color.setAlpha(alpha)
        return color

    def _draw_header(self, painter, now):
        total = self._total_unread()
        painter.setFont(self._font(15, True))
        painter.setPen(QColor(GMAIL_RED))
        title_rect = QRectF(PAD + 2, 4, 60, 24)
        painter.drawText(title_rect, Qt.AlignLeft | Qt.AlignVCenter, 'Gmail')
        title_w = QFontMetrics(self._font(15, True)).horizontalAdvance('Gmail')
        if total:
            painter.setFont(self._font(13, True))
            painter.setPen(self._text_color())
            painter.drawText(QRectF(PAD + 2 + title_w + 8, 4, 160, 24), Qt.AlignLeft | Qt.AlignVCenter,
                             f"{total} ongelezen")

        if self._message and now < self._message[1]:
            status = self._message[0]
        elif self._checking:
            status = 'Controleren…'
        elif self._last_check:
            status = f"Bijgewerkt {self._last_check:%H:%M}"
        else:
            status = 'Eerste controle…' if self.config['accounts'] else ''
        muted = bool(self.config.get('muted'))
        if muted and not (self._message and now < self._message[1]):
            status += ' · niet storen' if status else 'Niet storen'
        painter.setFont(self._font(10))
        painter.setPen(self._text_color(140))
        painter.drawText(QRectF(PAD + 2, 26, self.width() - 120, 14), Qt.AlignLeft | Qt.AlignVCenter, status)

        symbol_font = self._font(16, False, 'Segoe UI Symbol')
        emoji_font = self._font(14, False, 'Segoe UI Emoji')
        icons = (('⚙', 'settings', 'Instellingen / accounts', symbol_font),
                 ('⟳', 'refresh', 'Nu controleren', symbol_font),
                 ('🔕' if muted else '🔔', 'mute',
                  'Niet storen staat aan - klik om geluid en knipperen weer aan te zetten' if muted
                  else 'Niet storen: geen geluid of knipperen bij nieuwe mail', emoji_font))
        for index, (glyph, kind, tip, font) in enumerate(icons):
            rect = QRectF(self.width() - PAD - 28 * (index + 1), 8, 26, 26)
            hovered = self._hover is not None and rect.contains(self._hover)
            if hovered or (kind == 'mute' and muted):
                painter.setPen(Qt.NoPen)
                painter.setBrush(QColor(234, 67, 53, 90) if (kind == 'mute' and muted) else QColor(255, 255, 255, 30))
                painter.drawRoundedRect(rect, 6, 6)
            painter.setFont(font)
            painter.setPen(self._text_color(235 if (hovered or (kind == 'mute' and muted)) else 150))
            painter.drawText(rect, Qt.AlignCenter, glyph)
            self._add_hit(rect, kind, None, tip)

    def _draw_empty(self, painter, clip):
        painter.setFont(self._font(12))
        painter.setPen(self._text_color(170))
        painter.drawText(clip.adjusted(8, 0, -8, 0), Qt.AlignHCenter | Qt.AlignVCenter | Qt.TextWordWrap,
                         "Nog geen Gmail-accounts.\nKlik op ⚙ om er een toe te voegen.")
        self._add_hit(clip, 'settings', None, 'Accounts toevoegen')

    def _draw_account(self, painter, rect, clip, key, now):
        state = self.states[key]
        index = [a['email'].lower() for a in self.config['accounts']].index(key)
        address = account_label(self.config['accounts'][index])  # naam of (zonder naam) adres
        hovered = self._hover is not None and rect.contains(self._hover) and clip.contains(self._hover)
        flashing = now < state['new_until']

        painter.setPen(Qt.NoPen)
        if flashing:
            painter.setBrush(QColor(234, 67, 53, 70 if int(now * 2) % 2 else 40))
        else:
            painter.setBrush(QColor(255, 255, 255, 30 if hovered else 16))
        painter.drawRoundedRect(rect, 8, 8)

        avatar = QRectF(rect.left() + 8, rect.center().y() - 11, 22, 22)
        painter.setBrush(QColor(AVATAR_COLORS[index % len(AVATAR_COLORS)]))
        painter.drawEllipse(avatar)
        painter.setFont(self._font(12, True))
        painter.setPen(QColor('#ffffff'))
        painter.drawText(avatar, Qt.AlignCenter, address[:1].upper())

        self._add_hit(rect, 'open_inbox', key, f"Open {address} in Gmail", clip)

        x_right = rect.right() - 6
        if state['ok'] and (state['unread'] > 0 or state['expanded']):
            zone = QRectF(x_right - 22, rect.top(), 24, rect.height())
            painter.setFont(self._font(12, False, 'Segoe UI Symbol'))
            painter.setPen(self._text_color(190))
            painter.drawText(zone, Qt.AlignCenter, '▾' if state['expanded'] else '▸')
            self._add_hit(zone, 'toggle', key, 'Ongelezen berichten tonen/verbergen', clip)
            x_right -= 24

        if state['ok'] is False:
            icon = QRectF(x_right - 20, rect.center().y() - 9, 18, 18)
            painter.setPen(Qt.NoPen)
            painter.setBrush(QColor('#e03e3e'))
            painter.drawEllipse(icon)
            painter.setFont(self._font(12, True))
            painter.setPen(QColor('#ffffff'))
            painter.drawText(icon, Qt.AlignCenter, '!')
            self._add_hit(icon, 'open_inbox', key, state['error'] or 'Fout', clip)
            x_right -= 24
        elif state['ok']:
            text = str(state['unread'])
            font = self._font(11, True)
            width = max(22, QFontMetrics(font).horizontalAdvance(text) + 14)
            pill = QRectF(x_right - width, rect.center().y() - 9, width, 18)
            painter.setPen(Qt.NoPen)
            painter.setBrush(QColor(GMAIL_RED) if state['unread'] else QColor(255, 255, 255, 25))
            painter.drawRoundedRect(pill, 9, 9)
            painter.setFont(font)
            painter.setPen(QColor('#ffffff') if state['unread'] else self._text_color(120))
            painter.drawText(pill, Qt.AlignCenter, text)
            x_right -= width + 6
        elif state['ok'] is None:
            painter.setFont(self._font(12))
            painter.setPen(self._text_color(120))
            painter.drawText(QRectF(x_right - 24, rect.top(), 22, rect.height()), Qt.AlignCenter, '…')
            x_right -= 26

        font = self._font(12.5)
        painter.setFont(font)
        painter.setPen(self._text_color())
        text_rect = QRectF(avatar.right() + 8, rect.top(), max(10, x_right - avatar.right() - 12), rect.height())
        painter.drawText(text_rect, Qt.AlignLeft | Qt.AlignVCenter,
                         QFontMetrics(font).elidedText(address, Qt.ElideRight, int(text_rect.width())))

    def _draw_mail(self, painter, rect, clip, key, message):
        hovered = self._hover is not None and rect.contains(self._hover) and clip.contains(self._hover)
        painter.setPen(Qt.NoPen)
        painter.setBrush(QColor(255, 255, 255, 22 if hovered else 9))
        painter.drawRoundedRect(rect, 6, 6)
        self._add_hit(rect, 'open_mail', (key, message), 'Open dit bericht in Gmail', clip)

        right_w = 60
        if hovered:
            for index, (glyph, kind, tip) in enumerate((('🗑', 'trash', 'Naar prullenbak'),
                                                         ('✓', 'mark_read', 'Markeer als gelezen'))):
                icon = QRectF(rect.right() - 6 - 26 * (index + 1), rect.center().y() - 13, 26, 26)
                icon_hover = icon.contains(self._hover)
                if icon_hover:
                    painter.setPen(Qt.NoPen)
                    painter.setBrush(QColor(255, 255, 255, 40))
                    painter.drawRoundedRect(icon, 6, 6)
                painter.setFont(self._font(14, False, 'Segoe UI Emoji' if kind == 'trash' else 'Segoe UI Symbol'))
                painter.setPen(self._text_color(230 if icon_hover else 170))
                painter.drawText(icon, Qt.AlignCenter, glyph)
                self._add_hit(icon, kind, (key, message['uid']), tip, clip)
            right_w = 62
        else:
            painter.setFont(self._font(10.5))
            painter.setPen(self._text_color(130))
            painter.drawText(QRectF(rect.right() - 62, rect.top() + 5, 56, 16), Qt.AlignRight | Qt.AlignVCenter,
                             format_mail_date(message['timestamp']))

        text_w = int(rect.width() - 16 - right_w)
        sender_font, subject_font = self._font(12, True), self._font(11)
        painter.setFont(sender_font)
        painter.setPen(self._text_color())
        painter.drawText(QRectF(rect.left() + 8, rect.top() + 3, text_w, 18), Qt.AlignLeft | Qt.AlignVCenter,
                         QFontMetrics(sender_font).elidedText(message['sender'], Qt.ElideRight, text_w))
        painter.setFont(subject_font)
        painter.setPen(self._text_color(165))
        painter.drawText(QRectF(rect.left() + 8, rect.top() + 21, rect.width() - 16, 17),
                         Qt.AlignLeft | Qt.AlignVCenter,
                         QFontMetrics(subject_font).elidedText(message['subject'], Qt.ElideRight,
                                                               int(rect.width() - 16)))

    def _draw_note(self, painter, rect, text, clip, hit):
        painter.setFont(self._font(11))
        painter.setPen(self._text_color(140))
        painter.drawText(rect.adjusted(8, 0, 0, 0), Qt.AlignLeft | Qt.AlignVCenter, text)
        if hit:
            self._add_hit(rect, hit[0], hit[1], 'Open in Gmail', clip)

    # -- een mail lezen ----------------------------------------------------

    def _open_reader(self, key, message):
        address = self._display_address(key)
        mark_read = bool(self.config.get('mark_read_on_open', True))
        self._reader = {'key': key, 'address': address, 'message': message, 'status': 'loading',
                        'data': None, 'error': None, 'show_html': False, 'marked_read': False,
                        'mark_read': mark_read}
        try:
            password = self._account_password(address)
        except Exception:
            self._reader.update(status='error', error='Wachtwoord kan niet worden gelezen')
        else:
            threading.Thread(target=self._run_fetch_message, args=(address, password, message['uid'], mark_read),
                             name='GmailInboxReader', daemon=True).start()
        self._render_reader()
        self._layout_reader()
        self.update()

    def _run_fetch_message(self, address, password, uid, mark_read):
        result = fetch_message(address, password, uid, mark_read)
        self._emit(self.bridge.message_ready, address, uid, result)
        if mark_read and result['ok']:
            # de lijst en de tellers meteen bijwerken: de mail is nu gelezen
            self._emit(self.bridge.result, fetch_account(address, password, self.config.get('max_messages', 5)))

    def _on_message_ready(self, address, uid, data):
        reader = self._reader
        if not reader or reader['address'] != address or reader['message']['uid'] != uid:
            return  # intussen een andere mail geopend, of terug naar de lijst
        reader['data'] = data
        if data['ok']:
            reader['status'] = 'ok'
            reader['show_html'] = bool(data['html']) and not data['text'].strip()
            if reader['mark_read']:
                reader['marked_read'] = True
                self._drop_from_list(address, uid)
        else:
            reader['status'] = 'error'
            reader['error'] = data['error']
        self._render_reader()
        self.update()

    def _close_reader(self):
        self._reader = None
        self.reader_view.hide()
        self.reader_view.clear()
        self.update()

    def _layout_reader(self):
        view = getattr(self, 'reader_view', None)
        if view is None:
            return
        if getattr(self, '_reader', None):
            top = HEADER_H + READER_META_H
            view.setGeometry(PAD, top, max(10, self.width() - 2 * PAD), max(30, self.height() - top - PAD))
            view.show()
        else:
            view.hide()

    def _render_reader(self):
        reader = self._reader
        if not reader:
            return
        view = self.reader_view
        data = reader['data']
        scrollbars = ("QScrollBar:vertical { width: 8px; background: transparent; margin: 0; }"
                      "QScrollBar::handle:vertical { background: rgba(128,128,128,140); border-radius: 4px; min-height: 24px; }"
                      "QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical { height: 0; }"
                      "QScrollBar:horizontal { height: 8px; background: transparent; }"
                      "QScrollBar::handle:horizontal { background: rgba(128,128,128,140); border-radius: 4px; }"
                      "QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal { width: 0; }")
        if reader['status'] == 'ok' and reader['show_html']:
            # Mails met opmaak zijn gemaakt voor een witte achtergrond.
            base = "QTextBrowser { background: #ffffff; color: #202124; border: none; border-radius: 8px; padding: 8px; }"
        else:
            base = (f"QTextBrowser {{ background: rgba(255,255,255,16); color: {self.config.get('color', '#ffffff')}; "
                    "border: none; border-radius: 8px; padding: 8px; }")
        view.setStyleSheet(base + scrollbars)
        font = self._font(13)
        view.setFont(font)
        view.document().setDefaultFont(font)
        # Links: het standaard donkerblauw is op de donkere achtergrond bijna onleesbaar.
        on_white = reader['status'] == 'ok' and reader['show_html']
        view.document().setDefaultStyleSheet('a { color: #1a0dab; }' if on_white else 'a { color: #8ab4f8; }')

        if reader['status'] == 'loading':
            view.setHtml('<i>Mail laden…</i>')
        elif reader['status'] == 'error':
            view.setHtml(f"<p>Kon deze mail niet openen:<br>{html_escape(reader['error'] or 'onbekende fout')}</p>")
        else:
            note = ''
            if data.get('truncated'):
                note = '<p><i>Deze mail is erg groot en is ingekort. Gebruik ↗ om hem helemaal in Gmail te lezen.</i></p>'
            if reader['show_html']:
                body = sanitize_html(data['html'][:MAX_RENDER_CHARS])
            else:
                shown = data['text'] if data['text'].strip() else '(Deze mail heeft geen tekst.)'
                body = text_to_html(shown[:MAX_RENDER_CHARS])
            view.setHtml(note + body)
        view.verticalScrollBar().setValue(0)

    def _on_reader_link(self, url):
        if url.scheme().lower() in ('http', 'https', 'mailto'):
            QDesktopServices.openUrl(url)

    def _on_reader_hover(self, url):
        # Laat zien waar een link echt naartoe gaat (handig tegen valse links).
        self.reader_view.setToolTip(url.toString() if url.isValid() and not url.isEmpty() else '')

    def _draw_reader(self, painter, now):
        reader = self._reader
        data = reader['data'] if reader['status'] == 'ok' else None
        message = reader['message']
        symbol_font = self._font(16, False, 'Segoe UI Symbol')
        emoji_font = self._font(14, False, 'Segoe UI Emoji')

        buttons = [('🗑', 'reader_trash', 'Naar prullenbak', emoji_font),
                   ('↗', 'reader_open', 'Openen in Gmail (browser)', symbol_font)]
        if data is not None and not reader['marked_read']:
            buttons.append(('✓', 'reader_read', 'Markeer als gelezen', symbol_font))
        if data is not None and data['html'] and data['text'].strip():
            buttons.append(('Aa', 'reader_toggle', 'Wissel tussen opmaak en alleen tekst', self._font(12, True)))
        buttons.append(('←', 'reader_back', 'Terug naar de lijst', symbol_font))

        for index, (glyph, kind, tip, font) in enumerate(buttons):
            if kind == 'reader_back':
                rect = QRectF(PAD, 8, 26, 26)
            else:
                rect = QRectF(self.width() - PAD - 28 * (index + 1), 8, 26, 26)
            hovered = self._hover is not None and rect.contains(self._hover)
            if hovered:
                painter.setPen(Qt.NoPen)
                painter.setBrush(QColor(255, 255, 255, 30))
                painter.drawRoundedRect(rect, 6, 6)
            painter.setFont(font)
            painter.setPen(self._text_color(235 if hovered else 170))
            painter.drawText(rect, Qt.AlignCenter, glyph)
            self._add_hit(rect, kind, None, tip)
        right_edge = self.width() - PAD - 28 * (len(buttons) - 1) - 4

        subject = data['subject'] if data else message['subject']
        left = PAD + 32
        title_font = self._font(14, True)
        painter.setFont(title_font)
        painter.setPen(self._text_color())
        painter.drawText(QRectF(left, 4, max(10, right_edge - left), 24), Qt.AlignLeft | Qt.AlignVCenter,
                         QFontMetrics(title_font).elidedText(subject, Qt.ElideRight, int(max(10, right_edge - left))))

        account = next((a for a in self.config['accounts'] if a['email'].lower() == reader['key']), None)
        label = account_label(account) if account else ''
        if reader['status'] == 'loading':
            state_text = 'Laden…'
        elif reader['status'] == 'error':
            state_text = 'Niet geopend'
        else:
            state_text = 'Gemarkeerd als gelezen' if reader['marked_read'] else 'Nog ongelezen'
        painter.setFont(self._font(10))
        painter.setPen(self._text_color(140))
        painter.drawText(QRectF(left, 26, max(10, right_edge - left), 14), Qt.AlignLeft | Qt.AlignVCenter,
                         f"{label} · {state_text}" if label else state_text)

        # afzender, datum en bijlagen
        top = HEADER_H
        if data:
            sender = data['sender_name'] or data['sender_addr'] or '(onbekend)'
            address = f"  <{data['sender_addr']}>" if data['sender_name'] and data['sender_addr'] else ''
            when = data['date']
        else:
            sender, address, when = message['sender'], '', format_mail_date(message['timestamp'])
        width = self.width() - 2 * PAD - 4
        painter.setFont(self._font(12, True))
        sender_fm = QFontMetrics(self._font(12, True))
        sender_text = sender_fm.elidedText(sender, Qt.ElideRight, int(width * 0.6))
        painter.setPen(self._text_color())
        painter.drawText(QRectF(PAD + 2, top + 2, width, 18), Qt.AlignLeft | Qt.AlignVCenter, sender_text)
        if address:
            used = sender_fm.horizontalAdvance(sender_text)
            small_fm = QFontMetrics(self._font(11))
            painter.setFont(self._font(11))
            painter.setPen(self._text_color(130))
            room = int(width - used - 90)
            if room > 40:
                painter.drawText(QRectF(PAD + 2 + used, top + 2, room, 18), Qt.AlignLeft | Qt.AlignVCenter,
                                 small_fm.elidedText(address, Qt.ElideRight, room))
        if when:
            painter.setFont(self._font(10.5))
            painter.setPen(self._text_color(130))
            painter.drawText(QRectF(PAD + 2, top + 2, width, 18), Qt.AlignRight | Qt.AlignVCenter, when)
        if data and data['attachments']:
            names = ', '.join(a['name'] for a in data['attachments'][:3])
            more = f" +{len(data['attachments']) - 3}" if len(data['attachments']) > 3 else ''
            count = len(data['attachments'])
            line = f"📎 {count} bijlage{'n' if count != 1 else ''}: {names}{more} (open in Gmail om te downloaden)"
            painter.setFont(self._font(10.5, False, 'Segoe UI Emoji'))
            painter.setPen(self._text_color(150))
            painter.drawText(QRectF(PAD + 2, top + 21, width, 16), Qt.AlignLeft | Qt.AlignVCenter,
                             QFontMetrics(self._font(10.5, False, 'Segoe UI Emoji')).elidedText(line, Qt.ElideRight, int(width)))

    # -- muis -------------------------------------------------------------

    def _hit_at(self, pos):
        for rect, kind, payload, tooltip in reversed(self._hits):
            if rect.contains(QPointF(pos)):
                return kind, payload, tooltip
        return None

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self._press_global = event.globalPos()
        super().mousePressEvent(event)

    def mouseMoveEvent(self, event):
        self._hover = QPointF(event.pos())
        if not (self.dragging or self.resizing):
            hit = self._hit_at(event.pos())
            self.setCursor(Qt.PointingHandCursor if hit else Qt.OpenHandCursor)
            self.setToolTip(hit[2] if hit else '')
        super().mouseMoveEvent(event)
        self.update()

    def leaveEvent(self, event):
        self._hover = None
        super().leaveEvent(event)
        self.update()

    def wheelEvent(self, event):
        if self._reader:
            return  # in een geopende mail scrolt het tekstvak zelf
        self._scroll -= event.angleDelta().y() / 120 * 40
        self.update()

    def mouseReleaseEvent(self, event):
        was_click = (event.button() == Qt.LeftButton and self._press_global is not None and
                     (event.globalPos() - self._press_global).manhattanLength() < 5 and not self.resizing)
        self._press_global = None
        super().mouseReleaseEvent(event)
        if was_click:
            hit = self._hit_at(event.pos())
            if hit:
                self._dispatch(hit[0], hit[1])

    def _dispatch(self, kind, payload):
        if kind == 'refresh':
            self.check_all()
        elif kind == 'mute':
            self._toggle_muted()
        elif kind == 'settings':
            self.openSettings()
        elif kind == 'open_inbox':
            QDesktopServices.openUrl(QUrl(gmail_url(self._display_address(payload))))
        elif kind == 'toggle':
            self.states[payload]['expanded'] = not self.states[payload]['expanded']
            self.update()
        elif kind == 'open_mail':
            key, message = payload
            self._open_reader(key, message)  # lezen in de widget, geen browser meer
        elif kind == 'reader_back':
            self._close_reader()
        elif kind == 'reader_trash' and self._reader:
            self._do_action(self._reader['address'], self._reader['message']['uid'], 'trash')
            self._close_reader()
        elif kind == 'reader_read' and self._reader and not self._reader['marked_read']:
            self._reader['marked_read'] = True
            self._do_action(self._reader['address'], self._reader['message']['uid'], 'read')
            self.update()
        elif kind == 'reader_open' and self._reader:
            QDesktopServices.openUrl(QUrl(gmail_url(self._reader['address'], self._reader['message']['thrid'])))
        elif kind == 'reader_toggle' and self._reader and self._reader['status'] == 'ok':
            self._reader['show_html'] = not self._reader['show_html']
            self._render_reader()
            self.update()
        elif kind in ('mark_read', 'trash'):
            key, uid = payload
            self._do_action(self._display_address(key), uid, 'read' if kind == 'mark_read' else 'trash')

    def _display_address(self, key):
        for account in self.config['accounts']:
            if account['email'].lower() == key.lower():
                return account['email']
        return key


# --------------------------------------------------------------------------
# Instellingen
# --------------------------------------------------------------------------

class AccountDialog(QDialog):
    """Een Gmail-account toevoegen, of de naam / het app-wachtwoord van een bestaand account wijzigen."""

    def __init__(self, parent=None, address='', existing=(), name=''):
        super().__init__(parent)
        self.setWindowTitle('Gmail-account')
        self.existing = {e.lower() for e in existing}
        self.editing = bool(address)

        layout = QVBoxLayout(self)
        form = QFormLayout()
        self.address_edit = QLineEdit(address)
        self.address_edit.setReadOnly(self.editing)
        form.addRow('E-mailadres:', self.address_edit)
        self.name_edit = QLineEdit(name)
        self.name_edit.setPlaceholderText('bijv. Privé, Werk, Kaasdagboek')
        form.addRow('Naam in de widget:', self.name_edit)
        self.password_edit = QLineEdit()
        self.password_edit.setEchoMode(QLineEdit.Password)
        self.password_edit.setPlaceholderText('leeg laten = ongewijzigd' if self.editing else 'xxxx xxxx xxxx xxxx')
        form.addRow('App-wachtwoord:', self.password_edit)
        layout.addLayout(form)

        hint = QLabel('De widget toont alleen deze naam; het e-mailadres blijft verborgen. '
                      'Zonder naam zie je het adres.')
        hint.setWordWrap(True)
        layout.addWidget(hint)

        link = QLabel(f'<a href="{APP_PASSWORD_URL}">App-wachtwoord aanmaken bij Google</a> '
                      '(tweestapsverificatie moet aan staan)')
        link.setOpenExternalLinks(True)
        link.setWordWrap(True)
        layout.addWidget(link)

        self.result_label = QLabel('')
        self.result_label.setWordWrap(True)
        layout.addWidget(self.result_label)

        buttons = QHBoxLayout()
        test_button = QPushButton('Testen')
        test_button.clicked.connect(self.test_login)
        ok_button = QPushButton('Opslaan')
        ok_button.clicked.connect(self.accept_if_valid)
        cancel_button = QPushButton('Annuleren')
        cancel_button.clicked.connect(self.reject)
        for button in (test_button, ok_button, cancel_button):
            buttons.addWidget(button)
        layout.addLayout(buttons)

    def values(self):
        return self.address_edit.text().strip(), self.password_edit.text().strip()

    def display_name(self):
        return self.name_edit.text().strip()

    def _validate(self, need_password=True):
        address, password = self.values()
        if '@' not in address or ' ' in address:
            return 'Vul een geldig e-mailadres in.'
        if not self.editing and address.lower() in self.existing:
            return 'Dit account staat er al in.'
        if need_password and not password:
            return 'Vul het app-wachtwoord in.'
        return None

    def test_login(self):
        problem = self._validate()
        if problem:
            self.result_label.setText(problem)
            return
        address, password = self.values()
        QApplication.setOverrideCursor(Qt.WaitCursor)
        try:
            result = fetch_account(address, password, 1)
        finally:
            QApplication.restoreOverrideCursor()
        if result['ok']:
            self.result_label.setText(f"Gelukt: {result['unread']} ongelezen in de inbox.")
        else:
            self.result_label.setText(result['error'])

    def accept_if_valid(self):
        # Bij bewerken mag het wachtwoord leeg blijven: dan blijft het bestaande staan.
        problem = self._validate(need_password=not self.editing)
        if problem:
            self.result_label.setText(problem)
            return
        self.accept()


class GmailSettingsDialog(WidgetSettingsDialog):
    def __init__(self, widget, parent=None):
        super().__init__(widget, parent)
        self.setMinimumWidth(420)

    def _ensure_accounts(self):
        if not hasattr(self, 'accounts'):
            self.accounts = copy.deepcopy(self.widget.config['accounts'])

    def add_behavior_section(self, layout):
        self._ensure_accounts()
        config = self.widget.config

        accounts_group = QGroupBox('Gmail-accounts')
        accounts_layout = QVBoxLayout()
        self.account_list = QListWidget()
        self.account_list.setMinimumHeight(120)
        accounts_layout.addWidget(self.account_list)
        row = QHBoxLayout()
        for text, handler in (('Toevoegen…', self.add_account), ('Bewerken…', self.edit_account),
                              ('Verwijderen', self.remove_account)):
            button = QPushButton(text)
            button.clicked.connect(handler)
            row.addWidget(button)
        accounts_layout.addLayout(row)
        accounts_group.setLayout(accounts_layout)
        layout.addWidget(accounts_group)
        self._refresh_list()

        behavior_group = QGroupBox('Controleren')
        behavior_layout = QVBoxLayout()
        row = QHBoxLayout()
        row.addWidget(QLabel('Controleer elke:'))
        self.update_interval = QDoubleSpinBox()
        self.update_interval.setRange(1, 120)
        self.update_interval.setDecimals(0)
        self.update_interval.setSuffix(' min')
        self.update_interval.setValue(float(config.get('check_interval_minutes', 2)))
        row.addWidget(self.update_interval)
        behavior_layout.addLayout(row)

        row = QHBoxLayout()
        row.addWidget(QLabel('Ongelezen berichten per account in lijst:'))
        self.max_messages = QSpinBox()
        self.max_messages.setRange(1, 20)
        self.max_messages.setValue(int(config.get('max_messages', 5)))
        row.addWidget(self.max_messages)
        behavior_layout.addLayout(row)

        self.mark_read_check = QCheckBox('Mail als gelezen markeren zodra ik hem open')
        self.mark_read_check.setToolTip('Uit: de mail blijft ongelezen tot je zelf op ✓ drukt.')
        self.mark_read_check.setChecked(bool(config.get('mark_read_on_open', True)))
        behavior_layout.addWidget(self.mark_read_check)

        behavior_group.setLayout(behavior_layout)
        layout.addWidget(behavior_group)

        sound_group = QGroupBox('Geluid bij nieuwe mail')
        sound_layout = QVBoxLayout()
        self.sound_check = QCheckBox('Geluid afspelen')
        self.sound_check.setChecked(bool(config.get('notify_sound', True)))
        sound_layout.addWidget(self.sound_check)

        row = QHBoxLayout()
        self.sound_combo = QComboBox()
        self.sound_combo.addItem('Windows-pieptoon', '')
        for name, path in list_windows_sounds():
            self.sound_combo.addItem(name, path)
        self._select_sound(config.get('sound_file', ''))
        self.sound_combo.currentIndexChanged.connect(self.play_sound)  # meteen horen hoe het klinkt
        row.addWidget(self.sound_combo, 1)
        browse_button = QPushButton('Eigen bestand…')
        browse_button.clicked.connect(self.browse_sound)
        row.addWidget(browse_button)
        play_button = QPushButton('▶ Afspelen')
        play_button.clicked.connect(self.play_sound)
        row.addWidget(play_button)
        sound_layout.addLayout(row)
        sound_group.setLayout(sound_layout)
        layout.addWidget(sound_group)

    def add_custom_section(self, layout):
        config = self.widget.config
        look_group = QGroupBox('Uiterlijk')
        look_layout = QVBoxLayout()

        row = QHBoxLayout()
        row.addWidget(QLabel('Achtergrond dekking (%):'))
        self.bg_opacity = QSpinBox()
        self.bg_opacity.setRange(10, 100)
        self.bg_opacity.setValue(int(config.get('bg_opacity', 100)))
        row.addWidget(self.bg_opacity)
        look_layout.addLayout(row)

        row = QHBoxLayout()
        row.addWidget(QLabel('Tekstkleur:'))
        self.color_button = QPushButton()
        self.color_button.setStyleSheet(f"background-color: {config.get('color', '#ffffff')};")
        self.color_button.clicked.connect(self.choose_color)
        row.addWidget(self.color_button)
        look_layout.addLayout(row)

        look_group.setLayout(look_layout)
        layout.addWidget(look_group)

    def choose_color(self):
        color = QColorDialog.getColor(QColor(self.widget.config.get('color', '#ffffff')))
        if color.isValid():
            self.color_button.setStyleSheet(f"background-color: {color.name()};")
            self.widget.config['color'] = color.name()

    # -- geluid -----------------------------------------------------------

    def _select_sound(self, path):
        index = self.sound_combo.findData(path)
        if index < 0:  # een eigen bestand dat niet in de Windows-lijst staat
            self.sound_combo.addItem(f"{os.path.basename(path)} (eigen bestand)", path)
            index = self.sound_combo.count() - 1
        self.sound_combo.setCurrentIndex(index)

    def browse_sound(self):
        start = os.path.dirname(self.sound_combo.currentData() or '') or WINDOWS_MEDIA_DIR
        path, _ = QFileDialog.getOpenFileName(self, 'Kies een geluid (.wav)', start, 'Geluiden (*.wav)')
        if path:
            self._select_sound(os.path.normpath(path))

    def play_sound(self, *_):
        play_notification_sound(self.sound_combo.currentData() or '')

    # -- accountlijst -----------------------------------------------------

    def _refresh_list(self):
        self.account_list.clear()
        for account in self.accounts:
            self.account_list.addItem(account_label(account))  # naam; het adres alleen als er geen naam is

    def add_account(self):
        dialog = AccountDialog(self, existing=[a['email'] for a in self.accounts])
        if dialog.exec_():
            address, password = dialog.values()
            self.accounts.append({'email': address, 'name': dialog.display_name(),
                                  'password': encrypt_password(password.replace(' ', ''))})
            self._refresh_list()

    def edit_account(self):
        row = self.account_list.currentRow()
        if row < 0:
            return
        account = self.accounts[row]
        dialog = AccountDialog(self, address=account['email'], name=account.get('name', ''))
        if dialog.exec_():
            _, password = dialog.values()
            account['name'] = dialog.display_name()
            if password:
                account['password'] = encrypt_password(password.replace(' ', ''))
            self._refresh_list()
            self.account_list.setCurrentRow(row)

    def remove_account(self):
        row = self.account_list.currentRow()
        if row < 0:
            return
        address = account_label(self.accounts[row])
        if QMessageBox.question(self, 'Account verwijderen', f'{address} uit de widget verwijderen?',
                                QMessageBox.Yes | QMessageBox.No, QMessageBox.No) == QMessageBox.Yes:
            del self.accounts[row]
            self._refresh_list()

    def get_config(self):
        # Bewust zonder super().get_config(): die leest de kleur uit de
        # QPalette van de knop, wat na setStyleSheet() de verkeerde waarde geeft.
        return {
            'accounts': self.accounts,
            'check_interval_minutes': int(self.update_interval.value()),
            'max_messages': self.max_messages.value(),
            'mark_read_on_open': self.mark_read_check.isChecked(),
            'notify_sound': self.sound_check.isChecked(),
            'sound_file': self.sound_combo.currentData() or '',
            'bg_opacity': self.bg_opacity.value(),
            'color': self.widget.config.get('color', '#ffffff'),
        }


# Important: The class must be named 'Widget' for the loader to recognize it
Widget = GmailInboxWidget

if __name__ == "__main__":
    app = QApplication(sys.argv)
    widget = Widget()
    widget.show()
    sys.exit(app.exec_())
