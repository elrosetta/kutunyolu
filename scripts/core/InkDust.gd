class_name InkDust
extends Node2D
## v20 stil v2 yer tozu: ağır silahın başı yere indiğinde (çakma, yere değen baş üstü, yerde sürükleme, dalış inişi)
## kabaran mürekkep yıkaması toz bulutları, yere yatık sürünen toz, sekip duran moloz kırıkları, od silahında kor,
## kalıcı çatlak çıkartması (FX.decal) ve kısa sarsıntı (GroundSlamFX._juice). Biyoma göre renk: Ötüken orman toprağı,
## Bozkır sarı bozkır tozu, Kaf kar tozu (ak, mavimsi), Şahmeran mağara kumu, Tamu kül (koyu, korlu).
##
## Neden: v19'da GroundSlamFX v2'de görünmez yapılmış (piksel flaş / şok / moloz / çatlak mürekkebe uymuyordu) ve yerine
## yalnızca iki küçük soluk FX.dust kümesi kalmıştı; varsayılan stil v2 olunca ağır silahların yer tozu fiilen kayboldu.
## Bu düğüm o tozun mürekkep karşılığıdır (tek üçgen dizisi, shaders/ink_dust.gdshader; piksel kare yok).

const SHADER: Shader = preload("res://shaders/ink_dust.gdshader")

## biyom -> [koyu, orta, açık, mürekkep] (sRGB), kor var mı
const BIOME := {
	"otuken": [["3a3528", "77705a", "b8ad8e", "13110d"], false],
	"bozkir": [["5c4a30", "a08458", "dcc596", "24190e"], false],
	"kaf": [["7d90aa", "c2d2e6", "f4f8ff", "26303f"], false],
	"sahmeran": [["2c3529", "5a6552", "939b86", "0e120d"], false],
	"tamu": [["241d1f", "463c3e", "776a6a", "0c0809"], true],
	"cini_saray": [["423d4a", "7f7888", "bab2c2", "15121a"], false],
}
static var _mats: Dictionary = {}

var _puffs: Array = []   # [konum, hız, r0, ömür, yaş, gecikme, tür, tohum]
var _chips: Array = []   # [konum, hız, boy, ömür, yaş, tohum, durdu, seki, ışıltı]
var _embers: Array = []  # [konum, hız, boy, ömür, yaş]
var _t := 0.0
var back := false


static func _biome_id() -> String:
	var lv: Node = FX.level
	if lv != null and lv.get("biome") is Dictionary:
		return String(lv.biome.get("id", ""))
	return ""


static func _mat() -> ShaderMaterial:
	var bid := _biome_id()
	if not _mats.has(bid):
		var m := ShaderMaterial.new()
		m.shader = SHADER
		var cols: Array = []
		if BIOME.has(bid):
			for h in BIOME[bid][0]:
				cols.append(Color.html(h))
		else:
			# bilinmeyen biyom: FX.dust_col'dan türet
			var b := Color(FX.dust_col.r, FX.dust_col.g, FX.dust_col.b, 1.0)
			cols = [b.darkened(0.55), b.darkened(0.2), b.lightened(0.25), b.darkened(0.85)]
		var names := ["c_dark", "c_mid", "c_light", "c_ink"]
		for i in 4:
			var c: Color = (cols[i] as Color).srgb_to_linear()
			m.set_shader_parameter(names[i], Vector3(c.r, c.g, c.b))
		_mats[bid] = m
	return _mats[bid]


static func _spawn(pos: Vector2, back := false) -> InkDust:
	## back: kabaran bulutlar karakterlerin ardında (etkin z -1: süslerin önü, karoların / aktörlerin arkası; bulutun
	## yere taşan alt kısmı zeminin ardında kalır), önde yalnızca alçak sürünen toz, kırıklar ve kor
	if FX.root == null:
		return null
	var d := InkDust.new()
	d.material = _mat()
	d.position = pos
	d.back = back
	FX.root.add_child(d)
	return d


