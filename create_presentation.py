"""
Generate Week 3 Progress Briefing PowerPoint
Modern, professional design with gradients and clean styling
"""

from pptx import Presentation
from pptx.util import Inches, Pt
from pptx.dml.color import RGBColor
from pptx.enum.text import PP_ALIGN, MSO_ANCHOR
from pptx.enum.shapes import MSO_SHAPE
from pptx.oxml.ns import nsmap
from pptx.oxml import parse_xml

# Color scheme - Modern blue/teal gradient theme
PRIMARY_COLOR = RGBColor(0, 102, 153)      # Deep teal
SECONDARY_COLOR = RGBColor(0, 150, 199)    # Bright teal
ACCENT_COLOR = RGBColor(255, 107, 53)      # Orange accent
DARK_TEXT = RGBColor(51, 51, 51)           # Near black
LIGHT_TEXT = RGBColor(255, 255, 255)       # White
LIGHT_BG = RGBColor(245, 247, 250)         # Light gray-blue

def set_shape_fill(shape, color):
    """Set solid fill color for a shape."""
    shape.fill.solid()
    shape.fill.fore_color.rgb = color

def add_title_slide(prs, title, subtitle):
    """Add a title slide with modern design."""
    slide_layout = prs.slide_layouts[6]  # Blank layout
    slide = prs.slides.add_slide(slide_layout)
    
    # Background shape (gradient effect via two overlapping shapes)
    bg1 = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, 0, 0, prs.slide_width, prs.slide_height)
    set_shape_fill(bg1, PRIMARY_COLOR)
    bg1.line.fill.background()
    
    # Accent bar at bottom
    accent_bar = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, 0, Inches(6.5), prs.slide_width, Inches(1))
    set_shape_fill(accent_bar, SECONDARY_COLOR)
    accent_bar.line.fill.background()
    
    # Title
    title_box = slide.shapes.add_textbox(Inches(0.5), Inches(2), Inches(12.5), Inches(1.5))
    tf = title_box.text_frame
    tf.word_wrap = True
    p = tf.paragraphs[0]
    p.text = title
    p.font.size = Pt(44)
    p.font.bold = True
    p.font.color.rgb = LIGHT_TEXT
    p.alignment = PP_ALIGN.CENTER
    
    # Subtitle
    sub_box = slide.shapes.add_textbox(Inches(0.5), Inches(3.5), Inches(12.5), Inches(1))
    tf = sub_box.text_frame
    p = tf.paragraphs[0]
    p.text = subtitle
    p.font.size = Pt(24)
    p.font.color.rgb = LIGHT_TEXT
    p.alignment = PP_ALIGN.CENTER
    
    return slide

def add_section_slide(prs, title):
    """Add a section divider slide."""
    slide_layout = prs.slide_layouts[6]
    slide = prs.slides.add_slide(slide_layout)
    
    # Background
    bg = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, 0, 0, prs.slide_width, prs.slide_height)
    set_shape_fill(bg, SECONDARY_COLOR)
    bg.line.fill.background()
    
    # Title
    title_box = slide.shapes.add_textbox(Inches(0.5), Inches(2.5), Inches(12.5), Inches(2))
    tf = title_box.text_frame
    p = tf.paragraphs[0]
    p.text = title
    p.font.size = Pt(48)
    p.font.bold = True
    p.font.color.rgb = LIGHT_TEXT
    p.alignment = PP_ALIGN.CENTER
    
    return slide

def add_content_slide(prs, title, bullets, has_icon=False):
    """Add a content slide with bullet points."""
    slide_layout = prs.slide_layouts[6]
    slide = prs.slides.add_slide(slide_layout)
    
    # Header bar
    header = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, 0, 0, prs.slide_width, Inches(1.3))
    set_shape_fill(header, PRIMARY_COLOR)
    header.line.fill.background()
    
    # Title in header
    title_box = slide.shapes.add_textbox(Inches(0.5), Inches(0.35), Inches(12), Inches(0.8))
    tf = title_box.text_frame
    p = tf.paragraphs[0]
    p.text = title
    p.font.size = Pt(32)
    p.font.bold = True
    p.font.color.rgb = LIGHT_TEXT
    
    # Content area
    content_box = slide.shapes.add_textbox(Inches(0.7), Inches(1.7), Inches(12), Inches(5))
    tf = content_box.text_frame
    tf.word_wrap = True
    
    for i, bullet in enumerate(bullets):
        if i == 0:
            p = tf.paragraphs[0]
        else:
            p = tf.add_paragraph()
        
        p.text = bullet
        p.font.size = Pt(22)
        p.font.color.rgb = DARK_TEXT
        p.space_before = Pt(12)
        p.space_after = Pt(6)
        p.level = 0
    
    # Accent line at bottom
    line = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, 0, Inches(7.2), prs.slide_width, Inches(0.15))
    set_shape_fill(line, ACCENT_COLOR)
    line.line.fill.background()
    
    return slide

