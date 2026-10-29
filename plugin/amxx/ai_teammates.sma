/*
 * AI Teammates for Counter-Strike: Condition Zero
 * AMX Mod X Native Plugin (Compatible with AMXX 1.8.2, 1.8.3, 1.9, 1.10+)
 *
 * Implements:
 *  - Step 2: 2-second "HEARTBEAT|alive" pulse to Brain + "GOODBYE|shutdown" & stopsound on exit
 *  - Step 3: On-screen in-game team-colored bot chat via client_print_color (SayText HUD)
 *            with zero dependency on <cstrike> gamedata offsets
 *  - Step 4: In-engine WAV sound playback from czero/sound/ai_teammates/<tag>/ (.wav) via "spk"
 *            (Brain sends only a TAG; plugin picks random WAV, never same file twice in a row,
 *             enforcing 3s global cooldown & 8s per-tag cooldown)
 *  - Step 5: Console test commands (ai_test_say, ai_status, ai_test_sound, ai_sound_list,
 *            ai_force_fight, ai_force_chat, ai_reset) & real-time event hooks
 */

#include <amxmodx>
#include <amxmisc>
#include <sockets>

#define PLUGIN_NAME    "CZ AI Teammates"
#define PLUGIN_VERSION "1.3"
#define PLUGIN_AUTHOR  "AI Teammates Mod Team"

// Comment out DEBUG to strip compile-time terminal logs, or toggle "ai_debug" cvar at runtime
#define DEBUG 1

// GoldSrc SayText net message limit is ~192 bytes; cap at 188 for safety
#define MAX_CHAT_LEN 188

#define BRAIN_HOST "127.0.0.1"
#define BRAIN_PORT 27115

#define MAX_TAGS          19
#define MAX_FILES_PER_TAG 16
#define MAX_FILENAME_LEN  64

#if !defined MAX_PLAYERS
    #define MAX_PLAYERS 32
#endif

#if !defined MAX_NAME_LENGTH
    #define MAX_NAME_LENGTH 32
#endif

// Color constants for AMXX < 1.8.3 fallback compatibility
#if AMXX_VERSION_NUM < 183
    #define print_team_default 0
    #define print_team_grey    -1
    #define print_team_red     -2
    #define print_team_blue    -3
#endif

new g_socket = -1;
new bool:g_brainConnected = false;
new Float:g_lastBrainHeartbeat = 0.0;
new bool:g_awaitingReply = false;
new g_lastChatMessage[192];
new g_lastChatSpeakerId = 0;
new g_logFile[128];

// Cvars
new g_cvarDebug;
new g_cvarCooldownGlobal;
new g_cvarCooldownTag;

// Sound Cooldown & Anti-Repeat State
new Float:g_lastGlobalSoundTime = -99.0;
new Float:g_lastTagSoundTime[MAX_TAGS];
new g_lastTagFileIndex[MAX_TAGS];

// Cached WAV file list per tag from czero/sound/ai_teammates/<tag>/
new g_tagFiles[MAX_TAGS][MAX_FILES_PER_TAG][MAX_FILENAME_LEN];
new g_tagFileCount[MAX_TAGS];

// Track last event actor & reason for sound attribution
new g_lastEventActorId = 0;
new g_lastEventReason[64] = "";
new Float:g_lastKillEventTime = -99.0;
new Float:g_lastKillReactTime = -99.0;
new Float:g_lastRoundStartTime = -99.0;
new Float:g_lastChatDisplayTime = 0.0;
new g_lastIdleIndex = -1;
new g_pendingVictimName[MAX_NAME_LENGTH] = "teammate";
new bool:g_pendingIsTeammateDeath = true;
new bool:g_pendingIsHeadshot = false;

// Cached status values from Brain
new g_apiStatus[64] = "Offline (Waiting for Brain)";
new g_requestsLeft = 500;
new g_queueSize = 0;
new g_fightState[64] = "None";
new g_chatterSpeed[32] = "Very chatty";
new g_fightFreq[32] = "Normal";
new g_chatStyle[32] = "Full gamer";
new bool:g_offlineWarned = false;

// All 19 supported sound tags in czero/sound/ai_teammates/<tag>/
new const g_soundTags[MAX_TAGS][] = {
    "hype",
    "kill_headshot",
    "shock",
    "praise",
    "roast",
    "hindi_swear",
    "fail_sad",
    "apology_getup",
    "shut_up",
    "greeting",
    "laugh",
    "goodbye",
    "bomb_alert",
    "fail",
    "bad_play",
    "sus_or_tease",
    "panic",
    "celebrate_kill",
    "clutch"
};

new const g_soundDefaultLabels[MAX_TAGS][] = {
    "hell yeah",
    "boom headshot",
    "oh my god",
    "wah! nice shot",
    "bruh roast",
    "rage scream",
    "sad trombone",
    "sorry bhai",
    "shut up",
    "yo whats up",
    "heheheha laugh",
    "goodbye",
    "danger alarm",
    "sad fail horn",
    "doge bonk",
    "hehe boy",
    "noooo scream",
    "hitmarker",
    "sheesh clutch"
};

// Filename stem -> Friendly readable label lookup table
new const g_fileLookupKeys[][] = {
    "01_hell_yeaaaaah",
    "02_oh_yeah_meme",
    "03_oh_yessss",
    "04_yessss_nathan_online_audio_converter",
    "05_yeahh_boiiiiiiii",
    "06_yeah_buddy_lightweight",
    "07_sheeshsoundeffect1",
    "08_maja_aaya",
    "09_mickey_mouse_oh_boy",
    "01_boomheadshot_swf",
    "02_1_booom_1",
    "03_wtf_boom_sound_meme",
    "01_oh_my_god_meme",
    "02_oh_my_god_bro_ah_hell_nah",
    "03_modis_oh_my_god",
    "04_kevin_heart_damn",
    "05_dammmm_daniel",
    "01_modi_ji_wah",
    "02_gian_hain_aap",
    "03_sochna_pdta_hai_re_hindustani_bhau",
    "01_bruh_sound_effect_wstdzdm",
    "02_ye_kya_bak_rahe_ho_mc",
    "03_is_sajjan_ko_kya_takleef_hai_bhai",
    "04_tejaswi_modi_can_be_used_as_a_taunt_to_t",
    "05_masti_dekho_bc_cid_dubbing",
    "06_is_ka_karan_narendar_modi",
    "01_kyu_re_madarchod_cid",
    "02_lavden_bhojyam",
    "03_modi_ji_bkl",
    "04_there_a_guy_fucking_me_in_the_ass",
    "01_spongebob_disappointed_sound_effect_isep",
    "02_banana_cat_crying",
    "03_depression_indian",
    "04_modi_ji_rona_band_kijiye",
    "05_faaah",
    "01_hindi_guy_said_sorry",
    "02_uth_jaa",
    "03_bhai_ne_bola_karnekka",
    "01_shut_your_fckin_mouth",
    "02_you_shut_your_mouth_fatty",
    "03_get_out_meme",
    "01_scout_yo_whats_up",
    "02_what_39s_up_budweiser_commercial_mp3cut",
    "03_quandale_dingle_v2",
    "04_ha_got_eeem",
    "01_ny_video_online_audio_converter",
    "02_ayooogima",
    "03_hi_hi_hi_ha_clash_royale",
    "01_tmp8ljn9e7h"
};

new const g_fileLookupLabels[][] = {
    "hell yeah",
    "oh yeah",
    "oh yes",
    "yes!",
    "yeah boy",
    "yeah buddy",
    "sheesh",
    "maja aaya",
    "oh boy",
    "boom headshot",
    "boom",
    "wtf boom",
    "oh my god",
    "hell nah",
    "oh my god (modi)",
    "damn",
    "damn daniel",
    "wah",
    "gian hain aap",
    "sochna padta hai",
    "bruh",
    "ye kya bak rahe ho",
    "kya takleef hai bhai",
    "tejaswi log",
    "masti dekho",
    "iska karan",
    "kyu re",
    "lavden bhojyam",
    "bkl",
    "rage scream",
    "sad trombone",
    "banana cat crying",
    "sad violin",
    "rona band kijiye",
    "faaah fail",
    "sorry bhai",
    "uth jaa",
    "bhai ne bola",
    "shut your mouth",
    "shut up",
    "get out",
    "yo whats up",
    "whats up",
    "quandale dingle",
    "ha got eem",
    "funny laugh",
    "goofy laugh",
    "heheheha",
    "goodbye"
};

