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
## v23 (yapay zekâ): her arketipin rolü ve okunur ama tehlikeli takımı (docs/TASARIM.md "v23"). Ortak kurallar:
##   * "!" hazırlık karşı vuruşla kesilir; "!!" zırhlı hamle (turuncu) yalnız kritik alır, ağır vuruş / çarpışma keser.
##   * Baskı altındaki (son 0,8 sn'de vurulmuş) yaratık zırhlı saldırır: ezbere basmak cezalanır.
##   * Sarsılma bağışıklığı (hafif vuruşla sonsuz kilit yok), sersemletmede azalan getiri, kısa sürede N vuruş
##     yiyen yaratık tepki verir (geri sıçrar / ışınlanır / zırhlı intikam / kalkan darbesi).
##   * Saldırı jetonları: oyuncunun çevresinde aynı anda en çok 1-3 yakın, 2 uzak saldırgan; jetonsuzlar çevresinde
##     dolaşır, biri arkaya geçer (kuşatma).

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
var sanat_tut := 0.0     # v28 Göğe Yükseliş: havada kilitli (yerçekimi ve yapay zekâ yok); SavasSanati her karede tazeler
var sanat_hedef := Vector2.ZERO   # kilitliyken gidilecek ayak konumu (move_and_slide: duvara / tavana girmez)
var sanat_dus := false   # çakılma: hızlı düşüş, yere değince sanat_indi
var sanat_indi := false
var sanat_egim := NAN    # v31 kombo sanatları: kilitliyken gövde eğimi hedefi (rad; NAN: olağan -0,35 × yön)
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
## v22 zorluk: saldırı beklemesi bu hızla söner, hazırlık bu hızla akar (Zorluk.saldirganlik / hazirlik); öfkeli:
## Üçüncü Kut Mührü'nden sonra doğan sert çeşitleme. bar: can çubuğu (EnemyBar)
var ofkeli := false
var _aggr := 1.0
var _wind_k := 1.0
var bar: EnemyBar
var elite_star: Node2D
## Düşmana özgü sıçrantı rengi (tazı: kor; çor: zehir yeşili; iye: Erlik moru özsu; balbal: taş tozu; kam: lanet moru; gulyabani: ölü irin)
const BLOOD := {"tepegoz": Color(0.75, 0.25, 0.2), "sahmeran_ana": Color(0.5, 1.0, 0.4), "yelbegen": Color(0.6, 0.9, 1.0), "erlik_han": Color(1.0, 0.45, 0.15), "kara_boru": Color(0.6, 0.05, 0.05), "kayip_ruh": Color(0.55, 0.85, 1.0), "buz_balbali": Color(0.75, 0.9, 1.0), "cini_golemi": Color(0.5, 0.7, 0.85), "cor": Color(0.55, 0.85, 0.2), "agac_iyesi": Color(0.6, 0.28, 0.72), "balbal": Color(0.6, 0.6, 0.66),
		"arcura": Color(0.7, 0.25, 0.9), "surale": Color(0.5, 0.55, 0.42), "bekci": Color(0.55, 0.5, 0.45), "tosbaga": Color(0.45, 0.6, 0.3), "kara_boru_han": Color(0.5, 0.03, 0.06)}


const NOT_FLESH := ["balbal", "bekci", "buz_balbali", "cini_golemi", "arcura", "kayip_ruh", "agac_iyesi", "cor", "yelbegen", "sihirli_kandil", "isilti_bocegi"]


## v23: uygulanan bütün yapay zekâ türleri (eskiden tornado / crawler / swarm / caster / kamikaze / mimic / charmer
## sprite'ın yapay zekâsına düşüyordu; cin (teleporter) hiç kıpırdamıyordu)
const AI_TURLERI := ["lunger", "flyer_ranged", "brute", "hopper", "illusionist", "grabber", "pouncer", "shield", "charger",
	"turtle", "archer", "stalker", "diver", "walker", "teleporter", "crawler", "swarm", "caster", "kamikaze", "tornado", "charmer", "mimic"]
## v23 tepki: kısa sürede kaç vuruş yiyince tepki verir (_react: geri sıçrar / ışınlanır / zırhlı intikam / kalkan darbesi)
const TEPKI := {"lunger": 3, "pouncer": 3, "crawler": 3, "stalker": 3, "flyer_ranged": 2, "swarm": 2, "diver": 2,
	"illusionist": 2, "caster": 2, "charmer": 2, "archer": 2, "brute": 5, "tornado": 4, "hopper": 3, "grabber": 4,
	"mimic": 4, "shield": 3, "charger": 3, "turtle": 99, "kamikaze": 1}


func blood_col() -> Color:
	## v13: etten yaratıkların kanı koyu kırmızı; ruh/taş/bitki yaratıklarının kendi rengi
	if BLOOD.has(sprite_kind):
		return BLOOD[sprite_kind]
	return Color(0.55, 0.04, 0.06)


func is_flesh() -> bool:
	return not (sprite_kind in NOT_FLESH or kind in NOT_FLESH)


func setup(k: String, is_elite: bool, _tier: int, is_ofkeli := false) -> void:
	## v22: can / hasar Zorluk'tan (data/zorluk.json): world.json tabanı (1. derinlik) × derinlik çarpanı × mühür;
	## bosslar kendi derinliklerinde (Game.BOSS_AFTER), canları zorluk.json "boss" tablosundan
	kind = k
	def = Data.enemy_def(k)
	sprite_kind = String(def.get("sprite", k))
	if sprite_kind == "":
		sprite_kind = k
	elite = is_elite
	ofkeli = is_ofkeli and not elite
	var dd := Zorluk.derinlik()
	if String(def.get("ai", "")).begins_with("boss"):
		dd = Zorluk.boss_derinlik(k)
	max_hp = float(def.get("hp", 30)) * Zorluk.can_k(dd) * (Zorluk.seckin_can() if elite else 1.0)
	dmg = float(def.get("dmg", 10)) * Zorluk.hasar_k(dd) * (Zorluk.seckin_hasar() if elite else 1.0)
	if String(def.get("ai", "")).begins_with("boss"):
		max_hp = Zorluk.boss_can(k, max_hp)
	speed = float(def.get("speed", 80))
	if ofkeli:
		max_hp *= Zorluk.ofkeli("can")
		dmg *= Zorluk.ofkeli("hasar")
		speed *= Zorluk.ofkeli("hiz")
	hp = max_hp
	_aggr = Zorluk.saldirganlik(dd) * (Zorluk.ofkeli("saldirganlik") if ofkeli else 1.0)
	_wind_k = Zorluk.hazirlik(dd) * (Zorluk.ofkeli("hazirlik") if ofkeli else 1.0)
	ai = String(def.get("ai", Data.enemy_def(sprite_kind).get("ai", "lunger")))
	if not (ai in AI_TURLERI) and not ai.begins_with("boss"):
		ai = String(Data.enemy_def(sprite_kind).get("ai", "lunger"))
	if ai == "walker":
		ai = "shield"
	if ai == "teleporter":
		ai = "illusionist"
	if not (ai in AI_TURLERI) and not ai.begins_with("boss"):
		ai = "lunger"
	if not ai.begins_with("boss"):
		# v26: role göre can (zorluk.json "rol_can": tazılar daha çok, uzak / uçan daha az)
		max_hp *= Zorluk.rol_can(ai)
		hp = max_hp
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
		"tepegoz":
			size = Vector2(64, 150)
			heavy = true
			is_boss = true
		"sahmeran_ana":
			size = Vector2(80, 120)
			heavy = true
			is_boss = true
		"yelbegen":
			size = Vector2(66, 160)
			heavy = true
			is_boss = true
		"erlik_han":
			size = Vector2(60, 150)
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
	# düşmanın kendi kimliğiyle çizilmiş çeşitlemesi varsa (ör. kan_yarasasi_v2) onu kullan; renkleri çizimde
	# olduğundan biyom tonu uygulanmaz (yoklama: kendi çeşitlemesi yoksa taban türün v2 sprite'ı kullanılır)
	var own_v2 := kind != sprite_kind and FileAccess.file_exists("res://assets/sprites/%s_%s.json" % [kind, Data.STIL])
	anim.setup(kind if own_v2 else sprite_kind)
	_ds_setup()
	if def.has("tint") and not own_v2:
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
	if ofkeli:
		# v22 öfkeli (Kut Mührü 3+): koyu kızıl ton, biraz iri, kor ışığı
		base_tint = base_tint * Color(1.25, 0.72, 0.68)
		anim.set_tint(base_tint)
		base_scale = Vector2(1.1, 1.1)
		anim.scale = base_scale
		if level:
			level.add_light(Vector2(0, -size.y / 2.0), Color(1.0, 0.35, 0.2), 80.0, 0.5, self)
	if elite:
		elite_star = EliteStar.new()
		elite_star.position = Vector2(0, -size.y * base_scale.y - 18)
		add_child(elite_star)
	if not is_boss and not decoy:
		# v22 can çubuğu (EnemyBar): hasar alınca belirir, savaş dışında söner
		bar = EnemyBar.new()
		bar.host = self
		add_child(bar)
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
	if ai == "mimic":
		# v23 Karakoncolos: büzülmüş, kıpırtısız bir kar yığını gibi bekler; yaklaşınca sıçrayıp yakalar
		state = "lurk"
		anim.modulate = Color(0.72, 0.78, 0.9, 1.0)
	if ai == "shield" or ai == "charger":
		anim.play("walk")
	home = global_position
	warn = Label.new()
	warn.text = "!"
	warn.label_settings = LabelSettings.new()
	warn.label_settings.font = InkUI.font("brush")
	warn.label_settings.font_size = 26
	warn.label_settings.font_color = Color(1.0, 0.35, 0.25)
	warn.label_settings.shadow_color = Color(0.1, 0.02, 0.04, 0.95)
	warn.label_settings.shadow_offset = Vector2(2, 2)
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
	## v23: zırhlı hamle (sa_t) hafif sersemletmeyle (< 0,75 sn) kesilmez; çarpışma (0,8) ve ağır bitiriş keser.
	## Art arda sersemletmede azalan getiri (1 / 0,6 / 0,35 / 0,2): sersemleten silahla sonsuz kilit yok.
	if sa_t > 0.0 and t < 0.75:
		return
	sa_t = 0.0
	if has_meta("rev"):
		remove_meta("rev")
	var now := Game.clock()
	_stun_n = _stun_n + 1 if now - _stun_last < 1.6 else 0
	_stun_last = now
	t *= [1.0, 0.6, 0.35, 0.2][mini(_stun_n, 3)]
	stun_t = maxf(stun_t, t * (0.4 if is_boss else 1.0))
	if state in ["windup", "leap", "slam", "strike", "attack", "dash", "swoop", "dive", "spin", "fuse", "rev"]:
		state = "recover"
		st = 0.4
		contact = false


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
	# v19: duruşu kırık yaratık fazla hasar alır; infaz (Kut Alma) siperi / kalkanı / kabuğu aşar ve kesin öldürür
	var exe: bool = opts.get("exec", false)
	if evade_t > 0.0 and not exe:
		# v23: geri sıçrayışın / ışınlanmanın ilk anı dokunulmaz
		if Engine.get_physics_frames() % 6 == 0:
			FX.text(center() + Vector2(0, -size.y * 0.5 - 10.0), "ıska", Color(0.8, 0.8, 0.9), 7)
		return false
	if broken_t > 0.0:
		d *= float(POISE["break_dmg"])
	if guard_t > 0.0 and not exe and signf(float(opts.get("dir", 1))) == -float(facing):
		# Balbal siperi: önden gelen darbe taşa çarpar
		d *= 0.3
		opts["stagger"] = false
		FX.sparks(center() + Vector2(facing * 10, -4), Vector2(facing, -0.6), Color(0.85, 0.85, 1.0), 6, 150.0)
		FX.text(center() + Vector2(0, -30), "siper", Color(0.8, 0.8, 0.95), 7)
	# kalkanlı bekçi: önden gelen darbeler kalkana çarpar; ağır vuruş ya da 3 darbe kalkanı düşürür (sersemler, açık kalır)
	if (ai == "shield" or ai == "charger") and not exe and guard_hp > 0 and state != "stagger" and signf(float(opts.get("dir", 1))) == -float(facing) and not opts.get("behind", false):
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
			# v23: kalkana art arda vurana kalkan darbesiyle karşılık (zırhlı "!!": yuvarlan ya da arkasına geç)
			if not _passive() and state in ["idle", "chase", "recover"]:
				var nb := Game.clock()
				_block_n = _block_n + 1 if nb - _block_last < 1.0 else 1
				_block_last = nb
				if _block_n >= 2:
					_block_n = 0
					_revenge("bash")
		return false
	# tosbağa: kabuktayken dokunulmaz; dışarıdayken darbe alınca kabuğa çekilme şansı
	if ai == "turtle" and not exe:
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
	if exe:
		d = maxf(d, hp + 1.0)
	if state == "dormant":
		_wake()
	hp -= d
	if not aggro:
		_set_aggro()
	var crit: bool = opts.get("crit", false)
	var dir := float(opts.get("dir", 1))
	var big: bool = crit or opts.get("last", false) or float(opts.get("kb", 60.0)) > 180.0
	# v14 darbe flaşı: 2-3 kare yüksek kontrast, sonra hemen normale (uzun flaş "sersemleme" gibi okunur)
	flash_t = 0.05 if not big else 0.08
	var feel_done: bool = opts.get("feel_done", false)
	_feel_done = feel_done
	FX.number(center(), d, crit)
	# darbe tepkisi: gövde darbe yönünde ezilir ve yatar, düşmana özgü sıçrantı, kritikte ağır çekim ve ışık
	vis_scale = (Vector2(1.34, 0.72) if big else Vector2(1.28, 0.78)) if not heavy else Vector2(1.12, 0.9)
	_hit_tilt = -dir * (0.22 if big else 0.12) * (0.4 if heavy else 1.0)
	# v13 kan: her vuruşta hasara göre sıçrantı (çıkış yönünde koni + az geri sıçrama), kritikte fışkırma
	var hk := clampf(d / maxf(1.0, max_hp), 0.0, 1.0)
	var hitp := center() + Vector2(dir * 4, randf_range(-6, 4))
	Blood.spray(hitp, Vector2(dir, -0.35), blood_col(), 10 + int(hk * 45.0) + (14 if crit else 0) + (8 if big else 0), 1.0 + (0.35 if big else 0.0))
	if crit and is_flesh():
		Blood.spray(hitp, Vector2(dir, -1.0), blood_col(), 10, 1.4, false)
	# darbe çizgileri: büyük vuruşlarda darbe noktasından dışarı kısa ışınlar
	if big:
		for k in 5:
			var a := Vector2(dir, 0).angle() + randf_range(-0.9, 0.9)
			var dv := Vector2(cos(a), sin(a))
			FX.streak(center() + dv * 6.0, center() + dv * randf_range(22.0, 38.0), Color(1.0, 0.95, 0.85, 0.8), 0.09)
	if crit:
		FX.flash_light(center(), Color(1.0, 0.9, 0.6), 120.0, 1.6, 0.16)
		if not feel_done:
			# saldıran kamera/zaman hissini vermediyse (mermi, tuzak, patlama): burada sade bir kritik hissi
			Game.shake_dir(0.25, Vector2(dir, 0.3))
			Game.slowmo(0.35, 0.08)
			Game.hitstop(0.07)
			if SlashFX.has("crit_burst"):
				FX.slash_sprite("crit_burst", center(), 0.0, Vector2(0.8, 0.8), Color(1.0, 0.92, 0.6), true, Vector2(-1, -1), null, 30.0)
	elif not feel_done and big:
		Game.hitstop(0.05)
	# ses: yaratığın türüne göre acı sesi + darbe
	Ses.play(_hurt_sfx(), -4.0, 1.0, 0.1, 0.05, center())
	var tier := 2 if crit else (1 if big else 0)
	if guard_t > 0.0 and signf(dir) == -float(facing):
		Ses.hit(tier, center(), "metal") if Ses.has_method("hit") else Ses.play("darbe_metal", -2.0)
	elif sprite_kind == "balbal":
		Ses.hit(tier, center(), "tas") if Ses.has_method("hit") else Ses.play("darbe_tas", -3.0)
	elif (crit or not opts.get("sfx_done", false)) and not feel_done:
		# silah sesi saldıran tarafından çalınmadıysa (mermi, patlama, kapan): kademeli darbe sesi; v26: kritik her zaman
		# kritik sesini çalar (silah sesini kendisi çalan dönen balta / yer şoku kritikleri sessizdi)
		if Ses.has_method("hit"):
			Ses.hit(tier, center())
		elif crit:
			Ses.play("darbe_kritik", 0.0)
		elif big:
			Ses.play("darbe_agir", -1.0)
		else:
			Ses.play("darbe_et", -2.0)
	# hava kombosu: havadaki düşman vuruldukça havada kalır
	# v23: zırhlıyken havaya atılmaz; hava kombosu en çok ~1 sn havada tutar (sonsuz hokkabazlık yok)
	if launch_t > 0.0 and not heavy and not flying and not opts.has("launch") and _juggle_t < 1.0:
		velocity.y = minf(velocity.y, -190.0)
		launch_t = maxf(launch_t, 0.45)
		FX.ring(center(), 14, Color(1.0, 0.95, 0.8), 0.15)
	if opts.has("launch") and float(opts["launch"]) > 0.0 and not heavy and not flying and sa_t <= 0.0 and _juggle_t < 1.0:
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
	var big_hit: bool = big or opts.get("stagger", false) or opts.get("heavy", false)
	_ds_hit_age = 0.0     # v29: tepki animasyonu (hafif / ağır sarsılma)
	_ds_hit_big = big_hit
	var now := Game.clock()
	if now - _flinch_last > float(POISE["window"]):
		_flinch_n = 0
	# v19 duruş kırılması: diretirken (zincirle doldu) büyük vuruş (bitiriş / kritik / ağır / karşı vuruş) duruşu kırar;
	# ağır yaratık sarsılmasa da her vuruşun duruş hasarını (opts.poise, silah ağırlığıyla) biriktirir, dolunca kırılır
	var pz := float(opts.get("poise", 0.6 if float(opts.get("kb", 0.0)) > 0.0 else 0.0))
	if not is_boss and hp > 0.0 and now - _break_last > float(POISE["break_cd"]):
		if heavy:
			# yakın vuruş kendi duruş hasarını verir; diğerleri (ok, patlama) 0,6, itmesiz süreğen hasar (kor gölü) hiç
			# v23: zırhlı hamle sürerken yarısı; zırhlı hazırlığa karşı vuruş artık kırmaz (ezbere basış ödüllenmesin)
			poise_pts += pz * (0.5 if sa_t > 0.0 else 1.0)
			if poise_pts >= float(POISE["heavy_pts"]) * (1.6 if elite else 1.0) or (opts.get("counter", false) and crit and sa_t <= 0.0):
				_guard_break(dir)
		elif sa_t > 0.0:
			# v23: hafif yaratığın zırhlı hamlesini yalnızca ağır silah (duruş hasarı ≥ 2) kırar
			if opts.get("heavy", false) or pz >= 2.0:
				_guard_break(dir)
		elif big_hit and now < _poise_until:
			_guard_break(dir)
	# v23: zırhlı hamle (sa_t) ve sarsılma bağışıklığı (_flinch_imm: hafif vuruşlar sarsmaz) sonsuz kilidi önler
	var armored: bool = not is_boss and (sa_t > 0.0 or (not big_hit and (now < _poise_until or now < _flinch_imm)))
	if armored and (not heavy or opts.get("stagger", false) or crit):
		# direniyor: hasar ve küçük itme, sarsılma yok, hazırlık sürer
		_flinch_last = now
		velocity.x = dir * kb * 0.2
		vis_scale = Vector2(1.08, 0.94)
		# v23: sarsılma bağışıklığındaki vuruşlar da diretmeye sayılır (zincir → diretme → bitiriş duruşu kırar)
		if sa_t <= 0.0 and now >= _poise_until and not heavy:
			_flinch_n += 1
			if _flinch_n >= _poise_n() and not is_boss:
				_flinch_n = 0
				_poise_until = now + float(POISE["armor"])
				FX.ring(center(), 14.0, Color(0.95, 0.9, 0.8, 0.8), 0.16)
	elif not heavy or opts.get("stagger", false) or crit:
		_flinch_last = now
		_flinch_n += 1
		if _flinch_n >= _poise_n() and not is_boss:
			_flinch_n = 0
			_poise_until = now + float(POISE["armor"])
			FX.ring(center(), 14.0, Color(0.95, 0.9, 0.8, 0.8), 0.16)
		hurt_t = (float(POISE["flinch_big"]) if big_hit else float(POISE["flinch"])) if not heavy else 0.08
		if not is_boss:
			_flinch_imm = now + (0.5 if big_hit else Zorluk.yz("sarsilmaz", 0.34))   # v26: derinlikte daha uzun
		# v17 takas yok: sarsılan yaratığın süren saldırısı (sıçrama, hücum, çakma teması) kesilir; vurduğun düşman
		# aynı anda sana çarpıp can götürmez. Ağırlar ve bosslar sarsılmadıkça saldırısını sürdürür (önceden okunur).
		if contact and not is_boss:
			contact = false
		velocity.x = dir * kb * (0.4 if heavy else 1.0)
		if not flying and not heavy and not opts.has("launch"):
			velocity.y = minf(velocity.y, -kb * 0.25)
		if state == "windup" and not heavy and big_hit:
			state = "recover"
			st = 0.3
		if anim.has_anim("hurt"):
			anim.play("hurt", true)
	if hp <= 0.0:
		_die(dir, kb, crit)
		return true
	_count_react(now, dir)
	return false


