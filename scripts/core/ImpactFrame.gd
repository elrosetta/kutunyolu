class_name ImpactFrame
extends CanvasLayer
## Darbe karesi (anime "impact frame"): büyük vuruşta 2-3 kare boyunca ekran mürekkep karası olur,
## vuran ve vurulan bembeyaz siluet olarak kalır; kritikte bir kare de renkler ters döner ("çıtırtı").
## Gerçek zamanlı çalışır (hitstop sırasında oyun donuktur). Yalnızca kademe 2+ vuruşlarda; hafif
## vuruşlarda asla (okunurluk hiyerarşisi).

static var _active: ImpactFrame
static var _last_t := -10.0
const COOLDOWN := 1.2  # sn; sık tekrar vurguyu öldürür (yalnızca seçkin/boss ölümü bekleme süresini aşar); v22: 0,7 → 1,2

var _frames := 0
var _invert := false
var _rect: ColorRect
var _inv: ColorRect
var _n := 0
var _fade_t := -1.0
const FADE := 0.09   # v25: tam kareden sonra gerçek zamanda yumuşak sönüş (eski: 2 kare sonra tek karede kayboluyordu)


## v31 kalabalık sahne: aynı anda / 0,15 sn içinde birden çok düşmana gelen büyük vuruşlar tek ortak kare paylaşır
## (yeni hedefler açık karenin silüetlerine eklenir, ikinci kare açılmaz); zorunlu kare (seçkin / boss ölümü, infaz)
## da bir kareden 0,6 sn sonrasına dek yenisini açmaz. Çok hedefli karede (3+) karartma hafifler.
const MERGE := 0.15
const FORCE_GAP := 0.6


static func play(targets: Array, strength := 1.0, frames := 2, force := false) -> void:
	var now := Game.clock()
	if FX.root == null:
		return
	if _active != null and is_instance_valid(_active):
		if now - _last_t < MERGE:
			_active._add_targets(targets)
		return
	if (not force and now - _last_t < COOLDOWN) or (force and now - _last_t < FORCE_GAP):
		return
	_last_t = now
	if Game.fx_scale <= 0.0:
		return
	var f := ImpactFrame.new()
	f._frames = mini(frames, 1)  # v25: 1 tam kare + FADE sn yumuşak sönüş (eski: 2 kare sonra sert kesilme; "takılma" gibi okunuyordu)
	# ters renk karesi kaldırıldı: tüm ekranı bir kare bembeyaz yapıyor, göz yakıyordu
	f._invert = false
	f.layer = 6
	f.process_mode = Node.PROCESS_MODE_ALWAYS
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
	_add_targets(targets)
	_build_inv()
	_n = 0


var _sil_n := 0   # v31: karedeki silüet sayısı (oyuncu dahil)


func _add_targets(targets: Array) -> void:
	var vp := get_viewport()
	var ct := vp.get_canvas_transform()
	for t in targets:
		if _sil_n >= 6:
			break   # v31: en çok 6 silüet (kalabalıkta kare beyaz siluet yığınına dönmesin)
		if t != null and is_instance_valid(t) and has_meta("t_%d" % t.get_instance_id()):
			continue
		if t != null and is_instance_valid(t):
			set_meta("t_%d" % t.get_instance_id(), true)
		if t == null or not is_instance_valid(t) or not ("anim" in t) or t.anim == null:
			continue
		var src: Sprite2D = t.anim.base
		if src == null or src.texture == null:
			continue
		_sil_n += 1
		if _sil_n >= 4 and _rect:
			_rect.color.a = minf(_rect.color.a, 0.42)   # v31: çok hedefte karartma hafif
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
		# mürekkep sprite'ları doğrusal süzgeçli (yakın kamerada siluet kenarı bloklaşmasın)
		s.texture_filter = CanvasItem.TEXTURE_FILTER_LINEAR_WITH_MIPMAPS
		var m := ShaderMaterial.new()
		m.shader = Data.INK_SHADER  # mürekkep gölgelendiricisi
		# v31: ilk iki silüet (vuran + asıl hedef) bembeyaz; çok hedefte diğerleri yarı beyaz (kendi renkleri seçilir):
		# sanat / bitiriş üç-dört düşmana değince kare beyaz silüet yığınına dönmesin
		m.set_shader_parameter("flash", 1.0 if _sil_n <= 2 else 0.5)
		m.set_shader_parameter("flash_color", Color(1.0, 0.98, 0.94, 1.0))
		s.material = m
		s.transform = ct * src.get_global_transform()
		# Bengü'nün fizikli saçı (sprite'ta yok): bu karenin saç çizimi aynı beyaz siluetle, gövdenin arkasında
		var sac := BenguSac.bul(t.anim)
		if sac and sac.is_visible_in_tree():
			var sm := ShaderMaterial.new()
			sm.shader = BenguSac.SHADER
			sm.set_shader_parameter("flash", 1.0 if _sil_n <= 2 else 0.5)
			sm.set_shader_parameter("flash_color", Color(1.0, 0.98, 0.94, 1.0))
			sm.set_shader_parameter("vcol_linear", vp.use_hdr_2d)
			add_child(sac.kopya(ct * t.anim.get_global_transform(), sm))
		add_child(s)
		# silahlı kol iskeleti de siluete dahil (oyuncu)
		if "arm_root" in t and t.arm_root and t.arm_root.visible:
			for ch in t.arm_root.get_children():
				if ch is BenguKol and ch.visible:   # v43 yaşayan kol şeridi
					add_child((ch as BenguKol).kopya(ct * ch.get_global_transform(), m))
					continue
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


func _build_inv() -> void:
	var size := get_viewport().get_visible_rect().size
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


func _process(_delta: float) -> void:
	if Prof.on:
		var t0 := Time.get_ticks_usec()
		_process_ic(_delta)
		Prof.ekle(&"fx", t0)
		return
	_process_ic(_delta)


func _process_ic(_delta: float) -> void:
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
	if _fade_t < 0.0:
		_fade_t = 0.0
	_fade_t += _delta / maxf(0.05, Engine.time_scale)
	var u := clampf(_fade_t / FADE, 0.0, 1.0)
	var a := 1.0 - u * u * (3.0 - 2.0 * u)
	if a > 0.01:
		for ch in get_children():
			if ch is CanvasItem and ch != _inv:
				(ch as CanvasItem).modulate.a = a
		return
	_active = null
	queue_free()
