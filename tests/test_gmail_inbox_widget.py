import imaplib
import importlib.util
import os
import sys
import tempfile
import threading
import time
import unittest
from datetime import datetime
from email.message import EmailMessage
from unittest import mock

os.environ.setdefault('QT_QPA_PLATFORM', 'offscreen')

from PyQt5.QtCore import QUrl
from PyQt5.QtWidgets import QApplication

_app = QApplication.instance() or QApplication([])

_WIDGET_FILE = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    'widgets', 'gmail_inbox_widget', 'gmail_inbox_widget.py')

_spec = importlib.util.spec_from_file_location('gmail_inbox_widget_under_test', _WIDGET_FILE)
gmail = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(gmail)


def _header(sender, subject, date='Fri, 20 Nov 2026 14:32:00 +0100'):
    return f'From: {sender}\r\nSubject: {subject}\r\nDate: {date}\r\n\r\n'.encode()


# Zo ziet het antwoord van imaplib eruit voor `UID FETCH 102,103 (X-GM-THRID BODY.PEEK[HEADER.FIELDS (...)])`
FETCH_DATA = [
    (b'1 (UID 102 X-GM-THRID 1700000000000000255 BODY[HEADER.FIELDS (FROM SUBJECT DATE)] {99}',
     _header('"Anna de Vries" <anna@example.nl>', 'Hallo wereld')),
    b')',
    (b'2 (UID 103 X-GM-THRID 1700000000000000256 BODY[HEADER.FIELDS (FROM SUBJECT DATE)] {99}',
     _header('=?UTF-8?Q?J=C3=BCrgen?= <jurgen@example.nl>', '=?UTF-8?B?Q2Fmw6kgbmlldXdzYnJpZWY=?=')),
    b')',
]


def make_message(plain=None, html=None, attachments=(), subject='Test', sender='Anna <anna@example.nl>'):
    msg = EmailMessage()
    msg['From'] = sender
    msg['To'] = 'test.persoon@example.com'
    msg['Subject'] = subject
    msg['Date'] = 'Fri, 20 Nov 2026 14:32:00 +0100'
    if plain is not None:
        msg.set_content(plain)
        if html is not None:
            msg.add_alternative(html, subtype='html')
    elif html is not None:
        msg.set_content(html, subtype='html')
    for name, data in attachments:
        msg.add_attachment(data, maintype='application', subtype='octet-stream', filename=name)
    return msg.as_bytes()


def message_response(raw, size=None):
    """Zo ziet het antwoord van imaplib eruit voor `UID FETCH n (RFC822.SIZE BODY.PEEK[]<0.N>)`."""
    size = len(raw) if size is None else size
    return 'OK', [(b'1 (UID 102 RFC822.SIZE %d BODY[]<0> {%d}' % (size, len(raw)), raw), b')']


class FakeIMAP:
    instances = []
    uids = b'101 102 103'
    message = message_response(make_message(plain='Hallo wereld'))

    def __init__(self, host, port, timeout=None):
        self.calls = []
        FakeIMAP.instances.append(self)

    def login(self, user, password):
        self.calls.append(('login', user, password))
        if password == 'bad':
            raise imaplib.IMAP4.error('[AUTHENTICATIONFAILED] Invalid credentials (Failure)')
        return 'OK', [b'logged in']

    def select(self, mailbox, readonly=False):
        self.calls.append(('select', mailbox, readonly))
        return 'OK', [b'3']

    def uid(self, command, *args):
        self.calls.append(('uid', command) + args)
        if command == 'SEARCH':
            return 'OK', [self.uids]
        if command == 'FETCH' and 'BODY.PEEK[]' in str(args[1]):
            return FakeIMAP.message
        if command == 'FETCH':
            return 'OK', FETCH_DATA
        return 'OK', [b'done']

    def logout(self):
        self.calls.append(('logout',))


