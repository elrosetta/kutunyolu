extends Node
## v44 derinlik testi: Damgalar, Ozan'ın Destanı (kodeks), koşu özeti ve rekorlar, Destan Başarıları.
##   godot --headless --path . --quit-after 99999 -- --damga --kayit=user://test_v44.json      (DAMGA: teklif, seçim, yuva,
##        yeniden oyma, her Damganın etkisi, uyum, Damga Taşı ekranı ve konak akışı)
##   ... -- --kodeks     (öldürme kaydı, zaaf / bilgi eşikleri, silah görülme, Damga görülme, göç, tamamlanma, ekran sekmeleri)
##   ... -- --ozet       (koşu istatistikleri, ölüm nedeni, bitir: rekorlar, Mühür kademesi, geçmiş, zafer, ölüm akışı)
##   ... -- --basarim    (25 başarım, koşullar, ödüller (Kut / renk / söz), bildirim kuyruğu, sessiz göç, çerçeve rengi seçimi)
## Çekim (headless değil, --goruntu ile): --derinlik_ekran=damga | damga_vur | hud | kodeks_yaratik | kodeks_silah |
##   kodeks_damga | kodeks_destan | kodeks_basarim | rekor | ozet | zafer | toast
## Çıktı "[v44] ..." satırları, sonda "[v44] SONUC GECTI|KALDI". Kalıcı kayıt test sonunda geri yüklenir.

var main: Node
var _fail: Array = []
var _meta0: Dictionary = {}
var _ekran := ""
var _ok_n := 0


func _ready() -> void:
	process_mode = Node.PROCESS_MODE_ALWAYS
	for a in OS.get_cmdline_user_args():
		if String(a).begins_with("--derinlik_ekran="):
			_ekran = String(a).trim_prefix("--derinlik_ekran=")
	_meta0 = Game.meta.duplicate(true)
	_run.call_deferred()


func _p(s: String) -> void:
	print("[v44] ", s)


func _check(ok: bool, what: String) -> void:
	_p(("TAMAM " if ok else "HATA ") + what)
	if ok:
		_ok_n += 1
	else:
		_fail.append(what)


func _frames(n: int) -> void:
	for i in n:
		await get_tree().process_frame


func _has(flag: String) -> bool:
	return OS.get_cmdline_user_args().has(flag)


func _run() -> void:
	await _frames(5)
	if _ekran != "":
		await _ekran_kur()
		return
	if _has("--damga"):
		await _damga()
	if _has("--kodeks"):
		await _kodeks()
	if _has("--ozet"):
		await _ozet()
	if _has("--basarim"):
		await _basarim()
	Game.meta = _meta0
	Game.save_meta()
	_p("kalıcı kayıt geri yüklendi")
	_p("SONUC %s (%d denetim)%s" % ["GECTI" if _fail.is_empty() else "KALDI", _ok_n + _fail.size(), "" if _fail.is_empty() else " (" + ", ".join(_fail) + ")"])
	get_tree().quit()


func _temiz_meta() -> void:
	## Boş kayıt (yeni oyuncu): kodeks / başarım / rekor sıfır
	Game.meta = {"runs": 1, "wins": 0, "kut_bank": 0, "unlocked": [], "blueprints": [], "best_depth": 1}
	Hikaye.meta_hazirla()
	Kodeks.meta_hazirla()
	Game.meta["rekor"] = {}
	Basarim.meta_hazirla()
	Basarim.kuyruk.clear()


func _bolum(d: int) -> void:
	Game.run["depth"] = d
	Game.run["tier"] = Zorluk.kademe(d)
	main._build_level()
	main._start_play()
	await _frames(4)


func _konak(d: int) -> void:
	Game.run["depth"] = d
	Game.run["tier"] = Zorluk.kademe(d)
	main._build_konak()
	main._start_play()
	await _frames(4)


func _dusman(kind := "kara_boru", elite := false, dx := 60.0) -> Enemy:
	var lv: Node = main.level
	var pl: Node = lv.player
	var e: Enemy = lv.spawn_enemy(kind, pl.global_position + Vector2(dx, -4.0), elite)
	return e


func _ev(action: String) -> InputEventAction:
	var e := InputEventAction.new()
	e.action = action
	e.pressed = true
	return e


