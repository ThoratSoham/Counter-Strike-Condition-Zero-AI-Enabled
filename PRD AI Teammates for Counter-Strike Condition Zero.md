# PRD: AI Teammates for Counter-Strike: Condition Zero

*Version 1 (draft). Written in simple English. Open questions are at the end.*

## 1. Summary

We want to change the bots in Condition Zero (CZ) into **AI teammates that feel like real friends**. They talk in chat, they talk with voice, they react to the game, and they listen to you. Their voices must have real human feelings: happy, scared, angry, joking, tired.

**One-line vision:** "Playing CZ with 4 friends who are always online."

## 2. Goals and Non-Goals

### Goals

- Each teammate has a name, a personality, and a voice.
- Teammates talk by text chat and by voice, in a natural way.
- You can talk to them with your microphone, and they answer.
- Voices show real emotion that matches what happens in the game.
- The game stays smooth. No lag, no stutter.
- Works for single player and offline play.

### Non-Goals (for now)

- Making the bots aim or move better using AI. We keep the old bot code for that.
- Online multiplayer with other humans.
- Selling the mod. This is a personal/fan project.

## 3. Users

**Main user:** A single player who misses playing with friends and wants a fun, social match.

**Example:** "I play CZ at night. My friends are not online. I want teammates who joke with me, call out enemies, and cheer when I win."

## 4. Key Idea: Two Brains

AI models are too slow to control aiming and movement (they need answers in milliseconds). So we split the work:

| Brain | Job | Speed |
| --- | --- | --- |
| **Body brain** (old CZ bot code) | Walk, aim, shoot, buy, plant bomb | Very fast (every frame) |
| **Mind brain** (new AI) | Talk, feel, decide plans, react to you | Slow is OK (1 to 2 seconds) |

The Mind brain gives **high-level orders** to the Body brain, such as "go B site", "stay close to the player", "save weapon", "play safe, I am low HP".

## 5. System Design

### 5.1 Parts

1. **Game Plugin (C++)**
   - Runs inside the game as a Metamod plugin (CZ uses the GoldSrc engine).
   - Sends game events out: kills, deaths, damage, bomb events, round start/end, money, health, positions, who is near who.
   - Receives orders back and tells the bots what to do.
2. **AI Brain Service (Python or Node)**
   - Runs on the same PC as the game.
   - Keeps memory for each teammate: personality, mood, what happened this match, what the player said before.
   - Calls the language model to decide what to say and what mood to use.
3. **Voice Input (Speech-to-Text)**
   - Listens to your microphone (push-to-talk key).
   - Turns your voice into text.
   - Also notes how you sound (shouting, laughing, sad) if the tool supports it.
4. **Voice Output (Emotional Text-to-Speech)**
   - Turns the teammate's text into a voice with emotion.
   - Plays audio through the PC. Each teammate has a different voice.
   - Optional: 3D sound, so a teammate on your left sounds like they are on your left.
5. **Chat Bridge**
   - Shows teammate messages in the normal CZ chat box, like real players.
   - Reads your chat messages too.

### 5.2 Flow (example)

1. An enemy kills teammate "Rahul" (a bot).
2. Game Plugin sends event: *Rahul died, killer was at A long, 2 enemies left*.
3. Brain Service asks the language model: Rahul is hot-headed, he just died, what does he say?
4. Model answers: *text + emotion = annoyed*. Example: "Ugh! He was camping there, be careful!"
5. Voice Output makes an annoyed voice and plays it. The chat box shows the text.
6. Other teammates may react: "Chill bro, we got this."

### 5.3 Speed Target

- Teammate reply after you speak: **under 1.5 seconds** (best), **under 2.5 seconds** (acceptable).
- Reaction to game events (kill, bomb planted): **under 1 second**.
- Game FPS drop from the mod: **less than 3%**.

To reach this we use short replies, streaming (start talking before the full sentence is ready), and small fast models for quick reactions.

## 6. Features

### 6.1 Personalities (P0, must have)

- 4 teammates (CZ team size), each with:
  - Name, age feel, accent, humor style
  - Skill level (new player, average, pro)
  - Mood traits: calm, hot-headed, funny, serious
  - Likes and dislikes (for example: loves AWP, hates eco rounds)
- Personalities stay the same every match, but the mood changes in the match.

### 6.2 Text Chat (P0)

- Short, natural messages like real players. Light slang, small typos allowed (adjustable).
- Team chat and all chat.
- They answer when you type to them.
- They do **not** spam. Limit: a maximum number of messages per minute.

### 6.3 Voice Chat with Emotion (P0)

- Every spoken line has an **emotion tag**, for example: excited, scared, whispering, angry, sarcastic, laughing, sad, relieved.
- Voice must also support human sounds: laugh, sigh, gasp, "hmm", short pauses, breathing.
- Whispering when enemies are close. Shouting when in danger.
- Voices must not sound like the same robot repeating. Each line should be a little different.
- Teammates can talk over each other a little (real friends do this), but not too much.

### 6.4 Listen to the Player (P0)

