extends Node
## v44 Ata Kurganı / Silah Küpleri testi: godot --headless --path . --quit-after 6000 -- --yurt --kavanoz
##   DURUM:   denetimli kayıtla (açılanlar, parşömenler, keşif) yurt kurulur: temel eşya / keşfedilen açık, parşömeni olan
##            "parsomen", gelişmiş ve hiç ele geçmemiş "kilitli"; küp sayısı = silah + kalkan (+ Rastgele), sayaç yazısı.
##   YENİ:    Kupler.kesfet → YENİ + uyanış (oyuncu duvarın önünde, oyun akarken mühür kırılır, silah renge döner, uyandi),
##            kart görülünce YENİ söner; Level.equip (koşuda ilk kuşanma) ve Demirci (Main._demirci_ac) küpü açar.
##   SEÇİM:   W → gezme kipi (hud.mode "kupler"), imleç, açık küpte seçim → yurttaki koşunun yuvası hemen değişir, kayıt
##            tutar; Game.new_run (sonraki koşu) seçilen silahla başlar; ikincil yuva (atma / yay / kalkan) ayrı; aynı küp
##            yeniden seçilince varsayılana döner; kilitli küp seçilemez; test kipi (Kupler.devre_disi) seçimi yok sayar.
##   RASTGELE: 10 küpten önce kilitli; sonra açık küplerden rastgele yakın dövüş silahı, nadirlik +1.
##   EŞİK:    20 küpte +25 altın, 30'da +%5 can (data/kupler.json).
##   KAPI:    seçimden sonra Kut Kapısı → 1. derinlik bu silahla.
## Çekim kipleri (--goruntu ile, headless değil): --kavanoz_ekran=duvar | yakin | gez | uyanis | kosu
## Çıktı "[kavanoz] ..." satırları, sonda "[kavanoz] SONUC GECTI|KALDI". Kalıcı kayıt test sonunda (ve çıkışta) geri yazılır.

var main: Node
var _fail: Array = []
var _meta0: Dictionary = {}
var _ekran := ""
var _geri := false


func _ready() -> void:
	process_mode = Node.PROCESS_MODE_ALWAYS
	for a in OS.get_cmdline_user_args():
		if String(a).begins_with("--kavanoz_ekran="):
			_ekran = String(a).trim_prefix("--kavanoz_ekran=")
	_meta0 = Game.meta.duplicate(true)
	_run.call_deferred()


func _exit_tree() -> void:
	_geri_yaz()


func _geri_yaz() -> void:
	if _geri:
		return
	_geri = true
	Game.meta = _meta0.duplicate(true)
	Game.save_meta()


func _p(s: String) -> void:
	print("[kavanoz] ", s)


func _check(ok: bool, what: String) -> void:
	_p(("TAMAM " if ok else "HATA ") + what)
	if not ok:
		_fail.append(what)


func _frames(n: int) -> void:
	for i in n:
		await get_tree().process_frame


func _sure(sn: float) -> void:
	await get_tree().create_timer(sn, true, false, true).timeout


func _kayit(kesif: Array, bps: Array, unlocked: Array, secim := {}) -> void:
	Game.meta["unlocked"] = unlocked.duplicate()
	Game.meta["blueprints"] = bps.duplicate()
	Game.meta["kup"] = {"kesif": kesif.duplicate(), "yeni": [], "uyandi": [], "secim": secim.duplicate()}


func _yurt() -> void:
	main._build_hub()
	main._start_play()
	await _frames(4)


func _kg() -> KupGaleri:
	return main.level.kup_galeri


func _kup(id: String) -> Dictionary:
	for k in _kg().kupler:
		if k["id"] == id:
			return k
	return {}


func _oyuncu_onune(id: String) -> void:
	var k := _kup(id)
	var pl: Node2D = main.level.player
	pl.global_position = Vector2(_kg().global_position.x + (k["pos"] as Vector2).x, _kg().global_position.y - 2.0)
	pl.velocity = Vector2.ZERO


