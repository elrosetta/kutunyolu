class_name SinemaEfekt
extends Node2D
## v43 sinematik motorunun canlı öğeleri (Sinema.gd çekim listesindeki "efektler"). Tuval biriminde (2560x1440) çizer;
## bulunduğu düzlemle birlikte paralaks / yakınlaşma alır. Her öğe çekimin yerel zamanına (t) bağlıdır — zaman
## atlansa da (test, geçme) aynı kare çıkar: parçacık konumları t'nin işlevidir, birikmez.
##
## tur:
##   toz     parçacık: cesit = kul | yaprak | kor | altin | tuy | kar   (sayi, alan [x0,y0,x1,y1], hiz [vx,vy], boyut, renk)
##   duman   sürüklenen mürekkep / sis bulutları (smoke dokusu)             (sayi, alan, hiz, boyut, renk, a)
##   ates    tören ateşi: titreyen alev dilleri + kor ışığı; son: sönme anı (x, y, olcek, son)
##   zincir  dokuz gecenin zinciri: yol boyunca yılan gibi uzar (t0..t1), dalga; kir: kırılma anı (halkalar savrulur)
##   orgu    beş Gün Örgüsü şeridi: kip = akis (başından ışın gibi dalgalanır) | kes (tek tek kesilir, uçlar düşer) |
##           or (beş uç bir noktada örülür) | tek (tek örgü süzülür: kart / örgü sahnesi)
##   kus     ruh kuşu: yol anahtarları [[t, x, y], ...], kanat çırpar, altın iz bırakır
##   suru    uzak kuş sürüsü (V'ler)
##   isik    ışık huzmeleri (koken, acilar, uzunluk)
##   damla   mürekkep damlaları kâğıda düşüp yayılır: [[t, x, y, r], ...]
##   halka   ışık / şok halkası: [[t, x, y, r], ...]
##   yuvalar Gün Örgüleri göstergesi: beş fırça çemberi (dolu: önceden alınan sıralar, yeni: t_yeni anında dolan)

const ORGU_RENK := [Color(0.93, 0.27, 0.2), Color(0.98, 0.96, 0.9), Color(0.33, 0.62, 0.95), Color(0.98, 0.84, 0.28), Color(1.0, 0.72, 0.26)]

var d: Dictionary = {}
var tur := ""
var t := 0.0
var _p: Array = []          # parçacık tohumları
var _smoke: Texture2D
var _splat: Texture2D


func kur(veri: Dictionary) -> void:
	d = veri
	tur = String(d.get("tur", ""))
	var rs := RandomNumberGenerator.new()
	rs.seed = int(d.get("tohum", 4300)) + tur.hash()
	if bool(d.get("ekle", tur in ["ates", "isik", "halka"] or (tur == "toz" and String(d.get("cesit", "")) in ["kor", "altin"]))):
		var m := CanvasItemMaterial.new()
		m.blend_mode = CanvasItemMaterial.BLEND_MODE_ADD
		material = m
	_smoke = InkUI.tex("smoke")
	_splat = InkUI.tex("splat")
	var n := int(d.get("sayi", 40))
	if tur in ["toz", "duman", "suru"]:
		for i in n:
			_p.append([rs.randf(), rs.randf(), rs.randf_range(0.6, 1.4), rs.randf() * TAU, rs.randf_range(0.7, 1.3), rs.randf()])
	elif tur == "zincir":
		for i in 80:
			_p.append([rs.randf_range(-1, 1), rs.randf_range(-1.4, -0.2), rs.randf_range(-6, 6)])
	elif tur == "orgu":
		for i in 60:
			_p.append([rs.randf() * TAU, rs.randf_range(80, 420), rs.randf_range(0.4, 1.0)])


func adim(tt: float) -> void:
	t = tt
	queue_redraw()


func _r(a: Array, i: int, def := 0.0) -> float:
	return float(a[i]) if a.size() > i else def


func _renk(key: String, def: Color) -> Color:
	var c: Variant = d.get(key, null)
	if c is Array and (c as Array).size() >= 3:
		var a: Array = c
		return Color(float(a[0]), float(a[1]), float(a[2]), float(a[3]) if a.size() > 3 else 1.0)
	if c is Color:
		return c
	return def


func _zarf() -> float:
	## t0..t1 arası görünürlük (yarım saniyelik yumuşak giriş / çıkış); a: genel saydamlık
	var t0 := float(d.get("t0", 0.0))
	var t1 := float(d.get("t1", 999.0))
	var g := float(d.get("gir", 0.6))
	var c := float(d.get("cik", 0.6))
	return clampf(minf((t - t0) / maxf(0.01, g), (t1 - t) / maxf(0.01, c)), 0.0, 1.0) * float(d.get("a", 1.0))


