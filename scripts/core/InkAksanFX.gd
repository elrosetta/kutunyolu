class_name InkAksanFX
extends Node2D
## v27 mürekkep vurguları (SanatAnim): savuruşun ritmini çizen küçük, kısa ömürlü fırça işaretleri. Düşmanı örtmesin diye
## hepsi ince, 0,2-0,45 sn'de söner, çoğu bıçağın ucunda / takip yönünde (düşmanın ötesinde) doğar.
##   "fiske"   bıçak ucundan savrulan 2-4 sivri mürekkep damlası (hançer, kılıç takibi): uçar, yerçekimiyle eğilir, incelir
##   "nokta"   temas / takip noktasında 1-3 fırça noktası (yuvarlak değil: kenarı titrek, kuyruklu)
##   "firca"   bitirişin hat (hüsnühat) fırçası: bıçak ucunun son yayı boyunca, başta bastırılmış kalın, sonda kuru,
##             kıllarına ayrılan tek darbe; hilalin dış yanında, 1 kare gecikmeli çizilir
##   "pence"   Kurt Pençeleri: üç paralel sivri tırmık çizgisi
##   "catlak"  ağır çakma: yerde dallanan kısa çatlak çizgileri (zemine yapışık)
##   "yildiz"  kırbaç şaklaması: uçta 5 kısa ışınsal çizgi + nokta
##   "parilti" kına koyma "çıt"ı: kabzada yatay ince çizgi + küçük beyaz parıltı
##   "kiris"   yay bırakışı: gezde iki ayrılan kısa çizgi (kiriş şaklaması)
##   "girdap"  Rüzgâr / Ay: bitirişte bıçak ucunun çevresinde açılan ince hilal fırçası
## Gerçek zamanlı akar (vuruş duraklamasında da söner).

const INK := Color(0.07, 0.06, 0.08)
var kind := "fiske"
var col := Color(1, 1, 1)
var life := 0.3
var _t := 0.0
var els: Array = []     # her öğe: {"p": PackedVector2Array (yerel), "w": Array, "v": Vector2, "d": gecikme, "r": yarıçap}
var _rng := RandomNumberGenerator.new()


static func _new(k: String, pos: Vector2, c: Color, lf: float, z := 57) -> InkAksanFX:
	if FX.root == null:
		return null
	var f := InkAksanFX.new()
	f.kind = k
	f.col = c
	f.life = lf
	f.position = pos
	f.z_index = z
	f._rng.randomize()
	FX.root.add_child(f)
	return f


static func fiske(pos: Vector2, dir: Vector2, c: Color, n := 3, size := 1.0) -> InkAksanFX:
	var f := _new("fiske", pos, c, 0.28)
	if f == null:
		return null
	var d := dir.normalized() if dir.length() > 0.01 else Vector2.RIGHT
	for i in n:
		var a := f._rng.randf_range(-0.55, 0.55)
		var sp := f._rng.randf_range(110.0, 200.0) * size
		f.els.append({"o": Vector2.ZERO, "v": d.rotated(a) * sp + Vector2(0, -30.0), "len": f._rng.randf_range(4.0, 7.5) * size,
			"w": f._rng.randf_range(1.1, 1.8) * size, "d": 0.012 * i})
	return f


static func nokta(pos: Vector2, dir: Vector2, c: Color, n := 2, size := 1.0) -> InkAksanFX:
	var f := _new("nokta", pos, c, 0.34)
	if f == null:
		return null
	var d := dir.normalized() if dir.length() > 0.01 else Vector2.RIGHT
	for i in n:
		f.els.append({"o": d * (3.0 + 4.0 * i) * size + d.orthogonal() * f._rng.randf_range(-3.0, 3.0), "r": (1.9 - 0.45 * i) * size,
			"v": d * f._rng.randf_range(10.0, 26.0), "d": 0.02 * i, "dir": d})
	return f


