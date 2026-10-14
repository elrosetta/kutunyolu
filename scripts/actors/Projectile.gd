class_name Projectile
extends Node2D
## Ok, cirit, sapan taşı, spor, bomba, hayalet kartal... Duvar, düşman ve oyuncu çarpışmalarını yönetir.

var kind := "arrow"
var team := "p"
var velocity := Vector2.ZERO
var gravity := 0.0
var damage := 0.0
var pierce := 0
var bounces := 0
var life := 3.0
var homing := 0.0
var stick := false
var explode_on_wall := false
var on_hit: Callable
var on_explode: Callable
var atlas_item := ""
var atlas_mat := "demir"
var level: Node
var source: Node
var trail_col := Color(0, 0, 0, 0)  # alfa > 0 ise arkasında solan iz bırakır
var return_px := 0.0  # balta: bu kadar gidince sahibine döner
var fx_kind := ""      # ok uçuş efekti: "" sade, "altin" tam gerilmiş, "od" alev, "sel" mavi rüzgâr, "kizil" akıncı
var owner_node: Node2D
var returning := false
var _travel := 0.0
var _hit: Array = []
var _stuck_t := -1.0
var _t := 0.0
var _trail: Array = []
var spr: Sprite2D


func _ready() -> void:
	z_index = 20
	if atlas_item != "" and Data.has_weapon_sprite(atlas_item):
		spr = Sprite2D.new()
		spr.texture = Data.weapon_tex
		spr.region_enabled = true
		spr.region_rect = Data.weapon_region(atlas_item, atlas_mat)
		spr.centered = false
		spr.offset = -Data.weapon_pivot(atlas_item)
		if kind == "javelin":
			spr.offset.x -= 20
		var m := ShaderMaterial.new()
		m.shader = Game.toon_shader
		spr.material = m
		add_child(spr)
	if kind in ["spore", "eagle", "arrow"]:
		var gm := CanvasItemMaterial.new()
		gm.blend_mode = CanvasItemMaterial.BLEND_MODE_ADD if kind != "arrow" else CanvasItemMaterial.BLEND_MODE_MIX
		gm.light_mode = CanvasItemMaterial.LIGHT_MODE_UNSHADED if kind != "arrow" else CanvasItemMaterial.LIGHT_MODE_NORMAL
		material = gm


