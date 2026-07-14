import { apiRequest } from "./client";
import type { Language, TranslateResult } from "../types";

export function listLanguages(): Promise<Language[]> {
  return apiRequest<Language[]>("/languages");
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