# ================================================================== DAMGA
func _damga() -> void:
	_temiz_meta()
	main._new_run()
	await _frames(3)
	_check(Damga.D.size() >= 16 and Damga.D.size() <= 20, "Damga sayısı %d (16-20)" % Damga.D.size())
	var tamga_ok := true
	var hucre: Array = []
	for id in Damga.D:
		var d: Array = Damga.D[id]
		tamga_ok = tamga_ok and d.size() == 7 and String(d[4]) != "" and not (int(d[1]) in hucre)
		hucre.append(int(d[1]))
	_check(tamga_ok, "her Damganın adı, ayrı tamgası, etkisi, üslubu ve sözü var")
	# ---- yuva: yeni oyuncu 1; Kara Börü Han → 2; Şahmeran Ana → 3
	_check(Damga.yuva() == 1, "yeni oyuncuda 1 Damga yuvası (%d)" % Damga.yuva())
	# ---- konak: Damga Taşı ve teklif
	await _konak(2)
	var lv: Node = main.level
	var tas: Node = null
	for n in lv.npcs:
		if n is DamgaTasi:
			tas = n
	_check(tas != null, "konakta Damga Taşı var (x=%.0f)" % (tas.global_position.x if tas else -1.0))
	var usta_x := 0.0
	var dem_x := 0.0
	for n in lv.npcs:
		if n.id == "usta":
			usta_x = n.global_position.x
		elif n.id == "demirci":
			dem_x = n.global_position.x
	if tas:
		_check(tas.global_position.x > usta_x and tas.global_position.x < dem_x, "Damga Taşı Usta ile Demirci arasında")
	var tk: Array = Damga.teklif()
	var ayri: bool = tk.size() == 3 and tk[0] != tk[1] and tk[1] != tk[2] and tk[0] != tk[2]
	_check(ayri, "teklif: 3 ayrı Damga %s" % str(tk))
	var nadir_n := 0
	for id in tk:
		if bool(Damga.D[id][3]):
			nadir_n += 1
	_check(nadir_n <= 1, "teklifte en çok bir nadir Damga")
	# aynı tohum aynı teklif
	Game.run["damga_konak"] = -1
	Damga.yeni_konak(777)
	var t1: Array = Damga.teklif().duplicate()
	Game.run["damga_konak"] = -1
	Damga.yeni_konak(777)
	_check(t1 == Damga.teklif(), "aynı konak tohumu aynı teklif")
	# aynı derinlikte yeniden kurulum teklifi korur
	Damga.yeni_konak(999)
	_check(t1 == Damga.teklif(), "aynı konakta (derinlik) teklif yeniden çekilmez")
	for id in t1:
		_check(Kodeks.damga_gorulen(id), "teklif kodekse 'görüldü' yazıldı: %s" % id)
	# ---- ekran: Damga Taşı'yla konuşunca
	main._on_npc("damga")
	_check(main.hud.mode == "damga" and get_tree().paused, "Damga Taşı ekranı açıldı (oyun durdu)")
	# yeniden oyma: altın yetmez / yeter
	Game.run["gold"] = 0
	var r0 := Damga.oy()
	_check(not r0["ok"] and Damga.teklif() == t1, "altın yoksa yeniden oyma reddedilir")
	Game.run["gold"] = 500
	var c1 := Damga.oyma_bedel()
	DerinlikUI._girdi_damga(main, _ev("techizat2"), false, false)
	var t2: Array = Damga.teklif().duplicate()
	_check(int(Game.run["gold"]) == 500 - c1 and t2 != t1, "R: Bengisu yeniden oydu (-%d altın), teklif değişti" % c1)
	var c2 := Damga.oyma_bedel()
	_check(c2 > c1, "ikinci oyma pahalı (%d → %d)" % [c1, c2])
	_check(c1 == int(round(float(Damga.OYMA_TABAN) * Pazar.derinlik_k() / 5.0)) * 5, "oyma bedeli 30 x derinlik_k (%d)" % c1)
	# seçim (A/D + Boşluk)
	DerinlikUI._girdi_damga(main, _ev("sag"), false, false)
	_check(DerinlikUI.damga_sec == 1, "D ile ikinci kart seçildi")
	var secilen := String(t2[1])
	DerinlikUI._girdi_damga(main, InputEventAction.new(), true, false)
	_check(Damga.has(secilen) and Damga.secildi(), "Boşluk: %s vuruldu" % secilen)
	_check(Kodeks.damga_alinan(secilen) == 1, "kodekste alınma sayısı 1")
	_check(DerinlikUI.damga_sonuc == secilen, "VURULDU damgası basıldı")
	var r2 := Damga.oy()
	_check(not r2["ok"], "Damga vurulduktan sonra taş yeniden oymaz")
	await get_tree().create_timer(1.2, true, false, true).timeout
	DerinlikUI._girdi_damga(main, InputEventAction.new(), true, false)
	_check(main.hud.mode == "play" and not get_tree().paused, "Boşluk: oyuna dönüldü (mod=%s dt=%.2f sonuc=%s)" % [main.hud.mode, DerinlikUI._now() - DerinlikUI.damga_t, DerinlikUI.damga_sonuc])
	main._on_npc("damga")
	_check(main.hud.mode == "play" and not get_tree().paused, "aynı konakta ikinci kez: ekran açılmaz, yol sürer")
	# ---- yuva dolu: değiştirme
	var a0: Array = Damga.etkin().duplicate()
	Game.run["damga_secildi"] = -1
	var yeni := ""
	for id in Damga.D:
		if not Damga.has(id):
			yeni = id
			break
	var rr := Damga.al(yeni)
	_check(not rr["ok"] and Damga.etkin() == a0, "yuva doluyken silinecek seçilmeden vurulmaz")
	rr = Damga.al(yeni, String(a0[0]))
	_check(rr["ok"] and Damga.has(yeni) and not Damga.has(String(a0[0])), "yuva dolu: %s silindi, %s vuruldu" % [String(a0[0]), yeni])
	# ekran yolu: adım 1 (silinecek seç)
	Game.run["damga_secildi"] = -1
	Game.run["damga_konak"] = -1
	Damga.yeni_konak(4242)
	main._on_npc("damga")
	DerinlikUI._girdi_damga(main, InputEventAction.new(), true, false)
	_check(DerinlikUI.damga_adim == 1, "yuva dolu: Boşluk silinecek Damgayı sorar")
	var hedef := String(Damga.teklif()[0])
	DerinlikUI._girdi_damga(main, InputEventAction.new(), true, false)
	_check(Damga.has(hedef) and Damga.etkin().size() == 1, "silinecek seçildi, yeni Damga vuruldu (%s)" % hedef)
	await get_tree().create_timer(1.2, true, false, true).timeout
	DerinlikUI._girdi_damga(main, InputEventAction.new(), true, false)
	# yuva 2 / 3
	Kodeks._k()["y"]["kara_boru_han"] = [1, 0]
	_check(Damga.yuva() == 2, "Kara Börü Han devrildi: 2 yuva")
	Kodeks._k()["y"]["sahmeran_ana"] = [1, 0]
	_check(Damga.yuva() == 3, "Şahmeran Ana devrildi: 3 yuva")
	# göç: eski kayıt (derinlik 7) üç yuva
	Kodeks._k()["y"].erase("kara_boru_han")
	Kodeks._k()["y"].erase("sahmeran_ana")
	Game.meta["best_depth"] = 7
	_check(Damga.yuva() == 3, "eski kayıt (en derin 7): 3 yuva")
	Game.meta["best_depth"] = 1
	# ---- etkiler: gerçek bölüm, gerçek yaratıklar
	await _bolum(2)
	lv = main.level
	var pl: Player = lv.player
	for e0 in get_tree().get_nodes_in_group("dusman"):
		if e0.global_position.distance_to(pl.global_position) < 600.0:
			e0.queue_free()
	await _frames(2)
	var e: Enemy = _dusman("kara_boru", false, 50.0)
	var e2: Enemy = _dusman("kara_boru", false, 80.0)
	await _frames(2)
	_check(e != null and e2 != null, "sınama yaratıkları kuruldu")
	Game.run["ongun"] = {"kurt": 0, "kartal": 0, "ayi": 0}
	var hk := func(id: String, opts := {}) -> float:
		Game.run["damga"] = [id]
		return Damga.hasar_k(pl, e, opts)
	# Kurt İzi
	Game.run["damga"] = ["kurt_izi"]
	Damga.kosu_basi()
	var h0 := Damga.hiz_k()
	Damga.oldurme(lv, e2)
	_check(h0 == 1.0 and is_equal_approx(Damga.hiz_k(), 1.3) and is_equal_approx(Damga.hasar_k(pl, e, {}), 1.15), "Kurt İzi: öldürünce hız x1,3, hasar x1,15")
	# uyum
	Game.run["ongun"] = {"kurt": 3, "kartal": 1, "ayi": 0}
	_check(Damga.uyum("kurt_izi") and is_equal_approx(Damga.hiz_k(), 1.0 + 0.3 * 1.25), "uyum: Kurt tomarı önde → x1,25 (hız %.3f)" % Damga.hiz_k())
	_check(not Damga.uyum("ayi_postu") and not Damga.uyum("ata_kesesi"), "uyum: başka renk / renksiz uyumsuz")
	Game.run["ongun"] = {"kurt": 0, "kartal": 0, "ayi": 0}
	_check(not Damga.uyum("kurt_izi"), "uyum: tomar yoksa yok")
	# Kartal Gözü
	Game.run["damga"] = ["kartal_gozu"]
	Damga.vurus_sonra(pl, e, {}, {"ok": true, "crit": true}, 10.0, false)
	_check(e.has_meta("damga_nisan"), "Kartal Gözü: uzak kritik nişanlar")
	_check(is_equal_approx(Damga.hasar_k(pl, e, {}), 1.45) and not e.has_meta("damga_nisan"), "Kartal Gözü: yakın vuruş +%45, nişan söner")
	# Ayı Postu
	Game.run["damga"] = ["ayi_postu"]
	Game.run["hp"] = float(Game.run["max_hp"]) * 0.3
	_check(is_equal_approx(Damga.alinan_k(pl, e), 0.7), "Ayı Postu: can %40 altında alınan hasar x0,7")
	Game.run["hp"] = float(Game.run["max_hp"])
	_check(is_equal_approx(Damga.alinan_k(pl, e), 1.0), "Ayı Postu: can yüksekken etkisiz")
	# Od Tamgası
	e.burn_t = 2.0
	_check(is_equal_approx(hk.call("od_tamgasi"), 1.2), "Od: yanana +%20")
	e2.burn_t = 0.0
	var e3: Enemy = _dusman("kara_boru", false, 30.0)
	e3.burn_t = 2.0
	Damga.oldurme(lv, e3)
	_check(e2.burn_t > 0.0, "Od: yanarken ölen ateşi yakındakine sıçrattı")
	e.burn_t = 0.0
	e2.burn_t = 0.0
	e3.queue_free()
	# Kam
	Game.run["damga"] = ["kam_tamgasi"]
	pl.sanat.cd = 10.0
	Damga.oldurme(lv, e2)
	_check(is_equal_approx(pl.sanat.cd, 9.0), "Kam: öldürme sanat beklemesini 1 sn kısalttı (%.1f)" % pl.sanat.cd)
	# Börü Yası
	Game.run["damga"] = ["boru_yasi"]
	Game.run["damga_dirildi"] = false
	Game.run["hp"] = 0.0
	var dir1 := Damga.olumcul(pl)
	_check(dir1 and is_equal_approx(float(Game.run["hp"]), float(Game.run["max_hp"]) * 0.3), "Börü Yası: %30 canla dirildi")
	_check(not Damga.olumcul(pl), "Börü Yası: koşuda bir kez")
	Game.run["hp"] = float(Game.run["max_hp"])
	# gerçek ölümcül darbe yolu (Player.take_hit)
	Game.run["damga_dirildi"] = false
	pl.inv_t = 0.0
	pl.roll_t = 0.0
	pl.take_hit(99999.0, e)
	_check(not pl.dead and float(Game.run["hp"]) > 0.0, "Börü Yası: Player.take_hit ölümcül darbede ölüm yok")
	Game.run["hp"] = float(Game.run["max_hp"])
	pl.inv_t = 0.0
	# Usul
	Game.run["damga"] = ["usul_tamgasi"]
	Game.run["hp"] = float(Game.run["max_hp"]) * 0.5
	var hp0 := float(Game.run["hp"])
	Damga._usul_t = -99.0
	Damga.vurus_sonra(pl, e, {}, {"damga_usul": true}, 10.0, false)
	_check(float(Game.run["hp"]) > hp0, "Usul: usulde isabet can verdi (+%.1f)" % (float(Game.run["hp"]) - hp0))
	for i in 6:
		Damga.vurus_sonra(pl, e, {}, {"damga_usul": true}, 10.0, false)
	_check(float(Game.run["hp"]) - hp0 <= pl.max_hp() * 0.031, "Usul: saniyede en çok %3")
	# Tulga
	Game.run["damga"] = ["tulga"]
	Damga.savusturma(pl)
	var o_t := {}
	var mt := Damga.hasar_k(pl, e, o_t)
	_check(is_equal_approx(mt, 1.3) and bool(o_t.get("force_crit", false)), "Tulga: savuşturma sonrası +%30 ve kesin kritik")
	var o_t2 := {}
	Damga.hasar_k(pl, e, o_t2)
	_check(not o_t2.has("force_crit"), "Tulga: kesin kritik bir kez")
	# Yel
	pl.rolled_t = 2.0
	_check(is_equal_approx(hk.call("yel_tamgasi"), 1.35), "Yel: yuvarlanma sonrası +%35")
	pl.rolled_t = 0.0
	_check(is_equal_approx(hk.call("yel_tamgasi"), 1.0), "Yel: yuvarlanmadan etkisiz")
	# Kan
	e.bleed = 2
	_check(is_equal_approx(hk.call("kan_tamgasi"), 1.2), "Kan: kanayana +%20")
	Game.run["hp"] = float(Game.run["max_hp"]) * 0.5
	hp0 = float(Game.run["hp"])
	e2.bleed = 2
	Damga.oldurme(lv, e2)
	_check(float(Game.run["hp"]) > hp0, "Kan: kanayanı öldürünce can")
	e.bleed = 0
	e2.bleed = 0
	# Ayaz
	e.freeze_t = 1.0
	_check(hk.call("ayaz_tamgasi") >= 1.25, "Ayaz: donmuşa +%25")
	e.freeze_t = 0.0
	var don_n := 0
	Damga.rng.seed = 5
	for i in 200:
		var oo := {}
		Game.run["damga"] = ["ayaz_tamgasi"]
		Damga.hasar_k(pl, e, oo)
		if oo.has("freeze"):
			don_n += 1
	_check(don_n > 8 and don_n < 40, "Ayaz: ~%%10 dondurma (%d / 200)" % don_n)
	# Ata Kesesi
	Game.run["damga"] = ["ata_kesesi"]
	_check(is_equal_approx(Damga.altin_k(), 1.4), "Ata Kesesi: altın x1,4")
	var altin_say := func() -> int:
		return lv.get_children().filter(func(c: Node) -> bool: return c is Pickup and c.kind == "gold").size()
	var pk0: int = altin_say.call()
	var es: Enemy = _dusman("kara_boru", true, 120.0)
	Damga.oldurme(lv, es)
	_check(int(altin_say.call()) == pk0 + 4, "Ata Kesesi: seçkin 4 altın fazla bıraktı")
	# Kut
	Game.run["damga"] = ["kut_tamgasi"]
	_check(is_equal_approx(Damga.kut_k(), 1.4), "Kut: dolum x1,4")
	pl.kut = 0.0
	Damga.oldurme(lv, es)
	_check(is_equal_approx(pl.kut, 25.0), "Kut: seçkin +25 Kut gücü")
	pl.kut = 0.0
	pl.add_kut(10.0)
	var kbeklenen := 10.0 * Damga.kut_k() * (1.0 + 0.2 * Game.umay_level("kut_hizi")) * (1.12 if pl.slot(pl.mel_slot).get("material", "") == "tunc" else 1.0)
	_check(is_equal_approx(pl.kut, kbeklenen), "Kut: Player.add_kut kancası (%.1f)" % pl.kut)
	es.queue_free()
	# Tengri
	Game.run["damga"] = ["tengri_tamgasi"]
	Damga.tetik.clear()
	Damga.vurus_sonra(pl, e, Game.run["slots"]["melee"], {"crit": true}, 20.0, false)
	_check(int(Damga.tetik.get("tengri_tamgasi", 0)) == 1, "Tengri: kritik şimşek sıçrattı")
	# Umay
	Game.run["damga"] = ["umay_tamgasi"]
	_check(is_equal_approx(Damga.sise_k(), 1.4), "Umay: şişe x1,4")
	Damga.icti()
	_check(is_equal_approx(Damga.alinan_k(pl, e), 0.5), "Umay: içince alınan hasar yarıya")
	Damga._umay_t = -99.0
	# Sürü
	var ms: float = hk.call("suru_tamgasi")
	_check(ms > 1.05 and ms <= 1.3001, "Sürü: yakındaki yaratıklar hasar katıyor (x%.2f)" % ms)
	# Demir
	Game.run["damga"] = []
	Game.run["damga_secildi"] = -1
	var mh0 := float(Game.run["max_hp"])
	Damga.al("demir_tamgasi")
	_check(is_equal_approx(float(Game.run["max_hp"]), mh0 * 1.2), "Demir: azami can +%20")
	Damga._birak("demir_tamgasi")
	_check(is_equal_approx(float(Game.run["max_hp"]), mh0), "Demir: silinince azami can geri döndü")
	# Erlik
	_check(is_equal_approx(hk.call("erlik_muhru"), 1.4) and is_equal_approx(Damga.alinan_k(pl, e), 1.25), "Erlik Mührü: hasar x1,4, alınan x1,25")
	# Okçu
	_check(is_equal_approx(hk.call("okcu_tamgasi", {"ok": true}), 1.25) and is_equal_approx(hk.call("okcu_tamgasi", {}), 1.0), "Okçu: yalnızca uzak vuruş +%25")
	# Balbal
	e.elite = true
	_check(is_equal_approx(hk.call("balbal_tamgasi"), 1.15) and is_equal_approx(Damga.alinan_k(pl, e), 0.85), "Balbal: seçkine +%15, ondan -%15")
	e.elite = false
	# entegrasyon: Player._deal kancası (Erlik Mührü hasarı, koşu özeti)
	Game.run["damga"] = []
	var oz: Dictionary = KosuOzet._oz()
	var v0 := float(oz["verilen"])
	e.hp = 99999.0
	e.max_hp = 99999.0
	pl._deal(e, 10.0, Game.run["slots"]["melee"], {"ok": true})
	var d_yok := float(oz["verilen"]) - v0
	Game.run["damga"] = ["erlik_muhru"]
	v0 = float(oz["verilen"])
	pl._deal(e, 10.0, Game.run["slots"]["melee"], {"ok": true})
	var d_erlik := float(oz["verilen"]) - v0
	_check(d_yok > 0.0 and d_erlik > d_yok * 1.15, "Player._deal: Erlik Mührü hasarı artırdı (%.1f → %.1f)" % [d_yok, d_erlik])
	Game.run["damga"] = []
	# HUD (etkin Damgalar) ve bot
	Game.run["damga"] = ["kurt_izi", "ayi_postu"]
	main.hud.queue_redraw()
	await _frames(2)
	_check(true, "HUD Damga sırası çizildi (hata yok)")
	Game.run["damga"] = []


