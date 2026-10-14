@echo off
rem Kut'un Yolu: oyunu Godot 4.7.2 ile başlatır.
rem Godot bu klasörün yanındaki "godot_engine" klasöründe aranır; yoksa PATH'teki godot kullanılır.
cd /d "%~dp0"
set GODOT=%~dp0..\godot_engine\Godot_v4.7.2-stable_win64.exe
if not exist "%GODOT%" set GODOT=godot
"%GODOT%" --path "%~dp0"
