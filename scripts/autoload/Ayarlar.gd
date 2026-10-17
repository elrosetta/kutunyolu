extends Node
## Görüntü ayarları: pencere modu, çözünürlük, ölçekleme, doku kalitesi (HD paketleri), dikey eşitleme.
## Oyun 960x540 mantıksal görüntüde tasarlanır ve her pencere boyutuna ölçeklenir (canvas_items: çizim pencere
## çözünürlüğünde). Doku kalitesi 2K / 4K (ya da Otomatik'te 1440p ve üstü) gerçek yüksek çözünürlüklü doku paketini
## yükler (assets_hd/x2, x4; Data.tex): stil v2'de 2K ve 4K aynı 2 kat HD paketini kullanır. Paket dokular yüklenirken
## seçilir: değişiklik oyun yeniden başlatılınca uygulanır. Ayarlar user://ayarlar.cfg'de saklanır.

const PATH := "user://ayarlar.cfg"
const MODES := ["Pencereli", "Tam ekran", "Özel tam ekran"]
const SCALES := ["Ekranı doldur", "Keskin piksel"]
const QUALITIES := ["Otomatik", "Standart", "2K", "4K"]
const UI_SIZES := ["Normal", "Büyük"]
const FX_LEVELS := ["Tam", "Azaltılmış", "Kapalı"]
const RESOLUTIONS := [Vector2i(1280, 720), Vector2i(1366, 768), Vector2i(1600, 900), Vector2i(1920, 1080),
	Vector2i(2560, 1440), Vector2i(3200, 1800), Vector2i(3840, 2160)]

var mode := 1          # varsayılan: tam ekran (kenarsız, yerel çözünürlük)
var res_i := 3         # pencereli çözünürlük
var scale_i := 0
var quality := 0
var vsync := true
var ui_i := 0
var fx_i := 0      # kamera sarsıntısı ve ekran flaşları: 0 tam, 1 yarım + ters renk karesi yok, 2 kapalı
var hd_active := 0     # şu an etkin HD düzeyi (0 / 1 / 2)
var _test_size := Vector2i.ZERO
var hd_wanted := 0          # ayarda seçili paket; hd_active ile farklıysa yeniden başlatma gerekir
var _pack_locked := false   # ilk dokular yüklendikten sonra paket değişmez
var pack_missing := false   # HD istendi ama paket dosyaları bulunamadı (Data._init_pack)
## Otomatik: bu yükseklik ve üstünde HD paketi (1440p: 1,7 yakınlıkta ~4,5 ekran pikseli / dünya birimi > temel 4)
const AUTO_HD_H := 1400
const AUTO_4K_H := 2000


func pack_scale() -> int:
	## Etkin doku paketi çarpanı: 1 (standart), 2 (2K), 4 (4K)
	return [1, 2, 4][hd_active]


func lock_pack() -> void:
	_pack_locked = true


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
	get_tree().root.size_changed.connect(_on_resized)
	for arg in OS.get_cmdline_user_args():
		if String(arg).begins_with("--goruntu="):
			_snap(String(arg).trim_prefix("--goruntu="))
		elif String(arg).begins_with("--olcum="):
			_measure(float(String(arg).trim_prefix("--olcum=")))


