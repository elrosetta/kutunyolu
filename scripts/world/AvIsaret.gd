class_name AvIsaret
extends Node2D
## v42 Avcı sınavı: tamgalı avın başının üstünde kızıl av tamgası (yay-ok; otag_v2 atlası "ui_tamga_avci"), hafif nabız.

var e: Node2D
var _t := 0.0


func _ready() -> void:
	z_index = 30
	InkDraw.prep(self)
	var sz: Vector2 = e.get("size") if e.get("size") != null else Vector2(20, 24)
	var bs: Vector2 = e.get("base_scale") if e.get("base_scale") != null else Vector2.ONE
	position = Vector2(0, -sz.y * bs.y - (32.0 if bool(e.get("elite")) else 16.0))


func _process(delta: float) -> void:
	_t += delta
	if Engine.get_process_frames() % 3 == 0:
		queue_redraw()


func _draw() -> void:
	if e == null or bool(e.get("dead")):
		return
	var p := 0.5 + 0.5 * sin(_t * 4.0)
	InkDraw.soft(self, Vector2.ZERO, 9.0, Color(1.0, 0.3, 0.2, 0.18 + 0.12 * p))
	Otag.ui_draw(self, "ui_tamga_avci", Vector2(0, -1.0 * p), 12.0, Color(1.0, 0.42, 0.34, 0.95))