static func firca(path: PackedVector2Array, c: Color, width := 3.0, out := Vector2.ZERO) -> InkAksanFX:
	## path: dünya noktaları (kuyruk → ön uç); out: hilalin dış yönüne kaydırma
	if path.size() < 3:
		return null
	var o := path[0]
	var f := _new("firca", o, c, 0.42, 56)
	if f == null:
		return null
	var loc := PackedVector2Array()
	for p in path:
		loc.append(p - o + out)
	f.els.append({"p": loc, "w": width, "d": 0.017})
	return f


static func pence(pos: Vector2, dir: Vector2, c: Color, size := 1.0) -> InkAksanFX:
	var f := _new("pence", pos, c, 0.26, 59)
	if f == null:
		return null
	var d := dir.normalized() if dir.length() > 0.01 else Vector2.RIGHT
	var n := d.orthogonal()
	for i in 3:
		var off := n * (float(i) - 1.0) * 4.5 * size
		f.els.append({"a": off - d * 9.0 * size, "b": off + d * (9.0 + 2.0 * (1 - absi(i - 1))) * size, "w": 1.6 * size, "d": 0.018 * i})
	return f


static func catlak(pos: Vector2, facing: int, c: Color, power := 1.0) -> InkAksanFX:
	var f := _new("catlak", pos, c, 0.5, 2)
	if f == null:
		return null
	var n := 4 + int(power * 2.0)
	for i in n:
		var side := -1.0 if i % 2 == 0 else 1.0
		var ln := f._rng.randf_range(8.0, 18.0) * power * (1.25 if side == float(facing) else 0.85)
		var pts := PackedVector2Array([Vector2.ZERO])
		var p := Vector2(side * f._rng.randf_range(1.0, 4.0), 0.0)
		var steps := 3
		for s in steps:
			p += Vector2(side * ln / steps, f._rng.randf_range(-1.4, 1.2))
			pts.append(p)
		f.els.append({"p": pts, "w": f._rng.randf_range(1.0, 1.8), "d": 0.01 * i})
	return f


static func yildiz(pos: Vector2, dir: Vector2, c: Color, size := 1.0) -> InkAksanFX:
	var f := _new("yildiz", pos, c, 0.2, 59)
	if f == null:
		return null
	var d := dir.normalized() if dir.length() > 0.01 else Vector2.RIGHT
	for i in 5:
		var a := -1.0 + 0.5 * i + f._rng.randf_range(-0.12, 0.12)
		f.els.append({"dir": d.rotated(a), "len": f._rng.randf_range(5.0, 9.0) * size, "d": 0.0})
	return f


static func parilti(pos: Vector2, facing: int, c: Color) -> InkAksanFX:
	var f := _new("parilti", pos, c, 0.24, 60)
	if f != null:
		f.els.append({"f": float(facing)})
	return f


static func kiris(pos: Vector2, facing: int, c: Color) -> InkAksanFX:
	var f := _new("kiris", pos, c, 0.18, 60)
	if f != null:
		f.els.append({"f": float(facing)})
	return f


static func girdap(pos: Vector2, facing: int, c: Color, r := 14.0) -> InkAksanFX:
	var f := _new("girdap", pos, c, 0.32, 56)
	if f != null:
		f.els.append({"f": float(facing), "r": r})
	return f


func _ready() -> void:
	process_mode = Node.PROCESS_MODE_ALWAYS


func _process(delta: float) -> void:
	var d := delta / maxf(0.05, Engine.time_scale)
	_t += d
	if _t >= life:
		queue_free()
		return
	if kind == "fiske" or kind == "nokta":
		for e in els:
			if _t >= float(e["d"]):
				e["o"] = (e["o"] as Vector2) + (e["v"] as Vector2) * d
				e["v"] = (e["v"] as Vector2) * (1.0 - 5.0 * d) + Vector2(0, 260.0 * d if kind == "fiske" else 0.0)
	queue_redraw()


func _fade() -> float:
	var u := _t / life
	return clampf(1.0 - pow(u, 1.6), 0.0, 1.0)


