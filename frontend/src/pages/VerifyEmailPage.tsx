import { useEffect, useRef, useState } from "react";
import { Link, useSearchParams } from "react-router-dom";
import { verifyEmail } from "../api/auth";
import { ApiError } from "../api/client";
import { LoadingState } from "../components/StatusMessage";
import styles from "./AuthPage.module.css";

export function VerifyEmailPage() {
  const [searchParams] = useSearchParams();
  const token = searchParams.get("token") ?? "";
  const [status, setStatus] = useState<"loading" | "success" | "error">("loading");
  const [error, setError] = useState<string | null>(null);

  // React 18 StrictMode runs effects twice in development. The
  // verification token is single-use by design (see the backend's
  // AuthToken), so without this guard the second POST consumed nothing,
  // got a 400 back, and overwrote the first call's success with "invalid
  // or expired" — the email WAS verified, but the page said it failed.
  const hasRequestedRef = useRef(false);

  useEffect(() => {
    if (!token) {
      setStatus("error");
      setError("This link is missing its token. Please use the link from your email.");
      return;
    }
    if (hasRequestedRef.current) return;
    hasRequestedRef.current = true;

    verifyEmail(token)
      .then(() => setStatus("success"))
      .catch((err) => {
        setStatus("error");
        setError(err instanceof ApiError ? err.message : "This verification link is invalid or has expired.");
      });
  }, [token]);

  return (
    <div className={styles.page}>
      <div className={styles.card}>
        <h1>Email verification</h1>

        {status === "loading" && <LoadingState label="Verifying your email" />}
        {status === "success" && <p className={styles.subtitle}>Your email has been verified ✓</p>}
        {status === "error" && <div className={styles.errorText}>{error}</div>}

        <p className={styles.footer}>
          <Link to="/">Go to Lingua</Link>
        </p>
      </div>
    </div>
  );
}
