#!/usr/bin/env python3
"""Copy iTALC binaries and MinGW/Qt runtime DLLs into dist/."""
import os
import re
import shutil
import subprocess
from pathlib import Path

ROOT = Path(r"D:/Projects/C++/italc-italc3")
BUILD = ROOT / "build"
DIST = ROOT / "dist"
UCRT_BIN = Path(r"C:/msys64/ucrt64/bin")
UCRT_PLUGINS = Path(r"C:/msys64/ucrt64/share/qt5/plugins")

SYSTEM_DLLS = {
    "kernel32.dll", "user32.dll", "gdi32.dll", "shell32.dll", "advapi32.dll",
    "ole32.dll", "oleaut32.dll", "comctl32.dll", "comdlg32.dll", "winmm.dll",
    "ws2_32.dll", "wsock32.dll", "wtsapi32.dll", "netapi32.dll", "userenv.dll",
    "imm32.dll", "version.dll", "iphlpapi.dll", "ntdll.dll", "msvcrt.dll",
    "ucrtbase.dll", "sechost.dll", "rpcrt4.dll", "shlwapi.dll", "crypt32.dll",
    "cryptbase.dll", "bcrypt.dll", "bcryptprimitives.dll", "secur32.dll",
    "sspicli.dll", "dwmapi.dll", "uxtheme.dll", "msimg32.dll", "setupapi.dll",
    "cfgmgr32.dll", "devobj.dll", "hid.dll", "wintrust.dll", "imagehlp.dll",
    "dbghelp.dll", "psapi.dll", "powrprof.dll", "pdh.dll", "dnsapi.dll",
    "mswsock.dll", "wininet.dll", "urlmon.dll", "oleacc.dll", "winhttp.dll",
    "dhcpcsvc.dll", "wldap32.dll", "normaliz.dll", "nsi.dll", "ntmarta.dll",
    "aclui.dll", "authz.dll", "profapi.dll", "kernelbase.dll", "gdi32full.dll",
    "msvcp_win.dll", "win32u.dll", "combase.dll", "shcore.dll",
    "windows.storage.dll", "wintypes.dll", "cryptsp.dll", "rsaenh.dll",
    "gpapi.dll", "cryptnet.dll", "dxgi.dll", "d3d11.dll", "d3d9.dll",
    "opengl32.dll", "glu32.dll", "mpr.dll", "netutils.dll", "srvcli.dll",
    "wkscli.dll", "samcli.dll", "logoncli.dll", "dsrole.dll", "activeds.dll",
    "adsldpc.dll", "ntdsapi.dll", "fwpuclnt.dll", "rasadhlp.dll", "winnsi.dll",
    "winspool.drv", "winbrand.dll", "dsuiext.dll", "netbios.dll", "icmp.dll",
}


def dlls_of(path: Path):
    try:
        out = subprocess.check_output(
            ["objdump", "-p", str(path)],
            stderr=subprocess.DEVNULL,
            text=True,
            errors="ignore",
        )
    except Exception:
        return []
    return re.findall(r"DLL Name:\s+(\S+)", out)


def copy_file(src: Path, dest: Path):
    dest.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(src, dest)


def main():
    if DIST.exists():
        shutil.rmtree(DIST)
    DIST.mkdir(parents=True)

    binaries = [
        BUILD / "ima" / "italc.exe",
        BUILD / "ica" / "ica.exe",
        BUILD / "imc" / "imc.exe",
        BUILD / "lib" / "ItalcCore.dll",
        BUILD / "ica" / "win32" / "authSSP.dll",
        BUILD / "ica" / "win32" / "vnchooks.dll",
    ]
    for src in binaries:
        copy_file(src, DIST / src.name)

    (DIST / "qt.conf").write_text("[Paths]\nPrefix = .\nPlugins = .\n", encoding="utf-8")

    jar = BUILD / "ica" / "JavaViewer" / "VncViewer.jar"
    if jar.exists():
        copy_file(jar, DIST / "JavaViewer" / "VncViewer.jar")
    index = ROOT / "ica" / "JavaViewer" / "index.vnc"
    if index.exists():
        copy_file(index, DIST / "JavaViewer" / "index.vnc")

    # Qt platform/style/imageformat plugins needed to actually show windows
    plugin_map = {
        "platforms": ["qwindows.dll"],
        "styles": ["qwindowsvistastyle.dll"],
        "imageformats": ["qgif.dll", "qico.dll", "qjpeg.dll"],
        "iconengines": ["qsvgicon.dll"],
    }
    for sub, names in plugin_map.items():
        src_dir = UCRT_PLUGINS / sub
        for name in names:
            src = src_dir / name
            if src.exists():
                copy_file(src, DIST / sub / name)

    search_dirs = [UCRT_BIN, DIST]
    queue = list(DIST.rglob("*.exe")) + list(DIST.rglob("*.dll"))
    seen = set()
    copied = []
    missing = []
    while queue:
        current = queue.pop()
        key = current.name.lower()
        if key in seen:
            continue
        seen.add(key)
        for name in dlls_of(current):
            lname = name.lower()
            if lname in SYSTEM_DLLS or lname in seen:
                continue
            dest = DIST / name
            if dest.exists():
                queue.append(dest)
                continue
            src = None
            for folder in search_dirs:
                cand = folder / name
                if cand.exists():
                    src = cand
                    break
            if src:
                copy_file(src, dest)
                copied.append(name)
                queue.append(dest)
            else:
                missing.append(name)

    print("Copied extra DLLs:")
    for name in sorted(copied, key=str.lower):
        print(" ", name)
    if missing:
        print("Unresolved (may be optional/system):")
        for name in sorted(set(missing), key=str.lower):
            print(" ", name)
    print("Dist files:", len(list(DIST.rglob("*"))))


if __name__ == "__main__":
    main()
