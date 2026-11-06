// ==============================================================================
// COUNTER-STRIKE: CONDITION ZERO - HORROR "MONSTER HUNT" MODE
// Complete Monster Rework: Half-Life Zombie, Adaptive AI, Kill Abilities & Full UI
// Plugin: monster_hunt.sma
// ==============================================================================

#include <amxmodx>
#include <amxmisc>
#include <engine>
#include <fakemeta>
#include <hamsandwich>

#define PLUGIN_NAME    "Horror Monster Hunt Rework"
#define PLUGIN_VERSION "5.0.0"
#define PLUGIN_AUTHOR  "Antigravity DeepMind Team"

#define MONSTER_CLASSNAME    "monster_horror_zombie"
#define DUMMY_CLASSNAME      "monster_t_blocker"
#define DUMMY_NAME           "[HostProxy]"
#define PROJECTILE_CLASSNAME "monster_acid_spit"

// Offsets for Counter-Strike / Condition Zero
#define OFFSET_TEAM        114
#define CS_TEAM_UNASSIGNED 0
#define CS_TEAM_T          1
#define CS_TEAM_CT         2
#define CS_TEAM_SPECTATOR  3

// Half-Life Zombie Master Model
#define MODEL_ZOMBIE    "models/zombie.mdl"

// Half-Life Zombie Native Sounds
#define SOUND_ALERT1  "zombie/zo_alert10.wav"
#define SOUND_ALERT2  "zombie/zo_alert20.wav"
#define SOUND_ALERT3  "zombie/zo_alert30.wav"
#define SOUND_ATTACK1 "zombie/zo_attack1.wav"
#define SOUND_ATTACK2 "zombie/zo_attack2.wav"
#define SOUND_IDLE1   "zombie/zo_idle1.wav"
#define SOUND_IDLE2   "zombie/zo_idle2.wav"
#define SOUND_IDLE3   "zombie/zo_idle3.wav"
#define SOUND_IDLE4   "zombie/zo_idle4.wav"
#define SOUND_PAIN1   "zombie/zo_pain1.wav"
#define SOUND_PAIN2   "zombie/zo_pain2.wav"
#define SOUND_MISS1   "zombie/claw_miss1.wav"
#define SOUND_MISS2   "zombie/claw_miss2.wav"
#define SOUND_STRIKE1 "zombie/claw_strike1.wav"
#define SOUND_STRIKE2 "zombie/claw_strike2.wav"
#define SOUND_STRIKE3 "zombie/claw_strike3.wav"

// Atmosphere & FX Sounds
#define SOUND_HEARTBEAT   "player/heartbeat1.wav"
#define SOUND_SPIT_LAUNCH "zombie/spit_launch.wav"
#define SOUND_SPIT_HIT    "zombie/spit_hit.wav"
#define SOUND_STING       "zombie/jumpscare_sting.wav"
#define SOUND_STOMP       "weapons/explode3.wav"

// Sprites
#define SPRITE_LASERBEAM   "sprites/laserbeam.spr"
#define SPRITE_BLOODSPRAY  "sprites/bloodspray.spr"
#define SPRITE_BLOOD       "sprites/blood.spr"
#define SPRITE_SHOCKWAVE   "sprites/shockwave.spr"
#define SPRITE_SPIT        "sprites/bigspit.spr"
#define SPRITE_EXPLODE     "sprites/zerogxplode.spr"

// Tasks
#define TASK_ROUND_START   1001
#define TASK_COUNTDOWN     1002
#define TASK_AI_TICK       1003
#define TASK_MONSTER_MOVE  1008

new g_debugTracesThisSec = 0;
new g_debugTracesLastSec = 0;
new Float:g_lastTraceResetTime = 0.0;
new bool:g_modePendingChange = false;
new Float:g_monsterGoalPos[3];
new Float:g_monsterMoveSpeed = 0.0;
#define TASK_HEARTBEAT     1004
#define TASK_HEALTHBAR     1005
#define TASK_BOT_REACT     1006
#define TASK_SENSE_TICK    1007
#define TASK_DUMMY_MAINT   1008
#define TASK_DANGER_HUD    1009
#define TASK_HEAT_DECAY    1010
#define TASK_CAMP_TRACK    1011

// State Machine
enum MonsterState {
    STATE_NONE = 0,
    STATE_PATROL,
    STATE_STALK,
    STATE_INVESTIGATE,
    STATE_CHASE,
    STATE_ATTACK,
    STATE_STAGGER,
    STATE_RETREAT,
    STATE_LUNGE_WINDUP,
    STATE_LUNGING,
    STATE_STOMP_WINDUP,
    STATE_RANGED_WINDUP,
    STATE_DEAD
};

new const g_stateNames[][] = {
    "NONE",
    "PATROL",
    "STALK",
    "INVESTIGATE",
    "CHASE",
    "ATTACK",
    "STAGGER",
    "RETREAT",
    "LUNGE_WINDUP",
    "LUNGING",
    "STOMP_WINDUP",
    "RANGED_WINDUP",
    "DEAD"
};

// Attack Ability Types
enum AttackType {
    ATTACK_MELEE = 0,
    ATTACK_COMBO,
    ATTACK_LUNGE,
    ATTACK_STOMP,
    ATTACK_SPIT,
    ATTACK_JUMPSCARE
};

new const g_attackNames[][] = {
    "Basic Claw",
    "Combo Finisher",
    "Apex Lunge",
    "Ground Stomp",
    "Acid Spit",
    "Jumpscare Ambush"
};

// Teammate Bot Brain States
enum BotBrainState {
    BOT_STATE_NONE = 0,
    BOT_STATE_SEARCH,
    BOT_STATE_ENGAGE,
    BOT_STATE_KITE,
    BOT_STATE_PANIC
};

// CVars - Core & Difficulty
new g_cvarEnabled;
new g_cvarGameMode;           // 0=Survivors vs Monster (Co-op), 1=Both Teams vs Monster
new g_cvarDifficulty;
new g_cvarTraceBudget;
new g_cvarTint;         // 0=Easy, 1=Normal, 2=Nightmare, 3=Custom
new g_cvarHealth;
new g_cvarSpeedWalk;
new g_cvarSpeedRun;
new g_cvarSpeedMult;
new g_cvarDamageMult;
new g_cvarCooldownMult;
new g_cvarDmgReduction;       // Distance/single-attacker reduction (default 0.20)

// CVars - Tracking & Senses
new g_cvarTargetMode;         // 0=Nearest, 1=Weakest, 2=Random, 3=Lone
new g_cvarPreferBots;
new g_cvarTrackingMode;       // 0=Fair, 1=Relentless, 2=Adaptive
new g_cvarSightRange;
new g_cvarHearRange;
new g_cvarSense;
new g_cvarSenseInterval;

// CVars - Kill Abilities
new g_cvarAbilityCombo;
new g_cvarComboDamage;
new g_cvarComboCooldown;
new g_cvarAbilityLunge;
new g_cvarLungeDamage;
new g_cvarLungeRangeMin;
new g_cvarLungeRangeMax;
new g_cvarLungeCooldown;
new g_cvarAbilityStomp;
new g_cvarStompDamage;
new g_cvarStompRadius;
new g_cvarStompCooldown;
new g_cvarAbilityRanged;
new g_cvarRangedDamage;
new g_cvarRangedCooldown;
new g_cvarJumpscare;
new g_cvarFlashSafe;
new g_cvarJumpscareCooldown;

// CVars - UI & Presentation
new g_cvarHealthBar;
new g_cvarHealthBarAlways;
new g_cvarDangerHud;
new g_cvarRoundSummary;

// CVars - Bot AI
new g_cvarBotReact;
new g_cvarBotAI;
new g_cvarBotCourageMin;
new g_cvarBotCourageMax;
new g_cvarBotEngageDist;
new g_cvarBotDangerDist;
new g_cvarBotAimError;
new g_cvarBotCommitTime;
new g_cvarBotCallouts;

// CVars - Gore & Blood
new g_cvarBlood;
new g_cvarBloodAmount;
new g_cvarBloodColor;

// CVars - Atmosphere & Telemetry
new g_cvarAtmosphere;
new g_cvarHeartbeat;
new g_cvarScreenShake;
new g_cvarFlicker;
new g_cvarPulse;
new g_cvarDebug;

// Monster Runtime State
new g_monsterEnt = 0;
new MonsterState:g_monsterState = STATE_NONE;
new g_currentTarget = 0;
new Float:g_lastKnownPos[3];
new Float:g_lastKnownDir[3];
new Float:g_investigatePos[3];
new Float:g_sensePos[3];
new Float:g_staggerEndTime = 0.0;
new Float:g_offGroundDuration = 0.0;

stock stop_all_monster_sounds() {
    new max_clients = get_maxplayers();
    for (new i = 1; i <= max_clients; i++) {
        if (!is_user_connected(i)) continue;
        emit_sound(i, CHAN_STATIC, SOUND_HEARTBEAT, 0.0, 0.0, SND_STOP, PITCH_NORM);
        client_cmd(i, "stopsound");
    }
    if (g_monsterEnt > 0 && is_valid_ent(g_monsterEnt)) {
        emit_sound(g_monsterEnt, CHAN_VOICE,  SOUND_ALERT1,     0.0, 0.0, SND_STOP, PITCH_NORM);
        emit_sound(g_monsterEnt, CHAN_VOICE,  SOUND_ALERT2,     0.0, 0.0, SND_STOP, PITCH_NORM);
        emit_sound(g_monsterEnt, CHAN_VOICE,  SOUND_ALERT3,     0.0, 0.0, SND_STOP, PITCH_NORM);
        emit_sound(g_monsterEnt, CHAN_VOICE,  SOUND_IDLE1,      0.0, 0.0, SND_STOP, PITCH_NORM);
        emit_sound(g_monsterEnt, CHAN_WEAPON, SOUND_ATTACK1,    0.0, 0.0, SND_STOP, PITCH_NORM);
        emit_sound(g_monsterEnt, CHAN_WEAPON, SOUND_ATTACK2,    0.0, 0.0, SND_STOP, PITCH_NORM);
        emit_sound(g_monsterEnt, CHAN_BODY,   SOUND_PAIN1,      0.0, 0.0, SND_STOP, PITCH_NORM);
        emit_sound(g_monsterEnt, CHAN_ITEM,   SOUND_STOMP,      0.0, 0.0, SND_STOP, PITCH_NORM);
        emit_sound(g_monsterEnt, CHAN_STATIC, SOUND_SPIT_LAUNCH, 0.0, 0.0, SND_STOP, PITCH_NORM);
        emit_sound(g_monsterEnt, CHAN_AUTO,   SOUND_STING,      0.0, 0.0, SND_STOP, PITCH_NORM);
    }
}

stock Float:approach_angle(Float:target, Float:current, Float:speed) {
    new Float:diff = target - current;
    while (diff < -180.0) diff += 360.0;
    while (diff > 180.0) diff -= 360.0;
    if (diff > speed) return current + speed;
    if (diff < -speed) return current - speed;
    return target;
}


// Health Phases & Combat Memory
new g_currentPhase = 1;                     // 1 = 100-66%, 2 = 66-33%, 3 = <33%
new Float:g_lastDamageTakenTime = 0.0;
new Float:g_recentAttackerTime[33];

// Kill Abilities Cooldowns & State
new AttackType:g_lastAttackUsed = ATTACK_MELEE;
new g_comboStep = 0;
new Float:g_lastComboHitTime = 0.0;
new Float:g_abilityCooldownLunge = 0.0;
new Float:g_abilityCooldownStomp = 0.0;
new Float:g_abilityCooldownRanged = 0.0;
new Float:g_lungeWindupEndTime = 0.0;
new Float:g_lungeEndTime = 0.0;
new Float:g_lungeTargetDir[3];
new Float:g_stompWindupEndTime = 0.0;
new Float:g_rangedWindupEndTime = 0.0;
new Float:g_targetUnreachableDuration = 0.0;
new Float:g_lastJumpscareTime[33];

// Stuck Detection & Recovery

// Dynamic Bot Courage & Brain State
new g_botCourage[33];
new BotBrainState:g_botState[33];
new Float:g_botCommitTime[33];
new Float:g_botSearchTarget[33][3];
new Float:g_botNextSearchPick[33];
new Float:g_botLastBurstTime[33];
new g_botBurstShots[33];

// Shared Knowledge (Callouts)
new Float:g_sharedMonsterPos[3];
new Float:g_sharedMonsterTime = 0.0;
new Float:g_lastCalloutTime = 0.0;

// Round Statistics & Performance Tracking
new Float:g_roundMonsterMaxHP = 6000.0;
new Float:g_playerRoundDamage[33];
new Float:g_playerSpawnTime[33];
new Float:g_playerDeathTime[33];
new g_killsByAttack[AttackType];
new g_playersDevoured = 0;
new g_botsDevoured = 0;
new g_topDamagePlayer = 0;

// Team Management
new g_savedLimitTeams = 2;
new g_savedAutoTeamBalance = 1;
new g_dummyTBot = 0;
new bool:g_hasReGameDLLRoundInfinite = false;
new g_countdownSeconds = 3;

// Sprite & Decal Indices
new g_laserBeamIndex = 0;
new g_sprBloodSpray = 0;
new g_sprBlood = 0;
new g_sprShockwave = 0;
new g_sprSpit = 0;
new g_sprExplode = 0;
new g_decalBlood[8];
new g_decalYellowBlood[6];

// =========================================================================
// WAYPOINT GRAPH, HEAT MAP, HIDING SPOTS & FLANKING PATHS
// =========================================================================
#define MAX_WAYPOINTS 128
#define MAX_WP_NEIGHBORS 8
#define MAX_PATH_NODES 32

new Float:g_wpOrigin[MAX_WAYPOINTS][3];
new g_wpNeighbors[MAX_WAYPOINTS][MAX_WP_NEIGHBORS];
new g_wpNeighborCount[MAX_WAYPOINTS];
new g_totalWaypoints = 0;
new g_totalEdges = 0;

// Heat Map & Hiding Spots
new Float:g_wpHeat[MAX_WAYPOINTS];
new bool:g_wpIsCampSpot[MAX_WAYPOINTS];
new Float:g_wpLastCampTime[MAX_WAYPOINTS];
new Float:g_playerLastPos[33][3];
new Float:g_playerStationaryDuration[33];

// Path Execution
new g_currentPath[MAX_PATH_NODES];
new g_pathLength = 0;
new g_pathIndex = 0;
new Float:g_lastPathCalcTime = 0.0;
new g_currentPatrolGoal = -1;
new g_flankCounter = 0;

// Functions implemented below

// =========================================================================
// DIFFICULTY PRESET & STATS ENGINE (Step 2)
// =========================================================================

stock Float:get_difficulty_health() {
    new diff = get_pcvar_num(g_cvarDifficulty);
    switch (diff) {
        case 0: return 3000.0;     // Easy
        case 1: return 6000.0;     // Normal
        case 2: return 12000.0;    // Nightmare
        case 3: return get_pcvar_float(g_cvarHealth); // Custom
    }
    return 6000.0;
}

stock Float:get_difficulty_speed_mult() {
    new diff = get_pcvar_num(g_cvarDifficulty);
    new Float:mult = 1.0;
    switch (diff) {
        case 0: mult = 0.85;
        case 1: mult = 1.00;
        case 2: mult = 1.15;
        case 3: mult = get_pcvar_float(g_cvarSpeedMult);
    }
    // Health phase speed scaling
    if (g_currentPhase == 2) mult *= 1.15;
    else if (g_currentPhase == 3) mult *= 1.30;
    return mult;
}

stock Float:get_difficulty_damage_mult() {
    new diff = get_pcvar_num(g_cvarDifficulty);
    switch (diff) {
        case 0: return 0.80;
        case 1: return 1.00;
        case 2: return 1.30;
        case 3: return get_pcvar_float(g_cvarDamageMult);
    }
    return 1.00;
}

stock Float:get_difficulty_cooldown_mult() {
    new diff = get_pcvar_num(g_cvarDifficulty);
    new Float:mult = 1.0;
    switch (diff) {
        case 0: mult = 1.30;
        case 1: mult = 1.00;
        case 2: mult = 0.80;
        case 3: mult = get_pcvar_float(g_cvarCooldownMult);
    }
    // Enraged phases attack faster
    if (g_currentPhase == 2) mult *= 0.85;
    else if (g_currentPhase == 3) mult *= 0.70;
    return mult;
}

stock apply_difficulty_settings() {
    new diff = get_pcvar_num(g_cvarDifficulty);
    if (diff == 0) {
        set_pcvar_float(g_cvarHealth, 3000.0);
        set_pcvar_float(g_cvarSpeedMult, 0.85);
        set_pcvar_float(g_cvarDamageMult, 0.80);
        set_pcvar_float(g_cvarCooldownMult, 1.30);
    } else if (diff == 1) {
        set_pcvar_float(g_cvarHealth, 6000.0);
        set_pcvar_float(g_cvarSpeedMult, 1.00);
        set_pcvar_float(g_cvarDamageMult, 1.00);
        set_pcvar_float(g_cvarCooldownMult, 1.00);
    } else if (diff == 2) {
        set_pcvar_float(g_cvarHealth, 12000.0);
        set_pcvar_float(g_cvarSpeedMult, 1.15);
        set_pcvar_float(g_cvarDamageMult, 1.30);
        set_pcvar_float(g_cvarCooldownMult, 0.80);
    }
}

// =========================================================================
// PLUGIN PRECACHE & INIT
// =========================================================================

public plugin_precache() {
    // Precache unified standalone zombie model (all sequence groups & textures merged).
    precache_model(MODEL_ZOMBIE);
    precache_model("models/zombiet.mdl");

    precache_sound(SOUND_ALERT1);
    precache_sound(SOUND_ALERT2);
    precache_sound(SOUND_ALERT3);
    precache_sound(SOUND_ATTACK1);
    precache_sound(SOUND_ATTACK2);
    precache_sound(SOUND_IDLE1);
    precache_sound(SOUND_IDLE2);
    precache_sound(SOUND_IDLE3);
    precache_sound(SOUND_IDLE4);
    precache_sound(SOUND_PAIN1);
    precache_sound(SOUND_PAIN2);
    precache_sound(SOUND_MISS1);
    precache_sound(SOUND_MISS2);
    precache_sound(SOUND_STRIKE1);
    precache_sound(SOUND_STRIKE2);
    precache_sound(SOUND_STRIKE3);

    precache_sound(SOUND_HEARTBEAT);
    precache_sound(SOUND_SPIT_LAUNCH);
    precache_sound(SOUND_SPIT_HIT);
    precache_sound(SOUND_STING);
    precache_sound(SOUND_STOMP);

    g_laserBeamIndex  = precache_model(SPRITE_LASERBEAM);
    g_sprBloodSpray   = precache_model(SPRITE_BLOODSPRAY);
    g_sprBlood        = precache_model(SPRITE_BLOOD);
    g_sprShockwave    = precache_model(SPRITE_SHOCKWAVE);
    g_sprSpit         = precache_model(SPRITE_SPIT);
    g_sprExplode      = precache_model(SPRITE_EXPLODE);

    g_decalBlood[0] = get_decal_index("{blood1");
    g_decalBlood[1] = get_decal_index("{blood2");
    g_decalBlood[2] = get_decal_index("{blood3");
    g_decalBlood[3] = get_decal_index("{blood4");
    g_decalBlood[4] = get_decal_index("{blood5");
    g_decalBlood[5] = get_decal_index("{blood6");
    g_decalBlood[6] = get_decal_index("{blood7");
    g_decalBlood[7] = get_decal_index("{blood8");

    g_decalYellowBlood[0] = get_decal_index("{yblood1");
    g_decalYellowBlood[1] = get_decal_index("{yblood2");
    g_decalYellowBlood[2] = get_decal_index("{yblood3");
    g_decalYellowBlood[3] = get_decal_index("{yblood4");
    g_decalYellowBlood[4] = get_decal_index("{yblood5");
    g_decalYellowBlood[5] = get_decal_index("{yblood6");
}

