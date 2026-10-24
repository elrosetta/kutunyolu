class_name OdaSablon
extends RefCounted
## v43 EL YAPIMI ODA ŞABLONLARI (Dead Cells'in yaklaşımı: tasarımcının çizdiği odalar, çizge üretici tarafından dikilir).
##
## Şablonlar data/odalar/*.json dosyalarında ASCII çizimdir (bkz. docs/TASARIM.md "v43: el yapımı odalar ve geçitler").
## Bir şablon bir kesimin (LevelGen.SW x SH) içine oturur: en çok 20 sütun x 12 satır (iki kesimlik geniş salon: en
## çok 44 sütun). Satır 0 kesimin y0+1 satırıdır (tavan), taban genellikle 8-9. satırda.
##
## Karakterler:
##   #  kaya (katı)              .  hava                   -  tek yönlü platform      ^  tehlike (biyomun dikeni / lavı)
##   =  kütük / kiriş köprü (tek yönlü; biyoma göre devrik ağaç, ahşap kiriş, buz köprü, kaburga, demir kiriş çizilir)
##   L  sol kapı yuvası (sol kenar sütununda AYAKTA DURULAN hücre; altı taban)     R  sağ kapı yuvası
##   T  tavan yuvası (0. satırda katı; dikey geçit buradan iner: altındaki sütunlar tabana dek açık olmalı)
##   B  taban yuvası (taban satırında katı; dikey geçit buradan aşağı iner)
##   g  yer yaratığı yeri   a  hava yaratığı yeri   $  ganimet / merak (küp, altın)   *  simge çapası (anıt / sahne)
##   t  tırmanma: bu hücreden aşağı sarkan zincir / ip / sarmaşık (biyoma göre; erişim modeli tırmanmayı varsaymaz)
##   d  asılı süs (fener, sancak, kemik çıngırak, buz sarkıtı, ışıyan mantar)
##   ~  yumuşak iniş yığını (saman, kar, yaprak, kül)        w  su yüzeyi (sığ havuz; hava sayılır, görseldir)
##   boşluk: dış kaya (katı)
##
## Alanlar: ad, biyom ["*" ya da biyom kimlikleri], tur ["*" ya da acik / kale / inis / magara], rol (varsayılan
## ["ana", "dal"]), tip (süs yoğunluğu / anıt adaylığı için oda türü), gok (göğe açık üst satırda kullanılabilir),
## simge (bölümün akılda kalan sahne parçası: bölüm başına bir), agirlik, harita (satırlar).

const DOSYALAR := ["ortak", "otuken", "bozkir", "sahmeran", "kaf", "tamu", "genis"]
const KOK := "res://data/odalar/%s.json"

static var _liste: Array = []
static var _yuklendi := false
static var hatalar: Array = []


static var _hepsi: Array = []


static func liste() -> Array:
	if not _yuklendi:
		_yukle()
	return _liste


static func hepsi() -> Array:
	## Bütün şablonlar ve aynalı kopyaları (üretici bunlardan seçer)
	if _hepsi.is_empty():
		for t in liste():
			_hepsi.append(t)
			_hepsi.append(ayna(t))
	return _hepsi


static func _yukle() -> void:
	_yuklendi = true
	_liste = []
	hatalar = []
	for ad in DOSYALAR:
		var yol: String = KOK % ad
		if not FileAccess.file_exists(yol):
			continue
		var f := FileAccess.open(yol, FileAccess.READ)
		var d: Variant = JSON.parse_string(f.get_as_text())
		if not (d is Dictionary):
			hatalar.append("%s: JSON okunamadı" % yol)
			continue
		for o in (d as Dictionary).get("odalar", []):
			var t := _coz(o, ad)
			if not t.is_empty():
				_liste.append(t)


static func _coz(o: Dictionary, dosya: String) -> Dictionary:
	## Ham şablonu çözer: boyut, yuvalar, işaretler. Hatalı şablon boş döner (hatalar listesine yazılır).
	var satir: Array = o.get("harita", [])
	if satir.is_empty():
		return {}
	var w := 0
	for s in satir:
		w = maxi(w, String(s).length())
	var rows: Array = []
	for s in satir:
		rows.append(String(s).rpad(w, " "))
	var t := {"ad": String(o.get("ad", "?")), "dosya": dosya, "biyom": o.get("biyom", ["*"]), "tur": o.get("tur", ["*"]),
		"rol": o.get("rol", ["ana", "dal"]), "tip": String(o.get("tip", "salon")), "gok": bool(o.get("gok", false)),
		"simge": bool(o.get("simge", false)), "agirlik": float(o.get("agirlik", 1.0)), "rows": rows, "w": w, "h": rows.size(),
		"ayna": false}
	_yuvalar(t)
	var ad: String = t["ad"]
	if w > 44 or (w > 20 and w < 28) or rows.size() > 12:
		hatalar.append("%s: boyut %dx%d (en çok 20x12 ya da geniş 28-44)" % [ad, w, rows.size()])
		return {}
	for k in ["L", "R"]:
		var r: int = int(t[k])
		if r >= 0 and (r < 5 or r > 8):
			hatalar.append("%s: %s yuvası %d. satırda (5-8 olmalı: taban y0+7..y0+10)" % [ad, k, r])
			return {}
	return t