# ================================================================== KODEKS
func _kodeks() -> void:
	_temiz_meta()
	main._new_run()
	await _bolum(1)
	var lv: Node = main.level
	var pl: Player = lv.player
	var ids := Kodeks.yaratiklar()
	_check(ids.size() >= 50, "kodekste %d yaratık / boss" % ids.size())
	var boss_n := 0
	for id in ids:
		if Kodeks.boss_mu(id):
			boss_n += 1
	_check(boss_n == 5, "5 boss sayfası (%d)" % boss_n)
	var zaafsiz: Array = []
	for id in ids:
		if Kodeks.zaaf(id) == "":
			zaafsiz.append(id)
	_check(zaafsiz.is_empty(), "her yaratığın zaafı yazılı %s" % str(zaafsiz))
	var t0 := Kodeks.tamamlanma()
	_check(t0 >= 0.0 and t0 < 0.2, "yeni kayıtta tamamlanma düşük (%%%d)" % int(t0 * 100))
	# gerçek öldürme yolu
	var e: Enemy = _dusman("kara_boru", false, 60.0)
	await _frames(1)
	var k0 := Kodeks.oldurme("kara_boru")
	e.take_hit(999999.0, {"dir": 1.0, "kb": 60.0})
	await _frames(1)
	_check(Kodeks.oldurme("kara_boru") == k0 + 1, "gerçek öldürme kodekse yazıldı (%d)" % Kodeks.oldurme("kara_boru"))
	_check(int((Game.run["oz"]["oldurme"] as Dictionary).get("kara_boru", 0)) == 1, "koşu özeti av defterine yazıldı")
	_check(not Kodeks.zaaf_acik("kara_boru"), "zaaf 1 öldürmede kapalı")
	for i in Kodeks.ZAAF_N - 1:
		var ex: Enemy = _dusman("kara_boru", false, 60.0)
		await _frames(1)
		ex.take_hit(999999.0, {"dir": 1.0, "kb": 60.0})
		await _frames(1)
	_check(Kodeks.zaaf_acik("kara_boru") and not Kodeks.bilgi_acik("kara_boru"), "zaaf %d öldürmede açıldı, bilgi kapalı" % Kodeks.ZAAF_N)
	Kodeks._k()["y"]["kara_boru"] = [Kodeks.BILGI_N, 0]
	_check(Kodeks.bilgi_acik("kara_boru"), "bilgi %d öldürmede açıldı" % Kodeks.BILGI_N)
	# seçkin sayacı
	var s0 := int(Kodeks._k()["seckin"])
	var es: Enemy = _dusman("kara_boru", true, 60.0)
	await _frames(1)
	es.take_hit(9999999.0, {"dir": 1.0, "kb": 60.0})
	await _frames(1)
	_check(int(Kodeks._k()["seckin"]) == s0 + 1, "seçkin öldürme sayıldı")
	# boss zaafı 1 öldürmede
	Kodeks._k()["y"]["tepegoz"] = [1, 0]
	_check(Kodeks.zaaf_acik("tepegoz") and Kodeks.zaaf("tepegoz").contains("göz"), "boss zaafı 1 öldürmede (Tepegöz)")
	# seni devirdi
	Kodeks.devirdi("kara_boru")
	_check(Kodeks.devirme("kara_boru") == 1, "seni devirme sayısı")
	# silah görülme: kuşanma (on_equip)
	pl.on_equip()
	var mel := String(Game.run["slots"]["melee"].get("id", ""))
	_check(Kodeks.silah_gorulen(mel), "kuşanılan silah görüldü (%s)" % mel)
	var sl := Kodeks.silahlar()
	_check(sl.size() >= 60, "silah kitaplığı %d eşya" % sl.size())
	# silah öldürmesi (Player._deal → KosuOzet.vurus → Kodeks.silah_oldur)
	var e4: Enemy = _dusman("kara_boru", false, 40.0)
	await _frames(1)
	e4.hp = 1.0
	var sk0 := Kodeks.silah_oldurme(mel)
	pl._deal(e4, 50.0, Game.run["slots"]["melee"], {"ok": true})
	await _frames(1)
	_check(Kodeks.silah_oldurme(mel) == sk0 + 1, "silahın öldürmesi kodekse yazıldı")
	# kavanoz (ky-kavanoz44; yalnızca okunur)
	Game.meta["kavanoz"] = {mel: 1}
	_check(Kodeks.kavanozda(mel), "kavanoz verisi okunuyor (meta.kavanoz)")
	Game.meta.erase("kavanoz")
	# destan kayıtları
	var ds := Kodeks.destan_kayitlari()
	_check(ds.size() >= 10, "destan sayfaları %d (örgü, görüm, taş yazıt)" % ds.size())
	# göç: kodekssiz eski kayıt
	var m_eski := {"runs": 50, "unlocked": ["ayaz_kilici"], "best_depth": 6}
	Game.meta = m_eski
	Hikaye.meta_hazirla()
	Kodeks.meta_hazirla()
	_check(Game.meta.get("kodeks") is Dictionary and Kodeks.silah_gorulen("ayaz_kilici") and Kodeks.silah_gorulen("alp_kilici"), "göç: eski kayıtta kodeks kuruldu, açılan silahlar görüldü")
	_check(int(Game.meta["kodeks"]["surum"]) == 44, "kodeks sürüm 44")
	Basarim.meta_hazirla()
	# tamamlanma artar
	_temiz_meta()
	var ta := Kodeks.tamamlanma()
	for id in ids.slice(0, 20):
		Kodeks._k()["y"][id] = [6, 0]
	_check(Kodeks.tamamlanma() > ta + 0.1, "tamamlanma öldürmelerle arttı (%%%d → %%%d)" % [int(ta * 100), int(Kodeks.tamamlanma() * 100)])
	# ekran: duraklatmadan C, sekmeler, geri
	get_tree().paused = true
	main.hud.mode = "play"
	var ev := InputEventKey.new()
	ev.physical_keycode = KEY_C
	ev.pressed = true
	main._unhandled_input(ev)
	_check(main.hud.mode == "kodeks", "duraklatmada C kodeksi açtı")
	for i in DerinlikUI.SEKMELER.size():
		DerinlikUI._girdi_kodeks(main, _ev("techizat2"), false, false)
		main.hud.queue_redraw()
		await _frames(2)
	_check(DerinlikUI.sekme == 0, "R ile 6 sekme dolaşıldı (çizim hatasız)")
	DerinlikUI._girdi_kodeks(main, _ev("asagi"), false, false)
	_check(DerinlikUI.sec == 6, "S bir satır aşağı (6 sütun)")
	DerinlikUI._girdi_kodeks(main, _ev("duraklat"), false, true)
	_check(main.hud.mode == "play" and get_tree().paused, "Esc: duraklatmaya döndü")
	# Ozan'dan R
	main.hud.mode = "ozan"
	DerinlikUI.girdi(main, _ev("techizat2"))
	_check(main.hud.mode == "kodeks" and DerinlikUI.geri == "ozan", "Ozan ekranında R kodeksi açtı")
	DerinlikUI._girdi_kodeks(main, _ev("duraklat"), false, true)
	_check(main.hud.mode == "ozan", "kodeksten Ozan'a dönüldü")
	main._start_play()


