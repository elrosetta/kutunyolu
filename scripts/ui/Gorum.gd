class_name Gorum
extends CanvasLayer
## v42 Gün Ana görümü ve konuşma alt yazısı (oyun durmaz; dövüşü engellemez).
##
## gorum(metin, baslik): ekran ısınır (sıcak altın ışık üstten ve kenarlardan süzülür), Gün Ana'nın mürekkep silüeti
## (assets/hikaye/gun_ana_gorum.png) yan tarafta kâğıda emilir gibi belirir ve duman gibi dağılır, sözü fırçayla harf harf
## yazılır; havada altın mürekkep zerreleri. 3-6 sn; herhangi bir eylem tuşu 0,6 sn sonra hızla söndürür.
## konus(ad, metin, renk): boss / NPC sözü alt yazısı (ad küçük büyük harf, söz fırçayla yazılır), 3,5-5 sn.
## Main kurar (Gorum.inst); Level / HikayeSahne / GunParcasi çağırır. Görümler sıraya girer.

const ALTIN := Color(1.0, 0.82, 0.48)
const BONE := Color(0.96, 0.9, 0.8)
const HARF_HIZ := 34.0

static var inst: Gorum = null

var _kuyruk: Array = []
var _cur: Dictionary = {}
var _t := 0.0
var _sure := 0.0
var _sonme := -1.0
var _c: Control
var _sil: TextureRect
var _mat: ShaderMaterial
var _zerre: Array = []
var _kes_t := -1.0
var gosterilen := 0          # test: kaç görüm / konuşma oynadı
var son_metin := ""


func _ready() -> void:
	layer = 6   # dünyanın (derece 5) üstünde, HUD'un (10) altında
	process_mode = Node.PROCESS_MODE_ALWAYS
	inst = self
	_c = Control.new()
	_c.set_anchors_preset(Control.PRESET_FULL_RECT)
	_c.mouse_filter = Control.MOUSE_FILTER_IGNORE
	_c.draw.connect(_ciz)
	add_child(_c)
	_sil = TextureRect.new()
	_sil.mouse_filter = Control.MOUSE_FILTER_IGNORE
	_sil.expand_mode = TextureRect.EXPAND_IGNORE_SIZE
	_sil.stretch_mode = TextureRect.STRETCH_KEEP_ASPECT_CENTERED
	_sil.texture_filter = CanvasItem.TEXTURE_FILTER_LINEAR_WITH_MIPMAPS
	if ResourceLoader.exists("res://assets/hikaye/gun_ana_gorum.png"):
		_sil.texture = load("res://assets/hikaye/gun_ana_gorum.png")
	_mat = ShaderMaterial.new()
	_mat.shader = load("res://shaders/sumi_gorum.gdshader")   # toplamalı: silüet ışık gibi parlar (hayalet)
	_mat.set_shader_parameter("edge_dark", 0.0)
	_mat.set_shader_parameter("noise_scale", Vector2(5.0, 7.0))
	_sil.material = _mat
	_sil.visible = false
	add_child(_sil)


func _exit_tree() -> void:
	if inst == self:
		inst = null


static func gorum(metin: String, baslik := "", renk := ALTIN, sure := -1.0) -> void:
	if inst == null or metin == "":
		return
	inst._ekle({"tur": "gorum", "metin": metin, "baslik": baslik, "renk": renk, "sure": sure})


static func konus(ad: String, metin: String, renk := BONE, sure := -1.0) -> void:
	if inst == null or metin == "":
		return
	inst._ekle({"tur": "konus", "metin": metin, "ad": ad, "renk": renk, "sure": sure})


static func aktif() -> bool:
	return inst != null and not inst._cur.is_empty()


func _ekle(d: Dictionary) -> void:
	_kuyruk.append(d)
	if _cur.is_empty():
		_baslat()
	elif String(d["tur"]) == "gorum" and String(_cur["tur"]) == "konus" and _sonme < 0.0:
		# Gün Ana'nın sesi konuşmayı keser (söz yarım kalmasın diye en az 1,5 sn okunur)
		_t = maxf(_t, 0.0)
		_kes_t = 1.5


static func temizle() -> void:
	## Yeni bölüm / arena: sırada bekleyen eski konuşmalar atılır (görümler kalır: Gün Ana'nın sesi yolda da sürer)
	if inst == null:
		return
	inst._kuyruk = inst._kuyruk.filter(func(x: Dictionary) -> bool: return String(x["tur"]) == "gorum")
	if not inst._cur.is_empty() and String(inst._cur["tur"]) == "konus" and inst._sonme < 0.0:
		inst._sonme = 0.0


