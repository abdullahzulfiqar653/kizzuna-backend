import os
import secrets
import tempfile

import ffmpeg
from django.conf import settings
from django.core.files.base import ContentFile
from django.db.models.fields.files import FieldFile


def create_thumbnail(file: FieldFile, time: float) -> ContentFile:
    file_url = file.url if settings.USE_S3 else file.path
    out, err = (
        ffmpeg.input(file_url, ss=time)
        .output("pipe:1", vframes=1, format="image2")
        .run(overwrite_output=True, quiet=True)
    )
    thumbnail_name = f"thumbnail_{secrets.token_hex(5)}.jpg"
    return ContentFile(out, name=thumbnail_name)


def cut_media_file(file: FieldFile, start_time: float, end_time: float) -> ContentFile:
    media_type = file.name.split(".")[-1]
    file_url = file.url if settings.USE_S3 else file.path

    with tempfile.NamedTemporaryFile(suffix=f".{media_type}") as temp_file:
        # For input, we use file_url because ffmpeg can stream from URL
        # For output, we use temp_file because for video cutting ffmpeg expect it to be seekable
        (
            ffmpeg.input(file_url, ss=start_time, to=end_time)
            .output(temp_file.name, codec="copy", movflags="faststart")
            .overwrite_output()
            .run(quiet=True)
        )
        temp_file.seek(0)
        file_name = f"clip_{start_time}_{end_time}_{secrets.token_hex(3)}.{media_type}"
        clip = ContentFile(temp_file.read(), name=file_name)

    return clip


def merge_media_files(files):
    with tempfile.NamedTemporaryFile(suffix=".mp4") as temp_file:
        if settings.USE_S3:
            highlight_urls = "\n".join(f"file '{file.url}'" for file in files)
        else:
            # For local files, we need to use file: prefix
            # Ref: https://askubuntu.com/a/1368547
            highlight_urls = "\n".join(f"file file:'{file.path}'" for file in files)

        (
            ffmpeg.input(
                "pipe:",
                format="concat",
                safe=0,
                protocol_whitelist="file,http,https,tcp,tls,pipe",
            )
            .output(temp_file.name, c="copy", movflags="+faststart")
            .overwrite_output()
            .run(input=highlight_urls.encode(), quiet=True)
        )
        temp_file.seek(0)
        file = ContentFile(temp_file.read(), os.path.basename(temp_file.name))
    return file


def process_mp4_for_streaming(file):
    with tempfile.NamedTemporaryFile(suffix=".mp4") as temp_file:
        output_file = temp_file.name
        (
            ffmpeg.input("pipe:0")
            .output(output_file, movflags="faststart", codec="copy")
            .overwrite_output()
            .run(input=file.read(), quiet=True)
        )
        temp_file.seek(0)
        file = ContentFile(temp_file.read(), name=file.name)
    return file
