class CalendarValidation {
  is_calendar_request bool
  confidence_score float
}

function ValidateCalendarRequest(user_input: string) -> CalendarValidation {
  client "openai/gpt-4o-mini"
  prompt #"
    Determine if this is a calendar event request.

    User: {{ user_input }}

    {{ ctx.output_format }}
  "#
}

test schedule_meeting {
  functions [ValidateCalendarRequest]
  args {
    user_input "Schedule a meeting for tomorrow at 3 PM."
  }
}