func _draw() -> void:
	var z := _zarf()
	if z <= 0.0 and tur not in ["orgu", "zincir", "kus", "damla", "halka", "yuvalar"]:
		return
	match tur:
		"toz":
			_toz(z)
		"duman":
			_duman(z)
		"ates":
			_ates(z)
		"zincir":
			_zincir()
		"orgu":
			_orgu()
		"kus":
			_kus()
		"suru":
			_suru(z)
		"isik":
			_isik(z)
		"damla":
			_damla()
		"halka":
			_halka()
		"yuvalar":
			_yuvalar()


# ------------------------------------------------------------------ parçacıklar
func _toz(z: float) -> void:
	var al: Array = d.get("alan", [0, 0, 2560, 1440])
	var x0 := float(al[0])
	var y0 := float(al[1])
	var w := float(al[2]) - x0
	var h := float(al[3]) - y0
	var hz: Array = d.get("hiz", [20, 60])
	var vx := float(hz[0])
	var vy := float(hz[1])
	var bo := float(d.get("boyut", 6.0))
	var cs := String(d.get("cesit", "kul"))
	var col := _renk("renk", Color(0.2, 0.19, 0.2, 0.8) if cs == "kul" else Color(1.0, 0.6, 0.2))
	for p in _p:
		var sp: float = p[2]
		var ph: float = p[3]
		var px := x0 + fposmod(float(p[0]) * w + vx * sp * t + sin(t * 0.9 * sp + ph) * 30.0 * float(d.get("salinim", 1.0)), w)
		var py := y0 + fposmod(float(p[1]) * h + vy * sp * t, h)
		var s := bo * float(p[4])
		var a := z * col.a
		# alan kenarında yumuşak sönüm
		a *= clampf(minf(py - y0, y0 + h - py) / (h * 0.12), 0.0, 1.0)
		if a <= 0.01:
			continue
		var c := Color(col, a)
		match cs:
			"yaprak", "tuy":
				var ang := ph + t * 1.6 * sp * (1.0 if p[5] > 0.5 else -1.0)
				var flip := absf(cos(t * 2.2 * sp + ph))
				var ca := Vector2(cos(ang), sin(ang))
				var cb := Vector2(-ca.y, ca.x) * (0.25 + 0.75 * flip)
				var gold: bool = float(p[5]) < float(d.get("altin_oran", 0.0))
				var lc := Color(1.0, 0.78, 0.32, a) if gold else c
				if cs == "tuy":
					draw_line(Vector2(px, py) - ca * s * 1.4, Vector2(px, py) + ca * s * 1.4, lc, s * 0.18, true)
					draw_colored_polygon(PackedVector2Array([Vector2(px, py) - ca * s * 1.2, Vector2(px, py) + cb * s * 0.45, Vector2(px, py) + ca * s * 1.3, Vector2(px, py) - cb * s * 0.15]), Color(lc, a * 0.6))
				else:
					draw_colored_polygon(PackedVector2Array([Vector2(px, py) - ca * s, Vector2(px, py) + cb * s * 0.42 - ca * s * 0.1, Vector2(px, py) + ca * s * 1.1, Vector2(px, py) - cb * s * 0.38]), lc)
			"kor":
				var fl := 0.55 + 0.45 * sin(t * 9.0 * sp + ph * 5.0)
				draw_circle(Vector2(px, py), s * 2.6, Color(col.r, col.g * 0.6, col.b * 0.4, a * 0.12 * fl))
				draw_circle(Vector2(px, py), s * (0.6 + 0.4 * fl), Color(col.r, col.g, col.b, a * fl))
			"altin":
				var tw := 0.4 + 0.6 * absf(sin(t * 3.0 * sp + ph * 3.0))
				draw_circle(Vector2(px, py), s * 2.2, Color(col, a * 0.1 * tw))
				draw_circle(Vector2(px, py), s * 0.5 * tw + 0.6, Color(col, a * tw))
			_:
				var ang2 := ph + t * 0.8 * sp
				var u := Vector2(cos(ang2), sin(ang2)) * s
				var v2 := Vector2(-u.y, u.x) * 0.55
				draw_colored_polygon(PackedVector2Array([Vector2(px, py) - u, Vector2(px, py) + v2, Vector2(px, py) + u * 0.8, Vector2(px, py) - v2 * 0.7]), c)


