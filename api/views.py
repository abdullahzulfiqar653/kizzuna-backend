# api/views.py
import secrets
from datetime import datetime, timedelta
from textwrap import dedent

from django.conf import settings
from django.contrib.auth.models import User as AuthUser
from django.core.mail import send_mail
from django.utils import timezone
from django.utils.module_loading import import_string
from django.views.decorators.debug import sensitive_post_parameters
from rest_framework import exceptions, generics
from rest_framework.permissions import AllowAny
from rest_framework_simplejwt.views import TokenObtainPairView, api_settings

from api.serializers import (
    DoPasswordResetSerializer,
    InvitationSignupSerializer,
    InvitationStatusSerializer,
    InviteUserSerializer,
    PasswordUpdateSerializer,
    RequestPasswordResetSerializer,
    SignupSerializer,
)
from project.models import Project
from user.models import Invitation


# Signup
class SignupView(generics.CreateAPIView):
    queryset = AuthUser.objects.all()
    serializer_class = SignupSerializer
    permission_classes = [AllowAny]

    sensitive_post_parameters("password")

    def create(self, request, *args, **kwargs):
        return super().create(request, *args, **kwargs)


class PasswordUpdateView(generics.CreateAPIView):
    serializer_class = PasswordUpdateSerializer

    sensitive_post_parameters("old_password", "password")

    def create(self, request, *args, **kwargs):
        return super().create(request, *args, **kwargs)


class RequestPasswordResetView(generics.CreateAPIView):
    serializer_class = RequestPasswordResetSerializer
    permission_classes = [AllowAny]


class DoPasswordResetView(generics.CreateAPIView):
    serializer_class = DoPasswordResetSerializer
    permission_classes = [AllowAny]

    sensitive_post_parameters("password")

    def create(self, request, *args, **kwargs):
        return super().create(request, *args, **kwargs)


# Token
class TokenObtainPairAndRefreshView(TokenObtainPairView):
    def get_serializer_class(self):
        match self.request.data.get("grant_type"):
            case "password" | None:
                return import_string(api_settings.TOKEN_OBTAIN_SERIALIZER)
            case "refresh_token":
                return import_string(api_settings.TOKEN_REFRESH_SERIALIZER)


# Invite user
class InviteUserView(generics.CreateAPIView):
    serializer_class = InviteUserSerializer

    def perform_create(self, serializer):
        project_id = serializer.data["project_id"]
        emails = serializer.data["emails"]

        project = self.get_project(project_id)
        workspace = self.get_workspace(project)
        emails, existing_auth_users = self.handle_existing_users(
            emails, workspace, project
        )
        self.send_notification_emails(existing_auth_users, workspace, project)
        email_tokens = self.create_invitations(emails, workspace, project)
        self.send_invitation_emails(email_tokens, workspace, project)

    def get_workspace(self, project):
        workspace = project.workspace
        if not workspace.members.contains(self.request.user):
            raise exceptions.PermissionDenied("User doesn't have access to workspace.")
        return workspace

    def get_project(self, project_id):
        project = Project.objects.get(id=project_id)
        if not project.users.contains(self.request.user):
            raise exceptions.PermissionDenied("User doesn't have access to project.")
        return project

    def handle_existing_users(self, emails, workspace, project):
        existing_auth_users = AuthUser.objects.filter(username__in=emails)
        for auth_user in existing_auth_users:
            auth_user.workspaces.add(workspace)
            auth_user.projects.add(project)
            emails.remove(auth_user.username)
        return emails, existing_auth_users

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

    def send_notification_emails(self, auth_users, workspace, project):
        email_template = dedent(
            """
            Hi, you are invited to join our project "{project}" in workspace "{workspace}".
            Click the following link to go to the project: 
            {frontend_url}/projects/{project_id}/reports
        """
        )
        auth_user_emails = [auth_user.username for auth_user in auth_users]
        for email in auth_user_emails:
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


class InvitationStatusRetrieveView(generics.RetrieveAPIView):
    serializer_class = InvitationStatusSerializer
    permission_classes = [AllowAny]
    lookup_field = "token"
    queryset = Invitation.objects.all()


class InvitationSignupCreateView(generics.CreateAPIView):
    serializer_class = InvitationSignupSerializer
    permission_classes = [AllowAny]

    sensitive_post_parameters("password")

    def create(self, request, *args, **kwargs):
        return super().create(request, *args, **kwargs)
