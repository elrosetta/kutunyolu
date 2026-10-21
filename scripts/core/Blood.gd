class_name Blood
extends Node2D
## Gerçekçi kan (v13): her damla yerçekimi ve hava direnciyle uçar, hızına göre uzar.
##  - zemine düşünce yüzeye yapışan leke bırakır (çarpma hızıyla yayılır),
##  - duvara çarpınca yapışır, bir kısmı aşağı doğru süzülerek iz çizer,
##  - ölümde et parçaları saçılır; uçarken arkalarında kan bırakır, yere düşünce sekip yapışır.
## Lekeler bölüm boyunca kalır (kalıcı; çok birikince en eskileri silinir).
## Pikseller 2/3 dünya pikseli: 1080p'de 2x2 ekran pikseli (zemin dokularıyla aynı ızgara).
## Stil v2 (`ink`): aynı fizik, mürekkep çizimi (shaders/ink_blood.gdshader): damla = hız yönünde gözyaşı fırça
## zerresi, leke = koyu kenarlı düzensiz mürekkep lekesi + uydu noktalar, duvar akıntısı = incelen fırça izi,
## et parçası = mürekkep konturlu parça. Her katman tek üçgen dizisi (tek çizim çağrısı).

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
var _bos_cizildi := false   # v38: damla / akıntı / et parçası yokken boş kare bir kez çizildi (sonra çizim ve fizik atlanır)
const INK_SHADER: Shader = preload("res://shaders/ink_blood.gdshader")


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
	var im: ShaderMaterial = null
	im = ShaderMaterial.new()
	im.shader = INK_SHADER
	im.set_shader_parameter("telafi", telafi_of(lv))
	bl.material = im
	lv.add_child(bl)
	bl.stains = _Stains.new()
	bl.stains.material = im
	bl.stains.z_index = 1
	lv.add_child(bl.stains)
	lv.set_meta("blood", bl)
	return bl


static func _tone(col: Color, rng_k: float) -> Color:
	## Gerçekçi ton: damladan damlaya parlaklık değişir. v35 birleştirme: kırmızı kan daha doygun ve canlı (koyu
	## biyomda siyaha dönmesin): eskiden %12-30 koyulaşıyordu, şimdi %3-15 ve kırmızı kanal öne çıkar.
	var c := col.darkened(0.03 + 0.12 * rng_k)
	if c.r > maxf(c.g, c.b) * 2.0:
		c = Color(minf(1.0, c.r * 1.3 + 0.04), c.g * 0.7, c.b * 0.8)
	c.a = 1.0
	return c


static func telafi_of(lv: Node) -> float:
	## v35 birleştirme: gece ortam ışığı (Level CanvasModulate, Ötüken'de kırmızı ~0,32) kanı ve et şeridini siyaha
	## bastırıyordu. Kan / et gölgelendiricileri rengi bu katla önceden yükseltir (aydınlık biyomda ~1).
	if lv == null:
		return 1.0
	for ch in lv.get_children():
		if ch is CanvasModulate:
			var r: float = (ch as CanvasModulate).color.r
			return clampf(0.6 / maxf(r, 0.05), 1.0, 1.9)
	return 1.0


static func spray(pos: Vector2, dir: Vector2, col: Color, n: int, power := 1.0, back := true) -> void:
	## Vuruş sıçrantısı: darbe yönünde koni (çıkış), az miktar ters yöne (giriş), ince buğu
	var b := sys()
	if b == null:
		return
	# v22: vuruş kanı daha hafif (damla sayısı ×0,6; hızlı ardışık vuruşta ×0,35); ölüm fışkırması (burst) aynı
	if FX.in_hit:
		n = maxi(2, int(round(float(n) * (0.6 if FX.hit_k >= 0.99 else 0.35))))
	var n_bugu := n  # buğu kararı kısılmamış sayıya göre (görünüş aynı kalsın)
	n = Ayarlar.efekt_say(n, 2)  # v38: efekt yoğunluğu (damla sayısı)
	var d := dir.normalized() if dir.length() > 0.01 else Vector2.UP
	for i in n:
		var rev := back and i % 6 == 5
		var ang := d.angle() + (PI if rev else 0.0) + randf_range(-0.55, 0.55) - 0.25 * signf(d.x)
		var sp := randf_range(70.0, 300.0) * power * (0.5 if rev else 1.0)
		b._add(pos + Vector2(randf_range(-3, 3), randf_range(-3, 3)), Vector2(cos(ang), sin(ang)) * sp + Vector2(0, -randf_range(20, 90)), _tone(col, randf()), randf_range(1.4, 2.6), 1.0 if randf() < 0.55 else 2.0)
	if n_bugu >= 6:
		_mist(pos, d, col, 0.22 + 0.04 * minf(n_bugu, 30) / 10.0)


