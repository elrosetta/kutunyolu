extends Node
## Eşya üreteci: her düşüşte malzeme, nadirlik, hasar, hız, kritik, mekanik değeri ve
## ek özellikler yeniden yuvarlanır. Aynı silah tipi iki kez aynı gelmez.
## Veri aralıkları [en kötü, en iyi] sırasındadır; kalite yüzdesi buna göre hesaplanır.

var rng := RandomNumberGenerator.new()


func _ready() -> void:
	rng.randomize()


func _wpick(list: Array, weights: Array) -> Variant:
	var total := 0.0
	for w in weights:
		total += float(w)
	var r := rng.randf() * total
	for i in list.size():
		r -= float(weights[i])
		if r <= 0.0:
			return list[i]
	return list[list.size() - 1]


func _roll_range(r: Array, is_int: bool, g: RandomNumberGenerator = null) -> Array:
	## [değer, kalite 0..1]; g verilirse o zarla (v32 Usta: konak tohumuyla belirlenimci)
	var lo := minf(r[0], r[1])
	var hi := maxf(r[0], r[1])
	var v := (g if g else rng).randf_range(lo, hi)
	if is_int:
		v = roundf(v)
	var q := 0.5
	if r[0] != r[1]:
		q = clampf((v - float(r[0])) / (float(r[1]) - float(r[0])), 0.0, 1.0)
	return [v, q]


func implemented(cat: String) -> Array:
	var out: Array = []
	for it in Data.items[cat]:
		if it.get("impl", false):
			out.append(it["id"])
	return out


func unlocked(cat: String) -> Array:
	## Düşme havuzu: çalışan VE açılmış eşyalar (parşömenle Demirci'de açılanlar dahil).
	var out: Array = []
	for id in implemented(cat):
		if Game.is_unlocked(id):
			out.append(id)
	return out


func locked_implemented() -> Array:
	## Parşömeni düşebilecek eşyalar: çalışan ama henüz açılmamış ve parşömeni toplanmamış.
	var out: Array = []
	for cat in ["weapons", "shields", "gadgets"]:
		for id in implemented(cat):
			if not Game.is_unlocked(id) and not (id in Game.meta.get("blueprints", [])):
				out.append(id)
	return out


func random_drop(tier: int) -> Dictionary:
	## Gelişmiş sürümler (upgrade_of) yalnızca yeterli derinlikte (min_tier) düşer; düştüklerinde daha olasıdır.
	var cat: String = _wpick(["weapons", "shields", "gadgets"], [6, 2, 2])
	var ids := unlocked(cat)
	if ids.is_empty():
		ids = unlocked("weapons")
	if ids.is_empty():
		ids = implemented("weapons")
	var pool: Array = []
	var ws: Array = []
	for id in ids:
		var base := Data.find_item(id)
		var mt := int(base.get("min_tier", 0))
		if tier < mt:
			continue
		pool.append(id)
		ws.append(1.4 if base.has("upgrade_of") else 1.0)
	if pool.is_empty():
		pool = ids
		ws = []
		for id in ids:
			ws.append(1.0)
	# v44 Mühür yolu: nadirlik zarı mühür kadar ileri, nadirlik tabanı, kademe eki (mühürsüzde -1: eski zar)
	return roll(_wpick(pool, ws), clampi(tier + MuhurYolu.kademe_ek(), 0, 8), "", MuhurYolu.nadirlik_zar(tier))


func tuccar_drop(tier: int, rar_t: int, cat := "") -> Dictionary:
	## v34 Bezirgân malı: random_drop'un havuzu (açılmış eşyalar, en düşük kademe, gelişmiş sürüm x1,4) ama kategori
	## verilebilir ve nadirlik zarı rar_t sütunundan (items.json rarities.weight; pazar daha iyi nadirlik çeker)
	var c := cat if cat != "" else String(_wpick(["weapons", "shields", "gadgets"], [6, 2, 2]))
	var ids := unlocked(c)
	if ids.is_empty():
		ids = unlocked("weapons")
	if ids.is_empty():
		ids = implemented("weapons")
	var pool: Array = []
	var ws: Array = []
	for id in ids:
		var base := Data.find_item(id)
		if tier < int(base.get("min_tier", 0)):
			continue
		pool.append(id)
		ws.append(1.4 if base.has("upgrade_of") else 1.0)
	if pool.is_empty():
		pool = ids
		ws = []
		for id in ids:
			ws.append(1.0)
	var rars: Array = Data.items["rarities"]
	var rw: Array = []
	for r in rars:
		rw.append(_w_at(r["weight"], clampi(rar_t, 0, 8)))
	return roll(_wpick(pool, ws), tier, "", rars.find(_wpick(rars, rw)))


