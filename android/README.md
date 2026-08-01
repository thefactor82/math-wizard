# Math Wizard -> Android APK

Cross-compile the game with **Buildozer + python-for-android** inside a Docker
image (run from Windows via WSL2 / Docker Desktop). The Dockerfile lives in the
repo root; `android/build-apk.sh` builds it and runs Buildozer.

The bundled p4a `pygame` recipe is pygame 2.0.0-dev7 (SDL2), too old for
`pygame.SCALED` and `pygame.cursors.Cursor`. The game therefore uses a
**pygame-ce** recipe placed in `../p4a-recipes/` (loaded via
`p4a.local_recipes` in `buildozer.spec`).

## One-time setup (on Windows)

1. Docker Desktop running with the WSL2 backend (WSL2 distro: Ubuntu 24.04).
2. In WSL2: `git` available (Ubuntu has it by default).

## Build

From a WSL2 shell in the repo root:

```bash
android/build-apk.sh
```

- First run downloads the Android SDK/NDK and compiles everything
  (20-60 min). The cache lives in `~/.buildozer` so later builds are fast.
- Output: `bin/mathwizard-1.0.008-arm64-v8a-debug.apk`
- Copy to Windows: `cp bin/*.apk /mnt/c/Users/<you>/Downloads/` and install
  the APK on the phone (or `adb install bin/*.apk`).
- Android emulator: set `android.archs = x86_64` in `buildozer.spec`.
- Release/signed: `REL=1 android/build-apk.sh` (add `android.release_keystore`
  to `buildozer.spec` first).

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
