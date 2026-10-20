class_name InkFX
extends Node2D
## Mürekkep vuruş efektleri (FX.* bunlara yönlendirir).
## Atlas: assets/fx/ink/ink_fx.png (tools/artgen/inkfx.py), gölgelendirici shaders/ink_fx.gdshader.
## Bir efekt = birkaç öğe (şekil, konum, açı, boy, biçem, gecikme, açılış, ömür); hepsi tek üçgen dizisiyle,
## tek çizim çağrısında çizilir. Zaman ölçekli (hitstop'ta donar: donmuş karede de tam okunur).
##   hit      vuruş sıçrantısı: kesik izi (beyaz-sıcak çekirdekli fırça kesiği, savuruş yönünde), yönlü patlama
##            yıldızı, fırça dokunuşları, damlalar; kademe 2'de arkaya sıçrantı. Türler: cut / blunt / pierce /
##            magic / claw / spark
##   stamp    kritik: siyah mürekkep damgası + kızıl patlama + kesik
##   slam     yere vuruş fırça sıçrantısı (GroundSlamFX ile birlikte)
##   flourish savuşturma / kusursuz kaçış: ensō fırça halkası + kıvılcım yıldızı
##   ring     kuru fırça halkası (FX.ring yerine)

const SHADER: Shader = preload("res://shaders/ink_fx.gdshader")
const ATLAS: Texture2D = preload("res://assets/fx/ink/ink_fx.png")
## v31 silah atlası (tools/artgen/silah_fx_ink.py; aynı kodlama): yönlü fırça sıçrantısı, tek karelik darbe parlaması,
## iğne kesik, küt ezik, kritik hat darbesi + mühür, saplama halkası, ok saplanma / yay bırakışı / ok ucu parıltısı
const ATLAS31 := "res://assets/fx/ink/silah_fx.png"
const ATLAS31_JSON := "res://assets/fx/ink/silah_fx.json"

## Paletler (sRGB): mürekkep, çekirdek, gövde, kenar, sıcak
const PALETTES := [
	["2e0111", "86000c", "d80a10", "f43c16", "ffd6a0"],  # 0 kızıl (varsayılan; v20: bir ton koyu, derin kızıl)
	["1c0903", "7a2504", "f07812", "ffc040", "fff7d0"],  # 1 od
	["06121e", "144a78", "4cb8ea", "b4f0ff", "ffffff"],  # 2 ayaz
	["071408", "1a4a10", "55b828", "b8f04c", "f6ffd8"],  # 3 zehir
	["031416", "0a5052", "22c0aa", "8cf5dc", "f2fffb"],  # 4 ruh
	["060a1c", "1a2a78", "3f7cff", "a6d2ff", "ffffff"],  # 5 yıldırım
	["0c0414", "3a0c5c", "8c34d6", "e08cff", "fdeeff"],  # 6 erlik / bozgun
	["0a0c18", "2a3460", "8ea4dc", "dfe8ff", "ffffff"],  # 7 ay
	["08140f", "1f5240", "6cc8a4", "d4ffe8", "ffffff"],  # 8 yel / kayın
	["160c02", "6a3a06", "e0a020", "ffe080", "fffbe8"],  # 9 altın
	["0a0620", "2e2276", "7064f0", "c4b8ff", "f6f2ff"],  # 10 kam (v20 unsur: tayfsı mavi-mor)
	["07120a", "143c1a", "2f7d34", "d9c25c", "fff1b8"],  # 11 Yer-Su (v20 unsur: orman yeşili; v25: koyu zümrüt gövde, altın kenar)
]
const ID_PAL := {"od_kamcisi": 1, "kor_cekici": 1, "ayaz_kilici": 2, "yilan_kilici": 3, "ruh_kilici": 4,
	"yildirim_kilici": 5, "erlik_tirpani": 6, "bozgun_kilici": 6, "ay_palasi": 7, "ruzgar_kilici": 8, "kayin_asasi": 8}
const MAT_PAL := {"od_tasi": 1, "ayaz": 2, "ruh": 4, "gok_demiri": 5}

