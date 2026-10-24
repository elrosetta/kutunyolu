class_name GecitCiz
extends Node2D
## v43 geçit ve şablon süsleri çizimi (mürekkep + düz renk, çalışma anında vektör: çözünürlükten bağımsız, HD paketi
## gerekmez). Her dikey geçit türünün kendi görseli: demir zincir (salınır) ve demir raflar, ip merdiven, kök / sarmaşık
## duvarı ve kök düğümleri, kırık taş merdiven örgüsü, buz / kaya çıkıntıları (sarkıt, kar başlığı), rüzgâr bacası
## çizgileri, ahşap / buz iskele (dikme, çapraz), yumuşak iniş yığınları (saman, kar, yaprak, su, kül). Şablon süsleri:
## kütük / kiriş köprüler, tavandan sarkan tırmanılır zincir / ip / sarmaşık, su havuzları, asılı süsler.
## Geçitlerin tek yönlü karoları (basamak / kapak) Level'de görünmez karo olarak döşenir: görseli buradadır.

const TS := 24.0
const MUREKKEP := Color(0.07, 0.05, 0.06)

## Biyom renkleri: demir, ahşap, ip, kök, yaprak, taş, buz, yığın
const RENK := {
	"otuken": {"demir": Color(0.32, 0.33, 0.36), "ahsap": Color(0.46, 0.3, 0.17), "ip": Color(0.66, 0.53, 0.34), "kok": Color(0.36, 0.24, 0.15),
		"yaprak": Color(0.3, 0.52, 0.22), "tas": Color(0.45, 0.43, 0.38), "vurgu": Color(0.75, 0.62, 0.38)},
	"bozkir": {"demir": Color(0.36, 0.33, 0.3), "ahsap": Color(0.58, 0.4, 0.22), "ip": Color(0.78, 0.64, 0.4), "kok": Color(0.48, 0.36, 0.22),
		"yaprak": Color(0.62, 0.6, 0.3), "tas": Color(0.72, 0.6, 0.42), "vurgu": Color(0.9, 0.76, 0.48)},
	"kaf": {"demir": Color(0.4, 0.45, 0.52), "ahsap": Color(0.5, 0.42, 0.36), "ip": Color(0.72, 0.68, 0.6), "kok": Color(0.42, 0.38, 0.4),
		"yaprak": Color(0.55, 0.7, 0.75), "tas": Color(0.62, 0.72, 0.82), "vurgu": Color(0.86, 0.95, 1.0)},
	"sahmeran": {"demir": Color(0.3, 0.36, 0.34), "ahsap": Color(0.36, 0.3, 0.24), "ip": Color(0.5, 0.56, 0.4), "kok": Color(0.22, 0.3, 0.26),
		"yaprak": Color(0.2, 0.62, 0.5), "tas": Color(0.36, 0.42, 0.4), "vurgu": Color(0.45, 1.0, 0.8)},
	"tamu": {"demir": Color(0.28, 0.25, 0.26), "ahsap": Color(0.32, 0.22, 0.17), "ip": Color(0.45, 0.38, 0.3), "kok": Color(0.3, 0.18, 0.14),
		"yaprak": Color(0.5, 0.25, 0.15), "tas": Color(0.78, 0.72, 0.62), "vurgu": Color(1.0, 0.45, 0.15)},
}

var level: Node
var biyom := "otuken"
var gecitler: Array = []
var propler: Dictionary = {}
var _t := 0.0
var _salinim: Array = []   # [x, y0, y1, faz] salınan zincir / ip / sarmaşık (her karede yeniden çizilir)
var _sabit: Node2D           # salınmayan parçalar (bir kez çizilir)
var _kati: Node2D            # katı karoların üstüne binen süsler (taş örgü, kar başlığı, sarkıt): zemin karolarının önünde
var _rng := RandomNumberGenerator.new()


static func kur(lv: Node, gec: Array, pr: Dictionary, bid: String) -> GecitCiz:
	var g := GecitCiz.new()
	g.level = lv
	g.gecitler = gec
	g.propler = pr
	g.biyom = bid if RENK.has(bid) else "otuken"
	g.z_index = -1
	g.name = "GecitCiz"
	# biyomun ışığında düz renkler fazla parlamasın (mürekkep zeminiyle aynı değer aralığı)
	var k: float = float({"bozkir": 0.6, "otuken": 0.82, "kaf": 0.85, "sahmeran": 0.8, "tamu": 0.72}.get(g.biyom, 0.8))
	g.modulate = Color(k, k, k)
	lv.add_child(g)
	return g


func _ready() -> void:
	_rng.seed = 4343
	_sabit = Node2D.new()
	_sabit.z_index = 0
	_sabit.draw.connect(_ciz_sabit)
	add_child(_sabit)
	_kati = Node2D.new()
	_kati.z_as_relative = false
	_kati.z_index = 1
	_kati.draw.connect(_ciz_kati)
	add_child(_kati)
	for gv in gecitler:
		var tip := String(gv["tip"])
		if tip in ["zincir", "ip", "kok"]:
			for tr in gv["tirman"]:
				_salinim.append([(float(tr[0]) + float(tr[2])) * 0.5, float(tr[1]), float(tr[3]), _rng.randf() * TAU, tip, gv])
	for tr in propler.get("tirman", []):
		_salinim.append([(float(tr[0]) + float(tr[2])) * 0.5, float(tr[1]), float(tr[3]), _rng.randf() * TAU, _tirman_tipi(), {}])
	_sabit.queue_redraw()
	_kati.queue_redraw()