class TestHelpers(unittest.TestCase):
    def test_account_label_prefers_the_chosen_name_over_the_address(self):
        self.assertEqual(gmail.account_label({'email': 'a@gmail.com', 'name': 'Privé'}), 'Privé')

    def test_account_label_falls_back_to_the_address_without_a_name(self):
        self.assertEqual(gmail.account_label({'email': 'a@gmail.com'}), 'a@gmail.com')
        self.assertEqual(gmail.account_label({'email': 'a@gmail.com', 'name': '   '}), 'a@gmail.com')

    def test_gmail_url_selects_the_account(self):
        self.assertEqual(gmail.gmail_url('a@gmail.com'), 'https://mail.google.com/mail/?authuser=a%40gmail.com')

    def test_gmail_url_can_point_at_a_thread(self):
        self.assertTrue(gmail.gmail_url('a@gmail.com', '18c3f').endswith('#inbox/18c3f'))

    def test_friendly_error_for_bad_credentials(self):
        exc = imaplib.IMAP4.error('[AUTHENTICATIONFAILED] Invalid credentials (Failure)')
        self.assertIn('app-wachtwoord', gmail.friendly_error(exc))

    def test_friendly_error_for_network_problems(self):
        self.assertIn('verbinding', gmail.friendly_error(OSError('boom')))

    def test_format_mail_date(self):
        now = datetime(2026, 11, 20, 18, 0)
        today = datetime(2026, 11, 20, 14, 32).timestamp()
        yesterday = datetime(2026, 11, 19, 9, 0).timestamp()
        older = datetime(2026, 11, 3, 9, 0).timestamp()
        self.assertEqual(gmail.format_mail_date(today, now), '14:32')
        self.assertEqual(gmail.format_mail_date(yesterday, now), 'gisteren')
        self.assertEqual(gmail.format_mail_date(older, now), '3 nov')
        self.assertEqual(gmail.format_mail_date(None, now), '')


@unittest.skipUnless(sys.platform == 'win32', 'DPAPI bestaat alleen op Windows')
class TestPasswordEncryption(unittest.TestCase):
    def test_round_trip_and_not_plaintext(self):
        token = gmail.encrypt_password('abcd efgh ijkl mnop')
        self.assertTrue(token.startswith('dpapi:'))
        self.assertNotIn('abcd', token)
        self.assertEqual(gmail.decrypt_password(token), 'abcd efgh ijkl mnop')

    def test_non_ascii_round_trip(self):
        self.assertEqual(gmail.decrypt_password(gmail.encrypt_password('wachtwoord-é-ü')), 'wachtwoord-é-ü')


class TestParseFetchResponse(unittest.TestCase):
    def test_parses_newest_first_with_decoded_headers(self):
        messages = gmail.parse_fetch_response(FETCH_DATA)
        self.assertEqual([m['uid'] for m in messages], ['103', '102'])
        self.assertEqual(messages[0]['sender'], 'Jürgen')
        self.assertEqual(messages[0]['subject'], 'Café nieuwsbrief')
        self.assertEqual(messages[1]['sender'], 'Anna de Vries')

    def test_thread_id_is_converted_to_the_hex_gmail_uses_in_urls(self):
        messages = gmail.parse_fetch_response(FETCH_DATA)
        self.assertEqual(messages[1]['thrid'], format(1700000000000000255, 'x'))

    def test_ignores_non_message_entries(self):
        self.assertEqual(gmail.parse_fetch_response([b')', b'junk']), [])

    def test_missing_subject_gets_placeholder(self):
        data = [(b'1 (UID 5 X-GM-THRID 1 BODY[HEADER.FIELDS (FROM SUBJECT DATE)] {20}',
                 b'From: x@example.nl\r\n\r\n'), b')']
        self.assertEqual(gmail.parse_fetch_response(data)[0]['subject'], '(geen onderwerp)')


class TestFetchAccount(unittest.TestCase):
    def setUp(self):
        FakeIMAP.instances = []
        FakeIMAP.uids = b'101 102 103'
        patcher = mock.patch.object(gmail.imaplib, 'IMAP4_SSL', FakeIMAP)
        patcher.start()
        self.addCleanup(patcher.stop)

    def test_returns_unread_count_and_messages(self):
        result = gmail.fetch_account('test.persoon@example.com', 'abcd efgh', max_messages=2)
        self.assertTrue(result['ok'])
        self.assertEqual(result['unread'], 3)
        self.assertEqual(len(result['messages']), 2)

    def test_mailbox_is_opened_read_only_so_checking_never_marks_mail_as_read(self):
        gmail.fetch_account('test.persoon@example.com', 'pw')
        calls = FakeIMAP.instances[0].calls
        self.assertIn(('select', 'INBOX', True), calls)
        fetch = [c for c in calls if c[:2] == ('uid', 'FETCH')][0]
        self.assertIn('BODY.PEEK', fetch[3])

    def test_app_password_spaces_are_stripped(self):
        gmail.fetch_account('test.persoon@example.com', 'abcd efgh ijkl mnop')
        self.assertIn(('login', 'test.persoon@example.com', 'abcdefghijklmnop'), FakeIMAP.instances[0].calls)

    def test_only_the_newest_messages_are_fetched(self):
        FakeIMAP.uids = b' '.join(str(n).encode() for n in range(1, 51))
        gmail.fetch_account('test.persoon@example.com', 'pw', max_messages=3)
        fetch = [c for c in FakeIMAP.instances[0].calls if c[:2] == ('uid', 'FETCH')][0]
        self.assertEqual(fetch[2], b'48,49,50')

    def test_empty_inbox(self):
        FakeIMAP.uids = b''
        result = gmail.fetch_account('test.persoon@example.com', 'pw')
        self.assertTrue(result['ok'])
        self.assertEqual((result['unread'], result['messages']), (0, []))

    def test_bad_password_gives_friendly_error_instead_of_raising(self):
        result = gmail.fetch_account('test.persoon@example.com', 'bad')
        self.assertFalse(result['ok'])
        self.assertIn('Inloggen mislukt', result['error'])

    def test_always_logs_out(self):
        gmail.fetch_account('test.persoon@example.com', 'pw')
        self.assertEqual(FakeIMAP.instances[0].calls[-1], ('logout',))