static var player_pal := 0
static var _pal_cache: Dictionary = {}
static var _mats: Dictionary = {}
static var _shapes: Dictionary = {}
static var _atlas_size := Vector2(1024, 1024)
static var _shapes31: Dictionary = {}
static var _yuk_t := -9.0   # v31 kalabalık: vuruş sıçrantısı penceresinin başı (gerçek zaman)
static var _yuk_n := 0      # v31: pencerede istenen vuruş sıçrantısı sayısı
static var butce := true    # v31: kalabalık bütçesi (vitrin / test ızgarası kapatır)


static func palette(i: int) -> Array:
	## Doğrusal renkler (Vector3) — HDR 2D tuvali doğrusal çalışır
	i = clampi(i, 0, PALETTES.size() - 1)
	if not _pal_cache.has(i):
		var out: Array = []
		for h in PALETTES[i]:
			var c := Color.html(h).srgb_to_linear()
			out.append(Vector3(c.r, c.g, c.b))
		_pal_cache[i] = out
	return _pal_cache[i]


static func weapon_pal(it: Dictionary) -> int:
	var id := String(it.get("id", ""))
	if Unsur.of(it) != "":
		return Unsur.pal(Unsur.of(it))   # v20: unsurlu silah kendi unsurunun mürekkebinde
	if ID_PAL.has(id):
		return ID_PAL[id]
	return MAT_PAL.get(String(it.get("material", "")), 0)


static func pal_from_color(c: Color) -> int:
	## Eski çağrıların silah/efekt renginden palet: doygun olmayan (beyaz, metal) renkler kızıl mürekkep.
	if c.s < 0.295:
		# v31: soluk gök mavisi (şimşek, buz ışığı) kızıl mürekkebe düşmesin
		return 5 if (c.b > c.r + 0.18 and c.v > 0.6) else 0
	var h := c.h
	if h < 0.04 or h > 0.94:
		return 0
	if h < 0.115:
		return 1
	if h < 0.2:
		return 9
	if h < 0.42:
		return 3
	if h < 0.5:
		return 4
	if h < 0.58:
		return 2
	if h < 0.7:
		return 5
	return 6


static func _mat(p: int, a31 := false) -> ShaderMaterial:
	var key: int = p + (1000 if a31 else 0)
	if not _mats.has(key):
		var m := ShaderMaterial.new()
		m.shader = SHADER
		m.set_shader_parameter("atlas", Data.tex_full(ATLAS31 if a31 else ATLAS.resource_path))   # HD paketi varsa 2 kat (UV ile örneklenir)
		var pc: Array = palette(p)
		m.set_shader_parameter("c_ink", pc[0])
		m.set_shader_parameter("c_core", pc[1])
		m.set_shader_parameter("c_body", pc[2])
		m.set_shader_parameter("c_rim", pc[3])
		m.set_shader_parameter("c_hot", pc[4])
		_mats[key] = m
	return _mats[key]


static func _shape(n: String) -> Rect2:
	if _shapes.is_empty():
		var j: Dictionary = Data.load_json("res://assets/fx/ink/ink_fx.json")
		_atlas_size = Vector2(float(j["size"][0]), float(j["size"][1]))
		for k in j["shapes"]:
			var r: Array = j["shapes"][k]
			_shapes[k] = Rect2(float(r[0]), float(r[1]), float(r[2]), float(r[3]))
	return _shapes.get(n, Rect2(0, 0, 256, 256))


static func _shape31(n: String) -> Rect2:
	if _shapes31.is_empty():
		var j: Dictionary = Data.load_json(ATLAS31_JSON)
		for k in j.get("shapes", {}):
			var r: Array = j["shapes"][k]
			_shapes31[k] = Rect2(float(r[0]), float(r[1]), float(r[2]), float(r[3]))
	return _shapes31.get(n, Rect2(0, 0, 256, 256))


# ------------------------------------------------------------------ düğüm
enum { V_SPLASH, V_STAMP, V_CUT, V_DRY }
const R0 := 0.62   # ilk karedeki açılış payı

var _els: Array = []       # sözlükler
var _t := 0.0
var auto_pal := false      # paleti ilk karelerde oyuncunun (aynı karede başlayan) izinden al
var _auto_n := 0
var follow: Node2D
var _follow_off := Vector2.ZERO
var a31 := false           # v31: silah atlası (silah_fx.png)


