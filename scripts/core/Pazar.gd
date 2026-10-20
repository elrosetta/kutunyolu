class_name Pazar
extends RefCounted
## v24 Bezirgân Sartak'ın pazarı: mal (teklif) yuvarlama, fiyat, satın alma, malları yenileme ve altın tanesi değeri.
## v34: mallar oyuncunun donanımına göre (iyilesme): üst kademe + daha iyi nadirlik, aday seçimi, "Bezirgân'ın gözdesi".
## Bütün sayılar data/tuccar.json'da. Fiyat ve altın geliri aynı derinlik çarpanıyla büyür (derinlik_k), böylece her
## derinlikte "biriktirirsen 1-2 iyi mal" dengesi korunur. Ölçüm: -- --tuccar (tools/tests/tuccar_testi.gd).

const PATH := "res://data/tuccar.json"
static var _d: Dictionary = {}


static func data() -> Dictionary:
	if _d.is_empty():
		var f := FileAccess.open(PATH, FileAccess.READ)
		if f:
			var v: Variant = JSON.parse_string(f.get_as_text())
			if v is Dictionary:
				_d = v
	return _d


static func derinlik() -> int:
	return 1 if Game.run.is_empty() else maxi(1, int(Game.run.get("depth", 1)))


static func derinlik_k(d := -1) -> float:
	## Fiyat çarpanı: 1 + artış x (derinlik - 1)
	var dd := derinlik() if d < 1 else d
	return 1.0 + float(data().get("derinlik_artis", 0.3)) * float(dd - 1)


static func altin_k(d := -1) -> float:
	var dd := derinlik() if d < 1 else d
	return 1.0 + float(data().get("altin", {}).get("artis", 0.3)) * float(dd - 1)


static func altin_tane() -> int:
	## Bir altın tanesinin değeri: 1-3 x altin_k (derinlikle büyür; v23'te hep 1-3)
	var t: Array = data().get("altin", {}).get("tane", [1, 3])
	return maxi(1, int(round(float(randi_range(int(t[0]), int(t[1]))) * altin_k())))


static func esya_fiyat(it: Dictionary, d := -1, ust := false) -> int:
	## Eşya fiyatı: taban[kategori] x nadirlik x kalite (0,85-1,15) x unsur x kusur x derinlik_k (x üst kademe)
	var D := data()
	var f := float(D.get("taban", {}).get(String(it.get("cat", "weapons")), 60))
	var nd: Array = D.get("nadirlik", [1.0])
	f *= float(nd[clampi(int(it.get("rarity", 0)), 0, nd.size() - 1)])
	f *= 0.85 + 0.3 * clampf(float(it.get("quality", 50)) / 100.0, 0.0, 1.0)
	if Unsur.of(it) != "":
		f *= float(D.get("unsur", 1.25))
	if String(it.get("flaw", "")) != "":
		f *= float(D.get("kusur", 0.8))
	if ust:
		f *= float(D.get("ust_kademe", 1.35))
	f *= derinlik_k(d)
	return maxi(5, int(round(f / 5.0)) * 5)


static func sifa_fiyat(d := -1) -> int:
	return int(round(float(data().get("sifa", {}).get("fiyat", 34)) * derinlik_k(d)))


static func tomar_fiyat(d := -1) -> int:
	return int(round(float(data().get("tomar", {}).get("fiyat", 230)) * derinlik_k(d) / 5.0)) * 5


static func _pz() -> Dictionary:
	return data().get("pazar", {})


static func yuva(it: Dictionary) -> String:
	## Malın kuşanılacağı doğal yuva (Level.natural_slot ile aynı)
	if String(it.get("cat", "")) == "gadgets":
		return "g1"
	return "second" if Player.is_second_item(it) else "melee"


