from django.shortcuts import render
from .utils import paginate


def build_questions(prefix="Question", count=29):
    questions = []
    for i in range(1, count + 1):
        questions.append(
            {
                "id": i,
                "title": f"{prefix} {i}",
                "text": f"Question text {i}. This is a placeholder description.",
                "answers_count": (i * 3) % 17,
                "rating": (count - i) * 2,
                "tags": [f"tag{i % 5 + 1}", f"tag{i % 3 + 1}"],
                "author": f"user{i % 4 + 1}",
            }
        )
    return questions


def build_answers(question_id, count=7):
    answers = []
    for i in range(1, count + 1):
        answers.append(
            {
                "id": i,
                "text": f"Answer {i} for question {question_id}. Placeholder answer text.",
                "rating": i * 2 - 3,
                "author": f"user{i % 3 + 1}",
                "is_correct": i == 2,
            }
        )
    return answers


def index(request):
    questions = build_questions("New question", 29)
    page = paginate(questions, request, per_page=10)
    return render(
        request,
        "core/index.html",
        {
            "page_obj": page,
            "questions": page.object_list,
            "page_title": "Новые вопросы",
            "page_heading": "New questions",
        },
    )


def hot(request):
    questions = sorted(build_questions("Hot question", 29), key=lambda item: item["rating"], reverse=True)
    page = paginate(questions, request, per_page=10)
    return render(
        request,
        "core/hot.html",
        {
            "page_obj": page,
            "questions": page.object_list,
            "page_title": "Лучшие вопросы",
            "page_heading": "Best questions",
        },
    )


def tag(request, tag):
    questions = [q for q in build_questions("Tagged question", 29) if tag in q["tags"]]
    if not questions:
        questions = build_questions(f"Questions for #{tag}", 7)

    page = paginate(questions, request, per_page=10)
    return render(
        request,
        "core/tag.html",
        {
            "page_obj": page,
            "questions": page.object_list,
            "tag": tag,
            "page_title": f"Вопросы по тегу #{tag}",
            "page_heading": f"Tag: #{tag}",
        },
    )


def question(request, question_id):
    question_item = {
        "id": question_id,
        "title": f"Question {question_id}",
        "text": "######### #### ########## ######### ##### #### ## ##########",
        "rating": 0,
        "tags": ["tag2", "tag3", "tag4"],
        "author": "user1",
    }

    answers = build_answers(question_id, 7)
    page = paginate(answers, request, per_page=5)

    return render(
        request,
        "core/question.html",
        {
            "question_item": question_item,
            "answers": page.object_list,
            "page_obj": page,
            "page_title": question_item["title"],
        },
    )