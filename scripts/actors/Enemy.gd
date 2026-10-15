class_name Enemy
extends CharacterBody2D
## Ötüken düşmanları. Her yapay zekâ türü saldırıdan önce açıkça uyarır (titreme + "!").
## (Kimlikler eski adlarıyla kalır; görünen adlar data/world.json'da.)
##   lunger       Erlik Tazısı (kara_boru): koşar, çömelir, atılarak ısırır
##   flyer_ranged Çor Ruhu (cor): havada süzülür, buhurdan fenerinden zehirli spor savurur
##   brute        Kara İye (agac_iyesi): ağır yumruk + oyuncunun altından kök fırlatır
##   hopper       Balbal: uyanır, sekerek yaklaşır, taş kılıcını savurur; önden gelen vuruşları siper alır
##   illusionist  Kara Kam (arcura): uzak durur, iki hayalet kopya salar, arkana ışınlanıp lanet fırlatır
##   grabber      Gulyabani (surale): uzun kollarıyla yakalar, sersemletir, fırlatır; tuşlara basarak kurtulursun
## Sürü davranışı: ikinci tazı arkadan dolaşır; çor tependeyken dalış yapar; iye üç kök dalgası gönderir.

var kind := "kara_boru"
var sprite_kind := "kara_boru"  # çizilen temel yaratık (biyom reskinleri başka ada sahiptir)
var def: Dictionary
var anim: SpriteAnim
var hp := 30.0
var max_hp := 30.0
var dmg := 10.0
var speed := 90.0
var ai := "lunger"
var facing := -1
var state := "idle"
var st := 0.0
var cd := 1.0
var aggro := false
var dead := false
var elite := false
var is_boss := false
var flying := false
var heavy := false
var size := Vector2(20, 24)
var stun_t := 0.0
var root_t := 0.0
var freeze_t := 0.0
var burn_t := 0.0
var bleed := 0
var bleed_t := 0.0
var cursed_t := 0.0
var flash_t := 0.0
var hurt_t := 0.0
var _dot_t := 0.0
var home := Vector2.ZERO
var level: Node
var contact := false
var _did_hit := false
var hp_bar: Node2D
var warn: Label
var base_scale := Vector2.ONE
var vis_scale := Vector2.ONE
var launch_t := 0.0
var decoy := false    # Arçura hayaleti: tek vuruşta dağılır, ganimet düşürmez
var guard_t := 0.0    # Balbal siperi
var flank := 0        # kurt: 1 ise arkadan dolaşır
var grab_target: Node
var frost := 0        # Ayaz kılıcı don yükü (3'te donar)
var armor_break := 0  # Çivili topuz zırh kırığı (en çok 3)
var armor_mv := 8.0
var pulled_t := 0.0   # kement/zincirle çekildi (kritik penceresi)
var base_tint := Color(1, 1, 1)
var poison := 0       # zehir yığını (en çok 5)
var poison_t := 0.0
var overlay: StatusOverlay
var guard_hp := 0       # kalkanlı: kaç darbe daha siper tutar (0 -> sersemler)
var shell_t := 0.0      # tosbağa: kabukta geçen süre (dokunulmaz)
var elite_t := 0.0      # seçkin: kükreme sayacı
var elite_name := ""
var perch := Vector2.ZERO  # pusu: beklediği yer
var _label: Label
var _hidden := false     # gölge (stalker): görünmez
## Düşmana özgü sıçrantı rengi (tazı: kor; çor: zehir yeşili; iye: Erlik moru özsu; balbal: taş tozu; kam: lanet moru; gulyabani: ölü irin)
const BLOOD := {"kara_boru": Color(0.95, 0.42, 0.12), "cor": Color(0.55, 0.85, 0.2), "agac_iyesi": Color(0.6, 0.28, 0.72), "balbal": Color(0.6, 0.6, 0.66),
		"arcura": Color(0.7, 0.25, 0.9), "surale": Color(0.5, 0.55, 0.42), "bekci": Color(0.55, 0.5, 0.45), "tosbaga": Color(0.45, 0.6, 0.3), "kara_boru_han": Color(0.8, 0.1, 0.2)}


func blood_col() -> Color:
	return BLOOD.get(sprite_kind, Color(0.45, 0.12, 0.5))


func setup(k: String, is_elite: bool, tier: int) -> void:
	kind = k
	def = Data.enemy_def(k)
	sprite_kind = String(def.get("sprite", k))
	if sprite_kind == "":
		sprite_kind = k
	elite = is_elite
	var mult := 1.0 + 0.9 * tier
	max_hp = float(def.get("hp", 30)) * mult * (2.6 if elite else 1.0)
	hp = max_hp
	dmg = float(def.get("dmg", 10)) * (1.0 + 0.5 * tier) * (1.25 if elite else 1.0)
	speed = float(def.get("speed", 80))
	ai = String(def.get("ai", Data.enemy_def(sprite_kind).get("ai", "lunger")))
	if not (ai in ["lunger", "flyer_ranged", "brute", "hopper", "illusionist", "grabber", "pouncer", "shield", "charger", "turtle", "archer", "stalker", "diver", "walker"]) and not ai.begins_with("boss"):
		ai = String(Data.enemy_def(sprite_kind).get("ai", "lunger"))
	if ai == "walker":
		ai = "shield"
	match sprite_kind:
		"bekci":
			size = Vector2(26, 58)
			heavy = true
			guard_hp = 3
		"tosbaga":
			size = Vector2(58, 30)
			heavy = true
		"kara_boru_han":
			size = Vector2(120, 66)
			heavy = true
			is_boss = true
		"kara_boru":
			size = Vector2(34, 22)
		"cor":
			size = Vector2(22, 34)
			flying = true
		"agac_iyesi":
			size = Vector2(34, 74)
			heavy = true
		"balbal":
			size = Vector2(22, 46)
			heavy = true
		"arcura":
			size = Vector2(18, 30)
		"surale":
			size = Vector2(28, 62)
			heavy = true


func _ready() -> void:
	add_to_group("dusman")
	collision_layer = Game.LAYER_ENEMY
	collision_mask = Game.LAYER_WORLD | Game.LAYER_PLATFORM
	floor_snap_length = 6.0
	var shape := RectangleShape2D.new()
	shape.size = size
	var cs := CollisionShape2D.new()
	cs.shape = shape
	cs.position = Vector2(0, -size.y / 2.0)
	add_child(cs)
	anim = SpriteAnim.new()
	add_child(anim)
	anim.setup(sprite_kind)
	if def.has("tint"):
		var tt: Array = def["tint"]
		base_tint = Color(tt[0], tt[1], tt[2])
		anim.set_tint(base_tint)
	if sprite_kind == "balbal":
		anim.play("dormant")
		state = "dormant"
	else:
		anim.play("idle")
	if elite:
		base_scale = Vector2(1.3, 1.3)
		anim.scale = base_scale
		anim.set_tint(Color(1.2, 0.9, 1.3))
		elite_name = "SEÇKİN " + String(def.get("name", kind)).to_upper()
		elite_t = randf_range(3.0, 5.0)
		if level:
			level.add_light(Vector2(0, -size.y / 2.0), Color(0.85, 0.45, 1.0), 120.0, 0.7, self)
	if elite or is_boss:
		_label = Label.new()
		_label.text = elite_name
		_label.label_settings = LabelSettings.new()
		_label.label_settings.font_size = 8
		_label.label_settings.font_color = Color(0.95, 0.7, 1.0) if elite else Color(1.0, 0.4, 0.4)
		_label.label_settings.outline_size = 3
		_label.label_settings.outline_color = Color(0.1, 0.02, 0.08)
		_label.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
		_label.position = Vector2(-60, -size.y * base_scale.y - 34)
		_label.size = Vector2(120, 12)
		_label.z_index = 80
		_label.visible = elite
		add_child(_label)
	if ai == "pouncer":
		perch = global_position
		state = "perch"
	if ai == "stalker":
		_hidden = true
		anim.modulate = Color(1, 1, 1, 0.12)
	if ai == "shield" or ai == "charger":
		anim.play("walk")
	home = global_position
	warn = Label.new()
	warn.text = "!"
	warn.label_settings = LabelSettings.new()
	warn.label_settings.font_size = 14
	warn.label_settings.font_color = Color(1.0, 0.35, 0.25)
	warn.label_settings.outline_size = 3
	warn.label_settings.outline_color = Color(0.1, 0.02, 0.04)
	warn.position = Vector2(-4, -size.y - 26)
	warn.visible = false
	warn.z_index = 80
	add_child(warn)
	overlay = StatusOverlay.new()
	overlay.host = self
	add_child(overlay)
	cd = randf_range(0.5, 1.5)