func _poise_n() -> int:
	## v26: diretmeye kadar sarsılma sayısı (zorluk.json "yz.diretme"; seçkin POISE.n_elite)
	if elite:
		return int(POISE["n_elite"])
	return int(Zorluk.yz("diretme", float(POISE["n"])))


func _die(dir := 1.0, kb := 100.0, crit := false) -> void:
	dead = true
	remove_from_group("dusman")
	_drop_token()
	if grab_target and is_instance_valid(grab_target) and "grabbed_by" in grab_target and grab_target.grabbed_by == self:
		grab_target.release_grab(Vector2(-facing * 120.0, -160.0))
	if ai == "kamikaze" and not decoy and level:
		# v23 Işıltı Kamı: ölünce de patlar (küçük, gecikmeli): dibinde öldürmek bedava değil
		_death_blast(level, center(), dmg * 0.7)
	if decoy:
		FX.anim("smoke_puff", center(), 0.0, 0.8, Color(0.6, 0.35, 0.9), false)
		FX.burst(center(), Color(0.75, 0.45, 1.0), 10, 90, 0.4, 0.2, 100)
		FX.text(center() + Vector2(0, -26), "hayalet!", Color(0.8, 0.6, 1.0), 7)
		queue_free()
		return
	Game.run["kills"] = int(Game.run.get("kills", 0)) + 1
	Ses.play(_die_sfx(), 0.0, 1.0, 0.08, 0.03, center())
	if not _feel_done and Ses.has_method("hit"):
		Ses.hit(3, center())
	Game.hitstop(0.06 if not elite else 0.1)
	if crit or elite:
		Game.zoom_punch(0.05 if not elite else 0.08)
	# v14 öldürme: seçkin ya da kritik ölümde darbe karesi; kısa ölüm flaşı sprite'ı
	if elite or is_boss:
		ImpactFrame.play([level.player if level else null, self], 1.0, 3, true)
	if SlashFX.has("kill_flash"):
		FX.slash_sprite("kill_flash", center(), 0.0, Vector2(1.0, 1.0) * (1.4 if elite else 1.0), Color(1.0, 0.97, 0.9), true, Vector2(-1, -1), null, 30.0)
	Game.rumble(0.5 if not elite else 0.8, 0.25, 0.12 if not elite else 0.25)
	if level and level.has_method("ground_y_below"):
		var gy: float = level.ground_y_below(global_position + Vector2(0, -4))
		if gy >= 0.0:
			FX.decal("decal_blood_%d" % (randi() % 3), Vector2(global_position.x + dir * 6.0, gy + 2), 0.0, 10.0, 1.0 + (0.5 if elite else 0.0), Color(blood_col(), 0.85))
	# gövde savrulur, ruh zerreleri göğe yükselir, sıçrantı yere düşer
	if not _ds_death(Vector2(dir * maxf(140.0, kb * 1.3), -220.0 - kb * 0.4)):
		FX.corpse(anim.base, Vector2(dir * maxf(140.0, kb * 1.3), -220.0 - kb * 0.4), blood_col())
	FX.blood(center(), Vector2(dir, -0.8), blood_col(), 16)
	Blood.burst(center(), Vector2(dir, -0.6), blood_col(), 45 + (40 if elite else 0) + (90 if is_boss else 0), (randi_range(4, 6) + (4 if elite else 0) + (10 if is_boss else 0)), is_flesh())
	# sade ölüm: kan + ceset + ruh zerresi okunur; eski koyu kırmızı duman diski ve her ölümde halka kaldırıldı
	# (üst üste 10 katman ekranı bulandırıyordu)
	FX.smoke(center(), 3, 0.4, Color(0.32, 0.3, 0.36, 0.45))
	FX.soul(center(), Color(0.55, 0.95, 1.0), 12 if not elite else 30)
	if elite or is_boss:
		FX.ring(center(), 44, Color(0.6, 0.95, 1.0), 0.3)
	FX.flash_light(center(), Color(0.55, 0.95, 1.0), 100.0, 0.9, 0.2)
	Game.shake_dir(0.22 if not elite else 0.45, Vector2(dir, 0.4))
	Game.kick(Vector2(dir, 0), 3.0)
	if crit or elite:
		Game.slowmo(0.3, 0.14 if not elite else 0.3)
	if level:
		level.on_enemy_died(self)
	queue_free()


func _set_aggro() -> void:
	## v22: fark eden yaratık çevresindekileri de uyandırır (sürü çağrısı; boss / hayalet hariç)
	aggro = true
	if is_boss or decoy or level == null:
		return
	for o in get_tree().get_nodes_in_group("dusman"):
		if o != self and is_instance_valid(o) and not o.dead and not o.aggro and not o.is_boss \
				and o.global_position.distance_squared_to(global_position) < 180.0 * 180.0 and o.state != "dormant":
			o.aggro = true


func _pack_beat() -> void:
	## v22 sürü düzeni: bir yaratık hazırlığa girince oyuncunun çevresindeki öbür saldırganlar aynı kareye yığılmaz
	## (okunur kalsın: en az ~0,3 sn arayla), uzun bekleyenler ise sırayı kapar (pasif beklemek yok)
	if is_boss or level == null or level.player == null:
		return
	var pp: Vector2 = level.player.global_position
	for o in get_tree().get_nodes_in_group("dusman"):
		if o == self or not is_instance_valid(o) or o.dead or o.is_boss or not o.aggro:
			continue
		if o.global_position.distance_squared_to(pp) > 240.0 * 240.0 or o.cd > 50.0:
			continue
		if o.cd < 0.3:
			o.cd = 0.3 + randf() * 0.25
		elif o.cd > 1.1:
			o.cd = lerpf(o.cd, 0.9, 0.6)


func _windup_sfx() -> void:
	## Saldırı uyarısı: her yaratığın kendi hazırlık sesi (yoksa genel) + 2 karelik beyaz flaş ve gerilme (anticipation):
	## oyuncu saldırıyı sesten ve gövdeden aynı anda okur, kusursuz kaçışı zamanlayabilir
	_pack_beat()
	flash_t = maxf(flash_t, 0.035)
	vis_scale = Vector2(0.86, 1.12) if not heavy else Vector2(0.92, 1.06)
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
var _haz_cd := 0.0   # v25: tehlike çukuru yeniden vurmaz (sn)
var _haz_bt := 0.0   # v25: çukurdan sektirilirken kalan süre (yapay zekâ beklemede)
## v18 duruş (Dead Cells esinli): hızlı zincirler yaratığı sonsuza dek kilitlemesin. Kısa sürede art arda sarsılan
## yaratık bir an "diretir" (sarsılmaz, hazırlığı sürer); büyük vuruş (bitiriş, kritik, ağır) direnci yine kırar.
## Hafif vuruş hazırlığı iptal etmez, yalnızca geciktirir (sarsılma süresince yapay zekâ durur).
## v19: diretme 0,75 → 0,6 sn (hızlı zincir daha az "duvara" çarpar), hafif sarsılma 0,12 → 0,1, büyük 0,2 → 0,24 (bitiriş
## daha belirgin itsin). Duruş kırılması: diretirken gelen büyük vuruş ya da ağır yaratıkta biriken duruş hasarı
## (heavy_pts; seçkinde ×1,6) → break_stun sn sersemleme (ağırda break_stun_heavy), bu sürede ×break_dmg hasar; bekleme break_cd.
const POISE := {"n": 4, "n_elite": 2, "window": 0.9, "armor": 0.6, "flinch": 0.1, "flinch_big": 0.24,
	"heavy_pts": 7.0, "heavy_decay": 2.0, "break_stun": 0.9, "break_stun_heavy": 0.7, "break_dmg": 1.25, "break_cd": 2.2}
var poise_pts := 0.0     # v19: ağır yaratıkta biriken duruş hasarı (sn'de heavy_decay söner)
var broken_t := 0.0      # v19: duruşu kırık (sersem, fazla hasar alır, infaz edilebilir)
var _break_last := -9.0
var _flinch_n := 0
var _flinch_last := -9.0
var _poise_until := -9.0
var _feel_done := false  # son darbenin kamera/ses hissini saldıran verdi mi (Player yakın vuruş)
var _slam_t := 0.0
var _bounced := false
# v11 doğal hareket: ölçek ve eğilme yaylarla (hafif aşma, salınarak oturur)
var _sv := Vector2.ZERO
var _lean := 0.0
var _lean_v := 0.0
var _tumble := 0.0
var _was_floor := true
var _prev_vy := 0.0
var _last_facing := 1
var _breath_ph := randf() * TAU


func _motion(delta: float) -> void:
	## İkincil hareket: squash/stretch yayı, hıza göre öne eğilme, nefes, havada uzama, iniş ezilmesi, dönüş sıkışması.
	var k := 200.0 if heavy else 320.0
	var c := 13.0 if heavy else 16.5
	_sv += ((Vector2.ONE - vis_scale) * k - _sv * c) * delta
	vis_scale += _sv * delta
	var fl := is_on_floor()
	var sy := 1.0
	if fl and absf(velocity.x) < 20.0:
		sy += (0.012 if heavy else 0.02) * sin(Time.get_ticks_msec() * (0.0019 if heavy else 0.0026) + _breath_ph)
	elif not fl and not flying:
		sy += clampf(absf(velocity.y) / 2600.0, 0.0, 0.14)
	anim.scale = base_scale * vis_scale * Vector2(1.0 / sqrt(sy), sy)
	var tgt := clampf(velocity.x / maxf(speed, 60.0), -1.8, 1.8) * (0.15 if flying else (0.045 if heavy else 0.075))
	if flying:
		tgt += clampf(velocity.y / 400.0, -0.3, 0.3) * 0.12 * float(facing)
	_lean_v += ((tgt - _lean) * 170.0 - _lean_v * 17.0) * delta
	_lean += _lean_v * delta
	_hit_tilt = lerpf(_hit_tilt, 0.0, clampf(delta * 12.0, 0.0, 1.0))
	if launch_t <= 0.0:
		_tumble = lerpf(_tumble, 0.0, clampf(delta * 9.0, 0.0, 1.0))
	anim.rotation = _hit_tilt + _lean + _tumble
	if fl and not _was_floor and _prev_vy > 150.0 and not flying:
		var q := clampf(_prev_vy / 650.0, 0.0, 1.0) * (0.7 if heavy else 1.0)
		vis_scale = Vector2(1.0 + 0.38 * q, 1.0 - 0.32 * q)
		_sv = Vector2.ZERO
		FX.dust(global_position, Vector2.UP, int(2 + 6 * q), 0.24 + 0.14 * q)
		if heavy and q > 0.4:
			Game.shake(1.5 + 3.0 * q)
	_was_floor = fl
	_prev_vy = velocity.y
	if facing != _last_facing:
		_last_facing = facing
		vis_scale.x *= 0.8
		vis_scale.y *= 1.06


# ================================================================== v29 evre eşlemeli animasyon (yönetmen)
## Sprite json'unda "durum" varsa kareyi yapay zekâ değil bu yönetmen seçer (docs/v29/enemy_anim_json.md): yapay zekânın
## play / show_frame çağrıları yalnızca istek olarak kalır (SpriteAnim.req); json "durum" eşlemesi durumu, hamleyi ve
## zırhı ("!!") animasyon evresine bağlar; hazırlık st / st0 ile ilerler (derin kurulma karesi tutulur, "lead" karesi
## isabetten hemen önce), havadaki hamleler dikey hızla, tepkiler (sarsılma, savrulma, kalkış, dönüş, sersemleme)
## kendi süreleriyle. Zamanlar, vuruş kutuları ve yapay zekâ DEĞİŞMEZ: yalnızca görsel.
var _ds_on := false
var _ds: Dictionary = {}
var _ds_reset := false
var _ds_state := ""
var _ds_prev := ""
var _ds_move := ""
var _ds_aa := false
var _ds_t := 0.0
var _ds_st0 := 0.0
var _ds_vy0 := 0.0
var _ds_hit_age := 99.0
var _ds_hit_big := false
var _ds_air := false
var _ds_air_vy0 := -200.0
var _ds_last_vy := 0.0
var _ds_getup := 99.0
var _ds_turn := 99.0
var _ds_face := 0
var _ds_roar := 99.0
var _ds_elite_prev := 0.0
var _ds_cache: Dictionary = {}   # arama anahtarı -> giriş (ya da {}) önbelleği
var _ds_spawn := 99.0
var _ds_blink := 99.0


func _ds_setup() -> void:
	## "durum" sözlüğü olan her sayfada açılır. İki biçim (docs/v29/enemy_anim_json.md): giriş sözlüğü
	## {"a", "s", "u", "d"} ya da kısa biçim "durum adı": "satır adı" (uçan / büyücü sayfaları). Kısa adlar
	## eşlenir: windup_zirh -> windup!!, death -> _death, spawn -> _spawn, explode -> kamikaze:windup.
	var raw: Variant = anim.meta.get("durum", null)
	_ds_on = raw is Dictionary and not (raw as Dictionary).is_empty()
	anim.director = _ds_on
	if not _ds_on:
		return
	_ds = {}
	const ALIAS := {"windup_zirh": "windup!!", "death": "_death", "spawn": "_spawn", "explode": "kamikaze:windup"}
	for k in (raw as Dictionary).keys():
		var v: Variant = raw[k]
		var e: Dictionary = v if v is Dictionary else {"a": String(v), "u": "auto"}
		_ds[String(k)] = e
		if ALIAS.has(String(k)) and not (raw as Dictionary).has(ALIAS[k]):
			_ds[ALIAS[k]] = e
	_ds_face = facing
	_ds_spawn = 0.0 if _ds.has("_spawn") else 99.0


