class_name Bezirgan
extends Node2D
## v24 tüccar: Bezirgân Sartak ve kervan tezgâhı (çöken deve, mallı kilim, fener direği). Bazı bölümlerde durur
## (Level._place_bezirgan; kurallar data/tuccar.json "yer"). Oyuncu yaklaşınca W balonu; W (kısa dokunuş) pazarı açar
## (Main._on_tuccar, HUD._draw_tuccar). Mallar burada tutulur (offers), yenileme sayısı (rerolls) fiyatı artırır.
## Görsel: npc_tuccar_v2 (tools/artgen/tuccar_ink.py, idle / talk) + bezirgan_kervan_v2 süsü (sus_v2.json).

const NAME := "Bezirgân Sartak"
## tezgâh kökeninin tüccara göre konumu (dünya): tüccar devenin kuyruk yanında, kilimin sağında durur
## (tuccar_ink.STAND_X = 48: tezgâh kökeni tüccarın 48 birim solunda)
const TEZGAH_DX := -48.0
## tezgâhın kapladığı alan (tüccarın ayak noktasına göre, dünya): duvar denetimi ve yer seçimi için
const ALAN := Rect2(-146.0, -95.0, 192.0, 95.0)

var level: Node
var anim: SpriteAnim
var near := false
var talk_t := 0.0
var offers: Array = []
var soz := ""        # v32: konakta yakınken başının üstündeki kısa söz (biyoma göre, data/usta.json "sozler")
var rerolls := 0
var sold := 0
var _t := 0.0
var _stall: Sprite2D
var _yazi := true   # ad ve W balonu (pazar / duraklatma açıkken gizli: menünün arkasından görünmesin)


func _ready() -> void:
	z_index = 2
	process_mode = Node.PROCESS_MODE_ALWAYS   # duraklıyken de çizilir (ad gizlenir, tüccar pazarda canlı kalır)
	if level and level.has_method("_decor_v2"):
		var d: Dictionary = level._decor_v2("bezirgan_kervan")
		if not d.is_empty():
			_stall = _make_stall(d)
	anim = SpriteAnim.new()
	add_child(anim)
	anim.setup("npc_tuccar")
	anim.set_facing(1)
	anim.play("idle")
	anim.speed = 0.8
	if level:
		# fener direğinin ve sırt fenerinin sıcak ışığı (karanlık bölümde tezgâh okunur kalsın)
		var l: PointLight2D = level.add_light(Vector2(TEZGAH_DX - 60.0, -58.0), Color(1.0, 0.68, 0.32), 190.0, 1.1, self)
		IsikTitrek.attach(l, "mesale")   # v40: doğal fener titremesi
		IsikTitrek.attach(level.add_light(Vector2(8, -66), Color(1.0, 0.72, 0.36), 110.0, 0.6, self), "ocak")


func _make_stall(d: Dictionary) -> Sprite2D:
	var k := 1.0 / float(d.get("texel", 4.0))
	var s := Sprite2D.new()
	s.texture = d["tex"]
	s.centered = false
	s.offset = Vector2(-float(d["origin"][0]), -float(d["origin"][1]))
	s.scale = Vector2(k, k)
	s.position = Vector2(TEZGAH_DX, 2.0)
	s.texture_filter = CanvasItem.TEXTURE_FILTER_LINEAR_WITH_MIPMAPS
	var m := ShaderMaterial.new()
	m.shader = load("res://shaders/env_ink.gdshader")
	m.set_shader_parameter("moon_gain", float(level.art.get("ground_moon_gain", 0.6)))
	s.material = m
	s.z_index = -4   # oyuncunun ve yaratıkların arkasında (göreli: 2 - 4 = -2, süslerle aynı)
	add_child(s)
	if d.get("glow_tex") != null:
		var g := Sprite2D.new()
		g.texture = d["glow_tex"]
		g.centered = false
		g.offset = s.offset
		g.texture_filter = CanvasItem.TEXTURE_FILTER_LINEAR_WITH_MIPMAPS
		var gm := CanvasItemMaterial.new()
		gm.blend_mode = CanvasItemMaterial.BLEND_MODE_ADD
		gm.light_mode = CanvasItemMaterial.LIGHT_MODE_UNSHADED
		g.material = gm
		g.self_modulate = Color(1.5, 1.35, 1.2)
		s.add_child(g)
		var tw := g.create_tween().set_loops()
		tw.tween_property(g, "self_modulate:a", 0.8, 0.18)
		tw.tween_property(g, "self_modulate:a", 1.0, 0.22)
	return s


func talk() -> void:
	talk_t = 1.4
	anim.play("talk", true)


func _process(delta: float) -> void:
	_t += delta
	talk_t -= delta
	var paused := get_tree().paused
	if paused == _yazi:
		_yazi = not paused
		queue_redraw()
	if paused:
		if talk_t <= 0.0 and anim.anim != "idle":
			anim.play("idle")
		return
	var pl: Node = level.player if level else null
	if pl:
		# çizim sola bakar: oyuncu soldaysa facing 1 (NPC.gd ile aynı)
		anim.set_facing(1 if pl.global_position.x <= global_position.x else -1)
		near = absf(pl.global_position.x - global_position.x) < 44.0 and absf(pl.global_position.y - global_position.y) < 48.0
	if talk_t <= 0.0 and anim.anim != "idle":
		anim.play("idle")
	queue_redraw()


func world_rect() -> Rect2:
	return Rect2(global_position + ALAN.position, ALAN.size)


func _draw() -> void:
	if not _yazi:
		return
	PixUI.text(self, Vector2(-80, -101), NAME, PixUI.GOLD, 1, HORIZONTAL_ALIGNMENT_CENTER, 160, 2)
	if near:
		var y := roundf(-116.0 + sin(_t * 5.0) * 2.0)
		PixUI.key_cap(self, Vector2(-5, y), HUD.KEY_ETKILES)
		if soz != "":
			PixUI.text(self, Vector2(-110, y - 14.0), soz, Color(PixUI.TEXT, 0.85), 1, HORIZONTAL_ALIGNMENT_CENTER, 220, 2)