func center() -> Vector2:
	return global_position + Vector2(0, -size.y / 2.0)


func hurt_rect() -> Rect2:
	return Rect2(global_position + Vector2(-size.x / 2.0, -size.y), size)


func stun(t: float) -> void:
	stun_t = maxf(stun_t, t * (0.4 if is_boss else 1.0))
	if state in ["windup", "leap", "slam", "strike", "attack"]:
		state = "recover"
		st = 0.4


func apply_curse() -> void:
	cursed_t = 6.0
	FX.burst(center(), Color(0.3, 0.5, 1.0), 10, 60, 0.6, 0.2, 0, true)


# ------------------------------------------------------------------ hasar
func take_hit(d: float, opts: Dictionary) -> bool:
	if dead:
		return false
	if cursed_t > 0.0:
		d *= 1.25
	if armor_break > 0:
		d *= 1.0 + armor_mv / 100.0 * armor_break
	if guard_t > 0.0 and signf(float(opts.get("dir", 1))) == -float(facing):
		# Balbal siperi: önden gelen darbe taşa çarpar
		d *= 0.3
		opts["stagger"] = false
		FX.sparks(center() + Vector2(facing * 10, -4), Vector2(facing, -0.6), Color(0.85, 0.85, 1.0), 6, 150.0)
		FX.text(center() + Vector2(0, -30), "siper", Color(0.8, 0.8, 0.95), 7)
	# kalkanlı bekçi: önden gelen darbeler kalkana çarpar; ağır vuruş ya da 3 darbe kalkanı düşürür (sersemler, açık kalır)
	if (ai == "shield" or ai == "charger") and guard_hp > 0 and state != "stagger" and signf(float(opts.get("dir", 1))) == -float(facing) and not opts.get("behind", false):
		var heavy_hit: bool = opts.get("heavy", false) or float(opts.get("kb", 60.0)) >= 250.0
		guard_hp -= 3 if heavy_hit else 1
		var sp := center() + Vector2(facing * 14, -2)
		FX.impact_sprite("blunt", sp, Vector2(facing, 0), Color(1.0, 0.9, 0.6), 0.8)
		FX.sparks(sp, Vector2(facing, -0.5), Color(1.0, 0.9, 0.6), 10, 190.0)
		Ses.play("darbe_metal", -2.0, 1.1)
		Game.hitstop(0.04)
		Game.kick(Vector2(facing, 0), 3.0)
		vis_scale = Vector2(0.9, 1.08)
		if guard_hp <= 0:
			state = "stagger"
			st = 1.4
			velocity.x = facing * -90.0
			FX.text(center() + Vector2(0, -size.y - 8), "KALKAN DÜŞTÜ!", Color(1.0, 0.85, 0.4), 8)
			FX.anim("resonant_break", sp, 0.0, 0.9, Color(1.0, 0.85, 0.5))
			Game.slowmo(0.4, 0.12)
		else:
			FX.text(center() + Vector2(0, -size.y - 8), "KALKAN", Color(0.9, 0.9, 1.0), 7)
			velocity.x = facing * -40.0
		return false
	# tosbağa: kabuktayken dokunulmaz; dışarıdayken darbe alınca kabuğa çekilme şansı
	if ai == "turtle":
		if state in ["shell", "spin"]:
			d *= 0.08
			FX.sparks(center() + Vector2(float(opts.get("dir", 1)) * -16, -6), Vector2(-float(opts.get("dir", 1)), -0.6), Color(0.7, 0.9, 1.0), 6, 160.0)
			Ses.play("darbe_tas", -4.0, 1.2)
			FX.text(center() + Vector2(0, -34), "KABUK", Color(0.75, 0.9, 1.0), 7)
			opts["stagger"] = false
		elif randf() < 0.55 and stun_t <= 0.0:
			state = "shell"
			st = 1.3
			shell_t = 1.3
			anim.play("shell", true)
			FX.dust(global_position, Vector2.UP, 5, 0.3)
			FX.text(center() + Vector2(0, -34), "kabuğa çekildi", Color(0.75, 0.9, 1.0), 7)
	if _hidden:
		_reveal()
	if decoy:
		d = 9999.0
	if state == "dormant":
		_wake()
	hp -= d
	flash_t = 0.1
	aggro = true
	var crit: bool = opts.get("crit", false)
	var dir := float(opts.get("dir", 1))
	var big: bool = crit or opts.get("last", false) or float(opts.get("kb", 60.0)) > 180.0
	FX.number(center(), d, crit)
	# darbe tepkisi: gövde darbe yönünde ezilir ve yatar, düşmana özgü sıçrantı, kritikte ağır çekim ve ışık
	vis_scale = (Vector2(1.34, 0.72) if big else Vector2(1.28, 0.78)) if not heavy else Vector2(1.12, 0.9)
	_hit_tilt = -dir * (0.22 if big else 0.12) * (0.4 if heavy else 1.0)
	FX.blood(center() + Vector2(dir * 4, 0), Vector2(dir, -0.4), blood_col(), 12 if crit else 7)
	# darbe çizgileri: büyük vuruşlarda darbe noktasından dışarı kısa ışınlar
	if big:
		for k in 5:
			var a := Vector2(dir, 0).angle() + randf_range(-0.9, 0.9)
			var dv := Vector2(cos(a), sin(a))
			FX.streak(center() + dv * 6.0, center() + dv * randf_range(22.0, 38.0), Color(1.0, 0.95, 0.85, 0.8), 0.09)
	if crit:
		Game.shake(3.0)
		Game.slowmo(0.35, 0.1)
		FX.flash_light(center(), Color(1.0, 0.9, 0.6), 120.0, 1.6, 0.16)
		FX.ring(center(), 18, Color(1.0, 0.85, 0.4), 0.2)
	# ses: yaratığın türüne göre acı sesi + darbe
	Ses.play(_hurt_sfx(), -4.0, 1.0, 0.1, 0.05, center())
	if guard_t > 0.0 and signf(dir) == -float(facing):
		Ses.play("darbe_metal", -2.0)
	elif sprite_kind == "balbal":
		Ses.play("darbe_tas", -3.0)
	elif not opts.get("sfx_done", false):
		# silah sesi saldıran tarafından çalınmadıysa (mermi, patlama, kapan): genel darbe
		if crit:
			Ses.play("darbe_kritik", 0.0)
		elif big:
			Ses.play("darbe_agir", -1.0)
		else:
			Ses.play("darbe_et", -2.0)
	if opts.has("launch") and not heavy and not flying:
		velocity.y = -float(opts["launch"])
		launch_t = 0.5
		FX.ghost(anim.base, Color(1.0, 0.9, 0.6, 0.4), 0.25)
	if opts.has("stun") and float(opts["stun"]) > 0.0:
		stun(float(opts["stun"]))
	if opts.has("root"):
		root_t = maxf(root_t, float(opts["root"]))
	if opts.has("burn"):
		burn_t = maxf(burn_t, float(opts["burn"]))
	if opts.has("freeze"):
		if freeze_t <= 0.0:
			FX.anim("frost_nova", center(), 0.0, 0.9, Color(0.7, 0.9, 1.0))
			FX.frost(center(), 8)
		freeze_t = maxf(freeze_t, float(opts["freeze"]))
	if opts.has("poison"):
		poison = mini(5, poison + int(opts["poison"]))
		poison_t = 4.0
		FX.anim("acid_splash", center(), 0.0, 0.6, Color(0.6, 1.0, 0.4))
		FX.bubbles(center(), 4)
	if opts.has("burn") and burn_t <= 0.0:
		FX.anim("ember_jet", center(), -PI / 2.0, 0.6, Color(1.0, 0.7, 0.3))
	var kb := float(opts.get("kb", 60.0))
	if kb > 140.0 and not heavy:
		_slam_t = 0.3
	if not heavy or opts.get("stagger", false) or crit:
		hurt_t = 0.16 if not heavy else 0.08
		velocity.x = dir * kb * (0.4 if heavy else 1.0)
		if not flying and not heavy and not opts.has("launch"):
			velocity.y = minf(velocity.y, -kb * 0.25)
		if state == "windup" and not heavy:
			state = "recover"
			st = 0.3
		if anim.has_anim("hurt"):
			anim.play("hurt", true)
	if hp <= 0.0:
		_die(dir, kb, crit)
		return true
	return false


