class FullTextSearchEvaluationItem {
  question string
  keywords string[]
  chunk_id string?
}

function GenerateQueryKeywordsForSearch(item: FullTextSearchEvaluationItem) -> FullTextSearchEvaluationItem {
  client "openai/gpt-4o-mini"
  prompt #"
    Given the following question and an optional chunk ID, generate a list of keywords.
    If existing keywords are provided, you can refine or expand upon them.

    Question: {{ item.question }}
    Chunk ID: {{ item.chunk_id }}
    Existing Keywords: {{ item.keywords }}

    {{ ctx.output_format }}
  "#
}