import io
import os
from functools import lru_cache
from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field


app = FastAPI(title="Elio XTTS Service", version="1.0.0")


class SynthesizeRequest(BaseModel):
    text: str = Field(min_length=1, max_length=4000)
    voice: str = Field(min_length=1, max_length=120)
    language: str = Field(default="en", min_length=2, max_length=12)
    speed: float = Field(default=1.0, ge=0.5, le=1.5)


def _speaker_root() -> Path:
    return Path(os.getenv("ELIO_XTTS_SPEAKER_DIR", "/voices")).resolve()


def _speaker_dir(voice: str) -> Path:
    safe_voice = Path(voice).name
    return (_speaker_root() / safe_voice).resolve()


def _resolve_speaker_refs(voice: str):
    speaker_dir = _speaker_dir(voice)
    root = _speaker_root()
    if speaker_dir.parent != root:
        raise HTTPException(status_code=400, detail="Invalid voice profile.")
    if not speaker_dir.exists() or not speaker_dir.is_dir():
        raise HTTPException(status_code=404, detail=f"Voice profile '{speaker_dir.name}' not found.")

    prepared_dir = speaker_dir / "_prepared"
    refs_root = prepared_dir if prepared_dir.exists() and prepared_dir.is_dir() else speaker_dir
    refs = sorted(str(path) for path in refs_root.glob("*.wav"))
    if not refs:
        raise HTTPException(status_code=404, detail=f"Voice profile '{speaker_dir.name}' has no .wav references.")
    return refs


def _patch_transformers_for_xtts():
    import transformers
    from transformers.generation.beam_constraints import DisjunctiveConstraint, PhrasalConstraint
    from transformers.generation.beam_search import BeamSearchScorer, ConstrainedBeamSearchScorer
    from transformers.generation.configuration_utils import GenerationConfig
    from transformers.generation.logits_process import LogitsProcessorList
    from transformers.generation.stopping_criteria import StoppingCriteriaList
    from transformers.generation.utils import GenerationMixin

    exports = {
        "BeamSearchScorer": BeamSearchScorer,
        "ConstrainedBeamSearchScorer": ConstrainedBeamSearchScorer,
        "DisjunctiveConstraint": DisjunctiveConstraint,
        "GenerationConfig": GenerationConfig,
        "GenerationMixin": GenerationMixin,
        "LogitsProcessorList": LogitsProcessorList,
        "PhrasalConstraint": PhrasalConstraint,
        "StoppingCriteriaList": StoppingCriteriaList,
    }
    for name, value in exports.items():
        setattr(transformers, name, value)


def _patch_xtts_stream_generator_imports():
    import TTS

    stream_path = Path(TTS.__file__).resolve().parent / "tts" / "layers" / "xtts" / "stream_generator.py"
    legacy_import = """from transformers import (
    BeamSearchScorer,
    ConstrainedBeamSearchScorer,
    DisjunctiveConstraint,
    GenerationConfig,
    GenerationMixin,
    LogitsProcessorList,
    PhrasalConstraint,
    PreTrainedModel,
    StoppingCriteriaList,
)
from transformers.generation.utils import GenerateOutput, SampleOutput, logger
"""
    patched_import = """from transformers.generation.beam_constraints import DisjunctiveConstraint, PhrasalConstraint
from transformers.generation.beam_search import BeamSearchScorer, ConstrainedBeamSearchScorer
from transformers.generation.configuration_utils import GenerationConfig
from transformers.generation.logits_process import LogitsProcessorList
from transformers.generation.stopping_criteria import StoppingCriteriaList
from transformers.generation.utils import GenerateOutput, GenerationMixin, SampleOutput, logger
from transformers.modeling_utils import PreTrainedModel
"""

    contents = stream_path.read_text(encoding="utf-8")
    if legacy_import in contents:
        stream_path.write_text(contents.replace(legacy_import, patched_import), encoding="utf-8")


