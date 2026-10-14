@echo off
rem Kut'un Yolu: projeyi Godot düzenleyicisinde açar.
cd /d "%~dp0"
set GODOT=%~dp0..\godot_engine\Godot_v4.7.2-stable_win64.exe
if not exist "%GODOT%" set GODOT=godot
"%GODOT%" --path "%~dp0" --editor
