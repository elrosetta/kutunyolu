class_name LightningFX
extends Node2D
## Gök Asası şimşeği: iki nokta arasında kırık çizgi, 2-3 kez yeniden çizilip söner.

var a := Vector2.ZERO
var b := Vector2(60, 0)
var col := Color(0.7, 0.85, 1.0)
var life := 0.16
var _t := 0.0
var _pts := PackedVector2Array()
var _seed := 0


func _ready() -> void:
	z_index = 65
	top_level = true
	var m := CanvasItemMaterial.new()
	m.blend_mode = CanvasItemMaterial.BLEND_MODE_ADD
	m.light_mode = CanvasItemMaterial.LIGHT_MODE_UNSHADED
	material = m
	_rebuild()


func _rebuild() -> void:
	_pts.clear()
	var n := maxi(4, int(a.distance_to(b) / 10.0))
	var dir := (b - a)
	var nrm := Vector2(-dir.y, dir.x).normalized()
	for i in n + 1:
		var t := float(i) / n
		var off := 0.0 if (i == 0 or i == n) else randf_range(-7.0, 7.0)
		_pts.append(a + dir * t + nrm * off)


func _process(delta: float) -> void:
	_t += delta
	if _t >= life:
		queue_free()
		return
	if int(_t * 60.0) % 3 == 0:
		_rebuild()
	queue_redraw()


func _draw() -> void:
	var k := 1.0 - _t / life
	draw_polyline(_pts, Color(col.r * 1.4, col.g * 1.4, col.b * 1.6, k), 3.0 * k + 1.0)
	draw_polyline(_pts, Color(1.4, 1.4, 1.5, k), 1.0)
