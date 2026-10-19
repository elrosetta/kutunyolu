@echo off
rem Kut'un Yolu: oyunu baslatir (Godot 4.7.2 motoru motor klasorunde).
rem Not: klasor yolunda bosluk, parantez "(2)" ya da Turkce harf olabilir; bu yuzden parantezli
rem if bloklarinin icinde yol kullanilmaz (cmd ")" karakterini blogun sonu sanar), goto ile ilerlenir.
chcp 65001 >nul
cd /d "%~dp0"
set "M=%~dp0motor"
set "ZIP=%M%\Godot_v4.7.2-stable_win64.exe.zip"
set "GODOT=%M%\Godot_v4.7.2-stable_win64.exe"
set "GODOTC=%M%\Godot_v4.7.2-stable_win64_console.exe"

rem 1) Motor: motor klasoru (ilk calistirmada zip acilir), yoksa yandaki godot_engine, yoksa PATH
if exist "%GODOT%" goto motor_tamam
if not exist "%ZIP%" goto yan_klasor
echo Oyun motoru ilk kez aciliyor, biraz bekle...
powershell -NoProfile -ExecutionPolicy Bypass -Command "Expand-Archive -Force -LiteralPath $env:ZIP -DestinationPath $env:M"
if exist "%GODOT%" goto motor_tamam
:yan_klasor
set "GODOT=%~dp0..\godot_engine\Godot_v4.7.2-stable_win64.exe"
set "GODOTC=%~dp0..\godot_engine\Godot_v4.7.2-stable_win64_console.exe"
if exist "%GODOT%" goto motor_tamam
where godot >nul 2>nul
if errorlevel 1 goto motor_yok
set "GODOT=godot"
set "GODOTC=godot"
goto motor_tamam
:motor_yok
echo.
echo Godot 4.7.2 bulunamadi.
echo https://godotengine.org/download/archive/ adresinden 4.7.2-stable Windows 64-bit surumunu indir
echo ve Godot_v4.7.2-stable_win64.exe.zip dosyasini acmadan "motor" klasorune koy.
pause
exit /b 1
:motor_tamam
rem 2) Gorseller ve sesler ice aktarilir: ilk calistirmada birkac dakika surer; sonra yalnizca
rem    degisen dosyalar (or. GitHub'dan cekilen yeni surum) islenir. Bu adim atlanirsa oyun bos ekranda kalir.
echo Oyun dosyalari denetleniyor...
"%GODOTC%" --headless --path . --import
start "" "%GODOT%" --path .
