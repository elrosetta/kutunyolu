extends Node
## Görüntü ayarları: pencere modu, çözünürlük, doku kalitesi (HD paketi), dikey eşitleme.
## Oyun 960x540 mantıksal görüntüde tasarlanır ve her pencere boyutuna kesirli ölçekle oturur (canvas_items: çizim
## pencere çözünürlüğünde). Doku kalitesi 2K / 4K (ya da Otomatik'te 1440p ve üstü) gerçek yüksek çözünürlüklü doku
## paketini yükler (assets_hd/x2; Data.tex): 2K ve 4K aynı 2 kat HD paketini kullanır. Paket dokular yüklenirken
## seçilir: değişiklik oyun yeniden başlatılınca uygulanır. Ayarlar user://ayarlar.cfg'de saklanır. v30: v1 piksel
## stiline ait "Ölçekleme: Keskin piksel" (tam sayı ölçek) seçeneği kaldırıldı.
## v38: Grafik kalitesi hazır ayarları (Düşük / Orta / Yüksek / Ultra) ve alt ayarları: çizim çözünürlüğü, ışık ve parlama
## (gölgeli ışıklar, ışık sınırı, parlama, renk derecelendirme), arka plan katmanları, efekt yoğunluğu, kare sınırı. İlk
## açılışta GPU türüne göre seçilir (tümleşik: Orta, ayrık: Yüksek, OpenGL yedeği: Düşük). Eski ayarlar.cfg anahtarları aynen.

const PATH := "user://ayarlar.cfg"
const MODES := ["Pencereli", "Tam ekran", "Özel tam ekran"]
const QUALITIES := ["Otomatik", "Standart", "2K", "4K"]
const UI_SIZES := ["Normal", "Büyük"]
const FX_LEVELS := ["Tam", "Azaltılmış", "Kapalı"]
const RESOLUTIONS := [Vector2i(1280, 720), Vector2i(1366, 768), Vector2i(1600, 900), Vector2i(1920, 1080),
	Vector2i(2560, 1440), Vector2i(3200, 1800), Vector2i(3840, 2160)]

var mode := 1          # varsayılan: tam ekran (kenarsız, yerel çözünürlük)
var res_i := 3         # pencereli çözünürlük
var quality := 0
var vsync := true
var ui_i := 0
var fx_i := 0      # kamera sarsıntısı ve ekran flaşları: 0 tam, 1 yarım + ters renk karesi yok, 2 kapalı
var harita_i := 2  # v32 küçük harita boyu: 0 kapalı, 1 küçük, 2 normal, 3 büyük (HaritaUI.SIZES)
var harita_a := 1  # v32 küçük harita saydamlığı: 0 hafif, 1 orta, 2 koyu
const HARITA_BOY := ["Kapalı", "Küçük", "Normal", "Büyük"]
const HARITA_SAYDAM := ["Hafif", "Orta", "Koyu"]
## v38 grafik kalitesi (bkz. GRAFIK): hazır ayar ve alt değerleri. Işık / katman / efekt bir sonraki bölümde, çizim
## çözünürlüğü ve kare sınırı hemen, doku kalitesi yeniden başlatınca uygulanır.
const GRAFIK_AD := ["Düşük", "Orta", "Yüksek", "Ultra"]
## hazır ayar -> [çizim (0 tam, 1 yarım), doku (QUALITIES), ışık (0 az, 1 hafif, 2 tam), katman (0 az, 1 tam), efekt (0 az, 1 orta, 2 tam)]
const GRAFIK := [[1, 1, 0, 0, 0], [1, 1, 1, 1, 1], [0, 0, 2, 1, 2], [0, 2, 2, 1, 2]]
const CIZIM_AD := ["Tam", "Yarım (960x540)"]
const ISIK_AD := ["Az", "Hafif", "Tam"]
const KATMAN_AD := ["Az", "Tam"]
const EFEKT_AD := ["Az", "Orta", "Tam"]
const EFEKT_YOG := [0.5, 0.75, 1.0]
const FPS_SINIR := [0, 30, 60, 120, 144]
## ışık düzeyine göre en çok etkin sabit süs ışığı (Level.add_light; 0 = sınırsız)
const ISIK_SINIR := [14, 28, 0]
var grafik := 2       # hazır ayar (-1 = özel)
var cizim := 0
var isik := 2
var katman := 1
var efekt := 2
var fps_i := 0
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
		if String(arg).begins_with("--grafik="):
			_preset(clampi(int(String(arg).trim_prefix("--grafik=")), 0, 3))  # test (kaydedilmez)
		elif String(arg).begins_with("--g_isik="):   # test: tek alt ayar (kaydedilmez)
			isik = clampi(int(String(arg).trim_prefix("--g_isik=")), 0, 2)
		elif String(arg).begins_with("--g_katman="):
			katman = clampi(int(String(arg).trim_prefix("--g_katman=")), 0, 1)
		elif String(arg).begins_with("--g_cizim="):
			cizim = clampi(int(String(arg).trim_prefix("--g_cizim=")), 0, 1)
		elif String(arg).begins_with("--doku="):
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
		elif String(arg).begins_with("--gpu_perf"):
			add_child(load("res://tools/tests/gorsel_perf.gd").new())  # v38 görüntü / GPU başarım ölçümü
		elif String(arg).begins_with("--isik40="):
			add_child(load("res://tools/tests/isik40_cekim.gd").new())  # v40 ışık / renk çekim aracı


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
	Engine.max_fps = FPS_SINIR[clampi(fps_i, 0, FPS_SINIR.size() - 1)]
	_update_hd()


