import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { listCourses } from "../api/courses";
import { LoadingState, ErrorState } from "../components/StatusMessage";
import type { Course } from "../types";
import styles from "./CoursesPage.module.css";

export function CoursesPage() {
  const [courses, setCourses] = useState<Course[] | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    listCourses()
      .then(setCourses)
      .catch(() => setError("Something went wrong loading the courses."));
  }, []);

  return (
    <div className={styles.page}>
      <h1>Courses</h1>
      <p className={styles.subtitle}>Pick a course that matches your level and grow your vocabulary.</p>

      {error && <ErrorState message={error} />}
      {!error && !courses && <LoadingState label="Loading courses" />}

      {courses && courses.length === 0 && (
        <p className={styles.empty}>No courses yet.</p>
      )}

      <div className={styles.grid}>
        {courses?.map((course) => (
          <Link key={course.id} to={`/courses/${course.id}`} className={styles.card}>
            <span className={styles.level}>{course.level}</span>
            <h3>{course.title}</h3>
            <p className={styles.description}>{course.description}</p>
          </Link>
        ))}
      </div>
    </div>
  );
}