func _baslat() -> void:
	if _kuyruk.is_empty():
		_cur = {}
		_sil.visible = false
		_c.queue_redraw()
		return
	_cur = _kuyruk.pop_front()
	_t = 0.0
	_kes_t = -1.0
	_sonme = -1.0
	gosterilen += 1
	son_metin = String(_cur["metin"])
	var n := String(_cur["metin"]).length()
	var s := float(_cur.get("sure", -1.0))
	if String(_cur["tur"]) == "gorum":
		_sure = s if s > 0.0 else clampf(2.4 + n / HARF_HIZ * 1.6, 3.6, 6.0)
		_sil.visible = _sil.texture != null
		_mat.set_shader_parameter("seed", randf() * 10.0)
		_zerre.clear()
		for k in 26:
			_zerre.append([randf(), randf(), randf_range(0.6, 1.6), randf() * TAU])
		Ses.play("buyu", -12.0, 0.7)
		Ses.play("ad_toren", -16.0, 1.3)
	else:
		_sure = s if s > 0.0 else clampf(2.0 + n / HARF_HIZ * 1.5, 3.2, 5.5)
		_sil.visible = false
		# sırada Gün Ana'nın görümü bekliyorsa söz kısalır (2,6 sn okunur)
		if _kuyruk.any(func(x: Dictionary) -> bool: return String(x["tur"]) == "gorum"):
			_kes_t = 2.6


func _process(delta: float) -> void:
	if _cur.is_empty():
		return
	if get_tree().paused and Sinema.etkin == null and String(_cur["tur"]) == "gorum":
		# menü açıkken görüm bekler (arkadan akıp gitmesin); yazı da durur
		_c.queue_redraw()
		return
	_t += delta
	if _sonme < 0.0 and _t > 0.6:
		for a in ["saldiri1", "saldiri2", "zipla", "yuvarlan", "etkiles"]:
			if Input.is_action_just_pressed(a):
				_sonme = 0.0
				break
	if _sonme < 0.0 and _t >= _sure:
		_sonme = 0.0
	if _kes_t > 0.0 and _sonme < 0.0 and _t >= _kes_t:
		_sonme = 0.0
		_kes_t = -1.0
	if _sonme >= 0.0:
		_sonme += delta
		if _sonme >= 0.5:
			_baslat()
			return
	if String(_cur["tur"]) == "gorum":
		var vp := _c.get_viewport_rect().size
		var h := vp.y * 0.86
		var w := h * 640.0 / 900.0
		_sil.size = Vector2(w, h)
		_sil.position = Vector2(vp.x * 0.74 - w * 0.5, vp.y * 0.08 - sin(_t * 0.6) * 4.0)
		var ac := clampf(_t / 1.4, 0.0, 1.0)
		_mat.set_shader_parameter("reveal", ac * ac * (3.0 - 2.0 * ac))
		_mat.set_shader_parameter("dissolve", clampf(_sonme / 0.5, 0.0, 1.0) * 1.1 if _sonme >= 0.0 else clampf((_t - _sure + 0.8) / 0.8, 0.0, 1.0) * 0.6)
		_sil.modulate = Color(1.0, 0.9, 0.75, 0.55 * _sondur())
	_c.queue_redraw()


func _sondur() -> float:
	## Genel opaklık: açılış 0,5 sn, sönme 0,5 sn
	var a := clampf(_t / 0.5, 0.0, 1.0)
	if _sonme >= 0.0:
		a *= clampf(1.0 - _sonme / 0.5, 0.0, 1.0)
	return a


