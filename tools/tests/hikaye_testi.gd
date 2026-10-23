extends Node
## v42 Güneş Ana hikâyesi testi / çekimi:
##   godot --path . --quit-after 99999 -- --hikaye_test [--hikaye_cikti=<mutlak klasör>] [--pencere=1920x1080 --grafik=2]
## Sırayla: açılış sineması (6 panel), bölüm görümü + bölüm sahnesi (bitig taşı okunur), hikâye odası görümü, beş boss'un
## Gün Örgüsü (düşer → oyuncuya akar → kalıcı kayıt + görüm + ufuk ısınır), yurtta altın yapraklar (3 örgü) ve tan
## sökmüş yurt, son sineması + jenerik, konakta yoldaşlar ve hizmet ekranları (Umay / Ozan / Demirci / Alp Ata / Usta).
## Headless'ta çekim atlanır, denetimler yine çalışır. Kalıcı kaydın hikâye alanları test sonunda geri yazılır.

var main: Node
var _ok := 0
var _fail := 0
var _out := ""
var _yedek: Dictionary = {}


func _ready() -> void:
	process_mode = Node.PROCESS_MODE_ALWAYS
	for a in OS.get_cmdline_user_args():
		if String(a).begins_with("--hikaye_cikti="):
			_out = String(a).trim_prefix("--hikaye_cikti=")
	if _out != "":
		DirAccess.make_dir_recursive_absolute(_out)
	for k in ["gun_parca", "gorumler", "giris_izlendi", "son_izlendi", "kut_bank", "runs", "wins"]:
		_yedek[k] = Game.meta.get(k)
	_run.call_deferred()


func _p(s: String) -> void:
	print("[hikaye] " + s)


func _check(ok: bool, what: String) -> void:
	if ok:
		_ok += 1
		_p("OK   " + what)
	else:
		_fail += 1
		_p("HATA " + what)


func _frames(n: int) -> void:
	for i in n:
		await get_tree().process_frame


func _sn(s: float) -> void:
	await get_tree().create_timer(s, true, false, true).timeout


func _cek(ad: String) -> void:
	if _out == "" or DisplayServer.get_name() == "headless":
		return
	await RenderingServer.frame_post_draw
	var img := get_viewport().get_texture().get_image()
	if img == null or img.is_empty():
		return
	if get_viewport().use_hdr_2d:
		if img.get_format() != Image.FORMAT_RGBA8 and img.get_format() != Image.FORMAT_RGB8:
			img.convert(Image.FORMAT_RGBA8)
		img.linear_to_srgb()
	img.save_png(_out.path_join(ad + ".png"))
	_p("çekim " + ad)


func _bekle_metin(m: String, en_cok: float) -> bool:
	var t := 0.0
	while t < en_cok:
		if Gorum.inst.son_metin == m:
			return true
		await _sn(0.2)
		t += 0.2
	return false


func _meta_kur(parca: Array, son := false) -> void:
	Game.meta["gun_parca"] = parca.duplicate()
	Game.meta["son_izlendi"] = son
	Game.meta["gorumler"] = []


func _run() -> void:
	await _frames(4)
	_meta_kur([])
	await _sinema("giris", 6)
	await _bolum()
	await _orguler()
	await _yurt()
	await _sinema("son", 5)
	await _konak()
	# kalıcı kaydı geri yaz
	for k in _yedek:
		if _yedek[k] == null:
			Game.meta.erase(k)
		else:
			Game.meta[k] = _yedek[k]
	Game.save_meta()
	_p("SONUC %d OK, %d HATA" % [_ok, _fail])
	get_tree().quit()


# ------------------------------------------------------------------ sinema
func _sinema(tur: String, beklenen: int) -> void:
	get_tree().paused = true
	main.hud.mode = "sinema"
	var s: Sinema = Sinema.oynat(main, tur)
	await _frames(3)
	_check(s.paneller.size() == beklenen, "%s sineması %d panel (%d)" % [tur, beklenen, s.paneller.size()])
	var dokular := 0
	for k in s.paneller.size():
		await _frames(1)
		if s._ust.texture != null:
			dokular += 1
		# panel tam açılsın, yazı bitsin
		s.t = Sinema.YAZI_GECIKME + float(s._harf_sayi()) / Sinema.HARF_HIZ + 0.6
		await _sn(0.35)
		await _cek("%s_%d" % [tur, k + 1])
		if k == 0:
			# ara kare: panel mürekkeple belirirken (ilk panel, yarı yolda)
			pass
		s._sonraki()
	_check(dokular == beklenen, "%s panellerinin dokuları yüklü (%d / %d)" % [tur, dokular, beklenen])
	if tur == "son":
		_check(s._jenerik, "son: jenerik başladı")
		s._jt = 5.2
		await _sn(0.3)
		await _cek("son_jenerik")
	var bitti := [false]
	s.bitti.connect(func() -> void: bitti[0] = true)
	s._bitir()
	await _sn(2.0)
	_check(bitti[0] and not is_instance_valid(s), "%s sineması bitti sinyali, düğüm silindi" % tur)
	main._start_play()


