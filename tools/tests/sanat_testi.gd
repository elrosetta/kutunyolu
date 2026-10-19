extends Node
## v27 Savaş Sanatları testi (betikli girdi; Input.action_press ile oyuncunun kendi yolundan):
##   godot --headless --path . --quit-after 99999 -- --sanat --boss --muhur=0
## Ölçer: her sanat kuşanılıp mankenlere tetiklenir (bedel / bekleme / isabet / hasar / takılma), sınıf kuralı (gri),
## bekleme ve nişan yetmezliği reddi, Kasırga ek turu, Demir Duruş karşılığı, nişan kazancı (vuruş, öldürme, çarpışma,
## kusursuz kaçış), Alp Ata'nın öğretmesi ve kalıcı kayıt (kaydet / yeniden yükle), Sanat Tomarı.
## Kare şeridi (headless değil, --fixed-fps 60): -- --sanat --boss --sanat_kare=<klasör> [--sanat_tek=id] : her sanatın
## HER karesi oyuncunun çevresinden 640x400 kırpılmış PNG (<klasör>/<sanat>_<kare>.png).
## v28 Göğe Yükseliş: 3 sıradan + 1 seçkin: sıradanlar kalkar, tepede kilitli kalır, yere çakılır (zeminde, duvar /
## tavan içinde değil), seçkin kalkmaz; alçak tavanda (ızgaraya geçici tavan) kaldırma tavanın altında kalır.
## Kare şeridinde Göğe Yükseliş bu dizilişle çekilir (goge_yukselis_NNN.png).
## Efekt önizlemesi (headless değil): -- --sanat --boss --sanat_fx=<klasör> : SanatFX bileşimleri oyuncu gizliyken tek
## tek, her 2 karede kırpılmış PNG (<klasör>/fx_<ad>_<kare>.png).
## v31 kombo sanatları (Kurt Dansı, Evren Kuyruğu, Tengri Çarkı, Yer Yarığı, Akıncı Akını): 3 sıradan + 1 seçkin; açık alanda
## ritim TAM (halka kapanırken T), alçak tavanda erken basış (kaçar); sıradanlar kilitlenir / kalkar (Akıncı: çivilenir),
## seçkin kalkmaz, sonda hepsi yerde, duvar / tavan içinde değil, kilit kalmamış, tavanı aşan kare yok. Gerçek duvar
## kenarında Tengri Çarkı (duvar sekmesi) ve Kurt Dansı (atılış duvara girmez). Kare şeridinde bu dizilişle çekilir.
## Çıktı: "[sanat] ..." satırları, sonda "[sanat] SONUC GECTI|KALDI hata=N" ve "[sanat] TAKILMA=n".

var main: Node
var lv: Node
var pl: Player
var spot := Vector2.ZERO
var errors := 0
var stuck := 0
var snap_dir := ""
var only := ""
var fx_dir := ""
var _meta_bak: Dictionary = {}

const WEAPON := {"kasirga": "alp_kilici", "bir_cekis": "dag_cekici", "ay_hilali": "alp_kilici", "goge_yukselis": "kargi",
	"bozkurt_atilisi": "yatagan", "kam_darbesi": "kement", "ok_yagmuru": "alp_kilici", "demir_durus": "ulu_kilic",
	"kurt_dansi": "ikiz_bicak", "evren_kuyrugu": "teber", "tengri_carki": "kement", "yer_yarigi": "gurz", "akinci_akini": "alp_kilici"}
## v31 kombo testinin dizilişi: 3 sıradan (dx) + seçkin (dx)
const KOMBO := {"kurt_dansi": [[40.0, 92.0, 150.0], 66.0], "evren_kuyrugu": [[22.0, 50.0, -36.0], 38.0],
	"tengri_carki": [[60.0, 120.0, -70.0], 150.0], "yer_yarigi": [[26.0, 54.0, -40.0], 82.0],
	"akinci_akini": [[70.0, 105.0, 140.0], 122.0]}
## v31: kalkış eşiği (px; açık alan / alçak tavan) ve kilitlenmesi beklenen sıradan sayısı
const KOMBO_KALK := {"kurt_dansi": [20.0, 8.0], "evren_kuyrugu": [40.0, 10.0], "tengri_carki": [18.0, 8.0], "yer_yarigi": [30.0, 10.0],
	"akinci_akini": [-1.0, -1.0]}
const ACTS := ["saldiri1", "saldiri2", "zipla", "yuvarlan", "sag", "sol", "yukari", "asagi", "techizat1", "techizat2", "sise", "kut", "sanat"]
var CROP := Vector2i(640, 400)


func _ready() -> void:
	process_mode = Node.PROCESS_MODE_ALWAYS
	for arg in OS.get_cmdline_user_args():
		var a := String(arg)
		if a.begins_with("--sanat_kare="):
			snap_dir = a.trim_prefix("--sanat_kare=")
		elif a.begins_with("--sanat_fx="):
			fx_dir = a.trim_prefix("--sanat_fx=")
		elif a.begins_with("--sanat_tek="):
			only = a.trim_prefix("--sanat_tek=")
	_run.call_deferred()


func _p(s: String) -> void:
	print("[sanat] ", s)


func _err(s: String) -> void:
	errors += 1
	_p("HATA " + s)


func _f(n := 1) -> void:
	for i in n:
		await get_tree().physics_frame


func _release_all() -> void:
	for a in ACTS:
		Input.action_release(a)


func _tap(a: String, frames := 2) -> void:
	Input.action_press(a)
	await _f(frames)
	Input.action_release(a)


func _find_spot() -> Vector2:
	if "boss" in lv and lv.boss != null and is_instance_valid(lv.boss):
		lv.boss.remove_from_group("dusman")
		lv.boss.queue_free()
		lv.boss = null
		return Vector2(33 * Level.TS + 12, lv.surface_y(33) * Level.TS - 1)
	for x in range(20, Level.W - 30):
		var y0: int = lv.surface_y(x)
		var ok := true
		for dx in range(-9, 10):
			if lv.surface_y(x + dx) != y0:
				ok = false
				break
			for dy in range(1, 6):
				if lv.cell(x + dx, y0 - dy) == 1:
					ok = false
					break
			if not ok:
				break
		if ok:
			return Vector2(x * Level.TS + 12, y0 * Level.TS - 1)
	return Vector2(40 * Level.TS + 12, lv.surface_y(40) * Level.TS - 1)


