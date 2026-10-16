class_name Ok
extends Projectile
## v19 oyuncu oku (Okculuk.gd atar). Projectile'ın ok yolundan ayrı, kendi uçuşu:
##   * çok hızlı (650-1100 px/sn): kare içinde 6 px'lik alt adımlarla süpürülür, ince düşmanın içinden geçmez
##   * isabet: Okculuk'un kapanışı hasarı verir ({crit, killed} döner); son isabet oku düşmana saplar (Okculuk kaydı:
##     yakın dövüşle "ok sökme"), delen ok yoluna devam eder
##   * ıska: duvara / zemine saplanır, 6 sn kalır; üstünden geçince toplanır ("ok toplama" -> hazır ok)
##   * düşen ok (harmless): ölen düşmandan dökülen oklar; hasarsız, yere saplanınca toplanabilir
## Görünüş stil v2'de mürekkep: SusV2 ok sprite'ı (Projectile._ready) + shaders/ok_iz.gdshader fırça izi (koyu
## mürekkep kenar, oka özgü açık çekirdek, kuyrukta kuru fırça); v1'de Projectile'ın piksel izi.

const WALL_LIFE := 6.0
const SUB_STEP := 6.0
const TRAIL_AGE := 0.075        # iz bu kadar eski noktaları tutar (hızla birlikte boy: ~60-80 px)
const IZ_SHADER: Shader = preload("res://shaders/ok_iz.gdshader")
static var _iz_mat: ShaderMaterial

var okc: Okculuk
var core_col := Color(1.0, 0.93, 0.78)   # iz çekirdeği
var iz_w := 1.3                           # iz yarı genişliği (dünya birimi)
var collect := true                       # duvara saplanınca toplanabilir
var harmless := false                     # dökülen ok: hasar vermez
var ink_pal := 0                          # isabet mürekkep paleti (InkFX)
var big := false                          # tam bırakış / ağır ok: daha büyük isabet sıçrantısı
var _state := 0                           # 0 uçuş, 1 saplı (duvar / zemin)
var _wall_t := 0.0
var _pts: Array = []                      # [global konum, zaman]


func _ready() -> void:
	kind = "arrow"
	super._ready()
	if FX.ink():
		if _iz_mat == null:
			_iz_mat = ShaderMaterial.new()
			_iz_mat.shader = IZ_SHADER
			_iz_mat.set_shader_parameter("bristle", InkTrail.BRISTLE)
		material = _iz_mat
		if ink_spr:
			# sprite kendi ışık malzemesini kullanır (iz malzemesi çocuğa geçmesin)
			ink_spr.use_parent_material = false
	if harmless:
		trail_col = Color(0, 0, 0, 0)


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
	_pts.push_front([global_position, _t])
	while _pts.size() > 2 and _t - float(_pts[_pts.size() - 1][1]) > TRAIL_AGE:
		_pts.pop_back()
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
	if FX.ink():
		InkFX.hit("pierce", global_position, hd, ink_pal, 2 if crit else (1 if big else 0), 1.15 if big else 0.85)
	else:
		FX.impact(global_position, hd, Color(1.0, 0.95, 0.8) if fx_kind != "od" else Color(1.0, 0.6, 0.25), 1.2 if big else 0.9)
		FX.sparks(global_position, -hd, Color(1.0, 0.9, 0.7), 5, 140.0)
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
	_pts.clear()
	_trail.clear()
	queue_redraw()
	if not harmless:
		Ses.play_at("ok_vurus_tahta" if randf() < 0.6 else "ok_vurus_tas", global_position, -7.0)
		if FX.ink():
			var n := InkFX.spawn(7, global_position - hd * 2.0, 40)
			if n:
				n.el("burst_dir", Vector2.ZERO, (-hd).angle(), Vector2.ONE * 12.0, InkFX.V_DRY, 0.0, 0.04, 0.03, 0.22)
		else:
			FX.dust(global_position, -hd, 3, 0.2)
			FX.sparks(global_position, -hd, Color(1.0, 0.9, 0.7), 3, 90.0)
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
	if not FX.ink():
		super._draw()
		return
	if ink_spr:
		_ink_tick()
	if _state != 0 or _pts.size() < 2 or harmless:
		return
	# fırça izi: baş (ok) -> kuyruk; yerel koordinatta üçgen şeridi (tek çizim çağrısı)
	var pts := PackedVector2Array()
	var uvs := PackedVector2Array()
	var cols := PackedColorArray()
	var idx := PackedInt32Array()
	var m := _pts.size()
	var along := 0.0
	var prev: Vector2 = to_local(_pts[0][0])
	# baş: okun gövdesinin ortasından başlasın (ucun önüne taşmasın)
	var head_back := -velocity.normalized() * 6.0
	for i in m:
		var g: Vector2 = to_local(_pts[i][0]) + head_back
		if i > 0:
			along += g.distance_to(prev)
		var d: Vector2 = (prev - g) if i > 0 else -velocity.normalized()
		if i == 0 and m > 1:
			d = g - (to_local(_pts[1][0]) + head_back)
		d = d.normalized() if d.length() > 0.001 else Vector2.RIGHT
		var nrm := Vector2(-d.y, d.x)
		var u := float(i) / float(m - 1)
		var w := iz_w * (1.0 - 0.75 * u)
		var c := Color(core_col.r, core_col.g, core_col.b, u)
		pts.append(g + nrm * w)
		pts.append(g - nrm * w)
		uvs.append(Vector2(along / 40.0, 0.0))
		uvs.append(Vector2(along / 40.0, 1.0))
		cols.append(c)
		cols.append(c)
		if i > 0:
			var s := (i - 1) * 2
			idx.append_array([s, s + 1, s + 2, s + 1, s + 3, s + 2])
		prev = g
	if idx.is_empty():
		return
	RenderingServer.canvas_item_add_triangle_array(get_canvas_item(), idx, pts, cols, uvs)