class TestNotificationSound(unittest.TestCase):
    def _fake_winsound(self):
        fake = mock.MagicMock()
        fake.SND_FILENAME, fake.SND_ASYNC, fake.SND_NODEFAULT, fake.MB_ICONASTERISK = 1, 2, 4, 64
        return fake

    def test_plays_the_chosen_wav_without_blocking(self):
        fake = self._fake_winsound()
        with tempfile.TemporaryDirectory() as folder:
            path = os.path.join(folder, 'ding.wav')
            open(path, 'wb').close()
            with mock.patch.dict(sys.modules, {'winsound': fake}):
                gmail.play_notification_sound(path)
        fake.PlaySound.assert_called_once_with(path, 1 | 2 | 4)
        fake.MessageBeep.assert_not_called()

    def test_falls_back_to_the_windows_beep(self):
        for path in ('', os.path.join(tempfile.gettempdir(), 'bestaat-niet.wav'), 'geluid.mp3'):
            fake = self._fake_winsound()
            with mock.patch.dict(sys.modules, {'winsound': fake}):
                gmail.play_notification_sound(path)
            fake.MessageBeep.assert_called_once_with(64)
            fake.PlaySound.assert_not_called()

    def test_lists_only_wav_files_sorted_by_name(self):
        with tempfile.TemporaryDirectory() as folder:
            for name in ('b.wav', 'A.WAV', 'notes.txt'):
                open(os.path.join(folder, name), 'wb').close()
            with mock.patch.object(gmail, 'WINDOWS_MEDIA_DIR', folder):
                sounds = gmail.list_windows_sounds()
        self.assertEqual([name for name, _ in sounds], ['A', 'b'])

    def test_missing_media_folder_gives_empty_list(self):
        with mock.patch.object(gmail, 'WINDOWS_MEDIA_DIR', os.path.join(tempfile.gettempdir(), 'nope-xyz')):
            self.assertEqual(gmail.list_windows_sounds(), [])

    def test_defaults_are_not_muted(self):
        self.assertFalse(gmail.DEFAULT_CONFIG['muted'])
        self.assertIn('sound_file', gmail.DEFAULT_CONFIG)


class TestWithoutImaplib(unittest.TestCase):
    """Een met PyInstaller gebouwde app bevat imaplib alleen als hij in de .spec staat."""

    def test_module_still_loads_when_imaplib_cannot_be_imported(self):
        with mock.patch.dict(sys.modules, {'imaplib': None}):
            spec = importlib.util.spec_from_file_location('gmail_without_imaplib', _WIDGET_FILE)
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)
        self.assertIsNone(module.imaplib)
        self.assertTrue(hasattr(module, 'Widget'))

    def test_checking_reports_a_clear_error_instead_of_crashing(self):
        with mock.patch.object(gmail, 'imaplib', None):
            result = gmail.fetch_account('test.persoon@example.com', 'pw')
        self.assertFalse(result['ok'])
        self.assertIn('imaplib', result['error'])

    def test_spec_file_lists_the_modules_the_widget_needs(self):
        spec_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                                 'Imolia Desktop Customizer.spec')
        with open(spec_path, encoding='utf-8') as f:
            spec_text = f.read()
        self.assertIn("'imaplib'", spec_text)


