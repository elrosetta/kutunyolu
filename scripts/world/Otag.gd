class_name Otag
extends Node2D
## v42 sınav otağı (Otağ Yeri'nde, Kut Kapısı'nın önünde). Atlas assets/fx/ink/otag_v2.png (+ _e ışıma) + otag_v2.json
## (tools/artgen/otag_ink.py; HD paketi assets_hd/x2/fx/ink/otag_v2.webp). tur: cabuk | dokunulmaz | avci | han.
## Durum Level.sinav'dan: açık otağ (kazanılan mühür) ışır ve W ile girilir (OtagIc); kapalı otağın kapısında mum mühür
## (bekleyen: soluk renkli tamga; kaybedilen: gri, çatlak). Ödül bir kez alınır (alindi).

const JSON_PATH := "res://assets/fx/ink/otag_v2.json"
const PNG_PATH := "res://assets/fx/ink/otag_v2.png"
const GLOW_PATH := "res://assets/fx/ink/otag_v2_e.png"
const YAKIN := 26.0   # kapıya yatay uzaklık (px)

static var _meta: Dictionary = {}
static var _tex: Texture2D
static var _glow: Texture2D

var level: Node
var tur := "cabuk"
var cell := Vector2i.ZERO
var alindi := false
var near := false
var _spr: Sprite2D
var _light: PointLight2D
var _t := 0.0
var _son_durum := 99
var _degis_t := -9.0


static func meta() -> Dictionary:
	if _meta.is_empty():
		_meta = Data.load_json(JSON_PATH) if FileAccess.file_exists(JSON_PATH) else {"sprites": {}}
		if ResourceLoader.exists(PNG_PATH):
			_tex = Data.tex(PNG_PATH)
			_glow = load(GLOW_PATH) if ResourceLoader.exists(GLOW_PATH) else null
	return _meta


static func region(n: String) -> Rect2:
	var m: Dictionary = meta()["sprites"].get(n, {})
	if m.is_empty():
		return Rect2()
	var r: Array = m["rect"]
	return Rect2(r[0], r[1], r[2], r[3])


static func tex() -> Texture2D:
	meta()
	return _tex


static func texel(n: String) -> float:
	return float((meta()["sprites"].get(n, {}) as Dictionary).get("texel", 4.0))


static func sprite(n: String, lit := true) -> Sprite2D:
	var m: Dictionary = meta()["sprites"].get(n, {})
	if m.is_empty() or _tex == null:
		return null
	var k := 1.0 / float(m.get("texel", 4.0))
	var s := Sprite2D.new()
	s.texture = _tex
	s.region_enabled = true
	s.centered = false
	s.scale = Vector2(k, k)
	s.texture_filter = CanvasItem.TEXTURE_FILTER_LINEAR_WITH_MIPMAPS
	s.material = SusV2.lit_mat() if lit else SusV2.flat_mat()
	var g := Sprite2D.new()
	g.name = "glow"
	g.texture = _glow
	g.region_enabled = true
	g.centered = false
	g.texture_filter = CanvasItem.TEXTURE_FILTER_LINEAR_WITH_MIPMAPS
	g.material = SusV2.add_mat()
	s.add_child(g)
	set_region(s, n)
	return s


static func set_region(s: Sprite2D, n: String) -> void:
	var m: Dictionary = meta()["sprites"].get(n, {})
	if m.is_empty() or s == null:
		return
	s.region_rect = region(n)
	s.offset = -Vector2(float(m["pivot"][0]), float(m["pivot"][1]))
	var g := s.get_node_or_null("glow") as Sprite2D
	if g:
		g.region_rect = s.region_rect
		g.offset = s.offset
		g.visible = bool(m.get("glow", false)) and _glow != null


static func ui_draw(ci: CanvasItem, n: String, c: Vector2, boy: float, col: Color) -> void:
	## Arayüz: atlas parçasını c merkezli, boy yüksekliğinde çiz (renklendirilmiş)
	var r := region(n)
	if r.size.y <= 0.0 or tex() == null:
		return
	var k := boy / r.size.y
	var sz := r.size * k
	ci.draw_texture_rect_region(_tex, Rect2(c - sz * 0.5, sz), r, col)


