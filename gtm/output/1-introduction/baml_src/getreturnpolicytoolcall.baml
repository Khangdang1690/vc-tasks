class GetReturnPolicyArgs {
  // No specific arguments are extracted for a general return policy query.
  // The presence of this object indicates the tool should be called.
}

function GetReturnPolicyToolCall(user_message: string) -> GetReturnPolicyArgs {
  client "openai/gpt-4o"
  prompt #"
    The user has asked a question. If it is about the return policy, extract the arguments for the `GetReturnPolicy` tool.

    User: {{ user_message }}

    {{ ctx.output_format }}
  "#
}

test return_policy_query {
  functions [GetReturnPolicyToolCall]
  args {
    user_message "What is the return policy?"
  }
}