func _ciz() -> void:
	if _cur.is_empty():
		return
	var c := _c
	var vp := c.get_viewport_rect().size
	var a := _sondur()
	var renk: Color = _cur.get("renk", ALTIN)
	if String(_cur["tur"]) == "gorum":
		# ekran ısınır: üstten sıcak ışık + kenarlarda altın sis (toplamalı değil: hafif boya katmanı)
		var sm := InkUI.tex("smoke")
		var nef := 0.85 + 0.15 * sin(_t * 2.2)
		c.draw_rect(Rect2(Vector2.ZERO, vp), Color(0.6, 0.36, 0.12, 0.08 * a))
		if sm:
			c.draw_texture_rect(sm, Rect2(-vp.x * 0.1, -vp.y * 0.55, vp.x * 1.2, vp.y * 1.0), false, Color(1.0, 0.72, 0.35, 0.28 * a * nef))
			c.draw_texture_rect(sm, Rect2(vp.x * 0.45, vp.y * 0.0, vp.x * 0.6, vp.y * 0.95), false, Color(1.0, 0.78, 0.42, 0.22 * a * nef))
		# altın mürekkep zerreleri: yavaş yükselir, titreşir
		for z in _zerre:
			var px := float(z[0]) * vp.x
			var py := fposmod(float(z[1]) * vp.y - _t * 14.0 * float(z[2]), vp.y)
			var s := 1.2 + float(z[2]) * 1.4
			var za := a * (0.35 + 0.35 * sin(_t * 3.0 + float(z[3])))
			c.draw_circle(Vector2(px + sin(_t + float(z[3])) * 6.0, py), s, Color(1.0, 0.86, 0.5, za), true, -1.0, true)
		_yaz(c, vp, String(_cur["metin"]), "GÜN ANA", String(_cur.get("baslik", "")), renk, a, vp.y * 0.34)
	else:
		# konuşma: alt yazı bandı
		var sm2 := InkUI.tex("smoke")
		if sm2:
			c.draw_texture_rect(sm2, Rect2(vp.x * 0.12, vp.y - 140.0, vp.x * 0.76, 150.0), false, Color(0.02, 0.02, 0.03, 0.7 * a))
		_yaz(c, vp, String(_cur["metin"]), String(_cur.get("ad", "")).to_upper(), "", renk, a, vp.y - 84.0)


func _yaz(c: Control, vp: Vector2, metin: String, ad: String, baslik: String, renk: Color, a: float, y: float) -> void:
	var f := InkUI.font("lore")
	var fc := InkUI.font("caps")
	var fs := 21
	baslik = InkHUD.tr_upper(baslik)   # yazıt harfleri (Cinzel) yalnızca büyük harf çizer: İ noktalı kalsın
	ad = InkHUD.tr_upper(ad)
	if baslik != "":
		var wb := fc.get_string_size(baslik, HORIZONTAL_ALIGNMENT_LEFT, -1, 24).x
		c.draw_string_outline(fc, Vector2((vp.x - wb) * 0.5, y - 64.0), baslik, HORIZONTAL_ALIGNMENT_LEFT, -1, 24, 6, Color(0.05, 0.03, 0.02, 0.6 * a))
		c.draw_string(fc, Vector2((vp.x - wb) * 0.5, y - 64.0), baslik, HORIZONTAL_ALIGNMENT_LEFT, -1, 24, Color(renk, a))
		var st := InkUI.tex("stroke")
		if st:
			c.draw_texture_rect(st, Rect2(vp.x * 0.5 - wb * 0.35, y - 56.0, wb * 0.7, 4.0), false, Color(InkUI.SEAL, 0.85 * a))
	if ad != "":
		var wa := fc.get_string_size(ad, HORIZONTAL_ALIGNMENT_LEFT, -1, 12).x
		c.draw_string(fc, Vector2((vp.x - wa) * 0.5, y - 26.0), ad, HORIZONTAL_ALIGNMENT_LEFT, -1, 12, Color(renk, 0.8 * a))
	var lines := InkHUD.wrap_f(metin, f, fs, minf(560.0, vp.x * 0.7))
	var shown := _t * HARF_HIZ
	var k := 0
	for li in lines.size():
		var line := String(lines[li])
		var w := f.get_string_size(line, HORIZONTAL_ALIGNMENT_LEFT, -1, fs).x
		var x := (vp.x - w) * 0.5
		var yy := y + li * 28.0
		var n := clampi(int(shown) - k, 0, line.length())
		if n > 0:
			var vis := line.substr(0, n)
			c.draw_string_outline(f, Vector2(x, yy), vis, HORIZONTAL_ALIGNMENT_LEFT, -1, fs, 5, Color(0.04, 0.02, 0.01, 0.55 * a))
			c.draw_string(f, Vector2(x, yy), vis, HORIZONTAL_ALIGNMENT_LEFT, -1, fs, Color(BONE.lerp(renk, 0.35), a))
		# yazılmakta olan harf: yayılan mürekkep
		if n < line.length() and n >= 0 and int(shown) - k >= 0:
			var px := x + f.get_string_size(line.substr(0, n), HORIZONTAL_ALIGNMENT_LEFT, -1, fs).x
			var fr := fposmod(shown, 1.0)
			c.draw_string(f, Vector2(px, yy + (1.0 - fr) * 4.0), line.substr(n, 1), HORIZONTAL_ALIGNMENT_LEFT, -1, fs, Color(renk, fr * a))
		k += line.length()
