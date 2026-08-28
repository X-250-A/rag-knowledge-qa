import { useCallback, useState } from "react";
import {
    listDocuments,
    uploadDocument,
    deleteDocument,
} from "@/lib/api";
import type { Document } from "@/types";

// 文档管理 hook：列表、上传、删除
export function useDocuments() {
    const [documents, setDocuments] = useState<Document[]>([]);
    const [loading, setLoading] = useState(false);
    const [uploading, setUploading] = useState(false);
    const [error, setError] = useState("");

    const load = useCallback(async () => {
        setLoading(true);
        setError("");
        try {
            const list = await listDocuments();
            setDocuments(list);
        } catch (err) {
            setError(err instanceof Error ? err.message : "加载文档失败");
        } finally {
            setLoading(false);
        }
    }, []);

    const upload = useCallback(async (files: File[]) => {
        if (!files.length) return;
        setUploading(true);
        setError("");
        try {
            for (const file of files) {
                await uploadDocument(file);
            }
            await load();
        } catch (err) {
            setError(err instanceof Error ? err.message : "上传失败");
        } finally {
            setUploading(false);
        }
    }, [load]);

    const remove = useCallback(async (documentId: number) => {
        setError("");
        try {
            await deleteDocument(documentId);
        } catch (err) {
            setError(err instanceof Error ? err.message : "删除失败");
        } finally {
            // 无论成功还是失败都刷新列表：
            // 若后端实际已删除但返回报错，重拉列表即可移除残留行，避免用户误判
            await load();
        }
    }, [load]);

    return { documents, loading, uploading, error, load, upload, remove };
}