func _clear_enemies() -> void:
	for e in get_tree().get_nodes_in_group("dusman"):
		e.remove_from_group("dusman")
		e.queue_free()


func _enemy(dx: float, kind := "kara_boru", hp := 99999.0) -> Enemy:
	var e: Enemy = lv.spawn_enemy(kind, spot + Vector2(dx, 0))
	e.max_hp = hp
	e.hp = hp
	e.speed = 0.0
	e.cd = 99.0
	e.aggro = false
	e.facing = -1 if dx > 0 else 1
	return e


func _reset(weapon: String, second := "turk_yayi") -> void:
	_release_all()
	_clear_enemies()
	Game.run["slots"]["melee"] = ItemGen.roll(weapon, 1, "demir", 0)
	Game.run["slots"]["second"] = ItemGen.roll(second, 1, "demir", 0) if second != "" else {}
	pl.on_equip()
	pl.global_position = spot
	pl.velocity = Vector2.ZERO
	pl.facing = 1
	pl.roll_t = 0.0
	pl.hurt_t = 0.0
	pl.inv_t = 0.0
	pl.melee_buf = 0.0
	pl.sanat.cd = 0.0
	pl.sanat.buf = 0.0
	Game.run["hp"] = float(Game.run["max_hp"])
	await _f(20)


func _idle_check(tag: String) -> void:
	_release_all()
	await _f(120)
	var bad: Array = []
	if not pl.atk.is_empty():
		bad.append("atk=%s" % pl.atk.get("phase", "?"))
	if pl.sanat.aktif():
		bad.append("sanat")
	if absf(Engine.time_scale - 1.0) > 0.01:
		bad.append("time_scale=%.2f" % Engine.time_scale)
	if pl.roll_t > 0.0:
		bad.append("roll")
	if not bad.is_empty():
		stuck += 1
		_p("TAKILDI %s: %s" % [tag, ", ".join(bad)])


var crop_shift := 0.0
var crop_world := Vector2.INF   # v31: kare şeridi kırpması dünyada sabit bir noktaya (kamera değil arena) ortalanır


func _crop_snap(path: String) -> void:
	await RenderingServer.frame_post_draw
	if snap_dir == "" or DisplayServer.get_name() == "headless":
		return
	var vp := pl.get_viewport()
	var img := vp.get_texture().get_image()
	if vp.use_hdr_2d:
		if img.get_format() != Image.FORMAT_RGBA8 and img.get_format() != Image.FORMAT_RGB8:
			img.convert(Image.FORMAT_RGBA8)
		img.linear_to_srgb()
	var sc := Vector2(img.get_size()) / vp.get_visible_rect().size
	var sp := pl.get_global_transform_with_canvas().origin * sc
	if crop_world != Vector2.INF:
		sp = (pl.get_viewport().get_canvas_transform() * crop_world) * sc
	var r := Rect2i(Vector2i(int(sp.x) - CROP.x / 2 + 70 + int(crop_shift * sc.x), int(sp.y) - CROP.y + 110), CROP)
	r.position = r.position.clamp(Vector2i.ZERO, img.get_size() - CROP)
	img.get_region(r).save_png(path)


# ---------------------------------------------------------------- bir sanatı tetikle
func _cast(id: String, n_enemies := 3, extra_turn := false, snap := false) -> Dictionary:
	SavasSanati.sec(id)
	var w: String = WEAPON.get(id, "alp_kilici")
	await _reset(w)
	var foes: Array = []
	var dxs := [34.0, 70.0, -40.0] if id != "ay_hilali" else [60.0, 140.0, 220.0]
	if id == "ok_yagmuru":
		dxs = [110.0, 130.0, 150.0]
	elif id == "akinci_akini":
		dxs = [70.0, 105.0, 140.0]
	for i in n_enemies:
		foes.append(_enemy(dxs[i % dxs.size()]))
	await _f(10)
	Game.run["nisan"] = SavasSanati.nisan_max()
	var n0 := SavasSanati.nisan()
	var hp0 := 0.0
	for e in foes:
		hp0 += e.hp
	var cost := SavasSanati.bedel_nisan(id)
	var started := false
	var frames := 0
	var ek_done := false
	var tag := "%s_%03d.png"
	Input.action_press("sanat")
	for i in 400:
		await _f()
		frames += 1
		if i == 1:
			Input.action_release("sanat")
		if pl.sanat.aktif():
			started = true
		if extra_turn and not ek_done and pl.sanat.aktif() and float(pl.sanat.cur["t"]) > 0.3:
			ek_done = true
			Input.action_press("sanat")
			await _f(2)
			Input.action_release("sanat")
			frames += 2
		if snap and snap_dir != "":
			await _crop_snap("%s/%s" % [snap_dir, tag % [id, frames]])
		if started and not pl.sanat.aktif() and (i > 60 or id != "ok_yagmuru"):
			if id == "ok_yagmuru" and i < 110:
				continue
			break
	var spent := n0 - SavasSanati.nisan()
	var dealt := 0.0
	for e in foes:
		dealt += hp0 / foes.size() - (e.hp if is_instance_valid(e) else 0.0)
	var res := {"started": started, "frames": frames, "spent": spent, "cost": cost, "cd": pl.sanat.cd,
		"hits": int(pl.sanat.stats["isabet"].get(id, 0)), "dealt": dealt}
	return res


