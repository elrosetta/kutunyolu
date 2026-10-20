class_name HUD
extends Control
## Piksel arayüz (PixUI): can, şişe, altın, Kut, ongun rozetleri, silah yuvaları (ongun şeritli), Kut göstergesi,
## yerdeki eşya kartı (karşılaştırmalı), yuva seçimi, Kut Tomarı seçimi (v23; eski tılsım), başlık / hikâye / ölüm / bölüm sonu,
## Umay / Demirci / Ozan ekranları ve duraklatma.

var main: Node
var level: Node
var mode := "title"
var intro_i := 0
var _t := 0.0
var _card_t := 0.0
var sel := 0
var flash_msg := ""
var flash_t := 0.0
var ozan_i := 0
var ad_id := ""
var ad_t := 0.0
var _usul_flash := 0.0
var _last_streak := 0
var slot_opts: Array = []
var _open_t := 1.0
var _hp_lag := -1.0
var _kut_pulse := 0.0
var _last_mode := ""
var _ducked := false
var tuccar_onay := false          # v24 pazar: seçili mal için "satın al?" onayı açık
var demirci_son: Dictionary = {}  # v24: Demirci'nin az önce dövüp verdiği eşya (kart gösterilir)
var sanat_ogretmen := false       # v27: sanat ekranı Alp Ata'dan mı açıldı (öğretme), yoksa duraklatmadan mı (yalnız kuşanma)
## v32 Bengisu Usta ekranı (Main._usta_*): adım 0 silah, 1 hizmet, 2 seçenek (nakış adayı / unsur), 3 sonuç kartı
var usta_adim := 0
var usta_slot := ""
var usta_hid := ""
var usta_secs: Array = []
var usta_sonuc: Dictionary = {}
var usta_onay := false
var usta_damga_t := 0.0
## Öğretici (v15): mekanikler ilk karşılaşıldığında bağlamsal ipucu kartı; her ipucu en çok 3 koşuda gösterilir
var _tut_id := ""
var _tut_t := 0.0
var _tut_txt: Array = []
var _tut_keys: Array = []
var _tut_shown_run: Dictionary = {}
const TUT := {
	"don_ruh": [[["dokun", "ruhu em"]], "Seçkin düşman mor bir ruh bıraktı. Dokunup emersen onun kılığına girebilirsin."],
	"don_hazir": [[["G", "don değiştir"]], "Emdiğin ruh hazır: 10 sn boyunca o yaratığın kılığına gir ve hamle takımını kullan (kurt: atılış · dev: çakma · kanat: uçuş · büyücü: büyü)."],
	"agir": [[["J", "basılı tut: ağır vuruş"], ["bekle+J", "bitiriş"]], "Her silahın kendi zinciri var. İki vuruştan sonra kısa bekleyip J: silahın özel bitirişi. J'yi basılı tut: şarjlı ağır vuruş."],
	"usul": [[["J", "vuruşa denk"]], "Müzik aksak usulde çalıyor (sağdaki ölçer). Saldırıyı vuruşa denk getirirsen hasar artar, seri Kut verir."],
	"kacis": [[["L", "son anda yuvarlan"]], "Kusursuz Kaçış: darbenin isabet edeceği an yuvarlanırsan zaman yavaşlar ve sıradaki vuruşun kesin kritik olur."],
	# v19 dövüş
	"yanki": [[["J", "isabet anında"]], "Kut Yankısı: vuruş oturunca elde altın halka belirir; o an yeniden bas. Sıradaki vuruş hızlanır, altın bir yankı kesiği gelir. Üç yankı: Kut Mührü. Erken basma!"],
	"infaz": [[["J", "kızıl mühürlü düşmana"]], "Kut Alma: duruşu kırılmış ya da sersemlemiş, canı azalmış düşmanın başında kızıl mühür var. Yakınken saldır: tek hamlede infaz, can ve Kut kazanırsın."],
	"carpisma": [[["J", "darbesine doğru savur"]], "Çarpışma: düşmanın darbesi ya da mermisi savuruşunun ilk anında bıçağına değerse karşılanır. Saldıran sersemler, sıradaki vuruşun kesin kritik."],
	# v24 tüccar
	"tuccar": [[["W", "alışveriş"]], "Bezirgân Sartak: altınla silah, kalkan, teçhizat, Umay Sütü ve bazen Kut Tomarı satar. Fiyatlar derinlikle artar, malları altınla yenileyebilirsin. Altın ölünce yiter: biriktir ve harca!"],
	# v27 savaş sanatları
	"sanat": [[["T", "savaş sanatı"], ["Esc → T", "sanat seç"]], "Alp Nişanı hazır: T ile kuşandığın savaş sanatını kullan (sağ altta tamga ve taneler). Nişan isabetle, öldürerek, çarpışma ve kusursuz kaçışla dolar. Yeni sanatları yurtta Alp Ata öğretir; Sanat Tomarları da bulunur."],
	# v32 konak
	"konak": [[["W", "ocak / usta"]], "Konak: kervan seninle yol alıyor. Ateşin yanından geçince taşıdığın Kut Umay'a ulaşır. Bengisu Usta altınla silahına nakış (ek özellik) vurur, nakışları yeniden döver, unsur aşılar, kaliteyi yükseltir; Kut Mührü ucuz bir kumardır. Sağdaki kapı derine indirir."],
	# v32 harita ve Kut Taşı
	# v34 Kahraman İnişi
	"kahraman": [[["S+Boşluk", "havada: kahraman inişi"]], "Kahraman İnişi: havadayken S'ye basılı tutup Boşluk'a bas. Yere çakılır, çevredeki düşmanları şok dalgasıyla sersemletip savurursun; ne kadar yüksekten, o kadar güçlü. Çok yüksekten öylece düşersen kısa sersemlersin, inişle hiç sersemlemezsin."],
	"kut_tasi": [[["M", "harita"], ["W", "taşın dibinde"]], "Kut Taşı: yanından geçtiğin taşlar haritaya işlenir. Bölüm dallanır ve çıkmazlarla biter: çıkmazda kalınca M ile haritayı aç, bulduğun bir taşı seç, Boşluk ile ışınlan (1 sn Kut'a bağlanırsın; darbe alırsan bozulur)."],
}
var back_mode := "title"   # ayarlar ekranı kapanınca dönülecek mod

## v23: yan teçhizat E / R (eskiden U / I); etkileşim W / ↑ dokunuşu (v25: Üç Âlem ve T tuşu kaldırıldı)
const SLOT_KEYS := {"melee": "J", "second": "K", "g1": "E", "g2": "R"}
const KEY_ETKILES := "W"
const SLOT_NAMES := {"melee": "1. silah", "second": "2. silah", "g1": "1. teçhizat", "g2": "2. teçhizat"}
const CAT_TXT := {"weapons": "Silah", "shields": "Kalkan", "gadgets": "Teçhizat"}
const ONGUN_KEYS := ["kurt", "kartal", "ayi"]


func _ready() -> void:
	process_mode = Node.PROCESS_MODE_ALWAYS
	set_anchors_preset(Control.PRESET_FULL_RECT)
	mouse_filter = Control.MOUSE_FILTER_IGNORE
	texture_filter = CanvasItem.TEXTURE_FILTER_NEAREST
	# v2 mürekkep arayüzü: vektör yazı + boyalı dokular, doğrusal süzgeç (InkUI)
	texture_filter = CanvasItem.TEXTURE_FILTER_LINEAR_WITH_MIPMAPS
	InkUI.setup()


func _process(delta: float) -> void:
	_t += delta
	_test_hook()
	_card_t += delta
	flash_t -= delta
	_open_t = minf(1.0, _open_t + delta * 6.0)
	_kut_pulse = maxf(0.0, _kut_pulse - delta)
	ad_t += delta
	_usul_flash = maxf(0.0, _usul_flash - delta * 3.0)
	_tut_tick(delta)
	usta_damga_t += delta
	if mode != _last_mode:
		if mode in ["tilsim", "slot", "umay", "demirci", "ozan", "dead", "done", "ad", "tuccar", "sanat", "usta"]:
			_open_t = 0.0
		_last_mode = mode
	# menülerde ses kısılır (Ses.menu_duck varsa)
	var menu := mode != "play" or get_tree().paused
	if menu != _ducked:
		_ducked = menu
		if Ses.has_method("menu_duck"):
			Ses.call("menu_duck", menu)
	queue_redraw()


## Arayüz testi (yalnızca komut satırı): -- --arayuz=intro|ozan|done|ad|kombo|hasar|flash|ipucu|dusuk[,...]
## (--ekran=oyun ile birlikte; 2,5 sn sonra uygulanır). Ekran görüntüsü için Ayarlar --goruntu / --bekle.
var _test_ops: Array = []
var _test_done := false
var _test_dmg_t := 0.0
var _test_frames := 0


func _test_hook() -> void:
	if _test_done and _test_ops.is_empty():
		return
	if not _test_done:
		_test_done = true
		for a in OS.get_cmdline_user_args():
			if String(a).begins_with("--arayuz="):
				_test_ops = Array(String(a).trim_prefix("--arayuz=").split(","))
		if _test_ops.is_empty():
			return
	if level == null or level.player == null:
		return
	_test_frames += 1
	if _test_frames < 45:
		return
	var pl: Node = level.player
	for op in _test_ops.duplicate():
		match String(op):
			"intro":
				mode = "intro"
				intro_i = 1
				get_tree().paused = true
			"ozan":
				ozan_i = 3
				mode = "ozan"
				get_tree().paused = true
			"done":
				mode = "done"
				get_tree().paused = true
			"ad":
				ad_id = String(Adlar.ADLAR.keys()[2])
				ad_t = 0.0
				mode = "ad"
				get_tree().paused = true
			"flash":
				flash_msg = "Ayaz Kılıcı parşömeni bulundu"
				flash_t = 99.0
			"ipucu":
				_tut_show("agir", true)
				_tut_t = 6.0
			"dusuk":
				Game.run["hp"] = 21
			"kombo":
				pl.combo_n = 27
				pl.combo_t = 2.3
				continue  # her karede
			"hasar":
				_test_dmg_t -= get_process_delta_time()
				if _test_dmg_t <= 0.0:
					_test_dmg_t = 0.35
					var p0: Vector2 = pl.global_position + Vector2(40, -40)
					FX.number(p0 + Vector2(randf_range(-20, 20), 0), randf_range(8, 60), false)
					FX.number(p0 + Vector2(60, -10), randf_range(120, 260), true)
					FX.text(p0 + Vector2(-70, -30), "SAVUŞTURMA", Color(1.0, 0.85, 0.4))
				continue
		_test_ops.erase(op)


func _tut_show(id: String, force := false) -> void:
	## İpucu kartını göster: koşuda bir kez, kalıcı olarak en çok 3 kez (force: her koşuda)
	if _tut_id != "" or _tut_shown_run.has(id):
		return
	if not force and Game.learned(id) >= 3:
		return
	_tut_shown_run[id] = true
	# test koşuları (--ekran / --otomatik) sayacı kalıcı artırmaz: oyuncunun ipuçları tükenmesin
	var test_run := false
	for x in OS.get_cmdline_user_args():
		if String(x) == "--otomatik" or String(x).begins_with("--ekran="):
			test_run = true
	if not test_run:
		Game.learn(id)
	_tut_id = id
	_tut_t = 7.5
	var d: Array = TUT[id]
	_tut_keys = d[0]
	_tut_txt = PixUI.wrap(String(d[1]), 300)
	Ses.play("ui_ac", -8.0)


func _tut_tick(delta: float) -> void:
	if _tut_t > 0.0:
		_tut_t -= delta
		if _tut_t <= 0.0:
			_tut_id = ""
	if mode != "play" or get_tree().paused or Game.run.is_empty() or level == null or level.player == null:
		return
	var pl: Node = level.player
	if level.hub:
		return
	if level.konak:
		_tut_show("konak")   # v32: ilk konakta kervan ipucu
		return
	# tetikleyiciler (öncelik sırasıyla)
	if pl.don_kind != "" and not pl.don_on:
		_tut_show("don_hazir")
	if "perfect_t" in pl and float(pl.perfect_t) > 1.3:
		_tut_show("kacis")
	if _tut_id == "" and float(Game.run.get("time", 0.0)) > 14.0 and not Game.run["slots"].get("melee", {}).is_empty():
		_tut_show("agir")
	if _tut_id == "" and float(Game.run.get("time", 0.0)) > 40.0 and Ses.has_method("usul_now") and not Ses.usul_now().is_empty():
		_tut_show("usul")
	# v19: Kut Yankısı (ilk zincirlerden sonra), Çarpışma (ilk çarpışmada), Kut Alma (mühürlü düşman yakında)
	if _tut_id == "" and "v19_stats" in pl and Engine.get_process_frames() % 10 == 0:
		if int(pl.v19_stats.get("carpisma", 0)) > 0:
			_tut_show("carpisma")
		elif int(pl.combo_n) >= 4 and float(Game.run.get("time", 0.0)) > 20.0:
			_tut_show("yanki")
		for e in get_tree().get_nodes_in_group("dusman"):
			if is_instance_valid(e) and e.has_method("exec_ok") and e.global_position.distance_to(pl.global_position) < 140.0 and e.exec_ok():
				_tut_show("infaz")
				break
	# dünya nesneleri: don ruhu
	for p in level.pickups:
		if not is_instance_valid(p):
			continue
		if p.kind == "don" and p.global_position.distance_to(pl.global_position) < 150.0:
			_tut_show("don_ruh")
	if level.get("bezirgan") != null and level.bezirgan.global_position.distance_to(pl.global_position) < 260.0:
		_tut_show("tuccar")
	if _tut_id == "" and "sanat" in pl and pl.sanat != null and pl.sanat.hazir() and float(Game.run.get("time", 0.0)) > 8.0:
		_tut_show("sanat")   # v27
	if _tut_id == "" and "_air_top" in pl and not pl.is_on_floor() and float(pl.hero_t) < 0.0 and pl.global_position.y - float(pl._air_top) > 120.0:
		_tut_show("kahraman")   # v34: ilk uzun düşüşte


func _draw_tut(vp: Vector2) -> void:
	## İpucu kartı: üstte ortada, tuş rozetleri + sarılmış metin; girişte kayar, sonda solar
	if _tut_id == "":
		return
	var a := clampf(minf(_tut_t * 2.0, (7.5 - _tut_t) * 4.0), 0.0, 1.0)
	var slide := (1.0 - clampf((7.5 - _tut_t) * 4.0, 0.0, 1.0)) * -12.0
	var w := 324.0
	var h := 22.0 + _tut_txt.size() * 10.0
	var x := roundf((vp.x - w) / 2.0)
	var y := 34.0 + slide
	PixUI.fancy_panel(self, Rect2(x, y, w, h), Color(PixUI.GOLD, a), Color(PixUI.INK2, PixUI.INK2.a * a))
	var kx := x + 8.0
	for k in _tut_keys:
		PixUI.key_cap(self, Vector2(kx, y + 5), k[0], Color(PixUI.GOLD, a))
		kx += PixUI.key_w(k[0]) + 3.0
		PixUI.text(self, Vector2(kx, y + 5), k[1], Color(PixUI.TEXT, a))
		kx += PixUI.width(k[1]) + 12.0
	var ty := y + 18.0
	for l in _tut_txt:
		PixUI.text(self, Vector2(x + 8, ty), l, Color(PixUI.DIM.lightened(0.15), a), 1, HORIZONTAL_ALIGNMENT_LEFT, -1.0, 0)
		ty += 10.0


