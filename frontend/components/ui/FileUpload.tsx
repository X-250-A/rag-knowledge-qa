"use client";

import { useRef, useState } from "react";

interface Props {
    onFileSelect: (file: File) => void;
    accept?: string;
    uploading?: boolean;
}

const ACCEPT = ".pdf,.md,.docx";

export default function FileUpload({ onFileSelect, accept = ACCEPT, uploading = false }: Props) {
    const inputRef = useRef<HTMLInputElement>(null);
    const [fileName, setFileName] = useState("");
    const [dragOver, setDragOver] = useState(false);

    const handleFile = (file: File | undefined | null) => {
        if (!file) return;
        setFileName(file.name);
        onFileSelect(file);
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
                handleFile(e.dataTransfer.files?.[0]);
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
                className="hidden"
                onChange={(e) => handleFile(e.target.files?.[0])}
            />
            <div className="text-4xl mb-3">📄</div>
            <p className="text-sm font-medium text-stone-600">
                {fileName || "点击选择或拖拽文档到此处"}
            </p>
            <p className="text-xs text-stone-400 mt-1.5">支持 .pdf / .docx / .md</p>
            {uploading && (
                <p className="text-xs text-orange-500 mt-3 animate-pulse">上传解析中，请稍候...</p>
            )}
        </div>
    );
}
