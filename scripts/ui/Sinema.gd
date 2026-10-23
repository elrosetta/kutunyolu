class_name Sinema
extends CanvasLayer
## v42 hikâye sineması: sumi-e panelleri (assets/hikaye/<ad>.jpg + _isik.png; tools/artgen/hikaye_ink.py) sırayla,
## kâğıda emilen mürekkep gibi belirir (shaders/sumi_panel.gdshader), yavaşça yaklaşır / kayar (Ken Burns), altın ışıma
## nefes alır, anlatı fırçayla harf harf yazılır. "giris": açılış (ilk koşuda kendiliğinden; sonra Ozan'dan),
## "son": Erlik'in örgüsünden sonra son + jenerik. Boşluk / Enter: yazıyı tamamla → sonraki panel; Esc: hepsini geç.
## Oyun ağacı duraklıyken oynar (process ALWAYS). Bitince "bitti" sinyali, düğüm kendini siler.

signal bitti

const BONE := Color(0.95, 0.9, 0.8)
const SUMI := Color(0.08, 0.065, 0.06)
const ACILMA := 1.7        # panelin mürekkeple belirme süresi (sn)
const HARF_HIZ := 30.0     # sn başına harf
const YAZI_GECIKME := 1.0  # panel açıldıktan bu kadar sonra yazı başlar

static var etkin: Sinema = null

var tur := ""
var paneller: Array = []
var i := -1
var t := 0.0
var _meta: Dictionary = {}
var _bg: ColorRect
var _alt: TextureRect     # bir önceki panel (yenisi üstünde belirirken altta kalır)
var _ust: TextureRect
var _isik: TextureRect
var _yazi: Control
var _jenerik := false
var _jt := 0.0
var _kapanis := -1.0
var _yazi_tam := false
var _girdi_t := 0.0


static func oynat(parent: Node, k: String) -> Sinema:
	## k: "giris" ya da "son". Dönen düğümün "bitti" sinyaline bağlanılır.
	var s := Sinema.new()
	s.tur = k
	parent.add_child(s)
	return s


func _ready() -> void:
	layer = 40
	process_mode = Node.PROCESS_MODE_ALWAYS
	etkin = self
	paneller = Data.story.get(tur, [])
	if FileAccess.file_exists("res://assets/hikaye/paneller.json"):
		_meta = Data.load_json("res://assets/hikaye/paneller.json")
	_bg = ColorRect.new()
	_bg.color = Color(0.02, 0.018, 0.025)
	_bg.set_anchors_preset(Control.PRESET_FULL_RECT)
	_bg.mouse_filter = Control.MOUSE_FILTER_IGNORE
	add_child(_bg)
	_alt = _panel_rect()
	_ust = _panel_rect()
	_isik = TextureRect.new()
	_isik.mouse_filter = Control.MOUSE_FILTER_IGNORE
	_isik.expand_mode = TextureRect.EXPAND_IGNORE_SIZE
	_isik.stretch_mode = TextureRect.STRETCH_SCALE
	_isik.texture_filter = CanvasItem.TEXTURE_FILTER_LINEAR
	var am := CanvasItemMaterial.new()
	am.blend_mode = CanvasItemMaterial.BLEND_MODE_ADD
	_isik.material = am
	add_child(_isik)
	_yazi = Control.new()
	_yazi.set_anchors_preset(Control.PRESET_FULL_RECT)
	_yazi.mouse_filter = Control.MOUSE_FILTER_IGNORE
	_yazi.draw.connect(_ciz)
	add_child(_yazi)
	Ses.music("baslik" if tur == "giris" else "yurt", 2.0)
	Ses.play("ad_toren", -6.0, 0.8 if tur == "giris" else 1.0)
	_sonraki()


func _panel_rect() -> TextureRect:
	var r := TextureRect.new()
	r.mouse_filter = Control.MOUSE_FILTER_IGNORE
	r.expand_mode = TextureRect.EXPAND_IGNORE_SIZE
	r.stretch_mode = TextureRect.STRETCH_SCALE
	r.texture_filter = CanvasItem.TEXTURE_FILTER_LINEAR_WITH_MIPMAPS
	var m := ShaderMaterial.new()
	m.shader = load("res://shaders/sumi_panel.gdshader")
	r.material = m
	add_child(r)
	return r


func _exit_tree() -> void:
	if etkin == self:
		etkin = null


func _sonraki() -> void:
	i += 1
	t = 0.0
	_yazi_tam = false
	if i >= paneller.size():
		if tur == "son" and not _jenerik:
			_jenerik = true
			_jt = 0.0
			return
		_bitir()
		return
	var p: Dictionary = paneller[i]
	# önceki panel alta iner (tam açık), yenisi üstte mürekkeple belirir
	if _ust.texture != null:
		_alt.texture = _ust.texture
		_alt.set_meta("kay", _ust.get_meta("kay", [0, 0, 1, 1]))
		_alt.set_meta("son_k", 1.0)
		(_alt.material as ShaderMaterial).set_shader_parameter("reveal", 1.0)
		_alt.visible = true
	else:
		_alt.visible = false
	var ad := String(p.get("resim", ""))
	_ust.texture = load("res://assets/hikaye/%s.jpg" % ad) if ResourceLoader.exists("res://assets/hikaye/%s.jpg" % ad) else null
	_ust.set_meta("kay", p.get("kay", [0, 0, 1, 1.05]))
	var sm := _ust.material as ShaderMaterial
	sm.set_shader_parameter("reveal", 0.0)
	sm.set_shader_parameter("seed", float(i) * 0.37 + (0.5 if tur == "son" else 0.0))
	var ip := "res://assets/hikaye/%s_isik.png" % ad
	_isik.texture = load(ip) if ResourceLoader.exists(ip) else null
	if i > 0:
		Ses.play("ui_ac", -10.0, 0.7)


