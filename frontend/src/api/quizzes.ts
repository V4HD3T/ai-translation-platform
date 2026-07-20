import { apiRequest } from "./client";
import type { Quiz, QuizResult } from "../types";

export function getQuizByLesson(lessonId: number): Promise<Quiz> {
  // auth matters here twice over: adaptive difficulty only activates for
  // a known learner, and (v0.0.9) the backend records which questions it
  // served as a QuizSession -- submissions are graded against that served
  // set, and only authenticated fetches create one.
  return apiRequest<Quiz>(`/lessons/${lessonId}/quiz`, { auth: true });
}

export function submitQuiz(
  quizId: number,
  sessionId: number,
  answers: Record<string, string>
): Promise<QuizResult> {
  return apiRequest<QuizResult>(`/quizzes/${quizId}/submit`, {
    method: "POST",
    body: { session_id: sessionId, answers },
    auth: true,
  });
}
