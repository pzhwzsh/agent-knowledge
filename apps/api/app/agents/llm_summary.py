import json
from typing import TypeVar

from pydantic import BaseModel, ValidationError

from app.llm.base import ChatModel

SchemaT = TypeVar("SchemaT", bound=BaseModel)


def complete_json(
    chat_model: ChatModel,
    *,
    schema: type[SchemaT],
    task: str,
    payload: dict[str, object],
    fallback: SchemaT,
) -> SchemaT:
    messages = [
        {
            "role": "system",
            "content": (
                "你是个人知识库内容总结 Agent。只返回严格 JSON，不要 Markdown，不要额外解释。"
                "JSON 字段必须符合用户提供的 schema。"
            ),
        },
        {
            "role": "user",
            "content": (
                f"任务：{task}\n\n"
                f"JSON schema 字段：{list(schema.model_fields.keys())}\n\n"
                f"输入：{json.dumps(payload, ensure_ascii=False, default=str)}"
            ),
        },
    ]
    try:
        raw = chat_model.complete(messages)
        data = _parse_json_object(raw)
        return schema.model_validate(data)
    except (json.JSONDecodeError, ValidationError, TypeError, ValueError):
        return fallback


def _parse_json_object(raw: str) -> dict[str, object]:
    text = raw.strip()
    if text.startswith("```"):
        text = _strip_fenced_json(text)
    data = json.loads(text)
    if not isinstance(data, dict):
        raise TypeError("Summary model must return a JSON object")
    return data


def _strip_fenced_json(text: str) -> str:
    lines = text.splitlines()
    if lines and lines[0].startswith("```"):
        lines = lines[1:]
    if lines and lines[-1].strip() == "```":
        lines = lines[:-1]
    return "\n".join(lines).strip()


def complete_json_summary(
    chat_model: ChatModel,
    *,
    schema: type[SchemaT],
    task: str,
    payload: dict[str, object],
    fallback: SchemaT,
) -> SchemaT:
    return complete_json(chat_model, schema=schema, task=task, payload=payload, fallback=fallback)
