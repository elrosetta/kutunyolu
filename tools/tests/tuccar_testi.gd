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
##   ORAN (v34): birçok derinlikte (1-9) çok sayıda pazar ziyareti; oyuncunun o derinlikte tipik olarak taşıdığı donanım
##            oyunun kendi düşüş zarıyla kurulur (_tipik_donanim: başlangıç donanımı + her derinliğin kaide / yüksek çıkıntı /
##            hazine / seçkin düşüşleri, bulunanın en iyisi kuşanılır, beklenen tomar statıyla SnH), sonra Pazar.teklifler:
##            silah mallarının yüzde kaçı aynı yuvadaki silaha göre açık iyileşme (SnH >= +%10), ziyaret başına en az bir
##            iyileşme, iyileşmelerin fiyatı / bölüm başına toplanan altın. --tuccar_oran yalnızca bunu koşar
##            (--tuccar_ziyaret=N derinlik başına ziyaret, varsayılan 150).
## Çekim kipleri (--goruntu ile): --tuccar_ekran=dunya | pazar | demirci | yurt (kurar ve bekler, çıkmaz).
## Çıktı "[tuccar] ..." satırları, sonda "[tuccar] SONUC GECTI|KALDI".

var main: Node
var _fail: Array = []
var _meta0: Dictionary = {}
var _ekran := ""
var _altin_d: Dictionary = {}   # derinlik -> bölüm temizlenirse beklenen altın (EKONOMI)


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
	if OS.get_cmdline_user_args().has("--tuccar_oran"):
		await _oran()
		_p("SONUC %s%s" % ["GECTI" if _fail.is_empty() else "KALDI", "" if _fail.is_empty() else " (" + ", ".join(_fail) + ")"])
		get_tree().quit()
		return
	await _ekonomi()
	await _oran()
	await _pazar()
	await _parsomen()
	Game.meta = _meta0
	Game.save_meta()
	_p("kalıcı kayıt geri yüklendi")
	_p("SONUC %s%s" % ["GECTI" if _fail.is_empty() else "KALDI", "" if _fail.is_empty() else " (" + ", ".join(_fail) + ")"])
	get_tree().quit()


# ------------------------------------------------------------------ ekonomi
func _ekonomi() -> void:
	var n_seed := 6   # v34 birleştirme: 3 -> 6 (altın ölçümü gürültülüydü)
	var HT: Script = load("res://tools/tests/harita_testi.gd")
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
		var deger := 0.0
		var bz := 0
		var wall_ok := true
		for k in n_seed:
			await _build(d)
			var lv: Node = main.level
			deger += float(HT.icerik(lv)["deger"])
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
		# v34 birleştirme: bölümün altını harita testinin içerik ölçümünden (harita_testi.icerik: yerdeki taneler, yaratık
		# başına 1-2 tane (+%25) / seçkin +10, küp / gizli cep / lanetli sandık / kilitli oda); eski formül (sıradan 2-4 tane,
		# v25 parça "T" hazinesi) v34 yoğunluğunu ve düşük yaratık altınını görmüyordu. Boss (2, 4, 6, 8. derinlik sonu) 30 tane.
		var g := deger / n_seed + (30.0 if Game.BOSS_AFTER.has(d) else 0.0) * 2.0 * Pazar.altin_k(d)
		_altin_d[d] = g
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


# ------------------------------------------------------------------ v34 oran: pazar malları oyuncunun donanımına göre ne kadar iyi?
const TOPLAMA := 0.75   # bölümü koşan oyuncunun "hepsi" altınından topladığı pay (v24 ölçümü: %70-80)
const BULMA := 0.75     # oyuncunun bir bölümdeki eşya düşüşlerinden bulup baktığı pay


func _guc(it: Dictionary) -> float:
	## Kalkan / teçhizat karşılaştırma ölçüsü: teçhizatta güç, kalkanda blok x kademe x nadirlik (+ ek özellik başına %10)
	if it.is_empty():
		return 0.0
	match String(it.get("cat", "")):
		"weapons":
			return ItemGen.dps_oyuncu(it)
		"gadgets":
			return float(it.get("power", 0.0)) * (1.0 + 0.1 * (it.get("affixes", []) as Array).size())
		"shields":
			return float(it.get("block", 0.5)) * Zorluk.esya_k(int(it.get("tier", 0))) * Zorluk.nadirlik_k(int(it.get("rarity", 0))) * (1.0 + 0.1 * (it.get("affixes", []) as Array).size())
	return 0.0