static func burst(pos: Vector2, facing := 1, power := 1.0, fire := false, lite := false) -> InkDust:
	## Yer çarpması tozu. power: 0,5 hafif değme · 1 ağır silah · 1,5 tam şarj / bitiriş · 2 boss
	var b := _spawn(pos, true)
	var d := _spawn(pos)
	if d == null or b == null:
		return null
	var p := clampf(power, 0.4, 2.2)
	var f := 1.0 if facing >= 0 else -1.0
	var embers: bool = fire or (BIOME.has(_biome_id()) and bool(BIOME[_biome_id()][1]))
	# 1) iki yana açılan V tutamları: dik ve hızlı kol + yatık gövde (ileri taraf daha dolgun)
	for side: float in [-1.0, 1.0]:
		var fw := 1.15 if side == f else 0.85
		var n := 2 + int(p * 1.6)
		for j in n:
			var a := deg_to_rad(randf_range(58.0, 76.0) if j == 0 else randf_range(16.0, 44.0))
			var sp := (randf_range(110.0, 160.0) if j == 0 else randf_range(70.0, 125.0)) * (0.55 + 0.45 * p) * fw
			var r0 := (8.0 + 6.0 * p) * randf_range(0.8, 1.15) * (0.8 if j == 0 else 1.0) * fw
			b._puffs.append([Vector2(side * randf_range(2.0, 6.0), -r0 * 0.3), Vector2(cos(a) * side, -sin(a)) * sp, r0 * randf_range(0.7, 1.15), randf_range(0.8, 1.15) * (0.75 + 0.25 * p), 0.0, randf_range(0.0, 0.04), 0, randi() % 8])
	# 2) ortada yükselen kabarık çekirdek
	for j in 1 + int(p):
		var r1 := (10.0 + 7.0 * p) * randf_range(0.85, 1.1)
		b._puffs.append([Vector2(randf_range(-5.0, 5.0), -r1 * 0.4), Vector2(randf_range(-14.0, 14.0), -randf_range(35.0, 65.0) * p), r1, randf_range(0.95, 1.25), 0.0, 0.02 + 0.03 * j, 0, randi() % 8])
	# 3) zemin boyunca dışa yuvarlanan alçak toz (şok cephesi), gecikmeli
	for side: float in [-1.0, 1.0]:
		var n2 := 2 + int(p * 2.0)
		for j in n2:
			var dist := (14.0 + 16.0 * float(j)) * (0.6 + 0.4 * p)
			var r2 := (7.0 + 5.0 * p) * (1.0 - 0.12 * float(j)) * randf_range(0.85, 1.1)
			d._puffs.append([Vector2(side * dist, -r2 * 0.25), Vector2(side * randf_range(40.0, 70.0) * p, -randf_range(4.0, 12.0)), r2, randf_range(0.5, 0.75), 0.0, 0.03 + 0.045 * float(j), 2, randi() % 8])
	# 4) moloz: çoğu ileri; üçte biri yüzeyi yalayarak alçaktan
	var nc := clampi(int((7.0 + 9.0 * p) * (0.5 if lite else 1.0)), 4, 26)
	for i in nc:
		var side2 := f if randf() < 0.62 else -f
		var low := randf() < 0.34
		var a2 := deg_to_rad(randf_range(8.0, 22.0) if low else randf_range(35.0, 80.0))
		var sp2 := randf_range(90.0, 160.0 + 70.0 * p) * (1.25 if low else 1.0)
		d._chips.append([Vector2(side2 * randf_range(0.0, 5.0), -2.0), Vector2(cos(a2) * side2, -sin(a2)) * sp2, randf_range(2.2, 4.2) * (0.8 + 0.25 * p), randf_range(0.8, 1.2), 0.0, randi() % 8, false, 0, randf()])
	# 5) kor (od silahı, Tamu külü)
	if embers:
		for i in 6 + int(6.0 * p):
			d._embers.append([Vector2(randf_range(-10.0, 10.0) * p, -2.0), Vector2(randf_range(-60.0, 60.0), -randf_range(60.0, 150.0)), randf_range(1.2, 2.2), randf_range(0.6, 1.1), 0.0])
	# 6) çatlak çıkartması (FX.decal: v2'de dallanan fırça çatlağı) + ezik zemin lekesi
	if not lite and p >= 0.85:
		FX.decal("decal_crack_%d" % (randi() % 2), pos + Vector2(0, 1), 0.0, 6.0 + 2.0 * p, 0.55 + 0.4 * p)
		d._puffs.append([Vector2(0, -1.5), Vector2.ZERO, 9.0 + 6.0 * p, 1.3, 0.0, 0.0, 2, randi() % 8])
	return d


static func drag(pos: Vector2, dir: float) -> void:
	## Yerde sürüklenen silah başının arkasında küçük yatık toz + bir iki kırık
	var d := _spawn(pos)
	if d == null:
		return
	d._puffs.append([Vector2(0, -2.0), Vector2(dir * randf_range(20.0, 45.0), -randf_range(6.0, 18.0)), randf_range(3.5, 5.5), randf_range(0.4, 0.6), 0.0, 0.0, 2, randi() % 8])
	if randf() < 0.6:
		d._puffs.append([Vector2(0, -3.0), Vector2(dir * randf_range(10.0, 25.0), -randf_range(20.0, 40.0)), randf_range(3.0, 4.5), randf_range(0.5, 0.7), 0.0, 0.0, 0, randi() % 8])
	if randf() < 0.5:
		d._chips.append([Vector2(0, -1.0), Vector2(dir * randf_range(40.0, 90.0), -randf_range(50.0, 110.0)), randf_range(1.3, 2.2), 0.6, 0.0, randi() % 8, false, 0, randf()])


## Yere değebilen ağır savuruşlar (çakma / sarsıntı bayrağı olmasa da başı yere inenler): hafif toz
const GROUND_SW := ["heavy", "down", "diag_down", "overhead", "overhead_2h", "step_down", "slam", "slam_2h", "windmill"]


static func ground_swing(it: Dictionary, c: Dictionary) -> bool:
	return InkTrail.weapon_class(String(it.get("id", ""))) in ["agir", "uzun"] and String(c.get("s", "")) in GROUND_SW


