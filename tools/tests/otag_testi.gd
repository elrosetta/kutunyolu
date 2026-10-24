extends Node
## v42 sınav ve otağ testi: godot --headless --path . --quit-after 99999 -- --otag --muhur=0
##   KURULUM:  1. derinlik bölümü: Sinav kuruldu (3 mühür sürüyor), Çabuk süresi 75-240 sn, Otağ Yeri'nde 4 otağ (han,
##             cabuk, dokunulmaz, avci), her otağ ayakta durulan hücrede, girişten erişilir, Kut Kapısı önü (5 karo) boş;
##             av hedefi tamgalı (meta "av", AvIsaret).
##   KAYBETME: darbe (can düşer) -> Dokunulmaz çatlar; süre dolar -> Çabuk çatlar; tamgalı av kalmadı -> Avcı çatlar;
##             çatlak / bekleyen otağa girilemez (OtagIc açılmaz), Han kapalı.
##   KAZANMA:  yeni bölüm: tamgalı av oyunun yolundan öldürülür (Enemy.take_hit -> Level.on_enemy_died) -> Avcı; oyuncu
##             Otağ Yeri'ne konur -> Çabuk + Dokunulmaz (şişe içmek bozmaz) -> üçü birden: Han açık.
##   OTAĞ:     her açık otağa W (Level.otag_gir) -> OtagIc, oyun durur; kapat -> ödül (altın / Kut / eşya / tomar) verilir,
##             ikinci giriş reddedilir; Han ödülü Efsanevi.
##   TÜRLER:   açık / kale / iniş / mağara bölümlerinde (LevelGen.zorla_tur) d1 ve d4: en az 3 otağ, hepsi erişilir.
##   DEĞER:    derinlik 1-9, her otağ için 40 sandık: ortalama altın karşılığı (Sinav.deger) ve bölüm altınına oranı;
##             beklenen değer (varsayılan kazanma oranlarıyla).
## Çekim: --otag_ekran=<klasör> (headless değil; --pencere=1920x1080 --grafik=2 --bekle=16): afis.png, hud.png,
##   yer.png (açık / çatlak / bekleyen otağlar), ic.png (otağ içi ve sandık), han.png (Han Otağı açık), han_ic.png.
## Çıktı "[otag] ..." satırları, sonda "[otag] SONUC GECTI|KALDI". Kalıcı kayıt test sonunda geri yüklenir.

var main: Node
var _fail: Array = []
var _meta0: Dictionary = {}
var _ekran := ""


func _ready() -> void:
	process_mode = Node.PROCESS_MODE_ALWAYS
	for a in OS.get_cmdline_user_args():
		if String(a).begins_with("--otag_ekran="):
			_ekran = String(a).trim_prefix("--otag_ekran=")
	_meta0 = Game.meta.duplicate(true)
	_run.call_deferred()


func _p(s: String) -> void:
	print("[otag] ", s)


func _check(ok: bool, what: String) -> void:
	_p(("TAMAM " if ok else "HATA ") + what)
	if not ok:
		_fail.append(what)


func _frames(n: int) -> void:
	for i in n:
		await get_tree().process_frame


func _build(d: int) -> Node:
	Game.run["depth"] = d
	Game.run["tier"] = Zorluk.kademe(d)
	main._build_level()
	main._start_play()
	await _frames(3)
	return main.level


func _sakin(lv: Node, around: Vector2, r: float) -> void:
	## Testin olduğu yerin çevresindeki (tamgasız) yaratıkları kaldır: oyuncu dövülmesin
	for e in get_tree().get_nodes_in_group("dusman"):
		if is_instance_valid(e) and not e.has_meta("av") and e.global_position.distance_to(around) < r:
			e.remove_from_group("dusman")
			e.queue_free()


func _koy(lv: Node, pos: Vector2) -> void:
	lv.player.global_position = pos + Vector2(0, -2)
	lv.player.velocity = Vector2.ZERO
	if lv.camera and lv.camera.has_method("snap"):
		lv.camera.snap()


