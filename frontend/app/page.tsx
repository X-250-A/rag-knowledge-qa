"use client";

import { Suspense, useState, useCallback } from "react";
import { useAuth } from "@/hooks/useAuth";
import Loading from "@/components/ui/Loading";
import Button from "@/components/ui/Button";
import ChatContainer from "@/components/chat/ChatContainer";
import Link from "next/link";
import { useSearchParams } from "next/navigation";

function HomeContent() {
    const { user, loading, logout } = useAuth();
    const searchParams = useSearchParams();

    const initialConversationId = (() => {
        const raw = searchParams.get("conversationId");
        if (!raw) return null;
        const n = Number(raw);
        return Number.isNaN(n) ? null : n;
    })();

    const [currentConversationId, setCurrentConversationId] = useState<number | null>(initialConversationId);

    const handleConversationCreated = useCallback((conversationId: number) => {
        setCurrentConversationId(conversationId);
        window.history.replaceState(null, "", `/?conversationId=${conversationId}`);
    }, []);

    if (loading) {
        return (
            <div className="min-h-screen flex items-center justify-center">
                <Loading size="lg" text="正在加载..." />
            </div>
        );
    }

    if (!user) {
        return <LandingPage />;
    }

    return (
        <div className="min-h-screen flex flex-col">
            {/* 导航栏 */}
            <header className="glass-strong sticky top-0 z-50 border-b border-white/50">
                <div className="max-w-5xl mx-auto flex items-center justify-between px-6 py-3">
                    <Link href="/" className="flex items-center gap-2 shrink-0">
                        <span className="text-2xl">📚</span>
                        <span className="text-lg font-bold gradient-text">RAG 知识库问答</span>
                    </Link>

                    <div className="flex items-center gap-2 flex-wrap justify-end">
                        <Link
                            href="/"
                            onClick={(e) => {
                                e.preventDefault();
                                setCurrentConversationId(null);
                                window.history.replaceState(null, "", "/");
                            }}
                            className="text-sm text-stone-500 hover:text-orange-600 transition-colors px-2 py-1"
                        >
                            ＋ 新会话
                        </Link>
                        <Link
                            href="/documents"
                            className="text-sm text-stone-500 hover:text-orange-600 transition-colors px-2 py-1"
                        >
                            文档管理
                        </Link>
                        <span className="text-sm text-stone-400 pl-2 border-l border-stone-200">
                            {user.username}
                        </span>
                        <Button variant="ghost" size="sm" onClick={logout}>
                            退出
                        </Button>
                    </div>
                </div>
            </header>

            <main className="flex-1 overflow-hidden flex flex-col">
                <ChatContainer
                    conversationId={currentConversationId}
                    onConversationCreated={handleConversationCreated}
                />
            </main>
        </div>
    );
}

/** 未登录时展示的 Landing 页 */
function LandingPage() {
    return (
        <div className="min-h-screen flex flex-col">
            <header className="glass-strong sticky top-0 z-50 border-b border-white/50">
                <div className="max-w-6xl mx-auto flex items-center justify-between px-6 py-4">
                    <div className="flex items-center gap-2.5">
                        <span className="text-2xl">📚</span>
                        <span className="text-lg font-bold gradient-text">RAG 知识库问答</span>
                    </div>
                    <div className="flex items-center gap-3">
                        <Link href="/login">
                            <Button variant="ghost" size="sm">登录</Button>
                        </Link>
                        <Link href="/register">
                            <Button variant="primary" size="sm">免费注册</Button>
                        </Link>
                    </div>
                </div>
            </header>

            <main className="flex-1 flex items-center justify-center px-6">
                <div className="max-w-3xl w-full text-center">
                    <div className="relative mb-8">
                        <div className="animate-scale-in inline-flex items-center justify-center w-24 h-24 rounded-3xl bg-gradient-to-br from-orange-400 to-rose-500 shadow-2xl shadow-orange-300/50 mb-4">
                            <span className="text-5xl">🧠</span>
                        </div>
                    </div>

                    <h1 className="text-5xl sm:text-6xl font-extrabold text-stone-800 tracking-tight mb-4 animate-fade-in-up">
                        让 AI 读懂
                        <br />
                        <span className="gradient-text">你的文档</span>
                    </h1>

                    <p className="text-lg text-stone-500 mb-10 max-w-lg mx-auto leading-relaxed animate-fade-in-up" style={{ animationDelay: "0.1s" }}>
                        上传 PDF / Word / Markdown，
                        <br className="hidden sm:block" />
                        上传即可对话，答案引用原文片段。
                    </p>

                    <div className="flex gap-4 justify-center animate-fade-in-up" style={{ animationDelay: "0.2s" }}>
                        <Link href="/register">
                            <Button variant="primary" size="lg">
                                ✨ 开始使用
                            </Button>
                        </Link>
                        <Link href="/login">
                            <Button variant="secondary" size="lg">
                                已有账号
                            </Button>
                        </Link>
                    </div>

                    <div className="grid grid-cols-1 sm:grid-cols-3 gap-4 mt-16 animate-fade-in-up" style={{ animationDelay: "0.3s" }}>
                        <FeatureCard
                            emoji="📤"
                            title="文档即知识库"
                            desc="上传即解析、分块、向量化，自动入库"
                        />
                        <FeatureCard
                            emoji="🔍"
                            title="检索增强问答"
                            desc="向量检索 + LLM 生成，答案有据可依"
                        />
                        <FeatureCard
                            emoji="📎"
                            title="引用原文"
                            desc="每个答案附上来源片段，可追溯"
                        />
                    </div>
                </div>
            </main>

            <footer className="py-6 text-center text-sm text-stone-400">
                Made with ❤️ by RAG Knowledge QA
            </footer>
        </div>
    );
}

function FeatureCard({ emoji, title, desc }: { emoji: string; title: string; desc: string }) {
    return (
        <div className="glass rounded-2xl p-5 text-center hover:shadow-lg hover:-translate-y-0.5 transition-all duration-300">
            <div className="text-3xl mb-2">{emoji}</div>
            <h3 className="text-sm font-semibold text-stone-700 mb-1">{title}</h3>
            <p className="text-xs text-stone-400 leading-relaxed">{desc}</p>
        </div>
    );
}

export default function HomePage() {
    return (
        <Suspense
            fallback={
                <div className="min-h-screen flex items-center justify-center">
                    <Loading size="lg" />
                </div>
            }
        >
            <HomeContent />
        </Suspense>
    );
}