func _die(dir := 1.0, kb := 100.0, crit := false) -> void:
	dead = true
	remove_from_group("dusman")
	if decoy:
		FX.anim("smoke_puff", center(), 0.0, 0.8, Color(0.6, 0.35, 0.9), false)
		FX.burst(center(), Color(0.75, 0.45, 1.0), 10, 90, 0.4, 0.2, 100)
		FX.text(center() + Vector2(0, -26), "hayalet!", Color(0.8, 0.6, 1.0), 7)
		queue_free()
		return
	Game.run["kills"] = int(Game.run.get("kills", 0)) + 1
	Ses.play(_die_sfx(), 0.0, 1.0, 0.08, 0.03, center())
	Game.hitstop(0.05 if not elite else 0.09)
	if crit or elite:
		Game.zoom_punch(0.05 if not elite else 0.08)
	if level and level.has_method("ground_y_below"):
		var gy: float = level.ground_y_below(global_position + Vector2(0, -4))
		if gy >= 0.0:
			FX.decal("decal_blood_%d" % (randi() % 3), Vector2(global_position.x + dir * 6.0, gy + 2), 0.0, 10.0, 1.0 + (0.5 if elite else 0.0), Color(blood_col(), 0.85))
	# gövde savrulur, ruh zerreleri göğe yükselir, sıçrantı yere düşer
	FX.corpse(anim.base, Vector2(dir * maxf(140.0, kb * 1.3), -220.0 - kb * 0.4), blood_col())
	FX.blood(center(), Vector2(dir, -0.8), blood_col(), 16)
	FX.anim("smoke_puff", center(), 0.0, 0.9 + (0.5 if elite else 0.0), Color(blood_col(), 0.9).lerp(Color(0.3, 0.25, 0.35), 0.5), false)
	FX.smoke(center(), 4, 0.45, Color(blood_col().darkened(0.5), 0.6))
	FX.soul(center(), Color(0.55, 0.95, 1.0), 22 if not elite else 40)
	FX.ring(center(), 26 if not elite else 44, Color(0.6, 0.95, 1.0), 0.3)
	FX.flash_light(center(), Color(0.55, 0.95, 1.0), 140.0, 1.5, 0.3)
	Game.shake(3.0 if not elite else 6.0)
	Game.kick(Vector2(dir, 0), 3.0)
	if crit or elite:
		Game.slowmo(0.3, 0.16 if not elite else 0.35)
	if level:
		level.on_enemy_died(self)
	queue_free()


func _windup_sfx() -> void:
	## Saldırı uyarısı: her yaratığın kendi hazırlık sesi (yoksa genel)
	var w := "hazirlik_" + sprite_kind
	Ses.play(w if Ses.has(w) else "dusman_hazirlik", -8.0, 1.0, 0.12, 0.2, center())


func _anchor_g(key: String, fallback: Vector2) -> Vector2:
	## Sprite çapasının dünya konumu (fener, el...); yoksa yedek konum
	var a: Variant = anim.anchor(key) if anim else null
	if a == null:
		return fallback
	return global_position + (a as Vector2) * anim.scale


func _hurt_sfx() -> String:
	match sprite_kind:
		"bekci":
			return "tas_can"
		"tosbaga":
			return "tas_can"
		"kara_boru_han":
			return "kurt_can"
		"kara_boru":
			return "kurt_can"
		"cor":
			return "cor_can"
		"agac_iyesi":
			return "agac_can"
		"surale":
			return "surale_can"
		"balbal":
			return "tas_can"
		"arcura":
			return "hayalet_can"
	return "kurt_can"


func _die_sfx() -> String:
	match sprite_kind:
		"bekci":
			return "tas_olum"
		"tosbaga":
			return "tas_olum"
		"kara_boru_han":
			return "kurt_olum"
		"kara_boru":
			return "kurt_olum"
		"cor":
			return "cor_olum"
		"agac_iyesi":
			return "agac_olum"
		"surale":
			return "surale_olum"
		"balbal":
			return "tas_olum"
		"arcura":
			return "hayalet_olum"
	return "kurt_olum"


var _hit_tilt := 0.0
var _slam_t := 0.0
var _bounced := false


func _wall_slam() -> void:
	## Geri itilirken duvara çarptı: ek hasar, kıvılcım, kısa duraklama (Dead Cells duvar çarpması)
	_slam_t = 0.0
	var d := 5.0 + 2.0 * float(Game.run.get("tier", 0))
	hp -= d
	FX.number(center(), d, false, Color(1.0, 0.8, 0.6))
	var n := get_wall_normal()
	FX.impact_sprite("blunt", center() - n * 8.0, -n, Color(1.0, 0.9, 0.7), 0.9)
	FX.sparks(center() - n * 8.0, n, Color(1.0, 0.9, 0.7), 8, 180.0)
	FX.dust(global_position, n, 5, 0.3)
	Game.hitstop(0.05)
	Game.shake(2.5)
	Game.kick(-n, 3.0)
	Ses.play("darbe_kunt", -3.0)
	stun(0.45)
	vis_scale = Vector2(0.72, 1.3)
	velocity.x = n.x * 60.0
	if hp <= 0.0:
		_die(n.x, 120.0, false)


# ------------------------------------------------------------------ yapay zekâ
func _physics_process(delta: float) -> void:
	if dead:
		return
	var player: Node = level.player if level else null
	_tick_status(delta)
	if dead:
		return
	vis_scale = vis_scale.lerp(Vector2.ONE, clampf(delta * 12.0, 0.0, 1.0))
	anim.scale = base_scale * vis_scale
	_hit_tilt = lerpf(_hit_tilt, 0.0, clampf(delta * 14.0, 0.0, 1.0))
	anim.rotation = _hit_tilt
	if _slam_t > 0.0:
		_slam_t -= delta
		if is_on_wall() and absf(velocity.x) > 40.0:
			_wall_slam()
	if launch_t > 0.0:
		# havaya fırlatıldı: çaresizce düşer, yere çarpınca toz; hızlı düşüşte bir kez seker
		launch_t -= delta
		velocity.x = move_toward(velocity.x, 0.0, 300 * delta)
		velocity.y = minf(velocity.y + 1100.0 * delta, 540.0)
		anim.rotation = lerpf(anim.rotation, -0.6 * signf(anim.scale.x), clampf(delta * 6.0, 0.0, 1.0))
		var vy := velocity.y
		move_and_slide()
		if is_on_floor() and vy >= 0.0:
			if vy > 360.0 and not _bounced:
				_bounced = true
				launch_t = 0.3
				velocity.y = -vy * 0.35
				vis_scale = Vector2(1.35, 0.65)
				FX.dust(global_position, Vector2.UP, 7, 0.32)
				FX.impact_sprite("blunt", global_position, Vector2.UP, Color(1.0, 0.9, 0.75), 0.7)
				Game.hitstop(0.035)
				Game.shake(2.5)
				Ses.play("darbe_kunt", -6.0, 0.9)
				return
			launch_t = 0.0
			_bounced = false
			vis_scale = Vector2(1.3, 0.7)
			FX.dust(global_position, Vector2.UP, 6, 0.3)
			Game.shake(2.0)
		if Engine.get_physics_frames() % 3 == 0:
			FX.ghost(anim.base, Color(1.0, 0.85, 0.6, 0.3), 0.2)
		return
	anim.rotation = lerpf(anim.rotation, 0.0, clampf(delta * 10.0, 0.0, 1.0))
	flash_t -= delta
	anim.set_flash(1.0 if flash_t > 0.0 else (0.35 if stun_t > 0.0 and int(Time.get_ticks_msec() / 80) % 2 == 0 else 0.0))
	if freeze_t > 0.0 or stun_t > 0.0 or root_t > 0.0:
		if freeze_t > 0.0:
			anim.set_tint(Color(0.6, 0.9, 1.4))
			anim.speed = 0.0  # donmuş: animasyon durur
			if Engine.get_physics_frames() % 14 == 0:
				FX.frost(center(), 1)
		velocity.x = move_toward(velocity.x, 0.0, 800 * delta)
		if not flying:
			velocity.y = minf(velocity.y + 1100.0 * delta, 540.0)
		else:
			velocity.y = move_toward(velocity.y, 0.0, 400 * delta)
		move_and_slide()
		warn.visible = false
		return
	else:
		anim.speed = 1.0
		_status_tint()
	if hurt_t > 0.0:
		hurt_t -= delta
		velocity.x = move_toward(velocity.x, 0.0, 900 * delta)
		if not flying:
			velocity.y = minf(velocity.y + 1100.0 * delta, 540.0)
		move_and_slide()
		if hurt_t <= 0.0 and anim.anim == "hurt":
			anim.play("idle")
		return
	cd -= delta
	var to_p := Vector2.ZERO
	var dist := 9999.0
	if player and not player.dead:
		to_p = player.center() - center()
		dist = to_p.length()
		if not aggro and dist < 230.0 and absf(to_p.y) < 110.0 and level.los(center(), player.center()):
			aggro = true
		elif aggro and dist > 460.0:
			aggro = false
	if elite and aggro and player and not player.dead:
		_elite_tick(delta, player, dist)
	if state == "stagger":
		# kalkan düştü: açık, sendeler
		anim.play("stagger")
		velocity.x = move_toward(velocity.x, 0.0, 500 * delta)
		st -= delta
		if not flying:
			velocity.y = minf(velocity.y + 1100.0 * delta, 540.0)
		move_and_slide()
		if st <= 0.0:
			state = "chase"
			guard_hp = 3
			cd = 0.5
		return
	match ai:
		"lunger":
			_ai_lunger(delta, player, to_p, dist)
		"flyer_ranged":
			_ai_flyer(delta, player, to_p, dist)
		"brute":
			_ai_brute(delta, player, to_p, dist)
		"hopper":
			_ai_hopper(delta, player, to_p, dist)
		"illusionist":
			_ai_illusionist(delta, player, to_p, dist)
		"grabber":
			_ai_grabber(delta, player, to_p, dist)
		"pouncer":
			_ai_pouncer(delta, player, to_p, dist)
		"shield":
			_ai_shield(delta, player, to_p, dist)
		"charger":
			_ai_charger(delta, player, to_p, dist)
		"turtle":
			_ai_turtle(delta, player, to_p, dist)
		"archer":
			_ai_archer(delta, player, to_p, dist)
		"stalker":
			_ai_stalker(delta, player, to_p, dist)
		"diver":
			_ai_diver(delta, player, to_p, dist)
		_:
			_ai_custom(delta, player, to_p, dist)
	guard_t = maxf(0.0, guard_t - delta)
	if not flying:
		velocity.y = minf(velocity.y + 1100.0 * delta, 540.0)
	move_and_slide()
	anim.set_facing(facing)
	warn.visible = state == "windup" and int(Time.get_ticks_msec() / 90) % 2 == 0
	if contact and player and not player.dead and not _did_hit and hurt_rect().intersects(player.hurt_rect()):
		if player.take_hit(dmg, self):
			_did_hit = true