func _apply_scale() -> void:
	## 960x540 görüntü kesirli ölçekle pencereyi doldurur
	## v38 çizim çözünürlüğü Yarım: sahne 960x540'ta çizilip pencereye büyütülür (canvas_items yerine viewport kipi;
	## dünya ve arayüz düzeni aynı, piksel doldurma pencere çözünürlüğünden bağımsız). Zayıf GPU'lar için.
	var win := get_tree().root
	win.content_scale_stretch = Window.CONTENT_SCALE_STRETCH_FRACTIONAL
	win.content_scale_size = Vector2i(960, 540)
	var want := Window.CONTENT_SCALE_MODE_VIEWPORT if cizim == 1 else Window.CONTENT_SCALE_MODE_CANVAS_ITEMS
	if win.content_scale_mode != want:
		win.content_scale_mode = want


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
	## Ayarlar ekranından: satır değerini bir adım değiştir ve uygula (satırlar rows() sırasıyla; anahtar r[4])
	var rs := rows()
	if row < 0 or row >= rs.size():
		return
	var detay := false   # alt grafik ayarı değişti: hazır ayar "Özel" olabilir
	match String(rs[row][4]):
		"mod":
			mode = posmod(mode + dir, MODES.size())
		"cozunurluk":
			if mode == 0:
				res_i = posmod(res_i + dir, resolutions().size())
		"grafik":
			_preset(posmod((grafik if grafik >= 0 else 2) + dir, GRAFIK.size()))
		"cizim":
			cizim = posmod(cizim + dir, CIZIM_AD.size())
			detay = true
		"doku":
			quality = posmod(quality + dir, QUALITIES.size())
			detay = true
		"isik":
			isik = posmod(isik + dir, ISIK_AD.size())
			detay = true
		"katman":
			katman = posmod(katman + dir, KATMAN_AD.size())
			detay = true
		"efekt_yog":
			efekt = posmod(efekt + dir, EFEKT_AD.size())
			detay = true
		"fps":
			fps_i = posmod(fps_i + dir, FPS_SINIR.size())
		"vsync":
			vsync = not vsync
		"arayuz":
			ui_i = posmod(ui_i + dir, UI_SIZES.size())
		"efekt":
			fx_i = posmod(fx_i + dir, FX_LEVELS.size())
			Game.fx_scale = [1.0, 0.5, 0.0][fx_i]
		"muhur":
			# v22 Kut Mührü: açılmış kademeler arasında; bir sonraki koşuda geçerli (Game.meta)
			var n := Zorluk.muhur_acik() + 1
			Game.meta["muhur"] = posmod(Zorluk.muhur_secili() + dir, n)
			Game.save_meta()
		"harita_boy":
			harita_i = posmod(harita_i + dir, HARITA_BOY.size())
		"harita_saydam":
			harita_a = posmod(harita_a + dir, HARITA_SAYDAM.size())
	if detay:
		grafik = _preset_of()
	apply()
	save()


func _preset(i: int) -> void:
	## hazır ayarı alt değerlere uygular (GRAFIK tablosu)
	grafik = i
	var g: Array = GRAFIK[i]
	cizim = g[0]
	quality = g[1]
	isik = g[2]
	katman = g[3]
	efekt = g[4]


func _preset_of() -> int:
	## alt değerler bir hazır ayarla aynıysa onun sırası, yoksa -1 (Özel)
	for i in GRAFIK.size():
		if GRAFIK[i] == [cizim, quality, isik, katman, efekt]:
			return i
	return -1


func _auto_preset() -> int:
	## İlk açılış: GPU türüne göre. OpenGL yedeği (Vulkan yok) Düşük; tümleşik GPU Orta (1440p ve üstü ekranda da);
	## ayrık / sanal / bilinmeyen Yüksek (Otomatik doku: 1440p ve üstünde HD paketi).
	if RenderingServer.get_current_rendering_method() == "gl_compatibility":
		return 0
	var t := RenderingServer.get_video_adapter_type()
	var ad := RenderingServer.get_video_adapter_name().to_lower()
	if t == RenderingDevice.DEVICE_TYPE_CPU:
		return 0
	if t == RenderingDevice.DEVICE_TYPE_INTEGRATED_GPU or ad.contains("uhd") or ad.contains("iris") or ad.contains("hd graphics"):
		return 1
	return 2


