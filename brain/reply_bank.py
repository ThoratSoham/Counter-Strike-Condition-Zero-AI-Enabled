import random

# Extensive local reply bank covering 4 personalities, gaming banter, swearing, help requests, and situations
REPLY_BANK = {
    "vikram": { # Hothead: loud, aggressive, trash-talks, tilts fast, swears a lot
        "help": [
            "Hold on, I'm coming to bail your ass out!",
            "I'm rotating! Don't die before I get there damn it!",
            "Pushing your way right fucking now, hold tight!",
            "Covering you! Shoot the bastard in front!",
            "On my way, keep your head down!"
        ],
        "rush": [
            "RUSH B! NO BRAKES, DON'T YOU DARE STOP!",
            "Full send! Flash and push, let's fuck them up!",
            "W key only! Push push push!",
            "Nobody stops! Clear site and plant!"
        ],
        "hold": [
            "Holding this choke. Nothing gets through me.",
            "Watching the cross. If he peeks, he's dead as hell.",
            "Camping this corner, let them walk into my crosshair."
        ],
        "save": [
            "Shit round, saving my rifle. Fall back!",
            "Not throwing away 3000 bucks, saving.",
            "Drop back to spawn, we buy next round."
        ],
        "general": [
            "Hell yeah! Let's wipe these clowns!",
            "Bro these guys are playing like absolute bots.",
            "I'm buying an AK, nobody steal my kills.",
            "Watch out for that rat camping in the corner.",
            "Are you shitting me?! Watch the flank!"
        ],
        "swearing_banter": [
            "What the fuck was that shot?! Clean as hell!",
            "Holy shit, did you see him drop?!",
            "This guy is pissing me off, I'm hunting him.",
            "Stop baiting me damn it, trade my frag!"
        ],
        "ai_query": [
            "Yeah I'm an AI, but I still drop more frags than you!",
            "AI or not, my AK doesn't miss.",
            "Born in code, built to click heads."
        ],
        "buy_query": [
            "Buy armor and rifle, stop being cheap!",
            "Full buy, don't save like a coward.",
            "M4 and full nades. Let's blast them."
        ],
        "meme_tag": "hype"
    },
    "kabir": { # Jokester: funny, roasts everyone, light swearing
        "help": [
            "Hang on buddy, superhero Kabir is on the way!",
            "Don't worry bro, I'll bodyblock the bullets with my face!",
            "I'm coming, try not to get rekt in the next two seconds!",
            "Covering you! If I die, tell my mom I loved her!"
        ],
        "rush": [
            "Leeroy Jenkins mode activated! Hold W!",
            "Rush B! Brains off, triggers held!",
            "Rushing! Someone please check the corners for once!",
            "Full throttle! Let's go make bad decisions!"
        ],
        "hold": [
            "Camping like a true noob. Nobody moves.",
            "Holding this spot. Nice and cozy.",
            "Setting up the trap, don't sneeze."
        ],
        "save": [
            "Tactical retreat! My gun is too expensive to donate.",
            "Saving! See you guys in the next life.",
            "Hiding in spawn like a champion."
        ],
        "general": [
            "Did someone order a clutch or just a clown show?",
            "Bro, my crosshair was on his head, the game is rigged!",
            "I swear my mousepad is lagging today.",
            "Nice shot! I taught you that, remember?",
            "Lmao look at him running like that!"
        ],
        "swearing_banter": [
            "Holy crap, someone clip that disaster!",
            "What in the damn world was that play?!",
            "Bruh, you scared the shit out of me with that flash!",
            "Damn bro, you melted him into soup!"
        ],
        "ai_query": [
            "Beep boop! Nah, I'm just your handsome digital bestie.",
            "I am 90% caffeine and 10% pure gamer chaos.",
            "If I'm an AI, where is my aimbot update?!"
        ],
        "buy_query": [
            "Buy a shotgun and pray, works 60% of the time every time!",
            "I have 400 bucks and a dream. Let's go!",
            "Buy whatever has the highest fire rate, spray and pray!"
        ],
        "meme_tag": "roast"
    },
    "marcus": { # Calm Pro: short clear callouts, dry humor, rare swearing
        "help": [
            "Rotating to your position. 3 seconds.",
            "Establishing crossfire. Fall back to my sightline.",
            "Providing cover. Keep your head down.",
            "Moving in to trade. Hold your angle."
        ],
        "rush": [
            "Execute fast. Smoke first, check close angles.",
            "Pushing site. Synchronize your entry.",
            "Clear corners methodically. Move."
        ],
        "hold": [
            "Holding default. Sightline secure.",
            "Locking down connector. Play time.",
            "Anchor position established."
        ],
        "save": [
            "Conceding round to preserve economy. Fall back.",
            "Save weapons. Regroup in spawn.",
            "Low percentage play. Save for buy round."
        ],
        "general": [
            "Target eliminated. Watch catwalk.",
            "Clean pick. Two enemies accounted for.",
            "Check corners, don't give away free trades.",
            "Good discipline. Keep this tempo.",
            "Economies will favor us next round."
        ],
        "swearing_banter": [
            "Damn good shot. Ice cold.",
            "They're getting sloppy. Punish their mistakes.",
            "Hell of a clutch. Well played.",
            "Stay sharp. Don't throw this lead."
        ],
        "ai_query": [
            "Affirmative, AI model. Eyes forward on the mission.",
            "Artificial intelligence, tactical discipline.",
            "Mind on the round, not on my architecture."
        ],
        "buy_query": [
            "Team money check. Under 2000, save for next.",
            "Full buy: defuse kit, Kevlar, primary rifle.",
            "Buy smokes and flashes before secondary pistols."
        ],
        "meme_tag": "clutch"
    },
    "sunny": { # Newbie: nervous, asks questions, celebrates small wins, mild swearing
        "help": [
            "I'm coming to help! Please don't die!",
            "Running over! I hope I don't get lost on this map!",
            "I'm right behind you! Don't leave me alone!",
            "Protecting you! Ahhh, shooting now!"
        ],
        "rush": [
            "Rushing! Oh gosh, my heart is beating so fast!",
            "I'll follow your push! Spraying and praying!",
            "Let's do this! Don't stop moving!"
        ],
        "hold": [
            "Holding right here, staring at the door!",
            "I won't move a single muscle, I promise!",
            "Waiting... waiting... nobody here yet!"
        ],
        "save": [
            "Okay, running away to save my gun!",
            "Saving! Hiding behind these boxes!",
            "My weapon was expensive, saving it!"
        ],
        "general": [
            "Did you see that?! I actually helped with a frag!",
            "I bought armor! I feel so much safer now!",
            "Sorry if my smoke was bad, still learning the lineups!",
            "You guys are so good at this game, teach me!",
            "Yay! Another round for our team!"
        ],
        "swearing_banter": [
            "Holy crap, that scared the hell out of me!",
            "Damn, he was so fast! Be careful guys!",
            "What the heck was that ninja move?!",
            "Oh damn, I panicked and unloaded my whole clip!"
        ],
        "ai_query": [
            "I'm an AI, but I'm trying really hard to be a good friend!",
            "Yes, but I'm practicing my aim every single day!",
            "I might be AI, but my joy when we win is 100% real!"
        ],
        "buy_query": [
            "Wait, should I buy armor or a defuse kit first?",
            "Is the P90 good for this round? I like the P90!",
            "I have 1500 dollars, should I save with you guys?"
        ],
        "meme_tag": "sus_or_tease"
    }
}