func _run() -> void:
	await _frames(5)
	if _ekran != "":
		await _ekran_kur()
		return
	await _durumlar()
	await _yeni_uyanis()
	await _secim()
	await _rastgele_esik()
	await _demirci_ve_kusanma()
	await _kapi()
	_geri_yaz()
	_p("kalıcı kayıt geri yüklendi")
	_p("SONUC %s%s" % ["GECTI" if _fail.is_empty() else "KALDI", "" if _fail.is_empty() else " (" + ", ".join(_fail) + ")"])
	get_tree().quit()


# ------------------------------------------------------------------ durumlar ve sayaç
func _durumlar() -> void:
	_kayit(["kargi"], ["civili_topuz"], [])
	await _yurt()
	var kg := _kg()
	_check(kg != null, "yurtta küp galerisi kuruldu")
	var n_w := 0
	for it in Data.items["weapons"]:
		n_w += 1 if it.get("impl", false) else 0
	var n_s := 0
	for it in Data.items["shields"]:
		n_s += 1 if it.get("impl", false) else 0
	_check(Kupler.toplam() == n_w + n_s and kg.kupler.size() == n_w + n_s + 1, "küp sayısı = silah %d + kalkan %d (+ Rastgele) = %d" % [n_w, n_s, kg.kupler.size()])
	_check(kg.kupler.size() <= KupGaleri.SUTUN * KupGaleri.RAF_Y.size(), "küpler duvara sığar (%d <= %d)" % [kg.kupler.size(), KupGaleri.SUTUN * KupGaleri.RAF_Y.size()])
	for pair in [["alp_kilici", "acik"], ["turk_yayi", "acik"], ["kargi", "acik"], ["civili_topuz", "parsomen"], ["erlik_tirpani", "kilitli"],
			["yatagan", "kilitli"], [Kupler.RASTGELE, "kilitli"]]:
		var k := _kup(pair[0])
		_check(not k.is_empty() and k["durum"] == pair[1] and Kupler.durum(pair[0]) == pair[1], "%s küpü: %s (%s)" % [pair[0], pair[1], str(k.get("durum", "?"))])
	var kk := _kup("erlik_tirpani")
	_check((kk["silah"] as Sprite2D).modulate.r < 0.05 and (kk["halo"] as Sprite2D).modulate.a < 0.2, "kilitli küpte silah kara gölge, ışık sönük")
	var ka := _kup("kargi")
	_check((ka["silah"] as Sprite2D).modulate == Color(1, 1, 1, 1) and (ka["halo"] as Sprite2D).visible, "açık küpte silah renkli, Kut ışığı var")
	_check(Kupler.ipucu("erlik_tirpani").find("Parşömeni") >= 0 and Kupler.ipucu("civili_topuz").find("Demirci") >= 0 and Kupler.ipucu("yatagan").find("kuşan") >= 0, "ipuçları: parşömen / Demirci / kuşan")
	# temel: alp_kilici, turk_yayi, yuvarlak_kalkan, pala, coban_sapani (kara_barut teçhizat, küpü yok) + kargi
	_check(Kupler.acilan() == 6, "açılan sayısı 6 (%d)" % Kupler.acilan())
	_check(kg._sayac.text == "Açılan silahlar 6/%d" % Kupler.toplam(), "sayaç yazısı: %s" % kg._sayac.text)
	# sıra: sınıflar gruplu (kılıçlar önce, kalkanlar sonda, Rastgele en son)
	var ids: Array = Kupler.liste()
	_check(Kupler.sinif(String(ids[0])) == "slash" and Kupler.sinif(String(ids[ids.size() - 2])) == "shield" and ids[ids.size() - 1] == Kupler.RASTGELE, "sıra: kılıç ... kalkan, Rastgele")
	# yürürken kart: oyuncu kargı küpünün sütununda (alt raf satırı) → seçili küp o sütun
	_oyuncu_onune("alp_kilici")
	await _frames(3)
	_check(kg.yakin and kg.secili % KupGaleri.SUTUN == _kup("alp_kilici")["i"] % KupGaleri.SUTUN, "duvarın önünde: sütundaki küp vurgulanır (secili %d)" % kg.secili)
	main.level.player.global_position.x = 900.0
	await _frames(3)
	_check(not kg.yakin and kg.secili == -1, "duvardan uzaklaşınca kart kapanır")