func _sure() -> float:
	if i < 0 or i >= paneller.size():
		return 1.0
	return float(paneller[i].get("sure", 6.5))


func _koyu() -> bool:
	if i < 0 or i >= paneller.size():
		return true
	return bool(_meta.get(String(paneller[i].get("resim", "")), {}).get("koyu", true))


func _metin() -> String:
	if i < 0 or i >= paneller.size():
		return ""
	return String(paneller[i].get("metin", ""))


func _harf_sayi() -> int:
	return _metin().replace("\n", "").length()


func _input(event: InputEvent) -> void:
	if _kapanis >= 0.0 or _girdi_t < 0.35:
		return
	var go: bool = event.is_action_pressed("zipla") or event.is_action_pressed("saldiri1") or (event is InputEventKey and event.pressed and not event.echo and event.physical_keycode == KEY_ENTER)
	if event.is_action_pressed("duraklat"):
		get_viewport().set_input_as_handled()
		_bitir()
	elif go:
		get_viewport().set_input_as_handled()
		_girdi_t = 0.0
		if _jenerik:
			_bitir()
		elif not _yazi_tam:
			t = maxf(t, YAZI_GECIKME + float(_harf_sayi()) / HARF_HIZ + 0.3)
		else:
			_sonraki()


func _bitir() -> void:
	if _kapanis >= 0.0:
		return
	_kapanis = 0.0


func _process(delta: float) -> void:
	_girdi_t += delta
	if _kapanis >= 0.0:
		_kapanis += delta
		var k := clampf(1.0 - _kapanis / 0.6, 0.0, 1.0)
		for n in [_alt, _ust, _isik, _yazi]:
			n.modulate.a = k
		if _kapanis >= 0.75:
			bitti.emit()
			queue_free()
		_yazi.queue_redraw()
		return
	if _jenerik:
		_jt += delta
		var fk := clampf(1.0 - _jt / 2.0, 0.25, 1.0)
		_ust.modulate.a = fk
		_isik.modulate.a = fk
		_alt.visible = false
		_yerlestir(_ust, 1.0)
		var n_j: int = (Data.story.get("jenerik", []) as Array).size()
		if _jt > 6.0 + n_j * 2.6 + 4.0:
			_bitir()
		_yazi.queue_redraw()
		return
	t += delta
	var r := clampf(t / ACILMA, 0.0, 1.0)
	(_ust.material as ShaderMaterial).set_shader_parameter("reveal", r * r * (3.0 - 2.0 * r))
	if r >= 1.0:
		_alt.visible = false
	var sure := _sure()
	_yerlestir(_ust, clampf(t / sure, 0.0, 1.2))
	if _alt.visible:
		_yerlestir(_alt, 1.0 + t / sure * 0.1)
	if _isik.texture != null:
		_isik.position = _ust.position
		_isik.size = _ust.size
		_isik.modulate = Color(1, 1, 1, r * (0.24 + 0.1 * sin(t * 1.7)))
	_yazi_tam = t >= YAZI_GECIKME + float(_harf_sayi()) / HARF_HIZ
	if t >= sure + maxf(0.0, float(_harf_sayi()) / HARF_HIZ - 2.0):
		_sonraki()
	_yazi.queue_redraw()


func _yerlestir(r: TextureRect, u: float) -> void:
	## Ken Burns: panel ekranı örter (kenar boşluğu yok), kay = [dx, dy, z0, z1] (dx, dy ekran oranı)
	var vp := get_viewport().get_visible_rect().size
	var kay: Array = r.get_meta("kay", [0, 0, 1, 1.05])
	var e := u * u * (3.0 - 2.0 * u) if u <= 1.0 else 1.0 + (u - 1.0) * 0.5
	var z := lerpf(float(kay[2]), float(kay[3]), e) * 1.02
	var base := maxf(vp.x / 1600.0, vp.y / 900.0)
	var sz := Vector2(1600.0, 900.0) * base * z
	var off := Vector2(float(kay[0]), float(kay[1])) * vp * (e - 0.5)
	r.size = sz
	r.position = (vp - sz) * 0.5 + off