// Local fallback reply bank (Guarantees <2s reply even if Brain is completely offline)
new const g_fallbackHelp[][] = {
    "Vikram: Hold on, I'm coming to bail your ass out!",
    "Kabir: Don't worry bro, I'm rotating! Try not to die!",
    "Marcus: Rotating to your position. 3 seconds, hold your angle.",
    "Sunny: I'm coming to help! Please don't die!"
};

new const g_fallbackRush[][] = {
    "Vikram: RUSH B! NO BRAKES, DON'T YOU DARE STOP!",
    "Kabir: Rush mode activated! Brains off, triggers held!",
    "Marcus: Executing rush. Smoke first, check close angles.",
    "Sunny: Rushing! Oh gosh, let's do this!"
};

new const g_fallbackHold[][] = {
    "Vikram: Holding this choke. Nothing gets through me.",
    "Kabir: Camping like a true noob. Nobody moves.",
    "Marcus: Holding default. Sightline secure.",
    "Sunny: Holding right here, staring at the door!"
};

new const g_fallbackSave[][] = {
    "Vikram: Shit round, saving my rifle. Fall back!",
    "Kabir: Tactical retreat! My gun is too expensive to donate.",
    "Marcus: Conceding round to preserve economy. Save weapons.",
    "Sunny: Okay, running away to save my gun!"
};

new const g_fallbackGeneral[][] = {
    "Vikram: Hell yeah! Let's wipe these clowns!",
    "Kabir: Did someone order a clutch or just a clown show?",
    "Marcus: Target eliminated. Keep spacing.",
    "Sunny: Yay! Did you see that?! We are doing great!",
    "Vikram: What the fuck was that shot?! Clean as hell!",
    "Kabir: Bruh, someone clip that disaster!",
    "Marcus: Good discipline team. Maintain this tempo."
};

new const g_fallbackDeathReact[][] = {
    "Vikram: NOOO! They got our teammate! Trade that kill now!",
    "Kabir: Bro died in 4K! Don't worry, I'll avenge you!",
    "Marcus: Teammate down. Refrag and hold crossfires.",
    "Sunny: Oh no! Our teammate died! Please be careful!",
    "Vikram: He was holding that angle with an AWP! Watch out!",
    "Kabir: Avenge him brothers! Don't let him get away with that!",
    "Marcus: Man down. Maintain crossfire and trade the frag.",
    "Sunny: Eek! They just took down our teammate!"
};

new const g_fallbackKillReact[][] = {
    "Vikram: BOOM! Sit down! That is how we clear a site!",
    "Kabir: Deleted from the server! Someone check his monitor!",
    "Marcus: Target eliminated. One less to worry about.",
    "Sunny: Nice shot! You actually got him!",
    "Vikram: Easy frag! Keep pushing, they are shaking!",
    "Kabir: Bro didn't even have time to click his mouse!"
};

new const g_fallbackIdle[][] = {
    "Vikram: Check your corners boys, I have a feeling they're stacking.",
    "Kabir: My crosshair placement is so crisp today it should be illegal.",
    "Marcus: Stay disciplined. Don't give them free 1v1 peeks.",
    "Sunny: Guys, wait up for me! Don't leave me holding the rear alone!",
    "Vikram: If anyone flashes me one more time I'm buying a Negev.",
    "Kabir: Bro my ping is fine, it's the 2004 hitreg that's haunted!",
    "Marcus: Hold your utility until we hear footsteps at the choke.",
    "Sunny: Do you think the enemy bots know we're talking about them?",
    "Vikram: Don't bait me on the entry! Swing with me on contact!",
    "Kabir: Who bought a nightvision goggles on Dust2?! Confess right now!",
    "Marcus: Watch the flank. Someone always sneaks through mid.",
    "Sunny: I bought extra ammo and a defuse kit just in case!"
};

public plugin_init() {
    register_plugin(PLUGIN_NAME, PLUGIN_VERSION, PLUGIN_AUTHOR);

    g_cvarDebug = register_cvar("ai_debug", "1");
    g_cvarCooldownGlobal = register_cvar("ai_sound_cooldown_global", "3.0");
    g_cvarCooldownTag = register_cvar("ai_sound_cooldown_tag", "8.0");

    // Setup logging path: logs/mod.log in mod root
    get_basedir(g_logFile, charsmax(g_logFile));
    formatex(g_logFile, charsmax(g_logFile), "logs/mod.log");

    // Initialize sound tag state and scan czero/sound/ai_teammates/<tag>/
    for (new i = 0; i < MAX_TAGS; i++) {
        g_lastTagSoundTime[i] = -99.0;
        g_lastTagFileIndex[i] = -1;
        g_tagFileCount[i] = 0;
    }
    scan_sound_folders();

    log_step(1, "Plugin loaded (Metamod 'meta list' shows it). AMX Mod X hook initialized.");
    debug_log("[AI] ========================================");
    debug_log("[AI] CZ AI Teammates Plugin v%s Loaded", PLUGIN_VERSION);
    debug_log("[AI] ========================================");

    // Console & Server Commands
    register_concmd("ai_say", "cmd_srv_ai_say", -1, "<bot> <msg> - Makes a bot speak in team chat");
    register_concmd("ai_test_say", "cmd_ai_test_say", -1, "Makes a bot say a line in team chat with name & team color");
    register_concmd("ai_test_ping", "cmd_ai_test_ping", -1, "Tests the link plugin -> brain -> plugin");
    register_concmd("ai_test_sound", "cmd_ai_test_sound", -1, "<tag> - Plays a random meme sound from that tag");
    register_concmd("ai_sound_list", "cmd_ai_sound_list", -1, "Prints every meme sound tag with file count");
    register_concmd("ai_sound_menu", "cmd_ai_sound_menu", -1, "Opens the in-game voice pack sound menu");
    register_concmd("ai_force_fight", "cmd_ai_force_fight", -1, "Starts a bot fight/argument now");
    register_concmd("ai_force_chat", "cmd_ai_force_chat", -1, "Plays next idle chat script now");
    register_concmd("ai_reset", "cmd_ai_reset", -1, "Clears chatter queue and resets fight memory");
    register_concmd("ai_status", "cmd_ai_status", -1, "Shows plugin, brain, API, requests left, queue, fight state");

    // Hook player chat (say and say_team)
    register_clcmd("say", "hook_player_say");
    register_clcmd("say_team", "hook_player_say_team");

    // Hook game events (both GoldSrc LogEvents and DeathMsg "a"/"b" for Condition Zero compatibility)
    register_logevent("logevent_kill", 3, "1=killed");
    register_event("DeathMsg", "event_death", "a");
    register_event("DeathMsg", "event_death", "b");
    register_logevent("event_round_start", 2, "1=Round_Start");
    register_event("SendAudio", "event_bomb_planted", "a", "2=%!MRAD_BOMBPL");
    register_event("SendAudio", "event_bomb_defused", "a", "2=%!MRAD_BOMBDEF");
    register_event("SendAudio", "event_target_bombed", "a", "2=%!MRAD_TARGETBOM");
    register_event("SendAudio", "event_terwin", "a", "2=%!MRAD_terwin");
    register_event("SendAudio", "event_ctwin", "a", "2=%!MRAD_ctwin");

    // Open UDP socket to Brain service
    connect_to_brain();

    // Poll incoming Brain packets every 0.1s and send "HEARTBEAT|alive" every 2.0s (Step 2)
    set_task(0.1, "socket_poll_task", _, _, _, "b");
    set_task(2.0, "send_heartbeat_task", _, _, _, "b");
    set_task(8.0, "check_brain_startup_task");
    set_task(random_float(10.0, 16.0), "idle_chatter_watchdog_task", 4040);
}

public idle_chatter_watchdog_task() {
    // Reschedule next idle chatter check in 10 to 20 seconds (Step 5.5)
    set_task(random_float(10.0, 20.0), "idle_chatter_watchdog_task", 4040);

    if (!find_human_player()) return;

    new Float:now = get_gametime();
    // If Brain already displayed a line within the last 10s, don't overlap
    if (now - g_lastChatDisplayTime < 10.0) return;

    if (g_socket > 0 && g_brainConnected) {
        // If Brain hasn't sent a line in 16s, nudge it with FORCE_CHAT
        if (now - g_lastChatDisplayTime >= 16.0) {
            new packet[] = "FORCE_CHAT";
            socket_send(g_socket, packet, strlen(packet));
        }
        return;
    }

    // Local in-game idle chatter (10-20s intervals, no standalone timer sounds per Step 4)
    new total = sizeof(g_fallbackIdle);
    new idx = random(total);
    if (total > 1 && idx == g_lastIdleIndex) {
        idx = (idx + 1) % total;
    }
    g_lastIdleIndex = idx;

    new bot_name[32], reply_text[128];
    strtok(g_fallbackIdle[idx], bot_name, charsmax(bot_name), reply_text, charsmax(reply_text), ':');
    trim(reply_text);
    execute_bot_say(bot_name, reply_text);
}

