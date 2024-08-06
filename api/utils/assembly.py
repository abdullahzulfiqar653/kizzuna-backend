from typing import Dict, Any


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
