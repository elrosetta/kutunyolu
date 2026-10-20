class_name Gore
extends Node2D
## v36: Dead Cells tarzı ölüm patlaması (v35'in sprite dilimleme / kalıcı ceset yolunun yerine).
## Yaratık öldüğünde gövde anında kaybolur; yerinde, gövde silueti içinden sıkışık bir patlama çıkar:
##  - et: 40-90+ küçük düzensiz kan topağı (koyu kızıl / parlak kırmızı / pembe ışıklı, birkaç iri et topağı) + ince
##    damlalar + kısa kan buğusu; öldürücü darbe yönüne ve yukarı eğilimli fırlar, yerçekimiyle yay çizer,
##  - taş: gri moloz kırıntısı + toz bulutu; ruh: mürekkep / ektoplazma tülleri (yukarı süzülür); ateş: korlar.
## Topak / damla zemine düşünce küçük leke, duvara çarpınca duvar lekesi olur; lekeler söner (zemin 8-15 sn, duvar
## 3-6 sn, damla lekesi 4-8 sn). Güç (aşırı hasar, kritik, ağır vuruş, bitiriş) ve ölçek (seçkin / boss) topak sayısını
## ve hızını büyütür. Bütün zerreler bu tek düğümde paralel dizilerde (düğüm yok), çizim tek üçgen dizisi + birkaç buğu
## dairesi: 10 eşzamanlı öldürüşte bile ihmal edilebilir maliyet. Renkler gece ortam ışığına karşı (Blood.telafi_of)
## önceden yükseltilir: koyu biyomda kırmızı okunur kalır.

const MAX_P := 3200
const MAX_ST := 600
const MAT_ET := 0
const MAT_TAS := 1
const MAT_RUH := 2
const MAT_KOR := 3
const TAS := ["balbal", "buz_balbali", "cini_golemi"]
const KOR := ["sihirli_kandil", "isilti_bocegi", "od_iyesi"]
# zerre türleri
const K_TOPAK := 0
const K_DAMLA := 1
const K_MOLOZ := 2
const K_TUL := 3
const K_KOR := 4
const GRAV := [930.0, 900.0, 1150.0, -70.0, -150.0]
const DRAG := [1.7, 1.2, 0.9, 3.2, 2.0]
# Dead Cells örneğindeki gibi: koyu kızıl, parlak kırmızı, kırmızı-pembe, pembe ışık
const KAN := [Color(0.42, 0.02, 0.05), Color(0.68, 0.03, 0.07), Color(0.93, 0.09, 0.12), Color(1.0, 0.3, 0.36), Color(1.0, 0.58, 0.66)]
const KAN_W := [0.14, 0.2, 0.3, 0.22, 0.14]
const KOR_C := [Color(1.0, 0.85, 0.4), Color(1.0, 0.55, 0.15), Color(0.95, 0.28, 0.06)]
const MUREKKEP := Color(0.07, 0.05, 0.11)

var level: Node
var _has_cell := false
var _telafi := 1.0
# uçan zerreler
var _p := PackedVector2Array()
var _v := PackedVector2Array()
var _s := PackedFloat32Array()     # boyut (dünya px)
var _r := PackedFloat32Array()     # açı
var _w := PackedFloat32Array()     # dönüş hızı
var _l := PackedFloat32Array()     # kalan ömür
var _l0 := PackedFloat32Array()    # ilk ömür
var _c := PackedColorArray()
var _h := PackedColorArray()       # ışık rengi (topağın üst-sol kıyısı)
var _k := PackedByteArray()
var _b := PackedByteArray()        # sekme sayısı
# lekeler (zemin / duvar)
var _sp := PackedVector2Array()
var _sz := PackedVector2Array()
var _sc := PackedColorArray()
var _sl := PackedFloat32Array()
var _sl0 := PackedFloat32Array()
var _stw := 0
var _lek: Node2D          # lekeler ayrı tuvalde: yalnızca değişince / 4 karede bir yeniden çizilir
var _lek_kirli := false
var _kare := 0
# buğu / toz: [konum, r0, r1, t, süre, renk]
var _mist: Array = []
var n_bursts := 0
var n_spawned := 0
var peak := 0
var _drawn := false
var _drawn_p := false
var us_fizik := 0      # son karenin işlem süresi (µs): ölçüm için
var us_cizim := 0
var us_lek := 0
var us_patla := 0       # en uzun tek patlama kurulumu
var us_en_cok := 0


