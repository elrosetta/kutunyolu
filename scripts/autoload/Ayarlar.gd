extends Node
## Görüntü ayarları: pencere modu, çözünürlük, ölçekleme, doku kalitesi (HD paketleri), dikey eşitleme.
## Oyun 640x360 mantıksal çözünürlükte tasarlanır ve her pencere boyutuna ölçeklenir. Doku kalitesi
## 2K / 4K seçilince (ya da Otomatik'te 1440p / 2160p ve üstünde) gölgelendiriciler piksel sanatını
## Scale2x / Scale4x kurallarıyla büyütür (shaders/hdpix.gdshaderinc). Ayarlar user://ayarlar.cfg'de saklanır.

const PATH := "user://ayarlar.cfg"
const MODES := ["Pencereli", "Tam ekran", "Özel tam ekran"]
const SCALES := ["Ekranı doldur", "Keskin piksel"]
const QUALITIES := ["Otomatik", "Standart", "2K", "4K"]
const RESOLUTIONS := [Vector2i(1280, 720), Vector2i(1366, 768), Vector2i(1600, 900), Vector2i(1920, 1080),
	Vector2i(2560, 1440), Vector2i(3200, 1800), Vector2i(3840, 2160)]

var mode := 1          # varsayılan: tam ekran (kenarsız, yerel çözünürlük)
var res_i := 3         # pencereli çözünürlük
var scale_i := 0
var quality := 0
var vsync := true
var hd_active := 0     # şu an etkin HD düzeyi (0 / 1 / 2)
var _test_size := Vector2i.ZERO


func _ready() -> void:
	_load()
	# test / çekim: --doku=0..3 (Otomatik/Standart/2K/4K), --pencere=1920x1080 (kaydedilmez)
	for arg in OS.get_cmdline_user_args():
		if String(arg).begins_with("--doku="):
			quality = clampi(int(String(arg).trim_prefix("--doku=")), 0, 3)
		elif String(arg).begins_with("--pencere="):
			var p := String(arg).trim_prefix("--pencere=").split("x")
			mode = 0
			var want := Vector2i(int(p[0]), int(p[1]))
			_test_size = want
	apply()
	get_tree().root.size_changed.connect(_update_hd)
	for arg in OS.get_cmdline_user_args():
		if String(arg).begins_with("--goruntu="):
			_snap(String(arg).trim_prefix("--goruntu="))


func _snap(path: String) -> void:
	## Test: 2 sn sonra ekranın kendisini PNG olarak kaydet ve çık
	await get_tree().create_timer(6.0, true, false, true).timeout
	await RenderingServer.frame_post_draw
	var img := get_viewport().get_texture().get_image()
	img.save_png(path)
	print("goruntu: pencere=%s goruntu=%s hd=%d" % [str(get_tree().root.size), str(img.get_size()), hd_active])
	get_tree().quit()


func resolutions() -> Array:
	## Ekrana sığan çözünürlükler (en az bir tane)
	var scr := DisplayServer.screen_get_size()
	var out: Array = []
	for r in RESOLUTIONS:
		if r.x <= scr.x and r.y <= scr.y:
			out.append(r)
	if out.is_empty():
		out.append(RESOLUTIONS[0])
	return out


func res_text() -> String:
	if mode != 0:
		var s := DisplayServer.screen_get_size()
		return "%dx%d (ekran)" % [s.x, s.y]
	var rs := resolutions()
	var r: Vector2i = rs[clampi(res_i, 0, rs.size() - 1)]
	return "%dx%d" % [r.x, r.y]


func quality_text() -> String:
	if quality == 0:
		return "Otomatik (%s)" % ["Standart", "2K", "4K"][hd_active]
	return QUALITIES[quality]


func apply() -> void:
	var win := get_tree().root
	match mode:
		0:
			win.mode = Window.MODE_WINDOWED
			var rs := resolutions()
			res_i = clampi(res_i, 0, rs.size() - 1)
			var r: Vector2i = rs[res_i] if _test_size == Vector2i.ZERO else _test_size
			win.size = r
			var scr_pos := DisplayServer.screen_get_position()
			var scr := DisplayServer.screen_get_size()
			win.position = scr_pos + (scr - r) / 2
		1:
			win.mode = Window.MODE_FULLSCREEN
		2:
			win.mode = Window.MODE_EXCLUSIVE_FULLSCREEN
	win.content_scale_stretch = Window.CONTENT_SCALE_STRETCH_INTEGER if scale_i == 1 else Window.CONTENT_SCALE_STRETCH_FRACTIONAL
	DisplayServer.window_set_vsync_mode(DisplayServer.VSYNC_ENABLED if vsync else DisplayServer.VSYNC_DISABLED)
	_update_hd()


func _update_hd() -> void:
	## Doku kalitesi: Otomatik'te pencere yüksekliğine göre (1440p → 2K, 2160p → 4K)
	var lv := 0
	match quality:
		0:
			var h := get_tree().root.size.y
			lv = 2 if h >= 1800 else (1 if h >= 1200 else 0)
		1:
			lv = 0
		2:
			lv = 1
		3:
			lv = 2
	hd_active = lv
	RenderingServer.global_shader_parameter_set("hd_level", lv)


func change(row: int, dir: int) -> void:
	## Ayarlar ekranından: satır değerini bir adım değiştir ve uygula
	match row:
		0:
			mode = posmod(mode + dir, MODES.size())
		1:
			if mode == 0:
				res_i = posmod(res_i + dir, resolutions().size())
		2:
			scale_i = posmod(scale_i + dir, SCALES.size())
		3:
			quality = posmod(quality + dir, QUALITIES.size())
		4:
			vsync = not vsync
	apply()
	save()


func rows() -> Array:
	## [ad, değer, etkin mi]
	return [
		["Görüntü", MODES[mode], true],
		["Çözünürlük", res_text(), mode == 0],
		["Ölçekleme", SCALES[scale_i], true],
		["Doku kalitesi", quality_text(), true],
		["Dikey eşitleme", "Açık" if vsync else "Kapalı", true],
	]


func save() -> void:
	var c := ConfigFile.new()
	c.set_value("goruntu", "mod", mode)
	c.set_value("goruntu", "cozunurluk", res_i)
	c.set_value("goruntu", "olcek", scale_i)
	c.set_value("goruntu", "doku", quality)
	c.set_value("goruntu", "vsync", vsync)
	c.save(PATH)


func _load() -> void:
	var c := ConfigFile.new()
	if c.load(PATH) != OK:
		return
	mode = int(c.get_value("goruntu", "mod", mode))
	res_i = int(c.get_value("goruntu", "cozunurluk", res_i))
	scale_i = int(c.get_value("goruntu", "olcek", scale_i))
	quality = int(c.get_value("goruntu", "doku", quality))
	vsync = bool(c.get_value("goruntu", "vsync", vsync))
