extends Node
## v36 ölüm patlaması testi / çekimi (-- --vahset [--vahset_cek=<klasör>] [--vahset_cik]):
##   1) kare şeritleri (0 / 0,05 / 0,1 / 0,2 / 0,4 / 0,8 sn): sıradan, kritik, bitiriş, seçkin öldürüş ve taş yaratık
##      (pencereli koşuda serit_<ad>_<biyom>.jpg; --derinlik ile biyom seçilir);
##      --vahset_boss: kara_boru_han ölüm satırından sonraki dev patlama da çekilir;
##   2) başarım: arenada 40 öldürüş (8'lik dalgalar, aynı karede), her dalgada FPS, kare süresi, Gore zerre / leke sayısı;
##   3) dövüşten sonra oda görüntüsü (lekeler sönüyor mu: oda_<biyom>.jpg).
## Çıktı satırları "[vahset] ..."; headless'ta görüntü alınmaz, ölçümler yine yazılır.

var main: Node
var out_dir := ""
var kinds := ["kara_boru", "surale", "sicrayan_tazi", "karakoncolos", "tosbaga"]


func _ready() -> void:
	process_mode = Node.PROCESS_MODE_ALWAYS
	for arg in OS.get_cmdline_user_args():
		if String(arg).begins_with("--vahset_cek="):
			out_dir = String(arg).trim_prefix("--vahset_cek=")
	_run.call_deferred()


func _process(_d: float) -> void:
	if main and main.level and main.level.player:
		Game.run["hp"] = 100.0
		if "hp" in main.level.player:
			main.level.player.hp = main.level.player.max_hp() if main.level.player.has_method("max_hp") else main.level.player.hp


func _wait(s: float) -> void:
	await get_tree().create_timer(s, true, false, true).timeout


func _clear() -> void:
	for e in get_tree().get_nodes_in_group("dusman"):
		e.queue_free()


func _shot() -> Image:
	if DisplayServer.get_name() == "headless" or out_dir == "":
		return null
	await RenderingServer.frame_post_draw
	return get_viewport().get_texture().get_image()


func _screen_pos(p: Vector2) -> Vector2:
	## dünya → yakalanan görüntü pikseli (kamera merkezi + yakınlaştırma; görünür alandan doku boyuna ölçeklenir)
	var vp := get_viewport()
	var cam: Camera2D = vp.get_camera_2d()
	var vs := vp.get_visible_rect().size
	var q := (p - cam.get_screen_center_position()) * cam.zoom + vs * 0.5 if cam else vp.get_canvas_transform() * p
	return q * (Vector2(vp.get_texture().get_size()) / vs)


func _biyom() -> String:
	return String(main.level.biome.get("id", "otuken"))


func _strip(name: String, kind: String, opts: Dictionary, dmg_k: float, elite := false) -> void:
	var pl: Node2D = main.level.player
	_clear()
	await _wait(0.3)
	var en: Node = main.level.spawn_enemy(kind, pl.global_position + Vector2(70, -2), elite)
	if en == null:
		print("[vahset] %s: yaratık yok" % name)
		return
	en.set_physics_process(false)
	await _wait(0.5)
	en.set_physics_process(true)
	var c: Vector2 = en.center() if en.has_method("center") else en.global_position
	var sp := _screen_pos(c)
	print("[vahset] ekran=%s doku=%s" % [str(sp), str(get_viewport().get_texture().get_size())])
	var ts := [0.0, 0.05, 0.1, 0.2, 0.4, 0.8]
	var frames: Array = []
	var o := opts.duplicate()
	o["dir"] = 1
	var bekle := bool(o.get("_bekle", false))   # boss: ölüm satırından sonraki gecikmeli patlamayı bekle
	o.erase("_bekle")
	var n0 := int(Gore.stats().get("patlama", 0))
	var t0 := Time.get_ticks_msec()
	if o.has("_kesik_sinif"):
		# bitiriş: Player'daki gibi kesik yönü + savurma, sonra kesik ve öldürüş ağır çekimi (_finisher_fx)
		var cls := String(o["_kesik_sinif"])
		o.erase("_kesik_sinif")
		o["kesik_yon"] = KesikFX.ana_yon(cls, 1)
		o["launch"] = float(Player.V35["fin_firlat"])
		en.take_hit(float(en.hp) * dmg_k + 1.0, o)
		KesikFX.bitiris(c, 1, cls, 1.2)
		Game.slowmo(float(Player.V35["olum_yavas"][0]), float(Player.V35["olum_yavas"][1]))
	else:
		en.take_hit(float(en.hp) * dmg_k + 1.0, o)
	if bekle:
		var tb := Time.get_ticks_msec()
		while int(Gore.stats().get("patlama", 0)) == n0 and Time.get_ticks_msec() - tb < 9000:
			await get_tree().process_frame
		print("[vahset] boss gecikmeli patlama: %.2f sn sonra, patlama=%d" % [float(Time.get_ticks_msec() - tb) / 1000.0, int(Gore.stats().get("patlama", 0)) - n0])
		t0 = Time.get_ticks_msec()
	var st := Gore.stats()
	for t in ts:
		# oyun zamanı (vuruş duraksaması / ağır çekim dahil) yerine duvar saati: oyuncunun gördüğü an
		var dt := float(t) - float(Time.get_ticks_msec() - t0) / 1000.0
		if dt > 0.0:
			await _wait(dt)
		var im: Image = await _shot()
		if im:
			frames.append(im)
	print("[vahset] %s %s biyom=%s patlama_sonrasi=%s" % [name, kind, _biyom(), str(st)])
	if frames.is_empty():
		return
	var tex_k: float = float(frames[0].get_width()) / 1920.0
	sp *= float(frames[0].get_width()) / float(get_viewport().get_texture().get_size().x)   # görüntü dokudan küçük olabilir
	var cw := int(400 * tex_k)
	var chh := int(300 * tex_k)
	var strip := Image.create(cw * frames.size(), chh, false, Image.FORMAT_RGBA8)
	for i in frames.size():
		var im2: Image = frames[i]
		im2.convert(Image.FORMAT_RGBA8)
		var r := Rect2i(int(sp.x) - cw / 2, int(sp.y) - chh / 2 - int(30 * tex_k), cw, chh)
		r.position.x = clampi(r.position.x, 0, im2.get_width() - cw)
		r.position.y = clampi(r.position.y, 0, im2.get_height() - chh)
		strip.blit_rect(im2, r, Vector2i(i * cw, 0))
	var k := 2400.0 / float(strip.get_width())
	strip.resize(2400, int(strip.get_height() * k), Image.INTERPOLATE_LANCZOS)
	strip.save_jpg(out_dir.path_join("serit_%s_%s.jpg" % [name, _biyom()]), 0.9)