# ------------------------------------------------------------------ yeni küp ve uyanış
func _yeni_uyanis() -> void:
	var kg := _kg()
	_check(Kupler.kesfet("yatagan"), "yatağan ilk kez ele geçti: küp açıldı (yeni)")
	_check(not Kupler.kesfet("yatagan"), "ikinci kez: yeni değil")
	_check(Kupler.yeni_mi("yatagan") and not Kupler.uyandi_mi("yatagan"), "yatağan YENİ, henüz uyanmadı")
	kg.acildi("yatagan")
	var k := _kup("yatagan")
	_check(k["durum"] == "kilitli", "uyanmadan önce eski hâlinde (kilitli görünür)")
	_oyuncu_onune("yatagan")
	main.level.player.global_position.x += 60.0   # kartı hemen görmesin (YENİ etiketi uyanıştan sonra denetlenir)
	await _sure(2.2)
	_check(Kupler.uyandi_mi("yatagan") and k["durum"] == "acik", "uyanış oynadı: küp açık, uyandi")
	_check((k["silah"] as Sprite2D).modulate == Color(1, 1, 1, 1), "uyanıştan sonra silah tam renk")
	_check(k.has("etiket"), "YENİ etiketi ve kıvılcım var")
	_oyuncu_onune("yatagan")
	kg._satir = int(k["i"]) / KupGaleri.SUTUN
	await _sure(1.2)
	_check(not Kupler.yeni_mi("yatagan") and not k.has("etiket"), "kartı görüldü: YENİ söndü")
	await _yurt()
	_check(_kup("yatagan")["durum"] == "acik" and not _kg()._uyanacak.has(_kup("yatagan")), "sonraki yurt: uyanış yinelenmez")


# ------------------------------------------------------------------ başlangıç silahı seçimi
func _gez_sec(id: String) -> String:
	var kg := _kg()
	main._on_npc("kupler")
	_check(main.hud.mode == "kupler" and kg.gez and get_tree().paused, "W: gezme kipi açıldı (oyun durdu)")
	kg.secili = int(_kup(id)["i"])
	var r: String = kg.sec_secili()
	kg.gez_kapat()
	main._start_play()
	await _frames(2)
	return r


func _secim() -> void:
	await _yurt()
	var kg := _kg()
	# imleç hareketi
	main._on_npc("kupler")
	kg.secili = 0
	kg.gez_tasi(-1, 0)
	_check(kg.secili == KupGaleri.SUTUN - 1, "imleç solda sarar")
	kg.gez_tasi(0, 1)
	_check(kg.secili == 2 * KupGaleri.SUTUN - 1, "imleç bir raf aşağı")
	kg.gez_kapat()
	main._start_play()
	var r := await _gez_sec("kargi")
	_check(r == "secildi" and String(Game.run["slots"]["melee"].get("id", "")) == "kargi", "kargı seçildi: yurttaki koşunun yakın yuvası hemen kargı")
	_check(Kupler.secili("melee") == "kargi" and String(Game.meta["kup"]["secim"].get("melee", "")) == "kargi", "seçim kayıtta")
	Game.new_run()
	_check(String(Game.run["slots"]["melee"].get("id", "")) == "kargi", "sonraki koşu kargıyla başlar")
	_check(String(Game.run["slots"]["second"].get("id", "")) == "turk_yayi", "ikincil yuva değişmedi (Türk yayı)")
	await _yurt()
	r = await _gez_sec("coban_sapani")
	_check(r == "secildi" and Kupler.yuva("coban_sapani") == "second" and String(Game.run["slots"]["second"].get("id", "")) == "coban_sapani", "çoban sapanı ikincil yuvaya")
	Game.new_run()
	_check(String(Game.run["slots"]["melee"].get("id", "")) == "kargi" and String(Game.run["slots"]["second"].get("id", "")) == "coban_sapani", "sonraki koşu: kargı + sapan")
	await _yurt()
	r = await _gez_sec("erlik_tirpani")
	_check(r == "" and Kupler.secili("melee") == "kargi", "kilitli küp seçilemez")
	r = await _gez_sec("kargi")
	_check(r == "kaldirildi" and Kupler.secili("melee") == "" and String(Game.run["slots"]["melee"].get("id", "")) == "alp_kilici", "aynı küp yeniden: varsayılana döner (Alp Kılıcı)")
	Game.new_run()
	_check(String(Game.run["slots"]["melee"].get("id", "")) == "alp_kilici", "sonraki koşu varsayılan kılıçla")
	# test kipi: seçim yok sayılır
	Kupler.sec("kargi")
	Kupler.devre_disi = true
	Game.new_run()
	_check(String(Game.run["slots"]["melee"].get("id", "")) == "alp_kilici", "test kipinde (devre_disi) seçim uygulanmaz")
	Kupler.devre_disi = false
	Game.new_run()
	_check(String(Game.run["slots"]["melee"].get("id", "")) == "kargi", "seçim yeniden etkin")
	# Demirci Dostu (Umay): seçilen silah da bir kademe üstün döner
	var um: Dictionary = Game.meta.get("umay", {}).duplicate()
	Game.meta["umay"] = {"silah": 1}
	Game.new_run()
	var m: Dictionary = Game.run["slots"]["melee"]
	_check(String(m.get("id", "")) == "kargi" and String(m.get("material", "")) == "tunc", "Demirci Dostu: seçilen silah tunç döner")
	Game.meta["umay"] = um