func _run() -> void:
	seed(4242)   # bölüm tohumları (Main._build_level randi) belirlenimci
	await _frames(5)
	if _ekran != "":
		await _cekim()
		return
	await _kurulum()
	await _kaybetme()
	await _kazanma()
	await _turler()
	_deger()
	Game.meta = _meta0
	Game.save_meta()
	_p("kalıcı kayıt geri yüklendi")
	_p("SONUC %s%s" % ["GECTI" if _fail.is_empty() else "KALDI", "" if _fail.is_empty() else " (" + ", ".join(_fail) + ")"])
	get_tree().quit()


# ------------------------------------------------------------------ kurulum
func _yer_denetle(lv: Node, etiket: String) -> bool:
	var seen := LevelGen.reach_from(lv.grid, lv.W, lv.H, lv.spawn_cell.x, lv.spawn_cell.y)
	var ok := true
	for o in lv.otaglar:
		var c: Vector2i = o.cell
		var dur: bool = lv.cell(c.x, c.y + 1) == 1 and lv.cell(c.x, c.y) == 0 and lv.cell(c.x, c.y - 1) == 0
		var er: bool = seen[lv.idx(c.x, c.y)] == 1
		var kapi: bool = absi(c.x - lv.exit_cell.x) >= 4 or absi(c.y - lv.exit_cell.y) >= 4
		if not (dur and er and kapi):
			ok = false
			_p("  %s otağ %s karo %s: ayakta=%s erişim=%s kapıdan_uzak=%s" % [etiket, o.tur, str(c), str(dur), str(er), str(kapi)])
	return ok


func _kurulum() -> void:
	var lv := await _build(1)
	var sv: Sinav = lv.sinav
	_check(sv != null, "bölümde Sinav kuruldu")
	if sv == null:
		return
	_check(sv.durum["cabuk"] == 0 and sv.durum["dokunulmaz"] == 0 and sv.durum["avci"] == 0, "üç mühür sürüyor")
	_check(sv.par >= 75.0 and sv.par <= 240.0, "Çabuk süresi %d sn (yol %.1f sn, ana yol odası %d)" % [int(sv.par), sv.yol_sn, lv.main_rooms().size()])
	var turler: Array = []
	for o in lv.otaglar:
		turler.append(o.tur)
	_check(turler == ["han", "cabuk", "dokunulmaz", "avci"], "Otağ Yeri: 4 otağ, Kut Kapısı'na yakından uzağa %s" % str(turler))
	_check(_yer_denetle(lv, "d1"), "otağlar ayakta durulan hücrede, girişten erişilir, Kut Kapısı önünde değil")
	var av := 0
	for e in get_tree().get_nodes_in_group("dusman"):
		if is_instance_valid(e) and e.has_meta("av") and not e.is_queued_for_deletion():
			av += 1
	_check(av >= sv.av_gerek and av > 0, "tamgalı av: %s (%s; bölümde %d tamgalı)" % [sv.av_ad, sv.av_mod, av])
	for o in lv.otaglar:
		_check(not lv.otag_gir(o) and lv.otag_ic == null, "bekleyen %s otağına girilemez" % o.tur)


# ------------------------------------------------------------------ kaybetme
func _kaybetme() -> void:
	var lv: Node = main.level
	var sv: Sinav = lv.sinav
	Game.run["hp"] = float(Game.run["hp"]) - 5.0
	await _frames(3)
	_check(sv.durum["dokunulmaz"] == -1, "darbe alınınca Dokunulmaz çatladı")
	Game.run["bolum_sure"] = sv.par + 1.0
	await _frames(3)
	_check(sv.durum["cabuk"] == -1, "süre dolunca Çabuk çatladı (%d sn)" % int(sv.par))
	for e in get_tree().get_nodes_in_group("dusman"):
		if is_instance_valid(e) and e.has_meta("av"):
			e.remove_meta("av")
	await get_tree().create_timer(0.7).timeout
	_check(sv.durum["avci"] == -1, "tamgalı av kalmayınca Avcı çatladı")
	var catlak := 0
	for ol in sv.olaylar:
		if String(ol[1]) == "catlak":
			catlak += 1
	_check(catlak == 3, "üç çatlama olayı (arayüz canlandırması) %d" % catlak)
	for o in lv.otaglar:
		_check(o.durum() == -1 and not lv.otag_gir(o) and lv.otag_ic == null, "çatlak %s otağı kapalı, girilemez" % o.tur)