func _tick_status(delta: float) -> void:
	stun_t = maxf(0.0, stun_t - delta)
	pulled_t = maxf(0.0, pulled_t - delta)
	root_t = maxf(0.0, root_t - delta)
	freeze_t = maxf(0.0, freeze_t - delta)
	cursed_t = maxf(0.0, cursed_t - delta)
	_dot_t -= delta
	if burn_t > 0.0:
		burn_t -= delta
		if Engine.get_physics_frames() % 6 == 0:
			FX.fire(center() + Vector2(randf_range(-5, 5), randf_range(-4, 4)), 2, 0.28, 3.0)
		if Engine.get_physics_frames() % 20 == 0:
			FX.smoke(center() + Vector2(0, -8), 1, 0.3)
	if bleed_t > 0.0:
		bleed_t -= delta
		if bleed_t <= 0.0:
			bleed = 0
		elif Engine.get_physics_frames() % 16 == 0:
			FX.blood(center() + Vector2(randf_range(-4, 4), 0), Vector2.DOWN, blood_col(), 2)
	if poison_t > 0.0:
		poison_t -= delta
		if poison_t <= 0.0:
			poison = 0
		elif Engine.get_physics_frames() % 10 == 0:
			FX.bubbles(center() + Vector2(0, -2), 1 + poison / 2)
	if _dot_t <= 0.0:
		_dot_t = 0.5
		var tier := float(Game.run.get("tier", 0))
		var dot := 0.0
		if burn_t > 0.0:
			dot += 3.0 * (1.0 + 0.6 * tier)
		if bleed > 0:
			dot += 1.6 * bleed * (1.0 + 0.6 * tier)
		if poison > 0:
			dot += 1.4 * poison * (1.0 + 0.6 * tier)
		if dot > 0.0:
			hp -= dot
			var dc := Color(1.0, 0.3, 0.35)
			if poison > 0:
				dc = Color(0.55, 1.0, 0.35)
			if burn_t > 0.0:
				dc = Color(1.0, 0.55, 0.3)
			FX.number(center(), dot, false, dc)
			if hp <= 0.0:
				_die()


func _status_tint() -> void:
	## Durum rengi: yanma turuncu titreşir, zehir yeşil nabız atar, seçkin mor kalır
	var t := Time.get_ticks_msec() / 1000.0
	var c := (Color(1.15, 0.92, 1.25) if elite else Color(1, 1, 1)) * base_tint
	if poison > 0:
		c = c.lerp(Color(0.75, 1.3, 0.65), 0.45 + 0.25 * sin(t * 7.0))
	if burn_t > 0.0:
		c = c.lerp(Color(1.4, 0.85, 0.55), 0.5 + 0.3 * sin(t * 23.0))
	anim.set_tint(c)


func _face(to_p: Vector2) -> void:
	if absf(to_p.x) > 4.0:
		facing = int(sign(to_p.x))


func _wall_or_ledge() -> bool:
	var ahead := global_position + Vector2(facing * (size.x / 2.0 + 4.0), -6)
	var below := global_position + Vector2(facing * (size.x / 2.0 + 4.0), 6)
	return level.solid_at(ahead) or not level.ground_at(below)


func _patrol(delta: float) -> void:
	velocity.x = move_toward(velocity.x, facing * speed * 0.35, 400 * delta)
	if _wall_or_ledge() or absf(global_position.x - home.x) > 90.0 and sign(global_position.x - home.x) == facing:
		facing = -facing


func _ai_lunger(delta: float, player: Node, to_p: Vector2, dist: float) -> void:
	match state:
		"idle", "chase":
			if not aggro:
				state = "idle"
				_patrol(delta)
				anim.play("run" if absf(velocity.x) > 10.0 else "idle")
				return
			state = "chase"
			# sürü: kanat kurdu oyuncunun arkasına dolaşmaya çalışır
			if flank == 1 and player and dist > 70.0 and dist < 200.0:
				var behind: float = player.global_position.x - float(player.facing) * 60.0
				facing = int(signf(behind - global_position.x)) if absf(behind - global_position.x) > 6.0 else int(signf(to_p.x))
			else:
				_face(to_p)
			var tgt := facing * speed
			if _wall_or_ledge():
				tgt = 0.0
			velocity.x = move_toward(velocity.x, tgt, 600 * delta)
			anim.play("run")
			if dist < 95.0 and absf(to_p.y) < 40.0 and cd <= 0.0 and is_on_floor():
				_face(to_p)
				state = "windup"
				_windup_sfx()
				st = 0.45
				velocity.x = 0.0
		"windup":
			anim.play("windup")
			velocity.x = move_toward(velocity.x, 0.0, 900 * delta)
			st -= delta
			if st <= 0.0:
				state = "leap"
				st = 0.0
				velocity = Vector2(facing * 270.0, -230.0)
				contact = true
				_did_hit = false
				vis_scale = Vector2(0.8, 1.25)
				FX.dust(global_position, Vector2(-facing, -0.5), 5, 0.28)
		"leap":
			anim.play("leap")
			st += delta
			if Engine.get_physics_frames() % 3 == 0:
				FX.ghost(anim.base, Color(0.6, 0.3, 0.7, 0.35), 0.18)
			if is_on_floor() and st > 0.12:
				state = "recover"
				st = 0.55
				contact = false
				vis_scale = Vector2(1.25, 0.8)
				FX.dust(global_position, Vector2.UP, 4, 0.26)
		"recover":
			anim.play("idle")
			velocity.x = move_toward(velocity.x, 0.0, 700 * delta)
			st -= delta
			if st <= 0.0:
				state = "chase"
				cd = randf_range(0.8, 1.5)