public plugin_init() {
    register_plugin(PLUGIN_NAME, PLUGIN_VERSION, PLUGIN_AUTHOR);

    // CVars - Core & Presets
    g_cvarEnabled          = register_cvar("mh_enabled", "0");
    g_cvarTraceBudget      = register_cvar("mh_trace_budget", "30");
    g_cvarTint             = register_cvar("mh_tint", "0");
    g_cvarGameMode         = register_cvar("mh_gamemode", "0"); // 0=Survivors vs Monster, 1=Both Teams vs Monster
    g_cvarDifficulty       = register_cvar("mh_difficulty", "1"); // 0=Easy, 1=Normal, 2=Nightmare, 3=Custom
    g_cvarHealth           = register_cvar("mh_monster_health", "6000.0");
    g_cvarSpeedWalk        = register_cvar("mh_monster_speed_walk", "135.0");
    g_cvarSpeedRun         = register_cvar("mh_monster_speed_run", "235.0");
    g_cvarSpeedMult        = register_cvar("mh_speed_mult", "1.0");
    g_cvarDamageMult       = register_cvar("mh_damage_mult", "1.0");
    g_cvarCooldownMult     = register_cvar("mh_cooldown_mult", "1.0");
    g_cvarDmgReduction     = register_cvar("mh_dmg_reduction", "0.20");

    // CVars - Senses & Tracking
    g_cvarTargetMode       = register_cvar("mh_target_mode", "0");
    g_cvarPreferBots       = register_cvar("mh_prefer_bots", "0");
    g_cvarTrackingMode     = register_cvar("mh_tracking_mode", "2"); // 0=Fair, 1=Relentless, 2=Adaptive
    g_cvarSightRange       = register_cvar("mh_sight_range", "1500.0");
    g_cvarHearRange        = register_cvar("mh_hear_range", "1200.0");
    g_cvarSense            = register_cvar("mh_sense", "1");
    g_cvarSenseInterval    = register_cvar("mh_sense_interval", "8.0");

    // CVars - Kill Abilities
    g_cvarAbilityCombo     = register_cvar("mh_ability_combo", "1");
    g_cvarComboDamage      = register_cvar("mh_combo_damage", "38.0");
    g_cvarComboCooldown    = register_cvar("mh_combo_cooldown", "2.0");
    g_cvarAbilityLunge     = register_cvar("mh_ability_lunge", "1");
    g_cvarLungeDamage      = register_cvar("mh_lunge_damage", "55.0");
    g_cvarLungeRangeMin    = register_cvar("mh_lunge_range_min", "350.0");
    g_cvarLungeRangeMax    = register_cvar("mh_lunge_range_max", "800.0");
    g_cvarLungeCooldown    = register_cvar("mh_lunge_cooldown", "8.0");
    g_cvarAbilityStomp     = register_cvar("mh_ability_stomp", "1");
    g_cvarStompDamage      = register_cvar("mh_stomp_damage", "28.0");
    g_cvarStompRadius      = register_cvar("mh_stomp_radius", "350.0");
    g_cvarStompCooldown    = register_cvar("mh_stomp_cooldown", "12.0");
    g_cvarAbilityRanged    = register_cvar("mh_ability_ranged", "1");
    g_cvarRangedDamage     = register_cvar("mh_ranged_damage", "35.0");
    g_cvarRangedCooldown   = register_cvar("mh_ranged_cooldown", "10.0");
    g_cvarJumpscare        = register_cvar("mh_jumpscare", "1");
    g_cvarFlashSafe        = register_cvar("mh_flash_safe", "0");
    g_cvarJumpscareCooldown= register_cvar("mh_jumpscare_cooldown", "30.0");

    // CVars - UI & Presentation
    g_cvarHealthBar        = register_cvar("mh_healthbar", "1");
    g_cvarHealthBarAlways  = register_cvar("mh_healthbar_always", "0");
    g_cvarDangerHud        = register_cvar("mh_danger_hud", "1");
    g_cvarRoundSummary     = register_cvar("mh_round_summary", "1");

    // CVars - Bot AI
    g_cvarBotReact         = register_cvar("mh_bot_react", "1");
    g_cvarBotAI            = register_cvar("mh_bot_ai", "1");
    g_cvarBotCourageMin    = register_cvar("mh_bot_courage_min", "30");
    g_cvarBotCourageMax    = register_cvar("mh_bot_courage_max", "85");
    g_cvarBotEngageDist    = register_cvar("mh_bot_engage_dist", "850.0");
    g_cvarBotDangerDist    = register_cvar("mh_bot_danger_dist", "420.0");
    g_cvarBotAimError      = register_cvar("mh_bot_aim_error", "2.5");
    g_cvarBotCommitTime    = register_cvar("mh_bot_commit_time", "8.0");
    g_cvarBotCallouts      = register_cvar("mh_bot_callouts", "1");

    // CVars - Gore
    g_cvarBlood            = register_cvar("mh_blood", "1");
    g_cvarBloodAmount      = register_cvar("mh_blood_amount", "1");
    g_cvarBloodColor       = register_cvar("mh_blood_color", "0");

    // CVars - Atmosphere & Telemetry
    g_cvarAtmosphere       = register_cvar("mh_atmosphere", "1");
    g_cvarHeartbeat        = register_cvar("mh_heartbeat", "1");
    g_cvarScreenShake      = register_cvar("mh_screenshake", "1");
    g_cvarFlicker          = register_cvar("mh_flicker", "1");
    g_cvarPulse            = register_cvar("mh_pulse", "1");
    g_cvarDebug            = register_cvar("mh_debug", "0");

    // Commands & Menus
    register_clcmd("say /horror", "cmd_menu");
    register_clcmd("say /mh_modeltest", "cmd_modeltest");
    register_clcmd("mh_modeltest", "cmd_modeltest");
    register_clcmd("say_team /horror", "cmd_menu");
    register_clcmd("mh_menu", "cmd_menu");
    register_concmd("mh_spawn", "cmd_spawn_console", ADMIN_BAN, "Spawn the zombie in front of the caller");
    register_concmd("mh_kill", "cmd_kill_monster", ADMIN_BAN, "Kill active zombie");

    // Team Enforcement
    register_clcmd("jointeam", "cmd_jointeam");
    register_clcmd("chooseteam", "cmd_chooseteam");
    register_menucmd(register_menuid("Team_Select", 1), 1023, "menu_team_select");

    // Events
    register_event("HLTV", "event_new_round", "a", "1=0", "2=0");
    register_event("RoundTime", "event_round_start", "bc");
    register_logevent("logevent_round_start", 2, "1=Round_Start");
    register_logevent("logevent_round_end", 2, "1=Round_End");

    // Hooks
    RegisterHam(Ham_Spawn, "player", "fw_player_spawn_post", 1);
    register_forward(FM_PlaybackEvent, "fw_playback_event");
    register_forward(FM_CmdStart, "fw_cmd_start");

    RegisterHam(Ham_TakeDamage, "info_target", "fw_monster_takedamage", 0);
    RegisterHam(Ham_Killed, "info_target", "fw_monster_killed", 1);
    RegisterHam(Ham_TraceAttack, "info_target", "fw_monster_traceattack", 0);
    RegisterHam(Ham_TakeDamage, "player", "fw_player_takedamage", 0);

    register_touch(PROJECTILE_CLASSNAME, "*", "fw_spit_touch");

    g_hasReGameDLLRoundInfinite = (cvar_exists("mp_round_infinite") != 0);
    g_savedLimitTeams = get_cvar_num("mp_limitteams");
    g_savedAutoTeamBalance = get_cvar_num("mp_autoteambalance");

    new config_path[128];
    get_configsdir(config_path, charsmax(config_path));
    server_cmd("exec %s/monster_hunt.cfg", config_path);
    set_task(2.0, "task_build_waypoints");
}

public plugin_cfg() {
    set_pcvar_num(g_cvarEnabled, 0);
    g_modePendingChange = false;
    restore_team_rules_mode_off();
}

public plugin_end() {
    stop_all_monster_sounds();
    remove_monster_entity();
}

public client_disconnected(id) {
    g_playerRoundDamage[id] = 0.0;
    emit_sound(id, CHAN_STATIC, SOUND_HEARTBEAT, 0.0, 0.0, SND_STOP, PITCH_NORM);
    client_cmd(id, "stopsound");
}

// =========================================================================
// TEAM ENFORCEMENT & DUMMY T BOT (Steps 2 & 4)
// =========================================================================

public fw_player_spawn_post(id) {
    if (!is_user_connected(id)) return;
    if (g_dummyTBot > 0 && id == g_dummyTBot) {
        set_pev(id, pev_flags, pev(id, pev_flags) | FL_FROZEN);
        set_pev(id, pev_effects, pev(id, pev_effects) | EF_NODRAW);
        set_pev(id, pev_solid, SOLID_NOT);
        set_pev(id, pev_takedamage, DAMAGE_NO);
        set_pev(id, pev_origin, Float:{-9999.0, -9999.0, -9999.0});
        return;
    }

    // In Solo/Co-op Survivors mode (Mode 0), ensure all spawning players/bots join Survivors (CT)
    if (get_pcvar_num(g_cvarEnabled) && get_pcvar_num(g_cvarGameMode) == 0) {
        new team = get_pdata_int(id, OFFSET_TEAM);
        if (team == CS_TEAM_T) {
            if (is_user_bot(id)) {
                server_cmd("kick #%d", get_user_userid(id));
            } else {
                engclient_cmd(id, "jointeam", "2");
                engclient_cmd(id, "joinclass", "1");
                set_pdata_int(id, OFFSET_TEAM, CS_TEAM_CT);
                new ct_spawn = find_ent_by_class(-1, "info_player_start");
                if (ct_spawn > 0) {
                    new Float:sp_pos[3];
                    entity_get_vector(ct_spawn, EV_VEC_origin, sp_pos);
                    entity_set_vector(id, EV_VEC_origin, sp_pos);
                }
            }
        }
    }
}

stock apply_team_rules_mode_on() {
    set_cvar_num("mp_limitteams", 0);
    set_cvar_num("mp_autoteambalance", 0);
    if (get_pcvar_num(g_cvarGameMode) == 0) {
        set_cvar_string("bot_join_team", "ct");
        set_cvar_num("bot_defer_to_human", 1);
        maintain_dummy_t_bot();
        server_cmd("bot_kick t");
        force_all_survivors_to_ct();
    } else {
        set_cvar_string("bot_join_team", "any");
        remove_dummy_t_bot();
    }
    if (g_hasReGameDLLRoundInfinite) {
        set_cvar_num("mp_round_infinite", 1);
    }
}

stock restore_team_rules_mode_off() {
    set_cvar_num("mp_limitteams", g_savedLimitTeams);
    set_cvar_num("mp_autoteambalance", g_savedAutoTeamBalance);
    set_cvar_string("bot_join_team", "any");
    if (g_hasReGameDLLRoundInfinite) {
        set_cvar_num("mp_round_infinite", 0);
    }
    remove_dummy_t_bot();
}

stock maintain_dummy_t_bot() {
    if (get_pcvar_num(g_cvarGameMode) != 0) return;
    if (get_playersnum() == 0 || !is_user_connected(1)) return;
    if (g_dummyTBot > 0 && is_user_connected(g_dummyTBot)) return;
    new bot = engfunc(EngFunc_CreateFakeClient, DUMMY_NAME);
    if (bot > 0) {
        g_dummyTBot = bot;
        dllfunc(DLLFunc_ClientConnect, bot, DUMMY_NAME, "127.0.0.1");
        dllfunc(DLLFunc_ClientPutInServer, bot);
        set_pdata_int(bot, OFFSET_TEAM, CS_TEAM_T);
        set_pev(bot, pev_flags, pev(bot, pev_flags) | FL_FROZEN);
        set_pev(bot, pev_effects, pev(bot, pev_effects) | EF_NODRAW);
        set_pev(bot, pev_solid, SOLID_NOT);
        set_pev(bot, pev_takedamage, DAMAGE_NO);
        set_pev(bot, pev_origin, Float:{-9999.0, -9999.0, -9999.0});
    }
}

stock remove_dummy_t_bot() {
    if (g_dummyTBot > 0 && is_user_connected(g_dummyTBot)) {
        server_cmd("kick #%d", get_user_userid(g_dummyTBot));
        g_dummyTBot = 0;
    }
}

stock force_all_survivors_to_ct() {
    if (get_pcvar_num(g_cvarGameMode) != 0) return; // Only force CT in Survivors vs Monster mode

    new ct_spawn = find_ent_by_class(-1, "info_player_start");
    new Float:sp_pos[3];
    if (ct_spawn > 0) entity_get_vector(ct_spawn, EV_VEC_origin, sp_pos);

    new players[32], count;
    get_players(players, count);
    for (new i = 0; i < count; i++) {
        new id = players[i];
        if (id == g_dummyTBot) continue;
        new team = get_pdata_int(id, OFFSET_TEAM);
        if (team == CS_TEAM_T) {
            if (is_user_bot(id)) {
                server_cmd("kick #%d", get_user_userid(id));
            } else {
                engclient_cmd(id, "jointeam", "2");
                engclient_cmd(id, "joinclass", "1");
                set_pdata_int(id, OFFSET_TEAM, CS_TEAM_CT);
                if (is_user_alive(id) && ct_spawn > 0) {
                    entity_set_vector(id, EV_VEC_origin, sp_pos);
                }
            }
        }
    }
}

public cmd_jointeam(id) {
    if (!get_pcvar_num(g_cvarEnabled)) return PLUGIN_CONTINUE;
    new arg[8]; read_argv(1, arg, charsmax(arg));
    if (equal(arg, "1")) {
        client_print_color(id, print_team_blue, "^4[Horror] ^1Terrorist team is locked. Joining ^3Survivors (CT)^1!");
        engclient_cmd(id, "jointeam", "2");
        return PLUGIN_HANDLED;
    }
    return PLUGIN_CONTINUE;
}

public cmd_chooseteam(id) {
    if (!get_pcvar_num(g_cvarEnabled)) return PLUGIN_CONTINUE;
    engclient_cmd(id, "jointeam", "2");
    return PLUGIN_HANDLED;
}

public menu_team_select(id, key) {
    if (!get_pcvar_num(g_cvarEnabled)) return PLUGIN_CONTINUE;
    if (key == 0) {
        engclient_cmd(id, "jointeam", "2");
        return PLUGIN_HANDLED;
    }
    return PLUGIN_CONTINUE;
}

// =========================================================================
// ROUND LIFECYCLE & ROUND SUMMARY (Step 5)
// =========================================================================

public event_new_round() {
    remove_monster_entity();
    g_monsterState = STATE_NONE;
    g_pathLength = 0;
    g_currentPhase = 1;
    g_lastDamageTakenTime = get_gametime();
    g_topDamagePlayer = 0;
    g_playersDevoured = 0;
    g_botsDevoured = 0;

    for (new i = 0; i < 6; i++) g_killsByAttack[AttackType:i] = 0;
    for (new i = 1; i <= 32; i++) {
        g_playerRoundDamage[i] = 0.0;
        g_playerSpawnTime[i] = get_gametime();
        g_playerDeathTime[i] = 0.0;
        g_lastJumpscareTime[i] = 0.0;
        g_recentAttackerTime[i] = 0.0;
    }

    if (!get_pcvar_num(g_cvarEnabled)) {
        engfunc(EngFunc_LightStyle, 0, "m");
        return;
    }

    apply_team_rules_mode_on();
    apply_difficulty_settings();

    // Roll dynamic bot courage
    new min_c = get_pcvar_num(g_cvarBotCourageMin);
    new max_c = get_pcvar_num(g_cvarBotCourageMax);
    for (new i = 1; i <= 32; i++) {
        g_botCourage[i] = random_num(min_c, max_c);
    }

    if (get_pcvar_num(g_cvarAtmosphere)) {
        engfunc(EngFunc_LightStyle, 0, "b");
    }
}

public task_build_waypoints() { build_waypoint_graph(); }

public event_round_start() {
    if (g_modePendingChange) {
        g_modePendingChange = false;
        set_pcvar_num(g_cvarEnabled, 1);
        apply_team_rules_mode_on();
        client_print_color(0, print_team_red, "^4[Horror] ^1Monster Hunt mode is now ^3ACTIVE^1 for this round!");
    }

    if (g_totalWaypoints == 0) build_waypoint_graph();
    if (!get_pcvar_num(g_cvarEnabled)) {
        restore_team_rules_mode_off();
        return;
    }
    if (g_monsterEnt > 0 && is_valid_ent(g_monsterEnt)) return;
    if (task_exists(TASK_COUNTDOWN)) return;

    g_countdownSeconds = 3;
    set_task(1.0, "task_countdown_tick", TASK_COUNTDOWN, _, _, "b");
    client_print_color(0, print_team_red, "^4[Horror] ^1ANCIENT EVIL AWAKENING... Zombie enters the arena in ^33 seconds^1!");
}

public logevent_round_start() {
    event_round_start();
}

public logevent_round_end() {
    stop_all_monster_sounds();
    remove_task(TASK_MONSTER_MOVE);
    remove_task(TASK_COUNTDOWN);
    remove_task(TASK_AI_TICK);
    remove_task(TASK_HEALTHBAR);
    remove_task(TASK_BOT_REACT);
    remove_task(TASK_SENSE_TICK);
    remove_task(TASK_DANGER_HUD);
    remove_task(TASK_HEAT_DECAY);
    remove_task(TASK_CAMP_TRACK);

    if (!get_pcvar_num(g_cvarEnabled) || !get_pcvar_num(g_cvarRoundSummary)) return;

    // Compute Round Summary
    new Float:max_dmg = 0.0;
    new best_player = 0;
    for (new i = 1; i <= 32; i++) {
        if (g_playerRoundDamage[i] > max_dmg) {
            max_dmg = g_playerRoundDamage[i];
            best_player = i;
        }
    }

    new most_lethal_idx = 0;
    new most_kills = -1;
    for (new i = 0; i < 6; i++) {
        if (g_killsByAttack[AttackType:i] > most_kills) {
            most_kills = g_killsByAttack[AttackType:i];
            most_lethal_idx = i;
        }
    }

    new best_name[32] = "None";
    if (best_player > 0 && is_user_connected(best_player)) {
        get_user_name(best_player, best_name, charsmax(best_name));
    }

    new Float:hp_left = 0.0;
    if (is_valid_ent(g_monsterEnt)) {
        hp_left = entity_get_float(g_monsterEnt, EV_FL_health);
        if (hp_left < 0.0) hp_left = 0.0;
    }

    client_print_color(0, print_team_blue, "^4================== [MONSTER HUNT ROUND SUMMARY] ==================");
    client_print_color(0, print_team_default, "^1Monster Health Remaining: ^3%.0f / %.0f", hp_left, g_roundMonsterMaxHP);
    client_print_color(0, print_team_default, "^1Survivors Devoured: ^3%d Players, %d Bots", g_playersDevoured, g_botsDevoured);
    client_print_color(0, print_team_default, "^1Most Lethal Attack: ^4%s ^1(^3%d kills^1)", g_attackNames[most_lethal_idx], most_kills > 0 ? most_kills : 0);
    client_print_color(0, print_team_default, "^1Top Damage Dealer: ^3%s ^1with ^4%.0f damage", best_name, max_dmg);
    client_print_color(0, print_team_blue, "^4==================================================================");

    set_hudmessage(255, 200, 50, -1.0, 0.28, 1, 0.5, 6.0, 0.1, 0.2, 4);
    show_hudmessage(0, "--- ROUND SUMMARY ---\nTop Damage: %s (%.0f dmg)\nDevoured: %d Players, %d Bots\nDeadliest Attack: %s",
        best_name, max_dmg, g_playersDevoured, g_botsDevoured, g_attackNames[most_lethal_idx]);
}

