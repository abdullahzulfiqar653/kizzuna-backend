from collections import namedtuple


def blank_transcript():
    return {
        "id": "",
        "utterances": [],
        "audio_duration": 0,
        "language_code": "en_us",
    }


class AssemblyProcessor:
    def __init__(self, json: dict):
        self.json = json

    def to_transcript(self) -> dict:
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

    def highlight(self, text: str, id: str) -> tuple[bool, int | None, int | None]:
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
            return False, None, None

        for i, j in indices:
            (
                self.json["utterances"][i]["words"][j]
                .setdefault("highlight_ids", [])
                .append(id)
            )
        start = self.json["utterances"][indices[0][0]]["words"][indices[0][1]]["start"]
        end = self.json["utterances"][indices[-1][0]]["words"][indices[-1][1]]["end"]
        return True, start, end

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

    def map_to_recall_speakers(self, recall_transcript: dict) -> dict:
        # Preprocess the recall transcript
        recall_utterances = [
            dict(
                start=round(utterance["words"][0]["start_timestamp"] * 1000),
                end=round(utterance["words"][-1]["end_timestamp"] * 1000),
                speaker=utterance["speaker"],
            )
            for utterance in recall_transcript
        ]

        # Construct the timeline
        Event = namedtuple("Event", ["time", "source", "action", "speaker"])
        utterances = {
            "assembly": self.json["utterances"],
            "recall": recall_utterances,
        }
        timeline = [
            Event(
                time=utterance[action],
                source=source,
                action=action,
                speaker=utterance["speaker"],
            )
            for source in ["assembly", "recall"]
            for utterance in utterances[source]
            for action in ["start", "end"]
        ]
        timeline.sort(key=lambda x: x.time)

        # Find the overlaps between the assembly speakers and the recall speakers
        speaker = {"assembly": None, "recall": None}
        start_time = 0
        overlaps = {}
        # Calculate the overlaps between the assembly speakers and the recall speakers
        for event in timeline:
            match event.action:
                case "start":
                    speaker[event.source] = event.speaker
                    if speaker["assembly"] and speaker["recall"]:
                        start_time = event.time
                case "end":
                    if speaker["assembly"] and speaker["recall"]:
                        overlaps.setdefault(speaker["assembly"], {}).setdefault(
                            speaker["recall"], 0
                        )
                        overlaps[speaker["assembly"]][speaker["recall"]] += (
                            event.time - start_time
                        )
                    speaker[event.source] = None

        # Construct the mapping based on the overlaps
        mapping = {
            key: max(value.items(), key=lambda x: x[1])[0]
            for key, value in overlaps.items()
        }

        # Map the speakers in the assembly transcript
        for utterance in self.json["utterances"]:
            utterance["speaker"] = mapping[utterance["speaker"]]
        return self.json

    def to_markdown(self) -> str:
        return "\n".join(
            [
                f"Speaker {utterance['speaker']}: {utterance['text']}"
                for utterance in self.json["utterances"]
            ]
        )