func _tirman_tipi() -> String:
	match biyom:
		"tamu":
			return "zincir"
		"otuken", "sahmeran":
			return "sarmasik"
	return "ipt"


func _process(delta: float) -> void:
	_t += delta
	var cam := get_viewport().get_camera_2d()
	if cam == null or Engine.get_process_frames() % 2 != 0:
		return
	queue_redraw()


func R(k: String) -> Color:
	return RENK[biyom][k]


# ------------------------------------------------------------------ salınan parçalar (her kare)
func _draw() -> void:
	var cam := get_viewport().get_camera_2d()
	var vis := Rect2(-1e6, -1e6, 2e6, 2e6)
	if cam:
		var vs := get_viewport_rect().size / cam.zoom
		vis = Rect2(cam.get_screen_center_position() - vs * 0.6, vs * 1.2)
	for s in _salinim:
		var x := float(s[0]) * TS
		var y0 := float(s[1]) * TS
		var y1 := float(s[2]) * TS
		if not vis.intersects(Rect2(x - 40, y0, 80, y1 - y0)):
			continue
		match String(s[4]):
			"zincir":
				_zincir(x, y0, y1, float(s[3]))
			"ip":
				_ip_merdiven(s[5], float(s[3]))
			"kok":
				_kok_duvari(s[5], float(s[3]))
			"sarmasik":
				_sarmasik(x, y0, y1, float(s[3]))
			_:
				_ip(x, y0, y1, float(s[3]))
	for gv in gecitler:
		if String(gv["tip"]) == "ruzgar" and not (gv["ruzgar"] as Array).is_empty():
			_ruzgar(gv)


func _sal(yk: float, faz: float, genlik: float) -> float:
	## sarkaç salınımı: üstte 0, aşağı doğru artar
	return sin(_t * 1.4 + faz) * genlik * yk + sin(_t * 2.3 + faz * 1.7) * genlik * 0.25 * yk


func _zincir(x: float, y0: float, y1: float, faz: float) -> void:
	var ln := y1 - y0
	if ln <= 0.0:
		return
	# tavanda halka / kanca
	draw_circle(Vector2(x, y0 + 2.0), 6.0, MUREKKEP)
	draw_circle(Vector2(x, y0 + 2.0), 4.0, R("demir").lightened(0.15))
	var y := y0 + 6.0
	var i := 0
	while y < y1:
		var k := (y - y0) / ln
		var px := x + _sal(k, faz, 7.0)
		var c := R("demir")
		if i % 2 == 0:
			# önden görülen halka
			draw_arc(Vector2(px, y + 6.0), 6.5, 0.0, TAU, 14, MUREKKEP, 4.4)
			draw_arc(Vector2(px, y + 6.0), 6.5, 0.0, TAU, 14, c, 2.4)
			draw_arc(Vector2(px - 1.5, y + 4.5), 4.0, PI * 1.05, PI * 1.6, 6, c.lightened(0.45), 1.2)
		else:
			# yandan görülen halka
			draw_rect(Rect2(px - 2.4, y + 0.5, 4.8, 11.0), MUREKKEP)
			draw_rect(Rect2(px - 1.2, y + 1.5, 2.4, 9.0), c.lightened(0.1))
		y += 9.0
		i += 1


func _ip(x: float, y0: float, y1: float, faz: float) -> void:
	var ln := maxf(1.0, y1 - y0)
	var pts := PackedVector2Array()
	var y := y0
	while y <= y1:
		pts.append(Vector2(x + _sal((y - y0) / ln, faz, 5.0), y))
		y += 6.0
	if pts.size() < 2:
		return
	draw_polyline(pts, MUREKKEP, 5.0)
	draw_polyline(pts, R("ip"), 3.0)
	for j in range(0, pts.size(), 2):
		var p := pts[j]
		draw_line(p + Vector2(-1.5, -2), p + Vector2(1.5, 2), R("ip").darkened(0.35), 1.0)
	draw_circle(pts[pts.size() - 1], 3.5, MUREKKEP)
	draw_circle(pts[pts.size() - 1], 2.2, R("ip").darkened(0.15))


func _sarmasik(x: float, y0: float, y1: float, faz: float) -> void:
	var ln := maxf(1.0, y1 - y0)
	var pts := PackedVector2Array()
	var y := y0
	while y <= y1:
		var k := (y - y0) / ln
		pts.append(Vector2(x + sin(y * 0.07 + faz) * 3.0 + _sal(k, faz, 3.0), y))
		y += 5.0
	if pts.size() < 2:
		return
	draw_polyline(pts, MUREKKEP, 4.5)
	draw_polyline(pts, R("kok").lightened(0.1), 2.5)
	for j in range(1, pts.size(), 3):
		var p := pts[j]
		var s := 1.0 if j % 2 == 0 else -1.0
		_yaprak(p, Vector2(s * 7.0, 2.0), R("yaprak"))


