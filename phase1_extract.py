#!/usr/bin/env python3
"""
Phase 1: Environment Setup, Video Inspection, Faster-Whisper Transcription,
and PySceneDetect Camera Cut + Close-up Mapping.

Outputs:
  - video_metadata.json
  - transcript_part1.json
  - transcript_part2.json
  - scenes_index.json
"""

import glob
import json
import os
import re
import subprocess
import sys
import time
from pathlib import Path

import av
import cv2
import numpy as np
from faster_whisper import WhisperModel
from scenedetect import ContentDetector, open_video, SceneManager


ROOT = Path(__file__).resolve().parent


def find_ffmpeg() -> str:
    """Locate ffmpeg binary (PATH, /tmp/venv/bin, or imageio_ffmpeg)."""
    import shutil
    for cand in [shutil.which("ffmpeg"), "/tmp/venv/bin/ffmpeg"]:
        if cand and os.path.exists(cand):
            return cand
    try:
        import imageio_ffmpeg
        return imageio_ffmpeg.get_ffmpeg_exe()
    except Exception:
        raise RuntimeError("ffmpeg binary not found")


def detect_source_videos() -> list[Path]:
    """Auto-detect the two episode .mp4 files in repo root chronologically."""
    mp4s = [
        p for p in ROOT.glob("*.mp4")
        if p.name not in {"visual_master_sfx.mp4", "FINAL_YOUTUBE_VIDEO.mp4"}
    ]
    def sort_key(p: Path):
        m = re.search(r"part[_\- ]?(\d+)", p.name, re.IGNORECASE)
        return (int(m.group(1)) if m else 999, p.name.lower())
    mp4s.sort(key=sort_key)
    if len(mp4s) < 2:
        raise FileNotFoundError(f"Expected 2 source .mp4 files in {ROOT}, found {mp4s}")
    return mp4s[:2]


def inspect_video(path: Path) -> dict:
    with av.open(str(path)) as container:
        v = container.streams.video[0]
        a = container.streams.audio[0] if container.streams.audio else None
        dur = float(container.duration) / av.time_base if container.duration else 0.0
        return {
            "filename": path.name,
            "size_bytes": path.stat().st_size,
            "size_mb": round(path.stat().st_size / (1024 * 1024), 2),
            "duration_sec": round(dur, 3),
            "width": v.width,
            "height": v.height,
            "fps": round(float(v.average_rate), 3),
            "video_codec": v.codec_context.name,
            "audio_codec": a.codec_context.name if a else None,
            "audio_sample_rate": a.rate if a else None,
        }


def extract_wav(video_path: Path, wav_path: Path, ffmpeg_bin: str) -> None:
    if wav_path.exists() and wav_path.stat().st_size > 10000:
        return
    subprocess.run(
        [
            ffmpeg_bin, "-y", "-i", str(video_path),
            "-vn", "-ac", "1", "-ar", "16000", "-c:a", "pcm_s16le",
            str(wav_path), "-loglevel", "error",
        ],
        check=True,
    )


def transcribe_audio(model: WhisperModel, wav_path: Path, part_label: str, source_name: str, duration_sec: float) -> dict:
    t0 = time.time()
    segments_gen, info = model.transcribe(
        str(wav_path),
        language="ur",
        vad_filter=True,
        vad_parameters={"min_silence_duration_ms": 400, "threshold": 0.45},
        beam_size=1,
        best_of=1,
        temperature=0.0,
        condition_on_previous_text=False,
        no_speech_threshold=0.65,
    )
    segments = []
    for idx, seg in enumerate(segments_gen):
        txt = seg.text.strip()
        if not txt:
            continue
        segments.append({
            "id": idx,
            "start": round(float(seg.start), 2),
            "end": round(float(seg.end), 2),
            "text": txt,
            "avg_logprob": round(float(seg.avg_logprob), 3),
            "no_speech_prob": round(float(seg.no_speech_prob), 3),
        })
    elapsed = round(time.time() - t0, 2)
    print(f"[{part_label}] Transcribed {len(segments)} Urdu segments in {elapsed}s", flush=True)
    return {
        "part": part_label,
        "source_video": source_name,
        "duration_sec": duration_sec,
        "language": info.language,
        "language_probability": round(float(info.language_probability), 3),
        "model": "faster-whisper-small-int8",
        "elapsed_sec": elapsed,
        "segment_count": len(segments),
        "segments": segments,
    }


