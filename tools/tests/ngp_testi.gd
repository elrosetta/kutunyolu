extends Node
## v44 Mühür yolu (NG+) testi / çekimi:
##   godot --path . --quit-after 99999 -- --ngp [--ngp_cikti=<mutlak klasör>] [--pencere=1920x1080 --grafik=2]
## Sırayla: kayıt göçü (v44 öncesi kayıt), Erlik'i 0..4. mühürde yenince bir sonrakinin açılışı (zafer kaydı, emanet,
## tören kartı, zafer özeti, yurtta taşın töreni ve yuvaları), Mühür Taşı ekranı (seçim, koşuya uygulama), kurallar
## (I hazırlık, II damgalı seçkinler + Kalkanlı / Bölünen davranışı, III sis + sönen taşlar, IV Tamu bekçileri + kor
## yağmuru, V boss Zincir evresi), ödüller (nadirlik tabanı, Kut çarpanı, emanet düşüşü, Han Otağı), Bengü'nün süsü,
## Beşinci Mühürde gerçek son ve kayıtlar. Headless'ta çekim atlanır, denetimler yine çalışır. Kalıcı kayıt sonunda
## olduğu gibi geri yazılır.

var main: Node
var _ok := 0
var _fail := 0
var _out := ""
var _yedek: Dictionary = {}


func _ready() -> void:
	process_mode = Node.PROCESS_MODE_ALWAYS
	for a in OS.get_cmdline_user_args():
		if String(a).begins_with("--ngp_cikti="):
			_out = String(a).trim_prefix("--ngp_cikti=")
	if _out != "":
		DirAccess.make_dir_recursive_absolute(_out)
	_yedek = Game.meta.duplicate(true)
	_run.call_deferred()


func _p(s: String) -> void:
	print("[ngp] " + s)


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


func _taze_meta() -> void:
	## Tan sökmüş, beş örgü alınmış, boss kartları görülmüş; mühür yolu sıfır
	Game.meta["son_izlendi"] = true
	Game.meta["gun_parca"] = Hikaye.ORGU_SIRA.duplicate()
	Game.meta["boss_kart"] = {"kara_boru_han": 3, "tepegoz": 3, "sahmeran": 3, "yelbegen": 3, "erlik_han": 3}
	Game.meta["muhur_acik"] = 0
	Game.meta["muhur"] = 0
	for k in ["muhur_kayit", "muhur_emanet", "muhur_emanet_bulunan", "muhur_sus", "gercek_son", "muhur_toren", "muhur_surum"]:
		Game.meta.erase(k)
	Game.meta["muhur_surum"] = MuhurYolu.SURUM
	MuhurYolu.meta_hazirla()


func _run() -> void:
	await _frames(4)
	Zorluk.set_muhur(-1)
	await _goc()
	_taze_meta()
	await _acilis_akisi()
	await _tas_ekrani()
	await _kurallar()
	await _oduller()
	await _sus()
	await _gercek_son()
	_kayitlar()
	# kalıcı kaydı geri yaz
	Zorluk.set_muhur(-1)
	MuhurYolu.test_tamu_zorla = false
	Game.meta = _yedek
	Game.save_meta()
	_p("SONUC %d OK, %d HATA" % [_ok, _fail])
	get_tree().quit()


# ------------------------------------------------------------------ kayıt göçü
func _goc() -> void:
	var eski := Game.meta.duplicate(true)
	Game.meta = {"runs": 12, "wins": 3, "kut_bank": 40, "unlocked": [], "blueprints": [], "best_depth": 10, "muhur_acik": 2, "muhur": 2}
	MuhurYolu.meta_hazirla()
	_check(MuhurYolu.zafer_var(0) and MuhurYolu.zafer_var(1) and not MuhurYolu.zafer_var(2), "göç: açılmış mühürlerin altı zafer sayıldı (0, 1)")
	_check("tan_kilici" in MuhurYolu.emanet_acik() and "halka_pencesi" in MuhurYolu.emanet_acik() and MuhurYolu.emanet_acik().size() == 2, "göç: açılmış mühürlerin emanetleri (%s)" % str(MuhurYolu.emanet_acik()))
	_check(int(Game.meta.get("muhur_toren", 0)) == -1 and int(Game.meta.get("muhur_surum", 0)) == MuhurYolu.SURUM, "göç: tören yok, sürüm 44")
	MuhurYolu.meta_hazirla()
	_check(int(MuhurYolu.kayit(0).get("zafer", 0)) == 1, "göç iki kez çalışınca değer bozulmaz")
	Game.meta = eski
	await _frames(1)


