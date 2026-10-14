class_name RootSpikes
extends Node2D
## Ağaç İyesi'nin kök saldırısı: yerden fırlayan dikenli kökler.

var level: Node
var dmg := 10.0
var source: Node
var _t := 0.0
var _hit := false


func _ready() -> void:
	z_index = 12
	Game.shake(3.0)
	FX.burst(global_position, Color(0.5, 0.36, 0.22), 14, 160, 0.5, 0.25, 400)


func _process(delta: float) -> void:
	_t += delta
	if _t > 0.7:
		queue_free()
		return
	var pl: Node = level.player
	if not _hit and _t < 0.35 and pl and not pl.dead:
		var box := Rect2(global_position + Vector2(-16, -42), Vector2(32, 42))
		if box.intersects(pl.hurt_rect()):
			if pl.take_hit(dmg, source):
				_hit = true
	queue_redraw()


func _draw() -> void:
	var k := clampf(_t / 0.12, 0.0, 1.0) * (1.0 - clampf((_t - 0.45) / 0.25, 0.0, 1.0))
	var bark := Color(0.42, 0.28, 0.18)
	var lite := Color(0.62, 0.44, 0.28)
	for i in 5:
		var x := -14.0 + i * 7.0
		var h := (26.0 + 14.0 * absf(sin(i * 2.1))) * k
		var pts := PackedVector2Array([Vector2(x - 3, 0), Vector2(x + 3, 0), Vector2(x + 0.5, -h)])
		draw_colored_polygon(pts, bark)
		draw_line(Vector2(x - 1, -2), Vector2(x + 0.3, -h + 2), lite, 1.0)
