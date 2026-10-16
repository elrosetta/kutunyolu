class_name StatusOverlay
extends Node2D
## Düşmanın üstünde durum görselleri: donmuşken buz bloğu (yarı saydam, parlak kenarlı, alt kenarda
## buz sarkıtları) ve başın üstünde küçük durum simgeleri (alev, kar tanesi, zehir damlası, kan damlası).

var host: Node2D
var _t := 0.0


func _ready() -> void:
	z_index = 30
	var m := CanvasItemMaterial.new()
	m.light_mode = CanvasItemMaterial.LIGHT_MODE_UNSHADED
	material = m


func _process(delta: float) -> void:
	_t += delta
	queue_redraw()


func _draw() -> void:
	if host == null or not is_instance_valid(host):
		return
	var sz: Vector2 = host.size
	# --- buz bloğu
	if host.freeze_t > 0.0:
		var r := Rect2(-sz.x / 2.0 - 3.0, -sz.y - 4.0, sz.x + 6.0, sz.y + 5.0)
		var a := clampf(host.freeze_t * 2.0, 0.0, 1.0)
		draw_rect(r, Color(0.55, 0.85, 1.0, 0.32 * a))
		draw_rect(r, Color(0.85, 0.97, 1.0, 0.85 * a), false, 1.0)
		# parıltı çizgileri
		for i in 2:
			var x0 := r.position.x + 3.0 + i * 5.0
			draw_line(Vector2(x0, r.position.y + 3), Vector2(x0 + 6, r.position.y + 9), Color(1, 1, 1, 0.7 * a), 1.0)
		# sarkıtlar
		var n := int(r.size.x / 5.0)
		for i in n:
			var x := r.position.x + 2.0 + i * 5.0
			var hgt := 2.0 + float((i * 7) % 4)
			draw_colored_polygon(PackedVector2Array([Vector2(x, r.end.y), Vector2(x + 3, r.end.y), Vector2(x + 1.5, r.end.y + hgt)]), Color(0.75, 0.93, 1.0, 0.8 * a))
	# --- simgeler
	var icons: Array = []
	if host.burn_t > 0.0:
		icons.append("ates")
	if host.freeze_t > 0.0:
		icons.append("buz")
	if host.poison > 0:
		icons.append("zehir")
	if host.bleed > 0:
		icons.append("kan")
	var y := -sz.y - 14.0 + sin(_t * 4.0) * 1.0
	var x0 := -float(icons.size() - 1) * 4.5
	for i in icons.size():
		_icon(icons[i], Vector2(x0 + i * 9.0, y))
	# v19 Kut Alma: infaz edilebilir yaratığın başında nabız gibi atan kızıl mühür (halka + çapraz kesik)
	if host.has_method("exec_ok") and host.exec_ok():
		_exec_mark(Vector2(0.0, -sz.y * host.base_scale.y - (24.0 if icons.size() > 0 else 14.0)))


func _exec_mark(p: Vector2) -> void:
	## Hedef mührü: ortada kızıl elmas (aşağıyı, yaratığı gösterir), çevresinde içe doğru atan dört mürekkep köşeli
	## ayraç — "yasak" işaretine benzemesin diye halka / çapraz çizgi yok
	var pulse := 0.5 + 0.5 * sin(_t * 12.0)
	var ink := Color(0.1, 0.02, 0.03, 0.92)
	var red := Color(1.0, 0.2 + 0.25 * pulse, 0.14, 1.0)
	var d := 3.6 + 0.8 * pulse
	var dia := PackedVector2Array([p + Vector2(0, -d), p + Vector2(d * 0.8, 0), p + Vector2(0, d * 1.5), p + Vector2(-d * 0.8, 0)])
	var dia_o := PackedVector2Array([p + Vector2(0, -d - 1.6), p + Vector2(d * 0.8 + 1.4, 0), p + Vector2(0, d * 1.5 + 2.0), p + Vector2(-d * 0.8 - 1.4, 0)])
	draw_colored_polygon(dia_o, ink)
	draw_colored_polygon(dia, red)
	draw_line(p + Vector2(-0.6, -d * 0.5), p + Vector2(-0.6, d * 0.6), Color(1.0, 0.9, 0.75, 0.9), 1.0, true)
	var r := 9.5 - 2.0 * pulse
	for k in 4:
		var a := PI * 0.25 + k * PI * 0.5
		var c := p + Vector2(cos(a), sin(a)) * r
		var t1 := Vector2(cos(a + PI * 0.75), sin(a + PI * 0.75)) * 3.2
		var t2 := Vector2(cos(a - PI * 0.75), sin(a - PI * 0.75)) * 3.2
		draw_polyline(PackedVector2Array([c + t1, c, c + t2]), ink, 2.6, true)
		draw_polyline(PackedVector2Array([c + t1 * 0.85, c, c + t2 * 0.85]), red, 1.3, true)


func _icon(kind: String, p: Vector2) -> void:
	match kind:
		"ates":
			var fl := sin(_t * 18.0) * 0.6
			draw_colored_polygon(PackedVector2Array([p + Vector2(-3, 3), p + Vector2(3, 3), p + Vector2(fl, -4)]), Color(1.0, 0.55, 0.15))
			draw_colored_polygon(PackedVector2Array([p + Vector2(-1.5, 3), p + Vector2(1.5, 3), p + Vector2(fl * 0.5, -1)]), Color(1.0, 0.95, 0.5))
		"buz":
			for k in 3:
				var a := k * PI / 3.0
				var d := Vector2(cos(a), sin(a)) * 3.5
				draw_line(p - d, p + d, Color(0.75, 0.95, 1.0), 1.0)
			draw_circle(p, 1.0, Color(1, 1, 1))
		"zehir":
			draw_circle(p + Vector2(0, 1), 2.6, Color(0.45, 0.9, 0.25))
			draw_colored_polygon(PackedVector2Array([p + Vector2(-2, 0), p + Vector2(2, 0), p + Vector2(0, -4)]), Color(0.45, 0.9, 0.25))
			draw_circle(p + Vector2(-0.8, 0.4), 0.8, Color(0.85, 1.0, 0.7))
		"kan":
			draw_circle(p + Vector2(0, 1), 2.3, Color(0.85, 0.12, 0.15))
			draw_colored_polygon(PackedVector2Array([p + Vector2(-1.8, 0.4), p + Vector2(1.8, 0.4), p + Vector2(0, -3.5)]), Color(0.85, 0.12, 0.15))