# ------------------------------------------------------------------ kazanma ve otağlar
func _kazanma() -> void:
	var lv := await _build(3)
	var sv: Sinav = lv.sinav
	Game.run["hp"] = float(Game.run["max_hp"])
	Game.run["gold"] = 0
	Game.run["kut"] = 0
	await _frames(2)
	# av: oyunun yolundan öldür (Enemy.take_hit -> _die -> Level.on_enemy_died -> Sinav.olduruldu)
	var oldu := 0
	lv.player.inv_t = 9999.0   # av avlanırken çevredeki yaratıklar oyuncuyu vurmasın (Dokunulmaz ayrıca sınanır)
	# v43 birleştirme: test oyuncusu av boyunca donuk (fizik kapalı) ve girişte kalır (avın yanına konmaz): eskiden avın
	# yanına konunca boşluğa / dikene düşüp düşüş hasarı, zehir ya da sürünün öbür tazılarının yakalama darbesi
	# (inv_t'yi aşar) alıp Dokunulmaz'ı çatlatabiliyordu (koşuların ~%20'si). Kural aynı: can düşerse çatlar (_kaybetme
	# sınar); burada sınanan av -> Avcı ve şişenin Dokunulmaz'ı bozmaması. Av yine oyunun yolundan ölür (take_hit).
	lv.player.set_physics_process(false)
	lv.player.poison_t = 0.0
	var hp_av := float(Game.run["hp"])
	for e in get_tree().get_nodes_in_group("dusman"):
		if is_instance_valid(e) and e.has_meta("av") and not e.dead:
			for i in 30:
				if not is_instance_valid(e) or e.dead:
					break
				e.take_hit(99999.0, {"dir": 1.0})
				await _frames(2)
			oldu += 1
			await _frames(20)
			if sv.durum["avci"] == 1:
				break
	await _frames(4)
	Game.run["hp"] = float(Game.run["max_hp"])
	await _frames(2)
	_check(sv.durum["avci"] == 1, "tamgalı av öldürülünce Avcı kazanıldı (%s, %d öldürme)" % [sv.av_ad, oldu])
	# şişe / şifa can artırır: Dokunulmaz'ı bozmaz
	Game.run["hp"] = float(Game.run["hp"]) - 0.0
	lv.player.heal(5.0)
	await _frames(2)
	_check(sv.durum["dokunulmaz"] == 0, "can artışı (şişe) Dokunulmaz'ı bozmaz")
	if sv.durum["dokunulmaz"] != 0:
		_p("  tanı: av öncesi can %.1f, olaylar %s" % [hp_av, str(sv.olaylar)])
	lv.player.inv_t = 0.0
	lv.player.set_physics_process(true)
	var o0: Node = lv.otaglar[1]
	_sakin(lv, o0.global_position, 700.0)
	await _frames(2)
	Game.run["hp"] = float(Game.run["max_hp"])
	await _frames(1)
	_koy(lv, o0.global_position)
	await _frames(4)
	_check(sv.vardi and sv.durum["cabuk"] == 1 and sv.durum["dokunulmaz"] == 1, "Otağ Yeri'ne süresinde ve darbesiz varıldı: Çabuk + Dokunulmaz (süre %.1f / %d sn)" % [sv.var_sure, int(sv.par)])
	_check(sv.hepsi() and lv.otaglar[0].acik(), "üç mühür: Han Otağı açık")
	for o in lv.otaglar:
		_koy(lv, o.global_position)
		await _frames(3)
		var g0 := int(Game.run["gold"])
		var k0 := int(Game.run["kut"])
		var p0: int = lv.pickups.filter(func(p: Node) -> bool: return is_instance_valid(p)).size()
		_check(o.near and lv.otag_yakin() == o, "%s otağının kapısında (W)" % o.tur)
		var girdi: bool = lv.otag_gir(o)
		await _frames(2)
		_check(girdi and lv.otag_ic != null and get_tree().paused, "%s otağına girildi (OtagIc, oyun durdu)" % o.tur)
		if not girdi:
			continue
		var od: Dictionary = lv.otag_ic.odul
		lv.otag_ic.kapat()
		await _frames(3)
		var p1: int = lv.pickups.filter(func(p: Node) -> bool: return is_instance_valid(p)).size()
		var dusen := int((od["items"] as Array).size()) + int(od["tomar"]) + (1 if String(od["parsomen"]) != "" else 0)
		_check(not get_tree().paused and int(Game.run["gold"]) - g0 == int(od["altin"]) and int(Game.run["kut"]) - k0 == int(od["kut"]) and p1 - p0 == dusen,
			"%s ödülü verildi: altın +%d, Kut +%d, yere %d (%s)" % [o.tur, int(od["altin"]), int(od["kut"]), dusen, ", ".join((od["items"] as Array).map(func(it: Dictionary) -> String: return String(it.get("name", ""))))])
		match o.tur:
			"cabuk":
				_check(int(od["altin"]) > 0 and int((od["items"][0] as Dictionary).get("rarity", 0)) >= 1, "Çabuk: altın + en az Nadir eşya")
			"dokunulmaz":
				_check(int(od["tomar"]) == 1, "Dokunulmaz: Kut Tomarı%s" % (" + parşömen" if String(od["parsomen"]) != "" else ""))
			"avci":
				var it: Dictionary = od["items"][0]
				_check(int(od["kut"]) > 0 and String(it.get("kind", "")) in Sinav.AV_SILAH and int(it.get("rarity", 0)) >= 1, "Avcı: Kut + av silahı (%s, %s)" % [String(it.get("kind", "")), String(it.get("name", ""))])
			"han":
				_check(int((od["items"][0] as Dictionary).get("rarity", 0)) == 3, "Han Otağı: Efsanevi eşya")
		_check(not lv.otag_gir(o) and lv.otag_ic == null or not is_instance_valid(lv.otag_ic), "%s otağına ikinci kez girilemez (boş)" % o.tur)
	var rek: Dictionary = Game.meta.get("sinav", {})
	_check(int(rek.get("muhur", 0)) >= 3 and not (rek.get("en_iyi", {}) as Dictionary).is_empty(), "istatistik: kazanılan mühür %d, en iyi süre %s" % [int(rek.get("muhur", 0)), str(rek.get("en_iyi", {}))])


