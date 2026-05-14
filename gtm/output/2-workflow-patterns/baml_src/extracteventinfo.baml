class EventExtraction {
  description string
  is_calendar_event bool
  confidence_score float
}

function ExtractEventInfo(date_context: string, user_input: string) -> EventExtraction {
  client "openai/gpt-4o-mini"
  prompt #"
    {{ date_context }} Analyze if the text describes a calendar event.

    Text: {{ user_input }}

    {{ ctx.output_format }}
  "#
}