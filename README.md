Version 0.0... ...0.0.1 (Not useful for anyone)

Requires an OpenAI API key as an ENV var. If you sue this, and you shouldn't because it doesn't really work yet, then please take full responsibility under [OpenAI's usage guide](https://beta.openai.com/docs/going-live). The code will need to be modified to fulfill OpenAI's guidelines.

To do
- Clean up
  - Combine common s2t and t2s functions
  - Remove .wav files after .mp3s are created
- Nice interface
  - Be able to run in both text and voice mode
  - Create a top-level menu for room, story, and any future options
  - Get end-of-speech detection working
  - Fix the key capture (or remove the need for key capture) in gab room
  - Make the story interruptable, especially by voice
- Sane Architecture
  - Try Pykka
