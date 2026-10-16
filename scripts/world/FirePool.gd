class_name FirePool
extends Node2D
## Od Testisi'nin bıraktığı alev gölü: içindeki düşmanları yakar.

var level: Node
var radius := 32.0
var life := 4.0
var dps := 3.0
var _tick := 0.0
var _t := 0.0


func _ready() -> void:
	z_index = 8
	var m := CanvasItemMaterial.new()
	m.blend_mode = CanvasItemMaterial.BLEND_MODE_ADD
	m.light_mode = CanvasItemMaterial.LIGHT_MODE_UNSHADED
	material = m


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
	if Data.stil == "v2":
		# mürekkep alev dilleri: kenar yumuşatmalı sivri alevler (toplamalı), içte sarı çekirdek
		for k in 7:
			var x := -radius + k * radius / 3.0
			var h := 7.0 + absf(sin(_t * 9.0 + k * 1.7)) * 9.0
			var sw := sin(_t * 7.0 + k) * 2.0
			draw_colored_polygon(PackedVector2Array([Vector2(x - 4, 0), Vector2(x - 2.5, -h * 0.5), Vector2(x + sw, -h), Vector2(x + 2.5, -h * 0.45), Vector2(x + 4, 0)]), Color(1.3, 0.5, 0.14, 0.55 * a))
			draw_colored_polygon(PackedVector2Array([Vector2(x - 2, 0), Vector2(x - 1, -h * 0.35), Vector2(x + sw * 0.6, -h * 0.62), Vector2(x + 1, -h * 0.3), Vector2(x + 2, 0)]), Color(1.6, 1.1, 0.45, 0.75 * a))
		return
	for k in 7:
		var x := -radius + k * radius / 3.0
		var h := 6.0 + absf(sin(_t * 9.0 + k * 1.7)) * 8.0
		draw_rect(Rect2(x - 3, -h, 6, h), Color(1.3, 0.55, 0.15, 0.55 * a))
		draw_rect(Rect2(x - 1.5, -h * 0.6, 3, h * 0.6), Color(1.6, 1.1, 0.4, 0.7 * a))
