# seeders/seed.py

import os
import django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'cradarai.settings')

from faker import Faker
from django.contrib.auth.models import User as AuthUser
from user.models import User
from workspace.models import Workspace
from project.models import Project
from note.models import Note

fake = Faker()

def create_auth_users(n=10, email=None, password=None):
    for _ in range(n):
        # if email is not None:
        #     email = email
        # else:
        #     email = fake.unique.email()
        email = fake.unique.email()

        auth_user = AuthUser(
            email=email, 
            username=email, 
            first_name=fake.first_name(), 
            last_name=fake.last_name()
            )
        if password is not None:
            auth_user.set_password(password)
        else:
            auth_user.set_password(fake.password())
        auth_user.save()

        user = User.objects.create(
            first_name=auth_user.first_name,
            last_name=auth_user.last_name,
            auth_user_id=auth_user.id,
        )

        print(f"Created user {auth_user.email}")

def create_workspaces(n=10):
    users = AuthUser.objects.all()

    for _ in range(n):
        name = fake.unique.company()
        workspace = Workspace.objects.create(name=name)
        
        # Assign some users to this workspace
        for user in users:
            if fake.random_element(elements=(True, False)):  # Randomly decide if this user should be in this workspace
                workspace.members.add(user)
        
        print(f"Created workspace {name}")

def create_projects(n=10):

    random_workspace = Workspace.objects.first()

    for _ in range(n):
        project = Project.objects.create(
            name=fake.sentence(nb_words=5, variable_nb_words=False),
            description=fake.sentence(nb_words=20, variable_nb_words=False),
            workspace_id=random_workspace.id
        )

        print(f"Created project {project.name}")


def create_reports(n=10):

    random_project = Project.objects.first()
    random_user = User.objects.first()
    random_workspace = Workspace.objects.first()

    for _ in range(n):
        note = Note.objects.create(
            title=fake.sentence(nb_words=5, variable_nb_words=False),
            content=fake.sentence(nb_words=20, variable_nb_words=False),
            summary=fake.sentence(nb_words=20, variable_nb_words=False),
            company_name=fake.unique.company(),
            project_id=random_project.id,
            author_id=random_user.id,
            workspace_id=random_workspace.id,
            code=fake.passport_number()[:4]
        )

        print(f"Created note {note.title}")

def run():
    num_users = 5
    num_workspaces = 1
    num_projects = 1
    num_reports = 10
    
    # create usable self
    create_auth_users(1, 'testing@testing.com', 'testing')
    create_auth_users(num_users)
    create_workspaces(num_workspaces)
    create_projects(num_projects)
    create_reports(num_reports)

    

if __name__ == "__main__":
    run()