func grafik_text() -> String:
	return GRAFIK_AD[grafik] if grafik >= 0 else "Özel"


## --- v38 grafik ayarlarının okuyucuları (Level, ParallaxBG; Gore / Blood / FX parçacık sayıları efekt_say ile) ---
func efekt_yogunluk() -> float:
	## Efekt yoğunluğu çarpanı (1 tam, 0,75 orta, 0,5 az): kan / parçacık / kıvılcım sayıları bununla çarpılabilir
	return EFEKT_YOG[clampi(efekt, 0, 2)]


func efekt_say(n: int, en_az := 1, olum := false) -> int:
	## v38 birleştirme: efekt üreticilerinin (Gore, Blood, FX) parçacık / damla SAYISI (boyut değil). Tam (Yüksek / Ultra)
	## sayıyı hiç değiştirmez. olum: ölüm patlaması daha az kısılır (0,3 + 0,7k: Az %65, Orta %82,5), öldürme hissi kalsın.
	## en_az: bunun altına inilmez (zaten küçük sayılar olduğu gibi kalır).
	var k: float = EFEKT_YOG[clampi(efekt, 0, 2)]
	if k >= 1.0 or n <= en_az:
		return n
	if olum:
		k = 0.3 + 0.7 * k
	return maxi(en_az, int(round(float(n) * k)))


func isik_golge() -> bool:
	## gölgeli nokta ışıkları (süs çıraları, ocak, Kut Kapısı): yalnızca Işık ve parlama Tam'da
	return isik >= 2


func isik_siniri() -> int:
	## bölümdeki en çok etkin sabit süs ışığı (0 = sınırsız)
	return ISIK_SINIR[clampi(isik, 0, 2)]


func parlama() -> int:
	## 0 parlama ve renk derecelendirmesi kapalı (yalnızca vinyet), 1 hafif parlama, 2 tam
	return clampi(isik, 0, 2)


func arka_katman_az() -> bool:
	## Arka plan katmanları Az: süs niteliğindeki saydam pus / hüzme / ikincil kar katmanları çizilmez
	return katman == 0


func rows() -> Array:
	## [ad, değer, etkin mi, açıklama, anahtar]
	return [
		["Görüntü", MODES[mode], true, "Pencereli, tam ekran (kenarsız) ya da özel tam ekran.", "mod"],
		["Çözünürlük", res_text(), mode == 0, "Pencereli modda pencere boyutu. Tam ekranda ekranın kendi çözünürlüğü kullanılır.", "cozunurluk"],
		["Grafik kalitesi", grafik_text(), true, "Hazır ayar: aşağıdaki çizim, doku, ışık, arka plan ve efekt ayarlarını birlikte seçer. Düşük ve Orta zayıf (tümleşik) ekran kartları içindir; Ultra HD dokuları her çözünürlükte açar.", "grafik"],
		["  Çizim çözünürlüğü", CIZIM_AD[cizim], true, "Tam: her şey pencere çözünürlüğünde çizilir (keskin). Yarım: sahne 960x540'ta çizilip büyütülür; çok daha hızlı, biraz yumuşak.", "cizim"],
		["  Doku kalitesi", quality_text(), true, quality_tip(), "doku"],
		["  Işık ve parlama", ISIK_AD[isik], true, "Tam: yumuşak gölgeli meşale ışıkları, ışık hüzmeleri, tam parlama ve film derecelendirmesi. Hafif: gölgesiz, hüzmesiz, daha az ışık, hafif parlama. Az: parlama ve derecelendirme kapalı, en az ışık. Sonraki bölümde geçerli.", "isik"],
		["  Arka plan katmanları", KATMAN_AD[katman], true, "Az: pus ve ışık hüzmesi gibi saydam ara katmanlar çizilmez (dağlar, orman, gök aynı). Sonraki bölümde geçerli.", "katman"],
		["  Efekt yoğunluğu", EFEKT_AD[efekt], true, "Kan, kıvılcım, duman ve parçacık efektlerinin sayısı (boyutları aynı). Orta ve Az daha az parçacık üretir; ölüm patlaması Az'da da en az %65 kalır.", "efekt_yog"],
		["Kare sınırı", "Sınırsız" if fps_i == 0 else "%d FPS" % FPS_SINIR[fps_i], true, "Saniyedeki en çok kare. Dikey eşitleme açıkken ekran yenilemesi zaten sınırdır; dizüstünde 60 pil ve ısı kazandırır.", "fps"],
		["Dikey eşitleme", "Açık" if vsync else "Kapalı", true, "Kare hızını ekran yenilemesine kilitler (yırtılmayı önler).", "vsync"],
		["Arayüz boyutu", UI_SIZES[ui_i], true, "Oyun içi göstergelerin boyutu. Normal: daha çok oyun alanı görünür.", "arayuz"],
		["Sarsıntı ve flaş", FX_LEVELS[fx_i], true, "Kamera sarsıntısı, darbe kareleri ve ekran flaşları. Rahatsız ediyorsa Azaltılmış ya da Kapalı seç.", "efekt"],
		["Kut Mührü (yeni koşu)", muhur_text(), Zorluk.muhur_acik() > 0, "Kut Mühürleri: Erlik Han'ı her yenişinde bir sonraki zorluk kademesi açılır (daha dayanıklı ve saldırgan düşmanlar, daha az şifa, öfkeli yaratıklar). %s. Yeni koşuda geçerli." % String(Zorluk.muhur_def(Zorluk.muhur_secili()).get("desc", "")).trim_suffix("."), "muhur"],
		["Küçük harita", HARITA_BOY[harita_i], true, "Sağ alttaki parşömen haritanın boyu (keşfettikçe açılır; Kut Taşları ve ödüller işlenir). Kapalı: yalnızca M ile tam ekran harita.", "harita_boy"],
		["Harita saydamlığı", HARITA_SAYDAM[harita_a], true, "Küçük haritanın saydamlığı: Hafif dövüşte az yer kaplar, Koyu daha okunur.", "harita_saydam"],
	]


