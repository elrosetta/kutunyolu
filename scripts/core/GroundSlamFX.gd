class_name GroundSlamFX
extends Node2D
## v16 yer çarpması: ağır silahın başı yere indiğinde (çekiç, gürz, dev kılıç, bitiriş, boss çakması).
## Piksel sanatı, aşamalı, yerel; ekranı yıkamaz. Düğüm temas noktasına, zemin yüzeyine (karonun üst satırı) konur.
##   0-2 kare     temas flaşı: yalnız başın değdiği yerde basık mercek + yukarı yarım yelpaze ışın (toplamalı)
##   0-300 ms     şok cephesi: zemin çizgisini izleyerek iki yana koşan alçak toprak kabarması; arkasında yüzey
##                bir tık "kalkar" (açık çizgi, piksel düşürmeyle söner). Duvar / boşlukta durur
##   0-750 ms     toz: temas noktasında iki yana açılan V tutamları + cephenin geçtiği yerden yuvarlanan alçak toz
##   moloz        biyom toprağı tonlarında 1-3 px taşlar (FX.dust_col'dan); yerçekimi, yüzey profiline sekme,
##                durunca göz kırparak söner. Bir kısmı yüzeyi yalayarak alçaktan fırlar
##   kıvılcım     metal silahlarda 1 px çizgi kıvılcımlar (toplamalı, kısa)
##   kor          od silahlarında yükselen, titreyen korlar
##   çatlak       GroundCrack çıkartması (Level.decal_root): zemin çizgisini izleyen kırık çizgi + çukur + kenar
## Hepsi 1 px dünya ızgarasına oturur; gradyan, bulanıklık ve alfa solması yok (erime: piksel düşürme).
## power: 0,6 kılıç inişi · 1 ağır silah · 1,5 tam şarj / bitiriş · 2 boss. Kullanım: FX.ground_slam(...).

var power := 1.0
var facing := 1
var col := Color(1.0, 0.85, 0.6)       # silah rengi: flaşın ikinci karesi ve sıcak yüzey çizgisi bununla boyanır
var metal := true
var fire := false
var juice := true
var life := 1.3

const GAP := 9999.0
const T_FLASH := 0.034
const T_SHOCK := 0.3
const C_WHITE := Color(1.0, 0.98, 0.92)
const C_SPARK_HOT := Color(1.0, 0.96, 0.78)
const C_SPARK := Color(1.0, 0.72, 0.3)
const C_SPARK_DIM := Color(0.8, 0.32, 0.1)
const C_EMBER_HOT := Color(1.0, 0.88, 0.45)
const C_EMBER := Color(1.0, 0.55, 0.15)
const C_EMBER_DIM := Color(0.6, 0.16, 0.06)

var _R := 70.0
var _W := 120
var _gy := PackedFloat32Array()   # yerel zemin yüksekliği (x = -_W.._W), boşlukta GAP
var _lim := {-1: 0.0, 1: 0.0}      # cephenin o yönde ulaşabileceği en uzak mesafe
var _t := 0.0
var _frame := 0
var _rays: Array = []
var _rocks: Array = []
var _puffs: Array = []
var _sparks: Array = []
var _embers: Array = []
var _roll_i := {-1: 0, 1: 0}
var _back: Node2D
var _glow: Node2D
# palet (biyom tozundan türetilir; düz tonlar)
var _dd := Color()
var _dm := Color()
var _dl := Color()
var _rd := Color()
var _rm := Color()
var _rl := Color()
var _crest := Color()


class Layer extends Node2D:
	var fx: GroundSlamFX
	var kind := 0
	func _draw() -> void:
		if fx:
			if kind == 0:
				fx._draw_back(self)
			else:
				fx._draw_glow(self)


