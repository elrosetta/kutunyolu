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
var arrow_spr: Sprite2D      # 32 yönlü piksel ok (tools/artgen/arrows.py)
var arrow_variant := ""      # "" ise fx_kind / takıma göre seçilir
var _embed_t := -1.0         # duvara saplandı: titreşir, sonra söner
var _wobble := 0
const ARROW_DIRS := 32
const ARROW_VARIANTS := ["normal", "altin", "od", "sel", "kizil", "dusman"]
static var _arrow_tex: Texture2D


func _ready() -> void:
	z_index = 20
	if atlas_item != "" and Data.has_weapon_sprite(atlas_item):
		spr = Sprite2D.new()
		var wd: Dictionary = Data.weapon_sprite(atlas_item, atlas_mat)  # stil v2: mürekkep-cel atlas
		spr.texture = wd["tex"]
		spr.region_enabled = true
		spr.region_rect = wd["region"]
		spr.centered = false
		spr.offset = -(wd["pivot"] as Vector2)
		spr.scale = Vector2.ONE * float(wd["scale"])
		if kind == "javelin":
			spr.offset.x -= 10.0 / float(wd["scale"])
		var m := ShaderMaterial.new()
		m.shader = Data.INK_SHADER if wd["linear"] else Game.toon_shader
		spr.material = m
		add_child(spr)
	if kind == "arrow":
		if _arrow_tex == null:
			_arrow_tex = Data.tex("res://assets/fx/arrows.png")
		arrow_spr = Sprite2D.new()
		arrow_spr.texture = _arrow_tex
		arrow_spr.hframes = ARROW_DIRS
		arrow_spr.vframes = ARROW_VARIANTS.size()
		arrow_spr.texture_filter = CanvasItem.TEXTURE_FILTER_NEAREST
		add_child(arrow_spr)
		if arrow_variant == "":
			arrow_variant = "dusman" if team != "p" else {"altin": "altin", "od": "od", "sel": "sel", "kizil": "kizil"}.get(fx_kind, "normal")
		_set_arrow_frame(velocity.angle())
	if kind in ["fireball", "ground_wave"]:
		var gm2 := CanvasItemMaterial.new()
		gm2.blend_mode = CanvasItemMaterial.BLEND_MODE_ADD
		gm2.light_mode = CanvasItemMaterial.LIGHT_MODE_UNSHADED
		material = gm2
		if level and level.has_method("add_light"):
			level.add_light(Vector2.ZERO, Color(1.0, 0.55, 0.2) if kind == "fireball" else get_meta("col", Color(1, 0.8, 0.5)), 60.0, 0.8, self)
	if kind in ["spore", "eagle", "curse"]:
		var gm := CanvasItemMaterial.new()
		gm.blend_mode = CanvasItemMaterial.BLEND_MODE_ADD
		gm.light_mode = CanvasItemMaterial.LIGHT_MODE_UNSHADED
		material = gm
	if kind == "spore":
		trail_col = Color(0.5, 1.0, 0.3, 0.6)
		if level and level.has_method("add_light"):
			level.add_light(Vector2.ZERO, Color(0.55, 1.0, 0.35), 50.0, 0.8, self)


func _set_arrow_frame(ang: float, nudge := 0) -> void:
	if arrow_spr == null:
		return
	var d := (int(roundf(fposmod(ang, TAU) / TAU * ARROW_DIRS)) + nudge + ARROW_DIRS) % ARROW_DIRS
	arrow_spr.frame = maxi(0, ARROW_VARIANTS.find(arrow_variant)) * ARROW_DIRS + d


func _embed(wall: bool) -> void:
	## Ok duvara saplanır: biraz içeri girer, birkaç kare titrer (kare kaydırma), 1,4 sn sonra söner.
	_embed_t = 0.0
	_wobble = 6
	position += velocity.normalized() * 3.0
	_trail.clear()
	if wall:
		Ses.play_at("ok_vurus_tahta" if randf() < 0.6 else "ok_vurus_tas", global_position, -6.0)
		FX.dust(global_position, -velocity.normalized(), 3, 0.2)
		FX.sparks(global_position, -velocity.normalized(), Color(1.0, 0.9, 0.7), 3, 90.0)


func _stick_into(e: Node) -> void:
	## Düşmanın gövdesine saplanan ok: düşmanla birlikte hareket eder, kısa süre sonra söner.
	if arrow_spr == null or not is_instance_valid(e):
		return
	var s2 := Sprite2D.new()
	s2.texture = arrow_spr.texture
	s2.hframes = arrow_spr.hframes
	s2.vframes = arrow_spr.vframes
	s2.frame = arrow_spr.frame
	s2.texture_filter = CanvasItem.TEXTURE_FILTER_NEAREST
	s2.z_index = 5
	e.add_child(s2)
	s2.global_position = (global_position + velocity.normalized() * 4.0).round()
	var tw := s2.create_tween()
	tw.tween_interval(0.9)
	tw.tween_property(s2, "modulate:a", 0.0, 0.35)
	tw.tween_callback(s2.queue_free)