# ------------------------------------------------------------------ açılış akışı (0 → 5)
func _erlik_yen(n: int, sure := 600.0) -> Level:
	Game.meta["muhur"] = n
	Game.new_run()
	Game.run["depth"] = 10
	Game.run["time"] = sure
	main._build_boss("erlik_han")
	main._start_play()
	await _frames(3)
	var lv: Level = main.level
	Game.run["hp"] = 99999.0
	Game.run["max_hp"] = 99999.0
	var b: Enemy = lv.boss
	lv._on_boss_died(b)
	b.dead = true
	b.queue_free()
	await _frames(2)
	return lv


func _acilis_akisi() -> void:
	for n in 5:
		var bank0 := int(Game.meta.get("kut_bank", 0))
		var lv := await _erlik_yen(n, 900.0 - n * 30.0)
		_check(Zorluk.muhur() == n, "%d. mühürde koşu (Game.run.muhur)" % n)
		_check(Zorluk.muhur_acik() == n + 1 and int(Game.run.get("muhur_yeni", -1)) == n + 1, "Erlik %s ile yenildi → %s açıldı" % [MuhurYolu.ad(n), MuhurYolu.ad(n + 1)])
		_check(Zorluk.muhur_secili() == n + 1, "yeni mühür bir sonraki koşuda takılı")
		var em := String(MuhurYolu.odul(n + 1).get("emanet", ""))
		_check(em in MuhurYolu.emanet_acik(), "emanet açıldı: %s" % String(MuhurYolu.emanet_def(em).get("ad", "")))
		_check(int(MuhurYolu.kayit(n).get("zafer", 0)) == 1 and absf(float(MuhurYolu.kayit(n).get("en_iyi", 0.0)) - (900.0 - n * 30.0)) < 2.0, "kayıt: zafer 1, en iyi süre %s" % MuhurYolu.sure_yazi(float(MuhurYolu.kayit(n).get("en_iyi", 0.0))))
		var ilk := int(MuhurYolu.odul(n).get("ilk_zafer", 0))
		_check(int(Game.meta.get("kut_bank", 0)) - bank0 == ilk, "ilk zafer Kut'u +%d" % ilk)
		# kapıdan geçiş: tören kartı → zafer özeti → yurt
		await _sn(1.8)
		main._on_finished()
		await _frames(3)
		var kart: bool = main.sinema != null and main.sinema.ad == "muhur_toren"
		_check(kart, "%s: tören kartı oynadı" % MuhurYolu.ad(n + 1))
		if kart:
			var s: Sinema = main.sinema
			if n == 2:
				s.git(s.cekim_basi(0) + 3.0)
				await _sn(0.25)
				await _cek("toren_1_halka")
				s.git(s.cekim_basi(1) + 3.2)
				await _sn(0.35)
				await _cek("toren_2_muhur")
			s._bitir()
			await _sn(1.4)
		_check(main.hud.mode == "zafer", "zafer özeti açıldı (%s)" % main.hud.mode)
		var mb: Dictionary = DerinlikUI.son_ozet.get("mb", {})   # v44 birleştirme: tek özet (KosuOzet) mühür bilgisini taşır
		_check(bool(DerinlikUI.son_ozet.get("zafer", false)) and int(mb.get("n", -1)) == n and int(mb.get("yeni", -1)) == n + 1, "koşu özeti zaferi ve mühür bilgisini taşıyor (%s → %s)" % [MuhurYolu.ad(n), MuhurYolu.ad(int(mb.get("yeni", -1)))])
		if n == 2:
			await _sn(0.4)
			await _cek("zafer_ozeti")
		main._zafer_bitir()
		await _frames(4)
		var hub: Level = main.level
		var tas: MuhurTasi = null
		for np in hub.npcs:
			if np is MuhurTasi:
				tas = np
		_check(hub.hub and tas != null, "yurtta Mühür Taşı var")
		_check(tas != null and tas.toren == n + 1, "taşta %s töreni başladı" % MuhurYolu.ad(n + 1))
		if tas != null:
			hub.player.global_position = tas.global_position + Vector2(-58, -4)
			hub.player.facing = 1
			Game.camera.reset_smoothing.call_deferred()
			if n == 4:
				await _sn(1.7)
				await _cek("tas_toren_inis")
			var t := 0.0
			while not tas.toren_bitti and t < 6.0:
				await _sn(0.2)
				t += 0.2
			_check(tas.toren_bitti and int(Game.meta.get("muhur_toren", 0)) == -1, "tören bitti, yuvaya oturdu (kalıcı)")
		_check(int(Game.run.get("max_flasks", 0)) == maxi(1, 2 + Game.umay_level("sise") + Zorluk.sise_ek()), "yeni koşu %s ile (şişe %d)" % [MuhurYolu.ad(Zorluk.muhur()), int(Game.run.get("max_flasks", 0))])
	_check(Zorluk.muhur_acik() == 5, "beş mühür açık")
	main.hud._card_t = 99.0
	await _sn(0.6)
	await _cek("tas_bes_muhur")
	# yakın çekim: kamera taşa yaklaşır
	var z0: float = Game.base_zoom
	Game.base_zoom = z0 * 1.9
	for np in main.level.npcs:
		if np is MuhurTasi:
			main.level.player.global_position = np.global_position + Vector2(-46, -4)
	Game.camera.reset_smoothing.call_deferred()
	await _sn(0.8)
	await _cek("tas_yakin")
	Game.base_zoom = z0


