import importlib.util
import json
import os
import shutil
import sys
import tempfile
import time
import types
import unittest
from unittest import mock

os.environ.setdefault('QT_QPA_PLATFORM', 'offscreen')

from PyQt5.QtWidgets import QApplication

_app = QApplication.instance() or QApplication([])

# openai zit niet in requirements.txt (de widget regelt dat zelf); in een kale testomgeving
# volstaat een lege stand-in, want de tests vervangen de aanroepen toch.
try:
    import openai  # noqa: F401
except ImportError:
    sys.modules['openai'] = types.ModuleType('openai')

_SOURCE = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                       'widgets', 'LLM Chat', 'LLMChat.py')

# De widget bewaart zijn config naast het eigen .py-bestand. Daarom een kopie in een
# tijdelijke map laden, zodat de tests nooit in de projectmap schrijven.
_TMP = tempfile.TemporaryDirectory()
_COPY = os.path.join(_TMP.name, 'LLMChat.py')
shutil.copyfile(_SOURCE, _COPY)
_spec = importlib.util.spec_from_file_location('llm_chat_under_test', _COPY)
llm = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(llm)

CONFIG_FILE = os.path.join(_TMP.name, 'llm_chat_widget_config.json')
SECRET = 'sk-test-GEHEIM-0123456789'


def _wait_until(condition, timeout=5.0):
    end = time.time() + timeout
    while time.time() < end:
        _app.processEvents()
        if condition():
            return True
        time.sleep(0.01)
    return False


def _write_config(**values):
    with open(CONFIG_FILE, 'w') as f:
        json.dump(values, f)


def _read_config_text():
    with open(CONFIG_FILE) as f:
        return f.read()


class TestSecretEncryption(unittest.TestCase):
    def test_round_trip_and_not_readable_in_the_token(self):
        token = llm.encrypt_secret(SECRET)
        self.assertNotIn(SECRET, token)
        self.assertEqual(llm.decrypt_secret(token), SECRET)

    @unittest.skipUnless(sys.platform == 'win32', 'DPAPI bestaat alleen op Windows')
    def test_uses_windows_dpapi(self):
        self.assertTrue(llm.encrypt_secret(SECRET).startswith('dpapi:'))


class TestSharedDpapiWithOtherWidgets(unittest.TestCase):
    """Gmail Inbox en LLM Chat gebruiken allebei Windows DPAPI en draaien in één proces."""

    @classmethod
    def setUpClass(cls):
        spec = importlib.util.spec_from_file_location(
            'gmail_for_dpapi_test',
            os.path.join(os.path.dirname(_SOURCE), '..', 'gmail_inbox_widget', 'gmail_inbox_widget.py'))
        cls.gmail = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(cls.gmail)

    def test_the_widgets_do_not_break_each_others_encryption(self):
        for _ in range(2):  # afwisselend, in beide volgordes
            gmail_token = self.gmail.encrypt_password('gmail-wachtwoord')
            llm_token = llm.encrypt_secret(SECRET)
            self.assertEqual(self.gmail.decrypt_password(gmail_token), 'gmail-wachtwoord')
            self.assertEqual(llm.decrypt_secret(llm_token), SECRET)


class TestAskOpenAI(unittest.TestCase):
    def test_uses_the_new_api_when_available(self):
        client = mock.Mock()
        client.chat.completions.create.return_value = mock.Mock(
            choices=[mock.Mock(message=mock.Mock(content='antwoord nieuw'))])
        fake = types.SimpleNamespace(OpenAI=mock.Mock(return_value=client))
        with mock.patch.object(llm, 'openai', fake):
            self.assertEqual(llm.ask_openai('sleutel', 'gpt-4o', 'hoi'), 'antwoord nieuw')
        fake.OpenAI.assert_called_once_with(api_key='sleutel')

    def test_falls_back_to_openai_0_27_which_ships_with_the_app(self):
        # Dit is de versie die in de .exe zit; die kent openai.OpenAI niet.
        create = mock.Mock(return_value={'choices': [{'message': {'content': 'antwoord oud'}}]})
        fake = types.SimpleNamespace(ChatCompletion=types.SimpleNamespace(create=create))
        with mock.patch.object(llm, 'openai', fake):
            self.assertEqual(llm.ask_openai('sleutel', 'gpt-3.5-turbo', 'hoi'), 'antwoord oud')
        create.assert_called_once_with(model='gpt-3.5-turbo', messages=[{'role': 'user', 'content': 'hoi'}],
                                       api_key='sleutel')