func _draw_world_marks(vp: Vector2, pl: Node) -> void:
	## Dünya işaretleri: don ruhu
	if level.hub or level.boss_id != "":
		return
	var xf := get_viewport().get_canvas_transform()
	var us: float = Ayarlar.ui_scale()
	var bob := roundf(sin(_t * 4.0) * 2.0)
	for p in level.pickups:
		if is_instance_valid(p) and p.kind == "don" and p.global_position.distance_to(pl.global_position) < 220.0:
			var sp: Vector2 = (xf * p.global_position) / us
			PixUI.text(self, Vector2(sp.x - 60, sp.y - 26 + bob), "ruhu em", DonForm.COL, 1, HORIZONTAL_ALIGNMENT_CENTER, 120, 2)


func open_anim() -> void:
	_open_t = 0.0


func kut_pulse() -> void:
	_kut_pulse = 0.4


func _ease_open() -> float:
	var u := clampf(_open_t, 0.0, 1.0)
	return 1.0 - pow(1.0 - u, 3.0)


func _up(s: String) -> String:
	## Büyük harf: vektör yazıda Türkçe kuralı (i -> İ)
	return InkHUD.tr_upper(s)


func _blink(speed := 3.0) -> float:
	return 0.55 + 0.45 * sin(_t * speed)


func _dim(vp: Vector2, a := 0.72, col := Color(0.02, 0.015, 0.04)) -> void:
	draw_rect(Rect2(Vector2.ZERO, vp), Color(col, a * _ease_open()))
	InkUI.vignette(self, vp, 0.85 * _ease_open())


func _title(vp: Vector2, y: float, s: String, col := PixUI.GOLD, sub := "") -> void:
	var slide := (1.0 - _ease_open()) * -10.0
	InkHUD.title_wash(self, vp, y + slide, sub != "", _ease_open())
	PixUI.text(self, Vector2(0, y + slide), s, col, 2, HORIZONTAL_ALIGNMENT_CENTER, vp.x, 2)
	var tw := PixUI.width(s, 2)
	var x0 := (vp.x - tw) / 2.0
	PixUI.horn(self, Vector2(x0 - 14, y + slide + 8), col, -1)
	PixUI.horn(self, Vector2(x0 + tw + 8, y + slide + 8), col, 1)
	if sub != "":
		PixUI.text(self, Vector2(0, y + 26 + slide), sub, PixUI.TEXT, 1, HORIZONTAL_ALIGNMENT_CENTER, vp.x)


func _hint(vp: Vector2, items: Array, y := -1.0) -> void:
	## Alt bilgi satırı: [[tuş, açıklama], ...] tuş rozetleriyle
	var total := 0.0
	for it in items:
		total += PixUI.key_w(it[0]) + 3.0 + PixUI.width(it[1]) + 12.0
	total -= 12.0
	var x := roundf((vp.x - total) / 2.0)
	var yy := vp.y - 22.0 if y < 0.0 else y
	for it in items:
		PixUI.key_cap(self, Vector2(x, yy), it[0])
		x += PixUI.key_w(it[0]) + 3.0
		PixUI.text(self, Vector2(x, yy), it[1], Color(PixUI.TEXT, 0.85))
		x += PixUI.width(it[1]) + 12.0


const MENU_SCALE := 1.5  # menüler 640x360 tasarımında; 960x540 görüntüde 1,5 kat (1080p'de 3x, 4K'da 6x: keskin)


func _menu_vp() -> Vector2:
	## Menü ekranları: 1,5 kat ölçekli çizim, tasarım alanı ~640x360
	draw_set_transform(Vector2.ZERO, 0.0, Vector2.ONE * MENU_SCALE)
	InkUI.den = 3.0
	return get_viewport_rect().size / MENU_SCALE


func _hud_vp() -> Vector2:
	## Oyun içi HUD: Arayüz boyutu ayarına göre 1x (Normal) ya da 1,5x (Büyük)
	var s: float = Ayarlar.ui_scale()
	draw_set_transform(Vector2.ZERO, 0.0, Vector2.ONE * s)
	InkUI.den = 4.0 / s
	return get_viewport_rect().size / s


func _draw() -> void:
	var vp := _menu_vp()
	if mode == "ayarlar":
		if back_mode == "title" or Game.run.is_empty() or level == null or level.player == null:
			_draw_title(vp)
		else:
			_draw_hud(_hud_vp())
			vp = _menu_vp()
		_draw_settings(vp)
		return
	match mode:
		"title":
			_draw_title(vp)
			return
		"intro":
			_draw_intro(vp)
			return
		"demirci":
			_draw_demirci(vp)
			return
		"umay":
			_draw_umay(vp)
			return
		"ozan":
			_draw_ozan(vp)
			return
		"ad":
			_draw_ad(vp)
			return
	if Game.run.is_empty() or level == null or level.player == null:
		return
	var paused_play := mode == "play" and get_tree().paused
	if _card_t < 4.0 and mode == "play" and not paused_play:
		_draw_banner(vp)
	_draw_hud(_hud_vp())
	vp = _menu_vp()
	match mode:
		"dead":
			_draw_dead(vp)
		"done":
			_draw_done(vp)
		"tilsim":
			_draw_tilsim(vp)
		"slot":
			_draw_slot(vp)
		"tuccar":
			_draw_tuccar(vp)
		"usta":
			_draw_usta(vp)
		"sanat":
			_draw_sanat(vp)
		"harita":
			HaritaUI.full(self, vp, level, sel, _t, float(level.isin_t))   # v32 tam ekran harita
		"play":
			if get_tree().paused:
				_draw_pause(vp)


func _draw_banner(vp: Vector2) -> void:
	## Bölüm girişi: büyük ad, ince süslü çizgiler
	var a := clampf(minf(_card_t * 2.0, (4.0 - _card_t) * 1.5), 0.0, 1.0)
	var bm: Dictionary = level.biome
	var title: String
	var sub: String
	var col: Color
	if level.hub:
		title = "ULU KAYIN YURDU"
		sub = "Kut'unu Umay Ana'ya götür  ·  Demirci parşömen döver  ·  Alp Ata sanat öğretir  ·  kapı derine indirir"
		col = Color(0.6, 1.0, 1.0)
	elif level.konak:
		# v32: konak bir sonraki derinliğin eşiğinde
		title = "KONAK · %s" % _up(String(bm.get("name", "")))
		sub = "%d. derinliğin eşiği  ·  ocak Kut'u Umay'a ulaştırır  ·  Bengisu Usta silah nakışlar%s  ·  kapı derine indirir" % [int(Game.run["depth"]), "  ·  Sartak'ın kervanı burada" if level.get("bezirgan") != null else ""]
		col = Color(0.55, 1.0, 0.85)
	else:
		title = _up(String(bm.get("name", "Kararan Ötüken")))
		sub = "%d. derinlik  ·  %s" % [int(Game.run["depth"]), String(bm.get("sub", ""))]
		if level.get("bezirgan") != null:
			sub += "  ·  Bezirgân Sartak'ın kervanı bu yolda"   # v24
		col = PixUI.GOLD
	InkHUD.banner(self, vp, title, sub, col, a)


# ------------------------------------------------------------------ oyun içi
func _draw_hud(vp: Vector2) -> void:
	var R: Dictionary = Game.run
	var pl: Node = level.player
	# ---- can çubuğu
	var hp := float(R["hp"])
	var mhp := float(R["max_hp"])
	var hpk := clampf(hp / mhp, 0.0, 1.0)
	if _hp_lag < 0.0:
		_hp_lag = hpk
	_hp_lag = hpk if hpk > _hp_lag else lerpf(_hp_lag, hpk, 0.04)
	var bx := 8.0
	var y3 := 0.0
	y3 = InkHUD.top_left(self, R, hp, mhp, hpk, _hp_lag, _t, _kut_pulse)
	# ---- silah ve teçhizat yuvaları
	var y0 := vp.y - 40.0
	var sx := 8.0
	for key in ["melee", "second", "g1", "g2"]:
		if key == "g1":
			sx += 6.0
		_draw_slot_box(Rect2(sx, y0, 46, 30), key, pl)
		_draw_cephane(Rect2(sx, y0, 46, 30), key, pl)   # v25: çok oklu yayın atış hakları
		sx += 50.0
	_draw_hiz_yuk(pl, y0)   # v20 Kızışma / ivme yükleri (yakın silah yuvasının üstünde)
	# ---- Kut göstergesi
	var kx := sx + 16.0
	var ky := y0 + 15.0
	var kk: float = pl.kut / 100.0
	var full_k := kk >= 1.0
	var acol := PixUI.KUT if not full_k else Color(0.8, 1.0, 1.0, 0.6 + 0.4 * sin(_t * 8.0))
	InkHUD.ring(self, Vector2(kx, ky), kk, acol, "kurt", PixUI.KUT if full_k else Color(PixUI.KUT, 0.5), "F", PixUI.KUT, full_k)
	if pl.wolf_t > 0.0:
		var wx := vp.x / 2.0 - 70.0
		PixUI.panel(self, Rect2(wx, 30, 140, 26), Color(0.4, 0.85, 1.0))
		PixUI.text(self, Vector2(wx, 32), "BOZKURT  %.1f" % pl.wolf_t, Color(0.7, 1.0, 1.0), 1, HORIZONTAL_ALIGNMENT_CENTER, 140, 1)
		PixUI.bar(self, Rect2(wx + 6, 46, 128, 4), clampf(pl.wolf_t / 9.0, 0.0, 1.0), Color(0.6, 0.95, 1.0))
		PixUI.text(self, Vector2(0, 60), "J ısır  ·  K / Shift sıçra  ·  F ulu", Color(0.6, 0.9, 1.0), 1, HORIZONTAL_ALIGNMENT_CENTER, vp.x)
	# ---- kombo sayacı (sağ, ortanın biraz üstü)
	if pl.combo_n >= 3:
		var rk_name := ""
		var rk_col := Color(0.95, 0.92, 0.85)
		for i in pl.COMBO_RANKS.size():
			if pl.combo_n >= int(pl.COMBO_RANKS[i][0]):
				rk_name = pl.COMBO_RANKS[i][1]
				rk_col = pl.COMBO_RANKS[i][2]
		InkHUD.combo(self, vp, pl, rk_name, rk_col, _t)
	_draw_v12(vp, pl, kx, y0)
	if pl.wolf_t <= 0.0 and not pl.don_on:
		SanatUI.hud(self, Vector2(kx + 72.0, y0 + 15.0), pl, _t)   # v27 savaş sanatı halkası (T)
	# ---- boss can çubuğu
	if level.boss != null and is_instance_valid(level.boss) and not level.boss.dead and level.boss.state != "intro":
		InkHUD.boss_bar(self, vp, level.boss._label.text, clampf(level.boss.hp / level.boss.max_hp, 0.0, 1.0), _t, level.boss)
	# ---- lütuflar
	var lut: Array = R.get("lutuf", [])
	if not lut.is_empty():
		var lx := bx
		var ly := y3 + 17.0
		for id in lut:
			var l: Array = Game.LUTUF[id]
			var lc := Color(l[2][0], l[2][1], l[2][2])
			var w2 := PixUI.width(String(l[0])) + 10.0
			PixUI.panel(self, Rect2(lx, ly, w2, 12), lc.darkened(0.2), PixUI.INK)
			draw_circle(Vector2(lx + 5, ly + 6), 2.0, lc, true, -1.0, true)
			PixUI.text(self, Vector2(lx + 9, ly + 1), String(l[0]), lc.lightened(0.2), 1, HORIZONTAL_ALIGNMENT_LEFT, -1.0, 0)
			lx += w2 + 3.0
	# ---- sağ üst: biyom, derinlik, süre
	var place: String = ("Ulu Kayın Yurdu") if level.hub else (("Konak · " if level.konak else "") + String(level.biome.get("name", "Kararan Ötüken")))
	var tm0 := float(R["time"])
	var mh := ("%d. mühür · " % Zorluk.muhur()) if Zorluk.muhur() > 0 else ""   # v22 Kut Mührü
	InkHUD.place(self, vp, place, "%s%d. derinlik · %d:%02d · %d" % [mh, int(R.get("depth", 1)), int(tm0 / 60.0), int(tm0) % 60, int(R["kills"])], PixUI.GOLD if not level.hub else Color(0.6, 1.0, 1.0))
	# ---- v32 küçük harita (sağ alt; parşömen, sis, Kut Taşları): dövüşü kalabalıklaştırmasın diye boss / yurtta yok
	if mode == "play" and not get_tree().paused and level.get("harita") != null and not level.hub and level.boss_id == "":
		HaritaUI.minimap(self, vp, level, _t)
	# ---- öğretici ve dünya işaretleri
	if mode == "play" and not get_tree().paused:
		_draw_world_marks(vp, pl)
		_draw_ground_dps(pl)
		_draw_tut(vp)
		if level.get("isin_t") != null and float(level.isin_t) > 0.0:
			# ışınlanma kanalı: oyuncunun üstünde dolan halka
			var sp2: Vector2 = (get_viewport().get_canvas_transform() * (pl.global_position + Vector2(0, -58))) / Ayarlar.ui_scale()
			InkUI.ring(self, sp2, 9.0, 1.0 - float(level.isin_t) / float(level.ISIN_SURE), HaritaUI.KUT)
			PixUI.text(self, Vector2(sp2.x - 60, sp2.y - 22), "Kut'a bağlanıyor", HaritaUI.KUT, 1, HORIZONTAL_ALIGNMENT_CENTER, 120, 2)
	# ---- kısa mesaj
	if flash_t > 0.0 and flash_msg != "" and mode == "play":
		var a := clampf(flash_t, 0.0, 1.0)
		var fw := PixUI.width(flash_msg) + 16.0
		# v32: ipucu kartı açıksa ileti kartın altına iner (konak / Kut Taşı kartı iletiyle aynı anda çıkıyor, üst üste biniyordu)
		var fy := 72.0
		if _tut_id != "":
			fy = maxf(fy, 34.0 + 22.0 + _tut_txt.size() * 10.0 + 4.0)
		PixUI.panel(self, Rect2((vp.x - fw) / 2.0, fy, fw, 15), Color(PixUI.GOLD, a), Color(PixUI.INK, PixUI.INK.a * a))
		PixUI.text(self, Vector2(0, fy + 1.0), flash_msg, Color(PixUI.GOLD, a), 1, HORIZONTAL_ALIGNMENT_CENTER, vp.x)
	# ---- yerdeki eşya
	if mode != "play" or get_tree().paused:
		return
	var p: Node = level.nearest_item(pl.global_position + Vector2(0, -10))
	if p == null and level.get("bezirgan") != null and level.bezirgan.near:
		# W balonunun üstü (dünya biriminde: ad -101, balon -116; v32: söz varsa onun üstü)
		var dy_b := -146.0 if String(level.bezirgan.get("soz")) != "" else -132.0
		var spb: Vector2 = (get_viewport().get_canvas_transform() * (level.bezirgan.global_position + Vector2(0, dy_b))) / Ayarlar.ui_scale()
		_world_prompt(spb, KEY_ETKILES, "Bezirgân: alışveriş (%d altın)" % int(R["gold"]))
	elif p == null and level.konak:
		for n in level.npcs:
			if n.id == "usta" and n.near:
				var spu: Vector2 = (get_viewport().get_canvas_transform() * (n.global_position + Vector2(0, -146))) / Ayarlar.ui_scale()
				_world_prompt(spu, KEY_ETKILES, "Bengisu Usta: silah nakışı (%d altın)" % int(R["gold"]))
	if p and p.kind == "tilsim":
		var sp0: Vector2 = p.get_global_transform_with_canvas().origin / Ayarlar.ui_scale()
		_world_prompt(sp0 + Vector2(0, -34), KEY_ETKILES, "Kut Tomarını oku")
	elif p and p.kind == "lutuf":
		var sp1: Vector2 = p.get_global_transform_with_canvas().origin / Ayarlar.ui_scale()
		_world_prompt(sp1 + Vector2(0, -58), KEY_ETKILES, "Tanrı sunağı: lütuf dile")
	elif p == null and level.get("harita") != null and level.tasi_yakin() >= 0 and float(level.isin_t) <= 0.0:
		# v32: Kut Taşı'nın dibinde W harita / hızlı ışınlanma
		var ks: Node = level.tasi[level.tasi_yakin()]
		var sp3: Vector2 = (get_viewport().get_canvas_transform() * (ks.global_position + Vector2(0, -66))) / Ayarlar.ui_scale()
		_world_prompt(sp3, KEY_ETKILES, "Kut Taşı: haritadan ışınlan")
	elif p and not p.item.is_empty():
		var opts: Array = level.slot_options(p.item)
		var nat: String = level.natural_slot(p.item)
		var tgt := nat
		var free := false
		for sl in [nat] + opts:
			if R["slots"].get(sl, {}).is_empty():
				tgt = sl
				free = true
				break
		var cur: Dictionary = {} if free else R["slots"].get(nat, {})
		var ch := _card_h(p.item)
		var cy0 := 66.0
		_draw_card(p.item, Vector2(vp.x - 198, cy0), "YERDEKİ", cur)
		var sp: Vector2 = p.get_global_transform_with_canvas().origin / Ayarlar.ui_scale()
		var pr := "Al" if free else "Yuva seç"
		_world_prompt(sp + Vector2(0, -38), KEY_ETKILES, pr)
		var note := ("İki yuva da dolu: %s ile hangisini değiştireceğini seç." % KEY_ETKILES) if not free else "Boş yuvaya gider: %s [%s]" % [SLOT_NAMES[tgt], SLOT_KEYS[tgt]]
		var ny := cy0 + ch + 10.0
		for l in PixUI.wrap(note, 186):
			PixUI.text(self, Vector2(vp.x - 196, ny), l, PixUI.DIM, 1, HORIZONTAL_ALIGNMENT_LEFT, -1.0, 2)
			ny += 10