# ------------------------------------------------------------------ bölüm: görüm, sahne, hikâye odası
func _bolum() -> void:
	Game.new_run()
	Game.run["depth"] = 1
	main._build_level()
	main._start_play()
	await _frames(5)
	var lv: Level = main.level
	var hs: HikayeSahne = null
	for c in lv.get_children():
		if c is HikayeSahne:
			hs = c
	_check(hs != null, "bölümde HikayeSahne kuruldu")
	if hs == null:
		return
	_check(hs.sahne_kuruldu, "bölüm sahnesi (sahne_yeri) kuruldu: %s" % str(lv.sahne_yeri))
	_check(hs.gorum_plan > 0.0, "Ötüken'e ilk giriş görümü planlandı")
	var g0: int = Gorum.inst.gosterilen
	await _sn(2.2)
	await _cek("bolum_afis")
	await _sn(4.8)
	_check(Gorum.inst.gosterilen > g0, "biyom görümü oynadı: «%s»" % Gorum.inst.son_metin)
	_check(Hikaye.gorum_goruldu("biyom:otuken"), "biyom görümü kalıcı kayda işlendi")
	await _sn(1.8)
	await _cek("gorum")
	await _sn(4.0)
	# bitig taşı: oyuncu yanına
	if not hs._taslar.is_empty():
		var p: Vector2 = hs._taslar[0][0]
		lv.player.global_position = p + Vector2(-20, -4)
		lv.player.velocity = Vector2.ZERO
		await _sn(0.8)
		_check(hs.okunan > 0, "bitig taşı okundu: «%s»" % String(hs._taslar[0][1]))
		await _cek("sahne_bitig")
	if hs.sahne_merkez != Vector2.INF:
		lv.player.global_position = hs.sahne_merkez + Vector2(-70, -4)
		lv.player.velocity = Vector2.ZERO
		await _sn(0.8)
		await _cek("sahne")
	# hikâye odası: zorla açık bölüm
	var bulundu := false
	for sd in [11, 12, 13, 14, 15, 16]:
		Game.run["depth"] = 2
		var sv := 0
		for k in 30:
			if HikayeSahne.oda_acik(2, sd * 100 + k):
				sv = sd * 100 + k
				break
		if main.level:
			main.level.queue_free()
		var l2 := Level.new()
		l2.process_mode = Node.PROCESS_MODE_PAUSABLE
		main.add_child(l2)
		main.level = l2
		l2.build(sv)
		main.hud.level = l2
		await _frames(4)
		if not l2.hikaye_yeri.is_empty():
			bulundu = true
			break
	_check(bulundu, "hikâye odası (opts.hikaye_odasi) üretildi: %s" % str(main.level.hikaye_yeri))
	if bulundu:
		var lv2: Level = main.level
		var hs2: HikayeSahne = null
		for c in lv2.get_children():
			if c is HikayeSahne:
				hs2 = c
		_check(hs2 != null and hs2.oda_kuruldu, "hikâye odası sahnesi kuruldu")
		var g1: int = Gorum.inst.gosterilen
		lv2.player.global_position = hs2._oda + Vector2(-50, -4)
		lv2.player.velocity = Vector2.ZERO
		await _sn(2.4)
		_check(Gorum.inst.gosterilen > g1, "hikâye odasında Gün Ana görümü: «%s»" % Gorum.inst.son_metin)
		await _cek("hikaye_odasi")
		await _sn(5.0)


