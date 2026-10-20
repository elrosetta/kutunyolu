class_name TomarV2
extends RefCounted
## v34 Kut Tomarı görselleri (tools/artgen/tomar_ink.py): kayın kabuğu tomar, bozkurt başlı topuzlar, kızıl mum mühür,
## üç stat tamgası (Bozkurt kızılı / Kartal mavisi / Ayı yeşili). Atlas assets/fx/ink/tomar_v2.png (+ _e ışıma) +
## tomar_v2.json {rect, pivot, texel}; HD paketi assets_hd/x2/fx/ink/tomar_v2.webp (Data.tex). Kullananlar:
##   Pickup "tilsim" (yerdeki tomar + kaide, süzülme, ışıma nabzı, mürekkep zerreleri), TomarV2.acilis (okununca açılan
##   tomar ve seçilen statın tamgası), HUD tomar seçim kartları (ui_kart_*), Bezirgân satırı ve sol üst sayaç (ui_tomar).

const JSON_PATH := "res://assets/fx/ink/tomar_v2.json"
const PNG_PATH := "res://assets/fx/ink/tomar_v2.png"
const GLOW_PATH := "res://assets/fx/ink/tomar_v2_e.png"
const ACILIS_KARE := 6

static var _meta: Dictionary = {}
static var _tex: Texture2D
static var _glow: Texture2D


static func on() -> bool:
	return ResourceLoader.exists(PNG_PATH)


static func meta() -> Dictionary:
	if _meta.is_empty():
		_meta = Data.load_json(JSON_PATH) if FileAccess.file_exists(JSON_PATH) else {"sprites": {}}
		if on():
			_tex = Data.tex(PNG_PATH)   # HD paketi varsa 2 kat ayrıntı (temel boyutta raporlanır)
			_glow = load(GLOW_PATH) if ResourceLoader.exists(GLOW_PATH) else null
	return _meta


static func has(n: String) -> bool:
	return (meta().get("sprites", {}) as Dictionary).has(n)


static func region(n: String) -> Rect2:
	var m: Dictionary = meta()["sprites"].get(n, {})
	if m.is_empty():
		return Rect2()
	var r: Array = m["rect"]
	return Rect2(r[0], r[1], r[2], r[3])


static func sprite(n: String, lit := true, glow := Color(1.3, 1.25, 1.15)) -> Sprite2D:
	## Atlas parçası: köken pivot (dünya birimi 1/texel ölçekli). Işıma varsa toplamalı çocuk "glow".
	var m: Dictionary = meta()["sprites"].get(n, {})
	if m.is_empty() or _tex == null:
		return null
	var k := 1.0 / float(m.get("texel", meta().get("texel", 4.0)))
	var s := Sprite2D.new()
	s.texture = _tex
	s.region_enabled = true
	s.region_rect = region(n)
	s.centered = false
	s.offset = -Vector2(float(m["pivot"][0]), float(m["pivot"][1]))
	s.scale = Vector2(k, k)
	s.texture_filter = CanvasItem.TEXTURE_FILTER_LINEAR_WITH_MIPMAPS
	s.material = SusV2.lit_mat() if lit else SusV2.flat_mat()
	if bool(m.get("glow", false)) and _glow != null:
		var g := Sprite2D.new()
		g.name = "glow"
		g.texture = _glow
		g.region_enabled = true
		g.region_rect = s.region_rect
		g.centered = false
		g.offset = s.offset
		g.texture_filter = CanvasItem.TEXTURE_FILTER_LINEAR_WITH_MIPMAPS
		g.material = SusV2.add_mat()
		g.self_modulate = glow
		s.add_child(g)
	return s


static func set_region(s: Sprite2D, n: String) -> void:
	var m: Dictionary = meta()["sprites"].get(n, {})
	if m.is_empty() or s == null:
		return
	s.region_rect = region(n)
	s.offset = -Vector2(float(m["pivot"][0]), float(m["pivot"][1]))
	var g := s.get_node_or_null("glow") as Sprite2D
	if g:
		g.region_rect = s.region_rect
		g.offset = s.offset


static func ui(ci: CanvasItem, n: String, c: Vector2, w: float, col := Color(1, 1, 1), shadow := true) -> Rect2:
	## Arayüzde çiz (ışıma dokuya işlenmiş ui_* parçaları): c merkezli, w genişliğinde, en-boy korunur. Çizilen dikdörtgen.
	var rg := region(n)
	if rg.size == Vector2.ZERO or _tex == null:
		return Rect2()
	var sz := Vector2(w, w * rg.size.y / rg.size.x)
	var r := Rect2(c - sz * 0.5, sz)
	if shadow:
		ci.draw_texture_rect_region(_tex, Rect2(r.position + Vector2(1.0, 1.5) * maxf(1.0, w / 40.0), r.size), rg, Color(0, 0, 0, 0.45 * col.a))
	ci.draw_texture_rect_region(_tex, r, rg, col)
	return r


