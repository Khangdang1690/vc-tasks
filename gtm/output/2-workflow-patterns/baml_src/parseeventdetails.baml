class EventDetails {
  name string @description("Name of the event")
  date string @description("Date and time of the event. Use ISO 8601 to format this value.")
  duration_minutes int @description("Expected duration in minutes")
  participants string[] @description("List of participants")
}

function ParseEventDetails(dateContext: string, description: string) -> EventDetails {
  client "openai/gpt-4o-mini"
  prompt #"
    {{ dateContext }} Extract detailed event information. When dates reference 'next Tuesday' or similar relative dates, use this current date as reference.

    User: {{ description }}

    {{ ctx.output_format }}
  "#
}