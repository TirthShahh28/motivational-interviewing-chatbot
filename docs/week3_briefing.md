# Week 3 Progress Briefing

## Emotion-Aware Conversational Chatbot for Alcohol Dialogues

**Student:** [Your Name]
**Date:** [Date]
**Advisor:** [Advisor Name]

---

## Slide 1: Project Overview

### Problem Statement

- High-risk alcohol consumption is a critical public health challenge
- Motivational Interviewing (MI) is effective but not scalable
- Current chatbots lack emotional awareness and sensitivity

### Project Goal

Develop a chatbot that can:

- Detect user emotional state and defensiveness
- Respond with empathy using MI principles
- Provide harm-reduction support without medical advice

---

## Slide 2: Progress Summary (Weeks 1-3)

### Completed Tasks

✅ Literature review on Motivational Interviewing  
✅ Research on LLM-based conversational agents  
✅ Technology exploration (LangChain, Ollama, Vector DBs)  
✅ Environment setup and tool familiarization

### In Progress

🔄 Understanding RAG (Retrieval-Augmented Generation) architecture  
🔄 Learning prompt engineering techniques  
🔄 Defining state classification categories

---

## Slide 3: Literature Review - Motivational Interviewing

### What is MI?

- Collaborative, person-centered counseling approach
- Developed by Miller & Rollnick (1991)
- Proven effective for substance use behavior change

### Core Principles (OARS)

| Technique          | Description                     |
| ------------------ | ------------------------------- |
| **Open Questions** | Invite elaboration, not yes/no  |
| **Affirmations**   | Recognize strengths and efforts |
| **Reflections**    | Mirror back understanding       |
| **Summaries**      | Collect and present key points  |

### Key Insight for Chatbot

- Must "roll with resistance" - never argue or confront
- Detect defensiveness and adjust response strategy

---

## Slide 4: Understanding Defensiveness in Alcohol Conversations

### Common Defensive Patterns (from literature)

| Pattern             | Example                  |
| ------------------- | ------------------------ |
| **Denial**          | "I don't have a problem" |
| **Minimization**    | "I only drink a little"  |
| **Rationalization** | "Everyone does it"       |
| **Projection**      | "You don't understand"   |

### Why This Matters

- Traditional chatbots ignore these cues
- Confronting defensiveness increases resistance
- Need to detect and adapt in real-time

---

## Slide 5: Learning Generative AI Concepts

### Large Language Models (LLMs)

- What I'm learning: How LLMs generate contextual responses
- Models explored: GPT-4, Llama 3, Gemma
- Key concept: Prompt engineering shapes behavior

### Retrieval-Augmented Generation (RAG)

- Combines LLM with external knowledge base
- Allows grounding responses in expert guidelines
- Still learning: Vector embeddings, semantic search

### Tools Being Explored

| Tool      | Purpose           | Status      |
| --------- | ----------------- | ----------- |
| LangChain | LLM orchestration | Learning    |
| Ollama    | Local LLM hosting | Exploring   |
| ChromaDB  | Vector storage    | Researching |
| Streamlit | UI framework      | Familiar    |

---

## Slide 6: Proposed System Architecture (Conceptual)

```
User Input
    │
    ▼
┌─────────────────┐
│ State Inference │ ──► Detect emotion + defensiveness
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ Knowledge       │ ──► Retrieve relevant MI guidelines
│ Retrieval (RAG) │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ Response        │ ──► Generate adaptive, empathetic response
│ Generation      │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ Safety Check    │ ──► Ensure no harmful content
└────────┬────────┘
         │
         ▼
    Bot Response
```

_Note: This is a proposed design - implementation to follow_

---

## Slide 7: State Classification Categories (Proposed)

### Emotional States to Detect

- Neutral
- Frustrated
- Anxious
- Sad
- Angry
- Hopeful
- Contemplative

### Defensiveness Levels

- None (open/receptive)
- Low (slight resistance)
- Moderate (clear defensive markers)
- High (strong denial/rationalization)

### Approach Being Researched

- LLM-based classification with structured output
- Prompt engineering for accurate detection
- Possible rule-based fallback patterns

---

## Slide 8: Challenges & Learning Gaps

### Technical Challenges

| Challenge                             | Current Understanding          |
| ------------------------------------- | ------------------------------ |
| Prompt engineering for classification | Basic - need more practice     |
| RAG implementation                    | Conceptual - haven't built yet |
| Conversation context management       | Researching approaches         |
| Response quality evaluation           | Need to define metrics         |

### Domain Challenges

- Limited access to real MI training dialogues
- Need expert input on knowledge base content
- Balancing helpfulness with safety boundaries

---

## Slide 9: Next Steps (Weeks 4-6)

### Week 4

- [ ] Complete LangChain tutorial
- [ ] Build basic LLM interaction prototype
- [ ] Define state inference prompt

### Week 5

- [ ] Implement basic RAG pipeline
- [ ] Create initial knowledge base content
- [ ] Test retrieval quality

### Week 6

- [ ] Integrate components
- [ ] Create simple UI for testing
- [ ] Prepare mid-term demo

---

## Slide 10: Questions for Advisor

1. **Knowledge Base Content:**
   - Where can I find validated MI dialogue examples?
   - Should I create synthetic training scenarios?

2. **Evaluation Approach:**
   - How should I measure response quality without clinical trials?
   - Is expert review of 5-10 conversations sufficient for MVP?

3. **Scope Clarification:**
   - Should voice/speech be considered for future work section only?
   - Is the MVP scope (text-only, no long-term memory) appropriate?

---

## Slide 11: Timeline to Mid-Term

| Week | Focus               | Deliverable                 |
| ---- | ------------------- | --------------------------- |
| 3    | Research & Learning | This briefing               |
| 4    | LLM Prototyping     | Basic LLM integration       |
| 5    | RAG Development     | Knowledge retrieval working |
| 6    | Integration         | Connected pipeline          |
| 7    | **Mid-Term**        | Working prototype demo      |

### Risk Mitigation

- If RAG proves too complex: Use prompt-only approach
- If local LLM insufficient: Consider API-based model
- Focus on core features, defer enhancements

---

## Summary

### Key Takeaways

- Problem is well-defined with clear scope
- Literature review provides foundation for MI approach
- Learning GenAI tools and techniques
- Architecture designed, implementation starting next week

### Support Needed

- Guidance on evaluation methodology
- Access to MI resources or expert consultation
- Feedback on proposed architecture

---

## References (Sample)

1. Miller, W. R., & Rollnick, S. (2012). _Motivational interviewing: Helping people change_. Guilford Press.

2. Prochaska, J. O., & DiClemente, C. C. (1983). Stages and processes of self-change of smoking. _Journal of Consulting and Clinical Psychology_.

3. Lewis, P., et al. (2020). Retrieval-Augmented Generation for Knowledge-Intensive NLP Tasks. _NeurIPS_.

4. LangChain Documentation. https://python.langchain.com/

5. Ollama Documentation. https://ollama.com/
