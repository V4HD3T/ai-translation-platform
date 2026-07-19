import { apiRequest } from "./client";
import type { Course, Lesson, Page, VocabularyItem } from "../types";

export function listCourses(limit = 100, offset = 0): Promise<Page<Course>> {
  // The catalogue is small, so one generous page (backend max) keeps the
  // UI simple; the envelope's `total` still tells us if it ever outgrows
  // this and needs real paging controls.
  return apiRequest<Page<Course>>(`/courses?limit=${limit}&offset=${offset}`);
}

export function getCourse(courseId: number): Promise<Course> {
  return apiRequest<Course>(`/courses/${courseId}`);
}

export function listLessons(courseId: number): Promise<Lesson[]> {
  return apiRequest<Lesson[]>(`/courses/${courseId}/lessons`);
}

export function getLesson(lessonId: number): Promise<Lesson> {
  return apiRequest<Lesson>(`/lessons/${lessonId}`);
}

export function listVocabulary(lessonId: number): Promise<VocabularyItem[]> {
  return apiRequest<VocabularyItem[]>(`/lessons/${lessonId}/vocabulary`);
}
