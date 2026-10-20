class_name Harita
extends RefCounted
## v32 bölüm haritası: sis (keşfedilen karolar), küçük harita dokusu ve Kut Taşı kayıtları.
## Oyuncunun bulunduğu hücreden katı olmayan karolar boyunca taşan (duvardan geçmeyen) bir elips (RX x RY karo)
## görülmüş sayılır; görülen havanın bitişiğindeki katı karolar da görülür (duvar çizgisi). Doku: karo başına PX x PX
## piksel, RGBA; görülmeyen karo saydam (altındaki parşömen görünür), görülen hava hafif yıkama, katı mürekkep,
## platform kahve çizgi, tehlike kızıl. İşaretler (çıkış, tomar, eşya, tüccar, sunak, seçkin, zamanlı kapı) çizim
## anında bölümden sorulur ve karosu görülmüşse gösterilir (HaritaUI). Her bölümde sıfırlanır (koşu içinde kalıcı).

const PX := 2
const RX := 18
const RY := 11
const INK := Color(0.11, 0.08, 0.09, 0.95)
const WASH := Color(0.9, 0.83, 0.66, 0.96)   # görülen hava: açık parşömen (görülmeyen alanın üstünde koyu sis kalır)
const PLAT := Color(0.36, 0.24, 0.14, 0.95)
const HAZ := Color(0.72, 0.13, 0.1, 0.95)

var level: Node
var W := 0
var H := 0
var seen := PackedByteArray()
var img: Image
var tex: ImageTexture
var gorulen := 0          # görülen hava karosu sayısı
var toplam_hava := 0      # bölümdeki (sınırlar içindeki) hava karosu sayısı
var tasi: Array = []      # {cell: Vector2i, ad: String, oda: int, bulundu: bool, rol: String}
var _t := 0.3
var _last := Vector2i(-99, -99)
var _dirty := false


func setup(lv: Node) -> void:
	level = lv
	W = lv.W
	H = lv.H
	seen.resize(W * H)
	seen.fill(0)
	img = Image.create(W * PX, H * PX, false, Image.FORMAT_RGBA8)
	img.fill(Color(0, 0, 0, 0))
	tex = ImageTexture.create_from_image(img)
	toplam_hava = 0
	var b: Rect2i = lv.bounds
	for y in range(b.position.y, b.end.y):
		for x in range(b.position.x, b.end.x):
			if lv.cell(x, y) != 1:
				toplam_hava += 1


func tasi_ekle(cell: Vector2i, ad: String, oda: int, rol: String) -> int:
	tasi.append({"cell": cell, "ad": ad, "oda": oda, "bulundu": false, "rol": rol})
	return tasi.size() - 1


func tasi_bul(i: int) -> bool:
	## Taş keşfedildi (yakınından geçildi); true: ilk kez
	if i < 0 or i >= tasi.size() or bool(tasi[i]["bulundu"]):
		return false
	tasi[i]["bulundu"] = true
	return true


func bulunan() -> Array:
	var out: Array = []
	for i in tasi.size():
		if bool(tasi[i]["bulundu"]):
			out.append(i)
	return out


func goruldu(x: int, y: int) -> bool:
	if x < 0 or x >= W or y < 0 or y >= H:
		return false
	return seen[y * W + x] == 1


func yuzde() -> float:
	## Görülen hava karolarının oranı (0..1)
	return float(gorulen) / maxf(1.0, float(toplam_hava))


func tick(delta: float, feet: Vector2) -> void:
	_t += delta
	var c := Vector2i(int(floor(feet.x / level.TS)), int(floor((feet.y - 2.0) / level.TS)))
	if _t < 0.2 and c == _last:
		return
	_t = 0.0
	_last = c
	reveal(c)


func reveal(c: Vector2i) -> void:
	## Hücreden katı olmayan karolar boyunca elips içinde taşma; bitişik katılar da görülür
	if c.x < 0 or c.x >= W or c.y < 0 or c.y >= H:
		return
	var q: Array = [c]
	var vis := {c: true}
	var qi := 0
	while qi < q.size():
		var p: Vector2i = q[qi]
		qi += 1
		_see(p.x, p.y)
		for o in [Vector2i(1, 0), Vector2i(-1, 0), Vector2i(0, 1), Vector2i(0, -1)]:
			var n: Vector2i = p + o
			if n.x < 1 or n.x >= W - 1 or n.y < 1 or n.y >= H - 1 or vis.has(n):
				continue
			var dx := float(n.x - c.x) / RX
			var dy := float(n.y - c.y) / RY
			if dx * dx + dy * dy > 1.0:
				continue
			vis[n] = true
			if level.cell(n.x, n.y) == 1:
				_see(n.x, n.y)   # duvar yüzü görülür, ardına geçilmez
				continue
			q.append(n)
	if _dirty:
		tex.update(img)
		_dirty = false


