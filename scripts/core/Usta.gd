class_name Usta
extends RefCounted
## v32 Bengisu Usta: konaktaki silah ustası. Altınla, koşu zarıyla (konak tohumu) silaha hizmet verir:
##   nakis   Nakış: üç aday ek özellik yuvarlanır (nadir olanlar daha seyrek ve pahalı), biri seçilip silaha işlenir;
##           yuva sınırı nadirliğin ek özellik sayısı + 1 (+1 gök demiri)
##   dovme   Yeniden dövme: bütün ek özelliklerin değerleri yeniden yuvarlanır; aynı silahta her kullanım pahalanır
##   unsur   Unsur aşılama: rastgele (ucuz) ya da seçilen (pahalı) unsur, eskisinin yerine
##   kalite  Kalite: görünen şansla +5..15 kalite puanı (hasar puan başına x1,003); başarısızlıkta altın gider
##   muhur   Kut Mührü: ucuz kumar; nakış / kalite / unsur / kusur silme gelebilir, kusur da gelebilir
## Bütün sayılar data/usta.json'da; fiyat çarpanı Pazar.derinlik_k (tuccar.json) x nadirlik. Arayüz HUD._draw_usta,
## akış Main (_usta_*). Ölçüm: -- --konak (tools/tests/konak_testi.gd).

const PATH := "res://data/usta.json"
const HIZMETLER := ["nakis", "dovme", "unsur", "kalite", "muhur"]
const AD := {"nakis": "Nakış", "dovme": "Yeniden dövme", "unsur": "Unsur aşılama", "kalite": "Kalite", "muhur": "Kut Mührü"}
static var _d: Dictionary = {}
static var rng := RandomNumberGenerator.new()
static var _adaylar: Dictionary = {}   # yuva -> nakış adayları (konak başına bir kez yuvarlanır)
static var tohum := 0


static func data() -> Dictionary:
	if _d.is_empty():
		_d = Data.load_json(PATH)
	return _d


static func yeni_konak(seed_v: int) -> void:
	## Konak kurulurken: zar konak tohumuyla, adaylar sıfırlanır (aynı tohum aynı adaylar: test belirlenimci)
	tohum = seed_v
	rng.seed = seed_v
	_adaylar.clear()


static func ad() -> String:
	return String(data().get("ad", "Bengisu Usta"))


static func soz(biome: String, key := "usta") -> String:
	var s: Dictionary = data().get("sozler", {})
	var b: Dictionary = s.get(biome, s.get("_varsayilan", {}))
	return String(b.get(key, s.get("_varsayilan", {}).get(key, "")))


static func silahlar() -> Array:
	## Usta'nın bakacağı yuvalar: kuşanılı silahlar (yakın / uzak)
	var out: Array = []
	if Game.run.is_empty():
		return out
	for k in ["melee", "second"]:
		var it: Dictionary = Game.run["slots"].get(k, {})
		if not it.is_empty() and String(it.get("cat", "")) == "weapons":
			out.append(k)
	return out


static func derinlik() -> int:
	return 1 if Game.run.is_empty() else maxi(1, int(Game.run.get("depth", 1)))


static func fiyat_k(it: Dictionary, d := -1) -> float:
	var nk: Array = data().get("nadirlik_k", [1.0])
	return Pazar.derinlik_k(d) * float(nk[clampi(int(it.get("rarity", 0)), 0, nk.size() - 1)])


static func _f(v: float) -> int:
	return maxi(5, int(round(v / 5.0)) * 5)


static func max_nakis(it: Dictionary) -> int:
	return ItemGen.max_affix(it) + int(data().get("nakis", {}).get("ek_yuva", 1))


static func nakis_sayi(it: Dictionary) -> int:
	return (it.get("affixes", []) as Array).size()


static func nadir_mi(aid: String) -> bool:
	return aid in data().get("nadir_nakis", [])


static func nakis_havuzu(it: Dictionary) -> Array:
	## Silaha gelebilecek, üstünde olmayan ek özellik tanımları
	var have: Array = []
	for a in it.get("affixes", []):
		have.append(String(a["id"]))
	var out: Array = []
	for a in ItemGen.affix_pool(Data.find_item(String(it.get("id", ""))), String(it.get("cat", "weapons"))):
		if not (String(a["id"]) in have):
			out.append(a)
	return out


