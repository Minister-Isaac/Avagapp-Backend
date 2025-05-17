from django.test import TestCase
from django.contrib.auth import get_user_model
from learning.models import Question, Option, StudentAnswer, Game
from users.models import StudentProfile

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