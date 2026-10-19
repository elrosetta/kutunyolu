class_name StatusOverlay
extends Node2D
## Düşmanın üstünde durum görselleri: donmuşken buz bloğu (yarı saydam, parlak kenarlı, alt kenarda
## buz sarkıtları) ve başın üstünde küçük durum simgeleri (alev, kar tanesi, zehir damlası, kan damlası).

## Stil v2 (ink): buz bloğu ayaz yıkaması + fırça kenar + damla sarkıtlar; simgeler fırça alev, mürekkep yıldız,
## zehir / kan damlası (InkDraw).

var host: Node2D
var _t := 0.0


func _ready() -> void:
	z_index = 30
	var m := CanvasItemMaterial.new()
	m.light_mode = CanvasItemMaterial.LIGHT_MODE_UNSHADED
	material = m
	InkDraw.prep(self)


func _process(delta: float) -> void:
	_t += delta
	queue_redraw()


func _draw() -> void:
	if host == null or not is_instance_valid(host):
		return
	var sz: Vector2 = host.size
	# --- buz bloğu
	if host.freeze_t > 0.0:
		_ink_ice(sz)
	elif host.freeze_t > 0.0:
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
	# --- simgeler (v22: can çubuğu görünürken simgeleri çubuğun yanında EnemyBar çizer)
	var bar_on: bool = "bar" in host and host.bar != null and is_instance_valid(host.bar) and host.bar.shown()
	if bar_on:
		if host.has_method("exec_ok") and host.exec_ok():
			_exec_mark(Vector2(0.0, -sz.y * host.base_scale.y - 24.0))
		return
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


func _ink_ice(sz: Vector2) -> void:
	## Buz: dikdörtgen kutu yerine gövdeyi saran düzensiz ayaz yıkaması, kenarlarda kırık kristal fırça darbeleri,
	## altta damla sarkıtlar (sabit tohumlu: kare kare titremez)
	var r := Rect2(-sz.x / 2.0 - 3.0, -sz.y - 4.0, sz.x + 6.0, sz.y + 5.0)
	var a := clampf(host.freeze_t * 2.0, 0.0, 1.0)
	var cc := r.get_center()
	InkDraw.quad(self, "duman_1", cc, r.size * 1.5, 0.3, Color(0.55, 0.85, 1.0, 0.42 * a))
	InkDraw.quad(self, "leke_2", cc + Vector2(0, 1), r.size * 1.2, 0.0, Color(0.6, 0.88, 1.0, 0.22 * a))
	var ec := Color(0.88, 0.98, 1.0, 0.9 * a)
	var n := 7
	for i in n:
		# kristal kırıkları: çevre boyunca dışa bakan kısa sivri darbeler
		var ang := TAU * float(i) / float(n) + 0.4
		var d := Vector2(cos(ang), sin(ang))
		var p0 := cc + Vector2(d.x * r.size.x * 0.46, d.y * r.size.y * 0.46)
		var l := 3.0 + float((i * 5) % 4)
		InkDraw.stroke(self, p0 - d * l * 0.4, p0 + d.rotated(0.35 * (1 if i % 2 == 0 else -1)) * l, 2.0, ec)
	InkDraw.stroke(self, r.position + Vector2(4, 4), r.position + Vector2(10, 11), 2.2, Color(1, 1, 1, 0.75 * a))
	var m := int(r.size.x / 6.0)
	for i in m:
		var x := r.position.x + 4.0 + i * 6.0
		var hgt := 2.0 + float((i * 7) % 4)
		InkDraw.drop(self, Vector2(x, r.end.y + hgt * 0.3), 1.2 + hgt * 0.35, PI * 0.5, Color(0.75, 0.93, 1.0, 0.8 * a))


func _icon(kind: String, p: Vector2) -> void:
	match kind:
		"ates":
			InkDraw.flame(self, p + Vector2(0, 3.5), 5.0, 8.5, Color(1.0, 0.55, 0.15), sin(_t * 18.0) * 0.3)
			InkDraw.flame(self, p + Vector2(0, 3.5), 2.6, 4.5, Color(1.0, 0.95, 0.5))
		"buz":
			InkDraw.star(self, p, 4.2, 0.0, Color(0.75, 0.95, 1.0))
			InkDraw.star(self, p, 3.0, PI * 0.25, Color(0.85, 1.0, 1.0, 0.8))
		"zehir":
			InkDraw.drop(self, p + Vector2(0, 0.5), 3.0, PI * 0.5, Color(0.45, 0.9, 0.25))
		"kan":
			InkDraw.drop(self, p + Vector2(0, 0.5), 2.8, PI * 0.5, Color(0.85, 0.12, 0.15))