class TestMailAction(unittest.TestCase):
    def setUp(self):
        FakeIMAP.instances = []
        patcher = mock.patch.object(gmail.imaplib, 'IMAP4_SSL', FakeIMAP)
        patcher.start()
        self.addCleanup(patcher.stop)

    def test_mark_read_sets_seen_flag(self):
        gmail.mail_action('test.persoon@example.com', 'pw', '102', 'read')
        self.assertIn(('uid', 'STORE', '102', '+FLAGS', '(\\Seen)'), FakeIMAP.instances[0].calls)

    def test_trash_adds_trash_label_and_never_expunges(self):
        gmail.mail_action('test.persoon@example.com', 'pw', '102', 'trash')
        calls = FakeIMAP.instances[0].calls
        self.assertIn(('uid', 'STORE', '102', '+X-GM-LABELS', '(\\Trash)'), calls)
        self.assertFalse([c for c in calls if 'EXPUNGE' in str(c).upper()])

    def test_unknown_action_is_rejected(self):
        with self.assertRaises(ValueError):
            gmail.mail_action('test.persoon@example.com', 'pw', '102', 'explode')
        self.assertEqual(FakeIMAP.instances[0].calls[-1], ('logout',))


class TestParseMessage(unittest.TestCase):
    def test_plain_text_mail_with_accents(self):
        raw = make_message(plain='Hallo één wereld\nTot ziens', subject='Café nieuws', sender='"Jürgen" <jurgen@example.nl>')
        data = gmail.parse_message(raw)
        self.assertEqual(data['subject'], 'Café nieuws')
        self.assertEqual((data['sender_name'], data['sender_addr']), ('Jürgen', 'jurgen@example.nl'))
        self.assertIn('één wereld', data['text'])
        self.assertEqual(data['html'], '')
        self.assertIn('nov 2026', data['date'])

    def test_html_only_mail(self):
        data = gmail.parse_message(make_message(html='<p>Hallo <b>wereld</b></p>'))
        self.assertEqual(data['text'], '')
        self.assertIn('<b>wereld</b>', data['html'])

    def test_mail_with_both_versions_keeps_both(self):
        data = gmail.parse_message(make_message(plain='alleen tekst', html='<p>met opmaak</p>'))
        self.assertIn('alleen tekst', data['text'])
        self.assertIn('met opmaak', data['html'])

    def test_attachments_are_listed_by_name_but_not_returned(self):
        data = gmail.parse_message(make_message(plain='zie bijlage', attachments=[('factuur.pdf', b'x' * 1500)]))
        self.assertEqual(data['attachments'], [{'name': 'factuur.pdf', 'size': 1500}])
        self.assertIn('zie bijlage', data['text'])

    def test_unknown_charset_does_not_crash(self):
        raw = (b'From: a@example.nl\r\nSubject: x\r\nMIME-Version: 1.0\r\n'
               b'Content-Type: text/plain; charset=bestaat-niet\r\n\r\nGewoon tekst\r\n')
        self.assertIn('Gewoon tekst', gmail.parse_message(raw)['text'])

    def test_mail_without_subject_or_body(self):
        data = gmail.parse_message(b'From: a@example.nl\r\n\r\n')
        self.assertEqual(data['subject'], '(geen onderwerp)')
        self.assertEqual(data['text'], '')