func _yaprak(p: Vector2, d: Vector2, c: Color) -> void:
	var n := Vector2(-d.y, d.x).normalized() * d.length() * 0.35
	var poly := PackedVector2Array([p, p + d * 0.5 + n, p + d, p + d * 0.5 - n])
	draw_colored_polygon(poly, c)
	draw_polyline(PackedVector2Array([p, p + d * 0.5 + n, p + d, p + d * 0.5 - n, p]), MUREKKEP, 1.0)


func _ip_merdiven(gv: Dictionary, faz: float) -> void:
	if gv.is_empty():
		return
	var tr: Array = gv["tirman"][0]
	var xa := float(tr[0]) * TS + 5.0
	var xb := float(tr[2]) * TS - 5.0
	var y0 := float(gv["ust"]) * TS - 4.0
	var y1 := float(gv["alt"]) * TS - 6.0
	var ln := maxf(1.0, y1 - y0)
	var sol := PackedVector2Array()
	var sag := PackedVector2Array()
	var y := y0
	while y <= y1:
		var o := _sal((y - y0) / ln, faz, 3.0)
		sol.append(Vector2(xa + o, y))
		sag.append(Vector2(xb + o, y))
		y += 6.0
	# basamaklar (her 12 px bir; çarpışan basamaklar kalın tahta)
	var hy := {}
	for b in gv["basamak"]:
		hy[int(b[1])] = true
	y = y0 + 10.0
	while y < y1:
		var o2 := _sal((y - y0) / ln, faz, 3.0)
		var row := int(floor(y / TS))
		var kalin: bool = hy.has(row) and absf(y - float(row) * TS) < 6.0
		if kalin:
			draw_rect(Rect2(xa - 3.0 + o2, float(row) * TS - 1.0, xb - xa + 6.0, 7.0), MUREKKEP)
			draw_rect(Rect2(xa - 2.0 + o2, float(row) * TS, xb - xa + 4.0, 5.0), R("ahsap").lightened(0.1))
		else:
			draw_line(Vector2(xa + o2, y), Vector2(xb + o2, y), MUREKKEP, 4.0)
			draw_line(Vector2(xa + o2, y), Vector2(xb + o2, y), R("ahsap"), 2.2)
		y += 12.0
	for hat in [sol, sag]:
		if (hat as PackedVector2Array).size() >= 2:
			draw_polyline(hat, MUREKKEP, 4.5)
			draw_polyline(hat, R("ip"), 2.4)


func _kok_duvari(gv: Dictionary, faz: float) -> void:
	if gv.is_empty():
		return
	var tr: Array = gv["tirman"][0]
	var xa := float(tr[0]) * TS
	var xb := float(tr[2]) * TS
	var y0 := float(gv["ust"]) * TS - 10.0
	var y1 := float(gv["alt"]) * TS
	var rr := RandomNumberGenerator.new()
	rr.seed = int(xa * 13.0 + y0)
	# ana kökler: aşağı kıvrılarak inen 3-4 kalın kök
	for k in 4:
		var bx := lerpf(xa + 4.0, xb - 4.0, float(k) / 3.0)
		var pts := PackedVector2Array()
		var y := y0
		var ph := rr.randf() * TAU
		while y <= y1:
			pts.append(Vector2(bx + sin(y * 0.045 + ph) * 6.0 + sin(_t * 0.9 + faz + k) * 0.8, y))
			y += 6.0
		if pts.size() > 1:
			var w := 6.0 - float(k % 2) * 2.0
			draw_polyline(pts, MUREKKEP, w + 2.4)
			draw_polyline(pts, R("kok"), w)
			draw_polyline(pts, R("kok").lightened(0.25), maxf(1.0, w * 0.3))
		# yan filizler ve yapraklar
		for j in range(2, pts.size() - 1, 4):
			var p := pts[j]
			var s := -1.0 if (j + k) % 2 == 0 else 1.0
			draw_line(p, p + Vector2(s * 9.0, 5.0), MUREKKEP, 2.6)
			draw_line(p, p + Vector2(s * 9.0, 5.0), R("kok").lightened(0.1), 1.4)
			if rr.randf() < 0.7:
				_yaprak(p + Vector2(s * 8.0, 5.0), Vector2(s * 6.0, 4.0), R("yaprak").lightened(rr.randf() * 0.2))
	if biyom == "sahmeran":
		# ışıyan yosun damlaları
		for k2 in 6:
			var p2 := Vector2(rr.randf_range(xa, xb), rr.randf_range(y0, y1))
			draw_circle(p2, 2.2, R("vurgu") * Color(1, 1, 1, 0.55 + 0.35 * sin(_t * 2.0 + k2)))


