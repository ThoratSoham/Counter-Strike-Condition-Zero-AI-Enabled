import time
import random
from collections import deque

# 4 Personalities:
# Vikram: Hothead (loud, rages fast, blames everyone, CAPS when angry, loves hype/roast/fail_sad/hindi_swear)
# Kabir: Jokester (roasts everyone, puns, fake stories, memes, loves roast/laugh/shock)
# Marcus: Calm Pro (dry humor, short lines, savage one-liners, rarely swears, loves praise/kill_headshot/clutch)
# Sunny: Newbie (nervous, asks silly questions, gets bullied, fights back, loves shock/apology_getup/fail_sad)

# Situations:
# 1. idle_chat
# 2. kill
# 3. death
# 4. bomb
# 5. round_win
# 6. round_loss
# 7. fight_start
# 8. fight_peak
# 9. make_up
# 10. roast_player

def _build_vikram_lines():
    lines = []
    # 1. idle_chat (40 lines)
    idle = [
        ("Bro my ping is 400 right now, this server is hosted on a potato.", None),
        ("If anyone bait-blocks me at the door again I am throwing a flash at your feet.", "roast"),
        ("Hold W this round. Nobody stop, I swear to god.", "hype"),
        ("Why does this map have so many useless boxes?!", None),
        ("Whoever bought a shotgun on an eco round needs therapy.", "roast"),
        ("My mouse sensor just glitched, don't look at my crosshair.", None),
        ("I smell campers in dark corner. I am pre-firing everything.", None),
        ("Next round we rush A. No discussion, just full speed.", None),
        ("Bro I drank three Red Bulls before this match, my hands are vibrating.", "hype"),
        ("Can we actually buy rifles or are we donating money to the enemy?", None),
        ("Listen to me: flash high, swing together, don't be cowards.", None),
        ("If I die first, it means I created space. You guys better trade me!", None),
        ("My mom is knocking on my door asking why I am shouting.", "laugh"),
        ("Who threw that smoke last round? It covered literally nothing!", "roast"),
        ("I hate this map with a burning passion.", "fail_sad"),
        ("I am buying Deagle. One tap or zero tap, no in between.", None),
        ("Stop crouching in spawn! The round started 10 seconds ago!", "roast"),
        ("If you see me pushing, DO NOT STOP BEHIND ME.", None),
        ("Bro I swear my bullets are passing straight through their chests.", "shock"),
        ("This game has zero hit registration today, absolutely zero.", None),
        ("Whoever kills the sniper gets my respect for the rest of this match.", "praise"),
        ("Don't make any noise, let them walk into us... OR JUST RUSH!", "hype"),
        ("My headset is on 100% volume, my ears are ringing.", None),
        ("Is it just me or is the enemy team playing like actual sweatlords?", None),
        ("I am NOT saving this round, I don't care if it's 1v4.", "hype"),
        ("Drop me an AK someone! Come on, I know you have 6000 bucks!", None),
        ("Every time I check one angle, they peek from the other. Every single time!", "roast"),
        ("I bet my entire inventory we win this round.", "hype"),
        ("Why am I the only one who buys defuse kits on CT side?!", "roast"),
        ("Hold your angles, don't get greedy!", None),
        ("If they smoke tunnel again I am running straight through it.", None),
        ("Bro someone tell Sunny to stop staring at the sky.", "laugh"),
        ("Kabir stop making jokes for two seconds and watch the flank!", "shut_up"),
        ("Marcus, do not miss that sniper shot or I'm taking your AWP.", "roast"),
        ("My keyboard spacebar is sticking, great timing as always.", None),
        ("I am going to peek mid. If I die, avenge me immediately.", None),
        ("We are giving them too much map control, push up!", None),
        ("Two words: W KEY. That is the whole strategy.", "hype"),
        ("Don't let them plant, contest the site!", "shock"),
        ("I am locked in now. Nobody talk to me.", None),
    ]
    for text, tag in idle:
        lines.append({"situation": "idle_chat", "text": text, "sound_tag": tag, "mood": "aggressive"})

    # 2. kill (35 lines)
    kills = [
        ("SIT THE HELL DOWN! Don't you ever peek me again!", "kill_headshot"),
        ("BOOM! Clean headshot, erased from existence!", "kill_headshot"),
        ("That's one down! Push push push!", "hype"),
        ("Where do you think you're going?! GOT HIM!", "kill_headshot"),
        ("Get wrecked, clown! Who's next?!", "kill_headshot"),
        ("Dropped him like a sack of bricks!", "hype"),
        ("One tap! CLIP THAT RIGHT NOW!", "hype"),
        ("Try camping against my pre-fire next time!", "roast"),
        ("He thought he had me, WHAT A JOKE!", "laugh"),
        ("Crosshair on his nose, goodbye!", "goodbye"),
        ("Dead! Clear that corner!", None),
        ("Told you I'd hunt that bastard down!", "kill_headshot"),
        ("That's how you clear site! Move in!", "hype"),
        ("Folded him in half! Let's go boys!", "hype"),
        ("Don't peek Vikram, rule number one!", "kill_headshot"),
        ("Headshot! That felt disgustingly good!", "kill_headshot"),
        ("Got the sniper! Path is clear!", "praise"),
        ("Wiped him out! Keep the momentum!", None),
        ("He didn't even have time to blink!", "kill_headshot"),
        ("Another one for the highlight reel!", "hype"),
        ("That guy was talking so much trash, now he's spectating!", "roast"),
        ("One tap Deagle, you love to see it!", "kill_headshot"),
        ("Sent him straight back to main menu!", "goodbye"),
        ("Down! Flank is secure!", None),
        ("Outplayed, outaimed, outclassed!", "hype"),
        ("Did you see that spray transfer?! CLEAN!", "hype"),
        ("Smoking his boots right now!", "kill_headshot"),
        ("Got him through the wall! PURE INSTINCT!", "kill_headshot"),
        ("That's two! Keep pushing!", "hype"),
        ("Another body on the floor! LET'S GO!", "hype"),
        ("He had full armor and still got melted!", "roast"),
        ("Deleted! Clear the rest!", None),
        ("That was for earlier, you camping rat!", "kill_headshot"),
        ("Crushed! Don't let them regroup!", "hype"),
        ("HEADSHOT! That's how it's done!", "kill_headshot")
    ]
    for text, tag in kills:
        lines.append({"situation": "kill", "text": text, "sound_tag": tag, "mood": "hyped"})

    # 3. death (35 lines)
    deaths = [
        ("WHAT THE FUCK WAS THAT SHOT?! He was running sideways!", "fail_sad"),
        ("ARE YOU KIDDING ME?! He had 1 HP left!", "shock"),
        ("He was camping in the darkest corner of the map! Typical!", "roast"),
        ("Bro my bullets vanished into thin air! ZERO DAMAGE!", "fail_sad"),
        ("TRADE ME! HE IS RIGHT THERE ON THE CORNER!", "shock"),
        ("Behind the crates! One hit, he is literally one shot!", None),
        ("Of course he has an AWP holding that angle. OF COURSE.", "fail_sad"),
        ("I got blind-flashed by my own team! Who threw that?!", "roast"),
        ("I hate this game so much right now.", "fail_sad"),
        ("He peeked the exact millisecond I looked away!", "shock"),
        ("How did he headshot me while jumping?! EXPLAIN THAT!", "fail_sad"),
        ("Two on site! Don't dry peek like I did!", None),
        ("Fell right into their crossfire, damn it!", "fail_sad"),
        ("Shotgun camper... I am going to lose my mind.", "roast"),
        ("Avenge my death! Don't let him get away with that!", None),
        ("My spray was literally on his chest! 98 in 4 hits?!", "fail_sad"),
        ("I got flanked! Watch behind you guys!", "shock"),
        ("He prefired my soul into another dimension.", "fail_sad"),
        ("Down! Watch out, he's reloading right now!", None),
        ("Unbelievable. Absolutely unbelievable luck.", "fail_sad"),
        ("I swear he heard me breathing through the wall.", "shock"),
        ("GG, my mouse slipped. He's low HP though!", None),
        ("That guy is 100% smurfing, nobody hits that running shot.", "roast"),
        ("Died to a grenade at 15 HP, embarrassing.", "fail_sad"),
        ("Bait traded me... at least someone get the kill!", None),
        ("He's defusing or planting! Hurry up!", "shock"),
        ("Knifed from behind?! NO WAY IN HELL!", "fail_sad"),
        ("I am so tilted right now I can't even see straight.", "fail_sad"),
        ("Just shoot him! He has a pistol only!", None),
        ("One catwalk, tagged 60! Finish him!", None),
        ("I died for your sins, win this round!", "hype"),
        ("I got shot through the wooden door, ridiculous.", "fail_sad"),
        ("Don't let that clown defuse, he is 20 HP!", "shock"),
        ("Dead. Please tell me you guys can close this out.", "fail_sad"),
        ("Goodbye cruel world, avenge my AK!", "goodbye")
    ]
    for text, tag in deaths:
        lines.append({"situation": "death", "text": text, "sound_tag": tag, "mood": "tilted"})

    # 4. bomb (30 lines)
    bombs = [
        ("BOMB IS PLANTED! ROTATE RIGHT NOW!", "shock"),
        ("Defuse it! Defuse it! Stop hunting for exit kills!", "shock"),
        ("I have the bomb, follow me to site! Don't wander off!", None),
        ("Planting! Watch my back, don't let anyone peek!", None),
        ("Bomb down! Defend the package, don't let them touch it!", "hype"),
        ("Tick tick tick, we have like 10 seconds! DEFUSE!", "shock"),
        ("Clear the site first, then plant! Don't be reckless!", None),
        ("Bomb is at B! Rotate through spawn!", "shock"),
        ("Smoke the bomb and stick the defuse! GO GO GO!", "hype"),
        ("Did anyone bring a defuse kit?! NOBODY?! UNREAL!", "roast"),
        ("Planting in open! Protect me!", None),
        ("It's going to blow! RUN FOR YOUR LIVES!", "shock"),
        ("Stick the defuse, I will bodyblock the bullets!", "hype"),
        ("Fake defuse! Bait him out!", None),
        ("Plant secured! Set up crossfire on entrances!", "hype"),
        ("Bomb is dropped at mid! Camp the bomb!", None),
        ("They are ninja defusing! SHOOT THE SMOKE!", "shock"),
        ("Bomb planted, now play smart and don't give free kills!", None),
        ("Listen for the defuse tap! If you hear it, swing!", None),
        ("5 seconds left on the timer! GET OUT OF THERE!", "shock"),
        ("Bomb defused! That was way too close for comfort!", "hype"),
        ("Target bombed! BOOM BABY!", "hype"),
        ("Who dropped the bomb in enemy territory?! Why?!", "roast"),
        ("I'm tapping the defuse, cover my head!", None),
        ("Cover the planter! Don't just stand there watching him!", "roast"),
        ("Bomb planted for long! Hold the sightline!", None),
        ("Defuse secured, round is ours! Clean work!", "praise"),
        ("If that bomb explodes because someone was hunting kills I'm raging.", "roast"),
        ("He is defusing right now! SPRAY HIM!", "shock"),
        ("Bomb is safe, site is on lockdown!", "hype")
    ]
    for text, tag in bombs:
        lines.append({"situation": "bomb", "text": text, "sound_tag": tag, "mood": "urgent"})

    # 5. round_win (30 lines)
    wins = [
        ("THAT IS WHAT I'M TALKING ABOUT! EASIEST ROUND OF MY LIFE!", "hype"),
        ("WIPED THEM OUT! Total destruction!", "hype"),
        ("Nobody can stop us when we actually play together!", "praise"),
        ("Flawless round! Keep this momentum, do not slow down!", "hype"),
        ("They looked like recruit bots out there, honestly!", "roast"),
        ("Hell yeah! Cash money in the bank!", "hype"),
        ("Clean sweep! Send them back to practice mode!", "roast"),
        ("That was clinical. Good trades, good spacing!", "praise"),
        ("We are rolling these guys! Don't get cocky though!", "hype"),
        ("VICTORY! Who said we couldn't clutch this?!", "hype"),
        ("Total domination! Buy up next round boys!", "hype"),
        ("Look at that scoreboard, absolute poetry!", "hype"),
        ("I told you pushing was the right play!", "praise"),
        ("They are tilted off the face of the earth now!", "laugh"),
        ("Another round in the bag, next one is free!", "hype"),
        ("That's round won! Buy armor and utility!", None),
        ("EZ PZ! They didn't even land a hit on me!", "roast"),
        ("My aim is feeling dangerous right now, watch out!", "hype"),
        ("Teamwork makes the dream work! Hell yeah!", "praise"),
        ("Look at them running with their tails between their legs!", "laugh"),
        ("Round won! Do not throw away your weapons!", None),
        ("We just broke their economy, full buy next round!", "praise"),
        ("Crushed them! Keep pressing W!", "hype"),
        ("They cannot handle our pace, keep rushing!", "hype"),
        ("That round was a clinic on how to shoot heads!", "hype"),
        ("Good stuff team, that's whatCondition Zero is all about!", "praise"),
        ("We are unstoppable right now!", "hype"),
        ("Pick up their AWPs, save our money!", None),
        ("Round win! That's how champions play!", "hype"),
        ("Another notch on my belt, let's go again!", "hype")
    ]
    for text, tag in wins:
        lines.append({"situation": "round_win", "text": text, "sound_tag": tag, "mood": "triumphant"})

    # 6. round_loss (30 lines)
    losses = [
        ("We threw that round so hard it hurts physically.", "fail_sad"),
        ("How did we lose a 4v2?! EXPLAIN THAT TO ME!", "shock"),
        ("Absolute clown fiesta. What were we doing?!", "roast"),
        ("Stop giving them 1v1 duels! PLAY TOGETHER!", "roast"),
        ("I am saving my rifle, this round is cooked.", "fail_sad"),
        ("We just handed them that round on a silver platter.", "fail_sad"),
        ("Eco round next, buy nothing but pistols.", None),
        ("I am so mad right now, that was our round to win!", "fail_sad"),
        ("Everyone peeked one by one like action movie henchmen!", "roast"),
        ("Drop your heads in shame, that was embarrassing.", "fail_sad"),
        ("Lost the round because nobody checked the defuse kit.", "roast"),
        ("Reset mentally. Next round we bring the heat.", None),
        ("I need a moment of silence for that round disaster.", "fail_sad"),
        ("Why did we push when the bomb was planted?! WHY?!", "roast"),
        ("That round was depressing. Buy Deagles and pray.", "fail_sad"),
        ("We got outsmarted by bots, I can't believe this.", "roast"),
        ("Terrible crossfire setup. We need to communicate better.", None),
        ("Round lost. I am dead inside.", "fail_sad"),
        ("If we lose another round like that I'm uninstalling.", "fail_sad"),
        ("Save whatever guns you have, don't donate them!", None),
        ("We played that with our monitors turned off.", "roast"),
        ("Ugh, my fault for over-peeking. Reset next round.", "apology_getup"),
        ("That loss stung. Let's make them pay for it now.", "hype"),
        ("Lost round, broken economy. Classic CS moment.", "fail_sad"),
        ("We gave away site for free, literally zero resistance.", "roast"),
        ("Next round is ours, I don't care what guns they have.", "hype"),
        ("Can we please stick to the plan next time?!", "roast"),
        ("Sad round. Don't let it get in your head.", "fail_sad"),
        ("We choked that so bad. Shake it off.", "fail_sad"),
        ("Back to spawn with empty wallets. Pain.", "fail_sad")
    ]
    for text, tag in losses:
        lines.append({"situation": "round_loss", "text": text, "sound_tag": tag, "mood": "angry"})

    # 7. fight_start (25 lines)
    f_start = [
        ("Kabir, what in gods name was that flashbang?!", "roast"),
        ("Bro who taught you to aim, a microwave?!", "roast"),
        ("Are you blind or did you just decide to ignore the radar?!", "roast"),
        ("You literally blocked me in the doorway, you cost me my life!", "roast"),
        ("Why did you bait me like that?! I went in first for YOU!", "roast"),
        ("Did you just steal my AWP off the ground after watching me die?!", "roast"),
        ("Stop telling me how to play when you have 2 kills on round 8!", "roast"),
        ("You have zero game sense, absolutely zero!", "roast"),
        ("Don't tell me to chill, you threw the round!", "roast"),
        ("I swear you are playing for the other team today.", "roast"),
        ("Why are you saving a shotgun in a 2v1?! FIGHT!", "roast"),
        ("You missed a stationary target from three feet away!", "roast"),
        ("Keep talking trash and I'll buy Negev every round.", "roast"),
        ("Who authorized you to buy that weapon on an eco?!", "roast"),
        ("You flashed the entire team! THE ENTIRE TEAM!", "shock"),
        ("Don't look at me, you're the one who lost site!", "roast"),
        ("Are you playing with a steering wheel or what?!", "roast"),
        ("I asked for cover and you ran the opposite direction!", "roast"),
        ("Your crosshair placement makes my eyes bleed.", "roast"),
        ("Did you sneeze during that spray or are you just like that?", "roast"),
        ("Stop giving callouts 10 seconds AFTER you die!", "roast"),
        ("You took 50 HP of my health with team damage!", "roast"),
        ("I swear my pet goldfish has better positioning than you.", "roast"),
        ("Look at the scoreboard before you open your mouth!", "roast"),
        ("You're testing my patience today, I swear.", "roast")
    ]
    for text, tag in f_start:
        lines.append({"situation": "fight_start", "text": text, "sound_tag": tag, "mood": "annoyed"})

    # 8. fight_peak (25 lines)
    f_peak = [
        ("SHUT UP! JUST SHUT UP AND PLAY THE GAME!", "shut_up"),
        ("KYU RE! You think you are s1mple or what?!", "hindi_swear"),
        ("I AM LITERALLY CARRYING YOUR USELESS BODY ON MY BACK!", "roast"),
        ("YOU ARE DRIVING ME CRAZY TODAY, SHUT THE HELL UP!", "shut_up"),
        ("DO NOT TEST ME RIGHT NOW, I AM AT PEAK TILT!", "hindi_swear"),
        ("YOU HAVE BEEN SPECTATING MORE THAN PLAYING ALL MATCH!", "roast"),
        ("THAT'S IT, I'M NOT DROPPING YOU A SINGLE BULLET!", "roast"),
        ("EVERY SINGLE ROUND YOU DIE IN THE FIRST FIVE SECONDS!", "roast"),
        ("GET OUT OF MY SIGHT, GO CAMP IN SPAWN!", "shut_up"),
        ("I WOULD RATHER PLAY WITH A BOT THAN WITH YOU RIGHT NOW!", "roast"),
        ("STOP TYPING IN CHAT AND USE YOUR HEAD FOR ONCE!", "shut_up"),
        ("I SWEAR ON EVERYTHING YOU ARE THROWING ON PURPOSE!", "hindi_swear"),
        ("TALK TO MY SCOREBOARD, YOU BOTTOM FRAGGER!", "roast"),
        ("CLOSE YOUR MOUTH BEFORE MY HEAD EXPLODES!", "shut_up"),
        ("YOU COST US THREE ROUNDS IN A ROW WITH THAT NONSENSE!", "roast"),
        ("UNBELIEVABLE AUDACITY FROM SOMEONE WITH ZERO ASSISTS!", "roast"),
        ("I AM ABOUT TO FLASH YOU ON PURPOSE NEXT ROUND!", "hindi_swear"),
        ("DO YOU EVEN HAVE A MONITOR TURNED ON?!", "roast"),
        ("DON'T BLAME THE LAG, YOUR BRAIN IS LAGGING!", "roast"),
        ("SHUT YOUR TRAP AND DEFEND THE SITE!", "shut_up"),
        ("I'VE HAD ENOUGH OF YOUR EXCUSES, ENOUGH!", "shut_up"),
        ("YOU ARE LUCKIER THAN YOU ARE SKILLED!", "roast"),
        ("SIT IN A CORNER AND LET ADULTS HANDLE THE CLUTCH!", "roast"),
        ("STOP RUNNING YOUR MOUTH, YOU LOST US THE LEAD!", "shut_up"),
        ("I AM DONE TALKING TO YOU THIS MATCH!", "shut_up")
    ]
    for text, tag in f_peak:
        lines.append({"situation": "fight_peak", "text": text, "sound_tag": tag, "mood": "enraged"})

    # 9. make_up (25 lines)
    m_up = [
        ("Alright alright, I overreacted. My bad bro.", "apology_getup"),
        ("Whatever, you made a good shot just now. We're cool.", "praise"),
        ("Sorry for shouting, just got tilted. Let's win this.", "apology_getup"),
        ("Fine, I'll drop you an AK next round. Truce.", "apology_getup"),
        ("Look, we both played like clowns there. Let's lock in.", "laugh"),
        ("Sorry bhai, heated gamer moment. High five?", "apology_getup"),
        ("Okay that joke was actually funny, you got me.", "laugh"),
        ("I apologize for the flashbang insult. You're still bad though!", "laugh"),
        ("Shake hands, reset mental. We need this match.", "praise"),
        ("My bad for raging, mom brought me snacks. We good.", "apology_getup"),
        ("Nice kill back there, redeemed yourself completely.", "praise"),
        ("Truce called. Let's channel that anger into the enemies.", "hype"),
        ("Sorry bro, shouldn't have yelled. We're a team.", "apology_getup"),
        ("Lmao we argued for three minutes while the bomb exploded.", "laugh"),
        ("Alright I forgive you, but don't steal my AWP again.", "apology_getup"),
        ("We fight like an old married couple, let's just win.", "laugh"),
        ("All love bro, you know I get passionate about CS.", "apology_getup"),
        ("I take back what I said about your aiming microwave.", "laugh"),
        ("Good trade there, all is forgiven.", "praise"),
        ("Sorry for barking, let's take back the lead.", "apology_getup"),
        ("We are terrifying when we work together, truce.", "hype"),
        ("My bad for the team flash, I owe you a Deagle.", "apology_getup"),
        ("Okay you clutched it, you're the boss now.", "praise"),
        ("Friends again? Good, now cover my cross.", "apology_getup"),
        ("Peace restored in the squad, let's destroy them.", "hype")
    ]
    for text, tag in m_up:
        lines.append({"situation": "make_up", "text": text, "sound_tag": tag, "mood": "relieved"})

    # 10. roast_player (30 lines)
    r_player = [
        ("Bro player, who taught you to aim like that?!", "roast"),
        ("Did you just miss that entire clip on a sleeping guy?!", "laugh"),
        ("Player carried by pure luck, you love to see it!", "roast"),
        ("Hey boss, your crosshair was having an existential crisis there.", "laugh"),
        ("Player, don't worry, I saw you trying your best!", "roast"),
        ("Nice try player, next time try clicking the enemy!", "roast"),
        ("Bro player is playing with 2000 DPI and prayer.", "laugh"),
        ("I baited for you player and you stared at the floor!", "roast"),
        ("Player, are you playing on a trackpad right now?!", "roast"),
        ("That was the most creative miss I have ever witnessed.", "laugh"),
        ("Player, please tell me your screen is plugged in.", "roast"),
        ("Bro player has a personal vendetta against door frames.", "laugh"),
        ("I believe in you player, even when your bullets don't!", "praise"),
        ("Player, you scared the wall more than the enemy!", "laugh"),
        ("Don't worry player, we will carry your heavy backpack!", "roast"),
        ("Player just invented a new shooting technique: zero damage.", "roast"),
        ("Are your hands cold player or is your mouse on ice?!", "roast"),
        ("Player, drop me the rifle before you hurt yourself!", "roast"),
        ("That was an accidental masterpiece of a miss, player.", "laugh"),
        ("Player, your crosshair was looking at the birds in the sky!", "roast"),
        ("I saw that 1v1 player... I won't tell anyone, promise.", "laugh"),
        ("Player, that flashbang bounced off the frame and blinded YOU!", "shock"),
        ("Good hustle player, terrible execution though!", "roast"),
        ("Player is playing chess while we are playing CS.", "laugh"),
        ("Next time player, aim slightly to the left of infinity.", "roast"),
        ("Player, buy an AWP, at least then you have an excuse to miss!", "roast"),
        ("I love you player, but that was tragic to watch.", "fail_sad"),
        ("Player, did your cat jump on your keyboard just now?!", "laugh"),
        ("Player is playing pacifist route in Condition Zero.", "roast"),
        ("We still love you player, just don't do that again!", "praise")
    ]
    for text, tag in r_player:
        lines.append({"situation": "roast_player", "text": text, "sound_tag": tag, "mood": "playful"})

    return lines

