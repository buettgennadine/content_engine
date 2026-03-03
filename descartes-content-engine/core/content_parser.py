"""
Content Parser for Visual Agent.
Extracts structured data from draft content to drive Pillow template rendering.
Extraction rules loaded from prompts/visual_extraction.json if present.
"""

import re
import json
import logging
from dataclasses import dataclass
from pathlib import Path

logger = logging.getLogger(__name__)

def _load_extraction_config() -> dict:
    p = Path(__file__).resolve().parent.parent / "prompts" / "visual_extraction.json"
    if p.exists():
        try:
            with open(p, encoding="utf-8") as f:
                return json.load(f)
        except Exception as e:
            logger.warning(f"Could not load visual_extraction.json: {e}")
    return {}

_EX = _load_extraction_config()


@dataclass
class KeyNumber:
    number: str          # e.g. "£11.7bn"
    context: str         # e.g. "Motor claims paid by UK insurers in 2024"
    change: str | None   # e.g. "+17%" or None


@dataclass
class BeforeAfter:
    before: str          # e.g. "45 days"
    after: str           # e.g. "8 days"
    metric: str          # e.g. "End-to-end settlement time"


@dataclass
class CarouselSlide:
    number: int
    slide_type: str      # 'cover' | 'content' | 'cta'
    headline: str
    subtext: str | None


