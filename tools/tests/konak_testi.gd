extends Node
## v32 konak ve Bengisu Usta testi: godot --headless --path . --quit-after 99999 -- --konak --muhur=0
##   AKIS:  1. derinlik kurulur, oyuncu Kut Kapısı'na konur → Level.finished → Main._on_finished → KONAK (yurt değil):
##          level.konak, derinlik 2, can +%15 (Zorluk.derinlik_sifa), şişeler dolu, lütuflar söndü, Bengisu Usta ve ocak var,
##          Bezirgân kuralı (önceki bölümde pazar yoksa gelir).
##   OCAK:  oyuncu ateşin yanına konur → taşınan Kut Umay'ın bankasına geçer.
##   USTA:  Main._on_npc("usta") → hud.mode "usta"; hizmetler oyunun yolundan (Main._usta_sec / _usta_uygula → Usta.uygula):
##          nakış adayları (3; fiyat nadirlikle), nakış yuva sınırına dek işlenir sonra reddedilir, dövme değerleri değiştirir ve
##          pahalanır, unsur (rastgele / seçilen) aşılanır, kalite şansla +5..15 ya da değişmez (altın gider), Kut Mührü,
##          altın tam düşer, yetmeyen altın reddedilir, kartın SnH farkı = ItemGen.dps_oyuncu farkı, aynı tohum aynı adaylar.
##   KAPI:  konak kapısı → 2. derinlik bölümü (konak / yurt değil, derinlik aynı kalır).
##   BOSS:  2. derinlik sonu → boss arenası (derinlik 2) → boss ölünce kapı → konak (derinlik 3) → bölüm (derinlik 3).
##   YURT:  Main._build_hub → kapı → 1. derinlik bölümü (derinlik 1 kalır).
## Çekim kipleri (--goruntu ile, headless değil): --konak_ekran=dunya | usta | sonuc [--konak_derinlik=N] (kurar ve bekler).
## Çıktı "[konak] ..." satırları, sonda "[konak] SONUC GECTI|KALDI". Kalıcı kayıt test sonunda geri yüklenir.

var main: Node
var _fail: Array = []
var _meta0: Dictionary = {}
var _ekran := ""


func _ready() -> void:
	process_mode = Node.PROCESS_MODE_ALWAYS
	for a in OS.get_cmdline_user_args():
		if String(a).begins_with("--konak_ekran="):
			_ekran = String(a).trim_prefix("--konak_ekran=")
	_meta0 = Game.meta.duplicate(true)
	_run.call_deferred()


func _p(s: String) -> void:
	print("[konak] ", s)


func _check(ok: bool, what: String) -> void:
	_p(("TAMAM " if ok else "HATA ") + what)
	if not ok:
		_fail.append(what)


func _frames(n: int) -> void:
	for i in n:
		await get_tree().process_frame


func _build(d: int) -> void:
	Game.run["depth"] = d
	Game.run["tier"] = Zorluk.kademe(d)
	main._build_level()
	main._start_play()
	await _frames(3)


func _gecir() -> void:
	## Oyuncuyu bu bölümün Kut Kapısı'na koy; Level.finished → Main._on_finished (yeni bölüm / konak kurulur)
	var lv: Node = main.level
	lv.player.global_position = lv.exit_pos + Vector2(0, -2)
	lv.player.velocity = Vector2.ZERO
	await _frames(4)


func _run() -> void:
	await _frames(5)
	if _ekran != "":
		await _ekran_kur()
		return
	await _akis()
	await _ocak()
	await _yoldaslar()
	await _usta()
	await _kapi()
	await _boss()
	await _yurt()
	Game.meta = _meta0
	Game.save_meta()
	_p("kalıcı kayıt geri yüklendi")
	_p("SONUC %s%s" % ["GECTI" if _fail.is_empty() else "KALDI", "" if _fail.is_empty() else " (" + ", ".join(_fail) + ")"])
	get_tree().quit()


# ------------------------------------------------------------------ akış: kapı → konak
func _akis() -> void:
	await _build(1)
	var lv: Node = main.level
	Game.run["hp"] = 40.0
	Game.run["max_hp"] = 100.0
	Game.run["flasks"] = 0
	Game.run["lutuf"] = ["tengri"]
	Game.run["kut"] = 25
	var had_bz: bool = lv.bezirgan != null
	_p("1. derinlik kuruldu; bezirgan=%s can=40 şişe=0 lütuf=1 kut=25" % str(had_bz))
	# v32 entegrasyon: dallı (256 x 90) bölümün Kut Kapısı katı zeminde; oyuncu kapıya YÜRÜYEREK girer (ışınlanmaz)
	var ec := Vector2i(int(floor(lv.exit_pos.x / Level.TS)), int(floor(lv.exit_pos.y / Level.TS)))
	_check(lv.cell(ec.x, ec.y) != 0 and lv.cell(ec.x, ec.y - 1) == 0 and lv.cell(ec.x, ec.y - 3) == 0, "Kut Kapısı katı zeminde, üstü açık (karo %s)" % str(ec))
	var yon := 1
	if lv.cell(ec.x - 3, ec.y - 1) != 0 or lv.cell(ec.x - 3, ec.y) == 0:
		yon = -1   # kapının solu duvar / boşluksa sağından yürü
	lv.player.global_position = lv.exit_pos + Vector2(-72.0 * yon, -2.0)
	lv.player.velocity = Vector2.ZERO
	await _frames(2)
	var yuruyen := false
	for i in 120:
		Input.action_press("sag" if yon == 1 else "sol")
		await get_tree().physics_frame
		if main.level != lv:
			yuruyen = true
			break
	Input.action_release("sag")
	Input.action_release("sol")
	_check(yuruyen, "oyuncu Kut Kapısı'na yürüyerek girdi (bölüm bitti)")
	if not yuruyen:
		await _gecir()
	await _frames(3)
	lv = main.level
	_check(lv.konak and not lv.hub, "kapıdan sonra KONAK kuruldu (yurt değil; konak=%s hub=%s)" % [str(lv.konak), str(lv.hub)])
	_check(int(Game.run["depth"]) == 2, "derinlik 2 (%d)" % int(Game.run["depth"]))
	var beklenen := minf(100.0, 40.0 + 100.0 * Zorluk.derinlik_sifa())
	_check(is_equal_approx(float(Game.run["hp"]), beklenen), "can %%%d iyileşti: 40 → %d (beklenen %d)" % [int(round(Zorluk.derinlik_sifa() * 100.0)), int(Game.run["hp"]), int(beklenen)])
	_check(int(Game.run["flasks"]) == int(Game.run["max_flasks"]), "şişeler doldu (%d / %d)" % [int(Game.run["flasks"]), int(Game.run["max_flasks"])])
	_check((Game.run.get("lutuf", []) as Array).is_empty(), "lütuflar konakta söndü")
	_check(String(lv.biome.get("id", "")) == String(Game.biome_for_depth(2).get("id", "")), "konak 2. derinliğin biyomunda (%s)" % String(lv.biome.get("id", "")))
	var usta: Node = null
	for n in lv.npcs:
		if n.id == "usta":
			usta = n
	_check(usta != null, "Bengisu Usta konakta")
	_check(lv.konak_ates != Vector2.ZERO, "Umay Ocağı var (x=%.0f)" % lv.konak_ates.x)
	_check((lv.bezirgan != null) == (not had_bz), "Bezirgân kuralı: önceki bölümde pazar %s → konakta %s" % ["vardı" if had_bz else "yoktu", "yok" if lv.bezirgan == null else "var"])
	_check(get_tree().get_nodes_in_group("dusman").is_empty(), "konakta düşman yok")
	_check(main.hud.mode == "play" and not get_tree().paused, "oyun konakta sürüyor")
	# v32 entegrasyon: konakta harita / Kut Taşı yok (küçük harita çizilmez, M haritayı açmaz, ışınlanma reddedilir)
	_check(lv.harita == null and lv.rooms.is_empty(), "konakta harita sisi ve oda çizgesi yok (küçük harita gizli)")
	main._harita_ac()
	_check(main.hud.mode == "play" and not get_tree().paused, "konakta M haritayı açmaz")
	_check(not lv.isinlan(0), "konakta ışınlanma reddedilir")


# ------------------------------------------------------------------ ocak: Kut bankaya
func _ocak() -> void:
	var lv: Node = main.level
	var bank0 := int(Game.meta.get("kut_bank", 0))
	Game.run["kut"] = 25
	lv.player.global_position = lv.konak_ates + Vector2(-20, -2)
	lv.player.velocity = Vector2.ZERO
	await _frames(4)
	_check(int(Game.run["kut"]) == 0 and int(Game.meta.get("kut_bank", 0)) == bank0 + 25, "ocak Kut'u Umay'a ulaştırdı (banka %d → %d)" % [bank0, int(Game.meta.get("kut_bank", 0))])


# ------------------------------------------------------------------ v42 yoldaşlar
func _yoldaslar() -> void:
	## Konakta yurdun dört sakini de var; hizmet ekranları açılır (Umay / Ozan / Demirci / Alp Ata); sözleri hikâyeden
	var lv: Node = main.level
	var bek := {"umay": "umay", "ozan": "ozan", "demirci": "demirci", "alp_ata": "sanat"}
	for id in bek:
		var npc: Node = null
		for n in lv.npcs:
			if n.id == id:
				npc = n
		_check(npc != null, "konakta %s var" % id)
		if npc == null:
			continue
		_check(String(npc.soz) != "", "%s sözü: «%s»" % [id, String(npc.soz)])
		lv.player.global_position = npc.global_position + Vector2(-20, -2)
		lv.player.velocity = Vector2.ZERO
		await _frames(3)
		_check(npc.near, "oyuncu %s yanında (W balonu)" % id)
		lv.npc_requested.emit(id)
		await _frames(2)
		var ok: bool = main.hud.mode == bek[id] or (id == "ozan" and main.hud.mode == "ad")
		_check(ok and get_tree().paused, "%s ekranı konakta açıldı (%s)" % [id, main.hud.mode])
		main._start_play()
		await _frames(2)
	_check(main.hud.mode == "play" and not get_tree().paused, "yoldaşlardan sonra oyun sürüyor")


# ------------------------------------------------------------------ Bengisu Usta
func _usta() -> void:
	var lv: Node = main.level
	var usta: Node = null
	for n in lv.npcs:
		if n.id == "usta":
			usta = n
	if usta == null:
		return
	lv.player.global_position = usta.global_position + Vector2(-24, -2)
	lv.player.velocity = Vector2.ZERO
	await _frames(3)
	_check(usta.near, "oyuncu Usta'nın yanında (W balonu)")
	# belirli bir silah: Nadir Demir Alp Kılıcı (1 nakış yuvası + 1 ek = 2), unsursuz
	var it := ItemGen.roll("alp_kilici", 1, "demir", 1, "")
	Unsur.apply(it, "", -1.0)
	Game.run["slots"]["melee"] = it
	Game.run["slots"]["second"] = ItemGen.roll("turk_yayi", 1, "demir", 0, "")
	lv.player.on_equip()
	Game.run["gold"] = 5000
	lv.npc_requested.emit("usta")
	await _frames(3)
	_check(main.hud.mode == "usta" and get_tree().paused, "Usta ekranı açıldı (oyun duraklı)")
	_check(Usta.silahlar() == ["melee", "second"], "iki silah listelendi %s" % str(Usta.silahlar()))
	# belirlenimci adaylar: aynı tohum aynı adaylar
	var t0 := Usta.tohum
	Usta.yeni_konak(t0)
	var a1 := Usta.nakis_adaylari("melee", it).duplicate(true)
	Usta.yeni_konak(t0)
	var a2 := Usta.nakis_adaylari("melee", it).duplicate(true)
	_check(a1 == a2 and a1.size() == 3, "aynı tohumda aynı 3 nakış adayı")
	for c in a1:
		_p("aday: %s v=%s nadir=%s fiyat=%d" % [String(c["id"]), ItemGen.fmt(float(c["v"])), str(c["nadir"]), int(c["fiyat"])])
		_check(int(c["fiyat"]) == Usta.nakis_fiyat(it, String(c["id"])), "aday fiyatı nadirlikle (%s)" % String(c["id"]))
	var hs := Usta.hizmetler(it)
	for h in hs:
		_p("hizmet %s: %d altın uygun=%s şans=%s" % [String(h["id"]), int(h["fiyat"]), str(h["uygun"]), ("%d" % int(round(float(h["sans"]) * 100.0))) if float(h["sans"]) >= 0.0 else "-"])
	# 1) nakış: oyunun yolundan (silah seç → hizmet → aday → onay → işle)
	main.hud.sel = 0
	main._usta_sec(0)
	_check(main.hud.usta_adim == 1 and main.hud.usta_slot == "melee", "silah seçildi (adım 1)")
	main.hud.sel = 0
	main._usta_sec(0)
	_check(main.hud.usta_adim == 2 and main.hud.usta_hid == "nakis" and main.hud.usta_secs.size() == 3, "nakış adayları açıldı (adım 2, %d aday)" % main.hud.usta_secs.size())
	var g0 := int(Game.run["gold"])
	var n0 := Usta.nakis_sayi(it)
	var dps0 := ItemGen.dps_oyuncu(it)
	var aday: Dictionary = main.hud.usta_secs[0]
	main.hud.sel = 0
	main._usta_sec(0)
	_check(main.hud.usta_onay and int(Game.run["gold"]) == g0, "ilk basış onay soruyor, altın düşmedi")
	main._usta_sec(0)
	_check(main.hud.usta_adim == 3 and not main.hud.usta_sonuc.is_empty(), "sonuç kartı açıldı")
	_check(Usta.nakis_sayi(it) == n0 + 1 and String(it["affixes"][-1]["id"]) == String(aday["veri"]["id"]), "nakış işlendi: %s" % String(aday["ad"]))
	_check(int(Game.run["gold"]) == g0 - int(aday["fiyat"]), "altın düştü %d → %d (fiyat %d)" % [g0, int(Game.run["gold"]), int(aday["fiyat"])])
	var s: Dictionary = main.hud.usta_sonuc
	var d_once: float = main.hud._eff_dps(s["once"])
	var d_sonra: float = main.hud._eff_dps(s["sonra"])
	_check(is_equal_approx(d_once, dps0) and is_equal_approx(d_sonra, ItemGen.dps_oyuncu(it)), "kartın SnH farkı ItemGen.dps_oyuncu ile aynı (%s → %s)" % [ItemGen.fmt(d_once), ItemGen.fmt(d_sonra)])
	_check(String(it["name"]) != String(s["once"]["name"]) or n0 > 0, "ad yenilendi: %s" % String(it["name"]))
	await _frames(3)   # HUD sonuç kartını ve damgayı çizsin
	# yuva sınırına dek nakış, sonra ret
	var mx := Usta.max_nakis(it)
	_check(mx == ItemGen.max_affix(it) + 1, "nakış sınırı = nadirlik yuvası + 1 (%d)" % mx)
	var guard := 0
	while Usta.nakis_sayi(it) < mx and guard < 6:
		guard += 1
		var secs := Usta.secenekler("nakis", "melee", it)
		var r := Usta.uygula("nakis", "melee", secs[0])
		_check(bool(r["ok"]), "nakış %d / %d" % [Usta.nakis_sayi(it), mx])
	var secs2 := Usta.secenekler("nakis", "melee", it)
	var r_dolu := Usta.uygula("nakis", "melee", secs2[0] if not secs2.is_empty() else {})
	_check(not bool(r_dolu["ok"]) and Usta.nakis_sayi(it) == mx, "yuva dolunca nakış reddedildi (%s)" % String(r_dolu["msg"]))
	_check(not bool(Usta.hizmetler(it)[0]["uygun"]), "hizmet listesinde nakış uygun değil")
	# 2) yeniden dövme: değerler değişir, ikinci dövme pahalı
	var vals0: Array = []
	for a in it["affixes"]:
		vals0.append(float(a["v"]))
	var f_d0 := Usta.dovme_fiyat(it)
	var g1 := int(Game.run["gold"])
	var rd := Usta.uygula("dovme", "melee", {})
	var vals1: Array = []
	for a in it["affixes"]:
		vals1.append(float(a["v"]))
	_check(bool(rd["ok"]) and int(Game.run["gold"]) == g1 - f_d0, "dövme %d altın aldı" % f_d0)
	_check(vals0 != vals1 and vals0.size() == vals1.size(), "dövme değerleri değiştirdi %s → %s" % [str(vals0), str(vals1)])
	_check(Usta.dovme_fiyat(it) > f_d0, "ikinci dövme daha pahalı (%d > %d)" % [Usta.dovme_fiyat(it), f_d0])
	var ids0: Array = []
	for a in it["affixes"]:
		ids0.append(String(a["id"]))
	_check(ids0.size() == mx, "dövme nakış kimliklerini korudu %s" % str(ids0))
	# 3) unsur: rastgele sonra seçilen
	var u_secs := Usta.secenekler("unsur", "melee", it)
	_check(u_secs.size() == 6 and int(u_secs[1]["fiyat"]) > int(u_secs[0]["fiyat"]), "unsur seçenekleri: rastgele %d, seçerek %d" % [int(u_secs[0]["fiyat"]), int(u_secs[1]["fiyat"])])
	var ru := Usta.uygula("unsur", "melee", u_secs[0])
	_check(bool(ru["ok"]) and Unsur.of(it) != "", "rastgele unsur aşılandı: %s" % Unsur.of(it))
	var ru2 := Usta.uygula("unsur", "melee", u_secs[2])   # ayaz
	_check(bool(ru2["ok"]) and Unsur.of(it) == "ayaz" and String(it["name"]).contains("Ayazlı"), "seçilen unsur aşılandı: %s (%s)" % [Unsur.of(it), String(it["name"])])
	# 4) kalite: şans; başarıda +5..15, değilse değişmez; altın hep düşer
	var k_ok := 0
	var k_fail := 0
	for i in 8:
		var q0 := int(it["quality"])
		if q0 >= 100:
			break
		var dmg0 := float(it["dmg"])
		var gk := int(Game.run["gold"])
		var fk := Usta.kalite_fiyat(it)
		var rk := Usta.uygula("kalite", "melee", {})
		_check(bool(rk["ok"]) and int(Game.run["gold"]) == gk - fk, "kalite denemesi %d altın aldı" % fk)
		var dq := int(it["quality"]) - q0
		if bool(rk["iyi"]):
			k_ok += 1
			# v34 birleştirme: kalite %100'de kenetlenir (Usta._kalite_ekle): %96'dan +4 doğru sonuç (test eskiden KALDI diyordu)
			var lo := mini(5, 100 - q0)
			_check(dq >= lo and dq <= 15 and int(it["quality"]) <= 100 and float(it["dmg"]) > dmg0, "kalite +%d (%d..15, %%100 sınırı), hasar %s → %s" % [dq, lo, ItemGen.fmt(dmg0), ItemGen.fmt(float(it["dmg"]))])
		else:
			k_fail += 1
			_check(dq == 0 and is_equal_approx(float(it["dmg"]), dmg0), "kalite tutmadı: değişmedi")
	_p("kalite: %d tuttu, %d tutmadı, son kalite %%%d (şans %%%d)" % [k_ok, k_fail, int(it["quality"]), int(round(Usta.kalite_sansi(it) * 100.0))])
	_check(Usta.kalite_sansi(it) <= 0.9 and Usta.kalite_sansi(it) >= 0.2, "kalite şansı sınırlar içinde")
	# 5) Kut Mührü: birkaç kez; her sonuç bilinen bir damga
	var damgalar: Dictionary = {}
	for i in 6:
		var rm := Usta.uygula("muhur", "melee", {})
		_check(bool(rm["ok"]), "mühür %d: %s" % [i + 1, String(rm["msg"])])
		damgalar[String(rm.get("damga", ""))] = true
	_p("mühür damgaları: %s" % str(damgalar.keys()))
	# 6) yetmeyen altın
	Game.run["gold"] = Usta.muhur_fiyat(it) - 1
	var rr := Usta.uygula("muhur", "melee", {})
	_check(not bool(rr["ok"]) and int(Game.run["gold"]) == Usta.muhur_fiyat(it) - 1, "altın yetmeyince reddedildi (%s)" % String(rr["msg"]))
	main.hud.usta_adim = 1
	main.hud.sel = 4
	main._usta_sec(4)
	_check(not main.hud.usta_onay, "ekran da yetmeyen altını reddetti (%s)" % main.hud.flash_msg)
	# 7) ekrandan çık
	main._start_play()
	await _frames(2)
	_check(main.hud.mode == "play" and not get_tree().paused, "Usta'dan ayrıldı")
	_p("son silah: %s | nakış %s | unsur %s | kalite %%%d | SnH %s" % [String(it["name"]), str((it["affixes"] as Array).map(func(a): return "%s %s" % [a["id"], ItemGen.fmt(float(a["v"]))])), Unsur.of(it), int(it["quality"]), ItemGen.fmt(ItemGen.dps_oyuncu(it))])


# ------------------------------------------------------------------ konak kapısı → sıradaki derinlik
func _kapi() -> void:
	var lv: Node = main.level
	Game.run["gold"] = 300
	await _gecir()
	lv = main.level
	_check(not lv.konak and not lv.hub and lv.boss_id == "", "konak kapısından 2. derinlik bölümüne inildi")
	_check(int(Game.run["depth"]) == 2, "derinlik 2 kaldı (%d)" % int(Game.run["depth"]))


# ------------------------------------------------------------------ boss akışı: bölüm → boss → konak
func _boss() -> void:
	var lv: Node = main.level
	Game.run["boss_done"] = []
	await _gecir()
	lv = main.level
	_check(lv.boss_id == "kara_boru_han" and int(Game.run["depth"]) == 2, "2. derinlik sonunda boss arenası (%s)" % lv.boss_id)
	if lv.boss_id == "":
		return
	await _frames(2)
	lv._on_boss_died(lv.boss)
	lv.open_boss_gate()
	await _frames(2)
	await _gecir()
	lv = main.level
	_check(lv.konak and int(Game.run["depth"]) == 3, "bosstan sonra konak, derinlik 3 (konak=%s d=%d)" % [str(lv.konak), int(Game.run["depth"])])
	_check("kara_boru_han" in Game.run.get("boss_done", []), "boss geçildi olarak kaydedildi")
	_check(lv.bezirgan == null, "boss öncesi pazar vardı: bosstan sonraki konakta Bezirgân yok")
	await _gecir()
	lv = main.level
	_check(not lv.konak and lv.boss_id == "" and int(Game.run["depth"]) == 3, "konaktan 3. derinliğe inildi")


# ------------------------------------------------------------------ yurt: koşu başı
func _yurt() -> void:
	main._build_hub()
	main._start_play()
	await _frames(3)
	Game.run["depth"] = 1
	Game.run["tier"] = 0
	await _gecir()
	var lv: Node = main.level
	_check(not lv.hub and not lv.konak and int(Game.run["depth"]) == 1, "yurt kapısı 1. derinliğe indirdi (derinlik artmadı)")


# ------------------------------------------------------------------ çekim kipleri
func _ekran_kur() -> void:
	var d := int(_arg_or("--konak_derinlik", "2"))
	Game.run["depth"] = d - 1
	Game.run["tier"] = Zorluk.kademe(d - 1)
	Game.run["gold"] = 186
	Game.run["kut"] = 14
	main._to_konak()
	await _frames(4)
	var lv: Node = main.level
	var usta: Node = null
	for n in lv.npcs:
		if n.id == "usta":
			usta = n
	match _ekran:
		"dunya":
			lv.player.global_position = lv.konak_ates + Vector2(-60, -2)
			lv.player.facing = 1
			Game.camera.reset_smoothing()
		"usta", "sonuc":
			lv.player.global_position = usta.global_position + Vector2(-24, -2)
			lv.player.facing = 1
			Game.camera.reset_smoothing()
			var it := ItemGen.roll("ay_palasi", Zorluk.kademe(d), "gumus", 1, "")
			Game.run["slots"]["melee"] = it
			lv.player.on_equip()
			await _frames(20)
			lv.npc_requested.emit("usta")
			await _frames(2)
			main.hud.sel = 0
			if _ekran == "sonuc":
				main._usta_sec(0)
				main.hud.sel = 0
				main._usta_sec(0)
				main.hud.sel = 1
				main._usta_sec(1)
				main._usta_sec(1)
			else:
				main._usta_sec(0)
				main.hud.sel = 0
	# kalıcı kayıt: bu kipte test kendisi çıkmaz (Ayarlar --goruntu çıkar); kaydı hemen geri yaz
	Game.meta = _meta0.duplicate(true)
	Game.save_meta()


func _arg_or(name: String, def: String) -> String:
	for a in OS.get_cmdline_user_args():
		if String(a).begins_with(name + "="):
			return String(a).trim_prefix(name + "=")
	return def