# ------------------------------------------------------------------ boss örgüleri
func _orguler() -> void:
	_meta_kur([])
	var depths := {"kara_boru_han": 2, "tepegoz": 4, "sahmeran": 6, "yelbegen": 8, "erlik_han": 10}
	for bid in Hikaye.ORGU_SIRA:
		Game.new_run()
		Game.run["depth"] = int(depths[bid])
		main._build_boss(bid)
		main._start_play()
		var soz_ok: bool = await _bekle_metin(Hikaye.boss_soz(bid, "once"), 4.0)
		_check(soz_ok, "%s kükreyince sözü: «%s»" % [bid, Gorum.inst.son_metin])
		var lv: Level = main.level
		var b: Enemy = lv.boss
		lv.player.global_position = Vector2(b.global_position.x - 120.0, lv.player.global_position.y)
		var n0 := Hikaye.parca_sayi()
		lv._on_boss_died(b)
		b.queue_free()
		await _frames(2)
		var gp: GunParcasi = null
		for c in lv.get_children():
			if c is GunParcasi:
				gp = c
		_check(gp != null, "%s: Gün Örgüsü düştü (%s)" % [bid, String(Hikaye.orgu(bid).get("ad", ""))])
		var gor_ok: bool = await _bekle_metin(String(Hikaye.orgu(bid).get("gorum", "")), 8.0)
		_check(Hikaye.parca_var(bid) and Hikaye.parca_sayi() == n0 + 1, "%s: örgü alındı, kalıcı kayıt %d örgü" % [bid, Hikaye.parca_sayi()])
		_check(gor_ok, "%s: örgü görümü oynadı (son: «%s», sıra %d, şimdiki %s)" % [bid, Gorum.inst.son_metin, Gorum.inst._kuyruk.size(), str(Gorum.inst._cur.get("tur", "-"))])
		await _sn(1.6)
		await _cek("orgu_%s" % bid)
		if bid == "erlik_han":
			# son sineması kendiliğinden başlar (6,5 sn sonra)
			await _sn(6.0)
			_check(main.sinema != null, "Erlik'in Altın Örgüsü son sinemasını başlattı")
			if main.sinema != null:
				main.sinema._bitir()
				await _sn(1.2)
			_check(Hikaye.safak() and main.level.hub, "son: tan söktü, yeni koşu sabah yurdunda")
			_meta_kur(Hikaye.ORGU_SIRA.duplicate(), false)
		else:
			await _sn(4.0)


# ------------------------------------------------------------------ yurt
func _yurt() -> void:
	for durum in [[3, false, "yurt_3_orgu"], [5, true, "yurt_sabah"]]:
		_meta_kur(Hikaye.ORGU_SIRA.slice(0, int(durum[0])), bool(durum[1]))
		Game.new_run()
		main._build_hub()
		main._start_play()
		await _frames(4)
		var lv: Level = main.level
		var yap := 0
		for c in lv.decor_root.get_children():
			if c is Sprite2D and (c as Sprite2D).texture != null and String((c as Sprite2D).texture.resource_path).contains("altin_yaprak"):
				yap += 1
		_check(yap >= int(durum[0]) * 7, "yurt: Ulu Kayın'da %d altın yaprak (%d örgü)" % [yap, int(durum[0])])
		_check(absf(float(lv.vig_mat.get_shader_parameter("safak")) - (1.5 if durum[1] else Hikaye.safak_k())) < 0.01, "yurt: ufuk sıcaklığı %.2f" % float(lv.vig_mat.get_shader_parameter("safak")))
		lv.player.global_position = lv._hub_px(19.0, -4.0)
		await _sn(2.0)
		await _cek(String(durum[2]))


# ------------------------------------------------------------------ konak
func _konak() -> void:
	_meta_kur(["kara_boru_han", "tepegoz"])
	Game.new_run()
	Game.run["depth"] = 3
	Game.run["gold"] = 400
	Level.bezirgan_zorla = true
	main._build_konak()
	main._start_play()
	await _frames(5)
	var lv: Level = main.level
	var ids: Array = []
	for n in lv.npcs:
		ids.append(String(n.id))
	for want in ["umay", "ozan", "demirci", "alp_ata", "usta"]:
		_check(want in ids, "konakta %s var" % want)
	_check(lv.bezirgan != null, "konakta Bezirgân (zorla)")
	var sozlu := 0
	for n in lv.npcs:
		if String(n.soz) != "":
			sozlu += 1
	_check(sozlu == lv.npcs.size(), "konak yoldaşlarının hepsinin hikâye sözü var (%d)" % sozlu)
	# ateş başı çekimi: oyuncu ocak ile Ozan arasında
	lv.player.global_position = lv._hub_px(22.0, -4.0) + Vector2(60, 0)
	await _sn(1.5)
	for n in lv.npcs:
		if n.id == "ozan":
			lv.player.global_position = n.global_position + Vector2(-22, -2)
	await _sn(0.5)
	await _cek("konak")
	var bek := {"umay": "umay", "ozan": "ozan", "demirci": "demirci", "alp_ata": "sanat", "usta": "usta"}
	for id in bek:
		lv.npc_requested.emit(id)
		await _frames(3)
		_check(main.hud.mode == bek[id] and get_tree().paused, "konakta %s hizmeti açıldı (%s)" % [id, main.hud.mode])
		if id == "ozan":
			_check(Hikaye.ozan_sayfalari().size() >= 2, "Ozan destan özeti %d sayfa" % Hikaye.ozan_sayfalari().size())
			await _sn(0.4)
			await _cek("konak_ozan")
		main._start_play()
		await _frames(2)
	# geniş konak görüntüsü: kamera ortada
	lv.player.global_position = lv._hub_px(36.0, -4.0)
	await _sn(1.2)
	await _cek("konak_genis")
	Level.bezirgan_zorla = false