- Push-to-talk (default) or voice detection (optional).
- Understands commands like "go B", "hold here", "save this round", "cover me".
- Understands normal talk too: jokes, complaints, "nice shot".
- Hindi, English, and mixed speech support is a **nice to have** (see questions).

### 6.5 Game Awareness (P0)

Teammates react to:

- Kills, headshots, deaths, clutch rounds
- Bomb planted, defused, or exploded
- Low health, low money, eco round
- Round win and loss, match win and loss
- Player doing something funny (team kill, falling off a ledge, missing an easy shot)

### 6.6 Callouts and Teamwork (P1)

- Real callouts: "Two A long, one hurt", "Flash out!", "I'm reloading".
- Teammates ask for help and give help.
- Mind brain can change the plan (rush, slow play, stay together).

### 6.7 Relationship and Memory (P1)

- They remember you between matches: "You carried us last time!", "Don't forget, you owe me a weapon drop."
- Teammates have small friendships and fights with each other.
- Memory is saved in a local file.

### 6.8 Mood System (P1)

- Each teammate has mood meters: happy, stressed, confident, tilted.
- Mood changes voice, chat style, and play style a little (for example: a tilted bot buys too much).

### 6.9 Settings Menu (P1)

- Volume per teammate, talk amount (quiet / normal / chatty), language, swearing level (off by default), voice on/off, text on/off.
- Choose teammates and edit personalities.

### 6.10 Nice to Have (P2)

- Post-match talk: "GG, that last round was crazy."
- Teammate voice changes when tired late in a long match.
- Custom voice packs.
- Replay highlights where teammates comment.

## 7. Voice Quality Rules (very important)

The user says: *no lame, emotionless AI voices.* So:

1. **Use an emotional TTS model**, not a basic one. It must take emotion hints and give natural laughs, sighs, and pauses.
2. **Short lines only.** Real players say 3 to 12 words in a fight. Long sentences sound fake.
3. **Match emotion to game state.** A scared voice when the player is last alive; a calm voice in a safe moment.
4. **Add variety.** Same event should not give the same words twice in a row.
5. **Allow imperfect speech.** "Uh", "wait", "oh no", half sentences. This is what makes it feel human.
6. **Test with real people.** Goal: in a blind test, at least 7 out of 10 testers say the voice "sounds like a real person" in most lines.

**Choices for voice (to decide in tech spike):**

- *Cloud emotional TTS:* best quality, easy to start, costs money per use, needs internet, adds some delay.
- *Local open-source emotional TTS:* free after setup, works offline, needs a strong GPU, quality is improving but varies.
- *Hybrid:* cloud for big moments, local for quick short lines.

We will test 3 to 5 options and pick one in Phase 0.

## 8. Technical Requirements

- **Game:** Counter-Strike: Condition Zero (GoldSrc engine, Windows).
- **Game hook:** Metamod plugin in C++ (plus AMX Mod X for simple script parts if useful).
- **Link between game and brain:** local UDP or WebSocket, small JSON messages.
- **Language model:** one strong model for personality talk, one small fast model for quick reactions. Cloud or local (decide in Phase 0).
- **Speech-to-text:** a fast model, local if possible, for low delay.
- **Audio:** play through a separate audio app or overlay; mixed with game sound. Echo control so the mic does not hear teammate voices.
- **PC needs (target):** Normal gaming PC for cloud mode. A GPU with enough memory for local voice and language models if fully offline.
- **Fallback:** If the AI service is slow or offline, bots go back to normal CZ bots with simple pre-recorded lines. The game never freezes.

## 9. Safety, Legal, and Rules

- **Anti-cheat:** Do not use the mod on VAC-protected online servers. Use offline, LAN, or insecure servers only.
- **Game files:** Mod works only with a copy of CZ that the user owns. We do not share Valve game files.
- **Voice rights:** Do not clone voices of real people or celebrities without permission. Use licensed or original voices.
- **Privacy:** Microphone audio is used only when the user presses the talk key. Tell the user clearly if audio goes to a cloud service. Keep local mode available.
- **Content control:** Swearing, insults, and jokes have adjustable levels. Teammates should never be hateful or abusive. They should not get too personal.
- **AI honesty:** If the user sincerely asks "are you an AI?", the teammate answers honestly (can be done in a fun way).

## 10. Success Metrics

| Metric | Target |
| --- | --- |
| Reply speed after player speaks | Under 1.5 s typical |
| FPS loss from mod | Under 3% |
| "Feels like real friends" rating (testers, 1 to 5) | 4 or higher |
| Voice "sounds human" in blind test | 7 of 10 or more |
| Wrong or off-topic teammate lines | Under 5% |
| Crashes per 10 hours of play | 0 |
| Players who keep it on after 1 week | 70% or more |

## 11. Phases and Timeline (rough)

**Phase 0: Tech Spike (2 to 3 weeks)**

- Prove we can read game events and send orders to bots.
- Test 3 to 5 voice options and 2 language model options.
- Measure real delay and cost.

**Phase 1: MVP (4 to 6 weeks)**

- 2 teammates, text chat + voice output with emotion.
- Reacts to kills, deaths, bomb, round end.
- Basic settings.

