class_name Blood
extends Node2D
## Gerçekçi kan (v13): her damla yerçekimi ve hava direnciyle uçar, hızına göre uzar.
##  - zemine düşünce yüzeye yapışan leke bırakır (çarpma hızıyla yayılır),
##  - duvara çarpınca yapışır, bir kısmı aşağı doğru süzülerek iz çizer,
##  - ölümde et parçaları saçılır; uçarken arkalarında kan bırakır, yere düşünce sekip yapışır.
## Lekeler bölüm boyunca kalır (kalıcı; çok birikince en eskileri silinir).
## Pikseller 2/3 dünya pikseli: 1080p'de 2x2 ekran pikseli (zemin dokularıyla aynı ızgara).

const PX := 2.0 / 3.0
const MAX_DROPS := 900
const MAX_STAINS := 7000
const GRAV := 900.0

var level: Node
# uçan damlalar (paralel diziler: hızlı)
var _p := PackedVector2Array()
var _v := PackedVector2Array()
var _c := PackedColorArray()
var _life := PackedFloat32Array()
var _sz := PackedFloat32Array()
# duvardan süzülenler
var _drips: Array = []  # [pos: Vector2, speed: float, life: float, col: Color]
# et parçaları
var _gibs: Array = []  # {p, v, col, s, rot, w, bounces, trail}
var stains: _Stains


static func sys() -> Blood:
	var lv: Node = FX.level
	if lv == null or not is_instance_valid(lv):
		return null
	if lv.has_meta("blood"):
		var b: Variant = lv.get_meta("blood")
		if is_instance_valid(b):
			return b
	var bl := Blood.new()
	bl.level = lv
	bl.z_index = 24
	lv.add_child(bl)
	bl.stains = _Stains.new()
	bl.stains.z_index = 1
	lv.add_child(bl.stains)
	lv.set_meta("blood", bl)
	return bl


static func _tone(col: Color, rng_k: float) -> Color:
	## Gerçekçi ton: renk biraz koyulaşır, damladan damlaya parlaklık değişir
	var c := col.darkened(0.12 + 0.18 * rng_k)
	c.a = 1.0
	return c


static func spray(pos: Vector2, dir: Vector2, col: Color, n: int, power := 1.0, back := true) -> void:
	## Vuruş sıçrantısı: darbe yönünde koni (çıkış), az miktar ters yöne (giriş), ince buğu
	var b := sys()
	if b == null:
		return
	var d := dir.normalized() if dir.length() > 0.01 else Vector2.UP
	for i in n:
		var rev := back and i % 6 == 5
		var ang := d.angle() + (PI if rev else 0.0) + randf_range(-0.55, 0.55) - 0.25 * signf(d.x)
		var sp := randf_range(70.0, 300.0) * power * (0.5 if rev else 1.0)
		b._add(pos + Vector2(randf_range(-3, 3), randf_range(-3, 3)), Vector2(cos(ang), sin(ang)) * sp + Vector2(0, -randf_range(20, 90)), _tone(col, randf()), randf_range(1.4, 2.6), 1.0 if randf() < 0.55 else 2.0)
	if n >= 6:
		_mist(pos, d, col, 0.22 + 0.04 * minf(n, 30) / 10.0)


static func burst(pos: Vector2, dir: Vector2, col: Color, n: int, gibs := 0, flesh := true) -> void:
	## Ölüm: her yöne ağır sıçrantı + darbe yönünde fışkırma + et parçaları
	var b := sys()
	if b == null:
		return
	var d := dir.normalized() if dir.length() > 0.01 else Vector2.UP
	for i in n:
		var radial := i % 3 == 0
		var ang := (randf() * TAU) if radial else d.angle() + randf_range(-0.7, 0.7)
		var sp := randf_range(60.0, 360.0) * (0.7 if radial else 1.0)
		b._add(pos + Vector2(randf_range(-6, 6), randf_range(-8, 6)), Vector2(cos(ang), sin(ang)) * sp + Vector2(0, -randf_range(60, 160)), _tone(col, randf()), randf_range(1.6, 3.0), 1.0 if randf() < 0.7 else 2.0)
	for i in gibs:
		var ang2 := d.angle() + randf_range(-1.1, 1.1) - PI * 0.25 * signf(d.x)
		var sp2 := randf_range(140.0, 300.0)
		b._gibs.append({"p": pos + Vector2(randf_range(-5, 5), randf_range(-6, 4)), "v": Vector2(cos(ang2), sin(ang2)) * sp2 + Vector2(0, -randf_range(120, 220)),
			"col": col.darkened(randf_range(0.15, 0.4)) if flesh else col.darkened(0.2), "s": randi_range(2, 4), "rot": randf() * TAU, "w": randf_range(-14, 14),
			"bounces": 0, "trail": 0.0, "flesh": flesh, "life": 6.0})
	_mist(pos, d, col, 0.5)


