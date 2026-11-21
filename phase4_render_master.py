#!/usr/bin/env python3
"""
Phase 4B: Render 8-Minute @film.feel.50-Style Visual Master with Pre-Mixed SFX & Ambient Bed
Outputs:
  - visual_master_sfx.mp4 (480.0s, 1920x1080, 30fps, strictly under 85 MB)

Features:
  - Alternating micro-cut clips (<= 2.85s continuous per shot, 100% muted) and Ken Burns 1080p stills
  - 1.03x crop/scale, cinematic color grade (eq=contrast=1.08:saturation=1.15, warm highlights + cool shadows, vignette)
  - 3-frame white flash + micro-shake on shock/betrayal beats
  - 0.20s FFmpeg xfade transitions (fade, smoothleft, zoomin) mixed with sharp cuts
  - Sample-accurate pre-mix of whoosh, bass_hit, riser, heartbeat SFX + bg_ambient_bed.mp3 (-29 dB)
"""

import json
import os
import shutil
import subprocess
import time
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import numpy as np
from scipy.io import wavfile

ROOT = Path(__file__).resolve().parent
SFX_DIR = ROOT / "sfx_library"
WORK_DIR = Path("/tmp/render_8min_work")
SR = 48000
TOTAL_DUR = 480.0


def find_ffmpeg() -> str:
    for cand in [shutil.which("ffmpeg"), "/tmp/venv/bin/ffmpeg"]:
        if cand and os.path.exists(cand):
            return cand
    import imageio_ffmpeg
    return imageio_ffmpeg.get_ffmpeg_exe()


def run_ffmpeg(cmd: list[str]) -> None:
    res = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    if res.returncode != 0:
        raise RuntimeError(f"FFmpeg failed:\nCMD: {' '.join(cmd)}\nSTDERR:\n{res.stderr[-2000:]}")


def render_still_beat(beat: dict, render_dur: float, out_path: Path, ffmpeg_bin: str) -> None:
    """Extract crisp 1080p still, grade once, then animate with smooth Ken Burns zoompan."""
    bid = beat["beat_id"]
    src_video = ROOT / beat["source_video"]
    frame_t = beat["still"]["frame_timestamp_sec"]
    motion = beat["still"]["ken_burns_motion"]
    shock = beat["shock_flash_shake"]

    still_jpg = WORK_DIR / f"still_{bid:03d}.jpg"
    # 1.03x crop/scale + dramatic film color grade + subtle vignette applied to the 1080p frame
    vf_img = (
        "scale=1978:1112:flags=lanczos,crop=1920:1080,"
        "eq=contrast=1.08:saturation=1.15,"
        "colorbalance=rs=-0.04:gs=-0.01:bs=0.05:rh=0.05:gh=0.02:bh=-0.04,"
        "vignette=PI/5"
    )
    run_ffmpeg([
        ffmpeg_bin, "-y", "-threads", "1",
        "-ss", f"{frame_t:.3f}", "-i", str(src_video),
        "-frames:v", "1", "-q:v", "2", "-vf", vf_img,
        str(still_jpg), "-loglevel", "error",
    ])

    frames = max(1, int(round(render_dur * 30.0)))
    # Smooth Ken Burns motion (1.00 -> 1.09 zoom-in, zoom-out, or pan)
    if motion == "zoom_in":
        zp = f"zoompan=z='1.00+0.09*(on/{frames})':x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':d={frames}:s=1920x1080:fps=30"
    elif motion == "zoom_out":
        zp = f"zoompan=z='1.09-0.09*(on/{frames})':x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':d={frames}:s=1920x1080:fps=30"
    elif motion == "pan_right":
        zp = f"zoompan=z='1.08':x='(iw-iw/zoom)*(on/{frames})':y='ih/2-(ih/zoom/2)':d={frames}:s=1920x1080:fps=30"
    else:  # pan_left
        zp = f"zoompan=z='1.08':x='(iw-iw/zoom)*(1-on/{frames})':y='ih/2-(ih/zoom/2)':d={frames}:s=1920x1080:fps=30"

    vf_chain = [zp]
    if shock:
        # 3-frame white flash + micro-shake on shock/betrayal beats
        vf_chain.append(
            "scale=1956:1100:flags=bilinear,"
            "crop=1920:1080:"
            "'if(lt(n,10),(iw-1920)/2+14*sin(n*2.3),(iw-1920)/2)':"
            "'if(lt(n,10),(ih-1080)/2+9*cos(n*2.7),(ih-1080)/2)'"
        )
        vf_chain.append("drawbox=x=0:y=0:w=iw:h=ih:color=white@0.82:t=fill:enable='lt(n,3)'")
    vf_chain.extend(["fps=30", "format=yuv420p"])

    run_ffmpeg([
        ffmpeg_bin, "-y", "-threads", "1",
        "-i", str(still_jpg),
        "-vf", ",".join(vf_chain),
        "-t", f"{render_dur:.3f}",
        "-r", "30", "-video_track_timescale", "30000",
        "-c:v", "libx264", "-preset", "ultrafast", "-crf", "18",
        "-pix_fmt", "yuv420p", "-an",
        str(out_path), "-loglevel", "error",
    ])


