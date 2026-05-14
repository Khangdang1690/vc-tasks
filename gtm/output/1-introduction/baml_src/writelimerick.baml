function WriteLimerick(topic: string) -> string {
  client "openai/gpt-4o"
  prompt #"
    You're a helpful assistant.
    Write a limerick about the {{ topic }} programming language.

    {{ ctx.output_format }}
  "#
}

test python_limerick {
  functions [WriteLimerick]
  args {
    topic "Python"
  }
}