class SectionContent {
  content string
  key_points string[]
}

function GenerateSectionContent(topic: string, section_type: string, description: string, style_guide: string, target_length: string, previous_sections: string) -> SectionContent {
  client "openai/gpt-4o-mini"
  prompt #"
    You are a helpful assistant writing a section for a document.

    Topic: {{ topic }}
    Section Type: {{ section_type }}
    Description: {{ description }}
    Style Guide: {{ style_guide }}
    Target Length: {{ target_length }}
    Previous Sections: {{ previous_sections }}

    Please write the content for this section and identify the main points covered.

    {{ ctx.output_format }}
  "#
}