# ------------------------------------------------------------------ Mühür Taşı ekranı
func _tas_ekrani() -> void:
	var hub: Level = main.level
	if not hub.hub:
		main._build_hub()
		main._start_play()
		await _frames(3)
		hub = main.level
	hub.npc_requested.emit("muhur_tasi")
	await _frames(3)
	_check(main.hud.mode == "muhur" and get_tree().paused, "Mühür Taşı ekranı açıldı")
	main.hud.sel = 3
	await _sn(0.5)
	await _cek("tas_ekrani_3")
	main.hud.sel = 5
	await _sn(0.2)
	await _cek("tas_ekrani_5")
	# Boşluk: seçili mühür takılır ve yurttaki koşuya hemen uygulanır
	main.hud.sel = 3
	var ev := InputEventAction.new()
	ev.action = "zipla"
	ev.pressed = true
	MuhurUI.girdi(main, ev, true)
	_check(Zorluk.muhur_secili() == 3 and int(Game.run.get("muhur", -1)) == 3, "Üçüncü Mühür takıldı, koşuya uygulandı")
	_check(int(Game.run.get("flasks", 0)) == maxi(1, 2 + Game.umay_level("sise") - 1), "şişe sayısı mührün cezasıyla (%d)" % int(Game.run.get("flasks", 0)))
	var ev2 := InputEventAction.new()
	ev2.action = "duraklat"
	ev2.pressed = true
	MuhurUI.girdi(main, ev2, false)
	_check(main.hud.mode == "play" and not get_tree().paused, "Esc ile ekrandan çıkıldı")
	# kapıdan geçiş: koşunun mührü kesinleşir, deneme sayılır
	var d0 := int(MuhurYolu.kayit(3).get("deneme", 0))
	MuhurYolu.kosu_basla()
	_check(int(MuhurYolu.kayit(3).get("deneme", 0)) == d0 + 1 and Zorluk.muhur() == 3, "kapıda mühür kesinleşti, deneme sayıldı")


# ------------------------------------------------------------------ kurallar
func _bolum(n: int, d: int) -> Level:
	Zorluk.set_muhur(n)
	Game.new_run()
	Game.run["depth"] = d
	Game.run["tier"] = Zorluk.kademe(d)
	Game.run["hp"] = 99999.0
	Game.run["max_hp"] = 99999.0
	main._build_level()
	main._start_play()
	await _frames(4)
	return main.level


