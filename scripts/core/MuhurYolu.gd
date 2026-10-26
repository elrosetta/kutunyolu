class_name MuhurYolu
extends RefCounted
## v44 Mühür yolu (yeni oyun+ / NG+; Dead Cells "Boss Cell", Hades "Heat", Slay the Spire "Ascension" karşılığı).
##
## Tan söktükten sonra Erlik ölmez: her gece yeniden gelir. Erlik'i bir mühürde her yenişte zincirinden bir halka kalır;
## Umay o halkayı Ulu Kayın'ın dibindeki Mühür Taşı'na (MuhurTasi.gd, yurtta Kut Kapısı'nın yanı) bir Kut Mührü olarak
## basar ve bir sonraki mühür açılır (Zorluk.on_final_boss). Mühür koşu başında taştan seçilir (MuhurUI.gd).
##
## Her mühür sayıların (data/zorluk.json "muhurler": can / hasar / şişe...) üstüne bir KURAL ekler; kurallar birikir:
##   I   Kısa Uyarı      hazırlık %10 kısa (Zorluk.hazirlik)
##   II  Erlik Damgası   her seçkin bir damga taşır: Öfkeli / Kalkanlı / Bölünen (MuhurDamga.gd)
##   III Erlik'in Sisi   Kut Taşlarının yarısı söner, harita sisi dar (Level._kut_taslari, Harita)
##   IV  Tamu Bekçileri  Tamu dışı bölümlerde kor saçan, ölünce patlayan bekçiler; seçkinlerde iki damga
##   V   Zincir Evresi   bosslar canının %40'ında Erlik'in zincirini çağırır (MuhurEvre.gd)
## Ödüller ("muhur_odul"): Kut / altın çarpanı, nadirlik zarı ve tabanı, Han Otağı'na tomar / emanet, ilk zaferde Kut,
## mühür başına bir EMANET (yalnızca o mühürde ve üstünde düşen Efsanevi silah), Bengü'ye örgü süsü (o mühürde zafer),
## en üst mühürde gerçek son (data/sinema/gercek_son.json).
##
## Kalıcı kayıt (Game.meta; meta_hazirla göçü): muhur_kayit {"0".."5": {deneme, zafer, en_iyi (sn), en_derin}} (başka
## ekranlar okuyabilir: kayit(n)), muhur_emanet [id] (açılan), muhur_emanet_bulunan [id], muhur_sus (-1 kendiliğinden),
## gercek_son (bool), muhur_toren (taşta oynayacak yeni mühür, -1 yok), muhur_surum.

const SURUM := 44
const EN_COK := 5
const ROMA := ["0", "I", "II", "III", "IV", "V"]
## Mühür renkleri: beş mühür Gün Ana'nın beş örgüsünün rengini taşır (al, ak, gök, sarı, altın; SinemaEfekt.ORGU_RENK)
const RENK := [Color(0.62, 0.6, 0.66), Color(0.93, 0.27, 0.2), Color(0.96, 0.94, 0.88), Color(0.33, 0.62, 0.95), Color(0.98, 0.84, 0.28), Color(1.0, 0.68, 0.22)]
const SUS_AD := ["Gümüş şolpı", "Al şolpı", "Ak şolpı", "Gök şolpı", "Sarı şolpı", "Tan tamgası"]
const DAMGA_TUR := ["ofkeli", "kalkanli", "bolunen"]
const DAMGA_AD := {"ofkeli": "Öfkeli", "kalkanli": "Kalkanlı", "bolunen": "Bölünen", "tamu": "Tamu Bekçisi"}

static var _yavru := false        # Bölünen'in yavruları doğarken damga / bekçi verilmez
static var test_tamu_zorla := false   # test: ilk uygun yaratık bekçi olsun