func roll(id: String, tier: int = 0, material: String = "", rarity: int = -1, flaw: String = "?") -> Dictionary:
	var base := Data.find_item(id)
	if base.is_empty():
		push_error("Bilinmeyen eşya: %s" % id)
		return {}
	var cat: String = base["cat"]
	# v22: kademe 0..8 (derinlik - 1; hasar Zorluk.esya_k); v23: malzeme / nadirlik ağırlıkları kademe başına
	# (0..8; dizi kısaysa son sütun): iyi eşya derinde ve seyrek
	var t := clampi(tier, 0, 8)
	var mats: Array = Data.items["materials"]
	var mat: Dictionary
	if material != "":
		mat = Data.material_def(material)
	else:
		var ws: Array = []
		for m in mats:
			ws.append(_w_at(m["weight"], t))
		mat = _wpick(mats, ws)
	var rars: Array = Data.items["rarities"]
	var rar_i := rarity
	if rar_i < 0:
		var ws2: Array = []
		for r in rars:
			ws2.append(_w_at(r["weight"], t))
		rar_i = rars.find(_wpick(rars, ws2))
	var R: Dictionary = rars[rar_i]
	# ongun: tek renk ya da iki renk ["kurt", "ayi"]; nadir eşyalar bazen ikinci bir renk kazanır
	var base_on: Array = []
	var bo: Variant = base.get("ongun", "kurt")
	if bo is Array:
		base_on = (bo as Array).duplicate()
	else:
		base_on = [String(bo)]
	var on2 := String(base_on[1]) if base_on.size() > 1 else ""
	if on2 == "" and rng.randf() < [0.0, 0.14, 0.28, 0.45][clampi(rar_i, 0, 3)]:
		var others: Array = ["kurt", "kartal", "ayi"]
		others.erase(String(base_on[0]))
		on2 = String(others[rng.randi_range(0, others.size() - 1)])
	var it := {"id": id, "cat": cat, "name_base": base["name"], "tier": t, "material": mat["id"], "rarity": rar_i,
		"ongun": String(base_on[0]), "ongun2": on2, "affixes": [], "flaw": "", "epithet": ""}
	var qs: Array = []
	if cat == "weapons":
		var dq := rng.randf_range(0.85, 1.15)
		var sq := rng.randf_range(0.95, 1.04)   # v26: hız yuvarlaması daraldı (0,92-1,08)
		qs.append((dq - 0.85) / 0.3)
		qs.append((sq - 0.95) / 0.09)
		it["kind"] = base["kind"]
		it["dmg"] = dmg_for(id, t, String(mat["id"]), rar_i) * dq
		it["aps"] = float(base["aps"]) * float(mat["speed"]) * sq
		# v23: kritik yuvarlaması daraldı (-1..+1,5; v22 -2..+3); v26 -1..+1
		it["crit"] = maxf(0.0, float(base["crit"]) + float(mat["crit"]) + rng.randf_range(-1.0, 1.0))
		it["crit_mult"] = float(base["crit_mult"]) + float(mat["crit_mult"])
	elif cat == "shields":
		var bq := rng.randf_range(0.9, 1.1)
		qs.append((bq - 0.9) / 0.2)
		it["block"] = clampf(float(base["block"]) * bq, 0.3, 1.0)
		it["parry_win"] = float(base["parry_win"])
		it["kind"] = "shield"
	else:
		var cq := rng.randf_range(0.9, 1.1)
		qs.append((1.1 - cq) / 0.2)
		it["cd"] = float(base["cd"]) * cq
		it["power"] = Zorluk.taban() * Zorluk.esya_k(t) * Zorluk.nadirlik_k(rar_i) * rng.randf_range(0.9, 1.1)
		it["kind"] = "gadget"
	if base.has("mech"):
		var mr := _roll_range(base["mech"]["range"], base["mech"].get("int", false))
		it["mech_id"] = base["mech"]["id"]
		it["mech_v"] = mr[0]
		qs.append(mr[1])
	if base.has("kizisma"):
		# v20 Kızışma pasifi: yük başına saldırı hızı yuvarlanır (kalite yüzdesine katılır), en çok yük sabit
		var kr := _roll_range(base["kizisma"]["range"], false)
		it["kz_v"] = roundf(float(kr[0]) * 2.0) / 2.0
		it["kz_max"] = int(base["kizisma"].get("max", 5))
		qs.append(kr[1])
	var n_aff := int(R["affixes"]) + (1 if mat["id"] == "gok_demiri" else 0)
	var pool := affix_pool(base, cat)
	pool.shuffle()
	for i in mini(n_aff, pool.size()):
		var a: Dictionary = pool[i]
		var ar := _roll_range(a["range"], a.get("int", false))
		it["affixes"].append({"id": a["id"], "v": ar[0]})
		qs.append(ar[1])
	if flaw == "?":
		if rng.randf() < 0.16 and cat == "weapons":
			var fl: Array = Data.items["flaws"]
			it["flaw"] = fl[rng.randi_range(0, fl.size() - 1)]["id"]
			it["dmg"] *= 1.15
	elif flaw != "":
		it["flaw"] = flaw
	if R["id"] == "efsanevi":
		var ep: Array = Data.items["epithets"]
		it["epithet"] = ep[rng.randi_range(0, ep.size() - 1)]
	var qsum := 0.0
	for q in qs:
		qsum += float(q)
	it["quality"] = int(round(100.0 * qsum / maxf(1.0, qs.size())))
	if material == "":
		Unsur.roll_into(it, base, rng)   # v20: yerden alınan (rastgele malzemeli) silaha unsur (Unsur.gd)
	it["name"] = item_name(it)
	return it