# ================================================================== ÖZET
func _ozet() -> void:
	_temiz_meta()
	main._new_run()
	await _bolum(3)
	var lv: Node = main.level
	var pl: Player = lv.player
	var it: Dictionary = Game.run["slots"]["melee"]
	KosuOzet.vurus(123.0, it, false)
	KosuOzet.vurus(40.0, it, false)
	var oz: Dictionary = KosuOzet._oz()
	_check(is_equal_approx(float(oz["verilen"]), 163.0) and is_equal_approx(float(oz["en_iyi"]), 123.0), "verilen hasar ve en ağır vuruş")
	_check(String(oz["en_iyi_silah"]) == String(it.get("name", "")), "en ağır vuruşun silahı")
	KosuOzet.kombo(17)
	KosuOzet.kombo(9)
	_check(int(oz["kombo"]) == 17, "en yüksek kombo 17")
	KosuOzet.sinav()
	KosuOzet.otag()
	_check(int(oz["sinav"]) == 1 and int(oz["otag"]) == 1, "sınav ve otağ sayıldı")
	# gerçek hasar alma (Player.take_hit) ve ölüm akışı
	var e: Enemy = _dusman("cor", false, 40.0)
	await _frames(1)
	pl.inv_t = 0.0
	pl.roll_t = 0.0
	Game.run["hp"] = 50.0
	pl.take_hit(10.0, e)
	_check(float(oz["alinan"]) >= 9.0 and String(oz.get("son_vuran", "")) == "cor", "alınan hasar ve son vuran kaydı (%.1f, %s)" % [float(oz["alinan"]), String(oz.get("son_vuran", ""))])
	Game.run["kills"] = 42
	Game.run["altin_kazanc"] = 210
	Game.run["kut_kazanc"] = 33
	pl.inv_t = 0.0
	pl.take_hit(999999.0, e)
	for i in 900:
		await get_tree().process_frame
		if main.hud.mode == "dead":
			break
	_check(main.hud.mode == "dead", "ölüm: özet sayfası (dead)")
	var s: Dictionary = DerinlikUI.son_ozet
	_check(not s.is_empty() and String(s.get("neden", "")) == "cor" and int(s.get("derinlik", 0)) == 3, "özet: ölüm nedeni Çor Ruhu, derinlik 3")
	_check(int(s["oldurme"]) == 42 and int(s["altin"]) == 210 and int(s["kut"]) == 33 and int(s["kombo"]) == 17, "özet: öldürme, altın, Kut, kombo")
	_check(Kodeks.devirme("cor") == 1, "kodeks: Çor Ruhu seni 1 kez devirdi")
	var rk: Dictionary = Game.meta["rekor"]
	_check(float(rk.get("derinlik", 0)) == 3.0 and float(rk.get("oldurme", 0)) == 42.0, "rekorlar yazıldı")
	_check((s["yeni"] as Array).is_empty(), "ilk koşuda 'yeni rekor' mührü yok")
	_check((Game.meta["rekor_m"] as Dictionary).has("0"), "Mühür kademesi 0 rekorları")
	_check((Game.meta["gecmis"] as Array).size() == 1, "son koşular geçmişi 1")
	var s_tekrar := KosuOzet.bitir(false)
	_check(s_tekrar == Game.run["ozet"] and (Game.meta["gecmis"] as Array).size() == 1, "bitir bir koşuda bir kez")
	main.hud.queue_redraw()
	await _frames(2)
	# yeni koşu: daha derin → YENİ REKOR
	main._new_run()
	main._after_intro()
	await _bolum(5)
	Game.run["kills"] = 10
	var s2 := KosuOzet.bitir(false)
	_check("derinlik" in s2["yeni"] and not ("oldurme" in s2["yeni"]), "daha derin: derinlik rekoru mühürlendi, öldürme değil")
	# zafer ve en hızlı zafer
	Game.new_run()
	Game.run["depth"] = 10
	Game.run["time"] = 1500.0
	var w0 := int(Game.meta.get("wins", 0))
	DerinlikUI.ozet_kur(true)
	_check(float(Game.meta["rekor"].get("hizli_zafer", -1.0)) == 1500.0 and int(Game.meta["wins"]) == w0 + 1, "zafer: en hızlı zafer ve zafer sayısı")
	Game.new_run()
	Game.run["depth"] = 10
	Game.run["time"] = 1200.0
	var s3 := KosuOzet.bitir(true)
	_check("hizli_zafer" in s3["yeni"] and float(Game.meta["rekor"]["hizli_zafer"]) == 1200.0, "daha hızlı zafer: rekor (küçük olan iyi)")
	# Mühür kademesi
	Game.new_run()
	Game.run["muhur"] = 2
	Game.run["depth"] = 4
	KosuOzet.bitir(false)
	_check(float(Game.meta["rekor_m"]["2"]["derinlik"]) == 4.0, "Mühür 2 kademesi ayrı rekor")
	# ky-ngp44 muhur_kayit (varsa) rekor sayfasında
	Game.meta["muhur_kayit"] = {"3": {"derinlik": 7, "sure": 2222}}
	DerinlikUI.sekme = 5
	main.hud.mode = "kodeks"
	main.hud.queue_redraw()
	await _frames(2)
	_check(true, "rekor sayfası muhur_kayit ile çizildi")
	Game.meta.erase("muhur_kayit")
	# zafer ekranı
	main.hud.mode = "zafer"
	main.hud.queue_redraw()
	await _frames(2)
	DerinlikUI._t0 = -99.0
	DerinlikUI.girdi(main, InputEventAction.new())
	var go := InputEventKey.new()
	go.physical_keycode = KEY_ENTER
	go.pressed = true
	DerinlikUI.girdi(main, go)
	_check(main.hud.mode == "play", "zafer ekranından Enter ile yola")
	_check((Game.meta["gecmis"] as Array).size() <= 12, "geçmiş en çok 12")


