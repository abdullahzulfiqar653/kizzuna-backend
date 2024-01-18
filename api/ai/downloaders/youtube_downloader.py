import re

from django.utils import translation
from youtube_transcript_api import YouTubeTranscriptApi


class YoutubeDownloader:
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

    def format_segment_to_string(self, segment):
        mintues, seconds = divmod(round(segment["start"]), 60)
        start_time = f"{mintues}:{seconds:02}"
        return f"{start_time:>6}: {segment['text']}"

    def download(self, url):
        video_id = self.video_id_regex.search(url).group(1)
        language = translation.get_language().split("-")[0]
        transcript_dict = YouTubeTranscriptApi.get_transcript(
            video_id, languages=[language]
        )
        return "\n".join(
            self.format_segment_to_string(segment) for segment in transcript_dict
        )


__all__ = ["YoutubeDownloader"]