static func nakis_fiyat(it: Dictionary, aid: String, d := -1) -> int:
	var n: Dictionary = data().get("nakis", {})
	var f := float(n.get("fiyat", 45)) * fiyat_k(it, d)
	if nadir_mi(aid):
		f *= float(n.get("nadir_k", 1.5))
	return _f(f)


static func nakis_adaylari(slot: String, it: Dictionary, d := -1) -> Array:
	## Bu konakta bu yuvanın adayları (bir kez yuvarlanır; silah değişirse yeniden): [{id, v, nadir, fiyat}]
	var key := "%s:%s" % [slot, String(it.get("name", ""))]
	if _adaylar.has(key):
		return _adaylar[key]
	var n: Dictionary = data().get("nakis", {})
	var pool := nakis_havuzu(it)
	var out: Array = []
	var k := mini(int(n.get("aday", 3)), pool.size())
	for i in k:
		var ws: Array = []
		for a in pool:
			ws.append(float(n.get("nadir_agirlik", 0.5)) if nadir_mi(String(a["id"])) else 1.0)
		var tot := 0.0
		for w in ws:
			tot += float(w)
		var r := rng.randf() * tot
		var pick := pool.size() - 1
		for j in pool.size():
			r -= float(ws[j])
			if r <= 0.0:
				pick = j
				break
		var a: Dictionary = pool[pick]
		pool.remove_at(pick)
		var ra := ItemGen.roll_affix(a, rng)
		out.append({"id": ra["id"], "v": ra["v"], "nadir": nadir_mi(String(a["id"])), "fiyat": nakis_fiyat(it, String(a["id"]), d)})
	_adaylar[key] = out
	return out


static func dovme_fiyat(it: Dictionary, d := -1) -> int:
	var v: Dictionary = data().get("dovme", {})
	return _f(float(v.get("fiyat", 25)) * fiyat_k(it, d) * (1.0 + float(v.get("artis", 0.5)) * float(int(it.get("usta_dovme", 0)))))


static func unsur_fiyat(it: Dictionary, secim: bool, d := -1) -> int:
	var v: Dictionary = data().get("unsur", {})
	return _f(float(v.get("fiyat", 40)) * fiyat_k(it, d) * (float(v.get("secim_k", 1.75)) if secim else 1.0))


static func unsur_olur(it: Dictionary) -> bool:
	return String(it.get("kind", "")) in Unsur.KINDS or String(it.get("id", "")) in Unsur.MAGIC_OK


static func kalite_fiyat(it: Dictionary, d := -1) -> int:
	return _f(float(data().get("kalite", {}).get("fiyat", 30)) * fiyat_k(it, d))


static func kalite_sansi(it: Dictionary) -> float:
	## Kalite yükseltme şansı: kalite arttıkça düşer (0,9 - 0,7 x kalite / 100, en az 0,2)
	var k: Dictionary = data().get("kalite", {})
	return clampf(float(k.get("sans_taban", 0.9)) - float(k.get("sans_egim", 0.7)) * float(it.get("quality", 50)) / 100.0, float(k.get("sans_en_az", 0.2)), 0.99)


static func muhur_fiyat(it: Dictionary, d := -1) -> int:
	return _f(float(data().get("muhur", {}).get("fiyat", 15)) * fiyat_k(it, d))


