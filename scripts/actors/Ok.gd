class_name Ok
extends Projectile
## v19 oyuncu oku (Okculuk.gd atar). Projectile'ın ok yolundan ayrı, kendi uçuşu:
##   * çok hızlı (650-1100 px/sn): kare içinde 6 px'lik alt adımlarla süpürülür, ince düşmanın içinden geçmez
##   * isabet: Okculuk'un kapanışı hasarı verir ({crit, killed} döner); son isabet oku düşmana saplar (Okculuk kaydı:
##     yakın dövüşle "ok sökme"), delen ok yoluna devam eder
##   * ıska: duvara / zemine saplanır, 6 sn kalır; üstünden geçince toplanır ("ok toplama" -> hazır ok)
##   * düşen ok (harmless): ölen düşmandan dökülen oklar; hasarsız, yere saplanınca toplanabilir
## Görünüş stil v2'de mürekkep: SusV2 ok sprite'ı (Projectile._ready) + v25 OkIz: çok ince, unsur renginde fırça izi
## (ayrı düğüm: ok saplanınca / yok olunca iz erir); unsurlu okta sprite unsur rengine çalar ve ardında unsur zerresi
## uçuşur. v1'de Projectile'ın piksel izi.

const WALL_LIFE := 6.0
const SUB_STEP := 6.0

var okc: Okculuk
# v25: unsur (Projectile.unsur): iz rengi / sprite tonu / zerre ("altin" tam bırakış, "od" Od Okları)
var iz_w := 0.4                           # iz yarı genişliği (dünya birimi; 1080p'de x3,4 px)
var iz: OkIz = null
var collect := true                       # duvara saplanınca toplanabilir
var harmless := false                     # dökülen ok: hasar vermez
var ink_pal := 0                          # isabet mürekkep paleti (InkFX)
var big := false                          # tam bırakış / ağır ok: daha büyük isabet sıçrantısı
var _state := 0                           # 0 uçuş, 1 saplı (duvar / zemin)
var _wall_t := 0.0


func _ready() -> void:
	kind = "arrow"
	super._ready()
	if harmless:
		trail_col = Color(0, 0, 0, 0)
	else:
		iz = OkIz.attach(self, unsur, iz_w)
		trail_col = Color(0, 0, 0, 0)   # v1 piksel izi çizilmesin
		if ink_spr and unsur != "" and unsur != "altin" and OkIz.RENK.has(unsur):
			# v25: unsurlu ok unsur rengine çalar (v20'de oklar unsur tetikliyordu ama görünmüyordu)
			var uc: Color = Unsur.color(unsur)
			ink_spr.modulate = Color(1, 1, 1).lerp(Color(uc.r * 1.35, uc.g * 1.35, uc.b * 1.35), 0.55)


func iz_flying() -> bool:
	return _state == 0


func _physics_process(delta: float) -> void:
	_t += delta
	if _state == 1:
		_wall_tick(delta)
		return
	life -= delta
	if life <= 0.0:
		queue_free()
		return
	velocity.y += gravity * delta
	var step := velocity * delta
	var n := maxi(1, int(ceil(step.length() / SUB_STEP)))
	var p0 := position
	for k in n:
		var q := p0 + step * (float(k + 1) / float(n))
		if level.solid_at(q):
			position = q
			_hit_wall()
			return
		if not harmless and team == "p":
			for e in get_tree().get_nodes_in_group("dusman"):
				if not is_instance_valid(e) or e.dead or _hit.has(e):
					continue
				if e.hurt_rect().grow(3.0).has_point(q):
					position = q
					if _hit_enemy(e):
						return
	position = p0 + step
	_set_arrow_frame(velocity.angle())
	_trail_push()
	queue_redraw()


func _trail_push() -> void:
	if trail_col.a > 0.0:
		_trail.push_front(global_position)
		if _trail.size() > (14 if fx_kind != "" else 9):
			_trail.pop_back()
	match fx_kind:
		"od":
			if int(_t * 60.0) % 4 == 0:
				FX.fire(global_position, 1, 0.24, 1.0)


