import imaplib
import importlib.util
import os
import sys
import tempfile
import unittest
from datetime import datetime
from unittest import mock

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


class FakeIMAP:
    instances = []
    uids = b'101 102 103'

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
        if command == 'FETCH':
            return 'OK', FETCH_DATA
        return 'OK', [b'done']

    def logout(self):
        self.calls.append(('logout',))


class TestHelpers(unittest.TestCase):
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
        result = gmail.fetch_account('me@gmail.com', 'abcd efgh', max_messages=2)
        self.assertTrue(result['ok'])
        self.assertEqual(result['unread'], 3)
        self.assertEqual(len(result['messages']), 2)

    def test_mailbox_is_opened_read_only_so_checking_never_marks_mail_as_read(self):
        gmail.fetch_account('me@gmail.com', 'pw')
        calls = FakeIMAP.instances[0].calls
        self.assertIn(('select', 'INBOX', True), calls)
        fetch = [c for c in calls if c[:2] == ('uid', 'FETCH')][0]
        self.assertIn('BODY.PEEK', fetch[3])

    def test_app_password_spaces_are_stripped(self):
        gmail.fetch_account('me@gmail.com', 'abcd efgh ijkl mnop')
        self.assertIn(('login', 'me@gmail.com', 'abcdefghijklmnop'), FakeIMAP.instances[0].calls)

    def test_only_the_newest_messages_are_fetched(self):
        FakeIMAP.uids = b' '.join(str(n).encode() for n in range(1, 51))
        gmail.fetch_account('me@gmail.com', 'pw', max_messages=3)
        fetch = [c for c in FakeIMAP.instances[0].calls if c[:2] == ('uid', 'FETCH')][0]
        self.assertEqual(fetch[2], b'48,49,50')

    def test_empty_inbox(self):
        FakeIMAP.uids = b''
        result = gmail.fetch_account('me@gmail.com', 'pw')
        self.assertTrue(result['ok'])
        self.assertEqual((result['unread'], result['messages']), (0, []))

    def test_bad_password_gives_friendly_error_instead_of_raising(self):
        result = gmail.fetch_account('me@gmail.com', 'bad')
        self.assertFalse(result['ok'])
        self.assertIn('Inloggen mislukt', result['error'])

    def test_always_logs_out(self):
        gmail.fetch_account('me@gmail.com', 'pw')
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
            result = gmail.fetch_account('me@gmail.com', 'pw')
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
        gmail.mail_action('me@gmail.com', 'pw', '102', 'read')
        self.assertIn(('uid', 'STORE', '102', '+FLAGS', '(\\Seen)'), FakeIMAP.instances[0].calls)

    def test_trash_adds_trash_label_and_never_expunges(self):
        gmail.mail_action('me@gmail.com', 'pw', '102', 'trash')
        calls = FakeIMAP.instances[0].calls
        self.assertIn(('uid', 'STORE', '102', '+X-GM-LABELS', '(\\Trash)'), calls)
        self.assertFalse([c for c in calls if 'EXPUNGE' in str(c).upper()])

    def test_unknown_action_is_rejected(self):
        with self.assertRaises(ValueError):
            gmail.mail_action('me@gmail.com', 'pw', '102', 'explode')
        self.assertEqual(FakeIMAP.instances[0].calls[-1], ('logout',))


if __name__ == '__main__':
    unittest.main()
