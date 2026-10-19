class_name SanatFX
extends Node2D
## v27 Savaş Sanatları efektleri; v28: sumi-e mürekkep (dokulu fırça darbeleri, sıçrantı, yıkama, damga, altın varak).
## Ayrıntı: docs/TASARIM.md "v28: sanat görselleri ve Göğe Yükseliş". SavasSanati.gd kullanır.
##
## İki çizim türü (ikisi de tek üçgen dizisi, tek çizim çağrısı; zaman ölçekli: hitstop'ta donar, donmuş karede okunur):
##   fırça darbesi  değişken genişlikli şerit, shaders/sanat_firca.gdshader + assets/fx/ink/sanat_firca.png (8 fırça:
##                  ıslak, kuru, çok kuru, sulu kenar, sıçratan ...). Darbe ucundan kuyruğa ÇİZİLEREK açılır (açılış),
##                  kuyrukta kıllar ayrışır (kuru fırça), kâğıt tanesi; biçemler: S_INK sumi siyahı, S_COLOR paletin
##                  rengi, S_HOT ışıyan çekirdek, S_WASH sulu yıkama, S_GOLD altın varak, S_DRY yalnız kıllar
##   leke           atlas öğesi (assets/fx/ink/sanat_fx.png, InkFX kodlaması, shaders/ink_fx.gdshader): splat_a/b/c
##                  sıçrantı, wash/wash_b yıkama, gum "GÜM!" damgası, varak / varak_b altın pulları, crack yer yarığı,
##                  seal mühür
## Kipler:
##   muhur     sanatın telegrafı: kendini fırça fırça çizen ensō, içinde tamga (darbe darbe), yıkama, köşede mühür
##   hilal     Ay Hilali: ilerleyen gümüş mürekkep hilali (üç katman fırça) + yankı yıkamaları + hız çizgileri;
##             yolundaki düşmanlara kendi vurur (vurus_cb), duvarda kırılır
##   kasirga   Kasırga Kesişi: dönen eğik elips fırça darbeleri (ön yarı koyu, arka yarı eriyen) + yıkama
##   kalkan    Demir Duruş: öndeki dökme demir ensō kalkanı (çizilerek açılır, üstünde gezen parıltı)
##   ok_iz     Ok Yağmuru: okun ardında kuru fırça izi
##   ruh_kurt  Kam Darbesi / Bozkurt Atılışı: tayfsı kurt (kurt biçiminin solan kopyası), ardında mürekkep dumanı
##   parilti   bıçakta parlayan dört köşeli çelik yıldızı
##   v31 kombo sanatları:
##   ritim     daralan fırça halkası (kapandığı an T: bitiriş TAM); TAM'da altın, kaçırılınca solar
##   girdap    Tengri Çarkı: merkeze kıvrılan gök mavisi sarmal kollar (ön koyu, arka eriyen) + yıkama
##   kesik_iz  Kurt Dansı: düşmanın üstünde asılı kalan al kesik (düşmanı izler; patlayınca söner)
##   delen     Akıncı Akını: ilerleyen delen mürekkep oku (uzun fırça mızrağı + kuru hız çizgileri); yolundakilere
##             kendi vurur (vurus_cb), duvarda kırılır
##   firca / leke  serbest bileşim (aşağıdaki statik bileşimler: kesik, kasirga_son, cekis_inis, goge_*, ...)
## Fırça yardımcıları (stroke, glyph) HUD simgelerinde de kullanılır (SanatUI).

const FIRCA_SHADER: Shader = preload("res://shaders/sanat_firca.gdshader")
const INK_SHADER: Shader = preload("res://shaders/ink_fx.gdshader")
const BRUSH_TEX := "res://assets/fx/ink/sanat_firca.png"
const ATLAS_TEX := "res://assets/fx/ink/sanat_fx.png"
const ATLAS_JSON := "res://assets/fx/ink/sanat_fx.json"
## InkFX.PALETTES'e ek paletler (mürekkep, çekirdek, gövde, kenar, sıcak): 12 dökme demir (Demir Duruş), 13 sumi
## (yansız mürekkep yıkaması: lekeler sanatın renginde değil, gri-siyah su mürekkebi)
const PAL_EK := {12: ["050608", "262b33", "6f7a88", "d2d9e2", "ffffff"], 13: ["030304", "121116", "2c2a30", "57535a", "f4efe6"],
	# v31 kombo sanatları: 14 al (Kurt Dansı), 15 yeşim (Evren Kuyruğu), 16 gök (Tengri Çarkı), 17 toprak (Yer Yarığı),
	# 18 ak / kemik (Akıncı Akını)
	14: ["1c0410", "6e0a2e", "e02a62", "ff94b8", "fff0f5"], 15: ["03120a", "0c4228", "1fa060", "8fe8b0", "f2fff6"],
	16: ["030a1c", "0b3470", "2a90e8", "a0dcff", "ffffff"], 17: ["140802", "552a0c", "c86a1c", "ffbe6a", "fff3dc"],
	18: ["0a0a0c", "3a3834", "a8a090", "ece6d6", "ffffff"]}
const DEMIR := 12
const SUMI := 13
const ALTIN := 9

enum { S_INK, S_COLOR, S_HOT, S_WASH, S_GOLD, S_DRY }
enum { V_SPLASH, V_STAMP, V_CUT, V_DRY }
## fırça satırları (sanat_firca.png)
enum { B_ISLAK, B_ORTA, B_KURU, B_COK_KURU, B_SULU, B_INCE, B_KALIN_KURU, B_SICRAT }

const INK := Color(0.035, 0.02, 0.05)
const BRUSH_MODES := ["muhur", "hilal", "kasirga", "kalkan", "ok_iz", "firca", "yarik", "ritim", "girdap", "kesik_iz", "delen"]

static var _bmats: Dictionary = {}
static var _lmats: Dictionary = {}
static var _shapes: Dictionary = {}
static var _atlas_size := Vector2(1024, 1024)

var mode := ""
var col := Color(1, 1, 1)
var pal := 0
var life := 0.6
var t := 0.0
var follow: Node2D
var data: Dictionary = {}
var alive := true          # kasırga / kalkan: sürerken true; false olunca söner
var vel := Vector2.ZERO
var facing := 1
var vurus_cb: Callable     # hilal: vurus_cb.call(düşman, konum)
var grow := Vector2.ONE    # firca / leke: ömür boyunca ölçek (başta x, sonda y)
var strokes: Array = []    # firca: fırça darbeleri
var els: Array = []        # leke: atlas öğeleri
var _hit: Array = []
var _rng := RandomNumberGenerator.new()
var _spr: Sprite2D
var _fade := 1.0
var _end_t := 0.0
# fırça üçgen dizisi (her _draw'da doldurulur)
var _P := PackedVector2Array()
var _U := PackedVector2Array()
var _C := PackedColorArray()
var _I := PackedInt32Array()


# ================================================================== malzeme ve palet
static func pal3(i: int) -> Array:
	## Doğrusal palet (Vector3 x 5): InkFX paletleri + PAL_EK
	if PAL_EK.has(i):
		var out: Array = []
		for h in PAL_EK[i]:
			var c := Color.html(h).srgb_to_linear()
			out.append(Vector3(c.r, c.g, c.b))
		return out
	return InkFX.palette(i)


static func _apply_pal(m: ShaderMaterial, p: int) -> void:
	var pc: Array = pal3(p)
	m.set_shader_parameter("c_ink", pc[0])
	m.set_shader_parameter("c_core", pc[1])
	m.set_shader_parameter("c_body", pc[2])
	m.set_shader_parameter("c_rim", pc[3])
	m.set_shader_parameter("c_hot", pc[4])


static func _bmat(p: int) -> ShaderMaterial:
	if not _bmats.has(p):
		var m := ShaderMaterial.new()
		m.shader = FIRCA_SHADER
		m.set_shader_parameter("brush", Data.tex_full(BRUSH_TEX))   # HD paketi varsa 2 kat
		_apply_pal(m, p)
		_bmats[p] = m
	return _bmats[p]


static func _lmat(p: int) -> ShaderMaterial:
	if not _lmats.has(p):
		var m := ShaderMaterial.new()
		m.shader = INK_SHADER
		m.set_shader_parameter("atlas", Data.tex_full(ATLAS_TEX))
		_apply_pal(m, p)
		_lmats[p] = m
	return _lmats[p]


static func _shape(n: String) -> Rect2:
	if _shapes.is_empty():
		var j: Dictionary = Data.load_json(ATLAS_JSON)
		if j.has("size"):
			_atlas_size = Vector2(float(j["size"][0]), float(j["size"][1]))
		for k in j.get("shapes", {}):
			var r: Array = j["shapes"][k]
			_shapes[k] = Rect2(float(r[0]), float(r[1]), float(r[2]), float(r[3]))
	return _shapes.get(n, Rect2(0, 0, 256, 256))


static func pal_of(c: Color) -> int:
	return InkFX.pal_from_color(c)


# ================================================================== oluşturma
static func spawn(m: String, pos: Vector2, c: Color, lf := 0.6, p := -1) -> SanatFX:
	if FX.root == null:
		return null
	var n := SanatFX.new()
	n.mode = m
	n.col = c
	n.pal = p if p >= 0 else pal_of(c)
	n.life = lf
	n.top_level = true
	n.global_position = pos
	n.z_index = 57
	n._rng.randomize()
	if m in BRUSH_MODES:
		n.material = _bmat(n.pal)
	elif m == "leke":
		n.material = _lmat(n.pal)
	FX.root.add_child(n)
	return n


static func firca(pos: Vector2, p: int, z := 57) -> SanatFX:
	## Boş fırça düğümü: ek() ile darbe eklenir; son darbe eriyince kendini siler
	var n := spawn("firca", pos, Color.WHITE, 9.0, p)
	if n:
		n.z_index = z
		if z < 0:
			n.z_as_relative = false
	return n


static func leke(pos: Vector2, p: int, z := 57) -> SanatFX:
	var n := spawn("leke", pos, Color.WHITE, 9.0, p)
	if n:
		n.z_index = z
		if z < 0:
			n.z_as_relative = false
	return n


func ek(pts: PackedVector2Array, ws: PackedFloat32Array, style: int, row: int, delay := 0.0, dt := 0.08, hold := 0.08, fade := 0.2, drift := Vector2.ZERO) -> void:
	## Fırça darbesi: delay sonra dt sürede baştan kuyruğa çizilir, hold bekler, fade sürede erir (kıllar kopar)
	strokes.append({"p": pts, "w": ws, "s": style, "r": row, "d": delay, "dt": maxf(dt, 0.001), "h": hold, "f": maxf(fade, 0.001), "v": drift})
	_end_t = maxf(_end_t, delay + dt + hold + fade)


func el(shape: String, off: Vector2, rot: float, size: Vector2, variant := V_SPLASH, delay := 0.0, t_rev := 0.05, hold := 0.06, lf := 0.32, anchor := Vector2(0.5, 0.5)) -> void:
	## Atlas öğesi (InkFX.el ile aynı: açılış, bekleme, erime)
	els.append({"s": shape, "o": off, "r": rot, "z": size, "v": variant, "d": delay, "tr": maxf(t_rev, 0.001), "h": hold, "l": lf, "a": anchor})
	_end_t = maxf(_end_t, delay + lf)


func _ready() -> void:
	if mode == "kasirga":
		z_index = 2   # gövdenin önünde ve arkasında: arka yarı eriyen, ön yarı koyu


func _physics_process(delta: float) -> void:
	t += delta
	match mode:
		"hilal":
			_hilal_step(delta)
		"delen":
			_delen_step(delta)
		"kesik_iz":
			if follow and is_instance_valid(follow) and not follow.get("dead"):
				global_position = follow.call("center") if follow.has_method("center") else follow.global_position
			else:
				alive = false
			if not alive or t > 3.0:
				_fade = maxf(0.0, _fade - delta * 8.0)
				if _fade <= 0.0:
					queue_free()
					return
		"girdap":
			if not alive:
				_fade = maxf(0.0, _fade - delta * 5.0)
				if _fade <= 0.0:
					queue_free()
					return
			elif t > 8.0:
				alive = false
		"kasirga", "kalkan":
			if follow and is_instance_valid(follow):
				global_position = follow.global_position + (data.get("off", Vector2(0, -24)) as Vector2)
			if not alive:
				_fade = maxf(0.0, _fade - delta * (4.0 if mode == "kasirga" else 5.0))
				if _fade <= 0.0:
					queue_free()
					return
			elif t > 8.0:
				alive = false
		"ok_iz":
			_ok_iz_step(delta)
		"ruh_kurt":
			_kurt_step(delta)
			if t >= life:
				queue_free()
				return
		"firca", "leke":
			if follow and is_instance_valid(follow) and data.has("off"):
				global_position = follow.global_position + (data["off"] as Vector2)
			if grow != Vector2.ONE:
				scale = Vector2.ONE * lerpf(grow.x, grow.y, 1.0 - pow(1.0 - clampf(t / maxf(_end_t, 0.01), 0.0, 1.0), 2.0))
			if t >= _end_t + 0.02:
				queue_free()
				return
		_:
			if follow and is_instance_valid(follow) and data.has("off"):
				global_position = follow.global_position + (data["off"] as Vector2)
			if t >= life:
				queue_free()
				return
	queue_redraw()


# ================================================================== fırça çizimi
func _bs(pts: PackedVector2Array, ws: PackedFloat32Array, style: int, row: int, reveal := 1.0, diss := 0.0) -> void:
	## Bir fırça darbesini üçgen dizisine ekle: u = yay uzunluğu payı (0 baş .. 1 kuyruk), v enine
	var n := pts.size()
	if n < 2 or reveal <= 0.001 or diss >= 0.999:
		return
	var cum := PackedFloat32Array()
	cum.resize(n)
	var tot := 0.0
	for i in range(1, n):
		tot += pts[i].distance_to(pts[i - 1])
		cum[i] = tot
	if tot < 0.5:
		return
	var code := float(style + 8 * row) * 2.0
	var q := float(roundi(clampf(reveal, 0.0, 1.0) * 63.0)) * 2.0
	var c := Color(1, 1, 1, clampf(diss, 0.0, 1.0))
	var base := _P.size()
	for i in n:
		var a := pts[maxi(0, i - 1)]
		var b := pts[mini(n - 1, i + 1)]
		var dd := b - a
		if dd.length_squared() < 0.000001:
			dd = Vector2.RIGHT
		var nn := dd.normalized().orthogonal()
		var w := float(ws[mini(i, ws.size() - 1)]) * 0.5
		var u := cum[i] / tot
		_P.append(pts[i] + nn * w)
		_P.append(pts[i] - nn * w)
		_U.append(Vector2(u + code, q))
		_U.append(Vector2(u + code, 1.0 + q))
		_C.append(c)
		_C.append(c)
	for i in n - 1:
		var k := base + i * 2
		_I.append_array([k, k + 1, k + 2, k + 1, k + 3, k + 2])


