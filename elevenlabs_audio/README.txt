========================================================================
  ELEVENLABS VOICEOVER DROP FOLDER — MITTI DE BAWAY (8-MINUTE RECAP)
========================================================================

HOW TO GENERATE YOUR FINAL YOUTUBE VIDEO IN 3 STEPS:

STEP 1: Generate 8 Voiceover Clips in ElevenLabs
  - Open either:
      * script_roman_urdu_hindi.txt  (Roman Urdu / Hindi)
      * script_roman_arabic.txt      (Roman Arabic - Egyptian/White)
  - Copy each labeled 1-minute part (PART 1 through PART 8) into ElevenLabs
    (do NOT paste the "--- PART X ---" header line; paste only the spoken text).
  - Download each generated audio clip as MP3 and save them inside THIS folder
    (`elevenlabs_audio/`) with these exact filenames:

      part1.mp3
      part2.mp3
      part3.mp3
      part4.mp3
      part5.mp3
      part6.mp3
      part7.mp3
      part8.mp3

STEP 2: Run the One-Click Merger
  - Go back to the main repository folder and double-click:
      merge_audio.bat
  - (Or run in PowerShell: python merge_elevenlabs_audio.py)

STEP 3: Upload!
  - In a few seconds, `FINAL_YOUTUBE_VIDEO.mp4` (1080p, 30fps, YouTube-normalized
    voiceover + auto-ducked cinematic SFX & ambient bed) will be ready in the
    main folder!

REQUIREMENTS ON WINDOWS:
  - Python 3.9+ (python.org or Microsoft Store)
  - FFmpeg installed and on PATH (e.g. `winget install Gyan.FFmpeg`)
========================================================================