func _measure(dur: float) -> void:
	## Test: --bekle=<sn> ısınmadan sonra <dur> sn boyunca kare süreleri (ort / %95 / en kötü ms), FPS ve video
	## belleği (doku / toplam) yazılır, oyun kapanır. Ör. -- --otomatik --derinlik=7 --doku=2 --pencere=2560x1440 --bekle=8 --olcum=20
	var wait := 8.0
	for arg in OS.get_cmdline_user_args():
		if String(arg).begins_with("--bekle="):
			wait = maxf(0.1, float(String(arg).trim_prefix("--bekle=")))
	await get_tree().create_timer(wait, true, false, true).timeout
	var times: Array = []
	var t0 := Time.get_ticks_usec()
	var last := t0
	while float(Time.get_ticks_usec() - t0) / 1e6 < dur:
		await RenderingServer.frame_post_draw
		var now := Time.get_ticks_usec()
		times.append(float(now - last) / 1000.0)
		last = now
	times.sort()
	var avg := 0.0
	for x in times:
		avg += x
	avg /= maxf(1.0, times.size())
	var p95: float = times[int(times.size() * 0.95)] if times.size() > 0 else 0.0
	var worst: float = times[-1] if times.size() > 0 else 0.0
	var tex_mb := RenderingServer.get_rendering_info(RenderingServer.RENDERING_INFO_TEXTURE_MEM_USED) / 1048576.0
	var vid_mb := RenderingServer.get_rendering_info(RenderingServer.RENDERING_INFO_VIDEO_MEM_USED) / 1048576.0
	print("olcum: pencere=%s hd=%d paket_doku=%d (%.2f sn) kare=%d ort=%.2fms p95=%.2fms en_kotu=%.2fms fps=%.1f doku_vram=%.0fMB toplam_vram=%.0fMB" % [str(get_tree().root.size), hd_active, int(Data.get("_pack_hits")), float(Data.get("_pack_usec")) / 1e6, times.size(), avg, p95, worst, 1000.0 / maxf(0.01, avg), tex_mb, vid_mb])
	get_tree().quit()


func _snap(path: String) -> void:
	## Test: 6 sn (ya da --bekle=<sn>) sonra ekranın kendisini PNG olarak kaydet ve çık
	var wait := 6.0
	for arg in OS.get_cmdline_user_args():
		if String(arg).begins_with("--bekle="):
			wait = maxf(0.1, float(String(arg).trim_prefix("--bekle=")))
	# seri çekim (tek açılışta birden çok kare): --seri=<adet> --aralik=<sn>; dosyalar <ad>_0.png, <ad>_1.png ...
	var count := 1
	var step := 0.25
	for arg in OS.get_cmdline_user_args():
		if String(arg).begins_with("--seri="):
			count = maxi(1, int(String(arg).trim_prefix("--seri=")))
		elif String(arg).begins_with("--aralik="):
			step = maxf(0.02, float(String(arg).trim_prefix("--aralik=")))
	await get_tree().create_timer(wait, true, false, true).timeout
	for i in count:
		if i > 0:
			await get_tree().create_timer(step, true, false, true).timeout
		await RenderingServer.frame_post_draw
		var img := get_viewport().get_texture().get_image()
		# HDR 2D görüntü alanı doğrusal renk uzayında döner: ekranda görünenle aynı olsun diye sRGB'ye çevrilir.
		# .exr uzantısı: kayıpsız doğrusal yarım kayan nokta (koyu tonlarda bantlaşma yok; dönüştürme araç tarafında).
		var exr := path.get_extension().to_lower() == "exr"
		if get_viewport().use_hdr_2d and not exr:
			if img.get_format() != Image.FORMAT_RGBA8 and img.get_format() != Image.FORMAT_RGB8:
				img.convert(Image.FORMAT_RGBA8)
			img.linear_to_srgb()
		var out := path if count == 1 else "%s_%d.%s" % [path.get_basename(), i, path.get_extension()]
		if exr:
			img.save_exr(out, false)
		else:
			img.save_png(out)
		print("goruntu: %s pencere=%s goruntu=%s hd=%d" % [out.get_file(), str(get_tree().root.size), str(img.get_size()), hd_active])
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
	var t: String = ("Otomatik: %s" % ["Standart", "2K", "4K"][hd_wanted]) if quality == 0 else QUALITIES[quality]
	if restart_needed():
		t += " *"
	return t


func restart_needed() -> bool:
	return hd_wanted != hd_active and not (pack_missing and hd_wanted > 0)