static func sys() -> Gore:
	var lv: Node = FX.level
	if lv == null or not is_instance_valid(lv):
		return null
	if lv.has_meta("gore"):
		var g: Variant = lv.get_meta("gore")
		if is_instance_valid(g):
			return g
	var g2 := Gore.new()
	g2.level = lv
	g2.z_index = 3
	g2._has_cell = lv.has_method("cell")
	g2._telafi = Blood.telafi_of(lv)
	g2._lek = Node2D.new()
	g2._lek.show_behind_parent = true
	g2._lek.draw.connect(g2._draw_lek)
	g2.add_child(g2._lek)
	lv.add_child(g2)
	lv.set_meta("gore", g2)
	return g2


static func stats() -> Dictionary:
	var g := sys()
	if g == null:
		return {}
	return {"zerre": g._p.size(), "leke": g._sp.size(), "bugu": g._mist.size(), "tepe": g.peak,
		"patlama": g.n_bursts, "toplam_zerre": g.n_spawned,
		"fizik_us": g.us_fizik, "cizim_us": g.us_cizim, "leke_us": g.us_lek, "en_cok_us": g.us_en_cok, "patla_en_cok_us": g.us_patla}


static func material_of(sprite_kind: String, kind: String, flesh: bool) -> int:
	if flesh:
		return MAT_ET
	if kind in TAS:
		return MAT_TAS
	if kind in KOR:
		return MAT_KOR
	return MAT_RUH


static func burst(pos: Vector2, ext: Vector2, dir: Vector2, power: float, col: Color, mat := MAT_ET, scale_k := 1.0) -> void:
	## Ölüm patlaması. pos: gövde merkezi; ext: gövdenin yarı boyu (zerreler bu siluetin içinden çıkar);
	## dir: öldürücü darbe yönü (bitirişte kesik yönü + savurma); power 0,7..3; scale_k: seçkin ~1,4, boss ~3.
	var g := sys()
	if g == null:
		return
	g._burst(pos, ext, dir, power, col, mat, scale_k)


func _pal(col: Color, mat: int) -> Array:
	if mat == MAT_TAS:
		return [col.darkened(0.55), col.darkened(0.35), col.darkened(0.15), col.lightened(0.1), col.lightened(0.35)]
	if mat == MAT_ET and col.r > maxf(col.g, col.b) * 2.0:
		return KAN
	return [col.darkened(0.55), col.darkened(0.35), col.darkened(0.15), col, col.lightened(0.25)]


func _pick(pal: Array) -> int:
	var x := randf()
	for i in 5:
		x -= KAN_W[i]
		if x <= 0.0:
			return i
	return 2


func _lit(c: Color) -> Color:
	return Color(c.r * _telafi, c.g * _telafi, c.b * _telafi, c.a)


func _add(p: Vector2, v: Vector2, s: float, life: float, c: Color, h: Color, k: int) -> void:
	if _p.size() >= MAX_P:
		return
	_p.append(p)
	_v.append(v)
	_s.append(s)
	_r.append(randf() * TAU)
	_w.append(randf_range(-12.0, 12.0))
	_l.append(life)
	_l0.append(life)
	_c.append(_lit(c))
	_h.append(_lit(h))
	_k.append(k)
	_b.append(0)
	n_spawned += 1


