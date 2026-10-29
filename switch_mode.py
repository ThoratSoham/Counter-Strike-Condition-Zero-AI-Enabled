import os
import sys

def switch(to_metamod=True):
    liblist_path = os.path.join("czero", "liblist.gam")
    if not os.path.exists(liblist_path):
        print("Error: czero/liblist.gam not found")
        return

    with open(liblist_path, "r", encoding="latin-1") as f:
        content = f.read()

    if to_metamod:
        content = content.replace('gamedll "dlls\\mp.dll"', 'gamedll "addons\\metamod\\dlls\\metamod.dll"')
        content = content.replace('gamedll "dlls/mp.dll"', 'gamedll "addons\\metamod\\dlls\\metamod.dll"')
        print("Switched to Metamod mode (addons\\metamod\\dlls\\metamod.dll)")
    else:
        content = content.replace('gamedll "addons\\metamod\\dlls\\metamod.dll"', 'gamedll "dlls\\mp.dll"')
        content = content.replace('gamedll "addons/metamod/dlls/metamod.dll"', 'gamedll "dlls\\mp.dll"')
        print("Switched to Vanilla mode (dlls\\mp.dll)")

    with open(liblist_path, "w", encoding="latin-1") as f:
        f.write(content)

if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "--vanilla":
        switch(to_metamod=False)
    else:
        switch(to_metamod=True)
