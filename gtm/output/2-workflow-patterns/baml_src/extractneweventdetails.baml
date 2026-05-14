class NewEventDetails {
  name string
  date string
  duration_minutes int
  participants string[]
}

function ExtractNewEventDetails(description: string) -> NewEventDetails {
  client "openai/gpt-4o-mini"
  prompt #"
    Extract details for creating a new calendar event.

    User: {{ description }}

    {{ ctx.output_format }}
  "#
}

test new_event_test {
  functions [ExtractNewEventDetails]
  args {
    description "Schedule a team meeting about project X on October 26th at 3 PM for 60 minutes with Alice, Bob, and Charlie."
  }
}