# Gab

A voice-based open-ended chatbot

Requires an OpenAI API key as an ENV var. If you use this, and you shouldn't because it doesn't really work yet, then please take full responsibility under [OpenAI's usage guide](https://beta.openai.com/docs/going-live). The code will need to be modified to fulfill OpenAI's guidelines.

## Roadmap
### v0.1
- Complete the non-happy path options in Story
- Create a top-level menu for room, story, and any future options
- Use grammarless speech to text for getting tags and yes-no answers
- Combine common s2t and t2s functions
- Clean up old .mp3s when exiting
- Make Story able to continue indefinitely using maximum prompt length
- Fix the key capture (or remove the need for key capture) in Room
### Beyond
- Be able to run in both text and voice mode
- Get end-of-speech detection working
- Automatically cache text to speech requests to google
- Make it interruptable and restartable, especially by voice
- Use multiple voices for menus vs characters


## Changelog
### Unreleased
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