static func drip(pos: Vector2, col: Color, n := 1) -> void:
	## Yaralı gövdeden süzülen damla
	var b := sys()
	if b == null:
		return
	for i in n:
		b._add(pos + Vector2(randf_range(-4, 4), randf_range(-2, 2)), Vector2(randf_range(-12, 12), randf_range(0, 30)), _tone(col, randf()), 3.0, 1.0)


static func _mist(pos: Vector2, d: Vector2, col: Color, size: float) -> void:
	## Kan buğusu: darbe noktasında kısa ömürlü ince bulut
	if FX.root == null:
		return
	var p := FX._particles(pos, Color(col.darkened(0.3), 0.45), 5, 0.4, false, 26, "k_smoke2")
	p.direction = d
	p.spread = 40.0
	p.initial_velocity_min = 20.0
	p.initial_velocity_max = 70.0
	p.gravity = Vector2(0, 40)
	p.damping_min = 60.0
	p.damping_max = 120.0
	p.scale_amount_min = size
	p.scale_amount_max = size * 1.8


func _add(pos: Vector2, vel: Vector2, col: Color, life: float, sz: float) -> void:
	if _p.size() >= MAX_DROPS:
		return
	_p.append(pos)
	_v.append(vel)
	_c.append(col)
	_life.append(life)
	_sz.append(sz)


func _cell_at(p: Vector2) -> int:
	return level.cell(int(floorf(p.x / level.TS)), int(floorf(p.y / level.TS)))


