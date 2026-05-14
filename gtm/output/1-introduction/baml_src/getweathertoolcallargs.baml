class WeatherToolQuery {
  location string
  unit "celsius" | "fahrenheit"
}

function GetWeatherToolCallArgs(user_message: string) -> WeatherToolQuery {
  client "openai/gpt-4o"
  prompt #"
    The user has asked a weather question. Extract the location and the
    requested temperature unit.

    User: {{ user_message }}

    {{ ctx.output_format }}
  "#
}

test tokyo_weather {
  functions [GetWeatherToolCallArgs]
  args {
    user_message "What is the weather in Tokyo?"
  }
}