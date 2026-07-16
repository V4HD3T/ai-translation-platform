import styles from "./SpeakerButton.module.css";

interface SpeakerButtonProps {
  isSpeaking: boolean;
  onClick: () => void;
  disabled?: boolean;
  title?: string;
}

export function SpeakerButton({ isSpeaking, onClick, disabled, title }: SpeakerButtonProps) {
  return (
    <button
      type="button"
      className={`${styles.button} ${isSpeaking ? styles.speaking : ""}`}
      onClick={onClick}
      disabled={disabled}
      title={title ?? (isSpeaking ? "Stop" : "Listen")}
      aria-label={title ?? (isSpeaking ? "Stop reading aloud" : "Read aloud")}
      aria-pressed={isSpeaking}
    >
      <svg
        width="16"
        height="16"
        viewBox="0 0 24 24"
        fill="none"
        stroke="currentColor"
        strokeWidth="2"
        strokeLinecap="round"
        strokeLinejoin="round"
        aria-hidden="true"
      >
        <polygon points="11 5 6 9 2 9 2 15 6 15 11 19 11 5" />
        {isSpeaking ? (
          <line x1="16" y1="9" x2="22" y2="15" />
        ) : (
          <path d="M15.54 8.46a5 5 0 0 1 0 7.07" />
        )}
        {isSpeaking ? (
          <line x1="22" y1="9" x2="16" y2="15" />
        ) : (
          <path d="M19.07 4.93a10 10 0 0 1 0 14.14" />
        )}
      </svg>
    </button>
  );
}
