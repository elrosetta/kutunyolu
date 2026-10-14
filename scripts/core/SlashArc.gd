class_name SlashArc
extends Node2D
## Kılıç savuruşu izi: kalınlığı ve saydamlığı uca doğru artan toplamalı yay.

var facing := 1
var a0 := -2.4
var a1 := 0.6
var radius := 26.0
var width := 8.0
var col := Color(1, 0.95, 0.8)
var life := 0.14
var _t := 0.0


func _ready() -> void:
	z_index = 55
	var m := CanvasItemMaterial.new()
	m.blend_mode = CanvasItemMaterial.BLEND_MODE_ADD
	m.light_mode = CanvasItemMaterial.LIGHT_MODE_UNSHADED
	material = m


func _process(delta: float) -> void:
	_t += delta
	if _t >= life:
		queue_free()
		return
	queue_redraw()


func _draw() -> void:
	var k := _t / life
	var steps := 18
	var outer := PackedVector2Array()
	var inner := PackedVector2Array()
	var cols := PackedColorArray()
	var head := clampf(k * 1.6, 0.0, 1.0)
	var tail := clampf(k * 1.6 - 0.6, 0.0, 1.0)
	for i in steps + 1:
		var t := lerpf(tail, head, float(i) / steps)
		var a := lerpf(a0, a1, t)
		if facing < 0:
			a = PI - a
		var w := width * (0.25 + 0.75 * float(i) / steps) * (1.0 - k * 0.6)
		var dir := Vector2(cos(a), sin(a))
		outer.append(dir * radius)
		inner.append(dir * (radius - w))
	var pts := PackedVector2Array()
	for p in outer:
		pts.append(p)
	for i in range(inner.size() - 1, -1, -1):
		pts.append(inner[i])
	for i in pts.size():
		var edge := float(i) / pts.size()
		var al := (1.0 - k) * (0.35 + 0.65 * (1.0 - absf(edge - 0.5) * 2.0))
		cols.append(Color(col.r * 1.8, col.g * 1.7, col.b * 1.5, al))
	if pts.size() >= 3:
		draw_polygon(pts, cols)