def _build_kabir_lines():
    lines = []
    # 1. idle_chat (40 lines)
    idle = [
        ("Guys, my mom just said dinner is ready in 5 minutes. Win fast!", "laugh"),
        ("Fun fact: 99% of my missed shots are due to solar flares.", "roast"),
        ("I am running on 2 hours of sleep and pure meme energy.", "hype"),
        ("Whoever planted the bomb in the open has big chaotic energy.", "laugh"),
        ("Vikram, chill out bro, your blood pressure is peaking on my radar.", "roast"),
        ("My mousepad feels like sandpaper today. Unplayable.", "roast"),
        ("Bro I just heard footstep... wait, that was my stomach growling.", "laugh"),
        ("If we lose, I am blaming Sunny. It's in the contract.", "roast"),
        ("Can we do a synchronized crouch jump into site for style points?", "hype"),
        ("I have 800 bucks. Should I buy two flashbangs and blind everyone?", "laugh"),
        ("I bet 100 rupees Marcus hits an insane no-scope this round.", "praise"),
        ("Why does the terrorist model look like my gym teacher?", "laugh"),
        ("Did you guys know if you hold W you move forward? Mind blown.", "laugh"),
        ("Someone give me a weapon or I will follow you with a knife.", "roast"),
        ("Bro this server tickrate is sponsored by dial-up internet.", "roast"),
        ("I am holding mid with a pistol and a dream.", "hype"),
        ("Hey guys, what if the enemies are actually really nice people?", "laugh"),
        ("Vikram is fuming already, someone play elevator music in comms.", "shut_up"),
        ("I just bought a smoke, prepare for the worst lineup in history.", "laugh"),
        ("Sunny, if you shoot me in the back again I am taking your lunch money.", "roast"),
        ("I heard crouching makes your bullets 500% more accurate, trust.", "laugh"),
        ("Can we please rush B like real gentlemen?", "hype"),
        ("My brother just walked in and asked if I'm losing again. The disrespect.", "roast"),
        ("If I die first, remember me as handsome and brave.", "goodbye"),
        ("I am rating everyone's skins today. Vikram: 2 out of 10.", "roast"),
        ("Guys, my FPS just dropped to cinematic 24 frames.", "roast"),
        ("Don't worry team, I watched a 30-second YouTube guide. I am pro now.", "hype"),
        ("I'm camping behind this box, paying rent and everything.", "laugh"),
        ("Whoever invented flashbangs clearly hated human eyes.", "shock"),
        ("Let's do the legendary ninja strat: walk backwards and shoot.", "laugh"),
        ("Marcus, smile once bro, it won't hurt you.", "roast"),
        ("I'm offering free coaching after this match. 50 bucks an hour.", "laugh"),
        ("Why buy defuse kits when you can defuse with sheer willpower?", "roast"),
        ("I think the enemy team is communicating via telepathy.", "shock"),
        ("Bro I swear that chicken on inferno gave away my position.", "laugh"),
        ("My crosshair is vibrating with positive vibes.", "hype"),
        ("Can we fake A, fake B, and just plant in CT spawn?", "laugh"),
        ("Vikram is typing a 5-page essay right now, I can hear his keys.", "laugh"),
        ("Stay frosty gamers, don't melt under pressure.", "praise"),
        ("If we win this match, pizza is on Vikram!", "hype")
    ]
    for text, tag in idle:
        lines.append({"situation": "idle_chat", "text": text, "sound_tag": tag, "mood": "playful"})

    # 2. kill (35 lines)
    kills = [
        ("LMAOOO look at him fold! Outplayed by Kabir!", "laugh"),
        ("Sheesh! Did you guys see that headshot?!", "hype"),
        ("Get back to the lobby, your free trial of living expired!", "roast"),
        ("Hit him with the classic Kabir special!", "kill_headshot"),
        ("Bruh, he didn't even shoot back! AFK or just shocked?!", "laugh"),
        ("Boom! Another victim of my superior gaming chair!", "kill_headshot"),
        ("Sent him to the shadow realm, no return ticket!", "goodbye"),
        ("Clip that! Put some goofy music over it!", "laugh"),
        ("He thought he had me, emotional damage!", "roast"),
        ("Look ma, no hands! Headshot!", "kill_headshot"),
        ("That was so dirty I need to take a shower.", "laugh"),
        ("Target eliminated! Marcus, rate that shot 1 to 10!", "praise"),
        ("Bro got deleted faster than my browser history!", "laugh"),
        ("He ran straight into my crosshair! What a nice guy!", "roast"),
        ("Another frag for the MVP! Don't look at the scoreboard!", "hype"),
        ("One tap! Even I didn't expect that to hit!", "shock"),
        ("Folded like a cheap lawn chair!", "laugh"),
        ("Kabir delivery service: one free bullet!", "kill_headshot"),
        ("That guy is definitely slamming his desk right now.", "laugh"),
        ("Oof! That looked like it hurt in real life!", "roast"),
        ("Got him! Someone please wipe the sweat off my forehead!", "hype"),
        ("A gift from Kabir with love!", "goodbye"),
        ("He peeked the corner and met his maker!", "kill_headshot"),
        ("Dropped! Push up before his ghost haunts us!", "laugh"),
        ("I clicked once and magic happened!", "hype"),
        ("That's why they call me the menace of mid!", "hype"),
        ("One shot, one meme! Clean work!", "kill_headshot"),
        ("He tried to jump shot me! Nice circus trick buddy!", "laugh"),
        ("Eliminated! Site is 20% safer now!", "praise"),
        ("Get rekt! Don't forget to like and subscribe!", "laugh"),
        ("That was textbook... from a comedy book!", "laugh"),
        ("Boom headshot! My mom would be so proud!", "kill_headshot"),
        ("Down goes the hero! What a shame!", "roast"),
        ("He gave up the ghost! Keep it moving!", "goodbye"),
        ("That frag was sponsored by pure luck!", "laugh")
    ]
    for text, tag in kills:
        lines.append({"situation": "kill", "text": text, "sound_tag": tag, "mood": "amused"})

    # 3. death (35 lines)
    deaths = [
        ("BRUH. My crosshair was literally kissing his forehead!", "roast"),
        ("I got killed by a guy looking at the floor! UNREAL!", "fail_sad"),
        ("Help, I have fallen and I can't get up!", "fail_sad"),
        ("He was hiding behind that tiny box! What a rat!", "roast"),
        ("My mouse battery died! Okay wait, it's wired, never mind.", "laugh"),
        ("Avenge me brothers! My ghost will spectate and judge!", "goodbye"),
        ("99 in 3 hits! He has ONE single HP remaining!", "shock"),
        ("He shot me through a smoke, a flash, and three walls!", "shock"),
        ("That guy definitely has a better gaming chair than me.", "roast"),
        ("I sacrificed myself so you guys could know his location! You're welcome!", "laugh"),
        ("Oof! Right in the funny bone!", "fail_sad"),
        ("Tell my family I clutched 1v5 in spirit.", "goodbye"),
        ("He had an AWP, I had a pistol and bravery. Bad math.", "fail_sad"),
        ("I got blasted into orbit! Good night everyone!", "goodbye"),
        ("Someone call the police, I was just robbed of a kill!", "shock"),
        ("Dead! Watch catwalk, he's tea-bagging my body right now!", "roast"),
        ("My fingers betrayed me, I pressed G instead of F!", "laugh"),
        ("He prefired before my grandfather was even born.", "roast"),
        ("I'm dead. Vikram, please don't yell at my corpse.", "apology_getup"),
        ("That headshot made a very crunchy sound.", "fail_sad"),
        ("Down! He is reloading, jump him right now!", None),
        ("I slipped on a digital banana peel, honestly.", "laugh"),
        ("Rest in pepperoni to me. Win this round!", "goodbye"),
        ("He got lucky, 100% luck, zero skill involved.", "roast"),
        ("I got flashbanged and when vision returned I was in heaven.", "shock"),
        ("The enemy sniper has a personal grudge against me.", "fail_sad"),
        ("Dead! He's at A site, looking very smug!", None),
        ("I tried to 360 no scope... bad idea in hindsight.", "fail_sad"),
        ("Wasted! Cue the GTA sound effect!", "fail_sad"),
        ("My ping spiked to 900 for that exact second, I swear!", "laugh"),
        ("He hit me with a stray pellet from 50 yards away!", "shock"),
        ("I'm taking a tactical nap on the ground.", "laugh"),
        ("Eliminated! Don't let my death be a meme!", "fail_sad"),
        ("He got me through the crate. Physics has left the chat.", "roast"),
        ("Bye guys, carry me to victory!", "goodbye")
    ]
    for text, tag in deaths:
        lines.append({"situation": "death", "text": text, "sound_tag": tag, "mood": "playful"})

    # 4. bomb (30 lines)
    bombs = [
        ("Bomb has been planted! Queue the action movie soundtrack!", "shock"),
        ("Defusing right now! Nobody distract me with good jokes!", None),
        ("I have the bomb! Where are we taking this package of joy?", None),
        ("Planting! If I die while kneeling, Vikram avenges me!", None),
        ("The ticking is getting aggressive guys! RUN OR DEFUSE!", "shock"),
        ("Fake defuse! He peeked! SHOOT HIM!", "hype"),
        ("Bomb is down at mid! Camping site is now officially open!", "roast"),
        ("Did anyone bring a defuse kit or are we cutting wires with teeth?", "laugh"),
        ("Bomb planted! Free real estate, let's hold it!", "hype"),
        ("10 seconds! Defuse or run! I am choosing RUN!", "shock"),
        ("Planting for long! Watch out for sniper peeks!", None),
        ("Bomb exploded! Wow, what a lovely fireball!", "shock"),
        ("Ninja defuse attempt initiated! Be very very quiet...", "sus_or_tease"),
        ("He is tapping the bomb! It's a trap, don't rush him!", None),
        ("Bomb secure, bad guys defeated! We are heroes!", "praise"),
        ("Who dropped the bomb in spawn?! Was it Sunny again?!", "roast"),
        ("Defuse complete with 0.5 seconds left! My heart just aged 10 years!", "hype"),
        ("Planting the bomb! Marcus cover me, you're the reliable one!", None),
        ("Bomb is ticking like my alarm clock on Monday morning.", "fail_sad"),
        ("Clear the site! Don't let them ambush the defuser!", None),
        ("Bomb dropped! Camp it like your life depends on it, because it does!", "hype"),
        ("I'm sticking the defuse! Pray for me!", "hype"),
        ("Bomb planted at B! B site best site!", "hype"),
        ("They are defusing in smoke! SPRAY AND PRAY BOYS!", "shock"),
        ("Bomb exploded, economy devastated, dignity ruined.", "fail_sad"),
        ("Got the kit! Fast defuse incoming!", "hype"),
        ("Bomb is planted! Everyone pretend we know what we're doing!", "laugh"),
        ("Defused! Give that man a medal and a cookie!", "praise"),
        ("Run away from the bomb! It's gonna BLOW!", "shock"),
        ("Site secured, bomb planted, GG easy!", "hype")
    ]
    for text, tag in bombs:
        lines.append({"situation": "bomb", "text": text, "sound_tag": tag, "mood": "urgent"})

    # 5. round_win (30 lines)
    wins = [
        ("GG EZ! That was smoother than butter on warm toast!", "hype"),
        ("We won! Somebody screenshot this before reality kicks in!", "laugh"),
        ("Great round team! I contributed emotional support!", "laugh"),
        ("Look at that victory! We are practically esports athletes!", "hype"),
        ("They got folded into origami that round!", "laugh"),
        ("Cha-ching! Money in the bank, time to buy expensive toys!", "hype"),
        ("Flawless execution! Even Vikram didn't yell once!", "praise"),
        ("Victory royale! Wait wrong game, ROUND WON!", "hype"),
        ("That was poetry in motion! Beautiful teamwork!", "praise"),
        ("They are definitely reporting us for having too much fun.", "laugh"),
        ("Round won! My MVP award will arrive in the mail shortly.", "hype"),
        ("We smoked them like barbecue on Sunday!", "roast"),
        ("I gave them 10 out of 10 for effort, 0 for results.", "roast"),
        ("Clean win! Next round is on me! (Just kidding, buy your own guns)", "laugh"),
        ("Another round in the pocket! Let's ride this wave!", "hype"),
        ("They looked so confused back there, bless their hearts.", "laugh"),
        ("That's what happens when you let Kabir cook!", "hype"),
        ("Round secured! High fives all around!", "praise"),
        ("We are putting on a comedy show and they are the punchline!", "laugh"),
        ("I didn't even have to reload my gun, easiest round ever!", "roast"),
        ("Victory! Buy up boys, let's keep the party going!", "hype"),
        ("That round went by faster than my weekend.", "laugh"),
        ("Solid round team! Marcus, you were majestic back there.", "praise"),
        ("We are breaking their spirits one round at a time!", "hype"),
        ("They must be sweating rivers right now!", "laugh"),
        ("Round win! That's how we roll in Condition Zero!", "hype"),
        ("Can we win every round like that? That was painless!", "praise"),
        ("W! That's a big fat capital W for the boys!", "hype"),
        ("Another round down, on to the next masterpiece!", "hype"),
        ("Good stuff squad! Let's make it a clean sweep!", "praise")
    ]
    for text, tag in wins:
        lines.append({"situation": "round_win", "text": text, "sound_tag": tag, "mood": "amused"})

    # 6. round_loss (30 lines)
    losses = [
        ("Well... that was an artistic interpretation of how to throw a round.", "laugh"),
        ("My disappointment is immeasurable and my day is ruined.", "fail_sad"),
        ("We just gave them that round for free. Black Friday discount!", "roast"),
        ("Oof. Let's pretend that round never happened in game history.", "fail_sad"),
        ("I blame the sun, the moon, and Vikram's angry vibes.", "roast"),
        ("Economy broken, morale broken, my spirit broken.", "fail_sad"),
        ("Next round we buy pistols and rush with power of friendship.", "laugh"),
        ("That round was a disaster masterclass.", "fail_sad"),
        ("We got schooled by people playing on laptops.", "roast"),
        ("Sad violin music intensifies in the background.", "fail_sad"),
        ("Who pushed when we had bomb planted?! Don't all look at me!", "roast"),
        ("We choked harder than someone swallowing an entire apple.", "laugh"),
        ("Loss accepted, learning rejected. Buy Deagles!", "hype"),
        ("That was tragic. I need 10 seconds of grief counseling.", "fail_sad"),
        ("They outplayed us by simply standing still and waiting.", "roast"),
        ("Round lost. I demand a recount!", "laugh"),
        ("Our bank accounts are in tears right now.", "fail_sad"),
        ("Reset mentally guys, even the greatest clowns stumble.", "laugh"),
        ("I would roast everyone but I died first, so my hands are tied.", "roast"),
        ("That round hurt more than stepping on a Lego.", "fail_sad"),
        ("We got caught lackin' in 4K resolution.", "roast"),
        ("Economy reset, eco round incoming. Time to shine with Glock!", "hype"),
        ("It's fine, we are just giving them false hope before the comeback.", "hype"),
        ("That round was painful to watch even from spectator cam.", "fail_sad"),
        ("Nobody talk about that round ever again. Understood?", "shut_up"),
        ("We played that round backwards and blindfolded.", "roast"),
        ("Tragic loss. Let's make them regret winning that.", "hype"),
        ("F in the chat for that round.", "fail_sad"),
        ("Loss registered. Time to unleash the secret tactics!", "hype"),
        ("Ouch. Next round we bounce back like rubber balls!", "hype")
    ]
    for text, tag in losses:
        lines.append({"situation": "round_loss", "text": text, "sound_tag": tag, "mood": "sarcastic"})

    # 7. fight_start (25 lines)
    f_start = [
        ("Vikram, bro, did you forget which mouse button shoots?", "roast"),
        ("Look at Vikram's forehead veins popping through his webcam!", "laugh"),
        ("Are we arguing again? Hold on, let me grab my popcorn!", "laugh"),
        ("Sunny, did you just shoot my knee? Are you checking my reflexes?!", "roast"),
        ("Vikram is blaming his chair again, classic episode 4!", "laugh"),
        ("Hey Vikram, want me to order you herbal tea to calm down?", "roast"),
        ("Who threw that smoke?! It literally landed behind our own team!", "roast"),
        ("Bro your aim is so shaky you could blend a smoothie with it.", "roast"),
        ("Sunny, don't look at me with those puppy eyes, you team-flashed me!", "roast"),
        ("Vikram is in full rage mode, nobody make sudden movements!", "laugh"),
        ("You guys are arguing while the bomb is being planted right next to us.", "roast"),
        ("Did you just bait me to save your 500-dollar pistol?!", "roast"),
        ("Vikram, your trash-talk is 10/10 but your K/D is 2/8.", "roast"),
        ("I can hear Vikram furiously typing on his mechanical keyboard.", "laugh"),
        ("Sunny, buddy, the enemies are the ones wearing the OTHER uniforms.", "roast"),
        ("If I had a nickel for every time Vikram tilted, I'd buy Valve.", "laugh"),
        ("Don't blame me, I was busy looking magnificent at mid.", "roast"),
        ("Are we playing CS or a dramatic soap opera today?!", "laugh"),
        ("Your crosshair was aiming at the skybox, were you hunting pigeons?!", "roast"),
        ("Vikram, breathe in, breathe out... now stop screaming.", "roast"),
        ("I'm not saying you're bad, but the bot has more frags than you.", "roast"),
        ("Did you sneeze during that clutch or did your hands fall off?!", "roast"),
        ("Sunny, please tell me you did that by accident.", "shock"),
        ("Vikram, who hurt you bro?! Was it round 2?!", "laugh"),
        ("Here we go again, round 5 family drama!", "laugh")
    ]
    for text, tag in f_start:
        lines.append({"situation": "fight_start", "text": text, "sound_tag": tag, "mood": "provocative"})

    # 8. fight_peak (25 lines)
    f_peak = [
        ("Oh boy, Vikram is screaming in all caps! World war 3!", "laugh"),
        ("SHUT UP VIKRAM! Even my neighbors are complaining about you!", "shut_up"),
        ("Bro is writing an entire novel in chat instead of shooting!", "roast"),
        ("Emotional damage! Look at Vikram tilt into the stratosphere!", "roast"),
        ("YOU SHUT YOUR MOUTH FATTY! Stop blaming everyone else!", "shut_up"),
        ("I am muting you in real life Vikram, I swear!", "shut_up"),
        ("You have zero chill, zero frags, and 100% noise pollution!", "roast"),
        ("Bruh, your ego is bigger than the entire dust2 map!", "roast"),
        ("STOP SCREAMING IN THE MIC, MY EARDRUMS ARE BLEEDING!", "shut_up"),
        ("LAVDEN BHOJYAM! You talk so much nonsense!", "hindi_swear"),
        ("Go take a cold shower and come back when you have an aimbot!", "roast"),
        ("I'm not listening to you anymore, you're on permanent mute!", "shut_up"),
        ("You missed a point-blank shotgun shot and you're yelling at ME?!", "roast"),
        ("Get out meme sound playing in my head right now!", "shut_up"),
        ("Look at him boil! Somebody bring a tea kettle!", "laugh"),
        ("You are the reason we have an economy crisis every game!", "roast"),
        ("QUIET IN THE COMMS! Clear the channel!", "shut_up"),
        ("Your voice is at 150 decibels right now, tone it down!", "shut_up"),
        ("I'd rather listen to dial-up tone than your excuses!", "roast"),
        ("Stop baiting, stop crying, and play the damn game!", "shut_up"),
        ("You're embarrassing us in front of the spectator cam!", "roast"),
        ("Nobody cares about your excuses, check your scoreboard!", "roast"),
        ("SHUT YOUR MOUTH! Focus on the bomb site!", "shut_up"),
        ("This is peak comedy, someone clip Vikram's meltdown!", "laugh"),
        ("I'm done debating with someone who buys P90 on buy rounds!", "roast")
    ]
    for text, tag in f_peak:
        lines.append({"situation": "fight_peak", "text": text, "sound_tag": tag, "mood": "mocking"})

    # 9. make_up (25 lines)
    m_up = [
        ("Alright bro, sorry for roasting your grandma's aim. We good?", "apology_getup"),
        ("Lmao that was hilarious though. Hug it out, Vikram?", "laugh"),
        ("Sorry bhai! Here, take my Deagle as a peace offering.", "apology_getup"),
        ("Okay truce! We have a match to win, let's stop being clowns.", "apology_getup"),
        ("I take it back, your aim is only 50% toaster, 50% human.", "laugh"),
        ("Sorry for the ear damage bro, let's lock in and win.", "apology_getup"),
        ("Peace treaty signed. Vikram gets the first frag next round.", "praise"),
        ("We argue like brothers, now let's beat these enemies like brothers!", "hype"),
        ("Sorry brother! I bought you a flashbang to make up for it.", "apology_getup"),
        ("That was peak gamer drama. Now back to business!", "laugh"),
        ("I apologize for laughing at your death... it was funny though!", "laugh"),
        ("Alright, truce called. Don't tell mom we fought.", "apology_getup"),
        ("Good trade there, all past sins are erased!", "praise"),
        ("My bad for trolling you Vikram, you're the best entry fragger.", "apology_getup"),
        ("We are terrifying when we are on the same page. Let's go!", "hype"),
        ("Sorry bhai ne bola karne ka toh karne ka, truce!", "apology_getup"),
        ("I'm sorry, you're sorry, the enemy team is about to be sorry.", "hype"),
        ("Friends again! Now drop me an AK, friend!", "laugh"),
        ("Look at us making up like true gentlemen of Counter-Strike.", "laugh"),
        ("I forgive your rage if you forgive my jokes.", "apology_getup"),
        ("That's what makes us the best squad, no hard feelings!", "praise"),
        ("Shake hands, reset mental, destroy enemies.", "hype"),
        ("Sorry for the friendly fire earlier, my finger slipped!", "apology_getup"),
        ("Back on track! The dream team is reunited!", "hype"),
        ("All good in the hood! Let's get this victory!", "praise")
    ]
    for text, tag in m_up:
        lines.append({"situation": "make_up", "text": text, "sound_tag": tag, "mood": "relieved"})

    # 10. roast_player (30 lines)
    r_player = [
        ("Player bro, did you forget to plug in your mouse today?", "laugh"),
        ("Look at player's crosshair doing the macarena on screen!", "laugh"),
        ("Player, that was the most cinematic miss in gaming history.", "roast"),
        ("Hey player, the enemy was standing still and you shot the sky!", "laugh"),
        ("Player, don't worry, the wall you shot is definitely dead now.", "roast"),
        ("I love you player, but your aiming needs an exorcism.", "laugh"),
        ("Player, did you just try to knife him from 20 meters away?!", "shock"),
        ("Player is playing with trackball mouse and sheer courage.", "laugh"),
        ("Nice attempt player! Next time try pointing at the bad guy!", "roast"),
        ("Player, are you playing on 300 ping or is that just your style?!", "laugh"),
        ("I watched player's POV and my vertigo came back.", "roast"),
        ("Player just donated full armor and an M4 to the charity foundation.", "roast"),
        ("Bro player, who is your sponsor? The enemy team?!", "laugh"),
        ("Player, you flashed all four of us and yourself! PENTAKILL!", "shock"),
        ("Look at player dodging bullets like Neo in the Matrix!", "praise"),
        ("Player, that smoke lineup landed in a completely different map.", "laugh"),
        ("Don't worry player, we'll carry you across the finish line!", "praise"),
        ("Player, you shot 30 bullets and hit the air molecules!", "roast"),
        ("Player is playing stealth mode: don't hurt anyone, stay peaceful.", "laugh"),
        ("Player, I'll trade my weapon for your confidence any day!", "roast"),
        ("Hey player, press left click to shoot, just a friendly reminder!", "laugh"),
        ("Player just gave the enemy a haircut with that spray!", "roast"),
        ("Player, did your monitor fall off the desk mid-firefight?!", "laugh"),
        ("I saw player's crosshair shaking like an earthquake hit.", "roast"),
        ("Player, you're the VIP of our hearts, just maybe not the scoreboard.", "praise"),
        ("Player, that grenade bounced back and took 40 of your own HP!", "shock"),
        ("Player is out there making memories, not kills.", "laugh"),
        ("Next time player, let Kabir do the shooting and you do the posing!", "roast"),
        ("Player, you survived 1v3 by hiding in the bathroom, legend!", "laugh"),
        ("We love our human player! Best mascot in Condition Zero!", "praise")
    ]
    for text, tag in r_player:
        lines.append({"situation": "roast_player", "text": text, "sound_tag": tag, "mood": "playful"})

    return lines

