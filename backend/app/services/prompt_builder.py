from pathlib import Path


class PromptBuilder:
    def __init__(self):
        rag_system_prompt_path = Path(__file__).parent / "prompts" / "rag_system_prompt.txt"
        llm_intents_classifier_path = (
            Path(__file__).parent / "prompts" / "llm_intents_classifier_prompt.txt"
        )
        self.rag_system_prompt = rag_system_prompt_path.read_text("utf-8")
        self.llm_intents_classifier_prompt = llm_intents_classifier_path.read_text("utf-8")

    def build_prompt(self, question: str, content_chunks: list[dict]) -> list[dict] | None:
        if not content_chunks:
            return None
        system_prompt = [{"role": "system", "content": self.rag_system_prompt}]
        references = ""
        for i, chunk in enumerate(content_chunks, start=1):
            references += f"[{i}]文档，{chunk['document_id']}，第{chunk['seq_no']}段\n"
            references += f"{chunk['content']}\n\n"
        return [
            *system_prompt,
            {"role": "user", "content": f"参考资料：\n{references}\n用户问题：\n{question}"},
        ]
