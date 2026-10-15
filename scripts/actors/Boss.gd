class_name Boss
extends Enemy
## Kara Börü Han: Ötüken'in boss'u. Üç evre:
##   1 (can > %66): dev hamle (lunger), uluma -> iki Erlik tazısı çağırır, ulurken yakındaysan sersemlersin
##   2 (can %66-%33): sırtındaki bozgun kristalleri fırlar (yay çizen taş mermiler), gökten çakma (işaretli yere iner)
##   3 (can < %33): gölgesi ayrılır (hayalet kopya, %18 can), hızlanır; tüm hamleler daha sık
## Can çubuğu HUD'da; ölünce arena kapısı açılır (Level.on_boss_died).

signal phase_changed(p: int)

var phase := 1
var move_t := 0.0
var next_move := ""
var shadow_done := false
var intro_t := 2.2
var howl_t := 0.0
var _rage_fx := 0.0


func _ready() -> void:
	super._ready()
	is_boss = true
	elite = false
	_label.text = String(def.get("name", "KARA BÖRÜ HAN")).to_upper()
	_label.visible = false
	state = "intro"
	anim.play("howl")
	aggro = true
	cd = 1.2
	if level:
		level.add_light(Vector2(0, -36), Color(1.0, 0.3, 0.5), 220.0, 1.1, self)


func _ai_custom(delta: float, player: Node, to_p: Vector2, dist: float) -> void:
	var hpk := hp / max_hp
	var new_phase := 1 if hpk > 0.66 else (2 if hpk > 0.33 else 3)
	if new_phase != phase:
		phase = new_phase
		_enter_phase()
	var spd_mult := 1.0 + 0.25 * (phase - 1)
	match state:
		"intro":
			velocity.x = 0.0
			intro_t -= delta
			anim.play("howl")
			if intro_t <= 0.0:
				state = "chase"
				cd = 0.6
		"idle", "chase":
			state = "chase"
			_face(to_p)
			var tgt := facing * speed * spd_mult
			if _wall_or_ledge() or dist < 70.0:
				tgt = 0.0
			velocity.x = move_toward(velocity.x, tgt, 700 * delta)
			anim.play("run" if absf(velocity.x) > 10.0 else "idle")
			if cd <= 0.0 and player:
				_pick_move(player, to_p, dist)
		"windup":
			anim.play("windup")
			velocity.x = move_toward(velocity.x, 0.0, 900 * delta)
			st -= delta
			if st <= 0.0:
				_do_move(player, to_p, dist)
		"leap":
			anim.play("leap")
			st += delta
			if Engine.get_physics_frames() % 2 == 0:
				FX.ghost(anim.base, Color(0.8, 0.2, 0.5, 0.35), 0.2)
			if is_on_floor() and st > 0.15:
				state = "recover"
				st = 0.6
				contact = false
				vis_scale = Vector2(1.25, 0.8)
				FX.dust(global_position, Vector2.UP, 10, 0.4)
				FX.shock_line(global_position, 60.0, Color(0.5, 0.4, 0.45, 0.7))
				Game.shake(5.0)
				Ses.play("sarsinti", -4.0)
		"howl":
			anim.play("howl")
			velocity.x = 0.0
			howl_t -= delta
			if Engine.get_physics_frames() % 6 == 0:
				FX.ring(center() + Vector2(facing * 30, -10), 40 + 30 * (1.0 - howl_t / 1.4), Color(1.0, 0.3, 0.5, 0.5), 0.3)
			if howl_t <= 0.0:
				state = "recover"
				st = 0.5
		"rise":
			# gökten çakma: yukarı sıçrar, oyuncunun üstüne işaret koyar, iner
			anim.play("leap")
			st -= delta
			velocity.y = -520.0 if st > 0.3 else 0.0
			velocity.x = 0.0
			anim.modulate.a = clampf(st / 0.4, 0.0, 1.0)
			if st <= 0.0:
				var tgt: Vector2 = player.global_position if player else global_position
				set_meta("slam_x", tgt.x)
				level.telegraph_ground(Vector2(tgt.x, tgt.y), 0.9)
				state = "fall_wait"
				st = 0.9
		"fall_wait":
			st -= delta
			velocity = Vector2.ZERO
			if st <= 0.0:
				global_position = Vector2(float(get_meta("slam_x")), global_position.y - 260.0)
				anim.modulate.a = 1.0
				state = "fall"
				velocity = Vector2(0, 700)
				contact = true
				_did_hit = false
		"fall":
			anim.play("slam")
			velocity.y = 720.0
			if is_on_floor():
				state = "recover"
				st = 0.9
				contact = false
				vis_scale = Vector2(1.4, 0.7)
				Game.shake(9.0)
				Game.kick(Vector2.DOWN, 7.0)
				Ses.play("sarsinti", 0.0, 0.8)
				FX.anim("earth_rupture", global_position, 0.0, 1.6, Color(1.0, 0.5, 0.6), false)
				FX.ring(global_position, 90, Color(1.0, 0.4, 0.5), 0.4, 0.3)
				FX.shock_line(global_position, 90.0, Color(0.5, 0.35, 0.4, 0.8))
				if level.has_method("flash_white"):
					level.flash_white(0.25)
				if player and absf(player.global_position.x - global_position.x) < 110.0 and player.is_on_floor():
					player.take_hit(dmg * 1.2, self)
					if player.has_method("shove"):
						player.shove(Vector2(signf(player.global_position.x - global_position.x) * 300.0, -260.0))
				# dört yana kristal parçası
				for k in 6:
					_crystal_shot(Vector2(-200.0 + k * 80.0, -360.0 - randf_range(0, 80)))
		"spikes":
			anim.play("rage")
			velocity.x = 0.0
			st -= delta
			if int(st * 10.0) % 2 == 0 and Engine.get_physics_frames() % 6 == 0:
				_crystal_shot(Vector2(randf_range(-260.0, 260.0), -420.0 + randf_range(-60, 60)))
			if st <= 0.0:
				state = "recover"
				st = 0.6
		"recover":
			anim.play("idle")
			velocity.x = move_toward(velocity.x, 0.0, 700 * delta)
			st -= delta
			if st <= 0.0:
				state = "chase"
				cd = randf_range(0.9, 1.6) / spd_mult
	if phase >= 3 and Engine.get_physics_frames() % 8 == 0:
		FX.burst(center() + Vector2(randf_range(-50, 50), randf_range(-30, 10)), Color(1.0, 0.3, 0.5), 1, 30, 0.6, 0.18, -60, true)