func _physics_process(delta: float) -> void:
	_t += delta
	if _stuck_t >= 0.0:
		_stuck_t += delta
		var pl: Node = level.player
		if pl and pl.global_position.distance_to(global_position) < 22.0:
			pl.cd["second"] = 0.0
			queue_free()
		elif _stuck_t > 5.0:
			queue_free()
		return
	life -= delta
	if life <= 0.0:
		if on_explode.is_valid():
			_explode()
		else:
			queue_free()
		return
	if homing > 0.0 and not returning:
		var target := _nearest_target()
		if target:
			var want: Vector2 = (target.center() - global_position).normalized() * velocity.length()
			velocity = velocity.lerp(want, clampf(homing * delta, 0.0, 1.0))
	# geri dönen balta: menzili dolunca sahibine yönelir, ona ulaşınca kaybolur
	if return_px > 0.0:
		_travel += velocity.length() * delta
		if not returning and _travel >= return_px:
			_start_return()
		if returning and is_instance_valid(owner_node):
			var want2: Vector2 = (owner_node.center() - global_position).normalized() * 460.0
			velocity = velocity.lerp(want2, clampf(8.0 * delta, 0.0, 1.0))
			if global_position.distance_to(owner_node.center()) < 16.0:
				if "axe_out" in owner_node:
					owner_node.axe_out = false
				FX.sparks(global_position, Vector2.UP, Color(1, 0.95, 0.8), 4, 100.0)
				queue_free()
				return
	velocity.y += gravity * delta
	var next := position + velocity * delta
	if level.solid_at(next) and return_px > 0.0 and not returning:
		_start_return()
		return
	if level.solid_at(next) and returning:
		position = next  # dönüşte duvardan geçer
	elif level.solid_at(next):
		if bounces > 0:
			bounces -= 1
			if level.solid_at(Vector2(next.x, position.y)):
				velocity.x = -velocity.x * 0.8
			else:
				velocity.y = -velocity.y * 0.7
			_hit.clear()
			return
		if on_explode.is_valid():
			_explode()
			return
		if stick:
			_stuck_t = 0.0
			position = position + velocity.normalized() * 4.0
			return
		FX.burst(position, Color(0.8, 0.75, 0.6), 4, 50, 0.25, 0.15, 200)
		queue_free()
		return
	position = next
	if kind in ["arrow", "javelin", "eagle", "spore", "feather", "wave"]:
		rotation = velocity.angle()
	elif kind in ["bomb", "pot", "stone", "ice", "stone_big"]:
		rotation += delta * 10.0
	elif kind == "axe":
		rotation += delta * 22.0 * signf(velocity.x)
	if trail_col.a > 0.0:
		_trail.push_front(global_position)
		if _trail.size() > 9:
			_trail.pop_back()
	match fx_kind:
		"altin":
			if int(_t * 60.0) % 2 == 0:
				FX.burst(global_position, Color(1.0, 0.85, 0.4), 1, 20, 0.35, 0.16, 0, true)
		"od":
			if int(_t * 60.0) % 2 == 0:
				FX.fire(global_position, 1, 0.26, 1.0)
			if int(_t * 60.0) % 8 == 0:
				FX.smoke(global_position, 1, 0.22)
		"sel":
			if int(_t * 60.0) % 3 == 0:
				FX.burst(global_position, Color(0.55, 0.85, 1.0), 1, 25, 0.4, 0.15, -20, true)
	if kind in ["bomb", "pot"] and int(_t * 60.0) % 3 == 0:
		FX.burst(global_position, Color(1.0, 0.6, 0.2) if kind == "bomb" else Color(1.0, 0.45, 0.1), 1, 20, 0.3, 0.14, -40, true)
	queue_redraw()
	if team == "p":
		for e in get_tree().get_nodes_in_group("dusman"):
			if not is_instance_valid(e) or e.dead or _hit.has(e):
				continue
			if e.hurt_rect().grow(3.0).has_point(global_position):
				_hit.append(e)
				if on_explode.is_valid():
					_explode()
					return
				if on_hit.is_valid():
					on_hit.call(e)
					var hd := velocity.normalized()
					Ses.play("ok_vurus", -4.0, 1.0, 0.1)
					FX.impact(global_position, hd, Color(1.0, 0.95, 0.8) if fx_kind != "od" else Color(1.0, 0.6, 0.25), 1.2 if fx_kind == "altin" else 0.9)
					FX.sparks(global_position, -hd, Color(1.0, 0.9, 0.7), 5, 140.0)
					match fx_kind:
						"od":
							FX.fire(global_position, 8, 0.36, 4.0)
							FX.anim("ember_jet", global_position, hd.angle() + PI, 0.6, Color(1.0, 0.7, 0.3))
						"altin":
							FX.anim("solar_shrapnel", global_position, 0.0, 0.55, Color(1.0, 0.9, 0.5))
						"sel":
							FX.anim("splash_crown", global_position, 0.0, 0.5, Color(0.6, 0.85, 1.0))
				if pierce > 0:
					pierce -= 1
				elif bounces > 0:
					bounces -= 1
					velocity.x = -velocity.x
				else:
					queue_free()
					return
	else:
		var pl: Node = level.player
		if pl and not pl.dead and pl.hurt_rect().grow(2.0).has_point(global_position):
			var src: Node = source if is_instance_valid(source) else null
			var hit: bool = pl.take_hit(damage, src, self)
			if hit:
				Ses.play("ok_vurus", -6.0, 0.8, 0.1)
				if kind == "spore":
					FX.anim("acid_splash", position, 0.0, 0.8, Color(0.7, 1.0, 0.4))
					if pl.has_method("apply_poison"):
						pl.apply_poison(3.0)
				else:
					FX.burst(position, Color(0.7, 1.0, 0.3), 6, 60, 0.3, 0.2, 100, true)
				queue_free()


func _start_return() -> void:
	returning = true
	_hit.clear()
	velocity = -velocity * 0.5
	FX.impact(global_position, -velocity.normalized(), Color(1.0, 0.9, 0.7), 0.7)


