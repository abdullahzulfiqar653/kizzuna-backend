# api/views.py
import secrets
from datetime import datetime, timedelta
from textwrap import dedent

from django.conf import settings
from django.core.mail import send_mail
from django.utils import timezone
from rest_framework import generics

from api.models.invitation import Invitation
from api.models.user import User
from api.serializers.auth import InviteUserSerializer


# Invite user
class ProjectInvitationCreateView(generics.CreateAPIView):
    serializer_class = InviteUserSerializer

    def perform_create(self, serializer):
        emails = serializer.data["emails"]

        project = self.request.project
        workspace = project.workspace
        emails, existing_users = self.handle_existing_users(emails, workspace, project)
        self.send_notification_emails(existing_users, workspace, project)
        email_tokens = self.create_invitations(emails, workspace, project)
        self.send_invitation_emails(email_tokens, workspace, project)

    def handle_existing_users(self, emails, workspace, project):
        existing_users = User.objects.filter(username__in=emails)
        for user in existing_users:
            user.workspaces.add(workspace)
            user.projects.add(project)
            emails.remove(user.username)
        return emails, existing_users

    def create_invitations(self, emails, workspace, project):
        expire_at = datetime.now() + timedelta(seconds=settings.INVITATION_LINK_TIMEOUT)
        expire_at_tz = timezone.make_aware(expire_at)

        email_tokens = dict()
        for email in emails:
            token = secrets.token_hex(16)
            Invitation.objects.create(
                sender=self.request.user,
                recipient_email=email,
                token=token,
                workspace=workspace,
                project=project,
                expires_at=expire_at_tz,
                is_used=False,
            )
            email_tokens[email] = token
        return email_tokens

    def send_notification_emails(self, users, workspace, project):
        email_template = dedent(
            """
            Hi, you are invited to join our project "{project}" in workspace "{workspace}".
            Click the following link to go to the project: 
            {frontend_url}/projects/{project_id}/reports
        """
        )
        user_emails = [user.username for user in users]
        for email in user_emails:
            message = email_template.format(
                frontend_url=settings.FRONTEND_URL,
                workspace=workspace.name,
                project=project.name,
                project_id=project.id,
            )
            send_mail(
                subject="Invitation to our project",
                from_email=None,
                message=message,
                recipient_list=[email],
            )

    def send_invitation_emails(self, email_tokens, workspace, project):
        email_template = dedent(
            """
            Hi, you are invited to join our project "{project}" in workspace "{workspace}".
            Click the following link to sign up: 
            {frontend_url}/auth/invitedsignup/?token={token}
        """
        )
        for email, token in email_tokens.items():
            message = email_template.format(
                frontend_url=settings.FRONTEND_URL,
                token=token,
                workspace=workspace.name,
                project=project.name,
            )
            send_mail(
                subject="Invitation to our project",
                from_email=None,
                message=message,
                recipient_list=[email],
            )
