class WeatherQuery {
  location string
  unit "celsius" | "fahrenheit"
}

function GetWeatherToolCall(user_message: string) -> WeatherQuery {
  client "openai/gpt-4o"
  prompt #"
    The user has asked a weather question. Extract the location and the
    requested temperature unit.

    User: {{ user_message }}

    {{ ctx.output_format }}
  "#
}

test weather_paris {
  functions [GetWeatherToolCall]
  args {
    user_message "What's the weather like in Paris today?"
  }
}