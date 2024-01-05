import logging
import secrets
from datetime import datetime, timedelta

from django.conf import settings
from django.contrib.auth.models import User as AuthUser
from django.utils import timezone
from rest_framework import status
from rest_framework.test import APITestCase

from project.models import Project
from user.models import Invitation
from workspace.models import Workspace


class TestAuthUserRetrieveUpdateDestroyView(APITestCase):
    def setUp(self) -> None:
        self.user = AuthUser.objects.create_user(username="user", password="password")
        self.outsider = AuthUser.objects.create_user(
            username="outsider", password="password"
        )
        self.user_count = AuthUser.objects.count()
        self.username_set = set(AuthUser.objects.values_list("username", flat=True))

    def test_user_update_email(self):
        self.client.force_authenticate(self.user)
        url = "/api/auth-users/"
        response = self.client.patch(url, data={"email": "user@example.com"})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.user.refresh_from_db()
        self.assertEqual(self.user.username, "user@example.com")

    def test_user_delete_account(self):
        self.client.force_authenticate(self.user)
        url = "/api/auth-users/"
        response = self.client.delete(url)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertEqual(AuthUser.objects.count(), self.user_count - 1)
        self.assertSetEqual(
            set(AuthUser.objects.values_list("username", flat=True)),
            self.username_set - {"user"},
        )

    def test_outsider_delete_account(self):
        self.client.force_authenticate(self.outsider)
        url = "/api/auth-users/"
        response = self.client.delete(url)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertEqual(AuthUser.objects.count(), self.user_count - 1)
        self.assertSetEqual(
            set(AuthUser.objects.values_list("username", flat=True)),
            self.username_set - {"outsider"},
        )


class TestInvitationStatusRetrieveView(APITestCase):
    def setUp(self) -> None:
        """Reduce the log level to avoid errors like 'not found'"""
        logger = logging.getLogger("django.request")
        self.previous_level = logger.getEffectiveLevel()
        logger.setLevel(logging.ERROR)

        # Create user, workspace and project
        self.user = AuthUser.objects.create_user(
            username="user@example.com", email="user@example.com", password="password"
        )
        self.workspace = Workspace.objects.create(name="workspace")
        self.project = Project.objects.create(name="project", workspace=self.workspace)
        self.workspace.members.add(self.user)
        self.project.users.add(self.user)

        # Create invitation
        expire_at = datetime.now() + timedelta(seconds=settings.INVITATION_LINK_TIMEOUT)
        expire_at_tz = timezone.make_aware(expire_at)
        self.recipient_email = "recipient@example.com"
        self.token = secrets.token_hex(16)
        self.invitation = Invitation.objects.create(
            sender=self.user,
            recipient_email=self.recipient_email,
            token=self.token,
            workspace=self.workspace,
            project=self.project,
            expires_at=expire_at_tz,
            is_used=False,
        )

    def test_get_invitation_status(self):
        url = f"/api/invitation/{self.token}/"
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.json()
        self.assertEqual(data["is_signed_up"], False)
        self.assertEqual(data["sender"]["email"], self.user.email)
        self.assertEqual(data["workspace"]["id"], self.workspace.id)
        self.assertEqual(data["project"]["id"], self.project.id)

    def test_get_invitation_status_after_separate_signup(self):
        # Recipient signup before using the invitation token
        recipient = AuthUser.objects.create_user(
            username="recipient@example.com",
            email="recipient@example.com",
            password="password",
        )

        url = f"/api/invitation/{self.token}/"
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertFalse(
            self.workspace.members.filter(username=recipient.username).exists()
        )
        self.assertFalse(
            self.project.users.filter(username=recipient.username).exists()
        )
