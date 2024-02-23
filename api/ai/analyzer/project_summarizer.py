from api.ai.generators.project_clusterer import cluster_project
from api.ai.generators.project_summarizer import summarize_project
from api.models.project import Project


class ProjectSummarizer:
    def summarize_all_projects(self):
        for project in Project.objects.all():
            print(f"Summarizing project <{project.id}: {project.name}>")
            summarize_project(project)
            cluster_project(project)