func _ready() -> void:
	position = position.round()
	z_index = 46
	var m := CanvasItemMaterial.new()
	m.light_mode = CanvasItemMaterial.LIGHT_MODE_UNSHADED
	material = m
	_back = Layer.new()
	_back.fx = self
	_back.kind = 0
	_back.z_index = -16
	var bm := CanvasItemMaterial.new()
	bm.light_mode = CanvasItemMaterial.LIGHT_MODE_UNSHADED
	_back.material = bm
	add_child(_back)
	_glow = Layer.new()
	_glow.fx = self
	_glow.kind = 1
	_glow.z_index = 15
	var gm := CanvasItemMaterial.new()
	gm.light_mode = CanvasItemMaterial.LIGHT_MODE_UNSHADED
	gm.blend_mode = CanvasItemMaterial.BLEND_MODE_ADD
	_glow.material = gm
	add_child(_glow)
	power = clampf(power, 0.4, 2.2)
	# temas noktası zemin yüzeyine oturtulur (çağıran ayak konumu verse de)
	var lv: Node = FX.level
	if lv and lv.has_method("ground_y_below"):
		var gy0: float = lv.ground_y_below(global_position + Vector2(0, -12), 40.0)
		if gy0 >= 0.0:
			global_position.y = gy0
	_R = 26.0 + 38.0 * power
	_W = int(_R) + 48
	_palette()
	_sample_ground()
	# v2 yakın kamerada 1 px dünya ızgarası 4 ekran pikseline büyür: piksel katmanlar yerine mürekkep
	visible = false
	# v20: iki küçük soluk FX.dust kümesi yerine mürekkep toz bulutları, moloz, kor ve çatlak (InkDust)
	InkDust.burst(global_position, facing, power, fire, not juice)
	if juice:
		_juice()


func _palette() -> void:
	# biyom tozu biraz griye çekilir (gece sahnesinde zeytin rengi top gibi durmasın)
	var b := Color(FX.dust_col.r, FX.dust_col.g, FX.dust_col.b, 1.0).lerp(Color(0.62, 0.6, 0.62), 0.3)
	_dd = b.darkened(0.38)
	_dm = b.darkened(0.06)
	_dl = b.lightened(0.28)
	_crest = b.lightened(0.5)
	_rd = b.darkened(0.62)
	_rm = b.darkened(0.36)
	_rl = b.darkened(0.04)


func _sample_ground() -> void:
	## Zemin profili: her sütun için karonun üst satırı (yerel y). Karo başına bir sorgu.
	_gy.resize(2 * _W + 1)
	var lv: Node = FX.level
	var ok: bool = lv != null and lv.has_method("ground_y_below")
	var ts := float(Level.TS)
	var cache := {}
	var gp := global_position
	for i in range(-_W, _W + 1):
		var v := 0.0
		if ok:
			var tx := int(floor((gp.x + i) / ts))
			if not cache.has(tx):
				var gy: float = lv.ground_y_below(Vector2((tx + 0.5) * ts, gp.y - 30.0), 72.0)
				cache[tx] = (gy - gp.y) if gy >= 0.0 else GAP
			v = cache[tx]
		_gy[i + _W] = v
	# cephe yalnız aynı yüzeyde koşar: basamak / boşlukta durur
	for side: int in [-1, 1]:
		var x := 0
		while absi(x) < _W - 1 and absf(_g(x + side)) < 5.0:
			x += side
		_lim[side] = float(absi(x))


func _g(x: float) -> float:
	var i := int(floor(x)) + _W
	if i < 0 or i >= _gy.size():
		return GAP
	return _gy[i]


