"""Admin content-management API (v0.0.9).

Course/lesson/vocabulary/quiz content was previously hardcoded in
seed_data; these endpoints make the catalogue manageable at runtime.
Authorization is a plain is_admin flag on User. Promotion happens only
via scripts/make_admin.py against the database, never through the public
API -- UserCreate has no is_admin field, so there is no mass-assignment
path to it, and no privilege-escalation surface to defend.

Deletes cascade explicitly and destructively: removing a course removes
its lessons, their vocabulary (including learners' spaced-repetition
progress on those words), quizzes, questions, quiz sessions, and quiz
attempts. That is a real product decision made simple on purpose --
soft-delete/archival is the roadmap answer if learner data ever needs to
survive content removal.
"""

import json

from fastapi import APIRouter, Depends, HTTPException, status
from sqlmodel import Session, select

from app.database import get_session
from app.models import (
    Course,
    Lesson,
    Quiz,
    QuizAttempt,
    QuizQuestion,
    QuizSession,
    User,
    VocabularyItem,
    VocabularyProgress,
)
from app.routers.auth import get_current_user
from app.schemas import (
    AdminQuizQuestionRead,
    AdminQuizRead,
    CourseCreate,
    CourseRead,
    CourseUpdate,
    LessonCreate,
    LessonRead,
    LessonUpdate,
    QuizCreate,
    QuizQuestionCreate,
    QuizQuestionUpdate,
    QuizUpdate,
    VocabularyCreate,
    VocabularyRead,
    VocabularyUpdate,
)


def require_admin(current_user: User = Depends(get_current_user)) -> User:
    if not current_user.is_admin:
        raise HTTPException(status_code=403, detail="Admin privileges required")
    return current_user


router = APIRouter(prefix="/admin", tags=["admin"], dependencies=[Depends(require_admin)])


def _get_or_404(session: Session, model, obj_id: int, name: str):
    obj = session.get(model, obj_id)
    if not obj:
        raise HTTPException(status_code=404, detail=f"{name} not found")
    return obj


def _apply_updates(obj, payload) -> None:
    """Copies only the fields the client actually sent (exclude_unset), so
    a PATCH with one field doesn't blank out the rest."""
    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(obj, field, value)


def _lesson_read(lesson: Lesson, session: Session) -> LessonRead:
    course = session.get(Course, lesson.course_id)
    return LessonRead(
        id=lesson.id,
        course_id=lesson.course_id,
        title=lesson.title,
        content=lesson.content,
        order=lesson.order,
        language_code=course.language_code if course else "",
        grammar_note=lesson.grammar_note,
        cultural_note=lesson.cultural_note,
    )


def _question_read(question: QuizQuestion) -> AdminQuizQuestionRead:
    return AdminQuizQuestionRead(
        id=question.id,
        question_type=question.question_type,
        question_text=question.question_text,
        correct_answer=question.correct_answer,
        options=json.loads(question.options_json),
        audio_text=question.audio_text,
        difficulty=question.difficulty,
    )


# --- explicit cascade helpers ------------------------------------------------


def _delete_quiz_cascade(quiz: Quiz, session: Session) -> None:
    for model, column in (
        (QuizSession, QuizSession.quiz_id),
        (QuizAttempt, QuizAttempt.quiz_id),
        (QuizQuestion, QuizQuestion.quiz_id),
    ):
        for row in session.exec(select(model).where(column == quiz.id)).all():
            session.delete(row)
    session.delete(quiz)


def _delete_vocabulary_cascade(item: VocabularyItem, session: Session) -> None:
    for progress in session.exec(
        select(VocabularyProgress).where(VocabularyProgress.vocabulary_item_id == item.id)
    ).all():
        session.delete(progress)
    session.delete(item)


def _delete_lesson_cascade(lesson: Lesson, session: Session) -> None:
    for item in session.exec(
        select(VocabularyItem).where(VocabularyItem.lesson_id == lesson.id)
    ).all():
        _delete_vocabulary_cascade(item, session)
    for quiz in session.exec(select(Quiz).where(Quiz.lesson_id == lesson.id)).all():
        _delete_quiz_cascade(quiz, session)
    session.delete(lesson)


# --- courses -----------------------------------------------------------------


@router.post("/courses", response_model=CourseRead, status_code=status.HTTP_201_CREATED)
def create_course(payload: CourseCreate, session: Session = Depends(get_session)):
    course = Course(**payload.model_dump())
    session.add(course)
    session.commit()
    session.refresh(course)
    return course


@router.patch("/courses/{course_id}", response_model=CourseRead)
def update_course(
    course_id: int, payload: CourseUpdate, session: Session = Depends(get_session)
):
    course = _get_or_404(session, Course, course_id, "Course")
    _apply_updates(course, payload)
    session.add(course)
    session.commit()
    session.refresh(course)
    return course


