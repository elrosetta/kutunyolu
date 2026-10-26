class_name MuhurTamga
extends Node2D
## v44 Mühür yolu: Beşinci Mühürde Erlik'i yenen Bengü'nün süsü "Tan tamgası" — sırtında nefes alan altın güneş tamgası
## (katmanlı ışık halesi + dönen ince ışınlar + Kayı tamgası), altın örgü halkası ve şolpılar (MuhurYolu.sus_uygula).
## Oyuncunun çocuğu, gövdenin arkasında (z -1); oyuncu döndükçe aynalanmaz (tamga simetrik).

var _t := 0.0
var _isik: PointLight2D


func _ready() -> void:
	z_index = -1
	z_as_relative = true
	var m := CanvasItemMaterial.new()
	m.blend_mode = CanvasItemMaterial.BLEND_MODE_ADD
	m.light_mode = CanvasItemMaterial.LIGHT_MODE_UNSHADED
	material = m
	var lv: Node = get_parent().get("level") if get_parent() else null
	if lv != null and lv.has_method("add_light"):
		_isik = lv.add_light(Vector2(0, -30), Color(1.0, 0.72, 0.32), 70.0, 0.35, self)


func _process(delta: float) -> void:
	_t += delta
	var pl: Node = get_parent()
	visible = pl != null and not bool(pl.get("dead"))
	queue_redraw()


func _draw() -> void:
	var c := Vector2(0, -30)
	var nefes := 0.5 + 0.5 * sin(_t * 1.8)
	var gold := Color(1.0, 0.72, 0.3)
	draw_circle(c, 15.0 + 2.0 * nefes, Color(gold, 0.08 + 0.05 * nefes))
	draw_circle(c, 9.0, Color(gold, 0.1 + 0.06 * nefes))
	for i in 12:
		var a := _t * 0.25 + TAU * float(i) / 12.0
		var r0 := 10.0
		var r1 := 17.0 + 3.0 * sin(_t * 2.0 + i)
		draw_line(c + Vector2.from_angle(a) * r0, c + Vector2.from_angle(a) * r1, Color(gold, 0.18 + 0.1 * nefes), 1.2, true)
	draw_arc(c, 7.5, 0, TAU, 20, Color(1.0, 0.85, 0.5, 0.35 + 0.2 * nefes), 1.2, true)
	InkUI.tamga(self, 0, c, 11.0, Color(1.0, 0.8, 0.4, 0.45 + 0.25 * nefes))