func _build() -> void:
	var p := power
	# ışınlar: yalnız üst yarım düzlemde, yelpaze
	var nr := 5
	for i in nr:
		var a := -PI * (0.1 + 0.8 * float(i) / float(nr - 1)) + randf_range(-0.12, 0.12)
		_rays.append({"a": a, "l": randf_range(0.7, 1.0) * (1.0 if i % 2 == 0 else 0.6)})
	# moloz: çoğu ileri; üçte biri yüzeyi yalayarak alçaktan
	var n := clampi(int(7.0 + 9.0 * p), 7, 28)
	for i in n:
		var side := facing if randf() < 0.6 else -facing
		var low := randf() < 0.34
		var a := deg_to_rad(randf_range(7.0, 20.0) if low else randf_range(34.0, 80.0))
		var sp := randf_range(90.0, 150.0 + 70.0 * p) * (1.3 if low else 1.0)
		var r := randf()
		var sz := (2 if r < 0.5 else 1) if low else (3 if r < 0.14 + 0.14 * p else (2 if r < 0.75 else 1))
		_rocks.append({"p": Vector2(side * randf_range(0.0, 3.0 + 2.0 * p), 0.0), "v": Vector2(cos(a) * side, -sin(a)) * sp,
			"s": sz, "sh": randi() % 3, "life": randf_range(0.5, 0.85), "b": 0, "rest": false})
	# toz: temas noktasında iki yana açılan V tutamları
	for side: int in [-1, 1]:
		var np := 2 + (1 if p >= 1.1 else 0) + (1 if p >= 1.5 else 0)
		for j in np:
			# ilki dik ve hızlı (V'nin kolu), sonrakiler yatık ve yavaş (taban)
			var a := deg_to_rad(randf_range(60.0, 74.0) if j == 0 else randf_range(14.0, 38.0))
			var sp := (randf_range(95.0, 125.0) if j == 0 else randf_range(55.0, 95.0)) * (0.6 + 0.4 * p)
			var r1 := (2.2 + 2.2 * p) * (0.8 if j == 0 else 1.0) * randf_range(0.85, 1.1)
			_add_puff(Vector2(side * 2.0, -1.0), Vector2(cos(a) * side, -sin(a)) * sp, r1, randf_range(0.45, 0.65), 0.0, 0.9 if j == 0 else 0.7)
	# kıvılcım
	if metal:
		for i in 3 + int(3.0 * p):
			var side := facing if randf() < 0.65 else -facing
			var a := deg_to_rad(randf_range(18.0, 75.0))
			_sparks.append({"p": Vector2(side * 2.0, -2.0), "v": Vector2(cos(a) * side, -sin(a)) * randf_range(160.0, 290.0),
				"life": randf_range(0.14, 0.28)})
	# kor
	if fire:
		for i in 6 + int(6.0 * p):
			_embers.append({"p": Vector2(randf_range(-8.0, 8.0) * p, -1.0), "v": Vector2(randf_range(-40.0, 40.0), -randf_range(50.0, 120.0)),
				"life": randf_range(0.6, 1.1), "ph": randi() % 3, "w": randf() * TAU})


func _add_puff(p: Vector2, v: Vector2, r1: float, lf: float, delay := 0.0, asp := 0.8) -> void:
	## Toz tutamı: bir ana + 2-3 küçük yumru (karnabahar silüeti); asp < 1 yere yatık
	var lobes: Array = [[Vector2.ZERO, 1.0]]
	var dirx := signf(v.x) if absf(v.x) > 1.0 else 1.0
	for j in 2 + randi() % 2:
		var a := -PI * 0.5 + dirx * randf_range(0.3, 1.5) * (1.0 if j % 2 == 0 else -0.6)
		lobes.append([Vector2.from_angle(a) * randf_range(0.6, 0.95), randf_range(0.5, 0.72)])
	var frag: Array = []
	for j in 3:
		frag.append(Vector2.from_angle(randf() * TAU) * randf_range(0.35, 0.7))
	_puffs.append({"p": p, "v": v, "r1": r1, "life": lf, "t0": _t + delay, "frag": frag, "lobes": lobes, "asp": asp})


func _juice() -> void:
	# kısa, ağır, aşağı yönlü: travma sarsıntısı (dikey eksen), kamera itişi, titreşim, yerel ışık
	Game.shake_dir(clampf(0.14 + 0.13 * power, 0.0, 0.48), Vector2.DOWN)
	Game.kick(Vector2.DOWN, 2.0 + 2.4 * power)
	Game.rumble(0.45 + 0.25 * power, 0.25, 0.1 + 0.06 * power)
	FX.flash_light(global_position + Vector2(0, -6), col.lerp(Color(1.0, 0.8, 0.55), 0.5), 46.0 + 26.0 * power, 1.0, 0.14)