func _process(delta: float) -> void:
	if _ds_on and not dead and anim != null:
		_anim_tick(delta)


func _ds_move_now() -> String:
	if has_meta("rev"):
		return String(get_meta("rev"))
	if ai == "charger":
		return "bash" if get_meta("bash", false) else "charge"
	if ai == "pouncer" and get_meta("pounce", false):
		return "pounce"
	return String(get_meta("move", ""))


func _ds_get(k: String) -> Dictionary:
	return _ds[k] if _ds.has(k) else {}


func _ds_lookup() -> Dictionary:
	## durum anahtarı arama sırası: geçiş, ai:durum/hamle(!!), durum/hamle(!!), ai:durum(!!), durum(!!)
	var ck := "%s|%s|%s|%s" % [_ds_prev, _ds_state, _ds_move, "1" if _ds_aa else "0"]
	if _ds_cache.has(ck):
		return _ds_cache[ck]
	var keys: Array = ["%s>%s" % [_ds_prev, _ds_state]]
	var bases: Array = []
	if _ds_move != "":
		bases.append("%s:%s/%s" % [ai, _ds_state, _ds_move])
		bases.append("%s/%s" % [_ds_state, _ds_move])
	bases.append("%s:%s" % [ai, _ds_state])
	bases.append(_ds_state)
	for b in bases:
		if _ds_aa:
			keys.append(String(b) + "!!")
		keys.append(b)
	var e: Dictionary = {}
	for k in keys:
		if _ds.has(k):
			e = _ds[k]
			break
	_ds_cache[ck] = e
	return e


func _anim_tick(delta: float) -> void:
	if freeze_t > 0.0:
		return   # donmuş: kare olduğu yerde
	# ---- durum saati
	if state != _ds_state or _ds_reset:
		var mv := _ds_move_now()
		if mv == "" and not (state in ["idle", "chase", "perch", "dormant", "lurk"]) and state != _ds_state:
			mv = _ds_move   # hamle bir sonraki duruma taşınır (pusu: windup -> leap)
		if state in ["idle", "chase", "perch"]:
			mv = ""
		if state != _ds_state:
			_ds_prev = _ds_state
		_ds_state = state
		_ds_move = mv
		_ds_aa = sa_t > 0.0
		_ds_reset = false
		_ds_t = 0.0
		_ds_st0 = maxf(st, 0.0)
		_ds_vy0 = velocity.y
	_ds_t += delta
	_ds_hit_age += delta
	_ds_getup += delta
	_ds_turn += delta
	_ds_roar += delta
	_ds_spawn += delta
	_ds_blink += delta
	if elite and elite_t > _ds_elite_prev + 1.0:
		_ds_roar = 0.0
	_ds_elite_prev = elite_t
	var loco := state in ["idle", "chase", "perch"]
	if facing != _ds_face:
		_ds_face = facing
		if loco:
			_ds_turn = 0.0
	# ---- havaya savrulma (dikey hız evresi) ve iniş sonrası kalkış
	var air := launch_t > 0.0 or sanat_tut > 0.0
	if air:
		if not _ds_air or (velocity.y < -40.0 and _ds_last_vy > 40.0):
			_ds_air_vy0 = minf(velocity.y, -120.0)
		_ds_air = true
	elif _ds_air:
		_ds_air = false
		_ds_getup = 0.0
	_ds_last_vy = velocity.y
	var e: Dictionary = {}
	var u := -1.0
	if air and _ds.has("_launch"):
		e = _ds["_launch"]
		u = (velocity.y - _ds_air_vy0) / (-2.0 * _ds_air_vy0)
	elif (broken_t > 0.0 or stun_t > 0.0) and _ds.has("_break"):
		e = _ds["_break"]
	else:
		var hk := "_hurt_big" if _ds_hit_big and _ds.has("_hurt_big") else "_hurt"
		var he := _ds_get(hk)
		var calm := loco or state in ["recover", "guard", "dormant"]
		if not he.is_empty() and _ds_hit_age < float(he.get("d", 0.25)) and (hurt_t > 0.0 or (calm and sa_t <= 0.0)):
			e = he
			u = _ds_hit_age / float(he.get("d", 0.25))
		elif _ds_getup < float(_ds_get("_getup").get("d", 0.0)) and (loco or state == "recover") and absf(velocity.x) < 40.0:
			e = _ds["_getup"]
			u = _ds_getup / float(e.get("d", 0.5))
		elif _ds_blink < _ds_dur(_ds_get("blink_in")) and (loco or state == "recover"):
			e = _ds["blink_in"]
			u = _ds_blink / _ds_dur(e)
		elif _ds_spawn < _ds_dur(_ds_get("_spawn")) and (loco or state in ["recover", "dormant", "perch", "lurk"]):
			e = _ds["_spawn"]
			u = _ds_spawn / _ds_dur(e)
		else:
			e = _ds_lookup()
			if e.is_empty() and loco:
				if guard_t > 0.0 and _ds.has("_guard"):
					e = _ds["_guard"]
					if String(e.get("u", "")) == "up":
						u = clampf(_ds_t / float(e.get("d", 0.5)), 0.0, 1.0)
				elif _ds_turn < float(_ds_get("_turn").get("d", 0.0)) and absf(velocity.x) < 60.0:
					e = _ds["_turn"]
					u = _ds_turn / float(e.get("d", 0.2))
				elif _ds_roar < float(_ds_get("_roar").get("d", 0.0)) and absf(velocity.x) < 30.0:
					e = _ds["_roar"]
					u = _ds_roar / float(e.get("d", 0.8))
	if e.is_empty():
		_ds_fallback()
		return
	_ds_show(e, u)


func _ds_show(e: Dictionary, u_in: float) -> void:
	var a := String(e.get("a", ""))
	if not anim.has_anim(a):
		_ds_fallback()
		return
	var am: Dictionary = anim.meta["anims"][a]
	var mode := String(e.get("u", "st"))
	if mode == "auto":
		# kısa biçim: döngü satırı döner; "mk" [W, C, H] taşıyan satır evre zamanına (Bengü v28 kuralı) eşlenir;
		# yoksa geri sayan durumda st / st0, ileri sayanda satırın kendi süresi (kare / fps)
		if bool(am.get("loop", false)) and u_in < 0.0:
			anim.drive_loop(a, _ds_vx_speed(am))
			return
		if am.has("mk") and u_in < 0.0:
			_ds_show_mk(a, am)
			return
		mode = "st" if _ds_st0 > 0.001 else "up"
		if mode == "up" and not e.has("d"):
			e = e.duplicate()
			e["d"] = _ds_dur(e)
	if mode == "loop" and u_in < 0.0:
		anim.drive_loop(a, _ds_vx_speed(am))
		return
	var n := int(am["frames"])
	var i0 := 0
	var i1 := n
	var sname := String(e.get("s", ""))
	if sname != "" and am.has("seg") and (am["seg"] as Dictionary).has(sname):
		var sg: Array = am["seg"][sname]
		i0 = clampi(int(sg[0]), 0, n - 1)
		i1 = clampi(int(sg[1]), i0 + 1, n)
	var u := u_in
	var lead := 0.0
	if u < 0.0:
		match mode:
			"up":
				u = _ds_t / maxf(0.01, float(e.get("d", 0.5)))
			"vy":
				if _ds_vy0 < -30.0:
					u = (velocity.y - _ds_vy0) / (-2.0 * _ds_vy0)
				else:
					u = _ds_t / maxf(0.01, float(e.get("d", 0.6)))
			_:
				if _ds_st0 > 0.001:
					u = 1.0 - maxf(st, 0.0) / _ds_st0
					if am.has("lead") and sname != "" and (am["lead"] as Dictionary).has(sname):
						lead = float(am["lead"][sname])
				else:
					u = _ds_t / maxf(0.01, float(e.get("d", 0.4)))
	u = clampf(u, 0.0, 1.0)
	var last := i1 - 1
	if lead > 0.0 and i1 - i0 >= 2:
		if maxf(st, 0.0) <= lead:
			anim.drive(a, last)
			return
		# lead karesi dışındaki kareler kalan süreye yayılır
		u = clampf((_ds_st0 - maxf(st, 0.0)) / maxf(0.001, _ds_st0 - lead), 0.0, 0.9999)
		last = i1 - 2
	var ts: Array = am.get("ts", [])
	var f := i0
	if ts.size() == n:
		for i in range(i0, last + 1):
			if float(ts[i]) <= u + 0.0001:
				f = i
	else:
		f = i0 + mini(int(u * float(last - i0 + 1)), last - i0)
	anim.drive(a, f)


func _ds_dur(e: Dictionary) -> float:
	## giriş süresi: "d" ya da satırın kendi süresi (kare / fps)
	if e.is_empty():
		return 0.0
	if e.has("d"):
		return float(e["d"])
	var a := String(e.get("a", ""))
	if not anim.has_anim(a):
		return 0.0
	var am: Dictionary = anim.meta["anims"][a]
	return float(am["frames"]) / maxf(1.0, float(am.get("fps", 10)))


func _ds_show_mk(a: String, am: Dictionary) -> void:
	## "mk" = [W, C, H] satırı: hazırlık durumu [0, W] (son 0,05 sn süpürme [W, C]), vuruş / etkin durumlar [C, H],
	## toparlanma [H, 1]. Kare: başlangıç anı (ts; yoksa eşit aralık) bu zamanı geçmemiş son kare.
	var mk: Array = am["mk"]
	var w := float(mk[0])
	var c := float(mk[1])
	var h := float(mk[2])
	var p := 1.0 - maxf(st, 0.0) / _ds_st0 if _ds_st0 > 0.001 else clampf(_ds_t / 0.4, 0.0, 1.0)
	p = clampf(p, 0.0, 1.0)
	var tau := 0.0
	if _ds_state == "windup":
		if _ds_st0 > 0.001 and maxf(st, 0.0) <= 0.05:
			tau = lerpf(w, c, 1.0 - maxf(st, 0.0) / 0.05)
		else:
			tau = w * p
	elif _ds_state == "recover":
		tau = lerpf(h, 1.0, p)
	else:
		tau = lerpf(c, h, p)
	var n := int(am["frames"])
	var ts: Array = am.get("ts", [])
	var f := 0
	if ts.size() == n:
		for i in n:
			if float(ts[i]) <= tau + 0.0001:
				f = i
	else:
		f = mini(int(tau * float(n)), n - 1)
	anim.drive(a, f)


func _ds_vx_speed(am: Dictionary) -> float:
	if am.has("vx") and float(am["vx"]) > 0.0:
		return clampf(absf(velocity.x) / float(am["vx"]), 0.5, 2.2)
	return 1.0


func _ds_fallback() -> void:
	## eşleme yok: yapay zekânın istediği animasyon (döngüde adım kilidi ve yavaş hız yedeği "alt")
	var r := anim.req
	if r == "" or not anim.has_anim(r):
		return
	var am: Dictionary = anim.meta["anims"][r]
	if anim.req_frame >= 0:
		anim.drive(r, anim.req_frame)
		return
	if am.get("loop", false):
		for alt in am.get("alt", []):
			if absf(velocity.x) < float(alt[1]) and anim.has_anim(String(alt[0])):
				r = String(alt[0])
				am = anim.meta["anims"][r]
				break
		anim.drive_loop(r, _ds_vx_speed(am))
		return
	if anim.anim != r or anim.manual or anim.req_restart:
		anim.drive_loop(r, 1.0, true)
	anim.req_restart = false


func _ds_death(vel: Vector2) -> bool:
	## v29 ölüm kareleri (json "_death"): ceset satırı d sn'de oynar, dönmeden kayar, sonra çözülür
	if not _ds_on or not _ds.has("_death") or FX.root == null:
		return false
	var e: Dictionary = _ds["_death"]
	var a := String(e.get("a", ""))
	if not anim.has_anim(a):
		return false
	var am: Dictionary = anim.meta["anims"][a]
	var n := int(am["frames"])
	var frames: Array = []
	for i in n:
		frames.append(anim.frame_rect(a, i))
	var ts: Array = am.get("ts", [])
	if ts.size() != n:
		ts = []
		for i in n:
			ts.append(float(i) / float(n))
	anim.drive(a, 0)
	var c := Corpse.new()
	c.setup(anim.base, vel, blood_col())
	FX.root.add_child(c)
	c.play_frames(frames, ts, _ds_dur(e) if _ds_dur(e) > 0.0 else 0.9, global_position, is_on_floor(), anim.base)
	return true


func _ds_blink_out() -> void:
	## v29 kısa biçim "blink_out": ışınlanmadan önceki yerde satır bir kez oynar ve çözülür (blink_in: yeni yerde belirme)
	if not _ds_on or not _ds.has("blink_out") or FX.root == null:
		return
	var a := String(_ds["blink_out"].get("a", ""))
	if not anim.has_anim(a):
		return
	var am: Dictionary = anim.meta["anims"][a]
	var n := int(am["frames"])
	var frames: Array = []
	var ts: Array = []
	for i in n:
		frames.append(anim.frame_rect(a, i))
		ts.append(float(i) / float(n))
	anim.drive(a, 0)
	var c := Corpse.new()
	c.setup(anim.base, Vector2.ZERO, Color(0.55, 0.3, 0.8))
	FX.root.add_child(c)
	c.play_frames(frames, ts, _ds_dur(_ds["blink_out"]), global_position, true, anim.base)

func _wall_slam() -> void:
	## Geri itilirken duvara çarptı: ek hasar, kıvılcım, kısa duraklama (Dead Cells duvar çarpması)
	_slam_t = 0.0
	var d := 7.0 * Zorluk.dot_k()   # v22: eşya gücüyle ölçeklenir
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


func _guard_break(dir: float) -> void:
	## v19 duruş kırıldı: sersemler (hazırlık kesilir), kısa süre fazla hasar alır; canı azsa oyuncu infaz edebilir
	## (exec_ok, StatusOverlay kızıl mühür çizer)
	sa_t = 0.0
	_stun_n = 0
	_stun_last = -9.0
	if has_meta("rev"):
		remove_meta("rev")
	_break_last = Game.clock()
	_poise_until = -9.0
	_flinch_n = 0
	poise_pts = 0.0
	var t := float(POISE["break_stun_heavy"] if heavy else POISE["break_stun"])
	broken_t = t
	stun(t)
	contact = false
	FX.text(center() + Vector2(0, -size.y * 0.5 - 14.0), "DURUŞ KIRILDI", Color(1.0, 0.8, 0.45), 8)
	InkFX.ring(center(), 20.0 + size.y * 0.15, 9, 0.3)
	InkFX.hit("blunt", center(), Vector2(dir, -0.2), 9, 1, 0.9)
	Ses.play("darbe_kunt", -4.0, 0.8)
	Game.hitstop(0.03)
	vis_scale = Vector2(0.8, 1.15)
	if level and level.player and "v19_stats" in level.player:
		level.player.v19_stats["kirilma"] = int(level.player.v19_stats["kirilma"]) + 1


func exec_ok() -> bool:
	## v19 Kut Alma: duruşu kırık / sersem / donmuş ya da kalkanı düşmüş ve canı az (Player.V19.ex_hp; seçkinde
	## ex_hp_elite) yaratık infaz edilebilir. Bosslar ve hayaletler hariç.
	if dead or is_boss or decoy or max_hp <= 0.0:
		return false
	if not (broken_t > 0.0 or stun_t > 0.0 or state == "stagger" or freeze_t > 0.0):
		return false
	return hp <= max_hp * float(Player.V19["ex_hp_elite"] if elite else Player.V19["ex_hp"])


# ------------------------------------------------------------------ yapay zekâ
func _physics_process(delta: float) -> void:
	if dead:
		return
	var player: Node = level.player if level else null
	_tick_status(delta)
	if dead:
		return
	_motion(delta)
	if sanat_tut > 0.0:
		_sanat_kilit(delta)
		return
	if _hazard_tick(delta):
		return
	if _slam_t > 0.0:
		_slam_t -= delta
		if is_on_wall() and absf(velocity.x) > 40.0:
			_wall_slam()
	if launch_t > 0.0:
		# havaya fırlatıldı: çaresizce düşer, yere çarpınca toz; hızlı düşüşte bir kez seker
		launch_t -= delta
		_juggle_t += delta
		velocity.x = move_toward(velocity.x, 0.0, 300 * delta)
		velocity.y = minf(velocity.y + 1100.0 * delta, 540.0)
		_tumble = lerpf(_tumble, -0.7 * float(facing), clampf(delta * 5.0, 0.0, 1.0))
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
			_juggle_t = 0.0
			_bounced = false
			vis_scale = Vector2(1.3, 0.7)
			FX.dust(global_position, Vector2.UP, 6, 0.3)
			Game.shake(2.0)
		if Engine.get_physics_frames() % 3 == 0:
			FX.ghost(anim.base, Color(1.0, 0.85, 0.6, 0.3), 0.2)
		return
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
		# geri itme üstel söner: ilk kareler hızlı, sonra yumuşak oturma (doğrusal fren "kayma" gibi okunur)
		velocity.x = lerpf(velocity.x, 0.0, 1.0 - exp(-9.0 * delta))
		if not flying:
			velocity.y = minf(velocity.y + 1100.0 * delta, 540.0)
		move_and_slide()
		if hurt_t <= 0.0 and anim.anim == "hurt":
			anim.play("idle")
		return
	# v22: saldırganlık (bekleme daha hızlı söner) ve hazırlığın hafif hızlanması derinlikle (Zorluk)
	cd -= delta * _aggr
	if state == "windup" and _wind_k > 1.0:
		st -= delta * (_wind_k - 1.0)
	var to_p := Vector2.ZERO
	var dist := 9999.0
	if player and not player.dead:
		to_p = player.center() - center()
		dist = to_p.length()
		if not aggro and dist < 290.0 and absf(to_p.y) < 120.0 and level.los(center(), player.center()):
			_set_aggro()
		elif aggro and dist > 520.0:
			aggro = false
	if elite and aggro and player and not player.dead:
		_elite_tick(delta, player, dist)
	_dt = delta
	_track_player(delta, player)
	if state == "evade":
		_tick_evade(delta, player, to_p)
		_post_move(player)
		return
	if has_meta("rev") and state in ["windup", "rev"]:
		_tick_revenge(delta, player, to_p)
		_post_move(player)
		return
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
			# v23: kalkanı toparlanan bekçi hemen zırhlı kalkan darbesiyle karşılık verir (sonsuz kalkan kırma yok)
			if not _passive() and ai in ["shield", "charger"] and player and not player.dead and dist < 120.0:
				_revenge("bash")
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
		"crawler":
			_ai_crawler(delta, player, to_p, dist)
		"swarm":
			_ai_swarm(delta, player, to_p, dist)
		"caster":
			_ai_caster(delta, player, to_p, dist)
		"kamikaze":
			_ai_kamikaze(delta, player, to_p, dist)
		"tornado":
			_ai_tornado(delta, player, to_p, dist)
		"charmer":
			_ai_charmer(delta, player, to_p, dist)
		"mimic":
			_ai_mimic(delta, player, to_p, dist)
		_:
			_ai_custom(delta, player, to_p, dist)
	guard_t = maxf(0.0, guard_t - delta)
	_post_move(player)