func _draw_ground_dps(pl: Node) -> void:
	## v23: yerdeki silahların üstünde SnH (tomar statı ve oyuncunun gücüyle) ve kuşanılan silaha göre ▲ / ▼;
	## en yakın eşyanın büyük kartı ayrıca çizilir. Yalnızca yakındakiler (ekran kalabalık olmasın).
	var near: Node = level.nearest_item(pl.global_position + Vector2(0, -10))
	for p in level.pickups:
		if not is_instance_valid(p) or p.kind != "item" or p == near or p.item.is_empty() or String(p.item.get("cat", "")) != "weapons":
			continue
		if p.global_position.distance_to(pl.global_position) > 260.0:
			continue
		var it: Dictionary = p.item
		var d := _eff_dps(it)
		var cur: Dictionary = Game.run["slots"].get(level.natural_slot(it), {})
		var lbl := "SnH %s" % ItemGen.fmt(d)
		var col := PixUI.TEXT
		if not cur.is_empty() and String(cur.get("cat", "")) == "weapons":
			var dd := d - _eff_dps(cur)
			lbl += (" ▲" if dd >= 0.0 else " ▼")
			col = PixUI.GOOD if dd >= 0.0 else PixUI.BAD
		var sp: Vector2 = p.get_global_transform_with_canvas().origin / Ayarlar.ui_scale()
		var rc := Color.from_string(Data.items["rarities"][int(it["rarity"])]["color"], PixUI.DIM)
		var w := PixUI.width(lbl) + 8.0
		var y := roundf(sp.y - 34.0 + sin(_t * 3.0 + float(p.get_instance_id() % 7)) * 1.0)
		PixUI.panel(self, Rect2(roundf(sp.x - w / 2.0), y, w, 12), rc.darkened(0.2), PixUI.INK)
		PixUI.text(self, Vector2(roundf(sp.x - w / 2.0), y), lbl, col, 1, HORIZONTAL_ALIGNMENT_CENTER, w, 0)


func _world_prompt(at: Vector2, key: String, label: String) -> void:
	var w := PixUI.width(label) + 18.0
	var x := roundf(at.x - w / 2.0)
	var y := roundf(at.y + sin(_t * 4.0) * 1.5)
	PixUI.panel(self, Rect2(x, y, w, 14), PixUI.GOLD)
	PixUI.key_cap(self, Vector2(x + 2, y + 1), key)
	PixUI.text(self, Vector2(x + 14, y + 1), label, PixUI.TEXT)


func _draw_slot_box(r: Rect2, key: String, pl: Node) -> void:
	InkHUD.slot_box(self, r, key, pl)


func _draw_cephane(r: Rect2, key: String, pl: Node) -> void:
	## v25 cephane: yay yuvasının üstünde küçük mürekkep ok imleri (dolu: kemik rengi, boş: soluk iz, dolmakta olan:
	## aşağıdan yükselen çekirdek); boş tıkta kızarır, hak kazanınca sıçrar. Sınırsız yayda çizilmez.
	if key != String(pl.sec_slot) or pl.okc == null or int(pl.okc.ammo_max) <= 0:
		return
	var it: Dictionary = Game.run["slots"].get(key, {})
	if it.get("kind", "") != "bow":
		return
	var okc: Okculuk = pl.okc
	var n := okc.ammo_max
	var gap := minf(5.5, (r.size.x - 12.0) / float(n))
	var x0 := r.end.x - 3.0 - gap * float(n - 1)
	var pop := 1.0 + okc.ammo_pop * 1.6
	var y1 := r.position.y - 5.5
	var hgt := 8.0 * pop
	var red := clampf(okc.ammo_bos / 0.35, 0.0, 1.0)
	var ink := Color(0.03, 0.02, 0.03, 0.92)
	var bone := Color(0.98, 0.9, 0.7).lerp(Color(1.0, 0.35, 0.25), red)
	var dim := Color(0.55, 0.5, 0.45, 0.45).lerp(Color(1.0, 0.3, 0.2, 0.8), red)
	var fill := okc.ammo_k()
	for i in n:
		var x := x0 + gap * float(i)
		var a := Vector2(x, y1)
		var b := Vector2(x + 1.2, y1 - hgt)
		var full := i < okc.ammo
		draw_line(a, b, ink, 1.9, true)
		if full:
			draw_line(a, b, bone, 0.8, true)
		else:
			draw_line(a, b, dim, 0.6, true)
			if i == okc.ammo and fill > 0.0:
				draw_line(a, a.lerp(b, fill), Color(bone, 0.75), 0.8, true)
		# temren ve yelek
		var hd := (b - a).normalized()
		var nr := Vector2(-hd.y, hd.x)
		var hc := bone if full else dim
		draw_colored_polygon(PackedVector2Array([b + hd * 1.6, b + nr * 1.1, b - nr * 1.1]), hc if full else ink)
		draw_line(a, a + (-hd + nr) * 1.3, ink, 0.8, true)
		draw_line(a, a + (-hd - nr) * 1.3, ink, 0.8, true)


func _draw_hiz_yuk(pl: Node, y0: float) -> void:
	## v20: yakın silahın Kızışma (ya da yatağan ivmesi) yükleri yuvanın üstünde taneler; dolu taneler kızıldan altına,
	## tam yükte nabız; üstte "+%N hız". Pasifi olmayan silahta çizilmez.
	var y: Array = pl.hiz_yuk()
	if y.is_empty():
		return
	var n := int(y[0])
	var mx := maxi(1, int(y[1]))
	var full := n >= mx
	var i_slot := 0 if pl.mel_slot == "melee" else 1
	var bx := 8.0 + 50.0 * i_slot
	var step := minf(6.0, 32.0 / float(mx))
	var x0 := bx + 46.0 - 4.0 - step * float(mx - 1)
	var py := y0 - 11.0   # mürekkep çerçevesi yuvadan 4,5 px taşar
	var hot := Color(0.92, 0.34, 0.2) if String(y[3]) == "kizisma" else Color(0.75, 0.85, 1.0)
	var aa := true   # kenar yumuşatma
	for i in mx:
		var c := Vector2(x0 + step * i, py)
		var on := i < n
		var col := hot.lerp(PixUI.GOLD, float(i) / float(maxi(1, mx - 1)) * 0.7) if on else Color(0.3, 0.27, 0.34, 0.8)
		var r := 2.2 if on else 1.6
		if full:
			r += 0.5 + 0.4 * sin(_t * 14.0 + i)
		var pts := PackedVector2Array([c + Vector2(0, -r * 1.3), c + Vector2(r, 0), c + Vector2(0, r * 1.3), c + Vector2(-r, 0)])
		draw_colored_polygon(pts, Color(0.04, 0.02, 0.03, 0.85))
		var pts2 := PackedVector2Array()
		for q in pts:
			pts2.append(c + (q - c) * 0.72)
		draw_colored_polygon(pts2, col)
		if aa:
			pts.append(pts[0])
			draw_polyline(pts, Color(0.04, 0.02, 0.03, 0.6), 0.6, true)
	if n > 0:
		var txt := "+%%%d hız" % int(round(float(y[2])))
		PixUI.text(self, Vector2(bx, py - 14.0), txt, PixUI.GOLD if full else hot.lightened(0.25), 1, HORIZONTAL_ALIGNMENT_RIGHT, 46.0, 2)


# ------------------------------------------------------------------ eşya kartı
func _card_lines(it: Dictionary) -> Array:
	## [[metin, renk], ...] — açıklama, ek özellikler, kusur (sarılmış)
	var out: Array = []
	for l in ItemGen.describe(it):
		var is_aff := String(l).begins_with("•")
		var lc: Color = Color(0.55, 0.82, 1.0) if is_aff else PixUI.TEXT
		if String(l).begins_with(Unsur.MARK) or (String(l).begins_with("  ") and Unsur.of(it) != ""):
			lc = Unsur.color(Unsur.of(it)).lightened(0.15)   # v20 unsur satırları unsur renginde
		for w in PixUI.wrap(String(l), 176):
			out.append([w, lc])
	if it.get("flaw", "") != "":
		for f in Data.items["flaws"]:
			if f["id"] == it["flaw"]:
				for w in PixUI.wrap("Kusur: %s (%s)" % [f["name"], f["desc"]], 176):
					out.append([w, PixUI.BAD])
	return out


func _card_h(it: Dictionary) -> float:
	var h := 12.0 + 11.0 + 11.0 + 13.0 + 11.0 + 6.0
	if it.get("epithet", "") != "":
		h += 10.0
	if Data.find_item(it["id"]).has("upgrade_of"):
		h += 10.0
	if it["cat"] == "weapons":
		h += 21.0   # v23: SnH + tomar satırı
	h += _card_lines(it).size() * 10.0
	return h + 8.0


func _x(v: float) -> String:
	## v23 tomar çarpanı yazımı: iki ondalık, sondaki sıfırlar atılır (1,25 · 1,5 · 2)
	var t := "%.2f" % v
	t = t.rstrip("0").rstrip(".")
	return t.replace(".", ",")


func _eff_dps(it: Dictionary) -> float:
	## v23: kartın / yerdeki silahın SnH'si: tomar statı ve oyuncunun kalıcı güçleriyle (ItemGen.dps_oyuncu;
	## tools/tests/tomar_testi.gd ölçülen hasarla karşılaştırır)
	return ItemGen.dps_oyuncu(it)