func dmg_for(id: String, tier: int, material := "demir", rarity := 0) -> float:
	## v22 silah hasarı: taban (items.json) x malzeme x kademe (Zorluk.esya_k) x nadirlik (Zorluk.nadirlik_k);
	## yuvarlanan kalite (0,85-1,15) ve kusur (+%15) roll() içinde eklenir. v23: x Zorluk.taban (0,7): güç tomarlardan
	var base := Data.find_item(id)
	return float(base.get("dmg", 8)) * float(Data.material_def(material).get("dmg", 1.0)) * Zorluk.taban() * Zorluk.esya_k(tier) * Zorluk.nadirlik_k(rarity)


func _w_at(w: Variant, t: int) -> float:
	## Ağırlık dizisinin t. sütunu (dizi kısaysa son değer)
	if w is Array:
		var a: Array = w
		return 0.0 if a.is_empty() else float(a[clampi(t, 0, a.size() - 1)])
	return float(w)


func affix_pool(base: Dictionary, cat: String) -> Array:
	## Bu eşya türüne gelebilecek ek özellik tanımları (silah / kalkan / teçhizat; uzak silaha "ranged" olanlar da)
	var target := "weapon" if cat == "weapons" else ("shield" if cat == "shields" else "gadget")
	var pool: Array = []
	for a in Data.items["affixes"]:
		var fr: Array = a["for"]
		if fr.has(target) or (target == "weapon" and base.get("kind", "") in ["bow", "throw", "magic"] and fr.has("ranged")):
			pool.append(a)
	return pool


func max_affix(it: Dictionary) -> int:
	## Düşüşte yuvarlanan ek özellik sayısı: nadirliğin yuvası (+1 gök demiri). v32 Usta bunun üstüne ek yuva nakşeder.
	var R: Dictionary = Data.items["rarities"][clampi(int(it.get("rarity", 0)), 0, Data.items["rarities"].size() - 1)]
	return int(R["affixes"]) + (1 if String(it.get("material", "")) == "gok_demiri" else 0)


func roll_affix(a: Dictionary, g: RandomNumberGenerator = null) -> Dictionary:
	## v32 Usta: bir ek özellik tanımından değer yuvarla ({"id", "v"}); g verilirse konak zarıyla
	var ar := _roll_range(a["range"], a.get("int", false), g)
	return {"id": a["id"], "v": ar[0]}


