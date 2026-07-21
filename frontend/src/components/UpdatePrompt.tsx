import { useRegisterSW } from "virtual:pwa-register/react";
import styles from "./UpdatePrompt.module.css";

/**
 * Offline/update surface for the PWA (v0.1.3).
 *
 * registerType is "prompt", not "autoUpdate", on purpose: silently
 * swapping the app out from under someone mid-quiz would lose their
 * in-progress answers (the served-set session is server-side, but the
 * unsubmitted answers are React state). The person decides when to take
 * the new version.
 */
export function UpdatePrompt() {
  const {
    offlineReady: [offlineReady, setOfflineReady],
    needRefresh: [needRefresh, setNeedRefresh],
    updateServiceWorker,
  } = useRegisterSW();

  if (!offlineReady && !needRefresh) return null;

  function dismiss() {
    setOfflineReady(false);
    setNeedRefresh(false);
  }

  return (
    <div className={styles.prompt} role="status" aria-live="polite">
      <span className={styles.message}>
        {needRefresh ? "A new version is available." : "Ready to work offline."}
      </span>
      {needRefresh && (
        <button
          type="button"
          className={styles.reloadButton}
          onClick={() => updateServiceWorker(true)}
        >
          Reload
        </button>
      )}
      <button
        type="button"
        className={styles.dismissButton}
        onClick={dismiss}
        aria-label="Dismiss notification"
      >
        ×
      </button>
    </div>
  );
}
