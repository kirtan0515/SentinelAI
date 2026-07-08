/**
 * Shared TypeScript type definitions for SentinelAI frontend.
 */

export interface User {
  id: string;
  email: string;
  username: string;
  full_name: string | null;
  role: "user" | "analyst" | "admin";
  is_active: boolean;
  is_verified: boolean;
  mfa_enabled: boolean;
  last_login: string | null;
  created_at: string;
}

export interface TokenResponse {
  access_token: string;
  refresh_token: string;
  token_type: string;
  expires_in: number;
}

export interface ChatMessage {
  id: string;
  session_id: string;
  role: "user" | "assistant" | "system";
  content: string;
  model: string;
  tokens_used: number;
  latency_ms: number;
  security_score: number;
  blocked: boolean;
  created_at: string;
}

export interface ChatSession {
  id: string;
  title: string;
  model: string;
  message_count: number;
  created_at: string;
  updated_at: string;
}

export interface SecurityCheckResult {
  is_safe: boolean;
  score: number;
  threats_detected: string[];
  details: Record<string, any> | null;
}

export interface AuditLog {
  id: string;
  user_id: string;
  username: string;
  ip_address: string;
  endpoint: string;
  method: string;
  prompt: string | null;
  model: string | null;
  latency_ms: number | null;
  status_code: number;
  security_score: number | null;
  attack_detected: boolean;
  blocked: boolean;
  created_at: string;
}

export interface Document {
  id: string;
  filename: string;
  file_type: string;
  file_size: number;
  status: "processing" | "ready" | "failed";
  chunk_count: number;
  created_at: string;
}

export interface ModelConfig {
  id: string;
  provider: string;
  model_name: string;
  display_name: string;
  is_default: boolean;
  is_enabled: boolean;
  max_tokens: number;
  temperature: number;
}
