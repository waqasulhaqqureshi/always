#!/usr/bin/env python3
"""
Phase 4A: Build the 88-Beat Story-Synced Visual Timeline (visual_timeline_8min.json)
  - 8 parts x 11 beats = 88 beats, totaling EXACTLY 480.00 seconds (8 minutes)
  - Strictly alternating visual_mode: "clip" <-> "still"
  - Every "clip" beat split into 2 micro-cuts (2.70s - 2.75s max per shot) for YouTube Content ID safety
  - Every "still" beat paired with Ken Burns zoompan motion (1.00 -> 1.09)
  - Synced to actual scenes from scenes_index.json and dialogue from transcripts
  - Full SFX cue sheet (whoosh, bass_hit, riser, heartbeat) + shock_flash_shake flags + xfade mix
"""

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent

# Per-part duration pattern: 6 x 5.5s + 5 x 5.4s = 60.00s EXACTLY
BEAT_DURS = [5.5, 5.4, 5.5, 5.4, 5.5, 5.4, 5.5, 5.4, 5.5, 5.4, 5.5]
KEN_BURNS_CYCLE = ["zoom_in", "zoom_out", "pan_right", "pan_left"]
XFADE_CYCLE = ["fade", "smoothleft", "zoomin"]

# 88 story-mapped beats: (part_num, source_part, win_start, win_end, shock, sfx_override, transition_hint, story_beat)
STORY_SPEC = [
    # ==================== PART 1 (00:00 - 01:00): HOOK + OPENING + PRISON WALK ====================
    (1, "part1", 282, 296, False, "riser", "cut", "Hook: Woman in black praying for a vow fast"),
    (1, "part1", 450, 476, True, "bass_hit", "fade", "Hook: Billo in black holding tasbeeh awaiting vengeance"),
    (1, "part1", 190, 225, False, None, "cut", "Hook: Baala walking out as prisoners cheer him like a king"),
    (1, "part1", 510, 545, True, "bass_hit", "zoomin", "Hook: Kalashnikov assassins ambush Baala at the graveyard"),
    (1, "part1", 660, 705, False, "heartbeat", "cut", "Hook: Blood spilled in the dust — who is she and what is the score?"),
    (1, "part1", 20, 42, False, "whoosh", "fade", "Intro: Punjab's fertile soil of historic shrines"),
    (1, "part1", 44, 72, False, None, "cut", "Intro: Village arrival — love and hatred run equally deep"),
    (1, "part1", 72, 102, False, "whoosh", "smoothleft", "Intro: Mysterious black silhouette inside the vintage car"),
    (1, "part1", 118, 155, False, "riser", "cut", "1999: Gloomy prison corridor opens the story"),
    (1, "part1", 160, 190, False, "whoosh", "fade", "1999: Iqbal Channan alias Baala walking in stark black"),
    (1, "part1", 195, 232, True, "bass_hit", "cut", "Reveal: Inmates slamming bars and saluting Baala"),

    # ==================== PART 2 (01:00 - 02:00): BILLO'S VOW FAST & GRAVEYARD WALK ====================
    (2, "part1", 232, 260, False, "whoosh", "fade", "Prisoners chanting for Baala like a returning hero"),
    (2, "part1", 262, 294, False, "heartbeat", "cut", "Parallel cut: Bilqees Bano (Billo) draped in black praying"),
    (2, "part1", 286, 300, False, "whoosh", "zoomin", "Close-up: Billo raising her hands in intense prayer"),
    (2, "part1", 308, 336, False, None, "cut", "Heavy iron prison gates sliding open to daylight"),
    (2, "part1", 336, 366, False, "whoosh", "smoothleft", "Baala stepping free into his loyal supporters' embrace"),
    (2, "part1", 354, 384, False, None, "cut", "Younger brother Jooji hugging Baala with joy"),
    (2, "part1", 384, 412, False, "whoosh", "fade", "Graveyard arrival: Baala pouring water on his family grave"),
    (2, "part1", 412, 444, False, "heartbeat", "cut", "Baala standing solemn among the graves in quiet prayer"),
    (2, "part1", 446, 474, False, "whoosh", "fade", "Shrine interior: Billo refusing food with cold composure"),
    (2, "part1", 468, 496, False, "riser", "cut", "Billo declares her vow fast will only break when fulfilled"),
    (2, "part1", 476, 502, True, "bass_hit", "zoomin", "Tense close-up of Baala praying right before danger strikes"),

    # ==================== PART 3 (02:00 - 03:00): GRAVEYARD AMBUSH & BLOODY FALL ====================
    (3, "part1", 502, 526, True, "bass_hit", "cut", "Assassins emerge behind gravestones aiming Kalashnikovs"),
    (3, "part1", 522, 545, False, "whoosh", "smoothleft", "Baala spotting the ambush — silence shatters"),
    (3, "part1", 545, 578, True, "bass_hit", "cut", "Baala screaming at Jooji to run as Jooji refuses to leave"),
    (3, "part1", 580, 614, False, "whoosh", "zoomin", "Gunfire tearing across the cemetery"),
    (3, "part1", 614, 650, False, "heartbeat", "cut", "Parallel cut: Billo standing stone-cold outside the white shrine"),
    (3, "part1", 642, 665, False, "whoosh", "fade", "Billo's unblinking gaze sensing destiny unfold"),
    (3, "part1", 666, 692, True, "bass_hit", "cut", "Jooji gunned down, collapsing bloodied by a gravestone"),
    (3, "part1", 688, 718, False, "whoosh", "zoomin", "Baala struck by bullets crashing into the dust"),
    (3, "part1", 718, 756, False, "heartbeat", "cut", "Baala lying wounded as silence returns to the graveyard"),
    (3, "part1", 760, 795, False, "whoosh", "fade", "Back at the shrine: Billo standing tall in black"),
    (3, "part1", 796, 830, True, "bass_hit", "fade", "Chilling calm: Billo closing her eyes as her vow completes"),

    # ==================== PART 4 (03:00 - 04:00): FLASHBACK TO PEACEFUL SHOPKEEPER ====================
    (4, "part1", 834, 862, False, "riser", "fade", "Overhead shot of graveyard rewinding years into the past"),
    (4, "part1", 862, 892, False, "whoosh", "smoothleft", "Time shift: Years before prison, guns, and bloodshed"),
    (4, "part1", 886, 912, False, None, "cut", "Younger carefree Jooji riding his motorcycle through town"),
    (4, "part1", 906, 932, False, "whoosh", "fade", "Respectable Iqbal Channan before he became the feared Baala"),
    (4, "part1", 928, 958, False, None, "cut", "At home: Devoted wife Zareena speaking to Iqbal"),
    (4, "part2", 0, 15, False, "whoosh", "fade", "Zareena reminding Iqbal of the four-tola gold bangles promise"),
    (4, "part1", 936, 956, False, None, "cut", "Iqbal explaining Kausar's wedding comes first"),
    (4, "part2", 2, 16, False, "whoosh", "smoothleft", "Zareena reacting gently to Iqbal's devotion to his siblings"),
    (4, "part1", 914, 936, False, "heartbeat", "cut", "Iqbal insisting he is both mother and father to his siblings"),
    (4, "part2", 18, 34, False, "whoosh", "fade", "Transition to Iqbal's honest livelihood at the fabric shop"),
    (4, "part2", 22, 42, False, None, "cut", "Busy cloth shop where Iqbal built his life from scratch"),

    # ==================== PART 5 (04:00 - 05:00): CLOTH SHOP CONFRONTATION ====================
    (5, "part2", 28, 48, False, "riser", "cut", "Extortionists barging into the cloth shop demanding cash"),
    (5, "part2", 38, 56, True, "bass_hit", "zoomin", "Hot-blooded Jooji exploding at the street thugs"),
    (5, "part2", 46, 66, False, None, "cut", "Heated argument escalating almost to a physical brawl"),
    (5, "part2", 56, 76, False, "whoosh", "smoothleft", "Iqbal stepping calmly between Jooji and the thugs"),
    (5, "part2", 64, 84, False, None, "cut", "Iqbal greeting the gang elder with quiet diplomacy"),
    (5, "part2", 74, 92, False, "whoosh", "fade", "Jooji fuming after the thugs leave"),
    (5, "part2", 84, 102, False, None, "cut", "Jooji protesting why his brother scolded him"),
    (5, "part2", 92, 110, False, "whoosh", "fade", "Iqbal warning: We are here to trade, not play gangsters"),
    (5, "part2", 98, 118, False, "heartbeat", "cut", "Kausar's wedding and next year's Hajj — no enemies allowed"),
    (5, "part2", 104, 120, False, "riser", "zoomin", "Dramatic irony: The peaceful shopkeeper fated for war"),
    (5, "part2", 118, 144, False, None, "cut", "Neighborhood lanes buzzing as everyday life shifts"),

    # ==================== PART 6 (05:00 - 06:00): WADDE SARKAR & HAUNTED PAST ====================
    (6, "part2", 142, 166, False, "whoosh", "smoothleft", "Women chatting in the lane as commotion builds"),
    (6, "part2", 164, 186, False, None, "cut", "Convoy of white SUVs arriving at the wealthy Shah haveli"),
    (6, "part2", 174, 198, False, "whoosh", "fade", "Word spreads: Saint Wadde Sarkar has visited the Shahs"),
    (6, "part2", 198, 232, False, None, "cut", "Inside Iqbal's home: Family rushing as Iqbal returns"),
    (6, "part2", 232, 260, False, "whoosh", "fade", "Iqbal displeased catching young son Ibrahim playing music"),
    (6, "part2", 260, 294, False, None, "cut", "Haunted by society's stigma of his family's old bhaand past"),
    (6, "part2", 294, 326, False, "whoosh", "smoothleft", "Zareena laughing that Ibrahim is stubborn like Jooji"),
    (6, "part2", 326, 356, False, "heartbeat", "cut", "Zareena wishing she took Ibrahim to Wadde Sarkar for a blessing"),
    (6, "part2", 358, 384, False, "whoosh", "fade", "Inside Shah haveli: Elder Wadde Sarkar in black turban"),
    (6, "part2", 384, 412, False, "riser", "cut", "Wadde Sarkar praising the Shahs' devout new daughter-in-law"),
    (6, "part2", 440, 468, False, "whoosh", "zoomin", "Warning: Heavy trials await those walking the spiritual path"),

    # ==================== PART 7 (06:00 - 07:00): THE BOMBSHELL NAME & GLIMPSE IN WHITE ====================
    (7, "part2", 398, 424, False, None, "cut", "Back in Iqbal's courtyard: Zareena sharing neighborhood news"),
    (7, "part2", 412, 434, True, "bass_hit", "zoomin", "BOMBSHELL: Zareena speaks the name Bilqees Bano from Wazirabad"),
    (7, "part2", 422, 444, False, "heartbeat", "cut", "Iqbal freezes completely, leaving his meal untouched"),
    (7, "part2", 434, 456, False, "whoosh", "fade", "Zareena watching in bewildered silence as Iqbal walks out"),
    (7, "part2", 478, 514, False, None, "cut", "Shaken to his core, Iqbal wanders the narrow old-city lanes"),
    (7, "part2", 514, 548, False, "whoosh", "smoothleft", "Echoes of Bilqees's name haunting every footstep"),
    (7, "part2", 548, 582, False, "riser", "cut", "Ahead in the quiet alley: A woman draped in pure white"),
    (7, "part2", 582, 608, True, "bass_hit", "zoomin", "Figure in white stepping inside the Shah mansion gate"),
    (7, "part2", 608, 636, False, "heartbeat", "cut", "Iqbal standing frozen in the street staring upward"),
    (7, "part2", 636, 668, False, "whoosh", "fade", "Inside the sunlit room: Bilqees adjusting her white dupatta"),
    (7, "part2", 668, 698, False, "heartbeat", "cut", "Silent distance between two souls separated by fate"),

    # ==================== PART 8 (07:00 - 08:00): ANNIVERSARY TWIST & CLIFFHANGER ====================
    (8, "part2", 700, 722, False, "riser", "fade", "Inside Shah dining room: Husband Nazeer Shah sitting grim"),
    (8, "part2", 718, 738, True, "bass_hit", "zoomin", "TWIST: Tomorrow's wedding anniversary is Bilqees's brother's barsi"),
    (8, "part2", 726, 744, False, "heartbeat", "cut", "Nazeer Shah's chilling words connect love, honor, and blood"),
    (8, "part2", 744, 766, False, "whoosh", "fade", "Night falls over the silent courtyard as Iqbal returns home"),
    (8, "part2", 764, 792, False, None, "cut", "Iqbal looking quietly at sleeping Zareena and his child"),
    (8, "part2", 792, 816, False, "whoosh", "smoothleft", "Restless storm outside as Iqbal steps onto the dark balcony"),
    (8, "part2", 814, 840, False, "heartbeat", "cut", "Lonely silhouette in the dark night haunted by memories"),
    (8, "part2", 840, 864, False, "whoosh", "fade", "Flashback memory: Young Billo and Baala from Wazirabad"),
    (8, "part2", 864, 892, False, "riser", "cut", "Innocent smiles of youth shattered by pride and tragedy"),
    (8, "part2", 892, 926, True, "bass_hit", "zoomin", "Burning eyes of Baala — the quiet love turns to fire"),
    (8, "part2", 926, 956, True, "bass_hit", "fade", "Cliffhanger: Ghostly Billo in white beside Baala's tormented gaze"),
]