func _bflush() -> void:
	if not _I.is_empty():
		RenderingServer.canvas_item_add_triangle_array(get_canvas_item(), _I, _P, _C, _U)
	_P = PackedVector2Array()
	_U = PackedVector2Array()
	_C = PackedColorArray()
	_I = PackedInt32Array()


func _draw_strokes() -> void:
	for s in strokes:
		var tt := t - float(s["d"])
		if tt <= 0.0:
			continue
		var dt := float(s["dt"])
		var rv := 1.0 - pow(1.0 - clampf(tt / dt, 0.0, 1.0), 2.2)
		var ds := clampf((tt - dt - float(s["h"])) / float(s["f"]), 0.0, 1.0)
		if ds >= 1.0:
			continue
		var pts: PackedVector2Array = s["p"]
		var dv: Vector2 = s["v"]
		if dv != Vector2.ZERO:
			var moved := PackedVector2Array()
			for q in pts:
				moved.append(q + dv * tt)
			pts = moved
		_bs(pts, s["w"], int(s["s"]), int(s["r"]), rv, ds * (0.7 + 0.3 * ds))


func _draw_els() -> void:
	var pts := PackedVector2Array()
	var uvs := PackedVector2Array()
	var cols := PackedColorArray()
	var idx := PackedInt32Array()
	for e in els:
		var tt := t - float(e["d"])
		var L := float(e["l"])
		if tt < 0.0 or tt >= L:
			continue
		var tr := float(e["tr"])
		var rv := clampf(tt / tr, 0.0, 1.0)
		rv = lerpf(InkFX.R0, 1.0, 1.0 - (1.0 - rv) * (1.0 - rv))
		var t1 := tr + float(e["h"])
		var ds := clampf((tt - t1) / maxf(L - t1, 0.001), 0.0, 1.0)
		ds = ds * (0.6 + 0.4 * ds)
		var sz: Vector2 = e["z"] * (0.82 + 0.18 * rv + 0.05 * ds)
		var r := _shape(String(e["s"]))
		var an: Vector2 = e["a"]
		var rot := float(e["r"])
		var off: Vector2 = e["o"]
		var q := float(roundi(rv * 63.0)) * 2.0
		var vx := float(int(e["v"])) * 2.0
		var st := pts.size()
		for c in [Vector2(0, 0), Vector2(1, 0), Vector2(0, 1), Vector2(1, 1)]:
			pts.append(Vector2((c.x - an.x) * sz.x, (c.y - an.y) * sz.y).rotated(rot) + off)
			var uv := (r.position + Vector2(c.x * r.size.x, c.y * r.size.y)) / _atlas_size
			uvs.append(Vector2(uv.x + vx, uv.y + q))
			cols.append(Color(1, 1, 1, ds))
		idx.append_array([st, st + 1, st + 2, st + 1, st + 3, st + 2])
	if not idx.is_empty():
		RenderingServer.canvas_item_add_triangle_array(get_canvas_item(), idx, pts, cols, uvs)


# ------------------------------------------------------------------ yol ve genişlik yardımcıları
static func arc(c: Vector2, rx: float, ry: float, a0: float, a1: float, n: int, rot := 0.0) -> PackedVector2Array:
	var out := PackedVector2Array()
	for i in n + 1:
		var a := lerpf(a0, a1, float(i) / n)
		out.append(c + Vector2(cos(a) * rx, sin(a) * ry).rotated(rot))
	return out


static func line(a: Vector2, b: Vector2, n := 8, bow := 0.0, wob := 0.0, sd := 0) -> PackedVector2Array:
	## a -> b, ortada bow kadar (sola) kıvrık; wob: fırça titremesi
	var out := PackedVector2Array()
	var nn := (b - a).normalized().orthogonal()
	for i in n + 1:
		var u := float(i) / n
		var o := nn * (bow * sin(u * PI) + wob * sin(u * 17.0 + float(sd) * 3.1) * sin(u * PI))
		out.append(a.lerp(b, u) + o)
	return out


static func press(n: int, w: float, head := 0.6, tail := 0.06, peak := 0.22) -> PackedFloat32Array:
	## Fırça basıncı: başta head x w'dan hızla w'ya (peak), sonra kuyruğa doğru incelir
	var out := PackedFloat32Array()
	for i in n + 1:
		var u := float(i) / n
		if u < peak:
			out.append(w * lerpf(head, 1.0, smoothstep(0.0, peak, u)))
		else:
			out.append(w * lerpf(1.0, tail, pow((u - peak) / (1.0 - peak), 1.3)))
	return out


static func swell(n: int, w: float, ends := 0.08, pw := 0.8) -> PackedFloat32Array:
	## Ortada kalın, iki ucu ince (hilal, kesik)
	var out := PackedFloat32Array()
	for i in n + 1:
		out.append(w * maxf(ends, pow(sin(float(i) / n * PI), pw)))
	return out


static func scale_w(ws: PackedFloat32Array, k: float) -> PackedFloat32Array:
	var out := PackedFloat32Array()
	for w in ws:
		out.append(w * k)
	return out


static func flip(pts: PackedVector2Array, f: int) -> PackedVector2Array:
	if f >= 0:
		return pts
	var out := PackedVector2Array()
	for q in pts:
		out.append(Vector2(-q.x, q.y))
	return out


# ================================================================== çizim
func _draw() -> void:
	match mode:
		"muhur":
			_draw_muhur()
		"hilal":
			_draw_hilal()
		"kasirga":
			_draw_kasirga()
		"kalkan":
			_draw_kalkan()
		"ok_iz":
			_draw_ok_iz()
		"parilti":
			_draw_parilti()
		"ritim":
			_draw_ritim()
		"girdap":
			_draw_girdap()
		"kesik_iz":
			_draw_kesik_iz()
		"delen":
			_draw_delen()
		"firca", "yarik":
			_draw_strokes()
		"leke":
			_draw_els()
			return
	_bflush()


# ------------------------------------------------------------------ muhur (telegraf)
func _draw_muhur() -> void:
	## Kendini çizen ensō: yıkama, kuru fırça halkası, içte renkli damar; sonra tamga darbe darbe, köşede mühür izi
	var k := clampf(t / life, 0.0, 1.0)
	var ds := smoothstep(0.62, 1.0, k)
	var r := float(data.get("r", 30.0)) * (0.94 + 0.08 * (1.0 - pow(1.0 - k, 2.0)))
	var a0 := float(data.get("a0", -2.2))
	var n := 44
	var enso := PackedVector2Array()
	for i in n + 1:
		var u := float(i) / n
		var ang := a0 + TAU * 0.87 * u
		var rr := r * (1.0 + 0.05 * sin(u * 9.0 + a0) + 0.04 * u)
		enso.append(Vector2(cos(ang), sin(ang)) * rr)
	# yıkama: halkanın içi sulu mürekkep (önce)
	_bs(arc(Vector2.ZERO, r * 0.52, r * 0.52, a0, a0 + TAU * 0.95, 30), scale_w(swell(30, 1.0, 0.6, 0.4), r * 0.95), S_WASH, B_SULU,
		clampf(t / (life * 0.25), 0.0, 1.0), maxf(ds, 0.25))
	var dk := clampf(t / (life * 0.36), 0.0, 1.0)
	var ws := press(n, 14.0, 0.7, 0.1, 0.16)
	_bs(enso, ws, S_INK, B_KALIN_KURU, dk, ds)
	var inner := PackedVector2Array()
	for q in enso:
		inner.append(q * 0.96)
	_bs(inner, scale_w(ws, 0.2), S_COLOR, B_KURU, clampf((t - 0.02) / (life * 0.36), 0.0, 1.0), ds)
	# tamga: darbe darbe (her darbe 0,045 sn), mürekkep + renkli damar
	var id := String(data.get("id", ""))
	var gs := glyph_strokes(id, Vector2.ZERO, r * 0.5)
	var W := r * 0.5 * 0.22
	for i in gs.size():
		var st0 := life * 0.24 + 0.045 * i
		var rv := clampf((t - st0) / 0.05, 0.0, 1.0)
		if rv <= 0.0:
			continue
		var g: Array = gs[i]
		var gw := scale_w(g[1], W * 1.8)
		_bs(g[0], gw, S_INK, B_ORTA, rv, ds)
		_bs(g[0], scale_w(gw, 0.3), S_COLOR, B_KURU, rv, ds)
	# köşede küçük mühür izi (kızıl kare değil: renkli fırça damgası)
	var sk := clampf((t - life * 0.5) / 0.06, 0.0, 1.0)
	if sk > 0.0:
		var sc := Vector2(r * 0.78, r * 0.62) * Vector2(-1.0 if float(data.get("a0", -2.2)) > -1.5 else 1.0, 1.0)
		var sq := PackedVector2Array([sc + Vector2(-4.5, -3.0), sc + Vector2(4.5, -3.4), sc + Vector2(4.2, 3.6), sc + Vector2(-4.0, 3.2), sc + Vector2(-4.5, -2.6)])
		_bs(sq, PackedFloat32Array([3.4, 3.8, 3.6, 3.8, 3.2]), S_COLOR, B_ISLAK, sk, ds)


# ------------------------------------------------------------------ hilal (Ay Hilali)
func _hilal_step(delta: float) -> void:
	var dist := float(data.get("dist", 0.0)) + vel.length() * delta
	data["dist"] = dist
	var lv: Node = FX.level
	var nxt := global_position + vel * delta
	if lv and lv.has_method("ground_at") and lv.ground_at(nxt + Vector2(facing * 10.0, 0.0)) and t > 0.04:
		_hilal_break()
		return
	global_position = nxt
	var hist: Array = data.get("hist", [])
	hist.push_front(global_position)
	if hist.size() > 10:
		hist.pop_back()
	data["hist"] = hist
	# isabet: hilalin gövdesi
	var box := Rect2(global_position + Vector2(-16, -32) * _grow(), Vector2(32, 64) * _grow())
	var maxn := int(data.get("max", 6))
	for e in get_tree().get_nodes_in_group("dusman"):
		if _hit.size() >= maxn:
			break
		if not is_instance_valid(e) or e.dead or _hit.has(e):
			continue
		if box.intersects(e.hurt_rect()):
			_hit.append(e)
			if vurus_cb.is_valid():
				vurus_cb.call(e, e.hurt_rect().get_center())
	if Engine.get_physics_frames() % 3 == 0:
		FX.burst(global_position + Vector2(randf_range(-6, 6), randf_range(-18, 18)), col.lightened(0.3), 1, 30, 0.4, 0.14, 0, true)
	if dist >= float(data.get("menzil", 300.0)) or _hit.size() >= maxn:
		_hilal_break()


func _grow() -> float:
	return 0.6 + 0.4 * clampf(t / 0.12, 0.0, 1.0)


func _hilal_break() -> void:
	InkFX.hit("magic", global_position, Vector2(facing, 0), pal, 2, 1.0)
	# kırılış: hilal mürekkebe dağılır (sıçrantı + son yıkama)
	var l := leke(global_position, pal)
	if l:
		l.el("splat_b", Vector2.ZERO, randf() * TAU, Vector2.ONE * 46.0, V_SPLASH, 0.0, 0.04, 0.05, 0.3)
	var w := leke(global_position, SUMI, -1)
	if w:
		w.el("wash", Vector2(-facing * 6.0, 0), 0.0, Vector2(50, 64), V_DRY, 0.0, 0.05, 0.05, 0.3)
	FX.burst(global_position, col.lightened(0.4), 8, 90, 0.4, 0.18, 0, true)
	queue_free()


func _crescent_pts(off: Vector2, g: float, inset: float) -> PackedVector2Array:
	var f := float(facing)
	var R := 34.0 * g
	var out := PackedVector2Array()
	var n := 18
	for i in n + 1:
		var u := float(i) / n
		var ang := lerpf(-1.25, 1.25, u)
		var wob := 1.0 + 0.03 * sin(u * 13.0 + t * 30.0)
		out.append(off + Vector2(f * (cos(ang) * R * 0.55 - inset * sin(u * PI)), sin(ang) * R * (1.0 - inset * 0.004)) * wob)
	return out


func _draw_hilal() -> void:
	var g := _grow()
	var hist: Array = data.get("hist", [])
	# yankılar: geçtiği yerde sulu yıkama hilalleri (eriyerek)
	for j in range(hist.size() - 1, 0, -3):
		var off: Vector2 = (hist[j] as Vector2) - global_position
		_bs(_crescent_pts(off, g * (1.0 - 0.05 * j), 4.0), swell(18, 12.0 * g, 0.1), S_WASH, B_SULU, 1.0, 0.25 + float(j) / 12.0)
	# hız çizgileri: hilalin ardında kuru fırça
	for k in 3:
		var y := (float(k) - 1.0) * 17.0 * g
		var L := (58.0 + 18.0 * float(k % 2)) * g
		var a := Vector2(-facing * (6.0 + 4.0 * k), y)
		_bs(line(a, a + Vector2(-facing * L, 0.0), 6), press(6, 3.2 * g, 0.9, 0.05, 0.1), S_DRY, B_COK_KURU, 1.0, 0.1)
	# gövde: sumi kontur (kalın), gümüş gövde, ak çekirdek
	var body := _crescent_pts(Vector2.ZERO, g, 0.0)
	var reveal := clampf(t / 0.06, 0.0, 1.0)
	_bs(body, swell(18, 17.0 * g, 0.06, 0.75), S_INK, B_ISLAK, reveal)
	_bs(_crescent_pts(Vector2(-facing * 2.5, 0), g, 3.0), swell(18, 10.0 * g, 0.05, 0.8), S_COLOR, B_ORTA, reveal)
	_bs(_crescent_pts(Vector2(-facing * 3.5, 0), g * 0.97, 5.0), swell(18, 3.6 * g, 0.03, 0.9), S_HOT, B_INCE, reveal)


