# Gab

A voice-based open-ended chatbot

Requires an OpenAI API key as an ENV var. If you use this, and you shouldn't because it doesn't really work yet, then please take full responsibility under [OpenAI's usage guide](https://beta.openai.com/docs/going-live). The code will need to be modified to fulfill OpenAI's guidelines.

## Install and Run

1) You need python3 and pipenv
2) Clone the repo
3) Add a `.env` file in the root directory with the line `OPENAI_API_KEY=sk-YOUR_SECRET_KEY_FROM_OPEN_AI`
4) Then run:
```commandline
pipenv install
```

That should be it but if installation is failing, you may need:
```commandline
pip3 install --upgrade openai playsound google-cloud-speech google-cloud-texttospeech pyaudio pydub pynput pysm pykka pykkachu sounddevice soundfile
```

Run it with:
```commandline
  pipenv run python3 gab
```

## Roadmap
### v0.1
- Happy path for room and story modes should run without error
- Complete the non-happy path options in Story
- Move engine into env variable
- Use grammarless speech to text for getting tags and yes-no answers
- Combine common s2t and t2s functions across modes
- Clean up old .mp3s and .wavs when exiting
- Make Story able to continue indefinitely using maximum prompt length
- Fix Room so if it is exitable in all situations without needing to kill the program
- Fix the key capture (or remove the need for key capture) in Room
### Beyond
- Get end-of-speech detection working
- Automatically cache text to speech requests to google
- Make it interruptable and restartable, especially by voice
- Use multiple voices for menus vs characters

## Changelog
### Unreleased
- Added a pure listen mode to check how voices are being interpreted
- Added argparse for selecting mode from terminal
- Remove .wav files after .mp3s are created
- Refactored to the Actor Model
- Added Message classes
- Used dispatcher decorators, a directory, and a "Head" object to organize code
- Added a state machine for limbic
- Made the Worker into a Fleet called a Cortex
- Added logging
- Created a decorator for Events+State
- Separated generic pykka extensions into a pykkachu file
- Split out the generic pykka extension into a library and importing it