func _see(x: int, y: int) -> void:
	var i := y * W + x
	if seen[i] == 1:
		return
	seen[i] = 1
	_dirty = true
	var v: int = level.cell(x, y)
	if v != 1:
		gorulen += 1
	var col := WASH
	match v:
		1:
			col = INK
		2:
			col = PLAT
		3:
			col = HAZ
	if v == 2:
		img.fill_rect(Rect2i(x * PX, y * PX, PX, 1), col)
		img.fill_rect(Rect2i(x * PX, y * PX + 1, PX, PX - 1), WASH)
	else:
		img.fill_rect(Rect2i(x * PX, y * PX, PX, PX), col)


func hepsini_gor() -> void:
	## Test / hata ayıklama: bütün bölüm görülmüş sayılır
	var b: Rect2i = level.bounds
	for y in range(b.position.y, b.end.y):
		for x in range(b.position.x, b.end.x):
			_see(x, y)
	tex.update(img)
	_dirty = false


func hepsini_kesfet(oda_sec: Callable = Callable()) -> void:
	## Test / çekim (v33): oyuncunun gezerek göreceği hâl: bütün hava karoları ve bitişik duvar yüzleri görülür
	## (katı kayanın içi sisli kalır). oda_sec verilirse yalnızca onun true döndürdüğü karolar.
	var b: Rect2i = level.bounds
	for y in range(b.position.y, b.end.y):
		for x in range(b.position.x, b.end.x):
			if level.cell(x, y) == 1 or (oda_sec.is_valid() and not bool(oda_sec.call(x, y))):
				continue
			_see(x, y)
			for o in [Vector2i(1, 0), Vector2i(-1, 0), Vector2i(0, 1), Vector2i(0, -1), Vector2i(1, 1), Vector2i(-1, 1), Vector2i(1, -1), Vector2i(-1, -1)]:
				if level.cell(x + o.x, y + o.y) == 1:
					_see(x + o.x, y + o.y)
	tex.update(img)
	_dirty = false


func karo_degisti(x: int, y: int) -> void:
	## v34: karo hava / katı oldu (gizli cep kırıldı, kilit açıldı, zamanlı kapı kapandı): görülmüşse yeniden boyanır,
	## hava sayaçları güncellenir
	if x < 0 or x >= W or y < 0 or y >= H:
		return
	var i := y * W + x
	var b: Rect2i = level.bounds
	var hava: bool = level.cell(x, y) != 1
	if b.has_point(Vector2i(x, y)):
		toplam_hava += 1 if hava else -1
	if seen[i] == 1:
		if not hava:
			gorulen = maxi(0, gorulen - 1)   # eskiden hava sayılmıştı
		seen[i] = 0
		_see(x, y)   # yeni hava karosunu sayar ve boyar
		tex.update(img)
		_dirty = false


func _oda_goruldu(rm: Dictionary) -> bool:
	## Odanın ortası (taban hizası) görüldü mü
	var fl: Array = rm.get("fl", [])
	if fl.is_empty():
		return true
	var mx := (int(rm["ix0"]) + int(rm["ix1"])) / 2
	return goruldu(mx, int(fl[mx - int(rm["ix0"])]) - 2)


func sorular() -> Array:
	## v34 "?" ipuçları: görülmüş bir kapı ağzının (koridor / kuyu / pencere) öbür yanındaki oda henüz görülmediyse
	## koridorun / kuyunun ortasında soluk soru işareti (Dead Cells haritasının keşfedilmemiş açıklıkları)
	var out: Array = []
	var lv := level
	for d in lv.doors:
		if String(d["kind"]) == "sil":
			continue
		var A: Dictionary = lv.rooms[int(d["a"])]
		var B: Dictionary = lv.rooms[int(d["b"])]
		var ga := _oda_goruldu(A)
		var gb := _oda_goruldu(B)
		if ga == gb:
			continue
		var c := Vector2i.ZERO
		var ag := Vector2i.ZERO   # görülmüş yandaki ağız
		if String(d["dir"]) == "h":
			var y := int(d["y"]) - 2
			c = Vector2i((int(d["x"]) + int(d["x2"])) / 2, y)
			ag = Vector2i(int(d["x"]) - 1, y) if ga else Vector2i(int(d["x2"]) + 1, y)
		else:
			var dx := int(d.get("dus_x", d["x"])) + 1
			c = Vector2i(dx, (int(d["y"]) + int(d.get("y2", d["y"]))) / 2)
			ag = Vector2i(dx, int(d["y"]) - 1) if ga else Vector2i(dx, int(d.get("y2", d["y"])) - 1)
		if goruldu(ag.x, ag.y) or goruldu(c.x, c.y):
			out.append({"tur": "soru", "cell": c, "ad": "?", "i": -1})
	return out