static func spawn(p: int, pos: Vector2, z := 58, atlas31 := false) -> InkFX:
	if FX.root == null:
		return null
	var n := InkFX.new()
	n.a31 = atlas31
	n.material = _mat(p, atlas31)
	n.position = pos
	n.z_index = z
	FX.root.add_child(n)
	return n


func el(shape: String, off: Vector2, rot: float, size: Vector2, variant := V_SPLASH, delay := 0.0, t_rev := 0.05, hold := 0.06, life := 0.32, anchor := Vector2(0.5, 0.5)) -> void:
	_els.append({"s": shape, "o": off, "r": rot, "z": size, "v": variant, "d": delay, "tr": maxf(t_rev, 0.001), "h": hold, "l": life, "a": anchor})


func _process(delta: float) -> void:
	if Prof.on:
		var t0 := Time.get_ticks_usec()
		_process_ic(delta)
		Prof.ekle(&"fx", t0)
		return
	_process_ic(delta)


func _process_ic(delta: float) -> void:
	if auto_pal:
		# vuruş, izin oluştuğu karede izden ÖNCE işlenir: palet ilk birkaç karede yakındaki taze izden okunur
		_auto_n += 1
		var t := InkTrail.active
		if t != null and is_instance_valid(t) and t._s.size() > 0 and (t._s[t._s.size() - 1][1] as Vector2).distance_to(global_position) < 90.0:
			material = _mat(t.pal, a31)
			auto_pal = false
		elif _auto_n > 12:
			auto_pal = false
	_t += delta
	if follow and is_instance_valid(follow):
		global_position = follow.global_position + _follow_off
	var alive := false
	for e in _els:
		if _t - float(e["d"]) < float(e["l"]):
			alive = true
			break
	if not alive:
		queue_free()
		return
	queue_redraw()


func _draw() -> void:
	var pts := PackedVector2Array()
	var uvs := PackedVector2Array()
	var cols := PackedColorArray()
	var idx := PackedInt32Array()
	for e in _els:
		var t := _t - float(e["d"])
		var L := float(e["l"])
		if t < 0.0 or t >= L:
			continue
		var tr := float(e["tr"])
		# açılış: ilk karede şeklin çekirdeği zaten görünür (hitstop'ta zaman durur; donmuş karede boş kalmasın)
		var rv := clampf(t / tr, 0.0, 1.0)
		rv = lerpf(R0, 1.0, 1.0 - (1.0 - rv) * (1.0 - rv))
		var t1 := tr + float(e["h"])
		var ds := clampf((t - t1) / maxf(L - t1, 0.001), 0.0, 1.0)
		ds = ds * (0.6 + 0.4 * ds)
		var sz: Vector2 = e["z"] * (0.82 + 0.18 * rv + 0.05 * ds)
		var r := _shape31(String(e["s"])) if a31 else _shape(String(e["s"]))
		var an: Vector2 = e["a"]
		var rot := float(e["r"])
		var off: Vector2 = e["o"]
		var q := float(roundi(rv * 63.0)) * 2.0
		var vx := float(int(e["v"])) * 2.0
		var corners := [Vector2(0, 0), Vector2(1, 0), Vector2(0, 1), Vector2(1, 1)]
		var st := pts.size()
		for c in corners:
			var lp := Vector2((c.x - an.x) * sz.x, (c.y - an.y) * sz.y).rotated(rot) + off
			pts.append(lp)
			var uv := (r.position + Vector2(c.x * r.size.x, c.y * r.size.y)) / _atlas_size
			uvs.append(Vector2(uv.x + vx, uv.y + q))
			cols.append(Color(1, 1, 1, ds))
		idx.append_array([st, st + 1, st + 2, st + 1, st + 3, st + 2])
	if idx.is_empty():
		return
	RenderingServer.canvas_item_add_triangle_array(get_canvas_item(), idx, pts, cols, uvs)


# ------------------------------------------------------------------ efektler
static func _swing_dir(pos: Vector2, fallback: Vector2) -> Vector2:
	## Oyuncunun taze izinin uç yönü (kesik izi savuruşla aynı yönde); yoksa vuruş yönüne çapraz.
	var t := InkTrail.active
	if t and is_instance_valid(t):
		var d := t.tip_dir()
		if d != Vector2.ZERO and t._s.size() > 0 and (t._s[t._s.size() - 1][1] as Vector2).distance_to(pos) < 70.0:
			return d
	var f := fallback.normalized() if fallback.length() > 0.01 else Vector2.RIGHT
	return f.rotated(-0.9 * signf(f.x if absf(f.x) > 0.01 else 1.0))


