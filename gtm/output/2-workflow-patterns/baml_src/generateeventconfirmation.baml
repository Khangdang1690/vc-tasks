class EventConfirmation {
  confirmation_message string
  calendar_link string?
}

function GenerateEventConfirmation(event_details_json: string) -> EventConfirmation {
  client "openai/gpt-4o-mini"
  prompt #"
    Generate a natural confirmation message for the event. Sign off with your name; Susie.

    Event Details:
    {{ event_details_json }}

    {{ ctx.output_format }}
  "#
}

test sample_event_confirmation {
  functions [GenerateEventConfirmation]
  args {
    event_details_json #"
      {
        \"title\": \"Project Kickoff\",
        \"date\": \"2024-11-15\",
        \"time\": \"14:00\",
        \"location\": \"Conference Room A\",
        \"attendees\": [\"John Doe\", \"Jane Smith\"]
      }
    "#
  }
}