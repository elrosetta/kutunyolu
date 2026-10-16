class_name Corpse
extends Node2D
## Ölen gövde (v11): darbe yönünde savrulur; dönüşü darbeye bağlıdır (rastgele fırıldak değil).
## Yere değince sürtünmeyle kayar ve yan yatar; sonra kor kenarlı bir çözülmeyle kül olup göğe dağılır.

const DISSOLVE := """
shader_type canvas_item;
uniform float prog = 0.0;
uniform vec4 edge : source_color = vec4(0.6, 0.95, 1.0, 1.0);
uniform vec4 dark : source_color = vec4(0.2, 0.1, 0.2, 1.0);
uniform float darkk = 0.0;
float h(vec2 p) { return fract(sin(dot(p, vec2(12.9898, 78.233))) * 43758.5453); }
float n(vec2 p) {
	vec2 i = floor(p); vec2 f = fract(p); f = f * f * (3.0 - 2.0 * f);
	return mix(mix(h(i), h(i + vec2(1.0, 0.0)), f.x), mix(h(i + vec2(0.0, 1.0)), h(i + vec2(1.0, 1.0)), f.x), f.y);
}
void fragment() {
	vec4 c = COLOR;
	vec2 px = floor(UV / TEXTURE_PIXEL_SIZE / 2.0);
	float v = n(px * 0.22) * 0.75 + h(px) * 0.25;
	c.rgb = mix(c.rgb, dark.rgb, darkk);
	if (v < prog) { discard; }
	float e = 1.0 - smoothstep(prog, prog + 0.09, v);
	c.rgb = mix(c.rgb, edge.rgb * 1.7, e * step(0.002, prog));
	COLOR = c;
}
"""
static var _shader: Shader

var velocity := Vector2.ZERO
var ang_v := 0.0
var life := 1.35
var _t := 0.0
var spr: Sprite2D
var tint := Color(0.4, 0.15, 0.45)
var _mat: ShaderMaterial
var _grounded := false
var _half := Vector2(16, 16)
var _side := 1.0
var _ash_col := Color(0.6, 0.95, 1.0)


func setup(src: Sprite2D, vel: Vector2, col: Color) -> void:
	spr = Sprite2D.new()
	spr.texture = src.texture
	spr.region_enabled = src.region_enabled
	spr.region_rect = src.region_rect
	spr.centered = src.centered
	spr.flip_h = src.flip_h
	spr.offset = src.offset
	add_child(spr)
	global_transform = src.global_transform
	var sz := src.region_rect.size if src.region_enabled else Vector2(src.texture.get_size())
	_half = sz * 0.25 * src.scale.abs()  # doku yoğunluğu (SpriteAnim texel) dünya boyuna çevrilir
	var c := src.position + (Vector2.ZERO if src.centered else sz * 0.5)
	spr.position = src.position - c
	position = src.global_position - src.position + c
	velocity = vel
	_side = signf(vel.x if vel.x != 0.0 else 1.0)
	# dönüş darbe hızından: hafif gövde yavaş, sert darbe hızlı döndürür; büyük gövde ağır döner
	var mass := clampf(sz.length() / 120.0, 0.6, 2.5)
	ang_v = _side * clampf(absf(vel.x) / 60.0, 1.2, 6.0) / mass
	tint = col
	_ash_col = Color(col).lerp(Color(1.0, 0.85, 0.6), 0.45)
	z_index = 4
	if _shader == null:
		_shader = Shader.new()
		_shader.code = DISSOLVE
	_mat = ShaderMaterial.new()
	_mat.shader = _shader
	_mat.set_shader_parameter("edge", _ash_col)
	_mat.set_shader_parameter("dark", Color(col).darkened(0.6))
	spr.material = _mat


func _physics_process(delta: float) -> void:
	_t += delta
	var k := _t / life
	if not _grounded:
		velocity.y += 980.0 * delta
	position += velocity * delta
	rotation += ang_v * delta
	var lv := FX.level
	if lv and lv.has_method("ground_at") and velocity.y > 0.0 and lv.ground_at(position + Vector2(0, _half.y * 0.6)):
		if velocity.y > 220.0:
			# ilk çarpma: küçük sekme, toz, dönüş yarıya iner
			velocity.y = -velocity.y * 0.22
			velocity.x *= 0.55
			ang_v *= 0.45
			FX.dust(position + Vector2(0, _half.y * 0.5), Vector2.UP, 5, 0.3)
		else:
			_grounded = true
			velocity.y = 0.0
	if _grounded:
		# sürtünme ile kayar, en yakın 'yan yatış' açısına devrilir (yay)
		velocity.x = move_toward(velocity.x, 0.0, 900.0 * delta)
		var rest := snappedf(rotation, PI * 0.5)
		if absf(wrapf(rotation - rest, -PI, PI)) < 0.01 and absf(rest - roundf(rest / PI) * PI) < 0.01:
			rest = rotation + _side * PI * 0.5  # dik duruyorsa yana devril
		ang_v += (wrapf(rest - rotation, -PI, PI) * 60.0 - ang_v * 9.0) * delta
		if absf(velocity.x) > 30.0 and int(_t * 60.0) % 5 == 0:
			FX.dust(position + Vector2(0, _half.y * 0.5), Vector2(-signf(velocity.x), -0.4), 1, 0.22)
	# önce koyulaş, sonra kor kenarlı çözülme + kül zerreleri
	_mat.set_shader_parameter("darkk", clampf(k * 1.6, 0.0, 0.7))
	var pr := clampf((k - 0.42) / 0.55, 0.0, 1.0)
	_mat.set_shader_parameter("prog", pr * pr * (3.0 - 2.0 * pr))
	if pr > 0.0 and pr < 0.95 and int(_t * 60.0) % 2 == 0:
		var p := position + Vector2(randf_range(-_half.x, _half.x), randf_range(-_half.y, _half.y) * 0.8).rotated(rotation) * 0.8
		FX.burst(p, _ash_col, 1, 26, 0.7, 0.2, -70, true)
		if randf() < 0.4:
			FX.burst(p, Color(0.25, 0.22, 0.24, 0.8), 1, 18, 0.9, 0.26, -40, false)
	elif k < 0.4 and int(_t * 60.0) % 7 == 0:
		FX.burst(position, tint, 1, 40, 0.45, 0.22, 200)
	if _t >= life:
		queue_free()
