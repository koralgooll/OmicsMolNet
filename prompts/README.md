# Prompts

This directory stores git-tracked prompt templates used by OmicsMolNet.

## Layout

Each prompt has its own folder and each version is a YAML file:

```text
prompts/
  <prompt_id>/
    v1.yaml
    v2.yaml
```

Example:

- `prompts/joke/v1.yaml`

## YAML schema

Required keys:

- `name`: A human-readable name for the prompt (e.g. `joke-generator`)
- `version`: A version string matching the filename (e.g. `v1`)
- `template`: A LangChain template string (e.g. `tell me a joke about {topic}`)

## Pinning versions

Prompt versions are pinned in the repo-root `config_prompt.yaml` file:

```yaml
prompts_root: prompts
prompts:
  joke: v1
```
