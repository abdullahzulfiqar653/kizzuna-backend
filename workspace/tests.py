# from django.urls import reverse
# from rest_framework import status
# from rest_framework.test import APITestCase
# from .models import Workspace
# from unittest.mock import patch

# class WorkspaceViewTests(APITestCase):
    
#     def setUp(self):
#         # Create a sample workspace for testing
#         self.workspace = Workspace.objects.create(name="Sample Workspace")
#         self.workspace_data = {'name': 'New Workspace'}
        
#     def test_list_create_workspaces(self):
#         # Testing GET on WorkspaceListCreateView
#         response = self.client.get(reverse('workspace-list-create'))
#         self.assertEqual(response.status_code, status.HTTP_200_OK)
#         self.assertEqual(len(response.data), 1)

#         # Testing POST on WorkspaceListCreateView
#         response = self.client.post(reverse('workspace-list-create'), data=self.workspace_data)
#         self.assertEqual(response.status_code, status.HTTP_201_CREATED)
#         self.assertEqual(response.data['name'], self.workspace_data['name'])

#     @patch('workspace.views.WorkspaceRetrieveUpdateDeleteView.get_object')
#     def test_retrieve_workspace(self, mock_get_object):
#         mock_get_object.return_value = self.workspace

#         # Testing GET on WorkspaceRetrieveUpdateDeleteView
#         response = self.client.get(reverse('workspace-retrieve-update-delete', args=[self.workspace.id]))
#         self.assertEqual(response.status_code, status.HTTP_200_OK)
#         self.assertEqual(response.data['name'], self.workspace.name)
        
#     @patch('workspace.views.WorkspaceRetrieveUpdateDeleteView.get_object')
#     def test_update_workspace(self, mock_get_object):
#         mock_get_object.return_value = self.workspace

#         updated_data = {'name': 'Updated Workspace Name'}
#         # Testing PUT on WorkspaceRetrieveUpdateDeleteView
#         response = self.client.put(reverse('workspace-retrieve-update-delete', args=[self.workspace.id]), data=updated_data)
#         self.assertEqual(response.status_code, status.HTTP_200_OK)
#         self.workspace.refresh_from_db()
#         self.assertEqual(self.workspace.name, updated_data['name'])
        
#     @patch('workspace.views.WorkspaceRetrieveUpdateDeleteView.get_object')
#     def test_delete_workspace(self, mock_get_object):
#         mock_get_object.return_value = self.workspace

#         # Testing DELETE on WorkspaceRetrieveUpdateDeleteView
#         response = self.client.delete(reverse('workspace-retrieve-update-delete', args=[self.workspace.id]))
#         self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
#         self.assertFalse(Workspace.objects.filter(id=self.workspace.id).exists())