class_name SimsekKesikFX
extends Node2D
## v25 Yıldırım Kılıcı çizimleri (Player._yk_*): iki kip.
##   "line"  Şimşek Çekişi (zincir bitirişi) ve Yıldırım Hamlesi: oyuncunun geçtiği yol boyunca ekranı bir an ikiye
##           bölen kesik çizgisi. Baş 2 karede a → b koşar; beyaz kılcal çekirdek + mavi parıltı (toplamalı), iki yanında
##           ince mürekkep kenarı (kesiğin "yarığı": söndükçe iki kenar birbirinden açılır), çizgi boyunca titreyen
##           kısa şimşek kılcalları; ekranın iki ucuna uzanan soluk ince yarık 0,12 sn'de söner.
##   "arc"   Çekiş (iaido) kesiğinin şimşek parlaklığında hilali: bıçak ucunun geçtiği noktalar (pts) üstünde, ön uçta
##           kalın, kuyrukta kıl inceliğinde parlak yay + yay boyunca çıtırdayan kılcallar; 0,16 sn'de söner.
## Gerçek zamanlı akar (vuruş duraklamasında da söner; process_mode ALWAYS, delta / zaman ölçeği).

var mode := "line"
var a := Vector2.ZERO
var b := Vector2(100, 0)
var pts := PackedVector2Array()   # "arc" kipi: uç yolu (dünya)
var col := Color(0.62, 0.86, 1.0)
var life := 0.34
var power := 1.0                  # kalınlık / parlaklık çarpanı (Yıldırım Hamlesi 1,3)
var _t := 0.0
var _cracks: Array = []           # [çoklu nokta, doğuş payı] kılcal şimşekler (yerel)
var _flick := 0
var _ink: Node2D
var holding := false              # "arc" canlı kip: Player uç yolunu ekledikçe uzar; release() ile sönmeye başlar
var _held_t := 0.0


static func line(p0: Vector2, p1: Vector2, c: Color, pw := 1.0) -> SimsekKesikFX:
	if FX.root == null:
		return null
	var f := SimsekKesikFX.new()
	f.mode = "line"
	f.a = p0
	f.b = p1
	f.col = c
	f.power = pw
	FX.root.add_child(f)
	return f


static func arc(path: PackedVector2Array, c: Color, pw := 1.0) -> SimsekKesikFX:
	if FX.root == null or path.size() < 3:
		return null
	var f := SimsekKesikFX.new()
	f.mode = "arc"
	f.pts = path
	f.col = c
	f.power = pw
	f.life = 0.16
	FX.root.add_child(f)
	return f


static func arc_live(c: Color, pw := 1.0) -> SimsekKesikFX:
	## Canlı yay: bıçak süpürürken noktalar eklenir (add_point), savuruş vuruş evresinden çıkınca release()
	if FX.root == null:
		return null
	var f := SimsekKesikFX.new()
	f.mode = "arc"
	f.col = c
	f.power = pw
	f.life = 0.16
	f.holding = true
	FX.root.add_child(f)
	return f


func add_point(p: Vector2) -> void:
	if pts.is_empty() or pts[pts.size() - 1].distance_to(p) > 1.2:
		pts.append(p)


func release() -> void:
	if holding:
		holding = false
		_t = 0.0
		_make_cracks()


func _ready() -> void:
	process_mode = Node.PROCESS_MODE_ALWAYS
	top_level = true
	z_index = 64
	var m := CanvasItemMaterial.new()
	m.blend_mode = CanvasItemMaterial.BLEND_MODE_ADD
	m.light_mode = CanvasItemMaterial.LIGHT_MODE_UNSHADED
	material = m
	# mürekkep kenarı ayrı düğümde (normal karışım: koyu çizgi toplamalı katmanda görünmez)
	_ink = Node2D.new()
	_ink.z_index = -1
	_ink.z_as_relative = true
	_ink.draw.connect(_draw_ink)
	add_child(_ink)
	_make_cracks()