func _yuva(it: Dictionary) -> String:
	if String(it.get("cat", "")) == "gadgets":
		return "g1"
	return "second" if Player.is_second_item(it) else "melee"


func _karsi(it: Dictionary, sl: Dictionary, kalkan: Dictionary) -> float:
	## Malın aynı yuvadaki kuşanılana göre oranı (1,0 = eşit). Kalkan: en iyi bulunan kalkana; teçhizat: zayıf olana.
	match String(it.get("cat", "")):
		"weapons":
			var cur: Dictionary = sl.get(_yuva(it), {})
			if cur.is_empty() or String(cur.get("cat", "")) != "weapons":
				return 2.0
			return ItemGen.dps_oyuncu(it) / maxf(0.01, ItemGen.dps_oyuncu(cur))
		"shields":
			return 2.0 if kalkan.is_empty() else _guc(it) / maxf(0.01, _guc(kalkan))
		"gadgets":
			var a := _guc(sl.get("g1", {}))
			var b := _guc(sl.get("g2", {}))
			var lo := minf(a, b)
			return 2.0 if lo <= 0.0 else _guc(it) / lo
	return 0.0


func _al(it: Dictionary, sl: Dictionary, kalkan: Dictionary) -> void:
	## Tipik oyuncu bulduğu eşyayı yuvasındakinden iyiyse kuşanır (kalkan ayrı izlenir; ikinci yuvada yay kalır)
	match String(it.get("cat", "")):
		"weapons":
			var y := _yuva(it)
			if sl.get(y, {}).is_empty() or _karsi(it, sl, kalkan) > 1.0:
				sl[y] = it
		"shields":
			if kalkan.is_empty() or _guc(it) > _guc(kalkan):
				kalkan.clear()
				kalkan.merge(it)
		"gadgets":
			if sl.get("g2", {}).is_empty():
				sl["g2"] = it
			elif _karsi(it, sl, kalkan) > 1.0:
				var weak := "g1" if _guc(sl["g1"]) <= _guc(sl["g2"]) else "g2"
				sl[weak] = it


func _tipik_donanim(d: int) -> Dictionary:
	## d. derinlikteki pazara gelen tipik oyuncu: başlangıç donanımı; 1..d-1 derinliklerin düşüşleri tam, d.'nin yarısı
	## (pazar bölümün ortasında). Bölüm başına düşüş (Level): 3 kaide (kademe), yüksek çıkıntı (kademe+1), %50 alçak
	## çıkıntı (kademe), hazine / seçkin (kademe+1, ~1,5); her biri BULMA şansıyla görülür. Tomar statı beklenen modelden.
	Game.new_run()
	var sl: Dictionary = Game.run["slots"]
	var kalkan := {}
	for j in range(1, d + 1):
		Game.run["depth"] = j
		Game.run["tier"] = Zorluk.kademe(j)
		Game.run["ongun"] = Zorluk.beklenen_tomar(j)
		var t := Zorluk.kademe(j)
		var drops: Array = [t, t, t, t + 1, t + 1, t + 1]
		if randf() < 0.5:
			drops.append(t)
		var pay := 1.0 if j < d else 0.5
		for dt in drops:
			if randf() < BULMA * pay:
				_al(ItemGen.random_drop(mini(8, int(dt))), sl, kalkan)
	Game.run["depth"] = d
	Game.run["tier"] = Zorluk.kademe(d)
	var o := Zorluk.beklenen_tomar(d)
	o["kurt"] = int(o["kurt"]) + 1   # bölümün ilk yarısındaki tomar
	Game.run["ongun"] = o
	return kalkan