# ------------------------------------------------------------------ kayıt göçü
static func meta_hazirla() -> void:
	var m: Dictionary = Game.meta
	var k: Dictionary = m.get("muhur_kayit", {}) if m.get("muhur_kayit") is Dictionary else {}
	for n in EN_COK + 1:
		var s := str(n)
		var r: Dictionary = k.get(s, {}) if k.get(s) is Dictionary else {}
		k[s] = {"deneme": int(r.get("deneme", 0)), "zafer": int(r.get("zafer", 0)), "en_iyi": float(r.get("en_iyi", 0.0)), "en_derin": int(r.get("en_derin", 0))}
	m["muhur_kayit"] = k
	for key in ["muhur_emanet", "muhur_emanet_bulunan"]:
		if not (m.get(key) is Array):
			m[key] = []
	m["muhur_sus"] = int(m.get("muhur_sus", -1))
	m["gercek_son"] = bool(m.get("gercek_son", false))
	m["muhur_toren"] = int(m.get("muhur_toren", -1))
	if int(m.get("muhur_surum", 0)) < SURUM:
		# v44 öncesi kayıt: açılmış mühürlerin altındaki her mühür en az bir kez yenilmiştir (on_final_boss ancak açılan en
		# yüksek mühürde açar); emanetleri açılmış mühürlere göre verilir
		var acik := clampi(int(m.get("muhur_acik", 0)), 0, EN_COK)
		for n in acik:
			var r2: Dictionary = k[str(n)]
			r2["zafer"] = maxi(1, int(r2["zafer"]))
		if acik == 0 and int(m.get("wins", 0)) > 0:
			k["0"]["zafer"] = maxi(int(k["0"]["zafer"]), int(m.get("wins", 0)))
		for n in range(1, acik + 1):
			var em := String(odul(n).get("emanet", ""))
			if em != "" and not (em in m["muhur_emanet"]):
				(m["muhur_emanet"] as Array).append(em)
	m["muhur_surum"] = SURUM


# ------------------------------------------------------------------ veri
static func _liste(bolum: String) -> Array:
	return Zorluk.data().get(bolum, {}).get("liste", [])


static func kural(n := -1) -> Dictionary:
	var a := _liste("muhur_kural")
	if a.is_empty():
		return {}
	return a[clampi(Zorluk.muhur() if n < 0 else n, 0, a.size() - 1)]


static func odul(n := -1) -> Dictionary:
	var a := _liste("muhur_odul")
	if a.is_empty():
		return {}
	return a[clampi(Zorluk.muhur() if n < 0 else n, 0, a.size() - 1)]


static func _k(key: String, def: float) -> float:
	return float(kural().get(key, def))


static func _o(key: String, def: float) -> float:
	return float(odul().get(key, def))


static func damga_def(id: String) -> Dictionary:
	return Zorluk.data().get("damgalar", {}).get(id, {})


static func emanet_def(id: String) -> Dictionary:
	var d: Variant = Zorluk.data().get("emanetler", {}).get(id, {})
	return d if d is Dictionary else {}


static func renk(n: int) -> Color:
	return RENK[clampi(n, 0, RENK.size() - 1)]


static func ad(n: int) -> String:
	return Zorluk.muhur_adi(n)


static func kural_ad(n: int) -> String:
	return String(kural(n).get("ad", ""))


# ------------------------------------------------------------------ kurallar (kancalar)
static func hazirlik_k() -> float:
	## Zorluk.hazirlik çarpanı (I: Kısa Uyarı)
	return _k("hazirlik", 1.0)


static func damga_sayi() -> int:
	return int(_k("damga", 0.0))


static func sis_k() -> float:
	## Harita görüş yarıçapı çarpanı (III: Erlik'in Sisi)
	return _k("sis", 1.0)


static func tasi_yanar(i: int, rol: String) -> bool:
	## III: Kut Taşlarının bir kısmı söner (giriş ve çıkış taşı hep yanar). i: taşın üretici sırası
	var pay := _k("tasi", 1.0)
	if pay >= 1.0 or rol == "giris" or rol == "cikis":
		return true
	# pay 0,5: her iki taştan biri (sıraya göre, tohum gerektirmez; bölüm üretimi değişmez)
	var adim := maxi(2, int(round(1.0 / maxf(0.05, 1.0 - pay))))
	return i % adim != 1


static func tamu_sayi() -> int:
	## IV: Tamu dışı bölümde en çok kaç Tamu bekçisi
	if String(Game.run.get("biome", "")) == "tamu":
		return 0
	return int(_k("tamu", 0.0))


static func evre_k() -> float:
	return _k("evre", 0.0)