func reroll_affixes(it: Dictionary, g: RandomNumberGenerator = null) -> void:
	## v32 Usta "yeniden dövme": eşyadaki ek özelliklerin değerleri yeniden yuvarlanır (kimlikler kalır)
	for i in (it.get("affixes", []) as Array).size():
		var a: Dictionary = it["affixes"][i]
		var d := affix_def(String(a["id"]))
		if not d.is_empty():
			it["affixes"][i] = roll_affix(d, g)
	it["name"] = item_name(it)


func affix_def(aid: String) -> Dictionary:
	for a in Data.items["affixes"]:
		if a["id"] == aid:
			return a
	return {}


func aff(it: Dictionary, aid: String) -> float:
	var s := 0.0
	for a in it.get("affixes", []):
		if a["id"] == aid:
			s += float(a["v"])
	return s


func item_name(it: Dictionary) -> String:
	if it.has("emanet_ad"):
		return String(it["emanet_ad"])   # v44 mühür emaneti: sabit ad
	var pre := ""
	if it["affixes"].size() > 0:
		pre = affix_def(it["affixes"][0]["id"]).get("adj", "") + " "
	var ua := Unsur.name_adj(it)
	if pre == ua:
		pre = ""   # v32: nakış sıfatı unsur sıfatıyla aynıysa ("Ayazlı Ayazlı") bir kez yazılır
	return pre + ua + Data.material_def(it["material"])["adj"] + " " + it["name_base"]


func fmt(v: float) -> String:
	if absf(v - roundf(v)) < 0.01 or absf(v) >= 10.0:
		return str(int(roundf(v)))
	return ("%.1f" % v).replace(".", ",")


func describe(it: Dictionary) -> Array:
	var base := Data.find_item(it["id"])
	var lines: Array = []
	if it.has("emanet"):
		lines.append(MuhurYolu.emanet_satir(it))   # v44
	if base.has("mech"):
		lines.append(String(base["mech"]["desc"]).replace("{v}", fmt(it.get("mech_v", 0.0))))
	elif base.has("desc"):
		lines.append(base["desc"])
	if it.has("kz_v"):
		var kd: String = Data.items.get("pasifler", {}).get("kizisma", {}).get("desc", "Kızışma: her isabet +%{v} saldırı hızı (en çok {n} yük).")
		lines.append(kd.replace("{v}", fmt(float(it["kz_v"]))).replace("{n}", str(int(it.get("kz_max", 5)))).replace("{t}", fmt(float(it["kz_v"]) * int(it.get("kz_max", 5)))))
	for a in it["affixes"]:
		lines.append("• " + String(affix_def(a["id"]).get("desc", "")).replace("{v}", fmt(a["v"])))
	lines.append_array(Unsur.describe(it))   # v20 unsur satırları
	return lines


const MELEE_KINDS := ["slash", "dual", "heavy", "thrust", "whip"]


func hiz_pct(it: Dictionary) -> float:
	## v20: bu silahın kalıcı saldırı hızı (yüzde; silah niteliği + kuşanılan teçhizat + Kurt / lütuf / Umay, üst sınırlı)
	return Player.hiz_kalici(it)


func aps_eff(it: Dictionary) -> float:
	## v20: kartta görünen "Hız": yakın silahta gerçek tempodan (zincir boyunca vuruş / sn, Player.tempo_aps), uzak
	## silahta 1 / bekleme (yayda gerilme + kilit) — ikisi de saldırı hızı statıyla
	if it.get("cat", "") != "weapons":
		return 0.0
	if Silah27.owns_sec(it):
		return Silah27.card_aps(it)   # v27: Tatar Yayı (kurma), Küzgü (tik), Tengri Bağı
	var pct := hiz_pct(it)
	if String(it.get("kind", "")) in MELEE_KINDS:
		return float(Player.tempo_aps(it, pct)[0])
	if it.get("kind", "") == "bow":
		return 1.0 / maxf(0.05, Okculuk.kart_tur(it))   # v25: yayın gerçek atış turu (gerilme + pencere + kilit)
	var k := float(Player.HIZ["atis"])
	var a := float(it["aps"]) * (1.0 + Player.hiz_oran(it, pct) * k)
	if it.get("kind", "") == "throw":
		a = 1.0 / (1.0 / maxf(0.05, a) + 0.09)   # v25: fırlatma bekleme sonrası atılır (Player throw_t 0,07 sn + kare)
	return a