class GroundCrack extends Node2D:
	## Kalıcı yer çatlağı: piksel listesi; 6 sn sonra pikseller rastgele düşerek erir.
	var pixels: Array = []
	var cols: Array = []
	var life := 7.0
	var _t := 0.0
	var _melt := 0.0

	func _ready() -> void:
		z_index = 1
		var m := CanvasItemMaterial.new()
		m.light_mode = CanvasItemMaterial.LIGHT_MODE_UNSHADED
		material = m
		position = position.round()

	func _process(delta: float) -> void:
		_t += delta
		if _t >= life:
			queue_free()
			return
		var mk := clampf((_t - (life - 1.5)) / 1.5, 0.0, 1.0)
		if absf(mk - _melt) > 0.08 or (mk >= 1.0 and _melt < 1.0):
			_melt = mk
			queue_redraw()

	func _draw() -> void:
		var i := 0
		for e in pixels:
			i += 1
			if _melt > 0.0 and float((i * 7919) % 1000) / 1000.0 < _melt:
				continue
			var q: Vector2i = e[0]
			draw_rect(Rect2(q.x, q.y, 1, 1), cols[int(e[1])])


# ------------------------------------------------------------------ güncelleme
func _process(delta: float) -> void:
	if Prof.on:
		var t0 := Time.get_ticks_usec()
		_process_ic(delta)
		Prof.ekle(&"fx", t0)
		return
	_process_ic(delta)


func _process_ic(delta: float) -> void:
	# flaş evresi gerçek zamanda akar (vuruş duraklaması flaşı en çok 2 karede tutar; kalan donar)
	_t += maxf(delta, 1.0 / 60.0) if _t < T_FLASH else delta
	_frame += 1
	if _t >= life:
		queue_free()
		return
	_spawn_rolling()
	_step(delta)
	queue_redraw()
	_back.queue_redraw()
	_glow.queue_redraw()


func _front(side: int) -> float:
	var k := _ph(0.0, T_SHOCK, _t)
	return minf(_R * _eo(k), float(_lim[side]))


func _spawn_rolling() -> void:
	## cephe belirli mesafeleri geçtikçe arkasında alçak, dışa yuvarlanan toz tutamı bırakır
	var marks := [0.22, 0.4, 0.58, 0.76, 0.95]
	for side: int in [-1, 1]:
		var i: int = _roll_i[side]
		if i >= marks.size():
			continue
		var fx := _front(side)
		if fx >= _R * float(marks[i]) - 0.5:
			_roll_i[side] = i + 1
			if fx < float(_lim[side]) - 1.0 or i == 0:
				var r1 := (2.2 + 2.0 * power) * (1.0 - 0.4 * float(marks[i])) * randf_range(0.85, 1.1)
				_add_puff(Vector2(side * fx, _g(side * fx) - 1.0), Vector2(side * randf_range(30.0, 50.0) * power, -randf_range(8.0, 18.0)), r1, randf_range(0.34, 0.48), 0.0, 0.58)
		elif fx >= float(_lim[side]) - 0.5 and _ph(0.0, T_SHOCK, _t) >= 1.0:
			_roll_i[side] = marks.size()


func _step(delta: float) -> void:
	for r in _rocks:
		if r["rest"]:
			continue
		var v: Vector2 = r["v"]
		var p: Vector2 = r["p"]
		v.y += 760.0 * delta
		var np := p + v * delta
		var g := _g(np.x)
		# basamağa çarptı: geri sek
		if g < p.y - 3.0 and g < GAP:
			v.x = -v.x * 0.3
			np.x = p.x
			g = _g(np.x)
		if v.y > 0.0 and np.y >= g:
			np.y = g
			if int(r["b"]) >= 1 or absf(v.y) < 60.0:
				r["rest"] = true
				v = Vector2.ZERO
			else:
				r["b"] = int(r["b"]) + 1
				v.y = -v.y * 0.32
				v.x *= 0.55
		r["p"] = np
		r["v"] = v
	for s in _puffs:
		if _t < float(s["t0"]):
			continue
		var v: Vector2 = s["v"]
		v *= maxf(0.0, 1.0 - 4.2 * delta)
		v.y -= 10.0 * delta
		s["v"] = v
		s["p"] = s["p"] + v * delta
	for s in _sparks:
		var v: Vector2 = s["v"]
		v.y += 520.0 * delta
		v *= 1.0 - 2.0 * delta
		s["v"] = v
		s["p"] = s["p"] + v * delta
	for e in _embers:
		var v: Vector2 = e["v"]
		v.y += -30.0 * delta
		v = v.move_toward(Vector2(0, -40), 60.0 * delta)
		e["w"] = float(e["w"]) + delta * 9.0
		e["v"] = v
		e["p"] = e["p"] + (v + Vector2(sin(float(e["w"])) * 14.0, 0)) * delta


