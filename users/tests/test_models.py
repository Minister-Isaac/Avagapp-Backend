from django.test import TestCase
from django.utils import timezone
from django.urls import reverse
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient
from rest_framework import status, reverse

from users.models import Notification, NotificationRecipient, StudentProfile
from users.choices import UserType

from learning.models import Game, Question, Option, StudentAnswer, QuestionType


User = get_user_model()

class NotificationTests(TestCase):
    def setUp(self):
        self.admin = User.objects.create_user(email="admin@test.com", password="admin123", role=UserType.ADMIN)
        self.teacher = User.objects.create_user(email="teacher@test.com", password="teacher123", role=UserType.TEACHER)
        self.student = User.objects.create_user(email="student@test.com", password="student123", role=UserType.STUDENT)
        self.client = APIClient()

    def test_admin_can_create_notification_for_students_and_teachers(self):
        self.client.force_authenticate(user=self.admin)

        payload = {
            "title": "Test Notification",
            "message": "This is a test message.",
            "recipient_roles": "both",
            "recipients": [self.student.id]
        }

        response = self.client.post("/api/notifications/", payload, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        notification = Notification.objects.first()
        self.assertEqual(notification.title, "Test Notification")
        self.assertEqual(notification.recipients.count(), 2)


    def test_student_can_see_their_notifications(self):
        notification = Notification.objects.create(title="Hello", message="You have mail")
        NotificationRecipient.objects.create(user=self.student, notification=notification)

        self.client.force_authenticate(user=self.student)
        response = self.client.get("/api/notifications/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)

    
    def test_teacher_can_see_their_notifications(self):
        notification = Notification.objects.create(title="Hello", message="You have mail", recipient_roles= "teacher")
        NotificationRecipient.objects.create(user=self.student, notification=notification)

        self.client.force_authenticate(user=self.teacher)
        response = self.client.get("/api/notifications/")
        print(response.data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)


class StudentProfileMedalTest(TestCase):
    def setUp(self):
        self.student = User.objects.create_user(
            email="student@example.com",
            password="password123",
            first_name="John",
            last_name="Doe",
            role=UserType.STUDENT
        )
        # Get or create a student profile
        self.student_profile, created = StudentProfile.objects.get_or_create(student=self.student)

        self.game = Game.objects.create(title="Sample Game")

        self.question1 = Question.objects.create(
            question_type=QuestionType.QUIZ,
            points=10
        )
        self.question2 = Question.objects.create(
            question_type=QuestionType.QUIZ,
            points=10
        )
        
        self.game.questions.add(self.question1, self.question2)

        self.option1_correct = Option.objects.create(
            question=self.question1,
            option_text ="4",
            is_correct=True
        )
        self.option2_correct = Option.objects.create(
            question=self.question2,
            option_text  ="Paris",
            is_correct=True
        )
        self.option2_incorrect = Option.objects.create(
        question=self.question2,
        option_text="London",
        is_correct=False
    )

    def test_award_medal_for_80_percent_score(self):
        StudentAnswer.objects.create(
            student=self.student,
            question=self.question1,
            selected_option=self.option1_correct
        )
        StudentAnswer.objects.create(
            student=self.student,
            question=self.question2,
            selected_option=self.option2_correct
        )

        
        # Check if the student was not awarded a medal
        self.student_profile.refresh_from_db()
        self.assertEqual(self.student_profile.points, 20)
        self.assertEqual(self.student_profile.medals, 1)

    def test_no_medal_for_less_than_80_percent_score(self):
        # Student answers the first question correctly
        StudentAnswer.objects.create(
            student=self.student,
            question=self.question1,
            selected_option=self.option1_correct
        )

        # Student answers the second question incorrectly
        StudentAnswer.objects.create(
            student=self.student,
            question=self.question2,
            selected_option=self.option2_incorrect
        )

        # Check if the student was not awarded a medal
        self.student_profile.refresh_from_db()
        self.assertEqual(self.student_profile.medals, 0)
        self.assertEqual(self.student_profile.points, 10)