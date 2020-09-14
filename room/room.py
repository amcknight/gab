
import openai
import sys
from room.renderer import *
from room.capture import *
from pynput import keyboard

actions = ["ENTER", "EXIT"]
cast = {}
tokens = 100
notMe = False

log = []


def complete(prompt):
    response = openai.Completion.create(engine="davinci", prompt=prompt, max_tokens=tokens)
    return response.choices[0].text


def start(initial_cast):
    global cast

    def enter_cast(person):
        return enter(person, cast)

    return [enter(me, cast)] + list(map(enter_cast, initial_cast))


def build_message(msg):
    # TODO: Use a correct limitation rather than this 1000 word hack
    return " ".join(msg.split(' ')[-1000:]) + "\n"


def next_line(prompt):
    global notMe
    while True:
        message = build_message(prompt)
        result = complete(message)
        line = parse(result)
        if '@' in line:
            print(line)
            pass
        else:
            notMe = False
            return line


def parse_action(action):
    global cast
    parts = action.split(':')
    if len(parts) != 2:
        fart()
        return "FAIL @ Incorrectly structured action"
    elif parts[0] not in actions:
        fart()
        return "Fail @ Unknown action '" + parts[0] + "'"
    else:
        command = parts[0].strip()
        person = parts[1].strip()
        if command == "ENTER":
            if person in cast.keys():
                fart()
                return "Fail @ '" + person + "' cannot enter because they're in the room!"
            speak(person + " has entered " + location + ".", "en-US-Standard-E")
            return enter(person, cast)
        elif command == "EXIT":
            if person not in cast.keys():
                fart()
                return "Fail @ '" + person + "' cannot leave because they're not in the room!"
            speak(person + " has exited " + location + ".", "en-US-Standard-E")
            return exit(person, cast)
        else:
            fart()
            return "FAIL @ Unknown command '" + command + "'"


def parse(res):
    result = res.split('\n')[0]
    if '>' in result:
        parts = result.split('>')
        if len(parts) > 2:
            fart()
            return "FAIL @ Extra '>'"
        speaker = parts[0].strip()
        if speaker == me:
            if notMe:
                fart()
                return "Fail @ Waiting for not me"
            return speaker + ">"
        elif speaker in cast.keys():
            speak(speaker + " said", "en-US-Standard-E")
            return speaker + ">" + parts[1]
        else:
            fart()
            return "FAIL @ Unknown Speaker: '" + speaker + "'"
    elif '[' in result and ']' in result:
        parts1 = result.split('[')
        if len(parts1) == 2:
            action = parts1[1].split(']')[0].strip()
            return parse_action(action)
    else:
        fart()
        return "FAIL @ '" + result + "'"


def fart():
    playsound("room/resources/fart.mp3")

def user_input(prefix):
    print(prefix)

    c = Capture()

    def on_press(key):
        if key == keyboard.Key.space:
            c.on()
        elif key == keyboard.Key.esc:
            sys.exit()
        return True

    def on_release(key):
        if key == keyboard.Key.space:
            c.off()
        return True

    listener = keyboard.Listener(on_press=on_press, on_release=on_release, suppress=True)
    listener.start()
    c.run()

    # return input(prefix).strip()
    print(c.last_text)
    return c.last_text.strip()


def chat(lines):
    global notMe
    global cast
    while True:
        result = next_line(format(lines))
        if result == me + ">":
            playsound("room/resources/ding.mp3")
            user_said = user_input(prefix_line(result) + " ")
            if user_said == "":
                notMe = True
            if user_said.startswith("-->"):
                result = enter(user_said.split('-->')[1].strip(), cast)
                print(prefix_line(result))
            elif user_said.startswith("<--"):
                result = exit(user_said.split('<--')[1].strip(), cast)
                print(prefix_line(result))
            else:
                result += " " + user_said
        else:
            print(prefix_line(result))
            if '>' in result:
                parts = result.split('>')
                person = parts[0].strip()
                speak(parts[1], cast[person]["voice"])
        lines += [result]


def setup():
    global me
    global location
    global cast
    me = input("What's your name? ").strip()
    location = input("Where are you? ").strip()
    initial_cast = list(map(str.strip, input("Who are you with? ").split(','))) + ["John Snow"]

    enter_lines = start(initial_cast)
    initial_chat_lines = [
        say(me, "Hi everyone!"),
        say("John", "Uh, why am here?"),
        say(me, "You can leave John"),
        exit("John Snow", cast)
    ]
    first_hello = say(me, "Hello " + " and ".join(cast) + ".")
    return enter_lines + [first_hello] + initial_chat_lines