func _burst(pos: Vector2, ext: Vector2, dir: Vector2, power: float, col: Color, mat: int, m: float) -> void:
	var t0 := Time.get_ticks_usec()
	n_bursts += 1
	_telafi = Blood.telafi_of(level)
	var d := dir.normalized() if dir.length() > 0.01 else Vector2.UP
	var pw := clampf(power, 0.5, 3.5)
	var pal := _pal(col, mat)
	var ex := Vector2(maxf(4.0, ext.x * 0.75), maxf(4.0, ext.y * 0.75))
	var spd := (1.0 + 0.22 * (pw - 1.0)) * (1.0 + 0.12 * (m - 1.0))
	var n_main := int((44.0 + 26.0 * (pw - 1.0)) * m)
	var n_fine := int((44.0 + 30.0 * (pw - 1.0)) * m)
	var n_big := int((3.0 + pw * 2.0) * sqrt(m))
	var kind_main := K_TOPAK
	match mat:
		MAT_TAS:
			kind_main = K_MOLOZ
			n_main = int(n_main * 0.8)
			n_fine = int(n_fine * 0.4)
		MAT_RUH:
			kind_main = K_TUL
			n_fine = int(n_fine * 0.3)
			n_big = 0
		MAT_KOR:
			kind_main = K_KOR
			n_fine = int(n_fine * 0.4)
			n_big = 0
	for i in n_main + n_big:
		var big := i >= n_main
		var q := pos + Vector2(randf_range(-ex.x, ex.x), randf_range(-ex.y, ex.y))
		var a := randf() * TAU
		var sp := randf_range(70.0, 330.0) * spd
		var v := Vector2(cos(a), sin(a)) * sp * 0.8
		if randf() < 0.65:
			v += d * sp * randf_range(0.4, 0.9)   # darbe yönüne eğilim
		v.y -= randf_range(70.0, 230.0) * spd
		var ci := _pick(pal)
		var c: Color = pal[ci]
		var h: Color = pal[mini(4, ci + 1 + (1 if randf() < 0.4 else 0))]
		var s := randf_range(1.4, 3.0) if not big else randf_range(3.4, 5.0)
		var life := randf_range(1.0, 2.2)
		match kind_main:
			K_MOLOZ:
				s = randf_range(1.4, 3.2) if not big else randf_range(3.5, 5.0)
			K_TUL:
				v *= 0.55
				c = MUREKKEP if randf() < 0.35 else Color(pal[ci], 0.85)
				h = Color(pal[4], 0.9)
				s = randf_range(2.0, 4.0)
				life = randf_range(0.45, 1.0)
			K_KOR:
				v *= 0.7
				c = KOR_C[randi() % 3]
				h = KOR_C[0]
				s = randf_range(0.9, 1.8)
				life = randf_range(0.5, 1.3)
		if big:
			c = pal[randi_range(0, 1)]
			v *= 0.7
		_add(q, v, s, life, c, h, kind_main)
	# ince damlalar (et: kan; taş: kum)
	for i in n_fine:
		var q2 := pos + Vector2(randf_range(-ex.x, ex.x), randf_range(-ex.y, ex.y)) * 0.8
		var a2 := randf() * TAU
		var sp2 := randf_range(120.0, 470.0) * spd
		var v2 := Vector2(cos(a2), sin(a2)) * sp2 * 0.7
		if randf() < 0.7:
			v2 += d * sp2 * randf_range(0.5, 1.0)
		v2.y -= randf_range(40.0, 200.0) * spd
		var c2: Color = pal[_pick(pal)]
		if mat == MAT_KOR:
			c2 = KOR_C[randi() % 3]
		_add(q2, v2, randf_range(0.7, 1.3), randf_range(0.6, 1.5), c2, c2, K_DAMLA if mat != MAT_KOR else K_KOR)
	# buğu / toz / duman
	var mc: Color
	match mat:
		MAT_TAS:
			mc = Color(pal[3], 0.5)
		MAT_RUH:
			mc = Color(pal[3], 0.4)
		MAT_KOR:
			mc = Color(0.25, 0.2, 0.22, 0.45)
		_:
			mc = Color(pal[3], 0.22)
	var nm := 4 + int(m * 1.5)
	for i in nm:
		var mp := pos + Vector2(randf_range(-ex.x, ex.x), randf_range(-ex.y, ex.y)) * 0.6 + d * randf_range(0.0, 10.0) * m
		var r0 := maxf(ext.x, ext.y) * randf_range(0.15, 0.3)
		_mist.append([mp, r0, r0 * randf_range(1.6, 2.2) * (1.0 + 0.1 * pw), 0.0, randf_range(0.15, 0.3) * (1.8 if mat == MAT_TAS else 1.0), _lit(mc)])
	peak = maxi(peak, _p.size())
	us_patla = maxi(us_patla, Time.get_ticks_usec() - t0)


func _cell(p: Vector2) -> int:
	return level.cell(int(floorf(p.x / Level.TS)), int(floorf(p.y / Level.TS)))


func _stain(p: Vector2, size: Vector2, c: Color, life: float) -> void:
	c = c.darkened(0.25)
	c.a = 0.6
	_lek_kirli = true
	if _sp.size() < MAX_ST:
		_sp.append(p)
		_sz.append(size)
		_sc.append(c)
		_sl.append(life)
		_sl0.append(life)
	else:
		# dolu: sırayla en eskilerin yerine yaz
		_stw = (_stw + 1) % MAX_ST
		_sp[_stw] = p
		_sz[_stw] = size
		_sc[_stw] = c
		_sl[_stw] = life
		_sl0[_stw] = life


func _kill(i: int) -> void:
	var j := _p.size() - 1
	if i != j:
		_p[i] = _p[j]
		_v[i] = _v[j]
		_s[i] = _s[j]
		_r[i] = _r[j]
		_w[i] = _w[j]
		_l[i] = _l[j]
		_l0[i] = _l0[j]
		_c[i] = _c[j]
		_h[i] = _h[j]
		_k[i] = _k[j]
		_b[i] = _b[j]
	_p.resize(j)
	_v.resize(j)
	_s.resize(j)
	_r.resize(j)
	_w.resize(j)
	_l.resize(j)
	_l0.resize(j)
	_c.resize(j)
	_h.resize(j)
	_k.resize(j)
	_b.resize(j)