static func dogdu(lv: Node, e: Node) -> void:
	## Level.spawn_enemy kancası: seçkine Erlik damgası, sıradan yaratığı (IV) Tamu bekçisine çevirme, bossa evre
	if lv == null or e == null or not is_instance_valid(e) or Zorluk.muhur() <= 0 or _yavru:
		return
	if bool(lv.get("hub")) or bool(lv.get("konak")):
		return
	if bool(e.get("is_boss")):
		boss_kur(lv, e)
		return
	if bool(e.get("decoy")):
		return
	if bool(e.get("elite")):
		var n := damga_sayi()
		if n > 0:
			var havuz: Array = DAMGA_TUR.duplicate()
			havuz.shuffle()
			MuhurDamga.ekle(e, havuz.slice(0, mini(n, havuz.size())))
		return
	var ts := tamu_sayi()
	if ts <= 0 or bool(e.get("flying")) or bool(e.get("ofkeli")):
		return
	var sayi := int(lv.get_meta("muhur_tamu", 0))
	if sayi >= ts:
		return
	if test_tamu_zorla or randf() < _k("tamu_sans", 0.15):
		lv.set_meta("muhur_tamu", sayi + 1)
		MuhurDamga.ekle(e, ["tamu"])


static func boss_kur(lv: Node, b: Node) -> void:
	## V: Zincir evresi (Level.build_boss ve spawn_enemy kancası)
	if b == null or b.has_meta("muhur_evre") or evre_k() <= 0.0:
		return
	MuhurEvre.kur(lv, b, evre_k())


# ------------------------------------------------------------------ ödüller
static func kut_k(n := -1) -> float:
	return float(odul(n).get("kut", 1.0))


static func altin_k(n := -1) -> float:
	return float(odul(n).get("altin", 1.0))


static func kut_tane() -> int:
	## Toplanan Kut tanesinin değeri: çarpanın kesirli kısmı olasılıkla (ortalama = çarpan)
	var k := kut_k()
	var n := int(floor(k))
	return n + (1 if randf() < k - float(n) else 0)


static func altin(gv: int) -> int:
	return int(round(float(gv) * altin_k()))


static func nadirlik_zar(tier: int, taban := 0) -> int:
	## Düşen eşyanın nadirliği: mühürsüzde -1 (ItemGen kendi zarını atar); mühürde zar "nadir" sütun ileri, en az
	## max(nadir_taban, taban)
	var tb := maxi(int(_o("nadir_taban", 0.0)), taban)
	if Zorluk.muhur() <= 0 and tb <= 0:
		return -1
	var rars: Array = Data.items["rarities"]
	var col := clampi(tier + int(_o("nadir", 0.0)), 0, 8)
	var ws: Array = []
	for i in rars.size():
		ws.append(0.0 if i < tb else ItemGen._w_at(rars[i]["weight"], col))
	return rars.find(ItemGen._wpick(rars, ws))


static func kademe_ek() -> int:
	return int(_o("kademe", 0.0))


static func seckin_taban() -> int:
	return int(_o("seckin_taban", 0.0))


static func seckin_esya(tier: int) -> Dictionary:
	## Seçkin düşüşü: mührün seçkin nadirlik tabanı (II+: en az Nadir, IV+: en az Destansı)
	var it := ItemGen.random_drop(tier)
	var tb := maxi(seckin_taban(), int(_o("nadir_taban", 0.0)))
	if int(it.get("rarity", 0)) < tb:
		it = ItemGen.roll(String(it["id"]), int(it.get("tier", tier)), "", tb)
	return it


static func boss_esya(tier: int) -> Dictionary:
	## Boss düşüşü: açılmış emanet varsa koşunun ilk bekçisinden kesin, sonra %25; yoksa nadirlik tabanlı düşüş
	var havuz := emanet_havuz()
	if not havuz.is_empty() and (not bool(Game.run.get("emanet_dustu", false)) or randf() < 0.25):
		Game.run["emanet_dustu"] = true
		return emanet_yuvarla(_emanet_sec(havuz), tier)
	var it := ItemGen.random_drop(tier)
	var tb := maxi(int(_o("boss_taban", 0.0)), int(_o("nadir_taban", 0.0)))
	if int(it.get("rarity", 0)) < tb:
		it = ItemGen.roll(String(it["id"]), tier, "", tb)
	return it