def detect_scenes_for_video(video_path: Path, part_label: str) -> list[dict]:
    t0 = time.time()
    video = open_video(str(video_path))
    scene_manager = SceneManager()
    scene_manager.add_detector(ContentDetector(threshold=26.0, min_scene_len=20))
    scene_manager.detect_scenes(video, show_progress=False)
    scene_list = scene_manager.get_scene_list()

    # Load OpenCV Haar face detector to flag emotional close-up shots
    cascade_path = cv2.data.haarcascades + "haarcascade_frontalface_default.xml"
    face_cascade = cv2.CascadeClassifier(cascade_path) if os.path.exists(cascade_path) else None

    cap = cv2.VideoCapture(str(video_path))
    fps = cap.get(cv2.CAP_PROP_FPS) or 25.0
    width = cap.get(cv2.CAP_PROP_FRAME_WIDTH) or 854.0
    height = cap.get(cv2.CAP_PROP_FRAME_HEIGHT) or 450.0
    frame_area = width * height

    scenes = []
    for idx, (start_tc, end_tc) in enumerate(scene_list):
        s_sec = round(start_tc.get_seconds(), 3)
        e_sec = round(end_tc.get_seconds(), 3)
        dur = round(e_sec - s_sec, 3)
        if dur < 0.8:
            continue
        mid_sec = round(s_sec + dur * 0.5, 3)

        # Sample mid frame for brightness, sharpness, and close-up face area
        cap.set(cv2.CAP_PROP_POS_FRAMES, int(mid_sec * fps))
        ok, frame = cap.read()
        brightness = 0.0
        sharpness = 0.0
        face_count = 0
        max_face_ratio = 0.0
        shot_type = "medium"

        if ok and frame is not None:
            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            brightness = round(float(np.mean(gray)), 1)
            sharpness = round(float(cv2.Laplacian(gray, cv2.CV_64F).var()), 1)
            if face_cascade is not None:
                faces = face_cascade.detectMultiScale(
                    gray, scaleFactor=1.15, minNeighbors=4, minSize=(36, 36)
                )
                face_count = len(faces)
                if face_count > 0:
                    max_face_ratio = round(
                        max((w * h) / frame_area for (_, _, w, h) in faces), 4
                    )
                    if max_face_ratio >= 0.045:
                        shot_type = "closeup"
                    elif max_face_ratio >= 0.015:
                        shot_type = "medium_closeup"
                    else:
                        shot_type = "wide_group"
            if brightness < 25.0:
                shot_type = "dark_or_fade"

        scenes.append({
            "scene_id": f"{part_label}_s{idx:04d}",
            "part": part_label,
            "source_video": video_path.name,
            "start_sec": s_sec,
            "end_sec": e_sec,
            "duration_sec": dur,
            "mid_sec": mid_sec,
            "brightness": brightness,
            "sharpness": sharpness,
            "face_count": face_count,
            "max_face_ratio": max_face_ratio,
            "shot_type": shot_type,
        })

    cap.release()
    print(
        f"[{part_label}] Detected {len(scenes)} usable scenes "
        f"({sum(1 for s in scenes if s['shot_type'] in {'closeup', 'medium_closeup'})} close-ups) "
        f"in {round(time.time() - t0, 2)}s",
        flush=True,
    )
    return scenes


def main():
    ffmpeg_bin = find_ffmpeg()
    videos = detect_source_videos()
    print("Detected source videos:", [v.name for v in videos], flush=True)

    meta = {
        "episode_title": "Mitti De Baway - Episode 1",
        "leads": {"Billo": "Mahira Khan", "Baala": "Wahaj Ali"},
        "parts": [],
    }
    for i, vp in enumerate(videos, 1):
        info = inspect_video(vp)
        info["part"] = f"part{i}"
        meta["parts"].append(info)
    meta["total_duration_sec"] = round(sum(p["duration_sec"] for p in meta["parts"]), 3)

    with open(ROOT / "video_metadata.json", "w", encoding="utf-8") as f:
        json.dump(meta, f, indent=2, ensure_ascii=False)
    print("Saved video_metadata.json", flush=True)

    # Load faster-whisper model (local offline cache if present, else HuggingFace)
    local_model = Path("/tmp/whisper-small")
    model_id = str(local_model) if local_model.exists() else "medium"
    print(f"Loading faster-whisper model from: {model_id}", flush=True)
    model = WhisperModel(model_id, device="cpu", compute_type="int8", cpu_threads=os.cpu_count() or 2)

    # Transcribe both halves
    for i, vp in enumerate(videos, 1):
        part_label = f"part{i}"
        wav_path = Path(f"/tmp/{part_label}.wav")
        extract_wav(vp, wav_path, ffmpeg_bin)
        transcript = transcribe_audio(model, wav_path, part_label, vp.name, meta["parts"][i - 1]["duration_sec"])
        out_json = ROOT / f"transcript_{part_label}.json"
        with open(out_json, "w", encoding="utf-8") as f:
            json.dump(transcript, f, indent=2, ensure_ascii=False)
        print(f"Saved {out_json.name}", flush=True)

    # Scene detection on both halves
    all_scenes = []
    for i, vp in enumerate(videos, 1):
        part_label = f"part{i}"
        scenes = detect_scenes_for_video(vp, part_label)
        all_scenes.extend(scenes)

    scenes_payload = {
        "total_scenes": len(all_scenes),
        "detector": "PySceneDetect ContentDetector(threshold=26.0, min_scene_len=20)",
        "part1_count": sum(1 for s in all_scenes if s["part"] == "part1"),
        "part2_count": sum(1 for s in all_scenes if s["part"] == "part2"),
        "closeup_count": sum(1 for s in all_scenes if s["shot_type"] in {"closeup", "medium_closeup"}),
        "scenes": all_scenes,
    }
    with open(ROOT / "scenes_index.json", "w", encoding="utf-8") as f:
        json.dump(scenes_payload, f, indent=2, ensure_ascii=False)
    print(f"Saved scenes_index.json ({len(all_scenes)} scenes total)", flush=True)


if __name__ == "__main__":
    main()
