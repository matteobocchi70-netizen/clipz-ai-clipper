import os
import re
import glob
import json
import math
import subprocess
import streamlit as st
import yt_dlp
from yt_dlp.utils import download_range_func
from groq import Groq

st.set_page_config(page_title="VIRAL//AI CLIPPER — Auto-Clipper Pro", layout="wide")
client = Groq(api_key=st.secrets["GROQ_API_KEY"])


def prepare_cookie_file():
    if "YT_COOKIES" not in st.secrets:
        return None, 0
    raw_text = str(st.secrets["YT_COOKIES"]).strip()
    if not raw_text:
        return None, 0

    cookie_path = "cookies.txt"
    fixed_lines = []
    entry_count = 0

    for line in raw_text.splitlines():
        s_line = line.strip()
        if not s_line:
            continue
        if s_line.startswith("#") and not s_line.startswith("#HttpOnly_"):
            fixed_lines.append(s_line)
        elif "\t" in s_line:
            fixed_lines.append(s_line)
            entry_count += 1
        else:
            parts = re.split(r"\s+", s_line, maxsplit=6)
            if len(parts) >= 7:
                fixed_lines.append("\t".join(parts))
                entry_count += 1
            else:
                fixed_lines.append(s_line)

    if not fixed_lines or entry_count == 0:
        return None, 0

    with open(cookie_path, "w", encoding="utf-8") as cf:
        cf.write("\n".join(fixed_lines) + "\n")
    return cookie_path, entry_count


COOKIE_FILE, COOKIE_ENTRIES = prepare_cookie_file()
cookie_status = f"YT AUTH: ACTIVE ({COOKIE_ENTRIES}c)" if COOKIE_FILE else "YT AUTH: OFF"

st.markdown(f"""
<style>
@import url('https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@400;600;700;800&display=swap');

html, body, [class*="css"], .stApp {{
    background-color: #090b0e !important;
    color: #e6edf3 !important;
    font-family: 'JetBrains Mono', monospace !important;
}}

header[data-testid="stHeader"], footer, #MainMenu {{
    visibility: hidden !important;
    height: 0px !important;
}}
.block-container {{
    padding-top: 1.2rem !important;
    max-width: 1280px !important;
}}

.finder-topbar {{
    display: flex;
    justify-content: space-between;
    align-items: center;
    background-color: #0d1015;
    border: 1px solid #1f2630;
    border-radius: 6px;
    padding: 12px 18px;
    margin-bottom: 18px;
}}
.finder-brand {{
    display: flex;
    align-items: center;
    gap: 12px;
    font-weight: 800;
    font-size: 16px;
    letter-spacing: 0.5px;
    color: #ffffff;
}}
.dot-red {{
    height: 9px;
    width: 9px;
    background-color: #ff4b4b;
    border-radius: 50%;
    display: inline-block;
    box-shadow: 0 0 8px #ff4b4b;
}}
.badge-green {{
    background-color: rgba(0, 230, 118, 0.14);
    color: #00e676;
    border: 1px solid #00e676;
    padding: 3px 9px;
    border-radius: 4px;
    font-size: 11px;
    font-weight: 700;
}}
.badge-muted {{
    color: #7d8590;
    font-size: 12px;
}}

.stTextInput > div > div > input, .stSelectbox > div > div {{
    background-color: #11151c !important;
    color: #e6edf3 !important;
    border: 1px solid #262e3a !important;
    border-radius: 6px !important;
    font-family: 'JetBrains Mono', monospace !important;
    font-size: 13px !important;
}}
.stTextInput > div > div > input:focus {{
    border-color: #00e676 !important;
    box-shadow: 0 0 0 1px #00e676 !important;
}}
label {{
    color: #8b949e !important;
    font-size: 12px !important;
    text-transform: uppercase;
    letter-spacing: 0.5px;
}}

.stButton > button[kind="primary"] {{
    background-color: #00e676 !important;
    color: #050709 !important;
    border: none !important;
    border-radius: 6px !important;
    font-family: 'JetBrains Mono', monospace !important;
    font-weight: 800 !important;
    font-size: 13px !important;
    padding: 0.6rem 1.2rem !important;
    text-transform: uppercase;
    letter-spacing: 0.5px;
    transition: all 0.15s ease;
    width: 100%;
}}
.stButton > button[kind="primary"]:hover {{
    background-color: #00c865 !important;
    box-shadow: 0 0 14px rgba(0, 230, 118, 0.45);
}}

.stDownloadButton > button {{
    background-color: #131820 !important;
    color: #00e676 !important;
    border: 1px solid #00e676 !important;
    border-radius: 6px !important;
    font-family: 'JetBrains Mono', monospace !important;
    font-weight: 700 !important;
    width: 100%;
}}
.stDownloadButton > button:hover {{
    background-color: rgba(0, 230, 118, 0.12) !important;
}}

.clip-card {{
    background-color: #0e1218;
    border: 1px solid #1e2530;
    border-radius: 8px;
    padding: 18px;
    margin-bottom: 14px;
}}
.clip-header {{
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 12px;
}}
.score-ring {{
    border: 2px solid #00e676;
    color: #00e676;
    background: rgba(0, 230, 118, 0.08);
    border-radius: 50%;
    width: 46px;
    height: 46px;
    display: flex;
    align-items: center;
    justify-content: center;
    font-weight: 800;
    font-size: 16px;
}}
.tag-pill {{
    display: inline-block;
    background: #161b22;
    border: 1px solid #2b333e;
    color: #58a6ff;
    padding: 2px 8px;
    border-radius: 4px;
    font-size: 11px;
    font-weight: 700;
    margin-right: 6px;
}}
</style>

<div class="finder-topbar">
    <div class="finder-brand">
        <span class="dot-red"></span>
        <span>VIRAL//AI CLIPPER</span>
        <span class="badge-green">ENGINE: WHISPER + LLAMA-3</span>
        <span class="badge-muted">9:16 AUTO-CROP · {cookie_status}</span>
    </div>
    <div>
        <span class="badge-green">AUTO-CLIPPER PRO</span>
    </div>
</div>
""", unsafe_allow_html=True)