def render_clip_beat(beat: dict, render_dur: float, out_path: Path, ffmpeg_bin: str) -> None:
    """Extract 2 muted micro-cuts (each <= 2.9s), apply 1.03x crop/scale, film grade, and shock FX."""
    src_video = ROOT / beat["source_video"]
    shots = beat["shots"]
    shock = beat["shock_flash_shake"]

    # Distribute any +0.20s xfade padding evenly across the 2 micro-cuts (still strictly <= 2.85s each!)
    extra = max(0.0, render_dur - beat["duration_sec"])
    d0 = round(shots[0]["duration_sec"] + extra * 0.5, 3)
    d1 = round(render_dur - d0, 3)
    t0 = shots[0]["source_start_sec"]
    t1 = shots[1]["source_start_sec"]

    # Grade at native 854x450 first for speed + cleaner highlights, then 1.03x scale/crop to 1920x1080
    grade_pre = (
        "eq=contrast=1.08:saturation=1.15,"
        "colorbalance=rs=-0.04:gs=-0.01:bs=0.05:rh=0.05:gh=0.02:bh=-0.04,"
        "vignette=PI/5"
    )
    if shock:
        scale_crop_0 = (
            "scale=1978:1112:flags=lanczos,"
            "crop=1920:1080:"
            "'if(lt(n,10),(iw-1920)/2+14*sin(n*2.3),(iw-1920)/2)':"
            "'if(lt(n,10),(ih-1080)/2+9*cos(n*2.7),(ih-1080)/2)',"
            "drawbox=x=0:y=0:w=iw:h=ih:color=white@0.82:t=fill:enable='lt(n,3)'"
        )
    else:
        scale_crop_0 = "scale=1978:1112:flags=lanczos,crop=1920:1080"
    scale_crop_1 = "scale=1978:1112:flags=lanczos,crop=1920:1080"

    fc = (
        f"[0:v]trim=duration={d0:.3f},setpts=PTS-STARTPTS,fps=30,{grade_pre},{scale_crop_0},format=yuv420p[v0];"
        f"[1:v]trim=duration={d1:.3f},setpts=PTS-STARTPTS,fps=30,{grade_pre},{scale_crop_1},format=yuv420p[v1];"
        f"[v0][v1]concat=n=2:v=1:a=0,fps=30,format=yuv420p[out]"
    )

    run_ffmpeg([
        ffmpeg_bin, "-y", "-threads", "1",
        "-ss", f"{t0:.3f}", "-t", f"{d0 + 0.15:.3f}", "-i", str(src_video),
        "-ss", f"{t1:.3f}", "-t", f"{d1 + 0.15:.3f}", "-i", str(src_video),
        "-filter_complex", fc,
        "-map", "[out]", "-an",
        "-t", f"{render_dur:.3f}",
        "-r", "30", "-video_track_timescale", "30000",
        "-c:v", "libx264", "-preset", "ultrafast", "-crf", "18",
        "-pix_fmt", "yuv420p",
        str(out_path), "-loglevel", "error",
    ])