func _hit_enemy(e: Node) -> bool:
	## true: ok bitti (saplandı)
	_hit.append(e)
	var res: Variant = on_hit.call(e) if on_hit.is_valid() else {}
	var r: Dictionary = res if res is Dictionary else {}
	var hd := velocity.normalized()
	var crit: bool = r.get("crit", false)
	Ses.play("ok_vurus", -3.0 if crit else -4.5, 1.05 if not big else 0.9, 0.1, 0.02, global_position)
	InkFX.hit("pierce", global_position, hd, ink_pal, 2 if crit else (1 if big else 0), 1.15 if big else 0.85)
	if fx_kind == "od":
		FX.fire(global_position, 6, 0.34, 4.0)
	if pierce > 0:
		pierce -= 1
		if okc:
			okc.on_pierce(e, self)
		return false
	if okc and is_instance_valid(e) and not e.dead:
		okc.stick(e, self, global_position + hd * 4.0)
	queue_free()
	return true


func _hit_wall() -> void:
	## Duvara / zemine saplanır: biraz içeri girer, titrer; toplanabilir
	var hd := velocity.normalized()
	# yüzeye geri çek: ucun yarısı içeride kalsın
	for i in 8:
		if not level.solid_at(position - hd * 2.0):
			break
		position -= hd * 2.0
	position += hd * 3.0
	_state = 1
	_wall_t = 0.0
	_wobble = 6
	_trail.clear()
	if iz:
		iz.stop()
	queue_redraw()
	if not harmless:
		Ses.play_at("ok_vurus_tahta" if randf() < 0.6 else "ok_vurus_tas", global_position, -7.0)
		# v31: saplanma — geri sıçrayan küçük sumi patlaması + tek karelik parlama + geri yöne birkaç damla
		var n := InkFX.spawn(7, global_position - hd * 2.0, 40, true)
		if n:
			n.el("flash", Vector2.ZERO, hd.angle(), Vector2(16.0, 8.0), InkFX.V_CUT, 0.0, 0.001, 0.025, 0.05)
			n.el("burst_ink", Vector2.ZERO, hd.angle(), Vector2.ONE * 13.0, InkFX.V_DRY, 0.0, 0.04, 0.04, 0.24)
			n.el("drops_dir", Vector2.ZERO, (-hd).angle() + randf_range(-0.3, 0.3), Vector2(14.0, 10.0), InkFX.V_STAMP, 0.01, 0.05, 0.05, 0.3)
	if not collect or okc == null:
		_wall_t = WALL_LIFE - 1.0


func _wall_tick(delta: float) -> void:
	_wall_t += delta
	if _wobble > 0 and Engine.get_physics_frames() % 2 == 0:
		_wobble -= 1
		_set_arrow_frame(velocity.angle(), (1 if _wobble % 2 == 0 else -1) if _wobble > 1 else 0)
	# toplama: oyuncu üstünden geçer (yuvarlanırken de)
	if collect and okc and _wall_t > 0.12 and level and level.player:
		var pl: Node = level.player
		if not pl.dead and pl.hurt_rect().grow(7.0).has_point(global_position):
			okc.on_pickup(self)
			queue_free()
			return
	# toplanabilir ok: hafifçe nabız atan parıltı (son saniyede söner)
	var fade := clampf((WALL_LIFE - _wall_t) / 1.0, 0.0, 1.0)
	var pulse := 1.0 + (0.18 * (0.5 + 0.5 * sin(_wall_t * 6.0)) if collect and okc else 0.0)
	modulate = Color(pulse, pulse, pulse, fade)
	if _wall_t >= WALL_LIFE:
		queue_free()


func _draw() -> void:
	if ink_spr:
		_ink_tick()
	# v25: uçuş izi ayrı düğümde (OkIz)
