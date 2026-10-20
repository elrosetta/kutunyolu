class_name Sandik
extends Node2D
## v34 Lanetli Sandık (Dead Cells'in lanetli sandığı): uzantının ya da bir dalın sonundaki ödül odasında, zincirli kara
## sandık. Dibinde W ile açılır (isteğe bağlı: risk / ödül): üst kademe eşya + bol altın + Kut taneleri; karşılığında
## oyuncu LANETLENİR: LANET_OLDUR yaratık öldürene dek aldığı her darbe İKİ KAT (Level.lanet_*; ölümcül fazlalık
## Player.take_hit yoluyla, Umay / Deli Dumrul geçerli). Çizim: koyu ahşap gövde, demir köşebent, çapraz zincir, mor
## kafatası mührü; yaklaşınca W balonu ve lanet uyarısı.

const MOR := Color(0.72, 0.38, 1.0)
const AHSAP := Color(0.2, 0.13, 0.12)
const INK := Color(0.06, 0.04, 0.06)
const ETK_R := 40.0

var level: Node
var oda := -1
var acildi := false
var near := false
var altin := 14         # altın tanesi
var _t := 0.0
var _light: PointLight2D


func odalar() -> Array:
	return [oda]


func _ready() -> void:
	z_index = 2
	InkDraw.prep(self)
	if level:
		_light = level.add_light(Vector2(0, -18), MOR, 90.0, 0.5, self)


func _physics_process(delta: float) -> void:
	_t += delta
	var pl: Node = level.player if level else null
	near = false
	if pl != null and not acildi:
		near = absf(pl.global_position.x - global_position.x) < ETK_R and absf(pl.global_position.y - global_position.y) < 30.0
	if _light:
		_light.energy = 0.0 if acildi else 0.4 + 0.15 * sin(_t * 2.0) + (0.3 if near else 0.0)
	if Engine.get_process_frames() % 3 == 0:
		queue_redraw()


func ac() -> void:
	if acildi:
		return
	acildi = true
	var c := global_position + Vector2(0, -20)
	var tier := int(Game.run.get("tier", 0))
	level.drop_item(ItemGen.random_drop(tier + 2), c + Vector2(0, -12), false)
	for i in altin:
		level.drop_orb("gold", c)
	for i in 5:
		level.drop_orb("kut", c)
	FX.ring(c, 46, MOR, 0.5)
	FX.soul(c, MOR, 26)
	FX.flash_light(c, MOR, 240.0, 1.8, 0.45)
	Ses.play("kam_kahkaha", -4.0, 0.9)
	Ses.play("altin", -4.0)
	Game.shake(3.0)
	level.lanet_baslat()


func _draw() -> void:
	InkDraw.ellipse(self, Vector2(0, 1), 22.0, 4.0, Color(0, 0, 0, 0.4))
	if not acildi:
		InkDraw.soft(self, Vector2(0, -14), 22.0, Color(MOR, 0.1 + 0.06 * sin(_t * 2.0)), 5)
	# gövde
	var w := 34.0
	var h := 20.0
	draw_rect(Rect2(Vector2(-w * 0.5, -h), Vector2(w, h)), AHSAP)
	draw_rect(Rect2(Vector2(-w * 0.5, -h), Vector2(w, h)), INK, false, 1.8)
	# kapak: kapalıyken kemerli; açıkken arkaya devrik
	if acildi:
		draw_colored_polygon(PackedVector2Array([Vector2(-w * 0.5, -h), Vector2(w * 0.5, -h), Vector2(w * 0.5 + 4, -h - 14), Vector2(-w * 0.5 + 4, -h - 14)]), AHSAP.darkened(0.3))
		draw_polyline(PackedVector2Array([Vector2(-w * 0.5, -h), Vector2(-w * 0.5 + 4, -h - 14), Vector2(w * 0.5 + 4, -h - 14), Vector2(w * 0.5, -h)]), INK, 1.6, true)
		InkDraw.soft(self, Vector2(0, -h), 10.0, Color(MOR, 0.25), 2)
	else:
		var lid := PackedVector2Array()
		for i in 9:
			var a := PI + PI * i / 8.0
			lid.append(Vector2(cos(a) * w * 0.5, -h + sin(a) * 7.0))
		draw_colored_polygon(lid, AHSAP.lightened(0.05))
		draw_polyline(lid, INK, 1.6, true)
		# çapraz zincir
		InkDraw.stroke(self, Vector2(-w * 0.5, -h - 4), Vector2(w * 0.5, -2), 2.2, Color(0.3, 0.28, 0.3))
		InkDraw.stroke(self, Vector2(w * 0.5, -h - 4), Vector2(-w * 0.5, -2), 2.2, Color(0.3, 0.28, 0.3))
		# mor kafatası mührü
		var c := Vector2(0, -h * 0.5)
		draw_circle(c, 5.5, Color(MOR, 0.9), true, -1.0, true)
		draw_circle(c + Vector2(-2, -0.5), 1.2, INK, true, -1.0, true)
		draw_circle(c + Vector2(2, -0.5), 1.2, INK, true, -1.0, true)
		draw_line(c + Vector2(-1.5, 3), c + Vector2(1.5, 3), INK, 1.0, true)
	# demir köşebentler
	for sx in [-1.0, 1.0]:
		draw_line(Vector2(sx * (w * 0.5 - 4), -h), Vector2(sx * (w * 0.5 - 4), 0), Color(0.32, 0.3, 0.32), 2.0, true)
	if near and not acildi:
		# W balonu ve uyarı (Bezirgan / NPC balonu gibi)
		var y := -h - 30.0
		PixUI.key_cap(self, Vector2(-5, y - 22), HUD.KEY_ETKILES)
		var f := InkUI.font("body")
		var s := "Lanetli Sandık: aç  ·  %d öldürmeye dek hasar 2 kat" % Level.LANET_OLDUR
		var sw := InkHUD.str_w(f, s, 8)
		draw_rect(Rect2(Vector2(-sw * 0.5 - 4, y - 10), Vector2(sw + 8, 14)), Color(0.05, 0.03, 0.06, 0.75))
		InkUI.draw_str(self, Vector2(-sw * 0.5, y + 1), s, f, 8, Color(0.92, 0.8, 1.0), 1)


class Aura:
	## Lanetli oyuncunun çevresinde mor mürekkep halkası ve başının üstünde kalan öldürme sayısı
	extends Node2D
	var level: Node
	var _t := 0.0

	func _ready() -> void:
		z_index = 8
		InkDraw.prep(self)

	func _process(delta: float) -> void:
		_t += delta
		queue_redraw()

	func _draw() -> void:
		if level == null or int(level.lanet) <= 0:
			return
		var a := 0.35 + 0.15 * sin(_t * 5.0)
		InkDraw.ring(self, Vector2(0, -20), 20.0, 26.0, Color(MOR, a), _t)
		for i in 3:
			var ph := fmod(_t * 0.6 + i * 0.33, 1.0)
			InkDraw.soft(self, Vector2(sin(_t * 2.0 + i * 2.1) * 12.0, -6.0 - ph * 46.0), 2.6, Color(MOR, (1.0 - ph) * 0.6), i)
		var f := InkUI.font("caps")
		var s := "LANET %d" % int(level.lanet)
		var w := InkHUD.str_w(f, s, 8)
		InkUI.draw_str(self, Vector2(-w * 0.5, -58), s, f, 8, Color(0.85, 0.6, 1.0), 1)
