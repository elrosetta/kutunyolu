class_name Zorluk
extends RefCounted
## v22 zorluk: bütün denge düğmeleri tek yerde (data/zorluk.json). Düşman canı / hasarı / saldırganlığı derinlik
## dizileriyle, eşya hasarı kademe ve nadirlikle, şifa ekonomisi ve Kut Mühürleri (Dead Cells "Boss Cell" karşılığı:
## son bossu yendikçe açılan zorluk kademeleri) buradan okunur. "genel" bölümü bütün oyunu tek çarpanla çevirir.
## Ölçüm: -- --denge (tools/tests/denge_testi.gd).

const PATH := "res://data/zorluk.json"
const MUHUR_EN_COK := 5
static var _d: Dictionary = {}
static var _muhur_test := -1


static func data() -> Dictionary:
	if _d.is_empty():
		var f := FileAccess.open(PATH, FileAccess.READ)
		if f:
			var v: Variant = JSON.parse_string(f.get_as_text())
			if v is Dictionary:
				_d = v
	return _d


static func derinlik() -> int:
	if Game.run.is_empty():
		return 1
	return maxi(1, int(Game.run.get("depth", 1)))


static func _arr(key: String, d: int) -> float:
	var a: Array = data().get("derinlik", {}).get(key, [1.0])
	if a.is_empty():
		return 1.0
	var dd := derinlik() if d <= 0 else d
	return float(a[clampi(dd - 1, 0, a.size() - 1)])


static func _genel(key: String) -> float:
	return float(data().get("genel", {}).get(key, 1.0))


# ------------------------------------------------------------------ Kut Mühürleri
static func muhur() -> int:
	## Bu koşunun mühür kademesi (koşu başında seçilen; Game.run["muhur"])
	if _muhur_test >= 0:
		return _muhur_test
	if Game.run.is_empty():
		return 0
	return clampi(int(Game.run.get("muhur", 0)), 0, MUHUR_EN_COK)


static func set_muhur(n: int) -> void:
	## Test: koşudan bağımsız mühür (denge testi)
	_muhur_test = clampi(n, -1, MUHUR_EN_COK)


static func muhur_acik() -> int:
	## Açılmış en yüksek mühür (son boss her yenilişte bir sonrakini açar)
	return clampi(int(Game.meta.get("muhur_acik", 0)), 0, MUHUR_EN_COK)


static func muhur_secili() -> int:
	return clampi(int(Game.meta.get("muhur", 0)), 0, muhur_acik())


static func muhur_def(n := -1) -> Dictionary:
	var a: Array = data().get("muhurler", [])
	if a.is_empty():
		return {}
	return a[clampi(muhur() if n < 0 else n, 0, a.size() - 1)]


static func _m(key: String, def := 1.0) -> float:
	return float(muhur_def().get(key, def))


static func muhur_adi(n := -1) -> String:
	return String(muhur_def(n).get("ad", "Mühürsüz"))


static func on_final_boss() -> bool:
	## Erlik Han yenildi: bu koşunun mührü açılmış en yüksek mühürse bir sonraki açılır. true: yeni mühür açıldı.
	var cur := muhur()
	if cur >= muhur_acik() and muhur_acik() < MUHUR_EN_COK:
		Game.meta["muhur_acik"] = muhur_acik() + 1
		Game.meta["muhur"] = muhur_acik()   # Dead Cells gibi: yeni mühür bir sonraki koşuda takılı gelir
		Game.save_meta()
		return true
	return false


# ------------------------------------------------------------------ düşman
static func can_k(d := -1) -> float:
	return _arr("can", d) * _genel("can") * _m("can")


static func hasar_k(d := -1) -> float:
	return _arr("hasar", d) * _genel("hasar") * _m("hasar")


static func saldirganlik(d := -1) -> float:
	## Saldırı beklemesinin (Enemy.cd) sönme hızı: 1,0 eski tempo; büyüdükçe daha az bekler
	return _arr("saldirganlik", d) * _genel("saldirganlik") * _m("saldirganlik")


static func hazirlik(d := -1) -> float:
	## Hazırlık (uyarı) süresinin kısalma hızı; okunurluk için en çok %15
	return _arr("hazirlik", d)


static func yogunluk(d := -1) -> int:
	return int(_arr("yogunluk", d)) + int(_m("yogunluk", 0.0))


