class_name ImpactFX
extends Node2D
## Darbe yıldızı: vuruş anında beyaz bir flaş ve darbe yönünde uzayan ince ışınlar.
## Işınlar önce fırlar, sonra incelerek söner. Toplamalı; ışıktan etkilenmez.

var dir := Vector2.RIGHT
var col := Color(1, 0.95, 0.8)
var size := 1.0
var life := 0.16
var _t := 0.0
var _rays: Array = []


func _ready() -> void:
	z_index = 70
	var m := CanvasItemMaterial.new()
	m.blend_mode = CanvasItemMaterial.BLEND_MODE_ADD
	m.light_mode = CanvasItemMaterial.LIGHT_MODE_UNSHADED
	material = m
	var base := dir.angle() if dir.length() > 0.01 else 0.0
	var n := 7 + int(size * 2.0)
	for i in n:
		var a := base + randf_range(-PI, PI)
		# darbe yönüne yakın ışınlar daha uzun
		var along := 0.5 + 0.5 * cos(a - base)
		_rays.append({"a": a, "len": (10.0 + 18.0 * along + randf_range(0, 8)) * size, "w": randf_range(1.2, 2.4) * size})


func _process(delta: float) -> void:
	_t += delta
	if _t >= life:
		queue_free()
		return
	queue_redraw()


func _draw() -> void:
	var k := _t / life
	var grow := 1.0 - pow(1.0 - minf(1.0, k * 1.8), 2.0)
	var fade := 1.0 - k
	var c := Color(col.r * 1.6, col.g * 1.5, col.b * 1.3, fade)
	if k < 0.35:
		draw_circle(Vector2.ZERO, (9.0 * size) * (1.0 - k / 0.35) + 2.0, Color(1.4, 1.35, 1.2, (1.0 - k / 0.35) * 0.9))
	for r in _rays:
		var a: float = r["a"]
		var d := Vector2(cos(a), sin(a))
		var n := Vector2(-d.y, d.x)
		var l0: float = r["len"] * grow
		var l1: float = r["len"] * clampf(k * 1.3 - 0.15, 0.0, 1.0)
		var w: float = r["w"] * fade
		var pts := PackedVector2Array([d * l1 + n * w, d * l0, d * l1 - n * w])
		draw_colored_polygon(pts, c)