**Phase 2: Listen and Talk (4 to 6 weeks)**

- Push-to-talk, speech-to-text, voice commands.
- 4 full teammates with personalities.
- Callouts.

**Phase 3: Friends Feel (4 weeks)**

- Memory, mood, teammate-to-teammate talk.
- Fallback mode, polish, bug fixing.

**Phase 4: Release (2 weeks)**

- Easy installer, guide, small playtest group.

## 12. Risks and Answers

| Risk | Plan |
| --- | --- |
| Voice delay breaks the feel | Short lines, streaming audio, fast models, pre-made filler sounds ("hmm", "wait") |
| Cloud cost grows | Use small models for small talk, cache common lines, offer local mode |
| Bots talk too much | Talk budget per minute, priority system (danger calls first) |
| Bots say wrong info | Only let them talk about facts the plugin sends; do not let the model guess |
| Old game engine is hard to modify | Keep the plugin small; do heavy work outside the game |
| Mic picks up game and teammate sound | Push-to-talk, echo control, headphones recommended |
| AI breaks character or says bad things | Strong personality prompts, content filter, safe defaults |

## 13. Open Questions

1. **Budget:** Is a monthly cloud cost OK, or must everything run free on your PC?
2. **Your PC:** What GPU, RAM, and internet do you have?
3. **Language:** English only, or Hindi and Hinglish too?
4. **Voice style:** What accents and personalities do you want for your 4 friends?
5. **Play mode:** Single player only, or also LAN with human friends plus AI friends?
6. **Chat style:** Clean and polite, or real gamer banter with some swearing?
7. **Goal:** Personal use only, or do you plan to share it with other players?
8. **Skill:** Do you code in C++ and Python, or do you want a plan that is easy to follow step by step?

## 14. Decisions from Q&A (Update 1)

These answers **replace** the matching open questions in section 13 and the "choices" in sections 7 and 8.

### 14.1 How the AI runs: Cloud APIs (no GPU needed)

You have no GPU, so everything smart runs in the cloud. Your PC only runs the game, the small plugin, and the brain service. CZ is an old game, so a normal PC is fine.

| Job | Service to test first | Note |
| --- | --- | --- |
| Teammate thinking and chat | OpenRouter (many models, one API key) or Google AI Studio (Gemini API) | Use a small fast model for quick reactions. Use a stronger model for personality and long talk. |
| Voice with emotion | Google AI Studio (Gemini) speech generation, where you can describe the style, for example "say this scared, in a whisper" | OpenRouter is mainly for text models, so voice may need Google or another TTS service. We will check in Phase 0. |
| Understand your mic | Gemini audio input, or a cloud speech-to-text API | Keep audio short (push-to-talk) to save cost and time. |

**Important to check in Phase 0 (before we build):**

- Free tier limits: free plans often have request limits that a fast game can hit. We may need a small paid plan.
- Delay: cloud adds delay. We reduce it with short lines, streaming, and ready-made filler sounds ("wait", "oh no", laugh).
- Cost per hour of play: we will measure it and show it in the settings menu.
- Offline fallback: if the internet drops, bots use normal CZ bot radio lines.
- Keep the API key safe: store it in a local config file. Never put it inside the mod files you share.

### 14.2 Language: user can choose

- Setting in the menu: **Language** (default: English).
- The language is sent to the AI in every request, so chat and voice both follow it.
- Start with English and Hindi/Hinglish. More languages later, based on what the voice service supports well.
- Voice quality can differ by language, so we test each language before we list it as supported.

### 14.3 Chat style: real gamer talk, with swearing

- Default style: **real gamer banter**. Trash talk, jokes, and swearing like friends do.
- Settings slider: *Clean / Banter / Full gamer*. You can turn it down any time.
- Hard limits that stay on, even in Full gamer mode:
  - No hate speech or slurs about race, religion, gender, or similar.
  - No real threats.
  - The swearing is friendly and aimed at the game, the situation, or playful teasing of you. It is never truly cruel.
- Voice: swearing is spoken with emotion, like a real friend ("Oh come ON!"), not read flat.
- Some voice services block bad words. If so, we use soft versions in voice and keep the full words in text chat only.

### 14.4 Updated open questions

1. **Budget:** How much per month are you OK to spend on API use? (We will measure real cost in Phase 0.)
2. **Voice style:** What accents and personalities do you want for your 4 friends?
3. **Play mode:** Single player only, or LAN with human friends too?
4. **Sharing:** Personal use only, or will you share the mod with others?
5. **Skill:** Do you code in C++ and Python, or do you want step-by-step help?

## 15. Decisions from Q&A (Update 2): Zero Budget

These rules **override** earlier cost and cloud choices. **Hard rule: the mod must cost 0 rupees to run.**

### 15.1 The problem

- Free cloud plans (OpenRouter free models, Google AI Studio free tier) have **small limits** on requests per minute and per day. These limits can change, so check the current numbers in Phase 0.
- A fast game with 4 talking teammates can use up a free limit quickly.
- Free voice with strong emotion is the hardest part. The best emotional voices are often paid.

