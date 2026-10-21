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
var arrow_variant := ""      # "" ise fx_kind / takıma göre seçilir
var _embed_t := -1.0         # duvara saplandı: titreşir, sonra söner
var _wobble := 0
## stil v2: mürekkep-cel mermi sprite'ı (SusV2 atlası); serbest açıyla döner, iz kenar yumuşatmalı fırça çizgisi
var ink_spr: Sprite2D
var hit_pad := Vector2(3.0, 3.0)   # v25: düşman vuruş kutusu bu kadar büyütülür (kopuz dalgası dikeyde geniş)
var unsur := ""                    # v25: oyuncu fırlatması / okunun unsuru (OkIz rengi)
var _iz_node: Node2D = null        # v25: OkIz (stil v2 ince mürekkep izi)
const IZ_KINDS := ["javelin", "feather", "stone", "stone_big", "axe"]
const INK_KIND := {"stone": ["tas", true], "stone_big": ["tas_buyuk", true], "ice": ["buz", true], "fireball": ["ates_topu", false],
	"spore": ["spor", false], "curse": ["lanet", false], "feather": ["tuy", true], "eagle": ["kartal_ruhu", false],
	"wave": ["dalga", false], "ground_wave": ["yer_dalgasi", false], "root": ["kok", true]}


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
		m.shader = Data.INK_SHADER
		spr.material = m
		add_child(spr)
	if kind == "arrow":
		if arrow_variant == "":
			arrow_variant = "dusman" if team != "p" else {"altin": "altin", "od": "od", "sel": "sel", "kizil": "kizil"}.get(fx_kind, "normal")
		ink_spr = SusV2.sprite("ok_" + arrow_variant, true)
		if ink_spr:
			add_child(ink_spr)
			_set_arrow_frame(velocity.angle())
	elif spr == null and INK_KIND.has(kind):
		ink_spr = SusV2.sprite(INK_KIND[kind][0], INK_KIND[kind][1], Color(1.5, 1.4, 1.3))
		if ink_spr:
			add_child(ink_spr)
			if kind == "wave":
				ink_spr.modulate = Color(0.75, 0.92, 1.2)
			elif kind == "ground_wave":
				ink_spr.modulate = get_meta("col", Color(1.0, 0.8, 0.5))
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
	# v25: oyuncunun fırlattığı silah (cirit, tüy, taş, balta) ince unsur renkli mürekkep iziyle uçar (eski kalın çizgi yerine)
	if team == "p" and kind in IZ_KINDS:
		_iz_node = OkIz.attach(self, unsur, 0.45 if kind in ["javelin", "stone_big"] else 0.36, 24.0 if kind == "javelin" else 3.0)
		if _iz_node:
			trail_col = Color(0, 0, 0, 0)


func iz_flying() -> bool:
	## OkIz: mermi hâlâ uçuyor mu (saplanınca / gömülünce iz erir)
	return _embed_t < 0.0 and _stuck_t < 0.0


func _set_arrow_frame(ang: float, nudge := 0) -> void:
	if ink_spr and kind == "arrow":
		ink_spr.rotation = ang + nudge * 0.07


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
	if ink_spr and is_instance_valid(e):
		var s3 := ink_spr.duplicate() as Sprite2D
		s3.z_index = 5
		e.add_child(s3)
		s3.global_position = global_position + velocity.normalized() * 4.0
		s3.global_rotation = velocity.angle()
		var tw3 := s3.create_tween()
		tw3.tween_interval(0.9)
		tw3.tween_property(s3, "modulate:a", 0.0, 0.35)
		tw3.tween_callback(s3.queue_free)


func _physics_process(delta: float) -> void:
	if Prof.on:
		var t0 := Time.get_ticks_usec()
		_physics_process_ic(delta)
		Prof.ekle(&"mermi", t0)
		return
	_physics_process_ic(delta)


func _physics_process_ic(delta: float) -> void:
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
	elif kind in ["javelin", "eagle", "spore", "feather", "wave", "curse", "kargi", "ag"]:
		rotation = velocity.angle()
	elif kind == "orak":
		rotation += delta * 20.0 * (signf(velocity.x) if velocity.x != 0.0 else 1.0)
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
			if e.hurt_rect().grow_individual(hit_pad.x, hit_pad.y, hit_pad.x, hit_pad.y).has_point(global_position):
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
			if hit and on_hit.is_valid():
				on_hit.call(pl)   # v39: düşman mermisinin isabet kancası (Ağ Ana ağı)
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
	## v23: düşman mermisi oyuncuya güdümlenir (eskiden en yakın DÜŞMANA, çoğu kez atanın kendisine dönüyordu)
	if team != "p":
		var pl: Node = level.player if level else null
		if pl and not pl.dead and global_position.distance_to(pl.center()) < 320.0:
			return pl
		return null
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


func _ink_tick() -> void:
	match kind:
		"ice", "fireball":
			ink_spr.global_rotation = velocity.angle() if velocity.length() > 1.0 else ink_spr.global_rotation
		"ground_wave":
			ink_spr.flip_h = velocity.x < 0.0
			ink_spr.scale = Vector2(0.25, 0.25 * (0.75 + 0.35 * absf(sin(_t * 14.0))))
			ink_spr.position.y = 14.0
		"spore", "curse":
			var k := 0.25 * (1.0 + sin(_t * 18.0) * 0.12)
			ink_spr.scale = Vector2(k, k)


