# Math Wizard -> Android APK

Cross-compile the game with **Buildozer + python-for-android** inside a Docker
image (run from WSL2 on Windows, no Docker Desktop required). The Dockerfile
lives in the repo root; `android/build-apk.sh` builds it and runs Buildozer.

The bundled p4a `pygame` recipe is pygame 2.0.0-dev7 (SDL2), too old for
`pygame.SCALED` and `pygame.cursors.Cursor`. The game therefore uses a
**pygame-ce** recipe placed in `../p4a-recipes/` (loaded via
`p4a.local_recipes` in `buildozer.spec`).

## Prerequisites (already installed on this machine)

- WSL2 with **Ubuntu 24.04** (default user `mario`, systemd enabled).
- Docker CLI + daemon installed **inside WSL** (`/usr/bin/docker`).

## Build — step by step (from the Ubuntu 24.04 WSL terminal)

```bash
# 1) Start the Docker daemon (needs your sudo password, once per boot)
sudo systemctl start docker
#    verify it is up:
docker info --format '{{.ServerVersion}}'

# 2) Get the code. Prefer a git clone (the branch is already pushed):
git clone -b android-apk https://github.com/thefactor82/math-wizard.git ~/math-wizard
cd ~/math-wizard
#    (or copy from Windows: cp -r /mnt/c/Users/mmatteis/Documents/Sources/GitHub/math-wizard ~/math-wizard
#     — a clone into ~/ is faster and more reliable than building on /mnt/c)

# 3) Build the APK (first run: downloads SDK/NDK + compiles, 20-60 min)
android/build-apk.sh

# 4) Copy the APK to Windows and install on the phone
cp bin/*.apk /mnt/c/Users/mmatteis/Downloads/
adb install bin/mathwizard-1.0.008-arm64-v8a-debug.apk   # or install the file manually
```

The script builds the Docker image (`kivy/buildozer-math-wizard`) once, then
runs Buildozer with the SDK/NDK cached in `~/.buildozer`, so later builds are
much faster.

If `docker info` fails after step 1, inspect the service:
`journalctl -u docker --no-pager | tail -20` (and `systemctl status docker`).

### Variants

- Android emulator: set `android.archs = x86_64` in `buildozer.spec`.
- Release/signed: `REL=1 android/build-apk.sh` (add
  `android.release_keystore` to `buildozer.spec` first).

## Android adaptations in the game code

- `PROFILES_DIR` is redirected to the app's private dir when
  `ANDROID_ARGUMENT` is set (the "profiles" folder in CWD is not writable on
  Android).
- `update_ime()` calls `pygame.key.start_text_input()` / `stop_text_input()`
  so the soft keyboard appears while typing answers or a profile name.
- The repo link in the options page is wrapped in try/except (`webbrowser`
  does not work on Android and must not crash the game).

## Troubleshooting

- Build fails on `Cython`/`longintrepr.h`: the Dockerfile pins `Cython<0.30`;
  if a newer p4a requires a newer Cython, bump it but stay `<3.0`.
- Recipe errors (`sdl2_mixer.get_include_dirs`, `ndk_lib_dir_versioned`):
  the p4a version bundled with Buildozer may differ; update Buildozer or the
  recipe in `../p4a-recipes/pygame-ce/__init__.py`.
- "Unable to find main.py": `source.include_exts` in `buildozer.spec` must
  include `py`.
- App closes instantly: check Logcat (`adb logcat`) for a Python traceback.
