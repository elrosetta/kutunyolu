class_name FirePool
extends Node2D
## Od Testisi'nin bıraktığı alev gölü: içindeki düşmanları yakar.

var level: Node
var radius := 32.0
var life := 4.0
var dps := 3.0
var _tick := 0.0
var _t := 0.0
var ink := FX.ink()   # v2: fırça alev dilleri (InkDraw.flame), tabanda kor yıkaması


func _ready() -> void:
	z_index = 8
	var m := CanvasItemMaterial.new()
	m.blend_mode = CanvasItemMaterial.BLEND_MODE_ADD
	m.light_mode = CanvasItemMaterial.LIGHT_MODE_UNSHADED
	material = m
	if ink:
		InkDraw.prep(self)


func _process(delta: float) -> void:
	_t += delta
	life -= delta
	if life <= 0.0:
		queue_free()
		return
	_tick -= delta
	if _tick <= 0.0:
		_tick = 0.4
		var box := Rect2(global_position + Vector2(-radius, -26), Vector2(radius * 2.0, 28))
		for e in get_tree().get_nodes_in_group("dusman"):
			if is_instance_valid(e) and not e.dead and box.intersects(e.hurt_rect()):
				e.take_hit(dps, {"burn": 3.0, "kb": 0.0})
	if Engine.get_process_frames() % 3 == 0:
		FX.fire(global_position + Vector2(randf_range(-radius, radius), -2), 2, 0.34, 2.0)
		if Engine.get_physics_frames() % 12 == 0:
			FX.smoke(global_position + Vector2(randf_range(-radius, radius), -10), 1, 0.35)
	queue_redraw()


func _draw() -> void:
	var a := clampf(life, 0.0, 1.0)
	if ink:
		# mürekkep alev dilleri: fırça alev dokusu (toplamalı), içte sarı çekirdek; tabanda kor yıkaması
		InkDraw.ellipse(self, Vector2(0, -1), radius * 1.05, 4.0, Color(1.0, 0.35, 0.08, 0.35 * a), "duman_0")
		for k in 7:
			var x := -radius + k * radius / 3.0
			var h := 8.0 + absf(sin(_t * 9.0 + k * 1.7)) * 10.0
			var sw := sin(_t * 7.0 + k) * 0.6
			InkDraw.flame(self, Vector2(x, 1), 8.0, h, Color(1.3, 0.5, 0.14, 0.6 * a), sw)
			InkDraw.flame(self, Vector2(x, 1), 4.0, h * 0.6, Color(1.6, 1.1, 0.45, 0.8 * a), sw * 0.6)
		return
	for k in 7:
		var x := -radius + k * radius / 3.0
		var h := 6.0 + absf(sin(_t * 9.0 + k * 1.7)) * 8.0
		draw_rect(Rect2(x - 3, -h, 6, h), Color(1.3, 0.55, 0.15, 0.55 * a))
		draw_rect(Rect2(x - 1.5, -h * 0.6, 3, h * 0.6), Color(1.6, 1.1, 0.4, 0.7 * a))
