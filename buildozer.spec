[app]
title = Math Wizard
package.name = mathwizard
package.domain = org.mathwizard

# Directory / files packaged into the APK.
source.dir = .
source.include_exts = py,png,jpg,jpeg,json,ttf,otf,cur
version = 1.0.008

# pygame-ce is required: the built-in p4a "pygame" recipe is pygame 2.0.0-dev7
# which does not support pygame.SCALED / cursors.Cursor. The recipe lives in
# p4a-recipes/ and is picked up via p4a.local_recipes.
requirements = python3,pygame-ce
p4a.local_recipes = p4a-recipes

orientation = landscape
fullscreen = 1

# arm64-v8a = real phones. Use x86_64 instead to run on an Android emulator.
android.archs = arm64-v8a
android.minapi = 21

# If the build fails on SDK/NDK version, pin these to match your Buildozer/p4a:
# android.api = 34
# android.ndk = 25b

[buildozer]
log_level = 2
warn_on_root = 1