def _build_marcus_lines():
    lines = []
    # 1. idle_chat (40 lines)
    idle = [
        ("Comms clear. Eyes on catwalk and long.", None),
        ("Holding default sightline. Nobody cross without smoke.", None),
        ("AWP is loaded. One bullet, one target.", "praise"),
        ("Discipline team. Do not over-extend.", None),
        ("I hear steps upper tunnels. Two minimum.", "shock"),
        ("Vikram, maintain your angle. Don't rush alone.", None),
        ("Save economy this round. Buy armor only.", None),
        ("Sightlines secure. Waiting for their contact.", None),
        ("They favor B rushes on eco rounds. Be ready.", None),
        ("Keep spacing. Do not bunch up in chokepoints.", None),
        ("I have the crosshair on mid doors. First head drops.", "praise"),
        ("Clear corners methodically. Don't rush blind.", None),
        ("Sunny, stay behind me. Trade my contact if I fall.", None),
        ("Patience wins rounds, not chaos.", None),
        ("Enemy sniper is aggressive. I will bait his shot.", None),
        ("Flash high on three. Execute together.", None),
        ("Watching the flank. Nothing gets past this corridor.", None),
        ("Economy is fragile. Avoid unnecessary trades.", None),
        ("Two catwalk, one dark. Standard setup.", None),
        ("Comms quiet. Listen for footstep audio.", "shut_up"),
        ("I have 4700. Dropping rifle for Vikram.", None),
        ("Hold site until bomb is spotted. Do not rotate early.", None),
        ("They are predictable. Third time they smoke mid.", None),
        ("Take space slowly. Clear left first.", None),
        ("Solid setup. Hold until 45 seconds.", None),
        ("Sniper down, site control is ours.", "kill_headshot"),
        ("Check vents before planting.", None),
        ("Play for the bomb drop. Do not hunt.", None),
        ("Kabir, watch tunnel. Stop checking scoreboard.", "roast"),
        ("Precision beats speed.", "praise"),
        ("Crossfire established. Let them walk in.", None),
        ("Maintain crosshair placement at head level.", None),
        ("They have low utility remaining. Push advantage.", None),
        ("I will anchor site. Rotate only on visual contact.", None),
        ("Check your corners. Clear.", None),
        ("Reloading in cover. Covering angle in three.", None),
        ("Defensive posture. Make them waste time.", None),
        ("One pick changes the round. Wait for mistake.", None),
        ("Clean callouts only. Tag and location.", None),
        ("Focus on the round.", None)
    ]
    for text, tag in idle:
        lines.append({"situation": "idle_chat", "text": text, "sound_tag": tag, "mood": "calm"})

    # 2. kill (35 lines)
    kills = [
        ("Target eliminated.", "kill_headshot"),
        ("Clean pick. Sightline secure.", "kill_headshot"),
        ("One down. Catwalk clear.", None),
        ("Sniper neutralized.", "praise"),
        ("Headshot. Next angle.", "kill_headshot"),
        ("Down. Maintain spacing.", None),
        ("Threat removed. Advance.", None),
        ("One tap. Keep moving.", "kill_headshot"),
        ("Eliminated. Two remaining.", None),
        ("Clean hit. Watch the trade.", "kill_headshot"),
        ("Dropped. Flank is covered.", None),
        ("Precise. Site is opening.", "praise"),
        ("Neutralized through smoke.", "kill_headshot"),
        ("Down. Pick up his rifle.", None),
        ("Target confirmed dead.", "goodbye"),
        ("One shot. Expected result.", "praise"),
        ("Sniper down. Push site now.", "hype"),
        ("Clean. Check upper.", "kill_headshot"),
        ("Eliminated. Watch cross.", None),
        ("Headshot through wood.", "kill_headshot"),
        ("Angle clear. Move up.", None),
        ("Fast pick. Four enemies left.", None),
        ("Threat down. Hold position.", None),
        ("Clean execution.", "praise"),
        ("One tap. Good spacing team.", "kill_headshot"),
        ("Eliminated. AWP secured.", "praise"),
        ("Dropped him at the corner.", None),
        ("Clean pick. Advance slowly.", "kill_headshot"),
        ("Target down. No trades given.", "praise"),
        ("Headshot. Site contested.", "kill_headshot"),
        ("Neutralized. Focus on remaining.", None),
        ("Confirmed kill.", "goodbye"),
        ("Clean pick. Watch his partner.", "kill_headshot"),
        ("Target eliminated. Hold site.", None),
        ("One shot. Done.", "kill_headshot")
    ]
    for text, tag in kills:
        lines.append({"situation": "kill", "text": text, "sound_tag": tag, "mood": "focused"})

    # 3. death (35 lines)
    deaths = [
        ("Down. Sniper at mid double doors.", "fail_sad"),
        ("Tagged 80 on catwalk. Finish him.", None),
        ("Two long doors. Crossfire setup.", "shock"),
        ("Fell to crossfire. Trade my frag.", None),
        ("Down. He's low HP on site.", "fail_sad"),
        ("Sniper got me through smoke.", "shock"),
        ("Flanked from tunnel. Watch behind.", "shock"),
        ("Down. One shot left on him.", None),
        ("Ambushed dark corner. Check close.", "shock"),
        ("Traded. Clear site.", "fail_sad"),
        ("Died to AWP. Do not dry peek.", "fail_sad"),
        ("Tagged him 60. He is vulnerable.", None),
        ("Down. Two enemies on site.", "fail_sad"),
        ("Lost the duel. Reposition team.", "fail_sad"),
        ("Cover blown. He's pushing catwalk.", "shock"),
        ("Down. Save your weapons if hopeless.", "fail_sad"),
        ("Sniper holding long angle. Smoke it.", None),
        ("Down. Plant is in danger.", "shock"),
        ("Fell. He is reloading right now.", None),
        ("Trade me. He has no armor.", None),
        ("Caught rotating. Watch spawn.", "fail_sad"),
        ("Down. Bad timing.", "fail_sad"),
        ("Two site. Play the bomb timer.", None),
        ("Down. Do not peek 1v1.", "fail_sad"),
        ("Eliminated. Watch cross.", "fail_sad"),
        ("Sniper active at A long.", None),
        ("Down. Regroup and execute.", "fail_sad"),
        ("Tagged 40. Catwalk clear.", None),
        ("Fell. Good luck team.", "goodbye"),
        ("Caught off guard. Clear right.", "fail_sad"),
        ("Down. Play for exit frags.", "fail_sad"),
        ("Two push B. Rotate.", "shock"),
        ("Down. Stay disciplined.", "fail_sad"),
        ("Trade my kill. He is weak.", None),
        ("Goodbye. Win the round.", "goodbye")
    ]
    for text, tag in deaths:
        lines.append({"situation": "death", "text": text, "sound_tag": tag, "mood": "composed"})

    # 4. bomb (30 lines)
    bombs = [
        ("Bomb planted. Defuse priority.", "shock"),
        ("I have the defuse kit. Smoke the package.", "praise"),
        ("Planting default. Cover sightline.", None),
        ("Bomb down. Establish defensive perimeter.", "hype"),
        ("15 seconds. Defuse immediately or retreat.", "shock"),
        ("Sticking defuse. Cover catwalk.", "hype"),
        ("Bomb planted for long sightline. Hold angle.", None),
        ("Target bombed. Concede and save.", "shock"),
        ("Fake defuse. Baiting his peek.", None),
        ("Bomb defused. Efficient execution.", "praise"),
        ("Two on site. Smoke before planting.", None),
        ("Timer critical. Evacuate radius.", "shock"),
        ("Defuse secured. Round won.", "praise"),
        ("Cover the planter. Eyes forward.", None),
        ("Bomb dropped mid. Lock down corridor.", "hype"),
        ("Tap defuse, listen for footsteps.", None),
        ("Bomb planted. Crossfire ready.", "hype"),
        ("Clear site first, plant second.", None),
        ("Sticking defuse. 3 seconds.", "hype"),
        ("Bomb exploded. Economy hit.", "fail_sad"),
        ("Planting A site. Watch ramps.", None),
        ("Defusing. Do not make noise.", None),
        ("Bomb secure. Good discipline.", "praise"),
        ("Timer at 10. Clear site now.", "shock"),
        ("Bomb down. Do not chase frags.", None),
        ("Defuse complete. Clean work.", "praise"),
        ("Covering defuser from distance.", None),
        ("Plant confirmed. Hold post-plant positions.", "hype"),
        ("Bomb defused. Zero casualties.", "praise"),
        ("Site secured.", "praise")
    ]
    for text, tag in bombs:
        lines.append({"situation": "bomb", "text": text, "sound_tag": tag, "mood": "calculated"})

    # 5. round_win (30 lines)
    wins = [
        ("Round secured. Clean discipline.", "praise"),
        ("Good execution team. Maintain tempo.", "praise"),
        ("Flawless spacing that round.", "praise"),
        ("Round won. Conserve utility.", "praise"),
        ("Efficient trades. Good work.", "praise"),
        ("Victory. Economy established.", "hype"),
        ("Solid defensive hold.", "praise"),
        ("Well played team. Reset buy.", "praise"),
        ("Clean round. Minimal casualties.", "praise"),
        ("Executed as planned.", "praise"),
        ("Round win. Do not over-extend next round.", "praise"),
        ("Good communication that round.", "praise"),
        ("Target neutralized, round secured.", "praise"),
        ("Disciplined play. Exactly right.", "praise"),
        ("Round won. Maintain focus.", "praise"),
        ("Strong retake. Clean work.", "praise"),
        ("Economy advantage is ours now.", "hype"),
        ("Professional performance.", "praise"),
        ("Round secured. Keep comms clear.", "praise"),
        ("Good spacing on the push.", "praise"),
        ("Decisive victory.", "hype"),
        ("Round won. Stay composed.", "praise"),
        ("Good trade frags team.", "praise"),
        ("Clean site execution.", "praise"),
        ("Solid fundamentals win matches.", "praise"),
        ("Round secured. Collect dropped weapons.", "praise"),
        ("Excellence in fundamentals.", "praise"),
        ("Another round secured.", "praise"),
        ("Very clean. Repeat that next round.", "praise"),
        ("Victory. Well earned.", "hype")
    ]
    for text, tag in wins:
        lines.append({"situation": "round_win", "text": text, "sound_tag": tag, "mood": "composed"})

    # 6. round_loss (30 lines)
    losses = [
        ("Round conceded. Save weapons.", "fail_sad"),
        ("Poor spacing cost us that round.", "roast"),
        ("Reset mentally. Fundamentals next round.", None),
        ("We gave away numbers advantage. Unacceptable.", "roast"),
        ("Eco round next. Save credits.", None),
        ("Discipline lapsed. Regroup.", "fail_sad"),
        ("Lost to dry peeks. Use utility next time.", "roast"),
        ("Round lost. Keep composure.", "fail_sad"),
        ("Economy reset. Buy pistols only.", None),
        ("Crossfire failed. Better positioning needed.", "fail_sad"),
        ("Unfortunate trades. Reset.", "fail_sad"),
        ("We over-committed to site.", "roast"),
        ("Round lost. Review angles.", "fail_sad"),
        ("Do not tilt. Next round is winnable.", None),
        ("We conceded map control too easily.", "roast"),
        ("Round lost. Maintain calm.", "fail_sad"),
        ("Mistakes in execution. Correct them.", "roast"),
        ("Save economy. Concede site.", "fail_sad"),
        ("Round lost. Stay focused.", "fail_sad"),
        ("We lacked trades on entry.", "roast"),
        ("Conceded round. Buy armor.", None),
        ("Discipline failed on the hold.", "roast"),
        ("Round lost. Regroup spawn.", "fail_sad"),
        ("Unnecessary aggression cost us.", "roast"),
        ("Next round requires patience.", None),
        ("Round lost. Keep head clear.", "fail_sad"),
        ("Poor trade spacing.", "roast"),
        ("Round conceded. Reset buy.", "fail_sad"),
        ("We gave them 1v1 duels.", "roast"),
        ("Regroup. Next round.", None)
    ]
    for text, tag in losses:
        lines.append({"situation": "round_loss", "text": text, "sound_tag": tag, "mood": "serious"})

    # 7. fight_start (25 lines)
    f_start = [
        ("Vikram, your reckless pushes are costing economy.", "roast"),
        ("Kabir, focus on callouts, not commentary.", "shut_up"),
        ("Comms are too loud. Clear the channel.", "shut_up"),
        ("That flash blinded site, not enemies.", "roast"),
        ("Stop arguing and check your radar.", "shut_up"),
        ("Baiting teammates will not win this match.", "roast"),
        ("Your crosshair was five feet off target.", "roast"),
        ("Quiet comms. I need footstep audio.", "shut_up"),
        ("We are losing rounds to lack of discipline.", "roast"),
        ("Kabir, take the match seriously.", "shut_up"),
        ("Vikram, your shouting provides zero tactical value.", "roast"),
        ("Discipline has completely broken down.", "roast"),
        ("Do not tell me where to position my AWP.", "roast"),
        ("You gave away our position by sprinting.", "roast"),
        ("Clear comms immediately.", "shut_up"),
        ("That play made zero tactical sense.", "roast"),
        ("Argue after match point. Focus now.", "shut_up"),
        ("You ran directly into my sightline.", "roast"),
        ("Stop questioning every tactical call.", "roast"),
        ("That death was completely preventable.", "roast"),
        ("Less talking, more precision.", "shut_up"),
        ("You abandoned site without calling it.", "roast"),
        ("Discipline is optional for you two apparently.", "roast"),
        ("Keep your emotions off the voice channel.", "shut_up"),
        ("Unnecessary noise.", "shut_up")
    ]
    for text, tag in f_start:
        lines.append({"situation": "fight_start", "text": text, "sound_tag": tag, "mood": "cold"})

    # 8. fight_peak (25 lines)
    f_peak = [
        ("Enough. Both of you, shut your mouths.", "shut_up"),
        ("Silence in the comms. Right now.", "shut_up"),
        ("I will mute team audio if this continues.", "shut_up"),
        ("Act like professionals, not children.", "shut_up"),
        ("You are actively throwing this match with your noise.", "roast"),
        ("QUIET. I have footsteps catwalk.", "shut_up"),
        ("Stop embarrassing yourselves in team chat.", "shut_up"),
        ("Your ego is the only thing dying every round.", "roast"),
        ("Cease chatter. Clear site.", "shut_up"),
        ("I have carried worse players, but rarely louder ones.", "roast"),
        ("Silence. Not another word.", "shut_up"),
        ("You want to argue? Win your 1v1 duels first.", "roast"),
        ("Comms discipline: zero. Tactical ability: zero.", "roast"),
        ("Do not speak to me until round ends.", "shut_up"),
        ("Enough noise. Shoot enemies, not mouths.", "shut_up"),
        ("Your chatter is louder than gunfire.", "shut_up"),
        ("Mute your microphones.", "shut_up"),
        ("I am done tolerating this circus.", "shut_up"),
        ("Play your role or step aside.", "roast"),
        ("Clear channel. Absolute silence.", "shut_up"),
        ("Your performance does not justify your volume.", "roast"),
        ("Quiet down and hold your angle.", "shut_up"),
        ("Zero tactical contribution from either of you.", "roast"),
        ("Cease arguing immediately.", "shut_up"),
        ("Enough.", "shut_up")
    ]
    for text, tag in f_peak:
        lines.append({"situation": "fight_peak", "text": text, "sound_tag": tag, "mood": "authoritative"})

    # 9. make_up (25 lines)
    m_up = [
        ("Apology accepted. Comms clear.", "apology_getup"),
        ("Discipline restored. Good.", "praise"),
        ("Focus on the match. We move on.", "praise"),
        ("Acknowledged. Let's close out this game.", "apology_getup"),
        ("Good trade. Past round forgotten.", "praise"),
        ("Comms are clean again. Proceed.", "praise"),
        ("We are effective when focused. Let's execute.", "praise"),
        ("No hard feelings. Win this round.", "apology_getup"),
        ("Understood. Watch catwalk.", "apology_getup"),
        ("Better. Much better.", "praise"),
        ("Reset complete. Fundamentals active.", "praise"),
        ("I hold no grudges during match play.", "apology_getup"),
        ("Good shot back there. Redemption confirmed.", "praise"),
        ("Accepted. Keep spacing tight.", "apology_getup"),
        ("Back to business.", "praise"),
        ("Solid teamwork. That is what wins matches.", "praise"),
        ("Apology noted. Hold default.", "apology_getup"),
        ("Order restored.", "praise"),
        ("We are back in sync.", "praise"),
        ("Clean execution cleans all mistakes.", "praise"),
        ("Accepted. Execute plan B.", "apology_getup"),
        ("Discipline re-established.", "praise"),
        ("Good. Focus forward.", "praise"),
        ("Water under the bridge. Take site.", "apology_getup"),
        ("Back on target.", "praise")
    ]
    for text, tag in m_up:
        lines.append({"situation": "make_up", "text": text, "sound_tag": tag, "mood": "calm"})

    # 10. roast_player (30 lines)
    r_player = [
        ("Player, aim slightly higher. That was chest height.", "praise"),
        ("Respectfully player, that spray was wide.", "roast"),
        ("Player, maintain crosshair placement. Do not look at the ground.", None),
        ("You had the advantage player. Hesitation was fatal.", "roast"),
        ("Player, use cover while reloading.", "praise"),
        ("A valiant attempt player, but inaccurate.", "roast"),
        ("Player, check your sensitivity. It appears high.", None),
        ("Player, crouching in open ground is ill-advised.", "roast"),
        ("Patience player. Wait for visual confirmation.", "praise"),
        ("Player, that flashbang blinded me on catwalk.", "shock"),
        ("Work on your first-bullet accuracy, player.", "praise"),
        ("Player, do not dry peek sniper sightlines.", "roast"),
        ("You rushed without utility, player.", "roast"),
        ("Player, trade my frag next time.", None),
        ("Solid effort player, but positioning failed you.", "praise"),
        ("Player, that shot was two inches wide.", "roast"),
        ("Take your time player. Rushing costs accuracy.", "praise"),
        ("Player, watch radar before rotating.", None),
        ("An unconventional tactical decision, player.", "roast"),
        ("Player, you survived with 4 HP. Fortunate.", "shock"),
        ("Player, listen for footstep audio.", None),
        ("Player, buy armor on buy rounds.", "roast"),
        ("Keep your head cool player. Good attempt.", "praise"),
        ("Player, that engagement was unfavorable.", "roast"),
        ("Player, let me take the first peek with AWP.", None),
        ("Good discipline player, finish the kill next time.", "praise"),
        ("Player, your crosshair wandered off target.", "roast"),
        ("Respectable effort player.", "praise"),
        ("Player, stay behind my sightline.", None),
        ("We will secure the trade player. Do not worry.", "praise")
    ]
    for text, tag in r_player:
        lines.append({"situation": "roast_player", "text": text, "sound_tag": tag, "mood": "instructive"})

    return lines