static func _near_player_swing(pos: Vector2) -> bool:
	var t := InkTrail.active
	return t != null and is_instance_valid(t) and t.tip_dir() != Vector2.ZERO and t._s.size() > 0 and (t._s[t._s.size() - 1][1] as Vector2).distance_to(pos) < 70.0


static func hit(kind: String, pos: Vector2, dir: Vector2, p: int, tier := 1, size := 1.0) -> InkFX:
	## Vuruş sıçrantısı. tier 0 hafif, 1 orta, 2 büyük. v31 (silah atlası): her vuruş üç parça —
	##   1) TEK KARELİK darbe parlaması (ak-sıcak iğne yıldızı, uzun ekseni savuruş yönünde; ~1 kare + hitstop),
	##   2) türün imzası: kesikte iğne uçlu ince kesik, küt'te ezik sumi lekesi, saplamada yarık kesik + saplama halkası,
	##      hançerde ikiz fiske, büyüde ince halka,
	##   3) vuruş yönünde fırlayan yönlü fırça sıçrantısı (kökte sumi, öne fırça dili + damlalar); kademe 2'de ek damla
	##      konisi. Boylar v22 okunurluğuna göre ölçülü (düşmanın gövdesini örtmez).
	var near := _near_player_swing(pos)
	if near:
		p = InkTrail.active.pal
		if kind in ["cut", "spark"] and InkTrail.active.style == "hancer":
			kind = "claw"
	var n := spawn(p, pos, 58, true)
	if n == null:
		return null
	n.auto_pal = not near
	var hd := dir.normalized() if dir.length() > 0.01 else Vector2.RIGHT
	# v22: hızlı ardışık vuruşta (FX.hit_k < 1) en hafif kademe ve daha küçük
	if FX.in_hit and FX.hit_k < 0.99:
		tier = 0
		size *= lerpf(0.55, 1.0, FX.hit_k)
	# v31 kalabalık sahne: 0,1 sn içinde ilk 2 sıçrantı tam; 3-5. en hafif kademe ve küçük; sonrakiler yalnız küçük
	# parlama (çok düşmanlı sanat / bitiriş / alan hasarında ekran mürekkep yığınına dönmesin)
	var c := _kalabalik()
	if c > 5:
		var fl := minf(17.0 * size, 20.0)
		n.el("flash", Vector2.ZERO, hd.angle(), Vector2(fl * 1.4, fl * 0.6), V_CUT, 0.0, 0.001, 0.02, 0.05)
		return n
	if c > 2:
		tier = 0
		size *= 0.75
	var base := 17.0 * size * (1.0 + 0.2 * float(tier))
	var sd := _swing_dir(pos, hd)
	var flip := 1.0 if randf() < 0.5 else -1.0
	var sp := "splash_a" if randf() < 0.5 else "splash_b"
	# 1) darbe parlaması: tek kare tam, ikinci karede biter (zaman ölçekli: vuruş duraklamasında donmuş karede okunur)
	var fa := sd.angle() if kind in ["cut", "spark", "claw"] else hd.angle()
	var fk := minf(base, 24.0)   # parlama boyu sınırlı (ağır kritikte ekranı kaplamasın)
	n.el("flash", Vector2.ZERO, fa, Vector2(fk * 2.0, fk * (0.95 if kind != "pierce" else 0.7)), V_CUT, 0.0, 0.001, 0.03, 0.06)
	match kind:
		"blunt":
			n.el("blunt", -hd * base * 0.15, hd.angle(), Vector2(base * 1.45, base * 1.45 * flip), V_SPLASH, 0.0, 0.05, 0.05, 0.3)
			n.el("ring_thin", Vector2.ZERO, randf() * TAU, Vector2.ONE * base * 1.5, V_DRY, 0.015, 0.06, 0.0, 0.2)
		"pierce":
			n.el("cut_split", -hd * base * 0.4, hd.angle(), Vector2(base * 3.0, base * 0.42 * flip), V_CUT, 0.0, 0.03, 0.05, 0.22)
			n.el(sp, Vector2.ZERO, hd.angle(), Vector2(base * 1.45, base * 1.2 * flip), V_SPLASH, 0.01, 0.05, 0.05, 0.3)
			if tier >= 1:
				# saplama halkası: vuruş eksenine dik, yandan görülen elips (mızrak ucunun çevresinde açılan basınç halkası)
				n.el("ring_thin", hd * base * 0.15, hd.angle(), Vector2(base * 0.55, base * 1.7), V_DRY, 0.0, 0.05, 0.02, 0.2)
		"magic":
			n.el("ring_thin", Vector2.ZERO, randf() * TAU, Vector2.ONE * base * 1.8, V_SPLASH, 0.0, 0.08, 0.0, 0.26)
			n.el("burst_ink", Vector2.ZERO, randf() * TAU, Vector2.ONE * base * 1.1, V_SPLASH, 0.0, 0.04, 0.05, 0.28)
		"claw":
			n.el("twin_cut", Vector2.ZERO, sd.angle(), Vector2(base * 1.7, base * 1.5 * flip), V_CUT, 0.0, 0.025, 0.05, 0.2)
			n.el(sp, Vector2.ZERO, hd.angle(), Vector2(base * 1.1, base * 0.9 * flip), V_SPLASH, 0.01, 0.04, 0.04, 0.24)
		_:
			# cut / spark: savuruş yönünde iğne kesik + vuruş yönünde fırça sıçrantısı
			var cl := base * (1.9 if tier == 0 else 2.3)
			n.el("cut_thin" if tier == 0 else "cut_split", Vector2.ZERO, sd.angle(), Vector2(cl, cl * 0.13 * flip), V_CUT, 0.0, 0.025, 0.05 + 0.02 * tier, 0.2 + 0.04 * tier)
			n.el(sp, -hd * base * 0.1, hd.angle() + randf_range(-0.15, 0.15), Vector2(base * (1.25 if tier == 0 else 1.55), base * (1.0 if tier == 0 else 1.25) * flip), V_SPLASH, 0.0, 0.045, 0.05, 0.27 + 0.04 * tier)
	if tier >= 2:
		n.el("drops_dir", hd * base * 0.2, hd.angle() + randf_range(-0.2, 0.2), Vector2(base * 1.8, base * 1.4 * flip), V_STAMP, 0.015, 0.07, 0.07, 0.38)
	return n


