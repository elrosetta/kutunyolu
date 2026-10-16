class_name StreakFX
extends Node2D
## Hız çizgisi: başlangıçta kalın ve parlak, uca doğru incelir; önce ucu uzar, sonra kuyruğu toplanır.
## Stil v2 (ink): düz üçgen + 1 px çizgi yerine kuru fırça darbesi (InkDraw.stroke), baş ilerleyen uçta.

var a := Vector2.ZERO
var b := Vector2(40, 0)
var col := Color(1, 0.95, 0.8)
var life := 0.12
var _t := 0.0
var ink := FX.ink()


func _ready() -> void:
	z_index = 57
	top_level = true
	var m := CanvasItemMaterial.new()
	m.blend_mode = CanvasItemMaterial.BLEND_MODE_ADD
	m.light_mode = CanvasItemMaterial.LIGHT_MODE_UNSHADED
	material = m
	if ink:
		InkDraw.prep(self)


func _process(delta: float) -> void:
	_t += delta
	if _t >= life:
		queue_free()
		return
	queue_redraw()


func _draw() -> void:
	var k := _t / life
	var head := clampf(k * 2.2, 0.0, 1.0)
	var tail := clampf(k * 1.6 - 0.5, 0.0, 1.0)
	var p0 := a.lerp(b, tail)
	var p1 := a.lerp(b, head)
	var d := (p1 - p0)
	if d.length() < 1.0:
		return
	if ink:
		var ic := Color(col.r * 1.3, col.g * 1.25, col.b * 1.2, 1.0 - k)
		InkDraw.stroke(self, p1, p0, 5.0 * (1.0 - k * 0.6), ic)
		InkDraw.stroke(self, p1, p0.lerp(p1, 0.4), 2.0, Color(1.4, 1.4, 1.3, 1.0 - k))
		return
	var n := Vector2(-d.y, d.x).normalized()
	var w := 3.0 * (1.0 - k)
	var c := Color(col.r * 1.4, col.g * 1.35, col.b * 1.3, 1.0 - k)
	draw_colored_polygon(PackedVector2Array([p0 + n * w, p1, p0 - n * w]), c)
	draw_line(p0, p1, Color(1.5, 1.5, 1.4, (1.0 - k)), 1.0)
