
import os
import math
import numpy as np

from PIL import Image, ImageDraw, ImageFont, ImageOps
from moviepy import (
    VideoClip,
    AudioFileClip,
    CompositeAudioClip,
    vfx
)

CYAN = (0, 235, 255)
PINK = (255, 35, 210)
WHITE = (245, 248, 255)
BG = (7, 10, 28)


def font(size, bold=True):
    paths = [
        "C:/Windows/Fonts/arialbd.ttf" if bold
        else "C:/Windows/Fonts/arial.ttf",
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"
    ]

    for p in paths:
        if os.path.exists(p):
            return ImageFont.truetype(p, size)

    return ImageFont.load_default()


def fit(d, text, maxw, size):
    while size > 18 and d.textbbox(
        (0, 0), text, font=font(size)
    )[2] > maxw:
        size -= 2

    return font(size)


def frame(q, w, h, remaining, total, reveal):

    im = Image.new("RGB", (w, h), BG)
    d = ImageDraw.Draw(im)

    for r in range(100, min(w, h), 150):
        d.ellipse(
            (w//2-r, h//2-r, w//2+r, h//2+r),
            outline=(15, 28, 62),
            width=3
        )

    header = f"QUIZ CHALLENGE  •  QUESTION {q['number']:02d}"

    d.text(
        (int(w*.05), int(h*.055)),
        header,
        font=font(max(20, int(w*.023))),
        fill=CYAN
    )

    qf = fit(d, q["question"], int(w*.88), int(w*.05))
    bb = d.textbbox((0, 0), q["question"], font=qf)

    d.text(
        ((w-(bb[2]-bb[0]))//2, int(h*.15)),
        q["question"],
        font=qf,
        fill=WHITE
    )

    n = len(q["options"])

    if n == 2:
        cw = int(w*.39)
        ch = int(h*.43)
        gap = int(w*.055)
        sx = (w-2*cw-gap)//2
        sy = int(h*.31)

        boxes = [
            (sx, sy, cw, ch),
            (sx+cw+gap, sy, cw, ch)
        ]

    else:
        cw = int(w*.39)
        ch = int(h*.26)
        gapx = int(w*.055)
        gapy = int(h*.035)

        sx = (w-2*cw-gapx)//2
        sy = int(h*.28)

        boxes = [
            (sx, sy, cw, ch),
            (sx+cw+gapx, sy, cw, ch),
            (sx, sy+ch+gapy, cw, ch),
            (sx+cw+gapx, sy+ch+gapy, cw, ch)
        ]

    for i, (o, (x, y, cw, ch)) in enumerate(
        zip(q["options"], boxes)
    ):

        accent = (
            (80, 255, 160)
            if reveal and chr(65+i) == q["correct"]
            else (CYAN if i % 2 == 0 else PINK)
        )

        d.rounded_rectangle(
            (x, y, x+cw, y+ch),
            radius=28,
            fill=(17, 24, 52),
            outline=accent,
            width=6
        )

        p = o.get("image")

        if p and os.path.exists(p):
            photo = Image.open(p).convert("RGB")
            photo = ImageOps.fit(photo, (cw-16, ch-16))

            mask = Image.new("L", photo.size, 0)

            ImageDraw.Draw(mask).rounded_rectangle(
                (0, 0, photo.width-1, photo.height-1),
                radius=20,
                fill=255
            )

            im.paste(photo, (x+8, y+8), mask)
            d = ImageDraw.Draw(im)

        else:
            label = o["label"]
            f = fit(d, label, cw-40, 48)
            bb = d.textbbox((0, 0), label, font=f)

            d.text(
                (x+(cw-bb[2]+bb[0])//2, y+ch//2-25),
                label,
                font=f,
                fill=WHITE
            )

        d.rounded_rectangle(
            (x+12, y+12, x+78, y+75),
            radius=18,
            fill=BG,
            outline=PINK,
            width=3
        )

        d.text(
            (x+29, y+14),
            chr(65+i),
            font=font(42),
            fill=WHITE
        )

        label = o["label"]
        f = fit(d, label, cw-45, 32)
        bb = d.textbbox((0, 0), label, font=f)

        d.rounded_rectangle(
            (x+12, y+ch-65, x+cw-12, y+ch-12),
            radius=13,
            fill=(4, 8, 24)
        )

        d.text(
            (x+(cw-(bb[2]-bb[0]))//2, y+ch-62),
            label,
            font=f,
            fill=WHITE
        )

    # COUNTDOWN PROGRESS BAR

    bw = int(w*.68)
    bh = max(18, int(h*.022))
    bx = (w-bw)//2
    by = int(h*.87)

    d.rounded_rectangle(
        (bx, by, bx+bw, by+bh),
        radius=bh//2,
        fill=(35, 42, 72),
        outline=CYAN,
        width=3
    )

    # Calculate remaining progress, not original timer.
    progress = max(0, min(1, remaining / total))

    fw = int((bw-12) * progress)

    if fw > 0:
        d.rounded_rectangle(
            (bx+6, by+6, bx+6+fw, by+bh-6),
            radius=bh//2,
            fill=(0, 220, 170)
        )

    if reveal:

        msg = (
            f"CORRECT: {q['correct']} — "
            f"{q['options'][ord(q['correct'])-65]['label']}"
        )

        mf = fit(d, msg, int(w*.9), int(w*.027))
        bb = d.textbbox((0, 0), msg, font=mf)

        d.text(
            ((w-(bb[2]-bb[0]))//2, int(h*.93)),
            msg,
            font=mf,
            fill=(90, 255, 170)
        )

    else:

        msg = f"{max(0, math.ceil(remaining))} SECONDS"

        mf = font(max(22, int(w*.025)))
        bb = d.textbbox((0, 0), msg, font=mf)

        d.text(
            ((w-(bb[2]-bb[0]))//2, int(h*.92)),
            msg,
            font=mf,
            fill=WHITE
        )

    return np.asarray(im)



def render_quiz(
    questions,
    narrations,
    out,
    vertical=True,
    timer=5,
    music_path=None,
    tick_path=None,
    reveal_path=None
):

    w, h = (1080, 1920) if vertical else (1920, 1080)

    reveal_time = 2.5

    qs = []

    for i, original in enumerate(questions):
        q = dict(original)
        q["number"] = i + 1
        qs.append(q)

    audio_clips = []
    tracks = []
    scenes = []

    # Load narration and calculate each question's actual duration.
    for i, narration in enumerate(narrations):

        if isinstance(narration, dict):
            question_path = narration["question"]
            answer_path = narration["answer"]
        else:
            raise ValueError(
                "Narration format is incorrect. "
                "Please use the updated audio_generator.py."
            )

        question_audio = AudioFileClip(question_path)
        answer_audio = AudioFileClip(answer_path)

        audio_clips.extend([question_audio, answer_audio])

        question_duration = question_audio.duration
        answer_duration = answer_audio.duration

        # Countdown starts AFTER the question narration.
        answer_start = question_duration + timer

        # Keep the answer visible until narration finishes.
        actual_reveal_time = max(
            reveal_time,
            answer_duration + 0.5
        )

        scene_duration = answer_start + actual_reveal_time

        scenes.append({
            "question_duration": question_duration,
            "answer_start": answer_start,
            "duration": scene_duration,
            "question_audio": question_audio,
            "answer_audio": answer_audio
        })

    # Calculate the complete video duration.
    total_duration = sum(s["duration"] for s in scenes)

    # Render the correct question at every timestamp.
    def make_frame(t):

        offset = 0

        for i, scene in enumerate(scenes):

            scene_duration = scene["duration"]

            if t < offset + scene_duration:

                local = t - offset

                question_duration = scene["question_duration"]
                answer_start = scene["answer_start"]

                if local < question_duration:

                    # Narrator is reading the question.
                    # Keep the countdown bar full.
                    remaining = timer
                    reveal = False

                elif local < answer_start:

                    # Countdown starts after narration.
                    countdown_elapsed = local - question_duration

                    remaining = max(
                        0,
                        timer - countdown_elapsed
                    )

                    reveal = False

                else:

                    # Countdown finished: reveal the answer.
                    remaining = 0
                    reveal = True

                return frame(
                    qs[i],
                    w,
                    h,
                    remaining,
                    timer,
                    reveal
                )

            offset += scene_duration

        # Final fallback.
        return frame(
            qs[-1],
            w,
            h,
            0,
            timer,
            True
        )

    clip = VideoClip(
        make_frame,
        duration=total_duration
    )

    # Add question and answer narration at their correct times.
    offset = 0

    for scene in scenes:

        question_audio = scene["question_audio"]
        answer_audio = scene["answer_audio"]

        tracks.append(
            question_audio.with_start(offset + 0.1)
        )

        tracks.append(
            answer_audio.with_start(
                offset + scene["answer_start"] + 0.1
            )
        )

        offset += scene["duration"]

    # Background music.
    if music_path and os.path.exists(music_path):

        music = AudioFileClip(music_path)
        audio_clips.append(music)

        music = music.with_volume_scaled(0.15)
        music = music.with_effects([
            vfx.Loop(duration=total_duration)
        ])

        tracks.append(music)

    # Countdown tick sounds.
    if tick_path and os.path.exists(tick_path):

        tick = AudioFileClip(tick_path)
        audio_clips.append(tick)

        tick = tick.with_volume_scaled(0.5)

        offset = 0

        for scene in scenes:

            countdown_start = scene["question_duration"]

            for second in range(timer):

                tracks.append(
                    tick.with_start(
                        offset + countdown_start + second
                    )
                )

            offset += scene["duration"]

    # Correct answer reveal sound.
    if reveal_path and os.path.exists(reveal_path):

        effect = AudioFileClip(reveal_path)
        audio_clips.append(effect)

        effect = effect.with_volume_scaled(0.7)

        offset = 0

        for scene in scenes:

            tracks.append(
                effect.with_start(
                    offset + scene["answer_start"]
                )
            )

            offset += scene["duration"]

    # Combine all audio tracks.
    if tracks:

        final_audio = CompositeAudioClip(tracks)

        clip = clip.with_audio(final_audio)

    os.makedirs(
        os.path.dirname(out) or ".",
        exist_ok=True
    )

    clip.write_videofile(
        out,
        fps=24,
        codec="libx264",
        audio_codec="aac"
    )

    clip.close()

    for audio in audio_clips:
        try:
            audio.close()
        except Exception:
            pass
