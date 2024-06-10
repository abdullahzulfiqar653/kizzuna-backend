from api.ai.translator import GoogleTranslator


class TextProcessor:
    def __init__(self, text: str):
        self.text = text

    def set_translator(self, translator: GoogleTranslator):
        self.translator = translator
        return self

    def translate(self, language):
        # Translate the text
        # We convert \n to <br> before translating and convert it back
        # because google translator doesn't respect the line break character \n
        self.text = self.translator.translate(
            self.text.replace("\n", "<br>"), language
        ).replace("<br>", "\n")
        return self

    def truncate(self):
        lines = []
        length = 0
        for line in self.text.split("\n"):
            # The content state json structure for each line is about 120 chars
            length += len(line) + 120
            if length > 220_000:
                lines.append("...[text is truncated because it is too long]")
                break
            lines.append(line)
        self.text = "\n".join(lines)
        return self

    def to_lexical(self):
        return {
            "root": {
                "type": "root",
                "format": "",
                "indent": 0,
                "version": 1,
                "direction": "ltr",
                "children": [
                    {
                        "type": "paragraph",
                        "format": "",
                        "indent": 0,
                        "version": 1,
                        "children": [
                            {
                                "mode": "normal",
                                "text": paragraph,
                                "type": "text",
                                "style": "",
                                "detail": 0,
                                "format": 0,
                                "version": 1,
                            }
                        ],
                        "direction": "ltr",
                    }
                    for paragraph in self.text.split("\n")
                ],
            }
        }