# ------------------------------------------------------------------ bölüm türleri
func _turler() -> void:
	var say := 0
	var iyi := 0
	for tr in ["acik", "kale", "inis", "magara"]:
		for d in [1, 4]:
			LevelGen.zorla_tur = tr
			var lv := await _build(d)
			say += 1
			var n: int = lv.otaglar.size()
			var ok := n >= 3 and _yer_denetle(lv, "%s d%d" % [tr, d])
			if ok:
				iyi += 1
			_p("  tür %s d%d (%s): otağ=%d par=%d sn av=%s" % [tr, d, String(lv.biome.get("id", "")), n, int(lv.sinav.par), lv.sinav.av_ad])
	LevelGen.zorla_tur = ""
	_check(iyi == say, "her bölüm türünde Otağ Yeri geçerli ve erişilir (%d/%d)" % [iyi, say])


# ------------------------------------------------------------------ değer
const ORAN := {"cabuk": 0.5, "dokunulmaz": 0.2, "avci": 0.6, "han": 0.06}   # varsayılan kazanma oranı (beklenen değer)


func _deger() -> void:
	## Ölçü: otağ sandığının altın karşılığı (Sinav.deger: altın + eşyanın Bezirgân fiyatı + Kut Tomarı fiyatı + Kut x2).
	## Karşılaştırma: (a) tam temizlenen bölümün altını (~150 x altin_k; tuccar_testi EKONOMI yaklaşığı), (b) bölümün
	## bütün ganimeti aynı ölçüyle: altın + 3 kaide eşyası + 3 Kut Tomarı.
	var rng := RandomNumberGenerator.new()
	rng.seed = 42
	_p("DEGER d | ort. altın karşılığı: Çabuk Dokunulmaz Avcı Han | beklenen (oran %s) | bölüm altını | bölüm ganimeti | beklenen / altın | beklenen / ganimet" % str(ORAN))
	var top := 0.0
	var top_g := 0.0
	for d in range(1, 10):
		Game.run["depth"] = d
		var t := Zorluk.kademe(d)
		var row := {}
		for k in ["cabuk", "dokunulmaz", "avci", "han"]:
			var s := 0.0
			for i in 40:
				s += Sinav.deger(Sinav.odul(k, d, t, rng), d)
			row[k] = s / 40.0
		var ev := 0.0
		for k in row:
			ev += float(row[k]) * float(ORAN[k])
		var bolum := 150.0 * Pazar.altin_k(d)
		var esya := 0.0
		for i in 40:
			esya += float(Pazar.esya_fiyat(ItemGen.random_drop(t), d))
		var ganimet := bolum + 3.0 * esya / 40.0 + 3.0 * float(Pazar.tomar_fiyat(d))
		top += ev / bolum
		top_g += ev / ganimet
		_p("DEGER %d | %d %d %d %d | %d | %d | %d | x%.2f | x%.2f" % [d, int(row["cabuk"]), int(row["dokunulmaz"]), int(row["avci"]), int(row["han"]), int(ev), int(bolum), int(ganimet), ev / bolum, ev / ganimet])
	_p("DEGER ortalama beklenen / bölüm altını = x%.2f, beklenen / bölüm ganimeti = x%.2f" % [top / 9.0, top_g / 9.0])
	_check(top_g / 9.0 > 0.1 and top_g / 9.0 < 0.4, "otağ ödülleri anlamlı ama koşuyu bozmaz (beklenen değer bölüm ganimetinin %%%.0f'i)" % (100.0 * top_g / 9.0))


