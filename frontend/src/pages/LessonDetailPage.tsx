import { useEffect, useState } from "react";
import { Link, useParams } from "react-router-dom";
import { listVocabulary } from "../api/courses";
import { getQuizByLesson } from "../api/quizzes";
import { LoadingState, ErrorState } from "../components/StatusMessage";
import type { VocabularyItem } from "../types";
import styles from "./LessonDetailPage.module.css";

export function LessonDetailPage() {
  const { lessonId } = useParams<{ lessonId: string }>();
  const [vocabulary, setVocabulary] = useState<VocabularyItem[] | null>(null);
  const [hasQuiz, setHasQuiz] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!lessonId) return;
    const id = Number(lessonId);

    listVocabulary(id)
      .then(setVocabulary)
      .catch(() => setError("Something went wrong loading the vocabulary."));

    getQuizByLesson(id)
      .then(() => setHasQuiz(true))
      .catch(() => setHasQuiz(false));
  }, [lessonId]);

  return (
    <div className={styles.page}>
      <Link to="/courses" className={styles.backLink}>
        ← Courses
      </Link>

      <h1>Vocabulary</h1>

      {error && <ErrorState message={error} />}
      {!error && !vocabulary && <LoadingState label="Loading vocabulary" />}

      <div className={styles.vocabList}>
        {vocabulary?.map((item) => (
          <div key={item.id} className={styles.vocabCard}>
            <div className={styles.vocabHead}>
              <span className={styles.word}>{item.word}</span>
              <span className={styles.translation}>{item.translation}</span>
            </div>
            {item.example_sentence && (
              <p className={styles.example}>{item.example_sentence}</p>
            )}
          </div>
        ))}
      </div>

      {hasQuiz && (
        <Link to={`/lessons/${lessonId}/quiz`} className={styles.quizButton}>
          Start quiz
        </Link>
      )}
    </div>
  );
}