static func _kalabalik() -> int:
	## v31: son 0,1 sn'de (gerçek zaman) istenen vuruş / kritik mürekkebi sayısı (bu istek dahil)
	if not butce:
		return 1
	var now := Time.get_ticks_msec() / 1000.0
	if now - _yuk_t > 0.1:
		_yuk_t = now
		_yuk_n = 0
	_yuk_n += 1
	return _yuk_n


static func stamp(pos: Vector2, p: int = -1) -> InkFX:
	## Kritik (v31): tek karelik büyük parlama + savuruş yönünde kalın sumi hat darbesi (basılmış baş, kuru kuyruk) +
	## köşede küçük kızıl mühür (oyulmuş tamga). Hepsi ölçülü boyda; mühür biraz daha uzun kalır.
	var near := _near_player_swing(pos)
	if p < 0:
		p = InkTrail.active.pal if near else player_pal
	var n := spawn(p, pos, 59, true)
	if n == null:
		return null
	n.auto_pal = not near
	var sd := _swing_dir(pos, Vector2.RIGHT)
	var a := sd.angle()
	n.el("flash", Vector2.ZERO, a, Vector2(54.0, 26.0), V_CUT, 0.0, 0.001, 0.035, 0.07)
	n.el("cut_split", Vector2.ZERO, a, Vector2(62.0, 8.0), V_CUT, 0.0, 0.02, 0.07, 0.22)
	if _kalabalik() > 2:
		return n   # v31 kalabalık: aynı anda çok kritikte yalnız parlama + kesik (sıçrantı ve mühür yok)
	n.el("splash_b", -sd * 3.0, a + 0.25, Vector2(34.0, 28.0), V_SPLASH, 0.01, 0.04, 0.06, 0.32)
	# mühür: vermilyon (palet 0) ayrı düğümde, darbenin üstünde-yanında; hafif eğik, sonradan basılır
	var s := spawn(0, pos + sd.orthogonal() * -14.0 + Vector2(0, -10), 60, true)
	if s:
		s.el("seal", Vector2.ZERO, randf_range(-0.25, 0.25), Vector2.ONE * 15.0, V_SPLASH, 0.05, 0.03, 0.22, 0.42)
	return n