func _sanat_kilit(delta: float) -> void:
	## v28 Göğe Yükseliş: havada askı (hedefe yay gibi çekilir, küçük salınım SavasSanati'nde) ya da yere çakılış.
	## Hareket move_and_slide ile: duvara, tavana giremez. Kilit tazelenmezse kendiliğinden düşer (launch_t).
	sanat_tut -= delta
	contact = false
	warn.visible = false
	launch_t = 0.0
	flash_t -= delta
	anim.set_flash(1.0 if flash_t > 0.0 else 0.0)
	if sanat_dus:
		velocity = Vector2(lerpf(velocity.x, (sanat_hedef.x - global_position.x) * 10.0, 0.3), 1150.0)
		move_and_slide()
		_tumble = lerpf(_tumble, 0.5 * float(facing), clampf(delta * 10.0, 0.0, 1.0))
		if is_on_floor():
			sanat_dus = false
			sanat_indi = true
			sanat_tut = 0.0
			velocity = Vector2.ZERO
			vis_scale = Vector2(1.45, 0.6)
			_sv = Vector2.ZERO
			_tumble = 0.0
			stun(0.8)
		elif sanat_tut <= 0.0:
			sanat_dus = false
			launch_t = 0.4
		return
	var to := sanat_hedef - global_position
	velocity = (to * 16.0).limit_length(1100.0)
	move_and_slide()
	_tumble = lerpf(_tumble, (-0.35 * float(facing)) if is_nan(sanat_egim) else sanat_egim, clampf(delta * 6.0, 0.0, 1.0))
	if sanat_tut <= 0.0:
		launch_t = 0.4   # bırakıldı: olağan düşüş
		sanat_egim = NAN


func _post_move(player: Node) -> void:
	## Yerçekimi, hareket, uyarı ("!" / "!!") ve temas hasarı (contact_k: hamleye özgü çarpan)
	if not flying:
		velocity.y = minf(velocity.y + 1100.0 * _dt, 540.0)
	move_and_slide()
	anim.set_facing(facing)
	warn.visible = state == "windup" and int(Time.get_ticks_msec() / 90) % 2 == 0
	if contact and player and not player.dead and not _did_hit and hurt_rect().intersects(player.hurt_rect()):
		if player.take_hit(dmg * contact_k, self):
			_did_hit = true


func _tick_status(delta: float) -> void:
	if has_meta("unsur"):
		Unsur.tick(self, delta)   # v20: unsur durumu (ayaz yükü, töz damgası)
	stun_t = maxf(0.0, stun_t - delta)
	sa_t = maxf(0.0, sa_t - delta)
	evade_t = maxf(0.0, evade_t - delta)
	_blink_cd = maxf(0.0, _blink_cd - delta)
	if launch_t <= 0.0 and is_on_floor():
		_juggle_t = 0.0
	broken_t = maxf(0.0, broken_t - delta)
	poise_pts = maxf(0.0, poise_pts - float(POISE["heavy_decay"]) * delta)
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
	if hp < max_hp * 0.35 and Engine.get_physics_frames() % 11 == 0 and randf() < 0.6:
		Blood.drip(center() + Vector2(0, 4), blood_col())
	if bleed_t > 0.0:
		bleed_t -= delta
		if bleed_t <= 0.0:
			bleed = 0
		elif Engine.get_physics_frames() % 16 == 0:
			Blood.drip(center() + Vector2(randf_range(-4, 4), 0), blood_col(), 3)
	if poison_t > 0.0:
		poison_t -= delta
		if poison_t <= 0.0:
			poison = 0
		elif Engine.get_physics_frames() % 10 == 0:
			FX.bubbles(center() + Vector2(0, -2), 1 + poison / 2)
	if _dot_t <= 0.0:
		_dot_t = 0.5
		var dk := Zorluk.dot_k()   # v22: süreğen hasar oyuncunun eşya kademesiyle (eski: 1 + 0,6 x kademe)
		var dot := 0.0
		if burn_t > 0.0:
			dot += 3.0 * dk
		if bleed > 0:
			dot += 1.6 * bleed * dk
		if poison > 0:
			dot += 1.4 * poison * dk
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
	return level.solid_at(ahead) or not level.ground_at(below) or _haz_ahead(ahead, below)


func _haz_ahead(ahead: Vector2, below: Vector2) -> bool:
	## v25: tehlike çukuru (diken / zehir / lav) uçurum kenarı sayılır: yaratık içine yürümez (buz hariç)
	if flying or level == null or not level.has_method("hazard_at"):
		return false
	var h1: String = level.hazard_at(below)
	var h2: String = level.hazard_at(ahead)
	return (h1 != "" and h1 != "buz") or (h2 != "" and h2 != "buz")


func _hazard_tick(delta: float) -> bool:
	## v25: tehlike çukuruna itilen / düşen yaratık BİR kez hasar alır (azami canın %12'si) ve en yakın kenara sektirilir;
	## içinde kaldıkça vurulmaz (1,2 sn). Sektirme sürerken yapay zekâ çalışmaz. Uçanlar ve bosslar etkilenmez.
	## true: bu karede sektirme hareketi uygulandı.
	_haz_cd -= delta
	if _haz_bt > 0.0:
		_haz_bt -= delta
		velocity.y = minf(velocity.y + 1100.0 * delta, 540.0)
		move_and_slide()
		if is_on_floor() and _haz_bt < 0.5:
			_haz_bt = 0.0
		return true
	if flying or is_boss or level == null or _haz_cd > 0.0 or not level.has_method("hazard_at"):
		return false
	var hz: String = level.hazard_at(global_position + Vector2(0, -4))
	if hz == "":
		hz = level.hazard_at(global_position + Vector2(0, 2))
	if hz == "" or hz == "buz":
		return false
	_haz_cd = 1.2
	var d := max_hp * 0.12
	hp -= d
	flash_t = 0.12
	FX.number(center(), d, false, Color(1.0, 0.45, 0.35))
	if level.has_method("hazard_jab"):
		level.hazard_jab(global_position, hz)
	if hp <= 0.0:
		_die(float(facing), 60.0)
		return true
	var out: Vector2 = level.pit_exit(global_position, -facing) if level.has_method("pit_exit") else Vector2.INF
	var vx := -float(facing) * 150.0
	if out != Vector2.INF:
		var dx: float = out.x - global_position.x
		vx = signf(dx) * clampf(absf(dx) / 0.75 + 20.0, 100.0, 300.0)
	velocity = Vector2(vx, -440.0)
	_haz_bt = 0.9
	vis_scale = Vector2(0.8, 1.2)
	return true


func _patrol(delta: float) -> void:
	velocity.x = move_toward(velocity.x, facing * speed * 0.35, 400 * delta)
	if _wall_or_ledge() or absf(global_position.x - home.x) > 90.0 and sign(global_position.x - home.x) == facing:
		facing = -facing


# ================================================================== v23 ortak yapay zekâ
## Zırh, kaçış, tepki ve jeton durumları (docs/TASARIM.md "v23: yapay zeka ve boss mekanikleri")
var _juggle_t := 0.0     # havada tutulma süresi (hava kombosu sınırı)
var sa_t := 0.0          # zırhlı hamle: hafif vuruş sarsmaz / kesmez ("!!")
var evade_t := 0.0       # geri sıçrayış / ışınlanma dokunulmazlığı
var contact_k := 1.0     # temas hasarı çarpanı (hamleye özgü)
var _dt := 0.016
var _stun_n := 0
var _stun_last := -9.0
var _flinch_imm := -9.0
var _react_n := 0
var _react_last := -9.0
var _react_cd := -9.0
var _hit_last := -9.0
var _turn_t := 0.0
var _block_n := 0
var _block_last := -9.0
var _blink_cd := 0.0
var _beam: Node2D
## saldırı jetonları: örnek kimliği -> [bitiş zamanı, uzak mı]; oyuncunun çevresinde aynı anda sınırlı saldırgan
static var _tok: Dictionary = {}
## oyuncunun kıpırdamadan durduğu süre (uzaktan saldıranlar yerine tehlike koyar)
static var _pl_still := 0.0
static var _pl_frame := -1


func _passive() -> bool:
	## test mankeni (dovus_testi cd'yi 99'a çeker): tepki, kaçış, intikam yok
	return cd > 50.0


func _token(ranged := false) -> bool:
	## Saldırı jetonu al: aynı anda en çok _melee_cap() yakın / 2 uzak saldırgan (seçkin ve tek düşman hep alır)
	if _passive():
		return false
	var now := Game.clock()
	var id := get_instance_id()
	var n := 0
	for k in _tok.keys():
		var v: Array = _tok[k]
		if float(v[0]) < now or not is_instance_id_valid(int(k)):
			_tok.erase(k)
			continue
		if int(k) == id:
			return true
		if bool(v[1]) == ranged:
			n += 1
	if n >= (2 if ranged else _melee_cap()) and not elite:
		return false
	_tok[id] = [now + 3.0, ranged]
	return true


func _drop_token() -> void:
	_tok.erase(get_instance_id())


static func _melee_cap() -> int:
	## v26: derinliğe göre zorluk.json "yz.jeton" (1. derinlik 1: öğrenilir; sonra 2, 6.'dan sonra 3)
	var d := Zorluk.derinlik()
	return int(Zorluk.yz("jeton", 1.0 + (1.0 if d >= 3 else 0.0) + (1.0 if d >= 7 else 0.0)))


func _track_player(delta: float, player: Node) -> void:
	var f := Engine.get_physics_frames()
	if f == _pl_frame or player == null:
		return
	_pl_frame = f
	if player.velocity.length() < 12.0 and player.is_on_floor():
		_pl_still += delta
	else:
		_pl_still = 0.0


func _tele(t: float, armored := false) -> void:
	## Saldırı hazırlığı: "!" (karşı vuruşla kesilir) ya da "!!" (zırhlı, turuncu: yalnız kritik alır; ağır vuruş,
	## çarpışma ve duruş kırılması keser). Baskı altındaki (son 0,8 sn'de vurulmuş) yaratık zırhlı saldırır.
	if not armored and not _passive() and not is_boss and Game.clock() - _hit_last < Zorluk.yz("baski", 0.8):
		armored = true
		t = maxf(t, 0.3)
	state = "windup"
	st = t
	sa_t = t + 0.3 if armored else 0.0
	_ds_reset = true   # v29: aynı durum yeniden başlasa da evre saati sıfırlanır
	set_meta("v26_tele_t", Game.clock())   # v26: karşı vuruş yalnızca bu andan sonra başlayan savuruşa
	warn.text = "!!" if armored else "!"
	warn.label_settings.font_color = Color(1.0, 0.62, 0.12) if armored else Color(1.0, 0.35, 0.25)
	warn.position = Vector2(-8.0 if armored else -4.0, -size.y - 26.0)
	_windup_sfx()
	if armored and not is_boss:
		FX.ring(center(), 14.0 + size.y * 0.25, Color(1.0, 0.62, 0.2, 0.75), 0.2)


func _pa(names: Array) -> void:
	## var olan ilk animasyonu oynat (sprite'lar farklı adlar taşır)
	for n in names:
		if anim.has_anim(String(n)):
			anim.play(String(n))
			return


func _side_of(player: Node) -> float:
	var s := signf(global_position.x - player.global_position.x)
	return s if s != 0.0 else -float(facing)


func _blocked(d: float) -> bool:
	if level == null:
		return false
	var ahead := global_position + Vector2(d * (size.x / 2.0 + 4.0), -6)
	var below := global_position + Vector2(d * (size.x / 2.0 + 4.0), 6)
	return level.solid_at(ahead) or (not flying and not level.ground_at(below)) or _haz_ahead(ahead, below)


func _walk_to(tx: float, spd: float, acc: float, delta: float) -> void:
	var dx := tx - global_position.x
	var want := 0.0
	if absf(dx) > 6.0:
		want = signf(dx) * spd * clampf(absf(dx) / 30.0, 0.35, 1.0)
	if want != 0.0 and _blocked(signf(want)):
		want = 0.0
	velocity.x = move_toward(velocity.x, want, acc * delta)


func _orbit(delta: float, player: Node, to_p: Vector2, r0: float, r1: float, spd: float, behind := false) -> void:
	## Jetonsuz yakın dövüşçü: oyuncunun çevresinde bant içinde salınır (beklemez); behind: arkasına geçer
	var side := _side_of(player)
	if behind:
		side = -float(player.facing)
	var ph := sin(Game.clock() * 1.9 + _breath_ph) * 0.5 + 0.5
	_walk_to(player.global_position.x + side * lerpf(r0, r1, ph), spd, 800.0, delta)
	_face(to_p)


func _turn(to_p: Vector2, delay: float, delta: float) -> void:
	## Yavaş dönen ağır yaratık (kalkanlı, dev): arkasına geçen oyuncuya delay sn açık kalır
	if absf(to_p.x) < 6.0:
		return
	if int(signf(to_p.x)) != facing:
		_turn_t += delta
		if _turn_t >= delay:
			facing = -facing
			_turn_t = 0.0
			vis_scale = Vector2(0.86, 1.08)
	else:
		_turn_t = 0.0


func _strike(w: float, h: float, k: float, push := Vector2.ZERO, off := 0.0, both := false) -> bool:
	## Gövdenin önündeki (both: iki yanındaki) w x h kutu oyuncuya değerse dmg × k ve itme
	if level == null or level.player == null:
		return false
	var pl: Node = level.player
	var box := Rect2(global_position.x + (off if facing > 0 else -off - w), global_position.y - h, w, h)
	if both:
		box = Rect2(global_position.x - w, global_position.y - h, w * 2.0, h)
	if pl.dead or not box.intersects(pl.hurt_rect()):
		return false
	var ok: bool = pl.take_hit(dmg * k, self)
	if ok and push != Vector2.ZERO and pl.has_method("shove"):
		var sx := float(facing) if not both else signf(pl.global_position.x - global_position.x)
		pl.shove(Vector2(push.x * sx, push.y))
	return ok


func _count_react(now: float, dir: float) -> void:
	## Kısa sürede TEPKI[ai] vuruş yiyen yaratık tepki verir (bekleme 2,2 sn; seçkinde 1,6)
	if is_boss or decoy:
		return
	_hit_last = now
	if _passive() or dead or state in ["evade", "rev", "hold", "lurk"] or has_meta("rev") or sa_t > 0.0:
		return
	if now - _react_last > 1.3:
		_react_n = 0
	_react_last = now
	_react_n += 1
	# v26: derinlikte daha çabuk tepki (eşik zorluk.json "yz.tepki_azalt" kadar düşer, en az 2; bekleme "yz.tepki_bekleme")
	var esik := int(TEPKI.get(ai, 3))
	if esik > 2 and esik < 50:
		esik = maxi(2, esik - int(Zorluk.yz("tepki_azalt", 0.0)))
	if _react_n >= esik and now > _react_cd:
		_react_n = 0
		_react_cd = now + Zorluk.yz("tepki_bekleme", 2.2) * (0.75 if elite else 1.0)
		hurt_t = 0.0
		_react(dir)


func _react(_dir: float) -> void:
	var pl: Node = level.player if level else null
	if pl == null or pl.dead:
		return
	if ai == "kamikaze" and state != "windup":
		_tele(0.45, true)
		return
	if state in ["grab", "hold", "charge", "spin", "fuse", "dive", "swoop"]:
		return
	match ai:
		"lunger", "pouncer", "crawler":
			_evade(250.0, 0.34, 0.55)
		"stalker":
			_vanish()
		"flyer_ranged", "swarm", "diver":
			_evade(210.0, 0.42, 0.0)
		"illusionist", "caster", "charmer":
			_blink_away(pl)
		"archer":
			_evade(270.0, 0.38, 0.0)
		"brute", "tornado":
			_revenge("spin")
		"hopper":
			guard_t = 0.5
			_revenge("cut")
		"grabber", "mimic":
			_revenge("grab")
		"shield", "charger":
			_revenge("bash")


