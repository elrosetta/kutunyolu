class_name KutGate
extends Node2D
## Bölüm çıkışı: Ulu Kayın'ın kökünden yükselen, içinde kut ışığı dönen taş kemer.

var _t := 0.0
## stil v2: mürekkep kemer (sus_v2 "kut_kapi"), arkasında karanlık eşik, içinde ters dönen iki kut girdabı
var _ink := false
var _swirls: Array = []
var _front: Sprite2D


func _ready() -> void:
	z_index = -1
	if SusV2.on() and not SusV2.decor("kut_kapi").is_empty():
		_ink = true
		var back := SusV2.decor_sprite("kut_kapi_arka", false)
		if back:
			add_child(back)
		for i in 2:
			var sw := SusV2.decor_sprite("kut_kapi_girdap", false)
			if sw == null:
				break
			sw.material = SusV2.add_mat()
			sw.scale *= 1.0 if i == 0 else 0.72
			sw.self_modulate = Color(0.7, 1.4, 1.4, 0.85) if i == 0 else Color(1.0, 1.6, 1.5, 0.7)
			var holder := Node2D.new()
			holder.position = Vector2(0, -36)
			holder.scale = Vector2(0.86, 1.3)
			add_child(holder)
			holder.add_child(sw)
			_swirls.append(sw)
		_front = SusV2.decor_sprite("kut_kapi", true, Color(1.5, 1.6, 1.6))
		add_child(_front)


func _process(delta: float) -> void:
	_t += delta
	if _ink:
		for i in _swirls.size():
			var sw: Sprite2D = _swirls[i]
			sw.rotation = _t * (1.3 if i == 0 else -2.1)
			sw.self_modulate.a = (0.8 if i == 0 else 0.65) + 0.15 * sin(_t * 2.2 + i)
		var g: Sprite2D = _front.get_node_or_null("glow") as Sprite2D if _front else null
		if g:
			g.self_modulate.a = 0.75 + 0.25 * sin(_t * 2.0)
		return
	queue_redraw()


func _draw() -> void:
	if _ink:
		return
	var stone := Color(0.42, 0.44, 0.52)
	var dark := Color(0.22, 0.22, 0.3)
	draw_rect(Rect2(-30, -64, 10, 64), stone)
	draw_rect(Rect2(20, -64, 10, 64), stone)
	draw_rect(Rect2(-34, -72, 68, 10), stone)
	draw_rect(Rect2(-30, -64, 2, 64), dark)
	draw_rect(Rect2(28, -64, 2, 64), dark)
	for k in 5:
		var c := Color.from_hsv(0.48 + 0.02 * k, 0.6, 1.0, 0.18 + 0.05 * sin(_t * 2.0 + k))
		draw_rect(Rect2(-20 + k * 0.5, -62 + k, 40 - k, 62 - k), c)
	for k in 8:
		var a := _t * 1.5 + k * TAU / 8.0
		var p := Vector2(cos(a) * 12.0, -32.0 + sin(a) * 20.0)
		draw_circle(p, 1.6, Color(0.7, 1.0, 1.0, 0.9))
	var cloths := [Color(0.9, 0.2, 0.2), Color(0.95, 0.95, 0.95), Color(0.2, 0.5, 0.95), Color(0.95, 0.8, 0.2)]
	for k in 4:
		var x := -26 + k * 17
		draw_rect(Rect2(x, -62, 3, 8 + 2 * sin(_t * 3.0 + k)), cloths[k])
