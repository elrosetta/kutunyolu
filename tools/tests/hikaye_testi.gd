extends Node
## v42 Güneş Ana hikâyesi testi / çekimi (v43: sinematik motoru ve öne çıkan hikâye):
##   godot --path . --quit-after 99999 -- --hikaye_test [--hikaye_cikti=<mutlak klasör>] [--pencere=1920x1080 --grafik=2]
## Sırayla: açılış sineması (10 çekim: katmanlar, canlı öğeler, iki çekimin kare şeridi), boss kartı, örgü sahnesi,
## bölüm açılışı sineması (biyom ufku), bölüm görümü + bölüm sahnesi (bitig taşı okunur), hikâye odası görümü, olay
## görümleri (can, boss kapısı; dövüşte beklenir), beş boss'un kartı + Bengü ↔ bekçi atışması + Gün Örgüsü (düşer →
## oyuncuya akar → kalıcı kayıt + örgü sahnesi + gösterge), yurtta altın yapraklar (3 örgü) ve tan sökmüş yurt, son
## sineması + jenerik, Gün Örgüleri göstergesi (duraklatma / HUD), konakta yoldaşlar (Umay'ın anısı, Ozan'ın dizesi) ve
## hizmet ekranları. Headless'ta çekim atlanır, denetimler yine çalışır. Kalıcı kaydın hikâye alanları sonunda geri yazılır.

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
	for k in ["gun_parca", "gorumler", "giris_izlendi", "son_izlendi", "kut_bank", "runs", "wins", "boss_kart", "umay_ani", "ozan_dize", "olum_biyom"]:
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
	await _sinema("giris", 10)
	await _kartlar()
	await _acilis()
	await _bolum()
	await _olaylar()
	await _orguler()
	await _yurt()
	await _sinema("son", 5)
	await _gosterge()
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


# ------------------------------------------------------------------ sinema (v43 motoru)
const SERIT := {"kirki": [0.9, 1.15, 1.3, 1.7, 2.05, 4.55], "umay": [0.6, 2.0, 3.4, 4.6, 5.4, 7.2], "sonkir": [2.2, 2.62, 2.75, 3.1, 3.8, 5.5]}


func _sinema(tur: String, beklenen: int) -> void:
	get_tree().paused = true
	main.hud.mode = "sinema"
	var s: Sinema = Sinema.oynat(main, tur)
	await _frames(3)
	_check(s.cekimler.size() == beklenen, "%s sineması %d çekim (%d)" % [tur, beklenen, s.cekimler.size()])
	var top := s.toplam_sure()
	if tur == "giris":
		_check(top >= 60.0 and top <= 90.0, "açılış süresi 60-90 sn (%.1f)" % top)
		_check(s._muzik.stream != null, "açılış müziği yüklü (sinema_giris)")
	var katman := 0
	var efekt := 0
	var eksik := 0
	for k in s.cekimler.size():
		var c: Dictionary = s.cekimler[k]
		s.git(s.cekim_basi(k) + float(c.get("sure", 6.0)) * float(c.get("cek_an", 0.62)))
		await _frames(2)
		for o in s._cur.get("oge", []):
			if o["tur"] == "katman":
				katman += 1
				if (o["sprite"] as Sprite2D).texture == null:
					eksik += 1
			else:
				efekt += 1
		await _sn(0.3)
		await _cek("%s_%02d_%s" % [tur, k + 1, String(c.get("id", ""))])
		var sid := String(c.get("id", ""))
		if SERIT.has(sid):
			var n := 0
			for tt in SERIT[sid]:
				s.git(s.cekim_basi(k) + float(tt))
				await _frames(2)
				await _cek("%s_serit_%s_%d" % [tur, sid, n])
				n += 1
	_check(eksik == 0 and katman >= beklenen * 2, "%s: katman dokuları yüklü (%d katman, %d eksik)" % [tur, katman, eksik])
	_check(efekt >= beklenen, "%s: canlı öğeler kuruldu (%d)" % [tur, efekt])
	if tur == "son":
		s.git(top - 0.05)
		await _sn(0.5)
		_check(s._jenerik, "son: jenerik başladı")
		s._jt = 5.2
		await _sn(0.3)
		await _cek("son_jenerik")
	var bitti := [false]
	s.bitti.connect(func() -> void: bitti[0] = true)
	s._bitir()
	await _sn(1.4)
	_check(bitti[0] and not is_instance_valid(s), "%s sineması bitti sinyali, düğüm silindi" % tur)
	main._start_play()


