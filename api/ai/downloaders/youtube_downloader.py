import re

from django.utils import translation
from youtube_transcript_api import YouTubeTranscriptApi

from api.ai.paragrapher import Paragrapher


class YoutubeDownloader:
    paragrapher = Paragrapher()
    video_id_regex = re.compile(
        r"(?:youtube\.com\/(?:[^\/\n\s]+\/\S+\/|(?:v|e(?:mbed)?)\/|\S*?[?&]v=)"
        r"|youtu\.be\/)"
        r"([a-zA-Z0-9_-]{11})"
    )

    def is_youtube_link(self, url):
        match = self.video_id_regex.search(url)
        if match is None:
            # Cannot find video_id from url, so this is not a youtube link
            return False
        return True

    def group_segments(self, transcripts, group_size):
        """
        Segments in the transcript are too short.
        This function group several segments into one paragraph.
        It is a generator that returns a list of paragraphs.
        """
        current_group = []
        for segment in transcripts:
            text = segment.get("text", "")
            break_condition = len(current_group) >= 5 or text.startswith("[Music]")
            if break_condition is True and current_group:
                # Start a new group if break_condition is true
                yield " ".join(current_group)
                current_group = [text]
            else:
                current_group.append(text)

        # Append any remaining segments as a group
        if current_group:
            yield " ".join(current_group)

    def download(self, url) -> str:
        video_id = self.video_id_regex.search(url).group(1)
        language = translation.get_language().split("-")[0]
        transcript = YouTubeTranscriptApi.get_transcript(video_id, languages=[language])
        return "\n".join(self.group_segments(transcript, 5))


__all__ = ["YoutubeDownloader"]