func _draw_card(it: Dictionary, pos: Vector2, title: String, cmp: Dictionary = {}) -> void:
	var R: Dictionary = Data.items["rarities"][int(it["rarity"])]
	var col := Color.from_string(R["color"], PixUI.TEXT)
	var h := _card_h(it)
	var w := 190.0
	var x := roundf(pos.x)
	var y0 := roundf(pos.y)
	PixUI.panel(self, Rect2(x, y0, w, h), col.darkened(0.15))
	# başlık bandı: nadirlik renginde
	PixUI.rect(self, Rect2(x + 2, y0 + 2, w - 4, 2), col)
	PixUI.text(self, Vector2(x + 4, y0 - 19.0), title, PixUI.DIM, 1, HORIZONTAL_ALIGNMENT_LEFT, -1.0, 2)
	var y := y0 + 5.0
	PixUI.text(self, Vector2(x + 6, y), it["name"], col, 1, HORIZONTAL_ALIGNMENT_LEFT, -1.0, 1)
	y += 11.0
	if it.get("epithet", "") != "":
		PixUI.text(self, Vector2(x + 6, y), "«%s»" % it["epithet"], Color(1.0, 0.88, 0.55))
		y += 10.0
	PixUI.text(self, Vector2(x + 6, y), "%s · %s · Kalite %%%d" % [R["name"], CAT_TXT.get(it["cat"], ""), int(it["quality"])], PixUI.DIM, 1, HORIZONTAL_ALIGNMENT_LEFT, -1.0, 0)
	y += 11.0
	var base_def := Data.find_item(it["id"])
	if base_def.has("upgrade_of"):
		PixUI.text(self, Vector2(x + 6, y), "▲ %s'nın gelişmiş hali" % Data.find_item(base_def["upgrade_of"]).get("name", ""), Color(1.0, 0.85, 0.5))
		y += 10.0
	# ongun rozetleri: hangi renge göre güçlenir
	var ons := Game.item_onguns(it)
	var best := Game.item_best_ongun(it)
	var ox := x + 6.0
	for o in ons:
		var oc := PixUI.ongun_col(o)
		var on_best: bool = o == best
		var lbl := "%s ×%s" % [Data.items["ongun"][o]["name"], _x(Game.ongun_mult(o))]
		if ons.size() > 1 and on_best:
			lbl += " ★"
		var bw := PixUI.width(lbl) + 15.0
		PixUI.panel(self, Rect2(ox, y, bw, 12), oc if on_best else oc.darkened(0.5), Color(oc, 0.16) if on_best else PixUI.INK, false)
		PixUI.icon(self, o, Vector2(ox + 3, y + 3), oc if on_best else oc.darkened(0.4), 1, false)
		PixUI.text(self, Vector2(ox + 12, y + 1), lbl, oc.lightened(0.2) if on_best else PixUI.DIM, 1, HORIZONTAL_ALIGNMENT_LEFT, -1.0, 0)
		ox += bw + 3.0
	y += 13.0
	# değerler
	if it["cat"] == "weapons":
		PixUI.text(self, Vector2(x + 6, y), "Hasar %s  Hız %s/sn  Krit %%%s ×%s" % [ItemGen.fmt(it["dmg"]), ItemGen.fmt(ItemGen.aps_eff(it)), ItemGen.fmt(it["crit"]), ItemGen.fmt(it["crit_mult"])], PixUI.TEXT, 1, HORIZONTAL_ALIGNMENT_LEFT, -1.0, 0)
		y += 11.0
		var d := _eff_dps(it)
		PixUI.text(self, Vector2(x + 6, y), "Saniyede hasar: %s" % ItemGen.fmt(d), PixUI.GOLD)
		if not cmp.is_empty() and cmp.get("cat", "") == "weapons":
			var d_cmp := _eff_dps(cmp)
			var dd := d - d_cmp
			var pct := int(round(dd / maxf(0.01, d_cmp) * 100.0))
			var s := ("▲ +%s (+%%%d)" if dd >= 0.0 else "▼ %s (-%%%d)") % [ItemGen.fmt(dd), absi(pct)]
			PixUI.text(self, Vector2(x + 6, y), s, PixUI.GOOD if dd >= 0.0 else PixUI.BAD, 1, HORIZONTAL_ALIGNMENT_RIGHT, w - 12, 0)
		y += 10.0
		# v23: tomarın payı (tomarsız SnH ve stat çarpanı): tomar okudukça bu satır ve SnH büyür
		var bo := Game.item_best_ongun(it)
		PixUI.text(self, Vector2(x + 6, y), "tomarsız %s · %s %d tomar ×%s" % [ItemGen.fmt(ItemGen.dps_tomarsiz(it)), Data.items["ongun"][bo]["name"], int(Game.run["ongun"].get(bo, 0)) if not Game.run.is_empty() else 0, _x(Game.item_mult(it))], PixUI.DIM, 1, HORIZONTAL_ALIGNMENT_LEFT, -1.0, 0)
	elif it["cat"] == "shields":
		PixUI.text(self, Vector2(x + 6, y), "Blok %%%d   Savuşturma %s sn" % [int(float(it["block"]) * 100.0), ItemGen.fmt(it["parry_win"])], PixUI.TEXT, 1, HORIZONTAL_ALIGNMENT_LEFT, -1.0, 0)
		if not cmp.is_empty() and cmp.get("cat", "") == "shields":
			var db := int(round((float(it["block"]) - float(cmp["block"])) * 100.0))
			PixUI.text(self, Vector2(x + 6, y), ("▲ +%d" if db >= 0 else "▼ %d") % db, PixUI.GOOD if db >= 0 else PixUI.BAD, 1, HORIZONTAL_ALIGNMENT_RIGHT, w - 12, 0)
	else:
		PixUI.text(self, Vector2(x + 6, y), "Bekleme %s sn   Güç ×%s" % [ItemGen.fmt(it["cd"]), ItemGen.fmt(float(it["power"]) * Game.item_mult(it))], PixUI.TEXT, 1, HORIZONTAL_ALIGNMENT_LEFT, -1.0, 0)
	y += 11.0
	PixUI.divider(self, x + 8, y + 2, w - 16, col.darkened(0.3))
	y += 6.0
	for l in _card_lines(it):
		PixUI.text(self, Vector2(x + 6, y), l[0], l[1], 1, HORIZONTAL_ALIGNMENT_LEFT, -1.0, 0)
		y += 10.0
	PixUI.bar(self, Rect2(x + 6, y0 + h - 5, w - 12, 2), float(it["quality"]) / 100.0, col)


# ------------------------------------------------------------------ yuva seçimi
func _draw_slot(vp: Vector2) -> void:
	_dim(vp, 0.7)
	var p: Node = main.slot_pickup if main else null
	if p == null or not is_instance_valid(p):
		return
	_title(vp, 18, "HANGİ YUVAYA?", PixUI.GOLD)
	var e := _ease_open()
	var it: Dictionary = p.item
	var cx := roundf(vp.x / 2.0 - 205.0 + (1.0 - e) * -20.0)
	_draw_card(it, Vector2(cx, 64), "YENİ EŞYA")
	# iki seçenek
	var bx := roundf(vp.x / 2.0 + 10.0 + (1.0 - e) * 20.0)
	var oy := 64.0
	for i in slot_opts.size():
		var key: String = slot_opts[i]
		var cur: Dictionary = Game.run["slots"].get(key, {})
		var is_sel := i == sel
		var bh := 96.0
		var r := Rect2(bx, oy + i * (bh + 8), 196, bh)
		var col := PixUI.GOLD if is_sel else PixUI.EDGE.darkened(0.25)
		PixUI.panel(self, r, col, PixUI.INK2 if is_sel else PixUI.INK)
		if is_sel:
			# seçili: yanıp sönen ok
			var ax := r.position.x - 9 + sin(_t * 8.0) * 2.0
			PixUI.text(self, Vector2(ax, r.position.y + bh / 2.0 - 6), "→", PixUI.GOLD, 1, HORIZONTAL_ALIGNMENT_LEFT, -1.0, 2)
		PixUI.key_cap(self, r.position + Vector2(6, 5), SLOT_KEYS[key], PixUI.GOLD, is_sel)
		PixUI.text(self, r.position + Vector2(20, 5), _up(SLOT_NAMES[key]), col if is_sel else PixUI.DIM)
		if cur.is_empty():
			PixUI.text(self, r.position + Vector2(0, 40), "boş", PixUI.DIM, 1, HORIZONTAL_ALIGNMENT_CENTER, r.size.x)
		else:
			var rc := Color.from_string(Data.items["rarities"][int(cur["rarity"])]["color"], PixUI.TEXT)
			PixUI.rect(self, Rect2(r.position.x + 6, r.position.y + 20, 56, 34), Color(0, 0, 0, 0.25))
			PixUI.weapon(self, cur, r.position + Vector2(34, 37), Vector2(54, 32))
			PixUI.ongun_stripe(self, Rect2(r.position.x + 6, r.position.y + 55, 56, 2), Game.item_onguns(cur), Game.item_best_ongun(cur))
			var nl := PixUI.wrap(String(cur["name"]), 124)
			for j in mini(2, nl.size()):
				PixUI.text(self, r.position + Vector2(66, 20 + j * 10), nl[j], rc)
			var cat := String(cur["cat"])
			var stat := ""
			var delta := 0.0
			if cat == "weapons":
				stat = "SnH %s" % ItemGen.fmt(_eff_dps(cur))
				if it["cat"] == "weapons":
					delta = _eff_dps(it) - _eff_dps(cur)
			elif cat == "shields":
				stat = "Blok %%%d" % int(float(cur["block"]) * 100.0)
			else:
				stat = "Bekleme %s sn" % ItemGen.fmt(cur["cd"])
			PixUI.text(self, r.position + Vector2(66, 42), stat, PixUI.TEXT, 1, HORIZONTAL_ALIGNMENT_LEFT, -1.0, 0)
			if cat == "weapons" and it["cat"] == "weapons":
				var s := ("yeni ▲ +%s" if delta >= 0.0 else "yeni ▼ %s") % ItemGen.fmt(delta)
				PixUI.text(self, r.position + Vector2(66, 52), s, PixUI.GOOD if delta >= 0.0 else PixUI.BAD, 1, HORIZONTAL_ALIGNMENT_LEFT, -1.0, 0)
			PixUI.text(self, r.position + Vector2(6, bh - 14), "Bu eşya yere bırakılır" if is_sel else "Yerinde kalır", Color(PixUI.BAD, 0.9) if is_sel else PixUI.DIM, 1, HORIZONTAL_ALIGNMENT_LEFT, -1.0, 0)
	var keys := ["J", "K"] if "melee" in slot_opts else [SLOT_KEYS["g1"], SLOT_KEYS["g2"]]
	_hint(vp, [["A/D", "seç"], ["Boşluk", "onayla"], [keys[0] + "/" + keys[1], "doğrudan"], ["Esc", "vazgeç"]], 286.0)


# ------------------------------------------------------------------ Kut Tomarı (stat seçimi; v23, eski tılsım)
func _draw_tilsim(vp: Vector2) -> void:
	## v23 Kut Tomarı (Dead Cells "Scroll of Power"): üç stat kartı; her kartta stat çarpanının şimdi → sonra değeri,
	## can artışı ve kuşanılan eşyaların SnH'sinin bu tomarla nasıl değişeceği (seçimi gerçekten uygulayıp ölçerek)
	_dim(vp, 0.72)
	var R: Dictionary = Game.run
	_title(vp, 58, "KUT TOMARI", PixUI.GOLD, "Bir stat seç: o renkteki eşyaların hasarı artar (her tomar biraz daha az; çift renkli eşya yüksek statla). Okunan tomar: %d" % int(R.get("scrolls", 0)))
	var e := _ease_open()
	var cw := 176.0
	var gap := 10.0
	var x0 := roundf((vp.x - (cw * 3 + gap * 2)) / 2.0)
	for i in 3:
		var k: String = ONGUN_KEYS[i]
		var o: Dictionary = Data.items["ongun"][k]
		var col := PixUI.ongun_col(k)
		var is_sel := i == sel
		var x := x0 + i * (cw + gap)
		var y := 104.0 + (1.0 - e) * (20.0 + i * 10.0) - (5.0 if is_sel else 0.0)
		var ch := 220.0
		var r := Rect2(x, y, cw, ch)
		PixUI.fancy_panel(self, r, col if is_sel else col.darkened(0.5), Color(col.darkened(0.82), 0.97) if is_sel else PixUI.INK)
		# v34: açık Kut Tomarı resmi (kayın kabuğu, bozkurt başlı çubuk, halkada statın tamgası; tools/artgen/tomar_ink.py)
		if TomarV2.on() and TomarV2.has("ui_kart_" + k):
			var bob := sin(_t * 2.4 + i) * (1.2 if is_sel else 0.0)
			TomarV2.ui(self, "ui_kart_" + k, Vector2(x + cw / 2.0, y + 35.0 + bob), 72.0 if is_sel else 64.0, Color(1, 1, 1) if is_sel else Color(0.62, 0.6, 0.66))
		else:
			var isz := PixUI.icon_size(k) * 3.0
			PixUI.icon(self, k, Vector2(x + (cw - isz.x) / 2.0, y + 10), col if is_sel else col.darkened(0.35), 3)
		y += 24.0
		PixUI.text(self, Vector2(x, y + 36), _up(String(o["name"])), col, 1, HORIZONTAL_ALIGNMENT_CENTER, cw, 2)
		var lv := int(R["ongun"][k])
		var m0 := Game.ongun_mult_lv(k, 0)
		var m1 := Game.ongun_mult_lv(k, 1)
		PixUI.text(self, Vector2(x, y + 49), "Seviye %d  →  %d" % [lv, lv + 1], PixUI.TEXT, 1, HORIZONTAL_ALIGNMENT_CENTER, cw)
		PixUI.text(self, Vector2(x, y + 60), "hasar ×%s  →  ×%s" % [_x(m0), _x(m1)], col.lightened(0.25), 1, HORIZONTAL_ALIGNMENT_CENTER, cw, 0)
		PixUI.divider(self, x + 10, y + 75, cw - 20, col.darkened(0.3))
		var yy := y + 80.0
		for l in PixUI.wrap(String(o["desc"]), cw - 16):
			PixUI.text(self, Vector2(x + 8, yy), l, PixUI.DIM, 1, HORIZONTAL_ALIGNMENT_LEFT, -1.0, 0)
			yy += 10.0
		yy += 3.0
		PixUI.text(self, Vector2(x + 8, yy), "+%%%d bu renkte hasar" % int(round((m1 / m0 - 1.0) * 100.0)), PixUI.TEXT, 1, HORIZONTAL_ALIGNMENT_LEFT, -1.0, 0)
		yy += 10.0
		var extra := ""
		if k == "kurt":
			extra = "  ·  +%%%s saldırı hızı" % ItemGen.fmt(float(Player.HIZ["kurt"]))
		elif k == "ayi":
			extra = "  ·  %%%d hasar azaltma" % int(round(Zorluk.ayi_zirh(lv + 1) * 100.0))
		PixUI.text(self, Vector2(x + 8, yy), "+%%%d azami can%s" % [int(round(Zorluk.tomar_can(k) * 100.0)), extra], PixUI.GOOD, 1, HORIZONTAL_ALIGNMENT_LEFT, -1.0, 0)
		yy += 14.0
		# bu seçimden güçlenecek eşyalar: SnH şimdi -> sonra (stat geçici olarak artırılıp ölçülür)
		PixUI.text(self, Vector2(x + 8, yy), "Güçlenen eşyaların:", PixUI.DIM, 1, HORIZONTAL_ALIGNMENT_LEFT, -1.0, 0)
		yy += 11.0
		var any := false
		for sk in ["melee", "second", "g1", "g2"]:
			var it: Dictionary = R["slots"].get(sk, {})
			if it.is_empty():
				continue
			var now := Game.item_mult(it)
			var d0 := ItemGen.dps_oyuncu(it)
			R["ongun"][k] = lv + 1
			var after := Game.item_mult(it)
			var d1 := ItemGen.dps_oyuncu(it)
			R["ongun"][k] = lv
			if after - now <= 0.001 and d1 - d0 <= 0.01:
				continue
			any = true
			PixUI.rect(self, Rect2(x + 9, yy + 4, 3, 3), col)
			PixUI.text(self, Vector2(x + 15, yy), String(it["name_base"]), PixUI.TEXT, 1, HORIZONTAL_ALIGNMENT_LEFT, -1.0, 0)
			var gain := "SnH %s → %s" % [ItemGen.fmt(d0), ItemGen.fmt(d1)] if String(it.get("cat", "")) == "weapons" else "+%%%d" % int(round((after / now - 1.0) * 100.0))
			PixUI.text(self, Vector2(x + 8, yy), gain, PixUI.GOOD, 1, HORIZONTAL_ALIGNMENT_RIGHT, cw - 16, 0)
			yy += 10.0
		if not any:
			PixUI.text(self, Vector2(x + 8, yy), "(bu renkte eşyan yok)", Color(PixUI.DIM, 0.7), 1, HORIZONTAL_ALIGNMENT_LEFT, -1.0, 0)
	_hint(vp, [["A/D", "seç"], ["Boşluk", "oku"]], 330.0)