# ================================================================== BAŞARIM
func _basarim() -> void:
	_temiz_meta()
	main._new_run()
	await _bolum(1)
	_check(Basarim.B.size() == 25, "25 Destan Başarısı (%d)" % Basarim.B.size())
	var ok_ikon := true
	for id in Basarim.B:
		var b: Array = Basarim.B[id]
		ok_ikon = ok_ikon and InkUI.has_icon(String(b[2])) and String(b[3]) in ["kut", "renk", "soz"]
		if String(b[3]) == "renk":
			ok_ikon = ok_ikon and Basarim.RENK.has(String(b[4]))
	_check(ok_ikon, "her başarımın mürekkep simgesi ve geçerli ödülü var")
	_check(Basarim.acik_sayi() == 0, "yeni kayıtta açık başarım yok")
	# ilk kan: gerçek öldürme
	var e: Enemy = _dusman("kara_boru", false, 60.0)
	await _frames(1)
	e.take_hit(999999.0, {"dir": 1.0, "kb": 60.0})
	await _frames(1)
	_check(Basarim.acik("ilk_kan") and not Basarim.kuyruk.is_empty(), "İlk Kan açıldı, bildirim kuyruğunda")
	_check(not Basarim.ozan_dizeleri().is_empty(), "söz ödülü: Ozan dizesi eklendi")
	main.hud.queue_redraw()
	await _frames(2)
	# Kut ödülü
	var bank0 := int(Game.meta.get("kut_bank", 0))
	Kodeks._k()["y"]["kara_boru_han"] = [1, 0]
	Basarim.olay("boss")
	_check(Basarim.acik("kara_boru") and int(Game.meta["kut_bank"]) == bank0 + 20, "Kara Börü Han: +20 Kut")
	# renk ödülü ve seçim
	Kodeks._k()["y"]["kara_boru"] = [100, 0]
	Basarim.olay("oldurme")
	_check(Basarim.acik("yuz_bas") and Basarim.renk_acik("kizil"), "Yüz Baş: kızıl çerçeve açıldı")
	DerinlikUI.sekme = 4
	DerinlikUI.sec = Basarim.B.keys().find("yuz_bas")
	main.hud.mode = "kodeks"
	DerinlikUI._girdi_kodeks(main, InputEventAction.new(), true, false)
	_check(String(Game.meta.get("hud_renk", "")) == "kizil" and Basarim.hud_renk() == Basarim.RENK["kizil"][1], "Boşluk: HUD çerçevesi kızıl")
	DerinlikUI._girdi_kodeks(main, InputEventAction.new(), true, false)
	_check(String(Game.meta.get("hud_renk", "")) == "", "ikinci Boşluk: varsayılana döndü")
	DerinlikUI.sec = Basarim.B.keys().find("bin_bas")
	DerinlikUI._girdi_kodeks(main, InputEventAction.new(), true, false)
	_check(String(Game.meta.get("hud_renk", "")) == "", "kapalı başarımın rengi seçilemez")
	main._start_play()
	# derinlik, damga, altın, ad, konak koşulları
	Game.meta["best_depth"] = 5
	Basarim.olay("konak")
	_check(Basarim.acik("derin5") and not Basarim.acik("derin10"), "Beşinci Kat (10 değil)")
	Game.run["damga_secildi"] = -1
	Damga.al("kurt_izi")
	_check(Basarim.acik("damga_ilk"), "İlk Tamga")
	Kodeks._k()["y"]["sahmeran_ana"] = [1, 0]
	Game.run["damga"] = ["kurt_izi", "ayi_postu", "kam_tamgasi"]
	Basarim.olay("damga")
	_check(Basarim.acik("damga_uc") and Basarim.acik("sahmeran"), "Üç Tamgalı ve Şahmeran'ın Sırrı")
	Game.run["ongun"] = {"kurt": 3, "kartal": 0, "ayi": 1}
	Basarim.olay("damga")
	_check(Basarim.acik("damga_uyum"), "Ongun Uyumu (Kurt İzi + 3 Kurt tomarı)")
	Game.run["gold"] = 520
	Basarim.olay("oldurme")
	_check(Basarim.acik("sartak"), "Sartak'ın Dostu (500 altın)")
	Game.meta["adlar"] = {"basat": 1, "bogac": 1, "segrek": 1}
	Basarim.olay("konak")
	_check(Basarim.acik("ad_sahibi"), "Ad Sahibi (3 ad)")
	Game.run["depth"] = 3
	Game.run["time"] = 400.0
	Game.run["scrolls"] = 0
	Basarim.olay("konak", {"hasarsiz": true})
	_check(Basarim.acik("yel_gibi") and Basarim.acik("ciplak") and Basarim.acik("dokunulmaz"), "Yel Gibi, Çıplak Yiğit, Dokunulmaz")
	var oz: Dictionary = KosuOzet._oz()
	oz["kombo"] = 60
	oz["en_iyi"] = 320.0
	Basarim.olay("oldurme")
	_check(Basarim.acik("kombo") and Basarim.acik("dag_yaran"), "Destan Kombosu ve Dağ Yaran")
	# Main._to_konak akışı: hasarsız bölüm
	_temiz_meta()
	main._new_run()
	await _bolum(1)
	Game.run["kills"] = 3
	KosuOzet._oz()["bolum_alinan"] = 0.0
	main._to_konak()
	await _frames(3)
	_check(Basarim.acik("dokunulmaz") and float(Game.run["oz"]["bolum_alinan"]) == 0.0, "konağa varış: Dokunulmaz (Main._to_konak)")
	# bildirim kuyruğu akar (4,6 sn)
	var n0 := Basarim.kuyruk.size()
	_check(n0 >= 1, "kuyrukta %d bildirim" % n0)
	if n0 > 0:
		Basarim.kuyruk[0][1] = Game.clock() - 5.0
		main.hud.queue_redraw()
		await _frames(3)
		_check(Basarim.kuyruk.size() == n0 - 1, "süresi dolan bildirim kuyruktan çıktı")
	# sessiz göç: eski kayıt hak ettiğini bildirimsiz alır
	Basarim.kuyruk.clear()
	Game.meta = {"runs": 300, "best_depth": 10, "unlocked": [], "son_izlendi": true}
	Hikaye.meta_hazirla()
	Kodeks.meta_hazirla()
	Basarim.meta_hazirla()
	_check(Basarim.acik("derin10") and Basarim.acik("tan") and Basarim.kuyruk.is_empty(), "göç: eski kayıt (derinlik 10, tan) sessizce açtı")


