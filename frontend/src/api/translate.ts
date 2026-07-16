import { apiRequest } from "./client";
import type { Language, TranslateResult } from "../types";

export interface DetectLanguageResult {
  language_code: string;
  confidence: number;
  is_reliable: boolean;
}

export function listLanguages(): Promise<Language[]> {
  return apiRequest<Language[]>("/languages");
}

export function detectLanguage(text: string): Promise<DetectLanguageResult> {
  return apiRequest<DetectLanguageResult>("/detect-language", {
    method: "POST",
    body: { text },
  });
}

export function translateText(
  text: string,
  sourceLang: string,
  targetLang: string
): Promise<TranslateResult> {
  return apiRequest<TranslateResult>("/translate", {
    method: "POST",
    body: { text, source_lang: sourceLang, target_lang: targetLang },
    auth: true, // saved to history if a token is present; fine if not (backend allows anonymous use)
  });
}

export function fetchTranslationHistory(): Promise<TranslateResult[]> {
  return apiRequest<TranslateResult[]>("/translate/history", { auth: true });
}
