
import os
import asyncio
import edge_tts

os.makedirs("output/audio", exist_ok=True)


def make_narration(q, index, voice, timer_seconds=5):

    # Part 1: Question and options
    question_parts = [q["question"] + "."]

    for i, option in enumerate(q["options"]):
        letter = chr(65 + i)
        question_parts.append(
            f"Option {letter}: {option['label']}."
        )

    question_parts.append("Choose your answer.")

    question_text = " ".join(question_parts)

    # Part 2: Correct answer and explanation
    correct_index = ord(q["correct"]) - 65
    answer = q["options"][correct_index]["label"]

    answer_parts = [
        f"The correct answer is {q['correct']}. {answer}."
    ]

    if q.get("explanation"):
        answer_parts.append(q["explanation"])

    answer_text = " ".join(answer_parts)

    question_path = (
        f"output/audio/question_{index+1:03d}.mp3"
    )

    answer_path = (
        f"output/audio/answer_{index+1:03d}.mp3"
    )

    async def generate():

        # Generate question voice
        question_voice = edge_tts.Communicate(
            question_text,
            voice,
            rate="-10%"
        )

        await question_voice.save(question_path)

        # Generate answer voice
        answer_voice = edge_tts.Communicate(
            answer_text,
            voice,
            rate="-10%"
        )

        await answer_voice.save(answer_path)

    asyncio.run(generate())

    return {
        "question": question_path,
        "answer": answer_path
    }
