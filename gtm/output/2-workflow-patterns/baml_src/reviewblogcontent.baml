class SuggestedEdits {
  section_name string
  edits string[]
}

class ReviewFeedback {
  cohesion_score float
  suggested_edits SuggestedEdits[]
  final_version string
}

function ReviewBlogContent(topic: string, audience: string, sections: string) -> ReviewFeedback {
  client "openai/gpt-4o-mini"
  prompt #"
    You are an expert blog post reviewer. Your task is to provide a comprehensive review and suggestions for a blog post based on its topic, target audience, and content sections.

    Topic: {{ topic }}
    Target Audience: {{ audience }}
    Sections:
    {{ sections }}

    Please provide a cohesion score (0-1), suggested edits for each section, and a final polished version of the blog post.
    {{ ctx.output_format }}
  "#
}