# ------------------------------------------------------------------ ekranlar
func _draw_title(vp: Vector2) -> void:
	InkHUD.title_top(self, vp, _t)
	if mode == "title":
		_hint(vp, [["Tab", "ayarlar"]], 200.0)
	# kontroller
	var rows := [
		[["A/D", "hareket"], ["Boşluk", "zıpla"], ["J", "1. silah"], ["K", "2. silah"], ["L", "yuvarlan"]],
		[["E/R", "teçhizat"], ["Q", "şişe"], ["F", "Kut gücü"], ["T", "savaş sanatı"], ["W", "al / konuş"], ["Esc", "duraklat"]],
	]
	InkUI.wash(self, Rect2(vp.x / 2.0 - 300, vp.y - 92, 600, 100), 0.8)
	_hint(vp, rows[0], vp.y - 70)
	_hint(vp, rows[1], vp.y - 56)
	# uzun ipucu satırları 1x ölçekte (menü ölçeğinde ekrana sığmıyor)
	draw_set_transform(Vector2.ZERO, 0.0, Vector2.ONE)
	var fv := vp * MENU_SCALE
	PixUI.text(self, Vector2(0, fv.y - 63), "G don: seçkin ruhunun kılığı · W / ↑ dokun: al, konuş, tomar oku · müziğin usulüne denk vuruş güçlü", Color(0.85, 0.75, 1.0, 0.9), 1, HORIZONTAL_ALIGNMENT_CENTER, fv.x, 0)
	PixUI.text(self, Vector2(0, fv.y - 43), "J art arda = zincir · bekle+J = bitiriş · basılı = ağır · ↑J göğe savur · havada ↓J dalış · koşarken J akın · yuvarlan+J dönüş · S+J diz biçen", Color(1.0, 0.85, 0.5, 0.85), 1, HORIZONTAL_ALIGNMENT_CENTER, fv.x, 0)
	PixUI.text(self, Vector2(0, fv.y - 25), "Shift basılı = koş · S = çömel (çömelirken saldırı ve yay) · duvara doğru zıpla = kenara tutun", Color(0.75, 0.9, 1.0, 0.8), 1, HORIZONTAL_ALIGNMENT_CENTER, fv.x, 0)
	draw_set_transform(Vector2.ZERO, 0.0, Vector2.ONE * MENU_SCALE)


func _draw_intro(vp: Vector2) -> void:
	InkHUD.intro(self, vp, Data.story["intro"], intro_i)
	_hint(vp, [["Boşluk", "devam"], ["Esc", "atla"]])


func _stat_row(vp: Vector2, y: float, items: Array) -> void:
	## [[simge, metin, renk], ...] ortalanmış sıra
	var total := 0.0
	for it in items:
		total += 10.0 + PixUI.width(it[1]) + 14.0
	total -= 14.0
	var x := roundf((vp.x - total) / 2.0)
	for it in items:
		PixUI.icon(self, it[0], Vector2(x, y + 3), it[2])
		x += 10.0
		PixUI.text(self, Vector2(x, y), it[1], it[2])
		x += PixUI.width(it[1]) + 14.0


func _draw_dead(vp: Vector2) -> void:
	_dim(vp, 0.74, Color(0.05, 0.01, 0.03))
	var e := _ease_open()
	InkHUD.dead_backdrop(self, vp, e)
	_title(vp, 92, "RUH KUŞUN DALA KONMADI", Color(1.0, 0.55, 0.45), "Umay Ana seni yeniden yoğuruyor.")
	var R: Dictionary = Game.run
	var pw := 360.0
	var y := 144.0 + (1.0 - e) * 12.0
	PixUI.panel(self, Rect2((vp.x - pw) / 2.0, y, pw, 52))
	var tm := float(R.get("time", 0.0))
	_stat_row(vp, y + 6, [["kilic", "%d. derinlik" % int(R.get("depth", 1)), PixUI.TEXT], ["kafatasi", "%d düşman" % int(R["kills"]), PixUI.TEXT], ["altin", str(R["gold"]), PixUI.GOLD], ["zaman", "%d:%02d" % [int(tm / 60.0), int(tm) % 60], PixUI.DIM]])
	PixUI.text(self, Vector2(0, y + 22), "Taşıdığın %d Kut yitti. %s" % [int(R.get("kut_lost", 0)), flash_msg], Color(0.6, 0.95, 1.0), 1, HORIZONTAL_ALIGNMENT_CENTER, vp.x)
	PixUI.text(self, Vector2(0, y + 34), "Kut bankası: %d   ·   Bekleyen parşömen: %d" % [int(Game.meta.get("kut_bank", 0)), Game.meta.get("blueprints", []).size()], PixUI.DIM, 1, HORIZONTAL_ALIGNMENT_CENTER, vp.x)
	_hint(vp, [["Boşluk", "yeniden doğ"]], 214.0)


func _draw_done(vp: Vector2) -> void:
	_dim(vp, 0.7, Color(0.01, 0.04, 0.06))
	var R: Dictionary = Game.run
	_title(vp, 96, "KUT KAPISI", Color(0.6, 1.0, 1.0), "%d. derinliği geçtin. Silahların, ongunların ve canın seninle; şişelerin doldu." % int(R.get("depth", 1)))
	PixUI.text(self, Vector2(0, 138), "Aşağısı daha karanlık: düşmanlar güçlenir, eşyalar daha nadir düşer.", PixUI.DIM, 1, HORIZONTAL_ALIGNMENT_CENTER, vp.x)
	_hint(vp, [["Boşluk", "derine in"]], 200.0)


func _draw_pause(vp: Vector2) -> void:
	draw_rect(Rect2(Vector2.ZERO, vp), Color(0.02, 0.015, 0.04, 0.62))
	_title(vp, 64, "DURAKLATILDI", PixUI.GOLD)
	var R: Dictionary = Game.run
	var pw := 340.0
	var x := (vp.x - pw) / 2.0
	PixUI.fancy_panel(self, Rect2(x, 104, pw, 134), PixUI.EDGE, PixUI.INK2)
	PixUI.text(self, Vector2(x, 110), "TOMAR STATLARI (%d tomar)" % int(R.get("scrolls", 0)), PixUI.DIM, 1, HORIZONTAL_ALIGNMENT_CENTER, pw)
	var ox := x + 16.0
	for k in ONGUN_KEYS:
		var col := PixUI.ongun_col(k)
		PixUI.icon(self, k, Vector2(ox, 126), col, 2)
		PixUI.text(self, Vector2(ox + 18, 125), "%s %d" % [Data.items["ongun"][k]["name"], int(R["ongun"][k])], col)
		PixUI.text(self, Vector2(ox + 18, 135), "×%s" % _x(Game.ongun_mult(k)), PixUI.DIM, 1, HORIZONTAL_ALIGNMENT_LEFT, -1.0, 0)
		ox += 108.0
	PixUI.divider(self, x + 12, 152, pw - 24)
	var yy := 160.0
	for sk in ["melee", "second", "g1", "g2"]:
		var it: Dictionary = R["slots"].get(sk, {})
		PixUI.key_cap(self, Vector2(x + 14, yy), SLOT_KEYS[sk], PixUI.GOLD, not it.is_empty())
		if it.is_empty():
			PixUI.text(self, Vector2(x + 28, yy), "—", PixUI.DIM)
		else:
			var rc := Color.from_string(Data.items["rarities"][int(it["rarity"])]["color"], PixUI.TEXT)
			PixUI.text(self, Vector2(x + 28, yy), String(it["name"]), rc)
			if String(it.get("cat", "")) == "weapons":   # v23: kuşanılan silahın SnH'si (tomarlarla)
				PixUI.text(self, Vector2(x, yy), "SnH %s" % ItemGen.fmt(_eff_dps(it)), PixUI.GOLD, 1, HORIZONTAL_ALIGNMENT_RIGHT, pw - 46, 0)
			PixUI.ongun_stripe(self, Rect2(x + pw - 40, yy + 4, 26, 3), Game.item_onguns(it), Game.item_best_ongun(it))
		yy += 14.0
	# v20 saldırı hızı: yakın silah için toplam ve kaynakları
	var mel: Dictionary = R["slots"].get("melee", {})
	var hk := Player.hiz_kaynak(mel)
	var parts: Array = []
	for pk in [["silah", "silah"], ["techizat", "teçhizat"], ["kurt", "Kurt"], ["lutuf", "lütuf"], ["umay", "Umay"]]:
		if float(hk[pk[0]]) > 0.0:
			parts.append("%s %%%s" % [pk[1], ItemGen.fmt(float(hk[pk[0]]))])
	var htxt := "Saldırı hızı +%%%s" % ItemGen.fmt(Player.hiz_kalici(mel))
	if not parts.is_empty():
		htxt += "  (" + ", ".join(parts) + ")"
	PixUI.text(self, Vector2(x + 14, yy + 2), htxt, PixUI.GOLD, 1, HORIZONTAL_ALIGNMENT_LEFT, -1.0, 0)
	PixUI.text(self, Vector2(x, yy + 2), "en çok %%%d" % int(Player.HIZ["cap"]), PixUI.DIM, 1, HORIZONTAL_ALIGNMENT_RIGHT, pw - 14, 0)
	# v23 tuşlar: yan teçhizat E / R, etkileşim W / ↑ dokunuşu (v25: kam transı T kaldırıldı)
	_hint(vp, [["J/K", "silahlar"], ["E/R", "teçhizat"], ["W", "al / konuş"], ["T", "sanat"], ["G", "don"], ["Q", "şişe"], ["M", "harita"]], 252.0)
	_hint(vp, [["Esc", "devam et"], ["T", "savaş sanatları"], ["Tab", "ayarlar"]])


func _draw_settings(vp: Vector2) -> void:
	## Görüntü ayarları: pencere modu, çözünürlük, doku kalitesi (2K / 4K HD paketi), dikey eşitleme
	_dim(vp, 0.93)
	_title(vp, 40, "AYARLAR", PixUI.GOLD, "Görüntü ve çözünürlük")
	var rows: Array = Ayarlar.rows()
	var pw := 380.0
	var x := roundf((vp.x - pw) / 2.0)
	var y := 96.0
	PixUI.fancy_panel(self, Rect2(x, y - 8, pw, rows.size() * 22.0 + 14), PixUI.EDGE, PixUI.INK2)
	for i in rows.size():
		var r: Array = rows[i]
		var is_sel := i == sel
		var on: bool = r[2]
		var col := PixUI.GOLD if is_sel else (PixUI.TEXT if on else PixUI.DIM)
		if is_sel:
			draw_texture_rect(InkUI.tex("swash"), Rect2(x - 2, y - 4, pw + 4, 22), false, Color(PixUI.GOLD.darkened(0.55), 0.55))
			PixUI.text(self, Vector2(x - 10 + sin(_t * 8.0) * 2.0, y + 1), "→", PixUI.GOLD, 1, HORIZONTAL_ALIGNMENT_LEFT, -1.0, 2)
		PixUI.text(self, Vector2(x + 12, y + 1), r[0], col)
		var v: String = r[1]
		var vx := x + pw - 150.0
		PixUI.text(self, Vector2(vx, y + 1), "<" if on else "", col, 1, HORIZONTAL_ALIGNMENT_LEFT, -1.0, 0)
		PixUI.text(self, Vector2(vx + 8, y + 1), v, col if on else PixUI.DIM, 1, HORIZONTAL_ALIGNMENT_CENTER, 124)
		PixUI.text(self, Vector2(vx + 136, y + 1), ">" if on else "", col, 1, HORIZONTAL_ALIGNMENT_LEFT, -1.0, 0)
		y += 22.0
	var tips := [
		"Pencereli, tam ekran (kenarsız) ya da özel tam ekran.",
		"Pencereli modda pencere boyutu. Tam ekranda ekranın kendi çözünürlüğü kullanılır.",
		Ayarlar.quality_tip(),
		"Kare hızını ekran yenilemesine kilitler (yırtılmayı önler).",
		"Oyun içi göstergelerin boyutu. Normal: daha çok oyun alanı görünür.",
		"Kamera sarsıntısı, darbe kareleri ve ekran flaşları. Rahatsız ediyorsa Azaltılmış ya da Kapalı seç.",
		"Kut Mühürleri: Erlik Han'ı her yenişinde bir sonraki zorluk kademesi açılır (daha dayanıklı ve saldırgan düşmanlar, daha az şifa, öfkeli yaratıklar). %s. Yeni koşuda geçerli." % String(Zorluk.muhur_def(Zorluk.muhur_secili()).get("desc", "")).trim_suffix("."),
		"Sağ alttaki parşömen haritanın boyu (keşfettikçe açılır; Kut Taşları ve ödüller işlenir). Kapalı: yalnızca M ile tam ekran harita.",
		"Küçük haritanın saydamlığı: Hafif dövüşte az yer kaplar, Koyu daha okunur.",
	]
	var tl := PixUI.wrap(tips[clampi(sel, 0, tips.size() - 1)], 420)
	var ty := y + 14.0
	for l in tl:
		PixUI.text(self, Vector2(0, ty), l, PixUI.DIM, 1, HORIZONTAL_ALIGNMENT_CENTER, vp.x)
		ty += 11.0
	var ws := get_tree().root.size
	PixUI.text(self, Vector2(0, ty + 6), "Pencere: %dx%d  ·  ölçek ×%s" % [ws.x, ws.y, ItemGen.fmt(float(ws.y) / get_viewport_rect().size.y)], Color(PixUI.KUT, 0.8), 1, HORIZONTAL_ALIGNMENT_CENTER, vp.x, 0)
	_hint(vp, [["W/S", "seç"], ["A/D", "değiştir"], ["Esc", "geri"]])


func _draw_sanat(vp: Vector2) -> void:
	## v27 savaş sanatları: duraklatmadan (T) kuşan; Alp Ata'da öğren + kuşan (SanatUI)
	_dim(vp, 0.8, Color(0.05, 0.02, 0.03))
	if sanat_ogretmen:
		_title(vp, 20, _up("Alp Ata"), Color(1.0, 0.55, 0.45), "«Kılıç elde değil, yürekte döner. Kut'unu getir, sana bir sanat göstereyim.»")
	else:
		_title(vp, 20, _up("Savaş Sanatları"), PixUI.GOLD, "Tek sanat kuşanılır · T ile kullanılır · Alp Nişanı harcar")
	SanatUI.menu(self, vp, sel, sanat_ogretmen, _t, _ease_open(), flash_msg, flash_t)
	var id := String(SavasSanati.ids()[clampi(sel, 0, SavasSanati.ids().size() - 1)])
	var act := "kuşan" if SavasSanati.acik_mi(id) else ("öğren" if sanat_ogretmen else "—")
	_hint(vp, [["W/S", "seç"], ["Boşluk", act], ["Esc", "ayrıl" if sanat_ogretmen else "geri"]])


