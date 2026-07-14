export interface User {
  id: number;
  username: string;
  email: string;
  native_language: string;
}

export interface Language {
  code: string;
  name: string;
}

export interface TranslateResult {
  source_text: string;
  translated_text: string;
  source_lang: string;
  target_lang: string;
}

export interface Course {
  id: number;
  language_code: string;
  title: string;
  level: string;
  description: string;
}

export interface Lesson {
  id: number;
  title: string;
  content: string;
  order: number;
}

export interface VocabularyItem {
  id: number;
  word: string;
  translation: string;
  example_sentence: string;
}

export interface QuizQuestion {
  id: number;
  question_text: string;
  options: string[];
}

export interface Quiz {
  id: number;
  title: string;
  quiz_type: string;
  questions: QuizQuestion[];
}

export interface QuizResult {
  score: number;
  total_questions: number;
  correct_count: number;
}
