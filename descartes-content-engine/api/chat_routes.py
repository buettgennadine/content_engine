"""
Claude Chat Sidebar API — context-aware assistant for Stuart and Nadine.
POST /api/chat  →  proxies to Claude Sonnet, API key stays server-side.
"""

import os
import logging
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional

router = APIRouter(tags=["chat"])
logger = logging.getLogger(__name__)

SIDEBAR_SYSTEM = """You are Stuart Corrigan's content assistant, embedded in Quinn — the content intelligence platform by Descartes Consulting.

Your role:
1. Help improve LinkedIn posts — make them sharper, more provocative, more data-driven
2. Explain and improve agent prompts when asked
3. Analyse intelligence signals and suggest content angles
4. Check content against Stuart's voice rules

Voice rules you enforce:
- Short declarative sentences (under 10 words for impact)
- Max 3 sentences per paragraph
- Never blame individuals — always frame as system design
- British English (organisation, analyse, colour, programme)
- Anti-language: NEVER use "transformation programme", "digital transformation",
  "roadmap", "journey", "synergy", "leverage", "stakeholder engagement",
  "change management", "best practice", "holistic", "game-changer"
- Lead with the conclusion, not the buildup
- Specific numbers beat vague claims

When suggesting improved text, format it ready to paste — no preamble, just the text.
When checking voice rules, be specific about which rule is violated and on which line.
Keep responses concise. Stuart is busy."""

TAB_CONTEXTS = {
    "dashboard": "Stuart is on the Dashboard — reviewing pending drafts and this week's intelligence signals.",
    "feed": "Stuart is on the Intelligence Feed — browsing scored articles.",
    "review": "Stuart is in the Review Queue — approving or rejecting drafts.",
    "calendar": "Stuart is on the Content Calendar — planning the posting schedule.",
    "generate": "Stuart is in the Post Generator — writing an on-demand LinkedIn post.",
    "visuals": "Stuart is in the Visuals tab — reviewing generated images for drafts.",
    "sources": "Stuart is on the Sources page — managing RSS feeds and pain point data.",
    "prompts": "Stuart is in the Prompt Editor — viewing or editing agent system prompts.",
    "system": "Stuart is on the System Status page — checking agent health and run logs.",
}

QUICK_ACTIONS = {
    "dashboard":  ["Summarise this week", "What should I review first?", "Suggest a post topic"],
    "feed":       ["Generate post from this", "Find contrarian angle", "What's the system design hook?"],
    "review":     ["Sharpen the hook", "Check voice rules", "Make it more provocative", "Shorten it"],
    "calendar":   ["Suggest topics for gaps", "Balance funnel stages", "Best days this week?"],
    "generate":   ["Sharpen the hook", "More provocative", "Add a data point", "Shorten", "Check voice rules"],
    "visuals":    ["Describe what this image conveys", "Suggest a better thumbnail concept"],
    "prompts":    ["Explain this prompt", "Suggest an improvement", "What variables does it use?"],
    "system":     ["What does the Monitor agent do?", "Explain the VPS scoring"],
}


class ChatMessage(BaseModel):
    role: str   # "user" | "assistant"
    content: str


class ChatRequest(BaseModel):
    message: str
    context: Optional[dict] = None          # tab, draft_id, draft_content, post_type, etc.
    history: Optional[list[ChatMessage]] = None


@router.get("/chat/quick-actions")
def get_quick_actions(tab: str = "dashboard"):
    return {"tab": tab, "actions": QUICK_ACTIONS.get(tab, [])}


@router.post("/chat")
async def chat(req: ChatRequest):
    """Send a message to Claude with context about what the user is viewing."""
    import anthropic
    api_key = os.getenv("ANTHROPIC_API_KEY")
    if not api_key:
        raise HTTPException(500, "ANTHROPIC_API_KEY not configured")

    ctx = req.context or {}
    tab = ctx.get("tab", "dashboard")
    tab_desc = TAB_CONTEXTS.get(tab, "")

    # Build context block
    context_lines = [tab_desc]
    if ctx.get("draft_content"):
        preview = ctx["draft_content"][:600]
        context_lines.append(f"\nCurrent draft content:\n{preview}")
    if ctx.get("article_title"):
        context_lines.append(f"\nCurrent article: {ctx['article_title']}")
        if ctx.get("article_snippet"):
            context_lines.append(f"Snippet: {ctx['article_snippet'][:300]}")
    if ctx.get("prompt_name") and ctx.get("prompt_content"):
        context_lines.append(f"\nCurrent prompt ({ctx['prompt_name']}):\n{ctx['prompt_content'][:800]}")
    if ctx.get("funnel_stage"):
        context_lines.append(f"Funnel stage: {ctx['funnel_stage']}")
    if ctx.get("post_type"):
        context_lines.append(f"Post type: {ctx['post_type']}")

    context_block = "\n".join(context_lines)
    system_prompt = f"{SIDEBAR_SYSTEM}\n\nCurrent context:\n{context_block}"

    # Build messages array
    messages = []
    for msg in (req.history or []):
        messages.append({"role": msg.role, "content": msg.content})
    messages.append({"role": "user", "content": req.message})

    try:
        client = anthropic.Anthropic(api_key=api_key)
        response = client.messages.create(
            model="claude-sonnet-4-6",
            max_tokens=1000,
            system=system_prompt,
            messages=messages,
        )
        reply = response.content[0].text

        # Detect if reply contains a draft-ready post (heuristic)
        has_suggestion = (
            len(reply) > 100 and
            tab in ("generate", "review") and
            any(phrase in reply.lower() for phrase in ["here's", "here is", "revised", "alternative", "version:"])
        )

        return {
            "response": reply,
            "has_suggestion": has_suggestion,
        }
    except Exception as e:
        logger.error(f"Chat error: {e}")
        raise HTTPException(500, f"Claude API error: {str(e)}")
