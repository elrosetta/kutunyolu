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


func _roll_range(r: Array, is_int: bool) -> Array:
	var lo := minf(r[0], r[1])
	var hi := maxf(r[0], r[1])
	var v := rng.randf_range(lo, hi)
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
	return roll(_wpick(pool, ws), tier)


func roll(id: String, tier: int = 0, material: String = "", rarity: int = -1, flaw: String = "?") -> Dictionary:
	var base := Data.find_item(id)
	if base.is_empty():
		push_error("Bilinmeyen eşya: %s" % id)
		return {}
	var cat: String = base["cat"]
	var t := clampi(tier, 0, 5)
	var mats: Array = Data.items["materials"]
	var mat: Dictionary
	if material != "":
		mat = Data.material_def(material)
	else:
		var ws: Array = []
		for m in mats:
			ws.append(m["weight"][t])
		mat = _wpick(mats, ws)
	var rars: Array = Data.items["rarities"]
	var rar_i := rarity
	if rar_i < 0:
		var ws2: Array = []
		for r in rars:
			ws2.append(r["weight"][t])
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
		var sq := rng.randf_range(0.92, 1.08)
		qs.append((dq - 0.85) / 0.3)
		qs.append((sq - 0.92) / 0.16)
		it["kind"] = base["kind"]
		it["dmg"] = float(base["dmg"]) * float(mat["dmg"]) * (1.0 + 0.6 * t) * dq
		it["aps"] = float(base["aps"]) * float(mat["speed"]) * sq
		it["crit"] = maxf(0.0, float(base["crit"]) + float(mat["crit"]) + rng.randf_range(-2.0, 3.0))
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
		it["power"] = (1.0 + 0.6 * t) * rng.randf_range(0.9, 1.1)
		it["kind"] = "gadget"
	if base.has("mech"):
		var mr := _roll_range(base["mech"]["range"], base["mech"].get("int", false))
		it["mech_id"] = base["mech"]["id"]
		it["mech_v"] = mr[0]
		qs.append(mr[1])
	var n_aff := int(R["affixes"]) + (1 if mat["id"] == "gok_demiri" else 0)
	var target := "weapon" if cat == "weapons" else ("shield" if cat == "shields" else "gadget")
	var pool: Array = []
	for a in Data.items["affixes"]:
		var fr: Array = a["for"]
		if fr.has(target) or (target == "weapon" and base.get("kind", "") in ["bow", "throw", "magic"] and fr.has("ranged")):
			pool.append(a)
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
	var pre := ""
	if it["affixes"].size() > 0:
		pre = affix_def(it["affixes"][0]["id"]).get("adj", "") + " "
	return pre + Unsur.name_adj(it) + Data.material_def(it["material"])["adj"] + " " + it["name_base"]


func fmt(v: float) -> String:
	if absf(v - roundf(v)) < 0.01 or absf(v) >= 10.0:
		return str(int(roundf(v)))
	return ("%.1f" % v).replace(".", ",")


func describe(it: Dictionary) -> Array:
	var base := Data.find_item(it["id"])
	var lines: Array = []
	if base.has("mech"):
		lines.append(String(base["mech"]["desc"]).replace("{v}", fmt(it.get("mech_v", 0.0))))
	elif base.has("desc"):
		lines.append(base["desc"])
	for a in it["affixes"]:
		lines.append("• " + String(affix_def(a["id"]).get("desc", "")).replace("{v}", fmt(a["v"])))
	lines.append_array(Unsur.describe(it))   # v20 unsur satırları
	return lines


func dps(it: Dictionary) -> float:
	if it.get("cat", "") != "weapons":
		return 0.0
	var hd := 1.0 + aff(it, "hasar") / 100.0
	var hs := 1.0 + aff(it, "hiz") / 100.0
	var cc := clampf((float(it["crit"]) + aff(it, "krit_sans")) / 100.0, 0.0, 1.0)
	var cm := float(it["crit_mult"]) + aff(it, "krit_hasar") / 100.0
	var slow := 0.88 if it["flaw"] == "agir" else 1.0
	return float(it["dmg"]) * hd * float(it["aps"]) * hs * slow * (1.0 + cc * (cm - 1.0))