static func burst(pos: Vector2, dir: Vector2, col: Color, n: int, gibs := 0, flesh := true) -> void:
	## Ölüm: her yöne ağır sıçrantı + darbe yönünde fışkırma + et parçaları
	var b := sys()
	if b == null:
		return
	var d := dir.normalized() if dir.length() > 0.01 else Vector2.UP
	n = Ayarlar.efekt_say(n, 6, true)  # v38: efekt yoğunluğu; ölüm fışkırması Az'da da >= %65 (et parçaları aynı)
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


static func splat(pos: Vector2, col: Color, n: int, wall: bool) -> void:
	## v35 vahşet: iri mürekkep kan lekesi kümesi (parça duvara / yere çarptı); duvarda bir kısmı aşağı süzülür
	var b := sys()
	if b == null:
		return
	n = Ayarlar.efekt_say(n, 2, true)  # v38: efekt yoğunluğu (leke sayısı)
	for i in n:
		var q := pos + (Vector2(0.0, randf_range(-7.0, 7.0)) if wall else Vector2(randf_range(-7.0, 7.0), 0.0))
		var c := _tone(col, randf() * 0.6)
		if wall:
			var r := randf_range(2.0, 4.5)
			b.stains._ink_add(q, Vector2(r * randf_range(0.6, 0.9), r), c, 1)
			if randf() < 0.55:
				b._drips.append([q, randf_range(8.0, 18.0), randf_range(0.8, 2.6), c, b.stains.add_run(q, c)])
		else:
			b.stains.add(q, c, randi_range(3, 5), true)


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
	if Prof.on:
		var t0 := Time.get_ticks_usec()
		_physics_process_ic(delta)
		Prof.ekle(&"kan", t0)
		return
	_physics_process_ic(delta)


func _physics_process_ic(delta: float) -> void:
	if level == null or not is_instance_valid(level):
		return
	if _p.is_empty() and _drips.is_empty() and _gibs.is_empty():
		# v38: boşta her karede yeniden çizim yok; son kare (boş) bir kez temizlenir
		if not _bos_cizildi:
			_bos_cizildi = true
			queue_redraw()
		return
	_bos_cizildi = false
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
					_drips.append([wp, randf_range(6.0, 16.0), randf_range(0.6, 2.2), _c[i], stains.add_run(wp, _c[i])])
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
		if dr[4] != null:
			stains.grow_run(dr[4], nw.y)
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


func _ink_draw() -> void:
	var pts := PackedVector2Array()
	var uvs := PackedVector2Array()
	var cols := PackedColorArray()
	var idx := PackedInt32Array()
	for i in _p.size():
		var p := _p[i]
		var v := _v[i]
		var sp := v.length()
		var d := v / sp if sp > 1.0 else Vector2.DOWN
		var w := PX * _sz[i] * 0.85
		var L := w * (1.5 + minf(sp, 400.0) * 0.008)
		_Stains.quad(pts, uvs, cols, idx, p + d * L * 0.25, d * L, d.orthogonal() * w, _c[i], i % 64, 0)
	for g in _gibs:
		var n: int = g["s"]
		var sz := float(n) * PX * 1.7
		var ax := Vector2.from_angle(float(g["rot"]))
		_Stains.quad(pts, uvs, cols, idx, g["p"], ax * sz, ax.orthogonal() * sz * 0.8, g["col"], int(absf(float(g["w"])) * 7.0) % 64, 3)
	if not idx.is_empty():
		RenderingServer.canvas_item_add_triangle_array(get_canvas_item(), idx, pts, cols, uvs)


