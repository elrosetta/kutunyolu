class_name RingFX
extends Node2D
## Genişleyen halka (patlama, şok dalgası, savuşturma). aspect < 1 ise yere yatık elips.

var max_r := 30.0
var col := Color(1, 0.8, 0.4)
var life := 0.3
var aspect := 1.0
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
	# Sade halka: eskiden 1,6x HDR parlaklıkta, 4 px kalın ve çok büyük çiziliyordu; birkaç tanesi üst üste
	# binince ekran halkalarla doluyordu. Şimdi ince (1-2 px), sönük, yarıçapı 48 ile sınırlı.
	var k := _t / life
	var r := roundf(minf(max_r, 48.0) * (0.3 + 0.7 * sqrt(k)))
	var c := Color(col.r, col.g, col.b, 0.55 * (1.0 - k) * (1.0 - k))
	var w := 2.0 if k < 0.35 else 1.0
	if aspect >= 0.999:
		draw_arc(Vector2.ZERO, r, 0.0, TAU, maxi(16, int(r)), c, w, false)
		return
	var pts := PackedVector2Array()
	for i in 33:
		var a := TAU * float(i) / 32.0
		pts.append(Vector2(cos(a) * r, sin(a) * r * aspect))
	draw_polyline(pts, c, w)
	# ikinci, daha sönük iç halka: toprak dalgası hissi
	var pts2 := PackedVector2Array()
	for i in 33:
		var a := TAU * float(i) / 32.0
		pts2.append(Vector2(cos(a) * r * 0.6, sin(a) * r * aspect * 0.6))
	draw_polyline(pts2, Color(c, c.a * 0.5), w * 0.6)