func _physics_process(delta: float) -> void:
	_t += delta
	if _embed_t >= 0.0:
		_embed_t += delta
		if _wobble > 0 and Engine.get_physics_frames() % 2 == 0:
			_wobble -= 1
			_set_arrow_frame(velocity.angle(), (1 if _wobble % 2 == 0 else -1) if _wobble > 1 else 0)
		if _embed_t > 1.0:
			modulate.a = clampf(1.0 - (_embed_t - 1.0) / 0.4, 0.0, 1.0)
		if _embed_t > 1.4:
			queue_free()
		queue_redraw()
		return
	if _stuck_t >= 0.0:
		_stuck_t += delta
		var pl: Node = level.player
		if pl and pl.global_position.distance_to(global_position) < 22.0:
			if pl.sec_slot != "":
				pl.cd[pl.sec_slot] = 0.0
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
	if kind == "ground_wave":
		# zemine yapışık ilerler: önü duvar ise biter; altı boşsa aşağı iner
		if level.solid_at(Vector2(next.x + signf(velocity.x) * 8.0, position.y)):
			FX.dust(position, Vector2(-signf(velocity.x), -0.5), 4, 0.3)
			queue_free()
			return
		if not level.solid_at(Vector2(next.x, position.y + 18.0)):
			next.y += 6.0
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
			Ses.play_at("ok_vurus_tahta", global_position, -6.0)
			return
		if kind == "arrow":
			_embed(true)
			return
		FX.burst(position, Color(0.8, 0.75, 0.6), 4, 50, 0.25, 0.15, 200)
		queue_free()
		return
	position = next
	if kind == "arrow":
		_set_arrow_frame(velocity.angle())
	elif kind in ["javelin", "eagle", "spore", "feather", "wave", "curse"]:
		rotation = velocity.angle()
	elif kind in ["bomb", "pot", "stone", "ice", "stone_big"]:
		rotation += delta * 10.0
	elif kind == "axe":
		rotation += delta * 22.0 * signf(velocity.x)
	if trail_col.a > 0.0:
		_trail.push_front(global_position)
		if _trail.size() > (14 if fx_kind != "" else 9):
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
	if kind == "fireball" and int(_t * 60.0) % 2 == 0:
		FX.fire(global_position, 1, 0.3, 2.0)
	if kind == "ground_wave" and int(_t * 60.0) % 3 == 0:
		FX.dust(global_position + Vector2(0, 14), Vector2(-signf(velocity.x), -0.6), 1, 0.26)
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
					Ses.play("ok_vurus", -4.0, 1.0, 0.1, 0.03, global_position)
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
					if kind == "arrow":
						_stick_into(e)
					queue_free()
					return
	else:
		var pl: Node = level.player
		if pl and not pl.dead and pl.hurt_rect().grow(2.0).has_point(global_position):
			var src: Node = source if is_instance_valid(source) else null
			var hit: bool = pl.take_hit(damage, src, self)
			if hit:
				Ses.play("ok_vurus", -6.0, 0.8, 0.1, 0.03, global_position)
				if kind == "curse":
					FX.anim("arcane_parry", position, 0.0, 0.6, Color(0.85, 0.45, 1.0))
					Ses.play_at("kam_kahkaha", position, -8.0)
				elif kind == "spore":
					FX.anim("acid_splash", position, 0.0, 0.8, Color(0.7, 1.0, 0.4))
					if pl.has_method("apply_poison"):
						pl.apply_poison(3.0)
				elif kind == "fireball":
					FX.fire(position, 10, 0.4, 6.0)
					FX.anim("warm_explosion", position, 0.0, 0.6, Color(1.0, 0.7, 0.4))
				elif kind == "ice":
					FX.frost(position, 6)
					FX.anim("frost_nova", position, 0.0, 0.5, Color(0.7, 0.9, 1.0))
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
		# piksel iz: geçmiş konumlar boyunca tam sayı karelere oturan, kuyruğa doğru incelen/solan noktalar
		var n := _trail.size()
		var prev: Vector2 = to_local(_trail[0])
		for i in range(1, n):
			var cur: Vector2 = to_local(_trail[i])
			var f := 1.0 - float(i) / n
			var c := Color(trail_col.r, trail_col.g, trail_col.b, trail_col.a * f * 0.85)
			var steps := maxi(1, int(prev.distance_to(cur)))
			var sz := 2.0 if (f > 0.55 and fx_kind != "") else 1.0
			for k in steps:
				var q := prev.lerp(cur, float(k) / steps).round()
				draw_rect(Rect2(q - Vector2(sz, sz) * 0.5, Vector2(sz, sz)), c)
			prev = cur
	if fx_kind != "" and kind == "arrow" and _embed_t < 0.0:
		# uçta küçük parıltı çekirdeği
		draw_rect(Rect2((velocity.normalized() * 6.0).round() - Vector2(1, 1), Vector2(2, 2)), Color(trail_col, 0.9))
	if spr:
		return
	match kind:
		"arrow":
			pass
		"curse":
			var pulse := 1.0 + sin(_t * 20.0) * 0.25
			draw_circle(Vector2.ZERO, 5.0 * pulse, Color(0.6, 0.2, 0.9, 0.35))
			draw_circle(Vector2.ZERO, 2.6, Color(0.85, 0.45, 1.0))
			draw_rect(Rect2(-1, -1, 2, 2), Color(1.0, 0.85, 1.0))
		"arrow_old":
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
			# kuyruk: solan yeşil zerreler
			for i in _trail.size():
				var q: Vector2 = to_local(_trail[i])
				var f := 1.0 - float(i) / maxf(1.0, _trail.size())
				draw_circle(q, 1.0 + 2.5 * f, Color(0.5, 1.0, 0.3, 0.35 * f))
			draw_circle(Vector2.ZERO, 6.5 * pulse, Color(0.45, 0.9, 0.15, 0.2))
			draw_circle(Vector2.ZERO, 4.2 * pulse, Color(0.55, 1.0, 0.25, 0.5))
			draw_circle(Vector2.ZERO, 2.4, Color(0.9, 1.0, 0.6))
			for k in 3:
				var a := _t * 9.0 + k * TAU / 3.0
				draw_circle(Vector2(cos(a) * 6.0, sin(a) * 6.0), 1.0, Color(0.7, 1.0, 0.4, 0.8))
		"eagle":
			draw_colored_polygon(PackedVector2Array([Vector2(8, 0), Vector2(-4, -8), Vector2(-1, 0), Vector2(-4, 8)]), Color(0.5, 0.95, 1.2, 0.85))
		"root":
			draw_rect(Rect2(-3, -10, 6, 10), Color(0.45, 0.3, 0.2))
		"stone_big":
			# kaya: koyu taş, kenarda kristal parıltı (iz rengi)
			var pts := PackedVector2Array()
			for i in 7:
				var a := i * TAU / 7.0
				pts.append(Vector2(cos(a), sin(a)) * (6.0 + 1.5 * sin(a * 3.0)))
			draw_colored_polygon(pts, Color(0.38, 0.35, 0.36))
			draw_colored_polygon(PackedVector2Array([pts[0] * 0.5, pts[2] * 0.5, pts[4] * 0.4]), Color(0.55, 0.52, 0.5))
			if trail_col.a > 0.0:
				draw_circle(Vector2(2, -2), 1.5, Color(trail_col, 0.9))
		"ice":
			# buz sarkıtı: düşüş yönünde sivri
			var d := velocity.normalized()
			var n := Vector2(-d.y, d.x)
			draw_colored_polygon(PackedVector2Array([d * 9.0, n * 3.5 - d * 4.0, -d * 7.0, -n * 3.5 - d * 4.0]), Color(0.7, 0.92, 1.0))
			draw_colored_polygon(PackedVector2Array([d * 7.0, n * 1.2, -d * 3.0, -n * 1.2]), Color(0.95, 1.0, 1.0))
		"fireball":
			var pulse := 1.0 + sin(_t * 22.0) * 0.2
			draw_circle(Vector2.ZERO, 8.0 * pulse, Color(1.0, 0.35, 0.05, 0.25))
			draw_circle(Vector2.ZERO, 5.0 * pulse, Color(1.0, 0.6, 0.15, 0.7))
			draw_circle(Vector2.ZERO, 2.8, Color(1.0, 0.95, 0.7))
		"ground_wave":
			# yerden yükselen dalga: titreşen sütunlar
			var col: Color = get_meta("col", Color(1.0, 0.8, 0.5))
			for i in 5:
				var hh := 10.0 + 14.0 * absf(sin(_t * 14.0 + i * 1.3))
				draw_rect(Rect2(-10 + i * 4, 14 - hh, 3, hh), Color(col, 0.75 - i * 0.08))
			draw_rect(Rect2(-12, 12, 24, 2), Color(col.lightened(0.4), 0.9))
		_:
			draw_circle(Vector2.ZERO, 3.0, Color(1, 1, 1))
