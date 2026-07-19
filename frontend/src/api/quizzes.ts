import { apiRequest } from "./client";
import type { Quiz, QuizResult } from "../types";

export function getQuizByLesson(lessonId: number): Promise<Quiz> {
  // auth matters here even though the endpoint allows anonymous access:
  // adaptive difficulty (serving easier/harder questions based on the
  // learner's average score) only activates when the backend knows who is
  // asking. Without this, logged-in users were silently served the same
  // unfiltered question set as anonymous visitors.
  return apiRequest<Quiz>(`/lessons/${lessonId}/quiz`, { auth: true });
}

export function submitQuiz(
  quizId: number,
  answers: Record<string, string>
): Promise<QuizResult> {
  return apiRequest<QuizResult>(`/quizzes/${quizId}/submit`, {
    method: "POST",
    body: { answers },
    auth: true,
  });
}
