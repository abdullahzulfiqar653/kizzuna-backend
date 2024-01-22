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

    def download(self, url) -> str:
        video_id = self.video_id_regex.search(url).group(1)
        language = translation.get_language().split("-")[0]
        transcript = YouTubeTranscriptApi.get_transcript(video_id, languages=[language])
        segments = (segment["text"] for segment in transcript)
        return self.paragrapher.paragraphing(segments)


__all__ = ["YoutubeDownloader"]