func _duman(z: float) -> void:
	if _smoke == null:
		return
	var al: Array = d.get("alan", [0, 0, 2560, 1440])
	var x0 := float(al[0])
	var y0 := float(al[1])
	var w := float(al[2]) - x0
	var h := float(al[3]) - y0
	var hz: Array = d.get("hiz", [30, -10])
	var bo := float(d.get("boyut", 700.0))
	var col := _renk("renk", Color(0.05, 0.045, 0.06, 0.5))
	for p in _p:
		var sp: float = p[2]
		var px := x0 - bo * 0.5 + fposmod(float(p[0]) * (w + bo) + float(hz[0]) * sp * t, w + bo)
		var py := y0 + float(p[1]) * h + float(hz[1]) * sp * t + sin(t * 0.3 + float(p[3])) * 40.0
		var s := bo * float(p[4]) * (1.0 + 0.04 * t)
		var ang := float(p[3]) + t * 0.05 * (sp - 1.0)
		var edge := clampf(minf(px - (x0 - bo * 0.5), x0 + w + bo * 0.5 - px) / (bo * 0.6), 0.0, 1.0)
		draw_set_transform(Vector2(px, py), ang, Vector2(1.0, 0.6))
		draw_texture_rect(_smoke, Rect2(-s * 0.5, -s * 0.5, s, s), false, Color(col, col.a * z * edge * (0.5 + 0.5 * float(p[5]))))
	draw_set_transform(Vector2.ZERO)


func _ates(z: float) -> void:
	var x := float(d.get("x", 1280))
	var y := float(d.get("y", 1200))
	var s := float(d.get("olcek", 1.0))
	var son := float(d.get("son", 999.0))
	var k := z * clampf(1.0 - (t - son) / 1.4, 0.0, 1.0)
	if k <= 0.0:
		# sönmüş ateş: ince duman teli ve kor
		var kk := clampf((t - son) / 1.4, 0.0, 1.0) * clampf(1.0 - (t - son - 1.4) / 5.0, 0.0, 1.0)
		draw_circle(Vector2(x, y), 60.0 * s, Color(1.0, 0.3, 0.08, 0.25 * kk))
		return
	var fl := 0.85 + 0.15 * sin(t * 13.0) * sin(t * 7.3 + 1.0)
	for r in [380.0, 240.0, 140.0]:
		draw_circle(Vector2(x, y - 40.0 * s), r * s * fl, Color(1.0, 0.42, 0.12, 0.07 * k))
	var dil := int(d.get("dil", 9))
	for i in dil:
		var u := (float(i) / maxf(1.0, dil - 1.0)) * 2.0 - 1.0
		var hh := (230.0 - absf(u) * 130.0) * s * (0.75 + 0.25 * sin(t * (6.0 + i) + i * 1.7)) * k
		var ww := (46.0 - absf(u) * 14.0) * s
		var bx := x + u * 70.0 * s
		var sw := sin(t * 4.0 + i) * 18.0 * s
		var n := 10
		var lft := PackedVector2Array()
		var rgt := PackedVector2Array()
		for j in n + 1:
			var f := float(j) / n
			var cx := bx + sw * f * f
			var hw := ww * (1.0 - f) * (1.0 - f * 0.3)
			lft.append(Vector2(cx - hw, y - hh * f))
			rgt.append(Vector2(cx + hw + sin(t * 9.0 + f * 5.0 + i) * 6.0 * f * s, y - hh * f))
		var hot := 1.0 - absf(u)
		_serit_dolgu(lft, rgt, Color(1.0, 0.36 + 0.3 * hot, 0.1, 0.55 * k))
		var l2 := PackedVector2Array()
		var r2 := PackedVector2Array()
		for j in n + 1:
			l2.append(Vector2(bx + (lft[j].x - bx) * 0.45, y + (lft[j].y - y) * 0.62))
			r2.append(Vector2(bx + (rgt[j].x - bx) * 0.45, y + (rgt[j].y - y) * 0.62))
		_serit_dolgu(l2, r2, Color(1.0, 0.85, 0.5, 0.6 * k * hot))
	# odunlar (koyu, normal karışım altında okunmaz; ışıkta kızarır)
	draw_line(Vector2(x - 120 * s, y + 10 * s), Vector2(x + 120 * s, y - 14 * s), Color(1.0, 0.3, 0.08, 0.5 * k), 10.0 * s, true)
	draw_line(Vector2(x - 110 * s, y - 16 * s), Vector2(x + 115 * s, y + 12 * s), Color(1.0, 0.3, 0.08, 0.5 * k), 10.0 * s, true)