# ------------------------------------------------------------------ Rastgele küp ve eşikler
func _rastgele_esik() -> void:
	_kayit(["kargi", "yatagan", "gurz"], [], [], {})
	Game.meta["umay"] = {}
	await _yurt()
	_check(Kupler.acilan() == 8 and Kupler.durum(Kupler.RASTGELE) == "kilitli", "8 küpte Rastgele kilitli")
	var r := await _gez_sec(Kupler.RASTGELE)
	_check(r == "", "kilitli Rastgele seçilemez")
	Kupler.kesfet("teber")
	Kupler.kesfet("ikiz_bicak")
	_check(Kupler.acilan() == 10 and Kupler.durum(Kupler.RASTGELE) == "acik" and Kupler.yeni_mi(Kupler.RASTGELE), "10 küp: Rastgele açıldı (yeni)")
	await _yurt()
	_check(_kg()._uyanacak.size() >= 1, "Rastgele küp uyanmayı bekliyor")
	r = await _gez_sec(Kupler.RASTGELE)
	_check(r == "secildi" and Kupler.secili("melee") == Kupler.RASTGELE, "Rastgele seçildi")
	var gor := {}
	var nadir_ok := true
	for i in 12:
		Game.new_run()
		var m: Dictionary = Game.run["slots"]["melee"]
		gor[String(m.get("id", ""))] = true
		if int(m.get("rarity", 0)) < 1 or Kupler.durum(String(m.get("id", ""))) != "acik" or Kupler.yuva(String(m.get("id", ""))) != "melee":
			nadir_ok = false
	_check(nadir_ok, "Rastgele: hep açık bir yakın dövüş silahı, nadirlik >= 1")
	_check(gor.size() >= 2, "Rastgele: farklı silahlar çıkar (%s)" % str(gor.keys()))
	# eşikler: 20 küpte +25 altın, 30'da +%5 can
	Game.new_run()
	var g0 := int(Game.run["gold"])
	var hp0 := float(Game.run["max_hp"])
	var ek := 0
	for id in Kupler.liste():
		if Kupler.acilan() >= 30:
			break
		if id != Kupler.RASTGELE and Kupler.durum(id) != "acik" and Game.is_unlocked(id):
			Kupler.kesfet(id)
			ek += 1
	_check(Kupler.acilan() >= 30, "30 küp açıldı (%d)" % Kupler.acilan())
	Game.new_run()
	_check(int(Game.run["gold"]) == g0 + 25, "20 küp eşiği: +25 altın (%d → %d)" % [g0, int(Game.run["gold"])])
	_check(absf(float(Game.run["max_hp"]) - hp0 * 1.05) < 0.01 and float(Game.run["hp"]) == float(Game.run["max_hp"]), "30 küp eşiği: en yüksek can +%%5 (%.1f → %.1f)" % [hp0, float(Game.run["max_hp"])])