func _run() -> void:
	await _wait(1.0)
	var pl: Node2D = main.level.player
	var tx := 16
	pl.global_position = Vector2(tx * Level.TS, main.level.surface_y(tx) * Level.TS - 2)
	Game.camera.reset_smoothing.call_deferred()
	await _wait(0.6)
	# 1) şeritler
	await _strip("siradan", "kara_boru", {"kb": 120.0}, 1.0)
	await _strip("kritik", "surale", {"kb": 200.0, "crit": true}, 1.6)
	await _strip("bitiris", "sicrayan_tazi", {"kb": 220.0, "_kesik_sinif": "agir"}, 1.3)
	await _strip("seckin", "kara_boru", {"kb": 200.0, "heavy": true}, 1.5, true)
	await _strip("tas", "balbal", {"kb": 160.0}, 1.2)
	if OS.get_cmdline_user_args().has("--vahset_boss"):
		await _strip("boss", "kara_boru_han", {"kb": 200.0, "crit": true, "_bekle": true}, 40.0)
	await _wait(1.0)
	# 2) başarım: 40 öldürüş
	_clear()
	await _wait(0.3)
	var worst := 0.0
	var n := 0
	for wave in 5:
		var ens: Array = []
		for k in 8:
			var kd: String = kinds[(wave * 8 + k) % kinds.size()] if k != 7 else "bekci"
			var e: Node = main.level.spawn_enemy(kd, pl.global_position + Vector2(-150 + k * 42, -30), false)
			if e:
				ens.append(e)
		await _wait(0.5)
		var t_start := Time.get_ticks_usec()
		var f_start := Engine.get_process_frames()
		for e in ens:
			if is_instance_valid(e) and not e.dead:
				var heavy := (n % 3) == 2
				e.take_hit(float(e.hp) * (1.0 if n % 2 == 0 else 2.2) + 1.0, {"dir": 1 if n % 2 == 0 else -1, "kb": 340.0 if heavy else 140.0, "heavy": heavy, "crit": n % 4 == 1})
				n += 1
				await get_tree().physics_frame
		var mx := 0.0
		var t_prev := Time.get_ticks_usec()
		for f in 90:
			await get_tree().process_frame
			var now := Time.get_ticks_usec()
			mx = maxf(mx, float(now - t_prev) / 1000.0)
			t_prev = now
		worst = maxf(worst, mx)
		var frames := Engine.get_process_frames() - f_start
		var ms := float(Time.get_ticks_usec() - t_start) / 1000.0 / maxf(1.0, float(frames))
		print("[vahset] dalga=%d olum=%d fps=%d ort_kare_ms=%.2f en_kotu_kare_ms=%.2f fizik_ms=%.2f gore=%s" % [wave + 1, n,
			Engine.get_frames_per_second(), ms, mx, Performance.get_monitor(Performance.TIME_PHYSICS_PROCESS) * 1000.0, str(Gore.stats())])
	await _wait(3.0)
	var g := Gore.stats()
	print("[vahset] SON olum=%d en_kotu_kare_ms=%.2f gore=%s nesne=%d" % [n, worst, str(g), int(Performance.get_monitor(Performance.OBJECT_NODE_COUNT))])
	# 3) oda görüntüsü: lekeler sönüyor (ceset yok)
	var im: Image = await _shot()
	if im:
		im.resize(1920, 1080, Image.INTERPOLATE_LANCZOS)
		im.save_jpg(out_dir.path_join("oda_%s.jpg" % _biyom()), 0.88)
	print("[vahset] BITTI")
	if OS.get_cmdline_user_args().has("--vahset_cik"):
		get_tree().quit()