func quality_tip() -> String:
	## Ayarlar ekranı açıklaması: şu an etkin olan, seçilen ve yeniden başlatma gereği
	var names := ["Standart", "2K (HD)", "4K (HD)"]
	var t := "Otomatik: 1440p ve üstünde HD doku paketi. 2K / 4K: karakterler, yaratıklar, silahlar ve dünya 2 kat çözünürlükte yeniden çizilmiş dokularla (dünya boyu aynı, ayrıntı artar)."
	if pack_missing:
		t += " HD paketi bulunamadı: standart dokular kullanılıyor."
	else:
		t += " Şu an: %s." % names[hd_active]
	if restart_needed():
		t += " * Oyunu yeniden başlatınca: %s." % names[hd_wanted]
	return t


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
	_apply_scale()
	DisplayServer.window_set_vsync_mode(DisplayServer.VSYNC_ENABLED if vsync else DisplayServer.VSYNC_DISABLED)
	_update_hd()


func _apply_scale() -> void:
	## Ekranı doldur: 960x540 görüntü kesirli ölçekle pencereyi doldurur.
	## Keskin piksel: en yakın tam sayı kat seçilir (1080p 2x, 1440p 3x, 4K 4x) ve görüntü alanı pencereye
	## göre ayarlanır; pikseller eşit kalır, kenarlarda siyah boşluk oluşmaz.
	var win := get_tree().root
	win.content_scale_stretch = Window.CONTENT_SCALE_STRETCH_FRACTIONAL
	var base := Vector2i(960, 540)
	if scale_i == 1:
		var ws := win.size
		var f := maxi(1, roundi(float(ws.y) / base.y))
		win.content_scale_size = Vector2i(ws.x / f, ws.y / f)
	else:
		win.content_scale_size = base


func _on_resized() -> void:
	_apply_scale()
	_update_hd()


func _update_hd() -> void:
	## Doku paketi (assets_hd/x2 = 2K, x4 = 4K; stil v2'de ikisi de x2): gerçek yüksek çözünürlüklü çizimler.
	## Dokular yüklenirken seçildiği için değişiklik oyun yeniden başlatılınca uygulanır.
	## Otomatik: 1440p ve üstü → 2K, 2160p → 4K (pencereli modda pencere, tam ekranda ekran yüksekliği).
	var lv := 0
	match quality:
		0:
			var h := get_tree().root.size.y if is_inside_tree() else 1080
			if mode != 0:
				h = DisplayServer.screen_get_size().y
			lv = 2 if h >= AUTO_4K_H else (1 if h >= AUTO_HD_H else 0)
		1:
			lv = 0
		2:
			lv = 1
		3:
			lv = 2
	if not _pack_locked:
		hd_active = lv
	hd_wanted = lv


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
		5:
			ui_i = posmod(ui_i + dir, UI_SIZES.size())
		6:
			fx_i = posmod(fx_i + dir, FX_LEVELS.size())
			Game.fx_scale = [1.0, 0.5, 0.0][fx_i]
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
		["Arayüz boyutu", UI_SIZES[ui_i], true],
		["Sarsıntı ve flaş", FX_LEVELS[fx_i], true],
	]


func save() -> void:
	var c := ConfigFile.new()
	c.set_value("goruntu", "mod", mode)
	c.set_value("goruntu", "cozunurluk", res_i)
	c.set_value("goruntu", "olcek", scale_i)
	c.set_value("goruntu", "doku", quality)
	c.set_value("goruntu", "vsync", vsync)
	c.set_value("goruntu", "arayuz", ui_i)
	c.set_value("goruntu", "efekt", fx_i)
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
	ui_i = int(c.get_value("goruntu", "arayuz", ui_i))
	fx_i = int(c.get_value("goruntu", "efekt", fx_i))
	Game.fx_scale = [1.0, 0.5, 0.0][clampi(fx_i, 0, 2)]


func ui_scale() -> float:
	return 1.5 if ui_i == 1 else 1.0