func _ready() -> void:
	z_index = -1
	InkDraw.prep(self)
	_spr = sprite("otag_%s_kapali" % tur)
	if _spr:
		_spr.show_behind_parent = true   # kapı mührü (_draw) otağın üstünde
		add_child(_spr)
	_light = level.add_light(Vector2(0, -16), Color(1.0, 0.68, 0.34), 90.0, 0.0, self) if level and level.has_method("add_light") else null
	tazele()


func durum() -> int:
	if level == null or level.get("sinav") == null:
		return 0
	return level.sinav.durum_of(tur)


func acik() -> bool:
	return durum() == 1


func tazele() -> void:
	var d := durum()
	if d != _son_durum:
		if _son_durum != 99:
			_degis_t = _t
			if d == 1:
				Ses.play("otag_ac", -6.0, 1.0, 0.02, 0.05, global_position)
				FX.ring(global_position + Vector2(0, -20), 34, Sinav.RENK[tur], 0.5)
		_son_durum = d
		set_region(_spr, "otag_%s_%s" % [tur, "acik" if d == 1 else "kapali"])
	queue_redraw()


func _process(delta: float) -> void:
	_t += delta
	if level == null or level.player == null:
		return
	var pl: Node2D = level.player
	var dp: Vector2 = pl.global_position - global_position
	near = absf(dp.x) < YAKIN and absf(dp.y) < 30.0
	if _light:
		var hedef := 0.0
		if durum() == 1:
			hedef = (0.55 if alindi else 1.1) + 0.12 * sin(_t * 3.1)
		_light.energy = lerpf(_light.energy, hedef, 0.08)
	if _spr:
		var g := _spr.get_node_or_null("glow") as Sprite2D
		if g:
			g.self_modulate = Color(1.3, 1.2, 1.1, (0.55 if alindi else 1.0) * (0.85 + 0.15 * sin(_t * 2.7)))
	if Engine.get_process_frames() % 2 == 0:
		queue_redraw()


func kapi_y() -> float:
	return -28.0 * 0.55 if tur != "han" else -34.0 * 0.55


func _draw() -> void:
	## Kapalı otağın kapısında mum mühür + sınav tamgası (bekleyen: renkli soluk, nabız; kaybedilen: gri + çatlak)
	var d := durum()
	var c := Vector2(0, -28.0 * 0.9 * 0.55) if tur != "han" else Vector2(0, -34.0 * 0.9 * 0.55)
	if d == 1:
		if not alindi and near:
			InkDraw.ring(self, c + Vector2(0, -6), 18.0, 18.0, Color(Sinav.RENK[tur], 0.25 + 0.15 * sin(_t * 5.0)))
		return
	var col: Color = Sinav.RENK[tur]
	var mc := Color(0.86, 0.78, 0.62) if d == 0 else Color(0.5, 0.48, 0.48)
	var tc := col.darkened(0.15) if d == 0 else Color(0.32, 0.3, 0.32)
	if d == 0:
		tc.a = 0.75 + 0.25 * sin(_t * 2.2)
	var s := 9.0
	var k := clampf((_t - _degis_t) / 0.35, 0.0, 1.0)
	if d == -1 and k < 1.0:
		c += Vector2(randf_range(-1, 1), randf_range(-1, 1)) * (1.0 - k) * 2.0
	ui_draw(self, "ui_muhur", c, s * 1.5, mc)
	ui_draw(self, "ui_tamga_" + tur, c, s * 1.05, tc)
	if d == -1:
		var ink := Color(0.06, 0.05, 0.07, 0.95)
		var pts := [c + Vector2(-6, -5), c + Vector2(-1.5, -1), c + Vector2(-3, 2), c + Vector2(2, 6)]
		for i in pts.size() - 1:
			InkDraw.stroke(self, pts[i], pts[i + 1].lerp(pts[i], 1.0 - k), 1.6, ink)
		InkDraw.stroke(self, c + Vector2(-1.5, -1), (c + Vector2(5, -4)).lerp(c + Vector2(-1.5, -1), 1.0 - k), 1.2, ink)
