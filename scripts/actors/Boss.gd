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
	anim.play("howl" if kind == "kara_boru_han" else "rage")
	aggro = true
	cd = 1.2
	if level:
		var lc: Color = CFG.get(kind, {}).get("color", Color(1.0, 0.3, 0.5))
		level.add_light(Vector2(0, -size.y * 0.6), lc, 260.0, 1.1, self)


func _ai_custom(delta: float, player: Node, to_p: Vector2, dist: float) -> void:
	if kind == "kara_boru_han":
		_ai_kbh(delta, player, to_p, dist)
	else:
		_ai_gen(delta, player, to_p, dist)


func _ai_kbh(delta: float, player: Node, to_p: Vector2, dist: float) -> void:
	var hpk := hp / max_hp
	var new_phase := 1 if hpk > 0.66 else (2 if hpk > 0.33 else 3)
	if new_phase != phase:
		phase = new_phase
		_enter_phase_kbh()
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
				_pick_move_kbh(player, to_p, dist)
		"windup":
			anim.play("windup")
			velocity.x = move_toward(velocity.x, 0.0, 900 * delta)
			st -= delta
			if st <= 0.0:
				_do_move_kbh(player, to_p, dist)
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


func _enter_phase_kbh() -> void:
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


func _pick_move_kbh(player: Node, to_p: Vector2, dist: float) -> void:
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


func _do_move_kbh(player: Node, to_p: Vector2, dist: float) -> void:
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


# ================================================================ ortak boss motoru (Tepegöz, Şahmeran Ana, Yelbegen, Erlik Han)
## Hamleler: sweep (önde dev savuruş), stomp (oyuncuya sıçrayıp ezme + iki yana yer dalgası), volley (yelpaze mermi),
## wave (yere vurup iki yana yürüyen dalga), rain (gökten işaretli yağmur), summon (yardımcı çağırma), charge (hücum).
const CFG := {
	"tepegoz": {"color": Color(1.0, 0.75, 0.35), "proj": "stone_big", "rain": "stone_big",
		"summon": ["kurgan_bekcisi", "kara_kus_yavrusu"], "names": ["", "GÖZÜ KIZARIYOR", "DAĞ GİBİ ÖFKE"],
		"phases": [["sweep", "sweep", "stomp", "volley"], ["sweep", "stomp", "volley", "wave", "summon"], ["stomp", "wave", "volley", "sweep", "rain", "stomp"]],
		"roar": "agac_olum", "reach": 120.0},
	"sahmeran_ana": {"color": Color(0.5, 1.0, 0.5), "proj": "spore", "rain": "spore",
		"summon": ["kan_yarasasi", "magara_pususu"], "names": ["", "ZEHİR KABARIYOR", "KRALİÇENİN ÖFKESİ"],
		"phases": [["volley", "sweep", "charge"], ["volley", "wave", "rain", "summon", "charge"], ["charge", "rain", "wave", "volley", "sweep"]],
		"roar": "hayalet_olum", "reach": 110.0},
	"yelbegen": {"color": Color(0.6, 0.9, 1.0), "proj": "ice", "rain": "ice",
		"summon": ["ayaz_kurdu", "kaf_kartali"], "names": ["", "ÜÇ BAŞ UYANIYOR", "KAF FIRTINASI"],
		"phases": [["sweep", "volley", "stomp"], ["rain", "volley", "sweep", "wave", "summon"], ["stomp", "rain", "wave", "volley", "charge"]],
		"roar": "uluma", "reach": 130.0},
	"erlik_han": {"color": Color(1.0, 0.45, 0.2), "proj": "fireball", "rain": "fireball",
		"summon": ["kayip_ruh", "kor_pususu"], "names": ["", "TAMU KAYNIYOR", "ERLİK'İN GAZABI"],
		"phases": [["sweep", "volley", "wave"], ["rain", "sweep", "wave", "summon", "volley"], ["rain", "wave", "stomp", "volley", "charge", "sweep"]],
		"roar": "kut_donusum", "reach": 120.0},
}


func _cfg() -> Dictionary:
	return CFG.get(kind, CFG["tepegoz"])