public task_countdown_tick() {
    if (!get_pcvar_num(g_cvarEnabled)) {
        remove_task(TASK_COUNTDOWN);
        return;
    }
    g_countdownSeconds--;
    if (g_countdownSeconds > 0) {
        client_print_color(0, print_team_red, "^4[Horror] ^1The Zombie awakens in ^3%d seconds^1...", g_countdownSeconds);
    } else {
        remove_task(TASK_COUNTDOWN);
        spawn_monster_at_smart_location();
    }
}

// =========================================================================
// WAYPOINT GRAPH, HEAT MAP & ADAPTIVE PATHFINDING (Step 3)
// =========================================================================

public build_waypoint_graph() {
    g_totalWaypoints = 0;
    g_totalEdges = 0;

    for (new i = 0; i < MAX_WAYPOINTS; i++) {
        g_wpNeighborCount[i] = 0;
        g_wpHeat[i] = 0.0;
        g_wpIsCampSpot[i] = false;
        g_wpLastCampTime[i] = 0.0;
    }

    sample_spawn_points("info_player_start");
    sample_spawn_points("info_player_deathmatch");
    sample_spawn_points("armoury_entity");
    sample_spawn_points("hostage_entity");
    sample_spawn_points("func_bomb_target");
    sample_spawn_points("info_bomb_target");
    sample_spawn_points("info_vip_start");

    // Add midpoints between distant waypoints to bridge corridors
    new original_total = g_totalWaypoints;
    for (new i = 0; i < original_total && g_totalWaypoints < (MAX_WAYPOINTS - 8); i++) {
        for (new j = i + 1; j < original_total && g_totalWaypoints < (MAX_WAYPOINTS - 8); j++) {
            new Float:d = get_distance_f(g_wpOrigin[i], g_wpOrigin[j]);
            if (d >= 200.0 && d <= 450.0) {
                new Float:mid[3];
                mid[0] = (g_wpOrigin[i][0] + g_wpOrigin[j][0]) * 0.5;
                mid[1] = (g_wpOrigin[i][1] + g_wpOrigin[j][1]) * 0.5;
                mid[2] = (g_wpOrigin[i][2] + g_wpOrigin[j][2]) * 0.5;
                new Float:floor_mid[3];
                if (trace_down_to_floor(mid, floor_mid)) {
                    if (point_has_standable_clearance(floor_mid)) {
                        add_waypoint_if_unique(floor_mid, 80.0);
                    }
                }
            }
        }
    }

    for (new i = 0; i < g_totalWaypoints; i++) {
        for (new j = 0; j < g_totalWaypoints; j++) {
            if (i == j) continue;
            new Float:d = get_distance_f(g_wpOrigin[i], g_wpOrigin[j]);
            if (d <= 320.0 && check_direct_walkability(g_wpOrigin[i], g_wpOrigin[j])) {
                if (g_wpNeighborCount[i] < MAX_WP_NEIGHBORS) {
                    g_wpNeighbors[i][g_wpNeighborCount[i]] = j;
                    g_wpNeighborCount[i]++;
                    g_totalEdges++;
                }
            }
        }
    }
}

stock sample_spawn_points(const classname[]) {
    new ent = -1;
    new Float:pos[3];
    while ((ent = find_ent_by_class(ent, classname)) > 0 && g_totalWaypoints < MAX_WAYPOINTS) {
        entity_get_vector(ent, EV_VEC_origin, pos);
        new Float:floor_pos[3];
        if (trace_down_to_floor(pos, floor_pos)) {
            add_waypoint_if_unique(floor_pos, 80.0);
        }
    }
}

stock bool:add_waypoint_if_unique(const Float:pos[3], Float:min_spacing) {
    if (g_totalWaypoints >= MAX_WAYPOINTS) return false;
    for (new i = 0; i < g_totalWaypoints; i++) {
        if (get_distance_f(g_wpOrigin[i], pos) < min_spacing) return false;
    }
    g_wpOrigin[g_totalWaypoints] = pos;
    g_totalWaypoints++;
    return true;
}

stock bool:trace_down_to_floor(const Float:start[3], Float:floor_out[3]) {
    new Float:end[3];
    end[0] = start[0]; end[1] = start[1]; end[2] = start[2] - 500.0;
    engfunc(EngFunc_TraceLine, start, end, IGNORE_MONSTERS, 0, 0);
    new Float:fraction;
    get_tr2(0, TR_flFraction, fraction);
    if (fraction >= 1.0) return false;

    new Float:normal[3];
    get_tr2(0, TR_vecPlaneNormal, normal);
    get_tr2(0, TR_vecEndPos, floor_out);
    return (normal[2] >= 0.70); // Standable slope (<45 degrees)
}

stock bool:point_has_standable_clearance(const Float:pos[3]) {
    new Float:start[3], Float:end[3];
    start[0] = pos[0]; start[1] = pos[1]; start[2] = pos[2] + 4.0;
    end[0]   = pos[0]; end[1]   = pos[1]; end[2]   = pos[2] + 72.0;
    engfunc(EngFunc_TraceHull, start, end, DONT_IGNORE_MONSTERS, HULL_HUMAN, 0, 0);
    new Float:fraction;
    get_tr2(0, TR_flFraction, fraction);
    new allsolid = get_tr2(0, TR_AllSolid);
    new startsolid = get_tr2(0, TR_StartSolid);
    return (fraction >= 1.0 && !allsolid && !startsolid);
}

stock bool:check_direct_walkability(const Float:from[3], const Float:to[3]) {
    new Float:start[3], Float:end[3];
    start[0] = from[0]; start[1] = from[1]; start[2] = from[2] + 16.0;
    end[0]   = to[0];   end[1]   = to[1];   end[2]   = to[2] + 16.0;
    engfunc(EngFunc_TraceHull, start, end, DONT_IGNORE_MONSTERS, HULL_HUMAN, 0, 0);
    new Float:frac;
    get_tr2(0, TR_flFraction, frac);
    return (frac >= 0.98);
}

stock find_nearest_waypoint(const Float:pos[3]) {
    if (g_totalWaypoints <= 0) return -1;
    new best = 0;
    new Float:best_d = get_distance_f(g_wpOrigin[0], pos);
    for (new i = 1; i < g_totalWaypoints; i++) {
        new Float:d = get_distance_f(g_wpOrigin[i], pos);
        if (d < best_d) { best_d = d; best = i; }
    }
    return best;
}

// =========================================================================
// HEAT MAP & HIDING SPOT MONITORING (Step 3)
// =========================================================================

public task_heat_decay() {
    if (g_totalWaypoints <= 0) return;
    for (new i = 0; i < g_totalWaypoints; i++) {
        g_wpHeat[i] *= 0.95; // 5% decay every 3 seconds
    }
}

public task_camp_tracking() {
    if (g_totalWaypoints <= 0) return;
    new players[32], count;
    get_players(players, count, "a");

    for (new i = 0; i < count; i++) {
        new id = players[i];
        if (id == g_dummyTBot) continue;

        new Float:curr_pos[3];
        entity_get_vector(id, EV_VEC_origin, curr_pos);

        new Float:moved = get_distance_f(curr_pos, g_playerLastPos[id]);
        if (moved < 48.0) {
            g_playerStationaryDuration[id] += 1.0;
            if (g_playerStationaryDuration[id] >= 5.0) {
                new wp = find_nearest_waypoint(curr_pos);
                if (wp >= 0) {
                    g_wpIsCampSpot[wp] = true;
                    g_wpLastCampTime[wp] = get_gametime();
                    g_wpHeat[wp] = floatmin(g_wpHeat[wp] + 15.0, 100.0);
                }
            }
        } else {
            g_playerStationaryDuration[id] = 0.0;
            g_playerLastPos[id] = curr_pos;
        }
    }
}

stock add_heat_at_pos(const Float:pos[3], Float:amount) {
    new wp = find_nearest_waypoint(pos);
    if (wp >= 0) {
        g_wpHeat[wp] = floatmin(g_wpHeat[wp] + amount, 100.0);
    }
}

// =========================================================================
// A* PATHFINDING WITH FLANKING (Step 3)
// =========================================================================

stock bool:calculate_astar_path(start_wp, goal_wp, bool:do_flank) {
    if (start_wp < 0 || goal_wp < 0 || start_wp >= g_totalWaypoints || goal_wp >= g_totalWaypoints) return false;
    if (start_wp == goal_wp) {
        g_currentPath[0] = goal_wp;
        g_pathLength = 1;
        g_pathIndex = 0;
        return true;
    }

    new bool:closed[MAX_WAYPOINTS];
    new bool:open[MAX_WAYPOINTS];
    new came_from[MAX_WAYPOINTS];
    new Float:g_score[MAX_WAYPOINTS];
    new Float:f_score[MAX_WAYPOINTS];

    for (new i = 0; i < g_totalWaypoints; i++) {
        closed[i] = false;
        open[i] = false;
        came_from[i] = -1;
        g_score[i] = 9999999.0;
        f_score[i] = 9999999.0;
    }

    g_score[start_wp] = 0.0;
    f_score[start_wp] = get_distance_f(g_wpOrigin[start_wp], g_wpOrigin[goal_wp]);
    open[start_wp] = true;

    for (;;) {
        new current = -1;
        new Float:lowest_f = 9999999.0;
        for (new i = 0; i < g_totalWaypoints; i++) {
            if (open[i] && f_score[i] < lowest_f) {
                lowest_f = f_score[i];
                current = i;
            }
        }

        if (current == -1) break;
        if (current == goal_wp) {
            reconstruct_path(came_from, current);
            return true;
        }

        open[current] = false;
        closed[current] = true;

        for (new n = 0; n < g_wpNeighborCount[current]; n++) {
            new neighbor = g_wpNeighbors[current][n];
            if (closed[neighbor]) continue;

            new Float:edge_cost = get_distance_f(g_wpOrigin[current], g_wpOrigin[neighbor]);

            // Flanking route penalty: penalize waypoints visible to survivors
            if (do_flank) {
                if (is_waypoint_in_survivor_los(neighbor)) {
                    edge_cost += 500.0; // Force route through backdoors/unseen areas
                }
            }

            new Float:tentative_g = g_score[current] + edge_cost;
            if (!open[neighbor]) open[neighbor] = true;
            else if (tentative_g >= g_score[neighbor]) continue;

            came_from[neighbor] = current;
            g_score[neighbor] = tentative_g;
            f_score[neighbor] = tentative_g + get_distance_f(g_wpOrigin[neighbor], g_wpOrigin[goal_wp]);
        }
    }
    return false;
}

stock bool:is_waypoint_in_survivor_los(wp) {
    new players[32], count;
    get_players(players, count, "a");
    for (new i = 0; i < count; i++) {
        new id = players[i];
        if (id == g_dummyTBot) continue;
        new Float:p_origin[3];
        entity_get_vector(id, EV_VEC_origin, p_origin);
        if (get_distance_f(p_origin, g_wpOrigin[wp]) <= 900.0) {
            if (check_line_of_sight(id, p_origin, 0, g_wpOrigin[wp])) return true;
        }
    }
    return false;
}

stock reconstruct_path(came_from[], current) {
    new temp_path[MAX_PATH_NODES];
    new count = 0;
    new curr = current;
    while (curr != -1 && count < MAX_PATH_NODES) {
        temp_path[count++] = curr;
        curr = came_from[curr];
    }
    g_pathLength = 0;
    for (new i = count - 1; i >= 0 && g_pathLength < MAX_PATH_NODES; i--) {
        g_currentPath[g_pathLength++] = temp_path[i];
    }
    g_pathIndex = (g_pathLength > 1) ? 1 : 0;
}

// =========================================================================
// ADAPTIVE TARGET SELECTION & SPAWNING (Steps 2 & 3)
// =========================================================================

stock select_best_target(const Float:m_origin[3]) {
    new players[32], count;
    get_players(players, count, "a");
    if (count <= 0) return 0;

    // Filter out dummy bot
    new valid_players[32], valid_count = 0;
    for (new i = 0; i < count; i++) {
        if (players[i] != g_dummyTBot) {
            valid_players[valid_count++] = players[i];
        }
    }
    if (valid_count <= 0) return 0;

    // 1. High-Threat Target: if top damage dealer is nearby (<900u), prioritize them
    if (g_topDamagePlayer > 0 && is_user_alive(g_topDamagePlayer)) {
        new Float:p_orig[3];
        entity_get_vector(g_topDamagePlayer, EV_VEC_origin, p_orig);
        if (get_distance_f(m_origin, p_orig) <= 900.0) {
            return g_topDamagePlayer;
        }
    }

    new target_mode = get_pcvar_num(g_cvarTargetMode);

    // 2. Pack Awareness: calculate group clustering
    if (target_mode == 3 || get_pcvar_num(g_cvarTrackingMode) == 2) {
        new Float:cluster_center[3];
        cluster_center[0] = 0.0; cluster_center[1] = 0.0; cluster_center[2] = 0.0;
        for (new i = 0; i < valid_count; i++) {
            new Float:p_pos[3];
            entity_get_vector(valid_players[i], EV_VEC_origin, p_pos);
            cluster_center[0] += p_pos[0];
            cluster_center[1] += p_pos[1];
            cluster_center[2] += p_pos[2];
        }
        cluster_center[0] /= float(valid_count);
        cluster_center[1] /= float(valid_count);
        cluster_center[2] /= float(valid_count);

        new Float:avg_dist_to_center = 0.0;
        for (new i = 0; i < valid_count; i++) {
            new Float:p_pos[3];
            entity_get_vector(valid_players[i], EV_VEC_origin, p_pos);
            avg_dist_to_center += get_distance_f(p_pos, cluster_center);
        }
        avg_dist_to_center /= float(valid_count);

        // Clustered: pick straggler (furthest from center)
        if (avg_dist_to_center < 380.0) {
            new straggler = valid_players[0];
            new Float:max_d = -1.0;
            for (new i = 0; i < valid_count; i++) {
                new Float:p_pos[3];
                entity_get_vector(valid_players[i], EV_VEC_origin, p_pos);
                new Float:d = get_distance_f(p_pos, cluster_center);
                if (d > max_d) { max_d = d; straggler = valid_players[i]; }
            }
            return straggler;
        }
    }

    // 3. Weakest Target
    if (target_mode == 1) {
        new best = valid_players[0];
        new Float:lowest_hp = 99999.0;
        for (new i = 0; i < valid_count; i++) {
            new Float:hp = entity_get_float(valid_players[i], EV_FL_health);
            if (hp < lowest_hp) { lowest_hp = hp; best = valid_players[i]; }
        }
        return best;
    }

    // 4. Default: Nearest Target
    new best = valid_players[0];
    new Float:best_dist = 999999.0;
    for (new i = 0; i < valid_count; i++) {
        new Float:p_pos[3];
        entity_get_vector(valid_players[i], EV_VEC_origin, p_pos);
        new Float:d = get_distance_f(m_origin, p_pos);
        if (d < best_dist) { best_dist = d; best = valid_players[i]; }
    }
    return best;
}

stock predict_target_route(target, Float:out_pos[3]) {
    new Float:target_pos[3], Float:target_vel[3];
    entity_get_vector(target, EV_VEC_origin, target_pos);
    entity_get_vector(target, EV_VEC_velocity, target_vel);

    out_pos[0] = target_pos[0] + (target_vel[0] * 1.2);
    out_pos[1] = target_pos[1] + (target_vel[1] * 1.2);
    out_pos[2] = target_pos[2];
}

stock spawn_monster_at_smart_location() {
    new Float:spawn_pos[3];
    new bool:found = false;

    new players[32], count;
    get_players(players, count, "a");

    if (g_totalWaypoints > 0) {
        new best_wp = -1;
        new Float:max_dist = -1.0;
        for (new i = 0; i < g_totalWaypoints; i++) {
            new Float:min_to_player = 999999.0;
            for (new p = 0; p < count; p++) {
                if (players[p] == g_dummyTBot) continue;
                new Float:p_origin[3];
                entity_get_vector(players[p], EV_VEC_origin, p_origin);
                new Float:d = get_distance_f(g_wpOrigin[i], p_origin);
                if (d < min_to_player) min_to_player = d;
            }
            if (min_to_player > max_dist) {
                max_dist = min_to_player;
                best_wp = i;
            }
        }
        if (best_wp != -1) {
            spawn_pos = g_wpOrigin[best_wp];
            found = true;
        }
    }

    if (!found) {
        new ent = find_ent_by_class(-1, "info_player_deathmatch");
        if (ent > 0) entity_get_vector(ent, EV_VEC_origin, spawn_pos);
        else { spawn_pos[0] = 0.0; spawn_pos[1] = 0.0; spawn_pos[2] = 0.0; }
    }

    if (get_pcvar_num(g_cvarGameMode) == 0) {
        force_all_survivors_to_ct();
    }

    create_monster_entity(spawn_pos);
}

stock create_monster_entity(const Float:pos[3]) {
    remove_monster_entity();

    new ent = create_entity("info_target");
    if (!is_valid_ent(ent)) return 0;

    g_monsterEnt = ent;
    g_monsterState = STATE_PATROL;
    g_currentTarget = 0;
    g_currentPhase = 1;
    g_pathLength = 0;
    g_offGroundDuration = 0.0;
    g_lastDamageTakenTime = get_gametime();

    entity_set_string(ent, EV_SZ_classname, MONSTER_CLASSNAME);
    entity_set_model(ent, MODEL_ZOMBIE);

    // Ground-Planted Collision (Origin at feet Z = 0)
    new Float:mins[3] = {-16.0, -16.0, 0.0};
    new Float:maxs[3] = {16.0, 16.0, 72.0};
    entity_set_size(ent, mins, maxs);

    entity_set_int(ent, EV_INT_solid, SOLID_SLIDEBOX);
    entity_set_int(ent, EV_INT_movetype, MOVETYPE_STEP);
    entity_set_float(ent, EV_FL_gravity, 1.0);
    entity_set_float(ent, EV_FL_takedamage, DAMAGE_AIM);
    entity_set_int(ent, EV_INT_flags, entity_get_int(ent, EV_INT_flags) | FL_MONSTER);

    // Ham Hooks
    RegisterHamFromEntity(Ham_TraceAttack, ent, "fw_monster_traceattack", 0);
    RegisterHamFromEntity(Ham_TakeDamage, ent, "fw_monster_takedamage", 0);
    RegisterHamFromEntity(Ham_Killed, ent, "fw_monster_killed", 1);

    new Float:hp = get_difficulty_health();
    g_roundMonsterMaxHP = hp;
    entity_set_float(ent, EV_FL_health, hp);
    entity_set_float(ent, EV_FL_max_health, hp);

    // Clean Default Render Settings: normal render mode, no white diffuse modulation, scale 1.0
    entity_set_int(ent, EV_INT_rendermode, kRenderNormal);
    entity_set_int(ent, EV_INT_renderfx, kRenderFxNone);
    entity_set_float(ent, EV_FL_renderamt, 0.0);
    entity_set_vector(ent, EV_VEC_rendercolor, Float:{0.0, 0.0, 0.0});

    if (get_pcvar_num(g_cvarTint) == 1) {
        entity_set_int(ent, EV_INT_renderfx, kRenderFxGlowShell);
        entity_set_vector(ent, EV_VEC_rendercolor, Float:{40.0, 10.0, 10.0});
        entity_set_float(ent, EV_FL_renderamt, 15.0);
    }

    entity_set_int(ent, EV_INT_skin, 0);
    entity_set_int(ent, EV_INT_body, 0);
    entity_set_float(ent, EV_FL_scale, 1.0);
    entity_set_int(ent, EV_INT_sequence, 0); // idle1
    entity_set_float(ent, EV_FL_frame, 0.0);
    entity_set_float(ent, EV_FL_framerate, 1.0);
    entity_set_float(ent, EV_FL_animtime, get_gametime());

    entity_set_origin(ent, pos);
    engfunc(EngFunc_DropToFloor, ent);

    
    emit_sound(ent, CHAN_VOICE, SOUND_ALERT1, 1.0, ATTN_NORM, 0, PITCH_NORM);
    shake_all_screens(18.0, 2.0);

    new diff_str[32];
    new d_num = get_pcvar_num(g_cvarDifficulty);
    if (d_num == 0) copy(diff_str, charsmax(diff_str), "Easy");
    else if (d_num == 1) copy(diff_str, charsmax(diff_str), "Normal");
    else if (d_num == 2) copy(diff_str, charsmax(diff_str), "Nightmare");
    else copy(diff_str, charsmax(diff_str), "Custom");

    client_print_color(0, print_team_red, "^4[Horror] ^3THE ZOMBIE HAS AWAKENED! ^1Difficulty: ^4%s ^1| Health: ^3%.0f HP", diff_str, hp);

    // Fast Loop: 25Hz smooth yaw interpolation + movement stepping
    remove_task(TASK_MONSTER_MOVE);
    set_task(0.04, "task_monster_move", TASK_MONSTER_MOVE, _, _, "b");

    // Slow Loop: 4Hz target decisions, abilities, path search
    remove_task(TASK_AI_TICK);
    set_task(0.25, "monster_ai_tick", TASK_AI_TICK, _, _, "b");

    remove_task(TASK_HEALTHBAR);
    set_task(0.25, "task_update_healthbar", TASK_HEALTHBAR, _, _, "b");

    remove_task(TASK_BOT_REACT);
    set_task(0.20, "task_bot_brain_think", TASK_BOT_REACT, _, _, "b");

    remove_task(TASK_DANGER_HUD);
    set_task(0.33, "task_danger_meter", TASK_DANGER_HUD, _, _, "b");

    remove_task(TASK_HEAT_DECAY);
    set_task(3.0, "task_heat_decay", TASK_HEAT_DECAY, _, _, "b");

    remove_task(TASK_CAMP_TRACK);
    set_task(1.0, "task_camp_tracking", TASK_CAMP_TRACK, _, _, "b");

    remove_task(TASK_SENSE_TICK);
    set_task(8.0, "task_monster_sense_tick", TASK_SENSE_TICK, _, _, "b");

    remove_task(TASK_HEARTBEAT);
    set_task(1.0, "task_heartbeat_loop", TASK_HEARTBEAT, _, _, "b");

    return ent;
}

