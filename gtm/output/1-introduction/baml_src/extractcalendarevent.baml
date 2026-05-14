class CalendarEvent {
  name string
  date string
  participants string[]
}

function ExtractCalendarEvent(user_message: string) -> CalendarEvent {
  client "openai/gpt-4o"
  prompt #"
    Extract the event information.

    User: {{ user_message }}

    {{ ctx.output_format }}
  "#
}

test science_fair {
  functions [ExtractCalendarEvent]
  args {
    user_message "Alice and Bob are going to a science fair on Friday."
  }
}