func _draw() -> void:
	if Prof.on:
		var t0 := Time.get_ticks_usec()
		_draw_ic()
		Prof.ekle(&"kan_ciz", t0)
		return
	_draw_ic()


func _draw_ic() -> void:
	_ink_draw()


class _Stains:
	extends Node2D
	## Kalıcı lekeler: yüzey lekeleri yatay yayılır, duvar lekeleri tek piksel; zamanla koyulaşır (oksitlenme).
	const PX := 2.0 / 3.0
	const MAX_STAINS := 7000
	var pts := PackedVector2Array()
	var cols := PackedColorArray()
	var _dirty := false
	var _age_t := 0.0
	# stil v2 mürekkep lekeleri: biçim başına bir dörtgen [merkez, boy, renk, tohum, tür]
	const MAX_INK := 1600
	var _ik: Array = []
	var _runs: Array = []  # duvar akıntıları: [üst, alt_y, renk, tohum, genişlik]
	# v38: _ik dörtgenleri önbellekte; yeni lekeler eklenir, büyüyen leke yerinde güncellenir, koyulaşma / kırpma
	# tümünü yeniden kurar (eskiden kirli her karede 1600 dörtgen baştan yazılıyordu). Çizim aynı.
	var _c_pa := PackedVector2Array()
	var _c_ua := PackedVector2Array()
	var _c_ca := PackedColorArray()
	var _c_ia := PackedInt32Array()
	var _c_n := 0
	var _c_tam := true

	static func quad(pts: PackedVector2Array, uvs: PackedVector2Array, cols: PackedColorArray, idx: PackedInt32Array, c: Vector2, ax: Vector2, ay: Vector2, col: Color, seed: int, kind: int) -> void:
		## c merkez; ax: u ekseni (tam uzunluk), ay: v ekseni (tam uzunluk). UV'de tohum ve tür kodlanır.
		var st := pts.size()
		var ox := float(seed) * 2.0
		var oy := float(kind) * 2.0
		pts.append(c - ax * 0.5 - ay * 0.5)
		pts.append(c + ax * 0.5 - ay * 0.5)
		pts.append(c - ax * 0.5 + ay * 0.5)
		pts.append(c + ax * 0.5 + ay * 0.5)
		uvs.append(Vector2(ox, oy))
		uvs.append(Vector2(ox + 1.0, oy))
		uvs.append(Vector2(ox, oy + 1.0))
		uvs.append(Vector2(ox + 1.0, oy + 1.0))
		for k in 4:
			cols.append(col)
		idx.append_array([st, st + 1, st + 2, st + 1, st + 3, st + 2])

	func _ink_add(c: Vector2, size: Vector2, col: Color, kind: int) -> void:
		_ik.append([c, size, col, randi() % 64, kind])
		if _ik.size() > MAX_INK:
			_ik = _ik.slice(_ik.size() - MAX_INK + 200)
			_c_tam = true
		_dirty = true

	func add_run(p: Vector2, col: Color) -> Array:
		var r := [p, p.y, col.darkened(0.08), randi() % 64, randf_range(0.9, 1.6)]
		_runs.append(r)
		if _runs.size() > 260:
			_runs = _runs.slice(60)
		_dirty = true
		return r

	func grow_run(r: Array, y: float) -> void:
		if y > float(r[1]) + 0.3:
			r[1] = y
			_dirty = true

	func add(p: Vector2, col: Color, spread: int, surface: bool) -> void:
		var ci := col.darkened(0.06)
		if surface:
			# yakındaki taze lekeye düşen damla onu büyütür: zemin kenarında ince kırmızı çizgi yerine
			# seyrek, iri, düzensiz mürekkep lekeleri
			var sy := p.y - PX * 0.5
			for k in range(_ik.size() - 1, maxi(-1, _ik.size() - 48), -1):
				var e: Array = _ik[k]
				var ec: Vector2 = e[0]
				var es: Vector2 = e[1]
				if int(e[4]) == 1 and absf(ec.y + es.y * 0.18 - sy) < 1.2 and absf(ec.x - p.x) < es.x * 0.5 + 1.5:
					var nw := minf(es.x + float(spread) * 0.45 + 0.6, 24.0)   # v35 birleştirme: göl daha geniş (15 → 24)
					var nh := clampf(nw * 0.36, 1.8, 5.0)
					e[1] = Vector2(nw, nh)
					e[0] = Vector2(lerpf(ec.x, p.x, 0.2), sy - nh * 0.18)
					if k < _c_n and not _c_tam:
						_c_yer(k, e)
					_dirty = true
					return
			var w := float(spread) * 1.2 + randf_range(2.2, 3.4)
			var h := clampf(w * 0.4, 1.6, 3.6)
			_ink_add(Vector2(p.x, sy - h * 0.18), Vector2(w, h), ci, 1)
		else:
			var r := randf_range(1.1, 1.9)
			_ink_add(p, Vector2(r, r * randf_range(0.9, 1.3)), ci, 1)

	func add_chunk(p: Vector2, col: Color, n: int) -> void:
		var s := float(n) * PX * 1.7
		_ink_add(p, Vector2(s, s * 0.7), col, 3)

	func _process(delta: float) -> void:
		# lekeler yavaşça koyulaşır (her 4 sn bir adım); v35 birleştirme: taban 0,12 → 0,34 (kurumuş kan koyu kızıl
		# kalır, siyaha dönmez: savaş sonrası oda kanlı okunur)
		_age_t += delta
		if _age_t > 4.0:
			_age_t = 0.0
			for i in cols.size():
				var c := cols[i]
				if c.v > 0.34:
					cols[i] = c.darkened(0.035)
			for e in _ik:
				if (e[2] as Color).v > 0.34:
					e[2] = (e[2] as Color).darkened(0.035)
			_c_tam = true
			_dirty = true
		if _dirty:
			_dirty = false
			queue_redraw()

	func _c_yer(k: int, e: Array) -> void:
		## önbellekteki k. lekenin köşeleri (quad ile aynı formül; renk ve UV değişmez)
		var c: Vector2 = e[0]
		var sz: Vector2 = e[1]
		var ax := Vector2(sz.x, 0)
		var ay := Vector2(0, sz.y)
		var b := k * 4
		_c_pa[b] = c - ax * 0.5 - ay * 0.5
		_c_pa[b + 1] = c + ax * 0.5 - ay * 0.5
		_c_pa[b + 2] = c - ax * 0.5 + ay * 0.5
		_c_pa[b + 3] = c + ax * 0.5 + ay * 0.5

	func _draw() -> void:
		if _c_tam:
			_c_tam = false
			_c_n = 0
			_c_pa.clear()
			_c_ua.clear()
			_c_ca.clear()
			_c_ia.clear()
		for k in range(_c_n, _ik.size()):
			var e: Array = _ik[k]
			var sz: Vector2 = e[1]
			quad(_c_pa, _c_ua, _c_ca, _c_ia, e[0], Vector2(sz.x, 0), Vector2(0, sz.y), e[2], e[3], e[4])
		_c_n = _ik.size()
		if _runs.is_empty():
			if not _c_ia.is_empty():
				RenderingServer.canvas_item_add_triangle_array(get_canvas_item(), _c_ia, _c_pa, _c_ca, _c_ua)
			return
		var pa := _c_pa.duplicate()
		var ua := _c_ua.duplicate()
		var ca := _c_ca.duplicate()
		var ia := _c_ia.duplicate()
		for r in _runs:
			var top: Vector2 = r[0]
			var L := float(r[1]) - top.y + 1.2
			var w := float(r[4])
			quad(pa, ua, ca, ia, top + Vector2(0, L * 0.5 - 0.4), Vector2(w, 0), Vector2(0, L), r[2], r[3], 2)
		if not ia.is_empty():
			RenderingServer.canvas_item_add_triangle_array(get_canvas_item(), ia, pa, ca, ua)