stock remove_monster_entity() {
    stop_all_monster_sounds();
    remove_task(TASK_MONSTER_MOVE);
    if (g_monsterEnt > 0 && is_valid_ent(g_monsterEnt)) {
        remove_entity(g_monsterEnt);
        g_monsterEnt = 0;
    }
}

// =========================================================================
// MONSTER 100ms AI THINK LOOP & ATTACK DISPATCHER (Steps 3 & 4)
// =========================================================================

public task_monster_move() {
    new ent = g_monsterEnt;
    if (!is_valid_ent(ent) || !get_pcvar_num(g_cvarEnabled)) return;
    if (g_monsterState == STATE_NONE || g_monsterState == STATE_DEAD) return;

    new Float:now = get_gametime();
    if (now - g_lastTraceResetTime >= 1.0) {
        g_debugTracesLastSec = g_debugTracesThisSec;
        g_debugTracesThisSec = 0;
        g_lastTraceResetTime = now;
    }

    if (get_pcvar_num(g_cvarDebug) && is_user_connected(1)) {
        set_hudmessage(0, 220, 255, 0.02, 0.22, 0, 0.0, 0.2, 0.0, 0.0, 3);
        show_hudmessage(1, "[MH Debug] State: %d | Target: %d | Traces/s: %d | Speed: %.1f",
            g_monsterState, g_currentTarget, g_debugTracesLastSec, g_monsterMoveSpeed);
    }

    if (g_monsterMoveSpeed > 0.0 && (g_monsterState == STATE_PATROL || g_monsterState == STATE_CHASE || g_monsterState == STATE_INVESTIGATE)) {
        new Float:m_origin[3];
        entity_get_vector(ent, EV_VEC_origin, m_origin);
        face_and_move_direct(ent, m_origin, g_monsterGoalPos, g_monsterMoveSpeed, 0.04);
    }
}

public monster_ai_tick() {
    if (!is_valid_ent(g_monsterEnt) || g_monsterState == STATE_NONE || g_monsterState == STATE_DEAD) {
        return;
    }

    new ent = g_monsterEnt;
    new Float:gametime = get_gametime();
    new Float:m_origin[3];
    entity_get_vector(ent, EV_VEC_origin, m_origin);

    // 1. DropToFloor & Ground Check
    new flags = entity_get_int(ent, EV_INT_flags);
    if (!(flags & FL_ONGROUND)) {
        g_offGroundDuration += 0.1;
        if (g_offGroundDuration > 0.4 && g_monsterState != STATE_LUNGING) {
            engfunc(EngFunc_DropToFloor, ent);
            g_offGroundDuration = 0.0;
        }
    } else {
        g_offGroundDuration = 0.0;
    }

    // 2. Nightmare Regeneration (1% per 5s out of combat)
    if (get_pcvar_num(g_cvarDifficulty) == 2 && (gametime - g_lastDamageTakenTime >= 5.0)) {
        new Float:hp = entity_get_float(ent, EV_FL_health);
        new Float:max_hp = entity_get_float(ent, EV_FL_max_health);
        if (hp < max_hp) {
            entity_set_float(ent, EV_FL_health, floatmin(hp + (max_hp * 0.002), max_hp)); // 0.2% per 100ms = 1% per 5s
        }
    }

    // 3. Stagger / Recovery state
    if (g_monsterState == STATE_STAGGER) {
        if (gametime >= g_staggerEndTime) {
            g_monsterState = STATE_CHASE;
            set_monster_sequence(ent, 10); // walk
        }
        return;
    }

    // 4. Lunge Execution
    if (g_monsterState == STATE_LUNGE_WINDUP) {
        if (gametime >= g_lungeWindupEndTime) {
            execute_lunge_leap(ent);
        }
        return;
    }
    if (g_monsterState == STATE_LUNGING) {
        check_lunge_impact(ent, m_origin, gametime);
        return;
    }

    // 5. Stomp Windup
    if (g_monsterState == STATE_STOMP_WINDUP) {
        if (gametime >= g_stompWindupEndTime) {
            execute_ground_stomp_impact(ent, m_origin);
        }
        return;
    }

    // 6. Ranged Windup
    if (g_monsterState == STATE_RANGED_WINDUP) {
        if (gametime >= g_rangedWindupEndTime) {
            execute_ranged_spit_fire(ent, m_origin);
        }
        return;
    }

    // 7. Pick Best Prey Target
    new target = select_best_target(m_origin);
    g_currentTarget = target;

    if (target > 0 && is_user_alive(target)) {
        new Float:t_origin[3];
        entity_get_vector(target, EV_VEC_origin, t_origin);
        new Float:dist = get_distance_f(m_origin, t_origin);
        new bool:has_los = check_line_of_sight(target, t_origin, ent, m_origin);

        if (has_los) {
            g_lastKnownPos = t_origin;
            g_lastKnownDir[0] = t_origin[0] - m_origin[0];
            g_lastKnownDir[1] = t_origin[1] - m_origin[1];
            g_lastKnownDir[2] = 0.0;
        }

        // --- ATTACK DECISION ENGINE (Step 4) ---
        // Priority 1: Jumpscare if close (<150u) and target not facing monster
        if (dist <= 150.0 && get_pcvar_num(g_cvarJumpscare) && (gametime - g_lastJumpscareTime[target] >= get_pcvar_float(g_cvarJumpscareCooldown))) {
            if (!is_player_looking_at(target, t_origin, m_origin)) {
                trigger_jumpscare(ent, target, m_origin);
                return;
            }
        }

        // Priority 2: Combo Melee if close (<95u)
        if (dist <= 95.0 && get_pcvar_num(g_cvarAbilityCombo)) {
            execute_combo_melee_strike(ent, target, m_origin);
            return;
        }

        // Priority 3: Ground Stomp if >= 2 players within 350u
        if (get_pcvar_num(g_cvarAbilityStomp) && gametime >= g_abilityCooldownStomp && g_lastAttackUsed != ATTACK_STOMP) {
            if (count_players_in_radius(m_origin, get_pcvar_float(g_cvarStompRadius)) >= 2) {
                begin_ground_stomp(ent);
                return;
            }
        }

        // Priority 4: Apex Lunge if mid-range (350u to 800u) with clear LOS
        if (get_pcvar_num(g_cvarAbilityLunge) && gametime >= g_abilityCooldownLunge && g_lastAttackUsed != ATTACK_LUNGE) {
            new Float:min_r = get_pcvar_float(g_cvarLungeRangeMin);
            new Float:max_r = get_pcvar_float(g_cvarLungeRangeMax);
            if (dist >= min_r && dist <= max_r && has_los) {
                begin_lunge_charge(ent, m_origin, t_origin);
                return;
            }
        }

        // Priority 5: Ranged Acid Spit if target is out of reach or camping (>3s)
        if (dist > 350.0 && (!has_los || floatabs(t_origin[2] - m_origin[2]) > 120.0)) {
            g_targetUnreachableDuration += 0.1;
        } else {
            g_targetUnreachableDuration = 0.0;
        }

        if (get_pcvar_num(g_cvarAbilityRanged) && g_targetUnreachableDuration >= 3.0 && gametime >= g_abilityCooldownRanged && g_lastAttackUsed != ATTACK_SPIT) {
            begin_ranged_spit(ent);
            g_targetUnreachableDuration = 0.0;
            return;
        }

        // Navigation toward target with predictive route or flanking
        g_monsterState = STATE_CHASE;
        navigate_monster_towards(ent, m_origin, t_origin, target);

        if (get_pcvar_num(g_cvarDebug)) {
            render_debug_telemetry(m_origin, t_origin, dist);
        }
    } else {
        // No target: patrol hot waypoints & check hiding spots
        g_monsterState = STATE_PATROL;
        execute_patrol_behavior(ent, m_origin);
    }
}

// =========================================================================
// KILL ABILITIES IMPLEMENTATION (Step 4)
// =========================================================================

stock execute_combo_melee_strike(ent, target, const Float:m_origin[3]) {
    new Float:gametime = get_gametime();
    new Float:dmg_mult = get_difficulty_damage_mult();
    new Float:cd_mult = get_difficulty_cooldown_mult();

    if (gametime - g_lastComboHitTime > 1.8) {
        g_comboStep = 0; // Reset combo if timed out
    }

    g_comboStep++;
    g_lastComboHitTime = gametime;
    g_lastAttackUsed = ATTACK_COMBO;

    new Float:base_dmg = get_pcvar_float(g_cvarComboDamage) * dmg_mult;

    if (g_comboStep == 1) {
        // Swing 1
        set_monster_sequence(ent, 8); // attack1
        emit_sound(ent, CHAN_WEAPON, SOUND_ATTACK1, 1.0, ATTN_NORM, 0, PITCH_NORM);
        ExecuteHamB(Ham_TakeDamage, target, ent, ent, base_dmg, DMG_SLASH);
        emit_sound(target, CHAN_AUTO, SOUND_STRIKE1, 1.0, ATTN_NORM, 0, PITCH_NORM);
        shake_screen(target, 12.0, 0.8);
    } else if (g_comboStep == 2) {
        // Swing 2
        set_monster_sequence(ent, 9); // attack2
        emit_sound(ent, CHAN_WEAPON, SOUND_ATTACK2, 1.0, ATTN_NORM, 0, PITCH_NORM);
        ExecuteHamB(Ham_TakeDamage, target, ent, ent, base_dmg * 1.2, DMG_SLASH);
        emit_sound(target, CHAN_AUTO, SOUND_STRIKE2, 1.0, ATTN_NORM, 0, PITCH_NORM);
        shake_screen(target, 16.0, 1.0);
    } else {
        // Swing 3 - Combo Finisher Knockback!
        set_monster_sequence(ent, 9); // attack2
        emit_sound(ent, CHAN_WEAPON, SOUND_STRIKE3, 1.0, ATTN_NORM, 0, PITCH_NORM);
        ExecuteHamB(Ham_TakeDamage, target, ent, ent, base_dmg * 1.5, DMG_SLASH);
        shake_screen(target, 22.0, 1.5);

        // Apply massive kinetic knockback
        new Float:t_pos[3];
        entity_get_vector(target, EV_VEC_origin, t_pos);
        new Float:kb_dir[3];
        kb_dir[0] = t_pos[0] - m_origin[0];
        kb_dir[1] = t_pos[1] - m_origin[1];
        kb_dir[2] = 0.0;
        new Float:len = floatsqroot(kb_dir[0]*kb_dir[0] + kb_dir[1]*kb_dir[1]);
        if (len > 1.0) {
            kb_dir[0] /= len; kb_dir[1] /= len;
            new Float:kb_vel[3];
            kb_vel[0] = kb_dir[0] * 460.0;
            kb_vel[1] = kb_dir[1] * 460.0;
            kb_vel[2] = 220.0;
            entity_set_vector(target, EV_VEC_velocity, kb_vel);
        }

        g_killsByAttack[ATTACK_COMBO]++;
        g_comboStep = 0; // Combo completed
    }

    // Set brief recovery
    g_monsterState = STATE_ATTACK;
    g_staggerEndTime = gametime + (0.35 * cd_mult * (get_pcvar_float(g_cvarComboCooldown) / 2.0));
}

stock begin_lunge_charge(ent, const Float:m_origin[3], const Float:t_origin[3]) {
    new Float:gametime = get_gametime();
    g_monsterState = STATE_LUNGE_WINDUP;
    g_lungeWindupEndTime = gametime + 0.45; // 0.45s telegraph crouch

    set_monster_sequence(ent, 20); // pause / crouch telegraph
    emit_sound(ent, CHAN_VOICE, SOUND_ALERT3, 1.0, ATTN_NORM, 0, PITCH_NORM);
    shake_all_screens(15.0, 1.0);

    // Calculate normalized launch direction
    g_lungeTargetDir[0] = t_origin[0] - m_origin[0];
    g_lungeTargetDir[1] = t_origin[1] - m_origin[1];
    g_lungeTargetDir[2] = 0.0;
    new Float:len = floatsqroot(g_lungeTargetDir[0]*g_lungeTargetDir[0] + g_lungeTargetDir[1]*g_lungeTargetDir[1]);
    if (len > 1.0) {
        g_lungeTargetDir[0] /= len;
        g_lungeTargetDir[1] /= len;
    }
}

stock execute_lunge_leap(ent) {
    new Float:gametime = get_gametime();
    g_monsterState = STATE_LUNGING;
    g_lungeEndTime = gametime + 0.80; // Maximum airborne duration
    g_abilityCooldownLunge = gametime + (get_pcvar_float(g_cvarLungeCooldown) * get_difficulty_cooldown_mult());
    g_lastAttackUsed = ATTACK_LUNGE;

    set_monster_sequence(ent, 7); // falling / leap pose

    new Float:leap_vel[3];
    leap_vel[0] = g_lungeTargetDir[0] * 680.0;
    leap_vel[1] = g_lungeTargetDir[1] * 680.0;
    leap_vel[2] = 220.0;
    entity_set_vector(ent, EV_VEC_velocity, leap_vel);
    emit_sound(ent, CHAN_BODY, SOUND_ATTACK2, 1.0, ATTN_NORM, 0, PITCH_NORM);
}

stock check_lunge_impact(ent, const Float:m_origin[3], Float:gametime) {
    new players[32], count;
    get_players(players, count, "a");

    new hit = false;
    new Float:dmg = get_pcvar_float(g_cvarLungeDamage) * get_difficulty_damage_mult();

    for (new i = 0; i < count; i++) {
        new victim = players[i];
        if (victim == g_dummyTBot) continue;

        new Float:v_pos[3];
        entity_get_vector(victim, EV_VEC_origin, v_pos);
        if (get_distance_f(m_origin, v_pos) <= 90.0) {
            ExecuteHamB(Ham_TakeDamage, victim, ent, ent, dmg, DMG_SLASH);
            shake_screen(victim, 25.0, 1.5);
            emit_sound(victim, CHAN_AUTO, SOUND_STRIKE3, 1.0, ATTN_NORM, 0, PITCH_NORM);

            // Knock victim away
            new Float:kb[3];
            kb[0] = g_lungeTargetDir[0] * 400.0;
            kb[1] = g_lungeTargetDir[1] * 400.0;
            kb[2] = 180.0;
            entity_set_vector(victim, EV_VEC_velocity, kb);

            g_killsByAttack[ATTACK_LUNGE]++;
            hit = true;
            break;
        }
    }

    // Finished leap or timed out: enter 1.0s stagger recovery (punishable opening)
    if (hit || gametime >= g_lungeEndTime) {
        g_monsterState = STATE_STAGGER;
        g_staggerEndTime = gametime + 1.0;
        set_monster_sequence(ent, 5); // bigflinch stagger
        entity_set_vector(ent, EV_VEC_velocity, Float:{0.0, 0.0, 0.0});
    }
}

stock begin_ground_stomp(ent) {
    new Float:gametime = get_gametime();
    g_monsterState = STATE_STOMP_WINDUP;
    g_stompWindupEndTime = gametime + 0.40; // 0.40s telegraph
    set_monster_sequence(ent, 22); // stomp / heavy slam
    emit_sound(ent, CHAN_VOICE, SOUND_ALERT2, 1.0, ATTN_NORM, 0, PITCH_NORM);
}

stock execute_ground_stomp_impact(ent, const Float:m_origin[3]) {
    new Float:gametime = get_gametime();
    g_monsterState = STATE_CHASE;
    g_abilityCooldownStomp = gametime + (get_pcvar_float(g_cvarStompCooldown) * get_difficulty_cooldown_mult());
    g_lastAttackUsed = ATTACK_STOMP;

    emit_sound(ent, CHAN_BODY, SOUND_STOMP, 1.0, ATTN_NORM, 0, PITCH_NORM);
    shake_all_screens(22.0, 1.8);

    // Shockwave Cylinder Ring (TE_BEAMCYLINDER)
    message_begin(MSG_BROADCAST, SVC_TEMPENTITY);
    write_byte(TE_BEAMCYLINDER);
    write_coord(floatround(m_origin[0]));
    write_coord(floatround(m_origin[1]));
    write_coord(floatround(m_origin[2]));
    write_coord(floatround(m_origin[0]));
    write_coord(floatround(m_origin[1]));
    write_coord(floatround(m_origin[2] + 350.0));
    write_short(g_sprShockwave);
    write_byte(0); write_byte(16); write_byte(8); write_byte(35); write_byte(0);
    write_byte(255); write_byte(80); write_byte(20); write_byte(220); write_byte(0);
    message_end();

    new Float:radius = get_pcvar_float(g_cvarStompRadius);
    new Float:dmg = get_pcvar_float(g_cvarStompDamage) * get_difficulty_damage_mult();

    new players[32], count;
    get_players(players, count, "a");
    for (new i = 0; i < count; i++) {
        new id = players[i];
        if (id == g_dummyTBot) continue;

        new Float:p_orig[3];
        entity_get_vector(id, EV_VEC_origin, p_orig);
        new Float:d = get_distance_f(m_origin, p_orig);
        if (d <= radius) {
            ExecuteHamB(Ham_TakeDamage, id, ent, ent, dmg, DMG_GENERIC);
            // 2-second slow effect
            entity_set_float(id, EV_FL_maxspeed, 130.0);
            remove_task(id + 3000);
            set_task(2.0, "task_remove_slow", id + 3000);
            g_killsByAttack[ATTACK_STOMP]++;
        }
    }
}

public task_remove_slow(taskid) {
    new id = taskid - 3000;
    if (is_user_alive(id)) {
        entity_set_float(id, EV_FL_maxspeed, 250.0);
    }
}

stock begin_ranged_spit(ent) {
    new Float:gametime = get_gametime();
    g_monsterState = STATE_RANGED_WINDUP;
    g_rangedWindupEndTime = gametime + 0.50; // 0.50s windup
    set_monster_sequence(ent, 8); // attack1
    emit_sound(ent, CHAN_VOICE, SOUND_SPIT_LAUNCH, 1.0, ATTN_NORM, 0, PITCH_NORM);
}