public check_brain_startup_task() {
    if (!g_brainConnected && !g_offlineWarned) {
        g_offlineWarned = true;
        ai_chat_print(0, print_team_default, "^4[AI Team] ^1AI Brain not detected yet (using local fallback until Brain connects).");
    }
}

public plugin_end() {
    // Stop any playing sound in-engine immediately when map/game closes (Step 2 & Step 5.4)
    client_cmd(0, "stopsound");

    if (g_socket > 0) {
        new bye_pkt[] = "GOODBYE|shutdown";
        socket_send(g_socket, bye_pkt, strlen(bye_pkt));
        socket_close(g_socket);
        g_socket = -1;
    }
}

// ==========================================
// SAFE IN-GAME CHAT & DEBUG LOGGING HELPERS
// ==========================================

stock sanitize_chat_text(text[], maxlen) {
    replace_all(text, maxlen, "%", "pct");
}

stock strip_color_codes(text[], maxlen) {
    replace_all(text, maxlen, "^1", "");
    replace_all(text, maxlen, "^2", "");
    replace_all(text, maxlen, "^3", "");
    replace_all(text, maxlen, "^4", "");
}

stock ai_chat_print(target, color_sender, const fmt[], any:...) {
    new buffer[256];
    vformat(buffer, charsmax(buffer), fmt, 4);

    if (strlen(buffer) > MAX_CHAT_LEN) {
        buffer[MAX_CHAT_LEN - 3] = '.';
        buffer[MAX_CHAT_LEN - 2] = '.';
        buffer[MAX_CHAT_LEN - 1] = '.';
        buffer[MAX_CHAT_LEN] = EOS;
    }

#if AMXX_VERSION_NUM >= 183
    new sender = color_sender;
    if (sender > 0 && !is_user_connected(sender)) {
        sender = print_team_default;
    }
    client_print_color(target, sender, "%s", buffer);
#else
    strip_color_codes(buffer, charsmax(buffer));
    client_print(target, print_chat, "%s", buffer);
#endif
}

stock notify_player_and_chat(id, const chat_fmt[], any:...) {
    new buffer[256];
    vformat(buffer, charsmax(buffer), chat_fmt, 3);

    ai_chat_print(0, (id > 0 && is_user_connected(id)) ? id : print_team_default, "%s", buffer);

    new plain[256];
    copy(plain, charsmax(plain), buffer);
    strip_color_codes(plain, charsmax(plain));
    if (id > 0 && is_user_connected(id)) {
        console_print(id, "%s", plain);
    }
    debug_log("%s", plain);
}

stock debug_log(const fmt[], any:...) {
#if defined DEBUG
    if (g_cvarDebug && !get_pcvar_num(g_cvarDebug)) {
        return;
    }
    new buffer[256];
    vformat(buffer, charsmax(buffer), fmt, 2);
    server_print("%s", buffer);
#else
    #pragma unused fmt
#endif
}

stock log_step(step, const message[]) {
    new msg[256];
    formatex(msg, charsmax(msg), "[Step %d] %s", step, message);
    debug_log("[AI] %s", msg);

    new fp = fopen(g_logFile, "a+");
    if (fp) {
        new timestamp[32];
        get_time("%Y-%m-%d %H:%M:%S", timestamp, charsmax(timestamp));
        fprintf(fp, "[%s] %s^n", timestamp, msg);
        fclose(fp);
    }
}

stock log_offline(const reason[]) {
    if (g_offlineWarned) return;
    g_offlineWarned = true;

    new msg[256];
    formatex(msg, charsmax(msg), "[AI] offline: %s", reason);
    debug_log("%s", msg);

    ai_chat_print(0, print_team_default, "^4[AI] ^1Brain service offline (%s). Run ^4play_czero.bat ^1(using local fallback).", reason);

    new fp = fopen(g_logFile, "a+");
    if (fp) {
        new timestamp[32];
        get_time("%Y-%m-%d %H:%M:%S", timestamp, charsmax(timestamp));
        fprintf(fp, "[%s] %s^n", timestamp, msg);
        fclose(fp);
    }
}

// ==========================================
// STEP 4: IN-ENGINE WAV SOUND SYSTEM (czero/sound/ai_teammates/<tag>/)
// ==========================================

/**
 * Scans czero/sound/ai_teammates/<tag>/ at plugin init to cache all 16-bit 22050 Hz mono WAVs.
 */
stock scan_sound_folders() {
    new dir_path[128], filename[MAX_FILENAME_LEN];
    new total_loaded = 0;

    for (new t = 0; t < MAX_TAGS; t++) {
        g_tagFileCount[t] = 0;
        formatex(dir_path, charsmax(dir_path), "sound/ai_teammates/%s", g_soundTags[t]);

        new dp = open_dir(dir_path, filename, charsmax(filename));
        if (!dp) continue;

        do {
            new len = strlen(filename);
            if (len > 4 && equali(filename[len - 4], ".wav")) {
                if (g_tagFileCount[t] < MAX_FILES_PER_TAG) {
                    copy(g_tagFiles[t][g_tagFileCount[t]], MAX_FILENAME_LEN - 1, filename);
                    g_tagFileCount[t]++;
                    total_loaded++;
                }
            }
        } while (next_file(dp, filename, charsmax(filename)));

        close_dir(dp);
    }

    debug_log("[AI] Cached %d in-game WAV files across %d tags from sound/ai_teammates/.", total_loaded, MAX_TAGS);
}

stock find_tag_index(const tag[]) {
    for (new i = 0; i < MAX_TAGS; i++) {
        if (equali(tag, g_soundTags[i])) {
            return i;
        }
    }
    return -1;
}

stock get_friendly_sound_name(const raw_sound[], const tag[], output[], maxlen) {
    if (raw_sound[0] != EOS) {
        new base[128];
        copy(base, charsmax(base), raw_sound);

        new last_slash = -1;
        for (new i = 0; base[i] != EOS; i++) {
            if (base[i] == '/' || base[i] == '\') {
                last_slash = i;
            }
        }
        if (last_slash != -1 && base[last_slash + 1] != EOS) {
            copy(base, charsmax(base), base[last_slash + 1]);
        }

        new len = strlen(base);
        if (len > 4 && (equali(base[len - 4], ".wav") || equali(base[len - 4], ".mp3"))) {
            base[len - 4] = EOS;
        }

        for (new i = 0; i < sizeof(g_fileLookupKeys); i++) {
            if (equali(base, g_fileLookupKeys[i])) {
                copy(output, maxlen, g_fileLookupLabels[i]);
                return;
            }
        }

        new start = 0;
        while (base[start] != EOS && ((base[start] >= '0' && base[start] <= '9') || base[start] == '_' || base[start] == '-')) {
            start++;
        }
        if (base[start] != EOS) {
            copy(base, charsmax(base), base[start]);
        }

        replace_all(base, charsmax(base), "_", " ");
        replace_all(base, charsmax(base), "-", " ");
        trim(base);

        if (base[0] != EOS) {
            copy(output, maxlen, base);
            return;
        }
    }

    new tag_idx = find_tag_index(tag);
    if (tag_idx != -1) {
        copy(output, maxlen, g_soundDefaultLabels[tag_idx]);
        return;
    }

    if (tag[0] != EOS) {
        copy(output, maxlen, tag);
        replace_all(output, maxlen, "_", " ");
        return;
    }

    copy(output, maxlen, "voice line");
}

/**
 * Picks a random WAV from czero/sound/ai_teammates/<tag>/ (never the same file twice in a row),
 * enforces the 3s global and 8s per-tag cooldowns, plays it inside the GoldSrc engine via `spk`,
 * and prints colored attribution in chat.
 */