def assemble_part(part_num: int, part_beats: list[dict], ffmpeg_bin: str) -> Path:
    """Render all 11 beats of a 1-minute part and join them with xfade + sharp cuts to EXACTLY 60.00s."""
    t_start = time.time()
    beat_files = []
    render_durs = []

    jobs = []
    for idx, b in enumerate(part_beats):
        pad = b["xfade_duration_sec"] if (idx > 0 and b["transition_in"] != "cut") else 0.0
        rdur = round(b["duration_sec"] + pad, 3)
        bp = WORK_DIR / f"beat_{b['beat_id']:03d}.mp4"
        beat_files.append(bp)
        render_durs.append(rdur)
        jobs.append((b, rdur, bp))

    def _worker(job):
        b, rdur, bp = job
        if b["visual_mode"] == "still":
            render_still_beat(b, rdur, bp, ffmpeg_bin)
        else:
            render_clip_beat(b, rdur, bp, ffmpeg_bin)

    with ThreadPoolExecutor(max_workers=2) as pool:
        list(pool.map(_worker, jobs))

    # Build compact 11-input filter_complex mixing 0.20s xfade transitions and sharp cuts
    inputs = []
    for bp in beat_files:
        inputs.extend(["-i", str(bp)])

    filters = []
    for i in range(len(beat_files)):
        filters.append(f"[{i}:v]fps=30,settb=1/30000,setpts=PTS-STARTPTS,format=yuv420p[b{i}]")

    cur_label = "b0"
    cur_len = render_durs[0]
    for i in range(1, len(beat_files)):
        b = part_beats[i]
        nxt_label = f"m{i}"
        if b["transition_in"] != "cut" and b["xfade_duration_sec"] > 0:
            xd = b["xfade_duration_sec"]
            offset = round(cur_len - xd, 3)
            trans = b["transition_in"]
            filters.append(
                f"[{cur_label}][b{i}]xfade=transition={trans}:duration={xd:.3f}:offset={offset:.3f},settb=1/30000[{nxt_label}]"
            )
            cur_len = round(offset + render_durs[i], 3)
        else:
            filters.append(f"[{cur_label}][b{i}]concat=n=2:v=1:a=0,fps=30,settb=1/30000[{nxt_label}]")
            cur_len = round(cur_len + render_durs[i], 3)
        cur_label = nxt_label

    filters.append(f"[{cur_label}]fps=30,trim=duration=60.000,setpts=PTS-STARTPTS,format=yuv420p[vout]")

    part_out = WORK_DIR / f"part_render_{part_num}.mp4"
    # Bitrate calibrated so 480s video + 128k audio stays strictly under 85 MB (~68-74 MB target)
    run_ffmpeg([
        ffmpeg_bin, "-y",
        *inputs,
        "-filter_complex", ";".join(filters),
        "-map", "[vout]", "-an",
        "-t", "60.000", "-r", "30", "-video_track_timescale", "30000",
        "-c:v", "libx264", "-preset", "fast",
        "-b:v", "1050k", "-maxrate", "1450k", "-bufsize", "2900k",
        "-g", "60", "-pix_fmt", "yuv420p",
        str(part_out), "-loglevel", "error",
    ])

    # Remove intermediate beat clips to keep /tmp tidy
    for bp in beat_files:
        bp.unlink(missing_ok=True)

    print(
        f"  Part {part_num}/8 rendered ({cur_len:.2f}s -> 60.00s, {part_out.stat().st_size / 1e6:.2f} MB) "
        f"in {time.time() - t_start:.1f}s",
        flush=True,
    )
    return part_out


def load_wav_stereo_f32(path: Path) -> np.ndarray:
    sr, data = wavfile.read(str(path))
    assert sr == SR, f"Expected {SR}Hz for {path}, got {sr}"
    arr = data.astype(np.float32) / 32768.0
    if arr.ndim == 1:
        arr = np.column_stack([arr, arr])
    return arr