func _ruzgar(gv: Dictionary) -> void:
	var rz: Array = gv["ruzgar"]
	var xa := float(rz[0]) * TS
	var xb := float(rz[2]) * TS
	var y0 := float(rz[1]) * TS
	var y1 := float(rz[3]) * TS
	var h := y1 - y0
	for k in 9:
		var x := lerpf(xa + 4.0, xb - 4.0, fmod(float(k) * 0.37, 1.0))
		var y := y1 - fmod(_t * 160.0 + float(k) * 53.0, h)
		var c := Color(0.9, 0.97, 1.0, 0.35 + 0.25 * sin(float(k)))
		draw_line(Vector2(x + sin(y * 0.05) * 3.0, y), Vector2(x + sin((y + 18.0) * 0.05) * 3.0, y + 18.0), c, 1.6)
		draw_circle(Vector2(x + 6.0 * sin(_t + k), y + 30.0), 1.6, Color(1, 1, 1, 0.7))


# ------------------------------------------------------------------ sabit parçalar (bir kez)
func _ciz_sabit() -> void:
	var c := _sabit
	for gv in gecitler:
		match String(gv["tip"]):
			"zincir":
				for b in gv["basamak"]:
					_demir_raf(c, gv, int(b[0]), int(b[1]))
				for k in gv["kapak"]:
					_demir_izgara(c, int(k[0]), int(k[1]))
			"ip":
				_kiris(c, gv)
				for k in gv["kapak"]:
					_tahta_kapak(c, int(k[0]), int(k[1]))
			"kok":
				for b in gv["basamak"]:
					_kok_dugumu(c, int(b[0]), int(b[1]))
				for k in gv["kapak"]:
					_kok_kapak(c, int(k[0]), int(k[1]))
			"merdiven":
				for k in gv["kapak"]:
					_tas_kapak(c, int(k[0]), int(k[1]))
			"cikinti", "ruzgar":
				for k in gv["kapak"]:
					_tas_kapak(c, int(k[0]), int(k[1]))
			"iskele":
				_iskele(c, gv)
				for k in gv["kapak"]:
					_tahta_kapak(c, int(k[0]), int(k[1]))
			"dusus":
				for k in gv["kapak"]:
					_tahta_kapak(c, int(k[0]), int(k[1]))
		if not (gv["yumusak"] as Array).is_empty():
			var y: Array = gv["yumusak"]
			_yigin(c, int(y[0]), int(y[1]), int(y[2]))
	for y2 in propler.get("yumusak", []):
		_yigin(c, int(y2[0]), int(y2[1]), int(y2[2]))
	for kt in propler.get("kutuk", []):
		_kutuk(c, int(kt[0]), int(kt[1]), int(kt[2]))
	for s in propler.get("su", []):
		_su(c, int(s[0]), int(s[1]), int(s[2]), int(s[3]))
	for sd in propler.get("sus", []):
		_asili(c, int(sd[0]), int(sd[1]), int(sd[2]))


func _ciz_kati() -> void:
	for gv in gecitler:
		match String(gv["tip"]):
			"merdiven":
				for kc in gv["kati"]:
					_tas_orgu(_kati, int(kc[0]), int(kc[1]))
			"cikinti", "ruzgar":
				for kc in gv["kati"]:
					_cikinti_susu(_kati, int(kc[0]), int(kc[1]))


func _demir_raf(c: CanvasItem, gv: Dictionary, x: int, y: int) -> void:
	var r := Rect2(x * TS - 1.0, y * TS, TS + 2.0, 7.0)
	c.draw_rect(r.grow(1.5), MUREKKEP)
	c.draw_rect(r, R("demir"))
	c.draw_line(Vector2(r.position.x, r.position.y + 1.5), Vector2(r.end.x, r.position.y + 1.5), R("demir").lightened(0.35), 1.5)
	for k in 2:
		c.draw_circle(Vector2(x * TS + 6.0 + k * 12.0, y * TS + 4.0), 1.6, R("demir").lightened(0.5))
	# duvara yaslanan payanda: rafın duvar ucundan aşağı çapraz
	var duvar_sol: bool = x <= int(gv["x0"]) + 1
	var wx := float(int(gv["x0"])) * TS if duvar_sol else float(int(gv["x1"]) + 1) * TS
	if (duvar_sol and x == int(gv["x0"])) or (not duvar_sol and x == int(gv["x1"])):
		var a := Vector2(wx, y * TS + 18.0)
		var b := Vector2(x * TS + (TS if duvar_sol else 0.0), y * TS + 6.0)
		c.draw_line(a, b, MUREKKEP, 5.0)
		c.draw_line(a, b, R("demir").darkened(0.1), 3.0)


func _demir_izgara(c: CanvasItem, x: int, y: int) -> void:
	var r := Rect2(x * TS, y * TS, TS, 8.0)
	c.draw_rect(r.grow(1.0), MUREKKEP)
	c.draw_rect(r, R("demir").darkened(0.15))
	for k in 4:
		c.draw_line(Vector2(x * TS + 3.0 + k * 6.0, y * TS), Vector2(x * TS + 3.0 + k * 6.0, y * TS + 8.0), MUREKKEP, 1.5)
	c.draw_line(Vector2(x * TS, y * TS + 1.0), Vector2(x * TS + TS, y * TS + 1.0), R("demir").lightened(0.3), 1.2)


