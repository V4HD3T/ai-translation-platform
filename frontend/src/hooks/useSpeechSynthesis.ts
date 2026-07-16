import { useCallback, useEffect, useState } from "react";
import { toSpeechLang } from "../utils/speechLang";

interface UseSpeechSynthesisResult {
  /** Whether the browser supports the Web Speech Synthesis API. Support is
   * broader than SpeechRecognition — Firefox has it too, unlike STT. */
  isSupported: boolean;
  isSpeaking: boolean;
  speak: (text: string, langCode: string) => void;
  stop: () => void;
}

/** Wraps the browser's built-in text-to-speech API. Doesn't send text to a
 * server and doesn't download a voice model — runs entirely client-side,
 * using whatever voices the operating system already has installed. */
export function useSpeechSynthesis(): UseSpeechSynthesisResult {
  const [isSpeaking, setIsSpeaking] = useState(false);

  const isSupported = typeof window !== "undefined" && "speechSynthesis" in window;

  useEffect(() => {
    return () => {
      if (isSupported) window.speechSynthesis.cancel();
    };
  }, [isSupported]);

  const speak = useCallback(
    (text: string, langCode: string) => {
      if (!isSupported || !text.trim()) return;

      // Cancel anything already queued/playing before starting a new utterance;
      // otherwise clicking the button repeatedly queues up overlapping speech.
      window.speechSynthesis.cancel();

      const utterance = new SpeechSynthesisUtterance(text);
      utterance.lang = toSpeechLang(langCode);
      utterance.onstart = () => setIsSpeaking(true);
      utterance.onend = () => setIsSpeaking(false);
      utterance.onerror = () => setIsSpeaking(false);

      window.speechSynthesis.speak(utterance);
    },
    [isSupported]
  );

  const stop = useCallback(() => {
    if (isSupported) window.speechSynthesis.cancel();
    setIsSpeaking(false);
  }, [isSupported]);

  return { isSupported, isSpeaking, speak, stop };
}