func uzak_vurus(it: Dictionary) -> float:
	## v25: fırlatma / büyü atışı başına hedefe değen mermi sayısı (kartta): Kartal Tüyleri tüy sayısı
	if String(it.get("mech_id", "")) == "gudum":
		return float(int(it.get("mech_v", 3)))
	return 1.0


func krit_sans(it: Dictionary, oyuncu := true) -> float:
	## v23: vuruşun şans kritiği (yüzde): silah + "İsabetli" niteliği; oyuncu: + Ay Ata lütfu + Segrek adı.
	## Player._deal ve SnH aynı sayıyı kullanır.
	var c := float(it.get("crit", 0.0)) + aff(it, "krit_sans")
	if oyuncu and not Game.run.is_empty():
		if Game.has_lutuf("ay_ata"):
			c += Zorluk.lutuf_krit()
		if Adlar.earned("segrek"):
			c += Zorluk.segrek_krit()
	return c


func krit_carpan(it: Dictionary) -> float:
	return float(it.get("crit_mult", 1.9)) + aff(it, "krit_hasar") / 100.0


static func bitiris_adimi(it: Dictionary, c: Dictionary) -> bool:
	## v23: zincirin "bitiriş" adımı mı (ritimsiz basışta kritik değil Zorluk.bitiris_k hasar; yankı / usulde kritik):
	## ağır silahların bitiriş kritiği (fc), zincir içi kesin kritik adımı (Yatağan geri sıçrayışı), Alp'in üçüncü
	## vuruşu (ucuncu_vurus), Ay Palası'nın son vuruşu (ay_dansi)
	if c.get("fc", false):
		return true
	if c.get("crit", false) and not c.get("special", false) and not c.has("name"):
		return true
	var m := String(it.get("mech_id", ""))
	return c.get("last", false) and (m == "ucuncu_vurus" or m == "ay_dansi")


func zincir_vurus(it: Dictionary) -> float:
	## v23: bir zincir turunda düşmana değen vuruş sayısı (çok vuruşlu savuruşun ilk geçişi dahil; yer şoku hariç)
	var n_t := 0.0
	for c in Player._combo_for(it)["chain"]:
		var sw: Dictionary = Player.swing_def(c["s"])
		var n := float((sw["multi"] as Array).size()) if sw.has("multi") else 1.0
		if sw.has("multi") and Player._contact_k(sw) < float(sw["multi"][0]) - 0.04 and not c.get("through", false):
			n += 1.0   # (içinden geçişte gövde hedefin öbür yanına geçer: işaret sayısı kadar)
		n_t += n * (2.0 if c.get("double", false) else 1.0)
	return n_t


func zincir_hasar(it: Dictionary) -> float:
	## v23: bir zincir turunun toplam hasar çarpanı (taban hasara göre): adım çarpanları x gerçek vuruş sayısı x
	## bitiriş çarpanı (Alp'in üçüncü vuruşu +%mech_v dahil) + çift vuruşun ikincisi (%70) + yer şoku (%50)
	var chain: Array = Player._combo_for(it)["chain"]
	var a := 0.0
	for c in chain:
		var sw: Dictionary = Player.swing_def(c["s"])
		var n := float((sw["multi"] as Array).size()) if sw.has("multi") else 1.0
		# çok vuruşlu savuruş: temas ilk işaretten önce başlarsa ilk geçiş de vurur (işaretlerde vuruş listesi yenilenir)
		if sw.has("multi") and Player._contact_k(sw) < float(sw["multi"][0]) - 0.04 and not c.get("through", false):
			n += 1.0   # (içinden geçişte gövde hedefin öbür yanına geçer: işaret sayısı kadar)
		if c.get("double", false):
			n *= 1.7
		var k := 1.0
		if bitiris_adimi(it, c):
			k *= Zorluk.bitiris_k()
		if c.get("last", false) and String(it.get("mech_id", "")) == "ucuncu_vurus":
			k *= 1.0 + float(it.get("mech_v", 0.0)) / 100.0
		a += n * float(c.get("mult", 1.0)) * k
		if c.get("shock", false):
			a += 0.5   # yer şoku: önündeki düşmana tabanın yarısı (Player._attack_fx)
	return a


const KARE := 1.0 / 60.0