static func han_odul(o: Dictionary, tier: int, rng: RandomNumberGenerator) -> void:
	## Sinav.odul "han" kancası: ek tomar, Kut çarpanı, emanet olasılığı
	if Zorluk.muhur() <= 0:
		return
	o["kut"] = int(round(float(o.get("kut", 0)) * kut_k()))
	o["tomar"] = int(o.get("tomar", 0)) + int(_o("han_tomar", 0.0))
	var havuz := emanet_havuz()
	if not havuz.is_empty() and rng.randf() < _o("han_emanet", 0.0) and not (o.get("items", []) as Array).is_empty():
		o["items"][0] = emanet_yuvarla(_emanet_sec(havuz), tier + 1)


# ------------------------------------------------------------------ emanetler
static func emanet_acik() -> Array:
	return Game.meta.get("muhur_emanet", []) if Game.meta.get("muhur_emanet") is Array else []


static func emanet_havuz(n := -1) -> Array:
	## Bu mühürde düşebilecek emanetler: açılmış ve mührü <= koşunun mührü
	var m := Zorluk.muhur() if n < 0 else n
	var out: Array = []
	for id in emanet_acik():
		var d := emanet_def(String(id))
		if not d.is_empty() and int(d.get("muhur", 9)) <= m:
			out.append(String(id))
	return out


static func _emanet_sec(havuz: Array) -> String:
	## Önce henüz bulunmamış emanetler, sonra en yüksek mühürlü olana eğilimli
	var bul: Array = Game.meta.get("muhur_emanet_bulunan", [])
	var yeni := havuz.filter(func(x: Variant) -> bool: return not (x in bul))
	if not yeni.is_empty():
		return String(yeni[randi() % yeni.size()])
	return String(havuz[randi() % havuz.size()])


static func emanet_yuvarla(id: String, tier: int) -> Dictionary:
	## Emanet: taban silahın Efsanevi çeşitlemesi (malzeme, unsur, ek özellikler, ad sabit)
	var d := emanet_def(id)
	if d.is_empty():
		return ItemGen.random_drop(tier)
	var it := ItemGen.roll(String(d["esya"]), clampi(tier + kademe_ek(), 0, 8), String(d.get("malzeme", "demir")), 3, "")
	if it.is_empty():
		return ItemGen.random_drop(tier)
	var ek: Array = []
	for a in d.get("ek", []):
		ek.append({"id": String(a[0]), "v": float(a[1])})
	it["affixes"] = ek
	it["quality"] = 100
	it["emanet"] = id
	it["emanet_ad"] = String(d.get("ad", id))
	it["epithet"] = ""
	if String(d.get("unsur", "")) != "":
		Unsur.apply(it, String(d["unsur"]), 1.4)
	it["name"] = ItemGen.item_name(it)
	return it


static func emanet_bulundu(it: Dictionary) -> void:
	## Emanet eline geçti (Pickup alındı): kalıcı "bulunan" listesi
	var id := String(it.get("emanet", ""))
	if id == "":
		return
	var b: Array = Game.meta.get("muhur_emanet_bulunan", [])
	if not (id in b):
		b.append(id)
		Game.meta["muhur_emanet_bulunan"] = b
		Game.save_meta()


static func emanet_satir(it: Dictionary) -> String:
	var d := emanet_def(String(it.get("emanet", "")))
	return "◆ %s emaneti: %s" % [ad(int(d.get("muhur", 1))), String(d.get("soz", ""))]


# ------------------------------------------------------------------ ilerleme ve kayıtlar
static func kayit(n: int) -> Dictionary:
	## Mühür n'nin kaydı: {deneme, zafer, en_iyi (sn, 0: yok), en_derin}; ekranlar (kayıtlar, başarımlar) okuyabilir
	var k: Dictionary = Game.meta.get("muhur_kayit", {}) if Game.meta.get("muhur_kayit") is Dictionary else {}
	var r: Variant = k.get(str(clampi(n, 0, EN_COK)), {})
	return r if r is Dictionary else {}


