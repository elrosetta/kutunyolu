extends Node
## Piksel denetimi: oyun sürerken sahne ağacını düzenli tarar ve hâlâ piksel görünen her şeyi raporlar (v30: v1 piksel
## stili kaldırıldı; denetim artık eski piksel görünümün geri sızmasına karşı bekçi).
##   godot --headless --path . --quit-after 2400 -- --piksel_tara --otomatik --derinlik=3
##   (başka test bayraklarıyla birleşir: --boss=..., --yurt, --sahne, --ekran=...)
## Sınıflar:
##   suzgec   doku çizen düğümün etkin süzgeci en yakın komşu (NEAREST): büyütülünce bloklaşır
##   v1_doku  doku yolu mürekkep dışı bir varlık (ör. assets/sprites/x.png, assets/fx/anim/x.png)
##   kare     dokusuz CPUParticles2D (kare piksel parçacık)
##   yazi     piksel yazı tipi (pixel.fnt) kullanan etiket
##   iz       PikselIz.iz(): "_v2" sürümü olmayan varlık istendi (Data.stil_id) ya da mürekkep simgesi yok (PixUI.icon)
## Her taramada yeni bulguları "[piksel] YENİ ..." satırıyla, sonunda "[piksel] TOPLAM n" ile yazar.
## --piksel_tara=rapor.txt verilirse (mutlak yol) her taramada tam liste dosyaya da yazılır.

var main: Node
var _t := 0.0
var _found: Dictionary = {}   # anahtar -> {sinif, ayrinti, sayi}
var _out := ""
var _scans := 0

## mürekkep / yumuşak varlık yolları (bunlar v1 sayılmaz)
const INK_YOL := ["_v2", "/ink/", "/fonts/", "assets/fx/ink_p/", "/ink_", "assets/hikaye/"]   # v42: sumi-e sinema / görüm dokuları


func _ready() -> void:
	process_mode = Node.PROCESS_MODE_ALWAYS
	PikselIz.acik = true
	for a in OS.get_cmdline_user_args():
		if String(a).begins_with("--piksel_tara="):
			_out = String(a).trim_prefix("--piksel_tara=")
	print("[piksel] denetim açık, stil=%s" % Data.STIL)


func _process(delta: float) -> void:
	_t += delta / maxf(0.05, Engine.time_scale)
	if _t < 0.2:
		return
	_t = 0.0
	_scan()


func _notification(what: int) -> void:
	if what == NOTIFICATION_PREDELETE or what == NOTIFICATION_WM_CLOSE_REQUEST:
		_report(true)


func _add(sinif: String, ayrinti: String) -> void:
	var k := sinif + " | " + ayrinti
	if not _found.has(k):
		_found[k] = {"sinif": sinif, "ayrinti": ayrinti, "sayi": 0}
		print("[piksel] YENİ %s" % k)
	_found[k]["sayi"] = int(_found[k]["sayi"]) + 1


static func _is_ink_path(p: String) -> bool:
	for s in INK_YOL:
		if p.contains(s):
			return true
	return false


static func _eff_filter(ci: CanvasItem) -> int:
	## Etkin CanvasItem süzgeci (TEXTURE_FILTER_*): üst düğümlere, sonra görüntü alanı varsayılanına çıkar
	var n: Node = ci
	while n != null:
		if n is CanvasItem:
			var f: int = (n as CanvasItem).texture_filter
			if f != CanvasItem.TEXTURE_FILTER_PARENT_NODE:
				return f
		elif n is Viewport:
			match (n as Viewport).canvas_item_default_texture_filter:
				Viewport.DEFAULT_CANVAS_ITEM_TEXTURE_FILTER_NEAREST:
					return CanvasItem.TEXTURE_FILTER_NEAREST
				Viewport.DEFAULT_CANVAS_ITEM_TEXTURE_FILTER_LINEAR:
					return CanvasItem.TEXTURE_FILTER_LINEAR
				Viewport.DEFAULT_CANVAS_ITEM_TEXTURE_FILTER_LINEAR_WITH_MIPMAPS:
					return CanvasItem.TEXTURE_FILTER_LINEAR_WITH_MIPMAPS
				_:
					return CanvasItem.TEXTURE_FILTER_NEAREST_WITH_MIPMAPS
		n = n.get_parent()
	return CanvasItem.TEXTURE_FILTER_NEAREST


static func _nearest(f: int) -> bool:
	return f == CanvasItem.TEXTURE_FILTER_NEAREST or f == CanvasItem.TEXTURE_FILTER_NEAREST_WITH_MIPMAPS


static func _tex_info(t: Texture2D) -> Array:
	## [yol, CanvasTexture süzgeci ya da -1]
	var filt := -1
	if t is CanvasTexture:
		var ct := t as CanvasTexture
		if ct.texture_filter != CanvasItem.TEXTURE_FILTER_PARENT_NODE:
			filt = ct.texture_filter
		t = ct.diffuse_texture
	if t is AtlasTexture:
		t = (t as AtlasTexture).atlas
	if t == null:
		return ["", filt]
	var p := t.resource_path
	if p == "" and t.resource_name.begins_with("ink_p/"):
		p = "res://assets/fx/" + t.resource_name + ".png"  # InkDraw.particle boyut kılıfı
	elif p == "":
		p = "(çalışma zamanı %dx%d)" % [t.get_width(), t.get_height()]
	return [p, filt]


