from google.cloud import translate_v2 as translate


class GoogleTranslator:
    def __init__(self):
        self.client = translate.Client()

    def translate(self, text, language):
        return self.client.translate(text, target_language=language)["translatedText"]


google_translator = GoogleTranslator()
