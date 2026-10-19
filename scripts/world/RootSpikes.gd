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
	InkDraw.prep(self)
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
	InkDraw.blot(self, Vector2(0, 0.5), 12.0 * k, Color(0.12, 0.09, 0.08, 0.7 * k), 4)
	# mürekkep kökler: kenar yumuşatmalı kıvrık sivri kökler, mürekkep konturu, ışık yanında açık şerit, yan dikenler
	var inkc := Color(0.08, 0.085, 0.11)
	for i in 5:
		var x := -14.0 + i * 7.0
		var h := (26.0 + 14.0 * absf(sin(i * 2.1))) * k
		var bend := sin(i * 1.7) * 4.0 * k
		var pts := PackedVector2Array([Vector2(x - 3.4, 1), Vector2(x - 2.2, -h * 0.45), Vector2(x - 0.6 + bend, -h * 0.8), Vector2(x + bend * 1.3, -h),
			Vector2(x + 1.2 + bend, -h * 0.75), Vector2(x + 2.4, -h * 0.4), Vector2(x + 3.4, 1)])
		draw_colored_polygon(pts, bark)
		draw_polyline(pts, inkc, 1.3, true)
		draw_line(Vector2(x - 1.6, -2), Vector2(x - 0.8 + bend * 0.8, -h * 0.7), lite, 0.9, true)
		if h > 18.0:
			var sy := -h * 0.5
			var sp := PackedVector2Array([Vector2(x + 1.8, sy), Vector2(x + 6.0, sy - 5.0), Vector2(x + 2.2, sy - 2.5)])
			draw_colored_polygon(sp, bark)
			draw_polyline(sp, inkc, 0.8, true)
