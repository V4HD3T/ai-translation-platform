import { apiRequest } from "./client";
import type { User } from "../types";

export interface RegisterPayload {
  username: string;
  email: string;
  password: string;
  native_language: string;
}

export interface TokenResponse {
  access_token: string;
  token_type: string;
}

export function register(payload: RegisterPayload): Promise<User> {
  return apiRequest<User>("/auth/register", { method: "POST", body: payload });
}

export function login(username: string, password: string): Promise<TokenResponse> {
  return apiRequest<TokenResponse>("/auth/login", {
    method: "POST",
    form: { username, password },
  });
}

export function fetchCurrentUser(): Promise<User> {
  return apiRequest<User>("/auth/me", { auth: true });
}