func _draw_umay(vp: Vector2) -> void:
	_dim(vp, 0.8, Color(0.01, 0.04, 0.06))
	_title(vp, 22, "UMAY ANA", Color(0.6, 1.0, 1.0), "«Getirdiğin Kut ağaca işledi. Söyle, hangi dalı güçlendireyim?»")
	var bank := int(Game.meta.get("kut_bank", 0))
	var bt := "Kut bankası: %d" % bank
	var bw := PixUI.width(bt) + 26.0
	PixUI.panel(self, Rect2((vp.x - bw) / 2.0, 66, bw, 15), PixUI.KUT)
	PixUI.icon(self, "kut", Vector2((vp.x - bw) / 2.0 + 6, 70), PixUI.KUT)
	PixUI.text(self, Vector2((vp.x - bw) / 2.0 + 16, 68), bt, PixUI.KUT)
	var keys: Array = Game.UMAY.keys()
	var y := 90.0
	var pw := 420.0
	var x := roundf((vp.x - pw) / 2.0)
	for i in keys.size():
		var id: String = keys[i]
		var u: Array = Game.UMAY[id]
		var lv := Game.umay_level(id)
		var mx: int = (u[2] as Array).size()
		var cost := Game.umay_cost(id)
		var is_sel := i == sel
		var r := Rect2(x, y, pw, 30 if keys.size() <= 6 else 28)
		PixUI.panel(self, r, PixUI.KUT if is_sel else PixUI.EDGE.darkened(0.4), Color(0.06, 0.12, 0.14, 0.95) if is_sel else PixUI.INK, false)
		if is_sel:
			PixUI.text(self, Vector2(x - 10 + sin(_t * 8.0) * 2.0, y + 9), "→", PixUI.KUT, 1, HORIZONTAL_ALIGNMENT_LEFT, -1.0, 2)
		PixUI.text(self, Vector2(x + 8, y + 3), u[0], PixUI.TEXT if lv < mx else PixUI.KUT)
		PixUI.text(self, Vector2(x + 8, y + 15), u[1], PixUI.DIM, 1, HORIZONTAL_ALIGNMENT_LEFT, -1.0, 0)
		for k in mx:
			var c := PixUI.KUT if k < lv else Color(0.2, 0.22, 0.3)
			InkUI.splat(self, Vector2(x + 283.5 + k * 10, y + 14.5), 11.0 if k < lv else 8.0, c if k < lv else Color(c, 0.8), float(k) * 1.7 + float(i))
		var ct := ("%d" % cost) if cost >= 0 else "tamam"
		var can := cost >= 0 and bank >= cost
		var cc := (PixUI.KUT if can else Color(0.6, 0.55, 0.65)) if cost >= 0 else PixUI.GOOD
		if cost >= 0:
			PixUI.icon(self, "kut", Vector2(x + pw - 14 - PixUI.width(ct) - 8, y + 11), cc, 1, false)
		PixUI.text(self, Vector2(x + 8, y + 9), ct, cc, 1, HORIZONTAL_ALIGNMENT_RIGHT, pw - 18)
		y += 34.0 if keys.size() <= 6 else 31.0
	if flash_t > 0.0:
		PixUI.text(self, Vector2(0, vp.y - 40), flash_msg, PixUI.GOLD, 1, HORIZONTAL_ALIGNMENT_CENTER, vp.x, 2)
	_hint(vp, [["W/S", "seç"], ["Boşluk", "al"], ["Esc", "ayrıl"]])


func _draw_ozan(vp: Vector2) -> void:
	_dim(vp, 0.8, Color(0.05, 0.03, 0.02))
	_title(vp, 30, "OZAN BİLGE KOPUZ", PixUI.GOLD)
	var npc: Dictionary = Data.story["npcs"]["ozan"]
	var lines: Array = npc["first"] + npc["repeat"]
	var R: Dictionary = Game.run
	var lore: Array = Data.story["lore"].get("otuken", [])
	var said: Array = []
	for k in mini(ozan_i + 1, 4):
		if k < 3:
			said.append(lines[(k + int(Game.meta.get("runs", 0))) % lines.size()])
		else:
			said.append(lore[int(Game.meta.get("runs", 0)) % maxi(1, lore.size())])
	InkHUD.ozan(self, vp, said)
	var tm := float(R.get("time", 0.0))
	PixUI.text(self, Vector2(0, vp.y - 44), "Bu koşu: %d. derinlik  ·  %d düşman  ·  %d:%02d  ·  en derin: %d" % [int(R.get("depth", 1)), int(R.get("kills", 0)), int(tm) / 60, int(tm) % 60, int(Game.meta.get("best_depth", 1))], PixUI.DIM, 1, HORIZONTAL_ALIGNMENT_CENTER, vp.x)
	_hint(vp, [["Boşluk", "dinle"], ["Esc", "ayrıl"]])


func _draw_demirci(vp: Vector2) -> void:
	_dim(vp, 0.82, Color(0.05, 0.02, 0.02))
	if not demirci_son.is_empty():
		_draw_demirci_son(vp)
		return
	_title(vp, 24, "DEMİRCİ KAM KUZGUN", PixUI.GOLD, "«Parşömen getirdin. Kut ver, dövüp koşuna katayım.»")
	var bank := int(Game.meta.get("kut_bank", 0))
	var bt := "Kut bankası: %d" % bank
	var bw := PixUI.width(bt) + 26.0
	PixUI.panel(self, Rect2((vp.x - bw) / 2.0, 68, bw, 15), PixUI.KUT)
	PixUI.icon(self, "kut", Vector2((vp.x - bw) / 2.0 + 6, 72), PixUI.KUT)
	PixUI.text(self, Vector2((vp.x - bw) / 2.0 + 16, 70), bt, PixUI.KUT)
	var bps: Array = Game.meta.get("blueprints", [])
	if bps.is_empty():
		PixUI.text(self, Vector2(0, 150), "Bekleyen parşömen yok. Düşmanlar parşömen düşürür; seçkinler kesin düşürür.", PixUI.DIM, 1, HORIZONTAL_ALIGNMENT_CENTER, vp.x)
	else:
		var n := bps.size()
		var w := 122.0
		var gap := 10.0
		var total := n * w + (n - 1) * gap
		var x0 := vp.x / 2.0 - total / 2.0
		if total > vp.x - 40:
			x0 = (vp.x - w) / 2.0 - sel * (w + gap)
		for i in n:
			var id: String = bps[i]
			var base := Data.find_item(id)
			var cost := Game.unlock_cost(id)
			var can := bank >= cost
			var x := roundf(x0 + i * (w + gap))
			var y := 94.0 - (5.0 if i == sel else 0.0)
			var col := PixUI.KUT if can else Color(0.6, 0.55, 0.65)
			PixUI.fancy_panel(self, Rect2(x, y, w, 150), col if i == sel else col.darkened(0.5), PixUI.INK2 if i == sel else PixUI.INK)
			if Data.has_weapon_sprite(id):
				PixUI.rect(self, Rect2(x + 8, y + 10, w - 16, 40), Color(0, 0, 0, 0.25))
				PixUI.weapon(self, {"id": id, "material": "demir"}, Vector2(x + w / 2.0, y + 30), Vector2(w - 20, 36))
			PixUI.text(self, Vector2(x, y + 56), base.get("name", id), PixUI.TEXT, 1, HORIZONTAL_ALIGNMENT_CENTER, w)
			PixUI.text(self, Vector2(x, y + 67), CAT_TXT.get(base.get("cat", ""), ""), PixUI.DIM, 1, HORIZONTAL_ALIGNMENT_CENTER, w, 0)
			var mech: Dictionary = base.get("mech", {})
			var desc: String = String(mech.get("desc", base.get("desc", ""))).replace("{v}", "?")
			var lines := PixUI.wrap(desc, w - 12)
			for j in mini(5, lines.size()):
				PixUI.text(self, Vector2(x + 6, y + 80 + j * 10), lines[j], PixUI.TEXT, 1, HORIZONTAL_ALIGNMENT_LEFT, -1.0, 0)
			var ct := "%d" % cost
			PixUI.icon(self, "kut", Vector2(x + (w - PixUI.width(ct)) / 2.0 - 7, y + 136), col, 1, false)
			PixUI.text(self, Vector2(x + 5, y + 134), ct, col, 1, HORIZONTAL_ALIGNMENT_CENTER, w)
	if flash_t > 0.0 and flash_msg != "":
		PixUI.text(self, Vector2(0, 256), flash_msg, Color(PixUI.GOLD, clampf(flash_t, 0.0, 1.0)), 1, HORIZONTAL_ALIGNMENT_CENTER, vp.x, 2)
	PixUI.text(self, Vector2(0, vp.y - 36), "Açılan eşya hemen dövülüp önüne bırakılır (rastgele değerlerle); bundan sonra düşebilir de.", PixUI.DIM, 1, HORIZONTAL_ALIGNMENT_CENTER, vp.x)
	_hint(vp, [["A/D", "seç"], ["Boşluk", "parşömeni aç"], ["Esc", "yola çık"]] if not Game.meta.get("blueprints", []).is_empty() else [["Boşluk", "yola çık"]])


func _draw_demirci_son(vp: Vector2) -> void:
	## v24: Demirci parşömeni açınca eşyayı hemen döver: rastgele yuvarlanmış eşyanın kartı (kuşanılanla SnH farkı)
	var it: Dictionary = demirci_son
	var rc := Color.from_string(Data.items["rarities"][int(it["rarity"])]["color"], PixUI.TEXT)
	_title(vp, 24, "DEMİRCİ KAM KUZGUN", PixUI.GOLD, "«Al yiğit, %s. Sıcağı sıcağına; değerlerini ateş seçti.»" % String(it.get("name_base", "")))
	PixUI.text(self, Vector2(0, 74), _up("Örste dövüldü"), Color(1.0, 0.62, 0.3), 1, HORIZONTAL_ALIGNMENT_CENTER, vp.x, 2)
	var cur: Dictionary = Game.run["slots"].get(level.natural_slot(it), {}) if level and not Game.run.is_empty() else {}
	var ch := _card_h(it)
	var cx := roundf(vp.x / 2.0 - 95.0)
	var cy := 104.0 + (1.0 - _ease_open()) * 10.0
	_draw_card(it, Vector2(cx, cy), "ÖNÜNE BIRAKILDI", cur)
	var note := "%s · kalite %%%d · yerden %s ile al" % [String(Data.items["rarities"][int(it["rarity"])]["name"]), int(it["quality"]), KEY_ETKILES]
	PixUI.text(self, Vector2(0, cy + ch + 8.0), note, rc, 1, HORIZONTAL_ALIGNMENT_CENTER, vp.x)
	_hint(vp, [["Boşluk", "tamam"]])