stock play_attributed_sound(id, const raw_sound_path[], const tag[], const reason[], const fallback_speaker[] = "", const precomputed_friendly[] = "", bool:bypass_cooldown = false) {
    new tag_idx = find_tag_index(tag);
    new Float:now = get_gametime();

    // Enforce Step 4 Cooldowns: max 1 sound every 3s globally, same tag at most once every 8s
    if (!bypass_cooldown && now > 1.0) {
        new Float:global_cd = g_cvarCooldownGlobal ? get_pcvar_float(g_cvarCooldownGlobal) : 3.0;
        new Float:tag_cd = g_cvarCooldownTag ? get_pcvar_float(g_cvarCooldownTag) : 8.0;

        if (g_lastGlobalSoundTime > 0.0 && (now - g_lastGlobalSoundTime) < global_cd) {
            debug_log("[AI] Sound tag '%s' skipped (global cooldown %.1fs active)", tag, global_cd);
            return;
        }
        if (tag_idx != -1 && g_lastTagSoundTime[tag_idx] > 0.0 && (now - g_lastTagSoundTime[tag_idx]) < tag_cd) {
            debug_log("[AI] Sound tag '%s' skipped (tag cooldown %.1fs active)", tag, tag_cd);
            return;
        }
    }

    // 1. Resolve triggering player or bot safely
    new speaker_name[MAX_NAME_LENGTH];
    new color_sender = print_team_blue;

    if (id > 0 && id <= MAX_PLAYERS && is_user_connected(id)) {
        get_user_name(id, speaker_name, charsmax(speaker_name));
        color_sender = id;
    } else if (fallback_speaker[0] != EOS) {
        new bot_id = find_bot_by_name(fallback_speaker);
        if (bot_id > 0 && is_user_connected(bot_id)) {
            get_user_name(bot_id, speaker_name, charsmax(speaker_name));
            color_sender = bot_id;
        } else {
            copy(speaker_name, charsmax(speaker_name), fallback_speaker);
            color_sender = print_team_blue;
        }
    } else if (id == 0) {
        copy(speaker_name, charsmax(speaker_name), "Server");
        color_sender = print_team_grey;
    } else {
        copy(speaker_name, charsmax(speaker_name), "Disconnected Player");
        color_sender = print_team_grey;
    }

    // 2. Pick random WAV file from czero/sound/ai_teammates/<tag>/ (never same file twice in a row)
    new chosen_wav[MAX_FILENAME_LEN] = "";
    new spk_path[128] = "";

    if (raw_sound_path[0] != EOS) {
        copy(spk_path, charsmax(spk_path), raw_sound_path);
        copy(chosen_wav, charsmax(chosen_wav), raw_sound_path);
    } else if (tag_idx != -1 && g_tagFileCount[tag_idx] > 0) {
        new count = g_tagFileCount[tag_idx];
        new chosen_idx = 0;

        if (count == 1) {
            chosen_idx = 0;
        } else {
            chosen_idx = random(count);
            if (chosen_idx == g_lastTagFileIndex[tag_idx]) {
                chosen_idx = (chosen_idx + 1 + random(count - 1)) % count;
            }
        }

        g_lastTagFileIndex[tag_idx] = chosen_idx;
        copy(chosen_wav, charsmax(chosen_wav), g_tagFiles[tag_idx][chosen_idx]);
        formatex(spk_path, charsmax(spk_path), "ai_teammates/%s/%s", g_soundTags[tag_idx], chosen_wav);
    }

    // Update cooldown timestamps
    g_lastGlobalSoundTime = now;
    if (tag_idx != -1) {
        g_lastTagSoundTime[tag_idx] = now;
    }

    // 3. Play sound inside the Condition Zero engine via client_cmd "spk"
    if (spk_path[0] != EOS) {
        client_cmd(0, "spk ^"%s^"", spk_path);
    }

    // 4. Resolve readable sound label and broadcast colored attribution to chat
    new friendly_label[64];
    if (precomputed_friendly[0] != EOS) {
        copy(friendly_label, charsmax(friendly_label), precomputed_friendly);
    } else {
        get_friendly_sound_name(chosen_wav, tag, friendly_label, charsmax(friendly_label));
    }

    sanitize_chat_text(speaker_name, charsmax(speaker_name));
    sanitize_chat_text(friendly_label, charsmax(friendly_label));

    new clean_reason[64];
    copy(clean_reason, charsmax(clean_reason), reason);
    sanitize_chat_text(clean_reason, charsmax(clean_reason));

    if (clean_reason[0] != EOS) {
        ai_chat_print(0, color_sender, "^4[SOUND] ^3%s ^1played ^4^"%s^" ^1(%s)", speaker_name, friendly_label, clean_reason);
    } else if (tag[0] != EOS) {
        ai_chat_print(0, color_sender, "^4[SOUND] ^3%s ^1played ^4^"%s^" ^1(tag: %s)", speaker_name, friendly_label, tag);
    } else {
        ai_chat_print(0, color_sender, "^4[SOUND] ^3%s ^1played ^4^"%s^"", speaker_name, friendly_label);
    }

    new logMsg[256];
    formatex(logMsg, charsmax(logMsg), "Sound played in-game by '%s': ^"%s^" [%s] (%s)", speaker_name, friendly_label, spk_path, clean_reason[0] ? clean_reason : "event");
    log_step(7, logMsg);
}

// ==========================================
// STEP 2: BRAIN SERVICE UDP BRIDGE & 2s HEARTBEAT
// ==========================================

stock connect_to_brain() {
    new err = 0;
    if (g_socket > 0) {
        socket_close(g_socket);
        g_socket = -1;
    }

    g_socket = socket_open(BRAIN_HOST, BRAIN_PORT, SOCKET_UDP, err, SOCK_NON_BLOCKING);
    if (g_socket > 0) {
        new init_pkt[] = "PING|init";
        socket_send(g_socket, init_pkt, strlen(init_pkt));
    } else {
        log_offline("Failed to open UDP socket on port 27115");
    }
}

/**
 * Step 2: Sends a "game alive" heartbeat every 2.0 seconds to the Brain Service.
 */
public send_heartbeat_task() {
    if (g_socket <= 0) {
        connect_to_brain();
        return;
    }

    new hb_pkt[] = "HEARTBEAT|alive";
    socket_send(g_socket, hb_pkt, strlen(hb_pkt));

    new Float:now = get_gametime();
    if (g_brainConnected && (now - g_lastBrainHeartbeat > 6.0)) {
        g_brainConnected = false;
        copy(g_apiStatus, charsmax(g_apiStatus), "Offline (Local Bank)");
    }
}

public socket_poll_task() {
    if (g_socket <= 0) return;

    // Drain up to 8 UDP packets per tick so SOUND + SAY arrive together without delay
    new loops = 0;
    while (loops < 8 && socket_is_readable(g_socket, 0)) {
        new buffer[512];
        new bytes = socket_recv(g_socket, buffer, charsmax(buffer));
        if (bytes > 0) {
            buffer[bytes] = 0;
            process_brain_packet(buffer);
        } else {
            break;
        }
        loops++;
    }
}