static func _yuvalar(t: Dictionary) -> void:
	var rows: Array = t["rows"]
	var w: int = t["w"]
	t["L"] = -1
	t["R"] = -1
	var T: Array = []
	var Bs: Array = []
	var isaret: Array = []
	for y in rows.size():
		var s: String = rows[y]
		for x in w:
			var c := s[x]
			if c == "L" and x == 0:
				t["L"] = y
			elif c == "R" and x == w - 1:
				t["R"] = y
			elif c in ["g", "a", "$", "*", "t", "d", "~", "w"]:
				isaret.append([c, x, y])
	# dikey geçit yuvaları şablonun biçiminden bulunur (T / B harfleri yalnızca yazara hatırlatmadır):
	#   T (tavandan inen geçit): sütun tavanın altından tabana dek boş, taban düz ve katı (tehlike değil)
	#   B (tabandan inen geçit): sütunun en alt havası katı (tehlike / platform değil) tabana oturur, taban düz
	var h := rows.size()
	var tf: Array = []
	var bf: Array = []
	for x in w:
		var y := 0
		while y < h and hucre(String(rows[y])[x]) == 1:
			y += 1
		var f := -1
		if y < h:
			while y < h and hucre(String(rows[y])[x]) == 0:
				y += 1
			if y < h and hucre(String(rows[y])[x]) == 1:
				f = y
		tf.append(f)
		var fb := -1
		for yy in range(h - 1, 0, -1):
			if hucre(String(rows[yy - 1])[x]) == 0:
				if hucre(String(rows[yy])[x]) == 1:
					fb = yy
				break
		bf.append(fb)
	T = _duz_kosular(tf)
	for k in _duz_kosular(bf):
		Bs.append([k[0], k[1], int(bf[int(k[0])])])
	t["T"] = T
	t["B"] = Bs
	t["isaret"] = isaret
	# en uzun düz taban (aynı satır, üstünde 5 karo hava): Otağ Yeri / Bezirgân için uygunluk
	var duz := 0
	var run := 0
	var onceki := -2
	for x in w:
		var f: int = int(bf[x])
		var acik := f >= 5
		if acik:
			for k in range(1, 6):
				if hucre(String(rows[f - k])[x]) != 0:
					acik = false
		if acik and f == onceki:
			run += 1
		elif acik:
			run = 1
		else:
			run = 0
		onceki = f if acik else -2
		duz = maxi(duz, run)
	t["duz"] = duz


static func _duz_kosular(f: Array) -> Array:
	## Aynı taban satırındaki ardışık sütun koşuları (en az 5 sütun; -1 geçersiz)
	var out: Array = []
	var x0 := -1
	for x in f.size() + 1:
		var v := int(f[x]) if x < f.size() else -1
		if x0 >= 0 and v != int(f[x0]):
			if x - x0 >= 5:
				out.append([x0, x - 1])
			x0 = -1
		if x0 < 0 and v >= 0:
			x0 = x
	return out


static func _kosular(s: String, ch: String) -> Array:
	var out: Array = []
	var x0 := -1
	for x in s.length() + 1:
		var on := x < s.length() and s[x] == ch
		if on and x0 < 0:
			x0 = x
		elif not on and x0 >= 0:
			out.append([x0, x - 1])
			x0 = -1
	return out


static func ayna(t: Dictionary) -> Dictionary:
	## Yatay aynalı kopya (L <-> R)
	var m := t.duplicate()
	var rows: Array = []
	for s in t["rows"]:
		var r := String(s).reverse()
		r = r.replace("L", "\u0001").replace("R", "L").replace("\u0001", "R")
		rows.append(r)
	m["rows"] = rows
	m["ayna"] = not bool(t["ayna"])
	_yuvalar(m)
	return m


static func hucre(c: String) -> int:
	## Şablon karakteri -> ızgara değeri (0 hava, 1 katı, 2 tek yönlü, 3 tehlike)
	match c:
		"#", " ", "T", "B":
			return 1
		"-", "=":
			return 2
		"^":
			return 3
	return 0


static func uygun(t: Dictionary, biyom: String, tur: String, rol: String, gok: bool, genis: bool) -> bool:
	if not ("*" in t["biyom"] or biyom in t["biyom"]):
		return false
	if not ("*" in t["tur"] or tur in t["tur"]):
		return false
	if not (rol in t["rol"]):
		return false
	if gok and not bool(t["gok"]):
		return false
	if genis != (int(t["w"]) > 20):
		return false
	return true


static func yuva_uyar(t: Dictionary, sol: bool, sag: bool, ust: bool, alt: bool, en_az_kuyu: int) -> bool:
	## Odanın kapıları şablonun yuvalarıyla örtüşüyor mu (dikey geçitler için yuva en az en_az_kuyu sütun)
	if sol and int(t["L"]) < 0:
		return false
	if sag and int(t["R"]) < 0:
		return false
	if ust and _en_genis(t["T"]) < en_az_kuyu:
		return false
	if alt and _en_genis(t["B"]) < en_az_kuyu:
		return false
	return true


static func _en_genis(k: Array) -> int:
	var m := 0
	for r in k:
		m = maxi(m, int(r[1]) - int(r[0]) + 1)
	return m