### 15.2 The solution: use the AI only when it matters

We do not call the AI for every small thing. We use **4 layers**, from cheapest to most costly:

| Layer | What it does | Cost | Delay |
| --- | --- | --- | --- |
| 1. Voice Line Library | Hundreds of ready-made emotional voice lines ("Nice shot!", "I'm hit, help!", "Bomb down, cover me!"), saved as audio files on your PC | Free after creation | Almost none |
| 2. Small local CPU voice or small CPU text model | Quick, simple lines when no ready line fits | Free | Low |
| 3. Free cloud AI (Gemini free tier / OpenRouter free models) | Real conversation: replies to what you say, jokes, memory | Free but limited | 1 to 3 s |
| 4. Fallback | Normal CZ bot radio lines if limits run out or internet is off | Free | None |

### 15.3 How the Voice Line Library is made (one time)

1. Write a big list of lines for each teammate and each situation (kill, death, bomb, low HP, round win, joking, tilt, and so on).
2. Each line has an emotion tag (scared, hyped, angry, sarcastic, relieved...).
3. Make the audio slowly over several days using the free voice tier, a little each day, so we stay inside free limits.
4. Make 3 to 5 versions of each line, so the same line does not repeat.
5. Save all files locally. At game time, pick the best line for the moment and play it.
6. Add natural sounds: laugh, sigh, gasp, "uh", "wait".

This gives **real emotional voices, no delay, and no cost while playing**.

### 15.4 Live replies when you talk to them

- Your mic audio is turned into text using a free speech-to-text option (a small local one that runs on CPU, or a free cloud tier).
- The text goes to a free language model for the answer.
- The answer is spoken with: (a) a ready line from the library if it fits, or (b) a local CPU voice for custom lines.
- **Talk budget:** the system counts free requests. When it is near the limit, teammates talk less on voice, stay in text chat, and save requests for important moments (your questions, clutch rounds).
- Show a small "AI energy" bar in the settings so you know how much free usage is left today.

### 15.5 Honest trade-off

- Fully custom spoken sentences with deep emotion for free are **limited**. Ready-made lines sound best. Live custom voice sounds a bit less emotional.
- Text chat can be fully live and fresh, because text is cheap.
- If free limits become too tight, the mod still works in layers 1, 2 and 4.

### 15.6 Updated Phase 0 test list (all free)

- Check current free limits for Gemini API and OpenRouter free models.
- Test free and open-source voices that run on a normal CPU. Rate them for emotion.
- Test free speech-to-text on CPU for speed.
- Measure how many requests one 30-minute match uses. Target: **under 60% of the daily free limit**.
- Confirm the game plugin can run on a PC with no GPU.

### 15.7 Personalities (mix)

Use a **mix** of 4 different personalities so the team feels real, for example:

1. **The Hothead:** loud, trash-talks, gets tilted fast.
2. **The Jokester:** funny, roasts everyone, keeps mood high.
3. **The Calm Pro:** quiet, clear callouts, dry humor.
4. **The Newbie:** nervous, asks questions, celebrates small wins.

Each has a different voice, speech speed, and swearing level (all inside the safety limits in section 14.3).

### 15.8 Language and tools

- **Programming languages are not fixed.** The coding tool (Antigravity) may choose what fits your PC best.
- Technical note for the builder: the part that runs **inside the game** (a Metamod plugin) must be a native DLL, usually written in **C++**. The AMX Mod X scripting plugin is a simpler option for small parts. The **AI Brain Service** outside the game can use any language, for example Python.
- Keep the game plugin small and the brain service separate, as in section 5.

### 15.9 Remaining open questions

1. Single player only, or LAN with human friends too?
2. Personal use only, or will you share the mod later? (Sharing changes the rules for voices and API keys.)

## 16. Decisions from Q&A (Update 3): Single Player and GitHub

This closes all open questions. The PRD is now ready to give to a coding tool.

### 16.1 Single player only

- No LAN or online play in version 1. This makes the mod simpler and safer.
- Only one human player: you. All 4 teammates are AI.
- No need for network sync, anti-cheat handling, or server rules.
- The player is always the only voice the mic listens to.

### 16.2 Sharing on GitHub later

Because other people will use the mod, add these rules now:

1. **Bring your own key.** Every user adds their own free API key in a local config file. The repo must **never** contain a real key. Add the config file to `.gitignore` and ship an example file such as `config.example.json`.
2. **No Valve files.** Do not upload any CZ game files, maps, models, or sounds. The mod is an add-on that only works if the user owns CZ.
3. **Voice library: generate on the user's PC.** Do not ship the pre-made voice files at first. Ship the line list and a **setup tool** that creates the audio on first run, a little each day, inside the user's own free limits. Later we can ship the files if the voice service terms allow sharing the audio. Check the terms first.
4. **Check licenses.** For every model, voice, and library we use, write down its license in a `THIRD_PARTY.md` file. Pick a clear license for our own code (for example MIT).
5. **Privacy note in the README.** Tell users that text and voice may be sent to the cloud service they choose. Free tiers of some services may use the data to improve their products. Local mode stays an option.
6. **Safety note in the README.** Use the mod offline or single player only. Do not use it on VAC-protected online servers.
7. **Content note.** The default chat style has swearing. Show an 18+ style warning and keep the Clean / Banter / Full gamer slider. Consider making *Banter* the default for shared releases.
8. **Name.** Use a clear name like "CZ AI Teammates". Say it is a fan project and not made by Valve.

