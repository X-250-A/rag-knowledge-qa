from pathlib import Path

from backend.app.schemas.intent import Intent

# 意图类别 → 描述（prompt「### 意图类别」段的单一真源：
# Intent 枚举管值域、此表管说明文案，PromptBuilder 渲染进 prompt，禁止两处手写漂移)
_INTENT_CATEGORIES: dict[Intent, str] = {
    Intent.RAG_QUERY: "用户希望基于知识库中的文档内容进行问答，例如询问概念、原理、操作步骤、检索具体信息等",
    Intent.CHITCHAT: "用户进行闲聊或礼貌寒暄，如「你好」「谢谢」「你是谁」「再见」等，不涉及知识库内容",
    Intent.DOCUMENT_MANAGEMENT: "用户希望对文档进行管理操作，如上传、删除、列出、查看知识库文档等",
    Intent.OUT_OF_SCOPE: "以上类别都不匹配，或用户提出与知识库无关的其他请求",
}


class PromptBuilder:
    def __init__(self):
        rag_system_prompt_path = Path(__file__).parent / "prompts" / "rag_system_prompt.txt"
        llm_intents_classifier_path = (
            Path(__file__).parent / "prompts" / "llm_intents_classifier_prompt.txt"
        )
        self.rag_system_prompt = rag_system_prompt_path.read_text("utf-8")
        self.llm_intents_classifier_prompt = llm_intents_classifier_path.read_text("utf-8")

    def build_intents_classifier_prompt(self) -> str:
        """意图分类 prompt：{intent_categories} 占位符由 _INTENT_CATEGORIES 渲染，防 prompt 与代码漂移"""
        categories = "\n".join(
            f"- **`{i.value}`** —— {desc}" for i, desc in _INTENT_CATEGORIES.items()
        )
        return self.llm_intents_classifier_prompt.replace("{intent_categories}", categories)

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
