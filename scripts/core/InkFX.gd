class_name InkFX
extends Node2D
## Stil v2 mürekkep vuruş efektleri (yalnızca --stil=v2; FX.* bunlara yönlendirir, v1 değişmez).
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

## Paletler (sRGB): mürekkep, çekirdek, gövde, kenar, sıcak
const PALETTES := [
	["3a0214", "a00008", "fa0c06", "ff4a12", "ffdca0"],  # 0 kızıl (varsayılan; referanstan ölçüldü)
	["1c0903", "7a2504", "f07812", "ffc040", "fff7d0"],  # 1 od
	["06121e", "144a78", "4cb8ea", "b4f0ff", "ffffff"],  # 2 ayaz
	["071408", "1a4a10", "55b828", "b8f04c", "f6ffd8"],  # 3 zehir
	["031416", "0a5052", "22c0aa", "8cf5dc", "f2fffb"],  # 4 ruh
	["060a1c", "1a2a78", "3f7cff", "a6d2ff", "ffffff"],  # 5 yıldırım
	["0c0414", "3a0c5c", "8c34d6", "e08cff", "fdeeff"],  # 6 erlik / bozgun
	["0a0c18", "2a3460", "8ea4dc", "dfe8ff", "ffffff"],  # 7 ay
	["08140f", "1f5240", "6cc8a4", "d4ffe8", "ffffff"],  # 8 yel / kayın
	["160c02", "6a3a06", "e0a020", "ffe080", "fffbe8"],  # 9 altın
]
const ID_PAL := {"od_kamcisi": 1, "kor_cekici": 1, "ayaz_kilici": 2, "yilan_kilici": 3, "ruh_kilici": 4,
	"yildirim_kilici": 5, "erlik_tirpani": 6, "bozgun_kilici": 6, "ay_palasi": 7, "ruzgar_kilici": 8, "kayin_asasi": 8}
const MAT_PAL := {"od_tasi": 1, "ayaz": 2, "ruh": 4, "gok_demiri": 5}

static var player_pal := 0
static var _pal_cache: Dictionary = {}
static var _mats: Dictionary = {}
static var _shapes: Dictionary = {}
static var _atlas_size := Vector2(1024, 1024)


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
	if ID_PAL.has(id):
		return ID_PAL[id]
	return MAT_PAL.get(String(it.get("material", "")), 0)


static func pal_from_color(c: Color) -> int:
	## Eski çağrıların silah/efekt renginden palet: doygun olmayan (beyaz, metal) renkler kızıl mürekkep.
	if c.s < 0.295:
		return 0
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


static func _mat(p: int) -> ShaderMaterial:
	if not _mats.has(p):
		var m := ShaderMaterial.new()
		m.shader = SHADER
		m.set_shader_parameter("atlas", ATLAS)
		var pc: Array = palette(p)
		m.set_shader_parameter("c_ink", pc[0])
		m.set_shader_parameter("c_core", pc[1])
		m.set_shader_parameter("c_body", pc[2])
		m.set_shader_parameter("c_rim", pc[3])
		m.set_shader_parameter("c_hot", pc[4])
		_mats[p] = m
	return _mats[p]


static func _shape(n: String) -> Rect2:
	if _shapes.is_empty():
		var j: Dictionary = Data.load_json("res://assets/fx/ink/ink_fx.json")
		_atlas_size = Vector2(float(j["size"][0]), float(j["size"][1]))
		for k in j["shapes"]:
			var r: Array = j["shapes"][k]
			_shapes[k] = Rect2(float(r[0]), float(r[1]), float(r[2]), float(r[3]))
	return _shapes.get(n, Rect2(0, 0, 256, 256))


# ------------------------------------------------------------------ düğüm
enum { V_SPLASH, V_STAMP, V_CUT, V_DRY }
const R0 := 0.62   # ilk karedeki açılış payı

var _els: Array = []       # sözlükler
var _t := 0.0
var auto_pal := false      # paleti ilk karede oyuncunun (aynı karede başlayan) izinden al
var follow: Node2D
var _follow_off := Vector2.ZERO


static func spawn(p: int, pos: Vector2, z := 58) -> InkFX:
	if FX.root == null:
		return null
	var n := InkFX.new()
	n.material = _mat(p)
	n.position = pos
	n.z_index = z
	FX.root.add_child(n)
	return n


func el(shape: String, off: Vector2, rot: float, size: Vector2, variant := V_SPLASH, delay := 0.0, t_rev := 0.05, hold := 0.06, life := 0.32, anchor := Vector2(0.5, 0.5)) -> void:
	_els.append({"s": shape, "o": off, "r": rot, "z": size, "v": variant, "d": delay, "tr": maxf(t_rev, 0.001), "h": hold, "l": life, "a": anchor})