def _patch_tts_checkpoint_loading():
    import TTS.utils.io as tts_io

    original_load_fsspec = tts_io.load_fsspec
    if getattr(original_load_fsspec, "_elio_weights_only_patched", False):
        return

    def load_fsspec_with_unsafe_allowed(*args, **kwargs):
        kwargs.setdefault("weights_only", False)
        return original_load_fsspec(*args, **kwargs)

    load_fsspec_with_unsafe_allowed._elio_weights_only_patched = True
    tts_io.load_fsspec = load_fsspec_with_unsafe_allowed


def _patch_torchaudio_load_for_xtts():
    import soundfile as sf
    import torch
    import torchaudio

    original_load = torchaudio.load
    if getattr(original_load, "_elio_soundfile_patched", False):
        return

    def load_with_soundfile(
        uri,
        frame_offset=0,
        num_frames=-1,
        normalize=True,
        channels_first=True,
        format=None,
        buffer_size=4096,
        backend=None,
    ):
        del normalize, format, buffer_size, backend
        frames = -1 if num_frames is None or num_frames < 0 else int(num_frames)
        audio, sample_rate = sf.read(uri, start=int(frame_offset), frames=frames, dtype="float32", always_2d=True)
        tensor = torch.from_numpy(audio.T if channels_first else audio)
        return tensor, sample_rate

    load_with_soundfile._elio_soundfile_patched = True
    torchaudio.load = load_with_soundfile


def _patch_xtts_generation_mixin():
    from TTS.tts.layers.xtts.gpt_inference import GPT2InferenceModel
    from transformers.generation.utils import GenerationMixin

    if hasattr(GPT2InferenceModel, "generate"):
        return

    for name, value in GenerationMixin.__dict__.items():
        if name.startswith("__") or hasattr(GPT2InferenceModel, name):
            continue
        setattr(GPT2InferenceModel, name, value)


def _prime_xtts_generation_config(tts):
    from transformers.generation.configuration_utils import GenerationConfig

    gpt_inference = tts.synthesizer.tts_model.gpt.gpt_inference
    if getattr(gpt_inference, "generation_config", None) is None and getattr(gpt_inference, "config", None) is not None:
        gpt_inference.generation_config = GenerationConfig.from_model_config(gpt_inference.config)


@lru_cache(maxsize=1)
def _tts():
    use_gpu = os.getenv("ELIO_XTTS_USE_GPU", "true").strip().lower() in {"1", "true", "yes", "on"}
    model_name = os.getenv("ELIO_XTTS_MODEL", "tts_models/multilingual/multi-dataset/xtts_v2")
    _patch_transformers_for_xtts()
    _patch_torchaudio_load_for_xtts()
    _patch_xtts_stream_generator_imports()
    from TTS.api import TTS
    _patch_tts_checkpoint_loading()
    _patch_xtts_generation_mixin()
    tts = TTS(model_name).to("cuda" if use_gpu else "cpu")
    _prime_xtts_generation_config(tts)
    return tts


@app.get("/health")
def health():
    return {
        "ok": True,
        "model": os.getenv("ELIO_XTTS_MODEL", "tts_models/multilingual/multi-dataset/xtts_v2"),
        "speaker_dir": str(_speaker_root()),
        "gpu_requested": os.getenv("ELIO_XTTS_USE_GPU", "true"),
    }


@app.post("/synthesize")
def synthesize(payload: SynthesizeRequest):
    try:
        refs = _resolve_speaker_refs(payload.voice)
        split_sentences = os.getenv("ELIO_XTTS_SPLIT_SENTENCES", "true").strip().lower() in {"1", "true", "yes", "on"}
        wav = _tts().tts(
            text=payload.text,
            speaker_wav=refs,
            language=payload.language,
            split_sentences=split_sentences,
        )

        try:
            import soundfile as sf
        except ImportError as exc:
            raise RuntimeError("soundfile is required for XTTS audio encoding.") from exc

        buffer = io.BytesIO()
        sf.write(buffer, wav, 24000, format="WAV")
        buffer.seek(0)
        return StreamingResponse(buffer, media_type="audio/wav")
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc
