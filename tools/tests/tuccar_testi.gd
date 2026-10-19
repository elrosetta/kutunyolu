extends Node
## v24 tüccar ve silah parşömeni testi: godot --headless --path . --quit-after 99999 -- --tuccar
##   EKONOMI: her derinlik (1-9) için birkaç bölüm kurulur; yaratık / seçkin / hazine sayısından "hepsi öldürülürse"
##            beklenen altın (Pazar.altin_k ile), Bezirgân'ın çıkma sıklığı ve duvar denetimi (Level.bezirgan_ok),
##            o derinliğin ortalama fiyatları (Sıradan / Nadir / Destansı silah, Umay Sütü, Kut Tomarı, yenileme).
##   PAZAR:   3. derinlikte Bezirgân zorla yerleştirilir, oyuncu yanına konur, pazar oyunun yolundan açılır
##            (Main._on_tuccar), mallar Main._tuccar_sec ile (onay + alış) alınır: altın düşüşü, SATILDI, kilime düşen
##            eşya ve kuşanma (Level.try_equip), SnH farkı (HUD'un çizdiği sayı), şifa, yetmeyen altın, yenileme.
##   PARSOMEN: yurtta Demirci'de aynı parşömen iki kez açılır (Main._demirci_ac): her seferinde önüne rastgele
##            yuvarlanmış bir eşya düşer (kademe 0), eşya düşme havuzuna girer. Kalıcı kayıt test sonunda geri yüklenir.
## Çekim kipleri (--goruntu ile): --tuccar_ekran=dunya | pazar | demirci | yurt (kurar ve bekler, çıkmaz).
## Çıktı "[tuccar] ..." satırları, sonda "[tuccar] SONUC GECTI|KALDI".

var main: Node
var _fail: Array = []
var _meta0: Dictionary = {}
var _ekran := ""


func _ready() -> void:
	process_mode = Node.PROCESS_MODE_ALWAYS
	for a in OS.get_cmdline_user_args():
		if String(a).begins_with("--tuccar_ekran="):
			_ekran = String(a).trim_prefix("--tuccar_ekran=")
	_meta0 = Game.meta.duplicate(true)
	_run.call_deferred()


func _p(s: String) -> void:
	print("[tuccar] ", s)


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


func _run() -> void:
	await _frames(5)
	if _ekran != "":
		await _ekran_kur()
		return
	await _ekonomi()
	await _pazar()
	await _parsomen()
	Game.meta = _meta0
	Game.save_meta()
	_p("kalıcı kayıt geri yüklendi")
	_p("SONUC %s%s" % ["GECTI" if _fail.is_empty() else "KALDI", "" if _fail.is_empty() else " (" + ", ".join(_fail) + ")"])
	get_tree().quit()


# ------------------------------------------------------------------ ekonomi
func _ekonomi() -> void:
	var n_seed := 3
	for arg in OS.get_cmdline_user_args():
		if String(arg).begins_with("--tuccar_tohum="):
			n_seed = int(String(arg).trim_prefix("--tuccar_tohum="))
	_p("EKONOMI d | yaratık seçkin hazine | beklenen altın (hepsi) | bezirgân çıktı / bölüm, duvar | fiyat Sıradan Nadir Destansı (silah) | Umay Sütü | Tomar | yenile")
	var tot_bz := 0
	var tot_lv := 0
	for d in range(1, 10):
		var en := 0.0
		var el := 0.0
		var tr := 0.0
		var bz := 0
		var wall_ok := true
		for k in n_seed:
			await _build(d)
			var lv: Node = main.level
			for e in get_tree().get_nodes_in_group("dusman"):
				if is_instance_valid(e) and not e.is_queued_for_deletion():
					if e.elite:
						el += 1.0
					else:
						en += 1.0
			for ch in lv.chunks:
				for line in LevelGen.CHUNKS.get(String(ch["name"]), []):
					tr += float(String(line).count("T"))
			if lv.bezirgan != null:
				bz += 1
				wall_ok = wall_ok and lv.bezirgan_ok()
		en /= n_seed
		el /= n_seed
		tr /= n_seed
		tot_bz += bz
		tot_lv += n_seed
		# altın tanesi ortalaması 2 x altin_k; sıradan 2-4 tane (3), seçkin +10 (13), hazine 6; boss (2, 4, 6, 8. derinlik sonu) 30
		var g := (en * 3.0 + el * 13.0 + tr * 6.0 + (30.0 if Game.BOSS_AFTER.has(d) else 0.0)) * 2.0 * Pazar.altin_k(d)
		var pr := _fiyat_ort(d)
		_p("EKONOMI %d | %.1f %.1f %.1f | %d | %d/%d %s | %d %d %d | %d | %d | %d" % [d, en, el, tr, int(g), bz, n_seed, "duvar_ok" if wall_ok else "DUVARDA", pr[0], pr[1], pr[2], Pazar.sifa_fiyat(d), Pazar.tomar_fiyat(d), Pazar.yenile_fiyat(0, d)])
		_check(wall_ok, "d%d bezirgân duvarda değil" % d)
	_p("EKONOMI bezirgân toplam %d / %d bölüm" % [tot_bz, tot_lv])


func _fiyat_ort(d: int) -> Array:
	var sums := [0.0, 0.0, 0.0]
	var cnt := [0, 0, 0]
	var tier := Zorluk.kademe(d)
	for i in 300:
		var it := ItemGen.random_drop(tier)
		var r := int(it.get("rarity", 0))
		if String(it.get("cat", "")) != "weapons" or r > 2:
			continue
		sums[r] += Pazar.esya_fiyat(it, d)
		cnt[r] += 1
	return [int(sums[0] / maxi(1, cnt[0])), int(sums[1] / maxi(1, cnt[1])), int(sums[2] / maxi(1, cnt[2]))]


# ------------------------------------------------------------------ pazar
func _pazar_kur(d := 3) -> void:
	Level.bezirgan_zorla = true   # şanstan bağımsız: bu bölümde kesin
	await _build(d)
	Level.bezirgan_zorla = false
	var lv: Node = main.level
	await _frames(2)
	if lv.bezirgan == null:
		return
	var pl: Player = lv.player
	pl.global_position = lv.bezirgan.global_position + Vector2(-26, -2)
	pl.velocity = Vector2.ZERO
	pl.facing = 1
	Game.camera.reset_smoothing()
	await _frames(4)


func _pazar() -> void:
	await _pazar_kur(3)
	var lv: Node = main.level
	_check(lv.bezirgan != null, "bezirgân yerleşti")
	if lv.bezirgan == null:
		return
	var bz: Bezirgan = lv.bezirgan
	_check(lv.bezirgan_ok(), "tezgâh ve tüccar duvarın içinde değil")
	_check(bz.near, "oyuncu tüccarın yanında (W balonu)")
	Game.run["gold"] = 2000
	# pazarı oyunun yolundan aç: Level.tuccar_requested -> Main._on_tuccar
	lv.tuccar_requested.emit()
	await _frames(3)
	_check(main.hud.mode == "tuccar" and get_tree().paused, "pazar açıldı (oyun duraklı)")
	_check(bz.offers.size() >= 3 and bz.offers.size() <= 5, "mal sayısı 3-5 (%d)" % bz.offers.size())
	for i in bz.offers.size():
		var o: Dictionary = bz.offers[i]
		var extra := ""
		if String(o["tur"]) == "esya":
			var it: Dictionary = o["item"]
			extra = "%s · %s · %s" % [String(it["cat"]), String(Data.items["rarities"][int(it["rarity"])]["name"]), String(it["material"])]
			if String(it["cat"]) == "weapons":
				var cur: Dictionary = Game.run["slots"].get(lv.natural_slot(it), {})
				var dd := ItemGen.dps_oyuncu(it) - ItemGen.dps_oyuncu(cur)
				extra += " · SnH %s (%s%s)" % [ItemGen.fmt(ItemGen.dps_oyuncu(it)), "▲ +" if dd >= 0.0 else "▼ ", ItemGen.fmt(dd)]
		_p("mal %d: %s %s — %d altın %s" % [i, String(o["tur"]), Pazar.ad(o), int(o["fiyat"]), extra])
	# 1) ilk mal (silah): onay + alış
	main.hud.sel = 0
	var o0: Dictionary = bz.offers[0]
	var g0 := int(Game.run["gold"])
	var n_p: int = lv.pickups.size()
	main._tuccar_sec(0)
	_check(main.hud.tuccar_onay and int(Game.run["gold"]) == g0, "ilk basış onay soruyor, altın düşmedi")
	main._tuccar_sec(0)
	_check(int(Game.run["gold"]) == g0 - int(o0["fiyat"]), "altın düştü: %d -> %d (fiyat %d)" % [g0, int(Game.run["gold"]), int(o0["fiyat"])])
	_check(bool(o0["satildi"]), "mal SATILDI")
	_check(lv.pickups.size() == n_p + 1 and lv.pickups[lv.pickups.size() - 1].item == o0["item"], "eşya kilime (oyuncunun önüne) düştü")
	# SnH farkı: HUD'un çizdiği değer
	var it0: Dictionary = o0["item"]
	if String(it0["cat"]) == "weapons":
		var cur0: Dictionary = Game.run["slots"].get(lv.natural_slot(it0), {})
		var d_hud: float = main.hud._eff_dps(it0) - main.hud._eff_dps(cur0)
		_p("SnH farkı (kart / satır): %s → %s, fark %s%s" % [ItemGen.fmt(main.hud._eff_dps(cur0)), ItemGen.fmt(main.hud._eff_dps(it0)), "+" if d_hud >= 0.0 else "", ItemGen.fmt(d_hud)])
		_check(is_equal_approx(d_hud, ItemGen.dps_oyuncu(it0) - ItemGen.dps_oyuncu(cur0)), "kartın SnH farkı ItemGen.dps_oyuncu ile aynı")
	# 2) satılan malı yeniden almak olmaz
	var g1 := int(Game.run["gold"])
	main._tuccar_sec(0)
	_check(int(Game.run["gold"]) == g1 and not main.hud.tuccar_onay, "satılan mal yeniden alınamaz")
	# 3) şifa: şişe eksikken bir şişe dolar
	var si := -1
	var ti := -1
	for i in bz.offers.size():
		if String(bz.offers[i]["tur"]) == "sifa":
			si = i
		elif String(bz.offers[i]["tur"]) == "tomar":
			ti = i
	if si >= 0:
		Game.run["flasks"] = maxi(0, int(Game.run["max_flasks"]) - 1)
		var f0 := int(Game.run["flasks"])
		main._tuccar_sec(si)
		main._tuccar_sec(si)
		_check(int(Game.run["flasks"]) == f0 + 1, "Umay Sütü bir şişe doldurdu (%d -> %d)" % [f0, int(Game.run["flasks"])])
	if ti >= 0:
		var np2: int = lv.pickups.size()
		main._tuccar_sec(ti)
		main._tuccar_sec(ti)
		_check(lv.pickups.size() == np2 + 1 and lv.pickups[lv.pickups.size() - 1].kind == "tilsim", "Kut Tomarı kilime düştü")
	# 4) yetmeyen altın
	var ci := -1
	for i in bz.offers.size():
		if not bool(bz.offers[i]["satildi"]):
			ci = i
			break
	if ci >= 0:
		Game.run["gold"] = int(bz.offers[ci]["fiyat"]) - 1
		main._tuccar_sec(ci)
		main._tuccar_sec(ci)
		_check(not bool(bz.offers[ci]["satildi"]) and int(Game.run["gold"]) == int(bz.offers[ci]["fiyat"]) - 1, "altın yetmeyince satılmaz (%s)" % main.hud.flash_msg)
	# 5) yenileme
	Game.run["gold"] = 500
	var names0: Array = []
	for o in bz.offers:
		names0.append(Pazar.ad(o) + str(o["fiyat"]))
	var rc0 := Pazar.yenile_fiyat(0)
	main.hud.sel = bz.offers.size()
	main._tuccar_sec(bz.offers.size())
	var names1: Array = []
	for o in bz.offers:
		names1.append(Pazar.ad(o) + str(o["fiyat"]))
	_check(int(Game.run["gold"]) == 500 - rc0 and bz.rerolls == 1, "yenileme %d altın aldı" % rc0)
	_check(names0 != names1, "yenilemeden sonra mallar değişti")
	var none_sold := true
	for o in bz.offers:
		none_sold = none_sold and not bool(o["satildi"])
	_check(none_sold, "yeni mallar satılmamış")
	_check(Pazar.yenile_fiyat(1) > rc0, "ikinci yenileme daha pahalı (%d > %d)" % [Pazar.yenile_fiyat(1), rc0])
	await _frames(3)   # HUD birkaç kare pazarı çizsin (çizim hatası yakalansın)
	# 6) pazardan çık, kilimdeki eşyayı oyunun yolundan kuşan
	main._start_play()
	await _frames(2)
	var bought: Pickup = null
	for p in lv.pickups:
		if is_instance_valid(p) and p.kind == "item" and p.item == it0:
			bought = p
	if bought:
		var slot: String = lv.natural_slot(it0)
		Game.run["slots"][slot] = {}
		lv.try_equip(bought)
		await _frames(2)
		_check(Game.run["slots"][slot] == it0, "alınan eşya kuşanıldı (%s yuvası: %s)" % [slot, String(it0["name"])])
	else:
		_check(false, "alınan eşya kilimde bulunamadı")


# ------------------------------------------------------------------ parşömen
func _parsomen_id() -> String:
	var locked := ItemGen.locked_implemented()
	for id in locked:
		if String(Data.find_item(id).get("cat", "")) == "weapons":
			return id
	# hepsi açılmışsa: gelişmiş bir silahın kilidini test için geri al (kayıt sonunda geri yüklenir)
	for it in Data.items["weapons"]:
		if it.get("impl", false) and it.has("upgrade_of"):
			var ul: Array = Game.meta.get("unlocked", [])
			ul.erase(it["id"])
			Game.meta["unlocked"] = ul
			return String(it["id"])
	return ""


func _parsomen() -> void:
	main._build_hub()
	main._start_play()
	await _frames(4)
	var lv: Node = main.level
	var pl: Player = lv.player
	var dem: Node = null
	for n in lv.npcs:
		if n.id == "demirci":
			dem = n
	pl.global_position = Vector2(dem.global_position.x - 20.0, pl.global_position.y)
	pl.facing = 1
	await _frames(3)
	var id := _parsomen_id()
	_check(id != "", "açılacak parşömen var")
	if id == "":
		return
	var rolls: Array = []
	for k in 2:
		var ul: Array = Game.meta.get("unlocked", [])
		ul.erase(id)
		Game.meta["unlocked"] = ul
		Game.meta["blueprints"] = [id]
		Game.meta["kut_bank"] = 999
		var bank0 := int(Game.meta["kut_bank"])
		main._on_npc("demirci")
		await _frames(2)
		var n_p: int = lv.pickups.size()
		main.hud.sel = 0
		var ok: bool = main._demirci_ac(id)
		_check(ok, "parşömen açıldı (%s), Kut %d -> %d" % [id, bank0, int(Game.meta["kut_bank"])])
		_check(Game.is_unlocked(id) and id in ItemGen.unlocked(String(Data.find_item(id)["cat"])), "eşya düşme havuzunda")
		_check(lv.pickups.size() == n_p + 1, "önüne bir eşya düştü")
		var p: Pickup = lv.pickups[lv.pickups.size() - 1]
		var it: Dictionary = p.item
		_check(String(it.get("id", "")) == id and int(it.get("tier", -1)) == 0, "düşen eşya açılan silah, kademe 0")
		_check(p.global_position.distance_to(pl.global_position) < 60.0, "eşya oyuncunun önünde (%.0f px)" % p.global_position.distance_to(pl.global_position))
		_check(not main.hud.demirci_son.is_empty(), "Demirci kartı gösteriyor")
		var s := "%s | %s | %s | hasar %s hız %s krit %s | kalite %%%d | ek: %s | unsur %s | SnH %s" % [String(it["name"]), String(Data.items["rarities"][int(it["rarity"])]["name"]), String(it["material"]), ItemGen.fmt(float(it.get("dmg", 0))), ItemGen.fmt(float(it.get("aps", 0))), ItemGen.fmt(float(it.get("crit", 0))), int(it["quality"]), str((it["affixes"] as Array).map(func(a): return a["id"])), Unsur.of(it), ItemGen.fmt(ItemGen.dps_oyuncu(it))]
		_p("ARMAGAN %d: %s" % [k + 1, s])
		rolls.append(s)
		await _frames(4)   # HUD Demirci kartını çizsin
		main.hud.demirci_son = {}
		main._start_play()
		await _frames(2)
	_check(rolls.size() == 2 and rolls[0] != rolls[1], "iki açılışta farklı rastgele değerler")