func _enter_phase() -> void:
	phase_changed.emit(phase)
	Game.slowmo(0.35, 0.4)
	Game.shake(6.0)
	FX.ring(center(), 120, Color(1.0, 0.35, 0.5), 0.6)
	FX.flash_light(center(), Color(1.0, 0.3, 0.5), 320.0, 2.2, 0.5)
	Ses.play("uluma", 0.0, 0.7)
	var names := ["", "", "BOZGUN UYANIYOR", "GÖLGE AYRILIYOR"]
	FX.text(center() + Vector2(0, -90), names[phase], Color(1.0, 0.5, 0.6), 11)
	state = "recover"
	st = 0.8
	if phase == 3 and not shadow_done:
		shadow_done = true
		_spawn_shadow()


func _pick_move(player: Node, to_p: Vector2, dist: float) -> void:
	var pool: Array = ["leap", "leap", "howl"]
	if phase >= 2:
		pool += ["spikes", "rise", "leap"]
	if phase >= 3:
		pool += ["rise", "spikes"]
	if dist < 110.0 and absf(to_p.y) < 50.0:
		pool += ["leap", "leap"]
	next_move = pool[randi() % pool.size()]
	_face(to_p)
	state = "windup"
	_windup_sfx()
	st = 0.6 if next_move == "leap" else 0.45
	if next_move == "howl":
		st = 0.3
	warn.visible = true


func _do_move(player: Node, to_p: Vector2, dist: float) -> void:
	match next_move:
		"leap":
			state = "leap"
			st = 0.0
			var dx: float = clampf(to_p.x, -260.0, 260.0)
			velocity = Vector2(dx * 2.2 + facing * 160.0, -330.0)
			contact = true
			_did_hit = false
			vis_scale = Vector2(0.8, 1.25)
			FX.dust(global_position, Vector2(-facing, -0.5), 8, 0.36)
			Ses.play("sicrayis", -2.0, 0.7)
		"howl":
			state = "howl"
			howl_t = 1.4
			Ses.play("uluma", 0.0, 0.75)
			FX.anim("hush_lock", center() + Vector2(facing * 24, -16), 0.0, 2.0, Color(1.0, 0.35, 0.5))
			Game.shake(4.0)
			# tazı çağır
			var n := 2 if phase < 3 else 3
			for k in n:
				var e: Enemy = level.spawn_enemy("kara_boru", global_position + Vector2(-facing * (60 + k * 40), -20))
				e.aggro = true
				FX.anim("smoke_puff", e.center(), 0.0, 0.8, Color(0.7, 0.2, 0.4), false)
			if player and dist < 150.0 and player.has_method("shove"):
				player.shove(Vector2(signf(to_p.x) * 240.0, -180.0))
				player.take_hit(dmg * 0.3, self)
		"spikes":
			state = "spikes"
			st = 1.6
			Ses.play("kut_donusum", -6.0, 1.3)
		"rise":
			state = "rise"
			st = 0.5
			Ses.play("sicrayis", -2.0, 0.6)
			FX.dust(global_position, Vector2.UP, 8, 0.36)


func _crystal_shot(vel: Vector2) -> void:
	var p := Projectile.new()
	p.team = "e"
	p.kind = "stone_big"
	p.damage = dmg * 0.7
	p.source = self
	p.position = center() + Vector2(-facing * 10, -24)
	p.velocity = vel
	p.gravity = 700.0
	p.life = 3.0
	p.trail_col = Color(1.0, 0.3, 0.7, 0.7)
	level.add_projectile(p)
	FX.burst(p.position, Color(1.0, 0.4, 0.8), 4, 60, 0.3, 0.16, -40, true)


func _spawn_shadow() -> void:
	var g: Enemy = level.spawn_enemy("kara_boru_han", global_position + Vector2(-facing * 90, 0))
	g.hp = max_hp * 0.18
	g.max_hp = g.hp
	g.decoy = false
	g.anim.modulate = Color(0.5, 0.3, 0.8, 0.6)
	g.dmg = dmg * 0.6
	g.set_meta("golge", true)
	if g is Boss:
		(g as Boss).state = "chase"
		(g as Boss).intro_t = 0.0
		(g as Boss).shadow_done = true
	FX.anim("void_implosion", g.center(), 0.0, 1.6, Color(0.6, 0.3, 0.9))
	Ses.play("hayalet_olum", -4.0, 0.6)


func _die(dir := 1.0, kb := 100.0, crit := false) -> void:
	if get_meta("golge", false):
		FX.anim("void_implosion", center(), 0.0, 1.4, Color(0.6, 0.3, 0.9))
		FX.soul(center(), Color(0.7, 0.4, 1.0), 24)
		dead = true
		remove_from_group("dusman")
		queue_free()
		return
	super._die(dir, kb, crit)