func _ai_flyer(delta: float, player: Node, to_p: Vector2, dist: float) -> void:
	var t := Time.get_ticks_msec() / 1000.0
	match state:
		"idle", "chase":
			var target := home + Vector2(sin(t * 0.8) * 30.0, cos(t * 1.3) * 10.0)
			if aggro and player:
				state = "chase"
				var side := -signf(to_p.x) if absf(to_p.x) > 1.0 else 1.0
				target = player.center() + Vector2(side * 110.0, -60.0 + sin(t * 2.0) * 12.0)
				_face(to_p)
				if cd <= 0.0 and absf(to_p.x) < 40.0 and to_p.y > 40.0 and to_p.y < 140.0 and randf() < 0.5:
					state = "dive"
					st = 0.0
					contact = true
					_did_hit = false
					velocity = Vector2(signf(to_p.x) * 60.0, 330.0)
					FX.ghost(anim.base, Color(0.6, 1.0, 0.4, 0.4), 0.2)
				elif cd <= 0.0 and dist < 260.0 and level.los(center(), player.center()):
					state = "windup"
					_windup_sfx()
					st = 0.6
			var dv := (target - global_position)
			velocity = velocity.lerp(dv.limit_length(1.0) * speed, clampf(2.5 * delta, 0.0, 1.0))
			anim.play("idle")
		"windup":
			velocity = velocity.lerp(Vector2.ZERO, clampf(6.0 * delta, 0.0, 1.0))
			anim.show_frame("attack", 0)
			_face(to_p)
			st -= delta
			if st <= 0.0:
				state = "attack"
				st = 0.35
				var p := Projectile.new()
				p.team = "e"
				p.kind = "spore"
				p.damage = dmg
				p.source = self
				p.position = _anchor_g("mouth", center() + Vector2(facing * 8, -6))
				p.velocity = to_p.normalized() * 160.0
				p.homing = 0.6
				p.life = 3.0
				level.add_projectile(p)
		"attack":
			anim.show_frame("attack", 1)
			st -= delta
			if st <= 0.0:
				state = "chase"
				cd = randf_range(1.8, 2.8)
		"dive":
			anim.show_frame("attack", 1)
			st += delta
			if Engine.get_physics_frames() % 3 == 0:
				FX.ghost(anim.base, Color(0.6, 1.0, 0.4, 0.35), 0.18)
			if st > 0.45 or level.solid_at(global_position + Vector2(0, 8)):
				state = "recover"
				st = 0.6
				contact = false
				velocity = Vector2(0, -160)
				FX.dust(global_position + Vector2(0, 6), Vector2.UP, 4, 0.24)
		"recover":
			velocity = velocity.lerp(Vector2(0, -120), clampf(3.0 * delta, 0.0, 1.0))
			st -= delta
			if st <= 0.0:
				state = "chase"
				cd = randf_range(1.6, 2.4)


func _ai_brute(delta: float, player: Node, to_p: Vector2, dist: float) -> void:
	match state:
		"idle", "chase":
			if not aggro:
				state = "idle"
				velocity.x = move_toward(velocity.x, 0.0, 400 * delta)
				anim.play("idle")
				return
			state = "chase"
			_face(to_p)
			var tgt := facing * speed
			if _wall_or_ledge() or dist < 48.0:
				tgt = 0.0
			velocity.x = move_toward(velocity.x, tgt, 300 * delta)
			anim.play("walk" if absf(velocity.x) > 4.0 else "idle")
			if cd <= 0.0:
				if dist < 70.0 and absf(to_p.y) < 50.0:
					state = "windup"
					_windup_sfx()
					st = 0.75
					set_meta("move", "slam")
				elif dist < 230.0 and player.is_on_floor():
					state = "windup"
					_windup_sfx()
					st = 0.6
					set_meta("move", "roots")
					set_meta("target", player.global_position)
					level.telegraph_ground(player.global_position, 0.75)
		"windup":
			velocity.x = 0.0
			anim.play("windup")
			st -= delta
			if st <= 0.0:
				if get_meta("move") == "slam":
					state = "slam"
					st = 0.4
					Game.shake(5.0)
					var box := Rect2(global_position.x + (8.0 if facing > 0 else -78.0), global_position.y - 60.0, 70.0, 60.0)
					FX.shock_line(global_position + Vector2(facing * 40, 0), 36.0, Color(0.5, 0.42, 0.3, 0.7))
					Game.kick(Vector2.DOWN, 4.0)
					vis_scale = Vector2(1.15, 0.88)
					FX.flash_light(global_position + Vector2(facing * 40, -8), Color(1.0, 0.7, 0.4), 140.0, 1.2, 0.2)
					FX.ring(global_position + Vector2(facing * 40, -2), 40, Color(0.9, 0.7, 0.4), 0.3, 0.3)
					if player and box.intersects(player.hurt_rect()):
						player.take_hit(dmg * 1.2, self)
				else:
					state = "slam"
					st = 0.5
					var tgt: Vector2 = get_meta("target")
					level.spawn_roots(tgt, dmg * 0.8, self)
					_root_wave(tgt, 2)
		"slam":
			anim.play("slam")
			st -= delta
			if st <= 0.0:
				state = "recover"
				st = 0.7
		"recover":
			anim.play("idle")
			st -= delta
			if st <= 0.0:
				state = "chase"
				cd = randf_range(1.2, 2.2)


func _wake() -> void:
	state = "recover"
	st = 0.5
	aggro = true
	anim.play("idle")
	FX.burst(center(), Color(0.7, 0.7, 0.75), 16, 90, 0.5, 0.25, 250)
	Game.shake(2.0)


func _root_wave(target: Vector2, n: int) -> void:
	## İye: ilk kökten sonra oyuncuya doğru yürüyen iki kök daha (her biri önceden işaretlenir)
	for i in range(1, n + 1):
		await get_tree().create_timer(0.35 * i).timeout
		if dead or level == null or not is_instance_valid(level.player):
			return
		var pl: Node = level.player
		var pos := target.lerp(pl.global_position, float(i) / float(n + 1)) + Vector2(randf_range(-10, 10), 0)
		level.telegraph_ground(pos, 0.3)
		await get_tree().create_timer(0.3).timeout
		if dead or level == null:
			return
		level.spawn_roots(pos, dmg * 0.6, self)


func _ai_illusionist(delta: float, player: Node, to_p: Vector2, dist: float) -> void:
	match state:
		"idle", "chase":
			if not aggro:
				state = "idle"
				_patrol(delta)
				anim.play("run" if absf(velocity.x) > 10.0 else "idle")
				return
			state = "chase"
			# mesafeyi 110-170 px'te tut
			var want := 0.0
			if dist < 100.0:
				want = -signf(to_p.x) * speed
			elif dist > 180.0:
				want = signf(to_p.x) * speed
			if _wall_or_ledge() and signf(want) == facing:
				want = 0.0
			if absf(want) > 1.0:
				facing = int(signf(want))
			else:
				_face(to_p)
			velocity.x = move_toward(velocity.x, want, 500 * delta)
			anim.play("run" if absf(velocity.x) > 10.0 else "idle")
			if cd <= 0.0 and dist < 240.0 and level.los(center(), player.center()):
				state = "windup"
				_windup_sfx()
				st = 0.55
				_face(to_p)
		"windup":
			anim.show_frame("cast", 0)
			velocity.x = move_toward(velocity.x, 0.0, 800 * delta)
			st -= delta
			if Engine.get_physics_frames() % 4 == 0:
				FX.burst(center() + Vector2(facing * 10, -4), Color(0.7, 0.3, 0.9), 1, 30, 0.4, 0.16, -40, true)
			if st <= 0.0:
				state = "attack"
				st = 0.4
				anim.show_frame("cast", 1)
				if not decoy and randf() < 0.6:
					# iki hayalet kopya: oyuncuya koşar, dokununca patlar
					for side in [-1, 1]:
						var g: Enemy = level.spawn_enemy("arcura", global_position + Vector2(side * 14, 0))
						g.decoy = true
						g.aggro = true
						g.hp = 1.0
						g.max_hp = 1.0
						g.dmg = dmg * 0.5
						g.anim.modulate = Color(0.7, 1.0, 0.7, 0.55)
						g.set_meta("rush", true)
					# kendisi oyuncunun arkasına ışınlanır
					FX.anim("smoke_puff", center(), 0.0, 0.7, Color(0.55, 0.3, 0.8), false)
					var nx: float = player.global_position.x - float(player.facing) * 70.0
					var ty: int = level.surface_y(int(nx / 24.0))
					if abs(ty * 24 - global_position.y) < 120:
						global_position = Vector2(nx, ty * 24.0 - 1)
					FX.anim("smoke_puff", center(), 0.0, 0.7, Color(0.55, 0.3, 0.8), false)
					FX.anim("arcane_parry", center(), 0.0, 0.8, Color(0.75, 0.4, 1.0))
					Ses.play("kam_davul", -6.0, 1.0, 0.06, 0.03, center())
					_face(player.center() - center())
				else:
					var p := Projectile.new()
					p.team = "e"
					p.kind = "curse"
					p.damage = dmg
					p.source = self
					p.position = _anchor_g("hand", center() + Vector2(facing * 10, -4))
					Ses.play("kam_ilahi", -8.0, 1.0, 0.06, 0.03, center())
					p.velocity = to_p.normalized() * 150.0
					p.homing = 1.2
					p.life = 2.5
					level.add_projectile(p)
		"attack":
			anim.show_frame("cast", 2)
			st -= delta
			if st <= 0.0:
				state = "chase"
				cd = randf_range(1.8, 3.0)
		"recover":
			st -= delta
			if st <= 0.0:
				state = "chase"
	# hayalet kopya: dümdüz oyuncuya koşar, dokununca dağılır
	if decoy and player and not player.dead:
		_face(to_p)
		velocity.x = move_toward(velocity.x, facing * speed * 1.6, 900 * delta)
		anim.play("run")
		state = "chase"
		if hurt_rect().intersects(player.hurt_rect()):
			player.take_hit(dmg, self)
			_die(float(facing), 0.0, false)


