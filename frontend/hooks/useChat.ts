import { sendMessage as apiSendMessage, getConversationMessages } from "@/lib/api";
import type { Message, Citation } from "@/types";
import { useState, useRef, useCallback } from "react";

// 聊天核心 hook：发消息、接收 SSE 流、会话历史
export function useChat() {
    const [messages, setMessages] = useState<Message[]>([]);
    const [streaming, setStreaming] = useState("");
    const [sources, setSources] = useState<Citation[]>([]);
    const [sending, setSending] = useState(false);

    /** 当前已加载的会话 id，避免重复加载 */
    const loadedConversationRef = useRef<number | null>(null);
    /** streaming 文本同步副本 */
    const streamingBufRef = useRef("");
    /** 当前引用的同步副本 */
    const sourcesRef = useRef<Citation[]>([]);

    /** 加载会话历史消息 */
    const loadMessages = useCallback(async (conversationId: number) => {
        if (loadedConversationRef.current === conversationId) return;
        loadedConversationRef.current = conversationId;
        try {
            const history = await getConversationMessages(conversationId);
            setMessages(history);
        } catch {
            // 加载失败不阻断聊天，静默处理
        }
    }, []);

    /** 重置为新会话 */
    const reset = useCallback(() => {
        setMessages([]);
        setStreaming("");
        setSources([]);
        setSending(false);
        loadedConversationRef.current = null;
        streamingBufRef.current = "";
        sourcesRef.current = [];
    }, []);

    const sendMessage = async (text: string, conversationId: number | null): Promise<number | null> => {
        if (!text.trim() || sending) {
            return null;
        }

        const userMsg: Message = {
            id: Date.now(),
            conversation_id: conversationId ?? 0,
            role: "user",
            content: text,
            created_at: new Date().toISOString(),
        };
        setMessages((prev) => [...prev, userMsg]);
        setSending(true);

        const finalConversationId = await new Promise<number | null>((resolve) => {
            apiSendMessage(
                text,
                conversationId,
                {
                    onRetrieval: (sources) => {
                        sourcesRef.current = sources;
                        setSources(sources);
                    },
                    onToken: (chunk) => {
                        streamingBufRef.current += chunk;
                        setStreaming(streamingBufRef.current);
                    },
                    onDone: (newConversationId) => {
                        const finalText = streamingBufRef.current;
                        const finalSources = sourcesRef.current;
                        streamingBufRef.current = "";
                        sourcesRef.current = [];
                        setStreaming("");
                        setSources([]);

                        if (finalText.trim()) {
                            const aiMsg: Message = {
                                id: Date.now(),
                                conversation_id: newConversationId ?? conversationId ?? 0,
                                role: "assistant",
                                content: finalText,
                                citations: finalSources.length ? finalSources : undefined,
                                created_at: new Date().toISOString(),
                            };
                            setMessages((prev) => [...prev, aiMsg]);
                        }
                        setSending(false);
                        resolve(newConversationId ?? null);
                    },
                    onError: (err) => {
                        streamingBufRef.current = "";
                        sourcesRef.current = [];
                        setStreaming("");
                        setSources([]);
                        setSending(false);

                        const errMsg: Message = {
                            id: Date.now(),
                            conversation_id: conversationId ?? 0,
                            role: "assistant",
                            content: err,
                            created_at: new Date().toISOString(),
                        };
                        setMessages((prev) => [...prev, errMsg]);
                        resolve(null);
                    },
                },
            );
        });

        return finalConversationId;
    };

    return { messages, sources, streaming, sending, sendMessage, loadMessages, reset };
}