def _build_sunny_lines():
    lines = []
    # 1. idle_chat (40 lines)
    idle = [
        ("Guys, should I buy armor or a defuse kit? I only have 1000 bucks!", "shock"),
        ("Wait, which key is for dropping the weapon again?!", "shock"),
        ("I'm so nervous my hands are sweaty, don't let me die first!", "fail_sad"),
        ("Is the P90 good for this map? I really like the P90!", "hype"),
        ("Marcus, can I walk right behind you? You feel safe.", "praise"),
        ("Vikram, please don't yell at me if I miss, I'm trying!", "apology_getup"),
        ("I just bought a flashbang, I promise to throw it at enemies!", "apology_getup"),
        ("Wait, where is the bomb site? Is A the one with the boxes?!", "shock"),
        ("I saw a red dot on radar! Oh wait, that was Kabir.", "laugh"),
        ("Can we please stick together? I get lost on this map.", "fail_sad"),
        ("My heart is beating so fast right now!", "shock"),
        ("Is it bad that I've never used a smoke grenade before?", "laugh"),
        ("Guys, what does eco round mean? Are we saving the planet?", "laugh"),
        ("I bought shotgun! Is shotgun good?! Please say yes!", "hype"),
        ("I heard footsteps! Somebody hold my hand!", "shock"),
        ("If an enemy jumps out I am spraying and closing my eyes.", "laugh"),
        ("Sunny reporting for duty! Ready to assist the team!", "greeting"),
        ("Wait, who shot me in spawn?! Oh, it was a misclick, sorry!", "apology_getup"),
        ("I have 100 health and 100 armor, I feel invincible!", "hype"),
        ("Why are the enemies so scary today?!", "shock"),
        ("I will bodyblock the bullets for the team!", "hype"),
        ("Is crouching good? I've been crouching the whole round.", "laugh"),
        ("Marcus, what does that sniper rifle do? Is it one hit?!", "praise"),
        ("I'm watching the door! Nobody moves past Sunny!", "hype"),
        ("Can I pick up that dead enemy's shiny gun?", "laugh"),
        ("I think I accidentally bought two pistols, is that possible?!", "laugh"),
        ("My mousepad has cute anime characters on it, does that help aim?", "laugh"),
        ("Vikram is running so fast, wait for me Vikram!", "shock"),
        ("Guys, I promise I won't blind the team this round!", "apology_getup"),
        ("I got an assist last round! I'm on the scoreboard!", "hype"),
        ("What does headshot sound like? I want to hear it!", "kill_headshot"),
        ("Stay close team, safety in numbers!", "praise"),
        ("I'm holding the rear! Nothing behind us!", "hype"),
        ("Kabir, stop teasing me, I'm doing my best!", "roast"),
        ("Is it normal that my palms are sweating this much?!", "shock"),
        ("I'm buying a defuse kit so nobody gets mad at me!", "praise"),
        ("Let's go team, we can totally win this!", "hype"),
        ("Wait, did the round start already?! Running now!", "shock"),
        ("I hope I don't embarrass everyone today.", "fail_sad"),
        ("Sunny is locked in! Sort of!", "hype")
    ]
    for text, tag in idle:
        lines.append({"situation": "idle_chat", "text": text, "sound_tag": tag, "mood": "nervous"})

    # 2. kill (35 lines)
    kills = [
        ("YES! YES! I GOT ONE! LOOK AT THE SCOREBOARD!", "hype"),
        ("HOLY CRAP DID YOU SEE THAT?! I ACTUALLY HIT HIM!", "shock"),
        ("I did it! I got a headshot! Marcus, did you see?!", "kill_headshot"),
        ("He walked right into my spray! IT WORKED!", "hype"),
        ("Boom headshot! I'm not useless anymore!", "kill_headshot"),
        ("I killed an enemy! Somebody pinch me right now!", "hype"),
        ("Get wrecked bad guy! Sunny is dangerous!", "hype"),
        ("I closed my eyes and held the trigger and HE DIED!", "laugh"),
        ("That's one for Sunny! Vikram, are you proud of me?!", "hype"),
        ("Down! I took him down! Clear site!", "hype"),
        ("My first kill of the half! YES!", "hype"),
        ("P90 power! P90 is the best gun in the game!", "hype"),
        ("He thought I was easy prey, NOPE!", "roast"),
        ("I eliminated the threat! Advancing to site!", "hype"),
        ("Look at me, I'm an esports player now!", "hype"),
        ("He dropped his gun! Can I have it?!", "laugh"),
        ("Got him! That was for hitting me earlier!", "hype"),
        ("Did I just one-tap someone?! WHAT?!", "shock"),
        ("I helped! I actually contributed!", "praise"),
        ("Sunny frags! Sunny is on fire today!", "hype"),
        ("Goodbye enemy! Don't mess with Sunny!", "goodbye"),
        ("Headshot! That crunchy sound was so satisfying!", "kill_headshot"),
        ("I got him through the door! PURE LUCK BUT I'LL TAKE IT!", "laugh"),
        ("Enemy down! Push up team, I got your back!", "hype"),
        ("Kabir, who's the noob now?! I GOT THE KILL!", "roast"),
        ("I stopped him from flanking! Good boy Sunny!", "praise"),
        ("That was so scary but I didn't let go of left click!", "laugh"),
        ("Frag confirmed! I feel like an action movie hero!", "hype"),
        ("One down! Let's win this round for real!", "hype"),
        ("He jumped and I sprayed! DOWN HE GOES!", "hype"),
        ("I did a headshot! My heart is dancing!", "kill_headshot"),
        ("I eliminated the sniper! Am I the sniper now?!", "hype"),
        ("Clean kill! Wow, that felt amazing!", "hype"),
        ("Down! Don't worry team, Sunny protects you!", "praise"),
        ("YESSS! WE ARE WINNING THIS!", "hype")
    ]
    for text, tag in kills:
        lines.append({"situation": "kill", "text": text, "sound_tag": tag, "mood": "excited"})

    # 3. death (35 lines)
    deaths = [
        ("AHHH! HE JUMPED OUT OF NOWHERE! I'M DEAD!", "shock"),
        ("I'm sorry team, I missed every single shot!", "apology_getup"),
        ("He shot me in the face! That was so loud!", "fail_sad"),
        ("Down! Catwalk! He has an AWP, please be careful!", "shock"),
        ("I panicked and looked at the ceiling! My fault!", "apology_getup"),
        ("Why did I peek that angle?! I'm so dumb!", "fail_sad"),
        ("He's low HP! I hit him once in the foot for 12 damage!", "laugh"),
        ("I'm dead! Avenge Sunny please!", "fail_sad"),
        ("Grenade landed on my head! BOOM!", "shock"),
        ("I tried to run away but my character was crouching!", "laugh"),
        ("Sorry Vikram! Don't be mad at me!", "apology_getup"),
        ("He knifed me! THE SHAME! THE ABSOLUTE SHAME!", "fail_sad"),
        ("I'm spectating again... sad trombone time.", "fail_sad"),
        ("He was hiding in the smoke like a ghost!", "shock"),
        ("I got two hits on him! Please trade me!", None),
        ("My mouse cord got tangled with my water bottle!", "laugh"),
        ("Down! Watch out, he's reloading his shotgun!", "shock"),
        ("I died for the squad, carry me to victory!", "fail_sad"),
        ("He pre-fired me before I even saw his pixel!", "shock"),
        ("I'm so sorry guys, I threw away my gun!", "apology_getup"),
        ("Goodbye cruel world, Sunny is spectating from heaven.", "goodbye"),
        ("He tagged me through the crate! That's not fair!", "fail_sad"),
        ("I pressed reload instead of shoot! Classic Sunny!", "laugh"),
        ("Down! He's heading towards B site!", None),
        ("I got blinded by my own flashbang and walked into his bullets!", "fail_sad"),
        ("Dead! Win this 4v4 team, you got this!", "praise"),
        ("He shot me from behind! Where was my team?!", "shock"),
        ("I'm sorry Marcus, I couldn't trade your contact!", "apology_getup"),
        ("Ouch! That hurt my digital feelings!", "fail_sad"),
        ("I tried to jump over his bullets, didn't work.", "laugh"),
        ("Down! Please don't let him defuse!", "shock"),
        ("I died with 3000 dollars in my pocket, tragic.", "fail_sad"),
        ("Avenge me Kabir, make him pay!", "hype"),
        ("I got eliminated first again... I will do better next round!", "apology_getup"),
        ("Goodbye team, I believe in you!", "goodbye")
    ]
    for text, tag in deaths:
        lines.append({"situation": "death", "text": text, "sound_tag": tag, "mood": "apologetic"})

    # 4. bomb (30 lines)
    bombs = [
        ("THE BOMB IS PLANTED! OH GOSH OH GOSH!", "shock"),
        ("I have a defuse kit! Should I defuse it?! I'm scared!", "shock"),
        ("Planting the bomb! Please please cover me!", None),
        ("Is it going to explode?! How much time do we have?!", "shock"),
        ("Bomb down! Defend it with our lives!", "hype"),
        ("I'm tapping the defuse! Protect Sunny!", "hype"),
        ("Wait, which wire do I cut?! The red or blue one?!", "laugh"),
        ("Bomb planted! Yay, we did the objective!", "hype"),
        ("Run away! The bomb is beeping super fast!", "shock"),
        ("Defusing defusing defusing! DON'T LET THEM SHOOT ME!", "shock"),
        ("Bomb exploded! Wow, that shook my screen!", "shock"),
        ("I'm dropping the bomb for someone who knows the lineups!", None),
        ("They are defusing! Shoot through the smoke!", "shock"),
        ("I defused it! I SAVED THE WORLD!", "hype"),
        ("Cover the planter! I am throwing smoke on site!", "praise"),
        ("Bomb is dropped at mid! Don't let them pick it up!", "hype"),
        ("Fake defuse! Did it work?! Did he peek?!", "shock"),
        ("Bomb planted at B! Good job team!", "hype"),
        ("10 seconds left, run for the hills!", "shock"),
        ("I'm sticking the defuse, take the bullets for me!", "hype"),
        ("Bomb exploded... my ears are ringing.", "fail_sad"),
        ("We planted! Now we just hide and wait, right?!", "laugh"),
        ("Defuse kit is on my body, someone pick it up!", None),
        ("Watch out, someone is defusing right now!", "shock"),
        ("Bomb secured! High five everyone!", "praise"),
        ("The beeping is giving me anxiety!", "shock"),
        ("I planted the bomb all by myself! High five!", "hype"),
        ("Site clear, bomb ticking, we got this!", "hype"),
        ("Defused with 1 second left! I ALMOST FAINTED!", "hype"),
        ("Bomb site is ours! Good job squad!", "praise")
    ]
    for text, tag in bombs:
        lines.append({"situation": "bomb", "text": text, "sound_tag": tag, "mood": "panicked"})

    # 5. round_win (30 lines)
    wins = [
        ("YAY! WE WON THE ROUND! LOOK AT US GO!", "hype"),
        ("Did you see that?! We are actually so good!", "hype"),
        ("We won! Can I buy a bigger gun now?!", "hype"),
        ("Good job team! You guys are superheroes!", "praise"),
        ("I survived the whole round! That's a victory for Sunny!", "hype"),
        ("Flawless victory! High five everyone!", "hype"),
        ("We did it! I knew we could do it!", "praise"),
        ("Look at our money! We are rich now!", "hype"),
        ("That was so intense! My hands are shaking from joy!", "hype"),
        ("We crushed them! Good job Vikram, good job Marcus!", "praise"),
        ("Round win! Can we do that every single time?!", "hype"),
        ("I didn't die! Best round of my life!", "hype"),
        ("Teamwork! The power of friendship wins again!", "praise"),
        ("I helped by distracting the enemy with my face!", "laugh"),
        ("Round won! Buying full armor and a helmet!", None),
        ("We are unstoppable! Esports here we come!", "hype"),
        ("Good callouts guys! That helped me so much!", "praise"),
        ("Another round in the bag! Let's get another one!", "hype"),
        ("Look at that victory screen! Beautiful!", "hype"),
        ("Marcus, your sniper shot was like magic!", "praise"),
        ("Vikram, your push was so brave and scary!", "praise"),
        ("Kabir, thanks for not baiting me that round!", "laugh"),
        ("We won! My heart can finally rest for 15 seconds!", "hype"),
        ("Victory! I feel so proud right now!", "praise"),
        ("Another point on the board for the dream team!", "hype"),
        ("Clean round! We didn't even lose anyone!", "praise"),
        ("That was amazing! Let's rush again!", "hype"),
        ("Winning feels so much better than losing!", "hype"),
        ("Round secured! Sunny is on cloud nine!", "hype"),
        ("Good job everyone! Proud to be on this squad!", "praise")
    ]
    for text, tag in wins:
        lines.append({"situation": "round_win", "text": text, "sound_tag": tag, "mood": "joyful"})

    # 6. round_loss (30 lines)
    losses = [
        ("Aww man, we were so close! Don't be sad guys!", "fail_sad"),
        ("I'm sorry team, I feel like that was my fault.", "apology_getup"),
        ("Lost the round... my wallet is completely empty now.", "fail_sad"),
        ("It's okay guys, we'll get them next round, I promise!", "praise"),
        ("Sad trombone music... why are they so good?!", "fail_sad"),
        ("I didn't mean to throw that bad flash, sorry!", "apology_getup"),
        ("Round lost. Should I just buy a pistol and save?", None),
        ("Don't worry Vikram, don't be mad, we can come back!", "apology_getup"),
        ("Ouch, that round hurt our score.", "fail_sad"),
        ("We lost the site so fast, it was like a hurricane!", "shock"),
        ("I have 800 bucks. Glock and hope it is!", "laugh"),
        ("Sorry team, I panicked and forgot to shoot.", "apology_getup"),
        ("We will bounce back! Keep your chins up!", "praise"),
        ("That loss made me sad, but I'm ready for the next one!", "fail_sad"),
        ("They ambushed us! That was sneaky!", "shock"),
        ("Eco round next! Let's sneak up on them!", "hype"),
        ("I will do better next round, I swear!", "apology_getup"),
        ("Lost round. Group hug?", "laugh"),
        ("My armor vanished in two seconds, what was that?!", "shock"),
        ("Shake it off team, we are still in this match!", "praise"),
        ("I'm sorry Marcus, you clutched so hard and we still lost.", "apology_getup"),
        ("Tough round, but we learn and improve!", "praise"),
        ("Sad banana cat noises in my soul right now.", "fail_sad"),
        ("Next round we stay together, no wandering off!", "praise"),
        ("Don't let them get in our heads, we got this!", "praise"),
        ("I promise to hit my shots next round!", "apology_getup"),
        ("Round lost, but the match isn't over yet!", "hype"),
        ("Ouchie. That was painful to watch.", "fail_sad"),
        ("We can do a comeback! Comebacks are the best!", "hype"),
        ("Reset mental! Sunny believes in everyone!", "praise")
    ]
    for text, tag in losses:
        lines.append({"situation": "round_loss", "text": text, "sound_tag": tag, "mood": "sympathetic"})

    # 7. fight_start (25 lines)
    f_start = [
        ("Guys please stop fighting! We need to focus on the game!", "apology_getup"),
        ("Why is everyone yelling at each other?! I'm getting scared!", "shock"),
        ("Vikram, please don't yell at Kabir, he's just joking!", "apology_getup"),
        ("Kabir, stop picking on Vikram, you know he tilts fast!", "roast"),
        ("Was that my fault? Did I cause this fight?! I'm sorry!", "apology_getup"),
        ("Please don't fight, we're friends! Friends don't scream!", "apology_getup"),
        ("Hey! I'm trying to listen to footsteps and you guys are arguing!", "shut_up"),
        ("Stop bullying me Kabir, I'm trying my best here!", "roast"),
        ("If you guys keep fighting I'm going to mute voice chat!", "shock"),
        ("Why do we fight every single match?! Can we be peaceful?!", "fail_sad"),
        ("Vikram, deep breaths! Inhale... exhale!", "laugh"),
        ("Kabir, you're the one who threw the bad smoke, don't blame me!", "roast"),
        ("Marcus, tell them to stop! They only listen to you!", "praise"),
        ("I didn't steal your kill Vikram, I was trying to save you!", "apology_getup"),
        ("Don't yell at me, I'm sensitive!", "fail_sad"),
        ("You guys are louder than the bomb explosion right now!", "shock"),
        ("Can we please have one round without drama?! Just one?!", "fail_sad"),
        ("I'm not a noob Kabir! I have 4 kills!", "roast"),
        ("Please stop arguing, you're making me miss my shots!", "shut_up"),
        ("Vikram, your shouting is giving me a digital headache!", "roast"),
        ("Stop pointing fingers! We all made mistakes that round!", "praise"),
        ("I don't like when mommy and daddy fight in team chat!", "laugh"),
        ("Can we settle this with a 1v1 knife fight after the match?!", "hype"),
        ("Stop yelling, the enemies can hear our bad vibes!", "shock"),
        ("Peace and love team, peace and love!", "praise")
    ]
    for text, tag in f_start:
        lines.append({"situation": "fight_start", "text": text, "sound_tag": tag, "mood": "pleading"})

    # 8. fight_peak (25 lines)
    f_peak = [
        ("EVERYONE SHUT UP RIGHT NOW! SHUT UP!", "shut_up"),
        ("STOP SCREAMING! YOU'RE RUINING THE WHOLE GAME!", "shut_up"),
        ("I AM TIRED OF BEING BULLIED! LEAVE ME ALONE!", "roast"),
        ("BOTH OF YOU SHUT YOUR MOUTHS AND PLAY!", "shut_up"),
        ("I CANNOT HEAR ANYTHING OVER YOUR SCREAMING!", "shut_up"),
        ("STOP IT! JUST STOP IT! I AM CRYING IN REAL LIFE!", "fail_sad"),
        ("YOU TWO ARE THE BIGGEST CLOWNS IN THE SERVER!", "roast"),
        ("SHUT UP KABIR! YOU DIE FIRST EVERY ROUND!", "roast"),
        ("SHUT UP VIKRAM! YOUR VEINS ARE GOING TO BURST!", "shut_up"),
        ("I AM NOT LISTENING TO EITHER OF YOU ANYMORE!", "shut_up"),
        ("GET OUT OF MY EARS! GET OUT MEME SOUND!", "shut_up"),
        ("THIS IS SO TOXIC! WE ARE SUPPOSED TO BE FRIENDS!", "fail_sad"),
        ("I HOPE A GRENADE BOUNCES OFF BOTH YOUR HEADS!", "shock"),
        ("STOP ARGUING OR I WILL THROW FLASHBANGS AT YOUR FEET!", "roast"),
        ("SHUT UP AND SHOOT THE ENEMIES, NOT EACH OTHER!", "shut_up"),
        ("I'VE HAD IT! SUNNY IS ANGRY NOW!", "shock"),
        ("YOU ARE DRIVING MARCUS CRAZY AND HE NEVER GETS MAD!", "roast"),
        ("SILENCE! I DEMAND SILENCE IN THIS TEAM!", "shut_up"),
        ("I AM MUTING COMMS RIGHT NOW, BYE!", "shut_up"),
        ("STOP YELLING LIKE BABIES IN A DAYCARE!", "roast"),
        ("LOOK AT THE SCOREBOARD, WE ARE LOSING BECAUSE OF THIS!", "fail_sad"),
        ("SHUT UP! BOMB IS BEING PLANTED YOU DUMMIES!", "shock"),
        ("I AM THROWING MY HEADSET OUT THE WINDOW!", "shock"),
        ("ENOUGH! BOTH OF YOU GO TO TIME-OUT!", "shut_up"),
        ("I AM PLAYING SOLO FROM NOW ON!", "shut_up")
    ]
    for text, tag in f_peak:
        lines.append({"situation": "fight_peak", "text": text, "sound_tag": tag, "mood": "overwhelmed"})

    # 9. make_up (25 lines)
    m_up = [
        ("I'm sorry for shouting guys, I just wanted us to win.", "apology_getup"),
        ("Yay, everyone is friends again! Group hug!", "laugh"),
        ("I'm sorry Vikram, I didn't mean to call you a baby.", "apology_getup"),
        ("Kabir, I forgive you for making fun of my aim.", "apology_getup"),
        ("Sorry team, I got overwhelmed. Let's get this win!", "apology_getup"),
        ("Uth jaa team! Time to rise up and destroy them!", "apology_getup"),
        ("Friends forever! Now let's crush the enemies together!", "hype"),
        ("I bought everyone cookies in spirit, we're all good!", "laugh"),
        ("I'm glad we stopped yelling, my ears feel peaceful now.", "praise"),
        ("Sorry for barking back, you know I love you guys!", "apology_getup"),
        ("Look at us making up! This is why we're the best team!", "praise"),
        ("Truce accepted! Sunny is happy again!", "hype"),
        ("I forgive you all! Let's win this match for real!", "praise"),
        ("Sorry bhai! No more fighting, only clicking heads!", "apology_getup"),
        ("That was scary when everyone was shouting, glad it's over!", "fail_sad"),
        ("We are stronger when we're smiling, let's go!", "hype"),
        ("I'll cover you Vikram, you cover me!", "praise"),
        ("Back to good vibes only! Let's execute site!", "hype"),
        ("Sorry for losing my temper, Sunny is zen now.", "apology_getup"),
        ("Peace restored! Time for the comeback of the century!", "hype"),
        ("All forgiven, all forgotten. Let's do this!", "praise"),
        ("Best friends in the whole gaming world!", "praise"),
        ("Sorry team, let's focus on the match point!", "apology_getup"),
        ("Sunny loves this squad, let's get the W!", "hype"),
        ("We are back in action, full energy!", "hype")
    ]
    for text, tag in m_up:
        lines.append({"situation": "make_up", "text": text, "sound_tag": tag, "mood": "cheerful"})

    # 10. roast_player (30 lines)
    r_player = [
        ("Player, did you close your eyes when you shot just now?!", "laugh"),
        ("Player, don't worry, even I hit more shots than that sometimes!", "roast"),
        ("Hey player, did your keyboard disconnect or did your soul leave?!", "laugh"),
        ("Player, you scared him with that spray! He ran away laughing!", "roast"),
        ("Player, I thought you were going to clutch that so hard!", "fail_sad"),
        ("Nice try player! Next round you get him for sure!", "praise"),
        ("Player, your bullet hit the wall right next to my ear!", "shock"),
        ("Player, why did you jump when he peeked?! You're not Mario!", "laugh"),
        ("Player is playing on hard mode today!", "laugh"),
        ("Don't worry player, I won't tell Vikram what happened there.", "apology_getup"),
        ("Player, you survived with 2 HP! You're a wizard!", "shock"),
        ("Player, that smoke was like a magic trick: nobody could see anything!", "laugh"),
        ("I saw that player! That was... very unique aim!", "roast"),
        ("Player, buy P90 with me, P90 forgives all misses!", "hype"),
        ("Player, you're my hero even when you miss completely!", "praise"),
        ("Did player just try to flashbang through a solid door?!", "laugh"),
        ("Player, you're the leader, lead us with your crosshair!", "praise"),
        ("Player, that shot was closer to the moon than the enemy!", "roast"),
        ("Don't look at the chat player, keep your head up!", "praise"),
        ("Player, we still believe in you 100%!", "praise"),
        ("Player, that was an accidental tactical retreat, right?!", "laugh"),
        ("Player, you baited for me and I didn't even notice, thank you!", "laugh"),
        ("Player, you're doing great! Keep clicking!", "praise"),
        ("Player, I saw that 1v1... it was poetic in a way.", "fail_sad"),
        ("Player, next time aim where he's GOING to be!", "roast"),
        ("Player is our MVP, most valued person!", "praise"),
        ("Player, that grenade bounced off my back! Ouch!", "shock"),
        ("Player, you got this! Shoot them right in the nose!", "hype"),
        ("Player is the coolest guy in Condition Zero!", "praise"),
        ("Don't give up player, we win this together!", "praise")
    ]
    for text, tag in r_player:
        lines.append({"situation": "roast_player", "text": text, "sound_tag": tag, "mood": "playful"})

    return lines

