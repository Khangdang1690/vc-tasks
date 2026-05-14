class CalendarRequestType {
  request_type "new_event" | "modify_event" | "other"
  confidence_score float
  description string
}

function RouteCalendarRequest(user_input: string) -> CalendarRequestType {
  client "openai/gpt-4o-mini"
  prompt #"
    Determine if this is a request to create a new calendar event or modify an existing one.

    User: {{ user_input }}

    {{ ctx.output_format }}
  "#
}

test new_event_example {
  functions [RouteCalendarRequest]
  args {
    user_input "Please schedule a team sync for next Wednesday at 10 AM."
  }
}