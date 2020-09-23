Version 0.0... ...0.0.1 (Not useful for anyone)

Requires an OpenAI API key as an ENV var. If you use this, and you shouldn't because it doesn't really work yet, then please take full responsibility under [OpenAI's usage guide](https://beta.openai.com/docs/going-live). The code will need to be modified to fulfill OpenAI's guidelines.

# To Do
### General
- Be able to run in both text and voice mode
- Create a top-level menu for room, story, and any future options
- Get end-of-speech detection working
- Use grammarless speech to text for getting tags and yes-no answers
- Combine common s2t and t2s functions
### Story
- Complete the non-happy path options
- Make it interruptable and restartable, especially by voice
- Use multiple voices for menus vs story
- Make story able to continue indefinitely using maximum prompt length
### Room
- Fix the key capture (or remove the need for key capture)

# Changelog
### Unreleased
  - Remove .wav files after .mp3s are created
  - Refactored to the Actor Model
  - Added Message classes
  - Used dispatcher decorators, a directory, and a "Head" object to organize code