stock process_brain_packet(const packet[]) {
    new bool:wasConnected = g_brainConnected;
    g_brainConnected = true;
    g_offlineWarned = false;
    g_lastBrainHeartbeat = get_gametime();

    new parts[8][192];
    new count = explode_string(packet, "|", parts, 8, 191);
    if (count < 1) return;

    if (equal(parts[0], "HEARTBEAT_ACK")) {
        if (!wasConnected) {
            ai_chat_print(0, print_team_default, "^4[AI Team] ^1Connected to AI Teammates Brain Service (^4%s^1).", g_apiStatus);
        }
        return;
    }
    else if (equal(parts[0], "PONG")) {
        log_step(3, "Brain service responded with PONG.");
        if (!wasConnected) {
            ai_chat_print(0, print_team_default, "^4[AI] ^1Connected to AI Teammates Brain Service (^4%s^1).", g_apiStatus);
        }
    }
    else if (equal(parts[0], "SAY")) {
        // Format: SAY|bot_name|message
        new bot_name[32], message[192];
        copy(bot_name, charsmax(bot_name), parts[1]);
        copy(message, charsmax(message), parts[2]);

        execute_bot_say(bot_name, message);
        g_awaitingReply = false;
    }
    else if (equal(parts[0], "SOUND")) {
        // Step 4 Format: SOUND|speaker|tag|reason (or legacy SOUND|speaker|tag|friendly|reason)
        new speaker[32], tag[32], reason[64];
        copy(speaker, charsmax(speaker), parts[1]);
        copy(tag, charsmax(tag), parts[2]);

        if (count >= 5 && parts[4][0] != EOS) {
            copy(reason, charsmax(reason), parts[4]);
        } else if (count >= 4 && parts[3][0] != EOS) {
            copy(reason, charsmax(reason), parts[3]);
        } else if (g_lastEventReason[0] != EOS) {
            copy(reason, charsmax(reason), g_lastEventReason);
        } else {
            formatex(reason, charsmax(reason), "tag: %s", tag);
        }

        new speaker_id = find_player_or_bot_by_name(speaker);
        if (!speaker_id && g_lastEventActorId > 0 && is_user_connected(g_lastEventActorId)) {
            speaker_id = g_lastEventActorId;
        }

        // Plugin picks random WAV from czero/sound/ai_teammates/<tag>/ and plays it in-engine!
        play_attributed_sound(speaker_id, "", tag, reason, speaker, "", false);
        g_lastEventReason[0] = EOS;
    }
    else if (equal(parts[0], "ORDER")) {
        execute_bot_order(parts[1]);
    }
    else if (equal(parts[0], "CONSOLE")) {
        debug_log("[AI] %s", parts[1]);
        client_print(0, print_console, "[AI] %s", parts[1]);
        ai_chat_print(0, print_team_default, "^4[AI] ^1%s", parts[1]);
    }
    else if (equal(parts[0], "STATUS")) {
        copy(g_apiStatus, charsmax(g_apiStatus), parts[1]);
        g_requestsLeft = str_to_num(parts[2]);
        if (count > 3) g_queueSize = str_to_num(parts[3]);
        if (count > 4) copy(g_fightState, charsmax(g_fightState), parts[4]);
        if (count > 5) copy(g_chatterSpeed, charsmax(g_chatterSpeed), parts[5]);
        if (count > 6) copy(g_fightFreq, charsmax(g_fightFreq), parts[6]);
        if (count > 7) copy(g_chatStyle, charsmax(g_chatStyle), parts[7]);
    }
}

// ==========================================
// STEP 3: ON-SCREEN IN-GAME BOT CHAT
// ==========================================

/**
 * Returns 1 for Terrorist, 2 for CT, 0 otherwise using core <amxmodx> get_user_team
 * (avoids <cstrike> module CRC mismatch on Condition Zero mp.dll).
 */
stock get_player_team_num(id) {
    if (id <= 0 || !is_user_connected(id)) return 0;
    new team_str[16];
    new team_id = get_user_team(id, team_str, charsmax(team_str));
    if (team_str[0] == 'T' || team_id == 1) return 1;
    if (team_str[0] == 'C' || team_id == 2) return 2;
    return 0;
}

/**
 * Displays the bot line on the player's HUD chat screen in authentic team colors.
 * Why client_print_color (SayText) is used as primary display:
 *  - In Condition Zero, engclient_cmd(bot_id, "say_team", ...) is hidden by GoldSrc's
 *    Host_Say filter whenever the bot is dead and the human player is alive, or if the bot
 *    is on the opposite team.
 *  - client_print_color sends the native GoldSrc SayText HUD packet with the bot's team color
 *    so it is 100% visible on screen in all states (alive, dead, or before bots spawn).
 */
stock execute_bot_say(const bot_name[], const message[]) {
    if (!message[0]) return;
    g_lastChatDisplayTime = get_gametime();

    new bot_id = find_bot_by_name(bot_name);
    if (!bot_id) {
        bot_id = find_team_bot();
    }

    new human_id = find_human_player();
    new team_num = 2; // Default CT (Blue)
    new color_sender = print_team_blue;

    if (bot_id && is_user_connected(bot_id)) {
        team_num = get_player_team_num(bot_id);
        color_sender = bot_id;
    } else if (human_id && is_user_connected(human_id)) {
        team_num = get_player_team_num(human_id);
        color_sender = (team_num == 1) ? print_team_red : print_team_blue;
    }

    new safe_name[32], safe_msg[192];
    copy(safe_name, charsmax(safe_name), bot_name);
    copy(safe_msg, charsmax(safe_msg), message);
    sanitize_chat_text(safe_name, charsmax(safe_name));
    sanitize_chat_text(safe_msg, charsmax(safe_msg));

    if (team_num == 1) {
        ai_chat_print(0, color_sender, "^3(Terrorist) %s ^1:  %s", safe_name, safe_msg);
    } else {
        ai_chat_print(0, color_sender, "^3(Counter-Terrorist) %s ^1:  %s", safe_name, safe_msg);
    }

    new logMsg[256];
    formatex(logMsg, charsmax(logMsg), "Chat message sent into the game as a bot: [%s] %s", safe_name, safe_msg);
    log_step(6, logMsg);
}

stock execute_bot_order(const order[]) {
    new human_id = find_human_player();

    if (equal(order, "follow")) {
        if (human_id) engclient_cmd(human_id, "followme");
        server_cmd("bot_follow_user; bot_stop 0; bot_defer_to_human 1");
    } else if (equal(order, "rush")) {
        if (human_id) engclient_cmd(human_id, "stormfront");
        server_cmd("bot_stop 0; bot_defer_to_human 0");
    } else if (equal(order, "hold")) {
        if (human_id) engclient_cmd(human_id, "holdpos");
        server_cmd("bot_stop 1");
    } else if (equal(order, "save") || equal(order, "fallback")) {
        if (human_id) engclient_cmd(human_id, "fallback");
        server_cmd("bot_defer_to_human 1; bot_stop 1");
    } else if (equal(order, "drop")) {
        new bot_id = find_team_bot();
        if (bot_id && is_user_connected(bot_id)) {
            engclient_cmd(bot_id, "drop");
        }
    } else if (equal(order, "regroup")) {
        if (human_id) engclient_cmd(human_id, "regroup");
    }
}

stock find_human_player() {
    for (new i = 1; i <= get_maxplayers(); i++) {
        if (is_user_connected(i) && !is_user_bot(i)) {
            return i;
        }
    }
    return 0;
}

stock find_bot_by_name(const bot_name[]) {
    if (!bot_name[0]) return 0;
    for (new i = 1; i <= get_maxplayers(); i++) {
        if (is_user_connected(i) && is_user_bot(i)) {
            new name[32];
            get_user_name(i, name, charsmax(name));
            if (containi(name, bot_name) != -1) {
                return i;
            }
        }
    }
    return 0;
}

stock find_player_or_bot_by_name(const target_name[]) {
    if (!target_name[0]) return 0;
    for (new i = 1; i <= get_maxplayers(); i++) {
        if (is_user_connected(i)) {
            new name[32];
            get_user_name(i, name, charsmax(name));
            if (containi(name, target_name) != -1) {
                return i;
            }
        }
    }
    return 0;
}

stock find_team_bot() {
    new human = find_human_player();
    new hTeam = 0;
    if (human && is_user_connected(human)) {
        hTeam = get_player_team_num(human);
    }

    for (new i = 1; i <= get_maxplayers(); i++) {
        if (is_user_connected(i) && is_user_bot(i)) {
            if (hTeam == 0 || get_player_team_num(i) == hTeam) {
                return i;
            }
        }
    }
    return 0;
}

// ==========================================
// CHAT HOOKS & KEYWORD SOUND TRIGGERS
// ==========================================

public hook_player_say(id) {
    if (!is_user_connected(id) || is_user_bot(id)) return PLUGIN_CONTINUE;

    new message[192];
    read_args(message, charsmax(message));
    remove_quotes(message);
    trim(message);
    if (!message[0]) return PLUGIN_CONTINUE;

    handle_chat_input(id, message, false);
    return PLUGIN_CONTINUE;
}

public hook_player_say_team(id) {
    if (!is_user_connected(id) || is_user_bot(id)) return PLUGIN_CONTINUE;

    new message[192];
    read_args(message, charsmax(message));
    remove_quotes(message);
    trim(message);
    if (!message[0]) return PLUGIN_CONTINUE;

    handle_chat_input(id, message, true);
    return PLUGIN_CONTINUE;
}

