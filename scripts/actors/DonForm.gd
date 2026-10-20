class_name DonForm
extends Node2D
## Don Değiştirme (kam geleneğinde "don" = kılık): devrilen bir seçkinin ruhunu emersin, G ile onun kılığına girersin.
## Kılığın hamle takımı yaratığın türünden gelir:
##   kurt   (atılgan, pusucu, tazı): hızlı koşu, J üçlü atılış ısırığı, K yüksek sıçrayış
##   kalkan (kalkanlı)            : hasarın yarısını alır, J kalkan vuruşu (sersemletir), K siper (kısa dokunulmazlık)
##   kabuk  (kaplumbağa)          : J kabukta yuvarlanma (dokunulmaz, çok vuruş), K kabuğa çekilme
##   hucum  (hücumcu)             : J uzun hücum (duvara kadar), K ezme sıçrayışı
##   dev    (iri, yakalayan)      : yavaş, J yere çakma (geniş alan), K iki yana sarsıntı dalgası
##   kanat  (uçan, dalan)         : uçar (Boşluk basılı), J pike dalış, K tüy oku
##   buyucu (okçu, illüzyoncu)    : J üçlü büyü mermisi, K ışınlanma

const ARCH := {
	"lunger": "kurt", "pouncer": "kurt", "stalker": "kurt", "hopper": "kurt",
	"shield": "kalkan", "turtle": "kabuk", "charger": "hucum",
	"brute": "dev", "grabber": "dev",
	"flyer_ranged": "kanat", "diver": "kanat", "flyer": "kanat",
	"archer": "buyucu", "illusionist": "buyucu",
}
const ARCH_NAME := {"kurt": "atılgan", "kalkan": "kalkanlı", "kabuk": "kabuklu", "hucum": "hücumcu", "dev": "iri", "kanat": "kanatlı", "buyucu": "büyücü"}
const COL := Color(0.75, 0.55, 1.0)

var pl: Node
var kind := ""
var arch := "kurt"
var t := 0.0
var dur := 10.0
var anim: SpriteAnim
var atk: Dictionary = {}
var hit: Array = []
var cd_k := 0.0
var step := 0
var since := 9.0
var guard_t := 0.0
var proj_kind := "curse"
var sc_k := 1.0


static func arch_of(enemy_kind: String) -> String:
	var d := Data.enemy_def(enemy_kind)
	return String(ARCH.get(String(d.get("ai", "")), "kurt"))


func begin(p: Node, enemy_kind: String) -> void:
	pl = p
	kind = enemy_kind
	arch = arch_of(enemy_kind)
	var d := Data.enemy_def(enemy_kind)
	proj_kind = "arrow" if String(d.get("ai", "")) == "archer" else ("spore" if String(Game.run.get("biome", "")) == "sahmeran" else "curse")
	dur = 10.0 * (1.5 if Adlar.earned("donen") else 1.0)
	t = dur
	atk = {}
	step = 0
	since = 9.0
	cd_k = 0.0
	if anim:
		anim.queue_free()
	anim = SpriteAnim.new()
	add_child(anim)
	var spr := String(d.get("sprite", enemy_kind))
	anim.setup(spr if spr != "" else enemy_kind)
	var cell: Array = anim.meta.get("cell", [64, 64])
	var sc := clampf(70.0 / maxf(1.0, float(cell[1])), 0.55, 1.0)
	anim.scale = Vector2(sc, sc)
	sc_k = sc
	anim.set_tint(Color(1.05, 0.95, 1.25))
	anim.set_facing(pl.facing)
	_play(["idle"])
	visible = true


func _play(names: Array, restart := false) -> void:
	for n in names:
		if anim.has_anim(n):
			anim.play(n, restart)
			return


func _frame(names: Array, k: float) -> void:
	for n in names:
		if anim.has_anim(n):
			anim.show_frame(n, clampi(int(k * anim.frame_count(n)), 0, anim.frame_count(n) - 1))
			return


func dmg_mult() -> float:
	## Kılıktayken alınan hasar çarpanı
	match arch:
		"kalkan":
			return 0.0 if guard_t > 0.0 else 0.5
		"kabuk":
			return 0.0 if (atk.get("kind", "") in ["roll", "hide"]) else 0.6
		"dev":
			return 0.7
	return 0.85


func display_name() -> String:
	return String(Data.enemy_def(kind).get("name", kind))