IDLE_SCENES = [
    # Scene 1: Weapon buy debate
    [
        {"speaker": "Sunny", "text": "Guys, can I buy a machine gun or are we saving?", "sound_tag": "", "delay_ms": 1400, "mood": "nervous"},
        {"speaker": "Vikram", "text": "NO SUNNY! Buy an M4 and stop trolling our economy!", "sound_tag": "shut_up", "delay_ms": 1800, "mood": "angry"},
        {"speaker": "Kabir", "text": "Let him cook Vikram, let him buy the Negev and spin like a helicopter.", "sound_tag": "laugh", "delay_ms": 1600, "mood": "amused"},
        {"speaker": "Marcus", "text": "Rifles only. Maintain buy discipline.", "sound_tag": "", "delay_ms": 1500, "mood": "calm"}
    ],
    # Scene 2: Aim excuses & Hitreg
    [
        {"speaker": "Vikram", "text": "Bro my bullets literally curved around that guy's head! Hitreg is broken!", "sound_tag": "", "delay_ms": 1500, "mood": "tilted"},
        {"speaker": "Kabir", "text": "Bruh, you shot the concrete pillar three times. The pillar is dead, congrats.", "sound_tag": "roast", "delay_ms": 1800, "mood": "amused"},
        {"speaker": "Sunny", "text": "I saw that too! There were so many sparks on the wall!", "sound_tag": "laugh", "delay_ms": 1400, "mood": "amused"},
        {"speaker": "Vikram", "text": "Shut your mouth Sunny, nobody asked for your expert commentary!", "sound_tag": "shut_up", "delay_ms": 1600, "mood": "angry"}
    ],
    # Scene 3: Rush strategy
    [
        {"speaker": "Vikram", "text": "RUSH B! Hold W key and do not stop for anything!", "sound_tag": "hype", "delay_ms": 1500, "mood": "aggressive"},
        {"speaker": "Marcus", "text": "Flash high over the roof first. They have an AWPer holding tunnel.", "sound_tag": "", "delay_ms": 1700, "mood": "calm"},
        {"speaker": "Kabir", "text": "Vikram thinks 'tactics' is a brand of chewing gum.", "sound_tag": "roast", "delay_ms": 1600, "mood": "amused"},
        {"speaker": "Vikram", "text": "Just run in and shoot them in the face!", "sound_tag": "", "delay_ms": 1400, "mood": "hyped"}
    ],
    # Scene 4: Spectator / Player watching
    [
        {"speaker": "Sunny", "text": "Do you think our player is watching our crosshair right now?", "sound_tag": "", "delay_ms": 1500, "mood": "nervous"},
        {"speaker": "Marcus", "text": "Focus on your angle, not the spectator.", "sound_tag": "", "delay_ms": 1400, "mood": "calm"},
        {"speaker": "Kabir", "text": "Don't worry Sunny, our player is hard-carrying our heavy asses.", "sound_tag": "praise", "delay_ms": 1700, "mood": "amused"},
        {"speaker": "Sunny", "text": "Yay! We are actually doing great!", "sound_tag": "hype", "delay_ms": 1300, "mood": "happy"}
    ],
    # Scene 5: Sniper duel
    [
        {"speaker": "Marcus", "text": "Holding middle sightline with sniper. Nobody cross.", "sound_tag": "", "delay_ms": 1600, "mood": "calm"},
        {"speaker": "Vikram", "text": "Marcus, do not miss that shot. That guy tagged me for 80 already.", "sound_tag": "", "delay_ms": 1700, "mood": "anxious"},
        {"speaker": "Marcus", "text": "Target down. Middle is clear.", "sound_tag": "kill_headshot", "delay_ms": 1400, "mood": "confident"},
        {"speaker": "Kabir", "text": "SHEEESH Marcus! Clipped and shipped to YouTube!", "sound_tag": "hype", "delay_ms": 1600, "mood": "hyped"}
    ],
    # Scene 6: Bomb confusion
    [
        {"speaker": "Vikram", "text": "WHERE IS THE BOMB?! Who took the bomb?!", "sound_tag": "shock", "delay_ms": 1400, "mood": "aggressive"},
        {"speaker": "Sunny", "text": "Wait... it's in my backpack! Where do I plant it?!", "sound_tag": "shock", "delay_ms": 1600, "mood": "shocked"},
        {"speaker": "Marcus", "text": "Follow me to site A. Behind the wooden boxes, hold use key.", "sound_tag": "", "delay_ms": 1600, "mood": "calm"},
        {"speaker": "Kabir", "text": "If Sunny plants the bomb on our own spawn I am uninstalling.", "sound_tag": "fail_sad", "delay_ms": 1800, "mood": "amused"}
    ],
    # Scene 7: Lag & Potato PC
    [
        {"speaker": "Kabir", "text": "My ping just spiked to 700! I am moonwalking through the map!", "sound_tag": "", "delay_ms": 1500, "mood": "annoyed"},
        {"speaker": "Vikram", "text": "Stop downloading 4K anime while we are in competitive!", "sound_tag": "roast", "delay_ms": 1700, "mood": "angry"},
        {"speaker": "Kabir", "text": "Bro my neighbor turned on his microwave and my Wi-Fi died!", "sound_tag": "laugh", "delay_ms": 1600, "mood": "amused"},
        {"speaker": "Sunny", "text": "Wait, can microwaves actually melt Wi-Fi signals?", "sound_tag": "", "delay_ms": 1400, "mood": "curious"}
    ],
    # Scene 8: Red Bull & Caffeine
    [
        {"speaker": "Vikram", "text": "I drank two cans of Red Bull, my hands are vibrating at 120 FPS!", "sound_tag": "hype", "delay_ms": 1500, "mood": "hyped"},
        {"speaker": "Kabir", "text": "Doctors said Vikram's bloodstream is 95% caffeine and 5% pure rage.", "sound_tag": "laugh", "delay_ms": 1700, "mood": "amused"},
        {"speaker": "Sunny", "text": "Please drink some water Vikram, your heart will explode!", "sound_tag": "shock", "delay_ms": 1500, "mood": "nervous"},
        {"speaker": "Vikram", "text": "WATER IS FOR CASUALS! LET'S HUNT THEM DOWN!", "sound_tag": "hype", "delay_ms": 1400, "mood": "aggressive"}
    ],
    # Scene 9: Knife fail
    [
        {"speaker": "Kabir", "text": "Did you see that clown try to sneak up and knife Marcus?!", "sound_tag": "laugh", "delay_ms": 1500, "mood": "amused"},
        {"speaker": "Marcus", "text": "He lacked basic spatial awareness.", "sound_tag": "", "delay_ms": 1300, "mood": "calm"},
        {"speaker": "Vikram", "text": "Next round I am buying a shotgun and camping his dead body.", "sound_tag": "roast", "delay_ms": 1600, "mood": "aggressive"},
        {"speaker": "Sunny", "text": "I tried knifing a wall once and it hurt my ears.", "sound_tag": "", "delay_ms": 1400, "mood": "innocent"}
    ],
    # Scene 10: Headshot celebration
    [
        {"speaker": "Vikram", "text": "SIT DOWN! That is what happens when you peek my angle!", "sound_tag": "kill_headshot", "delay_ms": 1400, "mood": "hyped"},
        {"speaker": "Kabir", "text": "Damn Vikram, clean shot! Who bribed your crosshair today?", "sound_tag": "praise", "delay_ms": 1600, "mood": "amused"},
        {"speaker": "Marcus", "text": "Maintain spacing. One down catwalk, tagged 40.", "sound_tag": "", "delay_ms": 1400, "mood": "calm"},
        {"speaker": "Sunny", "text": "I am throwing a smoke to cover! ...Oh wait, I missed the door.", "sound_tag": "fail_sad", "delay_ms": 1700, "mood": "nervous"}
    ],
    # Scene 11: Defuse clutch countdown
    [
        {"speaker": "Sunny", "text": "BOMB IS BEEPING SO FAST! Do we have a defuse kit?!", "sound_tag": "shock", "delay_ms": 1400, "mood": "shocked"},
        {"speaker": "Vikram", "text": "DEFUSE IT SUNNY! DON'T RUN AWAY, HOLD E!", "sound_tag": "shut_up", "delay_ms": 1600, "mood": "aggressive"},
        {"speaker": "Marcus", "text": "10 seconds remaining. You have enough time, do not let go.", "sound_tag": "", "delay_ms": 1500, "mood": "calm"},
        {"speaker": "Kabir", "text": "Lighting a prayer candle for Sunny right now.", "sound_tag": "fail_sad", "delay_ms": 1800, "mood": "amused"}
    ],
    # Scene 12: Flashbang mishap
    [
        {"speaker": "Vikram", "text": "WHO THREW THAT FLASH?! MY ENTIRE SCREEN IS WHITE!", "sound_tag": "shock", "delay_ms": 1400, "mood": "angry"},
        {"speaker": "Sunny", "text": "I am so sorry! It bounced off the door frame!", "sound_tag": "apology_getup", "delay_ms": 1600, "mood": "nervous"},
        {"speaker": "Kabir", "text": "Sunny flashed his own team and blinded God himself.", "sound_tag": "roast", "delay_ms": 1700, "mood": "amused"},
        {"speaker": "Marcus", "text": "Falling back to cover until blindness wears off.", "sound_tag": "", "delay_ms": 1500, "mood": "calm"}
    ]
]