# ================================================================== çekimler
func _ornek_meta() -> void:
	## Görsel çekim için dolu bir kayıt: yaratıkların çoğu görülmüş, silahlar, Damgalar, başarımlar, rekorlar, geçmiş
	_temiz_meta()
	var ids := Kodeks.yaratiklar()
	for i in ids.size():
		if i % 7 == 6:
			continue
		Kodeks._k()["y"][ids[i]] = [[1, 3, 6, 14, 22, 40][i % 6], 1 if i % 5 == 0 else 0]
	var sl := Kodeks.silahlar()
	for i in sl.size():
		if i % 4 != 3:
			Kodeks._k()["s"][sl[i]] = [1, (i * 7) % 60]
	var dl := Damga.ids()
	for i in dl.size():
		if i % 3 != 2:
			Kodeks._k()["d"][dl[i]] = 1 + i % 4
			Kodeks._k()["dg"].append(dl[i])
	Game.meta["gun_parca"] = ["kara_boru_han", "tepegoz"]
	Game.meta["gorumler"] = ["biyom:otuken", "biyom:bozkir", "biyom:sahmeran", "biyom:kaf", "biyom:tamu", "oda:otuken:0", "oda:otuken:1", "oda:bozkir:0"]
	for bb in ["otuken", "bozkir", "sahmeran", "kaf", "tamu"]:
		Game.meta["gorumler"].append("acilis:" + bb)   # çekimde bölüm açılış sineması oynamasın
	Game.meta["best_depth"] = 7
	Game.meta["runs"] = 38
	Game.meta["wins"] = 1
	Game.meta["rekor"] = {"derinlik": 7.0, "oldurme": 412.0, "kombo": 48.0, "en_iyi": 286.0, "verilen": 41250.0, "hizli_zafer": 2310.0}
	Game.meta["rekor_m"] = {"0": {"derinlik": 10.0, "oldurme": 412.0, "hizli_zafer": 2310.0}, "1": {"derinlik": 7.0, "oldurme": 260.0}, "2": {"derinlik": 4.0, "oldurme": 120.0}}
	Game.meta["gecmis"] = [{"d": 2, "t": 410, "k": 60, "z": false, "dm": []}, {"d": 4, "t": 900, "k": 150, "z": false, "dm": ["kurt_izi"]},
		{"d": 3, "t": 700, "k": 110, "z": false, "dm": ["ayi_postu"]}, {"d": 6, "t": 1500, "k": 260, "z": false, "dm": ["kurt_izi", "od_tamgasi"]},
		{"d": 10, "t": 2310, "k": 412, "z": true, "dm": ["kurt_izi", "od_tamgasi", "suru_tamgasi"]}, {"d": 5, "t": 1300, "k": 220, "z": false, "dm": ["kartal_gozu", "okcu_tamgasi"]},
		{"d": 7, "t": 1900, "k": 330, "z": false, "dm": ["tulga", "balbal_tamgasi", "demir_tamgasi"]}]
	Game.meta["adlar"] = {"basat": 2, "bogac": 1}
	Basarim.sessiz = true
	Basarim.olay("goc")
	Basarim.sessiz = false
	Basarim.kuyruk.clear()