func _it() -> Dictionary:
	var it: Dictionary = pl.slot(pl.mel_slot)
	return it if not it.is_empty() else {"dmg": 12, "material": "demir", "aps": 1.5, "id": "don"}


func _hit_box(box: Rect2, mult: float, opts: Dictionary, once := true) -> int:
	var n := 0
	var it := _it()
	for e in pl.get_tree().get_nodes_in_group("dusman"):
		if not is_instance_valid(e) or e.dead or (once and hit.has(e)):
			continue
		if box.intersects(e.hurt_rect()):
			hit.append(e)
			var o := opts.duplicate()
			o["don"] = true
			pl._deal(e, float(it.get("dmg", 10)) * mult, it, o)
			var hp2: Vector2 = e.hurt_rect().intersection(box).get_center()
			FX.impact(hp2, Vector2(pl.facing, -0.3), COL, 1.1)
			FX.blood(hp2, Vector2(pl.facing, -0.5), e.blood_col(), 8)
			n += 1
	if n > 0:
		Game.hitstop(0.05)
		Game.kick(Vector2(pl.facing, 0), 3.5)
		t = minf(dur, t + 0.25)
	return n


func process(delta: float) -> void:
	t -= delta
	since += delta
	cd_k -= delta
	guard_t -= delta
	pl.inv_t -= delta
	pl.hurt_t -= delta
	pl.coyote -= delta
	pl.jump_buf -= delta
	pl.drop_t -= delta
	pl.set_collision_mask_value(4, pl.drop_t <= 0.0)   # v33: dönüşmüş biçimde de tek yönlü platformdan inilir
	if t <= 0.0:
		pl._end_don()
		return
	var dir := Input.get_axis("sol", "sag")
	var fl: bool = pl.is_on_floor()
	if Input.is_action_just_pressed("zipla"):
		pl.jump_buf = float(pl.FLOW["buf_jump"])   # v34: oyuncuyla aynı tampon / coyote
	if fl:
		pl.coyote = float(pl.FLOW["coyote"])
		pl.air_jumps = 1
	if Engine.get_physics_frames() % 3 == 0:
		FX.burst(pl.center() + Vector2(randf_range(-12, 12), randf_range(-14, 10)), COL, 1, 22, 0.5, 0.15, -50, true)
	var spd: float = pl.RUN * {"kurt": 1.5, "kalkan": 0.95, "kabuk": 0.85, "hucum": 1.15, "dev": 0.8, "kanat": 1.2, "buyucu": 1.05}.get(arch, 1.0)
	# ---------------- giriş: J ana hamle, K ikinci hamle
	if Input.is_action_just_pressed("saldiri1") and atk.is_empty():
		_start_j(dir)
	elif Input.is_action_just_pressed("saldiri2") and atk.is_empty() and cd_k <= 0.0:
		_start_k(dir)
	# ---------------- hamle güncelle
	if not atk.is_empty():
		_update_atk(delta)
	else:
		var target := dir * spd
		var acc: float = pl.ACC_GROUND if fl else pl.ACC_AIR
		if pl.hurt_t <= 0.0:
			pl.velocity.x = move_toward(pl.velocity.x, target, acc * delta)
		if dir != 0 and pl.hurt_t <= 0.0:
			pl.facing = int(signf(dir))
		if arch == "kanat":
			# uçuş: Boşluk basılıyken yüksel, bırakınca süzül
			if Input.is_action_pressed("zipla"):
				pl.velocity.y = move_toward(pl.velocity.y, -220.0, 1400.0 * delta)
				if Engine.get_physics_frames() % 6 == 0:
					FX.dust(pl.global_position + Vector2(0, 4), Vector2(0, 1), 1, 0.2, Color(COL, 0.4))
		elif pl.jump_buf > 0.0 and fl and Input.is_action_pressed("asagi"):
			# v33: aşağı + zıpla: tek yönlü platformdan / kuyu kapağından iner
			pl.drop_t = 0.25
			pl.jump_buf = 0.0
			pl.position.y += 2
		elif pl.jump_buf > 0.0 and (pl.coyote > 0.0 or pl.air_jumps > 0):
			if pl.coyote <= 0.0:
				pl.air_jumps -= 1
			pl.velocity.y = pl.JUMP_V * (0.9 if arch == "dev" else 1.05)
			pl.jump_buf = 0.0
			pl.coyote = 0.0
			pl.jumping = true
			pl.vis_scale = Vector2(0.85, 1.15)
			FX.dust(pl.global_position, Vector2.UP, 4, 0.28)
	# v34: yükseliş / düşüş yerçekimi oyuncuyla aynı (Dead Cells zıplaması); kanat süzülür
	var g: float = (pl.GRAV_RISE if pl.velocity.y < 0.0 else pl.GRAV_FALL) * (0.3 if arch == "kanat" else 1.0)
	if fl:
		pl.jumping = false
	elif pl.jumping and arch != "kanat" and pl.velocity.y < -140.0 and not Input.is_action_pressed("zipla"):
		pl.velocity.y *= pl.JUMP_CUT   # alçak zıplama (bir kez)
		pl.jumping = false
	pl.velocity.y = minf(pl.velocity.y + g * delta, pl.MAX_FALL * (0.45 if arch == "kanat" and not atk.get("kind", "") == "dive" else 1.0))
	pl.move_and_slide()
	anim.set_facing(pl.facing)
	if atk.is_empty():
		if pl.hurt_t > 0.0:
			_play(["hurt", "idle"])
		elif not pl.is_on_floor() and arch != "kanat":
			_frame(["jump", "leap", "windup", "idle"], 0.5 if pl.velocity.y < 0 else 0.9)
		elif absf(pl.velocity.x) > 14.0 or arch == "kanat":
			_play(["run", "walk", "fly", "idle"])
			anim.speed = clampf(absf(pl.velocity.x) / spd, 0.7, 1.5)
		else:
			_play(["idle"])
			anim.speed = 1.0
	# yaylı gövde (oyuncunun yayını paylaşır)
	pl._vs_v += ((Vector2.ONE - pl.vis_scale) * 320.0 - pl._vs_v * 17.0) * delta
	pl.vis_scale += pl._vs_v * delta
	anim.scale = Vector2.ONE * sc_k * pl.vis_scale
	anim.rotation = lerpf(anim.rotation, clampf(pl.velocity.x / 900.0, -0.12, 0.12), 0.2)
	if Engine.get_physics_frames() % 4 == 0 and absf(pl.velocity.x) > 120.0:
		FX.ghost(anim.base, Color(COL, 0.3), 0.2)
	anim.set_flash(0.3 if (t < 1.5 and int(t * 8.0) % 2 == 0) else 0.0)
	pl._safety(delta)


