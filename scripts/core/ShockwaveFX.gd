class_name ShockwaveFX
extends ColorRect
## Ekran uzayı şok dalgası halkası (shaders/shockwave.gdshader). FX.screen_layer() altındaki tam ekran
## dikdörtgen: her karede dünya konumunu kamera dönüşümüyle ekran UV'sine çevirir, yarıçapı
## ease-out ile 0 → max_r büyütür, kaymayı sönümler. Mantıksal 960x540 ızgarasında tam piksel kayma.
## Kullanım: FX.shockwave(pos, radius, strength).

static var _shader: Shader

var world_pos := Vector2.ZERO
var max_r := 80.0          # dünya pikseli (mantıksal piksele eşit: 1 dünya px = 1 mantıksal px)
var strength := 3.0        # en çok kayma, mantıksal piksel (3 ≈ 1080p'de 6 ekran pikseli)
var thickness := 8.0       # halka kalınlığı, mantıksal piksel
var life := 0.35
var _t := 0.0
var _mat: ShaderMaterial


func _ready() -> void:
	mouse_filter = Control.MOUSE_FILTER_IGNORE
	color = Color(1, 1, 1, 1)
	if _shader == null:
		_shader = load("res://shaders/shockwave.gdshader")
	_mat = ShaderMaterial.new()
	_mat.shader = _shader
	material = _mat
	_update()


func _process(delta: float) -> void:
	_t += delta
	if _t >= life:
		queue_free()
		return
	_update()


func _update() -> void:
	var vp := get_viewport()
	if vp == null:
		return
	var vs := vp.get_visible_rect().size
	if vs.x < 1.0 or vs.y < 1.0:
		return
	# çapa yok: görünür dikdörtgene elle oturtulur (pencere boyutu değişirse izler)
	if size != vs:
		position = Vector2.ZERO
		size = vs
	var sp: Vector2 = vp.get_canvas_transform() * world_pos
	var k := clampf(_t / life, 0.0, 1.0)
	var eo := 1.0 - pow(1.0 - k, 3.0)
	_mat.set_shader_parameter("center", sp / vs)
	_mat.set_shader_parameter("view_size", vs)
	_mat.set_shader_parameter("radius", floorf(max_r * eo))
	_mat.set_shader_parameter("thickness", thickness)
	# kayma önce tam güç, son üçte birde hızla söner
	_mat.set_shader_parameter("strength", strength * clampf((1.0 - k) * 1.5, 0.0, 1.0))
	_mat.set_shader_parameter("rim", 0.05 * (1.0 - k))