func _serit_dolgu(l: PackedVector2Array, r: PackedVector2Array, c: Color) -> void:
	## İki kenar arasını üçgenlerle doldur (üçgenleme gerektirmez; kendini kesen alev dilinde de çalışır)
	var cs := PackedColorArray([c, c, c])
	for j in l.size() - 1:
		draw_primitive(PackedVector2Array([l[j], r[j], r[j + 1]]), cs, PackedVector2Array())
		draw_primitive(PackedVector2Array([l[j], r[j + 1], l[j + 1]]), cs, PackedVector2Array())


# ------------------------------------------------------------------ zincir
func _yol_noktasi(yol: Array, u: float) -> Vector2:
	## Catmull-Rom yol (tuval noktaları) üzerinde u (0..1)
	var n := yol.size()
	if n == 0:
		return Vector2.ZERO
	if n == 1:
		return Vector2(float(yol[0][0]), float(yol[0][1]))
	var f := clampf(u, 0.0, 1.0) * (n - 1)
	var i := mini(int(f), n - 2)
	var tt := f - i
	var p0 := _yv(yol, i - 1)
	var p1 := _yv(yol, i)
	var p2 := _yv(yol, i + 1)
	var p3 := _yv(yol, i + 2)
	var t2 := tt * tt
	var t3 := t2 * tt
	return 0.5 * ((2.0 * p1) + (-p0 + p2) * tt + (2.0 * p0 - 5.0 * p1 + 4.0 * p2 - p3) * t2 + (-p0 + 3.0 * p1 - 3.0 * p2 + p3) * t3)


func _yv(yol: Array, i: int) -> Vector2:
	var j := clampi(i, 0, yol.size() - 1)
	return Vector2(float(yol[j][0]), float(yol[j][1]))


func _zincir() -> void:
	var yol: Array = d.get("yol", [[0, 700], [2560, 700]])
	var t0 := float(d.get("t0", 0.0))
	var t1 := float(d.get("t1", 2.0))
	var g := clampf((t - t0) / maxf(0.01, t1 - t0), 0.0, 1.0)
	g = 1.0 - pow(1.0 - g, 2.2)
	if g <= 0.0:
		return
	var L := float(d.get("halka", 70.0))
	var kal := float(d.get("kalinlik", 12.0))
	var col := _renk("renk", Color(0.04, 0.035, 0.05, 1.0))
	var dalga := float(d.get("dalga", 30.0))
	var kir := float(d.get("kir", -1.0))
	var kir_u := float(d.get("kir_u", 0.5))
	# yol uzunluğu (yaklaşık)
	var uz := 0.0
	var prev := _yol_noktasi(yol, 0.0)
	for k in range(1, 41):
		var q := _yol_noktasi(yol, k / 40.0)
		uz += q.distance_to(prev)
		prev = q
	var n := int(uz / (L * 0.8))
	var a := float(d.get("a", 1.0)) * clampf((float(d.get("son", 999.0)) - t) / 0.8, 0.0, 1.0)
	var kirildi := kir >= 0.0 and t >= kir
	var kt := t - kir
	for i in n:
		var u := (i + 0.5) / n
		if u > g:
			break
		var p := _yol_noktasi(yol, u)
		var p2 := _yol_noktasi(yol, minf(1.0, u + 0.01))
		var tg := (p2 - p).normalized()
		var nr := Vector2(-tg.y, tg.x)
		# yılan dalgası: uca doğru artar, zamanla akar
		var w := sin(u * 14.0 - t * 4.0) * dalga * (0.3 + 0.7 * (g - u + 0.2))
		p += nr * w
		var ang := tg.angle() + cos(u * 14.0 - t * 4.0) * 0.25
		var cc := col
		if kirildi:
			var du := absf(u - kir_u)
			if du < 0.012:
				continue
			# kırılma: yakın halkalar savrulur, uzaklar gerilip düşer
			var sp: Array = _p[i % _p.size()]
			var side := signf(u - kir_u)
			var kk := clampf(1.0 - du * 4.0, 0.0, 1.0)
			p += Vector2(side * (220.0 + float(sp[2]) * 30.0) * kk * kt, (float(sp[1]) * 300.0 * kk + 0.0) * kt + 380.0 * kt * kt * kk)
			ang += float(sp[2]) * kt * kk
			cc = Color(col, col.a * clampf(1.0 - kt * 0.35 * kk, 0.0, 1.0))
			# ışık yarığı: kırık uçlarda altın
			if du < 0.05:
				draw_circle(p, L * 0.6, Color(1.0, 0.8, 0.4, 0.25 * clampf(1.0 - kt, 0.0, 1.0)))
		cc.a *= a
		var face := i % 2 == 0
		var rx := L * 0.55
		var ry := L * (0.32 if face else 0.1)
		var pts := PackedVector2Array()
		for k in 15:
			var th := TAU * k / 14.0
			var e := Vector2(cos(th) * rx, sin(th) * ry).rotated(ang)
			pts.append(p + e)
		draw_polyline(pts, cc, kal * (1.0 if face else 1.35), true)
		if face:
			draw_polyline(pts, Color(0.5, 0.45, 0.42, cc.a * 0.25), kal * 0.25, true)