func _start_j(dir: float) -> void:
	if dir != 0:
		pl.facing = int(signf(dir))
	hit = []
	pl._usul_press()
	match arch:
		"kurt":
			if since > 0.45:
				step = 0
			atk = {"kind": "lunge", "t": 0.0, "dur": 0.26 if step < 2 else 0.34, "step": step}
			pl.velocity.x = pl.facing * (420.0 if step < 2 else 520.0)
			Ses.play("isirik", -2.0, 1.1 if step < 2 else 0.9)
		"kalkan":
			atk = {"kind": "bash", "t": 0.0, "dur": 0.3}
			pl.velocity.x = pl.facing * 340.0
			Ses.play("savur_agir", -3.0, 0.9)
		"kabuk":
			atk = {"kind": "roll", "t": 0.0, "dur": 0.9}
			Ses.play("yuvarlan", -2.0, 0.7)
		"hucum":
			atk = {"kind": "charge", "t": 0.0, "dur": 0.7}
			Ses.play("savur_dev", -3.0, 0.8)
			FX.ring(pl.center(), 26, COL, 0.25)
		"dev":
			atk = {"kind": "slam", "t": 0.0, "dur": 0.55, "done": false}
			pl.velocity.x = 0.0
			Ses.play("savur_dev", -2.0, 0.7)
		"kanat":
			atk = {"kind": "dive", "t": 0.0, "dur": 1.2}
			pl.velocity = Vector2(pl.facing * 260.0, 560.0)
			Ses.play("savur_hafif", -3.0, 0.8)
		"buyucu":
			atk = {"kind": "cast", "t": 0.0, "dur": 0.35, "done": false}
			pl.velocity.x *= 0.3
	pl.vis_scale = Vector2(1.12, 0.9)