func _ai_grabber(delta: float, player: Node, to_p: Vector2, dist: float) -> void:
	match state:
		"idle", "chase":
			if not aggro:
				state = "idle"
				velocity.x = move_toward(velocity.x, 0.0, 400 * delta)
				anim.play("idle")
				return
			state = "chase"
			_face(to_p)
			var tgt := facing * speed
			if _wall_or_ledge() or dist < 44.0:
				tgt = 0.0
			velocity.x = move_toward(velocity.x, tgt, 350 * delta)
			anim.play("walk" if absf(velocity.x) > 4.0 else "idle")
			if cd <= 0.0 and dist < 78.0 and absf(to_p.y) < 50.0:
				state = "windup"
				_windup_sfx()
				st = 0.5
		"windup":
			velocity.x = 0.0
			anim.play("windup")
			st -= delta
			if st <= 0.0:
				state = "grab"
				st = 0.0
				velocity.x = facing * 260.0
				FX.dust(global_position, Vector2(-facing, -0.4), 4, 0.26)
		"grab":
			anim.play("grab")
			st += delta
			velocity.x = move_toward(velocity.x, 0.0, 700 * delta)
			var box := Rect2(global_position.x + (6.0 if facing > 0 else -70.0), global_position.y - 70.0, 64.0, 70.0)
			if player and not player.dead and box.intersects(player.hurt_rect()) and player.has_method("get_grabbed") and player.grabbed_by == null and player.inv_t <= 0.0 and player.roll_t <= 0.0:
				player.get_grabbed(self)
				grab_target = player
				state = "hold"
				st = 1.3
				FX.anim("tether_catch", player.center(), 0.0, 1.0, Color(0.9, 0.8, 0.5))
				FX.text(center() + Vector2(0, -80), "GIDIKLIYOR!", Color(1.0, 0.8, 0.4), 9)
			elif st > 0.35:
				state = "recover"
				st = 0.7
		"hold":
			anim.play("grab")
			velocity.x = 0.0
			st -= delta
			if grab_target and is_instance_valid(grab_target) and grab_target.grabbed_by == self:
				grab_target.global_position = global_position + Vector2(facing * 34, -10)
				if Engine.get_physics_frames() % 24 == 0:
					grab_target.take_hit(dmg * 0.4, self, null, true)
					vis_scale = Vector2(1.1, 0.92)
				if st <= 0.0:
					grab_target.release_grab(Vector2(facing * 260.0, -220.0))
					grab_target = null
					state = "recover"
					st = 0.8
			else:
				grab_target = null
				state = "recover"
				st = 0.5
		"recover":
			anim.play("idle")
			velocity.x = move_toward(velocity.x, 0.0, 600 * delta)
			st -= delta
			if st <= 0.0:
				state = "chase"
				cd = randf_range(1.5, 2.6)


func _ai_custom(_delta: float, _player: Node, _to_p: Vector2, _dist: float) -> void:
	pass  # boss sınıfları üstüne yazar


func _elite_tick(delta: float, player: Node, dist: float) -> void:
	## Seçkin (mini boss): 6 sn'de bir kükrer: yakındaki oyuncuyu iter, 3 sn hızlanır; çevresinde mor aura
	elite_t -= delta
	if Engine.get_physics_frames() % 5 == 0:
		FX.burst(center() + Vector2(randf_range(-size.x * 0.5, size.x * 0.5), randf_range(-size.y, 0)), Color(0.75, 0.4, 1.0), 1, 20, 0.5, 0.14, -40, true)
	if elite_t <= 0.0 and state in ["idle", "chase", "perch"]:
		elite_t = 6.0
		FX.ring(center(), 70, Color(0.8, 0.45, 1.0), 0.4)
		FX.anim("hush_lock", center(), 0.0, 1.2, Color(0.8, 0.45, 1.0))
		FX.text(center() + Vector2(0, -size.y - 20), "KÜKREME", Color(0.9, 0.6, 1.0), 8)
		Ses.play("dusman_hazirlik", -2.0, 0.7)
		Game.shake(3.0)
		if dist < 80.0 and player.has_method("shove"):
			player.shove(Vector2(signf(player.global_position.x - global_position.x) * 260.0, -160.0))
		speed *= 1.3
		get_tree().create_timer(3.0).timeout.connect(func() -> void: if is_instance_valid(self): speed /= 1.3)


func _reveal() -> void:
	if not _hidden:
		return
	_hidden = false
	anim.modulate = Color(1, 1, 1, 1)
	FX.anim("smoke_puff", center(), 0.0, 0.8, Color(0.7, 0.6, 0.9), false)
	FX.ring(center(), 24, Color(0.9, 0.8, 1.0), 0.25)
	Ses.play("kam_davul", -6.0, 1.3)


func _ai_pouncer(delta: float, player: Node, to_p: Vector2, dist: float) -> void:
	## Pusu tazısı: yüksekte bekler; oyuncu altından/önünden geçince üstüne atlar, inişte toz dalgası; sonra tazı gibi kovalar
	match state:
		"perch":
			velocity.x = 0.0
			anim.play("idle")
			if Engine.get_physics_frames() % 40 == 0 and player:
				_face(to_p)
			if player and dist < 200.0 and to_p.y > -30.0 and absf(to_p.x) < 190.0:
				state = "windup"
				_windup_sfx()
				_face(to_p)
				st = 0.38
				set_meta("pounce", true)
		"windup":
			anim.play("windup")
			velocity.x = 0.0
			st -= delta
			if st <= 0.0:
				state = "leap"
				st = 0.0
				var tgt: Vector2 = player.global_position + player.velocity * 0.35 if player else global_position + Vector2(facing * 80, 0)
				var dx := tgt.x - global_position.x
				var tt := clampf(absf(dx) / 320.0, 0.3, 0.6)
				velocity = Vector2(dx / tt, -(maxf(0.0, global_position.y - tgt.y) + 60.0) / tt + 0.0)
				velocity.y = minf(velocity.y, -220.0)
				contact = true
				_did_hit = false
				vis_scale = Vector2(0.8, 1.25)
				FX.dust(global_position, Vector2(-facing, -0.5), 6, 0.3)
				FX.ghost(anim.base, Color(0.7, 0.5, 1.0, 0.4), 0.25)
		"leap":
			anim.play("leap")
			st += delta
			if Engine.get_physics_frames() % 2 == 0:
				FX.ghost(anim.base, Color(0.6, 0.3, 0.7, 0.35), 0.18)
			if is_on_floor() and st > 0.15:
				state = "recover"
				st = 0.5
				contact = false
				vis_scale = Vector2(1.35, 0.7)
				FX.dust(global_position, Vector2.UP, 8, 0.32)
				FX.ring(global_position, 30, Color(0.9, 0.85, 0.8), 0.25, 0.3)
				Game.shake(2.5)
				Ses.play("inis_2", -6.0)
				if player and absf(player.global_position.x - global_position.x) < 34.0 and absf(player.global_position.y - global_position.y) < 24.0 and player.is_on_floor():
					player.take_hit(dmg * 0.6, self)
		"recover":
			anim.play("idle")
			velocity.x = move_toward(velocity.x, 0.0, 700 * delta)
			st -= delta
			if st <= 0.0:
				state = "chase"
				cd = 0.6
		_:
			_ai_lunger(delta, player, to_p, dist)
			if state == "chase" and cd <= 0.0 and player and dist > 120.0 and to_p.y > 20.0 and randf() < 0.02:
				state = "windup"
				_windup_sfx()
				st = 0.38


