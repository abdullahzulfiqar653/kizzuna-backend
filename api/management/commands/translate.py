from glob import glob

import polib
from django.core.management.base import BaseCommand
from google.cloud import translate_v2 as google_translate
from tqdm import tqdm


class Command(BaseCommand):
    help = "Translate all the untranslated messages using Google Translate."

    def handle(self, *args, **options):
        client = google_translate.Client()
        files = glob("translations/*/LC_MESSAGES/django.po")
        for file in tqdm(files, desc="File:"):
            language = file.split("/")[1]
            po = polib.pofile(file)
            for entry in tqdm(po.untranslated_entries(), desc="Entry:", leave=False):
                response = client.translate(entry.msgid, target_language=language)
                entry.msgstr = response["translatedText"]
            po.save()