def add_two_column_slide(prs, title, left_title, left_items, right_title, right_items):
    """Add a two-column content slide."""
    slide_layout = prs.slide_layouts[6]
    slide = prs.slides.add_slide(slide_layout)
    
    # Header bar
    header = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, 0, 0, prs.slide_width, Inches(1.3))
    set_shape_fill(header, PRIMARY_COLOR)
    header.line.fill.background()
    
    # Title
    title_box = slide.shapes.add_textbox(Inches(0.5), Inches(0.35), Inches(12), Inches(0.8))
    tf = title_box.text_frame
    p = tf.paragraphs[0]
    p.text = title
    p.font.size = Pt(32)
    p.font.bold = True
    p.font.color.rgb = LIGHT_TEXT
    
    # Left column header
    left_header = slide.shapes.add_textbox(Inches(0.5), Inches(1.5), Inches(5.5), Inches(0.5))
    tf = left_header.text_frame
    p = tf.paragraphs[0]
    p.text = left_title
    p.font.size = Pt(22)
    p.font.bold = True
    p.font.color.rgb = PRIMARY_COLOR
    
    # Left content
    left_box = slide.shapes.add_textbox(Inches(0.5), Inches(2.1), Inches(5.5), Inches(4.5))
    tf = left_box.text_frame
    tf.word_wrap = True
    for i, item in enumerate(left_items):
        if i == 0:
            p = tf.paragraphs[0]
        else:
            p = tf.add_paragraph()
        p.text = "• " + item
        p.font.size = Pt(18)
        p.font.color.rgb = DARK_TEXT
        p.space_before = Pt(8)
    
    # Right column header
    right_header = slide.shapes.add_textbox(Inches(6.5), Inches(1.5), Inches(5.5), Inches(0.5))
    tf = right_header.text_frame
    p = tf.paragraphs[0]
    p.text = right_title
    p.font.size = Pt(22)
    p.font.bold = True
    p.font.color.rgb = PRIMARY_COLOR
    
    # Right content
    right_box = slide.shapes.add_textbox(Inches(6.5), Inches(2.1), Inches(5.5), Inches(4.5))
    tf = right_box.text_frame
    tf.word_wrap = True
    for i, item in enumerate(right_items):
        if i == 0:
            p = tf.paragraphs[0]
        else:
            p = tf.add_paragraph()
        p.text = "• " + item
        p.font.size = Pt(18)
        p.font.color.rgb = DARK_TEXT
        p.space_before = Pt(8)
    
    # Accent line
    line = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, 0, Inches(7.2), prs.slide_width, Inches(0.15))
    set_shape_fill(line, ACCENT_COLOR)
    line.line.fill.background()
    
    return slide