func _evade(spd := 240.0, t := 0.34, ctr := 0.0) -> void:
	## Geri sıçrayış (kurtlar, okçu) ya da uçarak kaçış: ilk %75'i dokunulmaz; ctr olasılıkla hemen karşı atılış
	var pl: Node = level.player if level else null
	var away := _side_of(pl) if pl else -float(facing)
	if not flying and _blocked(away):
		away = -away   # arkası duvar: oyuncunun üstünden aşar
		spd *= 1.25
	state = "evade"
	st = t
	evade_t = t * 0.75
	sa_t = 0.0
	velocity = Vector2(away * spd, -200.0 if not flying else -150.0)
	set_meta("ctr", ctr)
	contact = false
	_drop_token()
	if anim and anim.base:
		FX.ghost(anim.base, Color(0.85, 0.85, 1.0, 0.4), 0.22)
	FX.dust(global_position, Vector2(-away, -0.4), 4, 0.24)
	Ses.play("sicrayis", -9.0, 1.3, 0.1, 0.05, center())


func _tick_evade(delta: float, player: Node, to_p: Vector2) -> void:
	_pa(["leap", "hop", "attack", "run", "idle"])
	st -= delta
	if flying:
		velocity = velocity.lerp(Vector2.ZERO, clampf(3.0 * delta, 0.0, 1.0))
	if Engine.get_physics_frames() % 3 == 0 and anim.base:
		FX.ghost(anim.base, Color(0.8, 0.8, 1.0, 0.3), 0.16)
	if st <= 0.0 and (flying or is_on_floor() or st < -0.6):
		state = "chase"
		if player and not player.dead and randf() < float(get_meta("ctr", 0.0)) and absf(to_p.y) < 50.0:
			cd = 0.0
			_face(to_p)
			set_meta("n", 1)
			_tele(0.3)
		else:
			cd = maxf(cd, 0.35)


func _blink_away(player: Node) -> void:
	## Kam / iye / Erlik kızı: duman içinde oyuncudan uzağa ışınlanır (önce kendi yanına, olmazsa öbür yana)
	if _blink_cd > 0.0 or level == null:
		_evade(220.0, 0.32, 0.0)
		return
	var px: float = player.global_position.x
	var side := _side_of(player)
	for s in [side, -side]:
		var nx: float = px + s * 210.0
		var ty: int = level.surface_y(int(floor(nx / Level.TS)), int(floor(global_position.y / Level.TS)) - 2)
		var ny := ty * Level.TS - 1.0
		if absf(ny - global_position.y) < 100.0 and not level.solid_at(Vector2(nx, ny - size.y * 0.5)):
			FX.anim("smoke_puff", center(), 0.0, 0.7, Color(0.55, 0.3, 0.8), false)
			_ds_blink_out()
			_ds_blink = 0.0
			global_position = Vector2(nx, ny)
			FX.anim("smoke_puff", center(), 0.0, 0.7, Color(0.55, 0.3, 0.8), false)
			Ses.play("kam_davul", -8.0, 1.2, 0.06, 0.03, center())
			evade_t = 0.3
			velocity = Vector2.ZERO
			state = "recover"
			st = 0.35
			_blink_cd = 3.0
			_drop_token()
			cd = minf(cd, 0.5)
			return
	_evade(220.0, 0.32, 0.0)


func _vanish() -> void:
	## Yek: dumana karışır, görünmez olur ve kısa süre sonra oyuncunun arkasında belirip vurur
	_hidden = true
	anim.modulate = Color(1, 1, 1, 0.12)
	FX.anim("smoke_puff", center(), 0.0, 0.8, Color(0.4, 0.35, 0.5), false)
	state = "chase"
	evade_t = 0.5
	contact = false
	_drop_token()
	set_meta("ambush", 0.8)


func _revenge(kind: String) -> void:
	## Zırhlı intikam: "!!" hazırlık, sonra döner savuruş / kesik / kalkan darbesi / yakalama
	var pl: Node = level.player if level else null
	if pl:
		_face(pl.center() - center())
	set_meta("rev", kind)
	velocity.x = 0.0
	contact = false
	_tele(0.4 if kind == "grab" else 0.34, true)


func _tick_revenge(delta: float, _player: Node, _to_p: Vector2) -> void:
	var k := String(get_meta("rev", ""))
	match state:
		"windup":
			velocity.x = move_toward(velocity.x, 0.0, 900 * delta)
			_pa(["windup", "guard", "cast", "attack", "idle"])
			st -= delta
			if st <= 0.0:
				state = "rev"
				st = 0.32
				sa_t = 0.32
				vis_scale = Vector2(1.18, 0.88)
				match k:
					"spin":
						_pa(["slam", "strike", "grab", "idle"])
						FX.slash(global_position + Vector2(0, -size.y * 0.5), 1, -2.6, 0.6, size.y * 0.7, 9.0, Color(1.0, 0.75, 0.4), 0.18)
						FX.slash(global_position + Vector2(0, -size.y * 0.5), -1, -2.6, 0.6, size.y * 0.7, 9.0, Color(1.0, 0.75, 0.4), 0.18)
						FX.dust(global_position, Vector2.UP, 8, 0.34)
						Game.shake(3.0)
						Ses.play("savur_dev", -4.0, 0.9)
						_strike(size.x * 0.5 + 52.0, size.y, 1.0, Vector2(260.0, -170.0), 0.0, true)
					"cut":
						_pa(["strike", "slam", "attack", "idle"])
						velocity.x = facing * 200.0
						FX.slash(global_position + Vector2(facing * 6, -size.y * 0.6), facing, -2.2, 0.8, 38.0, 8.0, Color(1.0, 0.8, 0.5), 0.18)
						Ses.play("savur_cekic", -5.0, 1.1)
						_strike(66.0, size.y + 6.0, 1.0, Vector2(220.0, -140.0))
					"bash":
						_pa(["bash", "strike", "slam", "idle"])
						velocity.x = facing * 260.0
						FX.impact_sprite("blunt", center() + Vector2(facing * 18, 0), Vector2(facing, 0), Color(1.0, 0.85, 0.6), 0.9)
						Ses.play("darbe_kunt", -4.0)
						_strike(62.0, size.y, 0.8, Vector2(340.0, -160.0))
					"grab":
						remove_meta("rev")
						state = "grab"
						st = 0.0
						velocity.x = facing * 300.0
						FX.dust(global_position, Vector2(-facing, -0.4), 4, 0.26)
		"rev":
			velocity.x = move_toward(velocity.x, 0.0, 900 * delta)
			st -= delta
			if st <= 0.0:
				remove_meta("rev")
				state = "recover"
				st = 0.45


func _death_blast(lv: Node, pos: Vector2, d: float) -> void:
	if has_meta("blown"):
		return
	FX.text(pos + Vector2(0, -22), "!!", Color(1.0, 0.6, 0.15), 9)
	lv.get_tree().create_timer(0.3).timeout.connect(Callable(lv, "explode").bind(pos, 40.0, d, false))


func _spit(k: String, from: Vector2, v: Vector2, d: float, homing := 0.0, grav := 0.0, life := 3.0) -> Projectile:
	var p := Projectile.new()
	p.team = "e"
	p.kind = k
	p.damage = d
	p.source = self
	p.position = from
	p.velocity = v
	p.homing = homing
	p.gravity = grav
	p.life = life
	level.add_projectile(p)
	return p


func _end_attack(cd0: float, cd1: float) -> void:
	state = "chase"
	cd = randf_range(cd0, cd1) * Zorluk.yz("bekleme", 1.0)   # v26: derinlikte hamle arası kısalır
	contact = false
	_drop_token()


# ------------------------------------------------------------------ Erlik Tazısı (lunger): kurt sürüsü
## Rol: hızlı ve sinsi. Jetonsuzken çevrende dolaşır; jetonu alınca menzile girer, kısa (0,24) ya da uzun (0,42)
## hazırlıkla atılır, bazen inişte ikinci atılış; sonra geri seker. İkinci tazı arkana dolaşır. 3 vuruşta geri sıçrar
## (dokunulmaz) ve yarı yarıya hemen karşı atılır.
func _ai_lunger(delta: float, player: Node, to_p: Vector2, dist: float) -> void:
	match state:
		"idle", "chase":
			if not aggro or player == null or player.dead:
				state = "idle"
				_patrol(delta)
				anim.play("run" if absf(velocity.x) > 10.0 else "idle")
				return
			state = "chase"
			var tok := cd <= 0.0 and dist < 200.0 and _token()
			if tok:
				var side := _side_of(player)
				if flank == 1 and dist > 60.0:
					side = -float(player.facing)
				_walk_to(player.global_position.x + side * 76.0, speed * 1.2, 1000.0, delta)
				_face(to_p)
				if dist < 112.0 and absf(to_p.y) < 40.0 and is_on_floor():
					velocity.x = 0.0
					set_meta("dbl", randf() < 0.22 + 0.04 * Zorluk.derinlik())
					_tele(0.24 if randf() < 0.35 else 0.42)
			else:
				_orbit(delta, player, to_p, 100.0, 160.0, speed * 0.85, flank == 1)
			anim.play("run" if absf(velocity.x) > 10.0 else "idle")
		"windup":
			anim.play("windup")
			velocity.x = move_toward(velocity.x, 0.0, 900 * delta)
			st -= delta
			if st <= 0.0:
				state = "leap"
				st = 0.0
				if sa_t > 0.0:
					sa_t = 0.55   # zırhlı atılış havada da sürer
				velocity = Vector2(facing * 300.0, -220.0)
				contact = true
				contact_k = 1.0
				_did_hit = false
				vis_scale = Vector2(0.8, 1.25)
				FX.dust(global_position, Vector2(-facing, -0.5), 5, 0.28)
		"leap":
			anim.play("leap")
			st += delta
			if Engine.get_physics_frames() % 3 == 0:
				FX.ghost(anim.base, Color(0.6, 0.3, 0.7, 0.35), 0.18)
			if is_on_floor() and st > 0.12:
				contact = false
				vis_scale = Vector2(1.25, 0.8)
				FX.dust(global_position, Vector2.UP, 4, 0.26)
				if get_meta("dbl", false) and player and not player.dead and dist < 160.0:
					set_meta("dbl", false)
					_face(to_p)
					_tele(0.2)
				else:
					state = "back"
					st = 0.3
					velocity = Vector2(-facing * 170.0, -140.0)
		"back":
			anim.play("leap")
			st -= delta
			if st <= 0.0 and is_on_floor():
				_end_attack(0.45, 0.95)
		"recover":
			anim.play("idle")
			velocity.x = move_toward(velocity.x, 0.0, 700 * delta)
			st -= delta
			if st <= 0.0:
				_end_attack(0.45, 0.95)


# ------------------------------------------------------------------ Mağara Tazısı (crawler): zincir ısırık
## Rol: alçak ve çok hızlı; jetonu alınca 2-3 kısa atılışlık ısırık zinciri (her biri ayrı "!", aradaki boşlukta
## karşı vuruş), sonra kaçar. Yüksekten gelen savuruşlar üstünden geçebilir (alçak gövde).
func _ai_crawler(delta: float, player: Node, to_p: Vector2, dist: float) -> void:
	match state:
		"idle", "chase":
			if not aggro or player == null or player.dead:
				state = "idle"
				_patrol(delta)
				anim.play("run" if absf(velocity.x) > 10.0 else "idle")
				return
			state = "chase"
			if cd <= 0.0 and dist < 220.0 and _token():
				_walk_to(player.global_position.x + _side_of(player) * 92.0, speed * 1.1, 1300.0, delta)
				_face(to_p)
				if dist < 135.0 and absf(to_p.y) < 36.0 and is_on_floor():
					velocity.x = 0.0
					set_meta("n", 3 if Zorluk.derinlik() >= 4 else 2)
					_tele(0.3)
			else:
				_orbit(delta, player, to_p, 110.0, 175.0, speed * 0.9, flank == 1)
			anim.play("run" if absf(velocity.x) > 10.0 else "idle")
		"windup":
			anim.play("windup")
			velocity.x = move_toward(velocity.x, 0.0, 1400 * delta)
			st -= delta
			if st <= 0.0:
				state = "dash"
				st = 0.2
				if sa_t > 0.0:
					sa_t = 0.35
				velocity = Vector2(facing * 410.0, -70.0)
				contact = true
				contact_k = 0.8
				_did_hit = false
				Ses.play("isirik", -8.0, 1.3, 0.1, 0.05, center())
		"dash":
			anim.play("leap")
			st -= delta
			if Engine.get_physics_frames() % 2 == 0:
				FX.ghost(anim.base, Color(0.7, 0.35, 0.3, 0.3), 0.15)
			if st <= 0.0 and (is_on_floor() or st < -0.4):
				contact = false
				var n := int(get_meta("n", 1)) - 1
				set_meta("n", n)
				if n > 0 and player and not player.dead and dist < 190.0:
					_face(to_p)
					_tele(0.17)
				else:
					state = "back"
					st = 0.35
					velocity = Vector2(-facing * 210.0, -120.0)
		"back":
			anim.play("leap")
			st -= delta
			if st <= 0.0 and is_on_floor():
				_end_attack(0.6, 1.2)
		"recover":
			anim.play("idle")
			velocity.x = move_toward(velocity.x, 0.0, 700 * delta)
			st -= delta
			if st <= 0.0:
				_end_attack(0.6, 1.2)


# ------------------------------------------------------------------ Çor Ruhu (flyer_ranged): uzaktan spor, kaçar
## Rol: yukarıda çaprazda durur, öngörülü (oyuncunun hızını hesaba katan) güdümlü spor salvosu atar (derinlikle 1-3),
## yaklaşınca geri süzülür; tam üstündeyken "!" ile dalar.
func _ai_flyer(delta: float, player: Node, to_p: Vector2, dist: float) -> void:
	var t := Game.clock()
	match state:
		"idle", "chase":
			var target := home + Vector2(sin(t * 0.8) * 30.0, cos(t * 1.3) * 10.0)
			var fast := 1.0
			if aggro and player and not player.dead:
				state = "chase"
				var side := -signf(to_p.x) if absf(to_p.x) > 1.0 else 1.0
				var r := 120.0
				if dist < 90.0:
					r = 180.0
					fast = 1.7
				target = player.center() + Vector2(side * r, -78.0 + sin(t * 2.0 + _breath_ph) * 14.0)
				_face(to_p)
				if cd <= 0.0:
					if absf(to_p.x) < 46.0 and to_p.y > 50.0 and to_p.y < 170.0 and _token():
						set_meta("move", "dive")
						_tele(0.3)
					elif dist < 290.0 and level.los(center(), player.center()) and _token(true):
						set_meta("move", "spore")
						set_meta("n", 1 + (1 if Zorluk.derinlik() >= 3 else 0) + (1 if Zorluk.derinlik() >= 6 else 0))
						_tele(0.5)
			var dv := (target - global_position)
			velocity = velocity.lerp(dv.limit_length(1.0) * speed * fast, clampf(2.5 * delta, 0.0, 1.0))
			anim.play("idle")
		"windup":
			velocity = velocity.lerp(Vector2.ZERO, clampf(6.0 * delta, 0.0, 1.0))
			anim.show_frame("attack", 0)
			_face(to_p)
			st -= delta
			if st <= 0.0:
				if get_meta("move", "") == "dive" and player:
					state = "dive"
					st = 0.0
					contact = true
					contact_k = 1.0
					_did_hit = false
					var dd := to_p.normalized()
					dd.y = maxf(dd.y, 0.55)
					velocity = dd.normalized() * 360.0
					FX.ghost(anim.base, Color(0.6, 1.0, 0.4, 0.4), 0.2)
				else:
					state = "attack"
					st = 0.0
					set_meta("shot", 0)
		"attack":
			anim.show_frame("attack", 1)
			velocity = velocity.lerp(Vector2.ZERO, clampf(5.0 * delta, 0.0, 1.0))
			st -= delta
			if st <= 0.0:
				var k := int(get_meta("shot", 0))
				if k < int(get_meta("n", 1)) and player and not player.dead:
					set_meta("shot", k + 1)
					st = 0.2
					var aim: Vector2 = player.center() + player.velocity * 0.3 - center()
					var sp := _spit("spore", _anchor_g("mouth", center() + Vector2(facing * 8, -6)), aim.normalized().rotated(randf_range(-0.12, 0.12)) * 165.0, dmg, 0.7, 0.0, 3.0)
					sp.trail_col = Color(0.5, 1.0, 0.3, 0.6)
				else:
					_end_attack(1.1, 1.8)
		"dive":
			anim.show_frame("attack", 1)
			st += delta
			if Engine.get_physics_frames() % 3 == 0:
				FX.ghost(anim.base, Color(0.6, 1.0, 0.4, 0.35), 0.18)
			if st > 0.55 or level.solid_at(global_position + Vector2(0, 8)):
				state = "recover"
				st = 0.6
				contact = false
				velocity = Vector2(0, -160)
				FX.dust(global_position + Vector2(0, 6), Vector2.UP, 4, 0.24)
		"recover":
			velocity = velocity.lerp(Vector2(0, -120), clampf(3.0 * delta, 0.0, 1.0))
			st -= delta
			if st <= 0.0:
				_end_attack(1.0, 1.6)


