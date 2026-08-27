"use client";

import type { Document } from "@/types";
import Button from "@/components/ui/Button";

interface Props {
    documents: Document[];
    loading: boolean;
    onDelete: (id: number) => void;
}

const statusMeta: Record<string, { label: string; className: string }> = {
    pending: { label: "待处理", className: "bg-stone-100 text-stone-500" },
    parsing: { label: "解析中", className: "bg-amber-100 text-amber-600" },
    chunking: { label: "分块中", className: "bg-amber-100 text-amber-600" },
    embedding: { label: "向量化中", className: "bg-amber-100 text-amber-600" },
    ready: { label: "已就绪", className: "bg-emerald-100 text-emerald-600" },
    failed: { label: "失败", className: "bg-red-100 text-red-600" },
};

function formatSize(bytes: number): string {
    if (bytes < 1024) return `${bytes} B`;
    if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
    return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
}

export default function DocumentList({ documents, loading, onDelete }: Props) {
    if (loading) {
        return <p className="text-sm text-stone-400 text-center py-8">加载中...</p>;
    }

    if (documents.length === 0) {
        return (
            <p className="text-sm text-stone-400 text-center py-8">
                还没有文档，先上传一个吧
            </p>
        );
    }

    return (
        <div className="space-y-2.5">
            {documents.map((doc) => {
                const meta = statusMeta[doc.status] ?? statusMeta.pending;
                return (
                    <div
                        key={doc.id}
                        className="flex items-center gap-3 rounded-xl border border-stone-100 bg-white px-4 py-3 shadow-sm"
                    >
                        <span className="text-xl shrink-0">📄</span>
                        <div className="flex-1 min-w-0">
                            <p className="text-sm font-medium text-stone-700 truncate">{doc.file_name}</p>
                            <p className="text-xs text-stone-400 mt-0.5">
                                {doc.file_type.toUpperCase()} · {formatSize(doc.file_size)} · {doc.chunk_count} 块
                            </p>
                        </div>
                        <span className={`shrink-0 text-xs font-medium rounded-full px-2.5 py-1 ${meta.className}`}>
                            {meta.label}
                        </span>
                        <Button
                            variant="ghost"
                            size="sm"
                            onClick={() => onDelete(doc.id)}
                            className="text-red-400 hover:text-red-600 hover:bg-red-50 shrink-0"
                        >
                            删除
                        </Button>
                    </div>
                );
            })}
        </div>
    );
}
