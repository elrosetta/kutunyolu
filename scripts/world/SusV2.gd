class_name SusV2
extends RefCounted
## Stil v2 "mürekkep" ortak dünya nesneleri (tools/artgen/sus_ink.py, export_sus.py):
##   atlas  assets/fx/ink/sus_v2.png (+ _e ışıma) + sus_v2.json: toplanabilirler ve mermiler {rect, pivot}
##   süsler assets/decor/<ad>_v2.png (+ _e) + sus_v2.json: sunak, Kut Kapısı, totem, ruh taşı, bulutlar
## Doku yoğunluğu "texel" doku pikseli / dünya birimi (4); doğrusal süzgeç + mipmap. v1'de on() false: eski çizim aynen.

const ATLAS_JSON := "res://assets/fx/ink/sus_v2.json"
const DECOR_JSON := "res://assets/decor/sus_v2.json"

static var _meta: Dictionary = {}
static var _tex: Texture2D
static var _glow: Texture2D
static var _decor_meta: Dictionary = {}
static var _decor_tex: Dictionary = {}
static var _lit_mat: ShaderMaterial
static var _flat_mat: CanvasItemMaterial
static var _add_mat: CanvasItemMaterial


static func on() -> bool:
	return ResourceLoader.exists(ATLAS_JSON.replace(".json", ".png"))


static func meta() -> Dictionary:
	if _meta.is_empty():
		_meta = Data.load_json(ATLAS_JSON) if FileAccess.file_exists(ATLAS_JSON) else {"sprites": {}}
		_tex = Data.tex(ATLAS_JSON.replace(".json", ".png"))   # HD paketi varsa 2 kat ayrıntı (temel boyutta raporlanır)
		var gp := ATLAS_JSON.replace(".json", "_e.png")
		_glow = load(gp) if ResourceLoader.exists(gp) else null
	return _meta


static func has(n: String) -> bool:
	return (meta().get("sprites", {}) as Dictionary).has(n)


static func lit_mat() -> ShaderMaterial:
	## Işıktan etkilenen mürekkep malzemesi (env_ink: ay yumuşak, noktasal ışık tam)
	if _lit_mat == null:
		_lit_mat = ShaderMaterial.new()
		_lit_mat.shader = load("res://shaders/env_ink.gdshader")
		_lit_mat.set_shader_parameter("moon_gain", 0.5)
	return _lit_mat


static func flat_mat() -> CanvasItemMaterial:
	if _flat_mat == null:
		_flat_mat = CanvasItemMaterial.new()
		_flat_mat.light_mode = CanvasItemMaterial.LIGHT_MODE_UNSHADED
	return _flat_mat


static func add_mat() -> CanvasItemMaterial:
	if _add_mat == null:
		_add_mat = CanvasItemMaterial.new()
		_add_mat.blend_mode = CanvasItemMaterial.BLEND_MODE_ADD
		_add_mat.light_mode = CanvasItemMaterial.LIGHT_MODE_UNSHADED
	return _add_mat


static func sprite(n: String, lit := true, glow := Color(1.4, 1.3, 1.2)) -> Sprite2D:
	## Atlas parçası: köken pivot (dünya birimi 1/texel ölçekli). Işıma varsa toplamalı çocuk "glow".
	var m: Dictionary = meta()["sprites"].get(n, {})
	if m.is_empty():
		return null
	var k := 1.0 / float(meta().get("texel", 4.0))
	var r: Array = m["rect"]
	var s := Sprite2D.new()
	s.texture = _tex
	s.region_enabled = true
	s.region_rect = Rect2(r[0], r[1], r[2], r[3])
	s.centered = false
	s.offset = -Vector2(float(m["pivot"][0]), float(m["pivot"][1]))
	s.scale = Vector2(k, k)
	s.texture_filter = CanvasItem.TEXTURE_FILTER_LINEAR_WITH_MIPMAPS
	s.material = lit_mat() if lit else flat_mat()
	if bool(m.get("glow", false)) and _glow != null:
		var g := Sprite2D.new()
		g.name = "glow"
		g.texture = _glow
		g.region_enabled = true
		g.region_rect = s.region_rect
		g.centered = false
		g.offset = s.offset
		g.texture_filter = CanvasItem.TEXTURE_FILTER_LINEAR_WITH_MIPMAPS
		g.material = add_mat()
		g.self_modulate = glow
		s.add_child(g)
	return s


static func set_region(s: Sprite2D, n: String) -> void:
	## Aynı düğümde başka atlas parçasına geç (kanat çırpma karesi, ok türü)
	var m: Dictionary = meta()["sprites"].get(n, {})
	if m.is_empty() or s == null:
		return
	var r: Array = m["rect"]
	s.region_rect = Rect2(r[0], r[1], r[2], r[3])
	s.offset = -Vector2(float(m["pivot"][0]), float(m["pivot"][1]))
	var g := s.get_node_or_null("glow") as Sprite2D
	if g:
		g.region_rect = s.region_rect
		g.offset = s.offset


static func decor(n: String) -> Dictionary:
	## sus_v2.json süsü: {tex, glow_tex, origin, texel, size}; yoksa boş
	if _decor_meta.is_empty():
		_decor_meta = Data.load_json(DECOR_JSON) if FileAccess.file_exists(DECOR_JSON) else {"_": {}}
	var key := n + "_v2"
	if not _decor_meta.has(key):
		return {}
	if not _decor_tex.has(key):
		var d: Dictionary = (_decor_meta[key] as Dictionary).duplicate()
		d["tex"] = Data.tex("res://assets/decor/%s.png" % key)
		var gp := "res://assets/decor/%s_e.png" % key
		d["glow_tex"] = load(gp) if ResourceLoader.exists(gp) else null
		_decor_tex[key] = d
	return _decor_tex[key]


static func decor_sprite(n: String, lit := true, glow := Color(1.4, 1.3, 1.2)) -> Sprite2D:
	var d := decor(n)
	if d.is_empty():
		return null
	var k := 1.0 / float(d.get("texel", 4.0))
	var s := Sprite2D.new()
	s.texture = d["tex"]
	s.centered = false
	s.offset = -Vector2(float(d["origin"][0]), float(d["origin"][1]))
	s.scale = Vector2(k, k)
	s.texture_filter = CanvasItem.TEXTURE_FILTER_LINEAR_WITH_MIPMAPS
	s.material = lit_mat() if lit else flat_mat()
	if d.get("glow_tex") != null:
		var g := Sprite2D.new()
		g.name = "glow"
		g.texture = d["glow_tex"]
		g.centered = false
		g.offset = s.offset
		g.texture_filter = CanvasItem.TEXTURE_FILTER_LINEAR_WITH_MIPMAPS
		g.material = add_mat()
		g.self_modulate = glow
		s.add_child(g)
	return s


static func glow_only(n: String, col := Color(1, 1, 1)) -> Sprite2D:
	## Süsün yalnızca ışıma dokusu (girdap gibi): toplamalı, ışıksız
	var d := decor(n)
	if d.is_empty() or d.get("glow_tex") == null:
		return null
	var k := 1.0 / float(d.get("texel", 4.0))
	var s := Sprite2D.new()
	s.texture = d["glow_tex"]
	s.centered = false
	s.offset = -Vector2(float(d["origin"][0]), float(d["origin"][1]))
	s.scale = Vector2(k, k)
	s.texture_filter = CanvasItem.TEXTURE_FILTER_LINEAR_WITH_MIPMAPS
	s.material = add_mat()
	s.self_modulate = col
	return s