static func slam(pos: Vector2, facing := 1, power := 1.0, p := 0) -> InkFX:
	## Yere vuruş: zemin boyunca fırça sıçrantısı (taban pos'ta), yukarı damlalar, yatık kuru halka.
	var n := spawn(p, pos, 47)
	if n == null:
		return null
	var k := clampf(power, 0.5, 2.2)
	var fl := 1.0 if facing >= 0 else -1.0
	n.el("ground", Vector2.ZERO, 0.0, Vector2(92.0 * fl, 50.0) * k, V_SPLASH, 0.0, 0.06, 0.08, 0.46, Vector2(0.5, 0.82))
	n.el("ring", Vector2(0, -2), 0.0, Vector2(96.0, 20.0) * k, V_DRY, 0.0, 0.1, 0.0, 0.26)
	n.el("dab_a", Vector2(-30.0 * k, -2), PI + 0.15, Vector2(26, 26) * k, V_SPLASH, 0.03, 0.05, 0.06, 0.36)
	n.el("dab_b", Vector2(30.0 * k, -2), -0.15, Vector2(24, 24) * k, V_SPLASH, 0.03, 0.05, 0.06, 0.36)
	return n


static func flourish(pos: Vector2, kind := "parry", p := 9) -> InkFX:
	## Savuşturma: hızlı çizilen siyah ensō + sıcak kıvılcım yıldızı. Kusursuz kaçış: büyük soluk ensō + halka.
	var n := spawn(p, pos, 59)
	if n == null:
		return null
	var rng := randf() * TAU
	if kind == "parry":
		n.el("enso", Vector2.ZERO, rng, Vector2.ONE * 50.0, V_STAMP, 0.0, 0.1, 0.18, 0.55)
		n.el("shard", Vector2.ZERO, randf_range(-0.2, 0.2), Vector2.ONE * 46.0, V_CUT, 0.0, 0.03, 0.05, 0.24)
		n.el("burst_b", Vector2.ZERO, rng, Vector2.ONE * 30.0, V_SPLASH, 0.0, 0.04, 0.04, 0.26)
	else:
		n.el("enso", Vector2.ZERO, rng, Vector2.ONE * 74.0, V_SPLASH, 0.0, 0.14, 0.2, 0.7)
		n.el("ring", Vector2.ZERO, rng, Vector2.ONE * 90.0, V_DRY, 0.05, 0.12, 0.05, 0.45)
	return n


static func ring(pos: Vector2, radius: float, p: int, life := 0.3, aspect := 1.0) -> InkFX:
	var n := spawn(p, pos, 57)
	if n == null:
		return null
	var d := minf(radius, 48.0) * 1.6
	n.el("ring", Vector2.ZERO, randf() * TAU if aspect >= 0.99 else 0.0, Vector2(d, d * aspect), V_DRY, 0.0, life * 0.4, 0.0, life)
	return n


static func kill(pos: Vector2, big := false) -> InkFX:
	## Öldürücü vuruş (v31 silah atlası): ezik sumi lekesi + vuruş yönsüz damla konisi (iki yana) + tek karelik parlama.
	var n := spawn(player_pal, pos, 58, true)
	if n == null:
		return null
	var s := 1.4 if big else 1.0
	var a := randf() * TAU
	n.el("flash", Vector2.ZERO, a, Vector2(46.0, 24.0) * s, V_CUT, 0.0, 0.001, 0.03, 0.06)
	n.el("blunt", Vector2.ZERO, a, Vector2.ONE * 40.0 * s, V_STAMP, 0.0, 0.05, 0.1, 0.42)
	n.el("drops_dir", Vector2.ZERO, a + PI * 0.5, Vector2(44.0, 34.0) * s, V_STAMP, 0.02, 0.08, 0.1, 0.5)
	n.el("drops_dir", Vector2.ZERO, a - PI * 0.5, Vector2(40.0, -30.0) * s, V_SPLASH, 0.03, 0.08, 0.1, 0.46)
	return n
