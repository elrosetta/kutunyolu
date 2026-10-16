class_name LightningFX
extends Node2D
## Şimşek (Gök Asası zinciri, gök gürlemesi): orta nokta yer değiştirmesiyle üretilen ana kanal
## (adım başına sınırlı sapma; salt rastgele zikzak değil), boyun %30-70'inden çatallanan 2-4 dal
## (her biri daha ince ve kısa). Üç katman: 1 px beyaz çekirdek, 2-3 px renkli parıltı (toplamalı),
## soluk geniş hale. 3 kez titrer (dallar yeniden atılır, şiddet %100 → %60 → %85 → 0) ~0,18 s içinde.
## Piksel keskin: her katman tam piksel karelerle (draw_rect) çizilir, kenar yumuşatma yok.
## Çizim yalnızca evre değişince yenilenir (piksel kümeleri önbelleklenir).
## Stil v2 (ink): aynı kanal ve dallar piksel kümesine dökülmez; incelen şerit fırça çizgileri (InkDraw.line)
## olarak çizilir: geniş soluk yıkama + renkli fırça + beyaz kılcal çekirdek, dal uçları incelir.

var a := Vector2.ZERO
var b := Vector2(60, 0)
var col := Color(0.7, 0.85, 1.0)
var life := 0.18
var width := 1          # 1: zincir şimşeği; 2: gök gürlemesi (2 px çekirdek, 4 px parıltı, 6 px hale)
var branches := -1      # -1: 2-4 arası rastgele
var _t := 0.0
var _phase := -1
var _main := PackedVector2Array()
var _core: Array = []    # PackedVector2Array listesi: ana + dallar (piksel kümeleri)
var _glow: Array = []
var _halo := PackedVector2Array()
var _branch_from := 0    # dalların ana kanal üzerindeki başlangıç indeksleri için tohum
var ink := FX.ink()
var _lines: Array = []   # v2: [çoklu nokta, kalınlık çarpanı] (ana kanal 1, dal 0,55, dalcık 0,35)

const PHASES := [0.0, 0.3, 0.55, 0.8, 0.9]
const INTENS := [1.0, 0.6, 0.85, 0.45, 0.2]


func _ready() -> void:
	z_index = 65
	top_level = true
	var m := CanvasItemMaterial.new()
	m.blend_mode = CanvasItemMaterial.BLEND_MODE_ADD
	m.light_mode = CanvasItemMaterial.LIGHT_MODE_UNSHADED
	material = m
	if ink:
		InkDraw.prep(self)
	_main = _bolt(a, b, 0.24, _depth(a.distance_to(b)))
	_rebuild_branches()


static func _depth(len_px: float) -> int:
	## Alt bölme derinliği: parçalar ~6-10 px kalacak biçimde
	var d := 1
	var seg := len_px
	while seg > 9.0 and d < 7:
		seg *= 0.5
		d += 1
	return d


static func _bolt(p0: Vector2, p1: Vector2, frac: float, depth: int) -> PackedVector2Array:
	## Orta nokta yer değiştirmesi: her düzeyde parçanın orta noktası, parça boyunun en çok frac katı
	## kadar dik yönde kaydırılır; derinlik arttıkça sapma azalır → doğal, sınırlı kırıklar.
	var pts := PackedVector2Array([p0, p1])
	for d in depth:
		var out := PackedVector2Array()
		var f := frac * pow(0.72, float(d))
		for i in pts.size() - 1:
			var s := pts[i]
			var e := pts[i + 1]
			var seg := e - s
			var nrm := Vector2(-seg.y, seg.x).normalized()
			var mid := (s + e) * 0.5 + nrm * randf_range(-1.0, 1.0) * seg.length() * f
			out.append(s)
			out.append(mid)
		out.append(pts[pts.size() - 1])
		pts = out
	return pts


