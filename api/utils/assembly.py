from typing import Any, Dict


def blank_transcript():
    return {
        "id": "",
        "utterances": [],
        "audio_duration": 0,
        "language_code": "en_us",
    }


class AssemblyProcessor:
    def __init__(self, json: Dict[str, Any]):
        self.json = json

    def to_transcript(self) -> Dict[str, Any]:
        return {
            "id": self.json["id"],
            "utterances": self.json["utterances"],
            "audio_duration": self.json["audio_duration"],
            "language_code": self.json["language_code"],
        }

    def get_text_in_range(self, start, end):
        result = [
            word["text"]
            for utterance in self.json["utterances"]
            for word in utterance["words"]
            if word["start"] >= start and word["end"] <= end
        ]
        return " ".join(result)

    def highlight(self, text: str, id: str):
        if text == "":
            return False

        # This assumes that the `text`s of the `words` have been stripped
        subtext = text.strip()
        indices = []
        capturing = False
        break_outer_loop = False
        for i, utterance in enumerate(self.json["utterances"]):
            if break_outer_loop:
                break
            for j, word in enumerate(utterance["words"]):
                if capturing:
                    if subtext.startswith(word["text"]):
                        # Continue capturing
                        indices.append((i, j))
                        subtext = subtext[len(word["text"]) :].strip()
                        if not subtext:
                            break_outer_loop = True
                            break
                    else:
                        # Reset capturing
                        capturing = False
                        subtext = text.strip()
                        indices = []
                else:
                    if subtext.startswith(word["text"]):
                        # Start capturing
                        capturing = True
                        indices.append((i, j))
                        subtext = subtext[len(word["text"]) :].strip()
                        if not subtext:
                            break_outer_loop = True
                            break
        if subtext:
            # Couldn't match the entire text
            return False

        for i, j in indices:
            self.json["utterances"][i]["words"][j].setdefault(
                "highlight_ids", []
            ).append(id)
        return True

    def update_transcript_highlights(self, start, end, highlight_id):
        capturing = False

        for utterance in self.json["utterances"]:
            for word in utterance["words"]:
                if capturing or word["start"] == start:
                    capturing = True
                    word.setdefault("highlight_ids", []).append(highlight_id)
                    if word["end"] == end:
                        return self.json

    def remove_transcript_highlight(self, start, end, highlight_id):
        capturing = False

        for utterance in self.json["utterances"]:
            for word in utterance["words"]:
                if capturing or word["start"] == start:
                    capturing = True
                    if "highlight_ids" in word.keys():
                        if highlight_id in word["highlight_ids"]:
                            word["highlight_ids"].remove(highlight_id)
                    if word["end"] == end:
                        return self.json

    def to_markdown(self) -> str:
        return "\n".join(
            [
                f"Speaker {utterance['speaker']}: {utterance['text']}"
                for utterance in self.json["utterances"]
            ]
        )
