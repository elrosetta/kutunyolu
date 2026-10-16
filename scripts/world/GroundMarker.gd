class_name GroundMarker
extends Node2D
## Yerden gelecek saldırının uyarısı: titreşen kırmızı çizgi ve toz.

var life := 0.7
var _t := 0.0
var ink := FX.ink()   # v2: yerde ortası kalın, uçları incelen kızıl fırça darbesi + kül kırıntıları


func _ready() -> void:
	if ink:
		InkDraw.prep(self)


func _process(delta: float) -> void:
	_t += delta
	if _t >= life:
		queue_free()
		return
	queue_redraw()


func _draw() -> void:
	var on := int(_t * 14.0) % 2 == 0
	var c := Color(1.0, 0.3, 0.2, 0.9) if on else Color(1.0, 0.8, 0.3, 0.7)
	if ink:
		# mürekkep uyarı: yerde ortası kalın, iki yana incelen kızıl fırça darbesi + sıçrayan toprak kırıntıları
		InkDraw.stroke(self, Vector2(-2, -1), Vector2(-20, -1), 4.2, c)
		InkDraw.stroke(self, Vector2(2, -1), Vector2(20, -1), 4.2, c)
		for k in 3:
			InkDraw.flake(self, Vector2(-14 + k * 12, -4 - fmod(_t * 20.0 + k, 4.0)), 2.4, _t * 6.0 + k, Color(0.45, 0.32, 0.24))
		return
	draw_rect(Rect2(-18, -2, 36, 2), c)
	for k in 3:
		draw_rect(Rect2(-14 + k * 12, -5 - (int(_t * 20.0 + k) % 4), 2, 2), Color(0.6, 0.45, 0.3))