func _rebuild_branches() -> void:
	_core.clear()
	_glow.clear()
	_lines.clear()
	if ink:
		_lines.append([_main, 1.0])
	var main_px := _rasterize([_main]) if not ink else PackedVector2Array()
	_core.append(main_px)
	var n := branches if branches >= 0 else 2 + randi() % 3
	var dir := (b - a).normalized()
	var total := a.distance_to(b)
	var sgn := 1.0 if randf() < 0.5 else -1.0
	for i in n:
		var idx := int(lerpf(0.3, 0.7, randf()) * float(_main.size() - 1))
		var start := _main[idx]
		sgn = -sgn
		var bd := dir.rotated(sgn * randf_range(0.35, 1.05))
		var blen := total * randf_range(0.16, 0.36)
		var endp := start + bd * blen
		var pts := _bolt(start, endp, 0.3, maxi(1, _depth(blen)))
		var lines := [pts]
		# ikincil dalcık: dalın ortasından kısa bir çatal
		if randf() < 0.5 and pts.size() > 4:
			var j := pts.size() / 2
			var s2 := pts[j]
			var e2 := s2 + bd.rotated(-sgn * randf_range(0.5, 1.0)) * blen * 0.35
			lines.append(_bolt(s2, e2, 0.3, 2))
		if ink:
			_lines.append([pts, 0.55])
			if lines.size() > 1:
				_lines.append([lines[1], 0.35])
			continue
		_core.append(_rasterize(lines))
	if ink:
		return
	# parıltı: ana kanal 1 px genişletilir (dallar yarım parıltı: yalnız çekirdek + hale yok)
	var glow_main := _dilate(main_px, 1)
	_glow.append(glow_main)
	for i in range(1, _core.size()):
		_glow.append(_dilate(_core[i], 1) if width >= 2 else PackedVector2Array())
	_halo = _dilate(glow_main, 1)


func _rasterize(lines: Array) -> PackedVector2Array:
	## Çoklu çizgileri tam piksel adımlarına döker (DDA), tekrarları atar
	var seen: Dictionary = {}
	var out := PackedVector2Array()
	for pts in lines:
		var n: int = pts.size()
		for i in n - 1:
			var s: Vector2 = pts[i]
			var e: Vector2 = pts[i + 1]
			var steps := maxi(1, int(ceil(maxf(absf(e.x - s.x), absf(e.y - s.y)))))
			for k in steps + 1:
				var p := (s + (e - s) * (float(k) / float(steps))).floor()
				var key := Vector2i(p)
				if seen.has(key):
					continue
				seen[key] = true
				out.append(p)
				if width >= 2:
					# 2 px çekirdek: sağ ve alt komşu
					for o: Vector2i in [Vector2i(1, 0), Vector2i(0, 1), Vector2i(1, 1)]:
						var k2: Vector2i = key + o
						if not seen.has(k2):
							seen[k2] = true
							out.append(Vector2(k2))
	return out


static func _dilate(src: PackedVector2Array, r: int) -> PackedVector2Array:
	var seen: Dictionary = {}
	var out := PackedVector2Array()
	for p in src:
		var c := Vector2i(p)
		for dy in range(-r, r + 1):
			for dx in range(-r, r + 1):
				var k := c + Vector2i(dx, dy)
				if not seen.has(k):
					seen[k] = true
					out.append(Vector2(k))
	return out


func _process(delta: float) -> void:
	_t += delta
	if _t >= life:
		queue_free()
		return
	var k := _t / life
	var ph := 0
	for i in PHASES.size():
		if k >= PHASES[i]:
			ph = i
	if ph != _phase:
		if ph == 1 or ph == 2:
			_rebuild_branches()
		_phase = ph
		queue_redraw()


func _draw() -> void:
	if ink:
		_ink_draw()
		return
	var I: float = INTENS[maxi(0, _phase)]
	var halo := Color(col.r * 0.22 * I, col.g * 0.22 * I, col.b * 0.26 * I, 1.0)
	var glow := Color(col.r * 0.9 * I, col.g * 0.9 * I, col.b * 1.0 * I, 1.0)
	var core := Color(1.0 * I, 1.0 * I, 1.0 * I, 1.0)
	var branch_core := Color(0.85 * I, 0.9 * I, 1.0 * I, 1.0)
	var one := Vector2.ONE
	for p in _halo:
		draw_rect(Rect2(p, one), halo)
	for g in _glow:
		for p in g:
			draw_rect(Rect2(p, one), glow)
	for i in _core.size():
		var c := core if i == 0 else branch_core
		for p in _core[i]:
			draw_rect(Rect2(p, one), c)


func _ink_draw() -> void:
	var I: float = INTENS[maxi(0, _phase)]
	var w := float(width)
	for L in _lines:
		var pts: PackedVector2Array = L[0]
		var k: float = L[1]
		# geniş soluk yıkama, renkli fırça, beyaz kılcal çekirdek (dal uçları incelir)
		InkDraw.line(self, pts, 9.0 * w * k, 3.0 * w * k, Color(col.r * 0.3 * I, col.g * 0.3 * I, col.b * 0.4 * I, 1.0))
		InkDraw.line(self, pts, 4.2 * w * k, 1.0 * w * k, Color(col.r * 1.1 * I, col.g * 1.1 * I, col.b * 1.2 * I, 1.0))
		InkDraw.line(self, pts, 1.8 * w * k, 0.5, Color(1.3 * I, 1.3 * I, 1.35 * I, 1.0))