class TestSanitizeHtml(unittest.TestCase):
    def test_scripts_frames_and_styles_disappear_with_their_content(self):
        html = ('<p>Hoi</p><script>alert("x")</script><style>p{color:red}</style>'
                '<iframe src="http://evil.example"></iframe><object data="x"></object>')
        cleaned = gmail.sanitize_html(html)
        self.assertIn('Hoi', cleaned)
        for forbidden in ('script', 'alert', 'color:red', 'iframe', 'evil.example', 'object'):
            self.assertNotIn(forbidden, cleaned)

    def test_event_handlers_and_unsafe_links_are_removed(self):
        cleaned = gmail.sanitize_html('<a href="javascript:alert(1)" onclick="x()">klik</a>'
                                      '<a href="file:///C:/geheim.txt">lokaal</a>'
                                      '<a href="https://example.com/pad?a=1&b=2">veilig</a>')
        self.assertNotIn('javascript', cleaned)
        self.assertNotIn('onclick', cleaned)
        self.assertNotIn('file:', cleaned)
        self.assertIn('href="https://example.com/pad?a=1&amp;b=2"', cleaned)
        self.assertIn('klik', cleaned)  # de tekst blijft staan

    def test_images_are_never_loaded(self):
        cleaned = gmail.sanitize_html('<img src="http://tracker.example/pixel.gif" alt="Logo"><img src="cid:abc">')
        self.assertNotIn('src', cleaned)
        self.assertNotIn('tracker.example', cleaned)
        self.assertIn('[Logo]', cleaned)
        self.assertIn('[afbeelding]', cleaned)

    def test_layout_tags_survive(self):
        cleaned = gmail.sanitize_html('<table><tr><td colspan="2"><b>vet</b></td></tr></table><br><hr>')
        for expected in ('<table>', '<td colspan="2">', '<b>vet</b>', '<br>', '<hr>'):
            self.assertIn(expected, cleaned)

    def test_style_attribute_keeps_harmless_rules_only(self):
        cleaned = gmail.sanitize_html('<div style="color: red; background: url(http://x/y.png); width: expression(1)">a</div>')
        self.assertIn('color: red', cleaned)
        self.assertNotIn('url(', cleaned)
        self.assertNotIn('expression', cleaned)

    def test_stray_angle_brackets_are_escaped_not_interpreted(self):
        cleaned = gmail.sanitize_html('<p>1 &lt; 2 en <onbekend>tekst</onbekend></p>')
        self.assertIn('1 &lt; 2', cleaned)
        self.assertIn('tekst', cleaned)
        self.assertNotIn('<onbekend', cleaned)


class TestWithoutHtmlParser(unittest.TestCase):
    """html.parser zit alleen in een gebouwde app als hij in de .spec staat."""

    @classmethod
    def setUpClass(cls):
        spec = importlib.util.spec_from_file_location('gmail_without_html_parser', _WIDGET_FILE)
        cls.module = importlib.util.module_from_spec(spec)
        with mock.patch.dict(sys.modules, {'html.parser': None}):
            spec.loader.exec_module(cls.module)

    def test_the_widget_still_loads(self):
        self.assertTrue(hasattr(self.module, 'Widget'))

    def test_formatted_mail_falls_back_to_its_text_without_scripts_or_tags(self):
        cleaned = self.module.sanitize_html('<style>p{x:y}</style><p>Hallo <b>wereld</b></p><script>boem()</script>'
                                            '<p>Tweede &amp; laatste</p>')
        self.assertIn('Hallo wereld', cleaned)
        self.assertIn('Tweede &amp; laatste', cleaned)
        for forbidden in ('boem', '<b>', 'x:y', '<script'):
            self.assertNotIn(forbidden, cleaned)

    def test_spec_file_lists_html_parser(self):
        spec_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                                 'Imolia Desktop Customizer.spec')
        with open(spec_path, encoding='utf-8') as f:
            self.assertIn("'html.parser'", f.read())


class TestTextToHtml(unittest.TestCase):
    def test_text_is_escaped(self):
        html = gmail.text_to_html('<script>alert(1)</script> & meer')
        self.assertNotIn('<script>', html)
        self.assertIn('&lt;script&gt;', html)
        self.assertIn('&amp; meer', html)

    def test_links_are_clickable_without_trailing_punctuation(self):
        html = gmail.text_to_html('Zie https://example.nl/pad?a=1&b=2.')
        self.assertIn('<a href="https://example.nl/pad?a=1&amp;b=2">https://example.nl/pad?a=1&amp;b=2</a>.', html)

    def test_link_in_angle_brackets(self):
        html = gmail.text_to_html('Bekijk <https://example.nl/x> nu')
        self.assertIn('<a href="https://example.nl/x">https://example.nl/x</a>', html)

    def test_line_breaks_are_kept(self):
        self.assertIn('white-space: pre-wrap', gmail.text_to_html('a\nb'))