stock bool:check_chat_sound_command(id, const message[]) {
    if (message[0] != '!' && message[0] != '/') {
        return false;
    }

    new cmd[32], arg[32];
    strtok(message[1], cmd, charsmax(cmd), arg, charsmax(arg), ' ');
    trim(cmd);
    trim(arg);

    if (equali(cmd, "sounds") || equali(cmd, "soundmenu") || equali(cmd, "voicemenu")) {
        open_sound_menu(id);
        return true;
    }

    if (equali(cmd, "status") || equali(cmd, "aistatus")) {
        cmd_ai_status(id);
        return true;
    }

    if (equali(cmd, "fight")) {
        cmd_ai_force_fight(id);
        return true;
    }

    new matched_tag[32] = "";
    if (equali(cmd, "sound") || equali(cmd, "play")) {
        if (arg[0] != EOS) {
            copy(matched_tag, charsmax(matched_tag), arg);
        } else {
            copy(matched_tag, charsmax(matched_tag), g_soundTags[random(12)]);
        }
    } else if (equali(cmd, "hype") || equali(cmd, "gg") || equali(cmd, "nice")) {
        copy(matched_tag, charsmax(matched_tag), "hype");
    } else if (equali(cmd, "headshot") || equali(cmd, "hs") || equali(cmd, "boom")) {
        copy(matched_tag, charsmax(matched_tag), "kill_headshot");
    } else if (equali(cmd, "shock") || equali(cmd, "omg") || equali(cmd, "wtf")) {
        copy(matched_tag, charsmax(matched_tag), "shock");
    } else if (equali(cmd, "praise") || equali(cmd, "wah")) {
        copy(matched_tag, charsmax(matched_tag), "praise");
    } else if (equali(cmd, "roast") || equali(cmd, "bruh")) {
        copy(matched_tag, charsmax(matched_tag), "roast");
    } else if (equali(cmd, "swear") || equali(cmd, "rage")) {
        copy(matched_tag, charsmax(matched_tag), "hindi_swear");
    } else if (equali(cmd, "sad") || equali(cmd, "fail") || equali(cmd, "rip")) {
        copy(matched_tag, charsmax(matched_tag), "fail_sad");
    } else if (equali(cmd, "sorry") || equali(cmd, "apology")) {
        copy(matched_tag, charsmax(matched_tag), "apology_getup");
    } else if (equali(cmd, "shutup") || equali(cmd, "quiet")) {
        copy(matched_tag, charsmax(matched_tag), "shut_up");
    } else if (equali(cmd, "hello") || equali(cmd, "hi") || equali(cmd, "greeting")) {
        copy(matched_tag, charsmax(matched_tag), "greeting");
    } else if (equali(cmd, "laugh") || equali(cmd, "lol") || equali(cmd, "haha")) {
        copy(matched_tag, charsmax(matched_tag), "laugh");
    } else if (equali(cmd, "bye") || equali(cmd, "goodbye")) {
        copy(matched_tag, charsmax(matched_tag), "goodbye");
    }

    if (matched_tag[0] != EOS) {
        new reason[64];
        formatex(reason, charsmax(reason), "typed %s", message);
        trigger_sound_by_player(id, matched_tag, reason, false);
        return true;
    }

    return false;
}

stock trigger_sound_by_player(id, const tag[], const reason[], bool:bypass_cooldown = false) {
    new player_name[MAX_NAME_LENGTH] = "Server";
    if (id > 0 && is_user_connected(id)) {
        get_user_name(id, player_name, charsmax(player_name));
    }

    g_lastEventActorId = id;
    copy(g_lastEventReason, charsmax(g_lastEventReason), reason);

    // Play the sound directly in-engine from czero/sound/ai_teammates/<tag>/
    play_attributed_sound(id, "", tag, reason, player_name, "", bypass_cooldown);
}

stock handle_chat_input(id, const message[], bool:is_team) {
    if (!is_user_connected(id)) return;

    if (check_chat_sound_command(id, message)) {
        return;
    }

    new name[MAX_NAME_LENGTH];
    get_user_name(id, name, charsmax(name));

    new logMsg[256];
    formatex(logMsg, charsmax(logMsg), "Game event sent from plugin to brain service: player_chat by '%s' ('%s')", name, message);
    log_step(2, logMsg);

    g_awaitingReply = true;
    g_lastChatSpeakerId = id;
    copy(g_lastChatMessage, charsmax(g_lastChatMessage), message);

    g_lastEventActorId = id;
    formatex(g_lastEventReason, charsmax(g_lastEventReason), "reply to %s's chat", name);

    if (g_socket > 0) {
        new packet[256];
        formatex(packet, charsmax(packet), "EVENT|chat|%s|CT|%d|%s", name, is_team ? 1 : 0, message);
        socket_send(g_socket, packet, strlen(packet));
    } else {
        log_offline("Brain service socket not open. Triggering local reply.");
    }

    remove_task(1337);
    set_task(2.5, "fallback_reply_check_task", 1337);
}

public fallback_reply_check_task() {
    if (!g_awaitingReply) return;
    g_awaitingReply = false;

    log_offline("No reply received in 2.5s. Triggering instant local reply bank.");
    trigger_local_reply(g_lastChatSpeakerId, g_lastChatMessage);
}

stock trigger_local_reply(requester_id, const message[]) {
    new msg_lower[192];
    copy(msg_lower, charsmax(msg_lower), message);
    strtoupper(msg_lower);

    new chosen_line[128];
    new order[16] = "";
    new tag[32] = "hype";

    if (contain(msg_lower, "HELP") != -1 || contain(msg_lower, "COVER") != -1 || contain(msg_lower, "WHERE") != -1) {
        copy(chosen_line, charsmax(chosen_line), g_fallbackHelp[random(sizeof(g_fallbackHelp))]);
        copy(order, charsmax(order), "follow");
        copy(tag, charsmax(tag), "apology_getup");
    } else if (contain(msg_lower, "RUSH") != -1 || contain(msg_lower, "GO B") != -1 || contain(msg_lower, "GO A") != -1) {
        copy(chosen_line, charsmax(chosen_line), g_fallbackRush[random(sizeof(g_fallbackRush))]);
        copy(order, charsmax(order), "rush");
        copy(tag, charsmax(tag), "hype");
    } else if (contain(msg_lower, "HOLD") != -1 || contain(msg_lower, "STAY") != -1 || contain(msg_lower, "WAIT") != -1) {
        copy(chosen_line, charsmax(chosen_line), g_fallbackHold[random(sizeof(g_fallbackHold))]);
        copy(order, charsmax(order), "hold");
        copy(tag, charsmax(tag), "greeting");
    } else if (contain(msg_lower, "SAVE") != -1) {
        copy(chosen_line, charsmax(chosen_line), g_fallbackSave[random(sizeof(g_fallbackSave))]);
        copy(order, charsmax(order), "save");
        copy(tag, charsmax(tag), "fail_sad");
    } else {
        copy(chosen_line, charsmax(chosen_line), g_fallbackGeneral[random(sizeof(g_fallbackGeneral))]);
        copy(tag, charsmax(tag), "laugh");
    }

    new bot_name[32], reply_text[128];
    strtok(chosen_line, bot_name, charsmax(bot_name), reply_text, charsmax(reply_text), ':');
    trim(reply_text);

    new reason[64] = "triggered by chat";
    if (requester_id > 0 && is_user_connected(requester_id)) {
        new req_name[MAX_NAME_LENGTH];
        get_user_name(requester_id, req_name, charsmax(req_name));
        formatex(reason, charsmax(reason), "reply to %s", req_name);
    }

    new bot_id = find_bot_by_name(bot_name);
    play_attributed_sound(bot_id, "", tag, reason, bot_name, "", false);
    execute_bot_say(bot_name, reply_text);
    if (order[0]) {
        execute_bot_order(order);
    }
}

// ==========================================
// INTERACTIVE VOICE PACK MENU (/sounds)
// ==========================================

public cmd_ai_sound_menu(id) {
    if (id <= 0 || !is_user_connected(id)) {
        console_print(id, "[AI] Sound menu can only be opened by an in-game player.");
        return PLUGIN_HANDLED;
    }
    open_sound_menu(id);
    return PLUGIN_HANDLED;
}

stock open_sound_menu(id) {
    if (id <= 0 || !is_user_connected(id)) return;

    new menu = menu_create("\y[AI Teammates] Voice Pack Sound Menu:", "sound_menu_handler");
    for (new i = 0; i < 12; i++) {
        new item_text[64];
        formatex(item_text, charsmax(item_text), "\w%s \y(%s - %d files)", g_soundDefaultLabels[i], g_soundTags[i], g_tagFileCount[i]);
        menu_additem(menu, item_text, g_soundTags[i]);
    }
    menu_setprop(menu, MPROP_EXIT, MEXIT_ALL);
    menu_display(id, menu, 0);
}

