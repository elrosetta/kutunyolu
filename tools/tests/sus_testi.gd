extends Node
## Stil v2 süs / toplanabilir / mermi / âlem çekim testi:
##   godot --path . --resolution 1920x1080 -- --stil=v2 --yurt --sus=yurt --cikti=C:/abs/klasor
##   godot --path . --resolution 1920x1080 -- --stil=v2 --sus=dunya --cikti=C:/abs/klasor
## yurt : Bengü yurdun durak noktalarına ışınlanır, her birinde ekran kaydedilir (sus_yurt_<n>.png)
## dunya: toplanabilirler, sunak, totem, mermiler, Kut Kapısı, gök bulutları, ruh taşı ve gizli oda (yeraltı / bu dünya)
## Her karede "[sus] ..." satırı yazar; sonunda çıkar.

var main: Node
var mode := "yurt"
var out_dir := "user://"


func _ready() -> void:
	process_mode = Node.PROCESS_MODE_ALWAYS
	for a in OS.get_cmdline_user_args():
		if String(a).begins_with("--sus="):
			mode = String(a).trim_prefix("--sus=")
		elif String(a).begins_with("--cikti="):
			out_dir = String(a).trim_prefix("--cikti=")
	_run.call_deferred()


func _wait(s: float) -> void:
	await get_tree().create_timer(s, true, false, true).timeout


func _snap(name: String) -> void:
	await RenderingServer.frame_post_draw
	var img := get_viewport().get_texture().get_image()
	if get_viewport().use_hdr_2d:
		if img.get_format() != Image.FORMAT_RGBA8 and img.get_format() != Image.FORMAT_RGB8:
			img.convert(Image.FORMAT_RGBA8)
		img.linear_to_srgb()
	var p := out_dir.path_join("sus_%s.png" % name)
	img.save_png(p)
	print("[sus] kare %s %s" % [name, str(img.get_size())])


func _play() -> void:
	if main and main.get("hud"):
		main.hud.mode = "play"
	get_tree().paused = false


func _tp(pl: Node2D, pos: Vector2) -> void:
	pl.global_position = pos
	pl.velocity = Vector2.ZERO


func _run() -> void:
	await _wait(0.4)
	_play()
	if mode == "yurt":
		await _yurt()
	else:
		await _dunya()
	print("[sus] bitti")
	get_tree().quit()


func _yurt() -> void:
	var lv: Node = main.level
	var pl: Node2D = lv.player
	var i := 0
	for tx in [7, 17, 27, 37, 45, 54, 63, 72, 84]:
		_tp(pl, Vector2(tx * lv.TS, lv.surface_y(tx) * lv.TS - 2))
		pl.set("facing", 1)
		await _wait(1.4)
		_play()
		await _snap("yurt_%d" % i)
		i += 1


func _dunya() -> void:
	var lv: Node = main.level
	var pl: Node2D = lv.player
	# --- toplanabilirler sergisi: oyuncunun önünde düz bir zemin bul
	var tx := 20
	while tx < lv.W - 30:
		var ok := true
		for k in 14:
			if lv.surface_y(tx + k) != lv.surface_y(tx):
				ok = false
				break
		if ok:
			break
		tx += 1
	var gy: float = lv.surface_y(tx) * lv.TS
	_tp(pl, Vector2(tx * lv.TS, gy - 2))
	pl.set("facing", 1)
	var x0: float = tx * lv.TS + 40
	var kinds := ["gold", "kut", "sifa", "tilsim", "parsomen"]
	for k in kinds.size():
		var p := Pickup.new()
		p.kind = kinds[k]
		p.level = lv
		p.position = Vector2(x0 + k * 22, gy - (2 if kinds[k] in ["gold", "kut", "sifa"] else 0))
		if kinds[k] == "tilsim":
			p.pedestal = true
		if kinds[k] == "parsomen":
			p.item_id = "pala"
		lv.add_child(p)
	var it := ItemGen.random_drop(2)
	lv.drop_item(it, Vector2(x0 + 128, gy - 30), true)
	for k2 in ["don", "ruh_kusu"]:
		var q := Pickup.new()
		q.kind = k2
		q.item_id = "kara_boru"
		q.level = lv
		q.position = Vector2(x0 + (160 if k2 == "don" else 190), gy - 26)
		lv.add_child(q)
	var t := Totem.new()
	t.level = lv
	t.life = 30.0
	t.position = Vector2(x0 - 30, gy)
	lv.proj_root.add_child(t)
	await _wait(1.2)
	_play()
	await _snap("toplanir")
	# --- mermiler: havada donmuş sergi
	var specs := [["arrow", ""], ["arrow", "altin"], ["arrow", "od"], ["stone", ""], ["ice", ""], ["fireball", ""], ["spore", ""],
		["curse", ""], ["feather", ""], ["eagle", ""], ["stone_big", ""], ["wave", ""], ["ground_wave", ""]]
	var projs: Array = []
	for k in specs.size():
		var pr := Projectile.new()
		pr.kind = specs[k][0]
		pr.fx_kind = specs[k][1]
		pr.team = "p" if k % 2 == 0 else "e"
		pr.level = lv
		pr.velocity = Vector2(1, -0.15).normalized() * 0.001
		pr.life = 30.0
		if pr.kind in ["arrow", "spore"] or pr.fx_kind != "":
			pr.trail_col = Color(1.0, 0.85, 0.5, 0.8)
		pr.position = Vector2(x0 - 40 + (k % 7) * 40, gy - 70 - int(k / 7) * 40)
		lv.add_projectile(pr)
		projs.append(pr)
	await _wait(0.5)
	_play()
	await _snap("mermi")
	for pr in projs:
		if is_instance_valid(pr):
			pr.queue_free()
	# --- Kut Kapısı
	_tp(pl, lv.exit_pos + Vector2(-90, -2))
	await _wait(1.2)
	_play()
	await _snap("kapi")
	# --- âlemler
	var al: Alem = lv.alem
	if al and not al.clouds.is_empty():
		var c: Vector2 = al.clouds[0]["pos"]
		_tp(pl, c + Vector2(-60, 40))
		await _wait(1.0)
		await _snap("bulut_bu")
		pl.set("kam", 100.0)
		pl.call("_enter_realm", "gok")
		await _wait(1.2)
		await _snap("bulut_gok")
		pl.call("_exit_realm", false, 0.016)
		await _wait(0.6)
	if al and not al.rooms.is_empty():
		var r: Dictionary = al.rooms[0]
		var door: Rect2 = r["door"]
		_tp(pl, Vector2(door.get_center().x - 50, door.position.y - 1))
		await _wait(1.2)
		var gold_before := int(Game.run.get("gold", 0))
		await _snap("oda_bu")
		# ganimet bu dünyadan toplanmamalı (kapağın üstünde dur)
		_tp(pl, Vector2(door.get_center().x, door.position.y - 1))
		await _wait(1.0)
		print("[sus] kapak üstü altın farkı=%d (0 olmalı)" % (int(Game.run.get("gold", 0)) - gold_before))
		pl.set("kam", 100.0)
		pl.call("_enter_realm", "yer")
		await _wait(1.4)
		await _snap("oda_yer")
		await _wait(1.5)
		print("[sus] yeraltında altın farkı=%d (>0 olmalı)" % (int(Game.run.get("gold", 0)) - gold_before))
