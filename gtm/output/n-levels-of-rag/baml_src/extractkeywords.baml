function ExtractKeywords(query: string) -> string[] {
  client "openai/gpt-4"
  prompt #"
    You are a world class search engine. You are about to be given a question by a user. Make sure to generate as many possible keywords that are relevant to the question at hand which can help to identify relevant chunks of information to the user's query.
    Make sure to extract all possible keywords within the question itself first before generating new ones. Also expand all accronyms, identify synonyms and related topics.

    The question is {{ query }}.

    {{ ctx.output_format }}
  "#
}

test example_query {
  functions [ExtractKeywords]
  args {
    query "What is the capital of France?"
  }
}