def format_srt_time(seconds):
    hrs = int(seconds // 3600)
    mins = int((seconds % 3600) // 60)
    secs = int(seconds % 60)
    millis = int((seconds - int(seconds)) * 1000)
    return f"{hrs:02d}:{mins:02d}:{secs:02d},{millis:03d}"


def format_clock(seconds):
    hrs = int(seconds // 3600)
    mins = int((seconds % 3600) // 60)
    secs = int(seconds % 60)
    return f"{hrs:02d}:{mins:02d}:{secs:02d}"


def build_ydl_opts(use_cookies=True, client_list=None, format_selector=None, extra_opts=None, include_js_runtime=True):
    opts = {
        "quiet": True,
        "no_warnings": True,
        "nocheckcertificate": True,
        "ignoreerrors": False,
        "user_agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36",
    }
    if client_list:
        opts["extractor_args"] = {
            "youtube": {
                "player_client": client_list,
            }
        }
    if include_js_runtime:
        opts["js_runtimes"] = {"node": {}}
        opts["remote_components"] = ["ejs:github"]

    if format_selector:
        opts["format"] = format_selector

    if use_cookies and COOKIE_FILE and os.path.exists(COOKIE_FILE):
        opts["cookiefile"] = COOKIE_FILE

    if extra_opts:
        opts.update(extra_opts)

    return opts


def run_yt_dlp_resilient(opts, target_url):
    try:
        with yt_dlp.YoutubeDL(opts) as ydl:
            return ydl.extract_info(target_url, download=True)
    except Exception as err:
        msg = str(err).lower()
        if any(k in msg for k in ["js_runtimes", "remote_components", "unknown option", "unsupported"]):
            cleaned = {k: v for k, v in opts.items() if k not in ("js_runtimes", "remote_components")}
            with yt_dlp.YoutubeDL(cleaned) as ydl:
                return ydl.extract_info(target_url, download=True)
        raise


def download_media_resilient(target_url, outtmpl_pattern, mode="audio", ranges=None):
    extra = {}
    if ranges:
        extra["download_ranges"] = download_range_func(None, ranges)
        extra["force_keyframes_at_cuts"] = True

    if mode == "audio":
        preferred_formats = [None, "ba*/b*/w*"]
    else:
        extra["merge_output_format"] = "mp4"
        preferred_formats = ["bv*[height<=720]+ba*/b*[height<=720]/bv*+ba*/b*", None]

    client_groups = [
        ["mweb", "web"],
        ["tv", "mweb"],
        None,
    ]

    attempts = []
    if COOKIE_FILE:
        for fmt in preferred_formats:
            for c_group in client_groups:
                attempts.append((True, c_group, fmt))
    for fmt in preferred_formats:
        for c_group in client_groups:
            attempts.append((False, c_group, fmt))

    errors_by_mode = {}
    for use_ck, c_group, fmt in attempts:
        mode_key = "cookies=ON" if use_ck else "cookies=OFF"
        label = f"{mode_key}, clients={c_group or 'default'}, fmt={fmt or 'auto'}"
        opts = build_ydl_opts(
            use_cookies=use_ck,
            client_list=c_group,
            format_selector=fmt,
            extra_opts={**extra, "outtmpl": outtmpl_pattern},
            include_js_runtime=True,
        )
        try:
            return run_yt_dlp_resilient(opts, target_url)
        except Exception as err:
            if mode_key not in errors_by_mode:
                errors_by_mode[mode_key] = f"{err} [{label}]"

    summary = " | ".join(f"{k}: {v}" for k, v in errors_by_mode.items())
    raise RuntimeError(summary)


col_in1, col_in2, col_btn = st.columns([4, 1, 1.5])
with col_in1:
    url = st.text_input(
        "TARGET VOD / CLIP URL (TWITCH O YOUTUBE)",
        placeholder="https://www.twitch.tv/videos/... oppure https://www.youtube.com/watch?v=...",
    )
with col_in2:
    num_clips = st.selectbox("CLIPS OUTPUT", [3, 5], index=1)
with col_btn:
    st.markdown("<div style='height: 27px;'></div>", unsafe_allow_html=True)
    run_clicked = st.button("⚡ EXTRACT CLIPS", type="primary")

if run_clicked and url:
    clean_url = url.strip()

    with st.spinner("[1/3] SCANNING STREAM METADATA & EXTRACTING AUDIO TRACK..."):
        for old_audio in glob.glob("full_stream_audio.*"):
            os.remove(old_audio)

        try:
            info = download_media_resilient(
                clean_url,
                "full_stream_audio.%(ext)s",
                mode="audio",
            )
            if not info:
                st.error("ERRORE: impossibile leggere i metadati del video.")
                st.stop()
            if info.get("is_live"):
                st.error(
                    "⚠️ LIVE STREAM IN CORSO RILEVATA: inserisci il link del VOD registrato appena terminata la live o una clip esistente."
                )
                st.stop()
            video_title = info.get("title", "Stream VOD")
        except Exception as e:
            st.error(f"ERRORE ACCESSO VIDEO: {e}")
            st.stop()

        audio_files = glob.glob("full_stream_audio.*")
        if not audio_files:
            st.error("ERRORE: nessun file audio scaricato sul server.")
            st.stop()
        full_audio = audio_files[0]

    with st.spinner("[2/3] RUNNING AI VIRAL MOMENT DETECTION ACROSS FULL VOD..."):
        chunk_dir = "audio_chunks"
        os.makedirs(chunk_dir, exist_ok=True)
        for old_f in os.listdir(chunk_dir):
            os.remove(os.path.join(chunk_dir, old_f))

        subprocess.run(
            [
                "ffmpeg",
                "-y",
                "-i",
                full_audio,
                "-vn",
                "-ar",
                "16000",
                "-ac",
                "1",
                "-b:a",
                "32k",
                "-f",
                "segment",
                "-segment_time",
                "1200",
                f"{chunk_dir}/chunk_%03d.mp3",
            ],
            check=True,
        )

        chunk_files = sorted(os.listdir(chunk_dir))
        all_segments = []
        for idx_c, c_file in enumerate(chunk_files):
            offset = idx_c * 1200.0
            c_path = os.path.join(chunk_dir, c_file)
            with open(c_path, "rb") as f:
                trans = client.audio.transcriptions.create(
                    file=(c_file, f.read()),
                    model="whisper-large-v3-turbo",
                    response_format="verbose_json",
                )
            for s in (trans.segments or []):
                text_clean = (s.get("text") if isinstance(s, dict) else getattr(s, "text", "") or "").strip()
                start_val = s.get("start") if isinstance(s, dict) else getattr(s, "start", 0.0)
                end_val = s.get("end") if isinstance(s, dict) else getattr(s, "end", 0.0)
                if text_clean:
                    all_segments.append({
                        "start": round(float(start_val) + offset, 2),
                        "end": round(float(end_val) + offset, 2),
                        "text": text_clean,
                    })

        if not all_segments:
            st.error("NESSUN PARLATO RILEVATO NELLO STREAM.")
            st.stop()

        condensed = [{"s": round(x["start"], 1), "e": round(x["end"], 1), "t": x["text"]} for x in all_segments]
        condensed_for_ai = condensed[::math.ceil(len(condensed) / 650)] if len(condensed) > 650 else condensed

        prompt = f"""
        You are an elite viral content strategist for TikTok, Reels, and YouTube Shorts.
        Analyze this full stream transcript ("{video_title}") and find the TOP {num_clips} most viral, funny, emotional, or high-retention moments across the ENTIRE stream.
        Each clip MUST be between 20 and 50 seconds long and must NOT overlap with the others.
        Return ONLY a valid JSON object with a single key "clips" containing a list of {num_clips} objects, each with:
        - "start": number (exact start second from the transcript)
        - "end": number (exact end second, 20 to 50 seconds after start)
        - "virality_score": integer between 78 and 99
        - "hook_title": catchy viral hook title
        - "reason": brief explanation in Italian of why this moment will go viral
        Transcript: {json.dumps(condensed_for_ai)}
        """

        chat = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[{"role": "user", "content": prompt}],
            response_format={"type": "json_object"},
        )
        ai_data = json.loads(chat.choices[0].message.content)
        clips_list = ai_data.get("clips", [])[:num_clips]

    st.markdown(
        f"<div class='badge-green' style='margin-bottom:15px;'>✓ RILEVATI {len(clips_list)} MOMENTI VIRALI SU: {video_title[:70]}</div>",
        unsafe_allow_html=True,
    )
    progress_bar = st.progress(0)

    for i, clip in enumerate(clips_list):
        c_start = max(0.0, float(clip.get("start", 0)))
        c_end = float(clip.get("end", c_start + 30))
        c_dur = max(15.0, min(55.0, c_end - c_start))
        c_end = c_start + c_dur

        srt_seg = f"subs_{i}.srt"
        final_seg = f"viral_clip_{i+1}.mp4"
        for f in glob.glob(f"raw_clip_{i}.*") + [srt_seg, final_seg]:
            if os.path.exists(f):
                os.remove(f)

        try:
            download_media_resilient(
                clean_url,
                f"raw_clip_{i}.%(ext)s",
                mode="video",
                ranges=[(c_start, c_end)],
            )
        except Exception as seg_err:
            st.warning(f"⚠️ Clip #{i+1}: impossibile scaricare il segmento ({seg_err})")
            continue

        raw_files = glob.glob(f"raw_clip_{i}.*")
        if not raw_files:
            continue
        raw_seg = raw_files[0]

        srt_lines = []
        idx_s = 1
        for s in all_segments:
            if s["end"] >= c_start and s["start"] <= c_end:
                rel_s = max(0.0, s["start"] - c_start)
                rel_e = min(c_dur, s["end"] - c_start)
                if rel_e > rel_s and s["text"]:
                    words = s["text"].upper().split()
                    chunk_w = [" ".join(words[k:k+4]) for k in range(0, len(words), 4)]
                    step_t = (rel_e - rel_s) / max(1, len(chunk_w))
                    for w_i, w_text in enumerate(chunk_w):
                        w_s = rel_s + w_i * step_t
                        w_e = rel_s + (w_i + 1) * step_t
                        srt_lines.append(f"{idx_s}\n{format_srt_time(w_s)} --> {format_srt_time(w_e)}\n{w_text}\n")
                        idx_s += 1

        with open(srt_seg, "w", encoding="utf-8") as f:
            f.writelines(srt_lines)

        vf_filter = (
            f"crop=ih*9/16:ih,scale=1080:1920,"
            f"subtitles={srt_seg}:force_style='FontName=Arial Black,FontSize=21,PrimaryColour=&H0000FFFF,OutlineColour=&H00000000,BorderStyle=1,Outline=3,Shadow=1,Alignment=2,MarginV=85'"
        )
        subprocess.run(
            [
                "ffmpeg",
                "-y",
                "-i",
                raw_seg,
                "-vf",
                vf_filter,
                "-c:v",
                "libx264",
                "-preset",
                "veryfast",
                "-crf",
                "23",
                "-c:a",
                "aac",
                final_seg,
            ],
            check=True,
        )

        score_val = clip.get("virality_score", 88)
        col_v, col_info = st.columns([1, 2.2])
        with col_v:
            if os.path.exists(final_seg):
                st.video(final_seg)
                with open(final_seg, "rb") as vf:
                    st.download_button(
                        f"⬇ DOWNLOAD CLIP #{i+1} (9:16 MP4)",
                        vf,
                        file_name=f"clipz_viral_{i+1}.mp4",
                        mime="video/mp4",
                        key=f"dl_{i}",
                    )
        with col_info:
            st.markdown(f"""
            <div class="clip-card">
                <div class="clip-header">
                    <div>
                        <span class="tag-pill">CLIP #{i+1:02d}</span>
                        <span class="badge-green">9:16 VERTICAL</span>
                        <span class="badge-muted" style="margin-left:8px;">{format_clock(c_start)} → {format_clock(c_end)} ({round(c_dur)}s)</span>
                    </div>
                    <div class="score-ring">{score_val}</div>
                </div>
                <div style="font-size:17px; font-weight:800; color:#ffffff; margin-bottom:10px;">
                    {clip.get('hook_title', 'Viral Moment')}
                </div>
                <div style="font-size:13px; color:#9ba3ae; line-height:1.5;">
                    <strong style="color:#00e676;">SCORE BREAKDOWN · {score_val}/100:</strong> {clip.get('reason', '')}
                </div>
            </div>
            """, unsafe_allow_html=True)

        progress_bar.progress((i + 1) / len(clips_list))