# ------------------------------------------------------------------ yardımcılar
static func _eo(k: float) -> float:
	k = clampf(k, 0.0, 1.0)
	return 1.0 - pow(1.0 - k, 3.0)


static func _ph(t0: float, t1: float, t: float) -> float:
	return clampf((t - t0) / (t1 - t0), 0.0, 1.0)


static func _hash(i: int, s: int) -> float:
	return float(absi(i * 7919 + s * 104729) % 1000) / 1000.0


static func _hash2(x: int, y: int, s: int) -> float:
	var v := sin(float(x) * 12.9898 + float(y) * 78.233 + float(s) * 37.719) * 43758.5453
	return v - floorf(v)


func _blob(ci: CanvasItem, c: Vector2, rx: float, ry: float, cl: Color, drop := 0.0, seed_v := 0) -> void:
	## Yere oturan piksel elips: zemin satırına (ve altına) taşan satırlar kesilir, toz yerin içine girmez
	var irx := int(round(rx))
	var iry := int(round(ry))
	var cx := floorf(c.x)
	var cy := floorf(c.y)
	if irx <= 0 or iry <= 0:
		if cy < _g(cx):
			ci.draw_rect(Rect2(cx, cy, 1, 1), cl)
		return
	var gmin := minf(_g(cx - irx), minf(_g(cx), _g(cx + irx)))
	for y in range(-iry, iry + 1):
		var yy := cy + y
		if yy >= gmin:
			break
		var f := float(y) / (float(iry) + 0.5)
		var hw := int(floor(sqrt(maxf(0.0, 1.0 - f * f)) * (float(irx) + 0.5)))
		if drop <= 0.0:
			ci.draw_rect(Rect2(cx - hw, yy, 2 * hw + 1, 1), cl)
			continue
		# erime: dünya ızgarasına sabit desenle piksel düşürme (tutam yerinde dağılır, kıpırdamaz)
		# kenarlar önce erir: eşik merkezden uzaklıkla düşer
		for xx in range(int(cx) - hw, int(cx) + hw + 1):
			var dx := (float(xx) - cx) / (float(irx) + 0.5)
			var dn := sqrt(minf(1.0, dx * dx + f * f))
			if _hash2(xx, int(yy), seed_v) * (1.25 - 0.7 * dn) >= drop:
				ci.draw_rect(Rect2(xx, yy, 1, 1), cl)



func _line_px(ci: CanvasItem, a: Vector2, b: Vector2, cl: Color) -> void:
	var d := b - a
	var n := int(maxf(absf(d.x), absf(d.y)))
	for i in n + 1:
		var q := (a + d * (float(i) / maxf(1.0, float(n)))).floor()
		ci.draw_rect(Rect2(q, Vector2.ONE), cl)


# ------------------------------------------------------------------ çizim
func _draw() -> void:
	_draw_shock()
	_draw_rocks()