func _physics_process(delta: float) -> void:
	if level == null or not is_instance_valid(level):
		return
	if _p.is_empty() and _sp.is_empty() and _mist.is_empty():
		if _drawn:
			_drawn = false
			_drawn_p = false
			queue_redraw()   # son kareyi temizle
			_lek.queue_redraw()
		return
	_drawn = true
	var t0 := Time.get_ticks_usec()
	var TS := float(Level.TS)
	var i := _p.size() - 1
	while i >= 0:
		var k := _k[i]
		var p := _p[i]
		var v := _v[i]
		v.y += GRAV[k] * delta
		v *= 1.0 - DRAG[k] * delta
		var np := p + v * delta
		_l[i] -= delta
		_r[i] += _w[i] * delta
		if k <= K_MOLOZ and _has_cell:
			var c := _cell(np)
			if c == 1 or c == 4 or (c == 2 and v.y > 0.0 and _cell(p) != 2):
				var floor_hit := v.y > 0.0 and (_cell(Vector2(np.x, p.y)) == 0 or c == 2)
				var s := _s[i]
				if floor_hit:
					var top := floorf(np.y / TS) * TS
					if (k == K_MOLOZ and _b[i] < 2) or (k == K_TOPAK and s > 2.0 and _b[i] < 1 and v.y > 220.0):
						# iri topak bir kez, moloz iki kez seker
						_b[i] += 1
						v = Vector2(v.x * 0.5, -v.y * (0.32 if k == K_MOLOZ else 0.22))
						_v[i] = v
						_p[i] = Vector2(np.x, top - 0.5)
						i -= 1
						continue
					var sp := clampf(v.length() / 160.0, 1.0, 2.6)
					var col := _c[i]
					if k == K_MOLOZ:
						_stain(Vector2(np.x, top - s * 0.4), Vector2(s, s * 0.8), col, randf_range(4.0, 7.0))
					elif k == K_TOPAK or randf() < 0.35:
						_stain(Vector2(np.x, top + 0.3), Vector2(s * sp, maxf(0.6, s * 0.3)), col, randf_range(8.0, 15.0) if k == K_TOPAK else randf_range(4.0, 8.0))
				elif k == K_TOPAK or (k == K_DAMLA and randf() < 0.35):
					var wx := floorf(np.x / TS) * TS if v.x > 0.0 else (floorf(np.x / TS) + 1.0) * TS
					_stain(Vector2(wx, np.y), Vector2(maxf(0.7, s * 0.5), s * 1.5), _c[i], randf_range(3.0, 6.0))
				_kill(i)
				i -= 1
				continue
		if _l[i] <= 0.0:
			_kill(i)
			i -= 1
			continue
		_p[i] = np
		_v[i] = v
		i -= 1
	# lekeler söner
	var j := _sp.size() - 1
	while j >= 0:
		_sl[j] -= delta
		if _sl[j] <= 0.0:
			var e := _sp.size() - 1
			_sp[j] = _sp[e]
			_sz[j] = _sz[e]
			_sc[j] = _sc[e]
			_sl[j] = _sl[e]
			_sl0[j] = _sl0[e]
			_sp.resize(e)
			_sz.resize(e)
			_sc.resize(e)
			_sl.resize(e)
			_sl0.resize(e)
			_stw = 0
			_lek_kirli = true
		j -= 1
	var m := _mist.size() - 1
	while m >= 0:
		_mist[m][3] += delta
		if _mist[m][3] >= _mist[m][4]:
			_mist.remove_at(m)
		m -= 1
	_kare += 1
	if _lek_kirli or (_kare % 4 == 0 and not _sp.is_empty()):
		_lek_kirli = false
		_lek.queue_redraw()
	us_fizik = Time.get_ticks_usec() - t0
	if not _p.is_empty() or not _mist.is_empty() or _drawn_p:
		_drawn_p = not _p.is_empty() or not _mist.is_empty()
		queue_redraw()


# --------------------------------------------------------------- çizim: önceden ayrılmış dizilere dörtgen yazımı
static var _IDX := PackedInt32Array()   # dörtgen dizin kalıbı (0,1,2, 0,2,3, 4,5,6 ...), bir kez büyütülür
var _qp := PackedVector2Array()
var _qc := PackedColorArray()
var _qn := 0