# ------------------------------------------------------------------ Kan Çoru / Kayıp Ruh (swarm): sürü süzülüşü
## Rol: zayıf ama kalabalık; oyuncunun çevresinde döner, jetonu alan "!" ile içinden geçen bir süzülüş yapar
## (sırayla: aynı anda en çok jeton kadar). Yuvarlanarak içinden geçilir.
func _ai_swarm(delta: float, player: Node, to_p: Vector2, dist: float) -> void:
	var t := Game.clock()
	match state:
		"idle", "chase":
			if not aggro or player == null or player.dead:
				state = "idle"
				var hv := home + Vector2(sin(t * 1.1 + _breath_ph) * 40.0, cos(t * 1.7) * 14.0)
				velocity = velocity.lerp((hv - global_position).limit_length(1.0) * speed * 0.5, clampf(2.0 * delta, 0.0, 1.0))
				anim.play("idle")
				return
			state = "chase"
			var ang := t * 2.3 + _breath_ph * 3.0
			var target: Vector2 = player.center() + Vector2(cos(ang) * 96.0, -46.0 + sin(ang) * 34.0)
			velocity = velocity.lerp((target - global_position).limit_length(1.0) * speed, clampf(3.0 * delta, 0.0, 1.0))
			_face(to_p)
			anim.play("idle")
			if cd <= 0.0 and dist < 180.0 and _token():
				set_meta("aim", player.center() + player.velocity * 0.15)
				_tele(0.32)
		"windup":
			velocity = velocity.lerp(-to_p.normalized() * 50.0, clampf(5.0 * delta, 0.0, 1.0))
			anim.show_frame("attack", 0)
			_face(to_p)
			st -= delta
			if st <= 0.0:
				state = "swoop"
				st = 0.48
				var aim: Vector2 = get_meta("aim", center() + Vector2(facing * 60, 20))
				velocity = (aim - center()).normalized() * 440.0
				contact = true
				contact_k = 0.8
				_did_hit = false
				Ses.play("savur_bicak", -9.0, 1.2, 0.1, 0.05, center())
		"swoop":
			anim.show_frame("attack", 1)
			st -= delta
			if Engine.get_physics_frames() % 2 == 0:
				FX.ghost(anim.base, Color(1.0, 0.4, 0.4, 0.3), 0.14)
			if st <= 0.0 or level.solid_at(global_position + velocity.normalized() * 10.0):
				state = "recover"
				st = 0.35
				contact = false
		"recover":
			velocity = velocity.lerp(Vector2(0, -90), clampf(3.0 * delta, 0.0, 1.0))
			anim.play("idle")
			st -= delta
			if st <= 0.0:
				_end_attack(0.9, 1.6)


# ------------------------------------------------------------------ dalıcılar (diver): işaretli pike
## Rol: tepende süzülür; yere işaret koyar ("!" + yer uyarısı), işarete pike yapar, yere saplanıp 0,7 sn açık kalır
## (ceza penceresi), sonra yükselir.
func _ai_diver(delta: float, player: Node, to_p: Vector2, dist: float) -> void:
	match state:
		"idle", "chase":
			if not aggro or player == null or player.dead:
				state = "idle"
				var hv := home + Vector2(sin(Game.clock() * 0.9) * 30.0, 0.0)
				velocity = velocity.lerp((hv - global_position).limit_length(1.0) * speed * 0.5, clampf(2.0 * delta, 0.0, 1.0))
				anim.play("idle")
				return
			state = "chase"
			var target := Vector2(player.global_position.x + sin(Game.clock() * 1.3 + _breath_ph) * 55.0, player.global_position.y - 150.0)
			velocity = velocity.lerp((target - global_position).limit_length(1.0) * speed, clampf(2.5 * delta, 0.0, 1.0))
			_face(to_p)
			anim.play("idle")
			if cd <= 0.0 and absf(to_p.x) < 100.0 and to_p.y > 70.0 and level.los(center(), player.center()) and _token():
				var gp: Vector2 = player.global_position + Vector2(player.velocity.x * 0.25, 0.0)
				set_meta("aim", gp)
				level.telegraph_ground(gp, 0.75)
				_tele(0.45)
		"windup":
			velocity = velocity.lerp(Vector2(0, -40), clampf(6.0 * delta, 0.0, 1.0))
			anim.show_frame("attack", 0)
			st -= delta
			if st <= 0.0:
				state = "dive"
				st = 0.0
				contact = true
				contact_k = 1.1
				_did_hit = false
				var aim: Vector2 = get_meta("aim", global_position + Vector2(0, 150))
				velocity = (aim - global_position).normalized() * 460.0
				Ses.play("savur_bicak", -8.0, 0.8, 0.1, 0.05, center())
		"dive":
			anim.show_frame("attack", 1)
			st += delta
			if Engine.get_physics_frames() % 2 == 0:
				FX.ghost(anim.base, Color(0.8, 0.9, 1.0, 0.35), 0.16)
			if level.solid_at(global_position + Vector2(0, 6)) or st > 0.9:
				state = "stuck"
				st = 0.7
				contact = false
				velocity = Vector2.ZERO
				vis_scale = Vector2(1.3, 0.75)
				FX.dust(global_position, Vector2.UP, 7, 0.3)
				FX.ring(global_position, 26, Color(0.9, 0.9, 1.0, 0.7), 0.22, 0.3)
				Game.shake(2.0)
				if player and not player.dead and absf(player.global_position.x - global_position.x) < 38.0 and absf(player.global_position.y - global_position.y) < 30.0:
					player.take_hit(dmg * 0.5, self)
		"stuck":
			velocity = Vector2.ZERO
			anim.show_frame("attack", 1)
			st -= delta
			if st <= 0.0:
				state = "recover"
				st = 0.5
		"recover":
			velocity = velocity.lerp(Vector2(0, -200), clampf(3.0 * delta, 0.0, 1.0))
			anim.play("idle")
			st -= delta
			if st <= 0.0:
				_end_attack(1.0, 1.7)


# ------------------------------------------------------------------ Kara İye / Dev Çocuğu (brute): ağır, zırhlı
## Rol: yavaş döner (arkasına geç), ezbere basanı cezalandırır: zırhlı çakma ("!!" 0,8), zırhlı sıçrayıp ezme, uzaktan
## işaretli kök dalgası; dibine/arkasına girince hızlı ters tokat ("!" 0,3). 5 vuruşta zırhlı döner savuruş.
func _ai_brute(delta: float, player: Node, to_p: Vector2, dist: float) -> void:
	match state:
		"idle", "chase":
			if not aggro or player == null or player.dead:
				state = "idle"
				velocity.x = move_toward(velocity.x, 0.0, 400 * delta)
				anim.play("idle")
				return
			state = "chase"
			_turn(to_p, 0.4, delta)
			var tgt := facing * speed
			if _blocked(float(facing)) or dist < 52.0 or int(signf(to_p.x)) != facing:
				tgt = 0.0
			velocity.x = move_toward(velocity.x, tgt, 300 * delta)
			anim.play("walk" if absf(velocity.x) > 4.0 else "idle")
			if cd <= 0.0 and _token():
				var behind := absf(to_p.x) > 6.0 and int(signf(to_p.x)) != facing
				if dist < 66.0 and absf(to_p.y) < 50.0 and (behind or randf() < 0.3):
					set_meta("move", "swat")
					_tele(0.3)
				elif dist < 84.0 and absf(to_p.y) < 50.0:
					set_meta("move", "slam")
					_face(to_p)
					_tele(0.8, true)
				elif dist < 210.0 and randf() < 0.4 and is_on_floor() and player.is_on_floor():
					set_meta("move", "leap")
					_face(to_p)
					_tele(0.6, true)
				elif dist < 250.0 and player.is_on_floor():
					set_meta("move", "roots")
					set_meta("target", player.global_position)
					level.telegraph_ground(player.global_position, 0.75)
					_tele(0.6)
				else:
					_drop_token()
		"windup":
			velocity.x = 0.0
			anim.play("windup")
			st -= delta
			if st <= 0.0:
				match String(get_meta("move", "slam")):
					"slam":
						state = "slam"
						st = 0.4
						Game.shake(5.0)
						FX.shock_line(global_position + Vector2(facing * 44, 0), 40.0, Color(0.5, 0.42, 0.3, 0.7))
						Game.kick(Vector2.DOWN, 4.0)
						vis_scale = Vector2(1.15, 0.88)
						FX.flash_light(global_position + Vector2(facing * 40, -8), Color(1.0, 0.7, 0.4), 140.0, 1.2, 0.2)
						FX.ring(global_position + Vector2(facing * 44, -2), 44, Color(0.9, 0.7, 0.4), 0.3, 0.3)
						_strike(88.0, 64.0, 1.3, Vector2(240.0, -200.0), 4.0)
					"swat":
						state = "slam"
						st = 0.3
						FX.slash(global_position + Vector2(0, -size.y * 0.55), -facing, -2.0, 0.9, 40.0, 8.0, Color(0.9, 0.8, 0.6), 0.16)
						Ses.play("savur_dev", -6.0, 1.2)
						_strike(62.0, size.y, 0.8, Vector2(260.0, -150.0), 0.0, true)
					"leap":
						state = "leap"
						st = 0.0
						sa_t = 1.2
						var dx: float = clampf(player.global_position.x - global_position.x if player else facing * 80.0, -280.0, 280.0)
						velocity = Vector2(dx * 1.7, -400.0)
						contact = true
						contact_k = 1.0
						_did_hit = false
						FX.dust(global_position, Vector2.UP, 8, 0.34)
						Ses.play("sicrayis", -4.0, 0.7)
					_:
						state = "slam"
						st = 0.5
						var tgt: Vector2 = get_meta("target", global_position)
						level.spawn_roots(tgt, dmg * 0.8, self)
						_root_wave(tgt, 3 if Zorluk.derinlik() >= 4 else 2)
		"leap":
			anim.play("slam")
			st += delta
			if is_on_floor() and st > 0.15:
				state = "slam"
				st = 0.45
				contact = false
				sa_t = 0.0
				vis_scale = Vector2(1.35, 0.7)
				Game.shake(6.0)
				FX.ground_slam(global_position, facing, 1.2, Color(0.75, 0.6, 0.45), false, false, false)
				Ses.play("sarsinti", -4.0, 0.9)
				if player and not player.dead and absf(player.global_position.x - global_position.x) < 64.0 and player.is_on_floor():
					if player.take_hit(dmg * 1.2, self) and player.has_method("shove"):
						player.shove(Vector2(signf(player.global_position.x - global_position.x) * 280.0, -220.0))
		"slam":
			anim.play("slam")
			st -= delta
			if st <= 0.0:
				state = "recover"
				st = 0.55
		"recover":
			anim.play("idle")
			velocity.x = move_toward(velocity.x, 0.0, 700 * delta)
			st -= delta
			if st <= 0.0:
				_end_attack(0.6, 1.2)


# ------------------------------------------------------------------ Tozkoparan (tornado): kasırga
## Rol: alan kontrolü. Zırhlı kasırgaya dönüşür ("!!" 0,6), 1,7 sn oyuncuyu kovalayarak yerde döner, çevresindekini
## kendine çeker ve çok vuruşla dağlar; bitince 1 sn başı döner (ceza penceresi). Dibindeyken yel itişi.
func _ai_tornado(delta: float, player: Node, to_p: Vector2, dist: float) -> void:
	match state:
		"idle", "chase":
			if not aggro or player == null or player.dead:
				state = "idle"
				_patrol(delta)
				anim.play("walk" if absf(velocity.x) > 6.0 else "idle")
				return
			state = "chase"
			_face(to_p)
			var tgt := facing * speed * 0.55
			if _blocked(float(facing)) or dist < 60.0:
				tgt = 0.0
			velocity.x = move_toward(velocity.x, tgt, 400 * delta)
			anim.play("walk" if absf(velocity.x) > 4.0 else "idle")
			if cd <= 0.0 and _token():
				if dist < 72.0 and absf(to_p.y) < 50.0:
					set_meta("move", "gust")
					_tele(0.35)
				elif dist < 300.0:
					set_meta("move", "spin")
					_tele(0.6, true)
				else:
					_drop_token()
		"windup":
			velocity.x = move_toward(velocity.x, 0.0, 900 * delta)
			anim.play("windup")
			st -= delta
			if Engine.get_physics_frames() % 3 == 0:
				FX.dust(global_position + Vector2(randf_range(-20, 20), 0), Vector2(randf_range(-1, 1), -1), 1, 0.3, Color(0.75, 0.68, 0.5, 0.6))
			if st <= 0.0:
				if get_meta("move", "") == "gust":
					state = "slam"
					st = 0.35
					anim.play("slam")
					FX.dust(global_position + Vector2(facing * 30, -20), Vector2(facing, -0.2), 10, 0.36, Color(0.8, 0.72, 0.55, 0.7))
					Ses.play("savur_dev", -5.0, 1.3)
					_strike(84.0, 70.0, 0.6, Vector2(320.0, -170.0))
				else:
					state = "spin"
					st = 1.7
					sa_t = 1.8
					contact = true
					contact_k = 0.6
					_did_hit = false
					set_meta("hit_t", 0.45)
					Ses.play("sarsinti", -6.0, 1.5)
		"spin":
			anim.play("walk")
			anim.speed = 2.6
			if absf(to_p.x) > 30.0 and int(signf(to_p.x)) != facing:
				velocity.x = move_toward(velocity.x, -facing * 40.0, 700 * delta)
				if absf(velocity.x) < 50.0:
					facing = -facing
			else:
				velocity.x = move_toward(velocity.x, facing * 290.0, 900 * delta)
			var ht := float(get_meta("hit_t", 0.45)) - delta
			if ht <= 0.0:
				ht = 0.45
				_did_hit = false
			set_meta("hit_t", ht)
			if player and not player.dead and dist < 115.0 and player.roll_t <= 0.0 and player.grabbed_by == null:
				player.move_and_collide(Vector2(-signf(to_p.x) * 75.0 * delta, 0.0))
			if Engine.get_physics_frames() % 2 == 0:
				var a: float = Game.clock() * 14.0
				FX.dust(global_position + Vector2(cos(a) * 22.0, -10.0 - absf(sin(a)) * 50.0), Vector2(-sin(a), -0.6), 1, 0.34, Color(0.78, 0.7, 0.52, 0.6))
			if Engine.get_physics_frames() % 12 == 0:
				FX.ring(global_position + Vector2(0, -30), 30.0, Color(0.85, 0.78, 0.6, 0.5), 0.25, 0.4)
			st -= delta
			if st <= 0.0 or is_on_wall():
				contact = false
				anim.speed = 1.0
				sa_t = 0.0
				state = "dizzy"
				st = 1.0
				FX.text(center() + Vector2(0, -size.y * 0.5 - 12.0), "başı döndü", Color(0.95, 0.9, 0.7), 7)
		"dizzy":
			anim.play("idle")
			velocity.x = move_toward(velocity.x, 0.0, 600 * delta)
			if Engine.get_physics_frames() % 10 == 0:
				FX.burst(center() + Vector2(0, -size.y * 0.5), Color(1.0, 0.95, 0.6), 1, 30, 0.4, 0.14, -20, true)
			st -= delta
			if st <= 0.0:
				_end_attack(0.8, 1.4)
		"slam":
			st -= delta
			if st <= 0.0:
				state = "recover"
				st = 0.4
		"recover":
			anim.play("idle")
			velocity.x = move_toward(velocity.x, 0.0, 700 * delta)
			st -= delta
			if st <= 0.0:
				_end_attack(0.7, 1.3)


# ------------------------------------------------------------------ Su İyesi / Od İyesi (caster): tehlike koyar
## Rol: uzak durur (140-230 px), yaklaşınca kaçar, sıkışınca öbür yana ışınlanır. Duran oyuncunun altına (ya da
## rastgele) işaretli zehir / alev gölü (0,55 sn kurulur, 3,2 sn yakar; derinde üçlü); bazen yavaş üçlü küre.
func _ai_caster(delta: float, player: Node, to_p: Vector2, dist: float) -> void:
	var fire := kind == "od_iyesi"
	match state:
		"idle", "chase":
			if not aggro or player == null or player.dead:
				state = "idle"
				velocity.x = move_toward(velocity.x, 0.0, 400 * delta)
				anim.play("idle")
				return
			state = "chase"
			var want := 0.0
			if dist < 125.0:
				want = -signf(to_p.x) * speed * 1.3
				if _blocked(signf(want)) and dist < 80.0:
					_blink_away(player)
					return
			elif dist > 235.0:
				want = signf(to_p.x) * speed
			if want != 0.0 and _blocked(signf(want)):
				want = 0.0
			velocity.x = move_toward(velocity.x, want, 500 * delta)
			_face(to_p)
			anim.play("walk" if absf(velocity.x) > 6.0 else "idle")
			if cd <= 0.0 and dist < 310.0 and level.los(center(), player.center()) and _token(true):
				if _pl_still > 0.9 or randf() < 0.55:
					set_meta("move", "pool")
					set_meta("target", player.global_position + Vector2(player.velocity.x * 0.3, 0.0))
					_tele(0.65)
				else:
					set_meta("move", "orbs")
					_tele(0.5)
		"windup":
			velocity.x = move_toward(velocity.x, 0.0, 800 * delta)
			anim.play("windup")
			st -= delta
			if Engine.get_physics_frames() % 4 == 0:
				FX.burst(center() + Vector2(facing * 12, -size.y * 0.3), Color(1.0, 0.55, 0.2) if fire else Color(0.45, 0.95, 0.6), 1, 30, 0.4, 0.16, -40, true)
			if st <= 0.0:
				state = "slam"
				st = 0.45
				anim.play("slam")
				if get_meta("move", "") == "pool":
					var tgt: Vector2 = get_meta("target", player.global_position if player else global_position)
					Tehlike.spawn(level, "ates" if fire else "zehir", tgt, 42.0, 0.55, 3.2, dmg * 0.45, self)
					if Zorluk.derinlik() >= 5:
						for s in [-1, 1]:
							Tehlike.spawn(level, "ates" if fire else "zehir", tgt + Vector2(s * 92.0, 0.0), 36.0, 0.85, 2.8, dmg * 0.4, self)
					Ses.play("buyu", -7.0, 1.1, 0.06, 0.03, center())
				else:
					var hand := center() + Vector2(facing * 14, -size.y * 0.25)
					var base_a: float = (player.center() - hand).angle() if player else (0.0 if facing > 0 else PI)
					for k in 3:
						var p := _spit("fireball" if fire else "spore", hand, Vector2.from_angle(base_a + (k - 1) * 0.3) * 125.0, dmg * 0.8, 0.0 if fire else 0.35, 0.0, 3.2)
						p.trail_col = Color(1.0, 0.55, 0.2, 0.6) if fire else Color(0.45, 0.95, 0.6, 0.6)
					Ses.play("buyu", -6.0, 0.9, 0.06, 0.03, center())
		"slam":
			st -= delta
			if st <= 0.0:
				state = "recover"
				st = 0.4
		"recover":
			anim.play("idle")
			velocity.x = move_toward(velocity.x, 0.0, 700 * delta)
			st -= delta
			if st <= 0.0:
				_end_attack(1.3, 2.1)


