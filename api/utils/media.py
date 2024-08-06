import os
import io
import ffmpeg
import tempfile
import secrets
from django.conf import settings


def create_thumbnail(file, thumbnail_path, time):
    ffmpeg.input(file, ss=time).output(thumbnail_path, vframes=1).run(
        overwrite_output=True, quiet=True
    )
    with open(thumbnail_path, "rb") as f:
        thumbnail_content = io.BytesIO(f.read()).read()
        thumbnail_size = os.path.getsize(thumbnail_path)
    thumbnail_name = f"thumbnail_{secrets.token_hex(5)}.jpg"
    return thumbnail_content, thumbnail_name, thumbnail_size


def cut_media_file(file, start_time, end_time):
    media_type = file.name.split(".")[-1]
    temp_fd, temp_file_name = tempfile.mkstemp(suffix=f".{media_type}")
    os.close(temp_fd)

    file_url = file.url if settings.USE_S3 else file.path
    # Use ffmpeg to cut the media file from start_time to end_time
    # - `output(processed_file_path, vcodec="copy", acodec="copy")` saves
    #   the segment to a new file, copying the original video and audio without re-encoding.
    # - `run(overwrite_output=True, quiet=True)` allow overwriting  and suppressing extra output.
    ffmpeg.input(file_url, ss=start_time, to=end_time).output(temp_file_name).run(
        overwrite_output=True, quiet=True
    )
    with open(temp_file_name, "rb") as f:
        clip_content = io.BytesIO(f.read()).read()
        file_size = os.path.getsize(temp_file_name)

    thumbnail_size = 0
    thumbnail_name = None
    thumbnail_content = None
    if media_type in ("mp4", "mov", "avi", "mkv"):
        temp_thumbnail_path = tempfile.mktemp(suffix=".jpg")
        thumbnail_content, thumbnail_name, thumbnail_size = create_thumbnail(
            temp_file_name, temp_thumbnail_path, (end_time - start_time) / 2
        )
        os.remove(temp_thumbnail_path)
    os.remove(temp_file_name)

    file_name = f"clip_{start_time}_{end_time}_{secrets.token_hex(3)}.{media_type}"
    return (
        clip_content,
        file_name,
        file_size,
        thumbnail_content,
        thumbnail_name,
        thumbnail_size,
    )