# ------------------------------------------------------------------ çekim
func _bekle(sn: float) -> void:
	await get_tree().create_timer(sn, true, false, true).timeout


func _snap(name: String) -> void:
	await RenderingServer.frame_post_draw
	var img := get_viewport().get_texture().get_image()
	if img == null:
		return
	if get_viewport().use_hdr_2d:
		if img.get_format() != Image.FORMAT_RGBA8 and img.get_format() != Image.FORMAT_RGB8:
			img.convert(Image.FORMAT_RGBA8)
		img.linear_to_srgb()
	DirAccess.make_dir_recursive_absolute(_ekran)
	var path := _ekran.path_join(name + ".png")
	img.save_png(path)
	_p("kare: " + path)


func _cekim() -> void:
	var w := 16.0
	for a in OS.get_cmdline_user_args():
		if String(a).begins_with("--bekle="):
			w = float(String(a).trim_prefix("--bekle="))
	var tohum := 3
	for a in OS.get_cmdline_user_args():
		if String(a).begins_with("--otag_tohum="):
			tohum = int(String(a).trim_prefix("--otag_tohum="))
	seed(tohum)
	var lv := await _build(int(Game.run.get("depth", 1)))
	_sakin(lv, lv.player.global_position, 500.0)
	await _bekle(w)   # ısınma (gölgelendirici / doku yükleme)
	lv = await _build(1)
	_sakin(lv, lv.player.global_position, 500.0)
	await _bekle(2.4)
	await _snap("afis")   # bölüm afişi + sınav satırı + sağ üst mühürler
	var sv: Sinav = lv.sinav
	sv.kazan("avci")
	sv.kaybet("dokunulmaz")
	await _bekle(2.6)
	await _snap("hud")    # Avcı altın, Dokunulmaz çatlak, Çabuk sürüyor (kalan süre)
	# Otağ Yeri: Çabuk açık, Dokunulmaz çatlak, Avcı açık, Han kapalı
	var mid: Node = lv.otaglar[2]
	_sakin(lv, mid.global_position, 900.0)
	Game.run["hp"] = float(Game.run["max_hp"])
	_koy(lv, lv.otaglar[1].global_position + Vector2(26, 0))
	await _bekle(1.5)
	await _snap("yer")
	lv.otag_gir(lv.otaglar[1])
	await _bekle(2.2)
	await _snap("ic")
	lv.otag_ic.kapat()
	await _bekle(1.0)
	await _snap("yer_odul")
	# Han Otağı: üç mühür (yeni bölüm, hepsi kazanılmış)
	lv = await _build(4)
	sv = lv.sinav
	_sakin(lv, lv.otaglar[0].global_position, 1400.0)
	sv.kazan("avci")
	_koy(lv, lv.otaglar[2].global_position)
	await _bekle(1.0)
	_koy(lv, lv.otaglar[0].global_position + Vector2(-40, 0))
	await _bekle(3.5)
	await _snap("han")
	lv.otag_gir(lv.otaglar[0])
	await _bekle(2.2)
	await _snap("han_ic")
	Game.meta = _meta0
	Game.save_meta()
	get_tree().quit()