# ------------------------------------------------------------------ çekim kipleri
func _ekran_kur() -> void:
	match _ekran:
		"dunya", "pazar":
			await _pazar_kur(int(_arg_or("--tuccar_derinlik", "3")))
			var lv: Node = main.level
			Game.run["gold"] = 286
			for e in get_tree().get_nodes_in_group("dusman"):
				if is_instance_valid(e) and e.global_position.distance_to(lv.player.global_position) < 500.0:
					e.queue_free()
			if _ekran == "dunya":
				lv.player.global_position = lv.bezirgan.global_position + Vector2(-190, -2)
				lv.player.facing = 1
				Game.camera.reset_smoothing()
				await _frames(20)
				lv.player.global_position = lv.bezirgan.global_position + Vector2(-42, -2)
				return
			await _frames(30)
			lv.tuccar_requested.emit()
			await _frames(2)
			main.hud.sel = 0
		"demirci", "yurt":
			main._build_hub()
			main._start_play()
			await _frames(4)
			var lv2: Node = main.level
			for n in lv2.npcs:
				if n.id == "demirci":
					lv2.player.global_position = Vector2(n.global_position.x - 22.0, lv2.player.global_position.y)
			lv2.player.facing = 1
			Game.camera.reset_smoothing()
			await _frames(20)
			var id := _parsomen_id()
			Game.meta["blueprints"] = [id, "tufan_yayi"] if id != "tufan_yayi" else [id]
			Game.meta["kut_bank"] = 999
			main._on_npc("demirci")
			await _frames(2)
			main._demirci_ac(id)
			if _ekran == "yurt":
				main.hud.demirci_son = {}
				main._start_play()
			# kalıcı kayıt: bu kipte test kendisi çıkmaz (Ayarlar --goruntu çıkar); kaydı hemen geri yaz
			Game.meta = _meta0.duplicate(true)
			Game.save_meta()


func _arg_or(name: String, def: String) -> String:
	for a in OS.get_cmdline_user_args():
		if String(a).begins_with(name + "="):
			return String(a).trim_prefix(name + "=")
	return def
