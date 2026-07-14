import { useEffect, useState } from "react";
import { fetchTranslationHistory } from "../api/translate";
import { LoadingState, ErrorState } from "../components/StatusMessage";
import type { TranslateResult } from "../types";
import styles from "./HistoryPage.module.css";

export function HistoryPage() {
  const [history, setHistory] = useState<TranslateResult[] | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    fetchTranslationHistory()
      .then(setHistory)
      .catch(() => setError("Something went wrong loading your history."));
  }, []);

  return (
    <div className={styles.page}>
      <h1>Translation history</h1>
      <p className={styles.subtitle}>Translations you've made in the past.</p>

      {error && <ErrorState message={error} />}
      {!error && !history && <LoadingState label="Loading history" />}

      {history && history.length === 0 && (
        <p className={styles.empty}>You haven't translated anything yet.</p>
      )}

      <div className={styles.list}>
        {history?.map((item, index) => (
          <div key={index} className={styles.row}>
            <div className={styles.textCol}>
              <span className={styles.langTag}>{item.source_lang}</span>
              <p>{item.source_text}</p>
            </div>
            <span className={styles.arrow}>→</span>
            <div className={styles.textCol}>
              <span className={styles.langTag}>{item.target_lang}</span>
              <p>{item.translated_text}</p>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
