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
rem 2) Gorseller ve sesler ice aktarilir: ilk calistirmada bir iki dakika surer; sonra yalnizca
rem    degisen dosyalar (or. GitHub'dan cekilen yeni surum) islenir. Bu adim atlanirsa oyun bos ekranda kalir.
echo Oyun dosyalari denetleniyor...
"%GODOTC%" --headless --path . --import
start "" "%GODOT%" --path .