def add_table_slide(prs, title, headers, rows):
    """Add a slide with a styled table."""
    slide_layout = prs.slide_layouts[6]
    slide = prs.slides.add_slide(slide_layout)
    
    # Header bar
    header = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, 0, 0, prs.slide_width, Inches(1.3))
    set_shape_fill(header, PRIMARY_COLOR)
    header.line.fill.background()
    
    # Title
    title_box = slide.shapes.add_textbox(Inches(0.5), Inches(0.35), Inches(12), Inches(0.8))
    tf = title_box.text_frame
    p = tf.paragraphs[0]
    p.text = title
    p.font.size = Pt(32)
    p.font.bold = True
    p.font.color.rgb = LIGHT_TEXT
    
    # Table
    num_rows = len(rows) + 1
    num_cols = len(headers)
    table_width = Inches(11.5)
    table_height = Inches(min(5, num_rows * 0.6))
    
    table = slide.shapes.add_table(num_rows, num_cols, Inches(0.9), Inches(1.7), table_width, table_height).table
    
    # Style header row
    for j, h in enumerate(headers):
        cell = table.cell(0, j)
        cell.text = h
        cell.fill.solid()
        cell.fill.fore_color.rgb = SECONDARY_COLOR
        p = cell.text_frame.paragraphs[0]
        p.font.bold = True
        p.font.size = Pt(16)
        p.font.color.rgb = LIGHT_TEXT
        p.alignment = PP_ALIGN.CENTER
    
    # Data rows
    for i, row in enumerate(rows):
        for j, val in enumerate(row):
            cell = table.cell(i + 1, j)
            cell.text = val
            p = cell.text_frame.paragraphs[0]
            p.font.size = Pt(14)
            p.font.color.rgb = DARK_TEXT
            # Alternating row colors
            if i % 2 == 0:
                cell.fill.solid()
                cell.fill.fore_color.rgb = LIGHT_BG
            else:
                cell.fill.solid()
                cell.fill.fore_color.rgb = RGBColor(255, 255, 255)
    
    # Accent line
    line = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, 0, Inches(7.2), prs.slide_width, Inches(0.15))
    set_shape_fill(line, ACCENT_COLOR)
    line.line.fill.background()
    
    return slide

def add_architecture_slide(prs):
    """Add the system architecture diagram slide."""
    slide_layout = prs.slide_layouts[6]
    slide = prs.slides.add_slide(slide_layout)
    
    # Header
    header = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, 0, 0, prs.slide_width, Inches(1.3))
    set_shape_fill(header, PRIMARY_COLOR)
    header.line.fill.background()
    
    title_box = slide.shapes.add_textbox(Inches(0.5), Inches(0.35), Inches(12), Inches(0.8))
    tf = title_box.text_frame
    p = tf.paragraphs[0]
    p.text = "Proposed System Architecture"
    p.font.size = Pt(32)
    p.font.bold = True
    p.font.color.rgb = LIGHT_TEXT
    
    # Architecture boxes
    boxes = [
        ("User Input", Inches(5.2), Inches(1.6), SECONDARY_COLOR),
        ("State Inference\n(Emotion + Defensiveness)", Inches(5.2), Inches(2.5), PRIMARY_COLOR),
        ("Knowledge Retrieval\n(RAG)", Inches(5.2), Inches(3.6), PRIMARY_COLOR),
        ("Response Generation\n(MI-Based)", Inches(5.2), Inches(4.7), PRIMARY_COLOR),
        ("Safety Check", Inches(5.2), Inches(5.8), ACCENT_COLOR),
        ("Bot Response", Inches(5.2), Inches(6.7), SECONDARY_COLOR),
    ]
    
    box_width = Inches(3.2)
    box_height = Inches(0.8)
    
    for text, left, top, color in boxes:
        # Box
        box = slide.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, left, top, box_width, box_height)
        set_shape_fill(box, color)
        box.line.fill.background()
        
        # Text in box
        tf = box.text_frame
        tf.word_wrap = True
        p = tf.paragraphs[0]
        p.text = text
        p.font.size = Pt(14)
        p.font.bold = True
        p.font.color.rgb = LIGHT_TEXT
        p.alignment = PP_ALIGN.CENTER
        tf.anchor = MSO_ANCHOR.MIDDLE
    
    # Arrows (simple lines)
    arrow_positions = [
        (Inches(6.8), Inches(2.4), Inches(6.8), Inches(2.5)),
        (Inches(6.8), Inches(3.3), Inches(6.8), Inches(3.6)),
        (Inches(6.8), Inches(4.4), Inches(6.8), Inches(4.7)),
        (Inches(6.8), Inches(5.5), Inches(6.8), Inches(5.8)),
        (Inches(6.8), Inches(6.6), Inches(6.8), Inches(6.7)),
    ]
    
    # Note
    note = slide.shapes.add_textbox(Inches(9), Inches(4), Inches(3.5), Inches(1.5))
    tf = note.text_frame
    tf.word_wrap = True
    p = tf.paragraphs[0]
    p.text = "Note: This is a proposed design.\nImplementation to follow."
    p.font.size = Pt(12)
    p.font.italic = True
    p.font.color.rgb = DARK_TEXT
    
    return slide

