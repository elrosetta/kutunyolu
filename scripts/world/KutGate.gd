class_name KutGate
extends Node2D
## Bölüm çıkışı: Ulu Kayın'ın kökünden yükselen, içinde kut ışığı dönen taş kemer.

var _t := 0.0
## mürekkep kemer (sus_v2 "kut_kapi"), arkasında karanlık eşik, içinde ters dönen iki kut girdabı
var _swirls: Array = []
var _front: Sprite2D
## v2: false ise yalnızca eşik ve girdap (yurtta taç kapı kemeri zaten çerçeve); portal_scale girdap boyu
var frame := true
var portal_scale := 1.0


func _ready() -> void:
	z_index = -1
	if SusV2.on() and not SusV2.decor("kut_kapi").is_empty():
		var back := SusV2.decor_sprite("kut_kapi_arka", false)
		if back:
			back.scale *= portal_scale
			add_child(back)
		for i in 2:
			var sw := SusV2.decor_sprite("kut_kapi_girdap", false)
			if sw == null:
				break
			sw.material = SusV2.add_mat()
			sw.scale *= 1.0 if i == 0 else 0.72
			sw.self_modulate = Color(0.7, 1.4, 1.4, 0.85) if i == 0 else Color(1.0, 1.6, 1.5, 0.7)
			var holder := Node2D.new()
			holder.position = Vector2(0, -36 * portal_scale)
			holder.scale = Vector2(0.86, 1.3) * portal_scale
			add_child(holder)
			holder.add_child(sw)
			_swirls.append(sw)
		if frame:
			_front = SusV2.decor_sprite("kut_kapi", true, Color(1.5, 1.6, 1.6))
			add_child(_front)


func _process(delta: float) -> void:
	_t += delta
	for i in _swirls.size():
		var sw: Sprite2D = _swirls[i]
		sw.rotation = _t * (1.3 if i == 0 else -2.1)
		sw.self_modulate.a = (0.8 if i == 0 else 0.65) + 0.15 * sin(_t * 2.2 + i)
	var g: Sprite2D = _front.get_node_or_null("glow") as Sprite2D if _front else null
	if g:
		g.self_modulate.a = 0.75 + 0.25 * sin(_t * 2.0)
