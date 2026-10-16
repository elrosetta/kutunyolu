extends Node
## Yaratık çekim sahnesi (stil v2 yaratık seti B'nin canlı denetimi):
##   godot --path . --write-movie C:/x/f.png --fixed-fps 30 --resolution 1920x1080 --quit-after 1800
##         -- --stil=v2 --yaratik[=tür1,tür2,...] [--yaratik_kurt] [--yaratik_sure=7]
## Her tür için: düşmanlar temizlenir, oyuncunun önüne canlı (yapay zekâlı) bir tane konur; oyuncu ölümsüz, önce bekler
## (yaklaşma, hazırlık, saldırı), sonra iki kez vurur (kalkan / kabuk / yaralanma tepkileri). --yaratik_kurt: sonunda
## Bozkurt biçimi (koşu, ısırık zinciri, sıçrayış, uluma). Çıktıda "[yaratik] tür kare=N ekran=x,y" satırları.

var main: Node
var kinds: Array = ["bekci", "kurgan_bekcisi", "al_atli", "surale", "karakoncolos", "tosbaga", "tas_kertenkele", "buz_tosbagasi",
	"yilan_muhafiz", "simurg_muhafizi", "tamu_bekcisi", "kara_atli", "kurgan_atlisi", "tamu_muhafizi", "kaf_bekcisi"]
var wolf := false
var per := 7.0


func _ready() -> void:
	process_mode = Node.PROCESS_MODE_ALWAYS
	for arg in OS.get_cmdline_user_args():
		var a := String(arg)
		if a.begins_with("--yaratik="):
			kinds = Array(a.trim_prefix("--yaratik=").split(","))
		elif a == "--yaratik_kurt":
			wolf = true
		elif a.begins_with("--yaratik_sure="):
			per = float(a.trim_prefix("--yaratik_sure="))
	_run.call_deferred()


func _process(_d: float) -> void:
	if main and main.level and main.level.player:
		Game.run["hp"] = 100.0


func _wait(s: float) -> void:
	await get_tree().create_timer(s, true, false, false).timeout


func _tap(a: String, hold := 0.06) -> void:
	Input.action_press(a)
	await _wait(hold)
	Input.action_release(a)


func _p(s: String) -> void:
	var sp := Vector2.ZERO
	if main and main.level and main.level.player:
		var pl: Node2D = main.level.player
		var vp := pl.get_viewport()
		sp = pl.get_global_transform_with_canvas().origin * (Vector2(vp.get_window().size) / vp.get_visible_rect().size)
	print("[yaratik] %s kare=%d ekran=%d,%d" % [s, Engine.get_frames_drawn(), int(sp.x), int(sp.y)])


func _clear() -> void:
	for e in get_tree().get_nodes_in_group("dusman"):
		e.queue_free()


func _run() -> void:
	await _wait(1.0)
	var pl: Node = main.level.player
	# duvardan uzaklaş: kamera oyuncuyu ekranın içinde tutsun (düşman sağdan gelir)
	var tx := 16
	pl.global_position = Vector2(tx * Level.TS, main.level.surface_y(tx) * Level.TS - 2)
	Game.camera.reset_smoothing.call_deferred()
	await _wait(0.5)
	if Game.run.has("slots"):
		Game.run["slots"]["melee"] = ItemGen.roll("alp_kilici", 1, "demir", 0)
		pl.on_equip()
	for k in kinds:
		if wolf and k == "-":
			continue
		_clear()
		pl.facing = 1
		var en: Node = main.level.spawn_enemy(String(k), pl.global_position + Vector2(78, -2), false)
		_p(String(k) + " başla")
		await _wait(per * 0.62)
		if is_instance_valid(en) and "hp" in en:
			en.hp = maxf(float(en.hp), 9999.0)
		_p(String(k) + " vuruş")
		for i in 2:
			await _tap("saldiri1")
			await _wait(0.42)
		await _wait(per * 0.38 - 0.96)
	if wolf:
		_clear()
		_p("kurt başla")
		pl.kut = 100.0
		pl.call("_begin_wolf")
		await _wait(1.2)
		var en2: Node = main.level.spawn_enemy("bekci", pl.global_position + Vector2(150, -2), false)
		if is_instance_valid(en2):
			en2.set_physics_process(false)
			en2.hp = 99999.0
		_p("kurt koşu")
		Input.action_press("sag")
		await _wait(0.9)
		Input.action_release("sag")
		_p("kurt ısırık")
		for i in 3:
			await _tap("saldiri1")
			await _wait(0.32)
		await _wait(0.4)
		_p("kurt sıçrayış")
		await _tap("saldiri2")
		await _wait(0.9)
		_p("kurt uluma")
		await _tap("kut")
		await _wait(1.4)
		_p("kurt bitti")
	_p("son")
