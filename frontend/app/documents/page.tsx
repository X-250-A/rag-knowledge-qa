"use client";

import { useEffect } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";
import { useAuth } from "@/hooks/useAuth";
import { useDocuments } from "@/hooks/useDocuments";
import Loading from "@/components/ui/Loading";
import Button from "@/components/ui/Button";
import UploadZone from "@/components/document/UploadZone";
import DocumentList from "@/components/document/DocumentList";
import Card from "@/components/ui/Card";

export default function DocumentsPage() {
    const router = useRouter();
    const { user, loading: authLoading, logout } = useAuth();
    const { documents, loading, uploading, error, load, upload, remove } = useDocuments();

    useEffect(() => {
        if (!authLoading && !user) {
            router.push("/login");
        }
    }, [authLoading, user, router]);

    useEffect(() => {
        if (user) {
            load();
        }
    }, [user, load]);

    if (authLoading) {
        return (
            <div className="min-h-screen flex items-center justify-center">
                <Loading size="lg" text="正在加载..." />
            </div>
        );
    }

    if (!user) {
        return null;
    }

    return (
        <div className="min-h-screen flex flex-col">
            <header className="glass-strong sticky top-0 z-50 border-b border-white/50">
                <div className="max-w-4xl mx-auto flex items-center justify-between px-6 py-3">
                    <div className="flex items-center gap-2">
                        <span className="text-2xl">📚</span>
                        <span className="text-lg font-bold gradient-text">文档管理</span>
                    </div>
                    <div className="flex items-center gap-2">
                        <Link
                            href="/"
                            className="text-sm text-stone-500 hover:text-orange-600 transition-colors px-2 py-1"
                        >
                            ← 返回问答
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

            <main className="flex-1 max-w-4xl w-full mx-auto px-6 py-8 space-y-6">
                <Card title="上传文档" variant="glass">
                    <UploadZone onUpload={upload} uploading={uploading} error={error} />
                </Card>

                <Card title="我的文档">
                    <DocumentList documents={documents} loading={loading} onDelete={remove} />
                </Card>
            </main>
        </div>
    );
}