func _damgali(lv: Level) -> Array:
	var out: Array = []
	for e in lv.get_tree().get_nodes_in_group("dusman"):
		if e.has_meta("muhur_damga"):
			out.append(e)
	return out


func _kurallar() -> void:
	# I: Kısa Uyarı
	Zorluk.set_muhur(0)
	var h0 := Zorluk.hazirlik(3)
	Zorluk.set_muhur(1)
	_check(absf(Zorluk.hazirlik(3) - h0 * 1.1) < 0.001, "I Kısa Uyarı: hazırlık ×1,1 (%.3f → %.3f)" % [h0, Zorluk.hazirlik(3)])
	# II: damgalı seçkinler
	var lv := await _bolum(2, 3)
	var sec := 0
	var damgali := 0
	for e in lv.get_tree().get_nodes_in_group("dusman"):
		if e.elite:
			sec += 1
			if e.has_meta("muhur_damga") and (e.get_meta("muhur_damga") as MuhurDamga).turler.size() == 1:
				damgali += 1
	_check(sec > 0 and damgali == sec, "II Erlik Damgası: %d seçkinin %d'i tek damgalı" % [sec, damgali])
	# Kalkanlı: önden gelen vuruş kesilir, arkadan tam
	var pl: Node = lv.player
	var e1: Enemy = lv.spawn_enemy("kara_boru", pl.global_position + Vector2(90, -2), false, false, true)
	if e1 == null:
		e1 = lv.spawn_enemy("kara_boru", pl.global_position + Vector2(60, -40), false, false, false)
	await _frames(2)
	var dk := MuhurDamga.ekle(e1, ["kalkanli"])
	await _frames(1)
	e1.max_hp = 10000.0
	e1.hp = 10000.0
	e1.facing = -1
	var hp0 := e1.hp
	e1.take_hit(100.0, {"dir": 1.0, "kb": 0.0})   # önden (yüzü sola, vuruş sağa doğru: ön)
	var on_k := (hp0 - e1.hp) / 100.0
	e1.broken_t = 0.0
	var hp1 := e1.hp
	e1.facing = -1
	e1.take_hit(100.0, {"dir": -1.0, "kb": 0.0})   # arkadan
	var arka_k := (hp1 - e1.hp) / 100.0
	_check(on_k < 0.5 and arka_k > 0.8, "Kalkanlı: önden ×%.2f, arkadan ×%.2f" % [on_k, arka_k])
	for i in 6:
		e1.facing = -1
		e1.take_hit(1.0, {"dir": 1.0, "kb": 0.0})
	_check(dk.kalkan == 0, "Kalkanlı: ön vuruşlarla kalkan kırıldı")
	# Bölünen: iki yavru
	var say0 := lv.get_tree().get_nodes_in_group("dusman").size()
	var e2: Enemy = lv.spawn_enemy("kara_boru", pl.global_position + Vector2(-90, -2), false, false, true)
	if e2 == null:
		e2 = lv.spawn_enemy("kara_boru", pl.global_position + Vector2(-60, -40), false, false, false)
	await _frames(2)
	MuhurDamga.ekle(e2, ["bolunen"])
	await _frames(1)
	e2.take_hit(99999.0, {"dir": 1.0, "kb": 50.0})
	await _frames(4)
	var say1 := lv.get_tree().get_nodes_in_group("dusman").size()
	_check(say1 - say0 == 2, "Bölünen: ölünce iki yavru (%d → %d)" % [say0, say1])
	# III: Erlik'in Sisi
	lv = await _bolum(3, 3)
	var top_tasi: int = (lv._gen.get("tasi", []) as Array).size()
	_check(lv.harita._sis < 0.99 and lv.tasi.size() < top_tasi, "III Erlik'in Sisi: görüş ×%.2f, Kut Taşı %d / %d" % [lv.harita._sis, lv.tasi.size(), top_tasi])
	var lv0 := await _bolum(0, 3)
	_check((lv0._gen.get("tasi", []) as Array).size() == lv0.tasi.size() and is_equal_approx(lv0.harita._sis, 1.0), "mühürsüzde bütün taşlar yanar (%d)" % lv0.tasi.size())
	# IV: Tamu bekçileri + seçkinde iki damga
	MuhurYolu.test_tamu_zorla = true
	lv = await _bolum(4, 3)
	MuhurYolu.test_tamu_zorla = false
	var tamu: Array = []
	var cift := 0
	sec = 0
	for e in _damgali(lv):
		var dm: MuhurDamga = e.get_meta("muhur_damga")
		if dm.has("tamu"):
			tamu.append(e)
	for e in lv.get_tree().get_nodes_in_group("dusman"):
		if e.elite:
			sec += 1
			if e.has_meta("muhur_damga") and (e.get_meta("muhur_damga") as MuhurDamga).turler.size() == 2:
				cift += 1
	_check(tamu.size() >= 1 and tamu.size() <= 2, "IV Tamu bekçileri: bölümde %d bekçi (en çok 2)" % tamu.size())
	_check(sec > 0 and cift == sec, "IV: %d seçkinin %d'i iki damgalı" % [sec, cift])
	if not tamu.is_empty():
		var tb: Enemy = tamu[0]
		var tdm: MuhurDamga = tb.get_meta("muhur_damga")
		_check(tb.max_hp > 0.0 and tb.base_tint.r > 1.2, "Tamu bekçisi: kor kızılı mürekkep, dayanıklı")
		# oyuncunun yanına al, kor yağmurunu bekle (bölüm afişi kapalı)
		main.hud._card_t = 99.0
		pl = lv.player
		tb.global_position = pl.global_position + Vector2(170, -4)
		tb.state = "chase"
		tdm._atis = 0.2
		Game.camera.reset_smoothing.call_deferred()
		var t := 0.0
		var cekildi := false
		while tdm.atis_sayisi == 0 and t < 6.0:
			await _sn(0.1)
			t += 0.1
			if tdm._hazir > 0.45 and not cekildi:
				cekildi = true
				await _cek("tamu_bekcisi_hazirlik")
		await _sn(0.25)
		await _cek("tamu_bekcisi_kor")
		_check(tdm.atis_sayisi >= 1, "Tamu bekçisi kor yağmuru attı (%d)" % tdm.atis_sayisi)
	# V: Zincir evresi
	Zorluk.set_muhur(5)
	Game.new_run()
	Game.run["depth"] = 4
	Game.run["hp"] = 99999.0
	Game.run["max_hp"] = 99999.0
	main._build_boss("tepegoz")
	main._start_play()
	await _frames(3)
	var blv: Level = main.level
	var ev: MuhurEvre = blv.boss.get_meta("muhur_evre") if blv.boss.has_meta("muhur_evre") else null
	_check(ev != null, "V Zincir evresi: boss'a evre kuruldu")
	if ev != null:
		await _sn(2.5)
		_check(not ev.etkin, "evre canın %40'ına dek uyur")
		blv.boss.hp = blv.boss.max_hp * 0.35
		blv.player.global_position = Vector2(blv.boss.global_position.x - 200.0, blv.player.global_position.y)
		var t2 := 0.0
		var cek2 := false
		var cek3 := false
		main.hud._card_t = 99.0
		while (ev.inen < 2 or not cek3) and t2 < 12.0:
			await _sn(0.05)
			t2 += 0.05
			if ev.etkin and not ev._vuruslar.is_empty():
				var u: float = ev._t - float(ev._vuruslar[0][2])
				if not cek2 and u > 0.55 and u < MuhurEvre.HAZIR:
					cek2 = true
					await _cek("zincir_evresi_uyari")
				elif cek2 and not cek3 and u > MuhurEvre.HAZIR + MuhurEvre.INIS and u < MuhurEvre.HAZIR + MuhurEvre.INIS + 0.2:
					cek3 = true
					await _cek("zincir_evresi_inis")
		_check(ev.etkin and ev.inen >= 2, "Zincir evresi: evre başladı, %d zincir indi" % ev.inen)
	Zorluk.set_muhur(0)
	Game.new_run()
	main._build_boss("tepegoz")
	await _frames(2)
	_check(not main.level.boss.has_meta("muhur_evre"), "mühürsüzde boss'ta evre yok")
	main._start_play()


