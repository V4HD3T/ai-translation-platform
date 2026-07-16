import { apiRequest } from "./client";
import type { ReviewQueueItem, ReviewResult } from "../types";

export function getReviewQueue(): Promise<ReviewQueueItem[]> {
  return apiRequest<ReviewQueueItem[]>("/users/me/review-queue", { auth: true });
}

export function submitReview(
  vocabularyItemId: number,
  quality: number
): Promise<ReviewResult> {
  return apiRequest<ReviewResult>(`/vocabulary/${vocabularyItemId}/review`, {
    method: "POST",
    body: { quality },
    auth: true,
  });
}
