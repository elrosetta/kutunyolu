class_name SpiritWolf
extends Node2D
## Bozkurt Çağrısı / Bozkurt Ruhu: oyuncunun yanında koşan, düşmanlara atılan hayalet kurt.

var level: Node
var life := 12.0
var dmg := 9.0
var sprite_name := "kara_boru"  # "cor": Ruh Kuşu (uçan)
var anim: SpriteAnim
var facing := 1
var _cd := 0.4
var _lunge := 0.0
var _target: Node
var _hit: Array = []


func _ready() -> void:
	z_index = 3
	anim = SpriteAnim.new()
	add_child(anim)
	anim.setup(sprite_name)
	anim.set_tint(Color(0.55, 1.4, 1.8) if sprite_name == "kara_boru" else Color(1.3, 1.2, 0.6))
	anim.modulate = Color(1, 1, 1, 0.85)
	if anim.glow:
		anim.glow.visible = false
	FX.burst(global_position + Vector2(0, -12), Color(0.5, 0.95, 1.0), 20, 120, 0.6, 0.25, -30, true)


func _physics_process(delta: float) -> void:
	life -= delta
	if life <= 0.0:
		FX.burst(global_position + Vector2(0, -12), Color(0.5, 0.95, 1.0), 16, 90, 0.6, 0.22, -40, true)
		queue_free()
		return
	var pl: Node = level.player
	if pl == null:
		return
	_cd -= delta
	if _lunge > 0.0 and is_instance_valid(_target) and not _target.dead:
		_lunge -= delta
		var to: Vector2 = _target.center() - global_position
		global_position += to.normalized() * 420.0 * delta
		facing = int(sign(to.x)) if absf(to.x) > 2.0 else facing
		anim.play("leap" if anim.has_anim("leap") else "attack")
		if not _hit.has(_target) and _target.hurt_rect().grow(6).has_point(global_position + Vector2(0, -10)):
			_hit.append(_target)
			_target.take_hit(dmg, {"kb": 120.0, "dir": facing})
			FX.burst(_target.center(), Color(0.6, 1.0, 1.0), 8, 90, 0.3, 0.2, 0, true)
	else:
		_lunge = 0.0
		var goal: Vector2 = pl.global_position + Vector2(-pl.facing * 26.0, -34.0 if sprite_name == "cor" else 0.0)
		var to2 := goal - global_position
		global_position += to2 * clampf(6.0 * delta, 0.0, 1.0)
		if absf(to2.x) > 3.0:
			facing = int(sign(to2.x))
		anim.play("run" if (to2.length() > 8.0 and anim.has_anim("run")) else "idle")
		if _cd <= 0.0:
			var best: Node = null
			var bd := 170.0
			for e in get_tree().get_nodes_in_group("dusman"):
				if is_instance_valid(e) and not e.dead:
					var d := global_position.distance_to(e.center())
					if d < bd:
						bd = d
						best = e
			if best:
				_target = best
				_lunge = 0.35
				_hit.clear()
				_cd = 1.0
	anim.set_facing(facing)
	if Engine.get_physics_frames() % 6 == 0:
		FX.burst(global_position + Vector2(randf_range(-10, 10), -10), Color(0.5, 0.95, 1.0), 1, 20, 0.5, 0.15, -40, true)
