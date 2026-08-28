"use client";

import FileUpload from "@/components/ui/FileUpload";

interface Props {
    onUpload: (files: File[]) => void;
    uploading: boolean;
    error?: string;
}

export default function UploadZone({ onUpload, uploading, error }: Props) {
    return (
        <div className="space-y-2">
            <FileUpload onFileSelect={onUpload} uploading={uploading} />
            {error && (
                <p className="text-xs text-red-500 px-1">⚠️ {error}</p>
            )}
        </div>
    );
}