func _run() -> void:
	await get_tree().create_timer(0.6).timeout
	lv = main.level
	pl = lv.player
	spot = _find_spot()
	_meta_bak = Game.meta.duplicate(true)
	pl.sanat.log_on = OS.get_cmdline_user_args().has("--sanat_iz")
	Game.meta["sanat_acik"] = SavasSanati.ids()
	_p("arena=%s sanat=%d" % [str(spot), SavasSanati.ids().size()])
	if fx_dir != "":
		await _fx_onizleme()
		_restore()
		get_tree().quit()
		return
	if snap_dir != "":
		await get_tree().create_timer(4.0).timeout   # bölüm başlığı sönsün
		await _snaps()
		_restore()
		get_tree().quit()
		return
	# ---------------------------------------------------------------- 1) her sanat
	for id in SavasSanati.ids():
		if only != "" and id != only:
			continue
		var before_hits := int(pl.sanat.stats["isabet"].get(id, 0))
		var r := await _cast(id, 3, id == "kasirga")
		var d := SavasSanati.def_of(id)
		var hits := int(r["hits"]) - before_hits
		_p("%s: basladi=%s kare=%d (%d ms) nisan=%.0f/%.0f bekleme=%.1f isabet=%d hasar=%.0f" % [id, str(r["started"]), int(r["frames"]),
			int(round(float(r["frames"]) * 1000.0 / 60.0)), float(r["spent"]), float(r["cost"]), float(r["cd"]), hits, float(r["dealt"])])
		if not r["started"]:
			_err("%s başlamadı" % id)
		var want: float = float(r["cost"])
		if id == "kasirga":
			want += float((d.get("ek_tur", [0.5]) as Array)[0]) * SavasSanati.birim()
		if absf(float(r["spent"]) - want) > 0.5:
			_err("%s nişan harcaması %.0f (beklenen %.0f)" % [id, float(r["spent"]), want])
		if float(r["cd"]) <= 0.0 or float(r["cd"]) > float(d.get("bekleme", 4.0)):
			_err("%s bekleme %.2f" % [id, float(r["cd"])])
		if (hits <= 0 or float(r["dealt"]) <= 0.0) and id != "demir_durus":   # Demir Duruş: karşılık aşağıda (4)
			_err("%s isabet yok" % id)
		if int(r["frames"]) > 330:
			_err("%s çok uzun (%d kare)" % [id, int(r["frames"])])
		if d.has("ritim_k") and int(r["frames"]) > 150:
			_err("%s kombo çok uzun (%d kare)" % [id, int(r["frames"])])
		await _idle_check("sanat/" + id)
	# ---------------------------------------------------------------- 1b) Göğe Yükseliş: kaldırma, kilit, çakılma
	if only == "" or only == "goge_yukselis":
		await _goge_kaldirma(false)
		await _goge_kaldirma(true)
	# ---------------------------------------------------------------- 1c) v31 kombo sanatları
	for id in KOMBO:
		if only != "" and id != only:
			continue
		await _kombo(id, false, false, "tam")
		await _kombo(id, true, false, "erken")
	if only == "" or only == "tengri_carki" or only == "kurt_dansi":
		await _duvar_testi()
	# ---------------------------------------------------------------- 2) Kasırga ek tur
	var tr := int(pl.sanat.stats["isabet"].get("kasirga", 0))
	SavasSanati.sec("kasirga")
	await _reset("alp_kilici")
	var e1 := _enemy(30.0)
	Game.run["nisan"] = SavasSanati.nisan_max()
	await _tap("sanat")
	await _f(25)
	await _tap("sanat")
	await _f(4)
	var turs := int(pl.sanat.cur.get("turs", 0)) if pl.sanat.aktif() else -1
	await _f(60)
	_p("kasirga ek tur: tur=%d isabet=%d" % [turs, int(pl.sanat.stats["isabet"].get("kasirga", 0)) - tr])
	if turs != 2:
		_err("kasırga ek tur %d" % turs)
	await _idle_check("sanat/kasirga_ek")
	e1.queue_free()
	# ---------------------------------------------------------------- 3) sınıf kuralı, bekleme, nişan yetmezliği
	SavasSanati.sec("bir_cekis")
	await _reset("kement")
	Game.run["nisan"] = SavasSanati.nisan_max()
	var red0 := int(pl.sanat.stats["red"].get("sinif", 0))
	await _tap("sanat")
	await _f(10)
	var uy := SavasSanati.uygun("bir_cekis")
	_p("sinif: Bir Çekiş + kement uygun=%s basladi=%s red=%d" % [str(uy), str(pl.sanat.aktif()), int(pl.sanat.stats["red"].get("sinif", 0)) - red0])
	if uy or pl.sanat.aktif() or int(pl.sanat.stats["red"].get("sinif", 0)) == red0:
		_err("sınıf kuralı")
	# sınıf tablosu: her sanat × örnek silahlar
	var tbl := []
	for id in SavasSanati.ids():
		var row := []
		for w in ["ikiz_bicak", "yatagan", "alp_kilici", "kargi", "kement", "teber", "gurz", "ulu_kilic"]:
			row.append("%s:%s" % [w, "+" if SavasSanati.uygun(id, ItemGen.roll(w, 0, "demir", 0)) else "-"])
		tbl.append("%s [%s]" % [id, " ".join(row)])
	for l in tbl:
		_p("  " + l)
	if SavasSanati.uygun("ay_hilali", ItemGen.roll("ikiz_bicak", 0, "demir", 0)) or not SavasSanati.uygun("kam_darbesi", ItemGen.roll("kement", 0, "demir", 0)):
		_err("sınıf tablosu")
	if not SavasSanati.uygun("tengri_carki", ItemGen.roll("kement", 0, "demir", 0)) or SavasSanati.uygun("evren_kuyrugu", ItemGen.roll("ikiz_bicak", 0, "demir", 0)) \
			or not SavasSanati.uygun("kurt_dansi", ItemGen.roll("ikiz_bicak", 0, "demir", 0)) or SavasSanati.uygun("yer_yarigi", ItemGen.roll("kargi", 0, "demir", 0)):
		_err("v31 sınıf tablosu")
	# ok yağmuru yay ister
	SavasSanati.sec("ok_yagmuru")
	await _reset("alp_kilici", "")
	if SavasSanati.uygun("ok_yagmuru"):
		_err("ok yağmuru yaysız uygun")
	await _reset("alp_kilici", "turk_yayi")
	if not SavasSanati.uygun("ok_yagmuru"):
		_err("ok yağmuru yayla uygun değil")
	# bekleme
	SavasSanati.sec("ay_hilali")
	await _reset("alp_kilici")
	Game.run["nisan"] = SavasSanati.nisan_max()
	await _tap("sanat")
	await _f(70)
	var rb := int(pl.sanat.stats["red"].get("bekleme", 0))
	await _tap("sanat")
	await _f(4)
	_p("bekleme: cd=%.2f red=%d aktif=%s" % [pl.sanat.cd, int(pl.sanat.stats["red"].get("bekleme", 0)) - rb, str(pl.sanat.aktif())])
	if int(pl.sanat.stats["red"].get("bekleme", 0)) == rb or pl.sanat.aktif():
		_err("bekleme reddi")
	await _idle_check("sanat/bekleme")
	# nişan yetmez
	pl.sanat.cd = 0.0
	Game.run["nisan"] = 40.0
	var rn := int(pl.sanat.stats["red"].get("nisan", 0))
	await _tap("sanat")
	await _f(4)
	_p("nisan yetmez: red=%d aktif=%s nisan=%.0f" % [int(pl.sanat.stats["red"].get("nisan", 0)) - rn, str(pl.sanat.aktif()), SavasSanati.nisan()])
	if int(pl.sanat.stats["red"].get("nisan", 0)) == rn or pl.sanat.aktif() or absf(SavasSanati.nisan() - 40.0) > 0.01:
		_err("nişan reddi")
	# ---------------------------------------------------------------- 4) Demir Duruş karşılığı
	SavasSanati.sec("demir_durus")
	await _reset("alp_kilici")
	var foe := _enemy(46.0, "kara_boru", 2000.0)
	Game.run["nisan"] = SavasSanati.nisan_max()
	var hp_pl := float(Game.run["hp"])
	var k0 := int(pl.sanat.stats["red"].get("karsilandi", 0))
	var h0 := int(pl.sanat.stats["isabet"].get("demir_durus", 0))
	var fhp := foe.hp
	await _tap("sanat")
	await _f(12)
	var took := pl.take_hit(25.0, foe)
	await _f(50)
	_p("demir duruş: karşılandı=%d hasar_alindi=%s can=%.0f->%.0f karşılık_isabet=%d düşman_can=%.0f->%.0f" % [
		int(pl.sanat.stats["red"].get("karsilandi", 0)) - k0, str(took), hp_pl, float(Game.run["hp"]),
		int(pl.sanat.stats["isabet"].get("demir_durus", 0)) - h0, fhp, foe.hp if is_instance_valid(foe) else 0.0])
	if took or int(pl.sanat.stats["red"].get("karsilandi", 0)) == k0 or int(pl.sanat.stats["isabet"].get("demir_durus", 0)) == h0:
		_err("demir duruş karşılık")
	await _idle_check("sanat/demir_karsi")
	# boşa giden duruş: açık, sonra serbest
	pl.sanat.cd = 0.0
	await _tap("sanat")
	await _f(90)
	if pl.sanat.aktif():
		_err("demir duruş boşa gidince bitmedi")
	await _idle_check("sanat/demir_bos")
	# Bir Çekiş Demir Gönül: alınan hasar azalır
	SavasSanati.sec("bir_cekis")
	await _reset("dag_cekici")
	Game.run["nisan"] = SavasSanati.nisan_max()
	await _tap("sanat")
	await _f(70)
	var ak := pl.sanat.alinan_k()
	_p("demir gönül: alınan_k=%.2f süre=%.1f" % [ak, pl.sanat.def_t])
	if ak > 0.7:
		_err("demir gönül")
	await _idle_check("sanat/demir_gonul")
	# ---------------------------------------------------------------- 5) hasar altında kesilme (zırhsız sanat yok: süper zırh)
	SavasSanati.sec("ay_hilali")
	await _reset("alp_kilici")
	var hitter := _enemy(30.0)
	Game.run["nisan"] = SavasSanati.nisan_max()
	await _tap("sanat")
	await _f(6)
	pl.inv_t = 0.0
	pl.take_hit(5.0, hitter)
	await _f(4)
	_p("hasar sırasında: aktif=%s (süper zırh: sürer)" % str(pl.sanat.aktif()))
	await _idle_check("sanat/zirh")
	# ---------------------------------------------------------------- 6) nişan kazancı
	await _reset("alp_kilici")
	Game.run["nisan"] = 0.0
	var g0 := float(pl.sanat.stats["kazanc"])
	var vic := _enemy(30.0, "kara_boru", 60.0)
	for i in 12:
		await _tap("saldiri1")
		await _f(16)
		if not is_instance_valid(vic) or vic.dead:
			break
	await _f(30)
	var g_kill := float(pl.sanat.stats["kazanc"]) - g0
	pl.v19_stats["carpisma"] = int(pl.v19_stats["carpisma"]) + 1
	await _f(2)
	var g_clash := float(pl.sanat.stats["kazanc"]) - g0 - g_kill
	pl.perfect_t = 1.5
	await _f(2)
	var g_pd := float(pl.sanat.stats["kazanc"]) - g0 - g_kill - g_clash
	_p("kazanc: sıradan düşman (60 can) öldürme=%.0f çarpışma=%.0f kusursuz_kaçış=%.0f (1 nişan=%.0f)" % [g_kill, g_clash, g_pd, SavasSanati.birim()])
	if g_kill < 20.0 or g_clash < 30.0 or g_pd < 20.0:
		_err("nişan kazancı")
	if SavasSanati.nisan() > SavasSanati.nisan_max() + 0.01:
		_err("nişan tavanı")
	# ---------------------------------------------------------------- 7) kilit, öğretme, kayıt
	Game.meta["sanat_acik"] = []
	Game.meta["sanat_secili"] = ""
	var def_ok := SavasSanati.acik_mi("kasirga") and not SavasSanati.acik_mi("ay_hilali") and SavasSanati.secili() == "kasirga"
	Game.meta["kut_bank"] = 100
	var bought := SavasSanati.ogret("ay_hilali")
	var bank_after := int(Game.meta["kut_bank"])
	var poor := SavasSanati.ogret("goge_yukselis")   # 70 > 60 kalan
	SavasSanati.sec("ay_hilali")
	Game.save_meta()
	Game.meta["sanat_acik"] = []
	Game.meta["sanat_secili"] = ""
	Game.load_meta()
	var persist := SavasSanati.acik_mi("ay_hilali") and SavasSanati.secili() == "ay_hilali"
	# Sanat Tomarı: koşuda bulunur, hemen açar
	var tom := false
	if lv.has_method("drop_sanat_tomari"):
		lv.drop_sanat_tomari("bozkurt_atilisi", pl.center() + Vector2(0, -4))
		await _f(40)
		tom = SavasSanati.acik_mi("bozkurt_atilisi")
	_p("kilit: varsayilan=%s öğret=%s banka=100->%d yetmeyen=%s kalıcı=%s tomar=%s" % [str(def_ok), str(bought), bank_after, str(poor), str(persist), str(tom)])
	if not def_ok or not bought or bank_after != 60 or poor or not persist or not tom:
		_err("kilit / kayıt")
	_restore()
	_p("TAKILMA=%d" % stuck)
	_p("SONUC %s hata=%d" % ["GECTI" if errors == 0 and stuck == 0 else "KALDI", errors])
	get_tree().quit()


