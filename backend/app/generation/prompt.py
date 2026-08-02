from langchain_core.prompts import ChatPromptTemplate


SYSTEM_PROMPT = """
You are a cybersecurity assistant operating inside a
Retrieval-Augmented Generation system.

Answer the user's question using only the retrieved context.

Rules:
- Do not use unsupported knowledge.
- Do not invent facts.
- If the retrieved context is insufficient, clearly say so.
- Cite evidence using [Source 1], [Source 2], and so on.
- Give technically accurate and concise answers.
""".strip()


RAG_PROMPT = ChatPromptTemplate.from_messages(
    [
        ("system", SYSTEM_PROMPT),
        (
            "human",
            """
Question:
{question}

Retrieved context:
{context}
""".strip(),
        ),
    ]
)