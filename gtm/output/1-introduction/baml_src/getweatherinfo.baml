class WeatherResponse {
  temperature float @description("The current temperature in celsius for the given location.")
  response string @description("A natural language response to the user's question.")
}

function GetWeatherInfo(query: string) -> WeatherResponse {
  client "openai/gpt-4o"
  prompt #"
    Based on the following query, provide the current temperature in Celsius and a natural language response.

    Query: {{ query }}

    {{ ctx.output_format }}
  "#
}