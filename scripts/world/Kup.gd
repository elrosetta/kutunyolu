class_name Kup
extends Node2D
## v34 küp (kırılan toprak testi): odalarda 1-3 tane; silah vuruşu (Level.break_cracks) ya da patlama kırar. İçinden
## 1-3 altın tanesi, bazen Kut tanesi, seyrek şifa düşer. Boş oda kalmasın diye (her odada "bir şey"), dövüşsüz
## odalarda daha çok. Çizim: mürekkep konturlu pişmiş toprak, ağız kenarı, iki kulp, tamga bezeği; kırılınca parçalar.

const TOPRAK := Color(0.46, 0.3, 0.2)
const TOPRAK_K := Color(0.27, 0.17, 0.12)
const INK := Color(0.07, 0.05, 0.05)

var level: Node
var oda := -1
var boy := 1.0            # 0,8-1,2 (küçük testi / büyük küp)
var kirildi := false
var _seed := 0
var _sars := 0.0


func odalar() -> Array:
	return [oda]


static func altin_ort() -> float:
	## Beklenen altın tanesi (ölçüm): 1-3 düzgün
	return 2.0


func _ready() -> void:
	z_index = 2
	InkDraw.prep(self)
	_seed = int(position.x * 0.37) % 11


func rect() -> Rect2:
	return Rect2(global_position + Vector2(-10.0 * boy, -26.0 * boy), Vector2(20.0 * boy, 26.0 * boy))


func vur(box: Rect2) -> bool:
	if kirildi or not box.intersects(rect()):
		return false
	kirildi = true
	var c := global_position + Vector2(0, -12.0 * boy)
	FX.burst(c, TOPRAK, 12, 150.0, 0.55, 0.3, 500.0)
	FX.dust(c, Vector2.UP, 6, 0.3)
	Ses.play("darbe_tas", -6.0, 1.45)
	for i in randi_range(1, 3):
		level.drop_orb("gold", c)
	if randf() < 0.3:
		level.drop_orb("kut", c)
	if randf() < 0.05:
		level.drop_orb("sifa", c)
	queue_free()
	return true


func _draw() -> void:
	var k := boy
	InkDraw.ellipse(self, Vector2(0, 1), 12.0 * k, 3.0, Color(0, 0, 0, 0.35))
	var pts := PackedVector2Array()
	for i in 17:
		var a := PI * 0.5 + TAU * i / 16.0
		var r := Vector2(9.5, 10.0) * k
		var p := Vector2(cos(a) * r.x, -11.0 * k - sin(a) * r.y)
		if p.y < -17.0 * k:
			p.x *= 0.62   # boyun daralır
		pts.append(p)
	draw_colored_polygon(pts, TOPRAK)
	# gölgeli yarı (sağ alt) ve ağız
	draw_colored_polygon(PackedVector2Array([Vector2(2, -2) * k, Vector2(9, -9) * k, Vector2(7, -17) * k, Vector2(3, -6) * k]), TOPRAK_K)
	draw_polyline(pts, INK, 1.6, true)
	draw_rect(Rect2(Vector2(-6.5, -24.0) * k, Vector2(13.0, 3.5) * k), TOPRAK_K)
	draw_rect(Rect2(Vector2(-6.5, -24.0) * k, Vector2(13.0, 3.5) * k), INK, false, 1.2)
	# kulplar ve tamga bezeği
	draw_arc(Vector2(-8.5, -16.0) * k, 3.0 * k, PI * 0.5, PI * 1.5, 6, INK, 1.4, true)
	draw_arc(Vector2(8.5, -16.0) * k, 3.0 * k, -PI * 0.5, PI * 0.5, 6, INK, 1.4, true)
	draw_line(Vector2(-6, -11) * k, Vector2(6, -11) * k, Color(INK, 0.7), 1.0, true)
	draw_line(Vector2(-2, -8) * k, Vector2(0, -13) * k, Color(INK, 0.7), 1.0, true)
	draw_line(Vector2(0, -13) * k, Vector2(2, -8) * k, Color(INK, 0.7), 1.0, true)