func _tahta_kapak(c: CanvasItem, x: int, y: int) -> void:
	var r := Rect2(x * TS, y * TS, TS, 8.0)
	c.draw_rect(r.grow(1.0), MUREKKEP)
	c.draw_rect(r, R("ahsap"))
	c.draw_line(Vector2(x * TS, y * TS + 1.5), Vector2(x * TS + TS, y * TS + 1.5), R("ahsap").lightened(0.3), 1.2)
	c.draw_line(Vector2(x * TS + TS - 1.0, y * TS), Vector2(x * TS + TS - 1.0, y * TS + 8.0), MUREKKEP, 1.2)
	c.draw_circle(Vector2(x * TS + 4.0, y * TS + 4.0), 1.2, MUREKKEP)


func _kiris(c: CanvasItem, gv: Dictionary) -> void:
	## ip merdivenin asıldığı kiriş ve iki kazık
	var tr: Array = gv["tirman"][0]
	var xa := float(tr[0]) * TS - 8.0
	var xb := float(tr[2]) * TS + 8.0
	var y := float(gv["ust"]) * TS - 5.0
	c.draw_rect(Rect2(xa, y - 4.0, xb - xa, 8.0).grow(1.5), MUREKKEP)
	c.draw_rect(Rect2(xa, y - 4.0, xb - xa, 8.0), R("ahsap"))
	c.draw_line(Vector2(xa, y - 2.5), Vector2(xb, y - 2.5), R("ahsap").lightened(0.3), 1.2)
	for px in [xa + 3.0, xb - 3.0]:
		c.draw_rect(Rect2(px - 3.0, y - 12.0, 6.0, 14.0).grow(1.2), MUREKKEP)
		c.draw_rect(Rect2(px - 3.0, y - 12.0, 6.0, 14.0), R("ahsap").darkened(0.15))


func _kok_dugumu(c: CanvasItem, x: int, y: int) -> void:
	var cx := x * TS + TS * 0.5
	var cy := y * TS + 4.0
	var poly := PackedVector2Array([Vector2(cx - 14, cy - 1), Vector2(cx - 6, cy - 5), Vector2(cx + 5, cy - 4), Vector2(cx + 14, cy),
		Vector2(cx + 8, cy + 6), Vector2(cx - 2, cy + 8), Vector2(cx - 11, cy + 5)])
	c.draw_colored_polygon(poly, R("kok"))
	poly.append(poly[0])
	c.draw_polyline(poly, MUREKKEP, 2.0)
	c.draw_line(Vector2(cx - 9, cy - 1), Vector2(cx + 8, cy - 1), R("kok").lightened(0.35), 1.2)
	c.draw_line(Vector2(cx - 3, cy + 7), Vector2(cx - 5, cy + 16), MUREKKEP, 2.2)
	c.draw_line(Vector2(cx - 3, cy + 7), Vector2(cx - 5, cy + 16), R("kok"), 1.2)


func _kok_kapak(c: CanvasItem, x: int, y: int) -> void:
	var r := Rect2(x * TS - 2.0, y * TS, TS + 4.0, 7.0)
	c.draw_rect(r.grow(1.0), MUREKKEP)
	c.draw_rect(r, R("kok"))
	for k in 3:
		c.draw_line(Vector2(x * TS + k * 8.0, y * TS + 2.0), Vector2(x * TS + k * 8.0 + 7.0, y * TS + 5.0), R("kok").lightened(0.3), 1.2)
	_yaprak(Vector2(x * TS + 12.0, y * TS), Vector2(6.0, -4.0), R("yaprak"))


func _tas_orgu(c: CanvasItem, x: int, y: int) -> void:
	## kırık merdiven sahanlığının taş örgüsü (karo zemininin üstüne harç çizgileri)
	var p := Vector2(x * TS, y * TS)
	var tas := R("tas")
	c.draw_rect(Rect2(p + Vector2(1, 1), Vector2(TS - 2, TS - 2)), tas.darkened(0.05) * Color(1, 1, 1, 0.85))
	var kay := 12.0 if (y % 2 == 0) else 0.0
	c.draw_line(p + Vector2(0, 12), p + Vector2(TS, 12), MUREKKEP, 1.4)
	c.draw_line(p + Vector2(kay + 6, 0), p + Vector2(kay + 6, 12), MUREKKEP, 1.4)
	c.draw_line(p + Vector2(fmod(kay + 18.0, TS), 12), p + Vector2(fmod(kay + 18.0, TS), TS), MUREKKEP, 1.4)
	c.draw_line(p + Vector2(1, 2), p + Vector2(TS - 2, 2), tas.lightened(0.35), 1.2)
	if level and level.cell(x, y - 1) == 0:
		c.draw_rect(Rect2(p + Vector2(-1, -2), Vector2(TS + 2, 4)), MUREKKEP)
		c.draw_rect(Rect2(p + Vector2(0, -1), Vector2(TS, 2)), tas.lightened(0.25))
		if biyom == "tamu" and (x + y) % 3 == 0:
			_kafatasi(c, p + Vector2(12, 8))