static func hizmetler(it: Dictionary, d := -1) -> Array:
	## Hizmet satırları: {id, ad, aciklama, fiyat, sans (-1 yoksa), uygun, neden}
	var out: Array = []
	var ad_n := nakis_sayi(it)
	var mx := max_nakis(it)
	var ok_n := ad_n < mx and not nakis_havuzu(it).is_empty()
	var fmin := 0
	for a in nakis_havuzu(it):
		var f := nakis_fiyat(it, String(a["id"]), d)
		fmin = f if fmin == 0 else mini(fmin, f)
	out.append({"id": "nakis", "ad": AD["nakis"], "aciklama": "Üç aday nakıştan birini seç; silaha yeni bir ek özellik işlenir (yuva %d / %d). Nadir nakışlar seyrek ve pahalı." % [ad_n, mx],
		"fiyat": fmin, "sans": -1.0, "uygun": ok_n, "neden": "Nakış yeri kalmadı (%d / %d)." % [ad_n, mx] if ad_n >= mx else "Bu silaha işlenecek nakış kalmadı."})
	out.append({"id": "dovme", "ad": AD["dovme"], "aciklama": "Bütün ek özelliklerin değerleri yeniden yuvarlanır (kimlikleri kalır). Aynı silahta her dövme %%%d pahalanır." % int(float(data().get("dovme", {}).get("artis", 0.5)) * 100.0),
		"fiyat": dovme_fiyat(it, d), "sans": -1.0, "uygun": ad_n > 0, "neden": "Dövülecek nakış yok."})
	out.append({"id": "unsur", "ad": AD["unsur"], "aciklama": "Silaha bir unsur (Od / Ayaz / Yıldırım / Kam / Yer-Su) aşılanır; eskisi silinir. Rastgele ucuz, seçerek x%s." % ItemGen.fmt(float(data().get("unsur", {}).get("secim_k", 1.75))),
		"fiyat": unsur_fiyat(it, false, d), "sans": -1.0, "uygun": unsur_olur(it), "neden": "Bu silah unsur taşımaz."})
	var ka: Array = data().get("kalite", {}).get("artis", [5, 15])
	out.append({"id": "kalite", "ad": AD["kalite"], "aciklama": "Şansla kalite +%d..%d puan (hasar da artar). Kalite yükseldikçe şans düşer; tutmazsa altın gider." % [int(ka[0]), int(ka[1])],
		"fiyat": kalite_fiyat(it, d), "sans": kalite_sansi(it), "uygun": int(it.get("quality", 50)) < 100, "neden": "Kalite zaten %100."})
	out.append({"id": "muhur", "ad": AD["muhur"], "aciklama": "Ucuz kumar: Kut mührü basılır; nakış, kalite, unsur ya da kusurun silinmesi gelebilir... bir kusur da gelebilir.",
		"fiyat": muhur_fiyat(it, d), "sans": -1.0, "uygun": true, "neden": ""})
	return out


static func secenekler(hid: String, slot: String, it: Dictionary, d := -1) -> Array:
	## Alt seçenekler (nakış adayları / unsur listesi): {ad, aciklama, fiyat, veri}
	var out: Array = []
	match hid:
		"nakis":
			for c in nakis_adaylari(slot, it, d):
				var df := ItemGen.affix_def(String(c["id"]))
				out.append({"ad": "%s%s" % [String(df.get("adj", c["id"])), " ★" if bool(c["nadir"]) else ""],
					"aciklama": String(df.get("desc", "")).replace("{v}", ItemGen.fmt(float(c["v"]))), "fiyat": int(c["fiyat"]), "veri": c})
		"unsur":
			out.append({"ad": "Rastgele unsur", "aciklama": "Usta közden hangisi çıkarsa onu aşılar.", "fiyat": unsur_fiyat(it, false, d), "veri": ""})
			for u in Unsur.IDS:
				var df: Dictionary = Unsur.DEF[u]
				out.append({"ad": "%s (%s)" % [String(df["ad"]), String(df["tur"])], "aciklama": "%s silah." % String(df["sifat"]), "fiyat": unsur_fiyat(it, true, d), "veri": u})
	return out


static func _kalite_ekle(it: Dictionary, puan: int) -> void:
	var q0 := int(it.get("quality", 50))
	var q1 := mini(100, q0 + puan)
	it["quality"] = q1
	it["dmg"] = float(it.get("dmg", 1.0)) * (1.0 + float(data().get("kalite", {}).get("hasar_puan", 0.003)) * float(q1 - q0))


static func _ad_yenile(it: Dictionary) -> void:
	it["name"] = ItemGen.item_name(it)


