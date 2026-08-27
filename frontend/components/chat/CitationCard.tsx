"use client";

import type { Citation } from "@/types";

interface Props {
    citation: Citation;
    index?: number;
}

export default function CitationCard({ citation, index }: Props) {
    const preview = citation.content.length > 80
        ? `${citation.content.slice(0, 80)}…`
        : citation.content;

    return (
        <div className="flex items-start gap-2 rounded-lg bg-stone-50/80 border border-stone-100 px-2.5 py-1.5">
            <span className="shrink-0 mt-0.5 inline-flex items-center justify-center min-w-4 h-4 px-1 rounded bg-orange-100 text-[0.6rem] text-orange-600 font-semibold">
                {index != null ? index + 1 : citation.seq_no}
            </span>
            <div className="min-w-0">
                <p className="text-[0.7rem] text-stone-500 truncate">
                    📄 {citation.document_name} · 第 {citation.seq_no} 段
                </p>
                <p className="text-[0.7rem] text-stone-400 leading-snug">{preview}</p>
            </div>
        </div>
    );
}
