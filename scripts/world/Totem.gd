class_name Totem
extends Node2D
## Davul Totemi: yere dikilir, 10 sn boyunca her 1,2 sn'de ritimle sarsıntı dalgası yayar;
## 70 px içindeki düşmanları yaralar ve kısa süre sersemletir.

var level: Node
var dmg := 7.0
var life := 10.0
var _t := 0.0
var _beat := 0.4
var _pulse := 0.0
## stil v2: mürekkep totem (sus_v2 "totem" gövde + "totem_tuy" salınan tüyler); vuruşta davul ezilip zıplar
var _body: Sprite2D
var _plume: Sprite2D
var ink := false   # piksel denetimi: v2 mürekkep totem çiziliyor


func _ready() -> void:
	z_index = 3
	if SusV2.on():
		_body = SusV2.decor_sprite("totem")
		_plume = SusV2.decor_sprite("totem_tuy")
		if _body:
			add_child(_body)
			ink = true
		if _plume:
			_plume.position = Vector2(0, -39)
			add_child(_plume)
	FX.dust(global_position, Vector2.UP, 6, 0.3)
	if level:
		level.add_light(Vector2(0, -16), Color(1.0, 0.75, 0.45), 80.0, 0.9, self)


func _physics_process(delta: float) -> void:
	_t += delta
	life -= delta
	_beat -= delta
	_pulse = maxf(0.0, _pulse - delta * 4.0)
	if life <= 0.0:
		FX.smoke(global_position + Vector2(0, -10), 4, 0.4)
		queue_free()
		return
	if _beat <= 0.0:
		_beat = 1.2
		_pulse = 1.0
		FX.ring(global_position + Vector2(0, -4), 70, Color(1.0, 0.8, 0.5), 0.35, 0.35)
		FX.anim("earth_rupture", global_position + Vector2(0, 2), 0.0, 0.6, Color(1.0, 0.85, 0.6), false)
		Game.shake(1.5)
		for e in get_tree().get_nodes_in_group("dusman"):
			if is_instance_valid(e) and not e.dead and e.center().distance_to(global_position) < 76.0:
				e.take_hit(dmg, {"kb": 90.0, "dir": signf(e.center().x - global_position.x), "stun": 0.35})
	queue_redraw()


func _draw() -> void:
	if _body:
		var k := 1.0 + _pulse * 0.16
		_body.scale = Vector2(k, 1.0 / k) * 0.25
		_body.position.y = 0.0
		if _plume:
			_plume.position = Vector2(0, -39 * (1.0 / k) - 4.0 * _pulse)
			_plume.rotation = sin(_t * 3.0) * 0.12
		return
	var sq := 1.0 + _pulse * 0.18
	# direk
	draw_rect(Rect2(-2, -26, 4, 26), Color(0.35, 0.22, 0.14))
	# davul (yan görünüş): deri + kasnak
	draw_rect(Rect2(-9 * sq, -36 - 4 * _pulse, 18 * sq, 12), Color(0.55, 0.36, 0.22))
	draw_rect(Rect2(-9 * sq, -36 - 4 * _pulse, 18 * sq, 2), Color(0.85, 0.75, 0.55))
	draw_rect(Rect2(-9 * sq, -26 - 4 * _pulse, 18 * sq, 2), Color(0.85, 0.75, 0.55))
	for k in 4:
		draw_rect(Rect2(-8 + k * 5, -34 - 4 * _pulse, 1, 8), Color(0.8, 0.3, 0.25))
	# tepedeki tüyler
	for k in 3:
		var x := -4 + k * 4
		draw_line(Vector2(x, -36 - 4 * _pulse), Vector2(x + 2 * sin(_t * 3 + k), -46 - 4 * _pulse), [Color(0.9, 0.25, 0.2), Color(0.95, 0.95, 0.95), Color(0.3, 0.6, 1.0)][k], 1.5)