func _draw_shock() -> void:
	if _t >= T_SHOCK + 0.05:
		return
	var k := _ph(0.0, T_SHOCK, _t)
	var h := (1.5 + 2.2 * power) * pow(1.0 - k, 0.7)
	var wl := int(round(3.0 + 3.0 * power * (1.0 - 0.5 * k)))
	for side: int in [-1, 1]:
		var fx := floorf(_front(side))
		var stopped: bool = fx >= float(_lim[side]) - 0.5 and _lim[side] < _R
		# yüzey kalkması: cephenin arkasında açık renkli yüzey çizgisi, içten dışa doğru erir
		var x := floorf(fx * (0.3 + 0.55 * k))
		while x <= fx - wl:
			var gx := side * x
			var g := _g(gx)
			if g < GAP and _hash(int(x), side + 3) >= 0.2 + 0.8 * k:
				draw_rect(Rect2(gx, g - 1, 1, 1), _dl)
			x += 1.0
		# rüzgâr çizgileri: cephenin önünde yere paralel 1 px basınç çizgileri, dışa kayıp kısalır
		if k < 0.85:
			for li in 2:
				var ln := (8.0 + 9.0 * power) * (1.0 - k) * (1.0 if li == 0 else 0.6)
				var lx0 := fx + 2.0 + 3.0 * li - ln * 0.4
				var xx := lx0
				while xx < lx0 + ln:
					var gx2 := side * xx
					var g2 := _g(gx2)
					if g2 < GAP and _hash(int(xx) + li * 57, side + 21) >= k * 0.9:
						draw_rect(Rect2(gx2, g2 - 2.0 - 3.0 * li - (1.0 if li == 1 and power > 1.2 else 0.0), 1, 1), _crest if li == 0 else _dl)
					xx += 1.0
		if stopped and k > 0.45:
			continue
		# kabarma: cephede kalkan toprak sırtı. Önü dik, arkası yatık (dalga gibi); tepe açık, gövde orta, arka koyu
		for j in wl:
			var cx := side * (fx - j)
			var g0 := _g(cx)
			if g0 >= GAP:
				continue
			var hj := int(round(h * (1.0 - float(j) / float(wl)) if j > 0 else h * 0.75))
			for y in hj:
				var cl := _dm if y < hj - 1 else (_crest if j <= 1 else _dl)
				if j >= wl - 2 and y < hj - 1:
					cl = _dd
				draw_rect(Rect2(cx, g0 - 1 - y, 1, 1), cl)
		# sırttan kopan tek tük toprak tanesi (cephenin hemen üstünde)
		if k < 0.75:
			for q in 2:
				var hx := _hash(_frame + q * 17, side + 5)
				var px := side * (fx - 1.0 - floorf(hx * 3.0))
				var py := _g(px) - h - 1.0 - floorf(_hash(_frame + q * 31, side + 9) * 3.0)
				draw_rect(Rect2(px, floorf(py), 1, 1), _dl)



func _draw_rocks() -> void:
	for r in _rocks:
		var age: float = _t / float(r["life"])
		if age >= 1.0:
			continue
		# durduktan / ömrün sonunda göz kırparak söner
		if age > 0.7 and (_frame / 2) % 2 == 0:
			continue
		var p: Vector2 = (r["p"] as Vector2).floor()
		var s: int = r["s"]
		var sh: int = r["sh"]
		var base := _rm if sh != 0 else _rd
		if s == 1:
			draw_rect(Rect2(p.x, p.y - 1, 1, 1), _rl if sh == 2 else base)
			continue
		draw_rect(Rect2(p.x, p.y - s, s, s), base)
		# ışık üst-sol, gölge alt satır
		draw_rect(Rect2(p.x, p.y - s, s - 1, 1), _rl)
		draw_rect(Rect2(p.x, p.y - 1, s, 1), _rd)


func _draw_back(ci: CanvasItem) -> void:
	# üç geçiş, her geçişte tüm yumrular: koyu silüet → orta ton (üst-sola kayık) → ışık (yalnız tazeyken).
	# Yaşlanınca tutam büyümeyi sürdürür ama pikselleri sabit desenle düşerek erir (alfa yok).
	for band in 3:
		var si := 0
		for s in _puffs:
			si += 1
			var lt := (_t - float(s["t0"])) / float(s["life"])
			if lt < 0.0 or lt >= 1.0:
				continue
			if band == 2 and lt > 0.34:
				continue
			var r1: float = s["r1"]
			var asp: float = s["asp"]
			var c: Vector2 = s["p"]
			var pr := r1 * (0.4 + 0.6 * _eo(lt / 0.3) + 0.25 * _ph(0.3, 1.0, lt))
			var drop := _ph(0.5, 1.0, lt)
			drop = drop * (0.6 + 0.4 * drop)
			if band == 1:
				drop = minf(1.0, drop * 1.35 + 0.05 * float(drop > 0.0))
			for lb in s["lobes"]:
				var lc: Vector2 = c + (lb[0] as Vector2) * pr
				var lr: float = pr * float(lb[1])
				match band:
					0:
						_blob(ci, lc, lr, lr * asp, _dd, drop, si)
					1:
						_blob(ci, lc + Vector2(-lr * 0.18, -lr * 0.3), lr * 0.72, lr * 0.72 * asp, _dm, drop, si + 50)
					2:
						_blob(ci, lc + Vector2(-lr * 0.32, -lr * 0.48), lr * 0.36, lr * 0.36 * asp, _dl)