func _ai_gen(delta: float, player: Node, to_p: Vector2, dist: float) -> void:
	var cf := _cfg()
	var hpk := hp / max_hp
	var new_phase := 1 if hpk > 0.66 else (2 if hpk > 0.33 else 3)
	if new_phase != phase:
		phase = new_phase
		_enter_phase_gen()
	var spd_mult := 1.0 + 0.2 * (phase - 1)
	match state:
		"intro":
			velocity.x = 0.0
			intro_t -= delta
			anim.play("rage")
			if Engine.get_physics_frames() % 10 == 0:
				FX.ring(center(), 60 + 20 * (2.2 - intro_t), Color(cf["color"], 0.5), 0.35)
			if intro_t <= 0.0:
				state = "chase"
				cd = 0.5
				Ses.play(String(cf["roar"]), 0.0, 0.7)
				Game.shake(5.0)
		"idle", "chase":
			state = "chase"
			_face(to_p)
			var tgt := facing * speed * spd_mult
			if _wall_or_ledge() or dist < float(cf["reach"]) * 0.7:
				tgt = 0.0
			velocity.x = move_toward(velocity.x, tgt, 500 * delta)
			anim.play("walk" if absf(velocity.x) > 10.0 else "idle")
			anim.speed = clampf(absf(velocity.x) / maxf(1.0, speed), 0.6, 1.4) if absf(velocity.x) > 10.0 else 1.0
			if Engine.get_physics_frames() % 18 == 0 and absf(velocity.x) > 10.0 and is_on_floor():
				Game.shake(1.2)
				FX.dust(global_position + Vector2(facing * 14, 0), Vector2(-facing, -0.4), 3, 0.34)
			if cd <= 0.0 and player:
				_pick_gen(to_p, dist)
		"windup":
			velocity.x = move_toward(velocity.x, 0.0, 900 * delta)
			st -= delta
			if Engine.get_physics_frames() % 4 == 0:
				FX.burst(center() + Vector2(facing * 20, -20), cf["color"], 2, 40, 0.4, 0.18, -40, true)
			if st <= 0.0:
				_do_gen(player, to_p, dist)
		"sweep":
			anim.play("strike")
			velocity.x = move_toward(velocity.x, 0.0, 700 * delta)
			st -= delta
			if st <= 0.0:
				state = "recover"
				st = 0.5
		"leap":
			anim.play("slam")
			st += delta
			if Engine.get_physics_frames() % 2 == 0:
				FX.ghost(anim.base, Color(cf["color"], 0.3), 0.2)
			if is_on_floor() and st > 0.2:
				_land_gen(player)
		"charge":
			anim.play("walk")
			anim.speed = 2.2
			velocity.x = move_toward(velocity.x, facing * 420.0, 1600 * delta)
			st -= delta
			if Engine.get_physics_frames() % 2 == 0:
				FX.ghost(anim.base, Color(cf["color"], 0.3), 0.18)
				FX.dust(global_position + Vector2(-facing * 20, 0), Vector2(-facing, -0.4), 2, 0.3)
			if player and not player.dead and not _did_hit and hurt_rect().grow(4).intersects(player.hurt_rect()):
				_did_hit = true
				if player.take_hit(dmg * 1.2, self) and player.has_method("shove"):
					player.shove(Vector2(facing * 380.0, -240.0))
				Game.hitstop(0.06)
			if is_on_wall() or st <= 0.0:
				anim.speed = 1.0
				contact = false
				if is_on_wall():
					Game.shake(7.0)
					FX.impact_sprite("blunt", global_position + Vector2(facing * size.x * 0.5, -size.y * 0.5), Vector2(facing, 0), cf["color"], 1.6)
					Ses.play("darbe_cekic", -2.0, 0.8)
					stun(1.2)
				state = "recover"
				st = 0.8
		"cast":
			anim.play("cast")
			velocity.x = move_toward(velocity.x, 0.0, 900 * delta)
			st -= delta
			if st <= 0.0:
				state = "recover"
				st = 0.4
		"recover":
			anim.play("idle")
			anim.speed = 1.0
			velocity.x = move_toward(velocity.x, 0.0, 700 * delta)
			st -= delta
			if st <= 0.0:
				state = "chase"
				cd = randf_range(0.7, 1.3) / spd_mult
	if phase >= 3 and Engine.get_physics_frames() % 6 == 0:
		FX.burst(center() + Vector2(randf_range(-size.x * 0.5, size.x * 0.5), randf_range(-size.y * 0.5, size.y * 0.3)), cf["color"], 1, 30, 0.6, 0.18, -60, true)


