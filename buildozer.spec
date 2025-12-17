[app]
title = IngilizceOgren
package.name = ingilizceogren
package.domain = org.yunusemre
source.dir = .
source.include_exts = py,kv,json,png,jpg,jpeg,ttf,mp3,wav
version = 0.1

# Kivy + plyer yeterli (fazla bağımlılık ekleme; hata ihtimalini artırır)
requirements = python3,kivy,plyer

orientation = portrait
fullscreen = 0

# Android sürümleri
android.minapi = 21
android.api = 34

# CI'da lisans takılmasın
android.accept_sdk_license = True

# (İleride STT ekleyeceksen)
# android.permissions = RECORD_AUDIO

# Build sistemini sakinleştirir (opsiyonel ama faydalı)
log_level = 2

[buildozer]
log_level = 2
warn_on_root = 1