# ------------------------------------------------------------------ kasırga
func _draw_kasirga() -> void:
	## Dönen rüzgâr fırçaları: eğik elipsin parçaları (baş önde, kuyruk geride kuruyarak); arka yarı erir
	var spd := float(data.get("spd", 18.0))
	var rx := float(data.get("rx", 44.0))
	var ry := float(data.get("ry", 13.0))
	var a := _fade * clampf(t / 0.1, 0.0, 1.0)
	var dsb := 1.0 - a
	# altta sulu yıkama halkası
	_bs(arc(Vector2(0, 4), rx * 0.95, ry * 1.1, 0.0, TAU, 32), swell(32, 9.0, 0.7, 0.3), S_WASH, B_SULU, 1.0, maxf(dsb, 0.35))
	for j in 5:
		var ph := t * spd + float(j) * TAU / 5.0
		var yo := float(j - 2) * 7.0
		var span := 1.5 + 0.45 * sin(float(j) * 1.7)
		var pts := PackedVector2Array()
		var front := 0.0
		for i in 15:
			var u := float(i) / 14.0
			var ang := ph - span * u
			pts.append(Vector2(cos(ang) * rx * (1.0 + 0.07 * j), sin(ang) * ry + yo))
			front += sin(ang)
		var fr := front / 15.0
		var ds := dsb + (0.0 if fr > 0.0 else 0.45)
		var ws := press(14, 10.0 * (1.0 - 0.1 * j), 0.8, 0.05, 0.1)
		_bs(pts, ws, S_INK, B_KALIN_KURU if j % 2 == 0 else B_KURU, 1.0, ds)
		_bs(pts, scale_w(ws, 0.3), S_COLOR, B_INCE, 1.0, ds)
		if fr > 0.3 and j % 2 == 0:
			_bs(pts.slice(0, 6), scale_w(ws.slice(0, 6), 0.16), S_HOT, B_INCE, 1.0, dsb)


# ------------------------------------------------------------------ kalkan (Demir Duruş)
func _draw_kalkan() -> void:
	## Öndeki dökme demir ensō: dikey elips, çizilerek açılır; üstünde gezen parıltı
	var f := float(facing)
	var rv := clampf(t / 0.16, 0.0, 1.0)
	var ds := 1.0 - _fade
	var c := Vector2(f * 17.0, -2.0)
	var a0 := -PI * 0.5 - f * 0.3
	var pts := PackedVector2Array()
	for i in 29:
		var u := float(i) / 28.0
		var ang := a0 + f * TAU * 0.86 * u
		pts.append(c + Vector2(cos(ang) * 13.0 * (1.0 + 0.04 * sin(u * 7.0)), sin(ang) * 30.0))
	var ws := press(28, 11.0, 0.8, 0.15, 0.2)
	_bs(pts, ws, S_INK, B_KALIN_KURU, rv, ds)
	_bs(pts, scale_w(ws, 0.33), S_COLOR, B_ORTA, rv, ds)
	# parıltı: halka boyunca gezen kısa sıcak darbe
	if rv >= 1.0:
		var k := fmod(t * 1.6, 1.0)
		var i0 := clampi(int(k * 22.0), 0, 22)
		_bs(pts.slice(i0, i0 + 6), scale_w(ws.slice(i0, i0 + 6), 0.22), S_HOT, B_INCE, 1.0, ds)


# ------------------------------------------------------------------ ok izi (Ok Yağmuru)
func _ok_iz_step(_delta: float) -> void:
	var hist: Array = data.get("hist", [])
	if follow and is_instance_valid(follow):
		hist.push_front(follow.global_position)
		if hist.size() > 7:
			hist.pop_back()
		data["hist"] = hist
		global_position = Vector2.ZERO
	else:
		alive = false
		_fade = maxf(0.0, _fade - _delta * 6.0)
		if _fade <= 0.0 or hist.size() < 2:
			queue_free()
	if t > 3.0:
		queue_free()


func _draw_ok_iz() -> void:
	var hist: Array = data.get("hist", [])
	if hist.size() < 2:
		return
	var pts := PackedVector2Array()
	for q in hist:
		pts.append((q as Vector2) - global_position)
	var n := pts.size() - 1
	var w := float(data.get("w", 3.4))
	var ds := 1.0 - _fade
	_bs(pts, press(n, w, 1.0, 0.1, 0.05), S_INK, B_COK_KURU, 1.0, ds)
	_bs(pts, press(n, w * 0.4, 1.0, 0.1, 0.05), S_COLOR, B_INCE, 1.0, ds)


# ------------------------------------------------------------------ parıltı
func _draw_parilti() -> void:
	var k := clampf(t / life, 0.0, 1.0)
	var s := float(data.get("s", 10.0)) * (0.4 + 0.6 * sin(k * PI))
	var a := 1.0 - k
	var rot := t * 2.0
	for i in 4:
		var d := Vector2.from_angle(rot + i * PI / 2.0)
		var nrm := d.orthogonal() * s * 0.16
		draw_colored_polygon(PackedVector2Array([d * s, nrm, -nrm]), Color(col.lightened(0.5), a))
	draw_circle(Vector2.ZERO, s * 0.22, Color(1, 1, 1, a))


# ------------------------------------------------------------------ ruh kurdu (Kam Darbesi / Bozkurt Atılışı)
func setup_kurt(src: Sprite2D, f: int) -> void:
	facing = f
	if src == null or src.texture == null:
		return
	_spr = Sprite2D.new()
	_spr.texture = src.texture
	_spr.region_enabled = src.region_enabled
	_spr.region_rect = src.region_rect
	_spr.centered = src.centered
	_spr.offset = src.offset
	data["P"] = src.position
	data["S"] = src.scale
	_spr.flip_h = src.flip_h
	var m := CanvasItemMaterial.new()
	m.blend_mode = CanvasItemMaterial.BLEND_MODE_ADD
	m.light_mode = CanvasItemMaterial.LIGHT_MODE_UNSHADED
	_spr.material = m
	_spr.modulate = Color(col.r * 1.5, col.g * 1.5, col.b * 1.7, 0.0)
	# altında koyu mürekkep gölgesi (açık zeminde de okunsun): aynı kare, normal karışım
	var sh := Sprite2D.new()
	sh.texture = _spr.texture
	sh.region_enabled = true
	sh.region_rect = _spr.region_rect
	sh.centered = _spr.centered
	sh.offset = _spr.offset
	sh.flip_h = _spr.flip_h
	var pc: Array = pal3(pal)
	var ik: Vector3 = pc[1]
	sh.modulate = Color(ik.x * 0.6, ik.y * 0.6, ik.z * 0.6, 0.8)
	sh.show_behind_parent = true
	sh.position = Vector2(-3.0, 2.0)
	_spr.add_child(sh)
	add_child(_spr)


func _kurt_step(_delta: float) -> void:
	if _spr == null:
		return
	var k := clampf(t / life, 0.0, 1.0)
	var g := 0.8 + 0.3 * k
	var pos: Vector2
	if data.has("yol"):
		# Bozkurt Atılışı: atılış çizgisi boyunca koşar
		pos = (data["yol"] as Vector2) * (1.0 - pow(1.0 - minf(k / 0.7, 1.0), 2.0))
		g = 0.95 + 0.1 * k
	else:
		pos = Vector2(facing * (16.0 + 56.0 * (1.0 - pow(1.0 - k, 3.0))), 4.0)
	_spr.position = (data["P"] as Vector2) * g + pos
	_spr.scale = (data["S"] as Vector2) * g
	_spr.modulate.a = (1.0 - k) * (0.85 if k > 0.1 else k / 0.1 * 0.85)
	# ardında mürekkep dumanı: tayfın izinde eriyen yıkama lekeleri
	if Engine.get_physics_frames() % 4 == 0 and k < 0.7:
		var l := leke(global_position + pos + Vector2(-facing * 10.0, -14.0 + randf_range(-6, 6)), pal, 56)
		if l:
			l.el("wash_b" if randi() % 2 == 0 else "wash", Vector2.ZERO, randf() * TAU, Vector2.ONE * randf_range(18.0, 26.0), V_DRY, 0.0, 0.05, 0.03, 0.24)


# ================================================================== bileşimler (statik)
static func kesik(pos: Vector2, ang: float, L: float, w: float, p: int, bow := 0.18, hold := 0.07, z := 57, gold := false, hot := true) -> SanatFX:
	## Büyük sumi kesiği: ıslak sumi gövde + paletin rengi (ya da altın) + ışıyan çekirdek; açılış 0,05 sn
	var n := firca(pos, p, z)
	if n == null:
		return null
	var d := Vector2.from_angle(ang)
	var pts := line(-d * L * 0.5, d * L * 0.5, 14, bow * L, 1.2, int(ang * 10.0))
	var ws := swell(14, w, 0.05, 0.7)
	n.ek(pts, ws, S_INK, B_ISLAK, 0.0, 0.05, hold, 0.2)
	var off := d.orthogonal() * w * 0.16
	n.ek(line(-d * L * 0.47 + off, d * L * 0.5 + off, 14, bow * L * 0.97, 0.6, int(ang * 10.0)), scale_w(ws, 0.27), S_GOLD if gold else S_COLOR, B_KURU, 0.008, 0.05, hold, 0.18)
	if hot:
		n.ek(line(-d * L * 0.4, d * L * 0.46, 14, bow * L * 0.95), scale_w(ws, 0.15), S_HOT, B_INCE, 0.012, 0.05, hold * 0.6, 0.12)
	# kuru yankı: kesiğin bir yanında ince kuru fırça
	n.ek(line(-d * L * 0.42 + d.orthogonal() * w * 0.9, d * L * 0.38 + d.orthogonal() * w * 0.7, 10, bow * L * 0.9), press(10, w * 0.28, 0.9, 0.05, 0.1), S_DRY, B_COK_KURU, 0.02, 0.06, hold, 0.15)
	return n


static func sicrat(pos: Vector2, p: int, s := 60.0, z := 57, wash := true, gold := false) -> void:
	## Mürekkep sıçrantısı (+ yıkama, + altın varak)
	var l := leke(pos, p, z)
	if l == null:
		return
	# sumi sıçrantısı: siyah mürekkep (kenarı paletin renginde), üstünde daha küçük renkli sıçrantı
	l.el(["splat_a", "splat_b", "splat_c"][randi() % 3], Vector2.ZERO, randf() * TAU, Vector2.ONE * s, V_STAMP, 0.0, 0.04, 0.06, 0.34)
	l.el("splat_c", Vector2(randf_range(-0.1, 0.1), randf_range(-0.1, 0.1)) * s, randf() * TAU, Vector2.ONE * s * 0.55, V_SPLASH, 0.015, 0.04, 0.05, 0.28)
	if wash:
		var w := leke(pos, SUMI, -1)
		if w:
			w.el("wash" if randi() % 2 == 0 else "wash_b", Vector2.ZERO, randf() * TAU, Vector2.ONE * s * 1.3, V_DRY, 0.0, 0.06, 0.06, 0.36)
	if gold:
		var g := leke(pos + Vector2(0, -s * 0.2), ALTIN, z + 1)
		if g:
			g.el("varak" if randi() % 2 == 0 else "varak_b", Vector2.ZERO, randf() * TAU, Vector2.ONE * s * 1.4, V_SPLASH, 0.02, 0.05, 0.12, 0.5)


static func vurus_leke(hp: Vector2, dir: Vector2, p: int, tier: int) -> void:
	## Sanat vuruşunun fırça eki: kademe 2'de sıçrantı + yönlü iki fırça kılı
	if tier < 2:
		return
	var l := leke(hp + dir.normalized() * 6.0, p, 57)
	if l:
		l.el("splat_c", Vector2.ZERO, dir.angle(), Vector2.ONE * 44.0, V_SPLASH, 0.0, 0.035, 0.05, 0.28)
	var n := firca(hp, p, 57)
	if n:
		var a := dir.angle()
		for k in 2:
			var aa := a + (float(k) - 0.5) * 0.7 + randf_range(-0.2, 0.2)
			var d := Vector2.from_angle(aa)
			n.ek(line(d * 6.0, d * randf_range(30.0, 44.0), 6, randf_range(-5, 5)), press(6, 4.5, 1.0, 0.05, 0.08), S_INK, B_SICRAT, 0.0, 0.04, 0.04, 0.14)


static func telegraf(pl: Node2D, id: String, c: Color, p: int, f: int) -> SanatFX:
	## Telegraf: oyuncunun arkasında kendini çizen ensō + tamga (darbe darbe) + mühür izi
	var m := spawn("muhur", pl.global_position + Vector2(-f * 4, -28), c, 0.66, p)
	if m:
		m.data = {"id": id, "r": 34.0, "a0": -2.2 if f > 0 else -0.9, "off": Vector2(-f * 4, -28)}
		m.z_as_relative = false
		m.z_index = -1   # oyuncunun arkasında, dekorun önünde
		m.follow = pl
	return m


# ------------------------------------------------------------------ Kasırga
static func kasirga_son(pos: Vector2, R: float, p: int) -> void:
	## Son yarım tur: dışa savrulan fırça kılları (elips boyunca), iki yanda sıçrantı
	var n := firca(pos, p, 57)
	if n == null:
		return
	for k in 12:
		var a := float(k) / 12.0 * TAU + randf_range(-0.15, 0.15)
		var d := Vector2(cos(a), sin(a) * 0.32)
		var r0 := R * 0.55
		n.ek(line(d * r0, d * (R + 34.0 + randf_range(-8, 12)), 6, randf_range(-6, 6)), press(6, 6.0, 1.0, 0.05, 0.1), S_INK, B_KURU if k % 2 else B_SICRAT, 0.0, 0.07, 0.05, 0.18)
		n.ek(line(d * r0, d * (R + 24.0), 6, 0.0), press(6, 2.4, 1.0, 0.05, 0.1), S_COLOR, B_INCE, 0.01, 0.07, 0.04, 0.15)
	for sd in [-1.0, 1.0]:
		sicrat(pos + Vector2(sd * (R + 10.0), 4.0), p, 50.0, 57, false)


# ------------------------------------------------------------------ Bir Çekiş
static func cekis_inis(gp: Vector2, f: int, p: int, h := 78.0, w := 86.0) -> void:
	## Tek ağır iniş: yukarıdan yere kalın sumi darbe, yerde yarık, iki yana sulu sürtme, sıçrantı, altın varak
	var n := firca(gp, p, 57)
	if n:
		var top := Vector2(f * 6.0, -h - 26.0)
		var v := line(top, Vector2(-f * 2.0, 0.0), 10, f * 8.0, 1.5)
		var vw := press(10, 22.0, 0.5, 0.35, 0.3)
		n.ek(v, vw, S_INK, B_ISLAK, 0.0, 0.045, 0.08, 0.22)
		n.ek(v, scale_w(vw, 0.34), S_COLOR, B_SULU, 0.006, 0.045, 0.08, 0.2)
		n.ek(v, scale_w(vw, 0.12), S_HOT, B_INCE, 0.01, 0.045, 0.04, 0.12)
		for sd in [-1.0, 1.0]:
			for k in 2:
				var y := -1.5 - 3.5 * k
				var g := line(Vector2(sd * 6.0, y), Vector2(sd * (w + 14.0 * (1 - k)), y + 1.0), 8, -sd * 2.0, 1.0, k)
				var gw := press(8, 10.0 - 3.0 * k, 1.0, 0.05, 0.08)
				n.ek(g, gw, S_INK, B_SULU if k == 0 else B_KURU, 0.02, 0.09, 0.08, 0.22)
				n.ek(g, scale_w(gw, 0.3), S_COLOR, B_INCE, 0.025, 0.09, 0.06, 0.2)
		for k in 4:
			var a := -PI * 0.5 + (float(k) - 1.5) * 0.45 + randf_range(-0.1, 0.1)
			var d := Vector2.from_angle(a)
			n.ek(line(d * 8.0, d * randf_range(34.0, 56.0), 6, randf_range(-4, 4)), press(6, 5.0, 1.0, 0.05, 0.08), S_INK, B_SICRAT, 0.03, 0.06, 0.05, 0.16)
	var l := leke(gp, p, -1)
	if l:
		l.el("crack", Vector2(0, -0.3 * 46.0), 0.0, Vector2(190.0, 46.0), V_STAMP, 0.0, 0.05, 0.25, 0.7)
	var wl := leke(gp, SUMI, -1)
	if wl:
		wl.el("wash_b", Vector2(0, -12.0), 0.0, Vector2(130.0, 52.0), V_DRY, 0.0, 0.06, 0.08, 0.4)
	sicrat(gp + Vector2(f * 8.0, -16.0), p, 58.0, 57, false, true)


