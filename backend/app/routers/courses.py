from typing import List

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import func
from sqlmodel import Session, select

from app.database import get_session
from app.models import Course, Lesson, VocabularyItem
from app.schemas import CourseRead, LessonRead, Page, VocabularyRead

router = APIRouter(tags=["courses"])


def _build_lesson_read(lesson: Lesson, session: Session) -> LessonRead:
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


@router.get("/courses", response_model=Page[CourseRead])
def list_courses(
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    session: Session = Depends(get_session),
):
    """Paginated (Page envelope). With one seeded course this is
    admittedly ceremonial today -- but the admin endpoints planned for
    v0.0.9 make the catalogue growable at runtime, and changing a
    response shape is much cheaper now than after clients depend on it."""
    total = session.exec(select(func.count(Course.id))).one()
    courses = session.exec(
        select(Course).order_by(Course.id).offset(offset).limit(limit)
    ).all()
    return Page[CourseRead](
        items=[CourseRead.model_validate(course, from_attributes=True) for course in courses],
        total=total,
        limit=limit,
        offset=offset,
    )


@router.get("/courses/{course_id}", response_model=CourseRead)
def get_course(course_id: int, session: Session = Depends(get_session)):
    course = session.get(Course, course_id)
    if not course:
        raise HTTPException(status_code=404, detail="Course not found")
    return course


@router.get("/courses/{course_id}/lessons", response_model=List[LessonRead])
def list_lessons(course_id: int, session: Session = Depends(get_session)):
    lessons = session.exec(
        select(Lesson).where(Lesson.course_id == course_id).order_by(Lesson.order)
    ).all()
    return [_build_lesson_read(lesson, session) for lesson in lessons]


@router.get("/lessons/{lesson_id}", response_model=LessonRead)
def get_lesson(lesson_id: int, session: Session = Depends(get_session)):
    lesson = session.get(Lesson, lesson_id)
    if not lesson:
        raise HTTPException(status_code=404, detail="Lesson not found")
    return _build_lesson_read(lesson, session)


@router.get("/lessons/{lesson_id}/vocabulary", response_model=List[VocabularyRead])
def list_vocabulary(lesson_id: int, session: Session = Depends(get_session)):
    return session.exec(
        select(VocabularyItem).where(VocabularyItem.lesson_id == lesson_id)
    ).all()
