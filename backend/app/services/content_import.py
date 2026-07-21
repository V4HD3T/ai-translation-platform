"""Content pack import (v0.1.3).

Course content lives in `backend/content/*.json`, not in Python. That's a
direct continuation of the v0.0.9 decision to stop hardcoding the
catalogue: `seed_data` stays the minimal demo/test fixture (148 tests
depend on its exact shape), while real content ships as data that can be
imported into any database — dev, demo, or production — without a code
change or a deploy.

Packs are validated before anything is written: a malformed pack fails
loudly and atomically rather than leaving a half-imported course behind.
Imports are idempotent by (language_code, title), so re-running against a
populated database is a no-op instead of a duplicate catalogue.
"""

import json
from pathlib import Path
from typing import List

from pydantic import BaseModel, Field
from sqlmodel import Session, select

from app.models import Course, Language, Lesson, Quiz, QuizQuestion, VocabularyItem

CONTENT_DIR = Path(__file__).resolve().parent.parent.parent / "content"

QUESTION_TYPES = {"multiple_choice", "fill_blank", "listening", "sentence_order"}


class PackQuestion(BaseModel):
    question_type: str
    question_text: str
    correct_answer: str
    options: List[str] = []
    audio_text: str | None = None
    difficulty: int = Field(default=1, ge=1, le=3)


class PackQuiz(BaseModel):
    title: str
    questions: List[PackQuestion]


class PackVocabulary(BaseModel):
    word: str
    translation: str
    example_sentence: str = ""


class PackLesson(BaseModel):
    title: str
    order: int = 0
    content: str = ""
    grammar_note: str = ""
    cultural_note: str = ""
    vocabulary: List[PackVocabulary] = []
    quiz: PackQuiz | None = None


class PackCourse(BaseModel):
    language_code: str
    title: str
    level: str
    description: str = ""


class ContentPack(BaseModel):
    course: PackCourse
    lessons: List[PackLesson]


def load_pack(path: Path) -> ContentPack:
    """Parses and validates a pack file. Raises on malformed content."""
    pack = ContentPack.model_validate(json.loads(path.read_text(encoding="utf-8")))
    for lesson in pack.lessons:
        if lesson.quiz is None:
            continue
        for question in lesson.quiz.questions:
            if question.question_type not in QUESTION_TYPES:
                raise ValueError(
                    f"{path.name}: unknown question_type {question.question_type!r}"
                )
            # A multiple-choice question whose correct answer isn't among
            # its options is unanswerable -- catch it here, not in front of
            # a learner.
            if question.question_type == "multiple_choice":
                if question.correct_answer not in question.options:
                    raise ValueError(
                        f"{path.name}: correct answer {question.correct_answer!r} "
                        f"missing from options of {question.question_text!r}"
                    )
            # sentence_order words must reconstruct exactly the expected
            # sentence -- otherwise the question can never be scored right.
            if question.question_type == "sentence_order":
                if sorted(question.options) != sorted(question.correct_answer.split()):
                    raise ValueError(
                        f"{path.name}: scrambled words don't match the answer for "
                        f"{question.question_text!r}"
                    )
    return pack


def import_pack(pack: ContentPack, session: Session) -> Course | None:
    """Writes a validated pack into the database. Returns the created
    Course, or None if a course with the same language and title already
    exists (idempotent re-runs)."""
    existing = session.exec(
        select(Course).where(
            Course.language_code == pack.course.language_code,
            Course.title == pack.course.title,
        )
    ).first()
    if existing:
        return None

    # A course in a language the app doesn't list would be invisible in the
    # language pickers; add it rather than silently importing a dead course.
    if not session.exec(
        select(Language).where(Language.code == pack.course.language_code)
    ).first():
        session.add(
            Language(code=pack.course.language_code, name=pack.course.language_code.upper())
        )

    course = Course(**pack.course.model_dump())
    session.add(course)
    session.commit()
    session.refresh(course)

    for pack_lesson in pack.lessons:
        lesson = Lesson(
            course_id=course.id,
            title=pack_lesson.title,
            content=pack_lesson.content,
            order=pack_lesson.order,
            grammar_note=pack_lesson.grammar_note,
            cultural_note=pack_lesson.cultural_note,
        )
        session.add(lesson)
        session.commit()
        session.refresh(lesson)

        for item in pack_lesson.vocabulary:
            session.add(VocabularyItem(lesson_id=lesson.id, **item.model_dump()))

        if pack_lesson.quiz is not None:
            quiz = Quiz(lesson_id=lesson.id, title=pack_lesson.quiz.title)
            session.add(quiz)
            session.commit()
            session.refresh(quiz)
            for question in pack_lesson.quiz.questions:
                session.add(
                    QuizQuestion(
                        quiz_id=quiz.id,
                        question_type=question.question_type,
                        question_text=question.question_text,
                        correct_answer=question.correct_answer,
                        options_json=json.dumps(question.options),
                        audio_text=question.audio_text,
                        difficulty=question.difficulty,
                    )
                )
        session.commit()

    return course


def available_packs() -> List[Path]:
    return sorted(CONTENT_DIR.glob("*.json"))
