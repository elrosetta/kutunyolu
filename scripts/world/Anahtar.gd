class_name Anahtar
extends Node2D
## v34 anahtar: bölümdeki kilitli ödül odasının anahtarı (gizli cepte ya da başka bir ödül odasında). Havada süzülen
## mürekkep çizgili altın anahtar; oyuncu dokununca alınır (Level.anahtar += 1, HUD iletisi), kilitli kapıya
## yaklaşınca harcanır (KilitliKapi).

const ALTIN := Color(1.0, 0.82, 0.38)

var level: Node
var oda := -1
var alindi := false
var _t := 0.0


func odalar() -> Array:
	return [oda]


func _ready() -> void:
	z_index = 6
	InkDraw.prep(self)
	if level:
		level.add_light(Vector2(0, -16), ALTIN, 70.0, 0.6, self)


func _physics_process(delta: float) -> void:
	_t += delta
	if alindi or level == null or level.player == null:
		return
	if level.player.global_position.distance_to(global_position) < 30.0 and not bool(level.player.get("dead")):
		alindi = true
		level.anahtar = int(level.anahtar) + 1
		FX.ring(global_position + Vector2(0, -16), 30, ALTIN, 0.4)
		FX.text(global_position + Vector2(0, -44), "Anahtar alındı: kilitli kapıyı aç", ALTIN, 9)
		Ses.play("esya", -2.0, 1.2)
		queue_free()
		return
	queue_redraw()


func _draw() -> void:
	var y := -18.0 + 3.0 * sin(_t * 2.4)
	var c := Vector2(0, y)
	InkDraw.ellipse(self, Vector2(0, 1), 9.0, 2.5, Color(0, 0, 0, 0.3))
	InkDraw.soft(self, c, 11.0, Color(ALTIN, 0.2 + 0.08 * sin(_t * 3.0)), 4)
	var ink := Color(0.1, 0.07, 0.05)
	# halka (baş), sap, iki diş
	draw_arc(c + Vector2(-6, 0), 4.2, 0.0, TAU, 14, ink, 3.2, true)
	draw_arc(c + Vector2(-6, 0), 4.2, 0.0, TAU, 14, ALTIN, 1.8, true)
	draw_line(c + Vector2(-2, 0), c + Vector2(9, 0), ink, 3.4, true)
	draw_line(c + Vector2(-2, 0), c + Vector2(9, 0), ALTIN, 1.8, true)
	draw_line(c + Vector2(6, 0), c + Vector2(6, 4), ALTIN, 1.8, true)
	draw_line(c + Vector2(9, 0), c + Vector2(9, 3), ALTIN, 1.8, true)