@router.delete("/courses/{course_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_course(course_id: int, session: Session = Depends(get_session)):
    course = _get_or_404(session, Course, course_id, "Course")
    for lesson in session.exec(select(Lesson).where(Lesson.course_id == course_id)).all():
        _delete_lesson_cascade(lesson, session)
    session.delete(course)
    session.commit()


# --- lessons -----------------------------------------------------------------


@router.post(
    "/courses/{course_id}/lessons",
    response_model=LessonRead,
    status_code=status.HTTP_201_CREATED,
)
def create_lesson(
    course_id: int, payload: LessonCreate, session: Session = Depends(get_session)
):
    _get_or_404(session, Course, course_id, "Course")
    lesson = Lesson(course_id=course_id, **payload.model_dump())
    session.add(lesson)
    session.commit()
    session.refresh(lesson)
    return _lesson_read(lesson, session)


@router.patch("/lessons/{lesson_id}", response_model=LessonRead)
def update_lesson(
    lesson_id: int, payload: LessonUpdate, session: Session = Depends(get_session)
):
    lesson = _get_or_404(session, Lesson, lesson_id, "Lesson")
    _apply_updates(lesson, payload)
    session.add(lesson)
    session.commit()
    session.refresh(lesson)
    return _lesson_read(lesson, session)


@router.delete("/lessons/{lesson_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_lesson(lesson_id: int, session: Session = Depends(get_session)):
    lesson = _get_or_404(session, Lesson, lesson_id, "Lesson")
    _delete_lesson_cascade(lesson, session)
    session.commit()


# --- vocabulary --------------------------------------------------------------


@router.post(
    "/lessons/{lesson_id}/vocabulary",
    response_model=VocabularyRead,
    status_code=status.HTTP_201_CREATED,
)
def create_vocabulary(
    lesson_id: int, payload: VocabularyCreate, session: Session = Depends(get_session)
):
    _get_or_404(session, Lesson, lesson_id, "Lesson")
    item = VocabularyItem(lesson_id=lesson_id, **payload.model_dump())
    session.add(item)
    session.commit()
    session.refresh(item)
    return item


@router.patch("/vocabulary/{vocabulary_id}", response_model=VocabularyRead)
def update_vocabulary(
    vocabulary_id: int, payload: VocabularyUpdate, session: Session = Depends(get_session)
):
    item = _get_or_404(session, VocabularyItem, vocabulary_id, "Vocabulary item")
    _apply_updates(item, payload)
    session.add(item)
    session.commit()
    session.refresh(item)
    return item


@router.delete("/vocabulary/{vocabulary_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_vocabulary(vocabulary_id: int, session: Session = Depends(get_session)):
    item = _get_or_404(session, VocabularyItem, vocabulary_id, "Vocabulary item")
    _delete_vocabulary_cascade(item, session)
    session.commit()


# --- quizzes -----------------------------------------------------------------


@router.post(
    "/lessons/{lesson_id}/quiz",
    response_model=AdminQuizRead,
    status_code=status.HTTP_201_CREATED,
)
def create_quiz(
    lesson_id: int, payload: QuizCreate, session: Session = Depends(get_session)
):
    _get_or_404(session, Lesson, lesson_id, "Lesson")
    existing = session.exec(select(Quiz).where(Quiz.lesson_id == lesson_id)).first()
    if existing:
        # The public lookup (GET /lessons/{id}/quiz) resolves "the lesson's
        # quiz" with .first() -- allowing a second quiz would make that
        # lookup silently ambiguous.
        raise HTTPException(status_code=400, detail="Lesson already has a quiz")
    quiz = Quiz(lesson_id=lesson_id, **payload.model_dump())
    session.add(quiz)
    session.commit()
    session.refresh(quiz)
    return quiz


@router.patch("/quizzes/{quiz_id}", response_model=AdminQuizRead)
def update_quiz(quiz_id: int, payload: QuizUpdate, session: Session = Depends(get_session)):
    quiz = _get_or_404(session, Quiz, quiz_id, "Quiz")
    _apply_updates(quiz, payload)
    session.add(quiz)
    session.commit()
    session.refresh(quiz)
    return quiz


@router.delete("/quizzes/{quiz_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_quiz(quiz_id: int, session: Session = Depends(get_session)):
    quiz = _get_or_404(session, Quiz, quiz_id, "Quiz")
    _delete_quiz_cascade(quiz, session)
    session.commit()


# --- quiz questions ----------------------------------------------------------


@router.post(
    "/quizzes/{quiz_id}/questions",
    response_model=AdminQuizQuestionRead,
    status_code=status.HTTP_201_CREATED,
)
def create_question(
    quiz_id: int, payload: QuizQuestionCreate, session: Session = Depends(get_session)
):
    _get_or_404(session, Quiz, quiz_id, "Quiz")
    data = payload.model_dump()
    options = data.pop("options")
    question = QuizQuestion(quiz_id=quiz_id, options_json=json.dumps(options), **data)
    session.add(question)
    session.commit()
    session.refresh(question)
    return _question_read(question)


@router.patch("/questions/{question_id}", response_model=AdminQuizQuestionRead)
def update_question(
    question_id: int, payload: QuizQuestionUpdate, session: Session = Depends(get_session)
):
    question = _get_or_404(session, QuizQuestion, question_id, "Question")
    data = payload.model_dump(exclude_unset=True)
    if "options" in data:
        question.options_json = json.dumps(data.pop("options"))
    for field, value in data.items():
        setattr(question, field, value)
    session.add(question)
    session.commit()
    session.refresh(question)
    return _question_read(question)


@router.delete("/questions/{question_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_question(question_id: int, session: Session = Depends(get_session)):
    # Sessions that already served this question keep its id in their
    # served set; grading counts it as wrong (see submit_quiz). Deleting
    # questions from a live quiz is an admin judgment call.
    question = _get_or_404(session, QuizQuestion, question_id, "Question")
    session.delete(question)
    session.commit()