func _make_cracks() -> void:
	_cracks.clear()
	if mode == "line":
		var d := b - a
		var L := d.length()
		var n := clampi(int(L / 22.0), 3, 9)
		var nrm := Vector2(-d.y, d.x).normalized()
		for i in n:
			var u := (float(i) + randf_range(0.2, 0.8)) / float(n)
			var p := a + d * u
			var side := -1.0 if i % 2 == 0 else 1.0
			var tip := p + nrm * side * randf_range(6.0, 15.0) * power + d.normalized() * randf_range(-8.0, 8.0)
			_cracks.append([LightningFX._bolt(p, tip, 0.3, 3), u])
	else:
		if pts.size() < 4:
			return
		var n2 := clampi(pts.size() / 5, 2, 6)
		for i in n2:
			var j := clampi(int(float(i + 1) / float(n2 + 1) * pts.size()), 1, pts.size() - 2)
			var p2 := pts[j]
			var tan := (pts[j + 1] - pts[j - 1]).normalized()
			var nr := Vector2(-tan.y, tan.x)
			var tip2 := p2 + nr * randf_range(-12.0, 12.0) + tan * randf_range(2.0, 8.0)
			_cracks.append([LightningFX._bolt(p2, tip2, 0.32, 3), float(j) / float(pts.size())])


func _process(delta: float) -> void:
	var rd := delta / maxf(0.05, Engine.time_scale)
	if holding:
		# canlı yay: savuruş bırakmadan bittiyse (iptal) en geç 0,5 sn sonra kendiliğinden söner
		_held_t += rd
		if _held_t > 0.5:
			release()
		_flick += 1
		if _flick % 3 == 0:
			_make_cracks()
		queue_redraw()
		return
	_t += rd
	if _t >= life:
		queue_free()
		return
	_flick += 1
	if _flick % 4 == 0 and _t < life * 0.6:
		_make_cracks()   # kılcallar titreşir (yeniden atılır)
	queue_redraw()
	_ink.queue_redraw()


func _head() -> float:
	## çizginin başı: 2 karede (0,035 sn) a → b koşar
	return clampf(_t / 0.035, 0.0, 1.0)


func _fade() -> float:
	var u := clampf((_t - 0.04) / maxf(0.01, life - 0.04), 0.0, 1.0)
	return 1.0 - u * u * (3.0 - 2.0 * u)


func _draw() -> void:
	var f := _fade()
	if f <= 0.0:
		return
	if mode == "line":
		var h := _head()
		var e := a.lerp(b, h)
		var d := (b - a).normalized()
		# ekranı bölen soluk yarık: iki uca uzanır, çok hızlı söner
		var sf := clampf(1.0 - _t / 0.12, 0.0, 1.0)
		if sf > 0.0:
			draw_line(a - d * 420.0, e + d * 420.0 * h, Color(col.lightened(0.5), 0.22 * sf), 1.2, true)
		# geniş parıltı, renkli şerit, beyaz çekirdek (çekirdek söndükçe incelir)
		draw_line(a, e, Color(col, 0.22 * f), 11.0 * power * (0.6 + 0.4 * f), true)
		draw_line(a, e, Color(col.lightened(0.2), 0.55 * f), 4.5 * power * f + 0.8, true)
		draw_line(a, e, Color(1.0, 1.0, 1.0, 0.95 * f), maxf(0.8, 2.2 * power * f), true)
		# baş parıltısı (koşarken)
		if h < 1.0:
			draw_circle(e, 2.6 * power, Color(1.0, 1.0, 1.0, 0.85 * f))
	else:
		var n := pts.size()
		if n < 2:
			return
		for i in range(1, n):
			var q := float(i) / float(n - 1)          # 0 kuyruk → 1 ön uç
			var w := (0.4 + 3.6 * pow(q, 1.4)) * power * f
			draw_line(pts[i - 1], pts[i], Color(col, 0.35 * f), w * 2.6, true)
			draw_line(pts[i - 1], pts[i], Color(1.0, 1.0, 1.0, (0.35 + 0.6 * q) * f), maxf(0.6, w), true)
	# kılcal şimşekler
	for c in _cracks:
		var cp: PackedVector2Array = c[0]
		if mode == "line" and float(c[1]) > _head():
			continue
		draw_polyline(cp, Color(col.lightened(0.3), 0.7 * f), 1.4, true)
		draw_polyline(cp, Color(1.0, 1.0, 1.0, 0.85 * f), 0.7, true)


func _draw_ink() -> void:
	## mürekkep kenarları: çizginin iki yanında koyu ince fırça; söndükçe birbirinden açılır (yarık)
	if mode != "line":
		return
	var f := _fade()
	if f <= 0.0:
		return
	var h := _head()
	var e := a.lerp(b, h)
	var d := (b - a).normalized()
	var nrm := Vector2(-d.y, d.x)
	var gap := (2.6 + 3.5 * (1.0 - f)) * power
	var ic := Color(0.04, 0.03, 0.08, 0.75 * f)
	_ink.draw_line(a + nrm * gap, e + nrm * gap * 0.6, ic, 1.3, true)
	_ink.draw_line(a - nrm * gap, e - nrm * gap * 0.6, ic, 1.3, true)