func _who(n: Node) -> String:
	var s: Script = n.get_script()
	var sn := s.resource_path.get_file().get_basename() if s else n.get_class()
	var par := n.get_parent()
	var ps := ""
	if par:
		var pscr: Script = par.get_script()
		ps = pscr.resource_path.get_file().get_basename() if pscr else par.get_class()
	return "%s<%s" % [sn, ps]


func _check_tex(n: CanvasItem, t: Texture2D, what: String) -> void:
	if t == null:
		return
	var inf := _tex_info(t)
	var p: String = inf[0]
	var filt: int = inf[1] if int(inf[1]) >= 0 else _eff_filter(n)
	if p.begins_with("res://") and not _is_ink_path(p):
		_add("v1_doku", "%s %s %s" % [_who(n), what, p.trim_prefix("res://")])
	elif p.begins_with("(") and t.get_width() <= 16 and t.get_height() <= 16:
		_add("v1_doku", "%s %s küçük çalışma zamanı dokusu %s (piksel blok)" % [_who(n), what, p])
	if _nearest(filt):
		_add("suzgec", "%s %s %s" % [_who(n), what, p.trim_prefix("res://")])


func _scan() -> void:
	_scans += 1
	var stack: Array = [get_tree().root]
	while not stack.is_empty():
		var n: Node = stack.pop_back()
		for c in n.get_children():
			stack.append(c)
		if not (n is CanvasItem):
			continue
		var ci := n as CanvasItem
		if not ci.is_visible_in_tree():
			continue
		if ci is Sprite2D:
			_check_tex(ci, (ci as Sprite2D).texture, "Sprite2D")
		elif ci is AnimatedSprite2D:
			var sf := (ci as AnimatedSprite2D).sprite_frames
			if sf:
				var an := (ci as AnimatedSprite2D).animation
				if sf.get_frame_count(an) > 0:
					_check_tex(ci, sf.get_frame_texture(an, 0), "AnimatedSprite2D")
		elif ci is CPUParticles2D:
			var cp := ci as CPUParticles2D
			if cp.texture == null:
				_add("kare", "%s CPUParticles2D dokusuz" % _who(ci))
			else:
				_check_tex(ci, cp.texture, "CPUParticles2D")
		elif ci is GPUParticles2D:
			_check_tex(ci, (ci as GPUParticles2D).texture, "GPUParticles2D")
		elif ci is TextureRect:
			_check_tex(ci, (ci as TextureRect).texture, "TextureRect")
		elif ci is NinePatchRect:
			_check_tex(ci, (ci as NinePatchRect).texture, "NinePatchRect")
		elif ci is Line2D:
			_check_tex(ci, (ci as Line2D).texture, "Line2D")
		elif ci is Polygon2D:
			_check_tex(ci, (ci as Polygon2D).texture, "Polygon2D")
		elif ci is TileMapLayer:
			var ts := (ci as TileMapLayer).tile_set
			if ts:
				for i in ts.get_source_count():
					var src := ts.get_source(ts.get_source_id(i))
					if src is TileSetAtlasSource:
						_check_tex(ci, (src as TileSetAtlasSource).texture, "TileMapLayer")
		if ci is Label:
			var lb := ci as Label
			var f: Font = lb.label_settings.font if lb.label_settings and lb.label_settings.font else lb.get_theme_font("font")
			if f and (f.resource_path.contains("pixel") or (f is FontFile and (f as FontFile).antialiasing == TextServer.FONT_ANTIALIASING_NONE)):
				_add("yazi", "%s Label piksel yazı tipi '%s'" % [_who(ci), lb.text.left(12)])
			elif _nearest(_eff_filter(ci)) and lb.text != "":
				_add("suzgec", "%s Label yazı (en yakın süzgeç)" % _who(ci))
		# piksel kalıntısı: bir CanvasItem'ın kendi malzemesi ışığa piksel bantlı toon gölgelendiricisi mi
		var mat := ci.material
		if mat is ShaderMaterial and (mat as ShaderMaterial).shader and (mat as ShaderMaterial).shader.resource_path.ends_with("toon_light.gdshader"):
			_add("v1_doku", "%s toon_light (piksel bantlı ışık) malzemesi" % _who(ci))
	for k in PikselIz.kayit.keys():
		_add("iz", String(k))
	PikselIz.kayit.clear()
	_report(false)


func _report(final: bool) -> void:
	var keys := _found.keys()
	keys.sort()
	var by_cls: Dictionary = {}
	for k in keys:
		var c: String = _found[k]["sinif"]
		by_cls[c] = int(by_cls.get(c, 0)) + 1
	var line := "[piksel] TOPLAM %d (tarama %d) %s" % [keys.size(), _scans, str(by_cls)]
	if final or _scans % 30 == 0:
		print(line)
	if _out != "":
		var f := FileAccess.open(_out, FileAccess.WRITE)
		if f:
			f.store_line(line)
			for k in keys:
				f.store_line("%5d  %s" % [int(_found[k]["sayi"]), k])