func _taper(pts: PackedVector2Array, w0: float, w1: float, c: Color) -> void:
	## Sivrilen fırça gövdesi: w0 baş, w1 son. Her parça ayrı dörtgen (draw_primitive: üçgenleme yok, kıvrık yolda da
	## bozulmaz)
	var n := pts.size()
	if n < 2:
		return
	var left := PackedVector2Array()
	var right := PackedVector2Array()
	for i in n:
		var q := float(i) / float(n - 1)
		var t := (pts[mini(i + 1, n - 1)] - pts[maxi(i - 1, 0)]).normalized()
		var nn := t.orthogonal() * lerpf(w0, w1, q) * 0.5
		left.append(pts[i] + nn)
		right.append(pts[i] - nn)
	var cols := PackedColorArray([c, c, c, c])
	var uvs := PackedVector2Array([Vector2.ZERO, Vector2.ZERO, Vector2.ZERO, Vector2.ZERO])
	for i in range(n - 1):
		draw_primitive(PackedVector2Array([left[i], left[i + 1], right[i + 1], right[i]]), cols, uvs)


func _draw() -> void:
	var f := _fade()
	match kind:
		"fiske":
			for e in els:
				if _t < float(e["d"]):
					continue
				var o: Vector2 = e["o"]
				var v: Vector2 = e["v"]
				var dir := v.normalized() if v.length() > 1.0 else Vector2.RIGHT
				var ln := float(e["len"]) * (0.6 + 0.4 * f)
				var pts := PackedVector2Array([o - dir * ln, o - dir * ln * 0.45, o])
				_taper(pts, 0.2, float(e["w"]) * f + 0.3, Color(INK, 0.9 * f))
				draw_circle(o, float(e["w"]) * 0.55 * f + 0.2, Color(INK, 0.9 * f))
		"nokta":
			for e in els:
				if _t < float(e["d"]):
					continue
				var o: Vector2 = e["o"]
				var r := float(e["r"]) * (0.7 + 0.3 * minf(1.0, _t / 0.04))
				var dd: Vector2 = e["dir"]
				draw_circle(o, r, Color(INK, 0.88 * f))
				# kuyruk: fırçanın kalkışı
				_taper(PackedVector2Array([o - dd * r * 0.3, o - dd * r * 2.4]), r * 1.4, 0.2, Color(INK, 0.6 * f))
				draw_circle(o + dd.orthogonal() * r * 0.35 - dd * r * 0.2, r * 0.35, Color(col.lightened(0.2), 0.35 * f))
		"firca":
			for e in els:
				if _t < float(e["d"]):
					continue
				var p: PackedVector2Array = e["p"]
				var n := p.size()
				# ön uçtan kuyruğa koşarak açılır (0,05 sn), sonra kurur
				var grow := clampf((_t - float(e["d"])) / 0.05, 0.0, 1.0)
				var m := maxi(2, int(ceil(n * grow)))
				var seg := PackedVector2Array()
				for i in range(n - m, n):
					seg.append(p[i])
				var w := float(e["w"])
				# kuyruk kuru ve ince (kıllara ayrılır), ortası dolgun, baş sivri
				var mid := int(seg.size() / 2.0)
				var a := seg.slice(0, mid + 1)
				var b := seg.slice(mid, seg.size())
				_taper(a, 0.25, w * f, Color(INK, 0.82 * f))
				_taper(b, w * f, 0.35, Color(INK, 0.82 * f))
				# kuru fırça: kuyrukta iki ince kıl çizgisi
				if a.size() >= 2:
					var nn := (a[a.size() - 1] - a[0]).normalized().orthogonal()
					var hair := PackedVector2Array()
					var hair2 := PackedVector2Array()
					for q in a:
						hair.append(q + nn * w * 0.55)
						hair2.append(q - nn * w * 0.5)
					draw_polyline(hair, Color(INK, 0.45 * f), 0.7, true)
					draw_polyline(hair2, Color(INK, 0.35 * f), 0.6, true)
				# iç kenarda silah renginde ince ışık (v31: iki noktadan kısa yolda çizilmez)
				if b.size() >= 2:
					draw_polyline(b, Color(col.lightened(0.3), 0.4 * f), 0.8, true)
		"pence":
			for e in els:
				if _t < float(e["d"]):
					continue
				var a: Vector2 = e["a"]
				var b: Vector2 = e["b"]
				var g := clampf((_t - float(e["d"])) / 0.035, 0.0, 1.0)
				var bb := a.lerp(b, g)
				_taper(PackedVector2Array([a, a.lerp(bb, 0.4), bb]), 0.3, float(e["w"]) * 1.6 * f, Color(INK, 0.85 * f))
				draw_line(a.lerp(bb, 0.2), bb, Color(col.lightened(0.4), 0.5 * f), 0.7, true)
		"catlak":
			for e in els:
				if _t < float(e["d"]):
					continue
				var p: PackedVector2Array = e["p"]
				var g := clampf((_t - float(e["d"])) / 0.06, 0.0, 1.0)
				var m := maxi(2, int(ceil(p.size() * g)))
				_taper(p.slice(0, m), float(e["w"]) * 1.6 * f, 0.3, Color(INK, 0.8 * f))
		"yildiz":
			var gy := clampf(_t / 0.04, 0.0, 1.0)
			for e in els:
				var dd: Vector2 = e["dir"]
				var ln := float(e["len"])
				var a := dd * ln * 0.35 * gy
				var b := dd * ln * (0.5 + 0.5 * gy)
				_taper(PackedVector2Array([a, b]), 1.4 * f + 0.2, 0.2, Color(INK, 0.85 * f))
			draw_circle(Vector2.ZERO, 1.6 * f, Color(1.0, 0.97, 0.9, 0.9 * f))
		"parilti":
			var fc := float(els[0]["f"]) if els.size() > 0 else 1.0
			var g := clampf(_t / 0.03, 0.0, 1.0)
			var L := 9.0 * g
			_taper(PackedVector2Array([Vector2(-L * fc, 0), Vector2(L * 0.6 * fc, 0)]), 0.2, 1.6 * f, Color(INK, 0.8 * f))
			var s := 3.2 * f
			draw_line(Vector2(-s, 0), Vector2(s, 0), Color(1.0, 0.98, 0.92, 0.95 * f), 1.0, true)
			draw_line(Vector2(0, -s * 1.3), Vector2(0, s * 1.3), Color(1.0, 0.98, 0.92, 0.95 * f), 1.0, true)
			draw_circle(Vector2.ZERO, 1.1 * f, Color(1, 1, 1, f))
		"kiris":
			var fc2 := float(els[0]["f"]) if els.size() > 0 else 1.0
			var g2 := clampf(_t / 0.03, 0.0, 1.0)
			for sgn in [-1.0, 1.0]:
				var a2 := Vector2(-2.0 * fc2, sgn * 1.5)
				var b2 := a2 + Vector2(-7.0 * fc2 * g2, sgn * 4.0 * g2)
				_taper(PackedVector2Array([a2, b2]), 1.3 * f, 0.2, Color(INK, 0.8 * f))
			draw_circle(Vector2.ZERO, 1.2 * f, Color(1.0, 0.95, 0.8, 0.8 * f))
		"girdap":
			var fc3 := float(els[0]["f"]) if els.size() > 0 else 1.0
			var r := float(els[0]["r"]) if els.size() > 0 else 14.0
			var g3 := clampf(_t / 0.08, 0.0, 1.0)
			var pts := PackedVector2Array()
			var n := 14
			for i in n:
				var q := float(i) / float(n - 1)
				var ang := lerpf(-2.2, -2.2 + 3.6 * g3, q)
				pts.append(Vector2(cos(ang) * fc3, sin(ang) * 0.55) * r * (0.75 + 0.25 * q))
			_taper(pts, 0.3, 2.2 * f, Color(INK, 0.7 * f))
			draw_polyline(pts.slice(int(n / 2.0), n), Color(col.lightened(0.35), 0.45 * f), 0.8, true)
