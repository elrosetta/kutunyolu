@echo off
rem Kut'un Yolu: oyunu baslatir (Godot 4.7.2 motoru depodaki motor klasorunde).
chcp 65001 >nul
cd /d "%~dp0"
set M=%~dp0motor
set GODOT=%M%\Godot_v4.7.2-stable_win64.exe
set GODOTC=%M%\Godot_v4.7.2-stable_win64_console.exe
rem 1) Motor: depodaki motor klasoru (ilk calistirmada zip acilir), yoksa yandaki godot_engine, yoksa PATH
if not exist "%GODOT%" if exist "%M%\Godot_v4.7.2-stable_win64.exe.zip" (
  echo Oyun motoru ilk kez aciliyor, biraz bekle...
  powershell -NoProfile -ExecutionPolicy Bypass -Command "Expand-Archive -Force -LiteralPath '%M%\Godot_v4.7.2-stable_win64.exe.zip' -DestinationPath '%M%'"
)
if not exist "%GODOT%" (
  set GODOT=%~dp0..\godot_engine\Godot_v4.7.2-stable_win64.exe
  set GODOTC=%~dp0..\godot_engine\Godot_v4.7.2-stable_win64_console.exe
)
if not exist "%GODOT%" (
  set GODOT=godot
  set GODOTC=godot
)
rem 2) Ilk calistirma: gorseller ve sesler ice aktarilir (bir iki dakika surer)
if not exist "%~dp0.godot\imported" (
  echo Oyun dosyalari ilk kez hazirlaniyor, bir iki dakika surebilir...
  "%GODOTC%" --headless --path . --import
)
start "" "%GODOT%" --path .