static func cekis_topla(tip: Vector2, p: int) -> void:
	## Kaldırışta silahın ucuna toplanan kuru fırçalar (ağır inişin habercisi)
	var n := firca(tip, p, 57)
	if n == null:
		return
	for k in 5:
		var a := float(k) / 5.0 * TAU + randf_range(-0.2, 0.2)
		var d := Vector2.from_angle(a)
		n.ek(line(d * randf_range(34.0, 46.0), d * 6.0, 5, randf_range(-6, 6)), press(5, 3.6, 1.0, 0.2, 0.15), S_INK, B_KURU, 0.015 * k, 0.09, 0.02, 0.1)
		n.ek(line(d * 30.0, d * 6.0, 5), press(5, 1.4, 1.0, 0.2, 0.15), S_COLOR, B_INCE, 0.015 * k + 0.01, 0.09, 0.02, 0.1)


# ------------------------------------------------------------------ Ay Hilali
static func ay_cekis(pos: Vector2, f: int, p: int) -> void:
	## iaido çekişi: oyuncunun ardında soluk ay (sulu yıkama dolunay) + ileri uzanan ince hız çizgisi
	var m := firca(pos, p, -1)
	if m:
		m.ek(arc(Vector2(-f * 6.0, -6.0), 15.0, 15.0, -PI * 0.5, PI * 1.45, 26), swell(26, 30.0, 0.7, 0.4), S_WASH, B_SULU, 0.0, 0.08, 0.12, 0.25)
		m.ek(arc(Vector2(-f * 6.0, -6.0), 30.0, 30.0, -2.4, -2.4 + TAU * 0.8, 30), press(30, 3.4, 0.7, 0.1, 0.2), S_INK, B_KURU, 0.0, 0.1, 0.08, 0.2)
	var n := firca(pos, p, 57)
	if n:
		n.ek(line(Vector2(f * 8.0, -2.0), Vector2(f * 110.0, -6.0), 8, 0.0, 0.5), press(8, 3.6, 1.0, 0.05, 0.05), S_INK, B_INCE, 0.0, 0.05, 0.05, 0.14)
		n.ek(line(Vector2(f * 10.0, -2.0), Vector2(f * 100.0, -6.0), 8), press(8, 1.3, 1.0, 0.05, 0.05), S_HOT, B_INCE, 0.0, 0.05, 0.03, 0.1)


# ------------------------------------------------------------------ Göğe Yükseliş
static func goge_toplan(gp: Vector2, f: int, p: int) -> void:
	## Hazırlık: yerden ayağa toplanan kuru fırçalar (güç toplanır)
	var n := firca(gp, p, 57)
	if n == null:
		return
	for k in 4:
		var sd := -1.0 if k % 2 == 0 else 1.0
		var x0 := sd * (34.0 + 10.0 * k)
		n.ek(line(Vector2(x0, -2.0), Vector2(sd * 6.0, -4.0 - 2.0 * k), 6, sd * 3.0), press(6, 4.0, 1.0, 0.1, 0.15), S_INK, B_KURU, 0.02 * k, 0.1, 0.02, 0.12)
	var l := leke(gp, SUMI, -1)
	if l:
		l.el("wash", Vector2(0, -6.0), 0.0, Vector2(70.0, 26.0), V_DRY, 0.0, 0.08, 0.05, 0.3)


static func goge_yuksel(gp: Vector2, H: float, f: int, p: int) -> void:
	## Yükseliş: yerden göğe uzanan altın fırça darbeleri (kuyruk tepede kuru), yerde sıçrantı
	var n := firca(gp, p, 56)
	if n:
		for k in 3:
			var x: float = float(f) * [8.0, 22.0, -8.0][k]
			var wd: float = [13.0, 8.0, 6.0][k]
			var v := line(Vector2(x, 2.0), Vector2(x + f * (6.0 + 4.0 * k), -H - 20.0 * (1 - k)), 10, f * 6.0 * (k - 1), 1.0, k)
			var ws := press(10, wd, 0.9, 0.08, 0.15)
			n.ek(v, ws, S_INK, B_KURU if k == 0 else B_COK_KURU, 0.015 * k, 0.2, 0.1, 0.24)
			n.ek(v, scale_w(ws, 0.33), S_GOLD, B_ORTA, 0.02 + 0.015 * k, 0.2, 0.08, 0.22)
		n.ek(line(Vector2(f * 9.0, -6.0), Vector2(f * 14.0, -H * 0.8), 8), press(8, 2.2, 1.0, 0.1, 0.1), S_HOT, B_INCE, 0.03, 0.18, 0.04, 0.12)
	sicrat(gp + Vector2(f * 10.0, -6.0), p, 50.0, 57, true)


static func goge_kesik(c: Vector2, f: int, pass_i: int, p: int, r: float) -> void:
	## Tepedeki hava kombosu: 0 inen çapraz, 1 yükselen çapraz (ikisi X yazar), 2 geniş yatay hilal (altın varaklı)
	match pass_i:
		0:
			kesik(c, (PI * 0.25 if f > 0 else PI * 0.75), r * 1.8, 16.0, p, 0.12 * f, 0.1, 57, true)
		1:
			kesik(c + Vector2(0, -2), (-PI * 0.25 if f > 0 else -PI * 0.75), r * 1.8, 16.0, p, -0.12 * f, 0.1, 57, true)
		_:
			var n := firca(c, p, 57)
			if n:
				var a := arc(Vector2(-f * r * 0.3, 0.0), r * 1.05, r * 0.42, PI * 0.55, -PI * 0.55, 16) if f > 0 else arc(Vector2(r * 0.3, 0.0), r * 1.05, r * 0.42, PI * 0.45, PI * 1.55, 16)
				var ws := swell(16, 16.0, 0.05, 0.6)
				n.ek(a, ws, S_INK, B_ISLAK, 0.0, 0.05, 0.1, 0.22)
				n.ek(a, scale_w(ws, 0.34), S_GOLD, B_ORTA, 0.008, 0.05, 0.1, 0.2)
				n.ek(a, scale_w(ws, 0.15), S_HOT, B_INCE, 0.012, 0.05, 0.05, 0.12)
			var g := leke(c + Vector2(f * r * 0.4, 0.0), ALTIN, 58)
			if g:
				g.el("varak_b", Vector2.ZERO, randf() * TAU, Vector2.ONE * 70.0, V_SPLASH, 0.03, 0.05, 0.1, 0.42)


static func goge_dalis(pos: Vector2, f: int, p: int) -> void:
	## Dalış: oyuncunun çevresinde aşağı inen kuru hız çizgileri (dünyada sabit, yukarıdan aşağı çizilir)
	var n := firca(pos, p, 56)
	if n == null:
		return
	for k in 5:
		var x := (float(k) - 2.0) * 11.0 + f * 4.0
		var y0 := -50.0 - 18.0 * float(k % 2)
		n.ek(line(Vector2(x, y0), Vector2(x, y0 + 110.0 + 20.0 * float(k % 3)), 6), press(6, 3.0 if k != 2 else 4.5, 1.0, 0.05, 0.05), S_DRY if k != 2 else S_INK, B_COK_KURU, 0.012 * k, 0.12, 0.04, 0.12)


static func goge_gum(gp: Vector2, f: int, p: int, carp: int) -> void:
	## Çakılış: yer yarığı, altın yıkama, sıçrantı, varak, iki yana sumi sürtme, "GÜM!" damgası
	var big := carp > 0
	var l := leke(gp, p, -1)
	if l:
		l.el("crack", Vector2(0, -0.3 * 52.0), 0.0, Vector2(230.0, 52.0), V_STAMP, 0.0, 0.05, 0.3, 0.7)
	var w := leke(gp, SUMI, -1)
	if w:
		w.el("wash", Vector2(0, -14.0), 0.0, Vector2(150.0, 56.0), V_DRY, 0.0, 0.07, 0.1, 0.45)
	var n := firca(gp, p, 57)
	if n:
		for sd in [-1.0, 1.0]:
			for k in 2:
				var y := -1.5 - 4.0 * k
				var g := line(Vector2(sd * 8.0, y), Vector2(sd * (96.0 + 18.0 * (1 - k)), y + 1.0), 8, -sd * 2.0, 1.0, k)
				var gw := press(8, 12.0 - 4.0 * k, 1.0, 0.05, 0.08)
				n.ek(g, gw, S_INK, B_SULU if k == 0 else B_KURU, 0.0, 0.08, 0.1, 0.24)
				n.ek(g, scale_w(gw, 0.3), S_GOLD, B_ORTA, 0.006, 0.08, 0.08, 0.2)
		for k in 6:
			var a := -PI * 0.5 + (float(k) - 2.5) * 0.36 + randf_range(-0.08, 0.08)
			var d := Vector2.from_angle(a)
			n.ek(line(d * 10.0, d * randf_range(44.0, 72.0), 6, randf_range(-5, 5)), press(6, 6.0, 1.0, 0.05, 0.08), S_INK, B_SICRAT, 0.01, 0.06, 0.06, 0.18)
	sicrat(gp + Vector2(0, -18.0), p, 84.0 if big else 66.0, 57, false, true)
	# GÜM! damgası: altın sıçrantının önünde siyah fırça yazısı (eğik, kısa süre; düşmanların üstünde, yüzünde değil)
	var sp := gp + Vector2(f * 30.0, -66.0)
	var k := 1.0 if big else 0.8
	var s := leke(sp, p, 60)
	if s:
		s.el("splat_b", Vector2(-4, 4), randf() * TAU, Vector2.ONE * 74.0 * k, V_SPLASH, 0.0, 0.05, 0.2, 0.46)
	var g2 := leke(sp, p, 61)
	if g2:
		g2.el("gum", Vector2.ZERO, -0.1 * f, Vector2(92.0, 46.0) * k, V_STAMP, 0.02, 0.05, 0.26, 0.52)


static func yer_carpma(pos: Vector2, p: int) -> void:
	## Çakılan düşmanın altında küçük yıkama + sıçrantı
	var l := leke(pos, SUMI, -1)
	if l:
		l.el("wash_b", Vector2(0, -8.0), 0.0, Vector2(64.0, 26.0), V_DRY, 0.0, 0.05, 0.06, 0.34)
	sicrat(pos + Vector2(0, -10.0), p, 42.0, 57, false)
	FX.dust(pos, Vector2.UP, 6, 0.3)


# ------------------------------------------------------------------ Bozkurt Atılışı
static func simsek(p0: Vector2, p1: Vector2, p: int, w := 9.0, sd := 0, hold := 0.16) -> SanatFX:
	## Şimşek fırça çizgisi: kırık (zikzak) sumi + mavi damar + ak çekirdek
	var n := firca(p0, p, 57)
	if n == null:
		return null
	var d := p1 - p0
	var nn := d.normalized().orthogonal()
	var pts := PackedVector2Array()
	var rng := RandomNumberGenerator.new()
	rng.seed = sd
	var segs := maxi(5, int(d.length() / 15.0))
	for i in segs + 1:
		var u := float(i) / segs
		var j := 0.0 if i == 0 or i == segs else rng.randf_range(-11.0, 11.0) * (1.0 if i % 2 == 0 else -1.0) * 0.6 + rng.randf_range(-4.0, 4.0)
		pts.append(d * u + nn * j)
	# çatallar: iki kısa kuru kol
	for k in 2:
		var i0 := rng.randi_range(1, segs - 1)
		var a0: Vector2 = pts[i0]
		var dir := (d.normalized() * 0.8 + nn * (1.0 if k == 0 else -1.0) * 0.6).normalized()
		var fk := PackedVector2Array([a0, a0 + dir * 12.0 + nn * rng.randf_range(-4, 4), a0 + dir * 24.0])
		n.ek(fk, press(2, w * 0.4, 1.0, 0.1, 0.2), S_INK, B_KURU, 0.02, 0.04, hold * 0.6, 0.16)
		n.ek(fk, press(2, w * 0.15, 1.0, 0.1, 0.2), S_HOT, B_INCE, 0.025, 0.04, hold * 0.4, 0.1)
	var ws := press(segs, w, 0.7, 0.15, 0.2)
	n.ek(pts, ws, S_INK, B_KURU, 0.0, 0.04, hold, 0.22)
	n.ek(pts, scale_w(ws, 0.33), S_COLOR, B_ORTA, 0.0, 0.04, hold, 0.2)
	n.ek(pts, scale_w(ws, 0.16), S_HOT, B_INCE, 0.005, 0.04, hold * 0.7, 0.12)
	return n


static func bozkurt_kin(c: Vector2, p: int) -> void:
	## Kın kesiği: geçilen düşmanın üstünde şimşek X + sıçrantı
	simsek(c + Vector2(-24, -20), c + Vector2(24, 18), p, 8.0, randi(), 0.08)
	simsek(c + Vector2(-24, 17), c + Vector2(24, -17), p, 8.0, randi(), 0.08)
	sicrat(c, p, 46.0, 57, false)


# ------------------------------------------------------------------ Kam Darbesi
static func kam_topla(hand: Vector2, p: int) -> void:
	## Davulun ruhu avuçta toplanır: içe dolanan ince fırça sarmalı
	var n := firca(hand, p, 57)
	if n == null:
		return
	var pts := PackedVector2Array()
	for i in 25:
		var u := float(i) / 24.0
		var a := u * TAU * 1.3
		pts.append(Vector2(cos(a), sin(a) * 0.8) * (30.0 * (1.0 - u) + 3.0))
	n.ek(pts, press(24, 4.5, 0.4, 0.3, 0.3), S_INK, B_KURU, 0.0, 0.16, 0.03, 0.08)
	n.ek(pts, press(24, 1.8, 0.4, 0.3, 0.3), S_COLOR, B_INCE, 0.01, 0.16, 0.03, 0.08)


