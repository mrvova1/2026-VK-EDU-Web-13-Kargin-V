import random
from itertools import islice

from django.contrib.auth.hashers import make_password
from django.contrib.auth.models import User
from django.core.management.base import BaseCommand
from django.db import transaction
from django.utils.text import slugify
from faker import Faker

from questions.models import Answer, AnswerLike, Profile, Question, QuestionLike, Tag


def chunks(iterable, size):
    iterator = iter(iterable)
    while True:
        batch = list(islice(iterator, size))
        if not batch:
            break
        yield batch


class Command(BaseCommand):
    help = "Fill database with test data"

    def add_arguments(self, parser):
        parser.add_argument("ratio", type=int)

    @transaction.atomic
    def handle(self, *args, **options):
        ratio = options["ratio"]
        fake = Faker("ru_RU")

        users_count = ratio
        questions_count = ratio * 10
        answers_count = ratio * 100
        tags_count = ratio
        likes_count = ratio * 200

        password_hash = make_password("password123")

        self.stdout.write("Creating users...")
        users = [
            User(
                username=f"user_{i}_{fake.user_name()}",
                email=fake.unique.email(),
                password=password_hash,
                first_name=fake.first_name(),
                last_name=fake.last_name(),
                is_active=True,
            )
            for i in range(users_count)
        ]
        User.objects.bulk_create(users, batch_size=1000)
        users = list(User.objects.order_by("-id")[:users_count])

        self.stdout.write("Creating profiles...")
        profiles = [
            Profile(
                user=user,
                nickname=fake.unique.user_name(),
                bio=fake.text(max_nb_chars=120),
            )
            for user in users
        ]
        Profile.objects.bulk_create(profiles, batch_size=1000)

        self.stdout.write("Creating tags...")
        tags = []
        for i in range(tags_count):
            name = fake.unique.word() + f"_{i}"
            tags.append(Tag(name=name, slug=slugify(name)))
        Tag.objects.bulk_create(tags, batch_size=1000)
        tags = list(Tag.objects.order_by("-id")[:tags_count])

        self.stdout.write("Creating questions...")
        questions = []
        for i in range(questions_count):
            questions.append(
                Question(
                    author=random.choice(users),
                    title=fake.sentence(nb_words=6).rstrip("."),
                    text=fake.text(max_nb_chars=500),
                    rating=random.randint(-20, 200),
                )
            )
        Question.objects.bulk_create(questions, batch_size=1000)
        questions = list(Question.objects.order_by("-id")[:questions_count])

        self.stdout.write("Creating question-tag links...")
        question_tags_model = Question.tags.through
        question_tags = []
        for question in questions:
            chosen_tags = random.sample(tags, k=min(3, len(tags)))
            for tag in chosen_tags:
                question_tags.append(
                    question_tags_model(question_id=question.id, tag_id=tag.id)
                )
        question_tags_model.objects.bulk_create(question_tags, batch_size=5000)

        self.stdout.write("Creating answers...")
        answers = []
        for i in range(answers_count):
            answers.append(
                Answer(
                    question=random.choice(questions),
                    author=random.choice(users),
                    text=fake.text(max_nb_chars=300),
                    rating=random.randint(-50, 300),
                    is_correct=(i % 10 == 0),
                )
            )
        Answer.objects.bulk_create(answers, batch_size=2000)
        answers = list(Answer.objects.order_by("-id")[:answers_count])

        self.stdout.write("Creating question likes...")
        q_likes = []
        for i in range(likes_count):
            user = users[i % users_count]
            question = questions[(i // users_count) % questions_count]
            q_likes.append(QuestionLike(user=user, question=question, value=1))
        QuestionLike.objects.bulk_create(q_likes, batch_size=5000)

        self.stdout.write("Creating answer likes...")
        a_likes = []
        for i in range(likes_count):
            user = users[i % users_count]
            answer = answers[(i // users_count) % answers_count]
            a_likes.append(AnswerLike(user=user, answer=answer, value=1))
        AnswerLike.objects.bulk_create(a_likes, batch_size=5000)

        self.stdout.write(self.style.SUCCESS("Database filled successfully"))