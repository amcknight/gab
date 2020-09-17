Version 0.0... ...0.0.1 (Not useful for anyone)

Requires an OpenAI API key as an ENV var. If you use this, and you shouldn't because it doesn't really work yet, then please take full responsibility under [OpenAI's usage guide](https://beta.openai.com/docs/going-live). The code will need to be modified to fulfill OpenAI's guidelines.

# To Do
### Nice interface
- Complete the non-happy path options
- Be able to run in both text and voice mode
- Create a top-level menu for room, story, and any future options
- Get end-of-speech detection working
- Fix the key capture (or remove the need for key capture) in gab room
- Make the story interruptable and restartable, especially by voice
### Other
- Use grammarless speech to text for getting tags and yes-no answers
- Use multiple voices for menus vs story
- Combine common s2t and t2s functions
- Create tags module
- Create Message objects instead of strings

# Changelog
Unreleased
  - Remove .wav files after .mp3s are created
  - Refactored to the Actor Model