static func kam_davul(front: Vector2, f: int, p: int) -> void:
	## Davul vuruşu: büyüyen iki ensō halkası, mor yıkama ve sıçrantı
	var n := firca(front, p, 57)
	if n:
		n.grow = Vector2(0.7, 1.25)
		for k in 2:
			var r := 24.0 + 13.0 * k
			var a0 := randf() * TAU
			var pts := arc(Vector2.ZERO, r * 0.8, r, a0, a0 + TAU * 0.9, 28)
			var ws := press(28, 7.0 - 2.0 * k, 0.8, 0.1, 0.2)
			n.ek(pts, ws, S_INK, B_KALIN_KURU, 0.03 * k, 0.07, 0.06, 0.2)
			n.ek(pts, scale_w(ws, 0.33), S_COLOR, B_ORTA, 0.03 * k + 0.005, 0.07, 0.05, 0.18)
	var l := leke(front, p, -1)
	if l:
		l.el("wash_b", Vector2(f * 10.0, 0.0), 0.0, Vector2.ONE * 70.0, V_DRY, 0.0, 0.06, 0.05, 0.3)
	sicrat(front + Vector2(f * 14.0, 0.0), p, 64.0, 57, false)


# ------------------------------------------------------------------ Ok Yağmuru
static func ok_halka(pos: Vector2, p: int, hold: float) -> void:
	## Hedef alanı: yerde yassı fırça ensō'su (sürdükçe kalır) + ortada yıkama
	var n := firca(pos + Vector2(0, -3), p, 56)
	if n:
		var a0 := randf() * TAU
		var pts := arc(Vector2.ZERO, 64.0, 11.0, a0, a0 + TAU * 0.9, 36)
		var ws := press(36, 7.5, 0.8, 0.12, 0.15)
		n.ek(pts, ws, S_INK, B_KURU, 0.0, 0.22, hold, 0.3)
		n.ek(pts, scale_w(ws, 0.3), S_COLOR, B_INCE, 0.01, 0.22, hold, 0.28)
		n.ek(arc(Vector2.ZERO, 32.0, 5.0, 0.0, TAU, 24), swell(24, 12.0, 0.7, 0.3), S_WASH, B_SULU, 0.0, 0.2, hold, 0.3)


static func ok_iz(arrow: Node2D, p: int, w := 3.4) -> SanatFX:
	var n := spawn("ok_iz", Vector2.ZERO, Color.WHITE, 3.0, p)
	if n:
		n.follow = arrow
		n.data = {"hist": [arrow.global_position], "w": w}
		n.z_index = 56
	return n


static func ok_saplan(pos: Vector2, p: int) -> void:
	var l := leke(pos + Vector2(0, -2), p, 56)
	if l:
		l.el("splat_c", Vector2.ZERO, -PI * 0.5 + randf_range(-0.4, 0.4), Vector2(26.0, 20.0), V_SPLASH, 0.0, 0.03, 0.05, 0.26)


# ------------------------------------------------------------------ Demir Duruş
static func demir_kalkan(pl: Node2D, f: int) -> SanatFX:
	var n := spawn("kalkan", pl.global_position + Vector2(0, -22), Color.WHITE, 9.0, DEMIR)
	if n:
		n.follow = pl
		n.facing = f
		n.data = {"off": Vector2(0, -22)}
		n.z_index = 56
	return n


static func demir_ors(hp: Vector2, f: int) -> void:
	## Örs: karşılanan darbede altın ışınsal fırça kılları, varak, sıçrantı
	var n := firca(hp, ALTIN, 58)
	if n:
		for k in 9:
			var a := float(k) / 9.0 * TAU + randf_range(-0.12, 0.12)
			var d := Vector2.from_angle(a)
			n.ek(line(d * 6.0, d * randf_range(30.0, 48.0), 5, randf_range(-3, 3)), press(5, 4.5, 1.0, 0.05, 0.08), S_INK, B_SICRAT, 0.0, 0.05, 0.05, 0.16)
			n.ek(line(d * 6.0, d * 26.0, 5), press(5, 2.0, 1.0, 0.05, 0.08), S_GOLD, B_INCE, 0.004, 0.05, 0.04, 0.14)
	sicrat(hp, DEMIR, 52.0, 57, false, true)


static func demir_karsi(pos: Vector2, f: int, R: float) -> void:
	## Karşılık: altın varaklı büyük yatay sumi kesiği
	kesik(pos, (0.08 if f > 0 else PI - 0.08), R * 2.4, 15.0, ALTIN, -0.1 * f, 0.12, 58, true)
	var g := leke(pos + Vector2(f * R * 0.6, 0), ALTIN, 58)
	if g:
		g.el("varak", Vector2.ZERO, randf() * TAU, Vector2.ONE * 84.0, V_SPLASH, 0.03, 0.05, 0.14, 0.5)


# ================================================================== v31 kombo sanatları
# ------------------------------------------------------------------ ortak: damga (yansıma sözcüğü), yaprak, ritim
static func damga(pos: Vector2, word: String, p: int, f: int, k := 1.0) -> void:
	## Bitiriş yansıma sözcüğü (atlas: cit ÇIT!, kut KÜT!, vus VUŞ!, cat ÇAT!, viz VIZ!, tam TAM!): arkasında sıçrantı,
	## önünde eğik siyah fırça yazısı (düşmanların üstünde, kısa süre)
	var s := leke(pos, p, 60)
	if s:
		s.el("splat_b", Vector2(-4, 4), randf() * TAU, Vector2.ONE * 50.0 * k, V_SPLASH, 0.0, 0.05, 0.16, 0.4)
	var g := leke(pos, p, 61)
	if g:
		g.el(word, Vector2.ZERO, -0.1 * f, Vector2(84.0, 42.0) * k, V_STAMP, 0.02, 0.05, 0.22, 0.46)


static func yapraklar(n: SanatFX, c: Vector2, count: int, spread: float, speed: float, delay := 0.0, size := 5.0) -> void:
	## Erik çiçeği yaprakları (sumi-e): kısa kıvrık ıslak dokunuşlar, merkezden dışa savrulup süzülür
	for i in count:
		var a := randf() * TAU
		var d := Vector2.from_angle(a)
		var o := c + d * randf_range(0.2, 1.0) * spread
		var r := Vector2.from_angle(randf() * TAU) * size
		var pts := PackedVector2Array([o - r, o + r.orthogonal() * 0.35, o + r])
		var v := d * speed * randf_range(0.5, 1.0) + Vector2(0, randf_range(10.0, 40.0))
		n.ek(pts, PackedFloat32Array([size * 0.5, size * 1.2, size * 0.4]), S_COLOR, B_ISLAK, delay + randf() * 0.04, 0.03, randf_range(0.12, 0.3), 0.2, v)


func _draw_ritim() -> void:
	## Daralan halka: dıştan içteki hedef halkaya pre sürede kapanır; kapanış anı ışınlar (TAM'da altın)
	var pre := float(data.get("pre", 0.34))
	var ok: bool = data.get("ok", false)
	var miss: bool = data.get("kacti", false)
	var k := clampf(t / pre, 0.0, 1.0)
	var after := maxf(0.0, t - pre)
	var ds := clampf(after / 0.28, 0.0, 1.0)
	if miss:
		ds = maxf(ds, 0.6)
	var r1 := 18.0
	_bs(arc(Vector2.ZERO, r1, r1, -PI * 0.5, -PI * 0.5 + TAU * 0.96, 28), press(28, 2.4, 0.8, 0.5, 0.2), S_DRY, B_KURU, 1.0, maxf(0.3, ds))
	if k < 1.0:
		var r := lerpf(50.0, r1, k)
		var a0 := -PI * 0.5 + t * 2.5
		var pts := arc(Vector2.ZERO, r, r, a0, a0 + TAU * 0.92, 34)
		var ws := press(34, 3.5 + 3.5 * k, 0.7, 0.25, 0.15)
		_bs(pts, ws, S_INK, B_KURU, clampf(t / 0.06, 0.0, 1.0), ds)
		_bs(pts, scale_w(ws, 0.36), S_COLOR, B_INCE, clampf(t / 0.06, 0.0, 1.0), ds)
	elif after < 0.2:
		var q := after / 0.2
		var pts2 := arc(Vector2.ZERO, r1, r1, -PI * 0.5, -PI * 0.5 + TAU, 34)
		_bs(pts2, press(34, 7.0, 1.0, 0.8, 0.2), S_INK if not ok else S_HOT, B_ORTA, 1.0, q)
		for i in 8:
			var d := Vector2.from_angle(float(i) / 8.0 * TAU + 0.2)
			_bs(line(d * (r1 + 3.0), d * (r1 + 10.0 + 18.0 * q), 3), press(3, 3.2, 1.0, 0.1, 0.1), S_HOT if ok else S_DRY, B_INCE, 1.0, q * 0.8)


# ------------------------------------------------------------------ Kurt Dansı (al)
static func kurt_hazir(gp: Vector2, f: int, p: int) -> void:
	## Hazırlık: arkadan ayağa toplanan kuru hız çizgileri (çömelen kurt), altta yıkama
	var n := firca(gp, p, 56)
	if n:
		for k in 4:
			var y := -6.0 - 9.0 * k
			n.ek(line(Vector2(-f * (70.0 + 14.0 * k), y), Vector2(-f * 8.0, y + 2.0), 6, f * 2.0), press(6, 3.6, 0.5, 0.6, 0.6), S_DRY, B_COK_KURU, 0.015 * k, 0.09, 0.03, 0.12)
		n.ek(line(Vector2(-f * 60.0, -18.0), Vector2(-f * 6.0, -16.0), 6), press(6, 1.4, 0.4, 0.7, 0.7), S_COLOR, B_INCE, 0.02, 0.09, 0.03, 0.1)
	var l := leke(gp, SUMI, -1)
	if l:
		l.el("wash", Vector2(-f * 10.0, -6.0), 0.0, Vector2(80.0, 22.0), V_DRY, 0.0, 0.06, 0.05, 0.28)


static func kurt_adim(p0: Vector2, p1: Vector2, p: int, k: int) -> void:
	## Göz açıp kapayınca atılış: yol boyunca kuru hız fırçası (geniş), sumi çizgi, al damar, ak çekirdek, savrulan yapraklar
	var n := firca(p0, p, 57)
	if n == null:
		return
	var d := p1 - p0
	if d.length() < 4.0:
		d = Vector2(1, 0) * 4.0
	var sg := 1.0 if k % 2 == 0 else -1.0
	var a := Vector2.ZERO
	var b := d
	n.ek(line(a + Vector2(0, -6), b + Vector2(0, -8), 12, sg * 6.0, 1.0, k), swell(12, 22.0, 0.15, 0.5), S_WASH, B_SULU, 0.0, 0.05, 0.08, 0.2)
	n.ek(line(a + Vector2(0, 8), b + Vector2(0, 4), 10, sg * 4.0, 1.0, k + 3), press(10, 6.0, 0.5, 0.2, 0.7), S_DRY, B_COK_KURU, 0.0, 0.05, 0.06, 0.16)
	var main := line(a, b, 12, sg * 5.0, 1.2, k)
	var ws := press(12, 8.0, 0.35, 0.5, 0.7)
	n.ek(main, ws, S_INK, B_KURU, 0.0, 0.055, 0.1, 0.2)
	n.ek(main, scale_w(ws, 0.36), S_COLOR, B_ORTA, 0.004, 0.055, 0.1, 0.18)
	n.ek(main, scale_w(ws, 0.14), S_HOT, B_INCE, 0.008, 0.055, 0.05, 0.12)
	yapraklar(n, b * 0.6, 4, 16.0, 60.0, 0.03, 4.0)


static func kurt_kesik(p0: Vector2, p1: Vector2, p: int, k: int) -> void:
	## Varış kesiği: geçilen yol boyunca yatay, hafif eğik ince uzun sumi kesik (iaido) + al damar
	var c := (p0 + p1) * 0.5
	var L := maxf(60.0, p0.distance_to(p1) + 30.0)
	var ang := (p1 - p0).angle() + (0.12 if k % 2 == 0 else -0.12)
	kesik(c, ang, L, 9.0, p, 0.04 * (1.0 if k % 2 == 0 else -1.0), 0.06, 57, false, true)


func _draw_kesik_iz() -> void:
	## Düşmanın üstünde asılı al kesik: çizilerek açılır, nabız gibi atan ak çekirdek; patlayınca söner
	var ang := float(data.get("ang", 0.5))
	var L := float(data.get("L", 40.0))
	var d := Vector2.from_angle(ang)
	var rv := clampf(t / 0.05, 0.0, 1.0)
	var ds := 1.0 - _fade
	var pts := line(-d * L * 0.5, d * L * 0.5, 10, 0.08 * L, 0.6, int(ang * 10.0))
	var ws := swell(10, float(data.get("w", 8.0)), 0.06, 0.7)
	_bs(pts, ws, S_INK, B_ISLAK, rv, ds)
	_bs(pts, scale_w(ws, 0.4), S_COLOR, B_KURU, rv, ds)
	var pulse := 0.5 + 0.5 * sin(t * 26.0)
	_bs(pts, scale_w(ws, 0.13 + 0.06 * pulse), S_HOT, B_INCE, rv, maxf(ds, 0.35 - 0.3 * pulse))


static func kurt_iz(e: Node2D, ang: float, p: int, n: int) -> SanatFX:
	var iz := spawn("kesik_iz", e.call("center") if e.has_method("center") else e.global_position, Color.WHITE, 9.0, p)
	if iz:
		iz.follow = e
		iz.data = {"ang": ang + (0.0 if n <= 1 else (PI * 0.5 if n % 2 == 0 else 0.3)), "L": 40.0 + 6.0 * minf(n, 3), "w": 7.0 + 1.5 * minf(n, 3)}
		iz.z_index = 58
	return iz


static func kurt_patla(c: Vector2, p: int, n: int, tam: bool) -> void:
	## İzler patlar: büyük al X (sumi + ak çekirdek), sıçrantı, savrulan erik yaprakları (TAM: altın varak)
	var L := 74.0 + 8.0 * minf(n, 3)
	kesik(c, -PI * 0.25 + randf_range(-0.15, 0.15), L, 13.0, p, 0.1, 0.08, 58, false, true)
	kesik(c, PI * 0.25 + randf_range(-0.15, 0.15), L * 0.92, 12.0, p, -0.1, 0.08, 58, false, true)
	sicrat(c, p, 56.0, 57, true, tam)
	var y := firca(c, p, 58)
	if y:
		yapraklar(y, Vector2.ZERO, 9, 14.0, 130.0, 0.02, 5.0)


