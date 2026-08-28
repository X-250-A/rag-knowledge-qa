"use client";

import { useRef, useState } from "react";

interface Props {
    onFileSelect: (files: File[]) => void;
    accept?: string;
    uploading?: boolean;
}

const ACCEPT = ".pdf,.md,.docx";

export default function FileUpload({ onFileSelect, accept = ACCEPT, uploading = false }: Props) {
    const inputRef = useRef<HTMLInputElement>(null);
    const [fileNames, setFileNames] = useState<string[]>([]);
    const [dragOver, setDragOver] = useState(false);

    const handleFiles = (files: FileList | File[] | null) => {
        const list = files ? Array.from(files) : [];
        if (list.length === 0) return;
        setFileNames(list.map((f) => f.name));
        // 清空 input.value，允许重复选择同一文件
        if (inputRef.current) inputRef.current.value = "";
        onFileSelect(list);
    };

    return (
        <div
            onClick={() => inputRef.current?.click()}
            onDragOver={(e) => {
                e.preventDefault();
                setDragOver(true);
            }}
            onDragLeave={() => setDragOver(false)}
            onDrop={(e) => {
                e.preventDefault();
                setDragOver(false);
                handleFiles(e.dataTransfer.files);
            }}
            className={`cursor-pointer rounded-2xl border-2 border-dashed px-6 py-10 text-center transition-all duration-200
                ${dragOver
                    ? "border-orange-400 bg-orange-50"
                    : "border-stone-200 bg-stone-50/50 hover:border-orange-300 hover:bg-orange-50/40"}`}
        >
            <input
                ref={inputRef}
                type="file"
                accept={accept}
                multiple
                className="hidden"
                onChange={(e) => handleFiles(e.target.files)}
            />
            <div className="text-4xl mb-3">📄</div>
            <p className="text-sm font-medium text-stone-600">
                {fileNames.length
                    ? `已选 ${fileNames.length} 个文件`
                    : "点击选择或拖拽文档到此处（可多选）"}
            </p>
            {fileNames.length > 0 && (
                <p className="text-xs text-stone-400 mt-1.5 truncate px-4">
                    {fileNames.join("、")}
                </p>
            )}
            <p className="text-xs text-stone-400 mt-1.5">支持 .pdf / .docx / .md</p>
            {uploading && (
                <p className="text-xs text-orange-500 mt-3 animate-pulse">
                    上传解析中，请稍候...
                </p>
            )}
        </div>
    );
}
