import logging
from django.test import TestCase
from django.core.files import File
from django.core.files.base import ContentFile

from api.models.user import User
from api.models.note import Note
from api.models.project import Project
from api.models.workspace import Workspace

from api.ai.transcribers.text_transcriber import text_transcriber
from api.ai.transcribers.docx_transcriber import docx_transcriber
from api.ai.transcribers.pdfium_transcriber import pdfium_transcriber


class TestTranscribers(TestCase):
    def setUp(self) -> None:
        """Reduce the log level to avoid errors like 'not found'"""
        logger = logging.getLogger("django.request")
        self.previous_level = logger.getEffectiveLevel()
        logger.setLevel(logging.ERROR)

        self.user = User.objects.create_user(username="user", password="password")
        self.workspace = Workspace.objects.create(name="workspace", owned_by=self.user)
        self.project = Project.objects.create(name="project", workspace=self.workspace)

        with open("api/tests/files/test.pdf", "rb") as file:
            file_content = ContentFile(file.read(), "test.pdf")

        self.note = Note.objects.create(
            title="Sample Note",
            project=self.project,
            author=self.user,
            file=file_content,
        )
        return super().setUp()

    def tearDown(self) -> None:
        if self.note.file:
            self.note.file.delete(save=False)
        super().tearDown()

    def test_pdfium_transcriber(self):
        filetype = "pdf"
        language = "en"
        result = pdfium_transcriber.transcribe(self.note.file, filetype, language)
        result_text = result.to_lexical()["root"]["children"][0]["children"][0]["text"]
        self.assertTrue(result.to_lexical())
        self.assertIsInstance(result.to_lexical(), dict)
        self.assertEqual(result_text, "This is a test file")
        self.assertIn(filetype, pdfium_transcriber.supported_filetypes)

    def test_docx_transcriber(self):
        with open("api/tests/files/test.docx", "rb") as docx_file:
            file = File(docx_file)
            filetype = "docx"
            language = "en"

            result = docx_transcriber.transcribe(file, filetype, language)
            self.assertTrue(result)
            self.assertEqual(result.markdown, "This is a test file\n\n")
            self.assertIn(filetype, docx_transcriber.supported_filetypes)

    def test_text_transcriber(self):
        with open("api/tests/files/test.txt", "r") as txt_file:
            file = File(txt_file)
            filetype = "txt"
            language = "en"

            result = text_transcriber.transcribe(file, filetype, language)
            result_text = result.to_lexical()["root"]["children"][0]["children"][0][
                "text"
            ]
            self.assertTrue(result.to_lexical())
            self.assertIsInstance(result.to_lexical(), dict)
            self.assertEqual(result_text, "This is a test file")
            self.assertIn(filetype, text_transcriber.supported_filetypes)