public sound_menu_handler(id, menu, item) {
    if (item == MENU_EXIT || !is_user_connected(id)) {
        menu_destroy(menu);
        return PLUGIN_HANDLED;
    }

    new tag[32], item_name[64], access, callback;
    menu_item_getinfo(menu, item, access, tag, charsmax(tag), item_name, charsmax(item_name), callback);
    menu_destroy(menu);

    trigger_sound_by_player(id, tag, "selected from sound menu", false);
    return PLUGIN_HANDLED;
}

// ==========================================
// GAME EVENT HOOKS
// ==========================================

public logevent_kill() {
    new arg0[128], arg2[128], weapon[32];
    read_logargv(0, arg0, charsmax(arg0));
    read_logargv(2, arg2, charsmax(arg2));
    read_logargv(4, weapon, charsmax(weapon));

    new killer_name[MAX_NAME_LENGTH], victim_name[MAX_NAME_LENGTH];
    parse_loguser(arg0, killer_name, charsmax(killer_name));
    parse_loguser(arg2, victim_name, charsmax(victim_name));

    new headshot = 0;
    if (read_logargc() >= 6) {
        new extra[64];
        read_logargv(5, extra, charsmax(extra));
        if (containi(extra, "headshot") != -1) {
            headshot = 1;
        }
    }

    new victim_id = find_player_or_bot_by_name(victim_name);
    new killer_id = find_player_or_bot_by_name(killer_name);
    handle_kill_event(killer_id, victim_id, killer_name, victim_name, weapon, headshot);
}

public event_death() {
    new killer = read_data(1);
    new victim = read_data(2);
    new headshot = read_data(3);
    new weapon[32];
    read_data(4, weapon, charsmax(weapon));

    new killer_name[MAX_NAME_LENGTH] = "World";
    new victim_name[MAX_NAME_LENGTH] = "Player";

    if (killer > 0 && killer <= MAX_PLAYERS && is_user_connected(killer)) {
        get_user_name(killer, killer_name, charsmax(killer_name));
    }
    if (victim > 0 && victim <= MAX_PLAYERS && is_user_connected(victim)) {
        get_user_name(victim, victim_name, charsmax(victim_name));
    }

    handle_kill_event(killer, victim, killer_name, victim_name, weapon, headshot);
}

stock handle_kill_event(killer_id, victim_id, const killer_name[], const victim_name[], const weapon[], headshot) {
    new Float:now = get_gametime();
    if (now - g_lastKillEventTime < 0.25) {
        return; // Deduplicate if both logevent_kill and DeathMsg fire
    }
    g_lastKillEventTime = now;

    if (killer_id > 0 && killer_id <= MAX_PLAYERS && is_user_connected(killer_id)) {
        g_lastEventActorId = killer_id;
    } else if (victim_id > 0 && victim_id <= MAX_PLAYERS && is_user_connected(victim_id)) {
        g_lastEventActorId = victim_id;
    }

    if (headshot) {
        formatex(g_lastEventReason, charsmax(g_lastEventReason), "triggered by headshot kill on %s", victim_name);
    } else {
        formatex(g_lastEventReason, charsmax(g_lastEventReason), "triggered by %s's death", victim_name);
    }

    new logMsg[256];
    formatex(logMsg, charsmax(logMsg), "Game event sent from plugin: kill by '%s' on '%s' with %s (hs:%d)", killer_name, victim_name, weapon, headshot);
    log_step(2, logMsg);

    if (g_socket > 0) {
        new packet[256];
        formatex(packet, charsmax(packet), "EVENT|kill|%s|%s|%s|%d", killer_name, victim_name, weapon, headshot);
        socket_send(g_socket, packet, strlen(packet));
    }

    // Schedule in-game reaction check (4.0s cooldown so 20 bots fighting doesn't spam)
    if (now - g_lastKillReactTime >= 4.0) {
        g_lastKillReactTime = now;
        copy(g_pendingVictimName, charsmax(g_pendingVictimName), victim_name);
        g_pendingIsHeadshot = (headshot != 0);
        new human_id = find_human_player();
        if (human_id && victim_id && is_user_connected(victim_id)) {
            g_pendingIsTeammateDeath = (get_player_team_num(victim_id) == get_player_team_num(human_id));
        } else {
            g_pendingIsTeammateDeath = true;
        }
        remove_task(2020);
        set_task(1.4, "offline_bot_death_react_task", 2020);
    }
}

public offline_bot_death_react_task() {
    // If the Python Brain already replied with a chat line in the last 1.5s, don't duplicate
    if (g_brainConnected && (get_gametime() - g_lastChatDisplayTime < 1.5)) {
        return;
    }

    new chosen_line[128];
    new tag[32];
    new reason[64];

    if (g_pendingIsTeammateDeath) {
        copy(chosen_line, charsmax(chosen_line), g_fallbackDeathReact[random(sizeof(g_fallbackDeathReact))]);
        copy(tag, charsmax(tag), "fail_sad");
        formatex(reason, charsmax(reason), "triggered by %s's death", g_pendingVictimName);
    } else {
        copy(chosen_line, charsmax(chosen_line), g_fallbackKillReact[random(sizeof(g_fallbackKillReact))]);
        copy(tag, charsmax(tag), g_pendingIsHeadshot ? "kill_headshot" : "hype");
        formatex(reason, charsmax(reason), g_pendingIsHeadshot ? "triggered by headshot kill on %s" : "triggered by kill on %s", g_pendingVictimName);
    }

    new bot_name[32], reply_text[128];
    strtok(chosen_line, bot_name, charsmax(bot_name), reply_text, charsmax(reply_text), ':');
    trim(reply_text);

    new bot_id = find_bot_by_name(bot_name);
    if (!bot_id) bot_id = find_team_bot();
    play_attributed_sound(bot_id, "", tag, reason, bot_name, "", false);
    execute_bot_say(bot_name, reply_text);
}

public event_round_start() {
    new Float:now = get_gametime();
    if (now - g_lastRoundStartTime < 4.0) {
        return; // Prevent warmup / bot-spawn spam
    }
    g_lastRoundStartTime = now;

    g_lastEventActorId = find_team_bot();
    copy(g_lastEventReason, charsmax(g_lastEventReason), "triggered by round start");

    log_step(2, "Game event sent from plugin: round_start");
    if (g_socket > 0) {
        new packet[] = "EVENT|round_start";
        socket_send(g_socket, packet, strlen(packet));
    }
    if (!g_brainConnected) {
        play_attributed_sound(g_lastEventActorId, "", "greeting", "triggered by round start", "Vikram", "", false);
        execute_bot_say("Vikram", "Round start! Let's get these frags boys!");
    }
}

public event_bomb_planted() {
    g_lastEventActorId = find_team_bot();
    copy(g_lastEventReason, charsmax(g_lastEventReason), "triggered by bomb plant");

    log_step(2, "Game event sent from plugin: bomb_planted");
    if (g_socket > 0) {
        new packet[] = "EVENT|bomb_planted";
        socket_send(g_socket, packet, strlen(packet));
    }
    if (!g_brainConnected) {
        play_attributed_sound(g_lastEventActorId, "", "shock", "triggered by bomb plant", "Marcus", "", false);
        execute_bot_say("Marcus", "Bomb has been planted! Lock down the site!");
    }
}

public event_bomb_defused() {
    g_lastEventActorId = find_team_bot();
    copy(g_lastEventReason, charsmax(g_lastEventReason), "triggered by bomb defuse");

    log_step(2, "Game event sent from plugin: bomb_defused");
    if (g_socket > 0) {
        new packet[] = "EVENT|bomb_defused";
        socket_send(g_socket, packet, strlen(packet));
    }
    if (!g_brainConnected) {
        play_attributed_sound(g_lastEventActorId, "", "hype", "triggered by bomb defuse", "Sunny", "", false);
        execute_bot_say("Sunny", "Bomb defused! That was way too close for comfort!");
    }
}

public event_target_bombed() {
    g_lastEventActorId = find_team_bot();
    copy(g_lastEventReason, charsmax(g_lastEventReason), "triggered by bomb explosion");

    log_step(2, "Game event sent from plugin: bomb_exploded");
    if (g_socket > 0) {
        new packet[] = "EVENT|bomb_exploded";
        socket_send(g_socket, packet, strlen(packet));
    }
    if (!g_brainConnected) {
        play_attributed_sound(g_lastEventActorId, "", "shock", "triggered by bomb explosion", "Kabir", "", false);
        execute_bot_say("Kabir", "Target bombed! BOOM BABY!");
    }
}