### 16.3 Easy setup for other users

Goal: a new user installs in under 10 minutes.

1. Download the release zip from GitHub.
2. Run `setup` (checks CZ folder, installs Metamod and the plugin).
3. Paste a free API key when asked (the tool shows where to get one).
4. Pick language and chat style.
5. The tool builds the voice library in the background.
6. Start CZ and play.

The setup tool should also have a **Check** button that tests the game link, the mic, the speakers, and the API key.

### 16.4 GitHub repo layout (suggested)

- `plugin/` : the game plugin (C++)
- `brain/` : the AI Brain Service
- `voice/` : voice line list, emotion tags, setup tool
- `personalities/` : the 4 personality files (easy for the community to edit or add more)
- `docs/` : PRD, install guide, FAQ
- `config.example.json`, `README.md`, `LICENSE`, `THIRD_PARTY.md`

Community-made personalities and voice packs are a good future feature.

### 16.5 Final scope for Version 1

**In:** 4 AI teammates, mixed personalities, text chat, emotional voice (library + live), push-to-talk, game reactions, callouts, free-tier talk budget, language setting, chat style slider, fallback to normal bots, easy setup.

**Out for now:** LAN or online play, paid services, custom voice cloning, AI-controlled aiming and movement.

### 16.6 Open questions

None. Next step: give this PRD to the coding tool and start with **Phase 0 (tech spike)** from section 11, using the free-only test list in section 15.6.

## 17. Feature Catalog: 200 Features for "Feels Like Real People"

**Goal:** When you play with the mod, you must see and hear a clear difference from normal CZ bots.

**How to read this catalog**

- Features have IDs from F001 to F200 and are in 10 categories (A to J). Each category has 4 bundles of 5 features.
- You choose bundles with the pop-up questions in the chat. Only chosen features go into the build.
- Type tags: **\[Chat\]** text chat, **\[Order\]** changes what bots do, **\[Sound\]** audio, **\[Memory\]** remembers things, **\[Mood\]** moods and personality, **\[Tool\]** settings, testing, safety.
- **Honest note:** \[Order\] features are harder. The old CZ bot code controls aiming and movement. Phase 0 must test how much the plugin can really control. Where it cannot, bots will answer in chat and use the closest real bot behavior.

**Build order:** (1) Chat replies and event reactions, (2) Orders, (3) Personalities and memory, (4) Sounds, (5) Polish.

### Category A: Chat Replies and Conversation

**A1 Basic replies**

- F001 Reply to your say and say\_team messages within 3 seconds \[Chat\]
- F002 Answer when you call a bot by name, like "Rahul, help!" \[Chat\]
- F003 Choose the best bot to reply (nearest or most fitting) \[Chat\]
- F004 Understand typos and slang like "hlp", "wr r u", "pls" \[Chat\]
- F005 Short gamer-style replies, 2 to 12 words \[Chat\]

**A2 Smart answers**

- F006 Answer game questions with real data: "who has the AWP?", "how much money?" \[Chat\]
- F007 Say "on my way" and really move toward you \[Order\]
- F008 Sometimes refuse: "bro I'm broke", "too risky" \[Chat\]
- F009 Ask you questions back: "where are you?" \[Chat\]
- F010 Agree or disagree with your plan \[Chat\]

**A3 Talking with people**

- F011 Two bots talk to each other in the same chat \[Chat\]
- F012 Funny replies to your jokes \[Chat\]
- F013 Reply to thanks and compliments: "np", "ez" \[Chat\]
- F014 Reply to your insults with a roast \[Chat\]
- F015 Ignore spam and repeated messages \[Tool\]

**A4 Language and typing feel**

- F016 Reply in the language you picked \[Chat\]
- F017 Hinglish mode \[Chat\]
- F018 Ask "what?" or "which site?" when your message is unclear \[Chat\]
- F019 Reply length changes with mood (tired = short) \[Mood\]
- F020 Random 1 to 3 second typing delay so it feels human \[Chat\]

### Category B: Reacting to Game Events

**B1 Kills**

- F021 React to your kills and their own kills \[Chat\]
- F022 Hype on headshots \[Chat\]
- F023 Special reaction to knife kills \[Chat\]
- F024 Multi-kill reactions: double, triple \[Chat\]
- F025 Ace reaction when one player kills the whole enemy team \[Chat\]

**B2 Deaths**

- F026 Complain after own death: "he was camping!" \[Chat\]
- F027 React when a teammate dies \[Chat\]
- F028 Team kill reaction: anger or apology \[Chat\]
- F029 Special lines when killed by an AWP \[Chat\]
- F030 Special lines when killed while flashed \[Chat\]

**B3 Bomb**

