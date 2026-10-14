class_name WeaponTrail
extends Node2D
## Savuruş izi (tek efekt): her karede bıçağın kök ve uç noktası kaydedilir; aralarına yaşla solan bir
## şerit çizilir. Bıçak boyunca renkli gövde, uç kenarında beyaz parlak çekirdek (Dead Cells savuruş izi).
## Eski örnekler hem solar hem de uca doğru incelir: iz, kılıcın arkasında kuyruklu bir yay gibi okunur.

var col := Color(1, 0.95, 0.8)
var width_mul := 1.0
var life := 0.14
var done := false
var _pts: Array = []  # [kök, uç, zaman]
var _t := 0.0


func _ready() -> void:
	z_index = 56
	var m := CanvasItemMaterial.new()
	m.blend_mode = CanvasItemMaterial.BLEND_MODE_ADD
	m.light_mode = CanvasItemMaterial.LIGHT_MODE_UNSHADED
	material = m
	top_level = true


func add(base: Vector2, tip: Vector2) -> void:
	if _pts.size() > 0:
		var last: Array = _pts[_pts.size() - 1]
		if last[1].distance_to(tip) < 0.8:
			return
	_pts.append([base, tip, _t])


func _process(delta: float) -> void:
	_t += delta
	while _pts.size() > 0 and _t - float(_pts[0][2]) > life:
		_pts.pop_front()
	if _pts.is_empty() and done:
		queue_free()
		return
	queue_redraw()


func _draw() -> void:
	if _pts.size() < 2:
		return
	var n := _pts.size()
	var body := Color(col.r * 1.25, col.g * 1.2, col.b * 1.15, 1.0)
	var core := Color(1.5, 1.45, 1.35, 1.0)
	for i in range(n - 1):
		var a: Array = _pts[i]
		var b: Array = _pts[i + 1]
		var fa := 1.0 - clampf((_t - float(a[2])) / life, 0.0, 1.0)
		var fb := 1.0 - clampf((_t - float(b[2])) / life, 0.0, 1.0)
		# gövde: kökten uca, eskidikçe uca doğru daralır
		var wa := clampf(0.85 * width_mul * (0.35 + 0.65 * fa), 0.0, 1.0)
		var wb := clampf(0.85 * width_mul * (0.35 + 0.65 * fb), 0.0, 1.0)
		var ia: Vector2 = a[1] + (a[0] - a[1]) * wa
		var ib: Vector2 = b[1] + (b[0] - b[1]) * wb
		draw_primitive(PackedVector2Array([ia, a[1], b[1], ib]),
			PackedColorArray([Color(body, 0.0), Color(body, fa * fa * 0.75), Color(body, fb * fb * 0.75), Color(body, 0.0)]), PackedVector2Array())
		# çekirdek: uç kenarında ince beyaz bant
		var ca: Vector2 = a[1] + (a[0] - a[1]) * 0.16 * width_mul
		var cb: Vector2 = b[1] + (b[0] - b[1]) * 0.16 * width_mul
		draw_primitive(PackedVector2Array([ca, a[1], b[1], cb]),
			PackedColorArray([Color(core, 0.0), Color(core, fa * fa), Color(core, fb * fb), Color(core, 0.0)]), PackedVector2Array())
