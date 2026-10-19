extends Node
## Efekt vitrini (piksel denetimi önce/sonra çekimleri): oyuncunun çevresine her efekt türünü sabit düzende
## yerleştirir ve ekran görüntüsü alır. Pencereli çalıştırılır:
##   godot --path . -- --pencere=1920x1080 --fx_vitrin=C:/abs/klasor
## Dosyalar: vitrin_<panel>_<n>.png. Yalnızca FX / dünya düğümlerinin herkese açık API'sini kullanır.

var main: Node
var out_dir := "user://"
var pl: Node2D
var lv: Node


func _ready() -> void:
	process_mode = Node.PROCESS_MODE_ALWAYS
	for a in OS.get_cmdline_user_args():
		if String(a).begins_with("--fx_vitrin="):
			out_dir = String(a).trim_prefix("--fx_vitrin=")
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
	img.save_png(out_dir.path_join("vitrin_%s.png" % name))
	print("[vitrin] %s" % name)


func _ground(x: float) -> Vector2:
	var ts := float(Level.TS)
	var tx := int(x / ts)
	return Vector2(x, lv.surface_y(tx) * ts)


func _run() -> void:
	await _wait(0.5)
	main.hud.mode = "play"
	get_tree().paused = false
	lv = main.level
	pl = lv.player
	var ts := float(Level.TS)
	var tx := 6
	pl.global_position = Vector2(tx * ts, lv.surface_y(tx) * ts - 2)
	pl.facing = 1
	Game.camera.reset_smoothing.call_deferred()
	for e in get_tree().get_nodes_in_group("dusman"):
		e.queue_free()
	await _wait(4.5)  # bölüm başlığı sönsün
	pl.set_physics_process(false)
	var gx: float = Game.camera.get_screen_center_position().x
	var c: Vector2 = Vector2(gx, _ground(gx).y - 16.0)
	# --- durum simgeleri ve seçkin yıldızı: iki donmuş düşman
	var e1: Node = lv.spawn_enemy("kara_boru", _ground(gx + 70), true)
	var e2: Node = lv.spawn_enemy("kara_boru", _ground(gx - 70), false)
	await _wait(0.3)
	for e in [e1, e2]:
		if e:
			e.set_physics_process(false)
	if e1:
		e1.burn_t = 9.0
		e1.poison = 3
		e1.bleed = 2
	if e2:
		e2.freeze_t = 9.0
		e2.burn_t = 9.0
	await _wait(0.4)
	# --- A: parçacıklar, kıvılcım, kan, ruh, alev, duman, toz, halka, hız çizgisi, şimşek, yazılar
	FX.sparks(c + Vector2(40, -20), Vector2(1, -0.4), Color(1.0, 0.85, 0.5), 14, 220.0)
	FX.blood(c + Vector2(55, -6), Vector2(1, -0.2), Color(0.75, 0.08, 0.1), 14)
	FX.burst(c + Vector2(-40, -30), Color(1.0, 0.85, 0.4), 14, 90.0)
	FX.soul(c + Vector2(-90, -20), Color(0.6, 1.0, 1.0), 26)
	FX.fire(c + Vector2(100, 6), 8, 0.4, 6.0)
	FX.smoke(c + Vector2(-120, 0), 6, 0.5)
	FX.dust(_ground(gx - 30), Vector2.UP, 8, 0.35)
	FX.ring(c + Vector2(0, -40), 24, Color(1.0, 0.8, 0.5), 0.6)
	FX.streak(c + Vector2(-140, -60), c + Vector2(-40, -70), Color(1.0, 0.95, 0.8), 0.5)
	FX.lightning(c + Vector2(20, -110), c + Vector2(90, -40), Color(0.7, 0.85, 1.0))
	FX.number(c + Vector2(30, -40), 38.0, true)
	FX.number(c + Vector2(-30, -40), 12.0, false)
	FX.text(c + Vector2(0, -60), "Vitrin", Color(1.0, 0.9, 0.6), 9)
	FX.bubbles(c + Vector2(-60, 0), 6)
	FX.frost(c + Vector2(70, -30), 6)
	await _wait(0.1)
	await _snap("a_0")
	await _wait(0.15)
	await _snap("a_1")
	await _wait(1.2)
	# --- B: patlama, yer çarpması, gök gürlemesi, çıkartmalar, alev gölü, kökler, uyarı
	FX.explosion(c + Vector2(-80, 0), 40.0, Color(1.0, 0.85, 0.3), false, Vector2.UP, false)
	FX.ground_slam(_ground(gx + 40), 1, 1.2, Color(1.0, 0.85, 0.6), true, false, false)
	FX.decal("decal_blood_0", _ground(gx + 110) + Vector2(0, 2), 0.0, 10.0, 1.4, Color(0.7, 0.08, 0.1, 0.85))
	FX.decal("decal_crack_1", _ground(gx - 140) + Vector2(0, 2), 0.0, 10.0, 1.2)
	var fp := FirePool.new()
	fp.level = lv
	fp.position = _ground(gx + 150)
	FX.root.add_child(fp)
	var gm := GroundMarker.new()
	gm.life = 3.0
	gm.position = _ground(gx - 30)
	FX.root.add_child(gm)
	await _wait(0.12)
	await _snap("b_0")
	await _wait(0.2)
	await _snap("b_1")
	await _wait(0.5)
	await _snap("b_2")
	await _wait(1.2)
	# --- C: gök gürlemesi, kökler, totem, ölüm (ceset çözülmesi)
	FX.thunder(_ground(gx + 90), 1.0)
	var rs := RootSpikes.new()
	rs.level = lv
	rs.position = _ground(gx - 60)
	FX.root.add_child(rs)
	var tt := Totem.new()
	tt.level = lv
	tt.position = _ground(gx - 130)
	FX.root.add_child(tt)
	if e1 and is_instance_valid(e1):
		e1.set_physics_process(true)
		e1.take_hit(9999.0, {"kb": 160.0, "dir": 1.0})
	await _wait(0.07)
	await _snap("c_0")
	await _wait(0.2)
	await _snap("c_1")
	await _wait(0.6)
	await _snap("c_2")
	print("[vitrin] bitti")
	get_tree().quit()