static func guc(it: Dictionary) -> float:
	## Karşılaştırma ölçüsü: silahta oyuncunun SnH'si (ItemGen.dps_oyuncu), teçhizatta güç, kalkanda blok x kademe x
	## nadirlik; ek özellik başına +%10 (silahta SnH zaten içerir)
	if it.is_empty():
		return 0.0
	var ek := 1.0 + 0.1 * (it.get("affixes", []) as Array).size()
	match String(it.get("cat", "")):
		"weapons":
			return ItemGen.dps_oyuncu(it)
		"gadgets":
			return float(it.get("power", 0.0)) * ek
		"shields":
			return float(it.get("block", 0.5)) * Zorluk.esya_k(int(it.get("tier", 0))) * Zorluk.nadirlik_k(int(it.get("rarity", 0))) * ek
	return 0.0


static func iyilesme(it: Dictionary) -> float:
	## v34: mal, oyuncunun aynı yuvadaki eşyasına göre ne kadar güçlü (oran; 1,1 = %10 iyi). Yuva boşsa 2; kıyaslanamazsa
	## (ikinci yuvada yay varken kalkan) 0. Teçhizat iki yuvanın zayıfıyla kıyaslanır.
	if Game.run.is_empty() or it.is_empty():
		return 0.0
	var sl: Dictionary = Game.run.get("slots", {})
	match String(it.get("cat", "")):
		"weapons":
			var cur: Dictionary = sl.get(yuva(it), {})
			if cur.is_empty():
				return 2.0
			if String(cur.get("cat", "")) != "weapons":
				return 0.0
			return guc(it) / maxf(0.01, guc(cur))
		"shields":
			var sh: Dictionary = sl.get("second", {})
			if sh.is_empty():
				return 2.0
			if String(sh.get("cat", "")) != "shields":
				return 0.0
			return guc(it) / maxf(0.01, guc(sh))
		"gadgets":
			var lo := minf(guc(sl.get("g1", {})), guc(sl.get("g2", {})))
			return 2.0 if lo <= 0.0 else guc(it) / lo
	return 0.0


static func _aday(kt: int, nt: int, cat: String, n: int) -> Dictionary:
	## Sartak'ın ayırdığı mal: n aday arasından oyuncuya en iyi gelen (iyilesme); kıyaslanamayanlar arasında en güçlü
	var best := {}
	var bv := -1.0
	for i in maxi(1, n):
		var it := ItemGen.tuccar_drop(kt, nt, cat)
		var v := iyilesme(it)
		if v <= 0.0:
			v = 0.5 + 0.001 * guc(it)
		if v > bv:
			bv = v
			best = it
	return best


static func gozde_sec(kt: int, nt: int) -> Dictionary:
	## "Bezirgân'ın gözdesi": oyuncunun kuşandığı silahtan açıkça iyi (oran >= esik) bir silah; "deneme" aday aranır
	## (adayların ikinci üçte biri bir, son üçte biri iki kademe ve nadirlik sütunu üstten); bulunamazsa en iyi aday
	## bilenir (hasarı eşiğe dek artar, "bilendi"): ziyaret başına en az bir iyileşme kesin
	var G: Dictionary = _pz().get("gozde", {})
	var esik := float(G.get("esik", 1.15))
	var n := int(G.get("deneme", 40))
	var best := {}
	var bv := -1.0
	for i in n:
		var ust := (i * 3) / maxi(1, n)
		var it := ItemGen.tuccar_drop(mini(8, kt + ust), mini(8, nt + ust), "weapons")
		var v := iyilesme(it)
		if v >= esik:
			return it
		if v > bv:
			bv = v
			best = it
	# hiçbiri yetmedi (oyuncunun silahı çok iyi): Sartak en iyi adayı biler (hasar eşiğe dek, en çok x"bileme")
	if not best.is_empty() and bv > 0.0 and bv < esik and String(best.get("cat", "")) == "weapons":
		var k := minf(esik / bv, float(G.get("bileme", 1.35)))
		best["dmg"] = float(best["dmg"]) * k
		best["bilendi"] = true
	return best


