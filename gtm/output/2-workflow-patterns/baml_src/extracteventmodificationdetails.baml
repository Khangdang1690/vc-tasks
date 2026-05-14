class Change {
  field string
  new_value string
}

class ModifyEventDetails {
  event_identifier string
  changes Change[]
  participants_to_add string[]
  participants_to_remove string[]
}

function ExtractEventModificationDetails(description: string) -> ModifyEventDetails {
  client "openai/gpt-4o-mini"
  prompt #"
    Extract details for modifying an existing calendar event.

    User: {{ description }}

    {{ ctx.output_format }}
  "#
}