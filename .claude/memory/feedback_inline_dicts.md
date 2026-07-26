---
name: feedback-inline-dicts
description: Never build dicts or complex objects inline inside function calls — assign to a named variable first
metadata: 
  node_type: memory
  type: feedback
  originSessionId: 6574d139-aceb-42f3-92ac-6a3e0f8c674f
---

Never construct dicts or complex objects as inline arguments to function calls (e.g. `foo({...})`). Always assign to a named variable first, then pass it.

**Why:** Makes it easier to set a debugger breakpoint and inspect the value before the call executes.

**How to apply:** Any time a function call would receive a dict or multi-field object literal as an argument, extract it:
```python
# Wrong
chain.invoke({"title": pub["title"], "authors": ..., "journal": ...})

# Right
prompt_input = {"title": pub["title"], "authors": ..., "journal": ...}
chain.invoke(prompt_input)
```
Applies to all call sites: LLM chains, API clients, dataclass constructors, etc.
