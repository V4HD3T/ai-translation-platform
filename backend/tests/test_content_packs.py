"""Content packs (v0.1.3): every shipped pack must be valid and importable,
and the imported content must actually work through the real endpoints.

The Turkish pack pulls double duty here. It's real course content *and*
the first end-to-end proof of the v0.0.7 case-folding fix against
user-facing material: a learner typing MISIR with caps lock on must be
scored correct for 'mısır', which plain str.lower() would fold to
'misir' and mark wrong."""

import pytest
from sqlmodel import select

from app.models import Course, Lesson, Quiz, QuizQuestion, VocabularyItem
from app.services.content_import import available_packs, import_pack, load_pack


def _pack(name):
    path = next(p for p in available_packs() if p.stem == name)
    return load_pack(path)


def test_every_shipped_pack_validates():
    packs = available_packs()
    assert packs, "no content packs found"
    for path in packs:
        load_pack(path)  # raises on malformed content, bad options, or unscrambleable sentences


def test_import_creates_the_full_content_tree(session):
    course = import_pack(_pack("turkish-a1"), session)
    assert course is not None
    assert course.language_code == "tr"

    lessons = session.exec(select(Lesson).where(Lesson.course_id == course.id)).all()
    assert len(lessons) == 3
    assert [lesson.order for lesson in lessons] == [1, 2, 3]
    assert all(lesson.grammar_note and lesson.cultural_note for lesson in lessons)

    first = min(lessons, key=lambda lesson: lesson.order)
    vocab = session.exec(select(VocabularyItem).where(VocabularyItem.lesson_id == first.id)).all()
    assert {item.word for item in vocab} >= {"merhaba", "günaydın"}

    quiz = session.exec(select(Quiz).where(Quiz.lesson_id == first.id)).first()
    assert quiz is not None
    questions = session.exec(select(QuizQuestion).where(QuizQuestion.quiz_id == quiz.id)).all()
    assert {q.question_type for q in questions} == {
        "multiple_choice",
        "fill_blank",
        "listening",
        "sentence_order",
    }


def test_import_is_idempotent(session):
    assert import_pack(_pack("turkish-a1"), session) is not None
    assert import_pack(_pack("turkish-a1"), session) is None  # second run is a no-op
    courses = session.exec(select(Course).where(Course.language_code == "tr")).all()
    assert len(courses) == 1


def test_imported_content_is_served_through_the_public_api(client, session):
    import_pack(_pack("spanish-a2"), session)
    titles = [c["title"] for c in client.get("/courses?limit=100").json()["items"]]
    assert "Spanish: Out in the World" in titles
    assert "Spanish for Beginners" in titles  # the seeded course is untouched


def _auth_headers(client, username="packlearner"):
    client.post(
        "/auth/register",
        json={"username": username, "email": f"{username}@example.com", "password": "password1234"},
    )
    login = client.post("/auth/login", data={"username": username, "password": "password1234"})
    return {"Authorization": f"Bearer {login.json()['access_token']}"}


@pytest.mark.parametrize("typed_answer", ["mısır", "MISIR", "Mısır", "  mısır  "])
def test_turkish_fill_blank_accepts_uppercase_dotless_i(client, session, typed_answer):
    """The full-circle test for the v0.0.7 fix, now with real course content:
    'MISIR' must fold to 'mısır' (Turkish dotless I), not 'misir'."""
    course = import_pack(_pack("turkish-a1"), session)
    food_lesson = session.exec(
        select(Lesson).where(Lesson.course_id == course.id, Lesson.order == 3)
    ).first()
    quiz = session.exec(select(Quiz).where(Quiz.lesson_id == food_lesson.id)).first()

    headers = _auth_headers(client, username=f"corn{abs(hash(typed_answer)) % 10000}")
    served = client.get(f"/quizzes/{quiz.id}", headers=headers).json()
    corn_question = next(
        q for q in served["questions"] if "corn" in q["question_text"]
    )

    result = client.post(
        f"/quizzes/{quiz.id}/submit",
        json={"session_id": served["session_id"], "answers": {str(corn_question["id"]): typed_answer}},
        headers=headers,
    ).json()
    assert result["correct_count"] == 1, f"{typed_answer!r} should have been accepted"


def test_turkish_quiz_language_resolves_from_its_course(client, session):
    """Case folding is language-aware, and the language comes from the
    course -- so a wrong answer must still be wrong (the fix must not make
    everything match)."""
    course = import_pack(_pack("turkish-a1"), session)
    lesson = session.exec(
        select(Lesson).where(Lesson.course_id == course.id, Lesson.order == 3)
    ).first()
    quiz = session.exec(select(Quiz).where(Quiz.lesson_id == lesson.id)).first()

    headers = _auth_headers(client, username="wronganswer")
    served = client.get(f"/quizzes/{quiz.id}", headers=headers).json()
    corn_question = next(q for q in served["questions"] if "corn" in q["question_text"])

    result = client.post(
        f"/quizzes/{quiz.id}/submit",
        json={"session_id": served["session_id"], "answers": {str(corn_question["id"]): "misir"}},
        headers=headers,
    ).json()
    assert result["correct_count"] == 0  # dotted-i spelling is genuinely a different word