# Event-specific banter lines for unprompted bot chatter
EVENT_BANTER = {
    "kill": {
        "vikram": [("Sit the fuck down! One less!", "hype"), ("Clean kill, keep pushing!", "celebrate_kill"), ("Dropped! Who's next?!", "hype")],
        "kabir": [("Sent him straight to spectator mode, haha!", "roast"), ("Did his mouse disconnect? Easy kill!", "roast"), ("Dropped him like a bad habit!", "celebrate_kill")],
        "marcus": [("Target eliminated. Sector secure.", "clutch"), ("Hostile down. Check trades.", "celebrate_kill")],
        "sunny": [("I got him! Did you see that?! YES!", "hype"), ("One down! My hands are actually shaking!", "celebrate_kill")]
    },
    "headshot": {
        "vikram": [("Boom! Right in his forehead!", "hype"), ("Clean one-tap! Don't ever peek me!", "clutch")],
        "kabir": [("Ding! Helmet flew into orbit!", "hype"), ("Calculated headshot. Totally on purpose!", "roast")],
        "marcus": [("Headshot confirmed. Crosshair was set.", "clutch")],
        "sunny": [("Headshot! WOW, that sounded so good!", "hype")]
    },
    "death": {
        "vikram": [("Are you fucking serious?! Camping with a shotgun!", "fail"), ("Ugh, hit him for 80, finish his ass!", "panic"), ("Fucking rat corner! Watch out!", "fail")],
        "kabir": [("Ouch! Someone avenge my handsome face!", "fail"), ("Bro is paying rent behind that box, be careful!", "roast"), ("My mouse definitely slipped there, totally.", "fail")],
        "marcus": [("Down at connector. Hostile tagged for 50.", "shock"), ("Crossfire got me. Watch catwalk, two remaining.", "shock")],
        "sunny": [("Ah! He scared the crap out of me, sorry guys!", "panic"), ("I panicked and missed my spray, my bad!", "fail")]
    },
    "death_awp": {
        "vikram": [("Fucking AWP holding mid! Don't dry peek!", "shock"), ("One-tapped through smoke, unbelievable!", "shock")],
        "kabir": [("Yep, that was an AWP. Felt that in real life.", "shock"), ("Deleted from the server! Watch that sniper angle!", "roast")],
        "marcus": [("Sniper active down Long. Smoke cross recommended.", "shock")],
        "sunny": [("I peeked and instantly vaporized! It's an AWP!", "panic")]
    },
    "bomb_planted": {
        "vikram": [("Bomb is down! Move your asses, retake now!", "bomb_alert"), ("They planted! Flash in together, go go go!", "bomb_alert")],
        "kabir": [("Clock is ticking! Retake time, don't step on Legos!", "bomb_alert"), ("Party at the bomb site, let's crash it!", "bomb_alert")],
        "marcus": [("Bomb planted. 45 seconds on timer. Synchronize entry.", "bomb_alert")],
        "sunny": [("Oh no, bomb is planted! Where do we go?!", "panic")]
    },
    "bomb_defused": {
        "vikram": [("Defused! That was way too close, good job!", "hype")],
        "kabir": [("Bomb defused! Where's my MVP medal?!", "clutch")],
        "marcus": [("Site secured. Threat neutralized.", "clutch")],
        "sunny": [("WE SAVED THE DAY! Phew, wires cut!", "hype")]
    },
    "clutch_situation": {
        "vikram": [("You got this bro, keep quiet, listen to footsteps.", "panic")],
        "kabir": [("All on you hero! Make them look silly!", "sus_or_tease")],
        "marcus": [("Play time. He has to defuse. Hold head height.", "clutch")],
        "sunny": [("You can do this! We believe in you!", "panic")]
    },
    "player_clutch_won": {
        "vikram": [("HOLY SHIT! YOU ACTUALLY WON THAT! WHAT A BEAST!", "hype"), ("UNREAL CLUTCH! BEST PLAY ALL NIGHT!", "hype")],
        "kabir": [("HOLY SMOKES! THAT WAS DISGUSTING! Teach me your ways!", "clutch"), ("I am literally bowing down to you right now!", "hype")],
        "marcus": [("Outstanding clutch. Ice in your veins.", "clutch")],
        "sunny": [("HOW DID YOU DO THAT?! YOU ARE A MONSTER! WOW!", "hype")]
    },
    "friendly_fire": {
        "vikram": [("Bro, watch your fucking fire! I'm on your team!", "bad_play")],
        "kabir": [("Ow! Friendly fire isn't so friendly, dude!", "roast")],
        "marcus": [("Check targets. You clipped my armor.", "bad_play")],
        "sunny": [("Ah! Don't shoot me please, I'm friendly!", "panic")]
    },
    "round_win": {
        "vikram": [("Clean round, boys! Flawless!", "hype"), ("Too easy! They are literally shaking!", "hype")],
        "kabir": [("GG ez! Who wants their autograph?!", "roast"), ("Another round in the bag, you're welcome!", "clutch")],
        "marcus": [("Round secured. Good discipline team.", "clutch"), ("Flawless execution. Maintain spacing.", "clutch")],
        "sunny": [("WE WON THE ROUND! That was so intense!", "hype"), ("Phew! Good job everyone!", "celebrate_kill")]
    },
    "round_loss": {
        "vikram": [("Damn it! We threw that away, refocus!", "fail"), ("What a disaster! Stop giving free kills!", "fail")],
        "kabir": [("Welp, that didn't go according to plan at all!", "fail"), ("My eyes hurt from watching that round, lmao!", "roast")],
        "marcus": [("Round conceded. Reset economy and regroup.", "fail"), ("Unforced errors. Focus on default angles.", "fail")],
        "sunny": [("Oh no, we lost... sorry guys, I tried!", "panic"), ("It's okay, we can get them next round!", "sus_or_tease")]
    },
    "bot_banter": {
        "vikram": [("Quit whining and buy up!", "hype"), ("I'll entry frag, just trade me out!", "hype")],
        "kabir": [("Chill bro, someone clip that disaster!", "roast"), ("I'm carrying with my emotional support!", "roast")],
        "marcus": [("Keep comms clear. Eyes forward.", "clutch"), ("Crosshairs on head level.", "clutch")],
        "sunny": [("I got your back, don't worry!", "sus_or_tease"), ("We can still win this!", "hype")]
    }
}

