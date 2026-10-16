class_name ImpactFrame
extends CanvasLayer
## Darbe karesi (anime "impact frame"): büyük vuruşta 2-3 kare boyunca ekran mürekkep karası olur,
## vuran ve vurulan bembeyaz siluet olarak kalır; kritikte bir kare de renkler ters döner ("çıtırtı").
## Gerçek zamanlı çalışır (hitstop sırasında oyun donuktur). Yalnızca kademe 2+ vuruşlarda; hafif
## vuruşlarda asla (okunurluk hiyerarşisi).

static var _active: ImpactFrame
static var _last_t := -10.0
const COOLDOWN := 0.7  # sn; sık tekrar vurguyu öldürür (yalnızca seçkin/boss ölümü bekleme süresini aşar)

var _frames := 0
var _invert := false
var _rect: ColorRect
var _inv: ColorRect
var _n := 0


static func play(targets: Array, strength := 1.0, frames := 2, force := false) -> void:
	var now := Game.clock()
	if FX.root == null or _active != null or (not force and now - _last_t < COOLDOWN):
		return
	_last_t = now
	if Game.fx_scale <= 0.0:
		return
	var f := ImpactFrame.new()
	f._frames = mini(frames, 2)  # en çok 2 kare: uzun kararma "ekran gitti" gibi okunuyordu
	# ters renk karesi kaldırıldı: tüm ekranı bir kare bembeyaz yapıyor, göz yakıyordu
	f._invert = false
	f.layer = 6
	FX.root.get_tree().root.add_child(f)
	_active = f
	f._build(targets, strength)


func _build(targets: Array, strength: float) -> void:
	var vp := get_viewport()
	var size := vp.get_visible_rect().size
	_rect = ColorRect.new()
	_rect.size = size
	_rect.color = Color(0.03, 0.02, 0.05, clampf(0.5 + 0.15 * strength, 0.0, 0.68))
	add_child(_rect)
	var ct := vp.get_canvas_transform()
	for t in targets:
		if t == null or not is_instance_valid(t) or not ("anim" in t) or t.anim == null:
			continue
		var src: Sprite2D = t.anim.base
		if src == null or src.texture == null:
			continue
		var s := Sprite2D.new()
		s.texture = src.texture
		s.region_enabled = src.region_enabled
		s.region_rect = src.region_rect
		s.hframes = src.hframes
		s.vframes = src.vframes
		s.frame = src.frame
		s.centered = src.centered
		s.offset = src.offset
		s.flip_h = src.flip_h
		s.flip_v = src.flip_v
		# stil v2: mürekkep sprite'ları doğrusal süzgeçli (yakın kamerada siluet kenarı bloklaşmasın)
		s.texture_filter = CanvasItem.TEXTURE_FILTER_LINEAR_WITH_MIPMAPS if Data.stil == "v2" else CanvasItem.TEXTURE_FILTER_NEAREST
		var m := ShaderMaterial.new()
		m.shader = Game.toon_shader
		m.set_shader_parameter("flash", 1.0)
		m.set_shader_parameter("flash_color", Color(1.0, 0.98, 0.94, 1.0))
		s.material = m
		s.transform = ct * src.get_global_transform()
		add_child(s)
		# silahlı kol iskeleti de siluete dahil (oyuncu)
		if "arm_root" in t and t.arm_root and t.arm_root.visible:
			for ch in t.arm_root.get_children():
				if ch is Sprite2D and ch.visible and ch.texture:
					var w := Sprite2D.new()
					w.texture = ch.texture
					w.region_enabled = ch.region_enabled
					w.region_rect = ch.region_rect
					w.centered = ch.centered
					w.offset = ch.offset
					w.flip_h = ch.flip_h
					w.hframes = ch.hframes
					w.vframes = ch.vframes
					w.frame = ch.frame
					w.texture_filter = s.texture_filter
					w.material = m
					w.transform = ct * ch.get_global_transform()
					add_child(w)
	if _invert:
		_inv = ColorRect.new()
		_inv.size = size
		var sh := Shader.new()
		sh.code = "shader_type canvas_item;\nuniform sampler2D screen_tex : hint_screen_texture, filter_nearest;\nvoid fragment() {\n\tvec3 c = texture(screen_tex, SCREEN_UV).rgb;\n\tCOLOR = vec4(vec3(1.0) - c, 1.0);\n}\n"
		var im := ShaderMaterial.new()
		im.shader = sh
		_inv.material = im
		_inv.visible = false
		add_child(_inv)
	_n = 0


func _process(_delta: float) -> void:
	_n += 1
	if _n <= _frames:
		return
	if _invert and _n == _frames + 1:
		# ters renk karesi: siluet katmanı gizlenir, ekran bir kare negatif
		_rect.visible = false
		for ch in get_children():
			if ch is Sprite2D:
				ch.visible = false
		_inv.visible = true
		return
	_active = null
	queue_free()
