// ── 认证 ────────────────────────────────────────────────────────────

export interface User {
  id: number;
  username: string;
  created_at: string;
}

/** 后端登录接口返回：{ token, token_type }，注意不是 access_token */
export interface TokenResponse {
  token: string;
  token_type: string;
}

// ── 文档 ────────────────────────────────────────────────────────────

export type DocumentStatus =
  | "pending"
  | "parsing"
  | "chunking"
  | "embedding"
  | "ready"
  | "failed";

export interface Document {
  id: number;
  file_name: string;
  file_type: string;
  file_size: number;
  status: DocumentStatus;
  chunk_count: number;
  created_at: string;
  updated_at: string;
}

// ── 会话 / 消息 ─────────────────────────────────────────────────────

export interface Conversation {
  id: number;
  user_id: number;
  title: string;
  created_at: string;
  updated_at: string;
}

export interface Message {
  id: number;
  conversation_id: number;
  role: "user" | "assistant" | "system";
  content: string;
  created_at: string;
  /** 引用 JSON（assistant 消息），后端存的是字符串，这里可选解析后的数组 */
  citations?: Citation[];
}

/** 引用来源（对应后端 retrieval 事件里的 sources 元素） */
export interface Citation {
  document_id: number;
  document_name: string;
  seq_no: number;
  content: string;
  score: number;
}

// ── SSE 聊天 ────────────────────────────────────────────────────────

/** 后端 chat SSE 事件 */
export type SSEEvent =
  | { type: "retrieval"; sources: Citation[] }
  | { type: "delta"; text: string }
  | { type: "done"; conversation_id: number }
  | { type: "error"; details: string };

export interface SSEHandlers {
  onRetrieval?: (sources: Citation[]) => void;
  onToken?: (text: string) => void;
  onDone?: (conversationId?: number) => void;
  onError?: (err: string) => void;
}
