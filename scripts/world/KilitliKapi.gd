class_name KilitliKapi
extends Node2D
## v34 kilitli kapı: yan kapılı bir ödül odasının koridoru demir kapıyla kapalı (4 karo katı: Level.set_solid). Bölümde
## bir ANAHTAR vardır (gizli cepte ya da başka bir ödül odasında; Anahtar.gd). Anahtarı taşıyan oyuncu kapıya yaklaşınca
## kilit açılır (karolar havaya döner: Level.set_air), anahtar harcanır. Anahtarsız yaklaşınca "Anahtar gerek" yazısı.
## Çizim: taş söve, dövme kapı kanadı, ortada altın kilit tamgası; açılınca kanat yukarı çekilir.

const ALTIN := Color(1.0, 0.82, 0.38)

var level: Node
var cell := Vector2i.ZERO   # kapı sütunu ve taban satırı (geçit y-4..y-1)
var oda := -1
var acik := false
var _t := 0.0
var _acilma := 0.0
var _uyari_t := 0.0


func odalar() -> Array:
	return [oda]


func _ready() -> void:
	z_index = 4
	InkDraw.prep(self)
	if level:
		for y in range(cell.y - 4, cell.y):
			level.set_solid(cell.x, y)
		level.add_light(Vector2(level.TS * 0.5, -level.TS * 2.2), ALTIN, 60.0, 0.4, self)


func _physics_process(delta: float) -> void:
	_t += delta
	_acilma = maxf(0.0, _acilma - delta)
	_uyari_t = maxf(0.0, _uyari_t - delta)
	if level == null or level.player == null or acik:
		if Engine.get_process_frames() % 3 == 0:
			queue_redraw()
		return
	var pl: Node = level.player
	var d: float = absf(pl.global_position.x - (global_position.x + level.TS * 0.5))
	if d < 46.0 and absf(pl.global_position.y - global_position.y) < 60.0:
		if int(level.anahtar) > 0:
			ac()
		elif _uyari_t <= 0.0:
			_uyari_t = 3.0
			FX.text(global_position + Vector2(level.TS * 0.5, -level.TS * 5.0), "Kilitli: bölümde bir anahtar var", ALTIN, 8)
	if Engine.get_process_frames() % 3 == 0:
		queue_redraw()


func ac() -> void:
	if acik:
		return
	acik = true
	_acilma = 0.8
	level.anahtar = int(level.anahtar) - 1
	for y in range(cell.y - 4, cell.y):
		level.set_air(cell.x, y)
	var c := global_position + Vector2(level.TS * 0.5, -level.TS * 2.0)
	FX.ring(c, 40, ALTIN, 0.45)
	FX.flash_light(c, ALTIN, 200.0, 1.4, 0.35)
	FX.text(c + Vector2(0, -40), "Kilit açıldı", ALTIN, 9)
	Ses.play("kapi", -2.0, 1.15)
	Game.shake(2.0)


func _draw() -> void:
	var TS: float = float(level.TS) if level else 24.0
	var top := -4.0 * TS
	var ink := Color(0.08, 0.06, 0.08)
	InkDraw.stroke(self, Vector2(-3, 0), Vector2(-3, top - 4), 4.0, ink)
	InkDraw.stroke(self, Vector2(TS + 3, 0), Vector2(TS + 3, top - 4), 4.0, ink)
	InkDraw.stroke(self, Vector2(-8, top - 4), Vector2(TS + 8, top - 4), 5.0, ink)
	var k := 1.0
	if acik:
		k = clampf(_acilma / 0.8, 0.0, 1.0)   # kanat yukarı çekilir
		if k <= 0.0:
			InkDraw.soft(self, Vector2(TS * 0.5, top - 10), 6.0, Color(ALTIN, 0.2), 1)
			return
	var bot := top + (0.0 - top) * k
	var kanat := Color(0.2, 0.15, 0.13)
	draw_rect(Rect2(Vector2(1, top), Vector2(TS - 2, bot - top)), Color(kanat, 0.96))
	for i in 3:
		var x := 4.0 + i * (TS - 8.0) / 2.0
		InkDraw.stroke(self, Vector2(x, bot), Vector2(x, top), 2.0, ink)
	InkDraw.stroke(self, Vector2(0, top + (bot - top) * 0.3), Vector2(TS, top + (bot - top) * 0.3), 2.2, ink)
	InkDraw.stroke(self, Vector2(0, top + (bot - top) * 0.75), Vector2(TS, top + (bot - top) * 0.75), 2.2, ink)
	if not acik:
		# altın kilit: halka + gövde + anahtar deliği
		var c := Vector2(TS * 0.5, top * 0.5)
		var nb := 0.75 + 0.25 * sin(_t * 3.0)
		InkDraw.soft(self, c, 9.0, Color(ALTIN, 0.18 * nb), 2)
		draw_arc(c + Vector2(0, -5), 4.0, PI, TAU, 10, ALTIN, 1.6, true)
		draw_rect(Rect2(c + Vector2(-5, -5), Vector2(10, 9)), ALTIN)
		draw_circle(c + Vector2(0, -1.5), 1.4, ink, true, -1.0, true)
		draw_line(c + Vector2(0, -1), c + Vector2(0, 2.5), ink, 1.2, true)
