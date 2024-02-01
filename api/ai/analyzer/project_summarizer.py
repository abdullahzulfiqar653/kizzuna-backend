import datetime

from django.utils import timezone
from django.utils.translation import gettext
from langchain.prompts import ChatPromptTemplate
from langchain.schema.document import Document
from langchain.text_splitter import TokenTextSplitter
from langchain_community.chat_models import ChatOpenAI

from api.ai import config
from api.models.project import Project


class ProjectSummarizer:
    def summarize_project(self, project):
        llm = ChatOpenAI(model=config.model)
        prompt = ChatPromptTemplate.from_messages(
            [
                (
                    "system",
                    gettext(
                        "The following represents individual summaries "
                        "for each report generated by the user throughout the week. "
                        "To offer the user a comprehensive overview "
                        "of the week's reports and furnish strategic recommendations, "
                        "kindly compile an executive summary. "
                        "This summary should encapsulate key insights "
                        "from each report and provide strategic guidance "
                        "to assist the user in making informed decisions."
                    ),
                ),
                ("human", "\n\n{text}"),
            ]
        )
        chain = prompt | llm
        text_splitter = TokenTextSplitter(
            model_name=config.model,
            chunk_size=config.chunk_size,
            chunk_overlap=config.chunk_overlap,
        )

        cutoff = timezone.now() - datetime.timedelta(weeks=20)
        notes = project.notes.filter(created_at__gt=cutoff).order_by("-created_at")
        note_summaries_list = [
            summary_item
            for summary in notes.values_list("summary", flat=True)
            for summary_item in summary
        ]
        filtered_note_summaries_list = list(
            filter(lambda s: s.strip(), note_summaries_list)
        )
        if len(filtered_note_summaries_list) == 0:
            project.summary = "No report is created for the past week."
        else:
            note_summaries_string = "- " + "\n- ".join(filtered_note_summaries_list)
            doc = Document(page_content=note_summaries_string)
            truncated = text_splitter.split_documents([doc])[0].page_content
            print("\n\n", truncated, "\n")
            output = chain.invoke({"text": truncated})
            project.summary = output.content
        project.save()

    def summarize_all_projects(self):
        for project in Project.objects.all():
            print(f"Summarizing project <{project.id}: {project.name}>")
            self.summarize_project(project)