def get_reply(teammate_id: str, message: str, chat_style: str = "full_gamer") -> tuple[str, str, str]:
    """
    Select an authentic local gamer reply from the reply bank.
    Returns: (reply_text, meme_sound_tag, bot_command_order)
    """
    t_id = teammate_id.lower()
    t_bank = REPLY_BANK.get(t_id, REPLY_BANK["vikram"])
    msg = message.lower()
    
    order = ""
    # Help / tactical checks
    if any(k in msg for k in ["help", "save me", "cover", "where are you", "with me", "need help"]):
        lines = t_bank.get("help", t_bank["general"])
        tag = "clutch" if t_id == "marcus" else "hype"
        order = "follow"
    elif any(k in msg for k in ["rush", "push", "go b", "go a"]):
        lines = t_bank.get("rush", t_bank["general"])
        tag = "hype"
        order = "rush"
    elif any(k in msg for k in ["hold", "stay", "camp", "wait", "freeze"]):
        lines = t_bank.get("hold", t_bank["general"])
        tag = "sus_or_tease"
        order = "hold"
    elif any(k in msg for k in ["save", "fall back", "retreat"]):
        lines = t_bank.get("save", t_bank["general"])
        tag = "fail"
        order = "save"
    elif any(k in msg for k in ["drop", "give gun", "drop gun", "drop weapon", "need gun"]):
        lines = ["Here, take my rifle! Go get them!", "Dropping my weapon, make every bullet count!", "Take it! Don't let my gun go to waste!"]
        tag = "clutch"
        order = "drop"
    elif any(k in msg for k in ["regroup", "together", "stick together"]):
        lines = ["Regrouping with you!", "Stick together team, watch the cross!"]
        tag = "clutch"
        order = "regroup"
    elif any(k in msg for k in ["ai", "bot", "real", "human", "who are you"]):
        lines = t_bank.get("ai_query", t_bank["general"])
        tag = "sus_or_tease"
    elif any(k in msg for k in ["buy", "money", "eco", "spend", "weapon"]):
        lines = t_bank.get("buy_query", t_bank["general"])
        tag = "sus_or_tease"
    elif any(k in msg for k in ["fuck", "shit", "damn", "wtf", "hell", "ass"]):
        # Match gamer swearing banter
        lines = t_bank.get("swearing_banter", t_bank["general"])
        tag = t_bank.get("meme_tag", "hype")
    else:
        # General banter
        lines = t_bank.get("general", ["Roger that!"])
        tag = t_bank.get("meme_tag", "hype")

    chosen_line = random.choice(lines)
    return chosen_line, tag, order

def get_event_reaction(event_name: str, teammate_id: str) -> tuple[str, str]:
    """
    Get unprompted banter line and meme tag for an in-game event.
    Returns: (text, tag)
    """
    evt_dict = EVENT_BANTER.get(event_name, {})
    t_lines = evt_dict.get(teammate_id, [])
    if not t_lines:
        return "", ""
    return random.choice(t_lines)