func _start_k(dir: float) -> void:
	if dir != 0:
		pl.facing = int(signf(dir))
	hit = []
	match arch:
		"kurt":
			atk = {"kind": "pounce", "t": 0.0, "dur": 0.5}
			pl.velocity = Vector2(pl.facing * 360.0, -470.0)
			Ses.play("sicrayis", -2.0)
			cd_k = 0.8
		"kalkan":
			guard_t = 1.0
			cd_k = 3.0
			FX.ring(pl.center(), 30, Color(0.8, 0.85, 1.0), 0.4)
			FX.text(pl.center() + Vector2(0, -40), "SİPER", Color(0.8, 0.85, 1.0), 9)
			Ses.play("darbe_kalkan" if Ses.has("darbe_kalkan") else "darbe_kunt", -4.0)
		"kabuk":
			atk = {"kind": "hide", "t": 0.0, "dur": 0.8}
			pl.velocity.x = 0.0
			cd_k = 2.0
		"hucum":
			atk = {"kind": "pounce", "t": 0.0, "dur": 0.55}
			pl.velocity = Vector2(pl.facing * 240.0, -420.0)
			cd_k = 1.0
		"dev":
			cd_k = 2.2
			_quake()
		"kanat":
			cd_k = 0.45
			_shoot("eagle", 1, 380.0)
		"buyucu":
			cd_k = 1.4
			_blink()


func _update_atk(delta: float) -> void:
	atk["t"] = float(atk["t"]) + delta
	var k: float = float(atk["t"]) / float(atk["dur"])
	var f := float(pl.facing)
	var gp: Vector2 = pl.global_position
	match String(atk["kind"]):
		"lunge":
			_frame(["strike", "bite", "attack", "lunge", "windup"], k)
			pl.velocity.x = move_toward(pl.velocity.x, 0.0, 1400.0 * delta)
			if k > 0.15 and k < 0.75:
				var last: bool = int(atk["step"]) == 2
				_hit_box(Rect2(gp.x + (0.0 if f > 0 else -58.0), gp.y - 42.0, 58.0, 42.0), 1.2 if not last else 1.9, {"kb": 100.0 if not last else 260.0, "dir": f, "launch": 200.0 if last else 0.0, "bitiris": last})   # v26: kesin kritik değil, bitiriş hasarı
		"pounce":
			_frame(["leap", "jump", "strike", "windup"], minf(k, 0.99))
			_hit_box(pl.hurt_rect().grow(10), 1.5, {"kb": 180.0, "dir": f, "launch": 180.0, "stun": 0.4})
			if pl.is_on_floor() and k > 0.2:
				_shock(70.0, 1.0)
				atk["t"] = float(atk["dur"])
		"bash":
			_frame(["strike", "attack", "windup"], k)
			pl.velocity.x = move_toward(pl.velocity.x, 0.0, 1200.0 * delta)
			if k > 0.2 and k < 0.7:
				if _hit_box(Rect2(gp.x + (0.0 if f > 0 else -46.0), gp.y - 44.0, 46.0, 44.0), 1.3, {"kb": 320.0, "dir": f, "stun": 0.9, "stagger": true}) > 0:
					FX.sparks(gp + Vector2(f * 20, -24), Vector2(f, -0.4), Color(1, 0.9, 0.7), 8, 180.0)
		"roll":
			_frame(["roll", "strike", "idle"], fmod(k * 4.0, 1.0))
			pl.velocity.x = f * 430.0
			pl.inv_t = maxf(pl.inv_t, 0.1)
			if int(float(atk["t"]) / 0.2) != int((float(atk["t"]) - delta) / 0.2):
				hit = []
			_hit_box(pl.hurt_rect().grow(8), 0.6, {"kb": 160.0, "dir": f, "launch": 120.0})
			if pl.is_on_wall():
				pl.facing = -pl.facing
				Game.shake(2.0)
				FX.dust(gp, Vector2(-f, -0.4), 5, 0.3)
		"hide":
			_frame(["hide", "hurt", "idle"], k)
			pl.inv_t = maxf(pl.inv_t, 0.1)
			pl.velocity.x = move_toward(pl.velocity.x, 0.0, 1600.0 * delta)
		"charge":
			_frame(["run", "walk", "strike"], fmod(k * 3.0, 1.0))
			pl.velocity.x = f * 560.0
			if Engine.get_physics_frames() % 2 == 0:
				FX.dust(gp + Vector2(-f * 12, 0), Vector2(-f, -0.4), 2, 0.28)
			_hit_box(pl.hurt_rect().grow(12), 1.6, {"kb": 340.0, "dir": f, "launch": 160.0, "stun": 0.6})
			if pl.is_on_wall():
				Game.shake(6.0)
				Ses.play("darbe_cekic", -2.0, 0.8)
				FX.impact_sprite("blunt", gp + Vector2(f * 10, -22), Vector2(f, 0), COL, 1.2)
				atk["t"] = float(atk["dur"])
		"slam":
			_frame(["slam", "strike", "windup"], k)
			if k > 0.45 and not atk["done"]:
				atk["done"] = true
				_shock(84.0, 2.2, Vector2(f * 30, 0))
		"dive":
			_frame(["dive", "strike", "fly", "idle"], k)
			pl.velocity = Vector2(f * 260.0, 560.0)
			_hit_box(pl.hurt_rect().grow(10), 1.4, {"kb": 120.0, "dir": f, "stun": 0.3})
			if pl.is_on_floor():
				_shock(70.0, 1.4)
				atk["t"] = float(atk["dur"])
		"cast":
			_frame(["cast", "strike", "attack", "windup"], k)
			if k > 0.4 and not atk["done"]:
				atk["done"] = true
				_shoot(proj_kind, 3, 360.0)
	if k >= 1.0:
		if String(atk["kind"]) == "lunge":
			step = 0 if int(atk["step"]) == 2 else int(atk["step"]) + 1
			since = 0.0
		atk = {}