# ------------------------------------------------------------------ örgüler
func _orgu_renk(i: int) -> Color:
	var r: Variant = d.get("renkler", null)
	if r is Array and (r as Array).size() > i:
		var c: Array = r[i]
		return Color(float(c[0]), float(c[1]), float(c[2]))
	if d.has("renk"):
		return _renk("renk", ORGU_RENK[i % 5])
	return ORGU_RENK[i % 5]


func _serit(pts: PackedVector2Array, w0: float, col: Color, a: float, glow := 1.0) -> void:
	## Örgü şeridi: ışıma (geniş, saydam) + gövde + ters kama izleri (saç örgüsü)
	if pts.size() < 2:
		return
	var n := pts.size()
	for gi in 3:
		var gw := w0 * (3.6 - gi * 1.0)
		draw_polyline(pts, Color(col.lightened(0.2), a * 0.06 * glow), gw, true)
	var widths := PackedFloat32Array()
	for i in n:
		var f := float(i) / (n - 1)
		widths.append(w0 * (1.0 - 0.75 * pow(f, 1.4)))
	for i in n - 1:
		draw_line(pts[i], pts[i + 1], Color(col.darkened(0.25), a), widths[i], true)
	for i in n - 1:
		draw_line(pts[i], pts[i + 1], Color(col, a), widths[i] * 0.62, true)
	# kama izleri
	for i in range(1, n - 1, 2):
		var tg := (pts[i + 1] - pts[i - 1]).normalized()
		var nr := Vector2(-tg.y, tg.x)
		var ww := widths[i] * 0.5
		var side := 1.0 if (i / 2) % 2 == 0 else -1.0
		draw_line(pts[i] + nr * side * ww, pts[i] - tg * ww * 0.9, Color(col.darkened(0.45), a * 0.75), maxf(1.5, ww * 0.28), true)
		draw_line(pts[i] + nr * side * ww * 0.6, pts[i] - tg * ww * 0.4, Color(col.lightened(0.5), a * 0.55), maxf(1.0, ww * 0.12), true)


