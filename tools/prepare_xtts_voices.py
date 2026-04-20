import argparse
import json
import re
import subprocess
from datetime import datetime, timezone
from pathlib import Path


SUPPORTED_AUDIO_EXTENSIONS = {".wav", ".mp3", ".m4a", ".aac", ".flac", ".ogg", ".opus", ".wma"}


def _slugify(value: str) -> str:
    slug = re.sub(r"[^A-Za-z0-9_-]+", "-", value).strip("-").lower()
    return slug or "sample"


def _profile_dirs(root: Path, requested_profiles: list[str] | None = None) -> list[Path]:
    if requested_profiles:
        return [root / profile for profile in requested_profiles]
    return sorted(
        path
        for path in root.iterdir()
        if path.is_dir() and not path.name.startswith(".") and path.name != "_prepared"
    )


def _source_files(profile_dir: Path) -> list[Path]:
    return sorted(
        path
        for path in profile_dir.iterdir()
        if path.is_file() and path.suffix.lower() in SUPPORTED_AUDIO_EXTENSIONS
    )


def _clear_prepared_dir(prepared_dir: Path) -> None:
    if not prepared_dir.exists():
        return
    for path in prepared_dir.iterdir():
        if path.is_file():
            path.unlink()


def _transcode_file(ffmpeg_bin: str, source: Path, output_path: Path) -> None:
    command = [
        ffmpeg_bin,
        "-hide_banner",
        "-loglevel",
        "error",
        "-y",
        "-i",
        str(source),
        "-vn",
        "-ac",
        "1",
        "-ar",
        "24000",
        "-c:a",
        "pcm_s16le",
        str(output_path),
    ]
    subprocess.run(command, check=True)


def prepare_profile(profile_dir: Path, ffmpeg_bin: str) -> dict:
    if not profile_dir.exists() or not profile_dir.is_dir():
        raise FileNotFoundError(f"Voice profile '{profile_dir.name}' was not found at {profile_dir}.")

    sources = _source_files(profile_dir)
    prepared_dir = profile_dir / "_prepared"
    prepared_dir.mkdir(exist_ok=True)
    _clear_prepared_dir(prepared_dir)

    prepared_files = []
    for index, source in enumerate(sources, start=1):
        output_name = f"ref-{index:02d}-{_slugify(source.stem)}.wav"
        output_path = prepared_dir / output_name
        _transcode_file(ffmpeg_bin, source, output_path)
        prepared_files.append(
            {
                "source": str(source),
                "prepared": str(output_path),
            }
        )

    manifest_path = prepared_dir / "manifest.json"
    manifest = {
        "profile": profile_dir.name,
        "prepared_at": datetime.now(timezone.utc).isoformat(),
        "sources": prepared_files,
    }
    manifest_path.write_text(json.dumps(manifest, indent=2), encoding="utf-8")

    return {
        "profile": profile_dir.name,
        "sources": len(sources),
        "prepared": len(prepared_files),
        "prepared_dir": str(prepared_dir),
        "manifest": str(manifest_path),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Normalize raw XTTS speaker clips into prepared WAV references.")
    parser.add_argument("--root", default="voices/xtts", help="Root directory containing per-user voice folders.")
    parser.add_argument(
        "--profile",
        action="append",
        dest="profiles",
        help="Specific voice profile to prepare. Repeat for multiple profiles.",
    )
    parser.add_argument("--ffmpeg-bin", default="ffmpeg", help="Path to the ffmpeg executable.")
    parser.add_argument("--json", action="store_true", help="Emit the prep summary as JSON.")
    args = parser.parse_args()

    root = Path(args.root).resolve()
    if not root.exists() or not root.is_dir():
        raise SystemExit(f"Voice root '{root}' does not exist.")

    results = [prepare_profile(profile_dir, args.ffmpeg_bin) for profile_dir in _profile_dirs(root, args.profiles)]
    if args.json:
        print(json.dumps(results, indent=2))
    else:
        for item in results:
            print(
                f"{item['profile']}: prepared {item['prepared']} reference clips "
                f"from {item['sources']} source files into {item['prepared_dir']}"
            )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
