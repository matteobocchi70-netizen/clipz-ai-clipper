import os
import json
import subprocess
import streamlit as st
import yt_dlp
from groq import Groq

st.set_page_config(page_title="AI Viral Clipper & Scorer", layout="wide")
client = Groq(api_key=st.secrets["GROQ_API_KEY"])

def format_srt_time(seconds):
    hrs = int(seconds // 3600)
    mins = int((seconds % 3600) // 60)
    secs = int(seconds % 60)
    millis = int((seconds - int(seconds)) * 1000)
    return f"{hrs:02d}:{mins:02d}:{secs:02d},{millis:03d}"

st.title("AI Viral Clipper & Scorer (Pro)")
st.write("Incolla il link di una clip o video YouTube/Twitch per estrarre il momento più virale in 9:16 con sottotitoli.")

url = st.text_input("Link Video / Clip (YouTube o Twitch)", placeholder="https://www.youtube.com/watch?v=...")

if st.button("Genera Clip Virale", type="primary") and url:
    with st.spinner("Scaricamento, trascrizione AI e rendering 9:16 in corso..."):
        video_path, audio_path, srt_path, output_clip = "input.mp4", "audio.mp3", "subs.srt", "viral_clip_9_16.mp4"
        for f in [video_path, audio_path, srt_path, output_clip]:
            if os.path.exists(f):
                os.remove(f)

        ydl_opts = {
            "format": "bestvideo[height<=720][ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best",
            "outtmpl": video_path,
            "quiet": True,
        }
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([url.strip()])

        subprocess.run(["ffmpeg", "-y", "-i", video_path, "-vn", "-ar", "16000", "-ac", "1", "-b:a", "64k", audio_path], check=True)

        with open(audio_path, "rb") as file:
            transcription = client.audio.transcriptions.create(
                file=(audio_path, file.read()),
                model="whisper-large-v3-turbo",
                response_format="verbose_json",
            )

        segments = [{"start": round(s["start"], 2), "end": round(s["end"], 2), "text": s["text"].strip()} for s in (transcription.segments or [])]

        prompt = f"""
        You are an expert TikTok/Reels/Shorts viral clipper. Pick the single highest-retention 20 to 45 second clip.
        Return ONLY valid JSON with keys: "start" (number), "end" (number), "virality_score" (integer 72-99), "hook_title" (string), "reason" (Italian explanation).
        Segments: {json.dumps(segments[:150])}
        """
        chat = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[{"role": "user", "content": prompt}],
            response_format={"type": "json_object"},
        )
        result = json.loads(chat.choices[0].message.content)

        start = float(result.get("start", 0))
        end = float(result.get("end", start + 30))
        duration = max(12.0, min(60.0, end - start))
        clip_end = start + duration

        srt_lines = []
        idx = 1
        for s in segments:
            if s["end"] >= start and s["start"] <= clip_end:
                rel_start = max(0.0, s["start"] - start)
                rel_end = min(duration, s["end"] - start)
                if rel_end > rel_start and s["text"]:
                    srt_lines.append(f"{idx}\n{format_srt_time(rel_start)} --> {format_srt_time(rel_end)}\n{s['text'].upper()}\n")
                    idx += 1

        with open(srt_path, "w", encoding="utf-8") as f:
            f.writelines(srt_lines)

        vf_filter = f"crop=ih*9/16:ih,scale=1080:1920,subtitles={srt_path}:force_style='FontName=Arial,FontSize=18,PrimaryColour=&H00FFFFFF,OutlineColour=&H00000000,BorderStyle=1,Outline=2,Alignment=2,MarginV=65'"
        subprocess.run(["ffmpeg", "-y", "-ss", str(start), "-i", video_path, "-t", str(duration), "-vf", vf_filter, "-c:v", "libx264", "-preset", "veryfast", "-crf", "23", "-c:a", "aac", output_clip], check=True)

        col1, col2 = st.columns(2)
        with col1:
            st.video(output_clip)
            with open(output_clip, "rb") as v:
                st.download_button("Scarica Clip 9:16", v, file_name="viral_clip.mp4", mime="video/mp4")
        with col2:
            st.metric("Virality Score", f"{result.get('virality_score', 88)}/100")
            st.subheader(result.get("hook_title", "Viral Moment"))
            st.write(f"**Minutaggio:** {round(start, 1)}s - {round(clip_end, 1)}s")
            st.write(result.get("reason", ""))