func _oran() -> void:
	var n := 150
	for a in OS.get_cmdline_user_args():
		if String(a).begins_with("--tuccar_ziyaret="):
			n = int(String(a).trim_prefix("--tuccar_ziyaret="))
	_p("ORAN d | silah malı: açık iyileşme (>= +%%10) / herhangi > 0 | ziyarette >= 1 iyileşme (her mal) | gözde iyileşme | iyileşen silah fiyatı ort | bölüm altını (x%.2f) | fiyat / bölüm altını | tipik melee SnH" % TOPLAMA)
	var run0: Dictionary = Game.run.duplicate(true)
	var tot_w := 0
	var tot_up := 0
	var tot_v := 0
	var tot_vup := 0
	var oran_top := 0.0   # v34 birleştirme: iyileşen silah fiyatı / bölüm altını ortalaması (hedef ~1: bölüm başına bir iyi mal)
	var oran_n := 0
	for d in range(1, 10):
		var nw := 0
		var nup := 0
		var npos := 0
		var nvup := 0
		var ngz := 0
		var ngz_up := 0
		var fiyat_up := 0.0
		var melee_dps := 0.0
		for v in n:
			var kalkan := _tipik_donanim(d)
			var sl: Dictionary = Game.run["slots"]
			melee_dps += ItemGen.dps_oyuncu(sl["melee"])
			var offers: Array = Pazar.teklifler(d, false)
			var any := false
			for o in offers:
				if String(o["tur"]) != "esya":
					continue
				var it: Dictionary = o["item"]
				var r := _karsi(it, sl, kalkan)
				if r >= 1.1:
					any = true
				if bool(o.get("gozde", false)):
					ngz += 1
					if r >= 1.1:
						ngz_up += 1
				if String(it["cat"]) != "weapons":
					continue
				nw += 1
				if r >= 1.1:
					nup += 1
					fiyat_up += float(o["fiyat"])
				if r > 1.0:
					npos += 1
			if any:
				nvup += 1
		var g: float = float(_altin_d.get(d, 0.0))
		if g <= 0.0:
			g = 150.0 * Pazar.altin_k(d)   # yalnızca --tuccar_oran: EKONOMI ölçümü yoksa kaba tahmin
		var gl := g * TOPLAMA
		var fu := fiyat_up / maxf(1.0, float(nup))
		_p("ORAN %d | %%%d / %%%d | %%%d | %s | %d | %d | %.2f | %s" % [d, int(round(100.0 * nup / maxf(1.0, nw))), int(round(100.0 * npos / maxf(1.0, nw))), int(round(100.0 * nvup / float(n))), ("%%%d (%d)" % [int(round(100.0 * ngz_up / maxf(1.0, ngz))), ngz]) if ngz > 0 else "-", int(fu), int(gl), fu / maxf(1.0, gl), ItemGen.fmt(melee_dps / float(n))])
		if nup > 0 and _altin_d.has(d):
			oran_top += fu / maxf(1.0, gl)
			oran_n += 1
		tot_w += nw
		tot_up += nup
		tot_v += n
		tot_vup += nvup
	_p("ORAN toplam | silah malı açık iyileşme %%%d | ziyarette >= 1 iyileşme %%%d" % [int(round(100.0 * tot_up / maxf(1.0, tot_w))), int(round(100.0 * tot_vup / maxf(1.0, tot_v)))])
	if oran_n > 0:
		var om := oran_top / float(oran_n)
		_p("ORAN alım | iyileşen silah fiyatı / bölüm altını ort %.2f -> bölüm başına %.2f iyi mal, bir bölüm biriktirince %.2f" % [om, 1.0 / om, 2.0 / om])
		_check(om >= 0.8 and om <= 1.25, "Bezirgân alımı: bölüm başına ~1 iyi mal, biriktirince ~2 (fiyat / bölüm altını %.2f; 0,8-1,25)" % om)
	Game.run = run0


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
	_check(bz.offers.size() >= 3 and bz.offers.size() <= 6, "mal sayısı 3-6 (%d)" % bz.offers.size())
	# v34: ilk mal "Bezirgân'ın gözdesi": oyuncunun aynı yuvadaki silahından açıkça iyi (Pazar.iyilesme >= esik)
	var gz_o: Dictionary = bz.offers[0]
	var gz_iy := Pazar.iyilesme(gz_o["item"])
	_check(bool(gz_o.get("gozde", false)) and gz_iy >= float(Pazar.data().get("pazar", {}).get("gozde", {}).get("esik", 1.15)) * 0.97,
		"gözde mal açık iyileşme (x%.2f, %s)" % [gz_iy, String(gz_o["item"].get("name", ""))])
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