func _kafatasi(c: CanvasItem, p: Vector2) -> void:
	c.draw_circle(p, 5.0, MUREKKEP)
	c.draw_circle(p, 3.8, R("tas").lightened(0.2))
	c.draw_circle(p + Vector2(-1.6, -0.5), 1.1, MUREKKEP)
	c.draw_circle(p + Vector2(1.6, -0.5), 1.1, MUREKKEP)


func _tas_kapak(c: CanvasItem, x: int, y: int) -> void:
	var r := Rect2(x * TS, y * TS, TS, 7.0)
	c.draw_rect(r.grow(1.0), MUREKKEP)
	c.draw_rect(r, R("tas"))
	c.draw_line(Vector2(x * TS, y * TS + 1.5), Vector2(x * TS + TS, y * TS + 1.5), R("tas").lightened(0.3), 1.2)
	c.draw_line(Vector2(x * TS + 9.0, y * TS), Vector2(x * TS + 13.0, y * TS + 7.0), MUREKKEP, 1.2)


func _cikinti_susu(c: CanvasItem, x: int, y: int) -> void:
	if level == null:
		return
	var p := Vector2(x * TS, y * TS)
	if level.cell(x, y - 1) == 0:
		# üst yüz: kar / ot başlığı
		var cc := Color(0.95, 0.98, 1.0) if biyom == "kaf" else R("yaprak")
		var poly := PackedVector2Array([p + Vector2(-2, 2), p + Vector2(4, -3), p + Vector2(12, -2), p + Vector2(20, -4), p + Vector2(TS + 2, 2)])
		c.draw_colored_polygon(poly, cc)
		c.draw_polyline(poly, MUREKKEP, 1.4)
	if level.cell(x, y + 1) == 0:
		# alt yüz: buz sarkıtları / sarkan kök
		var cc2 := Color(0.7, 0.88, 1.0, 0.9) if biyom == "kaf" else R("kok")
		var n := 2 if (x + y) % 2 == 0 else 1
		for k in n:
			var bx := p.x + 5.0 + k * 11.0
			var ln := 8.0 + float((x * 7 + y * 3 + k * 5) % 9)
			var tri := PackedVector2Array([Vector2(bx - 3, p.y + TS), Vector2(bx + 3, p.y + TS), Vector2(bx, p.y + TS + ln)])
			c.draw_colored_polygon(tri, cc2)
			tri.append(tri[0])
			c.draw_polyline(tri, MUREKKEP, 1.2)


func _iskele(c: CanvasItem, gv: Dictionary) -> void:
	## kat iskelesi: tahta kalaslar, uçlarından aşağı dikmeler, iki kat arasında çapraz
	var runs := {}
	for b in gv["basamak"]:
		var y := int(b[1])
		var arr: Array = runs.get(y, [])
		arr.append(int(b[0]))
		runs[y] = arr
	var rows: Array = runs.keys()
	rows.sort()
	var tah := R("ahsap") if biyom != "kaf" else Color(0.66, 0.78, 0.86)
	for i in rows.size():
		var y: int = rows[i]
		var xs: Array = runs[y]
		xs.sort()
		var xa := float(int(xs[0])) * TS
		var xb := float(int(xs[xs.size() - 1]) + 1) * TS
		var alt: float = float(int(rows[i + 1])) * TS if i + 1 < rows.size() else float(int(gv["alt"])) * TS
		for px in [xa + 4.0, xb - 4.0]:
			c.draw_rect(Rect2(px - 3.0, y * TS + 4.0, 6.0, alt - y * TS - 4.0).grow(1.2), MUREKKEP)
			c.draw_rect(Rect2(px - 3.0, y * TS + 4.0, 6.0, alt - y * TS - 4.0), tah.darkened(0.2))
		c.draw_line(Vector2(xa + 4.0, y * TS + 8.0), Vector2(xb - 4.0, alt - 6.0), MUREKKEP, 4.0)
		c.draw_line(Vector2(xa + 4.0, y * TS + 8.0), Vector2(xb - 4.0, alt - 6.0), tah.darkened(0.1), 2.2)
		c.draw_rect(Rect2(xa - 2.0, y * TS, xb - xa + 4.0, 8.0).grow(1.5), MUREKKEP)
		for k in xs.size():
			var bx := float(int(xs[k])) * TS
			c.draw_rect(Rect2(bx, y * TS, TS - 1.0, 8.0), tah.lightened(0.05 * float(k % 2)))
			c.draw_circle(Vector2(bx + 4.0, y * TS + 4.0), 1.2, MUREKKEP)
		c.draw_line(Vector2(xa, y * TS + 1.5), Vector2(xb, y * TS + 1.5), tah.lightened(0.3), 1.2)
		if biyom != "kaf":
			c.draw_line(Vector2(xa + 2.0, y * TS + 10.0), Vector2(xa + 9.0, y * TS + 4.0), R("ip"), 2.0)