# ------------------------------------------------------------------ v24 tüccar (Bezirgân Sartak)
func _draw_tuccar(vp: Vector2) -> void:
	## Pazar: solda mallar (simge, ad, kategori · nadirlik, fiyat, silahta SnH farkı; satılanlar SATILDI), en altta
	## malları yenileme; sağda seçili malın tam eşya kartı (kuşanılanla karşılaştırmalı) ya da Umay Sütü / Kut Tomarı
	## açıklaması. Boşluk ilk basışta "satın al?" onayı, ikinci basışta alır.
	_dim(vp, 0.78, Color(0.04, 0.025, 0.02))
	if level == null or level.bezirgan == null:
		return
	var bz: Node = level.bezirgan
	var offers: Array = bz.offers
	var R: Dictionary = Game.run
	_title(vp, 20, _up("Bezirgân Sartak"), PixUI.GOLD, Usta.soz(String(level.biome.get("id", "")), "bezirgan") if level.konak else "«Bozkırın her yolu kervanıma çıkar, yiğit. Altının varsa malım var.»")
	var gold := int(R.get("gold", 0))
	var gt := "%d altın" % gold
	var gw := PixUI.width(gt) + 26.0
	PixUI.panel(self, Rect2((vp.x - gw) / 2.0, 62, gw, 15), PixUI.GOLD)
	PixUI.icon(self, "altin", Vector2((vp.x - gw) / 2.0 + 6, 66), PixUI.GOLD)
	PixUI.text(self, Vector2((vp.x - gw) / 2.0 + 16, 64), gt, PixUI.GOLD)
	var e := _ease_open()
	var lw := 232.0
	var cw := 190.0
	var x0 := roundf((vp.x - (lw + 14.0 + cw)) / 2.0 + (1.0 - e) * -16.0)
	var y := 88.0
	var rh := 30.0
	var n := offers.size()
	sel = clampi(sel, 0, n)
	for i in n + 1:
		var is_sel := i == sel
		var r := Rect2(x0, y, lw, rh - 3.0 if i < n else 22.0)
		if i == n:
			r.position.y += 4.0
		var edge := PixUI.GOLD if is_sel else PixUI.EDGE.darkened(0.35)
		PixUI.panel(self, r, edge, PixUI.INK2 if is_sel else PixUI.INK, false)
		if is_sel:
			PixUI.text(self, Vector2(r.position.x - 10 + sin(_t * 8.0) * 2.0, r.position.y + r.size.y / 2.0 - 6.0), "→", PixUI.GOLD, 1, HORIZONTAL_ALIGNMENT_LEFT, -1.0, 2)
		if i == n:
			var rc := Pazar.yenile_fiyat(int(bz.rerolls))
			var can_r := gold >= rc
			PixUI.text(self, r.position + Vector2(8, 4), "Malları yenile", PixUI.TEXT if can_r else PixUI.DIM)
			_price(r, rc, can_r)
			break
		var o: Dictionary = offers[i]
		var sold := bool(o["satildi"])
		var fiyat := int(o["fiyat"])
		var can := gold >= fiyat and not sold
		var tur := String(o["tur"])
		var it: Dictionary = o["item"]
		var name_col := PixUI.TEXT
		var sub := ""
		var ib := Rect2(r.position.x + 3, r.position.y + 3, 40, r.size.y - 6)
		PixUI.rect(self, ib, Color(0, 0, 0, 0.25))
		if tur == "esya":
			name_col = Color.from_string(Data.items["rarities"][int(it["rarity"])]["color"], PixUI.TEXT)
			sub = "%s · %s" % [CAT_TXT.get(String(it["cat"]), ""), String(Data.items["rarities"][int(it["rarity"])]["name"])]
			if bool(o.get("ust", false)):
				sub += " · seçme"
			PixUI.weapon(self, it, ib.get_center(), ib.size - Vector2(4, 4))
		elif tur == "sifa":
			name_col = Color(0.6, 1.0, 0.75)
			sub = "şifa"
			PixUI.icon(self, "sise", ib.get_center() - Vector2(6, 6), Color(0.45, 0.95, 0.8), 2)
		else:
			name_col = PixUI.GOLD
			sub = "stat tomarı"
			if TomarV2.on() and TomarV2.has("ui_tomar"):
				TomarV2.ui(self, "ui_tomar", ib.get_center() + Vector2(0, 1), ib.size.x + 2.0, Color(1, 1, 1, 1.0 if not bool(o["satildi"]) else 0.4))   # v34
			else:
				PixUI.icon(self, "tilsim", ib.get_center() - Vector2(6, 6), PixUI.GOLD, 2)
		var tx := r.position.x + 48.0
		var nm := Pazar.ad(o)
		var full_nm := nm
		while PixUI.width(nm + "…") > lw - 110.0 and nm.length() > 4:
			nm = nm.substr(0, nm.length() - 1)
		if nm != full_nm:
			nm += "…"
		PixUI.text(self, Vector2(tx, r.position.y + 2), nm, name_col if not sold else Color(name_col, 0.4))
		var info := sub
		var info_col := PixUI.DIM
		if tur == "esya" and String(it["cat"]) == "weapons" and not sold:
			# kuşanılan (aynı yuva türündeki) silaha göre SnH farkı
			var d := _eff_dps(it)
			var cur: Dictionary = R["slots"].get(level.natural_slot(it), {})
			info = "SnH %s" % ItemGen.fmt(d)
			if not cur.is_empty() and String(cur.get("cat", "")) == "weapons":
				var dd := d - _eff_dps(cur)
				# v34: fark yüzdesiyle (kuşanılan aynı yuva silahına göre)
				var pc := int(round(dd / maxf(0.01, _eff_dps(cur)) * 100.0))
				info += ("  ▲ +%s (+%%%d)" if dd >= 0.0 else "  ▼ %s (-%%%d)") % [ItemGen.fmt(dd), absi(pc)]
				info_col = PixUI.GOOD if dd >= 0.0 else PixUI.BAD
			elif cur.is_empty():
				info += "  · boş yuva"
				info_col = PixUI.GOOD
		elif tur == "esya" and not sold:
			# v34: kalkan / teçhizat: aynı yuvadakinden güçlüyse yeşil ▲ (Pazar.iyilesme)
			var iy := Pazar.iyilesme(it)
			if iy >= 1.1:
				info += ("  ▲ +%%%d" % int(round((iy - 1.0) * 100.0))) if iy < 1.99 else "  ▲ boş yuva"
				info_col = PixUI.GOOD
		if tur == "esya" and not sold:
			# v34: yeşil iyileşme rozeti (simgenin köşesi) ve "Bezirgân'ın gözdesi" damgası
			if Pazar.iyilesme(it) >= 1.1:
				var bc := Vector2(ib.end.x - 4.0, ib.position.y + 4.0)
				draw_circle(bc, 4.6, Color(0.05, 0.12, 0.05, 0.9))
				draw_circle(bc, 3.8, PixUI.GOOD)
				draw_colored_polygon(PackedVector2Array([bc + Vector2(0, -2.4), bc + Vector2(2.3, 1.6), bc + Vector2(-2.3, 1.6)]), Color(0.04, 0.12, 0.04))
			if bool(o.get("gozde", false)):
				var gw2 := PixUI.width("GÖZDE") + 8.0
				var gr := Rect2(r.end.x - gw2 - 4.0, r.position.y - 4.0, gw2, 10.0)
				draw_rect(gr, Color(0.55, 0.32, 0.06, 0.95))
				draw_rect(gr, PixUI.GOLD, false, 1.0)
				PixUI.text(self, gr.position + Vector2(0, -1), "GÖZDE", Color(1.0, 0.95, 0.75), 1, HORIZONTAL_ALIGNMENT_CENTER, gw2, 0)
		PixUI.text(self, Vector2(tx, r.position.y + 13), info, info_col if not sold else Color(PixUI.DIM, 0.4), 1, HORIZONTAL_ALIGNMENT_LEFT, -1.0, 0)
		if sold:
			var sc := Color(0.86, 0.24, 0.2, 0.95)
			PixUI.text(self, Vector2(r.position.x, r.position.y + 7), _up("Satıldı"), sc, 1, HORIZONTAL_ALIGNMENT_RIGHT, lw - 10, 2)
			draw_line(Vector2(tx - 2, r.position.y + 9), Vector2(r.end.x - 70, r.position.y + 9), Color(sc, 0.6), 1.0)
		else:
			_price(r, fiyat, can)
		y += rh
	# sağ: seçili malın kartı
	var cx := x0 + lw + 14.0
	var cy := 96.0
	if sel < n:
		var o2: Dictionary = offers[sel]
		if String(o2["tur"]) == "esya":
			var it2: Dictionary = o2["item"]
			var cur2: Dictionary = R["slots"].get(level.natural_slot(it2), {})
			_draw_card(it2, Vector2(cx, cy), ("BEZİRGÂN'IN GÖZDESİ" if bool(o2.get("gozde", false)) else "SATILIK") if not bool(o2["satildi"]) else "SATILDI", cur2)
		else:
			var lines := PixUI.wrap(Pazar.aciklama(o2), cw - 14.0)
			var h := 30.0 + lines.size() * 10.0
			PixUI.panel(self, Rect2(cx, cy, cw, h), PixUI.GOLD.darkened(0.2))
			PixUI.text(self, Vector2(cx + 6, cy + 5), Pazar.ad(o2), PixUI.GOLD, 1, HORIZONTAL_ALIGNMENT_LEFT, -1.0, 1)
			var ly := cy + 20.0
			for l in lines:
				PixUI.text(self, Vector2(cx + 6, ly), l, PixUI.TEXT, 1, HORIZONTAL_ALIGNMENT_LEFT, -1.0, 0)
				ly += 10.0
			if String(o2["tur"]) == "sifa":
				PixUI.text(self, Vector2(cx + 6, ly + 2), "Şişe %d / %d" % [int(R["flasks"]), int(R["max_flasks"])], PixUI.DIM, 1, HORIZONTAL_ALIGNMENT_LEFT, -1.0, 0)
	else:
		var tl := PixUI.wrap("Sartak denklerini çözer, bütün mallar yeniden yuvarlanır (satılanlar da). Her yenileme daha pahalı.", cw - 14.0)
		PixUI.panel(self, Rect2(cx, cy, cw, 12.0 + tl.size() * 10.0), PixUI.EDGE)
		var ty := cy + 6.0
		for l in tl:
			PixUI.text(self, Vector2(cx + 6, ty), l, PixUI.TEXT, 1, HORIZONTAL_ALIGNMENT_LEFT, -1.0, 0)
			ty += 10.0
	# onay
	if tuccar_onay and sel < n:
		var o3: Dictionary = offers[sel]
		var q := "%s — %d altın. Satın alınsın mı?" % [Pazar.ad(o3), int(o3["fiyat"])]
		var qw := PixUI.width(q) + 30.0
		var qr := Rect2((vp.x - qw) / 2.0, vp.y - 62.0, qw, 20.0)
		PixUI.fancy_panel(self, qr, PixUI.GOLD, PixUI.INK2)
		PixUI.text(self, Vector2(qr.position.x, qr.position.y + 4), q, PixUI.GOLD, 1, HORIZONTAL_ALIGNMENT_CENTER, qw, 2)
		_hint(vp, [["Boşluk", "evet, al"], ["Esc", "vazgeç"]])
	else:
		if flash_t > 0.0 and flash_msg != "":
			PixUI.text(self, Vector2(0, vp.y - 50), flash_msg, Color(PixUI.GOLD, clampf(flash_t, 0.0, 1.0)), 1, HORIZONTAL_ALIGNMENT_CENTER, vp.x, 2)
		_hint(vp, [["W/S", "seç"], ["Boşluk", "satın al"], ["Esc", "ayrıl"]])


# ------------------------------------------------------------------ v32 Bengisu Usta (konak)
const USTA_COL := Color(0.55, 1.0, 0.85)


func _draw_usta(vp: Vector2) -> void:
	## Usta: solda adım listesi (silah → hizmet → seçenek → sonuç), sağda seçili silahın kartı; sonuçta yeni kart
	## eskisiyle karşılaştırmalı (SnH ▲ / ▼) ve üstüne basılan mürekkep damgası.
	_dim(vp, 0.8, Color(0.02, 0.04, 0.035))
	if level == null or Game.run.is_empty():
		return
	var R: Dictionary = Game.run
	var biome_id := String(level.biome.get("id", "")) if level.get("biome") != null else ""
	_title(vp, 20, _up(Usta.ad()), USTA_COL, Usta.soz(biome_id, "usta"))
	var gold := int(R.get("gold", 0))
	var gt := "%d altın" % gold
	var gw := PixUI.width(gt) + 26.0
	PixUI.panel(self, Rect2((vp.x - gw) / 2.0, 62, gw, 15), PixUI.GOLD)
	PixUI.icon(self, "altin", Vector2((vp.x - gw) / 2.0 + 6, 66), PixUI.GOLD)
	PixUI.text(self, Vector2((vp.x - gw) / 2.0 + 16, 64), gt, PixUI.GOLD)
	var e := _ease_open()
	var lw := 232.0
	var cw := 190.0
	var x0 := roundf((vp.x - (lw + 14.0 + cw)) / 2.0 + (1.0 - e) * -16.0)
	var cx := x0 + lw + 14.0
	var cy := 96.0
	# adım izi
	var steps := ["silah", "hizmet", "seçim", "sonuç"]
	var bx := x0
	for i in steps.size():
		var on: bool = i == usta_adim
		var done: bool = i < usta_adim
		var sc := USTA_COL if on else (Color(USTA_COL, 0.55) if done else PixUI.DIM)
		var st := "%d. %s" % [i + 1, steps[i]]
		PixUI.text(self, Vector2(bx, 80), st, sc, 1, HORIZONTAL_ALIGNMENT_LEFT, -1.0, 1 if on else 0)
		bx += PixUI.width(st) + 16.0
	var y := 92.0
	var rh := 30.0
	var it: Dictionary = R["slots"].get(usta_slot, {}) if usta_slot != "" else {}
	match usta_adim:
		0:
			var sl := Usta.silahlar()
			sel = clampi(sel, 0, maxi(0, sl.size() - 1))
			if sl.is_empty():
				PixUI.text(self, Vector2(x0, y + 10), "Kuşanılı silahın yok.", PixUI.DIM, 1, HORIZONTAL_ALIGNMENT_LEFT, -1.0, 0)
			for i in sl.size():
				var w_it: Dictionary = R["slots"][sl[i]]
				var is_sel := i == sel
				var r := Rect2(x0, y, lw, rh - 3.0)
				_usta_row(r, is_sel)
				var ib := Rect2(r.position.x + 3, r.position.y + 3, 40, r.size.y - 6)
				PixUI.rect(self, ib, Color(0, 0, 0, 0.25))
				PixUI.weapon(self, w_it, ib.get_center(), ib.size - Vector2(4, 4))
				var rc := Color.from_string(Data.items["rarities"][int(w_it["rarity"])]["color"], PixUI.TEXT)
				PixUI.text(self, Vector2(r.position.x + 48.0, r.position.y + 2), _kisalt(String(w_it["name"]), lw - 60.0), rc)
				PixUI.text(self, Vector2(r.position.x + 48.0, r.position.y + 13), "%s · SnH %s · nakış %d/%d · kalite %%%d" % [SLOT_NAMES[sl[i]], ItemGen.fmt(_eff_dps(w_it)), Usta.nakis_sayi(w_it), Usta.max_nakis(w_it), int(w_it["quality"])], PixUI.DIM, 1, HORIZONTAL_ALIGNMENT_LEFT, -1.0, 0)
				y += rh
			if not sl.is_empty():
				it = R["slots"][sl[sel]]
			_usta_note(x0, y + 6.0, lw, "Usta yalnızca silaha bakar (yakın / uzak). Hizmetler altınla; fiyat derinlik ve nadirlikle artar.")
		1:
			var hs := Usta.hizmetler(it)
			sel = clampi(sel, 0, hs.size() - 1)
			for i in hs.size():
				var h: Dictionary = hs[i]
				var is_sel := i == sel
				var r := Rect2(x0, y, lw, rh - 3.0)
				_usta_row(r, is_sel)
				var ok := bool(h["uygun"])
				var can := ok and gold >= int(h["fiyat"])
				PixUI.text(self, Vector2(r.position.x + 8, r.position.y + 2), String(h["ad"]), (PixUI.TEXT if can else PixUI.DIM) if ok else Color(PixUI.DIM, 0.5))
				var sub := ""
				var sub_col := PixUI.DIM
				if not ok:
					sub = String(h["neden"])
				elif float(h["sans"]) >= 0.0:
					sub = "şans %%%d" % int(round(float(h["sans"]) * 100.0))
					sub_col = PixUI.GOOD if float(h["sans"]) >= 0.5 else PixUI.GOLD
				elif String(h["id"]) == "nakis":
					sub = "3 aday, birini seçersin (nadir ★ pahalı)"
				elif String(h["id"]) == "unsur":
					sub = "rastgele ya da seçerek"
				elif String(h["id"]) == "dovme":
					sub = "%d. dövme" % (int(it.get("usta_dovme", 0)) + 1)
				else:
					sub = "kumar: iyi de gelir kötü de"
				PixUI.text(self, Vector2(r.position.x + 8, r.position.y + 13), sub, sub_col if ok else Color(PixUI.DIM, 0.6), 1, HORIZONTAL_ALIGNMENT_LEFT, -1.0, 0)
				if ok:
					var ft := ("%d" % int(h["fiyat"])) if String(h["id"]) != "nakis" else ("%d+" % int(h["fiyat"]))
					var pc := PixUI.GOLD if can else Color(0.62, 0.5, 0.48)
					var tw := PixUI.width(ft)
					PixUI.icon(self, "altin", Vector2(r.end.x - 12.0 - tw - 9.0, r.position.y + r.size.y / 2.0 - 3.0), pc, 1, false)
					PixUI.text(self, Vector2(r.position.x, r.position.y + r.size.y / 2.0 - 6.0), ft, pc, 1, HORIZONTAL_ALIGNMENT_RIGHT, r.size.x - 8.0, 2)
				y += rh
			_usta_note(x0, y + 4.0, lw, String(hs[sel]["aciklama"]))
		2:
			sel = clampi(sel, 0, maxi(0, usta_secs.size() - 1))
			for i in usta_secs.size():
				var o: Dictionary = usta_secs[i]
				var is_sel := i == sel
				var r := Rect2(x0, y, lw, rh - 3.0)
				_usta_row(r, is_sel)
				var can := gold >= int(o["fiyat"])
				var nc := PixUI.TEXT if can else PixUI.DIM
				if usta_hid == "unsur" and String(o["veri"]) != "":
					nc = Unsur.color(String(o["veri"])).lightened(0.15) if can else PixUI.DIM
					Unsur.glyph(self, String(o["veri"]), Vector2(r.position.x + 12, r.position.y + 13), 5.0, Unsur.color(String(o["veri"])), _t)
				elif usta_hid == "nakis" and bool((o["veri"] as Dictionary).get("nadir", false)):
					nc = Color(1.0, 0.85, 0.45) if can else PixUI.DIM
				var tx := r.position.x + (24.0 if usta_hid == "unsur" and String(o["veri"]) != "" else 8.0)
				PixUI.text(self, Vector2(tx, r.position.y + 2), String(o["ad"]), nc)
				PixUI.text(self, Vector2(tx, r.position.y + 13), _kisalt(String(o["aciklama"]), lw - 80.0), PixUI.DIM, 1, HORIZONTAL_ALIGNMENT_LEFT, -1.0, 0)
				_price(r, int(o["fiyat"]), can)
				y += rh
			_usta_note(x0, y + 4.0, lw, "Nakış adayları bu konakta yuvarlandı; nadir (★) olanlar daha güçlü ve pahalı." if usta_hid == "nakis" else "Unsur silahın ruhudur: vuruşta tutuşturur, dondurur, şimşek indirir, töz damgalar ya da kök dolar. Eskisi silinir.")
		3:
			var s := usta_sonuc
			var once: Dictionary = s.get("once", {})
			var sonra: Dictionary = s.get("sonra", it)
			var iyi := bool(s.get("iyi", true))
			var kotu := bool(s.get("kotu", false))
			var pcol := PixUI.BAD if kotu else (USTA_COL if iyi else PixUI.GOLD)
			var lines := PixUI.wrap(String(s.get("msg", "")), lw - 16.0)
			var ph := 28.0 + lines.size() * 10.0 + 44.0
			PixUI.fancy_panel(self, Rect2(x0, y, lw, ph), pcol, PixUI.INK2)
			PixUI.text(self, Vector2(x0 + 8, y + 5), "%s · %d altın" % [String(Usta.AD.get(usta_hid, "")), int(s.get("fiyat", 0))], pcol, 1, HORIZONTAL_ALIGNMENT_LEFT, -1.0, 1)
			var ly := y + 18.0
			for l in lines:
				PixUI.text(self, Vector2(x0 + 8, ly), l, PixUI.TEXT, 1, HORIZONTAL_ALIGNMENT_LEFT, -1.0, 0)
				ly += 10.0
			PixUI.divider(self, x0 + 8, ly + 3, lw - 16, pcol.darkened(0.3))
			ly += 8.0
			if not once.is_empty():
				var d0 := _eff_dps(once)
				var d1 := _eff_dps(sonra)
				var dd := d1 - d0
				var ds := ("▲ +%s (+%%%d)" if dd >= 0.0 else "▼ %s (-%%%d)") % [ItemGen.fmt(dd), absi(int(round(dd / maxf(0.01, d0) * 100.0)))]
				PixUI.text(self, Vector2(x0 + 8, ly), "SnH %s → %s" % [ItemGen.fmt(d0), ItemGen.fmt(d1)], PixUI.TEXT, 1, HORIZONTAL_ALIGNMENT_LEFT, -1.0, 0)
				PixUI.text(self, Vector2(x0 + 8, ly), ds if absf(dd) > 0.05 else "SnH aynı", (PixUI.GOOD if dd >= 0.0 else PixUI.BAD) if absf(dd) > 0.05 else PixUI.DIM, 1, HORIZONTAL_ALIGNMENT_RIGHT, lw - 16.0, 0)
				ly += 10.0
				PixUI.text(self, Vector2(x0 + 8, ly), "Kalite %%%d → %%%d · nakış %d → %d · unsur %s → %s" % [int(once["quality"]), int(sonra["quality"]), Usta.nakis_sayi(once), Usta.nakis_sayi(sonra), _unsur_ad(once), _unsur_ad(sonra)], PixUI.DIM, 1, HORIZONTAL_ALIGNMENT_LEFT, -1.0, 0)
				ly += 10.0
				PixUI.text(self, Vector2(x0 + 8, ly), "Kalan altın: %d" % gold, PixUI.GOLD, 1, HORIZONTAL_ALIGNMENT_LEFT, -1.0, 0)
	# sağ: seçili silahın kartı (sonuçta yeni kart eskisiyle karşılaştırmalı) + damga
	if not it.is_empty():
		if usta_adim == 3 and not usta_sonuc.is_empty():
			var once2: Dictionary = usta_sonuc.get("once", {})
			var sonra2: Dictionary = usta_sonuc.get("sonra", it)
			_draw_card(sonra2, Vector2(cx, cy), "YENİ HÂLİ", once2)
			_usta_damga(Vector2(cx + cw / 2.0, cy + 40.0), String(usta_sonuc.get("damga", "")), bool(usta_sonuc.get("kotu", false)), bool(usta_sonuc.get("iyi", true)))
		else:
			_draw_card(it, Vector2(cx, cy), "SİLAHIN")
	# onay / ipucu
	if usta_onay:
		var q := ""
		if usta_adim == 2 and sel < usta_secs.size():
			q = "%s — %d altın. Usta işlesin mi?" % [String(usta_secs[sel]["ad"]), int(usta_secs[sel]["fiyat"])]
		else:
			var hs2 := Usta.hizmetler(it)
			var h2: Dictionary = hs2[clampi(sel, 0, hs2.size() - 1)]
			q = "%s — %d altın. Usta işlesin mi?" % [String(h2["ad"]), int(h2["fiyat"])]
		var qw := PixUI.width(q) + 30.0
		var qr := Rect2((vp.x - qw) / 2.0, vp.y - 62.0, qw, 20.0)
		PixUI.fancy_panel(self, qr, PixUI.GOLD, PixUI.INK2)
		PixUI.text(self, Vector2(qr.position.x, qr.position.y + 4), q, PixUI.GOLD, 1, HORIZONTAL_ALIGNMENT_CENTER, qw, 2)
		_hint(vp, [["Boşluk", "evet"], ["Esc", "vazgeç"]])
	else:
		if flash_t > 0.0 and flash_msg != "" and usta_adim != 3:
			PixUI.text(self, Vector2(0, vp.y - 50), flash_msg, Color(PixUI.GOLD, clampf(flash_t, 0.0, 1.0)), 1, HORIZONTAL_ALIGNMENT_CENTER, vp.x, 2)
		match usta_adim:
			0:
				_hint(vp, [["W/S", "silah"], ["Boşluk", "seç"], ["Esc", "ayrıl"]])
			1:
				_hint(vp, [["W/S", "hizmet"], ["Boşluk", "seç"], ["Esc", "geri"]])
			2:
				_hint(vp, [["W/S", "seçenek"], ["Boşluk", "işle"], ["Esc", "geri"]])
			_:
				_hint(vp, [["Boşluk", "başka hizmet"], ["Esc", "geri"]])


