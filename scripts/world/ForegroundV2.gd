class_name ForegroundV2
extends CanvasLayer
## Stil v2 ön plan (yalnızca --stil=v2 ve "fg" tanımı olan biyomlar, data/stil_v2.json):
## ekranın alt kenarında aktörlerin ÖNÜNDE mor-siyah siluet otlar, üst kenarda seyrek sarkan dallar, ekranda
## süzülen koyu yapraklar. Kameradan hızlı kayar (paralaks > 1: bakanın önünde). Oyuncunun çevresinde
## şerit yarı saydamlaşır (fg_sway.gdshader "hole"), oynanış asla örtülmez.

var spec: Dictionary = {}
var level: Node
var _strips: Array = []
var _vh := 540.0
var _base_y := 0.0


func _ready() -> void:
	layer = 3
	_vh = float(ProjectSettings.get_setting("display/window/size/viewport_height", 540))
	var grass: String = spec.get("grass", "")
	if grass != "":
		_add_strip(grass, float(spec.get("grass_fx", 1.25)), true, float(spec.get("grass_scale", 0.5)), float(spec.get("grass_alpha", 1.0)))
	var top: String = spec.get("top", "")
	if top != "":
		_add_strip(top, float(spec.get("top_fx", 1.15)), false, float(spec.get("top_scale", 0.5)), float(spec.get("top_alpha", 1.0)))
	var leaf: String = spec.get("leaf", "")
	if leaf != "":
		_add_leaves(leaf, int(spec.get("leaves", 7)))


func _add_strip(path: String, fx: float, bottom: bool, k: float, alpha: float) -> void:
	var tex: Texture2D = load(path)
	if tex == null:
		return
	var holder := Node2D.new()
	add_child(holder)
	var mat := ShaderMaterial.new()
	mat.shader = load("res://shaders/fg_sway.gdshader")
	mat.set_shader_parameter("root_bottom", bottom)
	mat.set_shader_parameter("amp_px", 7.0 if bottom else 5.0)
	mat.set_shader_parameter("alpha", alpha)
	var copies: Array = []
	for i in 3:
		var s := Sprite2D.new()
		s.texture = tex
		s.centered = false
		s.scale = Vector2(k, k)
		s.material = mat
		s.texture_filter = CanvasItem.TEXTURE_FILTER_LINEAR_WITH_MIPMAPS
		holder.add_child(s)
		copies.append(s)
	_strips.append({"copies": copies, "w": tex.get_width() * k, "h": tex.get_height() * k, "fx": fx, "bottom": bottom, "mat": mat})


func _add_leaves(path: String, n: int) -> void:
	## ekranda (kameraya göre) süzülen büyük koyu yapraklar: az sayıda, yavaş, dönerek
	var p := CPUParticles2D.new()
	p.texture = load(path)
	p.texture_filter = CanvasItem.TEXTURE_FILTER_LINEAR_WITH_MIPMAPS
	p.amount = n
	p.lifetime = 11.0
	p.preprocess = 11.0
	p.emission_shape = CPUParticles2D.EMISSION_SHAPE_RECTANGLE
	p.emission_rect_extents = Vector2(620, 10)
	p.position = Vector2(480, -40)
	p.direction = Vector2(-0.4, 1)
	p.spread = 25.0
	p.initial_velocity_min = 16.0
	p.initial_velocity_max = 34.0
	p.gravity = Vector2(-6, 12)
	p.angular_velocity_min = -120.0
	p.angular_velocity_max = 120.0
	p.angle_min = 0.0
	p.angle_max = 360.0
	p.scale_amount_min = 0.35
	p.scale_amount_max = 0.7
	p.color = Color(spec.get("leaf_col", "1e0c1e"))
	var mat := CanvasItemMaterial.new()
	mat.light_mode = CanvasItemMaterial.LIGHT_MODE_UNSHADED
	p.material = mat
	add_child(p)


func _process(_delta: float) -> void:
	var cam: Camera2D = Game.camera
	if cam == null:
		return
	var c := cam.get_screen_center_position()
	if _base_y == 0.0:
		_base_y = c.y
	var vp := get_viewport().get_visible_rect().size
	# saydamlık delikleri: oyuncu + ekranın alt bandındaki en yakın düşmanlar
	var holes := PackedVector2Array()
	var actors: Array = []
	if level != null and is_instance_valid(level.get("player")):
		actors.append(level.get("player"))
	for e in get_tree().get_nodes_in_group("dusman"):
		if actors.size() >= 6:
			break
		var en := e as Node2D
		if en == null or en.get("dead") == true:
			continue
		var p: Vector2 = en.get_global_transform_with_canvas().origin
		if p.y > vp.y * 0.55 and p.x > -40.0 and p.x < vp.x + 40.0:
			actors.append(en)
	for a in actors:
		var sp: Vector2 = (a as Node2D).get_global_transform_with_canvas().origin + Vector2(0, -24)
		holes.append(Vector2(sp.x / vp.x, sp.y / vp.y))
	var n_holes := holes.size()
	holes.resize(6)
	for S in _strips:
		var w: float = S["w"]
		var off := -fposmod(c.x * float(S["fx"]), w)
		var y: float
		if S["bottom"]:
			# alt kenara yaslı; kamera yükselince şerit biraz aşağı kayar (derinlik), alçalınca yükselmez
			y = vp.y - float(S["h"]) + clampf((_base_y - c.y) * 0.12, -6.0, 18.0)
		else:
			y = clampf((_base_y - c.y) * 0.12, -30.0, 6.0) - 4.0
		for k in S["copies"].size():
			S["copies"][k].position = Vector2(off + k * w, y)
		var m: ShaderMaterial = S["mat"]
		m.set_shader_parameter("holes", holes)
		m.set_shader_parameter("hole_count", n_holes)
		m.set_shader_parameter("aspect", vp.x / vp.y)