func _enter_phase_gen() -> void:
	var cf := _cfg()
	phase_changed.emit(phase)
	Game.slowmo(0.35, 0.45)
	Game.shake(7.0)
	FX.ring(center(), 150, cf["color"], 0.6)
	FX.flash_light(center(), cf["color"], 360.0, 2.2, 0.5)
	Ses.play(String(cf["roar"]), 0.0, 0.65)
	FX.text(center() + Vector2(0, -size.y - 30), String(cf["names"][phase - 1]), Color(cf["color"]).lightened(0.3), 12)
	state = "cast"
	anim.play("rage")
	st = 1.0
	if level and level.has_method("flash_white"):
		level.flash_white(0.2)


func _pick_gen(to_p: Vector2, dist: float) -> void:
	var cf := _cfg()
	var pool: Array = (cf["phases"][phase - 1] as Array).duplicate()
	if dist < float(cf["reach"]) and absf(to_p.y) < 80.0:
		pool += ["sweep", "sweep"]
	next_move = pool[randi() % pool.size()]
	_face(to_p)
	state = "windup"
	_windup_sfx()
	var wt: Dictionary = {"sweep": 0.65, "stomp": 0.55, "volley": 0.6, "wave": 0.7, "rain": 0.6, "summon": 0.6, "charge": 0.8}
	st = float(wt.get(next_move, 0.6)) / (1.0 + 0.15 * (phase - 1))
	anim.play("windup" if next_move in ["sweep", "stomp", "wave", "charge"] else "cast", true)
	warn.visible = true


func _do_gen(player: Node, to_p: Vector2, dist: float) -> void:
	var cf := _cfg()
	if OS.get_cmdline_user_args().has("--bosslog"):
		print("BOSS %s faz=%d hamle=%s can=%d/%d" % [kind, phase, next_move, int(hp), int(max_hp)])
	var col: Color = cf["color"]
	match next_move:
		"sweep":
			state = "sweep"
			st = 0.45
			anim.play("strike", true)
			var R := float(cf["reach"])
			var box := Rect2(global_position.x + (0.0 if facing > 0 else -R), global_position.y - size.y * 1.05, R, size.y * 1.05)
			FX.slash_sprite("arc_heavy", center() + Vector2(facing * R * 0.3, -10), 0.2 * facing, Vector2(R / 55.0 * facing, R / 55.0), col)
			FX.dust(global_position + Vector2(facing * R * 0.6, 0), Vector2(facing, -0.5), 8, 0.36)
			Ses.play("savur_dev", -1.0, 0.75)
			Game.shake(4.0)
			Game.kick(Vector2(facing, 0), 4.0)
			velocity.x = facing * 140.0
			if player and box.intersects(player.hurt_rect()):
				if player.take_hit(dmg * 1.1, self) and player.has_method("shove"):
					player.shove(Vector2(facing * 300.0, -200.0))
		"stomp":
			state = "leap"
			st = 0.0
			var dx: float = clampf(to_p.x, -300.0, 300.0)
			velocity = Vector2(dx * 1.6, -560.0)
			contact = true
			_did_hit = false
			FX.dust(global_position, Vector2.UP, 10, 0.4)
			Ses.play("sicrayis", -2.0, 0.6)
		"volley":
			state = "cast"
			st = 0.6
			anim.play("cast", true)
			var n := 3 + phase * 2
			var hand := center() + Vector2(facing * size.x * 0.6, -size.y * 0.3)
			for k in n:
				var spread := (float(k) / maxf(1.0, n - 1) - 0.5) * 0.9
				var ang: float = ((player.center() - hand).angle() if player else (0.0 if facing > 0 else PI)) + spread
				_shoot(String(cf["proj"]), hand, Vector2(cos(ang), sin(ang)) * 260.0 + Vector2(0, -60), col)
			Ses.play("buyu", -2.0, 0.7)
			FX.flash_light(hand, col, 140.0, 1.6, 0.2)
		"wave":
			state = "cast"
			st = 0.7
			anim.play("slam", true)
			Game.shake(6.0)
			Ses.play("sarsinti", -1.0, 0.8)
			FX.anim("earth_rupture", global_position + Vector2(facing * 30, 0), 0.0, 1.4, col, false)
			for sgn in [-1, 1]:
				_ground_wave(sgn, col)
			if phase >= 3:
				get_tree().create_timer(0.45).timeout.connect(_double_wave)
		"rain":
			state = "cast"
			st = 0.9
			anim.play("cast", true)
			Ses.play("buyu", -2.0, 0.6)
			var px: float = player.global_position.x if player else global_position.x
			var n2 := 4 + phase * 2
			for k in n2:
				var x: float = px + (randf_range(-160.0, 160.0) if k > 0 else 0.0)
				var gy: float = level.ground_y_below(Vector2(x, global_position.y - 200.0), 400.0) if level else global_position.y
				if gy < 0.0:
					gy = global_position.y
				level.telegraph_ground(Vector2(x, gy), 0.8)
				get_tree().create_timer(0.8 + k * 0.12).timeout.connect(_rain_drop.bind(x, gy))
		"summon":
			state = "cast"
			st = 0.8
			anim.play("cast", true)
			Ses.play(String(cf["roar"]), -4.0, 0.9)
			var pool: Array = cf["summon"]
			for k in (2 if phase < 3 else 3):
				var e: Enemy = level.spawn_enemy(pool[k % pool.size()], global_position + Vector2(-facing * (70 + k * 40), -10))
				e.aggro = true
				FX.anim("smoke_puff", e.center(), 0.0, 1.0, col, false)
				FX.ring(e.center(), 24, col, 0.3)
		"charge":
			state = "charge"
			st = 1.6
			contact = true
			_did_hit = false
			_face(to_p)
			Ses.play("savur_dev", -2.0, 0.6)
			FX.ring(center(), 40, col, 0.3)