func _physics_process(delta: float) -> void:
	if level == null or not is_instance_valid(level):
		return
	var TS: float = level.TS
	var i := _p.size() - 1
	while i >= 0:
		var p := _p[i]
		var v := _v[i]
		v.y += GRAV * delta
		v *= 1.0 - 0.9 * delta
		var np := p + v * delta
		var c := _cell_at(np)
		var hit := false
		if c == 1 or c == 4 or (c == 2 and v.y > 0.0 and _cell_at(p) != 2):
			hit = true
			var from_above := _cell_at(Vector2(np.x, p.y)) == 0 and v.y > 0.0
			if from_above or c == 2:
				# yüzeye yapış: düşüş hızına göre yatay yayılma
				var top := floorf(np.y / TS) * TS
				var spread := clampf(v.length() / 90.0, 1.0, 5.0)
				stains.add(Vector2(np.x, top + PX * 0.5), _c[i], int(spread), true)
			else:
				# duvar: yüzeye yapış; bazıları aşağı süzülür
				var wx := (floorf(np.x / TS) * TS) if v.x > 0.0 else (floorf(np.x / TS) + 1.0) * TS - PX
				var wp := Vector2(wx if v.x > 0.0 else wx, np.y)
				stains.add(wp, _c[i], 1, false)
				if randf() < 0.3:
					_drips.append([wp, randf_range(6.0, 16.0), randf_range(0.6, 2.2), _c[i]])
		_life[i] -= delta
		if hit or _life[i] <= 0.0 or np.y > level.H * TS + 50.0:
			_remove(i)
		else:
			_p[i] = np
			_v[i] = v
		i -= 1
	# duvar süzülmesi
	var j := _drips.size() - 1
	while j >= 0:
		var dr: Array = _drips[j]
		var old: Vector2 = dr[0]
		var nw := old + Vector2(0, float(dr[1]) * delta)
		dr[1] = maxf(2.0, float(dr[1]) * (1.0 - 0.6 * delta))
		dr[2] = float(dr[2]) - delta
		if int(old.y / PX) != int(nw.y / PX):
			stains.add(nw, (dr[3] as Color).darkened(0.1), 1, false)
		dr[0] = nw
		if float(dr[2]) <= 0.0 or _cell_at(nw + Vector2(0, 2)) == 1 and _cell_at(nw + Vector2(2, 0)) != 1 and _cell_at(nw - Vector2(2, 0)) != 1:
			_drips.remove_at(j)
		j -= 1
	# et parçaları
	var k := _gibs.size() - 1
	while k >= 0:
		var g: Dictionary = _gibs[k]
		var gv: Vector2 = g["v"]
		var gp: Vector2 = g["p"]
		gv.y += GRAV * delta
		gv *= 1.0 - 0.4 * delta
		var ngp := gp + gv * delta
		g["rot"] = float(g["rot"]) + float(g["w"]) * delta
		g["life"] = float(g["life"]) - delta
		# uçarken iz bırakır
		g["trail"] = float(g["trail"]) + delta
		if g["flesh"] and float(g["trail"]) > 0.035 and gv.length() > 60.0:
			g["trail"] = 0.0
			_add(gp, gv * 0.15 + Vector2(randf_range(-10, 10), 0), _tone(g["col"], randf()), 1.5, 1.0)
		var gc := _cell_at(ngp)
		if gc == 1 or gc == 4 or (gc == 2 and gv.y > 0.0):
			if _cell_at(Vector2(ngp.x, gp.y)) == 0 and gv.y > 0.0:
				# yere çarptı: seker, yavaşlar; sonunda yapışır
				var top2 := floorf(ngp.y / TS) * TS
				stains.add(Vector2(ngp.x, top2 + PX * 0.5), g["col"], 2 + int(g["s"]), true)
				g["bounces"] = int(g["bounces"]) + 1
				if gv.length() < 90.0 or int(g["bounces"]) >= 3:
					stains.add_chunk(Vector2(ngp.x, top2 - PX * float(g["s"]) * 0.5), g["col"], int(g["s"]))
					_gibs.remove_at(k)
					k -= 1
					continue
				gv = Vector2(gv.x * 0.45, -absf(gv.y) * 0.28)
				g["w"] = float(g["w"]) * 0.5
				ngp = Vector2(ngp.x, top2 - 0.5)
			else:
				gv.x = -gv.x * 0.3
				ngp = gp
		g["p"] = ngp
		g["v"] = gv
		if float(g["life"]) <= 0.0:
			_gibs.remove_at(k)
		k -= 1
	queue_redraw()


func _remove(i: int) -> void:
	var last := _p.size() - 1
	if i != last:
		_p[i] = _p[last]
		_v[i] = _v[last]
		_c[i] = _c[last]
		_life[i] = _life[last]
		_sz[i] = _sz[last]
	_p.resize(last)
	_v.resize(last)
	_c.resize(last)
	_life.resize(last)
	_sz.resize(last)


func _draw() -> void:
	for i in _p.size():
		var p := _p[i]
		var v := _v[i]
		var s := PX * _sz[i]
		var col := _c[i]
		var sp := v.length()
		# hızlı damla: hız yönünde uzayan iz (piksel ızgarasına oturtulmuş)
		var steps := clampi(int(sp / 120.0), 0, 3)
		for k in range(steps, -1, -1):
			var q := p - v.normalized() * (k * PX * 1.2) if sp > 1.0 else p
			var sn := Vector2(floorf(q.x / PX) * PX, floorf(q.y / PX) * PX)
			draw_rect(Rect2(sn, Vector2(s, s)), col if k == 0 else Color(col, 0.75 - 0.18 * k))
		if s > PX and sp < 200.0:
			var hl := Vector2(floorf(p.x / PX) * PX, floorf(p.y / PX) * PX)
			draw_rect(Rect2(hl, Vector2(PX, PX)), col.lightened(0.25))
	for g in _gibs:
		var gp: Vector2 = g["p"]
		var n: int = g["s"]
		var col2: Color = g["col"]
		var base := Vector2(floorf(gp.x / PX) * PX, floorf(gp.y / PX) * PX)
		var ca := cos(float(g["rot"]))
		var sa := sin(float(g["rot"]))
		for yy in n:
			for xx in n:
				if (xx == 0 or xx == n - 1) and (yy == 0 or yy == n - 1) and n > 2:
					continue
				var o := Vector2(xx - n / 2.0, yy - n / 2.0) * PX
				o = Vector2(o.x * ca - o.y * sa, o.x * sa + o.y * ca)
				var q2 := base + Vector2(roundf(o.x / PX) * PX, roundf(o.y / PX) * PX)
				var shade := col2.lightened(0.18) if yy == 0 else (col2.darkened(0.25) if yy == n - 1 else col2)
				draw_rect(Rect2(q2, Vector2(PX, PX)), shade)