func _kartlar() -> void:
	## Boss kartı (saydam), örgü sahnesi: yer tutucular dolar, çekim kurulur
	for bid in Hikaye.ORGU_SIRA:
		var s: Sinema = Sinema.oynat(main, "boss_kart", Sinema.boss_degisken(bid))
		await _frames(2)
		var y: Array = s.cekimler[0].get("yazi", [])
		_check(y.size() > 0 and String(y[0]["metin"]) == Hikaye.boss_ad(bid), "boss kartı %s: ad «%s», söz yerinde" % [bid, String(y[0]["metin"]) if y.size() > 0 else "-"])
		if bid == "kara_boru_han" or bid == "erlik_han":
			s.git(2.0)
			await _sn(0.3)
			await _cek("boss_kart_%s" % bid)
		s._bitir()
		await _sn(0.9)
	var s2: Sinema = Sinema.oynat(main, "orgu_sahne", Sinema.orgu_degisken("sahmeran", ["kara_boru_han", "tepegoz"]))
	await _frames(2)
	var ef_ok := false
	for o in s2._cur.get("oge", []):
		if o["tur"] == "efekt" and String((o["efekt"] as SinemaEfekt).tur) == "yuvalar":
			ef_ok = int((o["efekt"] as SinemaEfekt).d.get("yeni", -1)) == 2
	_check(ef_ok, "örgü sahnesi: yuvalar (Gök Örgü 3. yuvaya dolar)")
	for tt in [1.2, 3.6, 5.6]:
		s2.git(tt)
		await _sn(0.25)
		await _cek("orgu_sahne_%d" % int(tt * 10))
	s2._bitir()
	await _sn(0.9)


func _acilis() -> void:
	## Bölüm açılışı: biyomun paralaks ufku (isteğe bağlı katmanlar) + bölüm başlığı; oyunda ilk girişte kendiliğinden
	for bm in ["otuken", "bozkir", "sahmeran", "kaf", "tamu"]:
		var s: Sinema = Sinema.oynat(main, "bolum_acilis", Sinema.bolum_degisken(bm))
		await _frames(2)
		var n := 0
		for o in s._cur.get("oge", []):
			if o["tur"] == "katman":
				n += 1
		_check(n >= 6, "bölüm açılışı %s: %d ufuk katmanı" % [bm, n])
		if bm == "otuken" or bm == "kaf":
			for tt in [1.6, 4.0, 6.6]:
				s.git(tt)
				await _sn(0.25)
				await _cek("bolum_acilis_%s_%d" % [bm, int(tt * 10)])
		s._bitir()
		await _sn(0.9)


# ------------------------------------------------------------------ bölüm: görüm, sahne, hikâye odası
func _bolum() -> void:
	Game.new_run()
	Game.run["depth"] = 1
	Sinema.oyun_ici_zorla = true
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
	# v43: ilk girişte bölüm açılışı sineması; biyom görümü onun içinde okunur (ayrı görüm oynamaz)
	await _sn(0.8)
	_check(hs.acilis_oynadi and main.sinema != null and main.sinema.ad == "bolum_acilis", "Ötüken'e ilk giriş: bölüm açılışı sineması oynadı")
	_check(Hikaye.gorum_goruldu("acilis:otuken"), "bölüm açılışı kalıcı kayda işlendi")
	if main.sinema != null:
		main.sinema._bitir()
	await _sn(1.2)
	Sinema.oyun_ici_zorla = false
	_check(get_tree().paused == false and main.hud.mode == "play", "açılıştan sonra oyun sürüyor")
	# eski v42 akışı (afiş + görüm) için görüm kaydını sil ve aynı bölümü yeniden kur
	Game.meta["gorumler"] = ["acilis:otuken"]
	main._build_level()
	main._start_play()
	await _frames(5)
	lv = main.level
	for c in lv.get_children():
		if c is HikayeSahne:
			hs = c
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


