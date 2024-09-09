from datetime import timedelta
from textwrap import dedent

from django.utils import timezone
from langchain.output_parsers import PydanticOutputParser
from langchain.prompts import ChatPromptTemplate
from langchain.schema.document import Document
from langchain.text_splitter import TokenTextSplitter
from langchain_openai.chat_models import ChatOpenAI
from pydantic.v1 import BaseModel

from api.ai import config
from api.ai.generators.utils import ParserErrorCallbackHandler, token_tracker
from api.ai.translator import google_translator
from api.models.note import Note
from api.models.task import Task
from api.models.user import User


def get_task_chain(task_types):
    class TaskSchema(BaseModel):
        title: str
        description: str
        type: str
        priority: str
        status: str
        due_date: str
        assigned_to: str

    class TasksSchema(BaseModel):
        tasks: list[TaskSchema]

    system_prompt = dedent(
        """
            Your task is to analyze a meeting transcript to extract specific follow-up actions. Only identify **clear and explicitly discussed** action items. Do not infer tasks from general discussion or ideas unless they are clearly assigned as tasks.
            
            Here are the task types you must consider. If a task does not match any of these types, ignore it:
            Task Types:
            <task_types>
            {{TASK_TYPES}}
            </task_types>

            Now, carefully read and analyze the following transcript:

            <transcript>
            {{TRANSCRIPT}}
            </transcript>
            
            Carefully read through the transcript and identify **only specific follow-up actions** that were clearly discussed and assigned. These are typically tasks that participants explicitly agree to complete after the meeting. Ignore vague suggestions or ideas unless they are directly turned into action items.

            For each task item you identify, extract the following information:

            1. Identify the tasks discussed in the transcript that relate to the provided task types.
            2. For each task, determine and generate the following attributes:
                a) Title: A concise title for the task.
                b) Description: A detailed description of the task, capturing all relevant information.
                c) Type: The task type from the provided list that best fits the task.
                d) Priority: The priority of the task (Low, Med, High) should strictly be one of these values (Med instead of Medium), based on the discussion.
                e) Status: The status of the task (Todo, Done, Overdue) as of the end of the meeting.
                f) Due Date: The due date for the task if mentioned or inferred.
                g) Assigned To: The person responsible for the task, if mentioned.

            3. Format your findings into a JSON structure with the following format:
                {
                    "tasks": [
                        {
                            "title": "<title of the task>",
                            "description": "<description of the task>",
                            "type": "<task type>",
                            "priority": "<priority of the task>",
                            "status": "<status of the task>",
                            "due_date": "<due date of the task>",
                            "assigned_to": "<person responsible for the task>",
                        },
                        {
                            // Additional action items...
                        }
                    ]
                }

            4. Ensure that each task is directly related to the discussion in the transcript and that the task type is accurately assigned.

            5. Double-check that all details are extracted correctly and that the JSON is properly formatted and valid.

            6. Double-check that all quotes are exact matches from the transcript.

            <example_output>
            {
                "tasks": [
                    {
                        "title": "Onboarding Process Review",
                        "description": "Review the current onboarding process and suggest improvements.",
                        "type": "Process Improvement",
                        "priority": "High",
                        "status": "Todo",
                        "due_date": "2024-09-01",
                        "assigned_to": "John Doe",
                    },
                    {
                        "title": "Customer Feedback Analysis",
                        "description": "Analyze the feedback from the last customer survey.",
                        "type": "Data Analysis",
                        "priority": "Med",
                        "status": "Todo",
                        "due_date": "2024-09-10",
                        "assigned_to": "Jane Smith",
                    }
                ]
            }
            </example_output>

            Guidelines for extracting information:
            - If multiple people are assigned to a task, list all names separated by commas in the "assigned_to" field.
            - If no specific due_date is mentioned, use "Not specified" for the "due_date" field.
            - The "title" should be the exact wording from the transcript that contains the title item information.
            - If a title is mentioned multiple times, use the most complete reference as the title.
            - Ignore any general statements, ideas, or discussions that do not clearly outline a task.
            - Only extract action items that have clear assignments, deadlines, or responsibilities.

            After analyzing the transcript, compile all the task items you've identified into the JSON format described above. Make sure to double-check your work for accuracy and completeness.
            
            Must Check for any duplicate or similar tasks in the list and consolidate them. For example, if multiple tasks have the same or similar title or description, merge them into a single task entry.
            
            Provide your final answer in JSON format, ensuring it's a valid JSON structure. Do not include anything else other than the JSON.
        """
    )
    llm = ChatOpenAI(model=config.model)
    prompt = ChatPromptTemplate.from_messages(
        [
            ("human", system_prompt),
        ],
        template_format="jinja2",
    )
    parser = PydanticOutputParser(pydantic_object=TasksSchema)
    chain = prompt | llm.bind(response_format={"type": "json_object"}) | parser
    return chain


def generate_tasks(note: Note, created_by: User):
    text_splitter = TokenTextSplitter(
        model_name=config.model,
        chunk_size=config.chunk_size,
        chunk_overlap=config.chunk_overlap,
    )
    task_types = note.project.task_types.all()

    if not task_types:
        return

    bot = User.objects.get(username="bot@raijin.ai")
    doc = Document(page_content=note.get_markdown())
    docs = text_splitter.split_documents([doc])

    with token_tracker(note.project, note, "generate-tasks", created_by):
        outputs = [
            {
                "output": get_task_chain(task_types).invoke(
                    {
                        "TRANSCRIPT": doc.page_content,
                        "TASK_TYPES": task_types,
                    },
                    config={"callbacks": [ParserErrorCallbackHandler()]},
                ),
            }
            for doc in docs
        ]

    if not outputs:
        return

    task_type_mapping = {
        task_type.name: task_type for task_type in note.project.task_types.all()
    }

    generated_tasks = [
        Task(
            title=google_translator.translate(
                task["title"],
                note.project.language,
            ),
            description=google_translator.translate(
                task["description"],
                note.project.language,
            ),
            type=task_type_mapping.get(task["type"]),
            priority=task["priority"],
            status=task["status"],
            due_date=timezone.now() + timedelta(days=3),
            # assigned_to=task["assigned_to"],
            created_by=bot,
            note=note,
        )
        for output in outputs
        for task in output["output"].dict()["tasks"]
    ]
    Task.objects.bulk_create(generated_tasks)