static func seckin_sayi(d := -1) -> int:
	return int(_arr("seckin", d)) + int(_m("seckin", 0.0))


static func suru(d := -1) -> float:
	return _arr("suru", d)


# ------------------------------------------------------------------ v26 yapay zekâ baskısı
static func yz(key: String, def: float, d := -1) -> float:
	## zorluk.json "yz": derinlik dizisi (ya da tek sayı). tepki_azalt / tepki_bekleme / jeton / bekleme / sarsilmaz /
	## diretme / baski (Enemy.gd v26)
	var v: Variant = data().get("yz", {}).get(key, null)
	if v == null:
		return def
	if v is Array:
		var a: Array = v
		if a.is_empty():
			return def
		var dd := derinlik() if d <= 0 else d
		return float(a[clampi(dd - 1, 0, a.size() - 1)])
	return float(v)


static func rol_can(ai: String) -> float:
	## v26: yapay zekâ rolüne göre can çarpanı (derinlik eğrisinin üstüne; tazılar daha çok, uzak / uçan roller daha az)
	return float(data().get("rol_can", {}).get(ai, 1.0))


static func seckin_can() -> float:
	return float(data().get("seckin", {}).get("can", 3.0))


static func seckin_hasar() -> float:
	return float(data().get("seckin", {}).get("hasar", 1.3))


static func ofkeli_sans() -> float:
	return _m("ofkeli", 0.0)


static func ofkeli(key: String) -> float:
	return float(data().get("ofkeli", {}).get(key, 1.0))


# ------------------------------------------------------------------ boss
static func boss_derinlik(id: String) -> int:
	## Boss kimliği ya da boss yaratığının kimliği -> savaşıldığı derinlik (Game.BOSS_AFTER)
	var bid := id
	for b in Data.world.get("bosses", []):
		if String(b.get("enemy", "")) == id:
			bid = String(b["id"])
	for d in Game.BOSS_AFTER:
		if String(Game.BOSS_AFTER[d]) == bid:
			return int(d)
	return derinlik()


static func boss_id(id: String) -> String:
	for b in Data.world.get("bosses", []):
		if String(b.get("enemy", "")) == id or String(b["id"]) == id:
			return String(b["id"])
	return id


static func boss_can(id: String, fallback := 1000.0) -> float:
	var bd: Dictionary = data().get("boss", {}).get(boss_id(id), {})
	return float(bd.get("can", fallback)) * _genel("can") * _m("can")


# ------------------------------------------------------------------ eşya
static func kademe(d := -1) -> int:
	## Derinliğin eşya kademesi (düşme kalitesi, eşya hasarı); derinlik - 1, en çok dizinin sonu
	var a: Array = data().get("esya", {}).get("kademe", [1.0])
	var dd := derinlik() if d <= 0 else d
	return clampi(dd - 1, 0, maxi(0, a.size() - 1))


static func esya_k(t: int) -> float:
	var a: Array = data().get("esya", {}).get("kademe", [1.0])
	return float(a[clampi(t, 0, a.size() - 1)])


static func nadirlik_k(r: int) -> float:
	var a: Array = data().get("esya", {}).get("nadirlik", [1.0])
	return float(a[clampi(r, 0, a.size() - 1)])


static func taban() -> float:
	## v23: eşya taban hasarı / gücü çarpanı (silah hasarı ve teçhizat gücü; güç tomarlardan gelir)
	return float(data().get("esya", {}).get("taban", 1.0))


static func dot_k() -> float:
	## Süreğen hasar (yanma, kanama, zehir) ve duvar çarpması: oyuncunun gücüyle (taban x o derinliğin eşya kademesi x
	## en yüksek tomar statı); kaynağı bilinmediği için (kılıç, yay, tuzak) beklenen güç kullanılır
	var best := 0
	if not Game.run.is_empty():
		for k in Game.run.get("ongun", {}):
			best = maxi(best, int(Game.run["ongun"][k]))
	return taban() * esya_k(kademe()) * tomar_k(best)


# ------------------------------------------------------------------ v23 tomar ekonomisi (Dead Cells "Scroll of Power")
static func _tomar() -> Dictionary:
	return data().get("tomar", {})


static func tomar_kazanc(n: int) -> float:
	## n. tomarın (1'den) hasar kazancı: dizinin sonundan sonrası son değer (azalan getiri)
	var a: Array = _tomar().get("kazanc", [0.15])
	if a.is_empty() or n <= 0:
		return 0.0
	return float(a[clampi(n - 1, 0, a.size() - 1)])


