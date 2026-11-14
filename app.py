
import os
import streamlit as st

from audio_generator import make_narration
from video_generator import render_quiz


# ---------------------------------
# PAGE SETTINGS
# ---------------------------------

st.set_page_config(
    page_title="Quiz Video Studio",
    page_icon="🎬",
    layout="wide"
)

st.title("🎬 Quiz Video Studio")

st.write(
    "Create comparison quizzes or four-option quizzes "
    "with female English narration."
)


# ---------------------------------
# CREATE FOLDERS
# ---------------------------------

for folder in [
    "assets/images",
    "output/videos",
    "output/audio"
]:
    os.makedirs(folder, exist_ok=True)


if "questions" not in st.session_state:
    st.session_state.questions = []


# ---------------------------------
# SIDEBAR SETTINGS
# ---------------------------------

with st.sidebar:

    st.header("Video settings")

    formats = st.multiselect(
        "Export formats",
        ["Vertical 9:16", "Horizontal 16:9"],
        ["Vertical 9:16", "Horizontal 16:9"]
    )

    timer = st.slider(
        "Countdown seconds",
        3,
        20,
        5
    )

    voice = st.selectbox(
        "Female English voice",
        [
            "en-US-AriaNeural",
            "en-US-JennyNeural",
            "en-GB-SoniaNeural"
        ]
    )

    music = st.file_uploader(
        "Background music (optional)",
        type=["mp3", "wav"]
    )

    tick = st.file_uploader(
        "Countdown sound (optional)",
        type=["mp3", "wav"]
    )

    reveal = st.file_uploader(
        "Answer reveal sound (optional)",
        type=["mp3", "wav"]
    )


# ---------------------------------
# FILE UPLOAD FUNCTION
# ---------------------------------

def save_upload(upload, path):

    if upload is None:
        return None

    os.makedirs(os.path.dirname(path), exist_ok=True)

    with open(path, "wb") as f:
        f.write(upload.getbuffer())

    return path


def store_audio(upload, name):

    if not upload:
        return None

    ext = os.path.splitext(upload.name)[1]

    path = "assets/" + name + ext

    with open(path, "wb") as f:
        f.write(upload.getbuffer())

    return path


# ---------------------------------
# ADD QUESTION
# ---------------------------------

st.subheader("Add a question")

kind = st.radio(
    "Choose quiz type",
    [
        "Comparison Quiz (2 Options)",
        "Multiple Choice Quiz (4 Options)"
    ],
    horizontal=True,
    key="quiz_type"
)

n = 2 if kind.startswith("Comparison") else 4


with st.form("add_question", clear_on_submit=True):

    question = st.text_input(
        "Enter your question",
        placeholder="Which animal is faster?"
    )

    st.markdown("### Answer options")

    options = []
    uploads = []

    for i in range(n):

        letter = chr(65 + i)

        st.markdown(f"**Option {letter}**")

        label = st.text_input(
            f"Option {letter} text",
            key=f"label_{letter}"
        )

        upload = st.file_uploader(
            f"Upload Option {letter} image (optional)",
            type=["png", "jpg", "jpeg", "webp"],
            key=f"image_{letter}"
        )

        options.append(label)
        uploads.append(upload)

    st.markdown("### Correct answer")

    correct = st.selectbox(
        "Select the correct option",
        list("AB" if n == 2 else "ABCD")
    )

    explanation = st.text_input(
        "Explanation (optional)"
    )

    add = st.form_submit_button(
        "Add question",
        use_container_width=True
    )


# ---------------------------------
# SAVE QUESTION
# ---------------------------------

if add:

    if not question.strip() or any(not x.strip() for x in options):

        st.error(
            "Please enter the question and all option labels."
        )

    else:

        qid = len(st.session_state.questions) + 1

        saved = []

        for i, upload in enumerate(uploads):

            if upload:

                ext = os.path.splitext(upload.name)[1]

                path = (
                    f"assets/images/q{qid}_{chr(65+i)}{ext}"
                )

                saved.append(save_upload(upload, path))

            else:

                saved.append(None)

        st.session_state.questions.append({

            "type": "comparison" if n == 2 else "multiple",

            "question": question.strip(),

            "options": [
                {
                    "label": options[i].strip(),
                    "image": saved[i]
                }
                for i in range(n)
            ],

            "correct": correct,

            "explanation": explanation.strip()

        })

        st.success("Question added successfully!")

        st.rerun()


# ---------------------------------
# DISPLAY QUESTIONS
# ---------------------------------

st.subheader(
    f"Your questions ({len(st.session_state.questions)})"
)

for i, q in enumerate(st.session_state.questions):

    with st.expander(f"{i+1}. {q['question']}"):

        st.write(
            " | ".join(
                f"{chr(65+j)}. {o['label']}"
                for j, o in enumerate(q["options"])
            )
        )

        st.write("Correct answer: " + q["correct"])

        if st.button(
            "Remove question",
            key="del" + str(i)
        ):

            st.session_state.questions.pop(i)

            st.rerun()


if st.button("Clear all questions"):

    if st.session_state.questions:

        st.session_state.questions = []

        st.rerun()


# ---------------------------------
# GENERATE VIDEOS
# ---------------------------------

st.divider()

st.subheader("Generate your quiz videos")


if st.button(
    "Generate MP4 videos + narration",
    type="primary",
    disabled=not st.session_state.questions
):

    if not formats:

        st.warning("Please select at least one export format.")

    else:

        try:

            music_path = store_audio(music, "music")
            tick_path = store_audio(tick, "tick")
            reveal_path = store_audio(reveal, "reveal")

            results = []

            progress = st.progress(0)

            total = len(formats)

            with st.spinner(
                "Creating female narration and generating videos..."
            ):

                narrations = [
                    make_narration(q, i, voice, timer)
                    for i, q in enumerate(st.session_state.questions)
                ]

                for index, fmt in enumerate(formats):

                    vertical = fmt.startswith("Vertical")

                    if vertical:

                        path = "output/videos/quiz_vertical.mp4"

                    else:

                        path = "output/videos/quiz_horizontal.mp4"

                    render_quiz(
                        st.session_state.questions,
                        narrations,
                        path,
                        vertical,
                        timer,
                        music_path,
                        tick_path,
                        reveal_path
                    )

                    if not os.path.exists(path):

                        raise FileNotFoundError(
                            f"Video was not created: {path}"
                        )

                    if os.path.getsize(path) == 0:

                        raise ValueError(
                            "Generated video is empty."
                        )

                    results.append(path)

                    progress.progress((index + 1) / total)

            st.success("Videos generated successfully!")

            # ---------------------------------
            # VIDEO PREVIEW AND DOWNLOAD
            # ---------------------------------

            for video_path in results:

                st.divider()

                filename = os.path.basename(video_path)

                st.subheader("🎬 " + filename)

                with open(video_path, "rb") as f:

                    video_bytes = f.read()

                # SHOW VIDEO PREVIEW
                st.video(video_bytes)

                # DOWNLOAD VIDEO
                st.download_button(
                    label="⬇️ Download " + filename,
                    data=video_bytes,
                    file_name=filename,
                    mime="video/mp4",
                    key="download_" + filename
                )

            st.info(
                "Your narration and generated videos are stored "
                "temporarily on the server. Download your videos "
                "before the server restarts."
            )

        except Exception as e:

            st.error("Video generation failed.")

            st.exception(e)