func muhur_text() -> String:
	## v22: seçili zorluk kademesi; son bossu (Erlik Han) yendikçe bir sonraki açılır
	var s := Zorluk.muhur_secili()
	if Zorluk.muhur_acik() <= 0:
		return "Mühürsüz (Erlik Han'ı yen)"
	return "%s  (%d / %d)" % [Zorluk.muhur_adi(s), s, Zorluk.muhur_acik()]


func save() -> void:
	var c := ConfigFile.new()
	c.set_value("goruntu", "mod", mode)
	c.set_value("goruntu", "cozunurluk", res_i)
	c.set_value("goruntu", "doku", quality)
	c.set_value("goruntu", "vsync", vsync)
	c.set_value("goruntu", "arayuz", ui_i)
	c.set_value("goruntu", "efekt", fx_i)
	c.set_value("harita", "boy", harita_i)
	c.set_value("harita", "saydam", harita_a)
	# v38 grafik (eski sürümler bu bölümü yok sayar)
	c.set_value("grafik", "hazir", grafik)
	c.set_value("grafik", "cizim", cizim)
	c.set_value("grafik", "isik", isik)
	c.set_value("grafik", "katman", katman)
	c.set_value("grafik", "efekt", efekt)
	c.set_value("grafik", "fps", fps_i)
	c.save(PATH)


func _load() -> void:
	var c := ConfigFile.new()
	if c.load(PATH) != OK:
		_preset(_auto_preset())   # v38 ilk açılış: GPU'ya göre hazır ayar (kaydedilmez; ilk değişiklikte yazılır)
		return
	mode = int(c.get_value("goruntu", "mod", mode))
	res_i = int(c.get_value("goruntu", "cozunurluk", res_i))
	quality = int(c.get_value("goruntu", "doku", quality))
	vsync = bool(c.get_value("goruntu", "vsync", vsync))
	ui_i = int(c.get_value("goruntu", "arayuz", ui_i))
	fx_i = int(c.get_value("goruntu", "efekt", fx_i))
	Game.fx_scale = [1.0, 0.5, 0.0][clampi(fx_i, 0, 2)]
	harita_i = clampi(int(c.get_value("harita", "boy", harita_i)), 0, 3)
	harita_a = clampi(int(c.get_value("harita", "saydam", harita_a)), 0, 2)
	if c.has_section("grafik"):
		cizim = clampi(int(c.get_value("grafik", "cizim", cizim)), 0, CIZIM_AD.size() - 1)
		isik = clampi(int(c.get_value("grafik", "isik", isik)), 0, 2)
		katman = clampi(int(c.get_value("grafik", "katman", katman)), 0, 1)
		efekt = clampi(int(c.get_value("grafik", "efekt", efekt)), 0, 2)
		fps_i = clampi(int(c.get_value("grafik", "fps", fps_i)), 0, FPS_SINIR.size() - 1)
	else:
		# v38 öncesi ayar dosyası: kayıtlı doku kalitesi korunur, diğer grafik değerleri GPU'ya göre hazır ayardan
		var q := quality
		_preset(_auto_preset())
		quality = q
	grafik = _preset_of()


func ui_scale() -> float:
	return 1.5 if ui_i == 1 else 1.0