class TestWidgetKeyHandling(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        _write_config(api_key='', model='gpt-4o')
        cls.widget = llm.LLMChatWidget()
        cls.addClassCleanup(cls.widget.close)

    def setUp(self):
        self.widget.flush_config()
        self.widget.config['api_key'] = ''
        self.widget.chat_display.clear()
        self.widget.send_button.setEnabled(True)

    def test_the_key_is_stored_encrypted_not_as_plain_text(self):
        self.widget.config['api_key'] = SECRET
        self.widget.save_config()
        self.widget.flush_config()
        stored = _read_config_text()
        self.assertNotIn(SECRET, stored)
        self.assertIn('api_key_enc', stored)
        self.assertNotIn('"api_key"', stored)

    def test_an_old_plain_text_key_is_read_and_then_encrypted(self):
        _write_config(api_key=SECRET, model='gpt-4o')
        widget = llm.LLMChatWidget()
        try:
            self.assertEqual(widget.config['api_key'], SECRET)  # blijft bruikbaar
            widget.flush_config()
            self.assertNotIn(SECRET, _read_config_text())  # maar staat niet meer leesbaar op schijf
            reloaded = widget.load_config()
            self.assertEqual(reloaded['api_key'], SECRET)
        finally:
            widget.close()

    def test_an_unreadable_stored_key_does_not_crash_loading(self):
        _write_config(api_key_enc='dpapi:geen-geldige-base64!!', model='gpt-4o')
        with self.assertLogs('DesktopCustomizer.LLMChatWidget', level='ERROR'):
            config = self.widget.load_config()
        self.assertEqual(config['api_key'], '')

    def test_the_key_never_ends_up_in_the_log(self):
        with self.assertLogs('DesktopCustomizer.LLMChatWidget', level='DEBUG') as captured:
            self.widget.updateConfig({'api_key': SECRET, 'model': 'gpt-4o'})
            self.widget.flush_config()
            self.widget.load_config()
            with mock.patch.object(llm, 'ask_openai', side_effect=RuntimeError(f'Incorrect key {SECRET}')):
                self.widget.input_field.setPlainText('hoi')
                self.widget.send_message()
                self.assertTrue(_wait_until(lambda: self.widget.send_button.isEnabled()))
        self.assertNotIn(SECRET, '\n'.join(captured.output))


class TestSendingDoesNotFreezeTheDesktop(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        _write_config(api_key=SECRET, model='gpt-4o')
        cls.widget = llm.LLMChatWidget()
        cls.addClassCleanup(cls.widget.close)

    def setUp(self):
        self.widget.chat_display.clear()
        self.widget.send_button.setEnabled(True)

    def test_send_returns_immediately_and_the_answer_arrives_later(self):
        def slow_answer(api_key, model, user_input):
            time.sleep(0.5)
            return 'het antwoord'

        with mock.patch.object(llm, 'ask_openai', side_effect=slow_answer):
            self.widget.input_field.setPlainText('hoi')
            started = time.time()
            self.widget.send_message()
            self.assertLess(time.time() - started, 0.25)
            self.assertFalse(self.widget.send_button.isEnabled())  # geen dubbele verzoeken tegelijk
            self.assertTrue(_wait_until(lambda: 'AI: het antwoord' in self.widget.chat_display.toPlainText()))
            self.assertTrue(_wait_until(lambda: self.widget.send_button.isEnabled()))

    def test_errors_are_shown_in_the_chat_and_the_button_comes_back(self):
        with mock.patch.object(llm, 'ask_openai', side_effect=RuntimeError('kapot')):
            self.widget.input_field.setPlainText('hoi')
            self.widget.send_message()
            self.assertTrue(_wait_until(lambda: 'Error: kapot' in self.widget.chat_display.toPlainText()))
            self.assertTrue(_wait_until(lambda: self.widget.send_button.isEnabled()))

    def test_without_a_key_nothing_is_sent(self):
        self.widget.config['api_key'] = ''
        with mock.patch.object(llm, 'ask_openai') as ask:
            self.widget.input_field.setPlainText('hoi')
            self.widget.send_message()
        ask.assert_not_called()
        self.assertIn('no OpenAI API key', self.widget.chat_display.toPlainText())
        self.widget.config['api_key'] = SECRET


if __name__ == '__main__':
    unittest.main()