func _nearest_target() -> Node:
	var best: Node = null
	var bd := 260.0
	for e in get_tree().get_nodes_in_group("dusman"):
		if not is_instance_valid(e) or e.dead:
			continue
		var d := global_position.distance_to(e.center())
		if d < bd:
			bd = d
			best = e
	return best


func reflect(dir: int, mult: float) -> void:
	team = "p"
	velocity = Vector2(dir * maxf(200.0, absf(velocity.x) * 1.3), -absf(velocity.y) * 0.3)
	damage *= mult
	life = 2.0
	homing = 4.0
	var dmg := damage
	on_hit = func(e: Node) -> void:
		e.take_hit(dmg, {"kb": 80.0, "dir": dir, "crit": true})


func _explode() -> void:
	if on_explode.is_valid():
		on_explode.call(global_position)
	queue_free()


func _draw() -> void:
	if trail_col.a > 0.0 and _trail.size() >= 2:
		var n := _trail.size()
		for i in range(n - 1):
			var f := 1.0 - float(i) / n
			var a: Vector2 = to_local(_trail[i])
			var b: Vector2 = to_local(_trail[i + 1])
			draw_line(a, b, Color(trail_col.r, trail_col.g, trail_col.b, trail_col.a * f * 0.7), 2.5 * f)
	if spr:
		return
	match kind:
		"arrow":
			var head := Color(0.85, 0.88, 0.95)
			var flt := Color(0.9, 0.25, 0.2)
			match fx_kind:
				"od":
					head = Color(1.0, 0.65, 0.2)
				"altin":
					head = Color(1.0, 0.9, 0.45)
				"sel":
					flt = Color(0.4, 0.75, 1.0)
			draw_line(Vector2(-12, 0), Vector2(4, 0), Color(0.62, 0.42, 0.24), 1.5)
			draw_colored_polygon(PackedVector2Array([Vector2(4, -2), Vector2(9, 0), Vector2(4, 2)]), head)
			draw_line(Vector2(-12, 0), Vector2(-15, -3), flt, 1.5)
			draw_line(Vector2(-12, 0), Vector2(-15, 3), Color(0.95, 0.95, 0.95), 1.5)
			if fx_kind == "od":
				draw_circle(Vector2(7, 0), 2.5 + sin(_t * 30.0) * 0.6, Color(1.0, 0.5, 0.1, 0.6))
		"stone":
			draw_circle(Vector2.ZERO, 2.5, Color(0.6, 0.62, 0.68))
			draw_circle(Vector2(-0.8, -0.8), 1.0, Color(0.85, 0.87, 0.9))
		"feather":
			draw_colored_polygon(PackedVector2Array([Vector2(7, 0), Vector2(0, -2.5), Vector2(-8, -1), Vector2(-8, 1), Vector2(0, 2.5)]), Color(0.9, 0.9, 1.0))
			draw_line(Vector2(-8, 0), Vector2(6, 0), Color(0.5, 0.5, 0.7), 1.0)
		"wave":
			var k := clampf(_t / 1.2, 0.0, 1.0)
			for i in 3:
				var r := 10.0 + i * 6.0 + k * 14.0
				draw_arc(Vector2(-r, 0), r, -0.7, 0.7, 10, Color(0.7, 0.9, 1.0, 0.8 - i * 0.2), 2.0)
		"spore":
			var pulse := 1.0 + sin(_t * 18.0) * 0.2
			draw_circle(Vector2.ZERO, 4.5 * pulse, Color(0.45, 0.9, 0.15, 0.35))
			draw_circle(Vector2.ZERO, 2.6, Color(0.85, 1.0, 0.35))
		"eagle":
			draw_colored_polygon(PackedVector2Array([Vector2(8, 0), Vector2(-4, -8), Vector2(-1, 0), Vector2(-4, 8)]), Color(0.5, 0.95, 1.2, 0.85))
		"root":
			draw_rect(Rect2(-3, -10, 6, 10), Color(0.45, 0.3, 0.2))
		_:
			draw_circle(Vector2.ZERO, 3.0, Color(1, 1, 1))
