import type {
    User,
    Document,
    Conversation,
    Message,
    Citation,
    TokenResponse,
    SSEHandlers,
} from "@/types";

const BASE_URL = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

// ── 底层请求 ──────────────────────────────────────────────────────────

async function request<T>(
    method: string,
    path: string,
    body?: unknown,
): Promise<T> {
    const token = localStorage.getItem("token");
    const res = await fetch(`${BASE_URL}${path}`, {
        method,
        headers: {
            "Content-Type": "application/json",
            Authorization: token ? `Bearer ${token}` : "",
        },
        body: body ? JSON.stringify(body) : undefined,
    });

    if (res.status === 401) {
        localStorage.removeItem("token");
        window.location.href = "/login";
        throw new Error("登录已过期，请重新登录");
    }

    if (!res.ok) {
        const text = await res.text();
        let message: string;
        try {
            const json = JSON.parse(text);
            message = json.detail ?? text;
        } catch {
            message = text || res.statusText;
        }
        throw new Error(message);
    }

    return (await res.json()) as Promise<T>;
}

// ── 认证 ──────────────────────────────────────────────────────────────

export async function register(
    username: string,
    password: string,
): Promise<User> {
    return request<User>("POST", "/api/auth/register", { username, password });
}

export async function login(
    username: string,
    password: string,
): Promise<TokenResponse> {
    return request<TokenResponse>("POST", "/api/auth/login", { username, password });
}

export async function getMe(): Promise<User> {
    return request<User>("GET", "/api/auth/me");
}

// ── 文档 ──────────────────────────────────────────────────────────────

export async function listDocuments(): Promise<Document[]> {
    // 后端路由是 /api/documents/（带尾斜杠），避免 307 重定向
    return request<Document[]>("GET", "/api/documents/");
}

export async function uploadDocument(file: File): Promise<Document> {
    const token = localStorage.getItem("token");
    const form = new FormData();
    form.append("file", file);

    const res = await fetch(`${BASE_URL}/api/documents/`, {
        method: "POST",
        headers: { Authorization: token ? `Bearer ${token}` : "" },
        body: form,
    });

    if (res.status === 401) {
        localStorage.removeItem("token");
        window.location.href = "/login";
        throw new Error("登录已过期，请重新登录");
    }
    if (!res.ok) {
        const text = await res.text();
        let message: string;
        try {
            message = JSON.parse(text).detail ?? text;
        } catch {
            message = text || res.statusText;
        }
        throw new Error(message);
    }
    return (await res.json()) as Promise<Document>;
}

export async function deleteDocument(documentId: number): Promise<void> {
    await request<unknown>("DELETE", `/api/documents/${documentId}`);
}

// ── 会话 / 消息 ───────────────────────────────────────────────────────

export async function listConversations(): Promise<Conversation[]> {
    return request<Conversation[]>("GET", "/api/conversations/");
}

export async function getConversationMessages(
    conversationId: number,
): Promise<Message[]> {
    return request<Message[]>(
        "GET",
        `/api/conversations/${conversationId}/messages`,
    );
}

// ── 聊天 (SSE 流式) ───────────────────────────────────────────────────

export async function sendMessage(
    question: string,
    conversationId: number | null,
    handlers: SSEHandlers,
): Promise<void> {
    const { onRetrieval, onToken, onDone, onError } = handlers;

    const token = localStorage.getItem("token");
    const res = await fetch(`${BASE_URL}/api/chat`, {
        method: "POST",
        headers: {
            "Content-Type": "application/json",
            Authorization: token ? `Bearer ${token}` : "",
        },
        body: JSON.stringify({ question, conversation_id: conversationId ?? null }),
    });

    if (res.status === 401) {
        localStorage.removeItem("token");
        window.location.href = "/login";
        throw new Error("登录已过期，请重新登录");
    }
    if (!res.ok) {
        const text = await res.text();
        let message: string;
        try {
            message = JSON.parse(text).detail ?? text;
        } catch {
            message = text || res.statusText;
        }
        throw new Error(message);
    }

    const reader = res.body!.getReader();
    const decoder = new TextDecoder();
    let buffer = "";

    while (true) {
        const { done, value } = await reader.read();
        if (done) break;

        buffer += decoder.decode(value, { stream: true });

        const parts = buffer.split("\n\n");
        buffer = parts.pop() ?? "";

        for (const part of parts) {
            if (!part.startsWith("data: ")) continue;
            const data = JSON.parse(part.slice(6));
            switch (data.type) {
                case "retrieval":
                    onRetrieval?.((data.sources as Citation[]) ?? []);
                    break;
                case "delta":
                    onToken?.(data.text ?? "");
                    break;
                case "done":
                    onDone?.(data.conversation_id);
                    break;
                case "error":
                    onError?.(data.details ?? "生成失败");
                    break;
            }
        }
    }
}
