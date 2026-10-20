class_name Parmaklik
extends Node2D
## v34 parmaklıklı pencere (Dead Cells'in "görünen ama ulaşılmayan" ödülü): ana yol odasıyla ödül odası arasındaki kısa
## koridorun ortasında 1 sütun x 4 karoluk demir parmaklık. Izgarada katıdır (geçilmez; LevelGen erişim modeli duvar
## sayar); kaya karosu silinir, yerine dövme demir çubuklar çizilir ve aynı yere dünya katmanında çarpışma kutusu konur.
## Arkasındaki ödül (tomar / hazine) ve ışığı görünür: oyuncu dolaşarak odanın gerçek kapısını arar.

const DEMIR := Color(0.16, 0.14, 0.15)
const PAS := Color(0.42, 0.26, 0.16)

var level: Node
var cells: Array = []     # parmaklık karoları (x sabit)
var oda_a := -1           # yol odası
var oda_b := -1           # ödül odası
var _t := 0.0


func odalar() -> Array:
	return [oda_a, oda_b]


func _ready() -> void:
	z_index = 3
	InkDraw.prep(self)
	if level == null or cells.is_empty():
		return
	var TS := float(level.TS)
	var r := _rect()
	for c in cells:
		level.ground.erase_cell(c)
		level.overlay.erase_cell(c)
	# çarpışma: dünya katmanı (oyuncu / yaratık geçemez); mermiler için de duvar
	var body := StaticBody2D.new()
	body.collision_layer = Game.LAYER_WORLD
	body.collision_mask = 0
	var cs := CollisionShape2D.new()
	var sh := RectangleShape2D.new()
	sh.size = r.size
	cs.shape = sh
	cs.position = r.get_center() - global_position
	body.add_child(cs)
	add_child(body)
	# arkadaki ödülün ışığı parmaklığın iki yanına sızsın
	level.add_light(Vector2(TS * 0.5, -TS * 2.0), Color(1.0, 0.82, 0.5), 110.0, 0.35, self)


func _rect() -> Rect2:
	var TS := float(level.TS)
	var y0 := 99999
	var y1 := -1
	for c in cells:
		y0 = mini(y0, c.y)
		y1 = maxi(y1, c.y)
	return Rect2(float((cells[0] as Vector2i).x) * TS, y0 * TS, TS, (y1 - y0 + 1) * TS)


func _physics_process(delta: float) -> void:
	_t += delta
	if Engine.get_process_frames() % 6 == 0:
		queue_redraw()


func _draw() -> void:
	if level == null or cells.is_empty():
		return
	var TS := float(level.TS)
	var h := cells.size() * TS
	# üst ve alt kiriş (taş söve), dört dövme çubuk, ortada yatay bağ; uçlar sivri
	InkDraw.stroke(self, Vector2(-4, -h - 1), Vector2(TS + 4, -h - 1), 5.0, Color(0.08, 0.06, 0.08))
	InkDraw.stroke(self, Vector2(-3, 0), Vector2(TS + 3, 0), 4.0, Color(0.08, 0.06, 0.08))
	for i in 4:
		var x := 3.0 + i * (TS - 6.0) / 3.0
		InkDraw.stroke(self, Vector2(x, 1), Vector2(x, -h - 2), 3.0, DEMIR)
		draw_line(Vector2(x - 0.6, -h + 2), Vector2(x - 0.6, -3), Color(PAS, 0.35), 0.8, true)
	InkDraw.stroke(self, Vector2(-1, -h * 0.55), Vector2(TS + 1, -h * 0.55), 2.4, DEMIR)
	InkDraw.stroke(self, Vector2(-1, -h * 0.2), Vector2(TS + 1, -h * 0.2), 1.8, DEMIR)
	# arkadaki ödülün sıcak ışıltısı (parmaklık aralarından)
	var a := 0.12 + 0.05 * sin(_t * 2.0)
	InkDraw.soft(self, Vector2(TS * 0.5, -h * 0.45), TS * 0.9, Color(1.0, 0.8, 0.45, a), 3)