func _ready() -> void:
	z_index = -51 if back else 47
	top_level = true


func _process(delta: float) -> void:
	_t += delta
	var alive := false
	for s in _puffs:
		if _t < float(s[5]):
			alive = true
			continue
		s[4] = float(s[4]) + delta
		if float(s[4]) < float(s[3]):
			alive = true
		var v: Vector2 = s[1]
		v *= maxf(0.0, 1.0 - 3.6 * delta)
		v.y -= 9.0 * delta
		s[1] = v
		var np: Vector2 = (s[0] as Vector2) + v * delta
		# bulut yerin içine girmez
		np.y = minf(np.y, -float(s[2]) * 0.25)
		s[0] = np
	for c in _chips:
		c[4] = float(c[4]) + delta
		if float(c[4]) < float(c[3]):
			alive = true
		if c[6]:
			continue
		var v2: Vector2 = c[1]
		v2.y += 760.0 * delta
		var np2: Vector2 = (c[0] as Vector2) + v2 * delta
		if v2.y > 0.0 and np2.y >= 0.0:
			np2.y = 0.0
			if int(c[7]) >= 1 or absf(v2.y) < 60.0:
				c[6] = true
				v2 = Vector2.ZERO
			else:
				c[7] = int(c[7]) + 1
				v2 = Vector2(v2.x * 0.5, -v2.y * 0.3)
		c[1] = v2
		c[0] = np2
	for e in _embers:
		e[4] = float(e[4]) + delta
		if float(e[4]) < float(e[3]):
			alive = true
		var v3: Vector2 = e[1]
		v3 = v3.move_toward(Vector2(0, -35.0), 90.0 * delta)
		e[1] = v3
		e[0] = (e[0] as Vector2) + (v3 + Vector2(sin(float(e[4]) * 9.0 + float(e[2]) * 3.0) * 16.0, 0.0)) * delta
	if not alive:
		queue_free()
		return
	queue_redraw()


func _quad(pts: PackedVector2Array, uvs: PackedVector2Array, cols: PackedColorArray, idx: PackedInt32Array, c: Vector2, hx: Vector2, hy: Vector2, typ: int, seed: int, age: float) -> void:
	var st := pts.size()
	pts.append_array([c - hx - hy, c + hx - hy, c - hx + hy, c + hx + hy])
	var ux := float(typ) * 2.0
	var vy := float(seed) * 2.0
	uvs.append_array([Vector2(ux, vy), Vector2(ux + 1.0, vy), Vector2(ux, vy + 1.0), Vector2(ux + 1.0, vy + 1.0)])
	var cl := Color(1, 1, 1, age)
	cols.append_array([cl, cl, cl, cl])
	idx.append_array([st, st + 1, st + 2, st + 1, st + 3, st + 2])


func _draw() -> void:
	var pts := PackedVector2Array()
	var uvs := PackedVector2Array()
	var cols := PackedColorArray()
	var idx := PackedInt32Array()
	# önce yere yatık tozlar ve kırıklar, sonra kabaran bulutlar (bulut kırığın önünde), en son kor
	for pass_i in 2:
		for s in _puffs:
			if _t < float(s[5]):
				continue
			var k := float(s[4]) / float(s[3])
			if k >= 1.0:
				continue
			var typ: int = s[6]
			if (pass_i == 0) != (typ == 2):
				continue
			var r0: float = s[2]
			# büyüme: hızlı açılış, sonra yavaş kabarma
			var r := r0 * (0.5 + 0.5 * (1.0 - pow(1.0 - minf(k / 0.25, 1.0), 3.0)) + 0.55 * k)
			var hx := Vector2(r * (1.5 if typ == 2 else 1.0), 0)
			var hy := Vector2(0, r * (0.62 if typ == 2 else 0.92))
			_quad(pts, uvs, cols, idx, s[0], hx, hy, typ, int(s[7]), k)
		if pass_i == 0:
			for c in _chips:
				var k2 := float(c[4]) / float(c[3])
				if k2 >= 1.0:
					continue
				var sz: float = c[2]
				var v: Vector2 = c[1]
				var ang := float(c[5]) * 0.8 + (float(c[4]) * v.x * 0.08 if not c[6] else 0.0)
				var hx2 := Vector2.from_angle(ang) * sz
				var hy2 := Vector2.from_angle(ang + PI * 0.5) * sz * 0.8
				_quad(pts, uvs, cols, idx, (c[0] as Vector2) + Vector2(0, -sz * 0.6), hx2, hy2, 1, int(c[5]), k2)
	for e in _embers:
		var k3 := float(e[4]) / float(e[3])
		if k3 >= 1.0:
			continue
		var es: float = float(e[2]) * (1.0 - 0.5 * k3)
		_quad(pts, uvs, cols, idx, e[0], Vector2(es, 0), Vector2(0, es), 3, 0, k3)
	if idx.is_empty():
		return
	RenderingServer.canvas_item_add_triangle_array(get_canvas_item(), idx, pts, cols, uvs)