func _yigin(c: CanvasItem, x0: int, x1: int, fy: int) -> void:
	## yumuşak iniş yığını (düşüş yolunun dibi): biyoma göre saman / kar / yaprak / su / kül
	var tur: String = String(GecitGen.YUMUSAK.get(biyom, "saman"))
	var xa := float(x0) * TS - 4.0
	var xb := float(x1 + 1) * TS + 4.0
	var y := float(fy) * TS
	if tur == "su":
		_su(c, x0, x1, fy - 1, fy)
		return
	var renk := {"saman": Color(0.86, 0.72, 0.36), "kar": Color(0.94, 0.97, 1.0), "yaprak": Color(0.72, 0.42, 0.18), "kul": Color(0.4, 0.37, 0.36)}
	var cc: Color = renk.get(tur, Color(0.8, 0.7, 0.4))
	var pts := PackedVector2Array()
	var n := 10
	for k in n + 1:
		var t := float(k) / float(n)
		pts.append(Vector2(lerpf(xa, xb, t), y - sin(t * PI) * 13.0 - (2.0 if k % 2 == 0 else 0.0)))
	var poly := pts.duplicate()
	poly.append(Vector2(xb, y + 2.0))
	poly.append(Vector2(xa, y + 2.0))
	c.draw_colored_polygon(poly, cc)
	c.draw_polyline(pts, MUREKKEP, 2.0)
	var rr := RandomNumberGenerator.new()
	rr.seed = x0 * 31 + fy
	for k in 14:
		var px := rr.randf_range(xa + 4.0, xb - 4.0)
		var t2 := (px - xa) / (xb - xa)
		var top := y - sin(t2 * PI) * 12.0
		var py := rr.randf_range(top + 2.0, y)
		match tur:
			"saman":
				c.draw_line(Vector2(px, py), Vector2(px + rr.randf_range(-6, 6), py - rr.randf_range(2, 6)), cc.darkened(0.35), 1.2)
			"yaprak":
				_yaprak(Vector2(px, py), Vector2(rr.randf_range(-5, 5), -3.0), Color(0.75, 0.3 + rr.randf() * 0.3, 0.12))
			"kar":
				c.draw_line(Vector2(px - 3, py), Vector2(px + 3, py), Color(0.7, 0.82, 0.95), 1.2)
			"kul":
				if rr.randf() < 0.3:
					c.draw_circle(Vector2(px, py), 1.4, Color(1.0, 0.5, 0.15))
				else:
					c.draw_line(Vector2(px - 2, py), Vector2(px + 2, py), cc.lightened(0.3), 1.2)


func _kutuk(c: CanvasItem, x0: int, x1: int, y: int) -> void:
	## "=" köprü: Ötüken devrik ağaç gövdesi, Bozkır ahşap kiriş, Kaf buz köprü, Şahmeran kaburga, Tamu demir kiriş
	var xa := float(x0) * TS - 4.0
	var xb := float(x1 + 1) * TS + 4.0
	var yy := float(y) * TS
	match biyom:
		"otuken":
			var r := Rect2(xa, yy - 2.0, xb - xa, 16.0)
			c.draw_rect(r.grow(1.5), MUREKKEP)
			c.draw_rect(r, R("kok"))
			c.draw_line(Vector2(xa, yy + 1.0), Vector2(xb, yy + 1.0), R("kok").lightened(0.35), 2.0)
			for k in int((xb - xa) / 14.0):
				var px := xa + 7.0 + k * 14.0
				c.draw_line(Vector2(px, yy + 4.0), Vector2(px + 8.0, yy + 6.0), MUREKKEP, 1.2)
			c.draw_circle(Vector2(xb, yy + 6.0), 8.0, MUREKKEP)
			c.draw_circle(Vector2(xb, yy + 6.0), 6.5, R("vurgu"))
			c.draw_arc(Vector2(xb, yy + 6.0), 3.5, 0.0, TAU, 10, R("kok"), 1.2)
			_yaprak(Vector2(xa + 10.0, yy - 2.0), Vector2(7.0, -6.0), R("yaprak"))
		"kaf":
			var r2 := Rect2(xa, yy - 1.0, xb - xa, 10.0)
			c.draw_rect(r2.grow(1.2), MUREKKEP)
			c.draw_rect(r2, Color(0.7, 0.86, 0.98, 0.92))
			c.draw_line(Vector2(xa, yy + 1.0), Vector2(xb, yy + 1.0), Color(1, 1, 1), 1.5)
			for k in int((xb - xa) / 20.0):
				var px2 := xa + 10.0 + k * 20.0
				c.draw_line(Vector2(px2, yy), Vector2(px2 + 5.0, yy + 9.0), Color(0.45, 0.6, 0.78), 1.0)
				var tri := PackedVector2Array([Vector2(px2 - 3, yy + 9), Vector2(px2 + 3, yy + 9), Vector2(px2, yy + 18 + (k % 3) * 4)])
				c.draw_colored_polygon(tri, Color(0.75, 0.9, 1.0, 0.85))
		"sahmeran":
			c.draw_line(Vector2(xa, yy + 3.0), Vector2(xb, yy + 3.0), MUREKKEP, 8.0)
			c.draw_line(Vector2(xa, yy + 3.0), Vector2(xb, yy + 3.0), R("tas").lightened(0.4), 5.0)
			for k in int((xb - xa) / 12.0):
				var px3 := xa + 6.0 + k * 12.0
				c.draw_arc(Vector2(px3, yy + 10.0), 7.0, PI * 0.1, PI * 0.9, 6, MUREKKEP, 3.4)
				c.draw_arc(Vector2(px3, yy + 10.0), 7.0, PI * 0.1, PI * 0.9, 6, R("tas").lightened(0.5), 1.6)
		"tamu":
			var r3 := Rect2(xa, yy - 1.0, xb - xa, 9.0)
			c.draw_rect(r3.grow(1.5), MUREKKEP)
			c.draw_rect(r3, R("demir"))
			c.draw_line(Vector2(xa, yy + 1.0), Vector2(xb, yy + 1.0), R("demir").lightened(0.4), 1.2)
			for k in int((xb - xa) / 12.0):
				c.draw_circle(Vector2(xa + 6.0 + k * 12.0, yy + 4.0), 1.4, R("demir").lightened(0.5))
				c.draw_line(Vector2(xa + k * 12.0, yy + 8.0), Vector2(xa + 6.0 + k * 12.0, yy + 14.0), MUREKKEP, 2.0)
		_:
			var r4 := Rect2(xa, yy - 1.0, xb - xa, 10.0)
			c.draw_rect(r4.grow(1.5), MUREKKEP)
			c.draw_rect(r4, R("ahsap"))
			c.draw_line(Vector2(xa, yy + 1.0), Vector2(xb, yy + 1.0), R("ahsap").lightened(0.35), 1.4)
			for k in int((xb - xa) / 24.0) + 1:
				c.draw_line(Vector2(xa + k * 24.0, yy - 1.0), Vector2(xa + k * 24.0, yy + 9.0), MUREKKEP, 1.2)


