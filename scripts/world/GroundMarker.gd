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
	if Data.stil == "v2":
		# mürekkep uyarı: yerde incelen kızıl fırça çizgisi + sıçrayan toprak kırıntıları
		var w := 18.0
		for i in 8:
			var x0 := -w + i * w / 4.0
			var th := 2.4 * sin(PI * float(i) / 8.0) + 0.6
			draw_line(Vector2(x0, -1), Vector2(x0 + w / 4.0, -1), c, th, true)
		for k in 3:
			draw_circle(Vector2(-14 + k * 12, -4 - fmod(_t * 20.0 + k, 4.0)), 1.1, Color(0.45, 0.32, 0.24), true, -1.0, true)
		return
	draw_rect(Rect2(-18, -2, 36, 2), c)
	for k in 3:
		draw_rect(Rect2(-14 + k * 12, -5 - (int(_t * 20.0 + k) % 4), 2, 2), Color(0.6, 0.45, 0.3))
