import { useEffect, useState } from "react";
import { Link, useParams } from "react-router-dom";
import { getCourse, listLessons } from "../api/courses";
import { LoadingState, ErrorState } from "../components/StatusMessage";
import type { Course, Lesson } from "../types";
import styles from "./CoursesPage.module.css";

export function CourseDetailPage() {
  const { courseId } = useParams<{ courseId: string }>();
  const [course, setCourse] = useState<Course | null>(null);
  const [lessons, setLessons] = useState<Lesson[] | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!courseId) return;
    const id = Number(courseId);
    Promise.all([getCourse(id), listLessons(id)])
      .then(([courseData, lessonData]) => {
        setCourse(courseData);
        setLessons(lessonData);
      })
      .catch(() => setError("Something went wrong loading this course."));
  }, [courseId]);

  return (
    <div className={styles.page}>
      <Link to="/courses" className={styles.backLink}>
        ← Courses
      </Link>

      {error && <ErrorState message={error} />}
      {!error && !course && <LoadingState label="Loading course" />}

      {course && (
        <>
          <span className={styles.level}>{course.level}</span>
          <h1>{course.title}</h1>
          <p className={styles.subtitle}>{course.description}</p>

          <div className={styles.lessonList}>
            {lessons?.map((lesson) => (
              <Link
                key={lesson.id}
                to={`/lessons/${lesson.id}`}
                className={styles.lessonRow}
              >
                <span className={styles.lessonOrder}>{lesson.order}</span>
                <span className={styles.lessonTitle}>{lesson.title}</span>
              </Link>
            ))}
          </div>
        </>
      )}
    </div>
  );
}