func isaretler() -> Array:
	## Çizilecek işaretler: [{tur, cell, ad, i, ek}] (yalnızca karosu görülenler; Kut Taşı bulunduysa "tasi", görüldüyse "tasi_sonuk")
	var out: Array = []
	var lv := level
	var TS: int = lv.TS
	for i in tasi.size():
		var t: Dictionary = tasi[i]
		var c: Vector2i = t["cell"]
		if bool(t["bulundu"]):
			out.append({"tur": "tasi", "cell": c, "ad": String(t["ad"]), "i": i})
		elif goruldu(c.x, c.y):
			out.append({"tur": "tasi_sonuk", "cell": c, "ad": "?", "i": i})
	var ec: Vector2i = lv.exit_cell
	if goruldu(ec.x, ec.y):
		out.append({"tur": "cikis", "cell": ec, "ad": "Kut Kapısı", "i": -1})
	for p in lv.pickups:
		if not is_instance_valid(p) or p.is_queued_for_deletion():
			continue
		var c := Vector2i(int(floor(p.global_position.x / TS)), int(floor((p.global_position.y - 4.0) / TS)))
		if not goruldu(c.x, c.y):
			continue
		match String(p.kind):
			"tilsim":
				out.append({"tur": "tomar", "cell": c, "ad": "Kut Tomarı", "i": -1})
			"item":
				if bool(p.pedestal):
					out.append({"tur": "esya", "cell": c, "ad": "Eşya", "i": -1})
			"lutuf":
				out.append({"tur": "sunak", "cell": c, "ad": "Sunak", "i": -1})
	if lv.bezirgan != null and is_instance_valid(lv.bezirgan):
		var c := Vector2i(int(floor(lv.bezirgan.global_position.x / TS)), int(floor((lv.bezirgan.global_position.y - 4.0) / TS)))
		if goruldu(c.x, c.y):
			out.append({"tur": "pazar", "cell": c, "ad": "Bezirgân", "i": -1})
	for e in lv.get_tree().get_nodes_in_group("dusman"):
		if not is_instance_valid(e) or not bool(e.get("elite")) or bool(e.get("dead")) or e.get("level") != lv:
			continue
		var c := Vector2i(int(floor(e.global_position.x / TS)), int(floor((e.global_position.y - 4.0) / TS)))
		if goruldu(c.x, c.y):
			out.append({"tur": "seckin", "cell": c, "ad": "Seçkin", "i": -1})
	for z in lv.zamanli:
		if not is_instance_valid(z):
			continue
		var c: Vector2i = z.cell
		if goruldu(c.x, c.y - 2):
			out.append({"tur": "zamanli", "cell": Vector2i(c.x, c.y - 2), "ad": z.etiket(), "i": -1, "acik": z.acik})
	# v34: lanetli sandık, anahtar, kilitli kapı ve keşfedilmemiş açıklık ("?")
	for sd in lv.get("sandiklar") if lv.get("sandiklar") != null else []:
		if is_instance_valid(sd) and not sd.acildi:
			var c := Vector2i(int(floor(sd.global_position.x / TS)), int(floor((sd.global_position.y - 4.0) / TS)))
			if goruldu(c.x, c.y):
				out.append({"tur": "sandik", "cell": c, "ad": "Lanetli Sandık", "i": -1})
	for an in lv.get("anahtarlar") if lv.get("anahtarlar") != null else []:
		if is_instance_valid(an) and not an.alindi:
			var c := Vector2i(int(floor(an.global_position.x / TS)), int(floor((an.global_position.y - 4.0) / TS)))
			if goruldu(c.x, c.y):
				out.append({"tur": "anahtar", "cell": c, "ad": "Anahtar", "i": -1})
	for kk in lv.get("kilitler") if lv.get("kilitler") != null else []:
		if is_instance_valid(kk) and not kk.acik:
			var c := Vector2i(kk.cell.x, kk.cell.y - 2)
			if goruldu(c.x - 1, c.y) or goruldu(c.x + 1, c.y):
				out.append({"tur": "kilit", "cell": c, "ad": "Kilitli kapı", "i": -1})
	if not lv.doors.is_empty():
		out.append_array(sorular())
	return out


func sayac_parcalari() -> Array:
	## v34 birleştirme: sayacın parçaları [anahtar, ad, bulunan, toplam] (HaritaUI her parçanın önüne simgesini çizer:
	## Tomar için yeni kayın kabuğu tomar simgesi TomarV2 "ui_tomar")
	var ilk: Dictionary = level.get("sayac_ilk") if level.get("sayac_ilk") != null else {}
	if ilk.is_empty():
		return []
	var simdi: Dictionary = level.sayac()
	var out: Array = []
	for k in [["hazine", "Hazine"], ["tomar", "Tomar"], ["gizli", "Gizli"], ["kilit", "Kilit"]]:
		var top := int(ilk.get(k[0], 0))
		if top <= 0:
			continue
		out.append([k[0], k[1], top - mini(top, int(simdi.get(k[0], 0))), top])
	return out


func sayac_metni() -> String:
	## v34 tam harita sayacı: "Hazine 1/3 · Tomar 0/2 · Gizli 0/2 · Kilit 0/1" (bulunan / toplam; tamamlama dürtüsü)
	var parca: Array = []
	for p in sayac_parcalari():
		parca.append("%s %d/%d" % [p[1], int(p[2]), int(p[3])])
	return "  ·  ".join(parca)