func _ai_shield(delta: float, player: Node, to_p: Vector2, dist: float) -> void:
	## Kalkanlı bekçi: kalkan önde yavaş ilerler; yakında kalkan darbesi (iter) ya da topuz vuruşu
	match state:
		"idle", "chase":
			if not aggro:
				state = "idle"
				_patrol(delta)
				anim.play("walk" if absf(velocity.x) > 8.0 else "guard")
				return
			state = "chase"
			_face(to_p)
			var tgt := facing * speed
			if _wall_or_ledge() or dist < 40.0:
				tgt = 0.0
			velocity.x = move_toward(velocity.x, tgt, 300 * delta)
			anim.play("walk" if absf(velocity.x) > 4.0 else "guard")
			if cd <= 0.0 and dist < 64.0 and absf(to_p.y) < 50.0:
				state = "windup"
				_windup_sfx()
				st = 0.5
				set_meta("move", "bash" if randf() < 0.45 else "strike")
		"windup":
			velocity.x = 0.0
			anim.play("windup" if get_meta("move") == "strike" else "guard")
			st -= delta
			if st <= 0.0:
				state = "strike"
				st = 0.3
				var bash: bool = get_meta("move") == "bash"
				anim.play("bash" if bash else "strike", true)
				velocity.x = facing * (200.0 if bash else 90.0)
				var box := Rect2(global_position.x + (4.0 if facing > 0 else -62.0), global_position.y - 56.0, 58.0, 56.0)
				FX.slash(global_position + Vector2(facing * 8, -34), facing, -2.0, 0.9, 30.0, 7.0, Color(0.9, 0.85, 0.7), 0.16)
				if player and box.intersects(player.hurt_rect()):
					player.take_hit(dmg * (0.7 if bash else 1.1), self)
					if bash and player.has_method("shove"):
						player.shove(Vector2(facing * 300.0, -140.0))
				Ses.play("savur_cekic" if not bash else "darbe_kunt", -6.0)
		"strike":
			velocity.x = move_toward(velocity.x, 0.0, 900 * delta)
			st -= delta
			if st <= 0.0:
				state = "recover"
				st = 0.6
		"recover":
			anim.play("guard")
			velocity.x = move_toward(velocity.x, 0.0, 600 * delta)
			st -= delta
			if st <= 0.0:
				state = "chase"
				cd = randf_range(1.0, 1.8)


func _ai_charger(delta: float, player: Node, to_p: Vector2, dist: float) -> void:
	## Kalkanlı akıncı: uzaktan kalkanını kaldırıp ileri hücum eder; çarparsa fırlatır, duvara çarparsa sersemler
	match state:
		"idle", "chase":
			if not aggro:
				state = "idle"
				_patrol(delta)
				anim.play("walk" if absf(velocity.x) > 8.0 else "guard")
				return
			state = "chase"
			_face(to_p)
			var tgt := facing * speed
			if _wall_or_ledge() or dist < 50.0:
				tgt = 0.0
			velocity.x = move_toward(velocity.x, tgt, 300 * delta)
			anim.play("walk" if absf(velocity.x) > 4.0 else "guard")
			if cd <= 0.0 and dist > 90.0 and dist < 300.0 and absf(to_p.y) < 40.0 and level.los(center(), player.center()):
				state = "windup"
				_windup_sfx()
				st = 0.75
				_face(to_p)
			elif cd <= 0.0 and dist < 60.0 and absf(to_p.y) < 50.0:
				state = "windup"
				st = 0.4
				set_meta("bash", true)
		"windup":
			velocity.x = move_toward(velocity.x, 0.0, 900 * delta)
			anim.play("guard")
			st -= delta
			if Engine.get_physics_frames() % 4 == 0:
				FX.dust(global_position + Vector2(-facing * 8, 0), Vector2(-facing, -0.3), 1, 0.2)
			if st <= 0.0:
				if get_meta("bash", false):
					set_meta("bash", false)
					state = "strike"
					st = 0.3
					anim.play("bash", true)
					velocity.x = facing * 220.0
					var box := Rect2(global_position.x + (4.0 if facing > 0 else -62.0), global_position.y - 56.0, 58.0, 56.0)
					if player and box.intersects(player.hurt_rect()):
						player.take_hit(dmg * 0.7, self)
						if player.has_method("shove"):
							player.shove(Vector2(facing * 320.0, -150.0))
				else:
					state = "charge"
					st = 1.25
					contact = true
					_did_hit = false
					Ses.play("savur_dev", -4.0, 0.8)
					FX.ring(global_position + Vector2(facing * 10, -20), 20, Color(1.0, 0.8, 0.5), 0.25)
		"charge":
			anim.play("charge")
			velocity.x = move_toward(velocity.x, facing * 400.0, 2200 * delta)
			st -= delta
			if Engine.get_physics_frames() % 2 == 0:
				FX.ghost(anim.base, Color(1.0, 0.7, 0.4, 0.35), 0.18)
				FX.dust(global_position + Vector2(-facing * 10, 0), Vector2(-facing, -0.4), 2, 0.26)
			if player and not player.dead and not _did_hit and hurt_rect().grow(6).intersects(player.hurt_rect()):
				_did_hit = true
				if player.take_hit(dmg * 1.3, self) and player.has_method("shove"):
					player.shove(Vector2(facing * 380.0, -220.0))
				Game.hitstop(0.06)
				Game.shake(5.0)
				FX.impact_sprite("blunt", player.center(), Vector2(facing, 0), Color(1.0, 0.85, 0.6), 1.2)
			if is_on_wall() or st <= 0.0 or _wall_or_ledge():
				contact = false
				if is_on_wall():
					# duvara çarptı: uzun sersemleme, açık
					state = "stagger"
					st = 1.6
					guard_hp = 0
					velocity.x = -facing * 120.0
					Game.shake(6.0)
					Game.hitstop(0.05)
					FX.impact_sprite("blunt", global_position + Vector2(facing * 14, -30), Vector2(facing, 0), Color(1.0, 0.9, 0.7), 1.1)
					FX.sparks(global_position + Vector2(facing * 14, -30), Vector2(-facing, -0.6), Color(1.0, 0.9, 0.6), 12, 200.0)
					FX.text(center() + Vector2(0, -size.y - 8), "DUVARA ÇARPTI!", Color(1.0, 0.85, 0.4), 8)
					Ses.play("darbe_cekic", -4.0)
				else:
					state = "recover"
					st = 0.7
		"strike":
			velocity.x = move_toward(velocity.x, 0.0, 900 * delta)
			st -= delta
			if st <= 0.0:
				state = "recover"
				st = 0.5
		"recover":
			anim.play("guard")
			velocity.x = move_toward(velocity.x, 0.0, 800 * delta)
			st -= delta
			if st <= 0.0:
				state = "chase"
				guard_hp = 3
				cd = randf_range(1.2, 2.2)


