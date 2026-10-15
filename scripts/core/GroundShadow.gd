class_name GroundShadow
extends Node2D
## Temas (leke) gölgesi: her kare sahibinin altındaki zemini bulur ve ayakların altına keskin,
## iki tonlu piksel elips çizer (çekirdek + 1 px daha açık kenar). Yükseldikçe küçülür ve solar
## (FADE_H'de yok olur), ay ışığının gölge yönüne hafifçe kayar. Sahibinin İLK çocuğu olarak
## eklenir: sahiple aynı z'de ama sprite'tan önce çizilir; karolar (z 0) ve kan lekeleri (z 1)
## ile sprite arasında kalır. Sahip ölüyse ya da izlediği SpriteAnim görünmezse çizilmez.
## Işıktan etkilenmez (unshaded); yalnızca boyut/alfa değişince yeniden çizilir (konum değişimi
## ucuz bir dönüşüm güncellemesidir).

const INK := Color(0.03, 0.02, 0.06)
const CORE_A := 0.36  # kenar elipsinin üstüne biner: toplam ≈ 0.55
const EDGE_A := 0.30
const FADE_H := 140.0  # bu yükseklikte gölge tamamen söner
const SCAN_H := 160.0  # zemin bu kadar aşağıya kadar aranır (uçan düşmanlar: uzaktaki zemin, solgun)

static var _mat: CanvasItemMaterial

var host: Node2D         # gölgenin sahibi; ayak noktası = host.global_position
var anim: CanvasItem     # görünürlük ve alfa bu düğümden alınır (SpriteAnim); boşsa host
var width := 20.0        # yerdeki tam genişlik (dünya pikseli)
var scale_from: Node2D   # genişlik bu düğümün scale.x'iyle çarpılır (seçkin 1.3x, ezilme/esneme)
var level: Node
var _shade := 0.0  # ay gölgesi (0..1), yumuşak geçişli
var _shade_t := 0  # ışın testi her 3 karede bir
var _shade_hit := false
var _rx := 0
var _ry := 0
var _a := 0.0


static func attach(h: Node2D, w: float, a: CanvasItem = null, sf: Node2D = null) -> GroundShadow:
	## Sahibin ilk çocuğu olarak ekler (sprite'ın altında çizilsin).
	var s := GroundShadow.new()
	s.host = h
	s.width = w
	s.anim = a
	s.scale_from = sf
	h.add_child(s)
	h.move_child(s, 0)
	return s


func _ready() -> void:
	if _mat == null:
		_mat = CanvasItemMaterial.new()
		_mat.light_mode = CanvasItemMaterial.LIGHT_MODE_UNSHADED
	material = _mat


func _level() -> Node:
	if level != null and is_instance_valid(level):
		return level
	var lv = host.get("level")
	if lv == null:
		var pl = host.get("pl")  # DonForm: oyuncu üzerinden
		if pl != null:
			lv = pl.get("level")
	if lv == null:
		lv = FX.level
	if lv != null and not lv.has_method("ground_at"):
		lv = null
	level = lv
	return level


func _ground_y(lv: Node, feet: Vector2) -> float:
	## Ayakların altındaki ilk zemin/platform karosunun üst kenarı (piksel); yoksa -1
	var ts := float(Level.TS)
	var y := feet.y - 1.0
	var endy := feet.y + SCAN_H
	while y < endy:
		if lv.ground_at(Vector2(feet.x, y)):
			return floorf(y / ts) * ts
		y += 4.0
	return -1.0


func _process(_delta: float) -> void:
	if host == null or not is_instance_valid(host):
		return
	var lv := _level()
	var src: CanvasItem = anim if (anim != null and is_instance_valid(anim)) else host
	var ok: bool = lv != null and src.is_visible_in_tree() and host.get("dead") != true
	if not ok:
		if visible:
			hide()
		return
	var feet := host.global_position
	_update_moon_shade(lv, feet, _delta)
	var gy := _ground_y(lv, feet)
	var h := gy - feet.y
	var k := clampf(1.0 - maxf(0.0, h) / FADE_H, 0.0, 1.0)
	var alpha := k * src.modulate.a
	if gy < 0.0 or alpha <= 0.02:
		if visible:
			hide()
		return
	var w := width * (absf(scale_from.scale.x) if scale_from != null else 1.0)
	var rx := maxi(2, int(round(w * 0.5 * (0.4 + 0.6 * k))))
	var ry := clampi(int(round(float(rx) * 0.25)), 1, 6)
	# ay ışığının gölge yönü: yükseldikçe biraz daha kayar
	var ox := 0.0
	var moon = lv.get("moon")
	if moon != null:
		ox = -sin(moon.rotation) * (1.5 + maxf(0.0, h) * 0.12)
	global_position = Vector2(roundf(feet.x + ox), gy)
	if host.rotation != 0.0:
		global_rotation = 0.0
	if not visible:
		show()
	if rx != _rx or ry != _ry or absf(alpha - _a) > 0.03:
		_rx = rx
		_ry = ry
		_a = alpha
		queue_redraw()


func _update_moon_shade(lv: Node, feet: Vector2, delta: float) -> void:
	## Gövde ortasından aya ışın: çıkıntı/mağara altındaysa toon_light'ın ay payı kısılır (0,2 sn geçiş).
	## Sahibin set_moon_shade'i varsa (oyuncu: kol + silah) o çağrılır, yoksa SpriteAnim malzemesi.
	if not lv.has_method("moon_occluded"):
		return
	_shade_t -= 1
	if _shade_t <= 0:
		_shade_t = 3
		_shade_hit = lv.moon_occluded(feet + Vector2(0, -14))
	# aktörler gölgede bile okunur kalsın: ay payının en çok %55'i kesilir
	var target: float = float(lv.get("moon_shadow")) * 0.55 if _shade_hit else 0.0
	var ns := move_toward(_shade, target, delta * 5.0)
	if absf(ns - _shade) < 0.0001 and _shade_t != 3:
		return
	_shade = ns
	if host.has_method("set_moon_shade"):
		host.set_moon_shade(_shade)
	elif anim != null and is_instance_valid(anim) and anim.get("mat") is ShaderMaterial:
		(anim.get("mat") as ShaderMaterial).set_shader_parameter("moon_shade", _shade)


func _draw() -> void:
	# Elips zemin çizgisinin ÜSTÜNE oturur (alt satırı çizgide): karo üst kenarının koyu pikselleriyle
	# karışmaz, ayakların dibinde yassı bir leke olarak okunur.
	var cy := -_ry + 1
	_ellipse(_rx + 1, _ry + 1, cy, Color(INK, EDGE_A * _a))
	_ellipse(_rx, _ry, cy, Color(INK, CORE_A * _a))


func _ellipse(rx: int, ry: int, cy: int, c: Color) -> void:
	## Piksel ızgarasına oturan elips: her satır tam sayı genişlikte tek bir dikdörtgen
	for j in range(-ry, ry):
		var t := (float(j) + 0.5) / float(ry)
		var hw := int(round(float(rx) * sqrt(maxf(0.0, 1.0 - t * t))))
		if hw > 0:
			draw_rect(Rect2(-hw, cy + j, hw * 2, 1), c)
