extends Node
## v32 ışınlanma testi: godot --headless --path . --quit-after 99999 -- --isinlan [--muhur=0] [--isinlan_tohum=N]
##   Kut Taşı keşfi (yakınından geçince), harita ekranı (Main._harita_ac / _harita_sec), ışınlanma kanalı (konum,
##   dokunulmazlık, kamera), hasarla kanal bozulması, aynı taşa ışınlanma yasağı, sis (keşif yüzdesi), zamanlı kapı
##   (süre dolunca kapanır, içerideyken kapanmaz), bot rehberi yol bulma (LevelGen.path_cells).
## Çıktı "[isinlan] ..." satırları, sonda "[isinlan] SONUC GECTI|KALDI".

var main: Node
var _fail: Array = []


func _ready() -> void:
	process_mode = Node.PROCESS_MODE_ALWAYS
	_run.call_deferred()


func _p(s: String) -> void:
	print("[isinlan] ", s)


func _check(ok: bool, what: String) -> void:
	_p(("TAMAM " if ok else "HATA ") + what)
	if not ok:
		_fail.append(what)


func _phys(n: int) -> void:
	for i in n:
		await get_tree().physics_frame


func _arg_or(name: String, def: String) -> String:
	for a in OS.get_cmdline_user_args():
		if String(a).begins_with(name + "="):
			return String(a).trim_prefix(name + "=")
	return def


func _build(d: int, seed_v: int) -> Node:
	Game.run["depth"] = d
	Game.run["tier"] = Zorluk.kademe(d)
	if main.level:
		main.level.queue_free()
	var lv := Level.new()
	lv.process_mode = Node.PROCESS_MODE_PAUSABLE
	main.add_child(lv)
	main.level = lv
	lv.build(seed_v)
	lv.harita_requested.connect(main._harita_ac)
	main.hud.level = lv
	main.rehber.reset(lv)
	return lv


func _tp(pl: Node, cell: Vector2i) -> void:
	pl.global_position = Vector2(cell.x * Level.TS + Level.TS / 2.0, (cell.y + 1) * Level.TS - 1.0)
	pl.velocity = Vector2.ZERO