static func _kayit_yaz(n: int, r: Dictionary) -> void:
	var k: Dictionary = Game.meta.get("muhur_kayit", {}) if Game.meta.get("muhur_kayit") is Dictionary else {}
	k[str(clampi(n, 0, EN_COK))] = r
	Game.meta["muhur_kayit"] = k


static func zafer_var(n: int) -> bool:
	return int(kayit(n).get("zafer", 0)) > 0


static func en_yuksek_zafer() -> int:
	var en := -1
	for n in EN_COK + 1:
		if zafer_var(n):
			en = n
	return en


static func sec(n: int) -> void:
	## Taştan mühür seçildi (açılmışlar arasında); yurttaysa bu koşuya hemen uygulanır (şişe sayısı)
	Game.meta["muhur"] = clampi(n, 0, Zorluk.muhur_acik())
	Game.save_meta()
	if not Game.run.is_empty() and int(Game.run.get("depth", 1)) == 1 and String(Game.run.get("biome", "")) == "yurt":
		_uygula(Zorluk.muhur_secili())


static func _uygula(n: int) -> void:
	Game.run["muhur"] = n
	var fl := maxi(1, 2 + Game.umay_level("sise") + int(Zorluk.muhur_def(n).get("sise", 0)))
	Game.run["max_flasks"] = fl
	Game.run["flasks"] = fl


static func kosu_basla() -> void:
	## Yurttan Kut Kapısı'na girildi: koşunun mührü kesinleşir, deneme sayılır (Main._on_finished)
	_uygula(Zorluk.muhur_secili())
	var n := Zorluk.muhur()
	var r := kayit(n)
	r["deneme"] = int(r.get("deneme", 0)) + 1
	_kayit_yaz(n, r)
	Game.save_meta()


static func olum() -> void:
	## Koşu bitti (ölüm): bu mührün en derin kaydı
	if Game.run.is_empty():
		return
	var n := Zorluk.muhur()
	var r := kayit(n)
	r["en_derin"] = maxi(int(r.get("en_derin", 0)), int(Game.run.get("depth", 1)))
	_kayit_yaz(n, r)
	Game.save_meta()


static func zafer(lv: Node, e: Node) -> void:
	## Erlik Han devrildi (Level._on_boss_died): zafer kaydı, rekor süre, ilk zafer Kut'u, sonraki mührün açılışı,
	## emanet, gerçek son. Koşuya yazılanları Main._zafer okur (tören, özet ekranı).
	var n := Zorluk.muhur()
	var r := kayit(n)
	var ilk := int(r.get("zafer", 0)) == 0
	var sure := float(Game.run.get("time", 0.0))
	var eski := float(r.get("en_iyi", 0.0))
	r["zafer"] = int(r.get("zafer", 0)) + 1
	r["en_derin"] = maxi(int(r.get("en_derin", 0)), int(Game.run.get("depth", 1)))
	var rekor := sure > 0.0 and (eski <= 0.0 or sure < eski)
	if rekor:
		r["en_iyi"] = sure
	_kayit_yaz(n, r)
	Game.run["zafer"] = true
	Game.run["zafer_rekor"] = rekor and eski > 0.0
	Game.run["zafer_eski"] = eski
	Game.run["muhur_yeni"] = -1
	var kut := int(odul(n).get("ilk_zafer", 0)) if ilk else 0
	if kut > 0:
		Game.meta["kut_bank"] = int(Game.meta.get("kut_bank", 0)) + kut
	Game.run["ilk_zafer_kut"] = kut
	Game.run["zafer_ilk"] = ilk
	if Zorluk.on_final_boss():
		var yeni := Zorluk.muhur_acik()
		Game.run["muhur_yeni"] = yeni
		Game.meta["muhur_toren"] = yeni
		var em := String(odul(yeni).get("emanet", ""))
		var ac: Array = emanet_acik()
		if em != "" and not (em in ac):
			ac.append(em)
			Game.meta["muhur_emanet"] = ac
		Game.run["yeni_emanet"] = em
	if n >= EN_COK and not bool(Game.meta.get("gercek_son", false)):
		Game.run["gercek_son_bekliyor"] = true
	Game.save_meta()
	if lv != null and e != null and e.has_method("center"):
		var c: Vector2 = e.center()
		var y0: float = -float(e.size.y) - 66.0
		if int(Game.run["muhur_yeni"]) > 0:
			FX.text(c + Vector2(0, y0), "ZİNCİRDEN BİR HALKA: %s" % Sinema.buyuk(ad(int(Game.run["muhur_yeni"]))), renk(int(Game.run["muhur_yeni"])), 12)
		elif rekor:
			FX.text(c + Vector2(0, y0), "YENİ REKOR · %s" % sure_yazi(sure), Color(1.0, 0.85, 0.5), 12)


