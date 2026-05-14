class SubTask {
  title string
  description string
}

class OrchestratorPlan {
  topic_analysis string
  target_audience string
  sections SubTask[]
}

function GetOrchestratorPlan(topic: string, target_length: int, style: string) -> OrchestratorPlan {
  client "openai/gpt-4o-mini"
  prompt #"
    You are an expert blog post orchestrator. Your task is to create a detailed plan for a blog post.
    The blog post should be about: {{ topic }}
    It should aim for a target length of approximately {{ target_length }} words.
    The writing style should be: {{ style }}

    Provide a comprehensive plan including an analysis of the topic, the target audience, and a list of sections with their titles and descriptions.

    {{ ctx.output_format }}
  "#
}