func _usta_row(r: Rect2, is_sel: bool) -> void:
	PixUI.panel(self, r, USTA_COL if is_sel else PixUI.EDGE.darkened(0.35), PixUI.INK2 if is_sel else PixUI.INK, false)
	if is_sel:
		PixUI.text(self, Vector2(r.position.x - 10 + sin(_t * 8.0) * 2.0, r.position.y + r.size.y / 2.0 - 6.0), "→", USTA_COL, 1, HORIZONTAL_ALIGNMENT_LEFT, -1.0, 2)


func _usta_note(x: float, y: float, w: float, s: String) -> void:
	var tl := PixUI.wrap(s, w - 14.0)
	PixUI.panel(self, Rect2(x, y, w, 12.0 + tl.size() * 10.0), PixUI.EDGE)
	var ty := y + 6.0
	for l in tl:
		PixUI.text(self, Vector2(x + 6, ty), l, PixUI.TEXT, 1, HORIZONTAL_ALIGNMENT_LEFT, -1.0, 0)
		ty += 10.0


func _unsur_ad(it: Dictionary) -> String:
	var u := Unsur.of(it)
	return String(Unsur.DEF[u]["ad"]) if u != "" else "—"


func _kisalt(s: String, w: float) -> String:
	var t := s
	while PixUI.width(t + "…") > w and t.length() > 4:
		t = t.substr(0, t.length() - 1)
	return t if t == s else t + "…"


func _usta_damga(c: Vector2, txt: String, kotu: bool, iyi: bool) -> void:
	## Mürekkep damgası: kartın üstüne büyükten küçülerek basılır (0,35 sn), hafif eğik; kötü sonuç mor, tutmayan soluk
	if txt == "":
		return
	var k := clampf(usta_damga_t / 0.35, 0.0, 1.0)
	var ease_k := 1.0 - pow(1.0 - k, 3.0)
	var scl := lerpf(2.2, 1.0, ease_k)
	var a := lerpf(0.0, 1.0, clampf(k * 2.0, 0.0, 1.0))
	var col := Color(0.86, 0.24, 0.2) if (iyi and not kotu) else (Color(0.6, 0.3, 0.9) if kotu else Color(0.55, 0.5, 0.5))
	var w := PixUI.width(txt, 1) + 24.0
	var rot := -0.16
	draw_set_transform(c * MENU_SCALE, rot, Vector2.ONE * MENU_SCALE * scl)
	InkUI.splat(self, Vector2.ZERO, 26.0, Color(col, 0.22 * a), 0.7)
	InkUI.seal(self, Rect2(-w / 2.0, -11.0, w, 22.0), Color(col, a))
	PixUI.text(self, Vector2(-w / 2.0, -5.0), txt, Color(col.lightened(0.1), a), 1, HORIZONTAL_ALIGNMENT_CENTER, w, 1)
	draw_set_transform(Vector2.ZERO, 0.0, Vector2.ONE * MENU_SCALE)
	if k >= 1.0 and usta_damga_t < 0.6:
		# basılış anında mürekkep sıçrantısı
		var kk := (usta_damga_t - 0.35) / 0.25
		for i in 6:
			var ang := float(i) / 6.0 * TAU + 0.4
			var p := c + Vector2.from_angle(ang) * (18.0 + 26.0 * kk)
			draw_circle(p, 2.2 * (1.0 - kk), Color(col, 0.8 * (1.0 - kk)), true, -1.0, true)


func _price(r: Rect2, v: int, can: bool) -> void:
	var ct := "%d" % v
	var col := PixUI.GOLD if can else Color(0.62, 0.5, 0.48)
	var tw := PixUI.width(ct)
	PixUI.icon(self, "altin", Vector2(r.end.x - 12.0 - tw - 9.0, r.position.y + r.size.y / 2.0 - 3.0), col, 1, false)
	PixUI.text(self, Vector2(r.position.x, r.position.y + r.size.y / 2.0 - 6.0), ct, col, 1, HORIZONTAL_ALIGNMENT_RIGHT, r.size.x - 8.0, 2)



# ================================================================== v12 göstergeleri
func _draw_v12(vp: Vector2, pl: Node, kx: float, y0: float) -> void:
	# ---- don (G): emilmiş seçkin ruhu (v25: kam gücü halkası Üç Âlem'le birlikte kaldırıldı; don halkası onun yerinde)
	var ay := y0 + 15.0
	var dx := kx + 36.0
	var has_don: bool = pl.don_kind != ""
	var dcol := DonForm.COL
	InkHUD.ring(self, Vector2(dx, ay), 1.0 if has_don else 0.0, Color(dcol, 0.6 + 0.4 * sin(_t * 6.0)), "ruh", dcol if has_don else Color(dcol, 0.3), "G", dcol, has_don)
	if has_don:
		PixUI.text(self, Vector2(dx - 60, y0 - 11), String(Data.enemy_def(pl.don_kind).get("name", "")), dcol, 1, HORIZONTAL_ALIGNMENT_CENTER, 120, 2)
	# ---- don başlığı ve süre
	var py := 30.0
	if pl.don_on:
		var wx2 := vp.x / 2.0 - 80.0
		PixUI.panel(self, Rect2(wx2, py, 160, 26), dcol)
		PixUI.text(self, Vector2(wx2, py + 2), "DON: %s  %.1f" % [_up(pl.don.display_name()), pl.don.t], dcol.lightened(0.3), 1, HORIZONTAL_ALIGNMENT_CENTER, 160, 1)
		PixUI.bar(self, Rect2(wx2 + 6, py + 16, 148, 4), clampf(pl.don.t / pl.don.dur, 0.0, 1.0), dcol)
		var moves := {"kurt": "J atılış · K sıçrayış", "kalkan": "J kalkan vuruşu · K siper", "kabuk": "J yuvarlan · K kabuğa çekil",
			"hucum": "J hücum · K ezme", "dev": "J yere çak · K sarsıntı", "kanat": "Boşluk uç · J pike · K tüy", "buyucu": "J büyü · K ışınlan"}
		PixUI.text(self, Vector2(0, py + 30), String(moves.get(pl.don.arch, "")), Color(dcol, 0.85), 1, HORIZONTAL_ALIGNMENT_CENTER, vp.x)
	# ---- usul ölçeri (sağ): müziğin aksak usulü; vuruşlar çizgi, imleç akar
	if not level.hub:
		var u := Ses.usul_now()
		if not u.is_empty():
			if pl.usul_streak != _last_streak:
				if pl.usul_streak > _last_streak:
					_usul_flash = 1.0
				_last_streak = pl.usul_streak
			InkHUD.usul(self, vp, u, pl.usul_streak, _usul_flash)
	# ---- ad ve bekleyen destan (can çubuğunun yanında)
	var tt := Adlar.title()
	var tx := 204.0
	if tt != "":
		PixUI.text(self, Vector2(tx, 10), "Bengü «%s»" % tt, PixUI.GOLD, 1, HORIZONTAL_ALIGNMENT_LEFT, -1.0, 2)
	var pend := Adlar.pending().size()
	if pend > 0:
		PixUI.text(self, Vector2(tx, 22), "destan: %d · Ozan'a anlat" % pend, Color(PixUI.GOLD, 0.6 + 0.4 * sin(_t * 4.0)), 1, HORIZONTAL_ALIGNMENT_LEFT, -1.0, 2)


func _draw_ad(vp: Vector2) -> void:
	## Ad Koyma Töreni: Ozan destanı anlatır, yiğide adını koyar
	_dim(vp, 0.86, Color(0.06, 0.035, 0.02))
	if not Adlar.ADLAR.has(ad_id):
		return
	var a: Array = Adlar.ADLAR[ad_id]
	_title(vp, 34, "AD KOYMA TÖRENİ", PixUI.GOLD)
	var k := clampf(ad_t / 0.9, 0.0, 1.0)
	var l1 := "«Ozan kopuzunu eline aldı, boy boylayıp soy soylayıp şöyle dedi:»"
	PixUI.text(self, Vector2(0, 78), l1, Color(0.9, 0.85, 0.75, k), 1, HORIZONTAL_ALIGNMENT_CENTER, vp.x)
	var l2 := "«Bu yiğit %s. Adını ben koyayım:»" % String(a[1]).to_lower()
	PixUI.text(self, Vector2(0, 94), l2, Color(0.95, 0.9, 0.8, clampf((ad_t - 0.4) / 0.6, 0.0, 1.0)), 1, HORIZONTAL_ALIGNMENT_CENTER, vp.x)
	var kn := clampf((ad_t - 0.9) / 0.5, 0.0, 1.0)
	if kn > 0.0:
		InkHUD.ad_backdrop(self, vp, kn, String(a[0]))
		PixUI.text(self, Vector2(0, 124), _up(String(a[0])), Color(1.0, 0.88, 0.5, kn), 3, HORIZONTAL_ALIGNMENT_CENTER, vp.x, 2)
		PixUI.text(self, Vector2(0, 176), "«Adın %s olsun!»" % String(a[0]), Color(1.0, 0.95, 0.85, kn), 1, HORIZONTAL_ALIGNMENT_CENTER, vp.x)
		PixUI.text(self, Vector2(0, 200), "Ad gücü: " + String(a[2]), Color(0.7, 1.0, 0.85, kn), 1, HORIZONTAL_ALIGNMENT_CENTER, vp.x)
		var book: Dictionary = Game.meta.get("adlar", {})
		PixUI.text(self, Vector2(0, 220), "Ad Defteri: %d / %d ad" % [book.size(), Adlar.ADLAR.size()], PixUI.DIM, 1, HORIZONTAL_ALIGNMENT_CENTER, vp.x)
	if ad_t > 1.2:
		var more := not Adlar.pending().is_empty()
		_hint(vp, [["Boşluk", "sıradaki destan" if more else "devam"]])
