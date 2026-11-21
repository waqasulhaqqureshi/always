#!/usr/bin/env python3
"""
Local One-Click Audio Merger for Windows / macOS / Linux
Concatenates elevenlabs_audio/part1.mp3 ... part8.mp3, applies YouTube EBU R128
loudness normalization (loudnorm), mixes over visual_master_sfx.mp4 with automatic
sidechain ducking of the SFX/ambient bed whenever the voice speaks, and exports
FINAL_YOUTUBE_VIDEO.mp4 in seconds (stream-copying the 1080p video!).
"""

import argparse
import os
import shutil
import subprocess
import sys
import tempfile
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent


def find_ffmpeg() -> str:
    for cand in [
        shutil.which("ffmpeg"),
        str(ROOT / "ffmpeg.exe"),
        "/tmp/venv/bin/ffmpeg",
    ]:
        if cand and os.path.exists(cand):
            return cand
    try:
        import imageio_ffmpeg
        return imageio_ffmpeg.get_ffmpeg_exe()
    except Exception:
        pass
    print("[ERROR] FFmpeg was not found on your PATH.")
    print("Install it on Windows PowerShell with:  winget install Gyan.FFmpeg")
    print("Then restart your terminal and double-click merge_audio.bat again.")
    sys.exit(1)


def main():
    parser = argparse.ArgumentParser(description="Merge 8 ElevenLabs MP3 parts with visual_master_sfx.mp4")
    parser.add_argument("--audio-dir", default=str(ROOT / "elevenlabs_audio"), help="Folder containing part1.mp3..part8.mp3")
    parser.add_argument("--video", default=str(ROOT / "visual_master_sfx.mp4"), help="Pre-rendered 8-min visual master")
    parser.add_argument("--output", default=str(ROOT / "FINAL_YOUTUBE_VIDEO.mp4"), help="Final export path")
    args = parser.parse_args()

    t0 = time.time()
    ffmpeg_bin = find_ffmpeg()
    audio_dir = Path(args.audio_dir)
    video_path = Path(args.video)
    output_path = Path(args.output)

    if not video_path.exists():
        print(f"[ERROR] Visual master not found: {video_path}")
        sys.exit(1)

    part_files = [audio_dir / f"part{i}.mp3" for i in range(1, 9)]
    missing = [p.name for p in part_files if not p.exists()]
    if missing:
        print("=" * 68)
        print("  MISSING ELEVENLABS AUDIO FILES in:", audio_dir)
        print("=" * 68)
        for p in part_files:
            status = "[OK]     " if p.exists() else "[MISSING]"
            print(f"  {status} {p.name}")
        print("\nDrop part1.mp3 through part8.mp3 into elevenlabs_audio/ and re-run!")
        sys.exit(1)

    print(f"Using FFmpeg: {ffmpeg_bin}")
    print("Step 1/2: Concatenating part1.mp3 .. part8.mp3 + applying EBU R128 loudnorm...")

    with tempfile.TemporaryDirectory(prefix="yt_merge_") as tmp:
        tmp_dir = Path(tmp)
        concat_list = tmp_dir / "voice_parts.txt"
        concat_list.write_text(
            "\n".join(f"file '{p.resolve().as_posix()}'" for p in part_files) + "\n",
            encoding="utf-8",
        )
        voice_norm = tmp_dir / "voice_normalized.wav"

        # Concatenate all 8 MP3 clips cleanly, normalize to YouTube -14 LUFS broadcast standard
        cmd_voice = [
            ffmpeg_bin, "-y",
            "-f", "concat", "-safe", "0", "-i", str(concat_list),
            "-af", (
                "aresample=48000,"
                "aformat=sample_fmts=fltp:channel_layouts=stereo,"
                "highpass=f=75,"
                "loudnorm=I=-14:TP=-1.5:LRA=11"
            ),
            "-c:a", "pcm_s16le", str(voice_norm),
            "-loglevel", "error",
        ]
        res = subprocess.run(cmd_voice, capture_output=True, text=True)
        if res.returncode != 0:
            print("[ERROR] Failed to concatenate/normalize voice files:\n", res.stderr)
            sys.exit(1)

        print("Step 2/2: Auto-ducking SFX/ambient bed under voice & exporting FINAL_YOUTUBE_VIDEO.mp4...")

        # Sidechain ducking: whenever voice plays, duck the pre-mixed SFX/ambient bed smoothly
        # Video stream is copied directly (-c:v copy) for instant lossless export!
        fc = (
            "[1:a]aresample=48000,aformat=sample_fmts=fltp:channel_layouts=stereo,asplit=2[voice_main][voice_sc];"
            "[0:a]aresample=48000,aformat=sample_fmts=fltp:channel_layouts=stereo[bg_raw];"
            "[bg_raw][voice_sc]sidechaincompress="
            "threshold=0.025:ratio=4.5:attack=25:release=260:makeup=1[bg_ducked];"
            "[bg_ducked][voice_main]amix=inputs=2:duration=first:dropout_transition=2:normalize=0,"
            "alimiter=limit=0.95[aout]"
        )

        cmd_merge = [
            ffmpeg_bin, "-y",
            "-i", str(video_path),
            "-i", str(voice_norm),
            "-filter_complex", fc,
            "-map", "0:v:0",
            "-map", "[aout]",
            "-c:v", "copy",
            "-c:a", "aac", "-b:a", "192k", "-ar", "48000", "-ac", "2",
            "-movflags", "+faststart",
            str(output_path),
            "-loglevel", "error",
        ]
        res = subprocess.run(cmd_merge, capture_output=True, text=True)
        if res.returncode != 0:
            print("[ERROR] Failed during final video/audio merge:\n", res.stderr)
            sys.exit(1)

    size_mb = output_path.stat().st_size / (1024 * 1024)
    print("=" * 68)
    print(f"  SUCCESS! Exported: {output_path.name} ({size_mb:.2f} MB)")
    print(f"  Completed in {time.time() - t0:.1f} seconds.")
    print("=" * 68)


if __name__ == "__main__":
    main()