stock execute_ranged_spit_fire(ent, const Float:m_origin[3]) {
    new Float:gametime = get_gametime();
    g_monsterState = STATE_CHASE;
    g_abilityCooldownRanged = gametime + (get_pcvar_float(g_cvarRangedCooldown) * get_difficulty_cooldown_mult());
    g_lastAttackUsed = ATTACK_SPIT;

    if (!g_currentTarget || !is_user_alive(g_currentTarget)) return;

    new Float:t_pos[3];
    entity_get_vector(g_currentTarget, EV_VEC_origin, t_pos);

    new spit = create_entity("info_target");
    if (!is_valid_ent(spit)) return;

    entity_set_string(spit, EV_SZ_classname, PROJECTILE_CLASSNAME);
    if (g_sprSpit) entity_set_model(spit, SPRITE_SPIT); else entity_set_model(spit, SPRITE_SPIT);

    new Float:launch_pos[3];
    launch_pos[0] = m_origin[0];
    launch_pos[1] = m_origin[1];
    launch_pos[2] = m_origin[2] + 48.0;
    entity_set_origin(spit, launch_pos);

    entity_set_int(spit, EV_INT_movetype, MOVETYPE_BOUNCE);
    entity_set_int(spit, EV_INT_solid, SOLID_BBOX);
    entity_set_size(spit, Float:{-4.0, -4.0, -4.0}, Float:{4.0, 4.0, 4.0});
    entity_set_float(spit, EV_FL_gravity, 0.55);

    new Float:arc_vel[3];
    arc_vel[0] = t_pos[0] - launch_pos[0];
    arc_vel[1] = t_pos[1] - launch_pos[1];
    arc_vel[2] = (t_pos[2] - launch_pos[2]) + 160.0;
    new Float:len = floatsqroot(arc_vel[0]*arc_vel[0] + arc_vel[1]*arc_vel[1]);
    if (len > 1.0) {
        arc_vel[0] = (arc_vel[0] / len) * 720.0;
        arc_vel[1] = (arc_vel[1] / len) * 720.0;
    }
    entity_set_vector(spit, EV_VEC_velocity, arc_vel);
    entity_set_edict(spit, EV_ENT_owner, ent);
}

public fw_spit_touch(ptr, ptd) {
    if (!is_valid_ent(ptr)) return;

    new Float:hit_pos[3];
    entity_get_vector(ptr, EV_VEC_origin, hit_pos);

    emit_sound(ptr, CHAN_WEAPON, SOUND_SPIT_HIT, 1.0, ATTN_NORM, 0, PITCH_NORM);

    // Explosion Effect (TE_EXPLOSION)
    message_begin(MSG_BROADCAST, SVC_TEMPENTITY);
    write_byte(TE_EXPLOSION);
    write_coord(floatround(hit_pos[0]));
    write_coord(floatround(hit_pos[1]));
    write_coord(floatround(hit_pos[2]));
    write_short(g_sprExplode);
    write_byte(20); write_byte(15); write_byte(0);
    message_end();

    new Float:dmg = get_pcvar_float(g_cvarRangedDamage) * get_difficulty_damage_mult();
    new players[32], count;
    get_players(players, count, "a");

    for (new i = 0; i < count; i++) {
        new id = players[i];
        if (id == g_dummyTBot) continue;

        new Float:p_pos[3];
        entity_get_vector(id, EV_VEC_origin, p_pos);
        if (get_distance_f(hit_pos, p_pos) <= 150.0) {
            ExecuteHamB(Ham_TakeDamage, id, g_monsterEnt, g_monsterEnt, dmg, DMG_ACID);
            shake_screen(id, 14.0, 1.0);
            g_killsByAttack[ATTACK_SPIT]++;
        }
    }

    remove_entity(ptr);
}

stock trigger_jumpscare(ent, target, const Float:m_origin[3]) {
    new Float:gametime = get_gametime();
    g_lastJumpscareTime[target] = gametime;
    g_lastAttackUsed = ATTACK_JUMPSCARE;

    // Freeze victim movement for 0.4s
    set_pev(target, pev_flags, pev(target, pev_flags) | FL_FROZEN);
    remove_task(target + 4000);
    set_task(0.40, "task_unfreeze_victim", target + 4000);

    // Loud horror sting
    emit_sound(target, CHAN_STATIC, SOUND_STING, 1.0, ATTN_NONE, 0, PITCH_NORM);
    shake_screen(target, 24.0, 1.5);

    // ScreenFade (with photosensitivity flash-safe mode)
    new safe = get_pcvar_num(g_cvarFlashSafe);
    new r = safe ? 50 : 200;
    new a = safe ? 120 : 230;

    static msgScreenFade = 0;
    if (!msgScreenFade) msgScreenFade = get_user_msgid("ScreenFade");
    message_begin(MSG_ONE, msgScreenFade, _, target);
    write_short(floatround(0.4 * 4096.0));
    write_short(floatround(0.3 * 4096.0));
    write_short(0x0001); // FFADE_IN
    write_byte(r); write_byte(0); write_byte(0); write_byte(a);
    message_end();

    // Turn victim directly toward monster face
    new Float:diff[3];
    diff[0] = m_origin[0] - g_lastKnownPos[0];
    diff[1] = m_origin[1] - g_lastKnownPos[1];
    diff[2] = 0.0;
    new Float:look_ang[3];
    vector_to_angle(diff, look_ang);
    entity_set_vector(target, EV_VEC_angles, look_ang);
    entity_set_vector(target, EV_VEC_v_angle, look_ang);

    // Follow with heavy claw hit
    new Float:dmg = get_pcvar_float(g_cvarComboDamage) * 1.3 * get_difficulty_damage_mult();
    ExecuteHamB(Ham_TakeDamage, target, ent, ent, dmg, DMG_SLASH);
    g_killsByAttack[ATTACK_JUMPSCARE]++;

    set_monster_sequence(ent, 8); // attack1
}

public task_unfreeze_victim(taskid) {
    new id = taskid - 4000;
    if (is_user_alive(id)) {
        set_pev(id, pev_flags, pev(id, pev_flags) & ~FL_FROZEN);
    }
}

stock count_players_in_radius(const Float:center[3], Float:radius) {
    new players[32], count;
    get_players(players, count, "a");
    new inside = 0;
    for (new i = 0; i < count; i++) {
        if (players[i] == g_dummyTBot) continue;
        new Float:p_orig[3];
        entity_get_vector(players[i], EV_VEC_origin, p_orig);
        if (get_distance_f(center, p_orig) <= radius) inside++;
    }
    return inside;
}

stock navigate_monster_towards(ent, const Float:m_origin[3], const Float:t_origin[3], target) {
    new Float:move_speed = get_pcvar_float(g_cvarSpeedRun) * get_difficulty_speed_mult();

    // Check direct Line of Sight
    if (check_line_of_sight(target, t_origin, ent, m_origin)) {
        g_monsterGoalPos = t_origin;
        g_monsterMoveSpeed = move_speed;
        face_and_move_direct(ent, m_origin, t_origin, move_speed, 0.25);
        g_pathLength = 0;
        return;
    }

    // A* Pathfinding (check if repath needed)
    new Float:gametime = get_gametime();
    new bool:need_repath = false;
    if (g_pathLength == 0 || g_pathIndex >= g_pathLength) need_repath = true;
    else if (gametime - g_lastPathCalcTime >= 1.5) need_repath = true;

    if (need_repath) {
        new start_wp = find_nearest_waypoint(m_origin);

        // Flanking decision: every 3rd attempt, search for flanking route
        g_flankCounter++;
        new bool:do_flank = (g_flankCounter % 3 == 0);

        // Predictive target route
        new Float:dest[3];
        predict_target_route(target, dest);
        new goal_wp = find_nearest_waypoint(dest);

        if (start_wp != -1 && goal_wp != -1) {
            calculate_astar_path(start_wp, goal_wp, do_flank);
            g_lastPathCalcTime = gametime;
        }
    }

    // Follow waypoint path
    if (g_pathLength > 0 && g_pathIndex < g_pathLength) {
        new next_node = g_currentPath[g_pathIndex];
        new Float:node_origin[3];
        node_origin = g_wpOrigin[next_node];
        node_origin[2] = m_origin[2]; // Level heading

        new Float:dist_to_node = get_distance_f(m_origin, node_origin);
        if (dist_to_node <= 48.0) {
            g_pathIndex++;
            if (g_pathIndex < g_pathLength) {
                node_origin = g_wpOrigin[g_currentPath[g_pathIndex]];
                node_origin[2] = m_origin[2];
            }
        } else if (g_pathIndex + 1 < g_pathLength) {
            new skip_node = g_currentPath[g_pathIndex + 1];
            if (check_line_of_sight(0, g_wpOrigin[skip_node], ent, m_origin)) {
                g_pathIndex++;
                node_origin = g_wpOrigin[skip_node];
                node_origin[2] = m_origin[2];
            }
        }
        g_monsterGoalPos = node_origin;
        g_monsterMoveSpeed = move_speed;
        face_and_move_direct(ent, m_origin, node_origin, move_speed, 0.25);
    } else {
        face_and_move_direct(ent, m_origin, t_origin, move_speed);
    }
}

stock execute_patrol_behavior(ent, const Float:m_origin[3]) {
    new Float:walk_speed = get_pcvar_float(g_cvarSpeedWalk) * get_difficulty_speed_mult();
    if (g_totalWaypoints <= 0) return;

    if (g_currentPatrolGoal == -1 || g_pathLength == 0 || g_pathIndex >= g_pathLength) {
        // 1. Check known camping spots first
        new camp_goal = -1;
        for (new i = 0; i < g_totalWaypoints; i++) {
            if (g_wpIsCampSpot[i] && (get_gametime() - g_wpLastCampTime[i] <= 20.0)) {
                camp_goal = i;
                g_wpIsCampSpot[i] = false;
                break;
            }
        }

        if (camp_goal >= 0) {
            g_currentPatrolGoal = camp_goal;
        } else {
            // 2. Choose hottest waypoint
            new best_wp = random_num(0, g_totalWaypoints - 1);
            new Float:max_heat = -1.0;
            for (new i = 0; i < g_totalWaypoints; i++) {
                if (g_wpHeat[i] > max_heat) {
                    max_heat = g_wpHeat[i];
                    best_wp = i;
                }
            }
            g_currentPatrolGoal = best_wp;
        }

        new start_wp = find_nearest_waypoint(m_origin);
        if (start_wp != -1) {
            calculate_astar_path(start_wp, g_currentPatrolGoal, false);
        }
    }

    if (g_pathLength > 0 && g_pathIndex < g_pathLength) {
        new node = g_currentPath[g_pathIndex];
        new Float:node_origin[3];
        node_origin = g_wpOrigin[node];
        node_origin[2] = m_origin[2];

        if (get_distance_f(m_origin, node_origin) <= 48.0) {
            g_pathIndex++;
            if (g_pathIndex < g_pathLength) {
                node_origin = g_wpOrigin[g_currentPath[g_pathIndex]];
                node_origin[2] = m_origin[2];
            }
        }
        g_monsterGoalPos = node_origin;
        g_monsterMoveSpeed = walk_speed;
        face_and_move_direct(ent, m_origin, node_origin, walk_speed, 0.25);
    }
}

stock face_and_move_direct(ent, const Float:from[3], const Float:to[3], Float:speed, Float:dt = 0.10) {
    new Float:diff[3];
    diff[0] = to[0] - from[0];
    diff[1] = to[1] - from[1];
    diff[2] = 0.0;

    new Float:target_yaw[3];
    vector_to_angle(diff, target_yaw);
    target_yaw[0] = 0.0;

    new Float:cur_angles[3];
    entity_get_vector(ent, EV_VEC_angles, cur_angles);
    cur_angles[1] = approach_angle(target_yaw[1], cur_angles[1], 240.0 * dt);
    cur_angles[0] = 0.0;
    cur_angles[2] = 0.0;
    entity_set_vector(ent, EV_VEC_angles, cur_angles);

    new Float:step_dist = speed * dt;
    if (step_dist > 25.0) step_dist = 25.0;

    new walk_success = engfunc(EngFunc_WalkMove, ent, cur_angles[1], step_dist, WALKMOVE_NORMAL);
    if (!walk_success) {
        engfunc(EngFunc_MoveToOrigin, ent, to, step_dist, MOVE_NORMAL);
    }
}

// =========================================================================
// SENSES, HEARING & LINE OF SIGHT (Step 3)
// =========================================================================

public fw_playback_event(flags, invoker, eventindex) {
    if (!get_pcvar_num(g_cvarEnabled) || !is_valid_ent(g_monsterEnt)) return FMRES_IGNORED;
    if (invoker < 1 || invoker > 32 || !is_user_alive(invoker) || invoker == g_dummyTBot) return FMRES_IGNORED;

    new Float:p_origin[3];
    entity_get_vector(invoker, EV_VEC_origin, p_origin);

    new Float:m_origin[3];
    entity_get_vector(g_monsterEnt, EV_VEC_origin, m_origin);

    new Float:d = get_distance_f(p_origin, m_origin);
    if (d <= get_pcvar_float(g_cvarHearRange)) {
        g_investigatePos = p_origin;
        add_heat_at_pos(p_origin, 25.0);
        if (g_monsterState == STATE_PATROL) {
            g_monsterState = STATE_INVESTIGATE;
            g_pathLength = 0;
        }
    }
    return FMRES_IGNORED;
}

public task_monster_sense_tick() {
    if (!is_valid_ent(g_monsterEnt) || !get_pcvar_num(g_cvarSense)) return;
    new Float:m_origin[3];
    entity_get_vector(g_monsterEnt, EV_VEC_origin, m_origin);

    new target = select_best_target(m_origin);
    if (target > 0 && is_user_alive(target)) {
        new Float:t_origin[3];
        entity_get_vector(target, EV_VEC_origin, t_origin);
        g_sensePos[0] = t_origin[0] + random_float(-180.0, 180.0);
        g_sensePos[1] = t_origin[1] + random_float(-180.0, 180.0);
        g_sensePos[2] = t_origin[2];
        add_heat_at_pos(t_origin, 15.0);
    }
}

stock bool:check_line_of_sight(target, const Float:t_pos[3], ent, const Float:m_pos[3]) {
    g_debugTracesThisSec++;
    new budget = get_pcvar_num(g_cvarTraceBudget);
    if (budget > 0 && g_debugTracesThisSec > budget) {
        return false;
    }
    new Float:start[3], Float:end[3];
    start = m_pos; start[2] += 50.0;
    end   = t_pos; end[2]   += 20.0;
    engfunc(EngFunc_TraceLine, start, end, DONT_IGNORE_MONSTERS, ent, 0);
    new hit = get_tr2(0, TR_pHit);
    new Float:frac;
    get_tr2(0, TR_flFraction, frac);
    return (hit == target || frac >= 0.98);
}

stock bool:is_player_looking_at(player, const Float:p_origin[3], const Float:m_origin[3]) {
    new Float:view_angles[3];
    entity_get_vector(player, EV_VEC_v_angle, view_angles);
    new Float:fwd_vec[3];
    angle_vector(view_angles, ANGLEVECTOR_FORWARD, fwd_vec);

    new Float:to_monster[3];
    to_monster[0] = m_origin[0] - p_origin[0];
    to_monster[1] = m_origin[1] - p_origin[1];
    to_monster[2] = 0.0;

    new Float:len = floatsqroot(to_monster[0]*to_monster[0] + to_monster[1]*to_monster[1]);
    if (len < 1.0) return true;

    to_monster[0] /= len;
    to_monster[1] /= len;

    new Float:dot = (fwd_vec[0] * to_monster[0]) + (fwd_vec[1] * to_monster[1]);
    return (dot >= 0.50); // ~60 degree vision cone
}

// =========================================================================
// DAMAGE & HIT REACTIONS (Steps 2 & Gore)
// =========================================================================

stock render_monster_blood(tr, Float:damage, const Float:direction[3]) {
    if (!get_pcvar_num(g_cvarBlood)) return;
    new Float:hit_pos[3];
    get_tr2(tr, TR_vecEndPos, hit_pos);

    new blood_col = get_pcvar_num(g_cvarBloodColor);
    new blood_amt = clamp(get_pcvar_num(g_cvarBloodAmount), 1, 3);
    new col_sprite = (blood_col == 1) ? 195 : 247;
    new col_stream = (blood_col == 1) ? 195 : 70;

    // TE_BLOODSPRITE - Volumetric mist
    message_begin(MSG_BROADCAST, SVC_TEMPENTITY);
    write_byte(TE_BLOODSPRITE);
    write_coord(floatround(hit_pos[0]));
    write_coord(floatround(hit_pos[1]));
    write_coord(floatround(hit_pos[2]));
    write_short(g_sprBloodSpray);
    write_short(g_sprBlood);
    write_byte(col_sprite);
    write_byte(clamp(floatround(damage / 7.0) * blood_amt + 5, 5, 25));
    message_end();

    // TE_BLOODSTREAM - Arterial jet opposite to bullet
    message_begin(MSG_BROADCAST, SVC_TEMPENTITY);
    write_byte(TE_BLOODSTREAM);
    write_coord(floatround(hit_pos[0]));
    write_coord(floatround(hit_pos[1]));
    write_coord(floatround(hit_pos[2]));
    write_coord(floatround(direction[0] * -1.0));
    write_coord(floatround(direction[1] * -1.0));
    write_coord(floatround(direction[2] * -1.0));
    write_byte(col_stream);
    write_byte(clamp(floatround(damage / 3.0) + 20, 15, 80));
    message_end();

    // Wall/Floor Decal (TE_WORLDDECAL)
    new Float:trace_end[3];
    trace_end[0] = hit_pos[0] + (direction[0] * 90.0);
    trace_end[1] = hit_pos[1] + (direction[1] * 90.0);
    trace_end[2] = hit_pos[2] + (direction[2] * 90.0);

    engfunc(EngFunc_TraceLine, hit_pos, trace_end, DONT_IGNORE_MONSTERS, g_monsterEnt, 0);
    new Float:fraction;
    get_tr2(0, TR_flFraction, fraction);

    if (fraction < 1.0) {
        new Float:decal_pos[3];
        get_tr2(0, TR_vecEndPos, decal_pos);
        new decal_idx = (blood_col == 1) ? g_decalYellowBlood[random_num(0, 5)] : g_decalBlood[random_num(0, 7)];
        if (decal_idx > 0) {
            message_begin(MSG_BROADCAST, SVC_TEMPENTITY);
            write_byte(TE_WORLDDECAL);
            write_coord(floatround(decal_pos[0]));
            write_coord(floatround(decal_pos[1]));
            write_coord(floatround(decal_pos[2]));
            write_byte(decal_idx);
            message_end();
        }
    }
}

public fw_monster_traceattack(victim, attacker, Float:damage, Float:direction[3], tr, damage_bits) {
    if (victim != g_monsterEnt) return HAM_IGNORED;

    // Headshot Multiplier: 2x damage!
    new hitgroup = get_tr2(tr, TR_iHitgroup);
    if (hitgroup == 1) { // HIT_HEAD
        damage *= 2.0;
    }

    if (attacker >= 1 && attacker <= 32 && is_user_connected(attacker)) {
        new Float:m_origin[3];
        entity_get_vector(victim, EV_VEC_origin, m_origin);
        g_sharedMonsterPos = m_origin;
        g_sharedMonsterTime = get_gametime() + 7.0;

        if (is_user_bot(attacker)) {
            g_botCommitTime[attacker] = get_gametime() + get_pcvar_float(g_cvarBotCommitTime);
            g_botState[attacker] = BOT_STATE_ENGAGE;
        }
    }

    render_monster_blood(tr, damage, direction);
    ExecuteHamB(Ham_TakeDamage, victim, attacker, attacker, damage, damage_bits);

    // HAM_SUPERCEDE blocks engine metal sparks / ricochet
    return HAM_SUPERCEDE;
}

