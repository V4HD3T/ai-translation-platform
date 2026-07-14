import { useEffect, useState, type FormEvent } from "react";
import { Link, useParams } from "react-router-dom";
import { getQuizByLesson, submitQuiz } from "../api/quizzes";
import { useAuth } from "../context/AuthContext";
import { LoadingState, ErrorState } from "../components/StatusMessage";
import type { Quiz, QuizResult } from "../types";
import styles from "./QuizPage.module.css";

export function QuizPage() {
  const { lessonId } = useParams<{ lessonId: string }>();
  const { user } = useAuth();
  const [quiz, setQuiz] = useState<Quiz | null>(null);
  const [answers, setAnswers] = useState<Record<string, string>>({});
  const [result, setResult] = useState<QuizResult | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [isSubmitting, setIsSubmitting] = useState(false);

  useEffect(() => {
    if (!lessonId) return;
    getQuizByLesson(Number(lessonId))
      .then(setQuiz)
      .catch(() => setError("No quiz was found for this lesson."));
  }, [lessonId]);

  function selectAnswer(questionId: number, option: string) {
    setAnswers((prev) => ({ ...prev, [String(questionId)]: option }));
  }

  async function handleSubmit(e: FormEvent) {
    e.preventDefault();
    if (!quiz) return;
    setError(null);
    setIsSubmitting(true);
    try {
      const res = await submitQuiz(quiz.id, answers);
      setResult(res);
    } catch {
      setError("Something went wrong submitting your answers.");
    } finally {
      setIsSubmitting(false);
    }
  }

  function handleRetry() {
    setResult(null);
    setAnswers({});
  }

  if (!user) {
    return (
      <div className={styles.page}>
        <ErrorState message="You need to log in to take this quiz." />
        <Link to="/login" className={styles.backLink}>
          Log in →
        </Link>
      </div>
    );
  }

  return (
    <div className={styles.page}>
      <Link to={`/lessons/${lessonId}`} className={styles.backLink}>
        ← Back to lesson
      </Link>

      {error && <ErrorState message={error} />}
      {!error && !quiz && <LoadingState label="Loading quiz" />}

      {quiz && !result && (
        <>
          <h1>{quiz.title}</h1>
          <form onSubmit={handleSubmit}>
            {quiz.questions.map((question, index) => (
              <fieldset key={question.id} className={styles.question}>
                <legend className={styles.questionText}>
                  {index + 1}. {question.question_text}
                </legend>
                <div className={styles.options}>
                  {question.options.map((option) => (
                    <label key={option} className={styles.option}>
                      <input
                        type="radio"
                        name={`question-${question.id}`}
                        value={option}
                        checked={answers[String(question.id)] === option}
                        onChange={() => selectAnswer(question.id, option)}
                        required
                      />
                      {option}
                    </label>
                  ))}
                </div>
              </fieldset>
            ))}

            <button type="submit" className={styles.submit} disabled={isSubmitting}>
              {isSubmitting ? "Submitting..." : "Submit answers"}
            </button>
          </form>
        </>
      )}

      {result && (
        <div className={styles.result}>
          <span className={styles.resultScore}>{result.score}%</span>
          <p className={styles.resultDetail}>
            You got {result.correct_count} out of {result.total_questions} questions
            right.
          </p>
          <div className={styles.resultActions}>
            <button type="button" className={styles.retryButton} onClick={handleRetry}>
              Try again
            </button>
            <Link to={`/lessons/${lessonId}`} className={styles.backToLesson}>
              Back to lesson
            </Link>
          </div>
        </div>
      )}
    </div>
  );
}