# ------------------------------------------------------------------ Işıltı Kamı (kamikaze): patlayan
## Rol: sana koşar; dibine gelince "!!" fitil (0,6 sn, parlayarak büyür) ve patlar. Vurmak fitili ateşler; öldürmek
## de küçük bir patlama bırakır: uzaktan öldür ya da fitilde kaç.
func _ai_kamikaze(delta: float, player: Node, to_p: Vector2, dist: float) -> void:
	match state:
		"idle", "chase":
			if not aggro or player == null or player.dead:
				state = "idle"
				_patrol(delta)
				anim.play("run" if absf(velocity.x) > 10.0 else "idle")
				return
			state = "chase"
			_face(to_p)
			var tgt := facing * speed * 1.35
			if _blocked(float(facing)):
				tgt = 0.0
			velocity.x = move_toward(velocity.x, tgt, 900 * delta)
			anim.play("run")
			if Engine.get_physics_frames() % 6 == 0:
				FX.burst(center(), Color(1.0, 0.85, 0.4), 1, 20, 0.3, 0.14, -30, true)
			if dist < 48.0 and absf(to_p.y) < 44.0:
				_tele(0.6, true)
		"windup":
			_face(to_p)
			velocity.x = move_toward(velocity.x, facing * 40.0, 600 * delta)
			anim.play("cast")
			st -= delta
			var k := clampf(1.0 - st / 0.6, 0.0, 1.0)
			base_scale = Vector2.ONE * (1.0 + 0.35 * k) * (1.3 if elite else 1.0)
			flash_t = 0.04 if int(Time.get_ticks_msec() / maxf(30.0, 120.0 - 90.0 * k)) % 2 == 0 else 0.0
			if Engine.get_physics_frames() % 3 == 0:
				FX.burst(center(), Color(1.0, 0.75, 0.3), 2, 40, 0.3, 0.16, -20, true)
			if st <= 0.0:
				set_meta("blown", true)
				level.explode(center(), 58.0, dmg * 1.6, false)
				_die(float(facing), 0.0, false)
		"recover":
			anim.play("idle")
			base_scale = Vector2.ONE * (1.3 if elite else 1.0)
			velocity.x = move_toward(velocity.x, 0.0, 600 * delta)
			st -= delta
			if st <= 0.0:
				_end_attack(0.3, 0.6)


# ------------------------------------------------------------------ Erlik'in Kızı (charmer): büyü bağı
## Rol: uzak durur, yaklaşınca ışınlanır. "!" sonrası büyü bağı (mor ışın, 1,1 sn): yuvarlanmazsan seni kendine
## çeker, dibine gelince lanet patlaması; ya da iki güdümlü lanet küresi.
func _ai_charmer(delta: float, player: Node, to_p: Vector2, dist: float) -> void:
	match state:
		"idle", "chase":
			if not aggro or player == null or player.dead:
				state = "idle"
				_patrol(delta)
				anim.play("run" if absf(velocity.x) > 10.0 else "idle")
				return
			state = "chase"
			if dist < 80.0 and _blink_cd <= 0.0:
				_blink_away(player)
				return
			var want := 0.0
			if dist < 140.0:
				want = -signf(to_p.x) * speed
			elif dist > 240.0:
				want = signf(to_p.x) * speed
			if want != 0.0 and _blocked(signf(want)):
				want = 0.0
			velocity.x = move_toward(velocity.x, want, 500 * delta)
			_face(to_p)
			anim.play("run" if absf(velocity.x) > 10.0 else "idle")
			if cd <= 0.0 and dist < 290.0 and level.los(center(), player.center()) and _token(true):
				set_meta("move", "charm" if randf() < 0.5 else "curse")
				_tele(0.65 if get_meta("move") == "charm" else 0.5)
		"windup":
			velocity.x = move_toward(velocity.x, 0.0, 800 * delta)
			anim.show_frame("cast", 0)
			_face(to_p)
			st -= delta
			if Engine.get_physics_frames() % 4 == 0:
				FX.burst(center() + Vector2(facing * 10, -4), Color(0.85, 0.3, 0.7), 1, 30, 0.4, 0.16, -40, true)
			if st <= 0.0:
				if get_meta("move", "") == "charm":
					state = "charm"
					st = 1.1
					_beam = Isin.new()
					_beam.kind = "bag"
					_beam.level = level
					_beam.source = self
					level.fx_root.add_child(_beam)
					Ses.play("kam_ilahi", -6.0, 1.3, 0.06, 0.03, center())
				else:
					state = "attack"
					st = 0.45
					anim.show_frame("cast", 1)
					var hand := _anchor_g("hand", center() + Vector2(facing * 10, -4))
					for s in [-1, 1]:
						var p := _spit("curse", hand, (to_p.normalized().rotated(s * 0.45)) * 140.0, dmg, 1.3, 0.0, 2.6)
						p.trail_col = Color(0.85, 0.35, 0.8, 0.6)
					Ses.play("kam_ilahi", -8.0, 1.0, 0.06, 0.03, center())
		"charm":
			anim.show_frame("cast", 2)
			velocity.x = 0.0
			st -= delta
			var hand2 := _anchor_g("hand", center() + Vector2(facing * 10, -4))
			var broke: bool = player == null or player.dead or player.roll_t > 0.0
			if is_instance_valid(_beam):
				_beam.origin = hand2
				_beam.tip = player.center() if player else hand2
				_beam.on = st < 0.95 and not broke
			if not broke and st < 0.95 and player.grabbed_by == null:
				player.move_and_collide(Vector2(-signf(to_p.x) * 150.0 * delta, 0.0))
				if dist < 50.0:
					st = 0.0
					if player.take_hit(dmg * 1.1, self):
						FX.anim("arcane_parry", player.center(), 0.0, 0.8, Color(0.9, 0.4, 0.8))
						Ses.play("kam_kahkaha", -6.0, 1.1, 0.06, 0.03, center())
			if st <= 0.0 or broke:
				if is_instance_valid(_beam):
					_beam.queue_free()
				_beam = null
				state = "recover"
				st = 0.5
		"attack":
			st -= delta
			if st <= 0.0:
				state = "recover"
				st = 0.3
		"recover":
			if is_instance_valid(_beam):
				_beam.queue_free()
				_beam = null
			anim.play("idle")
			velocity.x = move_toward(velocity.x, 0.0, 700 * delta)
			st -= delta
			if st <= 0.0:
				_end_attack(1.4, 2.2)


# ------------------------------------------------------------------ Gulyabani (grabber): kavrama
## Rol: tehlikeli yakın dövüşçü. Kavrama hep "!!" (zırhlı, 0,5): savurarak kesilmez, yuvarlanarak kaçılır; ıskalarsa
## 1 sn açık kalır. Dibindeyken hızlı pençe ("!" 0,3). Yakalarsa sıkar ve fırlatır (4 basışla kurtulursun).
func _ai_grabber(delta: float, player: Node, to_p: Vector2, dist: float) -> void:
	match state:
		"idle", "chase":
			if not aggro or player == null or player.dead:
				state = "idle"
				velocity.x = move_toward(velocity.x, 0.0, 400 * delta)
				anim.play("idle")
				return
			state = "chase"
			_face(to_p)
			if cd <= 0.0 and _token():
				var tgt := facing * speed * 1.1
				if _blocked(float(facing)) or dist < 44.0:
					tgt = 0.0
				velocity.x = move_toward(velocity.x, tgt, 400 * delta)
				if dist < 60.0 and absf(to_p.y) < 50.0 and randf() < 0.35:
					set_meta("move", "claw")
					_tele(0.3)
				elif dist < 86.0 and absf(to_p.y) < 50.0:
					set_meta("move", "grab")
					_tele(0.5, true)
			else:
				_orbit(delta, player, to_p, 95.0, 150.0, speed * 0.8)
			anim.play("walk" if absf(velocity.x) > 4.0 else "idle")
		"windup":
			velocity.x = 0.0
			anim.play("windup")
			st -= delta
			if st <= 0.0:
				if get_meta("move", "grab") == "claw":
					state = "strike"
					st = 0.3
					anim.play("grab", true)
					velocity.x = facing * 120.0
					FX.slash(global_position + Vector2(facing * 8, -size.y * 0.6), facing, -2.0, 0.8, 34.0, 7.0, Color(0.9, 0.85, 0.5), 0.16)
					_strike(60.0, 62.0, 0.8, Vector2(200.0, -120.0))
				else:
					state = "grab"
					st = 0.0
					velocity.x = facing * 280.0
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
				st = 1.1
				set_meta("sq", 0.3)
				player.take_hit(dmg * 0.5, self, null, true)
				FX.anim("tether_catch", player.center(), 0.0, 1.0, Color(0.9, 0.8, 0.5))
				FX.text(center() + Vector2(0, -80), "YAKALANDIN! (4 kez bas)", Color(1.0, 0.8, 0.4), 8)
			elif st > 0.35:
				state = "recover"
				st = 1.0   # ıskaladı: uzun açık (ceza penceresi)
		"hold":
			anim.play("grab")
			velocity.x = 0.0
			st -= delta
			if grab_target and is_instance_valid(grab_target) and grab_target.grabbed_by == self:
				grab_target.global_position = global_position + Vector2(facing * 34, -10)
				var sq := float(get_meta("sq", 0.3)) - delta
				if sq <= 0.0:
					sq = 0.36
					grab_target.take_hit(dmg * 0.4, self, null, true)
					vis_scale = Vector2(1.1, 0.92)
				set_meta("sq", sq)
				if st <= 0.0:
					grab_target.take_hit(dmg * 0.5, self, null, true)
					grab_target.release_grab(Vector2(facing * 260.0, -220.0))
					grab_target = null
					state = "recover"
					st = 0.7
			else:
				grab_target = null
				state = "recover"
				st = 0.5
		"strike":
			velocity.x = move_toward(velocity.x, 0.0, 800 * delta)
			st -= delta
			if st <= 0.0:
				state = "recover"
				st = 0.45
		"recover":
			anim.play("idle")
			velocity.x = move_toward(velocity.x, 0.0, 600 * delta)
			st -= delta
			if st <= 0.0:
				_end_attack(0.7, 1.3)


# ------------------------------------------------------------------ Karakoncolos (mimic): kar yığını pusucu
## Rol: kıpırtısız bekler (yalnızca hafif soluk ton ele verir); yaklaşınca "!!" ile hızla yakalar. Açığa çıkınca
## Gulyabani gibi dövüşür, uzaktaysan kartopu fırlatır.
func _ai_mimic(delta: float, player: Node, to_p: Vector2, dist: float) -> void:
	if state == "lurk":
		velocity.x = 0.0
		anim.play("idle")
		anim.speed = 0.0
		# yakında oyalanan oyuncuya sabrı tükenir (2,5 sn)
		var lt := float(get_meta("lurk_t", 0.0))
		lt = lt + delta if player and dist < 175.0 else 0.0
		set_meta("lurk_t", lt)
		if player and not player.dead and ((dist < 82.0 and absf(to_p.y) < 50.0) or hp < max_hp or lt > 2.5):
			anim.speed = 1.0
			anim.modulate = Color(1, 1, 1, 1)
			aggro = true
			FX.anim("smoke_puff", center(), 0.0, 0.8, Color(0.85, 0.9, 1.0), false)
			FX.frost(center(), 8)
			Ses.play("surale_can", -4.0, 0.8, 0.06, 0.03, center())
			_face(to_p)
			set_meta("move", "grab")
			_tele(0.3, true)
		return
	if state in ["idle", "chase"] and aggro and player and not player.dead and cd <= 0.0 and dist > 140.0 and dist < 290.0 and level.los(center(), player.center()) and _token(true):
		set_meta("move", "snow")
		_face(to_p)
		_tele(0.45)
		return
	if state == "windup" and get_meta("move", "") == "snow":
		velocity.x = 0.0
		anim.play("windup")
		st -= delta
		if st <= 0.0:
			state = "strike"
			st = 0.35
			anim.play("grab", true)
			if player:
				var tt := clampf(dist / 360.0, 0.35, 0.8)
				var aim: Vector2 = player.center() + Vector2(player.velocity.x * tt * 0.6, 0.0) - center()
				var p := _spit("ice", center() + Vector2(facing * 12, -size.y * 0.4), Vector2(aim.x / tt, aim.y / tt - 0.5 * 420.0 * tt), dmg * 0.8, 0.0, 420.0, 2.5)
				p.trail_col = Color(0.8, 0.9, 1.0, 0.5)
			Ses.play("savur_bicak", -8.0, 0.8)
		return
	_ai_grabber(delta, player, to_p, dist)


func _ai_illusionist(delta: float, player: Node, to_p: Vector2, dist: float) -> void:
	## Kara Kam: 110-170 px'te durur; dibine girilince ışınlanır. İki hayalet kopya salıp arkana ışınlanır ya da
	## güdümlü lanet atar.
	if decoy:
		# hayalet kopya: dümdüz oyuncuya koşar, dokununca dağılır
		if player and not player.dead:
			_face(to_p)
			velocity.x = move_toward(velocity.x, facing * speed * 1.6, 900 * delta)
			anim.play("run")
			state = "chase"
			if hurt_rect().intersects(player.hurt_rect()):
				player.take_hit(dmg, self)
				_die(float(facing), 0.0, false)
		return
	match state:
		"idle", "chase":
			if not aggro or player == null or player.dead:
				state = "idle"
				_patrol(delta)
				anim.play("run" if absf(velocity.x) > 10.0 else "idle")
				return
			state = "chase"
			if dist < 60.0 and _blink_cd <= 0.0:
				_blink_away(player)
				return
			var want := 0.0
			if dist < 100.0:
				want = -signf(to_p.x) * speed
			elif dist > 180.0:
				want = signf(to_p.x) * speed
			if want != 0.0 and _blocked(signf(want)):
				want = 0.0
			velocity.x = move_toward(velocity.x, want, 500 * delta)
			_face(to_p)
			anim.play("run" if absf(velocity.x) > 10.0 else "idle")
			if cd <= 0.0 and dist < 250.0 and level.los(center(), player.center()) and _token(true):
				_tele(0.55)
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
				if randf() < 0.5 and player:
					for side in [-1, 1]:
						var g: Enemy = level.spawn_enemy(kind, global_position + Vector2(side * 14, 0))
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
					var ty: int = level.surface_y(int(nx / 24.0), int(global_position.y / 24.0) - 2)
					if abs(ty * 24 - global_position.y) < 120:
						global_position = Vector2(nx, ty * 24.0 - 1)
					FX.anim("smoke_puff", center(), 0.0, 0.7, Color(0.55, 0.3, 0.8), false)
					FX.anim("arcane_parry", center(), 0.0, 0.8, Color(0.75, 0.4, 1.0))
					Ses.play("kam_davul", -6.0, 1.0, 0.06, 0.03, center())
					_face(player.center() - center())
				elif player:
					var hand := _anchor_g("hand", center() + Vector2(facing * 10, -4))
					Ses.play("kam_ilahi", -8.0, 1.0, 0.06, 0.03, center())
					var n := 2 if Zorluk.derinlik() >= 3 else 1
					for k in n:
						var a: float = (player.center() - hand).angle() + (k - (n - 1) * 0.5) * 0.4
						_spit("curse", hand, Vector2.from_angle(a) * 150.0, dmg, 1.2, 0.0, 2.5)
		"attack":
			anim.show_frame("cast", 2)
			st -= delta
			if st <= 0.0:
				_end_attack(1.4, 2.4)
		"recover":
			anim.play("idle")
			st -= delta
			if st <= 0.0:
				_end_attack(0.8, 1.6)