- F031 Bomb planted callout \[Chat\]
- F032 Bomb defused cheer \[Chat\]
- F033 Bomb exploded reaction \[Chat\]
- F034 Last-second defuse panic and relief \[Chat\]
- F035 Bomb dropped or lost warning \[Chat\]

**B4 Rounds and match**

- F036 Round won reaction \[Chat\]
- F037 Round lost reaction \[Chat\]
- F038 Match win or loss reaction, with "gg" \[Chat\]
- F039 Eco round talk: "save this round" \[Chat\]
- F040 Clutch talk when only one teammate is left \[Chat\]

### Category C: Gamer Talk and Banter

**C1 Trash talk and praise**

- F041 Trash talk the enemy \[Chat\]
- F042 Roast teammates (friendly) \[Chat\]
- F043 Roast you when you miss easy shots \[Chat\]
- F044 Praise good plays: "clean!", "insane" \[Chat\]
- F045 Sarcasm \[Chat\]

**C2 Swearing and blame**

- F046 Swearing level slider: Clean / Banter / Full gamer \[Tool\]
- F047 Friendly nicknames and insults \[Chat\]
- F048 Fake rage: "I'm done with this team" \[Chat\]
- F049 Blame "lag" or "luck" \[Chat\]
- F050 Blame a teammate for a loss \[Chat\]

**C3 Gamer style**

- F051 Gamer slang: "clutch", "diff", "cracked" \[Chat\]
- F052 Small typos sometimes \[Chat\]
- F053 CAPS when excited or angry \[Chat\]
- F054 "gg", "ez", "wp", "nt" at the right time \[Chat\]
- F055 Short reactions: "lol", "bruh", "wtf" \[Chat\]

**C4 Fun extras**

- F056 Inside jokes that grow over the match \[Chat\]
- F057 Random funny comments in quiet moments \[Chat\]
- F058 Bots compete for MVP \[Chat\]
- F059 Bots bet with you: "I bet I get more kills" \[Chat\]
- F060 Pre-round hype talk \[Chat\]

### Category D: Orders and Teamwork

**D1 Movement orders**

- F061 "Follow me" \[Order\]
- F062 "Hold here" \[Order\]
- F063 "Go A" or "Go B" \[Order\]
- F064 "Rush" \[Order\]
- F065 "Save" (do not fight, keep weapons) \[Order\]

**D2 Team plans**

- F066 "Cover me" \[Order\]
- F067 "Wait here" \[Order\]
- F068 "Stay together" \[Order\]
- F069 "Split up" \[Order\]
- F070 "Fall back" \[Order\]

**D3 Buying and bomb**

- F071 "Buy AWP" or "Full buy" \[Order\]
- F072 Teammate drops a weapon for you when you ask \[Order\]
- F073 Teammate asks you for a weapon drop \[Chat\]
- F074 "Plant the bomb" \[Order\]
- F075 "Defuse the bomb" \[Order\]

**D4 Smart teamwork**

- F076 "Throw flash" or "Throw smoke" \[Order\]
- F077 "Check that area" \[Order\]
- F078 Hostage orders on hostage maps \[Order\]
- F079 Refuse an unsafe order and say why \[Chat\]
- F080 Confirm orders: "copy", "on it" \[Chat\]

### Category E: Callouts and Game Sense

**E1 Enemy info**

- F081 Enemy spotted with the real map area name \[Chat\]
- F082 How many enemies: "two A long" \[Chat\]
- F083 "He's low" when an enemy is hurt \[Chat\]
- F084 Enemy weapon callout: "AWP!" \[Chat\]
- F085 Enemy direction \[Chat\]

**E2 Self info**

- F086 "Reloading" \[Chat\]
- F087 "Need backup" \[Chat\]
- F088 "Flash out" \[Chat\]
- F089 "Smoke thrown" \[Chat\]
- F090 "I'm hit" with health \[Chat\]

**E3 Team info**

- F091 "Heard steps" from sound events \[Chat\]
- F092 Bomb carrier info \[Chat\]
- F093 Players left: "2 left, we got this" \[Chat\]
- F094 Time warning: "20 seconds" \[Chat\]
- F095 Money talk: "I can't buy" \[Chat\]

**E4 Advice**

- F096 Warn you about danger behind you \[Chat\]
- F097 Warn about a grenade \[Chat\]
- F098 Spot a sniper \[Chat\]
- F099 Suggest a plan at round start \[Chat\]
- F100 After a lost round: "what went wrong" talk \[Chat\]

### Category F: Personalities and Moods

**F1 The four personalities**

- F101 Hothead: loud, trash-talks, tilts fast \[Mood\]
- F102 Jokester: roasts everyone, keeps the mood high \[Mood\]
- F103 Calm Pro: short clear callouts, dry humor \[Mood\]
- F104 Newbie: nervous, asks questions, celebrates small wins \[Mood\]
- F105 Custom personality files anyone can edit or add \[Tool\]

**F2 Mood meters**

- F106 Happy meter \[Mood\]
- F107 Stress meter \[Mood\]
- F108 Tilt meter: angry after bad rounds \[Mood\]
- F109 Confidence meter \[Mood\]
- F110 Mood changes how they chat \[Mood\]