public event_ctwin() {
    new human_id = find_human_player();
    new bool:won = true;
    if (human_id && is_user_connected(human_id)) {
        won = (get_player_team_num(human_id) == 2);
    }
    notify_round_end(won);
}

public event_terwin() {
    new human_id = find_human_player();
    new bool:won = true;
    if (human_id && is_user_connected(human_id)) {
        won = (get_player_team_num(human_id) == 1);
    }
    notify_round_end(won);
}

stock notify_round_end(bool:won) {
    g_lastEventActorId = find_team_bot();
    copy(g_lastEventReason, charsmax(g_lastEventReason), won ? "triggered by round win" : "triggered by round loss");

    new logMsg[128];
    formatex(logMsg, charsmax(logMsg), "Game event sent from plugin: round_end (won: %d)", won ? 1 : 0);
    log_step(2, logMsg);
    if (g_socket > 0) {
        new packet[32];
        formatex(packet, charsmax(packet), "EVENT|round_end|%d", won ? 1 : 0);
        socket_send(g_socket, packet, strlen(packet));
    }
    if (!g_brainConnected) {
        if (won) {
            play_attributed_sound(g_lastEventActorId, "", "hype", "triggered by round win", "Vikram", "", false);
            execute_bot_say("Vikram", "THAT IS WHAT I'M TALKING ABOUT! Clean sweep!");
        } else {
            play_attributed_sound(g_lastEventActorId, "", "fail_sad", "triggered by round loss", "Kabir", "", false);
            execute_bot_say("Kabir", "We threw that round so hard it hurts physically.");
        }
    }
}

// ==========================================
// CONSOLE & SERVER COMMANDS
// ==========================================

public cmd_srv_ai_say(id) {
    new bot_name[32], message[192];
    read_argv(1, bot_name, charsmax(bot_name));
    read_argv(2, message, charsmax(message));
    if (!message[0]) {
        return cmd_ai_force_chat(id);
    }
    if (!bot_name[0]) copy(bot_name, charsmax(bot_name), "Vikram");
    execute_bot_say(bot_name, message);
    return PLUGIN_HANDLED;
}

public cmd_ai_test_say(id) {
    new bot_id = find_team_bot();
    new name[MAX_NAME_LENGTH] = "Vikram";

    if (bot_id && is_user_connected(bot_id)) {
        get_user_name(bot_id, name, charsmax(name));
    }
    execute_bot_say(name, "Hello! AI Teammate online and ready.");

    notify_player_and_chat(id, "^4[AI] ^1Test say complete: Bot ^3%s ^1spoke in team chat.", name);
    return PLUGIN_HANDLED;
}

public cmd_ai_test_ping(id) {
    if (g_socket <= 0) {
        notify_player_and_chat(id, "^4[AI] ^1PING FAILED: UDP socket is not initialized.");
        return PLUGIN_HANDLED;
    }

    new packet[] = "PING|manual";
    socket_send(g_socket, packet, strlen(packet));
    notify_player_and_chat(id, "^4[AI] ^1Ping sent to Brain Service (^4127.0.0.1:27115^1)...");
    return PLUGIN_HANDLED;
}

public cmd_ai_test_sound(id) {
    new tag[32];
    read_argv(1, tag, charsmax(tag));
    if (!tag[0]) {
        notify_player_and_chat(id, "^4[AI] ^1Usage: ^4ai_test_sound <tag> ^1(or type ^4!sound <tag> ^1in chat)");
        ai_chat_print(id, print_team_default, "^4[AI] ^1Tags: hype, kill_headshot, shock, praise, roast, hindi_swear, fail_sad, apology_getup, shut_up, greeting, laugh, goodbye");
        return PLUGIN_HANDLED;
    }

    new reason[64];
    formatex(reason, charsmax(reason), "command ai_test_sound %s", tag);
    trigger_sound_by_player(id, tag, reason, true);
    return PLUGIN_HANDLED;
}

public cmd_ai_sound_list(id) {
    console_print(id, "--------------------------------------------------");
    console_print(id, "[AI] In-Game WAV Sound Tags (czero/sound/ai_teammates/<tag>/):");
    for (new i = 0; i < 12; i++) {
        console_print(id, "[AI] - %-15s (%d WAV files) : %s", g_soundTags[i], g_tagFileCount[i], g_soundDefaultLabels[i]);
    }
    console_print(id, "--------------------------------------------------");
    console_print(id, "[AI] Test any tag with 'ai_test_sound <tag>' or '!sound <tag>'.");

    ai_chat_print(id, print_team_default, "^4[AI Sounds] ^112 tags installed in ^4czero/sound/ai_teammates/^1: hype, kill_headshot, shock, praise, roast...");
    ai_chat_print(id, print_team_default, "^4[AI Sounds] ^4fail_sad, apology_getup, shut_up, greeting, laugh, goodbye ^1(Type ^4!sounds ^1for menu)");
    return PLUGIN_HANDLED;
}

public cmd_ai_force_fight(id) {
    new caller[MAX_NAME_LENGTH] = "Server";
    if (id > 0 && is_user_connected(id)) {
        get_user_name(id, caller, charsmax(caller));
    }

    g_lastEventActorId = id;
    copy(g_lastEventReason, charsmax(g_lastEventReason), "triggered by bot fight");

    notify_player_and_chat(id, "^4[AI] ^3%s ^1started a teammate argument!", caller);

    if (g_socket > 0 && g_brainConnected) {
        new packet[] = "FORCE_FIGHT";
        socket_send(g_socket, packet, strlen(packet));
    } else {
        play_attributed_sound(find_bot_by_name("Vikram"), "", "roast", "triggered by bot fight", "Vikram", "", false);
        execute_bot_say("Vikram", "Kabir, who taught you to aim, a microwave?!");
        execute_bot_say("Kabir", "SHUT UP VIKRAM! Look at your own K/D!");
    }
    return PLUGIN_HANDLED;
}

public cmd_ai_force_chat(id) {
    g_lastEventActorId = id;
    copy(g_lastEventReason, charsmax(g_lastEventReason), "triggered by force chat");

    notify_player_and_chat(id, "^4[AI] ^1Triggering next bot chatter line...");
    if (g_socket > 0 && g_brainConnected) {
        new packet[] = "FORCE_CHAT";
        socket_send(g_socket, packet, strlen(packet));
    } else {
        trigger_local_reply(id, "general");
    }
    return PLUGIN_HANDLED;
}

public cmd_ai_reset(id) {
    if (g_socket > 0) {
        new packet[] = "RESET";
        socket_send(g_socket, packet, strlen(packet));
    }
    notify_player_and_chat(id, "^4[AI] ^1Chatter queue and fight memory reset.");
    return PLUGIN_HANDLED;
}

public cmd_ai_status(id) {
    console_print(id, "==================================================");
    console_print(id, "[AI] Plugin: LOADED (CZ AI Teammates Mod v%s)", PLUGIN_VERSION);
    console_print(id, "[AI] Brain Service: %s (127.0.0.1:27115, 2s Heartbeat)", g_brainConnected ? "CONNECTED" : "OFFLINE / DISCONNECTED");
    console_print(id, "[AI] AI Model: %s", g_apiStatus);
    console_print(id, "[AI] Requests Left Today: %d / 500", g_requestsLeft);
    console_print(id, "[AI] Chatter Queue Size: %d lines", g_queueSize);
    console_print(id, "[AI] Active Fight State: %s", g_fightState);
    console_print(id, "[AI] Chatter Speed: %s | Fight Frequency: %s", g_chatterSpeed, g_fightFreq);
    console_print(id, "[AI] Chat Style: %s", g_chatStyle);
    console_print(id, "[AI] Sound Engine: In-Game GoldSrc WAV (sound/ai_teammates/)");
    console_print(id, "==================================================");

    ai_chat_print(id, print_team_default, "^4[AI Status] ^1Brain: ^4%s ^1| Model: ^4%s ^1| Left: ^4%d/500",
        g_brainConnected ? "CONNECTED" : "OFFLINE", g_apiStatus, g_requestsLeft);
    ai_chat_print(id, print_team_default, "^4[AI Status] ^1Queue: ^4%d ^1| Fight: ^4%s ^1| Speed: ^4%s ^1| Style: ^4%s",
        g_queueSize, g_fightState, g_chatterSpeed, g_chatStyle);
    return PLUGIN_HANDLED;
}