class _Stains:
	extends Node2D
	## Kalıcı lekeler: yüzey lekeleri yatay yayılır, duvar lekeleri tek piksel; zamanla koyulaşır (oksitlenme).
	const PX := 2.0 / 3.0
	const MAX_STAINS := 7000
	var pts := PackedVector2Array()
	var cols := PackedColorArray()
	var _dirty := false
	var _age_t := 0.0

	func add(p: Vector2, col: Color, spread: int, surface: bool) -> void:
		var base := Vector2(floorf(p.x / PX) * PX, floorf(p.y / PX) * PX)
		var c := col.darkened(0.1)
		if not surface:
			pts.append(base)
			cols.append(c)
			_trim()
			_dirty = true
			return
		# yüzey: düzensiz göllenme. Ortası koyu ve kalın (zemine siner), kenarlar ince ve kesik,
		# ortada bir parlak piksel (ıslaklık), çevresine minik sıçrantı noktaları
		var w := spread + 1
		for k in range(-w, w + 1):
			var t := absf(k) / float(w)
			if randf() > 1.0 - t * 0.55:
				continue
			var ck := c.darkened(0.12 * (1.0 - t))
			pts.append(base + Vector2(k * PX, 0))
			cols.append(ck)
			if t < 0.65:
				pts.append(base + Vector2(k * PX, PX))
				cols.append(ck.darkened(0.15))
			if t < 0.3 and randf() < 0.6:
				pts.append(base + Vector2(k * PX, -PX))
				cols.append(ck.lightened(0.05))
		if spread >= 2:
			pts.append(base + Vector2(randi_range(-1, 1) * PX, -PX))
			cols.append(c.lightened(0.35))
		for m in randi_range(0, mini(3, spread)):
			pts.append(base + Vector2(randi_range(-w - 3, w + 3) * PX, randi_range(-1, 0) * PX))
			cols.append(c)
		_trim()
		_dirty = true

	func add_chunk(p: Vector2, col: Color, n: int) -> void:
		var base := Vector2(floorf(p.x / PX) * PX, floorf(p.y / PX) * PX)
		for yy in n:
			for xx in n + 1:
				if yy == 0 and (xx == 0 or xx == n):
					continue
				pts.append(base + Vector2((xx - n / 2) * PX, yy * PX))
				cols.append(col.lightened(0.12) if yy == 0 else col)
		_trim()
		_dirty = true

	func _trim() -> void:
		if pts.size() > MAX_STAINS:
			var cut := pts.size() - MAX_STAINS + 600
			pts = pts.slice(cut)
			cols = cols.slice(cut)

	func _process(delta: float) -> void:
		# lekeler yavaşça koyulaşır (her 4 sn bir adım)
		_age_t += delta
		if _age_t > 4.0:
			_age_t = 0.0
			for i in cols.size():
				var c := cols[i]
				if c.v > 0.12:
					cols[i] = c.darkened(0.035)
			_dirty = true
		if _dirty:
			_dirty = false
			queue_redraw()

	func _draw() -> void:
		var s := Vector2(PX, PX)
		for i in pts.size():
			draw_rect(Rect2(pts[i], s), cols[i])