# ------------------------------------------------------------------ ödüller
func _oduller() -> void:
	Game.new_run()
	Zorluk.set_muhur(0)
	var en_az0 := 9
	for i in 200:
		en_az0 = mini(en_az0, int(ItemGen.random_drop(1).get("rarity", 0)))
	Zorluk.set_muhur(3)
	var en_az3 := 9
	var ort3 := 0.0
	for i in 200:
		var r := int(ItemGen.random_drop(1).get("rarity", 0))
		en_az3 = mini(en_az3, r)
		ort3 += r / 200.0
	_check(en_az0 == 0 and en_az3 >= 1, "nadirlik tabanı: mühürsüz en az %d, Üçüncü Mühür en az %d (ort %.2f)" % [en_az0, en_az3, ort3])
	Zorluk.set_muhur(5)
	var top := 0
	for i in 4000:
		top += MuhurYolu.kut_tane()
	_check(absf(top / 4000.0 - 1.8) < 0.06, "Kut çarpanı (V): ortalama %.2f (beklenen 1,8)" % (top / 4000.0))
	_check(MuhurYolu.altin(10) == 15, "altın çarpanı (V): 10 → %d" % MuhurYolu.altin(10))
	# emanet: koşunun ilk bekçisinden kesin
	Game.new_run()
	Game.meta["muhur_emanet_bulunan"] = []
	var it := MuhurYolu.boss_esya(3)
	_check(it.has("emanet") and int(it.get("rarity", 0)) == 3 and int(it.get("quality", 0)) == 100, "ilk bekçi emanet düşürdü: %s" % String(it.get("name", "")))
	_check(String(ItemGen.describe(it)[0]).begins_with("◆") and String(it.get("name", "")) == String(MuhurYolu.emanet_def(String(it["emanet"])).get("ad", "")), "emanet kartı: sabit ad ve emanet satırı")
	_check(Unsur.of(it) != "", "emanetin unsuru var (%s)" % Unsur.of(it))
	Zorluk.set_muhur(1)
	var h1 := MuhurYolu.emanet_havuz()
	_check(h1.size() == 1 and String(h1[0]) == "tan_kilici", "Birinci Mühürde yalnızca birinci emanet düşer (%s)" % str(h1))
	Zorluk.set_muhur(0)
	_check(MuhurYolu.emanet_havuz().is_empty(), "mühürsüzde emanet düşmez")
	# Han Otağı
	Zorluk.set_muhur(5)
	var rng := RandomNumberGenerator.new()
	rng.seed = 7
	var o := Sinav.odul("han", 5, 4, rng)
	_check(int(o.get("tomar", 0)) >= 1 and (o["items"][0] as Dictionary).has("emanet"), "Han Otağı (V): +tomar, emanet (%s)" % String((o["items"][0] as Dictionary).get("name", "")))
	Zorluk.set_muhur(0)
	var o0 := Sinav.odul("han", 5, 4, rng)
	_check(int(o0.get("tomar", 0)) == 0 and not (o0["items"][0] as Dictionary).has("emanet"), "Han Otağı (mühürsüz) değişmedi")
	# emanet ele geçince kalıcı
	Zorluk.set_muhur(5)
	var lv: Level = main.level
	lv.drop_item(it, lv.player.global_position + Vector2(0, -12))
	var p: Pickup = lv.pickups[lv.pickups.size() - 1]
	lv.equip(p, "melee")
	_check(String(it["emanet"]) in Game.meta.get("muhur_emanet_bulunan", []), "emanet bulundu olarak işlendi")
	if lv.player:
		lv.player.on_equip()
	Zorluk.set_muhur(-1)