func _goge_kaldirma(tavan: bool, snap := false) -> void:
	## v28: 3 sıradan + 1 seçkin; kalkan / kilitli kalan / çakılan / yerde biten ve tavan denetimi
	SavasSanati.sec("goge_yukselis")
	await _reset("kargi")
	var normals: Array = [_enemy(22.0), _enemy(48.0), _enemy(74.0)]
	var el: Enemy = lv.spawn_enemy("kara_boru", spot + Vector2(36.0, 0), true)
	el.max_hp = 99999.0
	el.hp = 99999.0
	el.speed = 0.0
	el.cd = 99.0
	el.aggro = false
	el.facing = -1
	# alçak tavan: oyuncunun 4 karo üstüne geçici katı satır (yalnız ızgara: sanatın tavan taraması bunu görür)
	var tx0 := int(floor(spot.x / Level.TS)) - 6
	var ty := int(floor((spot.y - 1.0) / Level.TS)) - 4
	var saved: Dictionary = {}
	if tavan:
		for x in range(tx0, tx0 + 14):
			var i: int = lv.idx(x, ty)
			saved[i] = lv.grid[i]
			lv.grid[i] = 1
	var ceil_y := float(ty + 1) * Level.TS
	await _f(10)
	Game.run["nisan"] = SavasSanati.nisan_max()
	var y0: Array = []
	for e in normals:
		y0.append(e.global_position.y)
	var ey0 := el.global_position.y
	var lift: Array = [0.0, 0.0, 0.0]
	var locked: Array = [0, 0, 0]
	var el_lift := 0.0
	var above_ceil := 0
	var started := false
	Input.action_press("sanat")
	for i in 220:
		await _f()
		if i == 1:
			Input.action_release("sanat")
		if pl.sanat.aktif():
			started = true
		var seg := String(pl.sanat.cur.get("seg", "")) if pl.sanat.aktif() else ""
		for k in normals.size():
			var e: Enemy = normals[k]
			if not is_instance_valid(e) or e.dead:
				continue
			lift[k] = maxf(float(lift[k]), float(y0[k]) - e.global_position.y)
			if seg == "tepe" and e.sanat_tut > 0.0:
				locked[k] = int(locked[k]) + 1
			if tavan and e.global_position.y - e.size.y < ceil_y - 1.0:
				above_ceil += 1
		if is_instance_valid(el):
			el_lift = maxf(el_lift, ey0 - el.global_position.y)
		if snap and snap_dir != "":
			await _crop_snap("%s/goge_yukselis%s_%03d.png" % [snap_dir, "_tavan" if tavan else "", i])
		if started and not pl.sanat.aktif() and i > 30:
			break
	await _f(50)
	var gs: Dictionary = pl.sanat.stats.get("goge", {})
	var bad_pos := 0
	var on_floor := 0
	for e in normals:
		if not is_instance_valid(e) or e.dead:
			continue
		var in_solid: bool = lv.solid_at(e.center()) or lv.solid_at(e.global_position + Vector2(0, -3.0)) or lv.solid_at(e.global_position + Vector2(0, -e.size.y + 2.0))
		if in_solid:
			bad_pos += 1
		if e.is_on_floor() or absf(e.global_position.y - spot.y) < 3.0:
			on_floor += 1
		if e.sanat_tut > 0.0:
			bad_pos += 1
	var tag := "tavan" if tavan else "acik"
	_p("goge kaldırma (%s): H=%.0f kaldırılan=%d seçkin_kalkmadı=%d çakılan=%d kalkış=[%.0f %.0f %.0f] kilit_kare=[%d %d %d] seçkin_kalkış=%.0f yerde=%d/3 kötü_konum=%d tavan_üstü=%d" % [
		tag, float(gs.get("H", -1.0)), int(gs.get("kaldirilan", 0)), int(gs.get("seckin", 0)), int(gs.get("carpilan", 0)),
		float(lift[0]), float(lift[1]), float(lift[2]), int(locked[0]), int(locked[1]), int(locked[2]), el_lift, on_floor, bad_pos, above_ceil])
	if not started:
		_err("goge (%s) başlamadı" % tag)
	if int(gs.get("kaldirilan", 0)) != 3 or int(gs.get("carpilan", 0)) != 3:
		_err("goge (%s) kaldırılan / çakılan 3 değil" % tag)
	var need := 40.0 if not tavan else 12.0
	for k in 3:
		if float(lift[k]) < need or int(locked[k]) < 12:
			_err("goge (%s) düşman %d kalkmadı / kilitlenmedi" % [tag, k])
	if el_lift > 10.0 or int(gs.get("seckin", 0)) < 1:
		_err("goge (%s) seçkin kalktı (%.0f)" % [tag, el_lift])
	if on_floor < 3 or bad_pos > 0:
		_err("goge (%s) düşmanlar yerde değil / duvar-tavan içinde" % tag)
	if tavan and (above_ceil > 0 or float(gs.get("H", 999.0)) > 60.0):
		_err("goge tavanı aştı (H=%.0f, tavan_üstü=%d)" % [float(gs.get("H", -1.0)), above_ceil])
	for i in saved:
		lv.grid[i] = saved[i]
	await _idle_check("sanat/goge_" + tag)