func _double_wave() -> void:
	if is_instance_valid(self) and not dead:
		for sgn in [-1, 1]:
			_ground_wave(sgn, _cfg()["color"])


func _rain_drop(x: float, gy: float) -> void:
	if is_instance_valid(self) and not dead and level:
		_shoot(String(_cfg()["rain"]), Vector2(x, gy - 260.0), Vector2(0, 420.0), _cfg()["color"])


func _land_gen(player: Node) -> void:
	var cf := _cfg()
	var col: Color = cf["color"]
	state = "recover"
	st = 0.8
	contact = false
	vis_scale = Vector2(1.3, 0.75)
	Game.shake(9.0)
	Game.kick(Vector2.DOWN, 7.0)
	Ses.play("sarsinti", 0.0, 0.75)
	FX.anim("earth_rupture", global_position, 0.0, 1.8, col, false)
	FX.ring(global_position, 110, col, 0.4, 0.3)
	FX.shock_line(global_position, 110.0, Color(col, 0.7))
	FX.dust(global_position, Vector2.UP, 14, 0.42)
	if level and level.has_method("flash_white"):
		level.flash_white(0.2)
	if player and absf(player.global_position.x - global_position.x) < 120.0 and player.is_on_floor():
		if player.take_hit(dmg * 1.2, self) and player.has_method("shove"):
			player.shove(Vector2(signf(player.global_position.x - global_position.x) * 320.0, -280.0))
	if phase >= 2:
		for sgn in [-1, 1]:
			_ground_wave(sgn, col)


func _shoot(k: String, pos: Vector2, vel: Vector2, col: Color) -> void:
	var p := Projectile.new()
	p.team = "e"
	p.kind = k
	p.damage = dmg * 0.6
	p.source = self
	p.position = pos
	p.velocity = vel
	p.gravity = 0.0 if k == "spore" else (380.0 if k in ["stone_big", "ice"] else 120.0)
	p.homing = 0.6 if k == "spore" else 0.0
	p.life = 3.5
	p.trail_col = Color(col, 0.6)
	level.add_projectile(p)


func _ground_wave(sgn: int, col: Color) -> void:
	var p := Projectile.new()
	p.team = "e"
	p.kind = "ground_wave"
	p.damage = dmg * 0.7
	p.source = self
	p.position = global_position + Vector2(sgn * size.x * 0.6, -14)
	p.velocity = Vector2(sgn * 280.0, 0)
	p.life = 2.4
	p.set_meta("col", col)
	level.add_projectile(p)