func _ai_pouncer(delta: float, player: Node, to_p: Vector2, dist: float) -> void:
	## Pusu tazısı: yüksekte bekler; oyuncu altından/önünden geçince üstüne atlar, inişte toz dalgası; sonra tazı gibi kovalar
	match state:
		"perch":
			velocity.x = 0.0
			anim.play("idle")
			if Engine.get_physics_frames() % 40 == 0 and player:
				_face(to_p)
			if player and dist < 210.0 and to_p.y > -30.0 and absf(to_p.x) < 200.0:
				_face(to_p)
				set_meta("pounce", true)
				_tele(0.38)
		"windup":
			anim.play("windup")
			velocity.x = 0.0
			st -= delta
			if st <= 0.0:
				if not get_meta("pounce", false):
					# yerdeyken kurt gibi atılır
					_ai_lunger(delta, player, to_p, dist)
					return
				set_meta("pounce", false)
				state = "leap"
				st = 0.0
				var tgt: Vector2 = player.global_position + player.velocity * 0.35 if player else global_position + Vector2(facing * 80, 0)
				var dx := tgt.x - global_position.x
				var tt := clampf(absf(dx) / 320.0, 0.3, 0.6)
				velocity = Vector2(dx / tt, -(maxf(0.0, global_position.y - tgt.y) + 60.0) / tt + 0.0)
				velocity.y = minf(velocity.y, -220.0)
				contact = true
				contact_k = 1.0
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
				st = 0.45
				contact = false
				vis_scale = Vector2(1.35, 0.7)
				FX.dust(global_position, Vector2.UP, 8, 0.32)
				FX.ring(global_position, 30, Color(0.9, 0.85, 0.8), 0.25, 0.3)
				Game.shake(2.5)
				Ses.play("inis_2", -6.0)
				if player and absf(player.global_position.x - global_position.x) < 34.0 and absf(player.global_position.y - global_position.y) < 24.0 and player.is_on_floor():
					player.take_hit(dmg * 0.6, self)
		_:
			_ai_lunger(delta, player, to_p, dist)
			if state == "chase" and cd <= 0.0 and player and dist > 120.0 and dist < 230.0 and to_p.y > 20.0 and randf() < 0.03 and _token():
				set_meta("pounce", true)
				_tele(0.38)


func _ai_shield(delta: float, player: Node, to_p: Vector2, dist: float) -> void:
	## Kalkanlı bekçi: önden gelen darbeleri kalkanla karşılar ve YAVAŞ döner (0,45 sn): arkasına yuvarlan ya da
	## ağır vuruş / 3 darbeyle kalkanı düşür. Hızlı dürtme ("!" 0,28), gecikmeli zırhlı baş üstü ("!!" 0,75),
	## kalkan itişi ("!" 0,4). Kalkana art arda vurana kalkan darbesiyle karşılık verir.
	match state:
		"idle", "chase":
			if not aggro or player == null or player.dead:
				state = "idle"
				_patrol(delta)
				anim.play("walk" if absf(velocity.x) > 8.0 else "guard")
				return
			state = "chase"
			_turn(to_p, 0.45, delta)
			var tgt := facing * speed
			if _blocked(float(facing)) or dist < 42.0 or int(signf(to_p.x)) != facing:
				tgt = 0.0
			velocity.x = move_toward(velocity.x, tgt, 300 * delta)
			anim.play("walk" if absf(velocity.x) > 4.0 else "guard")
			if cd <= 0.0 and dist < 72.0 and absf(to_p.y) < 50.0 and int(signf(to_p.x)) == facing and _token():
				var r := randf()
				set_meta("move", "jab" if r < 0.35 else ("heavy" if r < 0.7 else "bash"))
				match String(get_meta("move")):
					"jab":
						_tele(0.28)
					"heavy":
						_tele(0.75, true)
					_:
						_tele(0.4)
		"windup":
			velocity.x = 0.0
			anim.play("guard" if get_meta("move", "") == "bash" else "windup")
			st -= delta
			if st <= 0.0:
				state = "strike"
				match String(get_meta("move", "jab")):
					"jab":
						st = 0.25
						anim.play("strike", true)
						velocity.x = facing * 110.0
						FX.slash(global_position + Vector2(facing * 8, -34), facing, -1.2, 0.4, 30.0, 6.0, Color(0.9, 0.85, 0.7), 0.12)
						Ses.play("savur_bicak", -6.0, 0.9)
						_strike(58.0, 54.0, 0.9)
					"heavy":
						st = 0.45
						anim.play("strike", true)
						velocity.x = facing * 160.0
						FX.slash(global_position + Vector2(facing * 8, -38), facing, -2.4, 0.9, 36.0, 9.0, Color(1.0, 0.85, 0.6), 0.18)
						FX.shock_line(global_position + Vector2(facing * 40, 0), 26.0)
						Game.shake(3.5)
						Ses.play("savur_cekic", -4.0, 0.85)
						_strike(72.0, 64.0, 1.4, Vector2(220.0, -170.0))
					_:
						st = 0.3
						anim.play("bash", true)
						velocity.x = facing * 240.0
						Ses.play("darbe_kunt", -6.0)
						_strike(60.0, 56.0, 0.7, Vector2(320.0, -150.0))
		"strike":
			velocity.x = move_toward(velocity.x, 0.0, 900 * delta)
			st -= delta
			if st <= 0.0:
				state = "recover"
				st = 0.5
		"recover":
			anim.play("guard")
			velocity.x = move_toward(velocity.x, 0.0, 600 * delta)
			st -= delta
			if st <= 0.0:
				_end_attack(0.6, 1.2)


func _ai_charger(delta: float, player: Node, to_p: Vector2, dist: float) -> void:
	## Kalkanlı akıncı: uzaktan kalkanını kaldırıp zırhlı hücum eder ("!!"); çarparsa fırlatır, duvara çarparsa uzun
	## sersemler (ceza penceresi). Üstünden atlanırsa kayarak döner ve kısa ikinci hücum yapabilir.
	match state:
		"idle", "chase":
			if not aggro or player == null or player.dead:
				state = "idle"
				_patrol(delta)
				anim.play("walk" if absf(velocity.x) > 8.0 else "guard")
				return
			state = "chase"
			_face(to_p)
			var tgt := facing * speed * 0.6
			if _blocked(float(facing)) or dist < 50.0:
				tgt = 0.0
			velocity.x = move_toward(velocity.x, tgt, 300 * delta)
			anim.play("walk" if absf(velocity.x) > 4.0 else "guard")
			if cd <= 0.0 and dist > 90.0 and dist < 320.0 and absf(to_p.y) < 40.0 and level.los(center(), player.center()) and _token():
				set_meta("bash", false)
				set_meta("again", randf() < 0.5)
				_tele(0.75, true)
				_face(to_p)
			elif cd <= 0.0 and dist < 64.0 and absf(to_p.y) < 50.0 and _token():
				set_meta("bash", true)
				_tele(0.4)
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
					_strike(60.0, 56.0, 0.7, Vector2(320.0, -150.0))
				else:
					state = "charge"
					st = 1.25
					sa_t = 1.3
					contact = true
					contact_k = 1.0
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
			# üstünden atlandı: kayarak dur, dön, kısa ikinci hücum
			if player and get_meta("again", false) and st < 1.0 and absf(to_p.x) > 70.0 and int(signf(to_p.x)) != facing and not is_on_wall():
				set_meta("again", false)
				contact = false
				velocity.x *= 0.3
				FX.dust(global_position, Vector2(facing, -0.3), 8, 0.32)
				facing = -facing
				_tele(0.4, true)
				return
			if is_on_wall() or st <= 0.0 or _wall_or_ledge():
				contact = false
				sa_t = 0.0
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
					_drop_token()
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
				guard_hp = 3
				_end_attack(0.9, 1.6)


func _ai_turtle(delta: float, player: Node, to_p: Vector2, dist: float) -> void:
	## Taş tosbağa: yavaş yürür, yakında ısırır; vurulunca kabuğa çekilir (dokunulmaz) ve yuvarlanarak ezer;
	## yuvarlanma bitince başı döner (ceza penceresi)
	match state:
		"idle", "chase":
			if not aggro or player == null or player.dead:
				state = "idle"
				_patrol(delta)
				anim.play("walk" if absf(velocity.x) > 6.0 else "idle")
				return
			state = "chase"
			_face(to_p)
			var tgt := facing * speed
			if _blocked(float(facing)) or dist < 50.0:
				tgt = 0.0
			velocity.x = move_toward(velocity.x, tgt, 250 * delta)
			anim.play("walk" if absf(velocity.x) > 4.0 else "idle")
			if cd <= 0.0 and dist < 66.0 and absf(to_p.y) < 44.0 and _token():
				_tele(0.5)
			elif cd <= 0.0 and dist > 110.0 and dist < 260.0 and absf(to_p.y) < 30.0 and randf() < 0.02 and _token():
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
				_strike(56.0, 36.0, 1.0, Vector2.ZERO, 10.0)
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
				contact_k = 1.2
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
				contact = false
				if player.take_hit(dmg * 1.2, self) and player.has_method("shove"):
					player.shove(Vector2(facing * 300.0, -200.0))
			if st <= 0.0:
				anim.speed = 1.0
				contact = false
				state = "recover"
				st = 1.0
				anim.play("idle", true)
				FX.text(center() + Vector2(0, -34), "başı döndü", Color(0.95, 0.9, 0.7), 7)
		"recover":
			anim.play("idle")
			velocity.x = move_toward(velocity.x, 0.0, 600 * delta)
			st -= delta
			if st <= 0.0:
				_end_attack(0.8, 1.6)


func _ai_archer(delta: float, player: Node, to_p: Vector2, dist: float) -> void:
	## Kurgan okçusu: 150-290 px uzakta durur; öngörülü ok (derinde üçlü salvo); dibine girilince geri takla atar
	match state:
		"idle", "chase":
			if not aggro or player == null or player.dead:
				state = "idle"
				_patrol(delta)
				anim.play("run" if absf(velocity.x) > 10.0 else "idle")
				return
			state = "chase"
			if dist < 90.0 and _blink_cd <= 0.0 and is_on_floor():
				_blink_cd = 2.5
				_evade(270.0, 0.38, 0.0)
				return
			var want := 0.0
			if dist < 140.0:
				want = -signf(to_p.x) * speed * 1.4
			elif dist > 300.0:
				want = signf(to_p.x) * speed
			if want != 0.0 and _blocked(signf(want)):
				want = 0.0
			velocity.x = move_toward(velocity.x, want, 500 * delta)
			_face(to_p)
			anim.play("run" if absf(velocity.x) > 10.0 else "idle")
			if cd <= 0.0 and dist < 330.0 and absf(to_p.y) < 170.0 and level.los(center(), player.center()) and _token(true):
				set_meta("n", 3 if Zorluk.derinlik() >= 3 and randf() < 0.45 else 1)
				_tele(0.62)
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
				if player:
					var n := int(get_meta("n", 1))
					var tt := clampf(dist / 380.0, 0.4, 0.9)
					var lead: Vector2 = Vector2(player.velocity.x * tt * 0.6, 0.0)
					for k in n:
						var aim: Vector2 = to_p + lead + Vector2((k - (n - 1) * 0.5) * 34.0, 0.0)
						var p := _spit("arrow", _anchor_g("hand", center() + Vector2(facing * 10, -6)), Vector2(aim.x / tt, aim.y / tt - 0.5 * 420.0 * tt), dmg, 0.0, 420.0, 2.5)
						p.trail_col = Color(0.9, 0.8, 0.6, 0.5)
					Ses.play("yay_birak", -6.0, 0.9)
		"attack":
			st -= delta
			if st <= 0.0:
				_end_attack(1.1, 1.8)
		"recover":
			st -= delta
			if st <= 0.0:
				_end_attack(0.6, 1.2)


func _ai_stalker(delta: float, player: Node, to_p: Vector2, dist: float) -> void:
	## Yek: görünmez sinsi; 110 px'e girince belirir ve hızlı hamle yapar. 3 vuruş yiyince dumana karışır ve
	## kısa süre sonra arkanda belirip vurur.
	if has_meta("ambush") and player and not player.dead:
		var a := float(get_meta("ambush")) - delta
		set_meta("ambush", a)
		velocity.x = move_toward(velocity.x, 0.0, 600 * delta)
		anim.play("idle")
		if a <= 0.0:
			remove_meta("ambush")
			var nx: float = player.global_position.x - float(player.facing) * 56.0
			var ty: int = level.surface_y(int(floor(nx / Level.TS)), int(floor(global_position.y / Level.TS)) - 2)
			if absf(ty * Level.TS - global_position.y) < 120.0 and not level.solid_at(Vector2(nx, ty * Level.TS - 20.0)):
				global_position = Vector2(nx, ty * Level.TS - 1.0)
			_reveal()
			_face(player.center() - center())
			_tele(0.3)
		return
	if _hidden:
		anim.play("idle")
		velocity.x = move_toward(velocity.x, 0.0, 600 * delta)
		if player and dist < 110.0:
			_reveal()
			_face(to_p)
			_tele(0.25)
		elif aggro and player and dist < 260.0 and Engine.get_physics_frames() % 2 == 0:
			# görünmezken sessizce yaklaşır
			_face(to_p)
			if not _wall_or_ledge():
				velocity.x = facing * speed * 0.6
		return
	_ai_lunger(delta, player, to_p, dist)


func _ai_hopper(delta: float, player: Node, to_p: Vector2, dist: float) -> void:
	## Balbal: uyanır, sekerek yaklaşır; önden savurmaya hazırlanana siper alır; taş kılıç ("!" 0,6) ya da zırhlı
	## sıçrayıp çakma ("!!" 0,55); 3 vuruşta siper + zırhlı kesik
	match state:
		"dormant":
			velocity.x = 0.0
			if aggro and dist < 170.0:
				_wake()
		"idle", "chase":
			if not aggro or player == null or player.dead:
				anim.play("idle")
				velocity.x = move_toward(velocity.x, 0.0, 600 * delta)
				return
			state = "chase"
			_face(to_p)
			anim.play("idle")
			velocity.x = move_toward(velocity.x, 0.0, 600 * delta)
			# oyuncu önden saldırıya hazırlanıyorsa siper al
			if dist < 64.0 and guard_t <= 0.0 and "atk" in player and not player.atk.is_empty() and player.atk.get("phase", "") == "wind" and randf() < 0.5:
				guard_t = 0.6
				vis_scale = Vector2(1.08, 0.94)
			if cd <= 0.0 and is_on_floor() and guard_t <= 0.0:
				if dist < 62.0 and absf(to_p.y) < 40.0 and _token():
					set_meta("move", "cut")
					_tele(0.6)
				elif dist > 80.0 and dist < 200.0 and randf() < 0.35 and _token():
					set_meta("move", "leap")
					_tele(0.55, true)
				elif not _blocked(float(facing)):
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
				cd = randf_range(0.3, 0.6)
		"windup":
			anim.play("windup")
			velocity.x = 0.0
			st -= delta
			if st <= 0.0:
				if get_meta("move", "cut") == "leap" and player:
					state = "leap"
					st = 0.0
					var dx: float = clampf(player.global_position.x - global_position.x, -220.0, 220.0)
					velocity = Vector2(dx * 1.8, -360.0)
					sa_t = 1.0
					contact = true
					contact_k = 1.0
					_did_hit = false
				else:
					state = "strike"
					st = 0.35
					FX.slash(global_position + Vector2(facing * 6, -30), facing, -2.2, 0.8, 34.0, 8.0, Color(0.85, 0.85, 0.95), 0.18)
					FX.sparks(global_position + Vector2(facing * 30, -6), Vector2(facing, -0.8), Color(0.9, 0.9, 1.0), 6, 150.0)
					vis_scale = Vector2(1.12, 0.9)
					_strike(54.0, 48.0, 1.0, Vector2.ZERO, 4.0)
		"leap":
			anim.play("hop")
			st += delta
			if is_on_floor() and st > 0.15:
				state = "strike"
				st = 0.35
				contact = false
				sa_t = 0.0
				Game.shake(3.5)
				vis_scale = Vector2(1.35, 0.7)
				FX.dust(global_position, Vector2.UP, 9, 0.34, Color(0.6, 0.6, 0.65, 0.6))
				FX.ring(global_position, 40, Color(0.8, 0.85, 0.95, 0.7), 0.25, 0.3)
				if player and not player.dead and absf(player.global_position.x - global_position.x) < 52.0 and player.is_on_floor():
					player.take_hit(dmg * 1.1, self)
		"strike":
			anim.play("strike")
			st -= delta
			if st <= 0.0:
				state = "recover"
				st = 0.55
		"recover":
			anim.play("idle")
			velocity.x = move_toward(velocity.x, 0.0, 600 * delta)
			st -= delta
			if st <= 0.0:
				_end_attack(0.4, 0.9)


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


class EliteStar extends Node2D:
	## Seçkin işareti: başın üstünde dönen, parlayan altın-mor yıldız
	var _t := 0.0

	func _ready() -> void:
		z_index = 85
		var m := CanvasItemMaterial.new()
		m.light_mode = CanvasItemMaterial.LIGHT_MODE_UNSHADED
		material = m

	func _process(delta: float) -> void:
		_t += delta
		position.y += sin(_t * 3.0) * 0.08
		queue_redraw()

	func _draw() -> void:
		var r1 := 7.0 + sin(_t * 5.0) * 0.8
		# v2: mor mürekkep halesi + altın fırça yıldızı (kenar yumuşatmasız çokgen yerine)
		InkDraw.soft(self, Vector2.ZERO, r1 * 1.5, Color(0.85, 0.45, 1.0, 0.4 + 0.15 * sin(_t * 6.0)))
		InkDraw.star(self, Vector2.ZERO, r1 * 1.25, _t * 0.8, Color(0.45, 0.15, 0.55))
		InkDraw.star(self, Vector2.ZERO, r1 * 1.05, _t * 0.8, Color(1.0, 0.86, 0.35))
		InkDraw.star(self, Vector2.ZERO, r1 * 0.5, _t * 0.8 + 0.4, Color(1.0, 0.98, 0.8))


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