# ---------------------------------------------------------------- v31 kombo sanatları
func _elit(dx: float) -> Enemy:
	var el: Enemy = lv.spawn_enemy("kara_boru", spot + Vector2(dx, 0), true)
	el.max_hp = 99999.0
	el.hp = 99999.0
	el.speed = 0.0
	el.cd = 99.0
	el.aggro = false
	el.facing = -1 if dx > 0 else 1
	return el


func _kombo(id: String, tavan: bool, snap := false, ritim := "") -> void:
	## 3 sıradan + 1 seçkin: kilit / kalkış / seçkin kalkmaz / yerde biter / duvar-tavan içinde değil; ritim: "tam" halka
	## kapanırken T, "erken" halka görünürken erken T (kaçar)
	SavasSanati.sec(id)
	await _reset(WEAPON.get(id, "alp_kilici"))
	var setup: Array = KOMBO[id]
	var normals: Array = []
	for dx in setup[0]:
		normals.append(_enemy(float(dx)))
	var el := _elit(float(setup[1]))
	var tx0 := int(floor(spot.x / Level.TS)) - 8
	var ty := int(floor((spot.y - 1.0) / Level.TS)) - 4
	var saved: Dictionary = {}
	if tavan:
		for x in range(tx0, tx0 + 18):
			var i: int = lv.idx(x, ty)
			saved[i] = lv.grid[i]
			lv.grid[i] = 1
	var ceil_y := float(ty + 1) * Level.TS
	await _f(10)
	Game.run["nisan"] = SavasSanati.nisan_max()
	var y0: Array = []
	for e in normals:
		y0.append(e.global_position.y)
	var ey0 := el.global_position.y
	var lift: Array = [0.0, 0.0, 0.0]
	var locked: Array = [0, 0, 0]
	var rooted: Array = [false, false, false]
	var el_lift := 0.0
	var above_ceil := 0
	var pl_ceil := 0
	var started := false
	var pressed_rit := false
	var hp0: Array = []
	for e in normals:
		hp0.append(e.hp)
	var el_hp0 := el.hp
	Input.action_press("sanat")
	var frames := 0
	for i in 260:
		await _f()
		frames += 1
		if i == 1:
			Input.action_release("sanat")
		if pl.sanat.aktif():
			started = true
			var rit: Dictionary = pl.sanat.cur.get("rit", {})
			if ritim != "" and not rit.is_empty() and not pressed_rit:
				var tt := float(pl.sanat.cur["t"])
				var at := float(rit["at"])
				var fire := (tt >= at - 0.035) if ritim == "tam" else (tt >= at - float(rit["pre"]) + 0.04)
				if fire and bool(rit.get("fx", false)):
					pressed_rit = true
					Input.action_press("sanat")
					await _f(2)
					Input.action_release("sanat")
					frames += 2
		for k in normals.size():
			var e: Enemy = normals[k]
			if not is_instance_valid(e) or e.dead:
				continue
			lift[k] = maxf(float(lift[k]), float(y0[k]) - e.global_position.y)
			if e.sanat_tut > 0.0:
				locked[k] = int(locked[k]) + 1
			if e.root_t > 0.0:
				rooted[k] = true
			if tavan and e.global_position.y - e.size.y < ceil_y - 1.0:
				above_ceil += 1
		if tavan and pl.global_position.y - 44.0 < ceil_y - 1.0:
			pl_ceil += 1
		if is_instance_valid(el):
			el_lift = maxf(el_lift, ey0 - el.global_position.y)
		if snap and snap_dir != "":
			await _crop_snap("%s/%s%s_%03d.png" % [snap_dir, id, "_tavan" if tavan else "", i])
		if started and not pl.sanat.aktif() and i > 30:
			break
	var dur_f := frames
	await _f(70)
	var ks: Dictionary = pl.sanat.stats.get("kombo", {})
	var bad_pos := 0
	var on_floor := 0
	var dealt := 0.0
	for k in normals.size():
		var e: Enemy = normals[k]
		if not is_instance_valid(e) or e.dead:
			on_floor += 1
			continue
		dealt += float(hp0[k]) - e.hp
		var in_solid: bool = lv.solid_at(e.center()) or lv.solid_at(e.global_position + Vector2(0, -3.0)) or lv.solid_at(e.global_position + Vector2(0, -e.size.y + 2.0))
		if in_solid:
			bad_pos += 1
		if e.is_on_floor() or absf(e.global_position.y - spot.y) < 3.0:
			on_floor += 1
		if e.sanat_tut > 0.0:
			bad_pos += 1
	var pl_bad: bool = lv.solid_at(pl.center()) or lv.solid_at(pl.global_position + Vector2(0, -3.0))
	var tag := "tavan" if tavan else "acik"
	var n_root := 0
	for r in rooted:
		if r:
			n_root += 1
	_p("kombo %s (%s): kare=%d H=%.0f kilit=%d seçkin_kalkmadı=%d bitiş=%d ritim=%d (%s) kalkış=[%.0f %.0f %.0f] kilit_kare=[%d %d %d] çivi=%d seçkin_kalkış=%.0f yerde=%d/3 kötü_konum=%d tavan_üstü=%d oyuncu_tavan=%d hasar=%.0f seçkin_hasar=%.0f" % [
		id, tag, dur_f, float(ks.get("H", -1.0)), int(ks.get("kilit", 0)), int(ks.get("seckin", 0)), int(ks.get("bitis", 0)), int(ks.get("ritim", 0)), ritim,
		float(lift[0]), float(lift[1]), float(lift[2]), int(locked[0]), int(locked[1]), int(locked[2]), n_root, el_lift, on_floor, bad_pos, above_ceil, pl_ceil,
		dealt, el_hp0 - (el.hp if is_instance_valid(el) else 0.0)])
	if not started:
		_err("%s (%s) başlamadı" % [id, tag])
	var need: float = float((KOMBO_KALK[id] as Array)[1 if tavan else 0])
	if need >= 0.0:
		if int(ks.get("kilit", 0)) != 3:
			_err("%s (%s) kilitlenen 3 değil" % [id, tag])
		for k in 3:
			if float(lift[k]) < need or int(locked[k]) < 6:
				_err("%s (%s) sıradan %d kalkmadı / kilitlenmedi" % [id, tag, k])
		if int(ks.get("seckin", 0)) < 1:
			_err("%s (%s) seçkin sayılmadı" % [id, tag])
	else:
		if n_root < 2:
			_err("%s (%s) sıradanlar çivilenmedi (%d)" % [id, tag, n_root])
	if el_lift > 10.0:
		_err("%s (%s) seçkin kalktı (%.0f)" % [id, tag, el_lift])
	if int(ks.get("bitis", 0)) < 1:
		_err("%s (%s) bitiriş yok" % [id, tag])
	if on_floor < 3 or bad_pos > 0 or pl_bad:
		_err("%s (%s) düşmanlar yerde değil / duvar-tavan içinde (oyuncu=%s)" % [id, tag, str(pl_bad)])
	if tavan and (above_ceil > 0 or pl_ceil > 0):
		_err("%s tavanı aştı (düşman=%d oyuncu=%d)" % [id, above_ceil, pl_ceil])
	if ritim == "tam" and int(ks.get("ritim", 0)) != 1:
		_err("%s ritim TAM olmadı" % id)
	if ritim == "erken" and (int(ks.get("ritim", 0)) != 0 or not bool(pl.sanat.cur.get("rit", {}).get("kacti", true))):
		_err("%s erken basış ritmi tuttu" % id)
	if dealt <= 0.0 or el_hp0 - (el.hp if is_instance_valid(el) else 0.0) <= 0.0:
		_err("%s (%s) hasar yok" % [id, tag])
	for i in saved:
		lv.grid[i] = saved[i]
	await _idle_check("sanat/kombo_%s_%s" % [id, tag])