# ------------------------------------------------------------------ Demirci ve koşuda kuşanma
func _demirci_ve_kusanma() -> void:
	_kayit([], ["civili_topuz"], [], {})
	Game.meta["kut_bank"] = 999
	await _yurt()
	_check(Kupler.durum("civili_topuz") == "parsomen", "çivili topuz: parşömen")
	_check(main._demirci_ac("civili_topuz"), "Demirci parşömeni açtı")
	main._start_play()
	_check(Kupler.durum("civili_topuz") == "acik" and Kupler.yeni_mi("civili_topuz") and _kg()._uyanacak.has(_kup("civili_topuz")), "Demirci: küp açık, YENİ, uyanacak")
	# koşuda ilk kuşanma (Level.equip): küp açılır
	main.level.drop_item(ItemGen.roll("ay_palasi", 0), main.level.player.global_position + Vector2(0, -10))
	var p: Pickup = main.level.pickups[main.level.pickups.size() - 1]
	main.level.equip(p, "melee")
	_check(Kupler.durum("ay_palasi") == "acik" and Kupler.yeni_mi("ay_palasi"), "koşuda ilk kuşanma: ay palası küpü açıldı")


# ------------------------------------------------------------------ kapı: seçilen silahla 1. derinlik
func _kapi() -> void:
	_kayit(["kargi"], [], [], {})
	await _yurt()
	await _gez_sec("kargi")
	var lv: Node = main.level
	lv.player.global_position = lv.exit_pos + Vector2(0, -2)
	lv.player.velocity = Vector2.ZERO
	await _frames(6)
	_check(main.level != lv and not main.level.hub and int(Game.run.get("depth", 0)) == 1, "Kut Kapısı → 1. derinlik")
	_check(String(Game.run["slots"]["melee"].get("id", "")) == "kargi", "1. derinlik seçilen kargıyla")


# ------------------------------------------------------------------ çekim
func _ekran_kur() -> void:
	# karışık durumlar: temel + birkaç keşif, parşömenler, birkaç yeni (uyanmış), kargı seçili
	var kesif := ["kargi", "yatagan", "gurz", "teber", "ikiz_bicak", "kement", "akinci_yayi", "kam_kopuzu", "cirit", "ruh_kilici", "ulu_kilic", "dag_cekici", "ayna_kalkan", "kartal_kalkani", "yel_borusu", "ay_palasi", "tas_kalkan", "dikenli_kalkan", "savas_baltasi"]
	_kayit(kesif, ["civili_topuz", "saganak_yayi", "kurt_pencesi"], ["ayaz_kilici", "od_oklari"], {"melee": "kargi", "second": "akinci_yayi"})
	Game.meta["kup"]["yeni"] = ["ulu_kilic", "akinci_yayi"]
	Game.meta["kup"]["uyandi"] = ["ulu_kilic", "akinci_yayi"]

	Game.new_run()
	await _yurt()
	main.hud._card_t = 99.0
	var kg := _kg()
	var pl: Node2D = main.level.player
	match _ekran:
		"duvar":
			kg.kart_kapali = true
			_oyuncu_onune("ruzgar_kilici")
			pl.global_position.x = kg.global_position.x + KupGaleri.GEN * 0.5 + 30.0
		"yakin":
			_oyuncu_onune("tulpar_mizragi")
			Game.meta["kup"]["yeni"].erase("akinci_yayi")
			kg._satir = int(_kup("tulpar_mizragi")["i"]) / KupGaleri.SUTUN
			Game.base_zoom = 2.25
		"gez":
			_oyuncu_onune("ruh_kilici")
			await _frames(3)
			main._on_npc("kupler")
			kg.secili = int(_kup("ulu_kilic")["i"])
		"uyanis":
			_oyuncu_onune("kut_kalkani")
			pl.global_position.x += 56.0
			kg._satir = 3
			Game.base_zoom = 2.0
			await _sure(12.0)
			Kupler.kesfet("kut_kalkani")
			kg.acildi("kut_kalkani")
			print("[kavanoz] uyanis_konum t=%d %s" % [Time.get_ticks_msec(), str(main.get_viewport().get_canvas_transform() * (_kup("kut_kalkani")["kok"] as Node2D).global_position)])
		"kosu":
			kg.secili = int(_kup("kargi")["i"])
			await _sure(1.0)
			pl.global_position = main.level.exit_pos + Vector2(0, -2)
	# kayıt hemen geri yazılır (görüntü kayıtlı duruma bağlı değil: küpler kuruldu); çıkışta yeniden