func _draw() -> void:
	if ink_spr:
		_ink_tick()
	# v2 iz: kenar yumuşatmalı, kuyruğa doğru incelen ve solan fırça çizgisi
	if trail_col.a > 0.0 and _trail.size() >= 2:
		var n2 := _trail.size()
		var prev2: Vector2 = to_local(_trail[0])
		for i in range(1, n2):
			var cur2: Vector2 = to_local(_trail[i])
			var f2 := 1.0 - float(i) / n2
			draw_line(prev2, cur2, Color(trail_col.r, trail_col.g, trail_col.b, trail_col.a * f2 * 0.8), (2.2 if fx_kind != "" else 1.4) * f2 + 0.3, true)
			prev2 = cur2
	if ink_spr == null and spr == null:
		_ink_body()
	if team == "p" and SPIN_R.has(kind) and iz_flying():
		_spin_smear()


## v31 dönen fırlatmanın leke yayı (balta, sapan / mancınık taşı): sprite'ın arkasında, dönüşün ardında kalan iki
## karşılıklı hilal (hareket bulanıklığı yerine mürekkep: kalın baş, kuru incelen kuyruk; koyu kontur + açık metal öz).
## Düğümle birlikte döner (yerel uzay), sprite çocuk olduğundan onun altında çizilir.
const SPIN_R := {"axe": 12.0, "stone": 5.5, "stone_big": 13.0}


func _spin_smear() -> void:
	var R := float(SPIN_R[kind])
	var sg := signf(velocity.x) if absf(velocity.x) > 1.0 else 1.0
	var span := 1.5 if kind == "axe" else 1.1
	for h in 2:
		var a0 := float(h) * PI
		var pts := SilahCizim.yay(Vector2.ZERO, Vector2(R, R), a0, a0 - sg * span, 10)
		var ws := PackedFloat32Array()
		for i in pts.size():
			var k := float(i) / float(pts.size() - 1)
			ws.append(R * (0.32 if kind == "axe" else 0.4) * pow(1.0 - k, 1.3) + 0.05)
		SilahCizim.serit(self, pts, ws, Color(0.05, 0.04, 0.06, 0.55), Color(0.05, 0.04, 0.06, 0.0))
		var wc := PackedFloat32Array()
		for v in ws:
			wc.append(v * 0.4)
		SilahCizim.serit(self, pts, wc, Color(0.92, 0.9, 0.86, 0.55), Color(0.92, 0.9, 0.86, 0.0))


func _ink_body() -> void:
	## v2: mürekkep atlasında karşılığı olmayan mermi gövdeleri (lanet, varsayılan) yumuşak mürekkep lekesi
	match kind:
		"curse":
			var pulse := 1.0 + sin(_t * 20.0) * 0.25
			InkDraw.soft(self, Vector2.ZERO, 5.0 * pulse, Color(0.6, 0.2, 0.9, 0.45))
			InkDraw.blot(self, Vector2.ZERO, 2.6, Color(0.85, 0.45, 1.0), int(_t * 8.0))
			InkDraw.star(self, Vector2.ZERO, 2.2, _t * 6.0, Color(1.0, 0.85, 1.0))
		"arrow":
			pass
		"orak":
			# v39 Aldaraş'ın dönen tunç orağı: mürekkep kontur + tunç hilal + parıltı
			for s in [0.0, PI]:
				draw_arc(Vector2.ZERO, 9.0, s - 0.2, s + 2.2, 10, Color(0.06, 0.04, 0.05), 5.0, true)
				draw_arc(Vector2.ZERO, 9.0, s - 0.1, s + 2.0, 10, Color(0.95, 0.68, 0.32), 2.6, true)
			InkDraw.soft(self, Vector2.ZERO, 6.0, Color(1.0, 0.75, 0.35, 0.35))
		"kargi":
			# v39 hayalet / ateş ciridi: ışık mızrağı
			var kc: Color = get_meta("col", Color(0.5, 1.0, 0.95))
			draw_line(Vector2(-16, 0), Vector2(12, 0), Color(0.05, 0.04, 0.06, 0.9), 4.0, true)
			draw_line(Vector2(-15, 0), Vector2(11, 0), kc, 2.0, true)
			draw_colored_polygon(PackedVector2Array([Vector2(10, -3.5), Vector2(19, 0), Vector2(10, 3.5)]), kc.lightened(0.3))
			InkDraw.soft(self, Vector2(10, 0), 6.0, Color(kc.r, kc.g, kc.b, 0.4))
		"ag":
			# v39 Ağ Ana'nın ağ yumağı: ışınsal teller + halkalar
			InkDraw.soft(self, Vector2.ZERO, 8.0, Color(0.95, 0.95, 0.9, 0.3))
			for i in 8:
				var a := float(i) / 8.0 * TAU + _t * 2.0
				draw_line(Vector2.ZERO, Vector2.from_angle(a) * 8.0, Color(0.95, 0.95, 0.9, 0.9), 1.0, true)
			draw_arc(Vector2.ZERO, 4.0, 0.0, TAU, 12, Color(0.95, 0.95, 0.9, 0.8), 1.0, true)
			draw_arc(Vector2.ZERO, 7.0, 0.0, TAU, 14, Color(0.95, 0.95, 0.9, 0.6), 1.0, true)
		_:
			InkDraw.soft(self, Vector2.ZERO, 4.0, Color(1, 1, 1, 0.5))
			InkDraw.blot(self, Vector2.ZERO, 2.6, Color(1, 1, 1), 2)