static func sure_yazi(s: float) -> String:
	if s <= 0.0:
		return "—"
	return "%d:%02d" % [int(s) / 60, int(s) % 60]


static func toren_degisken(n: int) -> Dictionary:
	## data/sinema/muhur_toren.json yer tutucuları
	var c := renk(n)
	var dolu: Array = []
	for i in range(1, n):
		dolu.append(i - 1)
	var em := emanet_def(String(odul(n).get("emanet", "")))
	return {"ad": Sinema.buyuk(ad(n)), "roma": ROMA[clampi(n, 0, EN_COK)], "kural": "%s — %s" % [kural_ad(n), String(kural(n).get("desc", ""))],
		"soz": umay_sozu(n), "renk": [c.r, c.g, c.b], "sira": n - 1, "dolu": dolu, "hx": 1280.0 + float(n - 3) * 150.0,
		"emanet": ("Emanet açıldı: %s" % String(em.get("ad", ""))) if not em.is_empty() else ""}


static func umay_sozu(n: int) -> String:
	var a: Array = Data.story.get("muhur_yolu", {}).get("toren", [])
	return "" if a.is_empty() else String(a[clampi(n - 1, 0, a.size() - 1)])


static func satir(k: String, salt := 0) -> String:
	## data/story.json "muhur_yolu.<k>" dizisinden bir satır
	var a: Variant = Data.story.get("muhur_yolu", {}).get(k, [])
	if a is Array and not (a as Array).is_empty():
		return String(a[posmod(salt, a.size())])
	return String(a) if a is String else ""


# ------------------------------------------------------------------ Bengü'nün örgü süsü
static func sus_acik(n: int) -> bool:
	## Süs n: o mühürde Erlik yenildi (0: gümüş şolpı hep açık)
	return n == 0 or zafer_var(n)


static func sus() -> int:
	var s := int(Game.meta.get("muhur_sus", -1))
	if s >= 0 and sus_acik(s):
		return s
	var en := 0
	for n in range(1, EN_COK + 1):
		if zafer_var(n):
			en = n
	return en


static func sus_sec(dir: int) -> int:
	## Açık süsler arasında döndür (taş ekranı)
	var acik: Array = []
	for n in EN_COK + 1:
		if sus_acik(n):
			acik.append(n)
	var i := acik.find(sus())
	var s := int(acik[posmod(i + dir, acik.size())])
	Game.meta["muhur_sus"] = s
	Game.save_meta()
	return s


static func sus_uygula(pl: Node) -> void:
	## Player kancası (saç kurulunca) ve taş ekranından: şolpı / örgü halkası rengi; Tan tamgası: sırtta güneş tamgası
	if pl == null or not is_instance_valid(pl):
		return
	var s := sus()
	var sac: Variant = pl.get("sac")
	if sac != null and is_instance_valid(sac) and sac.get("mat") != null:
		var mat: ShaderMaterial = sac.mat
		if s == 0:
			mat.set_shader_parameter("bead_col", Color(0.70, 0.73, 0.80))
			mat.set_shader_parameter("band_col", Color(0.918, 0.714, 0.306))
		else:
			var c := renk(s)
			mat.set_shader_parameter("bead_col", c.lerp(Color(1, 1, 1), 0.12))
			mat.set_shader_parameter("band_col", Color(1.0, 0.8, 0.36) if s >= EN_COK else c.lerp(Color(0.918, 0.714, 0.306), 0.35))
	var tg: Node = pl.get_node_or_null("MuhurTamga")
	if s >= EN_COK:
		if tg == null:
			tg = MuhurTamga.new()
			tg.name = "MuhurTamga"
			pl.add_child(tg)
	elif tg != null:
		tg.queue_free()
