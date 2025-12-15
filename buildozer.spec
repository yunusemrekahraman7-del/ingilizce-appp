[app]
title = IngilizceOgren
package.name = ingilizceogren
package.domain = org.yunusemre
source.dir = .
source.include_exts = py,kv,json,png,jpg,jpeg,ttf,mp3,wav
version = 0.1
requirements = python3,kivy,plyer
orientation = portrait
fullscreen = 0

# (İleride speech-to-text eklenirse açılır)
# android.permissions = RECORD_AUDIO

# Android uyumluluk
android.minapi = 21
android.api = 34

[buildozer]
log_level = 2
warn_on_root = 1