public fw_monster_takedamage(victim, inflictor, attacker, Float:damage, damage_type) {
    if (victim != g_monsterEnt) return HAM_IGNORED;

    new Float:gametime = get_gametime();
    g_lastDamageTakenTime = gametime;

    if (attacker >= 1 && attacker <= 32 && is_user_connected(attacker)) {
        g_playerRoundDamage[attacker] += damage;
        g_recentAttackerTime[attacker] = gametime;

        // Count active attackers in last 4.0s
        new active_attackers = 0;
        for (new i = 1; i <= 32; i++) {
            if (gametime - g_recentAttackerTime[i] <= 4.0) active_attackers++;
        }

        // Damage Reduction (default 20%) when distant (>700u) or single shooter
        new Float:m_pos[3], Float:a_pos[3];
        entity_get_vector(victim, EV_VEC_origin, m_pos);
        entity_get_vector(attacker, EV_VEC_origin, a_pos);
        new Float:d = get_distance_f(m_pos, a_pos);

        if (d > 700.0 || active_attackers <= 1) {
            damage *= (1.0 - get_pcvar_float(g_cvarDmgReduction));
            SetHamParamFloat(4, damage);
        }

        // Grenade 1.5x Multiplier
        if (damage_type & (DMG_GRENADE | DMG_BLAST)) {
            damage *= 1.5;
            SetHamParamFloat(4, damage);
        }

        // Track Top Damage Dealer
        if (g_playerRoundDamage[attacker] > g_playerRoundDamage[g_topDamagePlayer]) {
            g_topDamagePlayer = attacker;
        }

        // Health Phase Transitions (Step 2)
        new Float:curr_hp = entity_get_float(victim, EV_FL_health) - damage;
        new Float:max_hp = entity_get_float(victim, EV_FL_max_health);
        new Float:pct = (curr_hp / max_hp) * 100.0;

        if (pct <= 33.0 && g_currentPhase < 3) {
            g_currentPhase = 3; // Phase 3: BERSERK
            emit_sound(victim, CHAN_VOICE, SOUND_ALERT3, 1.0, ATTN_NORM, 0, PITCH_NORM);
            shake_all_screens(22.0, 2.0);
            client_print_color(0, print_team_red, "^4[Horror] ^3THE ZOMBIE ENTERS A BLOOD FRENZY! ^1Phase 3 - BERSERK! Speed and ferocity maximized!");
        } else if (pct <= 66.0 && g_currentPhase < 2) {
            g_currentPhase = 2; // Phase 2: ENRAGED
            emit_sound(victim, CHAN_VOICE, SOUND_ALERT2, 1.0, ATTN_NORM, 0, PITCH_NORM);
            shake_all_screens(16.0, 1.5);
            client_print_color(0, print_team_red, "^4[Horror] ^3THE ZOMBIE ENRAGES! ^1Phase 2 has begun! Increased speed!");
        }

        // Flinch / Stagger on heavy hits (unless performing special attack)
        if (damage >= 80.0 && g_monsterState != STATE_STAGGER && g_monsterState != STATE_LUNGE_WINDUP && g_monsterState != STATE_LUNGING && g_monsterState != STATE_STOMP_WINDUP) {
            g_monsterState = STATE_STAGGER;
            g_staggerEndTime = gametime + 0.45;
            set_monster_sequence(victim, 4); // flinch
            emit_sound(victim, CHAN_VOICE, (random_num(0, 1) ? SOUND_PAIN1 : SOUND_PAIN2), 1.0, ATTN_NORM, 0, PITCH_NORM);
        }
    }
    return HAM_IGNORED;
}

public fw_monster_killed(victim, attacker, should_gib) {
    if (victim != g_monsterEnt) return HAM_IGNORED;

    g_monsterState = STATE_DEAD;
    entity_set_int(victim, EV_INT_solid, SOLID_NOT);
    entity_set_int(victim, EV_INT_movetype, MOVETYPE_NONE);
    set_monster_sequence(victim, 17); // diesimple

    stop_all_monster_sounds();
    remove_task(TASK_MONSTER_MOVE);
    remove_task(TASK_AI_TICK);
    remove_task(TASK_HEALTHBAR);
    remove_task(TASK_BOT_REACT);
    remove_task(TASK_DANGER_HUD);

    // Floor Blood Puddle
    new Float:m_pos[3];
    entity_get_vector(victim, EV_VEC_origin, m_pos);
    new Float:floor_end[3];
    floor_end[0] = m_pos[0]; floor_end[1] = m_pos[1]; floor_end[2] = m_pos[2] - 128.0;

    engfunc(EngFunc_TraceLine, m_pos, floor_end, IGNORE_MONSTERS, victim, 0);
    new Float:floor_pos[3];
    get_tr2(0, TR_vecEndPos, floor_pos);

    new blood_col = get_pcvar_num(g_cvarBloodColor);
    for (new i = 0; i < 4; i++) {
        new Float:puddle_pos[3];
        puddle_pos[0] = floor_pos[0] + random_float(-20.0, 20.0);
        puddle_pos[1] = floor_pos[1] + random_float(-20.0, 20.0);
        puddle_pos[2] = floor_pos[2];

        new decal_idx = (blood_col == 1) ? g_decalYellowBlood[random_num(0, 5)] : g_decalBlood[random_num(0, 7)];
        if (decal_idx > 0) {
            message_begin(MSG_BROADCAST, SVC_TEMPENTITY);
            write_byte(TE_WORLDDECAL);
            write_coord(floatround(puddle_pos[0]));
            write_coord(floatround(puddle_pos[1]));
            write_coord(floatround(puddle_pos[2]));
            write_byte(decal_idx);
            message_end();
        }
    }

    // Death Gore Cloud
    for (new i = 0; i < 3; i++) {
        message_begin(MSG_BROADCAST, SVC_TEMPENTITY);
        write_byte(TE_BLOODSPRITE);
        write_coord(floatround(m_pos[0] + random_float(-15.0, 15.0)));
        write_coord(floatround(m_pos[1] + random_float(-15.0, 15.0)));
        write_coord(floatround(m_pos[2] + random_float(10.0, 40.0)));
        write_short(g_sprBloodSpray);
        write_short(g_sprBlood);
        write_byte(blood_col == 1 ? 195 : 247);
        write_byte(25);
        message_end();
    }

    new killer_name[32] = "Survivors";
    if (attacker >= 1 && attacker <= 32 && is_user_connected(attacker)) {
        get_user_name(attacker, killer_name, charsmax(killer_name));
    }

    client_print_color(0, print_team_blue, "^4[Horror] ^3THE NIGHTMARE IS SLAIN! ^1%s delivered the fatal blow!", killer_name);
    server_cmd("sv_restart 4");
    return HAM_IGNORED;
}

public fw_player_takedamage(victim, inflictor, attacker, Float:damage, damage_type) {
    if (attacker == g_monsterEnt || inflictor == g_monsterEnt) {
        SetHamParamFloat(4, damage);
        if (entity_get_float(victim, EV_FL_health) - damage <= 0.0) {
            if (is_user_bot(victim)) g_botsDevoured++;
            else g_playersDevoured++;
            g_playerDeathTime[victim] = get_gametime();
        }
        return HAM_HANDLED;
    }
    return HAM_IGNORED;
}

// =========================================================================
// TEAMMATE BOT BRAIN & REAL-TIME COMBAT (Step 4 & 5)
// =========================================================================

stock Float:get_bot_preferred_dist(id) {
    new clip, ammo;
    new wpn = get_user_weapon(id, clip, ammo);
    switch (wpn) {
        case CSW_M3, CSW_XM1014: return 450.0;
        case CSW_MAC10, CSW_UMP45, CSW_MP5NAVY, CSW_TMP, CSW_P90: return 580.0;
        case CSW_SCOUT, CSW_AWP, CSW_G3SG1, CSW_SG550: return 850.0;
        case CSW_KNIFE: return 120.0;
        default: return 700.0;
    }
    return 700.0;
}

public task_bot_brain_think() {
    if (!is_valid_ent(g_monsterEnt) || g_monsterState == STATE_NONE || g_monsterState == STATE_DEAD) return;
    if (!get_pcvar_num(g_cvarBotReact) || !get_pcvar_num(g_cvarBotAI)) return;

    new Float:gametime = get_gametime();
    new Float:m_origin[3];
    entity_get_vector(g_monsterEnt, EV_VEC_origin, m_origin);

    new Float:danger_dist = get_pcvar_float(g_cvarBotDangerDist);
    new Float:engage_dist = get_pcvar_float(g_cvarBotEngageDist);

    for (new id = 1; id <= 32; id++) {
        if (!is_user_connected(id) || !is_user_alive(id) || !is_user_bot(id) || id == g_dummyTBot) {
            g_botState[id] = BOT_STATE_NONE;
            continue;
        }

        new Float:b_origin[3];
        entity_get_vector(id, EV_VEC_origin, b_origin);
        new Float:d = get_distance_f(b_origin, m_origin);
        new bool:has_los = check_line_of_sight(id, b_origin, g_monsterEnt, m_origin);
        new Float:hp = entity_get_float(id, EV_FL_health);

        // Update shared knowledge on visual contact
        if (has_los && d <= engage_dist) {
            g_sharedMonsterPos = m_origin;
            g_sharedMonsterTime = gametime + 7.0;
            g_botCommitTime[id] = gametime + get_pcvar_float(g_cvarBotCommitTime);

            if (get_pcvar_num(g_cvarBotCallouts) && (gametime > g_lastCalloutTime + 6.0)) {
                new bot_name[32];
                get_user_name(id, bot_name, charsmax(bot_name));
                client_print_color(0, print_team_blue, "^4[Radio] ^3%s: ^1MONSTER SPOTTED! Focus fire!", bot_name);
                g_lastCalloutTime = gametime;
            }
        }

        // Reaction to monster special attacks
        if (g_monsterState == STATE_STOMP_WINDUP && d <= 450.0) {
            g_botState[id] = BOT_STATE_PANIC; // Flee from ground stomp shockwave
            continue;
        }
        if (g_monsterState == STATE_LUNGE_WINDUP && d <= 700.0) {
            g_botState[id] = BOT_STATE_KITE; // Sidestep away from charge path
            continue;
        }

        // State Machine Transitions
        if (hp < 25.0 || (d < 200.0 && g_botCourage[id] < 45)) {
            g_botState[id] = BOT_STATE_PANIC;
        } else if ((d < danger_dist || g_currentTarget == id) && (has_los || d < 350.0)) {
            g_botState[id] = BOT_STATE_KITE;
            g_botCommitTime[id] = gametime + get_pcvar_float(g_cvarBotCommitTime);
        } else if (has_los && d <= engage_dist) {
            g_botState[id] = BOT_STATE_ENGAGE;
            g_botCommitTime[id] = gametime + get_pcvar_float(g_cvarBotCommitTime);
        } else if (gametime < g_botCommitTime[id] && d <= engage_dist + 200.0) {
            g_botState[id] = BOT_STATE_ENGAGE;
        } else {
            g_botState[id] = BOT_STATE_SEARCH;
            if (gametime < g_sharedMonsterTime) {
                g_botSearchTarget[id] = g_sharedMonsterPos;
            } else if (gametime > g_botNextSearchPick[id]) {
                if (g_totalWaypoints > 0) {
                    new zoneWp = ((id * 7) + random_num(0, 3)) % g_totalWaypoints;
                    g_botSearchTarget[id] = g_wpOrigin[zoneWp];
                }
                g_botNextSearchPick[id] = gametime + random_float(4.0, 7.0);
            }
        }
    }
}

stock compute_aim_angles(const Float:bot_eyes[3], const Float:target_pos[3], Float:out_angles[3]) {
    new Float:diff[3];
    diff[0] = target_pos[0] - bot_eyes[0];
    diff[1] = target_pos[1] - bot_eyes[1];
    diff[2] = target_pos[2] - bot_eyes[2];

    vector_to_angle(diff, out_angles);

    // Normalize pitch from [0, 360] to [-180, +180]
    while (out_angles[0] > 180.0) out_angles[0] -= 360.0;
    while (out_angles[0] < -180.0) out_angles[0] += 360.0;

    // GoldSrc vector_to_angle outputs positive pitch for upward angles.
    // Client viewangles (v_angle / UC_ViewAngles) requires:
    // negative pitch for UP (sky), positive pitch for DOWN (floor).
    out_angles[0] = -out_angles[0];

    // Clamp to valid player pitch limits
    if (out_angles[0] > 89.0) out_angles[0] = 89.0;
    else if (out_angles[0] < -89.0) out_angles[0] = -89.0;

    out_angles[2] = 0.0;
}

public fw_cmd_start(id, uc_handle, random_seed) {
    if (!get_pcvar_num(g_cvarEnabled) || !is_valid_ent(g_monsterEnt) || g_monsterState == STATE_NONE || g_monsterState == STATE_DEAD) return FMRES_IGNORED;
    if (!is_user_alive(id) || !is_user_bot(id) || id == g_dummyTBot) return FMRES_IGNORED;
    if (!get_pcvar_num(g_cvarBotReact) || !get_pcvar_num(g_cvarBotAI)) return FMRES_IGNORED;

    new Float:b_origin[3];
    entity_get_vector(id, EV_VEC_origin, b_origin);
    new Float:m_origin[3];
    entity_get_vector(g_monsterEnt, EV_VEC_origin, m_origin);

    new Float:d = get_distance_f(b_origin, m_origin);
    new buttons = get_uc(uc_handle, UC_Buttons);
    new Float:gametime = get_gametime();

    switch (g_botState[id]) {
        case BOT_STATE_ENGAGE: {
            new Float:b_eye[3];
            entity_get_vector(id, EV_VEC_view_ofs, b_eye);
            b_eye[0] += b_origin[0];
            b_eye[1] += b_origin[1];
            b_eye[2] += b_origin[2];

            new Float:m_target[3];
            m_target[0] = m_origin[0];
            m_target[1] = m_origin[1];
            m_target[2] = m_origin[2] + 45.0; // Aim at monster chest

            new Float:aim_angles[3];
            compute_aim_angles(b_eye, m_target, aim_angles);

            new Float:err = get_pcvar_float(g_cvarBotAimError);
            if (err > 0.0) {
                aim_angles[0] += random_float(-err, err);
                aim_angles[1] += random_float(-err, err);
            }

            set_uc(uc_handle, UC_ViewAngles, aim_angles);
            entity_set_vector(id, EV_VEC_v_angle, aim_angles);

            new Float:pref = get_bot_preferred_dist(id);
            if (d > pref + 120.0) {
                set_uc(uc_handle, UC_ForwardMove, 220.0);
                buttons |= IN_FORWARD; buttons &= ~IN_BACK;
            } else if (d < pref - 120.0) {
                set_uc(uc_handle, UC_ForwardMove, -220.0);
                buttons |= IN_BACK; buttons &= ~IN_FORWARD;
            } else {
                set_uc(uc_handle, UC_ForwardMove, 0.0);
                set_uc(uc_handle, UC_SideMove, (id % 2 == 0) ? 120.0 : -120.0);
            }

            if (gametime > g_botLastBurstTime[id] + 0.12) {
                buttons |= IN_ATTACK;
                g_botBurstShots[id]++;
                if (g_botBurstShots[id] >= 4) {
                    g_botLastBurstTime[id] = gametime + random_float(0.18, 0.35);
                    g_botBurstShots[id] = 0;
                }
            } else buttons &= ~IN_ATTACK;

            set_uc(uc_handle, UC_Buttons, buttons);
            return FMRES_HANDLED;
        }
        case BOT_STATE_KITE: {
            new Float:b_eye[3];
            entity_get_vector(id, EV_VEC_view_ofs, b_eye);
            b_eye[0] += b_origin[0];
            b_eye[1] += b_origin[1];
            b_eye[2] += b_origin[2];

            new Float:m_target[3];
            m_target[0] = m_origin[0];
            m_target[1] = m_origin[1];
            m_target[2] = m_origin[2] + 45.0;

            new Float:aim_angles[3];
            compute_aim_angles(b_eye, m_target, aim_angles);

            set_uc(uc_handle, UC_ViewAngles, aim_angles);
            entity_set_vector(id, EV_VEC_v_angle, aim_angles);

            set_uc(uc_handle, UC_ForwardMove, -320.0);
            set_uc(uc_handle, UC_SideMove, (id % 2 == 0) ? 140.0 : -140.0);
            buttons |= IN_BACK; buttons &= ~IN_FORWARD;

            if (gametime > g_botLastBurstTime[id] + 0.10) {
                buttons |= IN_ATTACK;
                g_botBurstShots[id]++;
                if (g_botBurstShots[id] >= 5) {
                    g_botLastBurstTime[id] = gametime + 0.20;
                    g_botBurstShots[id] = 0;
                }
            }
            set_uc(uc_handle, UC_Buttons, buttons);
            return FMRES_HANDLED;
        }
        case BOT_STATE_PANIC: {
            new Float:diff[3];
            diff[0] = b_origin[0] - m_origin[0];
            diff[1] = b_origin[1] - m_origin[1];
            diff[2] = 0.0;
            new Float:flee[3];
            vector_to_angle(diff, flee);
            flee[0] = 0.0;

            set_uc(uc_handle, UC_ViewAngles, flee);
            entity_set_vector(id, EV_VEC_v_angle, flee);
            set_uc(uc_handle, UC_ForwardMove, 350.0);
            buttons |= IN_FORWARD; buttons &= ~(IN_BACK | IN_ATTACK);
            if (random_num(0, 4) == 0) buttons |= IN_JUMP;

            set_uc(uc_handle, UC_Buttons, buttons);
            return FMRES_HANDLED;
        }
        case BOT_STATE_SEARCH: {
            new Float:diff[3];
            diff[0] = g_botSearchTarget[id][0] - b_origin[0];
            diff[1] = g_botSearchTarget[id][1] - b_origin[1];
            diff[2] = 0.0;
            if (vector_length(diff) > 64.0) {
                new Float:mv[3];
                vector_to_angle(diff, mv);
                mv[0] = 0.0;
                set_uc(uc_handle, UC_ViewAngles, mv);
                entity_set_vector(id, EV_VEC_v_angle, mv);
                set_uc(uc_handle, UC_ForwardMove, 250.0);
                buttons |= IN_FORWARD; buttons &= ~IN_BACK;
                set_uc(uc_handle, UC_Buttons, buttons);
                return FMRES_HANDLED;
            }
        }
    }
    return FMRES_IGNORED;
}

// =========================================================================
// UI SYSTEMS: BOSS HEALTH BAR, DANGER METER & ATMOSPHERE (Step 5)
// =========================================================================

public task_update_healthbar() {
    if (!is_valid_ent(g_monsterEnt) || !get_pcvar_num(g_cvarHealthBar)) return;

    new Float:hp = entity_get_float(g_monsterEnt, EV_FL_health);
    new Float:max_hp = entity_get_float(g_monsterEnt, EV_FL_max_health);
    if (hp <= 0.0 || max_hp <= 0.0) return;

    new Float:pct = (hp / max_hp) * 100.0;
    if (pct < 0.0) pct = 0.0;
    if (pct > 100.0) pct = 100.0;

    new total_blocks = 20;
    new filled_blocks = floatround((pct / 100.0) * float(total_blocks));
    if (filled_blocks > total_blocks) filled_blocks = total_blocks;

    new bar[64];
    new len = 0;
    for (new i = 0; i < total_blocks; i++) {
        len += formatex(bar[len], charsmax(bar) - len, (i < filled_blocks ? "|" : " "));
    }

    new r = 40, g = 240, b = 40;
    new phase_str[32] = "[PHASE 1 - AWAKENED]";
    if (g_currentPhase == 3 || pct <= 33.0) {
        r = 255; g = 30; b = 30;
        copy(phase_str, charsmax(phase_str), "[PHASE 3 - BERSERK]");
    } else if (g_currentPhase == 2 || pct <= 66.0) {
        r = 255; g = 180; b = 20;
        copy(phase_str, charsmax(phase_str), "[PHASE 2 - ENRAGED]");
    }

    new Float:m_origin[3];
    entity_get_vector(g_monsterEnt, EV_VEC_origin, m_origin);
    new always = get_pcvar_num(g_cvarHealthBarAlways);

    new players[32], count;
    get_players(players, count, "a");

    for (new i = 0; i < count; i++) {
        new id = players[i];
        if (is_user_bot(id) || id == g_dummyTBot) continue;

        new Float:p_origin[3];
        entity_get_vector(id, EV_VEC_origin, p_origin);

        if (always || get_distance_f(m_origin, p_origin) <= 1200.0 || (get_gametime() - g_lastDamageTakenTime <= 3.0)) {
            set_hudmessage(r, g, b, -1.0, 0.03, 0, 0.0, 0.35, 0.05, 0.05, -1);
            show_hudmessage(id, "ZOMBIE   [%s]   %d%%\n%s", bar, floatround(pct), phase_str);
        }
    }
}