static func teklifler(d := -1, tomar_kesin := false) -> Array:
	## v34 (Dead Cells esinli): mallar o derinliğin kademesinin üstünden (data "pazar.kademe") ve daha iyi nadirlik
	## zarıyla ("pazar.nadirlik" sütun ileri) yuvarlanır; Sartak her mal için birkaç aday arasından oyuncunun aynı
	## yuvasındaki eşyasına göre en iyisini tezgâha koyar ("pazar.aday"). Mallar:
	##   1. Bezirgân'ın gözdesi: kuşanılandan açıkça iyi bir silah (kesin iyileşme), indirimli ("gozde.indirim"),
	##   2. bir silah, 3. rastgele bir eşya (silah / kalkan / teçhizat), 4. "seçme" mal (bir kademe daha üstten, pahalı),
	##   5. Umay Sütü, 6. şansla (boss öncesinde kesin) Kut Tomarı.
	var dd := derinlik() if d < 1 else d
	var tier := Zorluk.kademe(dd)
	var P := _pz()
	var kt := mini(8, tier + int(P.get("kademe", 1)))
	var nt := mini(8, tier + int(P.get("nadirlik", 2)))
	var n_aday := int(P.get("aday", 2))
	var out: Array = []
	var gz := gozde_sec(kt, nt)
	var gzf := maxi(5, int(round(float(esya_fiyat(gz, dd)) * float(P.get("gozde", {}).get("indirim", 0.85)) / 5.0)) * 5)
	out.append({"tur": "esya", "item": gz, "fiyat": gzf, "satildi": false, "gozde": true})
	var w := _aday(kt, nt, "weapons", n_aday)
	out.append({"tur": "esya", "item": w, "fiyat": esya_fiyat(w, dd), "satildi": false})
	var it2 := _aday(kt, nt, "", n_aday)
	out.append({"tur": "esya", "item": it2, "fiyat": esya_fiyat(it2, dd), "satildi": false})
	var it3 := _aday(mini(8, kt + 1), mini(8, nt + 1), "", n_aday)
	out.append({"tur": "esya", "item": it3, "fiyat": esya_fiyat(it3, dd, true), "satildi": false, "ust": true})
	out.append({"tur": "sifa", "item": {}, "fiyat": sifa_fiyat(dd), "satildi": false})
	if tomar_kesin or randf() < float(data().get("tomar", {}).get("sans", 0.35)):
		out.append({"tur": "tomar", "item": {}, "fiyat": tomar_fiyat(dd), "satildi": false})
	return out


static func gozde_tazele(bz: Node) -> void:
	## v34: pazar açılınca (mallar bölüm kurulurken yuvarlandı; oyuncu arada eşya almış olabilir) satılmamış gözde mal
	## artık açık iyileşme değilse oyuncunun şimdiki donanımına göre yeniden seçilir
	var G: Dictionary = _pz().get("gozde", {})
	for i in (bz.offers as Array).size():
		var o: Dictionary = bz.offers[i]
		if not bool(o.get("gozde", false)) or bool(o.get("satildi", false)):
			continue
		if iyilesme(o["item"]) >= float(G.get("esik", 1.15)) * 0.97:
			return
		var dd := derinlik()
		var tier := Zorluk.kademe(dd)
		var P := _pz()
		var gz := gozde_sec(mini(8, tier + int(P.get("kademe", 1))), mini(8, tier + int(P.get("nadirlik", 2))))
		o["item"] = gz
		o["fiyat"] = maxi(5, int(round(float(esya_fiyat(gz, dd)) * float(G.get("indirim", 0.85)) / 5.0)) * 5)
		return


static func yenile_fiyat(n_yenileme: int, d := -1) -> int:
	## Malları yenileme: her yenilemede pahalanır (+%60)
	var y: Dictionary = data().get("yenile", {})
	return int(round(float(y.get("fiyat", 14)) * derinlik_k(d) * (1.0 + float(y.get("artis", 0.6)) * float(n_yenileme))))


