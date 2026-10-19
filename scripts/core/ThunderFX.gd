class_name ThunderFX
extends Node2D
## Gök gürlemesi (yıldırım düşmesi): ışık önce, gürleme sonra.
##   kare 0-2     ön kıvılcım: ekranın üst kenarında, düşecek noktanın üstünde 2 kare titreyen minik çatal
##   kare 3       tam ekran beyaz (1 kare) + gökten pos'a inen ana şimşek (2-3 dal) + yer çarpma flaşı
##                (beyaz disk + ışınlar + kıvılcım + nokta ışığı) + yere yatık kavrulma halkası; Ses: simsek_catirti
##   +90 ms       gürleme: Game.shake_dir(0.5, AŞAĞI), rumble(0.9, 0.5, 0.35), kick, ekran kırılma halkası;
##                Ses: gok_gurleme (yoksa yildirim)
##   1,4 s        kavrulma izi erir, düğüm silinir
## Stil v2 (ink): ön kıvılcım ve ışınlar fırça darbesi, çarpma flaşı yumuşak mürekkep halesi, kavrulma izi
## piksel serpintisi yerine yere yatık yanık mürekkep lekesi + kül pulları (InkDraw).
## Ses adları Ses.has ile korunur (ses ajanı paralel üretiyor); yedek "yildirim".

var strength := 1.0
var col := Color(0.72, 0.86, 1.0)
var life := 1.5
var _t := 0.0
var _frame := 0
var _sky := Vector2.ZERO        # ekranın üst kenarındaki ön kıvılcım noktası
var _top := Vector2.ZERO        # ekran dışı başlangıç (ana şimşek)
var _struck := false
var _boomed := false
var _spark: PackedVector2Array
var _rays: Array = []
var _scorch: Array = []         # kavrulma pikselleri (yerel)
var _strike_t := 0.0
const T_BOOM := 0.09


func _ready() -> void:
	InkDraw.prep(self)
	z_index = 66
	var m := CanvasItemMaterial.new()
	m.light_mode = CanvasItemMaterial.LIGHT_MODE_UNSHADED
	material = m
	var vp := get_viewport()
	var top_y := global_position.y - 300.0
	if vp:
		var ct := vp.get_canvas_transform()
		top_y = (ct.affine_inverse() * Vector2.ZERO).y
	var jitter := randf_range(-40.0, 40.0) * strength
	_sky = Vector2(global_position.x + jitter, top_y + 10.0)
	_top = Vector2(global_position.x + jitter * 1.3, top_y - 40.0)
	# ön kıvılcım: 8-12 px kısa çatal
	var tip := _sky + Vector2(randf_range(-4, 4), randf_range(8, 12))
	_spark = LightningFX._bolt(_sky, tip, 0.35, 2)
	var nr := 5 + randi() % 2
	var base := randf() * TAU
	for i in nr:
		_rays.append(base + TAU * float(i) / nr + randf_range(-0.2, 0.2))
	# kavrulma: yere yatık elips içinde seyrek koyu pikseller
	var rx := 10.0 + 8.0 * strength
	for i in int(rx * 2.2):
		var a := randf() * TAU
		var d := sqrt(randf())
		_scorch.append(Vector2(floorf(cos(a) * rx * d), floorf(2.0 + sin(a) * rx * 0.3 * d)))


func _process(delta: float) -> void:
	_t += delta
	_frame += 1
	if _t >= life:
		queue_free()
		return
	if not _struck and _frame >= 3:
		_struck = true
		_strike()
	if _struck and not _boomed and _t >= _strike_t + T_BOOM:
		_boomed = true
		_boom()
	queue_redraw()


func _strike() -> void:
	_strike_t = _t
	# 1 kare tam beyaz ekran
	FX.screen_flash(clampf(0.75 + 0.2 * strength, 0.0, 1.0), 1)
	# ana şimşek: gökten pos'a, kalın, 2-3 dal
	var l := LightningFX.new()
	l.a = _top
	l.b = global_position
	l.col = col
	l.life = 0.22
	l.width = 2
	l.branches = 2 + randi() % 2
	FX.root.add_child(l)
	# yer çarpması
	FX.sparks(global_position, Vector2.UP, Color(0.9, 0.95, 1.0), 10 + int(6 * strength), 240.0)
	FX.flash_light(global_position, col, 120.0 + 80.0 * strength, 2.6, 0.3)
	FX.ring(global_position + Vector2(0, 3), 26.0 + 18.0 * strength, col, 0.22, 0.3)
	_snd(["simsek_catirti", "yildirim"])


func _boom() -> void:
	Game.shake_dir(clampf(0.5 * strength, 0.0, 0.85), Vector2.DOWN)
	Game.rumble(0.9, 0.5, 0.35)
	Game.kick(Vector2.DOWN, 3.0)
	FX.shockwave(global_position, 70.0 + 50.0 * strength, 0.7)
	_snd(["gok_gurleme", "yildirim"])


static func _snd(names: Array) -> void:
	for n in names:
		if Ses.has(n):
			Ses.play(n, 0.0)
			return


func _draw() -> void:
	_ink_draw()


func _disc(c: Vector2, r: int, colr: Color) -> void:
	var cx := floorf(c.x)
	var cy := floorf(c.y)
	var rr := float(r * r + r)
	for y in range(-r, r + 1):
		var hw := int(floor(sqrt(maxf(0.0, rr - float(y * y)))))
		draw_rect(Rect2(cx - hw, cy + y, 2 * hw + 1, 1), colr)


func _ink_draw() -> void:
	if not _struck:
		if _frame % 2 == 0:
			var pts := LightningFX._bolt(_sky, _sky + Vector2(randf_range(-4, 4), randf_range(8, 12)), 0.35, 2)
			var lp := PackedVector2Array()
			for q in pts:
				lp.append(to_local(q))
			InkDraw.line(self, lp, 2.2, 0.4, Color(1.3, 1.3, 1.35))
			InkDraw.soft(self, to_local(_sky), 3.0, Color(col, 0.9))
		return
	var dt := _t - _strike_t
	if dt < 0.035:
		var r := 9.0 + 6.0 * strength
		InkDraw.soft(self, Vector2(0, -2), r * 1.4, Color(col, 0.7))
		InkDraw.blot(self, Vector2(0, -2), r * 0.75, Color(1.4, 1.4, 1.45), 3)
		for a in _rays:
			var d := Vector2.from_angle(a)
			InkDraw.stroke(self, d * (r * 0.6), d * (r * 3.2), 3.0, Color(1.3, 1.3, 1.35))
	elif dt < 0.07:
		InkDraw.blot(self, Vector2(0, -2), 5.0 + 3.0 * strength, col, 5)
	# kavrulma izi: yanık mürekkep lekesi ve kül pulları, 0,9 sn sonra solar
	var sk := clampf((dt - 0.9) / 0.45, 0.0, 1.0)
	var rx := 10.0 + 8.0 * strength
	InkDraw.ellipse(self, Vector2(0, 2), rx, rx * 0.28, Color(0.07, 0.05, 0.07, 0.85 * (1.0 - sk)), "leke_1")
	for i in mini(6, _scorch.size()):
		var q: Vector2 = _scorch[i]
		InkDraw.flake(self, q, 2.2, float(i) * 1.7, Color(0.14, 0.11, 0.12, 1.0 - sk))