static func tomar_k(n: int) -> float:
	## Stat seviyesi n (o renkte okunan tomar) -> hasar çarpanı: 1 + kazançların toplamı
	var k := 1.0
	for i in range(1, maxi(0, n) + 1):
		k += tomar_kazanc(i)
	return k


static func tomar_can(stat: String) -> float:
	## Tomar başına en yüksek can artışı (o anki azami canın payı)
	return float(_tomar().get("can", {}).get(stat, 0.06))


static func tomar_iyilesme() -> float:
	## Tomar okununca ek iyileşme (azami canın payı)
	return float(_tomar().get("iyilesme", 0.1))


static func ayi_zirh(lv: int) -> float:
	## Ayı statı: alınan hasar azalması (seviye başına, üst sınırlı)
	return minf(float(_tomar().get("ayi_zirh_en_cok", 0.3)), float(_tomar().get("ayi_zirh", 0.03)) * float(lv))


static func beklenen_tomar(d: int) -> Dictionary:
	## Beklenen oyuncu (denge testi, --bot_gercek): d. derinliğin başında okunmuş tomarlar. Derinlik başına
	## "derinlik" tane (bölümdeki üç tomarın ortalaması) + geçilen her boss bir tane; "pay" oranında dağıtılır.
	var T := _tomar()
	var s := float(T.get("derinlik", 2.5)) * float(maxi(0, d - 1))
	for bd in Game.BOSS_AFTER:
		if int(bd) < d:
			s += float(T.get("boss", 1.0))
	var pay: Dictionary = T.get("pay", {"kurt": 0.6, "ayi": 0.25, "kartal": 0.15})
	return {"kurt": int(round(s * float(pay.get("kurt", 0.6)))), "ayi": int(round(s * float(pay.get("ayi", 0.25)))),
		"kartal": int(round(s * float(pay.get("kartal", 0.15))))}


static func beklenen_can(o: Dictionary, taban_can := 100.0) -> float:
	## Tomarlardan gelen beklenen azami can (her tomar o anki azami canı payınca artırır)
	var hp := taban_can
	for stat in ["kurt", "kartal", "ayi"]:
		for i in int(o.get(stat, 0)):
			hp *= 1.0 + tomar_can(stat)
	return hp


# ------------------------------------------------------------------ v23 kritik
static func _krit(key: String, def: float) -> float:
	return float(data().get("kritik", {}).get(key, def))


static func kosul_bekleme() -> float:
	## Durum koşullu silah kritiği (kanayan / yanan / sersem / havadaki hedef, arkadan, uçtan...) aynı düşmanda en
	## çok bu sıklıkta (sn): koşul sürüp gidince her vuruş kritik olmasın
	return _krit("kosul_bekleme", 1.0)


static func kosul_vurus() -> int:
	## Aynı düşmana iki koşul kritiği arasında en az bu kadar isabet (yavaş ağır silahta bekleme süresi yetmiyor)
	return int(_krit("kosul_vurus", 4.0))


static func bitiris_k() -> float:
	## Zincir bitirişi (Alp'in üçüncü vuruşu, ağır silahların bitiriş kritiği, Ay Dansı'nın son vuruşu): ritimsiz
	## basışta kritik değil bu hasar çarpanı; Kut Yankısı ya da usul vuruşuyla gelirse kritik
	return _krit("bitiris", 1.3)


static func lutuf_krit() -> float:
	return _krit("ay_ata", 6.0)


static func segrek_krit() -> float:
	return _krit("segrek", 5.0)


# ------------------------------------------------------------------ şifa
static func _sifa(key: String, def: float) -> float:
	return float(data().get("sifa", {}).get(key, def))


static func sise_sifa() -> float:
	return _sifa("sise", 0.45) * _genel("sifa") * _m("sifa")


static func ot_sifa() -> float:
	return _sifa("ot", 0.25) * _genel("sifa") * _m("sifa")


static func derinlik_sifa() -> float:
	return _sifa("derinlik", 0.15) * _genel("sifa") * _m("sifa")


static func sifa_dusme() -> float:
	return _sifa("dusme", 0.04)


static func sise_ek() -> int:
	## Mührün şişe cezası (en az 1 şişe kalır; Game.new_run uygular)
	return int(_m("sise", 0.0))
