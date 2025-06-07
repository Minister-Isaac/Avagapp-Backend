from django.urls import reverse
from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from rest_framework.test import APITestCase
from rest_framework import status

from users.models import StudentProfile
from users.choices import UserType
from learning.models import Game, KnowledgeTrail, Subject, StudentAnswer
from learning.choices import QuestionType

User = get_user_model()


class GameAnswerFlowTestCase(APITestCase):
    def setUp(self):
        self.teacher = User.objects.create_user(
            email="teacher@example.com", password="pass1234",
            first_name="Teacher", role=UserType.TEACHER
        )
        self.student = User.objects.create_user(
            email="student@example.com", password="pass1234",
            first_name="Student", role=UserType.STUDENT
        )
        StudentProfile.objects.get_or_create(student=self.student)

        self.client.force_authenticate(user=self.teacher)

        # Create game with all 4 question types
        url = reverse("game-list")
        payload = {
            "title": "Comprehensive Game",
            "badges_awarded": "Gold",
            "questions": [
                {
                    "question_text": "Capital of France?",
                    "question_type": QuestionType.QUIZ,
                    "points": 10,
                    "options": [
                        {"option_text": "Paris", "is_correct": True},
                        {"option_text": "Berlin", "is_correct": False},
                    ],
                    "correct_answer": ""
                },
                {
                    "question_text": "2 + 2 = ?",
                    "question_type": QuestionType.FILL_IN_THE_BLANK,
                    "points": 10,
                    "correct_answer": "4"
                },
                {
                    "question_text": "Symbol for Hydrogen?",
                    "question_type": QuestionType.DRAG_AND_DROP,
                    "points": 10,
                    "options": [
                        {"option_text": "H", "is_correct": True},
                        {"option_text": "Na", "is_correct": False}
                    ],
                    "correct_answer": ""
                },
                {
                    "question_text": "Order the planets by distance from the Sun",
                    "question_type": QuestionType.MATCH_THE_COLUMN,
                    "points": 10,
                    "options": [
                        {"option_text": "Mercury", "is_correct": True},
                        {"option_text": "Venus", "is_correct": True},
                        {"option_text": "Earth", "is_correct": True},
                        {"option_text": "Mars", "is_correct": True}
                    ],
                    "correct_answer": ""
                },
                {
                    "question_text": "How many times does APPLE appear?",
                    "question_type": QuestionType.WORD_HUNT,
                    "points": 10,
                    "options": [
                        {"option_text": "APPLE", "is_correct": True},
                        {"option_text": "APPLE", "is_correct": True},
                        {"option_text": "APPLE", "is_correct": True},
                        {"option_text": "BANANA", "is_correct": False},
                        {"option_text": "ORANGE", "is_correct": False}
                    ],
                    "correct_answer": ""  # optional, no longer used here
                }
            ]
        }
        response = self.client.post(url, payload, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        self.game = Game.objects.get(title="Comprehensive Game")
        self.questions = self.game.questions.all()

    def test_student_answers_all_types_correctly(self):
        self.client.force_authenticate(user=self.student)

        # Quiz
        quiz_q = self.questions.get(question_text__icontains="capital")
        quiz_correct = quiz_q.options.get(is_correct=True)
        StudentAnswer.objects.create(student=self.student, question=quiz_q, selected_option=quiz_correct)

        # Fill in the blank
        fill_q = self.questions.get(question_text__icontains="2 + 2")
        StudentAnswer.objects.create(student=self.student, question=fill_q, typed_answer="4")

        # Drag and drop
        drag_q = self.questions.get(question_text__icontains="Hydrogen")
        drag_correct = drag_q.options.get(is_correct=True)
        StudentAnswer.objects.create(student=self.student, question=drag_q, selected_option=drag_correct)

        # Match the column (ordering)
        order_q = self.questions.get(question_text__icontains="planets")
        correct_order_ids = list(order_q.options.order_by("order").values_list("id", flat=True))
        StudentAnswer.objects.create(
            student=self.student,
            question=order_q,
            typed_answer=",".join(map(str, correct_order_ids))
        )
        # Word Hunt: Answer with number of times APPLE appears (based on is_correct=True count)
        word_hunt_q = self.questions.get(question_text__icontains="APPLE")
        StudentAnswer.objects.create(
            student=self.student,
            question=word_hunt_q,
            typed_answer="3"  # Matches number of is_correct=True
        )

        profile = StudentProfile.objects.get(student=self.student)
        self.assertEqual(StudentAnswer.objects.filter(student=self.student).count(), 5)
        self.assertEqual(profile.points, 50)
        profile.refresh_from_db()
        self.assertEqual(profile.medals, 1)


class KnowledgeTrailTests(APITestCase):
    def setUp(self):
        # Create a teacher
        self.teacher = User.objects.create_user(
            email='teacher@example.com',
            password='testpass123',
            role=UserType.TEACHER
        )
        
        # Create some students
        self.student1 = User.objects.create_user(
            email='student1@example.com',
            password='testpass123',
            role=UserType.STUDENT
        )
        self.student2 = User.objects.create_user(
            email='student2@example.com',
            password='testpass123',
            role=UserType.STUDENT
        )
        self.student3 = User.objects.create_user(
            email='student3@example.com',
            password='testpass123',
            role=UserType.STUDENT
        )
        
        # Create a subject
        self.subject = Subject.objects.create(
            name='Mathematics',
            description='Mathematics subject'
        )
        
        # Create a PDF file for testing
        self.pdf_file = SimpleUploadedFile(
            "test.pdf",
            b"file_content",
            content_type="application/pdf"
        )
        self.url = reverse("knowledge-trail-list")

    def test_create_public_knowledge_trail(self):
        """Test creating a public knowledge trail"""
        self.client.force_authenticate(user=self.teacher)
        
        data = {
            'title': 'Test Knowledge Trail',
            'subject': self.subject.id,
            'description': 'Test Description',
            'is_public': True,
            'pdf_file': self.pdf_file
        }
        
        response = self.client.post(self.url, data, format='multipart')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(KnowledgeTrail.objects.filter(title='Test Knowledge Trail').exists())
        print(KnowledgeTrail.objects.get(title='Test Knowledge Trail'))

    def test_create_private_knowledge_trail(self):
        """Test creating a private knowledge trail for specific students"""
        self.client.force_authenticate(user=self.teacher)
        
        data = {
            'title': 'Private Knowledge Trail',
            'subject': self.subject.id,
            'description': 'Private Test Description',
            'is_public': False,
            'target_students': [self.student1.id, self.student2.id],
            'pdf_file': self.pdf_file
        }
        
        response = self.client.post(self.url, data, format='multipart')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        
        # Verify that the knowledge trail is associated with the selected students
        knowledge_trail = KnowledgeTrail.objects.get(title='Private Knowledge Trail')
        self.assertEqual(knowledge_trail.target_students.count(), 2)
        self.assertTrue(knowledge_trail.target_students.filter(id=self.student1.id).exists())

    def test_student_cannot_create_knowledge_trail(self):
        """Test that students cannot create knowledge trails"""
        self.client.force_authenticate(user=self.student1)
        
        data = {
            'title': 'Student Knowledge Trail',
            'subject': self.subject.id,
            'description': 'Test Description',
            'is_public': True,
            'pdf_file': self.pdf_file
        }
        
        response = self.client.post(self.url, data, format='multipart')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_private_knowledge_trail_requires_students(self):
        """Test that private knowledge trails require at least one target student"""
        self.client.force_authenticate(user=self.teacher)
        
        data = {
            'title': 'Invalid Private Trail',
            'subject': self.subject.id,
            'description': 'Test Description',
            'is_public': False,
            'pdf_file': self.pdf_file
        }
        
        response = self.client.post(self.url, data, format='multipart')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