# ------------------------------------------------------------------ yazı
func _ciz() -> void:
	var c := _yazi
	var vp := c.get_viewport_rect().size
	if _jenerik:
		_ciz_jenerik(c, vp)
		return
	var s := _metin()
	if s == "":
		return
	var f := InkUI.font("lore")
	var fs := 22
	var koyu := _koyu()
	var col := BONE if koyu else SUMI
	var lines := s.split("\n")
	var lh := 30.0
	var y0 := vp.y - 40.0 - lines.size() * lh
	# yazının ardında yumuşak yıkama bandı (koyu panelde mürekkep, açıkta kâğıt)
	var band_a := clampf((t - YAZI_GECIKME + 0.4) * 1.5, 0.0, 1.0)
	var bc := Color(0.02, 0.02, 0.03) if koyu else Color(0.96, 0.92, 0.84)
	var wash := InkUI.tex("smoke")
	var by := y0 + lines.size() * lh * 0.5 - 6.0
	if wash:
		c.draw_texture_rect(wash, Rect2(vp.x * 0.5 - vp.x * 0.42, by - 70.0, vp.x * 0.84, 150.0), false, Color(bc, 0.55 * band_a))
	var shown := (t - YAZI_GECIKME) * HARF_HIZ
	var k := 0
	for li in lines.size():
		var line: String = lines[li]
		var w := f.get_string_size(line, HORIZONTAL_ALIGNMENT_LEFT, -1, fs).x
		var x := (vp.x - w) * 0.5
		var y := y0 + li * lh + fs
		for ci in line.length():
			var a := clampf((shown - float(k)) / 5.0, 0.0, 1.0)
			k += 1
			if a <= 0.0:
				break
			var ch := line.substr(ci, 1)
			var px := x + f.get_string_size(line.substr(0, ci), HORIZONTAL_ALIGNMENT_LEFT, -1, fs).x
			var dy := (1.0 - a) * 5.0
			# fırça dokunuşu: harf önce kalın / bulanık (mürekkep yayılıyor), sonra oturur
			if a < 1.0:
				c.draw_string(f, Vector2(px, y + dy), ch, HORIZONTAL_ALIGNMENT_LEFT, -1, fs, Color(col, a * 0.35))
				c.draw_string_outline(f, Vector2(px, y + dy), ch, HORIZONTAL_ALIGNMENT_LEFT, -1, fs, int(3.0 * (1.0 - a)) + 1, Color(col, a * 0.25))
			else:
				c.draw_string(f, Vector2(px, y), ch, HORIZONTAL_ALIGNMENT_LEFT, -1, fs, col)
	# ilerleme: alt köşede küçük mühür noktaları + tuş ipucu
	var n := paneller.size()
	for q in n:
		var p := Vector2(vp.x - 24.0 - (n - 1 - q) * 12.0, vp.y - 18.0)
		if q == i:
			InkUI.splat(c, p, 10.0, Color(InkUI.SEAL, 0.9), float(q))
		else:
			c.draw_circle(p, 2.0, Color(col, 0.35), true, -1.0, true)
	var fb := InkUI.font("body")
	var hint := "Boşluk: ilerle   ·   Esc: geç"
	c.draw_string(fb, Vector2(18.0, vp.y - 13.0), hint, HORIZONTAL_ALIGNMENT_LEFT, -1, 11, Color(col, 0.4))


func _ciz_jenerik(c: Control, vp: Vector2) -> void:
	## Jenerik: kâğıt rengine çekilmiş son panelin üstünde sırayla belirip kaybolan adlar (fırçayla, ortada)
	c.draw_rect(Rect2(Vector2.ZERO, vp), Color(0.02, 0.02, 0.03, clampf(_jt / 2.0, 0.0, 0.62)))
	var J: Array = Data.story.get("jenerik", [])
	var fl := InkUI.font("caps")
	var fs := InkUI.font("lore")
	var idx := int((_jt - 2.0) / 2.6)
	for q in J.size():
		var st := 2.0 + q * 2.6
		var lt := _jt - st
		if lt < 0.0 or lt > 4.2:
			continue
		var a := clampf(minf(lt / 0.8, (4.2 - lt) / 0.9), 0.0, 1.0)
		var e: Array = J[q]
		var yy := vp.y * 0.5 - 20.0 - lt * 6.0 + (q - idx) * 0.0
		var big := 30 if q == 0 else 22
		var s1 := String(e[0])
		var w1 := fl.get_string_size(s1, HORIZONTAL_ALIGNMENT_LEFT, -1, big).x
		c.draw_string(fl, Vector2((vp.x - w1) * 0.5, yy), s1, HORIZONTAL_ALIGNMENT_LEFT, -1, big, Color(1.0, 0.86, 0.55, a))
		if String(e[1]) != "":
			var s2 := String(e[1])
			var w2 := fs.get_string_size(s2, HORIZONTAL_ALIGNMENT_LEFT, -1, 17).x
			c.draw_string(fs, Vector2((vp.x - w2) * 0.5, yy + 30.0), s2, HORIZONTAL_ALIGNMENT_LEFT, -1, 17, Color(BONE, a * 0.85))
		var st_t := InkUI.tex("stroke")
		if st_t:
			c.draw_texture_rect(st_t, Rect2(vp.x * 0.5 - w1 * 0.4 * a, yy + 8.0, w1 * 0.8 * a, 4.0), false, Color(InkUI.SEAL, 0.8 * a))
