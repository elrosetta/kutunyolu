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


func _ready() -> void:
	z_index = 3
	_body = SusV2.decor_sprite("totem")
	_plume = SusV2.decor_sprite("totem_tuy")
	if _body:
		add_child(_body)
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