static func uygula(hid: String, slot: String, opt: Dictionary, d := -1) -> Dictionary:
	## Hizmeti uygula: altın düşer, kuşanılı silah yerinde değişir. {"ok", "msg", "once", "sonra", "fiyat", "iyi", "kotu", "damga"}
	var it: Dictionary = Game.run["slots"].get(slot, {})
	if it.is_empty() or String(it.get("cat", "")) != "weapons":
		return {"ok": false, "msg": "Bu yuvada silah yok."}
	var fiyat := 0
	var veri: Variant = opt.get("veri", null)
	match hid:
		"nakis":
			if nakis_sayi(it) >= max_nakis(it):
				return {"ok": false, "msg": "Nakış yeri kalmadı."}
			if veri == null or not (veri is Dictionary):
				return {"ok": false, "msg": "Bir nakış seç."}
			fiyat = int(veri["fiyat"])
		"dovme":
			if nakis_sayi(it) == 0:
				return {"ok": false, "msg": "Dövülecek nakış yok."}
			fiyat = dovme_fiyat(it, d)
		"unsur":
			if not unsur_olur(it):
				return {"ok": false, "msg": "Bu silah unsur taşımaz."}
			if not (veri is String):
				veri = ""
			fiyat = unsur_fiyat(it, String(veri) != "", d)
		"kalite":
			if int(it.get("quality", 50)) >= 100:
				return {"ok": false, "msg": "Kalite zaten %100."}
			fiyat = kalite_fiyat(it, d)
		"muhur":
			fiyat = muhur_fiyat(it, d)
		_:
			return {"ok": false, "msg": "Böyle bir hizmet yok."}
	var gold := int(Game.run.get("gold", 0))
	if gold < fiyat:
		return {"ok": false, "msg": "Altının yetmez (%d gerekir, %d var)." % [fiyat, gold], "fiyat": fiyat}
	Game.run["gold"] = gold - fiyat
	var once := it.duplicate(true)
	var res := {"ok": true, "msg": "", "once": once, "sonra": it, "fiyat": fiyat, "iyi": true, "kotu": false, "damga": "NAKIŞLANDI"}
	match hid:
		"nakis":
			var c: Dictionary = veri
			it["affixes"].append({"id": c["id"], "v": c["v"]})
			_ad_yenile(it)
			var df := ItemGen.affix_def(String(c["id"]))
			res["msg"] = "%s nakşı işlendi: %s" % [String(df.get("adj", c["id"])), String(df.get("desc", "")).replace("{v}", ItemGen.fmt(float(c["v"])))]
			res["damga"] = "NAKIŞLANDI"
			_adaylar.clear()   # yeni silah hâli: adaylar yeniden yuvarlanır
		"dovme":
			ItemGen.reroll_affixes(it, rng)
			it["usta_dovme"] = int(it.get("usta_dovme", 0)) + 1
			res["msg"] = "Nakışlar yeniden dövüldü (%d. dövme)." % int(it["usta_dovme"])
			res["damga"] = "DÖVÜLDÜ"
		"unsur":
			var u := String(veri)
			if u == "":
				var pool: Array = Unsur.IDS.duplicate()
				pool.erase(Unsur.of(it))
				u = String(pool[rng.randi_range(0, pool.size() - 1)])
			var rar := clampi(int(it.get("rarity", 0)), 0, 3)
			Unsur.apply(it, u, Unsur.POWER[rar] * rng.randf_range(0.92, 1.08))
			res["msg"] = "%s unsuru aşılandı: %s." % [String(Unsur.DEF[u]["ad"]), String(it["name"])]
			res["damga"] = "AŞILANDI"
		"kalite":
			var p := kalite_sansi(it)
			var ka: Array = data().get("kalite", {}).get("artis", [5, 15])
			if rng.randf() < p:
				var puan := rng.randi_range(int(ka[0]), int(ka[1]))
				_kalite_ekle(it, puan)
				res["msg"] = "Kalite tuttu: +%d puan (%%%d)." % [puan, int(it["quality"])]
				res["damga"] = "KALİTE +%d" % puan
			else:
				res["iyi"] = false
				res["msg"] = "Tutmadı: közden çıkan demir soğudu (şans %%%d)." % int(round(p * 100.0))
				res["damga"] = "TUTMADI"
		"muhur":
			_muhur(it, res)
	return res