static func ad(o: Dictionary) -> String:
	match String(o.get("tur", "")):
		"sifa":
			return String(data().get("sifa", {}).get("ad", "Umay Sütü"))
		"tomar":
			return String(data().get("tomar", {}).get("ad", "Kut Tomarı"))
	return String(o.get("item", {}).get("name", "?"))


static func aciklama(o: Dictionary) -> String:
	match String(o.get("tur", "")):
		"sifa":
			return "Bir şifa şişesini doldurur. Şişelerin doluysa canının %%%d'ını hemen yeniler." % int(round(float(data().get("sifa", {}).get("can", 0.4)) * 100.0))
		"tomar":
			return "Bir stat seç (Bozkurt / Kartal / Ayı): o renkteki eşyaların hasarı ve azami can artar. Kilime bırakılır, W ile oku."
	return ""


static func satin_al(level: Node, bz: Node, i: int) -> Dictionary:
	## Malı al: altın düşer, mal SATILDI olur; eşya / tomar tüccarın kilimine, oyuncunun önüne bırakılır (W ile alınır,
	## iki yuva doluysa yuva seçimi). Şifa hemen etkir. {"ok": bool, "msg": String, "pickup": Pickup|null}
	var offers: Array = bz.offers
	if i < 0 or i >= offers.size():
		return {"ok": false, "msg": ""}
	var o: Dictionary = offers[i]
	if bool(o.get("satildi", false)):
		return {"ok": false, "msg": "Bu mal satıldı."}
	var fiyat := int(o["fiyat"])
	var gold := int(Game.run.get("gold", 0))
	if gold < fiyat:
		return {"ok": false, "msg": "Altının yetmez (%d gerekir, %d var)." % [fiyat, gold]}
	Game.run["gold"] = gold - fiyat
	o["satildi"] = true
	var pl: Node = level.player
	var at: Vector2 = (pl.global_position if pl else bz.global_position) + Vector2(0, -14)
	var res := {"ok": true, "msg": "", "pickup": null}
	match String(o["tur"]):
		"esya":
			level.drop_item(o["item"], at)
			res["pickup"] = level.pickups[level.pickups.size() - 1]
			res["msg"] = "%s alındı: kilimde, %s ile al." % [String(o["item"].get("name_base", "")), HUD.KEY_ETKILES]
		"tomar":
			level.drop_scroll(Vector2(at.x, at.y + 14))
			res["pickup"] = level.pickups[level.pickups.size() - 1]
			res["msg"] = "Kut Tomarı alındı: kilimde, %s ile oku." % HUD.KEY_ETKILES
		"sifa":
			if int(Game.run["flasks"]) < int(Game.run["max_flasks"]):
				Game.run["flasks"] = int(Game.run["flasks"]) + 1
				res["msg"] = "Umay Sütü: bir şişe doldu (%d / %d)." % [int(Game.run["flasks"]), int(Game.run["max_flasks"])]
			else:
				var h := float(Game.run["max_hp"]) * float(data().get("sifa", {}).get("can", 0.4))
				if pl and pl.has_method("heal"):
					pl.heal(h)
				else:
					Game.run["hp"] = minf(float(Game.run["max_hp"]), float(Game.run["hp"]) + h)
				res["msg"] = "Umay Sütü: can +%d." % int(round(h))
	bz.sold += 1
	return res


static func yenile(bz: Node) -> Dictionary:
	var c := yenile_fiyat(int(bz.rerolls))
	var gold := int(Game.run.get("gold", 0))
	if gold < c:
		return {"ok": false, "msg": "Yenilemeye altının yetmez (%d gerekir)." % c}
	Game.run["gold"] = gold - c
	bz.rerolls = int(bz.rerolls) + 1
	var had_tomar := false
	for o in bz.offers:
		had_tomar = had_tomar or (String(o["tur"]) == "tomar" and not bool(o["satildi"]))
	bz.offers = teklifler(-1, had_tomar)
	return {"ok": true, "msg": "Sartak denklerini çözdü: yeni mallar."}