# ------------------------------------------------------------------ Bengü'nün süsü
func _sus() -> void:
	Zorluk.set_muhur(-1)
	main._build_hub()
	main._start_play()
	await _frames(3)
	var lv: Level = main.level
	var pl: Player = lv.player
	var r5 := MuhurYolu.kayit(5)
	r5["zafer"] = 0
	MuhurYolu._kayit_yaz(5, r5)
	Game.meta["muhur_sus"] = -1
	_check(MuhurYolu.sus() == 4, "süs kendiliğinden en yüksek zafer: %s" % MuhurYolu.SUS_AD[MuhurYolu.sus()])
	MuhurYolu.sus_uygula(pl)
	var mat: ShaderMaterial = pl.sac.mat if pl.sac != null else null
	_check(mat != null and (mat.get_shader_parameter("bead_col") as Color).is_equal_approx(MuhurYolu.renk(4).lerp(Color(1, 1, 1), 0.12)), "şolpı rengi Sarı mühürden")
	r5["zafer"] = 1
	MuhurYolu._kayit_yaz(5, r5)
	MuhurYolu.sus_uygula(pl)
	await _frames(2)
	_check(MuhurYolu.sus() == 5 and pl.get_node_or_null("MuhurTamga") != null, "Beşinci Mühür zaferi: Tan tamgası takıldı")
	main.hud._card_t = 99.0
	var z0: float = Game.base_zoom
	Game.base_zoom = z0 * 2.4
	for np in lv.npcs:
		if np is MuhurTasi:
			pl.global_position = np.global_position + Vector2(-60, -4)
	pl.facing = 1
	Game.camera.reset_smoothing.call_deferred()
	await _sn(1.4)
	await _cek("bengu_tan_tamgasi")
	pl.facing = -1
	await _sn(0.6)
	await _cek("bengu_tan_tamgasi_arka")
	Game.base_zoom = z0
	MuhurYolu.sus_sec(1)
	_check(MuhurYolu.sus() == 0, "süs döndürülür (gümüşe döner)")
	MuhurYolu.sus_uygula(pl)
	await _frames(2)
	_check(pl.get_node_or_null("MuhurTamga") == null or pl.get_node("MuhurTamga").is_queued_for_deletion(), "Tan tamgası çıkarıldı")
	Game.meta["muhur_sus"] = -1
	MuhurYolu.sus_uygula(pl)
	r5["zafer"] = 0
	MuhurYolu._kayit_yaz(5, r5)