class TestFetchMessage(unittest.TestCase):
    def setUp(self):
        FakeIMAP.instances = []
        FakeIMAP.message = message_response(make_message(plain='Hallo wereld', subject='Onderwerp'))
        patcher = mock.patch.object(gmail.imaplib, 'IMAP4_SSL', FakeIMAP)
        patcher.start()
        self.addCleanup(patcher.stop)

    def calls(self):
        return FakeIMAP.instances[0].calls

    def test_returns_the_parsed_mail(self):
        result = gmail.fetch_message('test.persoon@example.com', 'pw', '102')
        self.assertTrue(result['ok'])
        self.assertEqual(result['subject'], 'Onderwerp')
        self.assertIn('Hallo wereld', result['text'])
        self.assertFalse(result['truncated'])

    def test_fetching_uses_peek_so_the_mail_is_not_marked_read_by_the_fetch(self):
        gmail.fetch_message('test.persoon@example.com', 'pw', '102', mark_read=False)
        fetch = [c for c in self.calls() if c[:2] == ('uid', 'FETCH')][0]
        self.assertIn('BODY.PEEK[]', fetch[3])
        self.assertNotIn(('uid', 'STORE', '102', '+FLAGS', '(\\Seen)'), self.calls())

    def test_without_marking_the_inbox_is_opened_read_only(self):
        gmail.fetch_message('test.persoon@example.com', 'pw', '102', mark_read=False)
        self.assertIn(('select', 'INBOX', True), self.calls())

    def test_marking_read_happens_after_a_successful_fetch(self):
        gmail.fetch_message('test.persoon@example.com', 'pw', '102', mark_read=True)
        calls = self.calls()
        self.assertIn(('select', 'INBOX', False), calls)
        fetch_at = [i for i, c in enumerate(calls) if c[:2] == ('uid', 'FETCH')][0]
        store_at = calls.index(('uid', 'STORE', '102', '+FLAGS', '(\\Seen)'))
        self.assertGreater(store_at, fetch_at)

    def test_a_missing_mail_gives_an_error_and_is_not_marked(self):
        FakeIMAP.message = ('OK', [None])
        result = gmail.fetch_message('test.persoon@example.com', 'pw', '999', mark_read=True)
        self.assertFalse(result['ok'])
        self.assertIn('bestaat niet meer', result['error'])
        self.assertFalse([c for c in self.calls() if c[:2] == ('uid', 'STORE')])

    def test_a_very_large_mail_is_flagged_as_truncated(self):
        raw = make_message(plain='begin van een enorme mail')
        FakeIMAP.message = message_response(raw, size=50_000_000)
        self.assertTrue(gmail.fetch_message('test.persoon@example.com', 'pw', '102')['truncated'])

    def test_the_size_limit_is_requested_from_the_server(self):
        gmail.fetch_message('test.persoon@example.com', 'pw', '102', max_bytes=1234)
        fetch = [c for c in self.calls() if c[:2] == ('uid', 'FETCH')][0]
        self.assertIn('<0.1234>', fetch[3])

    def test_bad_password_is_reported_not_raised(self):
        result = gmail.fetch_message('test.persoon@example.com', 'bad', '102')
        self.assertFalse(result['ok'])
        self.assertIn('Inloggen mislukt', result['error'])

    def test_always_logs_out(self):
        gmail.fetch_message('test.persoon@example.com', 'pw', '102')
        self.assertEqual(self.calls()[-1], ('logout',))


def _wait_until(condition, timeout=5.0):
    end = time.time() + timeout
    while time.time() < end:
        if condition():  # eerst kijken: onnodig Qt-events verwerken kan andere, nog openstaande dingen aanraken
            return True
        _app.processEvents()
        time.sleep(0.01)
    return condition()


def _wait_for_reader_threads():
    """Wacht tot de achtergrondthreads van een geopende mail klaar zijn en hun uitkomst is verwerkt."""
    _wait_until(lambda: not any(t.name == 'GmailInboxReader' and t.is_alive() for t in threading.enumerate()))
    for _ in range(5):
        _app.processEvents()
        time.sleep(0.01)


def _canned(plain='Hallo wereld', html='', subject='Onderwerp', ok=True, **extra):
    data = {'email': 'test.persoon@example.com', 'uid': '102', 'ok': ok, 'error': None if ok else 'Geen verbinding met Gmail',
            'subject': subject, 'sender_name': 'Anna', 'sender_addr': 'anna@example.nl',
            'date': '20 nov 2026 14:32', 'text': plain, 'html': html, 'attachments': [], 'truncated': False,
            'size': 100}
    data.update(extra)
    return data