func _process(delta: float) -> void:
	if auto_pal:
		# vuruş, izin oluştuğu karede izden ÖNCE işlenir: palet bir kare sonra izden okunur
		auto_pal = false
		if _near_player_swing(global_position):
			material = _mat(InkTrail.active.pal)
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
		var r := _shape(String(e["s"]))
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
	## Vuruş sıçrantısı. tier 0 hafif (küçük yıldız + ince kesik), 1 orta, 2 büyük (+ arkaya sıçrantı, damlalar).
	var near := _near_player_swing(pos)
	if near:
		p = InkTrail.active.pal
		if kind in ["cut", "spark"] and InkTrail.active.style == "hancer":
			kind = "claw"
	var n := spawn(p, pos)
	if n == null:
		return null
	n.auto_pal = not near
	var hd := dir.normalized() if dir.length() > 0.01 else Vector2.RIGHT
	var base := 22.0 * size * (1.0 + 0.28 * float(tier))
	var rng := randf() * TAU
	match kind:
		"blunt":
			n.el("burst_a", Vector2.ZERO, rng, Vector2.ONE * base * 1.35, V_SPLASH, 0.0, 0.05, 0.05, 0.34)
			n.el("ring", Vector2.ZERO, rng, Vector2(base * 1.9, base * 1.9), V_DRY, 0.01, 0.07, 0.0, 0.24)
			if tier >= 1:
				n.el("drops", hd * base * 0.3, hd.angle(), Vector2.ONE * base * 1.3, V_STAMP, 0.02, 0.08, 0.06, 0.4)
		"pierce":
			n.el("cut_b", hd * base * 0.2, hd.angle(), Vector2(base * 2.6, base * 0.65), V_CUT, 0.0, 0.035, 0.06, 0.24)
			n.el("burst_dir", hd * base * 0.15, hd.angle(), Vector2.ONE * base * 1.1, V_SPLASH, 0.01, 0.05, 0.05, 0.32)
		"magic":
			n.el("burst_b", Vector2.ZERO, rng, Vector2.ONE * base * 1.3, V_SPLASH, 0.0, 0.05, 0.05, 0.32)
			n.el("ring", Vector2.ZERO, rng, Vector2.ONE * base * 1.7, V_SPLASH, 0.0, 0.08, 0.0, 0.26)
			n.el("shard", Vector2.ZERO, rng * 0.2, Vector2.ONE * base * 1.0, V_CUT, 0.0, 0.03, 0.03, 0.16)
		"claw":
			var sd := _swing_dir(pos, hd)
			n.el("burst_b", Vector2.ZERO, rng, Vector2.ONE * base * 0.9, V_SPLASH, 0.0, 0.04, 0.04, 0.26)
			n.el("claw", Vector2.ZERO, sd.angle() + PI * 0.25, Vector2.ONE * base * 1.5, V_CUT, 0.0, 0.03, 0.06, 0.22)
		_:
			# cut / spark: savuruş yönünde kesik izi + yönlü yıldız
			var sd := _swing_dir(pos, hd)
			var cl := base * (2.1 if tier == 0 else 2.6)
			n.el("burst_dir", hd * base * 0.15, hd.angle(), Vector2.ONE * base * (0.95 if tier == 0 else 1.2), V_SPLASH, 0.0, 0.045, 0.05, 0.28 + 0.04 * tier)
			n.el("cut_a" if tier > 0 else "cut_b", Vector2.ZERO, sd.angle(), Vector2(cl, cl * 0.25), V_CUT, 0.0, 0.03, 0.06 + 0.02 * tier, 0.22 + 0.05 * tier)
	if tier >= 1 and kind != "blunt":
		var a := hd.angle()
		n.el("dab_a", hd.rotated(0.9) * base * 0.35, a + 0.9 + randf_range(-0.3, 0.3), Vector2.ONE * base * 0.75, V_SPLASH, 0.02, 0.05, 0.05, 0.3)
		n.el("dab_b", hd.rotated(-0.9) * base * 0.35, a - 0.9 + randf_range(-0.3, 0.3), Vector2.ONE * base * 0.65, V_SPLASH, 0.03, 0.05, 0.05, 0.3)
	if tier >= 2:
		n.el("spray", hd * base * 0.55, hd.angle(), Vector2.ONE * base * 1.7, V_SPLASH, 0.01, 0.07, 0.08, 0.4)
	return n


static func stamp(pos: Vector2, p: int = -1) -> InkFX:
	## Kritik: kızıl patlama + siyah mürekkep damgası + beyaz-sıcak kesik (darbe karesinde de okunur).
	var near := _near_player_swing(pos)
	if p < 0:
		p = InkTrail.active.pal if near else player_pal
	var n := spawn(p, pos, 59)
	if n == null:
		return null
	n.auto_pal = not near
	var rng := randf() * TAU
	var sd := _swing_dir(pos, Vector2.RIGHT)
	n.el("burst_b", Vector2.ZERO, rng, Vector2.ONE * 44.0, V_SPLASH, 0.0, 0.05, 0.08, 0.36)
	n.el("stamp", Vector2.ZERO, rng + 1.3, Vector2.ONE * 30.0, V_STAMP, 0.0, 0.035, 0.14, 0.42)
	n.el("cut_a", Vector2.ZERO, sd.angle(), Vector2(66.0, 16.5), V_CUT, 0.0, 0.03, 0.1, 0.3)
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
	## Öldürücü vuruş: siyah mürekkep patlaması + damlalar (kill_flash yerine).
	var n := spawn(player_pal, pos, 58)
	if n == null:
		return null
	var s := 1.4 if big else 1.0
	n.el("burst_a", Vector2.ZERO, randf() * TAU, Vector2.ONE * 46.0 * s, V_STAMP, 0.0, 0.05, 0.1, 0.45)
	n.el("drops", Vector2.ZERO, randf() * TAU, Vector2.ONE * 64.0 * s, V_STAMP, 0.02, 0.1, 0.1, 0.55)
	return n