**F3 Mood changes play**

- F111 Mood changes buying and risk (tilted bots over-buy or rush) \[Order\]
- F112 Mood slowly recovers over time \[Mood\]
- F113 Team morale: whole team gets hyped or down \[Mood\]
- F114 Rivalry between two bots \[Mood\]
- F115 Friendships between two bots \[Mood\]

**F4 Unique style**

- F116 Each bot has its own speech style \[Mood\]
- F117 Favorite and hated weapons: "I hate the Scout" \[Mood\]
- F118 Catchphrases that repeat, but not too often \[Mood\]
- F119 Skill-based personality: pro, average, noob \[Mood\]
- F120 Random daily mood so every match feels new \[Mood\]

### Category G: Memory and Relationships

**G1 Remember events**

- F121 Remember the last match \[Memory\]
- F122 Remember your favorite weapon \[Memory\]
- F123 Remember your team kills \[Memory\]
- F124 Remember your clutches \[Memory\]
- F125 Remember who carried the team \[Memory\]

**G2 Feelings about you**

- F126 Grudges: "you owe me for that team kill" \[Memory\]
- F127 Gratitude after you save them \[Memory\]
- F128 Nicknames for you \[Memory\]
- F129 Running score between you and the bots \[Memory\]
- F130 Callbacks: "just like last time" \[Memory\]

**G3 How memory works**

- F131 Save memory to a local file \[Memory\]
- F132 Separate memory for each bot \[Memory\]
- F133 AI writes a short summary of each match for later \[Memory\]
- F134 Reset or forget memory from the menu \[Tool\]
- F135 Session stats: kills, deaths, MVPs \[Memory\]

**G4 Learning you**

- F136 Learn your play style: rusher, camper, sniper \[Memory\]
- F137 Remember your habits: "always rushing B" \[Memory\]
- F138 Remember your player name \[Memory\]
- F139 Time-of-day talk: "late night grind" \[Memory\]
- F140 Map-specific memory: "this map always ruins us" \[Memory\]

### Category H: Sounds and Voice

**H1 Meme sound system**

- F141 Meme sounds by emotion tag \[Sound\]
- F142 Never play the same sound twice in a row \[Sound\]
- F143 Cooldown so sounds do not spam \[Sound\]
- F144 Volume normalizing \[Sound\]
- F145 Quieter when the bot is far away \[Sound\]

**H2 Real human feel**

- F146 Real recorded human voice clips (you and friends) \[Sound\]
- F147 Pitch-shifted clips so one voice becomes four \[Sound\]
- F148 Laugh, sigh, gasp and "hmm" clips \[Sound\]
- F149 Radio beep style for callouts \[Sound\]
- F150 Whisper and shout versions of key lines \[Sound\]

**H3 Moments**

- F151 Win and lose jingles \[Sound\]
- F152 Kill streak sounds \[Sound\]
- F153 Start and end of match "GG" sounds \[Sound\]
- F154 Sound packs that users can swap \[Sound\]
- F155 Sound manifest file that maps events to sounds \[Tool\]

**H4 Voice settings**

- F156 Optional TTS, off by default \[Sound\]
- F157 Local CPU voice as a backup \[Sound\]
- F158 Mute a single bot \[Tool\]
- F159 Sound frequency slider: Low / Normal / Chatty \[Tool\]
- F160 Subtitles in chat when a sound plays \[Sound\]

### Category I: Human-Like Quirks

**I1 Not perfect**

- F161 Random reaction delay \[Order\]
- F162 Small mistakes: a wasted flash, a missed callout \[Order\]
- F163 Rare short pause, like a real player looking away \[Order\]
- F164 Sometimes a wrong callout, then "my bad" \[Chat\]
- F165 Sometimes forgets to buy and says so \[Chat\]

**I2 Talking rhythm**

- F166 Typing-style delay for longer messages \[Chat\]
- F167 Bots interrupt each other a little \[Chat\]
- F168 Quiet in tense moments \[Chat\]
- F169 Chatty in dead time \[Chat\]
- F170 Warm-up talk before the round starts \[Chat\]

**I3 Behavior habits**

- F171 Gets distracted and says "wait what?" \[Chat\]
- F172 Panics when alone \[Mood\]
- F173 Overconfident after a streak \[Mood\]
- F174 Cautious after a loss \[Mood\]
- F175 Personal peek and hold habits for each bot \[Order\]

**I4 Fun actions**

- F176 Bots celebrate together: jump, crouch \[Order\]
- F177 Bots spray graffiti \[Order\]
- F178 Bot dance or crouch emotes after a win \[Order\]
- F179 Team name or clan tag for the bots \[Chat\]
- F180 Greeting at match start: "yo, let's go" \[Chat\]

### Category J: Settings, Testing, and Safety

**J1 Settings**

- F181 Settings menu \[Tool\]
- F182 Chat style slider \[Tool\]
- F183 Language selector \[Tool\]
- F184 Talk frequency slider \[Tool\]
- F185 Per-bot on and off \[Tool\]