func zincir_sure(it: Dictionary) -> float:
	## v23: sürekli basışta bir zincir turunun süresi (sn): Player.tempo_phases ile; zincir baştan başlarken ilk
	## hazırlık (zincir dışı) ve adım başına bir kare (oyun savuruşu 60 Hz karede başlatır). tools/tests/tomar_testi.gd
	## ölçülen hasarla karşılaştırır.
	var chain: Array = Player._combo_for(it)["chain"]
	var hz := Player.hiz_oran(it, hiz_pct(it))
	var t := 0.0
	for i in chain.size():
		var c: Dictionary = chain[i]
		var sw: Dictionary = Player.swing_def(c["s"])
		var spd := 1.0
		if it.get("kind", "") == "dual":
			spd *= 1.0 + Player.DUAL_RAMP * i
		if it.get("mech_id", "") == "ay_dansi":
			spd *= 1.0 + float(it.get("mech_v", 6.0)) / 100.0 * i
		if it.get("flaw", "") == "agir":
			spd *= 0.88
		var ph: Array = Player.tempo_phases(it, c, sw, i > 0, spd, "", hz)
		t += float(ph[0]) + float(ph[1]) + float(ph[2]) + float(ph[4]) + KARE
	return t


func dps(it: Dictionary, oyuncu := false) -> float:
	## v20: yakın silahta saniyedeki hasar gerçek tempodan: zincirin adım çarpanları / zincir süresi (TEMPO + v20
	## yavaşlaması + saldırı hızı; "Ağır" kusuru ve ikiz bıçak / Ay Dansı hızlanması dahil). Kızışma yükleri sayılmaz.
	## v23: tur hasarı / tur süresi (zincir_hasar / zincir_sure; bitiriş çarpanı, çok vuruş, yer şoku dahil). oyuncu: şans kritiği lütuf / adla (krit_sans), tomar statı
	## (Game.item_mult) ve oyuncunun genel hasar çarpanları (Erlik'in Gölgesi, Alp Er Tunga) dahil: kartın gösterdiği
	## sayı (dps_oyuncu). Kombo sayacı (+%1,5 / vuruş), usul, Kızışma, koşul kritikleri ve düşmana göre çarpanlar sayılmaz.
	if it.get("cat", "") != "weapons":
		return 0.0
	var hd := 1.0 + aff(it, "hasar") / 100.0
	var cc := clampf(krit_sans(it, oyuncu) / 100.0, 0.0, 1.0)
	var cm := krit_carpan(it)
	var rate := 0.0
	if String(it.get("kind", "")) in MELEE_KINDS:
		rate = zincir_hasar(it) / maxf(0.01, zincir_sure(it))
	else:
		# v25: yayda tur başına ok x tam gerilme çarpanı (Okculuk.kart_hiz; cephaneli yayda dolu cephane), fırlatmada mermi sayısı
		rate = (Okculuk.kart_hiz(it) if it.get("kind", "") == "bow" else aps_eff(it) * uzak_vurus(it)) * (0.88 if it["flaw"] == "agir" else 1.0)
		if Silah27.owns_sec(it):
			rate = Silah27.card_rate(it) * (0.88 if it["flaw"] == "agir" else 1.0)   # v27 (Silah27.card_rate)
	var v := float(it["dmg"]) * hd * rate * (1.0 + cc * (cm - 1.0))
	if oyuncu:
		v *= Game.item_mult(it) * genel_k()
	return v


func genel_k() -> float:
	## Oyuncunun her vuruşa işleyen genel hasar çarpanları (Player._deal ile aynı): Erlik'in Gölgesi, Alp Er Tunga adı
	var k := 1.0
	if Game.run.is_empty():
		return k
	if Game.has_lutuf("erlik"):
		k *= 1.35
	if Adlar.earned("alp_er_tunga"):
		k *= 1.15
	return k


func dps_oyuncu(it: Dictionary) -> float:
	## v23: kartta / yerdeki silahta görünen SnH: tomar statı ve oyuncunun kalıcı güçleriyle (tomar okununca artar)
	return dps(it, true)


func dps_tomarsiz(it: Dictionary) -> float:
	## Aynı silahın tomar statı olmadan SnH'si (kartta "tomarsız" karşılaştırması)
	return dps_oyuncu(it) / maxf(0.001, Game.item_mult(it))