func _duvar_bul() -> Vector2:
	## Gerçek duvar: zemin 7 karo düz, sağında en az 3 karo yükselen katı sütun (çarpışma şekli gerçek)
	for x in range(14, Level.W - 14):
		var y0: int = lv.surface_y(x)
		var ok := true
		for dx in range(-7, 1):
			if lv.surface_y(x + dx) != y0:
				ok = false
				break
			for dy in range(1, 5):
				if lv.cell(x + dx, y0 - dy) != 0:
					ok = false
					break
			if not ok:
				break
		if not ok:
			continue
		var wall := true
		for dy in range(1, 4):
			if lv.cell(x + 1, y0 - dy) != 1:
				wall = false
		if wall:
			return Vector2((x + 1) * Level.TS, y0 * Level.TS - 1)
	return Vector2.ZERO


func _duvar_testi() -> void:
	## Duvar kenarı: Tengri Çarkı savurduğunu duvara çakar (sekme); Kurt Dansı'nda düşmanın arkası duvar: oyuncu duvara girmez
	var w := _duvar_bul()
	if w == Vector2.ZERO:
		_p("duvar testi: uygun duvar yok (atlandı)")
		return
	var old_spot := spot
	for id in ["tengri_carki", "kurt_dansi"]:
		if only != "" and id != only:
			continue
		SavasSanati.sec(id)
		spot = w + Vector2(-110.0, 0.0)
		await _reset(WEAPON[id])
		var foes: Array = [_enemy(58.0), _enemy(86.0)] if id == "tengri_carki" else [_enemy(96.0)]
		await _f(10)
		Game.run["nisan"] = SavasSanati.nisan_max()
		Input.action_press("sanat")
		var max_x := -INF
		for i in 200:
			await _f()
			if i == 1:
				Input.action_release("sanat")
			max_x = maxf(max_x, pl.global_position.x)
			if i > 30 and not pl.sanat.aktif():
				break
		await _f(60)
		var ks: Dictionary = pl.sanat.stats.get("kombo", {})
		var bad := 0
		for e in foes:
			if is_instance_valid(e) and not e.dead:
				if lv.solid_at(e.center()) or lv.solid_at(e.global_position + Vector2(0, -3.0)) or e.sanat_tut > 0.0:
					bad += 1
		var pl_bad: bool = lv.solid_at(pl.center()) or lv.solid_at(pl.global_position + Vector2(0, -3.0)) or max_x > w.x - 6.0
		_p("duvar %s: duvar_x=%.0f duvar_sekmesi=%d oyuncu_en_sağ=%.0f kötü_konum=%d oyuncu_duvarda=%s" % [id, w.x, int(ks.get("duvar", 0)), max_x, bad, str(pl_bad)])
		if bad > 0 or pl_bad:
			_err("duvar %s: duvar içinde" % id)
		if id == "tengri_carki" and int(ks.get("duvar", 0)) < 1:
			_err("duvar sekmesi yok")
		await _idle_check("sanat/duvar_" + id)
	spot = old_spot
	await _reset("alp_kilici")