static func _idx_for(nq: int) -> PackedInt32Array:
	var have := _IDX.size() / 6
	if have < nq:
		var m := maxi(nq, have * 2 + 256)
		_IDX.resize(m * 6)
		for q in range(have, m):
			var b := q * 4
			var o := q * 6
			_IDX[o] = b
			_IDX[o + 1] = b + 1
			_IDX[o + 2] = b + 2
			_IDX[o + 3] = b
			_IDX[o + 4] = b + 2
			_IDX[o + 5] = b + 3
	return _IDX.slice(0, nq * 6)


func _begin(nq: int) -> void:
	_qn = 0
	if _qp.size() < nq * 4:
		_qp.resize(nq * 4)
		_qc.resize(nq * 4)


func _quad(c: Vector2, ax: Vector2, ay: Vector2, col: Color) -> void:
	var b := _qn * 4
	_qp[b] = c - ax - ay
	_qp[b + 1] = c + ax - ay
	_qp[b + 2] = c + ax + ay
	_qp[b + 3] = c - ax + ay
	_qc[b] = col
	_qc[b + 1] = col
	_qc[b + 2] = col
	_qc[b + 3] = col
	_qn += 1


func _flush(ci: RID) -> void:
	if _qn == 0:
		return
	RenderingServer.canvas_item_add_triangle_array(ci, _idx_for(_qn), _qp.slice(0, _qn * 4), _qc.slice(0, _qn * 4))


func _draw_lek() -> void:
	var t0 := Time.get_ticks_usec()
	_begin(_sp.size())
	for j in _sp.size():
		var c := _sc[j]
		c.a *= minf(1.0, _sl[j] / 1.5) * 0.85
		var z := _sz[j] * 0.5
		_quad(_sp[j], Vector2(z.x, 0.0), Vector2(0.0, z.y), c)
	_flush(_lek.get_canvas_item())
	us_lek = Time.get_ticks_usec() - t0


func _draw() -> void:
	var t0 := Time.get_ticks_usec()
	for mi in _mist:
		var u: float = mi[3] / mi[4]
		var mc: Color = mi[5]
		draw_circle(mi[0], lerpf(mi[1], mi[2], 1.0 - (1.0 - u) * (1.0 - u)), Color(mc, mc.a * (1.0 - u) * (1.0 - u)))
	_begin(_p.size() * 3)
	for i in _p.size():
		var k := _k[i]
		var p := _p[i]
		var s := _s[i]
		var c := _c[i]
		var u := _l[i] / _l0[i]
		if k == K_DAMLA:
			var v := _v[i]
			var sp := v.length()
			var dd := v / sp if sp > 1.0 else Vector2.DOWN
			var L := s * (0.8 + minf(sp, 500.0) * 0.004)
			if u < 0.25:
				c.a *= u * 4.0
			_quad(p, dd * L, Vector2(-dd.y, dd.x) * s * 0.55, c)
		elif k == K_TUL:
			var g := 1.0 + (1.0 - u) * 1.6
			c.a *= u
			var ax := Vector2.from_angle(_r[i]) * s * g * 0.6
			_quad(p, ax, Vector2(-ax.y, ax.x) * 0.7, c)
			var h := _h[i]
			h.a *= u * 0.6
			_quad(p + Vector2(-0.4, -0.4) * s, ax * 0.4, Vector2(-ax.y, ax.x) * 0.3, h)
		elif k == K_KOR:
			c.a *= u * (0.65 + 0.35 * sin(_r[i] * 3.0))
			_quad(p, Vector2(s * 0.5, 0.0), Vector2(0.0, s * 0.5), c)
		else:
			# düzensiz topak: dönen ana dörtgen + açılı ikinci dörtgen + üst-solda ışık kıyısı
			var sc := s * (1.0 if u > 0.15 else u / 0.15)
			var ax2 := Vector2.from_angle(_r[i]) * sc * 0.5
			var oy := Vector2(-ax2.y, ax2.x)
			_quad(p, ax2, oy * 0.75, c)
			var ax3 := Vector2.from_angle(_r[i] + 0.9) * sc * 0.36
			_quad(p + oy * 0.5, ax3, Vector2(-ax3.y, ax3.x) * 0.8, c)
			if sc > 1.0:
				_quad(p + Vector2(-0.28, -0.32) * sc, Vector2(sc * 0.2, 0.0), Vector2(0.0, sc * 0.16), _h[i])
	_flush(get_canvas_item())
	us_cizim = Time.get_ticks_usec() - t0
	us_en_cok = maxi(us_en_cok, us_fizik + us_cizim + us_lek)