func _su(c: CanvasItem, x0: int, x1: int, ys: int, dip: int) -> void:
	var xa := float(x0) * TS
	var xb := float(x1 + 1) * TS
	var top := float(ys) * TS + 6.0
	var bot := float(dip) * TS
	var su := Color(0.18, 0.5, 0.52, 0.55) if biyom == "sahmeran" else Color(0.25, 0.42, 0.6, 0.5)
	c.draw_rect(Rect2(xa, top, xb - xa, bot - top), su)
	c.draw_line(Vector2(xa, top), Vector2(xb, top), Color(0.75, 1.0, 0.95, 0.85), 2.0)
	for k in int((xb - xa) / 18.0):
		c.draw_line(Vector2(xa + 4.0 + k * 18.0, top + 5.0), Vector2(xa + 12.0 + k * 18.0, top + 5.0), Color(0.8, 1.0, 1.0, 0.45), 1.2)


func _asili(c: CanvasItem, x: int, y: int, tavan: int) -> void:
	## "d": tavandan sarkan süs (biyoma göre fener, kemik çıngırak, buz sarkıtı, ışıyan mantar salkımı)
	var px := float(x) * TS + TS * 0.5
	var ya := float(tavan) * TS
	var yb := float(y) * TS + TS * 0.5
	c.draw_line(Vector2(px, ya), Vector2(px, yb - 6.0), MUREKKEP, 1.6)
	match biyom:
		"kaf":
			var tri := PackedVector2Array([Vector2(px - 5, ya), Vector2(px + 5, ya), Vector2(px, yb + 8.0)])
			c.draw_colored_polygon(tri, Color(0.75, 0.9, 1.0, 0.9))
			tri.append(tri[0])
			c.draw_polyline(tri, MUREKKEP, 1.4)
		"tamu":
			for k in 3:
				c.draw_line(Vector2(px - 6 + k * 6, yb - 6.0), Vector2(px - 6 + k * 6, yb + 6.0 + k * 2), MUREKKEP, 3.4)
				c.draw_line(Vector2(px - 6 + k * 6, yb - 6.0), Vector2(px - 6 + k * 6, yb + 6.0 + k * 2), R("tas"), 1.8)
			_kafatasi(c, Vector2(px, yb - 6.0))
		"sahmeran":
			for k in 3:
				c.draw_circle(Vector2(px - 5 + k * 5, yb - 2 + k % 2 * 4), 3.2, MUREKKEP)
				c.draw_circle(Vector2(px - 5 + k * 5, yb - 2 + k % 2 * 4), 2.2, R("vurgu"))
		_:
			c.draw_rect(Rect2(px - 6, yb - 8, 12, 14).grow(1.4), MUREKKEP)
			c.draw_rect(Rect2(px - 6, yb - 8, 12, 14), Color(1.0, 0.75, 0.35))
			c.draw_line(Vector2(px - 6, yb - 8), Vector2(px + 6, yb - 8), R("ahsap"), 3.0)
			c.draw_line(Vector2(px - 6, yb + 6), Vector2(px + 6, yb + 6), R("ahsap"), 3.0)
