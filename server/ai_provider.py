import os
from functools import lru_cache

from openai import OpenAI


_LOCAL_TARGETS = {"local", "ollama", "vllm"}
_CLOUD_TARGETS = {"cloud", "openai"}
_DEFAULT_ROUTES = {
    "brain": "cloud",
    "intake": "local",
    "mission": "local",
    "meeting": "local",
    "bidding_scout": "local",
    "proposal_draft": "local",
    "memory_reflection": "local",
    "embeddings": "local",
    "podcast": "local",
    "vision": "cloud",
    "receipt_vision": "cloud",
    "self_audit": "cloud",
    "skill_codegen": "cloud",
}
_FAST_TASKS = {
    "intake",
    "mission",
    "meeting",
    "bidding_scout",
    "proposal_draft",
    "memory_reflection",
    "podcast",
}
_VISION_TASKS = {"vision", "receipt_vision"}


def _normalize_target(value: str) -> str:
    target = (value or "").strip().lower()
    if target in _LOCAL_TARGETS:
        return "local"
    if target in _CLOUD_TARGETS:
        return "cloud"
    return ""


def _env_key(task: str) -> str:
    return task.upper().replace("-", "_")


def _env_bool(name: str, default: bool = False) -> bool:
    raw = os.getenv(name)
    if raw is None:
        return default
    return raw.strip().lower() in {"1", "true", "yes", "on"}


def _llm_mode() -> str:
    return os.getenv("ELIO_LLM_MODE", "hybrid").strip().lower()


def _local_base_url() -> str:
    return os.getenv("ELIO_LOCAL_BASE_URL", "http://localhost:11434/v1").rstrip("/")


def _cloud_api_key() -> str:
    api_key = os.getenv("OPENAI_API_KEY", "").strip()
    if not api_key:
        raise RuntimeError("OPENAI_API_KEY is required for cloud-routed LLM tasks.")
    return api_key


def get_route_for_task(task: str) -> str:
    override = _normalize_target(os.getenv(f"ELIO_ROUTE_{_env_key(task)}", ""))
    if override:
        return override

    mode = _normalize_target(_llm_mode())
    if mode:
        return mode

    target = _DEFAULT_ROUTES.get(task, "cloud")
    if target == "cloud" and not os.getenv("OPENAI_API_KEY") and _env_bool("ELIO_ALLOW_LOCAL_FALLBACK", True):
        return "local"
    return target


def _model_from_env(task: str, target: str) -> str:
    task_key = _env_key(task)
    target_key = target.upper()

    explicit = os.getenv(f"ELIO_MODEL_{task_key}", "").strip()
    if explicit:
        return explicit

    if task == "embeddings":
        return (
            os.getenv(f"ELIO_{target_key}_EMBED_MODEL", "").strip()
            or ("nomic-embed-text" if target == "local" else "text-embedding-3-small")
        )

    if task in _VISION_TASKS:
        return (
            os.getenv(f"ELIO_{target_key}_VISION_MODEL", "").strip()
            or os.getenv(f"ELIO_{target_key}_CHAT_MODEL", "").strip()
            or ("qwen2.5vl:7b" if target == "local" else "gpt-4o")
        )

    if task in _FAST_TASKS:
        return (
            os.getenv(f"ELIO_{target_key}_FAST_MODEL", "").strip()
            or os.getenv(f"ELIO_{target_key}_CHAT_MODEL", "").strip()
            or ("qwen3:8b" if target == "local" else "gpt-4o-mini")
        )

    return (
        os.getenv(f"ELIO_{target_key}_CHAT_MODEL", "").strip()
        or ("qwen3:8b" if target == "local" else "gpt-4o")
    )


@lru_cache(maxsize=4)
def _client_for_target(target: str):
    if target == "local":
        return OpenAI(
            base_url=_local_base_url(),
            api_key=os.getenv("ELIO_LOCAL_API_KEY", "ollama"),
        )

    kwargs = {"api_key": _cloud_api_key()}
    custom_base_url = os.getenv("OPENAI_BASE_URL", "").strip()
    if custom_base_url:
        kwargs["base_url"] = custom_base_url
    return OpenAI(**kwargs)


def reset_provider_cache():
    _client_for_target.cache_clear()


def get_chat_model(task: str) -> str:
    return _model_from_env(task, get_route_for_task(task))


def get_embedding_model() -> str:
    return _model_from_env("embeddings", get_route_for_task("embeddings"))


def chat_completion(task: str, **kwargs):
    target = get_route_for_task(task)
    return _client_for_target(target).chat.completions.create(
        model=_model_from_env(task, target),
        **kwargs,
    )


def create_embeddings(input_text, task: str = "embeddings", **kwargs):
    target = get_route_for_task(task)
    return _client_for_target(target).embeddings.create(
        model=_model_from_env("embeddings", target),
        input=input_text,
        **kwargs,
    )


def get_runtime_settings():
    summary = {
        "mode": _llm_mode(),
        "allow_local_fallback": _env_bool("ELIO_ALLOW_LOCAL_FALLBACK", True),
        "local_base_url": _local_base_url(),
        "cloud_base_url": os.getenv("OPENAI_BASE_URL", "").strip() or "https://api.openai.com/v1",
        "routes": {},
    }
    tasks = sorted(set(_DEFAULT_ROUTES) | {"brain", "embeddings", "vision"})
    for task in tasks:
        route = get_route_for_task(task)
        summary["routes"][task] = {
            "target": route,
            "model": _model_from_env(task, route),
        }
    return summary