static func kurt_kin(c: Vector2, f: int, p: int) -> void:
	## Kına giriş: belde kısa yatay sumi + ak çekirdek (bıçağın kına kayışı)
	var n := firca(c + Vector2(-f * 4.0, 6.0), p, 58)
	if n:
		n.ek(line(Vector2(f * 26.0, 0.0), Vector2(-f * 22.0, 2.0), 6), press(6, 5.0, 1.0, 0.1, 0.1), S_INK, B_ORTA, 0.0, 0.04, 0.06, 0.16)
		n.ek(line(Vector2(f * 24.0, -0.5), Vector2(-f * 18.0, 1.5), 6), press(6, 1.6, 1.0, 0.1, 0.1), S_HOT, B_INCE, 0.005, 0.04, 0.04, 0.1)
	var g := spawn("parilti", c + Vector2(-f * 18.0, 6.0), Color(1.0, 0.75, 0.85), 0.22)
	if g:
		g.data = {"s": 14.0}


# ------------------------------------------------------------------ Evren Kuyruğu (yeşim)
static func _pul(n: SanatFX, c: Vector2, ang: float, s: float, delay: float) -> void:
	## Ejder pulu: küçük hilal dokunuş (kuru)
	var d := Vector2.from_angle(ang)
	var o := d.orthogonal()
	n.ek(PackedVector2Array([c - o * s, c + d * s * 0.6, c + o * s]), PackedFloat32Array([s * 0.3, s * 0.7, s * 0.25]), S_INK, B_KURU, delay, 0.04, 0.08, 0.16)


static func evren_toplan(gp: Vector2, f: int, p: int) -> void:
	## Hazırlık: ayakların çevresine toplanan pullar ve alçak yıkama
	var n := firca(gp, p, 56)
	if n:
		for k in 6:
			var sd := -1.0 if k % 2 == 0 else 1.0
			var x := sd * (26.0 + 8.0 * k)
			_pul(n, Vector2(x, -6.0 - 3.0 * (k % 3)), PI if sd > 0 else 0.0, 5.0, 0.015 * k)
		n.ek(line(Vector2(-f * 60.0, -3.0), Vector2(f * 14.0, -4.0), 8, 0.0, 1.0), press(8, 3.0, 0.4, 0.5, 0.6), S_COLOR, B_INCE, 0.02, 0.1, 0.04, 0.12)
	var l := leke(gp, SUMI, -1)
	if l:
		l.el("wash_b", Vector2(0, -6.0), 0.0, Vector2(96.0, 24.0), V_DRY, 0.0, 0.06, 0.06, 0.3)


static func evren_supur(gp: Vector2, f: int, R: float, p: int) -> void:
	## Alçak tam tur: ayak hizasında yassı elips fırça (arkadan başlayıp öne dolanır), kuyruk ucunda kuru kıllar, toz kılları
	var n := firca(gp + Vector2(0, -8.0), p, 57)
	if n == null:
		return
	var rx := R + 32.0
	var a0 := PI * 0.5 + (0.0 if f > 0 else PI) + PI
	var pts := arc(Vector2.ZERO, rx, 10.0, a0, a0 + f * TAU * 1.04, 36)
	var ws := press(36, 13.0, 0.5, 0.15, 0.25)
	n.ek(pts, ws, S_INK, B_KALIN_KURU, 0.0, 0.2, 0.05, 0.2)
	n.ek(pts, scale_w(ws, 0.34), S_COLOR, B_ORTA, 0.01, 0.2, 0.05, 0.18)
	n.ek(pts, scale_w(ws, 0.12), S_HOT, B_INCE, 0.015, 0.2, 0.03, 0.12)
	for k in 8:
		var a := float(k) / 8.0 * TAU + randf_range(-0.2, 0.2)
		var d := Vector2(cos(a), 0.0)
		var y := 6.0
		n.ek(line(Vector2(d.x * rx * 0.8, y), Vector2(d.x * (rx + randf_range(14, 30)), y - randf_range(8, 18)), 4, 0.0), press(4, 3.5, 1.0, 0.1, 0.1), S_DRY, B_SICRAT, 0.06 + 0.015 * k, 0.05, 0.03, 0.12)
	var l := leke(gp, SUMI, -1)
	if l:
		l.el("wash", Vector2(0, -4.0), 0.0, Vector2(rx * 2.2, 26.0), V_DRY, 0.0, 0.08, 0.08, 0.36)


static func evren_sarmal(gp: Vector2, H: float, f: int, p: int) -> void:
	## Yükselen sarmal: oyuncunun çevresinde iki tur yeşim fırça helezonu (önü koyu, arkası sulu), üstünde pullar
	var n := firca(gp, p, 57)
	var nb := firca(gp, p, -1)
	if n == null or nb == null:
		return
	var turns := 2.2
	var N := 44
	var cur_pts := PackedVector2Array()
	var cur_front := true
	for i in N + 1:
		var s := float(i) / N
		var th := s * TAU * turns * float(f) + PI * 0.5
		var q := Vector2(cos(th) * 34.0, -s * H + sin(th) * 6.0 - 4.0)
		var front := sin(th) > 0.0
		if i == 0:
			cur_front = front
		if front != cur_front or i == N:
			cur_pts.append(q)
			if cur_pts.size() >= 2:
				var ws := swell(cur_pts.size() - 1, 9.0 + 3.0 * (1.0 - s), 0.2, 0.6)
				var dl := 0.22 * s
				if cur_front:
					n.ek(cur_pts, ws, S_INK, B_KURU, dl, 0.04, 0.12, 0.2)
					n.ek(cur_pts, scale_w(ws, 0.36), S_COLOR, B_ORTA, dl + 0.004, 0.04, 0.12, 0.18)
					n.ek(cur_pts, scale_w(ws, 0.12), S_HOT, B_INCE, dl + 0.008, 0.04, 0.06, 0.12)
				else:
					nb.ek(cur_pts, scale_w(ws, 1.3), S_WASH, B_SULU, dl, 0.04, 0.12, 0.2)
					nb.ek(cur_pts, scale_w(ws, 0.5), S_DRY, B_COK_KURU, dl, 0.04, 0.1, 0.18)
			cur_pts = PackedVector2Array([q])
			cur_front = front
		else:
			cur_pts.append(q)
		if i % 5 == 2 and front:
			_pul(n, q + Vector2(0, -6.0), -PI * 0.5 + randf_range(-0.4, 0.4), 4.5, 0.22 * s + 0.02)


static func evren_cark(c: Vector2, f: int, p: int, R: float) -> void:
	## Çark: önde dikine dönen büyük yeşim halka (baş üstünden öne, aşağı); ejderin kuyruğu
	var n := firca(c, p, 57)
	if n == null:
		return
	var cc := Vector2(f * R * 0.35, 6.0)
	var r := R + 18.0
	var a0 := -PI * 0.5 - f * 0.9
	var pts := arc(cc, r, r * 1.05, a0, a0 + f * PI * 1.35, 26)
	var ws := press(26, 18.0, 0.4, 0.2, 0.4)
	n.ek(pts, ws, S_INK, B_ISLAK, 0.0, 0.1, 0.1, 0.22)
	n.ek(pts, scale_w(ws, 0.34), S_COLOR, B_ORTA, 0.006, 0.1, 0.1, 0.2)
	n.ek(pts, scale_w(ws, 0.13), S_HOT, B_INCE, 0.01, 0.1, 0.05, 0.14)
	for i in range(3, 24, 4):
		var q := pts[i]
		_pul(n, q + (q - cc).normalized() * 12.0, (q - cc).angle(), 5.0, 0.04 + 0.004 * i)


static func evren_kut(gp: Vector2, f: int, p: int, carp: int, tam: bool) -> void:
	## Çakılış: yukarı-arkadan kıvrılıp yere inen kalın ejder kuyruğu (S eğrisi, ucu yerde en kalın), pullar, yer yarığı,
	## iki yana yeşim sürtme, sıçrantı, "KÜT!" damgası
	var big := carp > 0
	var n := firca(gp, p, 57)
	if n:
		var pts := PackedVector2Array()
		var ws := PackedFloat32Array()
		var N := 18
		for i in N + 1:
			var u := float(i) / N
			var x := f * lerpf(-46.0, 14.0, u) + f * 24.0 * sin(u * PI * 1.4)
			var y := lerpf(-128.0, -2.0, pow(u, 1.15))
			pts.append(Vector2(x, y))
			ws.append(lerpf(3.0, 26.0, pow(u, 1.4)))
		n.ek(pts, ws, S_INK, B_ISLAK, 0.0, 0.06, 0.12, 0.24)
		n.ek(pts, scale_w(ws, 0.36), S_COLOR, B_ORTA, 0.006, 0.06, 0.12, 0.22)
		n.ek(pts, scale_w(ws, 0.12), S_HOT, B_INCE, 0.01, 0.06, 0.06, 0.14)
		for i in range(2, N, 3):
			var q := pts[i]
			var tg := (pts[mini(i + 1, N)] - pts[i - 1]).normalized()
			_pul(n, q - tg.orthogonal() * float(f) * (ws[i] * 0.5 + 4.0), tg.orthogonal().angle() + (PI if f > 0 else 0.0), 4.0 + ws[i] * 0.15, 0.05)
		for sd in [-1.0, 1.0]:
			for k in 2:
				var y2 := -1.5 - 4.0 * k
				var g := line(Vector2(sd * 8.0, y2), Vector2(sd * (88.0 + 16.0 * (1 - k)), y2 + 1.0), 8, -sd * 2.0, 1.0, k)
				var gw := press(8, 11.0 - 4.0 * k, 1.0, 0.05, 0.08)
				n.ek(g, gw, S_INK, B_SULU if k == 0 else B_KURU, 0.02, 0.08, 0.1, 0.24)
				n.ek(g, scale_w(gw, 0.3), S_COLOR, B_ORTA, 0.026, 0.08, 0.08, 0.2)
	var l := leke(gp, p, -1)
	if l:
		l.el("crack", Vector2(0, -0.3 * 50.0), 0.0, Vector2(220.0, 50.0), V_STAMP, 0.0, 0.05, 0.3, 0.7)
	var w := leke(gp, SUMI, -1)
	if w:
		w.el("wash", Vector2(0, -14.0), 0.0, Vector2(150.0, 54.0), V_DRY, 0.0, 0.07, 0.1, 0.45)
	sicrat(gp + Vector2(0, -16.0), p, 80.0 if big else 62.0, 57, false, tam)
	damga(gp + Vector2(f * 34.0, -70.0), "kut", p, f, (1.0 if big else 0.8) * (1.15 if tam else 1.0))


# ------------------------------------------------------------------ Tengri Çarkı (gök)
static func tengri_topla(pc: Vector2, f: int, p: int) -> void:
	## Hazırlık: baş üstüne toplanan ince rüzgâr çizgileri ve küçük ensō
	var n := firca(pc + Vector2(0, -40.0), p, 57)
	if n == null:
		return
	for k in 6:
		var a := float(k) / 6.0 * TAU + randf_range(-0.2, 0.2)
		var d := Vector2(cos(a), sin(a) * 0.5)
		n.ek(line(d * randf_range(56.0, 74.0), d * 10.0, 6, randf_range(-8, 8)), press(6, 3.0, 1.0, 0.2, 0.15), S_DRY, B_KURU, 0.015 * k, 0.12, 0.02, 0.1)
		n.ek(line(d * 50.0, d * 10.0, 6), press(6, 1.2, 1.0, 0.2, 0.15), S_COLOR, B_INCE, 0.015 * k + 0.01, 0.12, 0.02, 0.1)
	var a0 := randf() * TAU
	n.ek(arc(Vector2.ZERO, 14.0, 8.0, a0, a0 + TAU * 0.9, 20), press(20, 4.0, 0.8, 0.2, 0.2), S_INK, B_KURU, 0.08, 0.08, 0.1, 0.16)


func _draw_girdap() -> void:
	## Girdap: merkeze kıvrılan beş kol (log sarmal), dönerek daralır; ön yarı koyu, arka yarı sulu; ortada yıkama
	var tr := float(data.get("tr", 0.4))
	var R := lerpf(float(data.get("r0", 110.0)), float(data.get("r1", 46.0)), 1.0 - pow(1.0 - clampf(t / tr, 0.0, 1.0), 2.0))
	var spd := float(data.get("spd", 9.0))
	var a := _fade * clampf(t / 0.08, 0.0, 1.0)
	var dsb := 1.0 - a
	_bs(arc(Vector2.ZERO, R * 0.45, R * 0.2, 0.0, TAU, 28), swell(28, R * 0.5, 0.8, 0.3), S_WASH, B_SULU, 1.0, maxf(dsb, 0.3))
	for j in 5:
		var ph := -t * spd + float(j) * TAU / 5.0
		var pts := PackedVector2Array()
		var front := 0.0
		for i in 17:
			var s := float(i) / 16.0
			var th := ph + s * 2.6
			var rr := R * (1.0 - 0.84 * s)
			pts.append(Vector2(cos(th) * rr, sin(th) * rr * 0.42))
			front += sin(th)
		var fr := front / 17.0
		var ds := dsb + (0.0 if fr > -0.1 else 0.45)
		var ws := press(16, 9.0 * (1.0 - 0.08 * j), 0.9, 0.08, 0.12)
		_bs(pts, ws, S_INK, B_KALIN_KURU if j % 2 == 0 else B_KURU, 1.0, ds)
		_bs(pts, scale_w(ws, 0.32), S_COLOR, B_INCE, 1.0, ds)
		if fr > 0.2 and j % 2 == 1:
			_bs(pts.slice(0, 7), scale_w(ws.slice(0, 7), 0.15), S_HOT, B_INCE, 1.0, dsb)


static func tengri_vurus(cc: Vector2, k: int, f: int, p: int) -> void:
	## Hokkabazlık vuruşu: girdabın içinden geçen gök kesiği (her vuruş başka açıda)
	var angs := [-0.95, 0.95, 0.05, -0.3]
	var a: float = angs[k % 4]
	if f < 0:
		a = PI - a
	kesik(cc, a, 86.0 if k < 3 else 100.0, 11.0 if k < 3 else 13.0, p, 0.12 * (1.0 if k % 2 == 0 else -1.0), 0.06, 58, false, true)
	if k == 3:
		sicrat(cc + Vector2(f * 10.0, 0.0), p, 44.0, 57, false)


