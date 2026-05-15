# BAML Few-Shot Bundle

This file is the grounding context handed to the translator LLM. It is
seeded automatically on first run from `baml-cli init` so the syntax is
locked to the installed CLI version.

## Key syntactic rules

* `class Foo { field type }` — define a data shape. Types are bare names:
  `string`, `int`, `float`, `bool`, `string[]`, `Foo?` (optional), `Foo | Bar`
  (union), enums via `enum Color { RED GREEN BLUE }`.
* `function FuncName(arg: Type) -> ReturnType` — defines a typed LLM call.
* Inside `function`: `client "<provider>/<model>"` or a reference to a
  named client from clients.baml. The `prompt #" ... "#` block contains
  the actual prompt with `{{ arg }}` jinja-style interpolation and
  `{{ ctx.output_format }}` which BAML expands to the schema hint.
* `test name { functions [F1, F2] args { ... } }` — inline test blocks.

## Example 1: canonical extraction (resume parsing)

```baml
// Defining a data model.
class Resume {
  name string
  email string
  experience string[]
  skills string[]
}

// Create a function to extract the resume from a string.
function ExtractResume(resume: string) -> Resume {
  // Specify a client as provider/model-name
  // You can also use custom LLM params with a custom client name from clients.baml like "client CustomGPT5" or "client CustomSonnet4"
  client "openai-responses/gpt-5-mini" // Set OPENAI_API_KEY to use this client.
  prompt #"
    Extract from this content:
    {{ resume }}

    {{ ctx.output_format }}
  "#
}



// Test the function with a sample resume. Open the VSCode playground to run this.
test vaibhav_resume {
  functions [ExtractResume]
  args {
    resume #"
      Vaibhav Gupta
      vbv@boundaryml.com

      Experience:
      - Founder at BoundaryML
      - CV Engineer at Google
      - CV Engineer at Microsoft

      Skills:
      - Rust
      - C++
    "#
  }
}
```

## Example 2: client + retry policy definitions (clients.baml)

```baml
// Learn more about clients at https://docs.boundaryml.com/docs/snippets/clients/overview

// Using the new OpenAI Responses API for enhanced formatting
client<llm> CustomGPT5 {
  provider openai-responses
  options {
    model "gpt-5"
    api_key env.OPENAI_API_KEY
  }
}

client<llm> CustomGPT5Mini {
  provider openai-responses
  retry_policy Exponential
  options {
    model "gpt-5-mini"
    api_key env.OPENAI_API_KEY
  }
}

// Openai with chat completion
client<llm> CustomGPT5Chat {
  provider openai
  options {
    model "gpt-5"
    api_key env.OPENAI_API_KEY
  }
}

// Latest Anthropic Claude 4 models
client<llm> CustomOpus4 {
  provider anthropic
  options {
    model "claude-opus-4-1-20250805"
    api_key env.ANTHROPIC_API_KEY
  }
}

client<llm> CustomSonnet4 {
  provider anthropic
  options {
    model "claude-sonnet-4-20250514"
    api_key env.ANTHROPIC_API_KEY
  }
}

client<llm> CustomHaiku {
  provider anthropic
  retry_policy Constant
  options {
    model "claude-3-5-haiku-20241022"
    api_key env.ANTHROPIC_API_KEY
  }
}

// Example Google AI client (uncomment to use)
// client<llm> CustomGemini {
//   provider google-ai
//   options {
//     model "gemini-2.5-pro"
//     api_key env.GOOGLE_API_KEY
//   }
// }

// Example AWS Bedrock client (uncomment to use)
// client<llm> CustomBedrock {
//   provider aws-bedrock
//   options {
//     model "anthropic.claude-sonnet-4-20250514-v1:0"
//     region "us-east-1"
//     // AWS credentials are auto-detected from env vars
//   }
// }

// Example Azure OpenAI client (uncomment to use)
// client<llm> CustomAzure {
//   provider azure-openai
//   options {
//     model "gpt-5"
//     api_key env.AZURE_OPENAI_API_KEY
//     base_url "https://MY_RESOURCE_NAME.openai.azure.com/openai/deployments/MY_DEPLOYMENT_ID"
//     api_version "2024-10-01-preview"
//   }
// }

// Example Vertex AI client (uncomment to use)
// client<llm> CustomVertex {
//   provider vertex-ai
//   options {
//     model "gemini-2.5-pro"
//     location "us-central1"
//     // Uses Google Cloud Application Default Credentials
//   }
// }

// Example Ollama client for local models (uncomment to use)
// client<llm> CustomOllama {
//   provider openai-generic
//   options {
//     base_url "http://localhost:11434/v1"
//     model "llama4"
//     default_role "user" // Most local models prefer the user role
//     // No API key needed for local Ollama
//   }
// }

// https://docs.boundaryml.com/docs/snippets/clients/round-robin
client<llm> CustomFast {
  provider round-robin
  options {
    // This will alternate between the two clients
    strategy [CustomGPT5Mini, CustomHaiku]
  }
}

// https://docs.boundaryml.com/docs/snippets/clients/fallback
client<llm> OpenaiFallback {
  provider fallback
  options {
    // This will try the clients in order until one succeeds
    strategy [CustomGPT5Mini, CustomGPT5]
  }
}

// https://docs.boundaryml.com/docs/snippets/clients/retry
retry_policy Constant {
  max_retries 3
  strategy {
    type constant_delay
    delay_ms 200
  }
}

retry_policy Exponential {
  max_retries 2
  strategy {
    type exponential_backoff
    delay_ms 300
    multiplier 1.5
    max_delay_ms 10000
  }
}
```

## Example 3: codegen target config (generators.baml)

```baml
// This helps use auto generate libraries you can use in the language of
// your choice. You can have multiple generators if you use multiple languages.
// Just ensure that the output_dir is different for each generator.
generator target {
    // Valid values: "python/pydantic", "typescript", "go", "rust", "ruby/sorbet", "rest/openapi"
    output_type "typescript"

    // Where the generated code will be saved (relative to baml_src/)
    output_dir "../"

    // The version of the BAML package you have installed (e.g. same version as your baml-py or @boundaryml/baml).
    // The BAML VSCode extension version should also match this version.
    version "0.222.0"

    // Valid values: "sync", "async"
    // This controls what `b.FunctionName()` will be (sync or async).
    default_client_mode async
}
```

## Additional patterns the translator should know

### Enum classification

```baml
enum Sentiment {
  POSITIVE
  NEGATIVE
  NEUTRAL
}

function ClassifySentiment(text: string) -> Sentiment {
  client "openai/gpt-4o-mini"
  prompt #"
    Classify the sentiment of this text as POSITIVE, NEGATIVE, or NEUTRAL.

    Text: {{ text }}

    {{ ctx.output_format }}
  "#
}
```

### Tool / function calling (Anthropic-style)

```baml
class WeatherQuery {
  location string
  unit "celsius" | "fahrenheit"
}

function ChooseWeatherTool(user_message: string) -> WeatherQuery {
  client "anthropic/claude-3-5-sonnet-20241022"
  prompt #"
    The user has asked a weather question. Extract the location and the
    requested temperature unit.

    User: {{ user_message }}

    {{ ctx.output_format }}
  "#
}
```

### Optional fields and nested classes

```baml
class Address {
  street string
  city string
  state string?
  country string
}

class Person {
  name string
  email string?
  age int?
  addresses Address[]
}

function ExtractPerson(text: string) -> Person {
  client "openai/gpt-4o-mini"
  prompt #"
    Extract the person from the text.
    {{ ctx.output_format }}

    Text: {{ text }}
  "#
}
```