def create_presentation():
    """Create the complete Week 3 presentation."""
    prs = Presentation()
    prs.slide_width = Inches(13.333)
    prs.slide_height = Inches(7.5)
    
    # Slide 1: Title
    add_title_slide(
        prs,
        "Emotion-Aware Conversational Chatbot\nfor Alcohol Dialogues",
        "Week 3 Progress Briefing  •  [Your Name]  •  February 2026"
    )
    
    # Slide 2: Problem Statement
    add_content_slide(prs, "Problem Statement", [
        "🎯 High-risk alcohol consumption is a critical public health challenge",
        "🧠 Motivational Interviewing (MI) is effective but lacks scalability",
        "🤖 Current chatbots fail to detect emotional cues and defensiveness",
        "💡 Opportunity: Combine LLMs with emotional awareness for accessible intervention"
    ])
    
    # Slide 3: Project Goal
    add_content_slide(prs, "Project Goal", [
        "Develop an MVP chatbot that can:",
        "    ✓  Detect user emotional state in real-time",
        "    ✓  Identify defensiveness patterns (denial, rationalization)",
        "    ✓  Respond with empathy using MI principles",
        "    ✓  Provide harm-reduction support without medical advice",
        "",
        "Focus: Technical feasibility demonstration, not clinical deployment"
    ])
    
    # Slide 4: Progress Summary
    add_two_column_slide(
        prs, 
        "Progress Summary (Weeks 1-3)",
        "✅ Completed",
        [
            "Literature review on Motivational Interviewing",
            "Research on LLM-based conversational agents",
            "Technology exploration and comparison",
            "Development environment setup",
            "Initial project planning"
        ],
        "🔄 In Progress",
        [
            "Understanding RAG architecture",
            "Learning prompt engineering techniques",
            "Defining state classification categories",
            "Designing system architecture",
            "Selecting final technology stack"
        ]
    )
    
    # Slide 5: Literature Review - MI
    add_content_slide(prs, "Literature Review: Motivational Interviewing", [
        "What is MI?",
        "    • Collaborative, person-centered counseling approach",
        "    • Developed by Miller & Rollnick (1991)",
        "    • Proven effective for substance use behavior change",
        "",
        "Core Principles (OARS):",
        "    • Open Questions – Invite elaboration, not yes/no answers",
        "    • Affirmations – Recognize client strengths and efforts",
        "    • Reflections – Mirror back understanding to show empathy",
        "    • Summaries – Collect and present key points"
    ])
    
    # Slide 6: Defensiveness Patterns
    add_table_slide(
        prs,
        "Understanding Defensiveness in Alcohol Conversations",
        ["Pattern", "Example", "Chatbot Strategy"],
        [
            ["Denial", '"I don\'t have a problem"', "Simple reflection, validate perspective"],
            ["Minimization", '"I only drink a little"', "Explore without challenging"],
            ["Rationalization", '"Everyone does it"', "Double-sided reflection"],
            ["Projection", '"You don\'t understand"', "Emphasize autonomy, avoid arguing"],
        ]
    )
    
    # Slide 7: Learning GenAI
    add_content_slide(prs, "Learning Generative AI Concepts", [
        "Large Language Models (LLMs)",
        "    • Exploring: How LLMs generate contextual responses",
        "    • Models researched: GPT-4, Llama 3, Gemma",
        "    • Key learning: Prompt engineering shapes model behavior",
        "",
        "Retrieval-Augmented Generation (RAG)",
        "    • Combines LLM capabilities with external knowledge",
        "    • Allows grounding responses in expert MI guidelines",
        "    • Currently studying: Vector embeddings, semantic search"
    ])
    
    # Slide 8: Technology Stack
    add_table_slide(
        prs,
        "Technologies Being Explored",
        ["Tool", "Purpose", "Learning Status"],
        [
            ["LangChain", "LLM orchestration & chaining", "In progress"],
            ["Ollama", "Local LLM hosting", "Exploring"],
            ["ChromaDB", "Vector database for RAG", "Researching"],
            ["Streamlit", "Web UI framework", "Familiar"],
            ["Python", "Core development language", "Proficient"],
        ]
    )
    
    # Slide 9: Architecture
    add_architecture_slide(prs)
    
    # Slide 10: State Categories
    add_two_column_slide(
        prs,
        "Proposed State Classification Categories",
        "Emotional States",
        [
            "Neutral – Baseline state",
            "Frustrated – Feeling unheard",
            "Anxious – Worried about change",
            "Sad – Hopelessness, regret",
            "Angry – Hostility, blame",
            "Hopeful – Interest in change",
            "Contemplative – Weighing options"
        ],
        "Defensiveness Levels",
        [
            "None – Open and receptive",
            "Low – Slight resistance",
            "Moderate – Clear defensive markers",
            "High – Strong denial/rationalization",
            "",
            "Approach: LLM-based classification",
            "with structured JSON output"
        ]
    )
    
    # Slide 11: Challenges
    add_two_column_slide(
        prs,
        "Challenges & Learning Gaps",
        "Technical Challenges",
        [
            "Prompt engineering for accurate classification",
            "RAG implementation complexity",
            "Conversation context management",
            "Response quality evaluation",
            "Integration of multiple components"
        ],
        "Domain Challenges",
        [
            "Limited access to real MI dialogues",
            "Need expert input on knowledge base",
            "Balancing helpfulness with safety",
            "Defining evaluation criteria",
            "Scope management for MVP"
        ]
    )
    
    # Slide 12: Next Steps
    add_content_slide(prs, "Next Steps (Weeks 4-7)", [
        "Week 4:",
        "    • Complete LangChain tutorials and documentation",
        "    • Build basic LLM interaction prototype",
        "",
        "Week 5:",
        "    • Implement initial RAG pipeline",
        "    • Create starter knowledge base content",
        "",
        "Week 6:",
        "    • Integrate state inference with response generation",
        "    • Create simple testing UI",
        "",
        "Week 7 (Mid-Term):",
        "    • Working prototype demonstration",
        "    • Progress report with initial results"
    ])
    
    # Slide 13: Timeline
    add_table_slide(
        prs,
        "Project Timeline Overview",
        ["Week", "Focus Area", "Key Deliverable"],
        [
            ["1-3", "Research & Foundation", "Literature review, tech exploration"],
            ["4-5", "Core Development", "Basic LLM + RAG integration"],
            ["6-7", "Integration (Mid-Term)", "Working prototype demo"],
            ["8-9", "Safety & Logging", "Complete pipeline with guardrails"],
            ["10-11", "Evaluation", "Expert review, testing"],
            ["12-13", "Refinement", "Bug fixes, documentation"],
            ["14-15", "Final Delivery", "Presentation & report"],
        ]
    )
    
    # Slide 14: Questions for Advisor
    add_content_slide(prs, "Questions for Discussion", [
        "1. Knowledge Base Content",
        "    • Where can I find validated MI dialogue examples?",
        "    • Should I create synthetic training scenarios?",
        "",
        "2. Evaluation Approach",
        "    • How should I measure response quality without clinical trials?",
        "    • Is expert review of 5-10 conversations sufficient for MVP?",
        "",
        "3. Scope Confirmation",
        "    • Is the MVP scope (text-only, no memory) appropriate?",
        "    • Any concerns about the proposed architecture?"
    ])
    
    # Slide 15: Summary
    add_content_slide(prs, "Summary", [
        "✅ Problem is well-defined with clear MVP scope",
        "",
        "✅ Literature review provides solid foundation for MI approach",
        "",
        "✅ Actively learning GenAI tools and techniques",
        "",
        "✅ System architecture designed, ready for implementation",
        "",
        "📋 Next: Begin prototyping in Week 4",
        "",
        "🙏 Seeking: Feedback on approach and access to MI resources"
    ])
    
    # Slide 16: References
    add_content_slide(prs, "References", [
        "1. Miller, W. R., & Rollnick, S. (2012). Motivational Interviewing:",
        "    Helping People Change. Guilford Press.",
        "",
        "2. Prochaska, J. O., & DiClemente, C. C. (1983). Stages and processes",
        "    of self-change. Journal of Consulting and Clinical Psychology.",
        "",
        "3. Lewis, P., et al. (2020). Retrieval-Augmented Generation for",
        "    Knowledge-Intensive NLP Tasks. NeurIPS.",
        "",
        "4. LangChain Documentation - python.langchain.com",
        "",
        "5. Ollama Documentation - ollama.com"
    ])
    
    # Final slide
    add_title_slide(
        prs,
        "Thank You",
        "Questions?"
    )
    
    # Save
    output_path = "docs/Week3_Progress_Briefing.pptx"
    prs.save(output_path)
    print(f"Presentation saved to: {output_path}")
    return output_path

if __name__ == "__main__":
    create_presentation()