static func tengri_patla(cc: Vector2, f: int, p: int, tam: bool) -> void:
	## Çark patlar: sekiz kollu gök çarkı (ışınsal kalın fırça), dışa savrulan kırık ensō yayları, yıkama, sıçrantı
	var n := firca(cc, p, 58)
	if n:
		for i in 8:
			var a := float(i) / 8.0 * TAU + 0.2 + randf_range(-0.08, 0.08)
			var d := Vector2.from_angle(a)
			var L := randf_range(66.0, 92.0) * (1.15 if tam else 1.0)
			var pts := line(d * 12.0, d * L, 6, randf_range(-6, 6))
			var ws := press(6, 10.0, 0.6, 0.06, 0.25)
			n.ek(pts, ws, S_INK, B_KURU if i % 2 else B_ISLAK, 0.0, 0.06, 0.08, 0.2)
			n.ek(pts, scale_w(ws, 0.36), S_COLOR, B_ORTA, 0.005, 0.06, 0.08, 0.18)
			n.ek(pts, scale_w(ws, 0.14), S_HOT, B_INCE, 0.01, 0.06, 0.04, 0.12)
	var r := firca(cc, p, 58)
	if r:
		r.grow = Vector2(0.65, 1.45)
		for i in 4:
			var a0 := float(i) / 4.0 * TAU + randf_range(-0.2, 0.2)
			var pts2 := arc(Vector2.ZERO, 56.0, 50.0, a0, a0 + 1.0, 10)
			var ws2 := swell(10, 9.0, 0.1, 0.6)
			r.ek(pts2, ws2, S_INK, B_KALIN_KURU, 0.02, 0.05, 0.1, 0.22)
			r.ek(pts2, scale_w(ws2, 0.34), S_COLOR, B_INCE, 0.025, 0.05, 0.1, 0.2)
	var w := leke(cc, SUMI, -1)
	if w:
		w.el("wash", Vector2.ZERO, randf() * TAU, Vector2.ONE * 150.0, V_DRY, 0.0, 0.06, 0.08, 0.42)
	sicrat(cc, p, 70.0, 57, false, tam)


static func duvar_carp(pos: Vector2, nrm: Vector2, p: int) -> void:
	## Duvara çakılan düşman: duvarda sıçrantı ve duvar boyunca kuru kırık çizgiler
	sicrat(pos, p, 48.0, 57, false)
	var n := firca(pos, p, 57)
	if n:
		for k in 5:
			var a := nrm.angle() + PI * 0.5 + (float(k) - 2.0) * 0.5 + randf_range(-0.15, 0.15)
			var d := Vector2.from_angle(a)
			if d.dot(nrm) < 0.0:
				d = d - nrm * d.dot(nrm) * 1.2
			n.ek(line(Vector2.ZERO, d * randf_range(18.0, 34.0), 4, randf_range(-3, 3)), press(4, 4.0, 1.0, 0.1, 0.1), S_INK, B_KURU, 0.0, 0.04, 0.06, 0.18)
	FX.dust(pos, nrm, 5, 0.3)


# ------------------------------------------------------------------ Yer Yarığı (toprak)
static func yarik_tepme(gp: Vector2, f: int, p: int, xs: Array, R: float) -> void:
	## Zemin dövülür: önde küçük yarık, zemin boyunca iki yana koşan toprak çizgisi, seken her düşmanın altında yukarı
	## fışkıran toz fırçaları, havaya kalkan taş kıymıkları
	var hit := gp + Vector2(f * R * 0.7, 0.0)
	var l := leke(hit, p, -1)
	if l:
		l.el("crack", Vector2(0, -0.3 * 34.0), 0.0, Vector2(150.0, 34.0), V_STAMP, 0.0, 0.04, 0.2, 0.5)
	var n := firca(gp, p, 57)
	if n == null:
		return
	for sd in [-1.0, 1.0]:
		var g := line(Vector2(f * R * 0.7, -2.0), Vector2(f * R * 0.7 + sd * (R + 76.0), -1.0), 10, 0.0, 1.0)
		var gw := press(10, 6.0, 1.0, 0.05, 0.08)
		n.ek(g, gw, S_INK, B_KURU, 0.0, 0.12, 0.05, 0.18)
		n.ek(g, scale_w(gw, 0.35), S_COLOR, B_INCE, 0.005, 0.12, 0.04, 0.16)
	for x in xs:
		var bx := float(x)
		for k in 3:
			var ox := bx + (float(k) - 1.0) * 7.0
			n.ek(line(Vector2(ox, -2.0), Vector2(ox + randf_range(-6, 6), -randf_range(38.0, 58.0)), 5, randf_range(-3, 3)), press(5, 5.0 - k, 1.0, 0.05, 0.1), S_DRY if k != 1 else S_INK, B_COK_KURU, 0.02 * k, 0.08, 0.04, 0.16)
	for k in 6:
		var a := -PI * 0.5 + randf_range(-0.9, 0.9)
		var d := Vector2.from_angle(a)
		var o := Vector2(f * R * 0.7 + randf_range(-20, 20), -4.0)
		n.ek(PackedVector2Array([o, o + d * 4.0, o + d * 8.0]), PackedFloat32Array([5.0, 6.0, 3.0]), S_INK, B_ISLAK, 0.0, 0.02, 0.18, 0.15, d * randf_range(120.0, 220.0))


static func yarik_x(c: Vector2, f: int, k: int, p: int, r: float) -> void:
	## Havada X: toprak rengi iki çapraz kesik
	if k == 0:
		kesik(c, (PI * 0.25 if f > 0 else PI * 0.75), r * 1.8, 15.0, p, 0.12 * f, 0.1, 57, false, true)
	else:
		kesik(c + Vector2(0, -2), (-PI * 0.25 if f > 0 else -PI * 0.75), r * 1.8, 15.0, p, -0.12 * f, 0.1, 57, false, true)


static func yarik_cat(gp: Vector2, f: int, p: int, carp: int, tam: bool) -> void:
	## Dikine yarış: yukarıdan yere kalın toprak-sumi darbe, yer yarığı, sıçrantı, "ÇAT!"
	cekis_inis(gp, f, p, 92.0, 70.0)
	var n := firca(gp, p, 57)
	if n:
		n.ek(line(Vector2(-f * 4.0, -2.0), Vector2(f * 60.0, -1.0), 8, 0.0, 2.0), press(8, 4.0, 1.0, 0.1, 0.1), S_HOT, B_INCE, 0.03, 0.1, 0.12, 0.2)
	damga(gp + Vector2(f * 30.0, -72.0), "cat", p, f, (1.0 if carp > 0 else 0.8) * (1.15 if tam else 1.0))


static func yarik_parca(pos: Vector2, dir: int, p: int, k: int) -> void:
	## İlerleyen yarığın bir parçası: kısa yarık lekesi, kızgın toprak çizgisi, havaya sıçrayan kıymık
	var l := leke(pos, p, -1)
	if l:
		l.el("crack", Vector2(0, -0.3 * 22.0), 0.0 if k % 2 == 0 else PI, Vector2(70.0, 22.0), V_STAMP, 0.0, 0.03, 0.25, 0.6)
	var n := firca(pos, p, 56)
	if n:
		n.ek(line(Vector2(-dir * 14.0, -2.0), Vector2(dir * 12.0, -1.0), 4, 0.0, 1.5, k), press(4, 3.0, 1.0, 0.3, 0.3), S_HOT, B_INCE, 0.0, 0.03, 0.18, 0.25)
		for i in 2:
			var d := Vector2.from_angle(-PI * 0.5 + dir * randf_range(-0.2, 0.7))
			var o := Vector2(randf_range(-6, 6), -3.0)
			n.ek(PackedVector2Array([o, o + d * 3.0, o + d * 6.0]), PackedFloat32Array([4.0, 5.0, 2.5]), S_INK, B_ISLAK, 0.0, 0.02, 0.14, 0.14, d * randf_range(90.0, 170.0))
	FX.dust(pos, Vector2(dir * 0.3, -1.0), 2, 0.26)


static func yarik_son(pos: Vector2, dir: int, p: int) -> void:
	sicrat(pos + Vector2(0, -8.0), p, 40.0, 57, false)
	FX.dust(pos, Vector2(dir * 0.4, -1.0), 5, 0.3)


# ------------------------------------------------------------------ Akıncı Akını (ak)
static func akin_takla(gp: Vector2, f: int, p: int) -> void:
	## Geri takla: geriye-yukarı kıvrılan kuru fırça yayı
	var n := firca(gp, p, 56)
	if n == null:
		return
	var c := Vector2(-f * 18.0, -34.0)
	var a0 := PI * 0.5 + f * 0.4
	var pts := arc(c, 30.0, 34.0, a0, a0 - f * PI * 1.25, 20)
	var ws := press(20, 7.0, 0.5, 0.1, 0.3)
	n.ek(pts, ws, S_INK, B_KURU, 0.0, 0.16, 0.06, 0.18)
	n.ek(pts, scale_w(ws, 0.35), S_COLOR, B_INCE, 0.01, 0.16, 0.05, 0.16)


static func akin_yay(src: Vector2, f: int, p: int) -> void:
	## Yelpaze bırakışı: yaydan öne-aşağı açılan beş kuru çizgi + küçük ensō
	var n := firca(src, p, 57)
	if n == null:
		return
	for i in 5:
		var a := (0.35 + 0.14 * (float(i) - 2.0)) if f > 0 else (PI - 0.35 - 0.14 * (float(i) - 2.0))
		var d := Vector2.from_angle(a)
		n.ek(line(d * 8.0, d * randf_range(40.0, 56.0), 4), press(4, 3.0, 1.0, 0.05, 0.1), S_DRY, B_COK_KURU, 0.01 * i, 0.05, 0.03, 0.12)
	var a0 := randf() * TAU
	n.ek(arc(Vector2.ZERO, 11.0, 11.0, a0, a0 + TAU * 0.85, 18), press(18, 3.6, 0.8, 0.2, 0.2), S_INK, B_KURU, 0.0, 0.05, 0.05, 0.14)


static func civi(pos: Vector2, vel: Vector2, p: int) -> void:
	## Çivilenen düşman: saplanan okun gövdesi (kısa kalın sumi) + iki tüy kılı + küçük sıçrantı
	var d := vel.normalized() if vel.length() > 1.0 else Vector2.RIGHT
	var n := firca(pos, p, 58)
	if n:
		n.ek(line(-d * 16.0, d * 2.0, 3), press(3, 3.0, 1.0, 0.6, 0.2), S_INK, B_ORTA, 0.0, 0.02, 0.3, 0.16)
		for sd in [-1.0, 1.0]:
			n.ek(PackedVector2Array([-d * 14.0, -d * 19.0 + d.orthogonal() * sd * 4.0]), PackedFloat32Array([2.0, 0.6]), S_COLOR, B_INCE, 0.0, 0.02, 0.3, 0.14)
	var l := leke(pos + d * 2.0, p, 57)
	if l:
		l.el("splat_c", Vector2.ZERO, d.angle(), Vector2(22.0, 18.0), V_SPLASH, 0.0, 0.03, 0.05, 0.24)


static func akin_ger(tip: Vector2, f: int, p: int, dur: float) -> void:
	## Germe: okun ucuna doğru toplanan rüzgâr çizgileri (dur sürede), sonda uçta çelik parıltısı
	var n := firca(tip, p, 57)
	if n:
		for k in 7:
			var a := (PI if f > 0 else 0.0) + (float(k) - 3.0) * 0.32 + randf_range(-0.1, 0.1)
			var d := Vector2.from_angle(a)
			n.ek(line(d * randf_range(52.0, 70.0), d * 6.0, 5, randf_range(-5, 5)), press(5, 2.6, 1.0, 0.2, 0.15), S_DRY, B_KURU, dur * 0.12 * k, 0.1, 0.02, 0.08)
	var g := spawn("parilti", tip + Vector2(f * 6.0, 0.0), Color(1.0, 0.96, 0.85), dur + 0.08)
	if g:
		g.data = {"s": 12.0}


static func akin_birak(src: Vector2, f: int, p: int, tam: bool) -> void:
	## Bırakış: yayın arkasında geri tepen kuru çizgiler, yıkama halkası, sıçrantı (TAM: altın varak)
	var n := firca(src, p, 57)
	if n:
		for k in 5:
			var a := (PI if f > 0 else 0.0) + (float(k) - 2.0) * 0.4
			var d := Vector2.from_angle(a)
			n.ek(line(d * 6.0, d * randf_range(26.0, 40.0), 4), press(4, 3.0, 1.0, 0.05, 0.1), S_INK, B_SICRAT, 0.0, 0.04, 0.04, 0.12)
		n.ek(arc(Vector2.ZERO, 16.0, 16.0, 0.0, TAU, 24), swell(24, 10.0, 0.7, 0.3), S_WASH, B_SULU, 0.0, 0.05, 0.05, 0.2)
	sicrat(src + Vector2(f * 8.0, 0.0), p, 40.0, 57, false, tam)


func _delen_step(delta: float) -> void:
	## Delen ok: hilal gibi ilerler (vurus_cb ile vurur), duvarda / menzil sonunda kırılır
	var dist := float(data.get("dist", 0.0)) + vel.length() * delta
	data["dist"] = dist
	var lv: Node = FX.level
	var nxt := global_position + vel * delta
	if lv and lv.has_method("solid_at") and lv.solid_at(nxt + Vector2(facing * 10.0, 0.0)) and t > 0.02:
		_delen_break(true)
		return
	global_position = nxt
	var hist: Array = data.get("hist", [])
	hist.push_front(global_position)
	if hist.size() > 9:
		hist.pop_back()
	data["hist"] = hist
	var box := Rect2(global_position + Vector2(-20, -11), Vector2(40, 22))
	var maxn := int(data.get("max", 8))
	for e in get_tree().get_nodes_in_group("dusman"):
		if _hit.size() >= maxn:
			break
		if not is_instance_valid(e) or e.dead or _hit.has(e):
			continue
		if box.intersects(e.hurt_rect()):
			_hit.append(e)
			if vurus_cb.is_valid():
				vurus_cb.call(e, e.hurt_rect().get_center())
	if dist >= float(data.get("menzil", 420.0)) or _hit.size() >= maxn:
		_delen_break(false)


func _delen_break(wall: bool) -> void:
	InkFX.hit("pierce", global_position, Vector2(facing, 0), 7, 2, 1.0)
	sicrat(global_position, pal, 44.0 if wall else 34.0, 57, wall)
	if wall:
		var n := firca(global_position, pal, 57)
		if n:
			for k in 5:
				var d := Vector2.from_angle((PI if facing > 0 else 0.0) + (float(k) - 2.0) * 0.5)
				n.ek(line(Vector2.ZERO, d * randf_range(16.0, 30.0), 4), press(4, 3.4, 1.0, 0.1, 0.1), S_INK, B_KURU, 0.0, 0.04, 0.06, 0.16)
	queue_free()