func _run() -> void:
	await _phys(5)
	var seed_v := int(_arg_or("--isinlan_tohum", "4242"))
	var lv := _build(1, seed_v)
	main._start_play()
	await _phys(5)
	var pl: Node = lv.player
	for e in get_tree().get_nodes_in_group("dusman"):
		if is_instance_valid(e):
			e.queue_free()   # sessiz bölüm: keşif ve ışınlanma ölçümü
	await _phys(2)
	_p("bölüm stil=%s oda=%d taşı=%d zamanlı=%d spawn=%s" % [lv.style, lv.rooms.size(), lv.tasi.size(), lv.zamanli.size(), str(lv.spawn_cell)])
	_check(lv.harita != null, "harita kuruldu")
	_check(lv.tasi.size() >= 3 and lv.tasi.size() <= 6, "bölümde 3-6 Kut Taşı (%d)" % lv.tasi.size())
	_check(lv.harita.bulunan().is_empty(), "başta bulunmuş taş yok")
	var y0: float = lv.harita.yuzde()
	_check(y0 > 0.0 and y0 < 0.3, "başta sis: keşif %%%.1f (0 < k < 30)" % (y0 * 100.0))
	# --- keşif: giriş taşının yanına yürü
	var t0: Node = lv.tasi[0]
	_tp(pl, lv.harita.tasi[0]["cell"] + Vector2i(-2, 0))
	await _phys(6)
	_check(t0.bulundu and lv.harita.bulunan() == [0], "yakınından geçince taş keşfedildi (bulunan=%s)" % str(lv.harita.bulunan()))
	# ikinci taş: uzağa ışınla (test), keşfet
	var c1: Vector2i = lv.harita.tasi[1]["cell"]
	_tp(pl, c1 + Vector2i(1, 0))
	await _phys(6)
	_check(lv.harita.bulunan().size() == 2, "ikinci taş keşfedildi (bulunan=%d)" % lv.harita.bulunan().size())
	_check(lv.harita.goruldu(c1.x, c1.y) and lv.harita.goruldu(lv.harita.tasi[0]["cell"].x, lv.harita.tasi[0]["cell"].y), "iki taşın çevresi haritada görüldü")
	var y1: float = lv.harita.yuzde()
	_check(y1 > y0, "keşif yüzdesi arttı (%%%.1f -> %%%.1f)" % [y0 * 100.0, y1 * 100.0])
	# --- aynı taşa ışınlanma yasak (taş 1'in dibindeyiz)
	_check(lv.tasi_yakin() == 1, "taşın dibinde (yakın=%d)" % lv.tasi_yakin())
	_check(not lv.isinlan(1), "dibindeki taşa ışınlanma reddedilir")
	_check(not lv.isinlan(2), "bulunmamış taşa ışınlanma reddedilir")
	# --- harita ekranı: aç, seç, ışınlan
	main._harita_ac()
	await _phys(2)
	_check(main.hud.mode == "harita" and get_tree().paused, "M: harita ekranı açıldı, oyun durdu")
	var found: Array = lv.harita.bulunan()
	main._harita_sec(found.find(0))
	await _phys(1)
	_check(main.hud.mode == "play" and not get_tree().paused and lv.isin_t > 0.0, "seçim: harita kapandı, kanal başladı (%.2f sn)" % lv.isin_t)
	var p_before: Vector2 = pl.global_position
	await _phys(int(ceil(lv.ISIN_SURE * 60.0)) + 6)
	var c0: Vector2i = lv.harita.tasi[0]["cell"]
	var hedef := Vector2(c0.x * Level.TS + Level.TS / 2.0, (c0.y + 1) * Level.TS)
	var d: float = pl.global_position.distance_to(hedef)
	_check(lv.isin_t <= 0.0 and lv.isin_sayi == 1, "kanal bitti, ışınlanma sayıldı (%d)" % lv.isin_sayi)
	_check(d < 40.0, "oyuncu taş 0'a vardı (uzaklık %.0f px; önce %s)" % [d, str(p_before.round())])
	_check(float(pl.inv_t) > 0.0, "varışta dokunulmazlık (%.2f sn)" % float(pl.inv_t))
	_check(pl.is_on_floor() or lv.cell(int(pl.global_position.x / Level.TS), int((pl.global_position.y + 4.0) / Level.TS)) != 0, "varışta yerde")
	var cam_d: float = Game.camera.global_position.distance_to(pl.global_position)
	_check(cam_d < 320.0, "kamera oyuncuya atladı (%.0f px)" % cam_d)
	# --- hasar kanalı bozar
	await _phys(int(ceil(float(pl.inv_t) * 60.0)) + 5)
	_check(lv.isinlan(1), "kanal 2 başladı")
	await _phys(10)
	var hp0 := float(Game.run["hp"])
	pl.inv_t = 0.0
	pl.take_hit(3.0, null, null, true)
	await _phys(2)
	_check(float(Game.run["hp"]) < hp0 and lv.isin_t <= 0.0 and lv.isin_bozuk == 1, "darbe kanalı bozdu (bozuk=%d, can %.0f -> %.0f)" % [lv.isin_bozuk, hp0, float(Game.run["hp"])])
	_check(pl.global_position.distance_to(hedef) < 60.0, "bozulan kanal: oyuncu yerinde kaldı")
	# --- bot rehberi yol bulur
	var s := LevelGen.stand_cell(lv.grid, Level.W, Level.H, pl.global_position.x, pl.global_position.y, Level.TS)
	var path := LevelGen.path_cells(lv.grid, Level.W, Level.H, s.x, s.y, lv.exit_cell.x, lv.exit_cell.y)
	_check(not path.is_empty(), "rehber: girişten Kut Kapısı'na hücre yolu (%d adım)" % path.size())
	var n_odul := 0
	var n_yol := 0
	for rm in lv.rooms:
		if rm["role"] != "odul":
			continue
		n_odul += 1
		var sp: Vector2i = LevelGen._floor_spot(lv.grid, Level.W, Level.H, rm, LevelGen._odul_mid(rm))
		var p2 := LevelGen.path_cells(lv.grid, Level.W, Level.H, s.x, s.y, sp.x, sp.y)
		if not p2.is_empty():
			n_yol += 1
	_check(n_odul >= 2 and n_yol == n_odul, "her ödül odasına yol var (%d / %d)" % [n_yol, n_odul])
	# --- zamanlı kapı (varsa; yoksa bulana dek başka tohum)
	var zl: Node = null
	var tries := 0
	while zl == null and tries < 12:
		if not lv.zamanli.is_empty():
			zl = lv.zamanli[0]
			break
		tries += 1
		lv = _build(1 + tries % 5, seed_v + 17 * tries)
		main._start_play()
		await _phys(3)
		pl = lv.player
	if zl == null:
		_p("zamanlı kapı bulunamadı (12 tohum)")
	else:
		_p("zamanlı kapı tohum=%d hücre=%s süre=%.0f" % [seed_v + 17 * tries, str(zl.cell), zl.sure])
		_check(zl.acik and zl.etiket().ends_with("sn"), "başta açık, etiket süre (%s)" % zl.etiket())
		# dışarıdayken süre dolar: kapanır
		Game.run["bolum_sure"] = zl.sure + 1.0
		_tp(pl, lv.spawn_cell)
		await _phys(4)
		_check(not zl.acik, "süre dolunca kapı kapandı")
		var katı := true
		for y in range(zl.cell.y - 4, zl.cell.y):
			katı = katı and lv.cell(zl.cell.x, y) == 1
		_check(katı, "kapı geçidi katı karo oldu (ızgara + karo katmanı)")
		# içerideyken: kazanıldı, kapanmaz
		var lv2 := _build(1, seed_v + 17 * tries)
		main._start_play()
		await _phys(3)
		if not lv2.zamanli.is_empty():
			var z2: Node = lv2.zamanli[0]
			_tp(lv2.player, Vector2i(z2.cell.x + z2.ic_yon * 4, z2.cell.y - 1))
			await _phys(4)
			_check(z2.kazanildi, "zamanında girince kazanıldı")
			Game.run["bolum_sure"] = z2.sure + 1.0
			await _phys(4)
			_check(z2.acik, "kazanılmış kapı kapanmaz")
	_p("SONUC %s%s" % ["GECTI" if _fail.is_empty() else "KALDI", "" if _fail.is_empty() else " (" + ", ".join(_fail) + ")"])
	get_tree().quit()
