class_name Ruzgar
extends Node2D
## v23 Yelbegen'in yel üfürüğü / Kaf fırtınası görünüşü: oyuncunun çevresinde rüzgâr yönünde akan mürekkep çizgileri
## (snow: kar taneleri). İtmeyi boss yapar (Boss._apply_gust); bu düğüm yalnızca okunurluk içindir.

var level: Node
var dir := 1.0
var life := 2.0
var snow := false
var _t := 0.0
var _lines: Array = []


func _ready() -> void:
	z_index = 26
	InkDraw.prep(self)
	for i in 26:
		_lines.append(Vector3(randf_range(-420.0, 420.0), randf_range(-150.0, 10.0), randf_range(0.6, 1.4)))


func _process(delta: float) -> void:
	_t += delta
	if _t >= life:
		queue_free()
		return
	for i in _lines.size():
		var l: Vector3 = _lines[i]
		l.x += dir * 520.0 * l.z * delta
		if l.x * dir > 440.0:
			l.x = -dir * 440.0
			l.y = randf_range(-150.0, 10.0)
		_lines[i] = l
	queue_redraw()


func _draw() -> void:
	var pl: Node = level.player if level else null
	if pl == null:
		return
	var base: Vector2 = to_local(pl.global_position)
	var a := clampf(_t / 0.2, 0.0, 1.0) * clampf((life - _t) / 0.3, 0.0, 1.0)
	for lv3 in _lines:
		var l: Vector3 = lv3
		var p := base + Vector2(l.x, l.y)
		var ln := 26.0 + 30.0 * l.z
		InkDraw.stroke(self, p, p - Vector2(dir * ln, 0.0), 2.0 * l.z, Color(0.85, 0.93, 1.0, 0.5 * a))
		if snow:
			InkDraw.flake(self, p + Vector2(0.0, sin(_t * 6.0 + l.x) * 6.0), 3.0 * l.z, _t * 4.0 + l.y, Color(1.0, 1.0, 1.0, 0.8 * a))