# ------------------------------------------------------------------ gerçek son
func _gercek_son() -> void:
	Game.meta["gercek_son"] = false
	await _erlik_yen(5, 1500.0)
	_check(bool(Game.run.get("gercek_son_bekliyor", false)) and int(Game.run.get("muhur_yeni", 0)) == -1, "Beşinci Mühürde zafer: gerçek son bekliyor, yeni mühür yok")
	await _sn(1.8)
	main._on_finished()
	await _frames(3)
	var gs: bool = main.sinema != null and main.sinema.ad == "gercek_son"
	_check(gs, "gerçek son sineması oynadı")
	if gs:
		var s: Sinema = main.sinema
		_check(s.cekimler.size() == 5, "gerçek son 5 çekim (%d)" % s.cekimler.size())
		for k in [0, 2, 3]:
			s.git(s.cekim_basi(k) + float(s.cekimler[k].get("sure", 6.0)) * 0.72)
			await _sn(0.35)
			await _cek("gercek_son_%d_%s" % [k + 1, String(s.cekimler[k].get("id", ""))])
		s._bitir()
		await _sn(1.4)
	_check(bool(Game.meta.get("gercek_son", false)) and main.hud.mode == "zafer", "gerçek son kalıcı, ardından zafer özeti")
	_check(MuhurYolu.sus_acik(5), "Tan tamgası süsü açıldı")
	main._zafer_bitir()
	await _frames(3)
	# ikinci kez: gerçek son yeniden oynamaz
	await _erlik_yen(5, 1400.0)
	_check(not bool(Game.run.get("gercek_son_bekliyor", false)), "gerçek son bir kez")
	_check(bool(Game.run.get("zafer_rekor", false)) and absf(float(MuhurYolu.kayit(5).get("en_iyi", 0.0)) - 1400.0) < 2.0, "yeni rekor: 25:00 → 23:20")
	main._zafer_bitir()
	await _frames(2)


func _kayitlar() -> void:
	var k: Dictionary = Game.meta.get("muhur_kayit", {})
	_check(k.size() == 6, "Game.meta.muhur_kayit altı mühür")
	var hepsi := true
	for n in 6:
		hepsi = hepsi and MuhurYolu.zafer_var(n)
	_check(hepsi, "her mühürde en az bir zafer kayıtlı")
	_check(MuhurYolu.en_yuksek_zafer() == 5, "en yüksek zafer: Beşinci Mühür")