class TestReadingInTheWidget(unittest.TestCase):
    ADDRESS = 'test.persoon@example.com'

    @classmethod
    def setUpClass(cls):
        config = dict(gmail.DEFAULT_CONFIG)
        config['accounts'] = [{'email': cls.ADDRESS, 'name': 'Privé', 'password': gmail.encrypt_password('pw')}]
        for patcher in (
            mock.patch.object(gmail.GmailInboxWidget, 'load_config', lambda self: dict(config, accounts=list(config['accounts']))),
            mock.patch.object(gmail.GmailInboxWidget, 'save_config', lambda self: None),
            mock.patch.object(gmail.GmailInboxWidget, 'check_all', lambda self: None),  # nooit echt verbinden
            # Ook als er toch iets in een thread of timer terechtkomt: nooit een echte verbinding naar Gmail.
            mock.patch.object(gmail.imaplib, 'IMAP4_SSL', FakeIMAP),
        ):
            patcher.start()
            cls.addClassCleanup(patcher.stop)
        # De widget plant bij het aanmaken een controle over 1,5 s in (QTimer.singleShot). Die zou
        # na deze tests, tijdens andere testbestanden, alsnog afgaan: niet laten plannen.
        with mock.patch.object(gmail.QTimer, 'singleShot'):
            cls.widget = gmail.GmailInboxWidget()
        cls.widget.resize(380, 400)
        cls.addClassCleanup(cls._shutdown)

    @classmethod
    def _shutdown(cls):
        cls.widget.check_timer.stop()
        cls.widget.ui_timer.stop()
        cls.widget.close()

    def setUp(self):
        w = self.widget
        _wait_for_reader_threads()  # een late thread van de vorige test mag deze test niet beinvloeden
        w._close_reader()
        w.config['mark_read_on_open'] = True
        w.states[self.ADDRESS]['expanded'] = True
        w.states[self.ADDRESS]['ok'] = True
        w.states[self.ADDRESS]['unread'] = 2
        self.message = {'uid': '102', 'thrid': 'abc', 'sender': 'Anna', 'subject': 'Onderwerp', 'timestamp': time.time()}
        w.states[self.ADDRESS]['messages'] = [self.message, {'uid': '101', 'thrid': 'abd', 'sender': 'Bob',
                                                              'subject': 'Ander', 'timestamp': time.time()}]
        for patcher in (mock.patch.object(gmail.QDesktopServices, 'openUrl'),
                        mock.patch.object(gmail, 'fetch_account', side_effect=lambda *a, **k: {
                            'email': self.ADDRESS, 'ok': True, 'error': None, 'unread': 1,
                            'messages': [w.states[self.ADDRESS]['messages'][-1]]})):
            started = patcher.start()
            self.addCleanup(patcher.stop)
            if patcher.attribute == 'openUrl':
                self.open_url = started

    def open_mail(self, data):
        with mock.patch.object(gmail, 'fetch_message', return_value=data) as fetch:
            self.widget._dispatch('open_mail', (self.ADDRESS, self.message))
            self.assertTrue(_wait_until(lambda: self.widget._reader and self.widget._reader['status'] != 'loading'))
            _wait_for_reader_threads()
        return fetch

    def test_clicking_a_mail_reads_it_in_the_widget_and_never_opens_the_browser(self):
        self.open_mail(_canned('Dit is de mail'))
        self.assertIsNotNone(self.widget._reader)
        self.assertTrue(self.widget.reader_view.isVisibleTo(self.widget))
        self.assertIn('Dit is de mail', self.widget.reader_view.toPlainText())
        self.open_url.assert_not_called()

    def test_opening_marks_it_read_and_it_leaves_the_unread_list(self):
        fetch = self.open_mail(_canned())
        self.assertTrue(fetch.call_args[0][3])  # mark_read=True doorgegeven
        self.assertTrue(self.widget._reader['marked_read'])
        self.assertTrue(_wait_until(lambda: [m['uid'] for m in self.widget.states[self.ADDRESS]['messages']] == ['101']))
        self.assertEqual(self.widget.states[self.ADDRESS]['unread'], 1)

    def test_with_the_setting_off_the_mail_stays_unread_until_the_check_button(self):
        self.widget.config['mark_read_on_open'] = False
        fetch = self.open_mail(_canned())
        self.assertFalse(fetch.call_args[0][3])
        self.assertFalse(self.widget._reader['marked_read'])
        self.assertEqual(len(self.widget.states[self.ADDRESS]['messages']), 2)
        with mock.patch.object(self.widget, '_do_action') as action:
            self.widget._dispatch('reader_read', None)
        action.assert_called_once_with(self.ADDRESS, '102', 'read')
        self.assertTrue(self.widget._reader['marked_read'])

    def test_trash_button_moves_the_mail_to_the_trash_and_returns_to_the_list(self):
        self.open_mail(_canned())
        with mock.patch.object(self.widget, '_do_action') as action:
            self.widget._dispatch('reader_trash', None)
        action.assert_called_once_with(self.ADDRESS, '102', 'trash')
        self.assertIsNone(self.widget._reader)
        self.assertFalse(self.widget.reader_view.isVisibleTo(self.widget))

    def test_back_button_returns_to_the_list(self):
        self.open_mail(_canned())
        self.widget._dispatch('reader_back', None)
        self.assertIsNone(self.widget._reader)

    def test_open_in_gmail_button_still_opens_the_right_conversation(self):
        self.open_mail(_canned())
        self.widget._dispatch('reader_open', None)
        url = self.open_url.call_args[0][0].toString()
        self.assertIn('authuser=test.persoon%40example.com', url)
        self.assertTrue(url.endswith('#inbox/abc'))

    def test_html_mail_is_shown_sanitized_with_a_toggle_to_the_text_version(self):
        self.open_mail(_canned(plain='alleen tekst', html='<p>met <b>opmaak</b></p><script>boem()</script>'))
        reader = self.widget._reader
        self.assertFalse(reader['show_html'])  # er is een tekstversie: die eerst
        self.widget._dispatch('reader_toggle', None)
        self.assertTrue(reader['show_html'])
        shown = self.widget.reader_view.toHtml()
        self.assertIn('opmaak', self.widget.reader_view.toPlainText())
        self.assertNotIn('boem', shown)

    def test_html_only_mail_opens_in_formatted_view(self):
        self.open_mail(_canned(plain='', html='<p>Alleen <i>opmaak</i></p>'))
        self.assertTrue(self.widget._reader['show_html'])
        self.assertIn('Alleen opmaak', self.widget.reader_view.toPlainText())

    def test_a_failed_download_shows_the_reason_and_marks_nothing(self):
        self.open_mail(_canned(ok=False))
        self.assertEqual(self.widget._reader['status'], 'error')
        self.assertIn('Geen verbinding', self.widget.reader_view.toPlainText())
        self.assertEqual(len(self.widget.states[self.ADDRESS]['messages']), 2)

    def test_an_unreadable_password_gives_an_error_without_connecting(self):
        with mock.patch.object(self.widget, '_account_password', side_effect=ValueError('stuk')), \
                mock.patch.object(gmail, 'fetch_message') as fetch:
            self.widget._dispatch('open_mail', (self.ADDRESS, self.message))
        fetch.assert_not_called()
        self.assertEqual(self.widget._reader['status'], 'error')

    def test_late_answer_for_a_mail_that_is_no_longer_open_is_ignored(self):
        self.open_mail(_canned('eerste mail'))
        self.widget._close_reader()
        self.widget._on_message_ready(self.ADDRESS, '102', _canned('te laat'))
        self.assertIsNone(self.widget._reader)

    def test_only_web_and_mail_links_are_opened(self):
        for good in ('https://example.com/x', 'http://example.com', 'mailto:a@example.com'):
            self.widget._on_reader_link(QUrl(good))
        self.assertEqual(self.open_url.call_count, 3)
        self.open_url.reset_mock()
        for bad in ('javascript:alert(1)', 'file:///C:/geheim.txt', 'ftp://example.com'):
            self.widget._on_reader_link(QUrl(bad))
        self.open_url.assert_not_called()

    def test_reading_screen_draws_buttons_and_does_not_crash(self):
        self.open_mail(_canned(plain='tekst', html='<p>x</p>', attachments=[{'name': 'a.pdf', 'size': 10}]))
        self.widget.grab()
        kinds = {hit[1] for hit in self.widget._hits}
        self.assertTrue({'reader_back', 'reader_trash', 'reader_open', 'reader_toggle'} <= kinds)

    def test_an_already_read_mail_is_not_counted_twice_when_trashed(self):
        self.widget.states[self.ADDRESS]['messages'] = []
        self.widget.states[self.ADDRESS]['unread'] = 3
        self.widget._drop_from_list(self.ADDRESS, '102')
        self.assertEqual(self.widget.states[self.ADDRESS]['unread'], 3)

    def test_removing_the_account_while_reading_closes_the_mail(self):
        self.open_mail(_canned())
        self.widget.states.pop(self.ADDRESS)
        self.widget.updateConfig({'accounts': []})
        self.assertIsNone(self.widget._reader)
        self.widget._sync_states()
        self.widget.config['accounts'] = [{'email': self.ADDRESS, 'name': 'Privé', 'password': gmail.encrypt_password('pw')}]
        self.widget._sync_states()


if __name__ == '__main__':
    unittest.main()
