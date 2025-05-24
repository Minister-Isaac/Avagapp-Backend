from django.test import TestCase
from django.contrib.auth import get_user_model
from django.utils.timezone import now
from users.models import StudentProfile
from learning.models import (
    PlayedGame, Question, Option, StudentAnswer,
    Game, Statistics, Certificate
    )
from rest_framework.test import APIClient
from rest_framework import status
from users.choices import UserType

User = get_user_model()

class StudentAnswerTestCase(TestCase):
    def setUp(self):
        # Create a user
        self.student = User.objects.create_user(email="student@example.com", password="password", first_name="John")

        # Create a question
        self.question = Question.objects.create(
            question_text="What is the capital of France?",
            question_type="multiple_choice",
            points=10
        )

        # Create options for the question
        self.correct_option = Option.objects.create(question=self.question, option_text="Paris", is_correct=True)
        self.wrong_option = Option.objects.create(question=self.question, option_text="London", is_correct=False)

        # Create a game and associate the question
        self.game = Game.objects.create(title="Geography Quiz")
        self.game.questions.add(self.question)

    def test_correct_answer_adds_points(self):
        # Ensure the student profile starts with 0 points
        student_profile = StudentProfile.objects.get(student=self.student)
        self.assertEqual(student_profile.points, 0)

        # Submit a correct answer
        StudentAnswer.objects.create(student=self.student, question=self.question, selected_option=self.correct_option)

        # Check that points were added to the student's profile
        student_profile.refresh_from_db()
        self.assertEqual(student_profile.points, 10)

    def test_wrong_answer_does_not_add_points(self):
        # Ensure the student profile starts with 0 points
        student_profile = StudentProfile.objects.get(student=self.student)
        self.assertEqual(student_profile.points, 0)

        # Submit a wrong answer
        StudentAnswer.objects.create(student=self.student, question=self.question, selected_option=self.wrong_option)

        # Check that points were not added to the student's profile
        student_profile.refresh_from_db()
        self.assertEqual(student_profile.points, 0)
        

class TeacherStatsTest(TestCase):
    def setUp(self):
        self.client = APIClient()

        # Create a teacher user
        self.teacher = User.objects.create_user(
            email="teacher@example.com",
            password="password123",
            role=UserType.TEACHER
        )
        self.client.force_authenticate(user=self.teacher)

        # Create a statistics record
        self.stats = Statistics.objects.create(
            students=10,
            teachers=5,
            knowledge_trail_videos=3,
            certificates_issued=2
        )

    def test_get_teacher_stats(self):
        response = self.client.get("/learning/statistics/teacher-stats/")
        self.assertEqual(response.status_code, 200)
        self.assertIn("students", response.data)
        self.assertIn("classes", response.data)
        self.assertIn("lessons", response.data)
        self.assertIn("Certificates", response.data)
        
        
class StudentStatsTest(TestCase):    
    def setUp(self):
        # Create a student user
        self.student = User.objects.create_user(
            email="student@example.com",
            password="password123",
            first_name="John",
            last_name="Doe",
            role="student"
        )
        self.client = APIClient()
        self.client.force_authenticate(user=self.student)

        # Create a student profile
        self.student_profile, created = StudentProfile.objects.get_or_create(
            student=self.student
        )
        self.student_profile.points = 150
        self.student_profile.medals = 3
        self.student_profile.save()

        # Create a game and a PlayedGame record
        self.game = Game.objects.create(title="Sample Game")
        PlayedGame.objects.create(
            student=self.student,
            game=self.game,
            score=80,
            completed=True,
            played_at=now()
        )

        # Create a certificate
        Certificate.objects.create(
            student=self.student,
            file="certificate.pdf",
            created_at=now()
        )

    def test_get_student_stats(self):
        response = self.client.get("/learning/statistics/student-stats/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # Verify the response data
        self.assertIn("points", response.data)
        self.assertIn("medals", response.data)
        self.assertIn("played_games", response.data)
        self.assertIn("certificates", response.data)

        # Check the counts
        self.assertEqual(response.data["points"]["count"], 150)
        self.assertEqual(response.data["medals"]["count"], 3)
        self.assertEqual(response.data["played_games"]["count"], 1)
        self.assertEqual(response.data["certificates"]["count"], 1)

        # add more point and medals to the student profile
        self.student_profile.points += 50
        self.student_profile.medals += 2
        self.student_profile.save()
        self.student_profile.refresh_from_db()
        
        # Check the differences (assuming no changes since the last check)
        self.assertEqual(response.data["points"]["difference"], 150)
        self.assertEqual(response.data["medals"]["difference"], 3)
        self.assertEqual(response.data["played_games"]["new_played_games"], 0)
        self.assertEqual(response.data["certificates"]["new_certificates"], 0)
        

class LeaderboardAPITest(TestCase):
    def setUp(self):
        self.client = APIClient()

        # Create students
        self.student1 = User.objects.create_user(
            email="student1@example.com",
            password="password123",
            first_name="John",
            last_name="Doe"
        )
        self.student2 = User.objects.create_user(
            email="student2@example.com",
            password="password123",
            first_name="Jane",
            last_name="Smith"
        )
        self.student3 = User.objects.create_user(
            email="student3@example.com",
            password="password123",
            first_name="Alice",
            last_name="Johnson"
        )

        self.client.force_authenticate(user=self.student1)
        
        # Create a game
        self.game = Game.objects.create(title="Sample Game")

        # Create PlayedGame records
        PlayedGame.objects.create(student=self.student1, game=self.game, score=250, completed=True)
        PlayedGame.objects.create(student=self.student2, game=self.game, score=200, completed=True)
        PlayedGame.objects.create(student=self.student3, game=self.game, score=180, completed=True)

    def test_leaderboard(self):
        response = self.client.get("/learning/leaderboard/leaderboard/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # Verify the response structure
        self.assertEqual(len(response.data), 3)
        self.assertEqual(response.data[0]["student_name"], "John Doe")
        self.assertEqual(response.data[0]["total_score"], 250)
        self.assertEqual(response.data[1]["student_name"], "Jane Smith")
        self.assertEqual(response.data[1]["total_score"], 200)
        self.assertEqual(response.data[2]["student_name"], "Alice Johnson")
        self.assertEqual(response.data[2]["total_score"], 180)