func _orgu() -> void:
	var kip := String(d.get("kip", "akis"))
	var a := _zarf()
	var t0 := float(d.get("t0", 0.0))
	var g := clampf((t - t0) / maxf(0.01, float(d.get("buyume", 1.6))), 0.0, 1.0)
	g = 1.0 - pow(1.0 - g, 2.0)
	if a <= 0.0 or g <= 0.0:
		return
	var w := float(d.get("genislik", 26.0))
	var seg := 30
	match kip:
		"akis":
			var ko: Array = d.get("koken", [1280, 500])
			var o := Vector2(float(ko[0]), float(ko[1]))
			var ac: Array = d.get("acilar", [-150, -125, -90, -55, -30])
			var uz := float(d.get("uzunluk", 900.0))
			for i in ac.size():
				var pts := PackedVector2Array()
				var a0 := deg_to_rad(float(ac[i]))
				for j in seg + 1:
					var f := float(j) / seg * g
					var aa := a0 + 0.22 * sin(f * 5.0 - t * 1.3 + i * 1.3) * f
					pts.append(o + Vector2(cos(aa), sin(aa)) * uz * f * (0.9 + 0.1 * sin(i * 2.1)))
				_serit(pts, w, _orgu_renk(i), a)
		"kes":
			# beş örgü sağdan sola uzanır; kesimler[i] anında kes_x'te kesilir: sol parça düşer, sağ parça solar
			var ys: Array = d.get("ys", [560, 640, 720, 800, 880])
			var xa := float(d.get("x_bas", 2700))
			var xb := float(d.get("x_son", 300))
			var kx := float(d.get("kes_x", 900))
			var ks: Array = d.get("kesimler", [1.0, 1.5, 2.0, 2.5, 3.0])
			for i in ys.size():
				var tc := float(ks[i]) if ks.size() > i else 99.0
				var kesik := t >= tc
				var dt := t - tc
				var y0 := float(ys[i])
				var sag := PackedVector2Array()
				var sol := PackedVector2Array()
				for j in seg + 1:
					var f := float(j) / seg
					var x := lerpf(xa, xb, f * g)
					var y := y0 + sin(f * 6.0 - t * 2.2 + i) * float(d.get("dalga", 22.0)) * (0.35 + 0.65 * f)
					var p := Vector2(x, y)
					if not kesik or x >= kx:
						sag.append(p)
					if kesik and x <= kx:
						sol.append(p)
				var col := _orgu_renk(i)
				if kesik:
					# kesik uç: sola savrulur, döner, düşer
					var piv := Vector2(kx, y0)
					var ang := dt * (1.2 + i * 0.25) * (1.0 if i % 2 == 0 else -0.8)
					var off := Vector2(-160.0 * dt, 120.0 * dt + 420.0 * dt * dt)
					var moved := PackedVector2Array()
					for q in sol:
						moved.append(piv + (q - piv).rotated(ang) + off)
					var fade := clampf(1.0 - dt / 2.2, 0.0, 1.0)
					var rev := PackedVector2Array()
					for qi in range(moved.size() - 1, -1, -1):
						rev.append(moved[qi])
					_serit(rev, w * 0.9, col, a * fade, 0.6)
					# sağdaki kalan: renk söner (ışık kesildi)
					var grey := col.lerp(Color(0.35, 0.33, 0.36), clampf(dt / 1.2, 0.0, 0.85))
					_serit(sag, w, grey, a * (1.0 - 0.4 * clampf(dt, 0.0, 1.0)), 1.0 - clampf(dt, 0.0, 1.0))
					# kesim kıvılcımları
					if dt < 0.8:
						for s in 14:
							var sp: Array = _p[(s + i * 7) % _p.size()]
							var dir := Vector2.from_angle(float(sp[0]))
							var pp := Vector2(kx, y0) + dir * float(sp[1]) * dt * 1.4 + Vector2(0, 300.0 * dt * dt)
							draw_circle(pp, 5.0 * float(sp[2]) * (1.0 - dt / 0.8) + 1.0, Color(1.0, 0.85, 0.5, (1.0 - dt / 0.8) * a))
						draw_circle(Vector2(kx, y0), 90.0 * (1.0 - dt / 0.8), Color(1.0, 0.9, 0.6, 0.35 * (1.0 - dt / 0.8) * a))
				else:
					_serit(sag, w, col, a)
		"or":
			var he: Array = d.get("hedef", [1280, 900])
			var h := Vector2(float(he[0]), float(he[1]))
			var bas: Array = d.get("baslar", [[700, 200], [1000, 120], [1300, 100], [1600, 130], [1900, 220]])
			for i in bas.size():
				var s := Vector2(float(bas[i][0]), float(bas[i][1]))
				var pts := PackedVector2Array()
				for j in seg + 1:
					var f := float(j) / seg
					var ff := f * g
					var p := s.lerp(h, ff)
					var nr := (h - s).normalized().orthogonal()
					p += nr * sin(ff * PI * 3.0 + i * 1.25 + t * 1.5) * 70.0 * (1.0 - ff)
					pts.append(p)
				_serit(pts, w, _orgu_renk(i), a)
			if g >= 0.98:
				var k := clampf((t - t0 - float(d.get("buyume", 1.6))) / 1.0, 0.0, 1.0)
				draw_circle(h, 60.0 + 40.0 * k, Color(1.0, 0.85, 0.5, 0.22 * k * a))
				draw_circle(h, 22.0 + 10.0 * sin(t * 4.0), Color(1.0, 0.95, 0.75, 0.6 * k * a))
		"tek":
			var ko2: Array = d.get("koken", [1280, 720])
			var o2 := Vector2(float(ko2[0]), float(ko2[1]))
			var uz2 := float(d.get("uzunluk", 900.0))
			var ac2 := deg_to_rad(float(d.get("aci", 0.0)))
			var pts2 := PackedVector2Array()
			for j in seg + 1:
				var f := (float(j) / seg - 0.5) * g
				var p := o2 + Vector2.from_angle(ac2) * uz2 * f
				p += Vector2.from_angle(ac2 + PI * 0.5) * sin(f * 7.0 - t * 1.8) * 40.0
				pts2.append(p)
			var col2 := _orgu_renk(int(d.get("sira", 0)))
			_serit(pts2, w, col2, a, 1.6)
			for s in 24:
				var sp2: Array = _p[s % _p.size()]
				var ph := fposmod(t * 0.25 * float(sp2[2]) + float(sp2[0]), 1.0)
				var pp := o2 + Vector2.from_angle(ac2) * uz2 * (float(sp2[0]) / TAU - 0.5) * g + Vector2(0, -ph * 260.0)
				draw_circle(pp, 3.0 * float(sp2[2]) + 1.0, Color(col2.lightened(0.4), a * sin(ph * PI) * 0.8))


