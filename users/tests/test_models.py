from django.test import TestCase
from django.utils import timezone
from rest_framework.test import APIClient
from rest_framework import status, reverse

from users.models import CustomUser, UserType
from users.models import Notification, NotificationRecipient

class NotificationTests(TestCase):
    def setUp(self):
        self.admin = CustomUser.objects.create_user(email="admin@test.com", password="admin123", role=UserType.ADMIN)
        self.teacher = CustomUser.objects.create_user(email="teacher@test.com", password="teacher123", role=UserType.TEACHER)
        self.student = CustomUser.objects.create_user(email="student@test.com", password="student123", role=UserType.STUDENT)
        self.client = APIClient()
        self.url = reverse("notification-list")

    def test_admin_can_create_notification_for_students(self):
        self.client.force_authenticate(user=self.admin)

        payload = {
            "subject": "Test Notification",
            "message": "This is a test message.",
            "notification_type": "announcement",
            "link": "https://example.com",
            "recipients": [self.student.id]
        }

        response = self.client.post(self.url, payload, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        notification = Notification.objects.first()
        self.assertEqual(notification.subject, "Test Notification")
        self.assertEqual(notification.recipients.count(), 1)

        nr = NotificationRecipient.objects.get(user=self.student, notification=notification)
        self.assertFalse(nr.is_read)

    def test_student_can_see_their_notifications(self):
        notification = Notification.objects.create(subject="Hello", message="You have mail")
        NotificationRecipient.objects.create(user=self.student, notification=notification)

        self.client.force_authenticate(user=self.student)
        response = self.client.get("/api/notifications/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)

    def test_mark_as_read(self):
        notification = Notification.objects.create(subject="Reminder", message="Class starts soon.")
        NotificationRecipient.objects.create(user=self.student, notification=notification)

        self.client.force_authenticate(user=self.student)
        response = self.client.post(f"/api/notifications/{notification.id}/mark_as_read/")
        self.assertEqual(response.status_code, 200)

        nr = NotificationRecipient.objects.get(user=self.student, notification=notification)
        self.assertTrue(nr.is_read)

    def test_unread_count(self):
        notification = Notification.objects.create(subject="Unread", message="Please check.")
        NotificationRecipient.objects.create(user=self.student, notification=notification, is_read=False)

        self.client.force_authenticate(user=self.student)
        response = self.client.get("/api/notifications/unread_count/")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['unread_count'], 1)
