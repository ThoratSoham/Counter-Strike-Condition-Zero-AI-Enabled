# Meme Sound Library Guide

This mod uses **meme sound effects** instead of robotic TTS to express emotions and game reactions dynamically.

Because sound memes are copyright-sensitive, audio files are **not bundled** in the Git repository. You download the sounds you like directly from [MyInstants.com](https://www.myinstants.com/) or your favorite audio repository.

---

## 📂 Folder Layout

Place `.mp3` or `.wav` files into their respective tag subfolders inside `sounds/`:

```
sounds/
├── fail/             # For deaths, getting knifed, botched rounds
├── hype/             # For multi-kills, aces, round wins
├── shock/            # For sniper shots, sudden ambushes
├── roast/            # For roasting missed shots or trash talk
├── clutch/           # For 1vX clutch wins and insane shots
├── panic/            # When last alive or under heavy fire
├── bad_play/         # For team damage, team flashes, falling
├── celebrate_kill/   # For quick headshots and frags
├── bomb_alert/       # For bomb planted and defusal tension
└── sus_or_tease/     # For funny downtime banter and stealth plays
```

---

## 🔎 Recommended Search Queries on MyInstants.com

Visit [MyInstants.com](https://www.myinstants.com/) and search for any of the following:

| Tag | Search Queries on MyInstants | Example Moments |
|---|---|---|
| **fail** | `sad trombone`, `wah wah wah`, `sad violin` | Teammate dies to camper or bot gets knifed |
| **hype** | `air horn`, `MLG air horn`, `let's go` | 3k spray transfer or clean ace |
| **shock** | `vine boom`, `wow`, `oh my god` | AWPed through a door or sudden jump scare |
| **roast** | `bruh`, `oof`, `emotional damage` | Player misses full magazine or enemy gets rekt |
| **clutch** | `sheesh`, `nice`, `oh baby a triple` | Winning a 1v2 round with 5 HP remaining |
| **panic** | `oh no no no`, `nooo`, `scream` | Hearing 5 terrorists rushing your site |
| **bad_play** | `bonk`, `wasted`, `why are you running` | Friendly fire or failing a ladder jump |
| **celebrate_kill** | `hitmarker`, `airhorn short`, `dun dun dun` | Crisp AK-47 one-tap headshot |
| **bomb_alert** | `alarm`, `metal gear alert`, `here we go again` | "The bomb has been planted!" |
| **sus_or_tease** | `among us sus`, `hehe boy`, `laughing` | Camping in shadows or sneaking behind someone |

---

## ⚙️ How the Sound Engine Works

1. **Volume Normalization**: The audio player normalizes volume so clips do not blow out your ears.
2. **Anti-Spam Cooldown**: A global limiter prevents sound spam (default: max 1 sound every 4 seconds).
3. **Random Variety**: The engine will not repeat the same sound file twice in a row.
4. **Graceful Fallback**: If a folder is empty, the sound is quietly skipped with a single log warning, and text chat continues normally.