def pick_best_scenes(scenes_by_part: dict, part_key: str, win_start: float, win_end: float) -> list[dict]:
    """Return usable scenes overlapping [win_start, win_end], ranked by brightness & sharpness."""
    pool = scenes_by_part[part_key]
    matches = [
        s for s in pool
        if s["end_sec"] > win_start and s["start_sec"] < win_end and s["brightness"] >= 22.0
    ]
    if not matches:
        # Fallback to nearest scenes to midpoint
        mid = 0.5 * (win_start + win_end)
        matches = sorted(pool, key=lambda s: abs(s["mid_sec"] - mid))[:4]
    return matches


def clamp_time(t: float, max_dur: float) -> float:
    return round(max(0.2, min(t, max_dur - 3.2)), 3)


def main():
    assert len(STORY_SPEC) == 88, f"Expected 88 beats, got {len(STORY_SPEC)}"

    scenes_data = json.loads((ROOT / "scenes_index.json").read_text(encoding="utf-8"))
    meta = json.loads((ROOT / "video_metadata.json").read_text(encoding="utf-8"))
    dur_map = {p["part"]: p["duration_sec"] for p in meta["parts"]}
    file_map = {p["part"]: p["filename"] for p in meta["parts"]}

    scenes_by_part = {"part1": [], "part2": []}
    for s in scenes_data["scenes"]:
        scenes_by_part[s["part"]].append(s)

    beats = []
    cur_t = 0.0
    kb_idx = 0
    xf_idx = 0

    for idx, spec in enumerate(STORY_SPEC):
        part_num, src_part, win_s, win_e, shock, sfx_override, trans_hint, story_beat = spec
        in_part_idx = idx % 11
        dur = BEAT_DURS[in_part_idx]

        # Strictly alternating visual_mode across all 88 beats: even=clip, odd=still
        visual_mode = "clip" if (idx % 2 == 0) else "still"

        max_dur = dur_map[src_part]
        src_file = file_map[src_part]
        cands = pick_best_scenes(scenes_by_part, src_part, win_s, win_e)

        # Build shots / still frame
        if visual_mode == "clip":
            # Split into 2 distinct micro-cuts, strictly 2.70s or 2.75s max each (<= 3.0s Content ID safe!)
            half_a = round(dur / 2.0, 3)
            half_b = round(dur - half_a, 3)
            assert 2.5 <= half_a <= 3.0 and 2.5 <= half_b <= 3.0

            if len(cands) >= 2:
                s1 = cands[0]
                s2 = cands[min(len(cands) - 1, max(1, len(cands) // 2))]
                t1 = clamp_time(max(win_s, s1["start_sec"] + 0.15), max_dur)
                t2 = clamp_time(max(win_s + 3.0, s2["start_sec"] + 0.15), max_dur)
                if abs(t2 - t1) < 3.2:
                    t2 = clamp_time(t1 + 4.2, max_dur)
            else:
                t1 = clamp_time(win_s + 0.5, max_dur)
                t2 = clamp_time(min(win_e - 3.0, win_s + max(4.0, (win_e - win_s) * 0.55)), max_dur)

            shots = [
                {"source_start_sec": t1, "duration_sec": half_a, "mute_audio": True},
                {"source_start_sec": t2, "duration_sec": half_b, "mute_audio": True},
            ]
            still_info = None
        else:
            # Pick sharpest candidate near window center for crisp 1080p Ken Burns still
            best = max(cands, key=lambda s: s["sharpness"] * (1.2 if s["brightness"] > 45 else 0.8))
            frame_t = clamp_time(max(win_s, min(win_e, best["mid_sec"])), max_dur)
            kb_motion = KEN_BURNS_CYCLE[kb_idx % len(KEN_BURNS_CYCLE)]
            kb_idx += 1
            shots = []
            still_info = {
                "frame_timestamp_sec": frame_t,
                "ken_burns_motion": kb_motion,
                "zoom_range": [1.00, 1.09],
            }

        # Transition selection: first beat of each part is clean cut; mix xfade (0.20s) and sharp cuts inside parts
        if in_part_idx == 0:
            transition_in = "cut"
            xfade_dur = 0.0
        elif trans_hint in {"fade", "smoothleft", "zoomin"}:
            transition_in = trans_hint
            xfade_dur = 0.20
        elif in_part_idx % 2 == 1:
            transition_in = XFADE_CYCLE[xf_idx % len(XFADE_CYCLE)]
            xf_idx += 1
            xfade_dur = 0.20
        else:
            transition_in = "cut"
            xfade_dur = 0.0

        # SFX assignment: guarantee whoosh into stills unless a stronger cue is explicitly set
        if sfx_override is not None:
            sfx_cue = sfx_override
        elif visual_mode == "still":
            sfx_cue = "whoosh"
        else:
            sfx_cue = None

        beat = {
            "beat_id": idx + 1,
            "part_number": part_num,
            "timeline_start_sec": round(cur_t, 3),
            "timeline_end_sec": round(cur_t + dur, 3),
            "duration_sec": dur,
            "visual_mode": visual_mode,
            "source_part": src_part,
            "source_video": src_file,
            "shots": shots,
            "still": still_info,
            "transition_in": transition_in,
            "xfade_duration_sec": xfade_dur,
            "shock_flash_shake": bool(shock),
            "sfx_cue": sfx_cue,
            "story_beat": story_beat,
        }
        beats.append(beat)
        cur_t = round(cur_t + dur, 3)

    # Strict timeline integrity checks
    assert abs(cur_t - 480.0) < 1e-6, f"Timeline must total 480.0s, got {cur_t}"
    for i in range(1, len(beats)):
        assert beats[i]["visual_mode"] != beats[i - 1]["visual_mode"], (
            f"Beat {i+1} did not strictly alternate visual_mode!"
        )
    for b in beats:
        if b["visual_mode"] == "clip":
            for sh in b["shots"]:
                assert sh["duration_sec"] <= 3.0, f"Beat {b['beat_id']} shot exceeds 3.0s max!"

    payload = {
        "title": "Mitti De Baway Episode 1 - 8-Minute @film.feel.50 Visual Timeline",
        "total_beats": len(beats),
        "beats_per_part": 11,
        "total_duration_sec": 480.0,
        "output_spec": {
            "resolution": "1920x1080",
            "fps": 30,
            "color_grade": "1.03x crop/scale, eq=contrast=1.08:saturation=1.15, warm highlights + cool shadows, subtle vignette",
            "max_continuous_clip_sec": 2.75,
            "ambient_bed_db": -29.0,
            "max_file_size_mb": 85.0,
        },
        "summary_counts": {
            "clip_beats": sum(1 for b in beats if b["visual_mode"] == "clip"),
            "still_beats": sum(1 for b in beats if b["visual_mode"] == "still"),
            "shock_flash_shake_beats": sum(1 for b in beats if b["shock_flash_shake"]),
            "xfade_transitions": sum(1 for b in beats if b["transition_in"] != "cut"),
            "sfx_whoosh": sum(1 for b in beats if b["sfx_cue"] == "whoosh"),
            "sfx_bass_hit": sum(1 for b in beats if b["sfx_cue"] == "bass_hit"),
            "sfx_riser": sum(1 for b in beats if b["sfx_cue"] == "riser"),
            "sfx_heartbeat": sum(1 for b in beats if b["sfx_cue"] == "heartbeat"),
        },
        "beats": beats,
    }

    out_path = ROOT / "visual_timeline_8min.json"
    out_path.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(f"Saved {out_path.name}")
    print("Summary:", json.dumps(payload["summary_counts"], indent=2))


if __name__ == "__main__":
    main()
