class KBResponse {
  answer string
  source int
}

function RetrieveKnowledgeBaseAnswer(question: string) -> KBResponse {
  client "openai/gpt-4o"
  prompt #"
    Answer the following question based on your knowledge.
    Provide the answer and the record ID of the source.

    Question: {{ question }}

    {{ ctx.output_format }}
  "#
}