static func _muhur(it: Dictionary, res: Dictionary) -> void:
	## Kut Mührü: ağırlıklı rastgele sonuç
	var m: Dictionary = data().get("muhur", {})
	var tbl: Dictionary = m.get("sonuclar", {})
	var keys: Array = tbl.keys()
	var tot := 0.0
	for k in keys:
		tot += float(tbl[k])
	var r := rng.randf() * tot
	var pick := String(keys[keys.size() - 1])
	for k in keys:
		r -= float(tbl[k])
		if r <= 0.0:
			pick = String(k)
			break
	# uygulanamayan sonuçlar bir sonrakine kayar
	if pick == "nakis" and (nakis_sayi(it) >= max_nakis(it) or nakis_havuzu(it).is_empty()):
		pick = "kalite"
	if pick == "unsur" and not unsur_olur(it):
		pick = "kalite"
	if pick == "kusur_sil" and String(it.get("flaw", "")) == "":
		pick = "kalite"
	if pick == "kusur" and String(it.get("flaw", "")) != "":
		pick = "hic"
	if pick == "kalite" and int(it.get("quality", 50)) >= 100:
		pick = "hic"
	res["damga"] = "MÜHÜRLENDİ"
	match pick:
		"nakis":
			var pool := nakis_havuzu(it)
			var a: Dictionary = pool[rng.randi_range(0, pool.size() - 1)]
			it["affixes"].append(ItemGen.roll_affix(a, rng))
			_ad_yenile(it)
			res["msg"] = "Mühür nakış getirdi: %s." % String(a.get("adj", a["id"]))
			_adaylar.clear()
		"kalite":
			var puan := int(m.get("kalite_artis", 8))
			_kalite_ekle(it, puan)
			res["msg"] = "Mühür demiri sıkılaştırdı: kalite +%d." % puan
		"unsur":
			var pool: Array = Unsur.IDS.duplicate()
			pool.erase(Unsur.of(it))
			var u := String(pool[rng.randi_range(0, pool.size() - 1)])
			Unsur.apply(it, u, Unsur.POWER[clampi(int(it.get("rarity", 0)), 0, 3)])
			res["msg"] = "Mühürden %s unsuru fışkırdı." % String(Unsur.DEF[u]["ad"])
		"kusur_sil":
			var fl := String(it["flaw"])
			it["flaw"] = ""
			var fn := fl
			for f in Data.items["flaws"]:
				if f["id"] == fl:
					fn = f["name"]
			res["msg"] = "Mühür kusuru sildi: %s artık yok." % fn
		"kusur":
			var fls: Array = Data.items["flaws"]
			var f: Dictionary = fls[rng.randi_range(0, fls.size() - 1)]
			it["flaw"] = f["id"]
			res["iyi"] = false
			res["kotu"] = true
			res["msg"] = "Erlik güldü: silah %s kusuru kaptı (%s)." % [String(f["name"]), String(f["desc"])]
			res["damga"] = "LANETLENDİ"
		_:
			res["iyi"] = false
			res["msg"] = "Mühür soğuk bastı: bir şey olmadı."
			res["damga"] = "SESSİZ"


static func bot_hizmet(slot: String, d := -1) -> Dictionary:
	## --otomatik: paranın yettiği ilk uygun hizmeti uygula (nakışta ilk aday, unsurda rastgele)
	var it: Dictionary = Game.run["slots"].get(slot, {})
	if it.is_empty():
		return {"ok": false, "msg": "silah yok"}
	for h in hizmetler(it, d):
		if not bool(h["uygun"]):
			continue
		var opt := {}
		if String(h["id"]) in ["nakis", "unsur"]:
			var secs := secenekler(String(h["id"]), slot, it, d)
			if secs.is_empty():
				continue
			opt = secs[0]
		if int(Game.run.get("gold", 0)) < int(opt.get("fiyat", h["fiyat"])):
			continue
		return uygula(String(h["id"]), slot, opt, d)
	return {"ok": false, "msg": "altın yetmez"}