# ------------------------------------------------------------------ v43 olay görümleri
func _olaylar() -> void:
	## can: canı azalınca (dövüş yokken); kapi: boss derinliğinde Kut Kapısı'na yaklaşınca. Koşu başına bir kez.
	Game.new_run()
	Game.run["depth"] = 2
	main._build_level()
	main._start_play()
	await _frames(5)
	var lv: Level = main.level
	var hs: HikayeSahne = null
	for c in lv.get_children():
		if c is HikayeSahne:
			hs = c
	if hs == null:
		_check(false, "olay: HikayeSahne yok")
		return
	await _sn(1.0)
	# dövüş varken bekler: yakına düşman koy, canı düşür
	for e in get_tree().get_nodes_in_group("dusman"):
		if e is Node2D:
			(e as Node2D).global_position = lv.player.global_position + Vector2(90, -10)
			break
	Game.run["hp"] = float(Game.run["max_hp"]) * 0.2
	await _sn(1.2)
	var dovus_var := hs._dovus(lv.player.global_position)
	_check(not dovus_var or not ("can" in hs.olay_gosterilen), "olay: dövüşte görüm beklenir")
	for e in get_tree().get_nodes_in_group("dusman"):
		(e as Node).queue_free()
	await _sn(1.6)
	_check("can" in hs.olay_gosterilen, "olay görümü: can azalınca Gün Ana («%s»)" % Gorum.inst.son_metin)
	await _cek("olay_can")
	Game.run["hp"] = float(Game.run["max_hp"])
	await _sn(5.5)
	lv.player.global_position = lv.exit_pos + Vector2(-140, -10)
	lv.player.velocity = Vector2.ZERO
	await _sn(1.6)
	_check("kapi" in hs.olay_gosterilen, "olay görümü: boss kapısına yaklaşınca («%s»)" % Gorum.inst.son_metin)
	await _sn(5.0)
	var n := hs.olay_gosterilen.size()
	Game.run["hp"] = float(Game.run["max_hp"]) * 0.2
	await _sn(1.5)
	_check(hs.olay_gosterilen.size() == n, "olay görümleri koşu başına bir kez")
	Game.run["hp"] = float(Game.run["max_hp"])
	# biyomdaki ilk ölüm satırı
	Game.meta["olum_biyom"] = []
	Hikaye.olum_isaretle("otuken")
	_check(Hikaye.olum_satiri().contains("Külün"), "ilk ölüm satırı (Ötüken): «%s»" % Hikaye.olum_satiri())


