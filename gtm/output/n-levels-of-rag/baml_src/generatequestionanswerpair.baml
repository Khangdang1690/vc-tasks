class QuestionAnswerPair {
  question string
  answer string
  chain_of_thought string
}

function GenerateQuestionAnswerPair(chunk: string) -> QuestionAnswerPair {
  client "openai/gpt-3.5-turbo"
  prompt #"
    You are a world class algorithm that excels at generating great questions that can be only answered by a specific text that will soon be passed to you.

    Generate a question and answer pair that uses information and content that is specific to the following text chunk, including a chain of thought:

    Text Chunk:
    {{ chunk }}

    {{ ctx.output_format }}
  "#
}

test sample_qa_pair {
  functions [GenerateQuestionAnswerPair]
  args {
    chunk #"
      The quick brown fox jumps over the lazy dog. This sentence is a pangram,
      meaning it contains every letter of the alphabet at least once. Pangrams
      are often used for testing typefaces and keyboard layouts.
    "#
  }
}