func _draw_delen() -> void:
	## Delen ok: arkada geniş kuru hız izi + sulu yankılar, uzun sumi gövde, kemik rengi damar, ak çekirdek, uçta kama, tüyler
	var f := float(facing)
	var g := 1.0 + (0.18 if data.get("tam", false) else 0.0)
	var hist: Array = data.get("hist", [])
	for j in range(hist.size() - 1, 0, -3):
		var off: Vector2 = (hist[j] as Vector2) - global_position
		_bs(line(off + Vector2(-f * 20.0, 0), off + Vector2(f * 6.0, 0), 4), swell(4, 9.0 * g, 0.3, 0.6), S_WASH, B_SULU, 1.0, 0.3 + float(j) / 12.0)
	for k in 3:
		var y := (float(k) - 1.0) * 6.0 * g
		_bs(line(Vector2(-f * 30.0, y), Vector2(-f * (110.0 + 20.0 * float(k % 2)), y * 1.4), 5), press(5, 3.0 * g, 0.9, 0.05, 0.1), S_DRY, B_COK_KURU, 1.0, 0.1)
	var body := line(Vector2(-f * 84.0 * g, 0.0), Vector2(f * 10.0, 0.0), 10)
	var ws := press(10, 10.0 * g, 0.25, 0.7, 0.75)
	var rv := clampf(t / 0.04, 0.0, 1.0)
	_bs(body, ws, S_INK, B_ISLAK, rv)
	_bs(body, scale_w(ws, 0.4), S_COLOR, B_ORTA, rv)
	_bs(body, scale_w(ws, 0.15), S_HOT, B_INCE, rv)
	_bs(PackedVector2Array([Vector2(f * 6.0, 0.0), Vector2(f * 14.0, 0.0), Vector2(f * 24.0 * g, 0.0)]), PackedFloat32Array([11.0 * g, 6.0 * g, 0.6]), S_INK, B_ISLAK, rv)
	for sd in [-1.0, 1.0]:
		_bs(PackedVector2Array([Vector2(-f * 62.0 * g, 0.0), Vector2(-f * 72.0 * g, sd * 7.0 * g)]), PackedFloat32Array([3.0, 0.8]), S_INK, B_KURU, rv)


# ================================================================== düz fırça yardımcıları (HUD)
static func stroke(ci: CanvasItem, pts: PackedVector2Array, ws: PackedFloat32Array, c: Color) -> void:
	## Değişken genişlikli fırça çizgisi: noktaların iki yanına normal boyunca yarı genişlik; tek çokgen
	var n := pts.size()
	if n < 2 or c.a <= 0.003:
		return
	var left := PackedVector2Array()
	var right := PackedVector2Array()
	for i in n:
		var a := pts[maxi(0, i - 1)]
		var b := pts[mini(n - 1, i + 1)]
		var d := (b - a)
		if d.length() < 0.0001:
			d = Vector2.RIGHT
		var nn := d.normalized().orthogonal()
		var w := float(ws[mini(i, ws.size() - 1)]) * 0.5
		left.append(pts[i] + nn * w)
		right.append(pts[i] - nn * w)
	var poly := PackedVector2Array(left)
	for i in range(n - 1, -1, -1):
		poly.append(right[i])
	if Geometry2D.triangulate_polygon(poly).is_empty():
		# kendini kesen çokgen: parça parça dörtgenler
		for i in n - 1:
			var q := PackedVector2Array([left[i], left[i + 1], right[i + 1], right[i]])
			if not Geometry2D.triangulate_polygon(q).is_empty():
				ci.draw_colored_polygon(q, c)
		return
	ci.draw_colored_polygon(poly, c)


static func _arc_pts(c: Vector2, r: float, a0: float, a1: float, n: int, sx := 1.0, sy := 1.0) -> PackedVector2Array:
	var out := PackedVector2Array()
	for i in n + 1:
		var a := lerpf(a0, a1, float(i) / n)
		out.append(c + Vector2(cos(a) * r * sx, sin(a) * r * sy))
	return out


static func _taper(n: int, w0: float, w1: float, w2 := -1.0) -> PackedFloat32Array:
	## n+1 genişlik: w0 → (ortada w1) → w2 (verilmezse w0)
	var out := PackedFloat32Array()
	var we := w0 if w2 < 0.0 else w2
	for i in n + 1:
		var u := float(i) / n
		out.append(lerpf(w0, w1, u * 2.0) if u < 0.5 else lerpf(w1, we, (u - 0.5) * 2.0))
	return out


static func glyph_strokes(id: String, c: Vector2, s: float) -> Array:
	## Sanatın tamgası darbe darbe (yazılış sırasıyla): [[noktalar, göreli genişlikler (x W = s x 0,22)], ...]
	var out: Array = []
	match id:
		"kasirga":
			var sp := PackedVector2Array()
			var sw := PackedFloat32Array()
			for i in 29:
				var u := float(i) / 28.0
				var a := -PI * 0.5 + u * TAU * 1.15
				var r := s * (0.12 + 0.72 * u)
				sp.append(c + Vector2(cos(a), sin(a) * 0.82) * r)
				sw.append(lerpf(0.3, 1.0, u))
			out.append([sp, sw])
			out.append([_arc_pts(c + Vector2(0, s * 0.1), s * 0.98, 2.4, 3.3, 8), _taper(8, 0.2, 0.7, 0.1)])
		"bir_cekis":
			out.append([PackedVector2Array([c + Vector2(-s * 0.55, -s * 0.62), c + Vector2(s * 0.1, -s * 0.72), c + Vector2(s * 0.5, -s * 0.66)]),
				PackedFloat32Array([0.5, 0.9, 0.4])])
			out.append([PackedVector2Array([c + Vector2(s * 0.05, -s * 0.85), c + Vector2(-s * 0.02, -s * 0.2), c + Vector2(-s * 0.12, s * 0.45), c + Vector2(-s * 0.4, s * 0.9)]),
				PackedFloat32Array([0.6, 1.25, 1.0, 0.15])])
		"ay_hilali":
			var o := _arc_pts(c, s * 0.82, -2.2, 2.2, 16)
			var w2 := PackedFloat32Array()
			for i in 17:
				w2.append(0.15 + 1.6 * sin(float(i) / 16.0 * PI))
			var m := PackedVector2Array()
			for q in o:
				m.append(c + (q - c) * Vector2(-1, 1))
			out.append([m, w2])
			out.append([PackedVector2Array([c + Vector2(s * 0.25, 0), c + Vector2(s * 0.95, 0)]), PackedFloat32Array([0.7, 0.1])])
		"goge_yukselis":
			out.append([_arc_pts(c + Vector2(s * 0.45, s * 0.35), s * 0.95, PI * 0.95, PI * 1.55, 12), _taper(12, 0.2, 1.3, 0.15)])
			out.append([PackedVector2Array([c + Vector2(s * 0.1, -s * 0.2), c + Vector2(s * 0.12, s * 0.85)]), PackedFloat32Array([0.2, 0.9])])
			out.append([PackedVector2Array([c + Vector2(-s * 0.15, s * 0.6), c + Vector2(s * 0.12, s * 0.9), c + Vector2(s * 0.4, s * 0.6)]), PackedFloat32Array([0.6, 0.8, 0.6])])
		"bozkurt_atilisi":
			for k in 3:
				var y := (k - 1) * s * 0.42
				var x0 := -s * (0.9 - 0.2 * absf(k - 1))
				out.append([PackedVector2Array([c + Vector2(x0, y), c + Vector2(s * 0.55, y * 0.6)]), PackedFloat32Array([0.15, 1.1 if k == 1 else 0.6])])
			out.append([PackedVector2Array([c + Vector2(s * 0.35, -s * 0.5), c + Vector2(s * 0.92, 0), c + Vector2(s * 0.35, s * 0.5)]), PackedFloat32Array([0.4, 1.1, 0.4])])
		"kam_darbesi":
			out.append([_arc_pts(c, s * 0.62, -PI, PI, 24), _taper(24, 0.9, 0.5, 0.9)])
			for k in 5:
				var a := -PI * 0.5 + (k - 2) * 0.42
				var d := Vector2(cos(a), sin(a))
				out.append([PackedVector2Array([c + d * s * 0.2, c + d * s * 0.98]), PackedFloat32Array([0.8, 0.2])])
			out.append([PackedVector2Array([c + Vector2(-s * 0.06, s * 0.12), c + Vector2(s * 0.06, s * 0.12)]), PackedFloat32Array([1.5, 1.5])])
		"ok_yagmuru":
			for k in 3:
				var bx := (k - 1) * s * 0.5
				var p0 := c + Vector2(bx - s * 0.25, -s * 0.85 + absf(k - 1) * s * 0.2)
				var p1 := c + Vector2(bx + s * 0.15, s * 0.65 + absf(k - 1) * s * 0.1)
				out.append([PackedVector2Array([p0, p1]), PackedFloat32Array([0.3, 0.7])])
				var dv := (p1 - p0).normalized()
				# ok ucu: kısa kama darbe
				out.append([PackedVector2Array([p1 - dv * s * 0.09, p1 + dv * s * 0.35]), PackedFloat32Array([1.9, 0.1])])
		"demir_durus":
			out.append([PackedVector2Array([c + Vector2(-s * 0.95, -s * 0.15), c + Vector2(0, -s * 0.32), c + Vector2(s * 0.95, -s * 0.5)]), PackedFloat32Array([0.3, 1.1, 0.2])])
			out.append([_arc_pts(c + Vector2(0, -s * 0.05), s * 0.7, PI * 0.15, PI * 0.85, 14), _taper(14, 0.3, 1.0, 0.3)])
			out.append([PackedVector2Array([c + Vector2(0, s * 0.62), c + Vector2(0, s * 0.95)]), PackedFloat32Array([0.9, 0.5])])
		"kurt_dansi":
			# üç kıvrık pençe kesiği (sağ üstten sol alta) + altta kın çizgisi
			for k in 3:
				var x := (float(k) - 1.0) * s * 0.4
				out.append([PackedVector2Array([c + Vector2(x + s * 0.38, -s * 0.85), c + Vector2(x + s * 0.02, -s * 0.05), c + Vector2(x - s * 0.3, s * 0.6)]),
					PackedFloat32Array([0.25, 1.25, 0.12])])
			out.append([PackedVector2Array([c + Vector2(-s * 0.9, s * 0.9), c + Vector2(s * 0.9, s * 0.8)]), PackedFloat32Array([0.9, 0.3])])
		"evren_kuyrugu":
			# kıvrılan ejder kuyruğu (S): baş kalın, kuyruk ince + iki pul
			var ep := PackedVector2Array()
			var ew := PackedFloat32Array()
			for i in 17:
				var u := float(i) / 16.0
				ep.append(c + Vector2(lerpf(-0.8, 0.8, u) * s, sin(u * PI * 1.8 + 0.3) * s * 0.5))
				ew.append(lerpf(1.5, 0.12, u))
			out.append([ep, ew])
			out.append([PackedVector2Array([c + Vector2(-s * 0.45, -s * 0.5), c + Vector2(-s * 0.3, -s * 0.78)]), PackedFloat32Array([0.8, 0.2])])
			out.append([PackedVector2Array([c + Vector2(s * 0.15, s * 0.42), c + Vector2(s * 0.32, s * 0.72)]), PackedFloat32Array([0.8, 0.2])])
		"tengri_carki":
			# üç kollu çark (her kol merkezden dışa kıvrılır) + ortada nokta
			for k in 3:
				var tp := PackedVector2Array()
				var tw := PackedFloat32Array()
				for i in 11:
					var u := float(i) / 10.0
					var a := float(k) / 3.0 * TAU + u * 2.0
					tp.append(c + Vector2(cos(a), sin(a)) * s * (0.18 + 0.78 * u))
					tw.append(lerpf(1.1, 0.12, u))
				out.append([tp, tw])
			out.append([PackedVector2Array([c + Vector2(-s * 0.08, 0), c + Vector2(s * 0.08, 0)]), PackedFloat32Array([1.6, 1.6])])
		"yer_yarigi":
			# yukarıdan inen kalın darbe, zemin çizgisi, zeminden ilerleyen kırık yarık
			out.append([PackedVector2Array([c + Vector2(-s * 0.1, -s * 0.95), c + Vector2(-s * 0.05, -s * 0.25), c + Vector2(-s * 0.1, s * 0.45)]), PackedFloat32Array([0.5, 1.35, 1.0])])
			out.append([PackedVector2Array([c + Vector2(-s * 0.95, s * 0.52), c + Vector2(s * 0.95, s * 0.48)]), PackedFloat32Array([0.4, 0.9])])
			out.append([PackedVector2Array([c + Vector2(-s * 0.05, s * 0.55), c + Vector2(s * 0.25, s * 0.72), c + Vector2(s * 0.12, s * 0.84), c + Vector2(s * 0.5, s * 0.96), c + Vector2(s * 0.85, s * 0.9)]),
				PackedFloat32Array([0.7, 0.5, 0.45, 0.3, 0.1])])
		"akinci_akini":
			# gerili yay (yay ve kiriş) içinden geçen tek uzun ok, uçta kama, kuyrukta tüy
			out.append([_arc_pts(c + Vector2(-s * 0.6, 0), s * 0.85, -1.15, 1.15, 12), _taper(12, 0.3, 1.1, 0.3)])
			out.append([PackedVector2Array([c + Vector2(-s * 0.6 + cos(-1.15) * s * 0.85, sin(-1.15) * s * 0.85), c + Vector2(-s * 0.72, 0), c + Vector2(-s * 0.6 + cos(1.15) * s * 0.85, sin(1.15) * s * 0.85)]), PackedFloat32Array([0.25, 0.3, 0.25])])
			out.append([PackedVector2Array([c + Vector2(-s * 0.95, 0), c + Vector2(s * 0.7, 0)]), PackedFloat32Array([0.35, 0.8])])
			out.append([PackedVector2Array([c + Vector2(s * 0.62, 0), c + Vector2(s * 1.0, 0)]), PackedFloat32Array([1.9, 0.1])])
			for sd in [-1.0, 1.0]:
				out.append([PackedVector2Array([c + Vector2(-s * 0.82, 0), c + Vector2(-s * 0.98, sd * s * 0.22)]), PackedFloat32Array([0.6, 0.15])])
		_:
			out.append([PackedVector2Array([c + Vector2(-s * 0.1, 0), c + Vector2(s * 0.1, 0)]), PackedFloat32Array([2.7, 2.7])])
	return out


static func glyph(ci: CanvasItem, id: String, c: Vector2, s: float, cl: Color, wk := 1.0) -> void:
	## Sanatın tamgası (düz fırça; HUD): s yarıçap; wk fırça kalınlık çarpanı
	var W := s * 0.22 * wk
	for g in glyph_strokes(id, c, s):
		stroke(ci, g[0], scale_w(g[1], W), cl)
