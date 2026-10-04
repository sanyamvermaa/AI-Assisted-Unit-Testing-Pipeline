"""Small helpers shared by the LLM-backed agents."""

import re

_FENCE = re.compile(r"```[a-zA-Z0-9_+-]*\s*\n(.*?)\n?```", re.DOTALL)


def strip_code_fences(text: str) -> str:
    """Extract code from a Markdown code fence, if present.

    Free models frequently wrap code in ```python ... ``` even when told
    not to, sometimes with surrounding prose. Extracting the fence content
    is safe because the result is still validated with ast.parse().
    """
    text = text.strip()
    match = _FENCE.search(text)
    return match.group(1).strip() if match else text