public task_danger_meter() {
    if (!is_valid_ent(g_monsterEnt) || !get_pcvar_num(g_cvarDangerHud)) return;

    new Float:m_origin[3];
    entity_get_vector(g_monsterEnt, EV_VEC_origin, m_origin);

    new players[32], count;
    get_players(players, count, "a");

    for (new i = 0; i < count; i++) {
        new id = players[i];
        if (is_user_bot(id) || id == g_dummyTBot) continue;

        new Float:p_origin[3];
        entity_get_vector(id, EV_VEC_origin, p_origin);
        new Float:d = get_distance_f(p_origin, m_origin);

        if (d <= 1200.0) {
            // Relative Angle & Direction Hint
            new Float:p_angles[3];
            entity_get_vector(id, EV_VEC_v_angle, p_angles);

            new Float:to_m[3];
            to_m[0] = m_origin[0] - p_origin[0];
            to_m[1] = m_origin[1] - p_origin[1];
            to_m[2] = 0.0;

            new Float:ang_to_m[3];
            vector_to_angle(to_m, ang_to_m);

            new Float:diff_yaw = ang_to_m[1] - p_angles[1];
            while (diff_yaw > 180.0) diff_yaw -= 360.0;
            while (diff_yaw < -180.0) diff_yaw += 360.0;

            new dir_hint[32];
            if (diff_yaw >= -45.0 && diff_yaw <= 45.0) copy(dir_hint, charsmax(dir_hint), "AHEAD");
            else if (diff_yaw > 45.0 && diff_yaw <= 135.0) copy(dir_hint, charsmax(dir_hint), "TO YOUR LEFT");
            else if (diff_yaw < -45.0 && diff_yaw >= -135.0) copy(dir_hint, charsmax(dir_hint), "TO YOUR RIGHT");
            else copy(dir_hint, charsmax(dir_hint), "BEHIND YOU!");

            new bar[16];
            new r = 0, g = 255, bl = 255;
            if (d < 400.0) {
                copy(bar, charsmax(bar), "[|||||]");
                r = 255; g = 30; bl = 30;
            } else if (d < 650.0) {
                copy(bar, charsmax(bar), "[|||| ]");
                r = 255; g = 140; bl = 0;
            } else if (d < 900.0) {
                copy(bar, charsmax(bar), "[|||  ]");
                r = 255; g = 255; bl = 0;
            } else {
                copy(bar, charsmax(bar), "[|    ]");
                r = 80; g = 200; bl = 255;
            }

            set_hudmessage(r, g, bl, 0.04, 0.82, 0, 0.0, 0.40, 0.05, 0.05, 3);
            show_hudmessage(id, "DANGER: %s   (%.0fu)\nDIRECTION: %s", bar, d, dir_hint);
        }
    }
}

public task_heartbeat_loop() {
    if (!is_valid_ent(g_monsterEnt)) return;
    new Float:m_origin[3];
    entity_get_vector(g_monsterEnt, EV_VEC_origin, m_origin);

    new players[32], count;
    get_players(players, count, "a");

    new do_hb = get_pcvar_num(g_cvarHeartbeat);
    new do_fl = get_pcvar_num(g_cvarFlicker);
    new do_pu = get_pcvar_num(g_cvarPulse);

    for (new i = 0; i < count; i++) {
        new id = players[i];
        if (is_user_bot(id) || id == g_dummyTBot) continue;

        new Float:p_origin[3];
        entity_get_vector(id, EV_VEC_origin, p_origin);
        new Float:d = get_distance_f(m_origin, p_origin);

        if (d <= 1000.0) {
            if (do_hb && (d <= 750.0 || random_num(1, 2) == 1)) {
                emit_sound(id, CHAN_STATIC, SOUND_HEARTBEAT, 0.9, ATTN_NORM, 0, PITCH_NORM);
            }
            if (do_fl && random_num(1, 4) == 1) {
                client_cmd(id, "impulse 100");
            }
            if (do_pu && d <= 400.0) {
                static msgScreenFade = 0;
                if (!msgScreenFade) msgScreenFade = get_user_msgid("ScreenFade");
                message_begin(MSG_ONE_UNRELIABLE, msgScreenFade, _, id);
                write_short(floatround(0.3 * 4096.0));
                write_short(floatround(0.2 * 4096.0));
                write_short(0x0001);
                write_byte(120); write_byte(0); write_byte(0); write_byte(70);
                message_end();
            }
        }
    }
}

stock render_debug_telemetry(const Float:m_origin[3], const Float:t_origin[3], Float:dist) {
    // 1. Drop Laser Beam
    message_begin(MSG_BROADCAST, SVC_TEMPENTITY);
    write_byte(TE_BEAMPOINTS);
    write_coord(floatround(m_origin[0]));
    write_coord(floatround(m_origin[1]));
    write_coord(floatround(m_origin[2]));
    write_coord(floatround(m_origin[0]));
    write_coord(floatround(m_origin[1]));
    write_coord(floatround(m_origin[2] - 32.0));
    write_short(g_laserBeamIndex);
    write_byte(0); write_byte(0); write_byte(1); write_byte(8); write_byte(0);
    write_byte(0); write_byte(255); write_byte(255); write_byte(180); write_byte(0);
    message_end();

    // 2. A* Path Laser Beam
    if (g_pathLength > 0 && g_pathIndex < g_pathLength) {
        new next_node = g_currentPath[g_pathIndex];
        message_begin(MSG_BROADCAST, SVC_TEMPENTITY);
        write_byte(TE_BEAMPOINTS);
        write_coord(floatround(m_origin[0]));
        write_coord(floatround(m_origin[1]));
        write_coord(floatround(m_origin[2] + 20.0));
        write_coord(floatround(g_wpOrigin[next_node][0]));
        write_coord(floatround(g_wpOrigin[next_node][1]));
        write_coord(floatround(g_wpOrigin[next_node][2] + 20.0));
        write_short(g_laserBeamIndex);
        write_byte(0); write_byte(0); write_byte(1); write_byte(12); write_byte(0);
        write_byte(255); write_byte(100); write_byte(0); write_byte(220); write_byte(0);
        message_end();
    }

    // 3. Bot State Laser Beams
    for (new b = 1; b <= 32; b++) {
        if (!is_user_connected(b) || !is_user_alive(b) || !is_user_bot(b) || b == g_dummyTBot) continue;
        new Float:b_pos[3];
        entity_get_vector(b, EV_VEC_origin, b_pos);
        new r = 0, g = 255, bl = 0;
        if (g_botState[b] == BOT_STATE_ENGAGE) { r = 255; g = 255; bl = 0; }
        else if (g_botState[b] == BOT_STATE_KITE) { r = 255; g = 140; bl = 0; }
        else if (g_botState[b] == BOT_STATE_PANIC) { r = 255; g = 20; bl = 20; }

        message_begin(MSG_BROADCAST, SVC_TEMPENTITY);
        write_byte(TE_BEAMPOINTS);
        write_coord(floatround(b_pos[0])); write_coord(floatround(b_pos[1])); write_coord(floatround(b_pos[2] + 25.0));
        write_coord(floatround(m_origin[0])); write_coord(floatround(m_origin[1])); write_coord(floatround(m_origin[2] + 45.0));
        write_short(g_laserBeamIndex);
        write_byte(0); write_byte(0); write_byte(1); write_byte(8); write_byte(0);
        write_byte(r); write_byte(g); write_byte(bl); write_byte(160); write_byte(0);
        message_end();
    }

    new t_name[32] = "None";
    if (g_currentTarget > 0 && is_user_connected(g_currentTarget)) {
        get_user_name(g_currentTarget, t_name, charsmax(t_name));
    }

    new Float:monster_feet_z = m_origin[2];
    new Float:player_feet_z  = t_origin[2] - 36.0;
    new Float:z_delta        = floatabs(monster_feet_z - player_feet_z);

    set_hudmessage(0, 255, 120, 0.03, 0.22, 0, 0.0, 0.20, 0.02, 0.02, 2);
    show_hudmessage(0,
        "--- MONSTER HUNT DEBUG ---\n\
        State: %s (Phase %d) | Target: %s (Dist: %.0fu)\n\
        Path: %d/%d nodes | Graph: %d nodes, %d edges\n\
        Last Attack: %s | Flank Count: %d\n\
        Feet Z -> Monster: %.1f | Player: %.1f (Delta: %.1f)",
        g_stateNames[_:g_monsterState], g_currentPhase, t_name, dist,
        g_pathIndex, g_pathLength, g_totalWaypoints, g_totalEdges,
        g_attackNames[_:g_lastAttackUsed], g_flankCounter,
        monster_feet_z, player_feet_z, z_delta
    );
}

// =========================================================================
// FULL SETTINGS SUB-MENU SYSTEM WITH PERSISTENCE (Step 5)
// =========================================================================

public cmd_menu(id) {
    new menu = menu_create("\r[Horror] \yMonster Hunt Control Panel", "menu_main_handler");

    new is_on = get_pcvar_num(g_cvarEnabled);
    new item_mode[96], item_diff[64], item_atmo[64], item_bots[64];

    if (g_modePendingChange) {
        formatex(item_mode, charsmax(item_mode), "\wMode: \y[Monster Hunt (Pending Next Round)]");
    } else if (is_on) {
        formatex(item_mode, charsmax(item_mode), "\wMode: \y[Monster Hunt (ACTIVE)]");
    } else {
        formatex(item_mode, charsmax(item_mode), "\wMode: \d[Regular Match (Standard CS)]");
    }
    menu_additem(menu, item_mode, "1");

    new diff = get_pcvar_num(g_cvarDifficulty);
    new diff_str[32];
    if (diff == 0) copy(diff_str, charsmax(diff_str), "Easy");
    else if (diff == 1) copy(diff_str, charsmax(diff_str), "Normal");
    else if (diff == 2) copy(diff_str, charsmax(diff_str), "Nightmare");
    else copy(diff_str, charsmax(diff_str), "Custom");
    formatex(item_diff, charsmax(item_diff), "\wDifficulty: \y[%s]", diff_str);
    menu_additem(menu, item_diff, "2");

    new atmo = get_pcvar_num(g_cvarAtmosphere);
    new atmo_str[32];
    if (atmo == 2) copy(atmo_str, charsmax(atmo_str), "Heavy (Midnight)");
    else if (atmo == 1) copy(atmo_str, charsmax(atmo_str), "Light (Dusk)");
    else copy(atmo_str, charsmax(atmo_str), "Off (Daylight Normal)");
    formatex(item_atmo, charsmax(item_atmo), "\wAtmosphere: \y[%s]", atmo_str);
    menu_additem(menu, item_atmo, "3");

    new bots_ai = get_pcvar_num(g_cvarBotAI);
    formatex(item_bots, charsmax(item_bots), "\wBots: Fight & Flee: \y[%s]", bots_ai ? "ON" : "OFF");
    menu_additem(menu, item_bots, "4");

    menu_additem(menu, "\wAdvanced Settings (Admins Only) \r>", "5");

    menu_setprop(menu, MPROP_EXIT, MEXIT_ALL);
    menu_display(id, menu, 0);
    return PLUGIN_HANDLED;
}

public menu_main_handler(id, menu, item) {
    if (item == MENU_EXIT) {
        menu_destroy(menu);
        return PLUGIN_HANDLED;
    }

    new bool:is_admin = bool:(get_user_flags(id) & ADMIN_CFG);

    if (item != 4 && !is_admin) {
        client_print_color(id, print_team_red, "^4[Horror] ^1You must be a server admin (^3ADMIN_CFG^1) to change game settings.");
        menu_destroy(menu);
        cmd_menu(id);
        return PLUGIN_HANDLED;
    }

    switch (item) {
        case 0: { // 1. Mode: Regular / Monster Hunt
            if (g_modePendingChange) {
                g_modePendingChange = false;
                client_print_color(0, print_team_blue, "^4[Horror] ^1Queued Monster Hunt startup was cancelled. Regular match continues.");
            } else if (get_pcvar_num(g_cvarEnabled)) {
                set_pcvar_num(g_cvarEnabled, 0);
                restore_team_rules_mode_off();
                remove_monster_entity();
                stop_all_monster_sounds();
                engfunc(EngFunc_LightStyle, 0, "m");
                client_print_color(0, print_team_blue, "^4[Horror] ^1Monster Hunt disabled. Regular Match restored.");
            } else {
                g_modePendingChange = true;
                client_print_color(0, print_team_red, "^4[Horror] ^1Monster Hunt selected by Admin! Takes effect at ^3NEXT ROUND START^1.");
            }
            menu_destroy(menu);
            cmd_menu(id);
            return PLUGIN_HANDLED;
        }
        case 1: { // 2. Difficulty
            new diff = (get_pcvar_num(g_cvarDifficulty) + 1) % 4;
            set_pcvar_num(g_cvarDifficulty, diff);
            apply_difficulty_settings();
            save_settings_to_cfg();
            menu_destroy(menu);
            cmd_menu(id);
            return PLUGIN_HANDLED;
        }
        case 2: { // 3. Atmosphere
            new atmo = (get_pcvar_num(g_cvarAtmosphere) + 1) % 3;
            set_pcvar_num(g_cvarAtmosphere, atmo);
            if (get_pcvar_num(g_cvarEnabled)) {
                if (atmo == 2) engfunc(EngFunc_LightStyle, 0, "b");
                else if (atmo == 1) engfunc(EngFunc_LightStyle, 0, "f");
                else engfunc(EngFunc_LightStyle, 0, "m");
            }
            save_settings_to_cfg();
            menu_destroy(menu);
            cmd_menu(id);
            return PLUGIN_HANDLED;
        }
        case 3: { // 4. Bots Fight & Flee
            new bots = get_pcvar_num(g_cvarBotAI) ? 0 : 1;
            set_pcvar_num(g_cvarBotAI, bots);
            set_pcvar_num(g_cvarBotReact, bots);
            save_settings_to_cfg();
            menu_destroy(menu);
            cmd_menu(id);
            return PLUGIN_HANDLED;
        }
        case 4: { // 5. Advanced Settings
            menu_destroy(menu);
            if (!is_admin) {
                client_print_color(id, print_team_red, "^4[Horror] ^1Advanced settings are restricted to server administrators (^3ADMIN_CFG^1).");
                return PLUGIN_HANDLED;
            }
            menu_advanced(id);
            return PLUGIN_HANDLED;
        }
    }
    menu_destroy(menu);
    return PLUGIN_HANDLED;
}

public menu_advanced(id) {
    new menu = menu_create("\r[Horror] \yAdvanced Configuration (Admins)", "menu_advanced_handler");

    menu_additem(menu, "\wCustom Monster Attributes \r>", "1");
    menu_additem(menu, "\wAdaptive Tracking & Senses \r>", "2");
    menu_additem(menu, "\wKill Abilities & Attacks \r>", "3");
    menu_additem(menu, "\wUI, Comfort & Atmosphere \r>", "4");
    menu_additem(menu, "\wTelemetry & Performance (mh_debug) \r>", "5");
    menu_additem(menu, "\rSpawn Zombie In Front Of Me", "6");
    menu_additem(menu, "\rKill Active Zombie Now", "7");

    menu_setprop(menu, MPROP_EXIT, MEXIT_ALL);
    menu_display(id, menu, 0);
    return PLUGIN_HANDLED;
}

public menu_advanced_handler(id, menu, item) {
    if (item == MENU_EXIT) {
        menu_destroy(menu);
        cmd_menu(id);
        return PLUGIN_HANDLED;
    }

    switch (item) {
        case 0: { menu_destroy(menu); menu_sub_monster(id); return PLUGIN_HANDLED; }
        case 1: { menu_destroy(menu); menu_sub_tracking(id); return PLUGIN_HANDLED; }
        case 2: { menu_destroy(menu); menu_sub_attacks(id); return PLUGIN_HANDLED; }
        case 3: { menu_destroy(menu); menu_sub_atmosphere(id); return PLUGIN_HANDLED; }
        case 4: {
            new dbg = get_pcvar_num(g_cvarDebug) ? 0 : 1;
            set_pcvar_num(g_cvarDebug, dbg);
            client_print_color(id, print_team_default, "^4[Horror] ^1Debug telemetry toggled: ^3%s", dbg ? "ENABLED" : "DISABLED");
            menu_destroy(menu);
            menu_advanced(id);
            return PLUGIN_HANDLED;
        }
        case 5: {
            menu_destroy(menu);
            cmd_spawn_console(id, ADMIN_CFG);
            return PLUGIN_HANDLED;
        }
        case 6: {
            menu_destroy(menu);
            cmd_kill_monster(id, ADMIN_CFG);
            return PLUGIN_HANDLED;
        }
    }
    menu_destroy(menu);
    return PLUGIN_HANDLED;
}

public cmd_modeltest(id) {
    if (!is_user_alive(id)) {
        client_print(id, print_chat, "[Monster Hunt] You must be alive to run the model test.");
        return PLUGIN_HANDLED;
    }

    new ent = create_entity("info_target");
    if (!is_valid_ent(ent)) return PLUGIN_HANDLED;

    entity_set_string(ent, EV_SZ_classname, "monster_model_test");
    entity_set_model(ent, MODEL_ZOMBIE);

    new Float:mins[3] = {-16.0, -16.0, 0.0};
    new Float:maxs[3] = {16.0, 16.0, 72.0};
    entity_set_size(ent, mins, maxs);

    entity_set_int(ent, EV_INT_solid, SOLID_SLIDEBOX);
    entity_set_int(ent, EV_INT_movetype, MOVETYPE_STEP);

    // Clean Default Render Settings (No white tint, no glow shell, scale 1.0)
    entity_set_int(ent, EV_INT_rendermode, kRenderNormal);
    entity_set_int(ent, EV_INT_renderfx, kRenderFxNone);
    entity_set_float(ent, EV_FL_renderamt, 0.0);
    entity_set_vector(ent, EV_VEC_rendercolor, Float:{0.0, 0.0, 0.0});
    entity_set_int(ent, EV_INT_skin, 0);
    entity_set_int(ent, EV_INT_body, 0);
    entity_set_float(ent, EV_FL_scale, 1.0);
    entity_set_int(ent, EV_INT_sequence, 0); // idle1
    entity_set_float(ent, EV_FL_frame, 0.0);
    entity_set_float(ent, EV_FL_framerate, 1.0);
    entity_set_float(ent, EV_FL_animtime, get_gametime());

    new Float:origin[3], Float:fwd[3];
    entity_get_vector(id, EV_VEC_origin, origin);
    velocity_by_aim(id, 85, fwd);
    origin[0] += fwd[0]; origin[1] += fwd[1];
    entity_set_origin(ent, origin);
    engfunc(EngFunc_DropToFloor, ent);

    client_print_color(id, print_team_default, "^4[Monster Hunt] ^1Spawned ^3models/zombie.mdl^1 next to you with clean, default render settings!");
    client_print(id, print_console, "[Monster Hunt] Model Test spawned at (%.1f, %.1f, %.1f). Check textures and lighting.", origin[0], origin[1], origin[2]);
    return PLUGIN_HANDLED;
}