func _fx_onizleme() -> void:
	## SanatFX bileşimleri tek tek (oyuncu gizli): her biri 0,8 sn, 2 karede bir kırpılmış kare
	await _reset("alp_kilici")
	await get_tree().create_timer(4.0).timeout
	pl.visible = false
	var save_dir := snap_dir
	snap_dir = fx_dir
	var c := pl.center()
	var g := pl.global_position
	var list := {
		"debug_firca": func() -> void:
			var n := SanatFX.firca(c + Vector2(-60, -60), 9, 57)
			for s in 6:
				n.ek(SanatFX.line(Vector2(0, s * 26.0), Vector2(220, s * 26.0), 12), SanatFX.press(12, 22.0, 0.8, 0.1, 0.15), s, s, 0.0, 0.2, 0.6, 0.2),
		"telegraf": func() -> void: SanatFX.telegraf(pl, "goge_yukselis", SavasSanati.renk("goge_yukselis"), 9, 1),
		"kesik_altin": func() -> void: SanatFX.kesik(c + Vector2(40, 0), PI * 0.25, 90.0, 12.0, 9, 0.12, 0.1, 57, true),
		"goge_yuksel": func() -> void: SanatFX.goge_yuksel(g, 130.0, 1, 9),
		"goge_kesik2": func() -> void: SanatFX.goge_kesik(c + Vector2(40, -10), 1, 2, 9, 60.0),
		"goge_gum": func() -> void: SanatFX.goge_gum(g + Vector2(30, 0), 1, 9, 3),
		"kasirga_son": func() -> void: SanatFX.kasirga_son(g + Vector2(0, -24), 50.0, 4),
		"cekis_inis": func() -> void: SanatFX.cekis_inis(g + Vector2(50, 0), 1, 0, 78.0, 86.0),
		"ay_cekis": func() -> void: SanatFX.ay_cekis(c, 1, 7),
		"simsek": func() -> void: SanatFX.simsek(c + Vector2(-80, 4), c + Vector2(90, 0), 5, 10.0, 7, 0.2),
		"bozkurt_kin": func() -> void: SanatFX.bozkurt_kin(c + Vector2(40, 0), 5),
		"kam_davul": func() -> void: SanatFX.kam_davul(c + Vector2(30, 0), 1, 6),
		"ok_halka": func() -> void: SanatFX.ok_halka(g + Vector2(60, -2), 1, 0.5),
		"demir_ors": func() -> void: SanatFX.demir_ors(c + Vector2(20, 0), 1),
		"demir_karsi": func() -> void: SanatFX.demir_karsi(c + Vector2(40, 0), 1, 40.0),
		"kurt_adim": func() -> void: SanatFX.kurt_adim(c + Vector2(-90, 0), c + Vector2(90, 0), 14, 0),
		"kurt_patla": func() -> void: SanatFX.kurt_patla(c + Vector2(30, 0), 14, 2, true),
		"evren_supur": func() -> void: SanatFX.evren_supur(g, 1, 44.0, 15),
		"evren_sarmal": func() -> void: SanatFX.evren_sarmal(g, 130.0, 1, 15),
		"evren_cark": func() -> void: SanatFX.evren_cark(c, 1, 15, 44.0),
		"evren_kut": func() -> void: SanatFX.evren_kut(g + Vector2(30, 0), 1, 15, 3, false),
		"tengri_patla": func() -> void: SanatFX.tengri_patla(c + Vector2(40, -10), 1, 16, true),
		"yarik_tepme": func() -> void: SanatFX.yarik_tepme(g, 1, 17, [30.0, 60.0], 40.0),
		"yarik_cat": func() -> void: SanatFX.yarik_cat(g + Vector2(30, 0), 1, 17, 3, false),
		"akin_birak": func() -> void: SanatFX.akin_birak(c + Vector2(20, 0), 1, 18, true),
		"damgalar": func() -> void:
			var ws := ["cit", "kut", "vus", "cat", "viz", "tam"]
			for i in ws.size():
				SanatFX.damga(c + Vector2(-150 + 100 * (i % 3), -70 + 80 * (i / 3)), ws[i], [14, 15, 16, 17, 18, 9][i], 1, 1.0),
	}
	for nm in list:
		if only != "" and nm != only:
			continue
		(list[nm] as Callable).call()
		for i in 48:
			await _f()
			if i % 2 == 0:
				await _crop_snap("%s/fx_%s_%03d.png" % [fx_dir, nm, i])
		await _f(20)
	# sürekli kipler: hilal, kasırga girdabı, kalkan
	var h := SanatFX.spawn("hilal", c + Vector2(-60, 0), Color(0.78, 0.86, 1.0), 1.5, 7)
	if h:
		h.facing = 1
		h.vel = Vector2(200, 0)
		h.data = {"menzil": 250.0, "max": 6, "pal": 7}
	for i in 40:
		await _f()
		if i % 2 == 0:
			await _crop_snap("%s/fx_hilal_%03d.png" % [fx_dir, i])
	var k := SanatFX.spawn("kasirga", g + Vector2(0, -24), Color(0.45, 0.95, 0.86), 9.0, 4)
	if k:
		k.data = {"rx": 62.0, "ry": 12.0, "spd": TAU / 0.3}
	for i in 30:
		await _f()
		if i % 2 == 0:
			await _crop_snap("%s/fx_kasirga_%03d.png" % [fx_dir, i])
	if k:
		k.alive = false
	await _f(20)
	var kl := SanatFX.demir_kalkan(pl, 1)
	for i in 30:
		await _f()
		if i % 2 == 0:
			await _crop_snap("%s/fx_kalkan_%03d.png" % [fx_dir, i])
	if kl:
		kl.alive = false
	await _f(20)
	# v31 sürekli kipler: girdap, ritim halkası, delen ok
	var gd := SanatFX.spawn("girdap", c + Vector2(50, -20), Color(0.48, 0.8, 1.0), 9.0, 16)
	if gd:
		gd.data = {"r0": 120.0, "r1": 46.0, "tr": 0.4, "spd": 9.0}
	var rt := SanatFX.spawn("ritim", c, Color(1.0, 0.45, 0.62), 0.66, 14)
	if rt:
		rt.data = {"pre": 0.34, "ok": true}
	var dl := SanatFX.spawn("delen", c + Vector2(-120, 10), Color(0.95, 0.92, 0.84), 2.0, 18)
	if dl:
		dl.facing = 1
		dl.vel = Vector2(400, 0)
		dl.data = {"menzil": 300.0, "max": 8, "pal": 18}
	for i in 40:
		await _f()
		if i % 2 == 0:
			await _crop_snap("%s/fx_girdap_%03d.png" % [fx_dir, i])
	if gd:
		gd.alive = false
	await _f(20)
	snap_dir = save_dir
	pl.visible = true


