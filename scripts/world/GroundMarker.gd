class_name GroundMarker
extends Node2D
## Yerden gelecek saldırının uyarısı: titreşen kırmızı çizgi ve toz.

var life := 0.7
var _t := 0.0


func _process(delta: float) -> void:
	_t += delta
	if _t >= life:
		queue_free()
		return
	queue_redraw()


func _draw() -> void:
	var on := int(_t * 14.0) % 2 == 0
	var c := Color(1.0, 0.3, 0.2, 0.9) if on else Color(1.0, 0.8, 0.3, 0.7)
	draw_rect(Rect2(-18, -2, 36, 2), c)
	for k in 3:
		draw_rect(Rect2(-14 + k * 12, -5 - (int(_t * 20.0 + k) % 4), 2, 2), Color(0.6, 0.45, 0.3))
