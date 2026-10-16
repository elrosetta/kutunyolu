class_name ParallaxBG
extends CanvasLayer
## Paralaks arka plan: gökyüzü sabit, dağlar / uzak orman / orta orman / yakın gövdeler
## kameradan farklı hızlarda kayar ve yatayda dikişsiz döşenir. En önde zamanla süzülen
## sis bandı, ağaçların arasında soğuk ay hüzmeleri vardır.

## [doku, yatay çarpan, dikey çarpan, zamanla kayma (px/sn)]
const LAYERS := [
	["res://assets/bg/otuken_0_sky.png", 0.0, 0.0, 0.0],
	["res://assets/bg/otuken_1_mountains.png", 0.05, 0.03, 0.0],
	["res://assets/bg/otuken_2_far.png", 0.16, 0.08, 0.0],
	["res://assets/bg/otuken_3_mid.png", 0.38, 0.16, 0.0],
	["res://assets/bg/otuken_4_near.png", 0.62, 0.28, 0.0],
	["res://assets/bg/otuken_5_fog.png", 0.5, 0.22, 9.0],
]

var level: Node
var layers: Array = LAYERS
## Stil v2 (mürekkep): dokular doğrusal süzgeç + mipmap ile çizilir (v1 keskin piksel kalır). Katman türü
## (spec[4]): "" normal, "add" toplamalı ışık hüzmesi (yavaş nefes alır), "fog" sürüklenen yer sisi (nefes alır).
var smooth := false
var ray_color := Color(0.62, 0.8, 1.0, 0.07)
var _layers: Array = []
var _rays: Array = []
var _base_y := 0.0
## yatay kaydırma birikimi: ekran pikseli cinsinden kamera yolu (yakınlık x dünya yolu). Yakınlık değişirse (boss
## sığdırma, CameraV2.fit) katman sıçramaz, yalnızca o andan sonraki kayma hızı değişir. Sabit yakınlıkta c.x x z'ye eşit.
var _scroll := 0.0
var _last_cx := INF


var _vh := 540.0


func _ready() -> void:
	layer = -10
	_vh = float(ProjectSettings.get_setting("display/window/size/viewport_height", 540))
	for i in layers.size():
		var spec: Array = layers[i]
		var tex: Texture2D = Data.tex(spec[0])
		var holder := Node2D.new()
		add_child(holder)
		var copies: Array = []
		var n := 1 if spec[1] == 0.0 else 3
		# katmanlar görüntü yüksekliğine (540) oturacak şekilde ölçeklenir; 540 px üretilen katmanlar 1:1 çizilir
		var k_px := _vh / float(tex.get_height())
		var kind: String = String(spec[4]) if spec.size() > 4 else ""
		var mat: CanvasItemMaterial = null
		if kind == "add":
			mat = CanvasItemMaterial.new()
			mat.blend_mode = CanvasItemMaterial.BLEND_MODE_ADD
		for k in n:
			var s := Sprite2D.new()
			s.texture = tex
			s.centered = false
			s.scale = Vector2(k_px, k_px)
			if smooth:
				s.texture_filter = CanvasItem.TEXTURE_FILTER_LINEAR_WITH_MIPMAPS
			if mat:
				s.material = mat
			holder.add_child(s)
			copies.append(s)
		_layers.append({"holder": holder, "copies": copies, "w": float(tex.get_width()) * k_px, "k": k_px, "fx": spec[1], "fy": spec[2], "drift": spec[3], "kind": kind, "ph": randf() * TAU})
		if i == layers.size() - 3 and ray_color.a > 0.0:
			_add_rays()


func _add_rays() -> void:
	var tex: Texture2D = load("res://assets/fx/god_ray.png")
	for k in 4:
		var r := Sprite2D.new()
		r.texture = tex
		r.centered = false
		r.rotation_degrees = 28.0
		r.scale = Vector2(randf_range(1.2, 2.2), 1.9)
		r.modulate = ray_color
		var m := CanvasItemMaterial.new()
		m.blend_mode = CanvasItemMaterial.BLEND_MODE_ADD
		r.material = m
		add_child(r)
		_rays.append({"s": r, "x": 120.0 + k * 170.0 + randf_range(-30, 30), "ph": randf() * TAU})


func _process(_delta: float) -> void:
	var cam: Camera2D = Game.camera
	if cam == null:
		return
	var c := cam.get_screen_center_position()
	if _base_y == 0.0:
		_base_y = c.y
	var vp := get_viewport().get_visible_rect().size
	var t := Time.get_ticks_msec() / 1000.0
	# kamera yakınlığı (stil v2): oyun alanı ekranda z kat hızlı kayar, katmanlar da aynı oranda (derinlik hissi korunur)
	var z: float = Game.base_zoom * float(cam.get("fit") if cam.get("fit") != null else 1.0)
	if _last_cx == INF:
		_scroll = c.x * z
	else:
		_scroll += (c.x - _last_cx) * z
	_last_cx = c.x
	for L in _layers:
		var fx: float = L["fx"]
		var w: float = L["w"]
		var y := clampf((_base_y - c.y) * float(L["fy"]) * z, -50.0, 60.0) + (vp.y - _vh)
		if fx == 0.0:
			L["copies"][0].position = Vector2(0, 0)
			var kp: float = L["k"]
			L["copies"][0].scale = Vector2(maxf(kp, kp * vp.x / w), maxf(kp, vp.y / _vh * kp))
			continue
		var off := -fposmod(_scroll * fx + t * float(L["drift"]), w)
		for k in L["copies"].size():
			L["copies"][k].position = Vector2(off + k * w, y)
		match L["kind"]:
			"add":
				L["holder"].modulate.a = 0.78 + 0.22 * sin(t * 0.35 + float(L["ph"]))
			"fog":
				L["holder"].modulate.a = 0.85 + 0.15 * sin(t * 0.22 + float(L["ph"]))
	for r in _rays:
		var x := fposmod(float(r["x"]) - c.x * 0.3, vp.x + 300.0) - 150.0
		r["s"].position = Vector2(x, -40)
		r["s"].modulate.a = ray_color.a * (0.7 + 0.5 * sin(t * 0.5 + float(r["ph"])))