def build_premixed_audio(beats: list[dict], ffmpeg_bin: str) -> Path:
    """Sample-accurate 48kHz stereo pre-mix of bg_ambient_bed (-29dB) + all SFX cues."""
    t0 = time.time()
    # Decode bg_ambient_bed.mp3 to raw 48kHz stereo WAV in /tmp
    bed_wav = WORK_DIR / "bed_48k.wav"
    run_ffmpeg([
        ffmpeg_bin, "-y", "-i", str(SFX_DIR / "bg_ambient_bed.mp3"),
        "-ar", str(SR), "-ac", "2", "-t", f"{TOTAL_DUR:.3f}",
        "-c:a", "pcm_s16le", str(bed_wav), "-loglevel", "error",
    ])
    bed = load_wav_stereo_f32(bed_wav)
    n_total = int(TOTAL_DUR * SR)
    mix = np.zeros((n_total, 2), dtype=np.float32)
    n_copy = min(len(bed), n_total)
    mix[:n_copy] = bed[:n_copy]

    sfx_bank = {
        "whoosh": load_wav_stereo_f32(SFX_DIR / "whoosh.wav"),
        "bass_hit": load_wav_stereo_f32(SFX_DIR / "bass_hit.wav"),
        "riser": load_wav_stereo_f32(SFX_DIR / "riser.wav"),
        "heartbeat": load_wav_stereo_f32(SFX_DIR / "heartbeat.wav"),
    }

    # Gain scaling relative to full-scale SFX assets so narration sits cleanly above later
    gains = {
        "whoosh": 10.0 ** (-12.0 / 20.0),
        "bass_hit": 10.0 ** (-6.5 / 20.0),
        "riser": 10.0 ** (-11.0 / 20.0),
        "heartbeat": 10.0 ** (-10.0 / 20.0),
    }

    def add_sfx(kind: str, start_sec: float, gain_mult: float = 1.0) -> None:
        clip = sfx_bank[kind] * (gains[kind] * gain_mult)
        idx = int(round(start_sec * SR))
        if idx < 0:
            clip = clip[-idx:]
            idx = 0
        if idx >= n_total or len(clip) == 0:
            return
        end = min(idx + len(clip), n_total)
        mix[idx:end] += clip[: end - idx]

    placed = 0
    for b in beats:
        cue = b["sfx_cue"]
        if not cue:
            continue
        ts = b["timeline_start_sec"]
        te = b["timeline_end_sec"]
        if cue == "whoosh":
            # Peak right on the transition into the still frame
            add_sfx("whoosh", max(0.0, ts - 0.16))
            placed += 1
        elif cue == "bass_hit":
            add_sfx("bass_hit", ts)
            placed += 1
        elif cue == "riser":
            # Swell finishes right at the end of the beat leading into the next impact
            add_sfx("riser", max(0.0, te - 1.48))
            placed += 1
        elif cue == "heartbeat":
            add_sfx("heartbeat", ts + 0.15)
            add_sfx("heartbeat", ts + 1.55, gain_mult=0.80)
            placed += 2

    # Smooth soft limiter to prevent any clipping on stacked hits
    mix = np.tanh(mix * 1.05) / 1.05
    # 1.5s fade-out at very end of 480s
    fo = int(1.5 * SR)
    mix[-fo:] *= np.linspace(1.0, 0.0, fo, dtype=np.float32)[:, None]

    mix_wav = WORK_DIR / "master_sfx_mix.wav"
    wavfile.write(str(mix_wav), SR, np.clip(mix * 32767.0, -32768, 32767).astype(np.int16))

    mix_m4a = WORK_DIR / "master_sfx_mix.m4a"
    run_ffmpeg([
        ffmpeg_bin, "-y", "-i", str(mix_wav),
        "-c:a", "aac", "-b:a", "128k", "-ar", str(SR), "-ac", "2",
        str(mix_m4a), "-loglevel", "error",
    ])
    bed_wav.unlink(missing_ok=True)
    mix_wav.unlink(missing_ok=True)
    print(
        f"Pre-mixed audio ({placed} SFX hits + -29dB bed -> {mix_m4a.stat().st_size / 1e6:.2f} MB) "
        f"in {time.time() - t0:.1f}s",
        flush=True,
    )
    return mix_m4a


def main():
    t_all = time.time()
    WORK_DIR.mkdir(parents=True, exist_ok=True)
    ffmpeg_bin = find_ffmpeg()

    timeline = json.loads((ROOT / "visual_timeline_8min.json").read_text(encoding="utf-8"))
    beats = timeline["beats"]
    assert len(beats) == 88

    print("Rendering 8 x 1-minute visual parts (1080p 30fps)...", flush=True)
    part_files = []
    for p in range(1, 9):
        p_beats = [b for b in beats if b["part_number"] == p]
        pf = assemble_part(p, p_beats, ffmpeg_bin)
        part_files.append(pf)

    # Pre-mix audio bed + SFX
    audio_m4a = build_premixed_audio(beats, ffmpeg_bin)

    # Concatenate all 8 parts cleanly (stream-copy video) + mux SFX audio
    concat_txt = WORK_DIR / "parts_concat.txt"
    concat_txt.write_text(
        "\n".join(f"file '{pf.as_posix()}'" for pf in part_files) + "\n",
        encoding="utf-8",
    )

    final_out = ROOT / "visual_master_sfx.mp4"
    run_ffmpeg([
        ffmpeg_bin, "-y",
        "-f", "concat", "-safe", "0", "-i", str(concat_txt),
        "-i", str(audio_m4a),
        "-map", "0:v:0", "-map", "1:a:0",
        "-c:v", "copy", "-c:a", "copy",
        "-shortest", "-movflags", "+faststart",
        str(final_out), "-loglevel", "error",
    ])

    size_mb = final_out.stat().st_size / (1024 * 1024)
    print(f"\nRendered {final_out.name}: {size_mb:.2f} MB in {time.time() - t_all:.1f}s", flush=True)
    assert size_mb < 85.0, f"Output {size_mb:.2f} MB exceeds 85 MB limit!"


if __name__ == "__main__":
    main()
