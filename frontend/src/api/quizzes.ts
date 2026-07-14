import { apiRequest } from "./client";
import type { Quiz, QuizResult } from "../types";

export function getQuizByLesson(lessonId: number): Promise<Quiz> {
  return apiRequest<Quiz>(`/lessons/${lessonId}/quiz`);
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