stock menu_sub_monster(id) {
    new menu = menu_create("\r[Horror] \yCustom Monster Attributes", "menu_monster_handler");
    new str[64];

    formatex(str, charsmax(str), "\wHealth: \y[%.0f HP] (Click to cycle)", get_pcvar_float(g_cvarHealth));
    menu_additem(menu, str, "1");
    formatex(str, charsmax(str), "\wSpeed Mult: \y[%.2fx]", get_pcvar_float(g_cvarSpeedMult));
    menu_additem(menu, str, "2");
    formatex(str, charsmax(str), "\wDamage Mult: \y[%.2fx]", get_pcvar_float(g_cvarDamageMult));
    menu_additem(menu, str, "3");
    formatex(str, charsmax(str), "\wDistance Dmg Reduction: \y[%.0f%%]", get_pcvar_float(g_cvarDmgReduction) * 100.0);
    menu_additem(menu, str, "4");

    menu_setprop(menu, MPROP_EXIT, MEXIT_ALL);
    menu_display(id, menu, 0);
}

public menu_monster_handler(id, menu, item) {
    if (item == MENU_EXIT) { menu_destroy(menu); cmd_menu(id); return PLUGIN_HANDLED; }
    if (!(get_user_flags(id) & ADMIN_CFG)) {
        client_print_color(id, print_team_red, "^4[Horror] ^1Admin privileges required.");
        menu_destroy(menu); cmd_menu(id); return PLUGIN_HANDLED;
    }

    switch (item) {
        case 0: {
            new Float:h = get_pcvar_float(g_cvarHealth);
            if (h >= 15000.0) h = 3000.0;
            else h += 2000.0;
            set_pcvar_float(g_cvarHealth, h);
            set_pcvar_num(g_cvarDifficulty, 3);
        }
        case 1: {
            new Float:s = get_pcvar_float(g_cvarSpeedMult) + 0.10;
            if (s > 1.55) s = 0.85;
            set_pcvar_float(g_cvarSpeedMult, s);
            set_pcvar_num(g_cvarDifficulty, 3);
        }
        case 2: {
            new Float:d = get_pcvar_float(g_cvarDamageMult) + 0.15;
            if (d > 1.80) d = 0.80;
            set_pcvar_float(g_cvarDamageMult, d);
            set_pcvar_num(g_cvarDifficulty, 3);
        }
        case 3: {
            new Float:r = get_pcvar_float(g_cvarDmgReduction) + 0.10;
            if (r > 0.55) r = 0.0;
            set_pcvar_float(g_cvarDmgReduction, r);
        }
    }
    save_settings_to_cfg();
    menu_destroy(menu);
    menu_sub_monster(id);
    return PLUGIN_HANDLED;
}

stock menu_sub_tracking(id) {
    new menu = menu_create("\r[Horror] \yAdaptive Tracking & Senses", "menu_tracking_handler");
    new str[64];

    new t_mode = get_pcvar_num(g_cvarTrackingMode);
    formatex(str, charsmax(str), "\wTracking Engine: \y[%s]", t_mode == 0 ? "Fair" : t_mode == 1 ? "Relentless" : "Adaptive");
    menu_additem(menu, str, "1");

    new tgt = get_pcvar_num(g_cvarTargetMode);
    formatex(str, charsmax(str), "\wPrey Selection: \y[%s]", tgt == 0 ? "Nearest" : tgt == 1 ? "Weakest" : tgt == 2 ? "Random" : "Lone Player");
    menu_additem(menu, str, "2");

    formatex(str, charsmax(str), "\wSixth Sense Wall-Awareness: %s", get_pcvar_num(g_cvarSense) ? "\y[ON]" : "\d[OFF]");
    menu_additem(menu, str, "3");

    formatex(str, charsmax(str), "\wHearing Range: \y[%.0fu]", get_pcvar_float(g_cvarHearRange));
    menu_additem(menu, str, "4");

    menu_setprop(menu, MPROP_EXIT, MEXIT_ALL);
    menu_display(id, menu, 0);
}

public menu_tracking_handler(id, menu, item) {
    if (item == MENU_EXIT) { menu_destroy(menu); cmd_menu(id); return PLUGIN_HANDLED; }
    if (!(get_user_flags(id) & ADMIN_CFG)) {
        client_print_color(id, print_team_red, "^4[Horror] ^1Admin privileges required.");
        menu_destroy(menu); cmd_menu(id); return PLUGIN_HANDLED;
    }

    switch (item) {
        case 0: set_pcvar_num(g_cvarTrackingMode, (get_pcvar_num(g_cvarTrackingMode) + 1) % 3);
        case 1: set_pcvar_num(g_cvarTargetMode, (get_pcvar_num(g_cvarTargetMode) + 1) % 4);
        case 2: set_pcvar_num(g_cvarSense, get_pcvar_num(g_cvarSense) ? 0 : 1);
        case 3: {
            new Float:hr = get_pcvar_float(g_cvarHearRange) + 300.0;
            if (hr > 2100.0) hr = 900.0;
            set_pcvar_float(g_cvarHearRange, hr);
        }
    }
    save_settings_to_cfg();
    menu_destroy(menu);
    menu_sub_tracking(id);
    return PLUGIN_HANDLED;
}

stock menu_sub_attacks(id) {
    new menu = menu_create("\r[Horror] \yKill Abilities & Attacks", "menu_attacks_handler");
    new str[64];

    formatex(str, charsmax(str), "\wCombo Melee Finisher: %s", get_pcvar_num(g_cvarAbilityCombo) ? "\y[ON]" : "\d[OFF]");
    menu_additem(menu, str, "1");
    formatex(str, charsmax(str), "\wApex Lunge / Charge: %s", get_pcvar_num(g_cvarAbilityLunge) ? "\y[ON]" : "\d[OFF]");
    menu_additem(menu, str, "2");
    formatex(str, charsmax(str), "\wGround Stomp Shockwave: %s", get_pcvar_num(g_cvarAbilityStomp) ? "\y[ON]" : "\d[OFF]");
    menu_additem(menu, str, "3");
    formatex(str, charsmax(str), "\wRanged Acid Spit: %s", get_pcvar_num(g_cvarAbilityRanged) ? "\y[ON]" : "\d[OFF]");
    menu_additem(menu, str, "4");
    formatex(str, charsmax(str), "\wJumpscare Ambush: %s", get_pcvar_num(g_cvarJumpscare) ? "\y[ON]" : "\d[OFF]");
    menu_additem(menu, str, "5");
    formatex(str, charsmax(str), "\wPhotosensitivity Flash-Safe: %s", get_pcvar_num(g_cvarFlashSafe) ? "\y[SAFE ON]" : "\d[OFF]");
    menu_additem(menu, str, "6");

    menu_setprop(menu, MPROP_EXIT, MEXIT_ALL);
    menu_display(id, menu, 0);
}

public menu_attacks_handler(id, menu, item) {
    if (item == MENU_EXIT) { menu_destroy(menu); cmd_menu(id); return PLUGIN_HANDLED; }
    if (!(get_user_flags(id) & ADMIN_CFG)) {
        client_print_color(id, print_team_red, "^4[Horror] ^1Admin privileges required.");
        menu_destroy(menu); cmd_menu(id); return PLUGIN_HANDLED;
    }

    switch (item) {
        case 0: set_pcvar_num(g_cvarAbilityCombo, get_pcvar_num(g_cvarAbilityCombo) ? 0 : 1);
        case 1: set_pcvar_num(g_cvarAbilityLunge, get_pcvar_num(g_cvarAbilityLunge) ? 0 : 1);
        case 2: set_pcvar_num(g_cvarAbilityStomp, get_pcvar_num(g_cvarAbilityStomp) ? 0 : 1);
        case 3: set_pcvar_num(g_cvarAbilityRanged, get_pcvar_num(g_cvarAbilityRanged) ? 0 : 1);
        case 4: set_pcvar_num(g_cvarJumpscare, get_pcvar_num(g_cvarJumpscare) ? 0 : 1);
        case 5: set_pcvar_num(g_cvarFlashSafe, get_pcvar_num(g_cvarFlashSafe) ? 0 : 1);
    }
    save_settings_to_cfg();
    menu_destroy(menu);
    menu_sub_attacks(id);
    return PLUGIN_HANDLED;
}

stock menu_sub_bots(id) {
    new menu = menu_create("\r[Horror] \yTeammate Bot AI Settings", "menu_bots_handler");
    new str[64];

    formatex(str, charsmax(str), "\wAdvanced Bot Brain: %s", get_pcvar_num(g_cvarBotAI) ? "\y[ON (Kite/Engage)]" : "\d[OFF]");
    menu_additem(menu, str, "1");
    formatex(str, charsmax(str), "\wShared Radio Callouts: %s", get_pcvar_num(g_cvarBotCallouts) ? "\y[ON]" : "\d[OFF]");
    menu_additem(menu, str, "2");
    formatex(str, charsmax(str), "\wCombat Commitment: \y[%.0fs]", get_pcvar_float(g_cvarBotCommitTime));
    menu_additem(menu, str, "3");
    formatex(str, charsmax(str), "\wDanger Kite Distance: \y[%.0fu]", get_pcvar_float(g_cvarBotDangerDist));
    menu_additem(menu, str, "4");

    menu_setprop(menu, MPROP_EXIT, MEXIT_ALL);
    menu_display(id, menu, 0);
}

public menu_bots_handler(id, menu, item) {
    if (item == MENU_EXIT) { menu_destroy(menu); cmd_menu(id); return PLUGIN_HANDLED; }
    if (!(get_user_flags(id) & ADMIN_CFG)) {
        client_print_color(id, print_team_red, "^4[Horror] ^1Admin privileges required.");
        menu_destroy(menu); cmd_menu(id); return PLUGIN_HANDLED;
    }

    switch (item) {
        case 0: set_pcvar_num(g_cvarBotAI, get_pcvar_num(g_cvarBotAI) ? 0 : 1);
        case 1: set_pcvar_num(g_cvarBotCallouts, get_pcvar_num(g_cvarBotCallouts) ? 0 : 1);
        case 2: {
            new Float:ct = get_pcvar_float(g_cvarBotCommitTime) + 2.0;
            if (ct > 14.0) ct = 4.0;
            set_pcvar_float(g_cvarBotCommitTime, ct);
        }
        case 3: {
            new Float:dd = get_pcvar_float(g_cvarBotDangerDist) + 50.0;
            if (dd > 600.0) dd = 300.0;
            set_pcvar_float(g_cvarBotDangerDist, dd);
        }
    }
    save_settings_to_cfg();
    menu_destroy(menu);
    menu_sub_bots(id);
    return PLUGIN_HANDLED;
}

stock menu_sub_atmosphere(id) {
    new menu = menu_create("\r[Horror] \yAtmosphere & Immersion", "menu_atmosphere_handler");
    new str[64];

    formatex(str, charsmax(str), "\wDark Midnight Ambient: %s", get_pcvar_num(g_cvarAtmosphere) ? "\y[DARK]" : "\d[NORMAL]");
    menu_additem(menu, str, "1");
    formatex(str, charsmax(str), "\wProximity Heartbeat: %s", get_pcvar_num(g_cvarHeartbeat) ? "\y[ON]" : "\d[OFF]");
    menu_additem(menu, str, "2");
    formatex(str, charsmax(str), "\wScreen Shake Footsteps: %s", get_pcvar_num(g_cvarScreenShake) ? "\y[ON]" : "\d[OFF]");
    menu_additem(menu, str, "3");
    formatex(str, charsmax(str), "\wFlashlight Panic Flicker: %s", get_pcvar_num(g_cvarFlicker) ? "\y[ON]" : "\d[OFF]");
    menu_additem(menu, str, "4");
    formatex(str, charsmax(str), "\wProximity Danger HUD: %s", get_pcvar_num(g_cvarDangerHud) ? "\y[ON]" : "\d[OFF]");
    menu_additem(menu, str, "5");

    menu_setprop(menu, MPROP_EXIT, MEXIT_ALL);
    menu_display(id, menu, 0);
}

public menu_atmosphere_handler(id, menu, item) {
    if (item == MENU_EXIT) { menu_destroy(menu); cmd_menu(id); return PLUGIN_HANDLED; }
    if (!(get_user_flags(id) & ADMIN_CFG)) {
        client_print_color(id, print_team_red, "^4[Horror] ^1Admin privileges required.");
        menu_destroy(menu); cmd_menu(id); return PLUGIN_HANDLED;
    }

    switch (item) {
        case 0: {
            new a = get_pcvar_num(g_cvarAtmosphere) ? 0 : 1;
            set_pcvar_num(g_cvarAtmosphere, a);
            engfunc(EngFunc_LightStyle, 0, a ? "b" : "m");
        }
        case 1: set_pcvar_num(g_cvarHeartbeat, get_pcvar_num(g_cvarHeartbeat) ? 0 : 1);
        case 2: set_pcvar_num(g_cvarScreenShake, get_pcvar_num(g_cvarScreenShake) ? 0 : 1);
        case 3: set_pcvar_num(g_cvarFlicker, get_pcvar_num(g_cvarFlicker) ? 0 : 1);
        case 4: set_pcvar_num(g_cvarDangerHud, get_pcvar_num(g_cvarDangerHud) ? 0 : 1);
    }
    save_settings_to_cfg();
    menu_destroy(menu);
    menu_sub_atmosphere(id);
    return PLUGIN_HANDLED;
}

stock save_settings_to_cfg() {
    new config_path[128];
    get_configsdir(config_path, charsmax(config_path));
    format(config_path, charsmax(config_path), "%s/monster_hunt.cfg", config_path);

    new fp = fopen(config_path, "w");
    if (!fp) return;

    fprintf(fp, "// ==============================================================================^n");
    fprintf(fp, "// HORROR MONSTER HUNT - DYNAMIC CONFIGURATION (AUTO-SAVED)^n");
    fprintf(fp, "// ==============================================================================^n^n");

    // Always persist mh_enabled 0 so server starts in Regular Match^n    fprintf(fp, "mh_enabled 0^n");
    fprintf(fp, "mh_gamemode %d^n", get_pcvar_num(g_cvarGameMode));
    fprintf(fp, "mh_difficulty %d^n", get_pcvar_num(g_cvarDifficulty));
    fprintf(fp, "mh_monster_health %.0f^n", get_pcvar_float(g_cvarHealth));
    fprintf(fp, "mh_speed_mult %.2f^n", get_pcvar_float(g_cvarSpeedMult));
    fprintf(fp, "mh_damage_mult %.2f^n", get_pcvar_float(g_cvarDamageMult));
    fprintf(fp, "mh_cooldown_mult %.2f^n", get_pcvar_float(g_cvarCooldownMult));
    fprintf(fp, "mh_dmg_reduction %.2f^n", get_pcvar_float(g_cvarDmgReduction));
    fprintf(fp, "mh_target_mode %d^n", get_pcvar_num(g_cvarTargetMode));
    fprintf(fp, "mh_prefer_bots %d^n", get_pcvar_num(g_cvarPreferBots));
    fprintf(fp, "mh_tracking_mode %d^n", get_pcvar_num(g_cvarTrackingMode));
    fprintf(fp, "mh_sight_range %.1f^n", get_pcvar_float(g_cvarSightRange));
    fprintf(fp, "mh_hear_range %.1f^n", get_pcvar_float(g_cvarHearRange));
    fprintf(fp, "mh_sense %d^n", get_pcvar_num(g_cvarSense));
    fprintf(fp, "mh_sense_interval %.1f^n", get_pcvar_float(g_cvarSenseInterval));
    fprintf(fp, "mh_ability_combo %d^n", get_pcvar_num(g_cvarAbilityCombo));
    fprintf(fp, "mh_ability_lunge %d^n", get_pcvar_num(g_cvarAbilityLunge));
    fprintf(fp, "mh_ability_stomp %d^n", get_pcvar_num(g_cvarAbilityStomp));
    fprintf(fp, "mh_ability_ranged %d^n", get_pcvar_num(g_cvarAbilityRanged));
    fprintf(fp, "mh_jumpscare %d^n", get_pcvar_num(g_cvarJumpscare));
    fprintf(fp, "mh_flash_safe %d^n", get_pcvar_num(g_cvarFlashSafe));
    fprintf(fp, "mh_healthbar %d^n", get_pcvar_num(g_cvarHealthBar));
    fprintf(fp, "mh_danger_hud %d^n", get_pcvar_num(g_cvarDangerHud));
    fprintf(fp, "mh_round_summary %d^n", get_pcvar_num(g_cvarRoundSummary));
    fprintf(fp, "mh_bot_react %d^n", get_pcvar_num(g_cvarBotReact));
    fprintf(fp, "mh_bot_ai %d^n", get_pcvar_num(g_cvarBotAI));
    fprintf(fp, "mh_bot_callouts %d^n", get_pcvar_num(g_cvarBotCallouts));
    fprintf(fp, "mh_blood %d^n", get_pcvar_num(g_cvarBlood));
    fprintf(fp, "mh_blood_amount %d^n", get_pcvar_num(g_cvarBloodAmount));
    fprintf(fp, "mh_blood_color %d^n", get_pcvar_num(g_cvarBloodColor));
    fprintf(fp, "mh_atmosphere %d^n", get_pcvar_num(g_cvarAtmosphere));
    fprintf(fp, "mh_heartbeat %d^n", get_pcvar_num(g_cvarHeartbeat));
    fprintf(fp, "mh_screenshake %d^n", get_pcvar_num(g_cvarScreenShake));
    fprintf(fp, "mh_flicker %d^n", get_pcvar_num(g_cvarFlicker));
    fprintf(fp, "mh_pulse %d^n", get_pcvar_num(g_cvarPulse));
    fprintf(fp, "mh_debug %d^n", get_pcvar_num(g_cvarDebug));

    fclose(fp);
}

// Commands
public cmd_spawn_console(id, level) {
    new Float:origin[3], Float:view_ofs[3], Float:fwd_vec[3];
    entity_get_vector(id, EV_VEC_origin, origin);
    entity_get_vector(id, EV_VEC_view_ofs, view_ofs);
    origin[0] += view_ofs[0]; origin[1] += view_ofs[1]; origin[2] += view_ofs[2];

    new Float:angles[3];
    entity_get_vector(id, EV_VEC_v_angle, angles);
    angle_vector(angles, ANGLEVECTOR_FORWARD, fwd_vec);

    origin[0] += fwd_vec[0] * 120.0; origin[1] += fwd_vec[1] * 120.0;
    create_monster_entity(origin);
    console_print(id, "[Monster Hunt] Zombie spawned directly in front of you.");
    return PLUGIN_HANDLED;
}

public cmd_kill_monster(id, level) {
    if (!is_valid_ent(g_monsterEnt)) {
        console_print(id, "[Monster Hunt] No active zombie found.");
        return PLUGIN_HANDLED;
    }
    ExecuteHamB(Ham_Killed, g_monsterEnt, id, 0);
    console_print(id, "[Monster Hunt] Active zombie slain.");
    return PLUGIN_HANDLED;
}

stock set_monster_sequence(ent, seq) {
    if (!is_valid_ent(ent)) return;
    if (entity_get_int(ent, EV_INT_sequence) != seq) {
        entity_set_int(ent, EV_INT_sequence, seq);
        entity_set_float(ent, EV_FL_frame, 0.0);
    }
    entity_set_float(ent, EV_FL_framerate, 1.0);
    entity_set_float(ent, EV_FL_animtime, get_gametime());
}

stock shake_screen(id, Float:amplitude, Float:duration) {
    if (!get_pcvar_num(g_cvarScreenShake)) return;
    static msgScreenShake = 0;
    if (!msgScreenShake) msgScreenShake = get_user_msgid("ScreenShake");
    message_begin(MSG_ONE, msgScreenShake, _, id);
    write_short(floatround(amplitude * 4096.0));
    write_short(floatround(duration * 4096.0));
    write_short(floatround(255.0 * 4096.0));
    message_end();
}

stock shake_all_screens(Float:amplitude, Float:duration) {
    new players[32], count;
    get_players(players, count, "c");
    for (new i = 0; i < count; i++) {
        shake_screen(players[i], amplitude, duration);
    }
}