**J2 Debug tools**

- F186 Log file for every step \[Tool\]
- F187 `ai_status` command \[Tool\]
- F188 `ai_test_say` command \[Tool\]
- F189 `ai_test_ping` command \[Tool\]
- F190 `ai_test_sound` command \[Tool\]

**J3 Free-tier and fallback**

- F191 Free request counter \[Tool\]
- F192 "AI energy" bar \[Tool\]
- F193 Local reply bank for when the API fails \[Tool\]
- F194 Full offline mode \[Tool\]
- F195 Auto reconnect to the brain service \[Tool\]

**J4 Safety and setup**

- F196 Hard safety limits: no slurs, no hate, no real threats \[Tool\]
- F197 Spam limiter \[Tool\]
- F198 `config.example.json` and a safe API key setup \[Tool\]
- F199 Setup and Check tool for new users \[Tool\]
- F200 Crash safety: the game never freezes if the AI fails \[Tool\]

### 17.1 Acceptance Test: the "Before and After" Test

The mod passes only if all of these are true:

1. You press U, type "help me at B", and a teammate answers within 3 seconds.
2. The teammate really moves toward you, or says honestly why not.
3. A bot dies and a teammate reacts with a chat line in character.
4. A bomb is planted and a callout appears.
5. Over one match, the 4 bots sound different from each other.
6. With the API turned off, chat replies still work from the local reply bank.
7. The game has no crash and loses less than 3% FPS.

### 17.2 Rules for Choosing Features

- Pick **chat and event** features first. They give the biggest change for the least work.
- &#91;Order\] features depend on Phase 0 results. Do not promise them before the test.
- Do not build everything at once. Build one category, test it, then go on.
- Every chosen feature needs a log line and a test, so we can prove it works.

## 18. Final Selection and Build Plan

**Decision:** All 200 features (F001 to F200) are selected.

Building all 200 at once will fail. So we build in **milestones**. Each milestone must pass its test before the next one starts.

### 18.1 Milestones

| Milestone | Features | Goal | Test to pass |
| --- | --- | --- | --- |
| M0: Proof it works | F186 to F190, F195, F200 | Plugin loads, brain connects, a bot says "hello" in team chat. Logs show every step. | `meta list` shows the plugin. `ai_test_say` and `ai_test_ping` work. |
| M1: Chat that answers | F001 to F005, F011 to F020, F193, F194, F196, F197 | Bots reply to your chat in 3 seconds, even with the API off. | Type "help" with the API off: a bot still answers. |
| M2: Reactions | F021 to F040, F081 to F095 | Bots react to kills, deaths, bomb, rounds, and give callouts. | One full match with natural chat from events. |
| M3: Gamer talk | F041 to F060, F046, F182 | Trash talk, swearing slider, gamer style, banter. | The 3 chat styles clearly differ. |
| M4: Personalities and moods | F101 to F120, F105 | 4 different bots with moods that change chat and buying. | Blind test: you can tell the bots apart without names. |
| M5: Orders | F006 to F010, F061 to F080, F096 to F100 | Bots follow real orders (follow, hold, go A/B, buy, drop, plant, defuse). | "Follow me" and "Hold" visibly change bot movement. |
| M6: Memory | F121 to F140 | Bots remember you across rounds and matches. | A bot refers to a past match correctly. |
| M7: Sounds | F141 to F160 | Meme sounds and human clips, with anti-repeat and cooldowns. | Sounds fit events and do not spam. |
| M8: Human quirks | F161 to F180 | Small mistakes, delays, interruptions, emotes, greetings. | Playtest: it feels less like a script. |
| M9: Settings and setup | F181 to F185, F191, F192, F198, F199 | Menu, language, counters, easy installer for GitHub. | A new PC can install in under 10 minutes. |

### 18.2 Dependencies

- M0 comes first. Without it, nothing else can be tested.
- M1 and M2 give the biggest visible change. If time is short, stop after M3 and you already have a very different game.
- M5 (orders) depends on how much of the CZ bots the plugin can control. Test this early in M0, then decide the scope of M5.
- M7 can start any time after M1, but needs your sound files.

### 18.3 Risks for the full 200

| Risk | Plan |
| --- | --- |
| Too much at once | Strict milestones. No new milestone until the last one passes. |
| Free API limits | Local reply bank first, API only for real conversation (section 15). |
| Orders cannot control the bots well | Test in M0. If limited, use the best available bot behavior and say so honestly in chat. |
| Chat spam | Talk budget and priority system (F197). |
| Sounds are copyrighted | Keep the sounds folder local and out of GitHub (section 16). |
| Code gets messy | Keep the plugin small, the brain separate, and every feature behind an on/off flag in config. |

### 18.4 Definition of Done (whole mod)

1. All milestone tests M0 to M9 pass.
2. The "Before and After" test in section 17.1 passes.
3. The mod runs for 10 hours with no crash.
4. FPS loss is under 3%.
5. The repo has a README, a LICENSE, `THIRD_PARTY.md`, a config example, and no secrets or Valve files.

### 18.5 Open Questions

None. The next step is to build **M0**.