func _ekran_kur() -> void:
	var bekle := 6.0
	for a in OS.get_cmdline_user_args():
		if String(a).begins_with("--bekle="):
			bekle = float(String(a).trim_prefix("--bekle="))
	_ornek_meta()
	main._new_run()
	await _frames(2)
	Game.run["ongun"] = {"kurt": 3, "kartal": 1, "ayi": 1}
	Game.run["gold"] = 186
	match _ekran:
		"damga", "damga_vur":
			Game.run["damga"] = ["ayi_postu"]
			await _konak(4)
			var lv: Node = main.level
			Game.run["damga_konak"] = -1
			Damga.yeni_konak(20)
			var tk: Array = Damga.teklif()
			if not ("kurt_izi" in tk) and not Damga.has("kurt_izi"):
				tk[0] = "kurt_izi"
			for n in lv.npcs:
				if n is DamgaTasi:
					lv.player.global_position = n.global_position + Vector2(-20, -2)
			await _frames(10)
			DerinlikUI.damga_ac(main)
			DerinlikUI.damga_sec = 0
			if _ekran == "damga_vur":
				while Time.get_ticks_msec() < int((bekle - 2.5) * 1000.0):
					await get_tree().process_frame
				DerinlikUI._vur(main, String(tk[0]), "")
		"damga_dunya":
			await _konak(4)
			var lv: Node = main.level
			for n in lv.npcs:
				if n is DamgaTasi:
					lv.player.global_position = n.global_position + Vector2(-28, -2)
		"hud", "toast":
			Game.run["damga"] = ["kurt_izi", "od_tamgasi", "suru_tamgasi"]
			Game.meta["hud_renk"] = "kizil"
			await _bolum(3)
			if _ekran == "toast":
				while Time.get_ticks_msec() < int((bekle - 2.5) * 1000.0):
					await get_tree().process_frame
				Game.meta["basarim"].erase("dag_yaran")
				Basarim.ac("dag_yaran")
		"kodeks_yaratik", "kodeks_silah", "kodeks_damga", "kodeks_destan", "kodeks_basarim", "rekor":
			await _bolum(2)
			get_tree().paused = true
			var sek := {"kodeks_yaratik": 0, "kodeks_silah": 1, "kodeks_damga": 2, "kodeks_destan": 3, "kodeks_basarim": 4, "rekor": 5}
			DerinlikUI.kodeks_ac(main, int(sek[_ekran]))
			match _ekran:
				"kodeks_yaratik":
					DerinlikUI.sec = maxi(0, Kodeks.yaratiklar().find("surale"))
				"kodeks_silah":
					DerinlikUI.sec = maxi(0, Kodeks.silahlar().find("ayaz_kilici"))
				"kodeks_damga":
					DerinlikUI.sec = 0
				"kodeks_destan":
					DerinlikUI.sec = 5
				"kodeks_basarim":
					DerinlikUI.sec = 1
		"ozet":
			Game.run["damga"] = ["kartal_gozu", "okcu_tamgasi", "tengri_tamgasi"]
			await _bolum(5)
			var lv: Node = main.level
			var pl: Player = lv.player
			var oz := KosuOzet._oz()
			oz["verilen"] = 18420.0
			oz["alinan"] = 1260.0
			oz["en_iyi"] = 312.0
			oz["en_iyi_silah"] = "Ayaz Kılıcı"
			oz["kombo"] = 41
			oz["seckin"] = 7
			oz["sinav"] = 5
			oz["otag"] = 3
			oz["silahlar"] = ["Ayaz Kılıcı", "Türk Yayı", "Kurt Pençesi"]
			oz["oldurme"] = {"kara_boru": 34, "cor": 21, "balbal": 12, "kurgan_bekcisi": 9, "surale": 6, "arcura": 5, "tozkoparan": 2}
			Game.run["kills"] = 89
			Game.run["time"] = 1714.0
			Game.run["altin_kazanc"] = 640
			Game.run["kut_kazanc"] = 96
			Game.run["scrolls"] = 9
			Game.meta["rekor"]["en_iyi"] = 290.0
			var e: Enemy = _dusman("agac_iyesi", false, 50.0)
			await _frames(2)
			pl.inv_t = 0.0
			pl.roll_t = 0.0
			pl.take_hit(999999.0, e)
		"zafer":
			Game.run["damga"] = ["kurt_izi", "od_tamgasi", "suru_tamgasi"]
			Game.run["depth"] = 10
			Game.run["time"] = 2190.0
			Game.run["kills"] = 438
			Game.run["altin_kazanc"] = 1820
			Game.run["kut_kazanc"] = 310
			var oz2 := KosuOzet._oz()
			oz2["verilen"] = 96200.0
			oz2["alinan"] = 3900.0
			oz2["en_iyi"] = 512.0
			oz2["en_iyi_silah"] = "Erlik Tırpanı"
			oz2["kombo"] = 58
			oz2["seckin"] = 22
			oz2["oldurme"] = {"kara_atli": 40, "od_iyesi": 31, "tamu_bekcisi": 28, "kayip_ruh": 60, "erlik_han": 1, "yasavul": 12}
			oz2["silahlar"] = ["Erlik Tırpanı", "Akıncı Yayı"]
			DerinlikUI.ozet_kur(true)
			Game.new_run()
			main._build_hub()
			main._start_play()
			main.hud.mode = "zafer"
			get_tree().paused = true
	_p("çekim kuruldu: %s" % _ekran)