func _ai_turtle(delta: float, player: Node, to_p: Vector2, dist: float) -> void:
	## Taş tosbağa: yavaş yürür, yakında ısırır; vurulunca kabuğa çekilir (dokunulmaz) ve yuvarlanarak ezer
	match state:
		"idle", "chase":
			if not aggro:
				state = "idle"
				_patrol(delta)
				anim.play("walk" if absf(velocity.x) > 6.0 else "idle")
				return
			state = "chase"
			_face(to_p)
			var tgt := facing * speed
			if _wall_or_ledge() or dist < 50.0:
				tgt = 0.0
			velocity.x = move_toward(velocity.x, tgt, 250 * delta)
			anim.play("walk" if absf(velocity.x) > 4.0 else "idle")
			if cd <= 0.0 and dist < 66.0 and absf(to_p.y) < 44.0:
				state = "windup"
				_windup_sfx()
				st = 0.55
			elif cd <= 0.0 and dist > 110.0 and dist < 240.0 and absf(to_p.y) < 30.0 and randf() < 0.01:
				state = "shell"
				st = 0.5
				anim.play("shell", true)
		"windup":
			velocity.x = 0.0
			anim.play("windup")
			st -= delta
			if st <= 0.0:
				state = "strike"
				st = 0.3
				anim.play("bite", true)
				velocity.x = facing * 120.0
				var box := Rect2(global_position.x + (10.0 if facing > 0 else -66.0), global_position.y - 36.0, 56.0, 36.0)
				if player and box.intersects(player.hurt_rect()):
					player.take_hit(dmg, self)
				Ses.play("isirik", -6.0, 0.8)
		"strike":
			velocity.x = move_toward(velocity.x, 0.0, 800 * delta)
			st -= delta
			if st <= 0.0:
				state = "recover"
				st = 0.5
		"shell":
			anim.play("shell")
			velocity.x = move_toward(velocity.x, 0.0, 600 * delta)
			st -= delta
			if st <= 0.0:
				# kabuktan çıkıp yuvarlan: oyuncuya doğru
				state = "spin"
				st = 1.4
				_face(to_p)
				contact = true
				_did_hit = false
				Ses.play("sarsinti", -8.0, 1.4)
		"spin":
			anim.play("spin")
			anim.speed = 2.0
			velocity.x = move_toward(velocity.x, facing * 300.0, 1400 * delta)
			st -= delta
			if Engine.get_physics_frames() % 3 == 0:
				FX.dust(global_position + Vector2(-facing * 14, 0), Vector2(-facing, -0.3), 2, 0.28)
				FX.sparks(global_position + Vector2(facing * 10, -2), Vector2(-facing, -0.8), Color(0.8, 1.0, 1.0), 2, 120.0)
			if is_on_wall():
				facing = -facing
				_did_hit = false
				Game.shake(2.0)
				FX.dust(global_position, Vector2(-facing, -0.5), 5, 0.3)
			if player and not player.dead and not _did_hit and hurt_rect().grow(4).intersects(player.hurt_rect()):
				_did_hit = true
				if player.take_hit(dmg * 1.2, self) and player.has_method("shove"):
					player.shove(Vector2(facing * 300.0, -200.0))
			if st <= 0.0:
				anim.speed = 1.0
				contact = false
				state = "recover"
				st = 0.8
				anim.play("idle", true)
		"recover":
			anim.play("idle")
			velocity.x = move_toward(velocity.x, 0.0, 600 * delta)
			st -= delta
			if st <= 0.0:
				state = "chase"
				cd = randf_range(1.0, 2.0)


func _ai_archer(delta: float, player: Node, to_p: Vector2, dist: float) -> void:
	## Kurgan okçusu: 150-280 px uzakta durur; ok atar; yaklaşınca geri çekilir
	match state:
		"idle", "chase":
			if not aggro:
				state = "idle"
				_patrol(delta)
				anim.play("run" if absf(velocity.x) > 10.0 else "idle")
				return
			state = "chase"
			var want := 0.0
			if dist < 130.0:
				want = -signf(to_p.x) * speed * 1.4
			elif dist > 300.0:
				want = signf(to_p.x) * speed
			if _wall_or_ledge() and signf(want) == facing:
				want = 0.0
			if absf(want) > 1.0:
				facing = int(signf(want))
			else:
				_face(to_p)
			velocity.x = move_toward(velocity.x, want, 500 * delta)
			anim.play("run" if absf(velocity.x) > 10.0 else "idle")
			if cd <= 0.0 and dist < 320.0 and absf(to_p.y) < 160.0 and level.los(center(), player.center()):
				state = "windup"
				_windup_sfx()
				st = 0.7
				_face(to_p)
		"windup":
			anim.show_frame("cast", 0)
			velocity.x = move_toward(velocity.x, 0.0, 800 * delta)
			_face(to_p)
			st -= delta
			if st <= 0.0:
				state = "attack"
				st = 0.35
				anim.show_frame("cast", 2)
				var p := Projectile.new()
				p.team = "e"
				p.kind = "arrow"
				p.damage = dmg
				p.source = self
				p.position = _anchor_g("hand", center() + Vector2(facing * 10, -6))
				var tt := clampf(dist / 380.0, 0.4, 0.9)
				p.velocity = Vector2(to_p.x / tt, to_p.y / tt - 0.5 * 420.0 * tt)
				p.gravity = 420.0
				p.life = 2.5
				p.trail_col = Color(0.9, 0.8, 0.6, 0.5)
				level.add_projectile(p)
				Ses.play("yay_birak", -6.0, 0.9)
		"attack":
			st -= delta
			if st <= 0.0:
				state = "chase"
				cd = randf_range(1.4, 2.2)
		"recover":
			st -= delta
			if st <= 0.0:
				state = "chase"


func _ai_stalker(delta: float, player: Node, to_p: Vector2, dist: float) -> void:
	## Yek: görünmez sinsi; 110 px'e girince belirir ve hızlı hamle yapar
	if _hidden:
		anim.play("idle")
		velocity.x = move_toward(velocity.x, 0.0, 600 * delta)
		if player and dist < 110.0:
			_reveal()
			state = "windup"
			_windup_sfx()
			_face(to_p)
			st = 0.25
		elif aggro and player and dist < 260.0 and Engine.get_physics_frames() % 2 == 0:
			# görünmezken sessizce yaklaşır
			_face(to_p)
			if not _wall_or_ledge():
				velocity.x = facing * speed * 0.6
		return
	_ai_lunger(delta, player, to_p, dist)


func _ai_diver(delta: float, player: Node, to_p: Vector2, dist: float) -> void:
	## Dalıcı çor: spor atmaz, daha sık dalar
	if state in ["idle", "chase"] and aggro and player and cd <= 0.0 and absf(to_p.x) < 60.0 and to_p.y > 30.0:
		state = "dive"
		st = 0.0
		contact = true
		_did_hit = false
		velocity = Vector2(signf(to_p.x) * 90.0, 360.0)
		Ses.play("savur_bicak", -8.0, 0.8)
		FX.ghost(anim.base, Color(0.8, 0.9, 1.0, 0.4), 0.2)
		return
	if state == "windup":
		state = "chase"
		cd = 0.3
	_ai_flyer(delta, player, to_p, dist)


func _ai_hopper(delta: float, player: Node, to_p: Vector2, dist: float) -> void:
	match state:
		"dormant":
			velocity.x = 0.0
			if aggro and dist < 170.0:
				_wake()
		"idle", "chase":
			if not aggro:
				anim.play("idle")
				velocity.x = move_toward(velocity.x, 0.0, 600 * delta)
				return
			state = "chase"
			_face(to_p)
			anim.play("idle")
			velocity.x = move_toward(velocity.x, 0.0, 600 * delta)
			# oyuncu önden saldırıya hazırlanıyorsa siper al
			if player and dist < 60.0 and guard_t <= 0.0 and "atk" in player and not player.atk.is_empty() and player.atk.get("phase", "") == "wind" and randf() < 0.5:
				guard_t = 0.6
				vis_scale = Vector2(1.08, 0.94)
			if cd <= 0.0 and is_on_floor() and guard_t <= 0.0:
				if dist < 60.0 and absf(to_p.y) < 40.0:
					state = "windup"
					_windup_sfx()
					st = 0.6
				elif not _wall_or_ledge():
					state = "hop"
					st = 0.0
					velocity = Vector2(facing * speed * 1.6, -250.0)
		"hop":
			anim.play("hop")
			st += delta
			if is_on_floor() and st > 0.1:
				Game.shake(2.0)
				vis_scale = Vector2(1.3, 0.75)
				FX.dust(global_position, Vector2.UP, 7, 0.32, Color(0.6, 0.6, 0.65, 0.6))
				velocity.x = 0.0
				state = "chase"
				cd = randf_range(0.35, 0.7)
		"windup":
			anim.play("windup")
			velocity.x = 0.0
			st -= delta
			if st <= 0.0:
				state = "strike"
				st = 0.35
				var box := Rect2(global_position.x + (4.0 if facing > 0 else -58.0), global_position.y - 48.0, 54.0, 48.0)
				FX.slash(global_position + Vector2(facing * 6, -30), facing, -2.2, 0.8, 34.0, 8.0, Color(0.85, 0.85, 0.95), 0.18)
				FX.sparks(global_position + Vector2(facing * 30, -6), Vector2(facing, -0.8), Color(0.9, 0.9, 1.0), 6, 150.0)
				vis_scale = Vector2(1.12, 0.9)
				if player and box.intersects(player.hurt_rect()):
					player.take_hit(dmg, self)
		"strike":
			anim.play("strike")
			st -= delta
			if st <= 0.0:
				state = "recover"
				st = 0.6
		"recover":
			anim.play("idle")
			velocity.x = move_toward(velocity.x, 0.0, 600 * delta)
			st -= delta
			if st <= 0.0:
				state = "chase"
				cd = randf_range(0.5, 1.0)
