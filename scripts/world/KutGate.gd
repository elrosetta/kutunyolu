class_name KutGate
extends Node2D
## Bölüm çıkışı: Ulu Kayın'ın kökünden yükselen, içinde kut ışığı dönen taş kemer.

var _t := 0.0


func _ready() -> void:
	z_index = -1


func _process(delta: float) -> void:
	_t += delta
	queue_redraw()


func _draw() -> void:
	var stone := Color(0.42, 0.44, 0.52)
	var dark := Color(0.22, 0.22, 0.3)
	draw_rect(Rect2(-30, -64, 10, 64), stone)
	draw_rect(Rect2(20, -64, 10, 64), stone)
	draw_rect(Rect2(-34, -72, 68, 10), stone)
	draw_rect(Rect2(-30, -64, 2, 64), dark)
	draw_rect(Rect2(28, -64, 2, 64), dark)
	for k in 5:
		var c := Color.from_hsv(0.48 + 0.02 * k, 0.6, 1.0, 0.18 + 0.05 * sin(_t * 2.0 + k))
		draw_rect(Rect2(-20 + k * 0.5, -62 + k, 40 - k, 62 - k), c)
	for k in 8:
		var a := _t * 1.5 + k * TAU / 8.0
		var p := Vector2(cos(a) * 12.0, -32.0 + sin(a) * 20.0)
		draw_circle(p, 1.6, Color(0.7, 1.0, 1.0, 0.9))
	var cloths := [Color(0.9, 0.2, 0.2), Color(0.95, 0.95, 0.95), Color(0.2, 0.5, 0.95), Color(0.95, 0.8, 0.2)]
	for k in 4:
		var x := -26 + k * 17
		draw_rect(Rect2(x, -62, 3, 8 + 2 * sin(_t * 3.0 + k)), cloths[k])