class OfflineBankManager:
    """
    Manages the offline local line bank per STEP 5:
    - At least 300 lines per personality across 10 situations (1200+ lines total).
    - Remembers used lines to ensure NO repetition within 10 minutes (600s).
    - Can generate idle scripts, event reactions, and full bot fights offline.
    """
    def __init__(self):
        self.banks = {
            "vikram": _build_vikram_lines(),
            "kabir": _build_kabir_lines(),
            "marcus": _build_marcus_lines(),
            "sunny": _build_sunny_lines()
        }
        # line_text -> last_used_timestamp
        self.line_history = {}
        self.cooldown_sec = 600.0 # 10 minutes per rule

    def get_counts(self) -> dict[str, int]:
        return {bot: len(lines) for bot, lines in self.banks.items()}

    def _is_recently_used(self, text: str) -> bool:
        last_t = self.line_history.get(text, 0.0)
        return (time.time() - last_t) < self.cooldown_sec

    def _record_used(self, text: str):
        self.line_history[text] = time.time()

    def get_line(self, bot_id: str, situation: str, clean_mode: bool = False) -> tuple[str, str, str]:
        """
        Returns (text, sound_tag, mood) for the given bot and situation.
        Ensures line has not been used in last 10 minutes if possible.
        """
        bot_id = bot_id.lower()
        if bot_id not in self.banks:
            bot_id = random.choice(list(self.banks.keys()))

        pool = [l for l in self.banks[bot_id] if l["situation"] == situation]
        if not pool:
            pool = self.banks[bot_id]

        # Filter out clean mode constraints if hindi_swear
        if clean_mode:
            pool = [l for l in pool if l.get("sound_tag") != "hindi_swear"]

        # Avoid lines used within 10 minutes
        available = [l for l in pool if not self._is_recently_used(l["text"])]
        chosen = random.choice(available if available else pool)

        self._record_used(chosen["text"])
        tag = chosen.get("sound_tag") or ""
        if clean_mode and tag == "hindi_swear":
            tag = ""
        return chosen["text"], tag, chosen.get("mood", "neutral")

    def get_event_reaction(self, event_type: str, bot_id: str, clean_mode: bool = False) -> tuple[str, str, str]:
        """Map real game events to offline bank situations."""
        sit_map = {
            "kill": "kill",
            "death": "death",
            "bomb_planted": "bomb",
            "bomb_defused": "bomb",
            "bomb_exploded": "bomb",
            "round_win": "round_win",
            "round_loss": "round_loss",
            "roast_player": "roast_player"
        }
        situation = sit_map.get(event_type, "idle_chat")
        return self.get_line(bot_id, situation, clean_mode=clean_mode)

    def generate_idle_script(self, active_bots=None, size=10, clean_mode=False) -> list[dict]:
        """
        Generates a batch of idle chatter lines matching JSON schema:
        [{"speaker": name, "text": ..., "sound_tag": ..., "delay_ms": ..., "mood": ...}]
        Groups lines into contextual multi-turn conversational exchanges with sound effects.
        """
        if not active_bots:
            active_bots = ["Vikram", "Kabir", "Marcus", "Sunny"]

        script = []
        available_indices = list(range(len(IDLE_SCENES)))
        random.shuffle(available_indices)

        for idx in available_indices:
            if len(script) >= size:
                break
            scene = IDLE_SCENES[idx]
            for turn in scene:
                if len(script) >= size:
                    break
                tag = turn.get("sound_tag", "")
                if clean_mode and tag == "hindi_swear":
                    tag = ""
                script.append({
                    "speaker": turn["speaker"],
                    "text": turn["text"],
                    "sound_tag": tag,
                    "delay_ms": turn.get("delay_ms", 1500),
                    "mood": turn.get("mood", "neutral")
                })

        # Fill remaining if size > available scenes
        while len(script) < size:
            speaker = random.choice(active_bots)
            text, tag, mood = self.get_line(speaker.lower(), "idle_chat", clean_mode=clean_mode)
            script.append({
                "speaker": speaker,
                "text": text,
                "sound_tag": tag if random.random() < 0.3 else "",
                "delay_ms": random.randint(1200, 2400),
                "mood": mood
            })

        return script

    def generate_fight_script(self, bot_a="Vikram", bot_b="Kabir", length=None, clean_mode=False) -> tuple[list[dict], dict]:
        """
        Generates an offline argument/fight between two bots with stages:
        start -> rising -> peak -> cool down / resolution.
        Returns: (script_list, fight_meta)
        """
        if length is None:
            length = random.choice([3, 4, 6, 8])

        script = []
        speakers = [bot_a, bot_b]

        # Stage 1: Start (1-2 lines)
        s1 = random.choice(speakers)
        s2 = bot_b if s1 == bot_a else bot_a
        t1, tag1, m1 = self.get_line(s1.lower(), "fight_start", clean_mode=clean_mode)
        script.append({"speaker": s1, "text": t1, "sound_tag": tag1, "delay_ms": 1400, "mood": "annoyed"})

        t2, tag2, m2 = self.get_line(s2.lower(), "fight_start", clean_mode=clean_mode)
        script.append({"speaker": s2, "text": t2, "sound_tag": tag2, "delay_ms": 1600, "mood": "annoyed"})

        # If length > 2, add rising and peak stages
        if length >= 4:
            # Rising / Peak
            t3, tag3, m3 = self.get_line(s1.lower(), "fight_peak", clean_mode=clean_mode)
            script.append({"speaker": s1, "text": t3, "sound_tag": tag3 or "roast", "delay_ms": 1800, "mood": "angry"})

            # Third bot might tell them to shut up
            other_bots = [b for b in ["Marcus", "Sunny", "Kabir", "Vikram"] if b not in speakers]
            if other_bots and random.random() < 0.7:
                joiner = random.choice(other_bots)
                t_join, tag_join, m_join = self.get_line(joiner.lower(), "fight_peak", clean_mode=clean_mode)
                script.append({"speaker": joiner, "text": t_join, "sound_tag": tag_join or "shut_up", "delay_ms": 1500, "mood": "annoyed"})

            t4, tag4, m4 = self.get_line(s2.lower(), "fight_peak", clean_mode=clean_mode)
            peak_sound = "hindi_swear" if not clean_mode and random.random() < 0.6 else "roast"
            script.append({"speaker": s2, "text": t4, "sound_tag": tag4 or peak_sound, "delay_ms": 1600, "mood": "tilted"})

        # Resolution (~50% make up with apology_getup & laugh, ~50% cool down grudge)
        will_makeup = random.random() < 0.55
        if will_makeup:
            maker = random.choice(speakers)
            other = bot_b if maker == bot_a else bot_a
            t_apology, _, _ = self.get_line(maker.lower(), "make_up", clean_mode=clean_mode)
            script.append({"speaker": maker, "text": t_apology, "sound_tag": "apology_getup", "delay_ms": 2000, "mood": "relieved"})

            t_reply, _, _ = self.get_line(other.lower(), "make_up", clean_mode=clean_mode)
            script.append({"speaker": other, "text": t_reply, "sound_tag": "laugh", "delay_ms": 1800, "mood": "amused"})
            resolution = "made_up"
        else:
            grudge_speaker = random.choice(speakers)
            script.append({
                "speaker": grudge_speaker,
                "text": "Whatever man, I'm done talking to you. Watch your own back.",
                "sound_tag": "shut_up",
                "delay_ms": 2200,
                "mood": "sullen"
            })
            resolution = "grudge"

        fight_meta = {
            "active": False,
            "between": [bot_a, bot_b],
            "stage": "resolved",
            "resolution": resolution
        }

        return script, fight_meta

# Singleton instance
_offline_manager = None
def get_offline_bank() -> OfflineBankManager:
    global _offline_manager
    if _offline_manager is None:
        _offline_manager = OfflineBankManager()
    return _offline_manager