class ContentParser:
    """Extracts visual-relevant data from draft content."""

    # Signature phrases / scoring — loaded from config or hardcoded defaults
    _qcfg = _EX.get("quote", {})
    QUOTE_BOOST_PHRASES = _qcfg.get("boost_phrases", ["not a people problem", "design problem", "by design"])
    QUOTE_BOOST_WORDS   = _qcfg.get("boost_words", ["system", "designed", "design"])
    QUOTE_REFRAME_WORDS = _qcfg.get("reframe_words", ["not", "isn't", "doesn't", "won't"])
    QUOTE_AVOID_WORDS   = _qcfg.get("avoid_words", ["click", "follow", "dm me", "comment"])
    QUOTE_MAX_WORDS     = _qcfg.get("max_words", 25)
    QUOTE_PREFER_SHORT  = _qcfg.get("prefer_short_under_words", 12)
    QUOTE_FALLBACK      = _qcfg.get("fallback", "Change the design. Change the results.")

    HEADLINE_MAX_WORDS  = _EX.get("headline", {}).get("max_words", 8)
    HEADLINE_FALLBACK   = _EX.get("headline", {}).get("fallback", "Systems Thinking")
    HEADLINE_STRIP      = _EX.get("headline", {}).get("strip_prefixes", ['🔴','🟢','🔥','📊','📋','❓','📖','*','**'])

    QUOTE_TRIGGER_WORDS = _EX.get("quote_trigger_words", ["design", "system", "not", "never", "always"])

    # Common number patterns in Stuart's content
    NUMBER_PATTERNS = [
        # Currency: £11.7bn, $4.2m, €289m
        r'[£$€]\s*[\d,.]+\s*(?:bn|billion|mn|million|m|k|thousand)?',
        # Percentage: 54%, +17%, -30pp
        r'[+-]?\d+(?:\.\d+)?%',
        r'[+-]?\d+(?:\.\d+)?pp',
        # Large numbers: 305,726 or 11.7 billion
        r'\d{1,3}(?:,\d{3})+',
        r'\d+(?:\.\d+)?\s*(?:billion|million|thousand)',
        # Multipliers: 2.5×, 6×
        r'\d+(?:\.\d+)?[×x]',
    ]

    # Before/After signal words
    BEFORE_WORDS = ['before', 'from', 'was', 'old', 'previous', 'originally']
    AFTER_WORDS = ['after', 'to', 'now', 'new', 'became', 'reduced to', 'improved to']

    def detect_visual_type(self, content: str, post_type: str, carousel_data: dict | None = None) -> str:
        """Decide which visual type fits best.

        Returns: 'carousel' | 'thumbnail' | 'data_visual' | 'quote_card' | 'none'
        """
        if post_type == "poll":
            return "none"

        if post_type == "carousel":
            return "carousel"

        if post_type == "thumbnail":
            return "thumbnail"

        # post_type == "text" → analyze content
        if self.extract_key_number(content):
            return "data_visual"

        if self._has_strong_quote(content):
            return "quote_card"

        # Default: no visual for text posts unless manually triggered
        return "none"

    def extract_headline(self, content: str, max_words: int = None) -> str:
        """Extract or generate a short headline for thumbnail overlay.

        Strategy: Take the first sentence (the hook), compress to max_words.
        """
        if max_words is None:
            max_words = self.HEADLINE_MAX_WORDS
        # Get first line/sentence
        lines = [l.strip() for l in content.strip().split('\n') if l.strip()]
        if not lines:
            return self.HEADLINE_FALLBACK

        first_line = lines[0]

        # Remove common prefixes
        for prefix in self.HEADLINE_STRIP:
            first_line = first_line.lstrip(prefix).strip()

        # If already short enough
        words = first_line.split()
        if len(words) <= max_words:
            return first_line.rstrip('.')

        # Compress: take first max_words, find natural break
        truncated = words[:max_words]
        headline = ' '.join(truncated)

        # Try to end at a natural break
        for punct in ['.', '?', '!', '—', '–', ':']:
            idx = headline.rfind(punct)
            if idx > len(headline) // 2:
                return headline[:idx + 1]

        return headline + '...'

    def extract_key_number(self, content: str) -> KeyNumber | None:
        """Find the most prominent number + context for Data Visuals.

        Priority: currency amounts > percentages > large numbers > multipliers
        """
        best_match = None
        best_priority = 99

        for priority, pattern in enumerate(self.NUMBER_PATTERNS):
            matches = list(re.finditer(pattern, content, re.IGNORECASE))
            if matches and priority < best_priority:
                match = matches[0]  # Take first occurrence
                best_match = match
                best_priority = priority

        if not best_match:
            return None

        number_str = best_match.group().strip()

        # Extract surrounding context (the sentence containing the number)
        start = max(0, content.rfind('.', 0, best_match.start()) + 1)
        end = content.find('.', best_match.end())
        if end == -1:
            end = min(len(content), best_match.end() + 100)

        context = content[start:end].strip()
        # Remove the number itself from context
        context = context.replace(number_str, '').strip(' .,;:–—')

        # Look for a change indicator nearby
        change = None
        nearby = content[max(0, best_match.start() - 50):best_match.end() + 50]
        change_match = re.search(r'[+-]\d+(?:\.\d+)?%', nearby)
        if change_match and change_match.group() != number_str:
            change = change_match.group()

        return KeyNumber(number=number_str, context=context[:120], change=change)

    def extract_hook_quote(self, content: str, max_words: int = None) -> str:
        """Extract the strongest sentence for Quote Cards.

        Strategy:
        1. Look for sentences with Stuart's signature patterns
        2. Prefer short, declarative sentences
        3. Prefer sentences with contrast or reframing
        """
        if max_words is None:
            max_words = self.QUOTE_MAX_WORDS
        sentences = self._split_sentences(content)

        # Score each sentence
        scored = []
        for s in sentences:
            score = 0
            words = s.split()
            s_lower = s.lower()

            # Short sentences score higher (Stuart's style)
            if len(words) <= self.QUOTE_PREFER_SHORT:
                score += 3
            elif len(words) <= 20:
                score += 1

            # Stuart's signature patterns (from config)
            for phrase in self.QUOTE_BOOST_PHRASES:
                if phrase in s_lower:
                    score += 4
            if any(w in s_lower for w in self.QUOTE_BOOST_WORDS):
                score += 2
            if any(w in s_lower for w in self.QUOTE_REFRAME_WORDS):
                score += 1

            # Avoid questions and meta-text
            if s.endswith('?'):
                score -= 1
            if any(w in s_lower for w in self.QUOTE_AVOID_WORDS):
                score -= 5

            if len(words) <= max_words:
                scored.append((score, s))

        if not scored:
            # Fallback: first non-trivial sentence
            for s in sentences:
                if len(s.split()) >= 4:
                    words = s.split()[:max_words]
                    return ' '.join(words)
            return self.QUOTE_FALLBACK

        scored.sort(key=lambda x: x[0], reverse=True)
        return scored[0][1]

    def parse_carousel_slides(self, carousel_data: dict | str | None) -> list[CarouselSlide]:
        """Parse carousel_data into structured slide objects.

        Handles both JSON dict and plain text formats.
        """
        if not carousel_data:
            return []

        # If string, try JSON parse
        if isinstance(carousel_data, str):
            try:
                carousel_data = json.loads(carousel_data)
            except json.JSONDecodeError:
                # Plain text: split by double newlines or numbered items
                return self._parse_text_carousel(carousel_data)

        # If dict with 'slides' key
        if isinstance(carousel_data, dict) and 'slides' in carousel_data:
            slides_raw = carousel_data['slides']
        elif isinstance(carousel_data, list):
            slides_raw = carousel_data
        else:
            return []

        slides = []
        total = len(slides_raw)

        for i, slide in enumerate(slides_raw):
            if isinstance(slide, str):
                headline = slide
                subtext = None
            elif isinstance(slide, dict):
                headline = slide.get('headline', slide.get('text', slide.get('point', '')))
                subtext = slide.get('subtext', slide.get('detail', slide.get('description', None)))
            else:
                continue

            # Determine slide type
            if i == 0:
                slide_type = 'cover'
            elif i == total - 1:
                slide_type = 'cta'
            else:
                slide_type = 'content'

            slides.append(CarouselSlide(
                number=i + 1,
                slide_type=slide_type,
                headline=headline,
                subtext=subtext
            ))

        return slides

    def extract_before_after(self, content: str) -> BeforeAfter | None:
        """Find Before/After metrics in content."""
        content_lower = content.lower()

        # Pattern: "from X to Y"
        from_to = re.search(
            r'from\s+([\d,.]+\s*\w+)\s+to\s+([\d,.]+\s*\w+)',
            content_lower
        )
        if from_to:
            return BeforeAfter(
                before=from_to.group(1).strip(),
                after=from_to.group(2).strip(),
                metric=self._extract_metric_context(content, from_to.start())
            )

        # Pattern: "reduced/improved from X to Y" or "X → Y"
        arrow = re.search(
            r'([\d,.]+\s*\w+)\s*[→>]\s*([\d,.]+\s*\w+)',
            content
        )
        if arrow:
            return BeforeAfter(
                before=arrow.group(1).strip(),
                after=arrow.group(2).strip(),
                metric=self._extract_metric_context(content, arrow.start())
            )

        return None

    # ─── Private helpers ─────────────────────────────────────────────────

    def _split_sentences(self, content: str) -> list[str]:
        """Split content into sentences, respecting abbreviations."""
        # Simple split on sentence-ending punctuation
        raw = re.split(r'(?<=[.!?])\s+', content)
        sentences = []
        for s in raw:
            s = s.strip()
            # Skip very short fragments
            if len(s.split()) >= 3:
                sentences.append(s)
        return sentences

    def _has_strong_quote(self, content: str) -> bool:
        """Check if content contains a strong, quotable statement."""
        sentences = self._split_sentences(content)
        for s in sentences:
            words = s.split()
            if 5 <= len(words) <= 20:
                lower = s.lower()
                if any(w in lower for w in self.QUOTE_TRIGGER_WORDS):
                    return True
        return False

    def _extract_metric_context(self, content: str, position: int) -> str:
        """Extract what metric is being measured around a given position."""
        # Look backwards for context
        start = max(0, content.rfind('.', 0, position) + 1)
        snippet = content[start:position].strip()

        # Common metric words
        for word in ['time', 'days', 'cost', 'rate', 'ratio', 'score', 'staff',
                     'complaints', 'settlement', 'cycle', 'throughput']:
            if word in snippet.lower():
                return snippet[-80:].strip(' .,;:')

        return snippet[-60:].strip(' .,;:') if snippet else "Key metric"

    def _parse_text_carousel(self, text: str) -> list[CarouselSlide]:
        """Parse plain text into carousel slides."""
        # Split by numbered items or double newlines
        parts = re.split(r'\n\s*\n|\n(?=\d+[.)]\s)', text.strip())
        parts = [p.strip() for p in parts if p.strip()]

        if not parts:
            return []

        slides = []
        total = len(parts)

        for i, part in enumerate(parts):
            # Remove numbering prefix
            clean = re.sub(r'^\d+[.)]\s*', '', part)

            if i == 0:
                slide_type = 'cover'
            elif i == total - 1:
                slide_type = 'cta'
            else:
                slide_type = 'content'

            # Split into headline + subtext at first newline
            lines = clean.split('\n', 1)
            headline = lines[0].strip()
            subtext = lines[1].strip() if len(lines) > 1 else None

            slides.append(CarouselSlide(
                number=i + 1,
                slide_type=slide_type,
                headline=headline,
                subtext=subtext
            ))

        return slides