func _draw_glow(ci: CanvasItem) -> void:
	var t := _t
	var p := power
	var hot := col.lerp(C_WHITE, 0.45)
	# temas flaşı: 1. kare beyaz mercek + yarım disk + ışın; 2. kare silah renginde küçülen mercek
	if t < T_FLASH * 0.5:
		var lw := int(round(5.0 + 4.0 * p))
		ci.draw_rect(Rect2(-lw, -2, 2 * lw + 1, 2), C_WHITE)
		_half_disc(ci, int(round(2.0 + 2.0 * p)), C_WHITE)
		for r in _rays:
			var d := Vector2.from_angle(float(r["a"]))
			var l: float = (9.0 + 9.0 * p) * float(r["l"])
			_line_px(ci, (d * (3.0 + 2.0 * p)).round(), (d * l).round(), C_WHITE)
	elif t < T_FLASH:
		var lw := int(round(7.0 + 5.0 * p))
		ci.draw_rect(Rect2(-lw, -1, 2 * lw + 1, 1), hot)
		_half_disc(ci, int(round(1.0 + 1.5 * p)), hot)
	# sıcak yüzey çizgisi: temas çevresinde zemin bir an kızarır, dışa doğru piksel düşerek söner
	var hk := _ph(0.0, 0.12, t)
	if hk < 1.0:
		var hl := int((7.0 + 7.0 * p) * (0.6 + 0.4 * hk))
		var hc := Color(hot.r, hot.g * 0.85, hot.b * 0.6, 0.75)
		for x in range(-hl, hl + 1):
			if absf(_g(x)) > 3.0:
				continue
			if _hash(x, 11) < hk * (0.4 + 0.6 * float(absi(x)) / float(hl + 1)):
				continue
			ci.draw_rect(Rect2(x, _g(x), 1, 1), hc)
	# kıvılcımlar: hız yönünde 1 px çizgi
	for s in _sparks:
		var age: float = t / float(s["life"])
		if age >= 1.0:
			continue
		var v: Vector2 = s["v"]
		var cl := C_SPARK_HOT if age < 0.35 else (C_SPARK if age < 0.7 else C_SPARK_DIM)
		var pp: Vector2 = s["p"]
		var ln := clampf(v.length() * 0.028, 1.0, 6.0)
		_line_px(ci, pp.floor(), (pp - v.normalized() * ln).floor(), cl)
	# korlar: titrer, söner
	for e in _embers:
		var age: float = t / float(e["life"])
		if age >= 1.0:
			continue
		var ph: int = (_frame + int(e["ph"])) % 3
		if age > 0.7 and ph != 0:
			continue
		var cl := C_EMBER_HOT if (ph == 0 and age < 0.4) else C_EMBER
		if age > 0.65:
			cl = C_EMBER_DIM
		ci.draw_rect(Rect2((e["p"] as Vector2).floor(), Vector2.ONE), cl)


func _half_disc(ci: CanvasItem, r: int, cl: Color) -> void:
	## Zeminin üstünde kalan yarım disk (y <= -1)
	var rr := float(r * r + r)
	for y in range(-r, 0):
		var hw := int(floor(sqrt(maxf(0.0, rr - float(y * y)))))
		ci.draw_rect(Rect2(-hw, y, 2 * hw + 1, 1), cl)
