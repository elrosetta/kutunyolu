class_name KutTasi
extends Node2D
## v32 Kut Taşı: ışınlanma dikilitaşı (mürekkep menhir; Göktürk tamgalı). Oyuncu yakınından geçince (BUL_R) keşfedilir:
## mürekkep parlaması, ruh taşı sesi, HUD iletisi; haritada seçilebilir olur (Level.isinlan). Taşın dibinde W (ETK_R)
## haritayı açar (hızlı ışınlanma). Çizim: koyu taş gövde, açık kenar ışığı, Kut rengi oyma tamga; keşfedilince
## oymalar nabız atar ve dipte ışık yanar.

const BUL_R := 84.0
const ETK_R := 34.0
const STONE := Color(0.13, 0.11, 0.14)
const STONE_HI := Color(0.3, 0.27, 0.32)
const KUT := Color(0.36, 0.86, 0.9)

var level: Node
var idx := -1
var ad := "Kut Taşı"
var bulundu := false
var near := false
var _t := 0.0
var _flash := 0.0
var _light: PointLight2D
var _seed := 0


func _ready() -> void:
	z_index = -1
	InkDraw.prep(self)
	_seed = idx * 17 + int(position.x) % 7
	if level:
		_light = level.add_light(Vector2(0, -22), KUT, 90.0, 0.0, self)


func _physics_process(delta: float) -> void:
	_t += delta
	_flash = maxf(0.0, _flash - delta * 2.0)
	var pl: Node = level.player if level else null
	if pl == null or not is_instance_valid(pl):
		return
	var d: float = pl.global_position.distance_to(global_position)
	near = d < ETK_R and absf(pl.global_position.y - global_position.y) < 30.0
	if not bulundu and d < BUL_R and not bool(pl.get("dead")):
		kesfet()
	if _light:
		var e := 0.0
		if bulundu:
			e = 0.55 + 0.2 * sin(_t * 2.3) + _flash * 1.5
		_light.energy = e
	if Engine.get_process_frames() % 2 == 0:
		queue_redraw()


func kesfet(sessiz := false) -> void:
	if bulundu:
		return
	bulundu = true
	_flash = 1.0
	if level and level.harita:
		level.harita.tasi_bul(idx)
	if sessiz:
		return
	FX.ring(global_position + Vector2(0, -22), 54, KUT, 0.5)
	FX.soul(global_position + Vector2(0, -24), KUT, 18)
	FX.flash_light(global_position + Vector2(0, -24), KUT, 240.0, 1.6, 0.4)
	FX.text(global_position + Vector2(0, -56), "Kut Taşı: " + ad, KUT, 9)
	Ses.play("ruh_tasi", -4.0)
	if level and level.has_signal("tasi_bulundu"):
		level.emit_signal("tasi_bulundu", idx)


func _draw() -> void:
	## Dikilitaş: 22 px geniş, 46 px yüksek; hafif eğik, pürüzlü kenar; dipte iki kaya; önde tamga oyması
	var k := 1.0 + _flash * 0.06
	var pts := PackedVector2Array([Vector2(-9, 0), Vector2(-11, -14), Vector2(-9, -30), Vector2(-5, -44), Vector2(2, -47), Vector2(8, -42), Vector2(10, -26), Vector2(11, -10), Vector2(9, 0)])
	for i in pts.size():
		pts[i] = pts[i] * k + Vector2(sin(i * 2.1 + _seed) * 0.6, 0)
	# gölge lekesi ve dip kayalar
	InkDraw.ellipse(self, Vector2(0, 1), 16.0, 4.0, Color(0, 0, 0, 0.35))
	InkDraw.blot(self, Vector2(-11, -2), 4.0, STONE, _seed + 1)
	InkDraw.blot(self, Vector2(12, -1), 3.2, STONE, _seed + 2)
	draw_colored_polygon(pts, STONE)
	# kenar ışığı (sol üst), fırça vuruşu
	InkDraw.stroke(self, Vector2(-8, -12) * k, Vector2(-3, -42) * k, 2.6, Color(STONE_HI, 0.9))
	InkDraw.stroke(self, Vector2(6, -40) * k, Vector2(9, -14) * k, 1.6, Color(0.05, 0.04, 0.06, 0.9))
	# tamga: Kut rengi (bulunmadıysa sönük taş rengi)
	var col := KUT if bulundu else Color(0.42, 0.4, 0.46)
	var a := (0.75 + 0.25 * sin(_t * 2.6)) if bulundu else 0.7
	var c := Color(col, a)
	draw_line(Vector2(0, -36) * k, Vector2(0, -16) * k, c, 1.6, true)
	draw_line(Vector2(-5, -30) * k, Vector2(0, -36) * k, c, 1.6, true)
	draw_line(Vector2(5, -30) * k, Vector2(0, -36) * k, c, 1.6, true)
	draw_line(Vector2(-4, -20) * k, Vector2(4, -20) * k, c, 1.4, true)
	draw_circle(Vector2(0, -12) * k, 1.8, c, true, -1.0, true)
	if bulundu:
		InkDraw.soft(self, Vector2(0, -26) * k, 14.0 + 3.0 * sin(_t * 2.6), Color(KUT, 0.16 + _flash * 0.4), _seed)
		# yükselen Kut zerreleri
		for i in 3:
			var ph := fmod(_t * 0.5 + i * 0.37, 1.0)
			var px := sin((_t + i) * 1.7) * 6.0
			InkDraw.soft(self, Vector2(px, -8 - ph * 50.0), 2.2, Color(KUT, (1.0 - ph) * 0.5), i)
	if near and bulundu:
		InkDraw.ring(self, Vector2(0, 0), 14.0, 5.0, Color(KUT, 0.35 + 0.2 * sin(_t * 6.0)))