# ------------------------------------------------------------------ kuşlar, ışık, damla
func _kus() -> void:
	var yol: Array = d.get("yol", [[0, 1280, 1200], [3, 1280, 700]])
	if yol.is_empty():
		return
	var a := _zarf()
	if a <= 0.0:
		return
	# anahtarlar arası yumuşak geçiş
	var p := Vector2(float(yol[0][1]), float(yol[0][2]))
	var v := Vector2.ZERO
	for i in yol.size() - 1:
		var ka: Array = yol[i]
		var kb: Array = yol[i + 1]
		if t >= float(ka[0]) and t <= float(kb[0]):
			var f := (t - float(ka[0])) / maxf(0.01, float(kb[0]) - float(ka[0]))
			f = f * f * (3.0 - 2.0 * f)
			p = Vector2(float(ka[1]), float(ka[2])).lerp(Vector2(float(kb[1]), float(kb[2])), f)
			v = Vector2(float(kb[1]) - float(ka[1]), float(kb[2]) - float(ka[2]))
			break
		elif t > float(kb[0]):
			p = Vector2(float(kb[1]), float(kb[2]))
	var s := float(d.get("boyut", 60.0))
	var col := _renk("renk", Color(1.0, 0.82, 0.42))
	var hiz := float(d.get("cirpma", 7.0))
	var flap := sin(t * hiz)
	var yon := -1.0 if v.x < 0.0 else 1.0
	# ışıma ve iz
	for r in [s * 3.2, s * 1.9, s * 1.1]:
		draw_circle(p, r, Color(col, 0.07 * a))
	for k in 10:
		var tk := t - k * 0.06
		var off := Vector2(-yon * k * s * 0.18, sin(tk * 3.0) * s * 0.1 + k * s * 0.05)
		draw_circle(p + off, s * 0.12 * (1.0 - k / 10.0) + 1.0, Color(col, a * 0.5 * (1.0 - k / 10.0)))
	for side in [-1.0, 1.0]:
		var root := p + Vector2(0, -s * 0.05)
		var tip := p + Vector2(side * s * 1.25, -s * (0.25 + 0.75 * flap * side * side))
		var mid := p + Vector2(side * s * 0.6, -s * (0.55 + 0.35 * flap))
		var back := p + Vector2(side * s * 0.45, s * 0.12)
		draw_colored_polygon(PackedVector2Array([root, mid, tip, back]), Color(col, a * 0.92))
	draw_colored_polygon(PackedVector2Array([p + Vector2(-yon * s * 0.45, s * 0.05), p + Vector2(0, -s * 0.18), p + Vector2(yon * s * 0.5, -s * 0.05), p + Vector2(yon * s * 0.1, s * 0.2), p + Vector2(-yon * s * 0.7, s * 0.35)]), Color(col.lightened(0.3), a))


func _suru(z: float) -> void:
	var al: Array = d.get("alan", [0, 100, 2560, 500])
	var hz: Array = d.get("hiz", [60, -5])
	var col := _renk("renk", Color(0.06, 0.05, 0.07, 0.85))
	var bo := float(d.get("boyut", 18.0))
	var w := float(al[2]) - float(al[0])
	for p in _p:
		var x := float(al[0]) + fposmod(float(p[0]) * w + float(hz[0]) * float(p[2]) * t, w)
		var y := float(al[1]) + float(p[1]) * (float(al[3]) - float(al[1])) + float(hz[1]) * t + sin(t * 0.8 + float(p[3])) * 12.0
		var s := bo * float(p[4])
		var f := sin(t * 6.0 * float(p[2]) + float(p[3]))
		draw_polyline(PackedVector2Array([Vector2(x - s, y - s * 0.4 * f), Vector2(x - s * 0.3, y - s * 0.15), Vector2(x, y), Vector2(x + s * 0.3, y - s * 0.15), Vector2(x + s, y - s * 0.4 * f)]), Color(col, col.a * z), maxf(2.0, s * 0.16), true)


