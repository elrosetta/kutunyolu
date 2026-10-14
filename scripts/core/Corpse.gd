class_name Corpse
extends Node2D
## Ölen gövde: sprite'ın kopyası savrulur, döner, yere çarpınca sıçrar, kararıp dağılır.

var velocity := Vector2.ZERO
var ang_v := 0.0
var life := 0.75
var _t := 0.0
var spr: Sprite2D
var tint := Color(0.4, 0.15, 0.45)


func setup(src: Sprite2D, vel: Vector2, col: Color) -> void:
	spr = Sprite2D.new()
	spr.texture = src.texture
	spr.region_enabled = src.region_enabled
	spr.region_rect = src.region_rect
	spr.centered = src.centered
	spr.flip_h = src.flip_h
	spr.offset = src.offset
	add_child(spr)
	global_transform = src.global_transform
	# döndürme merkezi: gövdenin ortası
	var sz := src.region_rect.size if src.region_enabled else Vector2(src.texture.get_size())
	var c := src.position + (Vector2.ZERO if src.centered else sz * 0.5)
	spr.position = src.position - c
	position = src.global_position - src.position + c
	velocity = vel
	ang_v = randf_range(-8.0, 8.0) * signf(vel.x if vel.x != 0.0 else 1.0)
	tint = col
	z_index = 4


func _physics_process(delta: float) -> void:
	_t += delta
	var k := _t / life
	velocity.y += 900.0 * delta
	position += velocity * delta
	rotation += ang_v * delta
	if FX.level and FX.level.has_method("ground_at") and velocity.y > 0.0 and FX.level.ground_at(position + Vector2(0, 6)):
		velocity.y = -velocity.y * 0.35
		velocity.x *= 0.6
		ang_v *= 0.5
		FX.dust(position + Vector2(0, 4), Vector2.UP, 4, 0.28)
	# kararma ve dağılma: önce koyulaşır, sonra saydamlaşır ve küçülür
	spr.modulate = Color(1, 1, 1, 1).lerp(Color(tint, 1.0), clampf(k * 2.0, 0.0, 1.0))
	spr.modulate.a = 1.0 - clampf((k - 0.55) / 0.45, 0.0, 1.0)
	scale = Vector2.ONE * (1.0 - 0.25 * clampf((k - 0.6) / 0.4, 0.0, 1.0))
	if int(_t * 60.0) % 6 == 0 and k < 0.6:
		FX.burst(position, tint, 1, 40, 0.45, 0.22, 200)
	if _t >= life:
		queue_free()