func _shock(r: float, mult: float, off := Vector2.ZERO) -> void:
	var c: Vector2 = pl.global_position + off
	Game.shake(6.0)
	Game.kick(Vector2.DOWN, 5.0)
	Ses.play("sarsinti", -2.0, 0.9)
	FX.anim("earth_rupture", c, 0.0, r / 60.0, COL, false)
	FX.ring(c, r, COL, 0.35)
	FX.dust(c, Vector2.UP, 10, 0.38)
	hit = []
	_hit_box(Rect2(c.x - r, c.y - 50.0, r * 2.0, 56.0), mult, {"kb": 220.0, "dir": float(pl.facing), "launch": 220.0, "stun": 0.5})


func _quake() -> void:
	## İri kılık: iki yana yerden sarsıntı dalgası
	_play(["slam", "strike"], true)
	Game.shake(7.0)
	Ses.play("sarsinti_buyuk", 0.0, 0.8)
	for sgn in [-1, 1]:
		var p := Projectile.new()
		p.team = "p"
		p.kind = "ground_wave"
		p.position = pl.global_position + Vector2(sgn * 14, -14)
		p.velocity = Vector2(sgn * 300.0, 0)
		p.life = 1.4
		p.pierce = 9
		p.set_meta("col", COL)
		var it := _it()
		p.on_hit = func(e: Node) -> void:
			pl._deal(e, float(it.get("dmg", 10)) * 0.9, it, {"kb": 160.0, "dir": float(sgn), "launch": 200.0, "don": true})
		pl.level.add_projectile(p)


func _shoot(k: String, n: int, speed: float) -> void:
	var it := _it()
	_play(["cast", "strike", "attack"], true)
	Ses.play("buyu" if k != "arrow" else "yay_birak", -3.0, 1.0)
	for i in n:
		var p := Projectile.new()
		p.team = "p"
		p.kind = k
		p.position = pl.center() + Vector2(pl.facing * 14, -6)
		var a := (float(i) - (n - 1) / 2.0) * 0.18
		p.velocity = Vector2(pl.facing * speed, 0).rotated(a * pl.facing)
		p.gravity = 0.0
		p.life = 1.6
		p.trail_col = Color(COL, 0.7)
		var sgn := float(pl.facing)
		p.on_hit = func(e: Node) -> void:
			pl._deal(e, float(it.get("dmg", 10)) * 0.8, it, {"kb": 70.0, "dir": sgn, "don": true})
		pl.level.add_projectile(p)
	FX.flash_light(pl.center(), COL, 120.0, 1.4, 0.2)


func _blink() -> void:
	var from: Vector2 = pl.global_position
	var to := from
	for k in range(5, 0, -1):
		var c := from + Vector2(pl.facing * 24.0 * k, 0)
		if not pl.level.solid_at(c + Vector2(0, -20)) and not pl.level.solid_at(c + Vector2(0, -36)):
			to = c
			break
	FX.anim("smoke_puff", from + Vector2(0, -20), 0.0, 0.9, COL, false)
	FX.ghost(anim.base, Color(COL, 0.6), 0.3)
	pl.global_position = to
	pl.inv_t = maxf(pl.inv_t, 0.3)
	FX.anim("smoke_puff", to + Vector2(0, -20), 0.0, 0.9, COL, false)
	FX.ring(to + Vector2(0, -20), 24, COL, 0.25)
	Ses.play("buyu", -4.0, 1.3)