static func stat_col(stat: String) -> Color:
	return Color.from_string(String(Data.items["ongun"].get(stat, {}).get("color", "#ffd070")), Color(1.0, 0.82, 0.4))


# ------------------------------------------------------------------ okununca: tomar açılır, tamga parlar ve oyuncuya uçar
static func acilis(parent: Node, pos: Vector2, stat: String, target: Node2D = null) -> Node2D:
	if not on() or not has("tomar_ac_0") or parent == null:
		return null
	var a := Acilis.new()
	a.stat = stat
	a.target = target
	a.position = pos
	a.scale = Vector2.ONE * 1.3   # yerdeki tomarla (Pickup.TOMAR_OLCEK) aynı irilikte açılır
	a.z_index = 40
	parent.add_child(a)
	return a


class Acilis extends Node2D:
	## Asma tomar açılışı (~1,4 sn): mühür kırılır (mum kıymıkları), 6 kare açılır, halkada seçilen statın tamgası
	## belirir ve parlar, sonra ışık topu gibi oyuncuya uçar; tomar solar.
	var stat := "kurt"
	var target: Node2D = null
	var t := 0.0
	var spr: Sprite2D
	var tam: Sprite2D
	var col := Color(1, 0.8, 0.4)
	var _burst := false
	var _fly0 := Vector2.ZERO

	func _ready() -> void:
		process_mode = Node.PROCESS_MODE_PAUSABLE
		col = TomarV2.stat_col(stat)
		spr = TomarV2.sprite("tomar_ac_0", false, Color(1.2, 1.15, 1.05))
		if spr:
			spr.position = Vector2(0, -10)
			add_child(spr)
		tam = TomarV2.sprite("tamga_" + stat, false, Color(2.0, 2.0, 2.0))
		if tam:
			tam.modulate = Color(1, 1, 1, 0)
			add_child(tam)
		# mühür kırılır: kızıl mum kıymıkları, altın halka
		FX.burst(global_position + Vector2(6, 0), Color(0.75, 0.12, 0.14), 10, 120, 0.5, 0.22, 420.0, false)
		FX.burst(global_position, Color(1.0, 0.82, 0.4), 8, 70, 0.45, 0.16, -60.0, true)
		FX.ring(global_position, 16, Color(1.0, 0.82, 0.4), 0.25)

	func _process(delta: float) -> void:
		t += delta
		var k := clampf(t / 0.5, 0.0, 1.0)
		if spr:
			var fr := mini(TomarV2.ACILIS_KARE - 1, int(floor(k * float(TomarV2.ACILIS_KARE - 1) + 0.0001)))
			TomarV2.set_region(spr, "tomar_ac_%d" % fr)
			spr.position = Vector2(0, -10.0 - 8.0 * (1.0 - pow(1.0 - k, 3.0)))
			spr.modulate.a = 1.0 - clampf((t - 1.0) / 0.4, 0.0, 1.0)
		# tamga: halkanın merkezinde (üst çubuğun 14 birim altı) belirir
		if tam and spr:
			var c := spr.position + Vector2(0, 14)
			var e := clampf((t - 0.38) / 0.22, 0.0, 1.0)
			if t < 0.85:
				var ov := 1.0 + 0.25 * sin(e * PI)
				tam.position = c
				tam.scale = Vector2.ONE * 0.25 * (0.55 + 0.45 * e) * ov
				tam.modulate = Color(1, 1, 1, e)
			else:
				if not _burst:
					_burst = true
					_fly0 = c
					FX.ring(to_global(c), 34, col, 0.4)
					FX.soul(to_global(c), col, 26)
					FX.burst(to_global(c), col, 14, 110, 0.55, 0.22, 0.0, true)
					FX.burst(to_global(c), Color(0.06, 0.05, 0.08, 0.85), 8, 60, 0.7, 0.2, -40.0, false)   # mürekkep zerreleri
					FX.flash_light(to_global(c), col, 120.0, 2.0, 0.3)
				var f := clampf((t - 0.85) / 0.4, 0.0, 1.0)
				var dst := _fly0
				if is_instance_valid(target):
					var tc: Vector2 = target.call("center") if target.has_method("center") else target.global_position
					dst = to_local(tc)
				var fe := f * f
				tam.position = _fly0.lerp(dst, fe) + Vector2(0, -18.0 * sin(f * PI))
				tam.scale = Vector2.ONE * 0.25 * (1.0 - 0.7 * fe)
				tam.modulate = Color(1, 1, 1, 1.0 - clampf((f - 0.75) / 0.25, 0.0, 1.0))
				if f >= 1.0 and tam.visible and is_instance_valid(target):
					FX.ring(to_global(dst), 22, col, 0.25)
					tam.visible = false
		if t > 1.5:
			queue_free()