# ------------------------------------------------------------------ boss örgüleri
func _orguler() -> void:
	_meta_kur([])
	# v43 birleştirme: kart ilk üç karşılaşmada oynar; gerçek kayıttaki sayaç (ör. çekimlerden 3) testi bozmasın
	# (_yedek sonda geri yükler)
	Game.meta["boss_kart"] = {}
	var depths := {"kara_boru_han": 2, "tepegoz": 4, "sahmeran": 6, "yelbegen": 8, "erlik_han": 10}
	for bid in Hikaye.ORGU_SIRA:
		Game.new_run()
		Game.run["depth"] = int(depths[bid])
		main._build_boss(bid)
		main._start_play()
		# v43: kükreyişten sonra boss kartı, kart bitince Bengü ↔ bekçi atışması
		var kart_ok := false
		for w in 20:
			await _sn(0.2)
			if main.sinema != null and main.sinema.ad == "boss_kart":
				kart_ok = true
				break
		_check(kart_ok, "%s: boss kartı oynadı" % bid)
		if kart_ok:
			main.sinema._bitir()
		var soz_ok: bool = await _bekle_metin(Hikaye.boss_soz(bid, "bengu"), 5.0)
		_check(soz_ok, "%s: Bengü'nün sözü: «%s»" % [bid, Gorum.inst.son_metin])
		var yanit_ok: bool = await _bekle_metin(Hikaye.boss_soz(bid, "yanit"), 6.0)
		_check(yanit_ok, "%s: bekçinin cevabı: «%s»" % [bid, Gorum.inst.son_metin])
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
		var sahne_ok := false
		for w in 50:
			await _sn(0.2)
			if main.sinema != null and main.sinema.ad == "orgu_sahne":
				sahne_ok = true
				break
		_check(Hikaye.parca_var(bid) and Hikaye.parca_sayi() == n0 + 1, "%s: örgü alındı, kalıcı kayıt %d örgü" % [bid, Hikaye.parca_sayi()])
		_check(sahne_ok, "%s: örgü sahnesi oynadı (%s)" % [bid, String(Hikaye.orgu(bid).get("ad", ""))])
		if sahne_ok:
			await _sn(3.4)
			if bid == "kara_boru_han":
				await _cek("orgu_sahne_oyun_%s" % bid)
			main.sinema._bitir()
			await _sn(1.0)
		var bs_ok: bool = await _bekle_metin(Hikaye.boss_soz(bid, "bengu_sonra"), 6.0)
		_check(bs_ok, "%s: devrilince Bengü'nün cevabı: «%s»" % [bid, Gorum.inst.son_metin])
		_check(OrguGosterge.gecen() < 9.0, "%s: Gün Örgüleri göstergesi HUD'da belirdi" % bid)
		await _cek("orgu_%s" % bid)
		if bid == "erlik_han":
			# son sineması örgü sahnesinden sonra kendiliğinden başlar
			await _sn(1.4)
			_check(main.sinema != null and main.sinema.ad == "son", "Erlik'in Altın Örgüsü son sinemasını başlattı")
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


# ------------------------------------------------------------------ v43 Gün Örgüleri göstergesi
func _gosterge() -> void:
	_meta_kur(["kara_boru_han", "tepegoz", "sahmeran"])
	Game.new_run()
	Game.run["depth"] = 5
	main._build_level()
	main._start_play()
	await _sn(1.0)
	OrguGosterge.bildir(2)
	await _sn(0.8)
	await _cek("orgu_gosterge_hud")
	get_tree().paused = true
	await _sn(0.3)
	await _cek("orgu_gosterge_duraklat")
	_check(OrguGosterge.gecen() < 2.0, "Gün Örgüleri göstergesi: HUD ve duraklatma ekranında")
	main._start_play()


# ------------------------------------------------------------------ konak
func _konak() -> void:
	_meta_kur(["kara_boru_han", "tepegoz"])
	Game.meta["umay_ani"] = 1
	Game.meta["ozan_dize"] = []
	Game.new_run()
	Game.run["depth"] = 3
	Game.run["gold"] = 400
	Level.bezirgan_zorla = true
	main._build_konak()
	main._start_play()
	await _frames(5)
	var lv: Level = main.level
	# v43: ikinci örgüyle Umay'ın anısı, yeni bölümün Ozan dizesi (kalıcı, bir kez)
	var ani: Array = Data.story["olay"]["umay_ani"]
	var ani_ok: bool = await _bekle_metin(String(ani[1]), 5.0)
	_check(ani_ok and int(Game.meta.get("umay_ani", 0)) == 2, "konak: Umay'ın kız kardeş anısı («%s»)" % Gorum.inst.son_metin)
	await _cek("konak_umay_ani")
	var bm := String(lv.biome.get("id", ""))
	var dize_ok: bool = await _bekle_metin(String(Data.story["olay"]["ozan_dize"].get(bm, "-")), 14.0)
	_check(dize_ok and bm in Game.meta.get("ozan_dize", []), "konak: Ozan'ın %s dizesi" % bm)
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
