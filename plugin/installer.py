import os
import shutil

AI_TEAMMATES_HEADER = "// --- AI TEAMMATES MOD CONFIG ---"

BOT_PROFILES_APPEND = """
// --- AI TEAMMATES MOD BOT PROFILES ---
Elite+Rifle Vikram
	Skin = 2
	VoicePitch = 96
End

Expert+Punch Kabir
	Skin = 4
	VoicePitch = 100
End

Elite+Sniper Marcus
	Skin = 3
	VoicePitch = 88
End

Normal+Spray Sunny
	Skin = 1
	VoicePitch = 105
End
"""

CFG_COMMANDS = """
// --- AI TEAMMATES MOD CONFIG ---
log on
mp_logdetail 3
mp_logecho 1
mp_logfile 1
logaddress_delall
logaddress_add 127.0.0.1 27115
rcon_password "czeroai"
bot_chatter "off"
bot_defer_to_human 1
"""

def setup_game_directory(czero_dir="czero"):
    """
    Sets up Metamod, AMX Mod X, plugin registrations, BotProfile.db,
    and server logging configs for Condition Zero.
    """
    if not os.path.exists(czero_dir):
        print(f"[Installer] Error: Directory '{czero_dir}' does not exist.")
        return False

    base_dir = os.path.dirname(os.path.abspath(czero_dir)) if os.path.isabs(czero_dir) else "."

    # 1. Update liblist.gam to load Metamod
    liblist_path = os.path.join(czero_dir, "liblist.gam")
    if os.path.exists(liblist_path):
        with open(liblist_path, "r", encoding="latin-1") as f:
            content = f.read()
        if "addons\\metamod\\dlls\\metamod.dll" not in content and "addons/metamod/dlls/metamod.dll" not in content:
            content = content.replace('gamedll "dlls\\mp.dll"', 'gamedll "addons\\metamod\\dlls\\metamod.dll"')
            content = content.replace('gamedll "dlls/mp.dll"', 'gamedll "addons\\metamod\\dlls\\metamod.dll"')
            with open(liblist_path, "w", encoding="latin-1") as f:
                f.write(content)
            print(f"[Installer] Updated {liblist_path} to hook Metamod.")

    # 2. Ensure metamod/plugins.ini loads AMX Mod X
    meta_plugins_ini = os.path.join(czero_dir, "addons", "metamod", "plugins.ini")
    os.makedirs(os.path.dirname(meta_plugins_ini), exist_ok=True)
    meta_content = ""
    if os.path.exists(meta_plugins_ini):
        with open(meta_plugins_ini, "r") as f:
            meta_content = f.read()
    if "amxmodx_mm.dll" not in meta_content:
        with open(meta_plugins_ini, "a") as f:
            f.write("\nwin32 addons\\amxmodx\\dlls\\amxmodx_mm.dll\n")
        print(f"[Installer] Registered AMX Mod X in {meta_plugins_ini}.")

    # 3. Ensure amxmodx/configs/plugins.ini loads czero_ai_teammates.amxx and disables broken statsx
    amx_plugins_ini = os.path.join(czero_dir, "addons", "amxmodx", "configs", "plugins.ini")
    if os.path.exists(amx_plugins_ini):
        with open(amx_plugins_ini, "r") as f:
            amx_p_content = f.read()
        updated_ini = False
        if "\nstatsx.amxx" in amx_p_content:
            amx_p_content = amx_p_content.replace("\nstatsx.amxx", "\n;statsx.amxx")
            updated_ini = True
        if "czero_ai_teammates.amxx" not in amx_p_content:
            amx_p_content += "\n; AI Teammates Mod Plugin\nczero_ai_teammates.amxx\n"
            updated_ini = True
        if updated_ini:
            with open(amx_plugins_ini, "w") as f:
                f.write(amx_p_content)
            print(f"[Installer] Updated {amx_plugins_ini}.")

    # 4. Copy compiled .amxx plugin if exists in scripting or compiled
    src_amxx = os.path.join(czero_dir, "addons", "amxmodx", "scripting", "czero_ai_teammates.amxx")
    if not os.path.exists(src_amxx):
        src_amxx = os.path.join(czero_dir, "addons", "amxmodx", "scripting", "compiled", "czero_ai_teammates.amxx")
    dst_amxx = os.path.join(czero_dir, "addons", "amxmodx", "plugins", "czero_ai_teammates.amxx")
    if os.path.exists(src_amxx):
        os.makedirs(os.path.dirname(dst_amxx), exist_ok=True)
        shutil.copyfile(src_amxx, dst_amxx)
        print(f"[Installer] Copied plugin {src_amxx} -> {dst_amxx}")

    # 5. Update listenserver.cfg
    listenserver_path = os.path.join(czero_dir, "listenserver.cfg")
    cfg_content = ""
    if os.path.exists(listenserver_path):
        with open(listenserver_path, "r", encoding="latin-1") as f:
            cfg_content = f.read()

    if AI_TEAMMATES_HEADER not in cfg_content:
        with open(listenserver_path, "a", encoding="latin-1") as f:
            f.write("\n" + CFG_COMMANDS.strip() + "\n")
        print(f"[Installer] Configured {listenserver_path}.")

    # 6. Update BotProfile.db
    botprofile_path = os.path.join(czero_dir, "BotProfile.db")
    if os.path.exists(botprofile_path):
        with open(botprofile_path, "r", encoding="latin-1") as f:
            bp_content = f.read()
        if "Vikram" not in bp_content:
            with open(botprofile_path, "a", encoding="latin-1") as f:
                f.write("\n" + BOT_PROFILES_APPEND.strip() + "\n")
            print(f"[Installer] Injected bot profiles into {botprofile_path}.")

    # 7. Create logs folder
    os.makedirs(os.path.join(base_dir, "logs"), exist_ok=True)

    print("[Installer] Condition Zero setup completed successfully!")
    return True

if __name__ == "__main__":
    setup_game_directory()
