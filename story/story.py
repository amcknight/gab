#!/usr/bin/env python3

import re
import openai


def complete(prompt, tokens):
    response = openai.Completion.create(engine="davinci", prompt=prompt, max_tokens=tokens)
    return response.choices[0].text


async def complete_sentences(prompt, tokens):
    response = complete(prompt, tokens)
    ending = re.split("\.|\n|!|\?", response)[-1]
    return response[:-len(ending)]


def andify(tags):
    if len(tags) == 0:
        return ""
    if len(tags) == 1:
        return tags[0]
    tags2 = tags.copy()
    tags2[-1] = "and " + tags[-1]
    return ", ".join(tags2)


def get_prompt(tags):
    with open("story/res/tag2prompt.txt") as t2p_file:
        data = t2p_file.read()

    return data + "\n\n[tags] " + ", ".join(tags) + "\n[prompt]"


async def ask_yesno(question):
    while True:
        await speak(question, "en-US", "question.mp3")
        record("story/res/yesno", 3)
        raw = await speech_to_text("story/res/yesno.mp3")
        if raw == "Yes.":
            return True
        elif raw == "No.":
            return False


def get_tags(text):
    if text[-4:] == " and":
        text = text[-4:]
    tags = text.split(" and ")
    return tags


async def storytime():
    # speak("Welcome to story time! Name some things to include in your story:", "en-US", "story/res/intro.mp3")
    await play("story/res/intro.mp3")
    record("story/input_audio", 5)
    tags_text = await speech_to_text("story/input_audio.mp3")
    tags = get_tags(tags_text)
    confirm_tags_task = speak("This is a story about " + andify(tags), "en-US", "story/tags.mp3")
    t2p = get_prompt(tags)
    prompt = await complete_sentences(t2p, 100)
    await confirm_tags_task
    await speak(prompt, "en-GB", "story/prompt.mp3")
    go = await ask_yesno("Would you like to continue this story?")

    more_story = prompt
    while go:
        prev_story_part_task = speak(more_story, "en-GB", "story/story.mp3")
        more_story = await complete_sentences(prompt, 200)
        await prev_story_part_task
    await speak("Goodbye, and have a wonderful night", "en-US", "story/res/goodbye.mp3")