func _isik(z: float) -> void:
	var ko: Array = d.get("koken", [1280, 300])
	var o := Vector2(float(ko[0]), float(ko[1]))
	var ac: Array = d.get("acilar", [70, 80, 90, 100, 110])
	var uz := float(d.get("uzunluk", 1400.0))
	var col := _renk("renk", Color(1.0, 0.8, 0.45, 0.22))
	for i in ac.size():
		var a := deg_to_rad(float(ac[i]) + sin(t * 0.3 + i) * 1.5)
		var wd := deg_to_rad(float(d.get("genislik", 4.0)))
		var e := col.a * z * (0.6 + 0.4 * sin(t * 0.7 + i * 1.7))
		var p1 := o + Vector2.from_angle(a - wd) * uz
		var p2 := o + Vector2.from_angle(a + wd) * uz
		draw_polygon(PackedVector2Array([o, p1, p2]), PackedColorArray([Color(col, e), Color(col, 0.0), Color(col, 0.0)]))


func _damla() -> void:
	if _splat == null:
		return
	var col := _renk("renk", Color(0.04, 0.035, 0.05, 0.95))
	for e in d.get("liste", []):
		var dt := t - float(e[0])
		if dt < 0.0:
			continue
		var r := float(e[3])
		var k := 1.0 - pow(1.0 - clampf(dt / 0.9, 0.0, 1.0), 3.0)
		var s := r * (0.2 + 0.8 * k)
		draw_set_transform(Vector2(float(e[1]), float(e[2])), float(e[0]) * 7.0, Vector2.ONE)
		draw_texture_rect(_splat, Rect2(-s, -s, s * 2.0, s * 2.0), false, Color(col, col.a * clampf(dt / 0.15, 0.0, 1.0) * float(d.get("a", 1.0))))
	draw_set_transform(Vector2.ZERO)


func _halka() -> void:
	var col := _renk("renk", Color(1.0, 0.85, 0.5, 0.8))
	for e in d.get("liste", []):
		var dt := t - float(e[0])
		if dt < 0.0 or dt > 1.2:
			continue
		var k := dt / 1.2
		var r := float(e[3]) * (1.0 - pow(1.0 - k, 3.0))
		draw_arc(Vector2(float(e[1]), float(e[2])), r, 0.0, TAU, 64, Color(col, col.a * (1.0 - k)), 30.0 * (1.0 - k) + 2.0, true)


func _yuvalar() -> void:
	var y := float(d.get("y", 1230))
	var dolu: Array = d.get("dolu", []) if d.get("dolu") is Array else []
	var yeni := int(d.get("yeni", -1)) if not (d.get("yeni") is String) else -1
	var ty := float(d.get("t_yeni", 3.0))
	var a := clampf(t / 0.6, 0.0, 1.0)
	var enso := InkUI.tex("enso")
	for i in 5:
		var c := Vector2(1280.0 + (i - 2) * 150.0, y)
		var col: Color = ORGU_RENK[i]
		if enso:
			draw_texture_rect(enso, Rect2(c - Vector2(52, 52), Vector2(104, 104)), false, Color(0.0, 0.0, 0.0, 0.75 * a))
			draw_texture_rect(enso, Rect2(c - Vector2(46, 46), Vector2(92, 92)), false, Color(0.9, 0.85, 0.75, 0.35 * a))
		var k := 0.0
		if i in dolu:
			k = 1.0
		elif i == yeni:
			k = clampf((t - ty) / 0.5, 0.0, 1.0)
		if k > 0.0:
			var puls := 1.0 + (0.25 * clampf(1.0 - (t - ty) / 0.8, 0.0, 1.0) if i == yeni else 0.0)
			draw_circle(c, 44.0 * puls, Color(col, 0.12 * k * a))
			draw_circle(c, 26.0 * k * puls, Color(col, 0.85 * a))
			draw_circle(c, 12.0 * k, Color(col.lightened(0.6), 0.9 * a))
		if i == yeni and t >= ty and t < ty + 1.2:
			var q := (t - ty) / 1.2
			draw_arc(c, 30.0 + q * 120.0, 0.0, TAU, 48, Color(col, (1.0 - q) * 0.8), 6.0 * (1.0 - q) + 1.0, true)