func _restore() -> void:
	Game.meta = _meta_bak
	Game.save_meta()


# ---------------------------------------------------------------- kare şeritleri
func _snaps() -> void:
	for id in SavasSanati.ids():
		if only != "" and id != only:
			continue
		crop_shift = 90.0 if id in ["ay_hilali", "bozkurt_atilisi"] else (130.0 if id == "ok_yagmuru" else 0.0)
		CROP = Vector2i(960, 540) if id == "ok_yagmuru" else Vector2i(640, 400)
		if id == "goge_yukselis":
			# v28: 3 sıradan + 1 seçkin dizilişiyle tam dizi
			CROP = Vector2i(640, 460)
			await _goge_kaldirma(false, true)
			CROP = Vector2i(640, 400)
			await _f(30)
			continue
		if KOMBO.has(id):
			# v31: 3 sıradan + 1 seçkin, ritim TAM ile tam dizi
			CROP = Vector2i(760, 600)
			crop_shift = 0.0
			crop_world = spot + Vector2(float((KOMBO[id] as Array)[1]) * 0.5 - (25.0 if id == "akinci_akini" else 0.0), 0.0)
			await _kombo(id, false, true, "tam")
			crop_world = Vector2.INF
			CROP = Vector2i(640, 400)
			await _f(30)
			continue
		var r := await _cast(id, 3 if id != "demir_durus" else 1, id == "kasirga", true)
		if id == "demir_durus":
			# karşılık karesi: duruşta düşman vurur
			SavasSanati.sec(id)
			await _reset("ulu_kilic")
			var foe := _enemy(50.0, "kara_boru")
			Game.run["nisan"] = SavasSanati.nisan_max()
			Input.action_press("sanat")
			for i in 120:
				await _f()
				if i == 1:
					Input.action_release("sanat")
				if i == 14:
					pl.take_hit(20.0, foe)
				await _crop_snap("%s/%s_karsi_%03d.png" % [snap_dir, id, i])
				if i > 20 and not pl.sanat.aktif():
					break
		_p("kare %s kareler=%d isabet=%d" % [id, int(r["frames"]), int(r["hits"])])
		await _f(30)
