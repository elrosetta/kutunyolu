extends Node
## Dövüş akıcılığı testi (betikli girdi; Input.action_press ile oyuncunun kendi yolundan sürer):
##   godot --headless --path . --quit-after 99999 -- --dovus --boss [--stil=v2]   (--boss: düz arena)
## Ölçer: girdi→eylem gecikmesi (kare, 60 Hz), saldırı sırasında ara belleğe alınan basışların karşılanması,
## iptal pencereleri (yuvarlanma / zıplama / saldırı), yuvarlanma içinden saldırı, ardışık yuvarlanma, koşudan
## saldırıya ivme, havada yön verme, hedef yardımı (arkadaki / biraz uzaktaki / dibindeki düşman), üç vuruşluk
## zincirde ıskalama, çok düşmanlı vuruşta duraklama (hitstop) toplamı, ağır saldırı tanıma süresi, hasar
## sonrası denetim dönüşü ve takılı kalan durum (saldırı, yuvarlanma, şarj sesi döngüsü, zaman ölçeği).
## Çıktı: "[dovus] anahtar=değer" satırları + sonunda "[dovus] OZET ..." ve "[dovus] TAKILMA=n".

var main: Node
var lv: Node
var pl: Player
var spot := Vector2.ZERO
var stuck := 0
var _swings := 0
var _last_atk: Dictionary = {}
var _heavies := 0
var _frozen := 0
var _kick_max := 0.0
var _track := false

const WEAPONS := ["ikiz_bicak", "yatagan", "alp_kilici", "kargi", "ulu_kilic", "dag_cekici"]
## v18 tempo tablosu: her silah sınıfından bir temsilci (basış→temas, zincir aralığı)
## v19: tüm yakın dövüş silahları (silah başına basış→temas ve zincir aralığı raporu)
const TEMPO_WEAPONS := ["ikiz_bicak", "bori_hanceri", "kurt_pencesi", "ay_palasi", "yatagan", "ruzgar_kilici", "alp_kilici", "pala",
	"ruh_kilici", "yilan_kilici", "ayaz_kilici", "yildirim_kilici", "kargi", "tulpar_mizragi", "kement", "od_kamcisi", "teber",
	"erlik_tirpani", "kayin_asasi", "gurz", "civili_topuz", "savas_baltasi", "ikiz_balta", "ulu_kilic", "bozgun_kilici", "dag_cekici",
	"kor_cekici"]
const ACTS := ["saldiri1", "saldiri2", "zipla", "yuvarlan", "sag", "sol", "yukari", "asagi", "techizat1", "techizat2", "sise", "kut"]


func _ready() -> void:
	process_mode = Node.PROCESS_MODE_ALWAYS
	_run.call_deferred()


func _p(s: String) -> void:
	print("[dovus] ", s)


func _f(n := 1) -> void:
	for i in n:
		await get_tree().physics_frame
		_tick()


func _tick() -> void:
	## Her karenin başında (oyuncudan önce) sayaçlar: yeni savuruş, ağır saldırı, donmuş kare, kamera itişi
	if pl == null:
		return
	Game.run["hp"] = float(Game.run["max_hp"])
	for e in get_tree().get_nodes_in_group("dusman"):
		if is_instance_valid(e) and not e.dead:
			e.cd = 99.0
			e.hp = maxf(e.hp, 1.0)
	if not _track:
		return
	if not pl.atk.is_empty() and not is_same(pl.atk, _last_atk):
		if pl.atk.get("heavy", false):
			_heavies += 1
		else:
			_swings += 1
	_last_atk = pl.atk
	if Engine.time_scale < 0.5:
		_frozen += 1
	_kick_max = maxf(_kick_max, Game.kick_off.length())


func _release_all() -> void:
	for a in ACTS:
		Input.action_release(a)


func _tap(a: String, frames := 2) -> void:
	Input.action_press(a)
	await _f(frames)
	Input.action_release(a)


func _until(cond: Callable, max_f := 120) -> int:
	## koşul sağlanana dek kare say; 0 = basışla aynı karede. -1 = hiç
	for n in max_f:
		await _f()
		if cond.call():
			return n
	return -1


func _find_spot() -> Vector2:
	## Test arenası: --boss ile kurulan düz boss arenası (boss kaldırılır, iki platform arası 16 karo boş);
	## yoksa bölümde düz, tavansız bir şerit aranır.
	if "boss" in lv and lv.boss != null and is_instance_valid(lv.boss):
		lv.boss.remove_from_group("dusman")
		lv.boss.queue_free()
		lv.boss = null
		return Vector2(33 * Level.TS + 12, lv.surface_y(33) * Level.TS - 1)
	var best_x := -1
	for x in range(20, Level.W - 30):
		var y0: int = lv.surface_y(x)
		var ok := true
		for dx in range(-7, 8):
			var xx := x + dx
			if lv.surface_y(xx) != y0:
				ok = false
				break
			for dy in range(1, 5):
				if lv.cell(xx, y0 - dy) == 1:
					ok = false
					break
			if not ok:
				break
		if ok:
			best_x = x
			break
	if best_x < 0:
		_p("UYARI: düz şerit bulunamadı")
		best_x = 40
	return Vector2(best_x * Level.TS + 12, lv.surface_y(best_x) * Level.TS - 1)


func _clear_enemies() -> void:
	for e in get_tree().get_nodes_in_group("dusman"):
		e.remove_from_group("dusman")
		e.queue_free()


func _reset(weapon: String) -> void:
	_release_all()
	_track = false
	_clear_enemies()
	if String(Game.run["slots"]["melee"].get("id", "")) != weapon:
		Game.run["slots"]["melee"] = ItemGen.roll(weapon, 1, "demir", 0)
	Game.run["slots"]["second"] = ItemGen.roll("turk_yayi", 1, "demir", 0)
	pl.on_equip()
	pl.global_position = spot
	pl.velocity = Vector2.ZERO
	pl.facing = 1
	pl.roll_t = 0.0
	pl.roll_cd = 0.0
	pl.hurt_t = 0.0
	pl.inv_t = 0.0
	pl.melee_buf = 0.0
	pl.jump_buf = 0.0
	pl.since_atk = 9.0
	pl.last_step = -1
	pl.rolled_t = 0.0
	pl.combo_break("")
	await _f(24)
	_swings = 0
	_heavies = 0
	_frozen = 0
	_kick_max = 0.0
	_last_atk = pl.atk
	_track = true


func _enemy(dx: float, kind := "kara_boru") -> Enemy:
	var e: Enemy = lv.spawn_enemy(kind, spot + Vector2(dx, 0))
	e.max_hp = 99999.0
	e.hp = 99999.0
	e.speed = 0.0
	e.cd = 99.0
	e.aggro = false
	e.facing = -1 if dx > 0 else 1
	return e


func _idle_check(tag: String) -> void:
	## Girdi yokken 1,5 sn sonra her şey serbest olmalı
	_release_all()
	await _f(90)
	var bad: Array = []
	if not pl.atk.is_empty():
		bad.append("atk=%s" % pl.atk.get("phase", "?"))
	if pl.roll_t > 0.0:
		bad.append("roll")
	if pl.charge_t >= 0.0:
		bad.append("charge")
	if pl.aim_t >= 0.0:
		bad.append("aim")
	if Ses._loops.has("sarj"):
		bad.append("sarj_dongusu")
	if absf(Engine.time_scale - 1.0) > 0.01:
		bad.append("time_scale=%.2f" % Engine.time_scale)
	if not bad.is_empty():
		stuck += 1
		_p("TAKILDI %s: %s" % [tag, ", ".join(bad)])


func _at_contact() -> bool:
	## savuruş temas anına (ck) ulaştı mı (v18; eski sürümde vuruş penceresinin başı)
	if pl.atk.is_empty() or pl.atk.get("phase", "") == "charge":
		return false
	var k := float(pl.atk["t"]) / float(pl.atk["dur"])
	var ck: float = pl._contact_k(pl.atk["sw"]) if pl.has_method("_contact_k") else float(pl.atk["sw"]["hit"][0])
	return k >= ck - 0.0001 and pl.atk.get("phase", "") != "wind"


func _ms(fr: int) -> String:
	return "yok" if fr < 0 else "%d kare (%d ms)" % [fr, int(round(fr * 1000.0 / 60.0))]


func _run() -> void:
	await get_tree().create_timer(0.6).timeout
	lv = main.level
	pl = lv.player
	spot = _find_spot()
	_p("arena=%s stil=%s" % [str(spot), "v2" if OS.get_cmdline_user_args().has("--stil=v2") else "v1"])
	var ks := ""
	for arg in OS.get_cmdline_user_args():
		if String(arg).begins_with("--klip="):
			ks = String(arg).trim_prefix("--klip=")
	if ks != "":
		await _klip_silahlar(ks.split(","))
		get_tree().quit()
		return
	if OS.get_cmdline_user_args().has("--klip19"):
		await _klip19()
		get_tree().quit()
		return
	if OS.get_cmdline_user_args().has("--klip"):
		await _klip()
		get_tree().quit()
		return
	var sum := {}
	if OS.get_cmdline_user_args().has("--klip20"):
		await _klip20()
		get_tree().quit()
		return
	if OS.get_cmdline_user_args().has("--hiz"):
		await _hiz()
		_p("TAKILMA=%d" % stuck)
		get_tree().quit()
		return
	if OS.get_cmdline_user_args().has("--v19"):
		await _v19()
		_p("TAKILMA=%d" % stuck)
		get_tree().quit()
		return
	if OS.get_cmdline_user_args().has("--yildirim"):
		await _yildirim()
		_p("TAKILMA=%d" % stuck)
		get_tree().quit()
		return
	# ---------------------------------------------------------------- 1) gecikme, kilit, ara bellek (her silah)
	for w in WEAPONS:
		await _reset(w)
		Input.action_press("saldiri1")
		var l_start := await _until(func() -> bool: return not pl.atk.is_empty(), 30)
		Input.action_release("saldiri1")
		var l_strike := await _until(func() -> bool: return pl.atk.get("phase", "") == "act", 120)
		var l_ck := 0
		if not _at_contact():
			l_ck = await _until(func() -> bool: return _at_contact(), 60) + 1
		var l_rec := await _until(func() -> bool: return pl.atk.is_empty() or pl.atk.get("phase", "") == "rec", 120)
		var l_end := await _until(func() -> bool: return pl.atk.is_empty(), 120)
		var strike_total := l_start + 1 + l_strike + 1
		var cancel_total := strike_total + l_ck + l_rec + 1
		_p("%s: basış→saldırı=%s basış→vuruş=%s basış→temas=%s basış→iptal_edilebilir=%s kuyruk=%s" % [w, _ms(l_start), _ms(strike_total), _ms(strike_total + l_ck), _ms(cancel_total), _ms(l_end + 1)])
		await _idle_check(w + "/tek")
		# ara bellek: ilk savuruşun farklı anlarında bir kez bas (kısa dokunuş) -> ikinci savuruş gelmeli
		var honoured := 0
		var tries := 0
		for at in [2, 6, 10, 16, 24]:
			await _reset(w)
			await _tap("saldiri1", 2)
			await _f(at)
			if pl.atk.is_empty():
				continue  # savuruş bu andan önce bitti (hızlı silah) — ölçülmez
			tries += 1
			await _tap("saldiri1", 2)
			await _until(func() -> bool: return _swings >= 2 and pl.atk.is_empty(), 150)
			if _swings >= 2:
				honoured += 1
		_p("%s: savuruş_içi_basış_karşılandı=%d/%d" % [w, honoured, tries])
		sum[w] = [strike_total, cancel_total, honoured, tries]
		await _idle_check(w + "/arabellek")
		# seri basış: 10 Hz, 2 sn
		await _reset(w)
		for i in 20:
			await _tap("saldiri1", 2)
			await _f(4)
		await _f(60)
		_p("%s: seri_basış 20 basış → %d savuruş, %d ağır" % [w, _swings, _heavies])
		await _idle_check(w + "/seri")

	# ---------------------------------------------------------------- 1b) tempo: basış→temas ve zincir aralığı (seri basış)
	var tline := ""
	for w in TEMPO_WEAPONS:
		if OS.get_cmdline_user_args().has("--iz") and w != "gurz":
			continue
		await _reset(w)
		var contacts: Array = []
		var cur: Dictionary = {}
		var seen := false
		var first_ck := -1
		for i in 300:
			if OS.get_cmdline_user_args().has("--iz") and not pl.atk.is_empty():
				_p("  iz %s k=%.3f ph=%s s=%s step=%s" % [w, float(pl.atk["t"]) / float(pl.atk["dur"]), pl.atk.get("phase", ""), pl.atk["c"]["s"], str(pl.atk["step"])])
			if i % 3 == 0 and contacts.size() < 4:
				Input.action_press("saldiri1")
			elif i % 3 == 1:
				Input.action_release("saldiri1")
			await _f()
			if not is_same(pl.atk, cur):
				cur = pl.atk
				seen = false
			if not pl.atk.is_empty() and not seen and _at_contact():
				seen = true
				contacts.append(i)
				if first_ck < 0:
					first_ck = i + 1
			if contacts.size() >= 4:
				break
		Input.action_release("saldiri1")
		var gaps: Array = []
		for j in range(1, contacts.size()):
			gaps.append(int(round((int(contacts[j]) - int(contacts[j - 1])) * 1000.0 / 60.0)))
		_p("tempo %s: basış→temas=%s zincir aralıkları(ms)=%s" % [w, _ms(first_ck), str(gaps)])
		tline += "%s %d/%s | " % [w, int(first_ck * 1000.0 / 60.0), str(gaps)]
		await _idle_check("tempo/" + w)
	_p("TEMPO " + tline)
	# ---------------------------------------------------------------- 1c) v19 mekanikleri
	await _v19()
	# ---------------------------------------------------------------- 1d) v20 saldırı hızı ve Kızışma
	await _hiz()
	# ---------------------------------------------------------------- 2) iptaller (alp kılıcı)
	var w0 := "alp_kilici"
	await _reset(w0)
	await _tap("saldiri1", 2)
	await _f(3)
	Input.action_press("yuvarlan")
	var r_wind := await _until(func() -> bool: return pl.roll_t > 0.0, 60)
	Input.action_release("yuvarlan")
	_p("iptal: hazırlıkta yuvarlan → %s" % _ms(r_wind))
	await _idle_check("iptal/yuv")
	# toparlanmada zıpla
	await _reset(w0)
	await _tap("saldiri1", 2)
	await _until(func() -> bool: return pl.atk.get("phase", "") == "rec", 120)
	Input.action_press("zipla")
	var j_rec := await _until(func() -> bool: return pl.velocity.y < -100.0, 60)
	var atk_after := "bitti" if pl.atk.is_empty() else String(pl.atk.get("phase", ""))
	Input.action_release("zipla")
	_p("iptal: toparlanmada zıpla → %s (saldırı: %s)" % [_ms(j_rec), atk_after])
	await _idle_check("iptal/zipla_rec")
	# vuruş anında zıpla (ara bellek: toparlanmada zıplamalı)
	await _reset(w0)
	await _tap("saldiri1", 2)
	await _until(func() -> bool: return pl.atk.get("phase", "") == "act", 120)
	await _tap("zipla", 2)
	var j_act := await _until(func() -> bool: return pl.velocity.y < -100.0, 60)
	_p("iptal: vuruşta zıpla → %s sonra zıplama" % _ms(j_act))
	await _idle_check("iptal/zipla_act")
	# hazırlıkta zıpla
	await _reset(w0)
	await _tap("saldiri1", 2)
	await _f(2)
	Input.action_press("zipla")
	var j_wind := await _until(func() -> bool: return pl.velocity.y < -100.0, 60)
	var atk_w := "bitti" if pl.atk.is_empty() else String(pl.atk.get("phase", ""))
	Input.action_release("zipla")
	_p("iptal: hazırlıkta zıpla → %s (saldırı: %s)" % [_ms(j_wind), atk_w])
	await _idle_check("iptal/zipla_wind")
	# yuvarlanma içinden saldırı (kaçış saldırısı)
	await _reset(w0)
	await _tap("yuvarlan", 2)
	await _f(6)
	await _tap("saldiri1", 2)
	var ra := await _until(func() -> bool: return not pl.atk.is_empty(), 60)
	var ra_name := String(pl.atk.get("c", {}).get("name", pl.atk.get("c", {}).get("s", ""))) if not pl.atk.is_empty() else "-"
	_p("yuvarlanmada saldırı (8. karede bas) → %s sonra saldırı [%s]" % [_ms(ra), ra_name])
	await _idle_check("yuv/saldiri")
	# ardışık yuvarlanma: ilk yuvarlanmanın 15. karesinde bas
	await _reset(w0)
	await _tap("yuvarlan", 2)
	await _f(13)
	await _tap("yuvarlan", 2)
	var rr := await _until(func() -> bool: return pl.roll_t > ROLL_PROBE, 60)
	_p("ardışık yuvarlanma (15. karede bas) → %s sonra ikinci yuvarlanma" % _ms(rr))
	await _idle_check("yuv/yuv")
	# vuruş anında yay basışı (ara bellek): toparlanmada saldırıyı kesip ok atmalı
	await _reset(w0)
	await _tap("saldiri1", 2)
	await _until(func() -> bool: return pl.atk.get("phase", "") == "act", 120)
	await _tap("saldiri2", 2)
	var bw := await _until(func() -> bool: return pl.aim_t >= 0.0 or pl.bow_rel_t > 0.0, 60)
	_p("vuruş anında yay basışı → %s sonra yay" % _ms(bw))
	await _idle_check("yay/iptal")
	# ---------------------------------------------------------------- 3) hareket
	await _reset(w0)
	Input.action_press("sag")
	await _f(30)
	var v_run := pl.velocity.x
	var x0 := pl.global_position.x
	await _tap("saldiri1", 2)
	var vs: Array = []
	for i in 12:
		await _f()
		vs.append(int(pl.velocity.x))
	Input.action_release("sag")
	await _until(func() -> bool: return pl.atk.is_empty(), 120)
	_p("koşudan saldırı: koşu=%d px/sn, saldırı hızları %s, savuruşta yol=%d px" % [int(v_run), str(vs), int(pl.global_position.x - x0)])
	await _idle_check("hareket/kosu")
	# havada yön verme
	await _reset(w0)
	Input.action_press("sag")
	await _f(20)
	await _tap("zipla", 3)
	await _f(10)
	await _tap("saldiri1", 2)
	var avs: Array = []
	for i in 10:
		await _f()
		avs.append(int(pl.velocity.x))
	Input.action_release("sag")
	_p("havada saldırı (sağ basılı): yatay hız %s" % str(avs))
	await _idle_check("hareket/hava")
	# dururken saldırı: adım
	await _reset(w0)
	var sx := pl.global_position.x
	await _tap("saldiri1", 2)
	await _until(func() -> bool: return pl.atk.is_empty(), 120)
	_p("dururken saldırı adımı: %.1f px" % (pl.global_position.x - sx))
	# ---------------------------------------------------------------- 4) hedef yardımı
	for case in [["arkada 26 px", -26.0], ["önde boşluk (menzil+22)", 31.0 + 12.0 + 22.0 + 10.0], ["dibinde (6 px)", 6.0]]:
		await _reset(w0)
		var e := _enemy(float(case[1]))
		await _f(4)
		var hp0 := e.hp
		await _tap("saldiri1", 2)
		await _until(func() -> bool: return pl.atk.is_empty(), 120)
		_p("hedef yardımı %s: isabet=%s yön=%d" % [case[0], "EVET" if e.hp < hp0 else "hayır", pl.facing])
	# zincir ıskalama: canlı (geri itilen) düşmana üç vuruş, her savuruşun vuruş anında bas
	for w in ["alp_kilici", "ikiz_bicak", "kargi", "dag_cekici"]:
		await _reset(w)
		var e2 := _enemy(26.0)
		await _f(4)
		var hits := 0
		var last_hp := e2.hp
		var presses := 0
		var cur: Dictionary = {}
		var pressed_cur := false
		var rel_at := -1
		# ritimli oyuncu: ilk basış, sonra her savuruşun vuruş anında bir basış (toplam 3 savuruş)
		Input.action_press("saldiri1")
		presses = 1
		rel_at = 2
		for i in 60 * 4:
			await _f()
			if e2.hp < last_hp:
				hits += 1
				last_hp = e2.hp
			if i == rel_at:
				Input.action_release("saldiri1")
			if not is_same(pl.atk, cur):
				cur = pl.atk
				pressed_cur = false
			if not pl.atk.is_empty() and pl.atk.get("phase", "") == "act" and not pressed_cur and presses < 3:
				pressed_cur = true
				Input.action_press("saldiri1")
				presses += 1
				rel_at = i + 2
			if presses >= 3 and pl.atk.is_empty() and i > rel_at + 30:
				break
		_p("zincir %s: %d savuruş, %d isabet; düşman uzaklığı %d px, oyuncu düşmanın %s" % [w, _swings, hits, int(absf(e2.global_position.x - pl.global_position.x)), "önünde" if (e2.global_position.x - pl.global_position.x) * pl.facing > 0 else "ARKASINDA"])
		await _idle_check("zincir/" + w)
	# ---------------------------------------------------------------- 5) çok düşmanlı vuruş: donma toplamı
	for w in ["alp_kilici", "ulu_kilic"]:
		await _reset(w)
		for dx in [14.0, 22.0, 30.0, 38.0]:
			_enemy(dx)
		await _f(4)
		await _tap("saldiri1", 2)
		await _until(func() -> bool: return pl.atk.is_empty(), 200)
		_p("4 düşman tek savuruş %s: donmuş kare=%d (%d ms), en büyük kamera itişi=%.1f px" % [w, _frozen, int(_frozen * 1000.0 / 60.0), _kick_max])
		await _idle_check("coklu/" + w)
	# ---------------------------------------------------------------- 6) ağır saldırı
	for w in ["alp_kilici", "ikiz_bicak", "dag_cekici"]:
		await _reset(w)
		Input.action_press("saldiri1")
		var hv := await _until(func() -> bool: return pl.atk.get("heavy", false), 90)
		await _f(20)
		Input.action_release("saldiri1")
		var hv_act := await _until(func() -> bool: return pl.atk.get("phase", "") == "act", 120)
		_p("ağır %s: basılı tut→şarj başlar %s, bırak→vuruş %s" % [w, _ms(hv), _ms(hv_act)])
		await _idle_check("agir/" + w)
		# 100 ms'lik dokunuş: hafif vuruşun gecikmesi
		await _reset(w)
		Input.action_press("saldiri1")
		var ts := 0
		var t_strike := -1
		for i in 120:
			await _f()
			if i == 6:
				Input.action_release("saldiri1")
			if pl.atk.get("phase", "") == "act":
				t_strike = i
				break
		_p("ağır %s: 100 ms dokunuş→vuruş %s (ağır=%s)" % [w, _ms(t_strike), "EVET" if _heavies > 0 else "hayır"])
		await _idle_check("dokunus/" + w)
	# şarj sırasında yuvarlan: döngü sesi / efekt kalmamalı
	await _reset("alp_kilici")
	Input.action_press("saldiri1")
	await _until(func() -> bool: return pl.atk.get("heavy", false), 90)
	await _f(10)
	await _tap("yuvarlan", 2)
	Input.action_release("saldiri1")
	await _idle_check("sarj/yuvarlan")
	_p("şarjda yuvarlan: sarj_dongusu=%s" % ("KALDI" if Ses._loops.has("sarj") else "temiz"))
	# ---------------------------------------------------------------- 7) hasar sonrası denetim
	await _reset("alp_kilici")
	var foe := _enemy(40.0)
	await _f(2)
	await _tap("saldiri1", 2)
	await _f(4)
	pl.take_hit(5.0, foe)
	await _f(2)
	await _tap("saldiri1", 2)
	var back := await _until(func() -> bool: return not pl.atk.is_empty(), 90)
	_p("hasar aldıktan 2 kare sonra saldırı → %s sonra saldırı" % _ms(back))
	await _idle_check("hasar")
	# düşman sıçrarken vurulunca temas hasarı vermeye devam ediyor mu (takas)
	await _reset("alp_kilici")
	var lunger := _enemy(70.0)
	lunger.state = "leap"
	lunger.st = 0.0
	lunger.velocity = Vector2(-270.0, -230.0)
	lunger.contact = true
	lunger._did_hit = false
	await _f(1)
	lunger.take_hit(5.0, {"kb": 110.0, "dir": 1.0})
	_p("sıçrayan düşman vurulunca temas=%s durum=%s" % [str(lunger.contact), lunger.state])
	await _idle_check("takas")
	# ---------------------------------------------------------------- özet
	var line := ""
	for w in WEAPONS:
		var s: Array = sum[w]
		line += "%s vuruş=%dms iptal=%dms arabellek=%d/%d | " % [w, int(s[0] * 1000.0 / 60.0), int(s[1] * 1000.0 / 60.0), s[2], s[3]]
	_p("OZET " + line)
	_p("TAKILMA=%d" % stuck)
	_release_all()
	get_tree().quit()


const ROLL_PROBE := 0.25


func _pin(e: Node, dx: float) -> void:
	## Düşmanı yerinde tut (geri itme testi bozmasın)
	if is_instance_valid(e) and not e.dead:
		e.global_position.x = spot.x + dx
		e.velocity.x = 0.0


func _hit_wait(e: Node, dx: float, max_f := 60) -> int:
	## Süren savuruş bir düşmana oturana dek bekle (düşman yerinde tutulur)
	for n in max_f:
		await _f()
		_pin(e, dx)
		if pl.atk.has("hit_at"):
			return n
	return -1


func _v19() -> void:
	## v19: Kut Yankısı, Çarpışma, Karşı Vuruş, Kut Alma (infaz), duruş kırılması, isabet iptali
	# --- Kut Yankısı: isabetten 1 kare sonra bas → sıradaki savuruş yankılı
	await _reset("alp_kilici")
	var e := _enemy(26.0)
	await _f(4)
	await _tap("saldiri1", 2)
	await _hit_wait(e, 26.0)
	await _f(1)
	await _tap("saldiri1", 2)
	var yk := await _until(func() -> bool: return int(pl.atk.get("yanki", 0)) > 0, 40)
	_p("v19 yankı: isabetten 1 kare sonra bas → yankılı=%s" % ("EVET" if yk >= 0 else "hayır"))
	await _until(func() -> bool: return pl.atk.is_empty(), 120)
	await _f(30)
	# erken basış (hazırlıkta) + isabette yeniden basış → yankı yok
	await _reset("alp_kilici")
	e = _enemy(26.0)
	await _f(4)
	await _tap("saldiri1", 2)
	await _f(1)
	await _tap("saldiri1", 1)
	await _hit_wait(e, 26.0)
	await _tap("saldiri1", 2)
	var yk2 := await _until(func() -> bool: return int(pl.atk.get("yanki", 0)) > 0, 30)
	_p("v19 yankı: hazırlıkta erken basış sonra isabette bas → yankılı=%s (beklenen: hayır)" % ("EVET" if yk2 >= 0 else "hayır"))
	await _until(func() -> bool: return pl.atk.is_empty(), 120)
	await _f(30)
	# geç basış (isabetten 300 ms sonra) → yankı yok
	await _reset("alp_kilici")
	e = _enemy(26.0)
	await _f(4)
	await _tap("saldiri1", 2)
	await _hit_wait(e, 26.0)
	await _f(18)
	await _tap("saldiri1", 2)
	var yk3 := await _until(func() -> bool: return int(pl.atk.get("yanki", 0)) > 0, 30)
	_p("v19 yankı: isabetten 300 ms sonra bas → yankılı=%s (beklenen: hayır)" % ("EVET" if yk3 >= 0 else "hayır"))
	await _until(func() -> bool: return pl.atk.is_empty(), 120)
	await _idle_check("v19/yanki")
	# üç yankı → Kut Mührü; yankılı vuruşun basış→temas süresi
	for w in ["ikiz_bicak", "alp_kilici", "dag_cekici"]:
		await _reset(w)
		e = _enemy(24.0)
		await _f(4)
		var m0 := int(pl.v19_stats["muhur"])
		var hp_track := e.hp
		await _tap("saldiri1", 2)
		var cont: Array = []
		var prev: Dictionary = {}
		var since := 0
		for i in 5:
			# yeni bir savuruşun isabetini bekle (basıştan isabete süre; yankılıysa "Y")
			var got := false
			for n in 150:
				await _f()
				since += 1
				_pin(e, 24.0)
				if n == 1:
					Input.action_release("saldiri1")
				if not pl.atk.is_empty() and not is_same(pl.atk, prev) and pl.atk.has("hit_at"):
					got = true
					break
			if not got:
				break
			prev = pl.atk
			if i > 0:
				cont.append(("Y" if pl.atk.get("yanki", 0) else "-") + str(int(round(since * 1000.0 / 60.0))))
			await _f(1)
			Input.action_press("saldiri1")
			since = 0
		Input.action_release("saldiri1")
		await _until(func() -> bool: return pl.atk.is_empty(), 150)
		_p("v19 yankı serisi %s: yankı=%d mühür=%d, yankı basışından isabete (Y=yankılı, ms)=%s, hasar=%d" % [w, int(pl.v19_stats["yanki"]), int(pl.v19_stats["muhur"]) - m0, str(cont), int(hp_track - e.hp)])
		await _idle_check("v19/seri/" + w)
	# --- Çarpışma: vuruşun ilk anında gelen darbe bıçağa çarpar
	await _reset("alp_kilici")
	var foe := _enemy(30.0)
	await _f(4)
	await _tap("saldiri1", 2)
	await _until(func() -> bool: return pl.atk.get("phase", "") == "act", 60)
	var hp0 := float(Game.run["hp"])
	pl.inv_t = 0.0  # adımın kısa dokunulmazlığı ölçümü bozmasın
	var took: bool = pl.take_hit(5.0, foe)
	_p("v19 çarpışma: hasar alındı=%s, düşman sersem=%.2f sn, karşılık=%.2f sn" % [str(took), foe.stun_t, pl.riposte_t])
	await _until(func() -> bool: return pl.atk.is_empty(), 120)
	await _tap("saldiri1", 2)
	var k0 := int(pl.v19_stats["carpisma"])
	await _until(func() -> bool: return pl.atk.is_empty(), 120)
	_p("v19 çarpışma sayısı=%d (hp %.0f→%.0f)" % [k0, hp0, float(Game.run["hp"])])
	await _idle_check("v19/carpisma")
	# geç darbe (vuruş penceresinden sonra): çarpışma yok
	await _reset("alp_kilici")
	foe = _enemy(30.0)
	await _f(4)
	await _tap("saldiri1", 2)
	await _until(func() -> bool: return pl.atk.get("phase", "") == "rec", 60)
	pl.inv_t = 0.0
	var took2: bool = pl.take_hit(5.0, foe)
	_p("v19 çarpışma: toparlanmada gelen darbe → hasar alındı=%s (beklenen: true)" % str(took2))
	await _idle_check("v19/carpisma_gec")
	# --- Karşı vuruş: hazırlıktaki düşmana isabet
	await _reset("alp_kilici")
	foe = _enemy(26.0)
	await _f(4)
	foe.state = "windup"
	foe.st = 9.0
	var kv := int(pl.v19_stats["karsi"])
	await _tap("saldiri1", 2)
	await _hit_wait(foe, 26.0)
	await _f(2)
	_p("v19 karşı vuruş: sayıldı=%s, düşman durumu=%s sersem=%.2f" % [str(int(pl.v19_stats["karsi"]) > kv), foe.state, foe.stun_t])
	await _until(func() -> bool: return pl.atk.is_empty(), 120)
	await _idle_check("v19/karsi")
	# --- Kut Alma: sersem + canı az düşman, her silah sınıfından biri
	for w in ["alp_kilici", "ikiz_bicak", "kargi", "kement", "teber", "dag_cekici"]:
		await _reset(w)
		foe = _enemy(34.0)
		await _f(4)
		foe.max_hp = 100.0
		foe.hp = 20.0
		foe.stun(3.0)
		var ok0: bool = foe.exec_ok()
		await _tap("saldiri1", 2)
		var n0 := int(pl.v19_stats["infaz"])
		var exn := await _until(func() -> bool: return int(pl.v19_stats["infaz"]) > n0, 90)
		_p("v19 infaz %s: işaret=%s, %s sonra öldü, savuruş=%s" % [w, str(ok0), _ms(exn), String(pl.atk.get("c", {}).get("s", "-"))])
		await _until(func() -> bool: return pl.atk.is_empty(), 120)
		await _idle_check("v19/infaz/" + w)
	# --- Duruş kırılması: ağır yaratık (biriken duruş hasarı) ve hafif yaratık (diretirken bitiriş)
	for pair in [["dag_cekici", "agac_iyesi"], ["alp_kilici", "kara_boru"], ["ikiz_bicak", "kara_boru"]]:
		await _reset(String(pair[0]))
		foe = _enemy(28.0, String(pair[1]))
		await _f(4)
		var b0 := int(pl.v19_stats["kirilma"])
		var first_break := -1
		for i in 240:
			if i % 3 == 0:
				Input.action_press("saldiri1")
			elif i % 3 == 1:
				Input.action_release("saldiri1")
			await _f()
			_pin(foe, 28.0)
			if first_break < 0 and int(pl.v19_stats["kirilma"]) > b0:
				first_break = i
				break
		_release_all()
		_p("v19 duruş kırılması %s → %s: %s sonra kırıldı" % [pair[0], pair[1], _ms(first_break)])
		await _until(func() -> bool: return pl.atk.is_empty(), 150)
		await _idle_check("v19/kirilma/" + String(pair[0]))
	# --- İsabet iptali: isabetten 4 kare sonra zıpla
	for w in ["alp_kilici", "dag_cekici"]:
		await _reset(w)
		foe = _enemy(26.0)
		await _f(4)
		await _tap("saldiri1", 2)
		await _hit_wait(foe, 26.0, 90)
		await _f(3)
		Input.action_press("zipla")
		var jc := await _until(func() -> bool: return pl.velocity.y < -100.0, 60)
		Input.action_release("zipla")
		_p("v19 isabet iptali %s: isabetten 4 kare sonra zıpla → %s sonra zıplama" % [w, _ms(jc)])
		await _idle_check("v19/iptal/" + w)
	_p("v19 sayaçlar %s" % str(pl.v19_stats))


func _klip() -> void:
	## --dovus --klip: kısa gösteri (çekim için, --write-movie): koşudan zincir + adım, arkadakine dönüş,
	## yuvarlanma içinden Dönüş Kesiği, havada yön vererek saldırı, vuruş anında zıplama ara belleği
	await _reset("alp_kilici")
	_track = false
	for dx in [110.0, 150.0]:
		var e := _enemy(dx)
		e.max_hp = 99999.0
	await _f(20)
	Input.action_press("sag")
	await _f(22)
	Input.action_release("sag")
	for i in 3:
		await _tap("saldiri1", 2)
		await _until(func() -> bool: return pl.atk.get("phase", "") == "act", 60)
	await _until(func() -> bool: return pl.atk.is_empty(), 90)
	await _f(20)
	_enemy(pl.global_position.x - spot.x - 30.0)
	await _f(10)
	await _tap("saldiri1", 2)
	await _until(func() -> bool: return pl.atk.is_empty(), 90)
	await _f(16)
	Input.action_press("sag")
	await _tap("yuvarlan", 2)
	Input.action_release("sag")
	await _f(6)
	await _tap("saldiri1", 2)
	await _until(func() -> bool: return pl.atk.is_empty(), 90)
	await _f(16)
	Input.action_press("sol")
	await _tap("zipla", 4)
	await _f(8)
	await _tap("saldiri1", 2)
	await _f(30)
	Input.action_release("sol")
	await _f(30)
	await _tap("saldiri1", 2)
	await _until(func() -> bool: return pl.atk.get("phase", "") == "act", 60)
	await _tap("zipla", 3)
	await _f(60)


func _klip_silahlar(list: Array) -> void:
	## --dovus --klip=alp_kilici,ikiz_bicak,... : her silahta önde iki düşmana tam zincir (her savuruşun temas anında
	## yeni basış: en hızlı akış), kısa ara, sonra basılı tutulan ağır saldırı. Çıktıda "[dovus] klip <silah> kare=N".
	for w in list:
		await _reset(String(w))
		_track = false
		if not OS.get_cmdline_user_args().has("--klip_bos"):
			for dx in [40.0, 66.0]:
				var e := _enemy(dx)
				e.max_hp = 99999.0
		await _f(14)
		_p("klip %s zincir kare=%d" % [w, Engine.get_frames_drawn()])
		var n := 0
		var cur: Dictionary = {}
		Input.action_press("saldiri1")
		var rel := 2
		for i in 240:
			await _f()
			if i == rel:
				Input.action_release("saldiri1")
			if not is_same(pl.atk, cur):
				cur = pl.atk
				if not cur.is_empty():
					n += 1
			if _at_contact() and n < 6 and i > rel + 1 and not Input.is_action_pressed("saldiri1"):
				Input.action_press("saldiri1")
				rel = i + 2
			if n >= 6 and pl.atk.is_empty():
				break
		_release_all()
		await _f(24)
		_p("klip %s agir kare=%d" % [w, Engine.get_frames_drawn()])
		Input.action_press("saldiri1")
		await _f(40)
		Input.action_release("saldiri1")
		await _until(func() -> bool: return pl.atk.is_empty(), 120)
		await _f(24)


var _snap_dir := ""
var _snap_n := 0


func _snap(tag: String, pre := "v19") -> void:
	## --anlik=<klasör>: o anki kareyi PNG kaydet (HDR 2D doğrusal → sRGB)
	if _snap_dir == "":
		for arg in OS.get_cmdline_user_args():
			if String(arg).begins_with("--anlik="):
				_snap_dir = String(arg).trim_prefix("--anlik=")
	if _snap_dir == "" or DisplayServer.get_name() == "headless":
		return
	await RenderingServer.frame_post_draw
	var img := get_viewport().get_texture().get_image()
	if get_viewport().use_hdr_2d:
		if img.get_format() != Image.FORMAT_RGBA8 and img.get_format() != Image.FORMAT_RGB8:
			img.convert(Image.FORMAT_RGBA8)
		img.linear_to_srgb()
	_snap_n += 1
	var out := "%s/%s_%02d_%s.png" % [_snap_dir, pre, _snap_n, tag]
	img.save_png(out)
	_p("anlik %s" % out)


func _wait_hit_new(prev: Dictionary, e: Node, dx: float, max_f := 150) -> bool:
	for n in max_f:
		await _f()
		if e != null:
			_pin(e, dx)
		if not pl.atk.is_empty() and not is_same(pl.atk, prev) and pl.atk.has("hit_at"):
			return true
	return false


func _klip19() -> void:
	## --dovus --boss --klip19 [--anlik=<klasör>] : v19 hamlelerinin gösterisi ve anlık görüntüleri
	## (1920x1080 için --pencere=1920x1080; headless değil)
	_track = false
	# 1) Kut Yankısı serisi (Alp Kılıcı): her isabetten hemen sonra bas → yankı kesikleri, üçüncüde Kut Mührü
	await _reset("alp_kilici")
	var e := _enemy(30.0)
	var e2 := _enemy(46.0)
	await _f(150)  # bölüm adı kartı kaybolsun
	await _tap("saldiri1", 2)
	var prev: Dictionary = {}
	for i in 5:
		if not await _wait_hit_new(prev, e, 30.0):
			break
		prev = pl.atk
		_pin(e2, 46.0)
		if pl.atk.get("yanki", 0) and i <= 2 and OS.get_cmdline_user_args().has("--yanki_kare"):
			for k in 12:
				await _f(1)
				await _snap("yanki_%d_%d" % [i, k])
			break
		await _f(1)
		await _tap("saldiri1", 2)
	await _until(func() -> bool: return pl.atk.is_empty(), 150)
	await _f(30)
	# 2) Çarpışma: düşmanın atılışı savuruşun ilk anında bıçağa çarpar
	await _reset("alp_kilici")
	var foe := _enemy(34.0)
	await _f(20)
	await _tap("saldiri1", 2)
	await _until(func() -> bool: return pl.atk.get("phase", "") == "act", 60)
	pl.inv_t = 0.0
	pl.take_hit(5.0, foe)
	await _f(3)
	await _snap("carpisma")
	await _until(func() -> bool: return pl.atk.is_empty(), 120)
	await _f(6)
	await _tap("saldiri1", 2)
	await _wait_hit_new({}, foe, 40.0)
	await _f(2)
	await _snap("karsilik")
	await _until(func() -> bool: return pl.atk.is_empty(), 120)
	await _f(30)
	# 3) Karşı vuruş: hazırlıktaki ("!") düşmana isabet
	await _reset("pala")
	foe = _enemy(30.0)
	await _f(20)
	foe.state = "windup"
	foe.st = 9.0
	await _f(10)
	await _snap("hazirlik")
	await _tap("saldiri1", 2)
	await _wait_hit_new({}, foe, 30.0)
	await _f(3)
	await _snap("karsi_vurus")
	await _until(func() -> bool: return pl.atk.is_empty(), 120)
	await _f(30)
	# 4) Duruş kırılması (Dağ Çekici → Kara İye) ve Kut Alma
	await _reset("dag_cekici")
	foe = _enemy(32.0, "agac_iyesi")
	foe.max_hp = 400.0
	foe.hp = 400.0
	await _f(20)
	var b0 := int(pl.v19_stats["kirilma"])
	for i in 300:
		if i % 3 == 0:
			Input.action_press("saldiri1")
		elif i % 3 == 1:
			Input.action_release("saldiri1")
		await _f()
		_pin(foe, 32.0)
		foe.hp = maxf(foe.hp, 300.0)
		if int(pl.v19_stats["kirilma"]) > b0:
			break
	_release_all()
	await _f(2)
	await _snap("durus_kirildi")
	await _until(func() -> bool: return pl.atk.is_empty(), 150)
	foe.hp = foe.max_hp * 0.2
	foe.stun(3.0)
	await _f(12)
	await _snap("infaz_isareti")
	var n0 := int(pl.v19_stats["infaz"])
	await _tap("saldiri1", 2)
	await _until(func() -> bool: return pl.atk.get("phase", "") == "act", 90)
	await _snap("infaz_vurus")
	await _until(func() -> bool: return int(pl.v19_stats["infaz"]) > n0, 60)
	await _f(4)
	await _snap("infaz_sonu")
	await _until(func() -> bool: return pl.atk.is_empty(), 120)
	await _f(30)
	# 5) İkiz bıçakla infaz (içinden geçiş) ve kılıçla (çekiş)
	for w in ["ikiz_bicak", "alp_kilici"]:
		await _reset(w)
		foe = _enemy(40.0, "kara_boru")
		await _f(16)
		foe.max_hp = 100.0
		foe.hp = 15.0
		foe.stun(3.0)
		await _f(4)
		await _tap("saldiri1", 2)
		await _until(func() -> bool: return pl.atk.get("phase", "") == "act", 90)
		await _f(1)
		await _snap("infaz_" + w)
		await _until(func() -> bool: return pl.atk.is_empty(), 120)
		await _f(24)
	# 6) Yeni zincirler: Gürz (ezme → yel değirmeni → çakma), Kor Çekici (sürükle → iniş), Ruh Kılıcı
	for w in ["gurz", "kor_cekici", "ruh_kilici"]:
		await _reset(w)
		e = _enemy(30.0, "agac_iyesi")
		e.max_hp = 99999.0
		await _f(16)
		Input.action_press("saldiri1")
		var rel := 2
		var cur: Dictionary = {}
		var n := 0
		for i in 240:
			await _f()
			_pin(e, 30.0)
			if i == rel:
				Input.action_release("saldiri1")
			if not is_same(pl.atk, cur):
				cur = pl.atk
				if not cur.is_empty():
					n += 1
			if _at_contact() and not pl.atk.has("snapped"):
				pl.atk["snapped"] = true
				await _f(1)
				await _snap("%s_%d_%s" % [w, n, String(pl.atk.get("c", {}).get("s", ""))])
				if n < 3:
					Input.action_press("saldiri1")
					rel = i + 3
			if n >= 3 and pl.atk.is_empty():
				break
		_release_all()
		await _f(24)


# ================================================================== v20: saldırı hızı statı ve Kızışma
const KZ_WEAPONS := ["ikiz_bicak", "bori_hanceri", "kurt_pencesi", "ruzgar_kilici", "kement", "od_kamcisi"]


func _hiz_reset(w: String, pct: float) -> void:
	## silahı taban aps'iyle (malzeme / kalite sapması yok: ölçüm kararlı) kuşan, saldırı hızını sabitle
	await _reset(w)
	var it: Dictionary = Game.run["slots"]["melee"]
	it["aps"] = float(Data.find_item(w)["aps"])
	it["affixes"] = []
	it["flaw"] = ""
	pl.hiz_test = pct
	pl.kz_n = 0


func _tempo_olc(w: String, kz_full := false) -> Array:
	## 20 Hz seri basış: [basış→temas (kare), zincir aralıkları (ms)] — 1b ile aynı yöntem
	var contacts: Array = []
	var cur: Dictionary = {}
	var seen := false
	var first_ck := -1
	var it: Dictionary = Game.run["slots"]["melee"]
	for i in 300:
		if kz_full:
			pl.kz_n = int(it.get("kz_max", 5))
			pl._kz_id = w
			pl.kz_t = 0.0
		if i % 3 == 0 and contacts.size() < 4:
			Input.action_press("saldiri1")
		elif i % 3 == 1:
			Input.action_release("saldiri1")
		await _f()
		if not is_same(pl.atk, cur):
			cur = pl.atk
			seen = false
		if not pl.atk.is_empty() and not seen and _at_contact():
			seen = true
			contacts.append(i)
			if first_ck < 0:
				first_ck = i + 1
		if contacts.size() >= 4:
			break
	Input.action_release("saldiri1")
	var gaps: Array = []
	for j in range(1, contacts.size()):
		gaps.append(int(round((int(contacts[j]) - int(contacts[j - 1])) * 1000.0 / 60.0)))
	return [first_ck, gaps]


func _hiz() -> void:
	_p("---- v20 saldırı hızı (TEMPO_YAVAS=%s, üst sınır %%%d / Kızışma dahil %%%d)" % [str(Player.TEMPO_YAVAS), int(Player.HIZ["cap"]), int(Player.HIZ["cap_all"])])
	var only := ""
	for arg in OS.get_cmdline_user_args():
		if String(arg).begins_with("--hiz_silah="):
			only = String(arg).trim_prefix("--hiz_silah=")
	# --- 1) tempo tablosu: saldırı hızı 0 / 20 / 40 ve tam Kızışma
	var line := ""
	for w in TEMPO_WEAPONS:
		if only != "" and not (w in only.split(",")):
			continue
		var row := "%s" % w
		for pct in [0.0, 20.0, 40.0]:
			await _hiz_reset(w, pct)
			var r := await _tempo_olc(w)
			row += " | %%%d: %d/%s" % [int(pct), int(round(int(r[0]) * 1000.0 / 60.0)), str(r[1])]
			await _idle_check("hiz/%s/%d" % [w, int(pct)])
		if w in KZ_WEAPONS:
			await _hiz_reset(w, 0.0)
			var it: Dictionary = Game.run["slots"]["melee"]
			var r2 := await _tempo_olc(w, true)
			row += " | Kızışma %d×%s: %d/%s" % [int(it["kz_max"]), ItemGen.fmt(float(it["kz_v"])), int(round(int(r2[0]) * 1000.0 / 60.0)), str(r2[1])]
			pl.kz_n = 0
			await _idle_check("hiz/%s/kz" % w)
		_p("hiz " + row)
		line += row + " || "
	pl.hiz_test = -1.0
	# --- 2) en az kare: %60'ta hiçbir evre okunurluk sınırının (ya da zaten kısaysa tabanın) altına inmiyor
	var bad := 0
	for w in TEMPO_WEAPONS:
		var it2 := ItemGen.roll(w, 1, "demir", 0)
		it2["aps"] = float(Data.find_item(w)["aps"])
		for c in Player._combo_for(it2)["chain"]:
			var sw: Dictionary = Player.SWINGS[c["s"]]
			var p0 := Player.tempo_phases(it2, c, sw, true, 1.0, "", 0.0)
			var p6 := Player.tempo_phases(it2, c, sw, true, 1.0, "", Player.hiz_oran(it2, 60.0))
			var mins := [float(Player.HIZ["min_wind"]), float(Player.HIZ["min_sweep"]), float(Player.HIZ["min_lock"])]
			for i in 3:
				if float(p6[i]) < minf(float(p0[i]), float(mins[i])) - 0.0001:
					bad += 1
	_p("hiz en_az_kare ihlali=%d" % bad)
	# --- 3) kaynaklar ve üst sınır
	await _reset("alp_kilici")
	var mel: Dictionary = Game.run["slots"]["melee"]
	mel["affixes"] = [{"id": "hiz", "v": 12.0}]
	var shield := ItemGen.roll("yuvarlak_kalkan", 1, "demir", 0)
	shield["affixes"] = [{"id": "saldiri_hizi", "v": 8.0}]
	Game.run["slots"]["g2"] = shield
	var kurt0 := int(Game.run["ongun"]["kurt"])
	Game.run["ongun"]["kurt"] = 3
	var lut0: Array = (Game.run.get("lutuf", []) as Array).duplicate()
	Game.grant_lutuf("yel_ana")
	_p("hiz kaynaklar=%s toplam=%%%s" % [str(Player.hiz_kaynak(mel)), ItemGen.fmt(Player.hiz_kalici(mel))])
	Game.run["ongun"]["kurt"] = 30
	_p("hiz üst_sınır: Kurt 30 → toplam=%%%s (en çok %%%d)" % [ItemGen.fmt(Player.hiz_kalici(mel)), int(Player.HIZ["cap"])])
	Game.run["ongun"]["kurt"] = 0
	Game.run["lutuf"] = []
	Game.run["slots"]["g2"] = {}
	mel["affixes"] = []
	var dps_line := ""
	for w in ["ikiz_bicak", "alp_kilici", "kargi", "gurz", "ulu_kilic"]:
		var it3 := ItemGen.roll(w, 1, "demir", 0)
		it3["aps"] = float(Data.find_item(w)["aps"])
		it3["affixes"] = []
		it3["flaw"] = ""
		var a0 := ItemGen.aps_eff(it3)
		var d0 := ItemGen.dps(it3)
		it3["affixes"] = [{"id": "hiz", "v": 20.0}]
		var a20 := ItemGen.aps_eff(it3)
		var d20 := ItemGen.dps(it3)
		dps_line += "%s hız %s→%s/sn SnH %s→%s | " % [w, ItemGen.fmt(a0), ItemGen.fmt(a20), ItemGen.fmt(d0), ItemGen.fmt(d20)]
	_p("hiz kart (+%20 Çevik): " + dps_line)
	Game.run["ongun"]["kurt"] = kurt0
	Game.run["lutuf"] = lut0
	# --- 4) yay: gerilme ve atış kilidi
	pl.hiz_test = 0.0
	await _f(2)
	var d0b := Okculuk.prof(Game.run["slots"]["second"])
	var dr0 := float(d0b["draw"])
	var rc0 := float(d0b["rec"])
	pl.hiz_test = 40.0
	await _f(2)
	var d40 := Okculuk.prof(Game.run["slots"]["second"])
	_p("hiz yay (Türk yayı): gerilme %d → %d ms, kilit %d → %d ms (%%40)" % [int(dr0 * 1000.0), int(float(d40["draw"]) * 1000.0), int(rc0 * 1000.0), int(float(d40["rec"]) * 1000.0)])
	pl.hiz_test = -1.0
	await _f(2)
	# --- 5) Kızışma: yük kazanma (iki düşmana vuruş tek yük), sönme, hasar
	for w in ["ikiz_bicak", "kement"]:
		await _hiz_reset(w, 0.0)
		pl.hiz_test = -1.0
		var it4: Dictionary = Game.run["slots"]["melee"]
		var dx := 22.0 if w == "ikiz_bicak" else 40.0
		var e := _enemy(dx)
		var e2 := _enemy(dx + 8.0)
		await _f(4)
		var seq: Array = []
		for i in 9:
			Input.action_press("saldiri1")
			await _f(1)
			Input.action_release("saldiri1")
			for k in 11:
				await _f(1)
				_pin(e, dx)
				_pin(e2, dx + 8.0)
			seq.append(pl.kz_n)
		var full_t := -1.0
		var t0 := Game.clock()
		var decay_first := -1.0
		var n0 := pl.kz_n
		while Game.clock() - t0 < 4.0:
			await _f(1)
			if decay_first < 0.0 and pl.kz_n < n0:
				decay_first = Game.clock() - t0
			if pl.kz_n == 0:
				full_t = Game.clock() - t0
				break
		_p("hiz Kızışma %s (+%%%s × %d): 9 savuruşta yük=%s; ilk sönme %.2f sn, tümden %.2f sn" % [w, ItemGen.fmt(float(it4["kz_v"])), int(it4["kz_max"]), str(seq), decay_first, full_t])
		# hasar alınca söner
		pl.kz_n = 3
		pl._kz_id = w
		pl.kz_t = 0.0
		pl.inv_t = 0.0
		pl.roll_t = 0.0
		pl.take_hit(3.0, e)
		_p("hiz Kızışma hasar sonrası yük=%d" % pl.kz_n)
		pl.inv_t = 0.0
		pl.hurt_t = 0.0
		_clear_enemies()
		await _idle_check("hiz/kz/" + w)
	# ses perdesi
	await _hiz_reset("ikiz_bicak", 0.0)
	pl.kz_n = int(Game.run["slots"]["melee"]["kz_max"])
	pl._kz_id = "ikiz_bicak"
	_p("hiz ses perdesi tam yükte ×%s" % ItemGen.fmt(pl._kz_pitch()))
	pl.kz_n = 0
	pl.hiz_test = -1.0
	_p("HIZ " + line)


func _klip20() -> void:
	## --dovus --boss --klip20 --anlik=<klasör> (headless değil): Kızışma görseli ve HUD göstergesi anlık görüntüleri
	_track = false
	await _hiz_reset("ikiz_bicak", 0.0)
	pl.hiz_test = -1.0
	var e := _enemy(26.0)
	var e2 := _enemy(40.0)
	await _f(150)  # bölüm adı kartı kaybolsun
	var done := {}
	for i in 40:
		Input.action_press("saldiri1")
		await _f(1)
		Input.action_release("saldiri1")
		for k in 8:
			await _f(1)
			_pin(e, 26.0)
			_pin(e2, 40.0)
			if pl.kz_n in [2, 4] and not done.has(pl.kz_n) and not pl.atk.is_empty() and pl.atk.get("phase", "") == "act":
				done[pl.kz_n] = true
				await _snap("kizisma_yuk%d" % pl.kz_n, "v20")
			if pl.kz_flash > 0.6 and not done.has("tam"):
				done["tam"] = true
				await _snap("kizisma_tam_parilti", "v20")
		if done.has("tam") and i > 12:
			break
	# tam yükte savuruş (hız çizgileri)
	for i in 6:
		Input.action_press("saldiri1")
		await _f(1)
		Input.action_release("saldiri1")
		for k in 8:
			await _f(1)
			_pin(e, 26.0)
			_pin(e2, 40.0)
			if i == 3 and k == 3:
				await _snap("kizisma_tam_savurus", "v20")
	# düşmansız: tam yükte boşa savuruş (hız çizgileri net görünsün) ve dururken eldeki tüller
	_clear_enemies()
	for i in 4:
		Input.action_press("saldiri1")
		await _f(1)
		Input.action_release("saldiri1")
		for k in 8:
			pl.kz_n = int(Game.run["slots"]["melee"]["kz_max"])
			pl.kz_t = 0.0
			await _f(1)
			if i == 2 and k in [2, 4]:
				await _snap("kizisma_bos_savurus_%d" % k, "v20")
	for k in 40:
		pl.kz_n = int(Game.run["slots"]["melee"]["kz_max"])
		pl.kz_t = 0.0
		await _f(1)
	await _snap("kizisma_durus", "v20")
	# kement ile yük
	await _hiz_reset("kement", 0.0)
	pl.hiz_test = -1.0
	e = _enemy(40.0)
	for i in 10:
		Input.action_press("saldiri1")
		await _f(1)
		Input.action_release("saldiri1")
		for k in 12:
			await _f(1)
			_pin(e, 40.0)
			if i == 6 and k == 4:
				await _snap("kizisma_kement", "v20")
	await _f(10)


func _yildirim() -> void:
	## v21 Yıldırım Hamlesi: tam şarjlı hamlede yıldırım oyuncunun yerine değil, deldiği düşmanların tepesine iner.
	## Çıktı: inen her şimşeğin konumu, en yakın düşmana uzaklığı ve oyuncuya uzaklığı.
	var strikes: Array = []
	var on_add := func(n: Node) -> void:
		if n is ThunderFX:
			strikes.append(n)
	get_tree().node_added.connect(on_add)
	for full in [true, false]:
		await _reset("yildirim_kilici")
		strikes.clear()
		var foes := [_enemy(60.0), _enemy(110.0)]
		await _f(2)
		var start := pl.global_position
		Input.action_press("saldiri1")
		await _until(func() -> bool: return pl.atk.get("heavy", false), 90)
		await _f(60 if full else 4)
		Input.action_release("saldiri1")
		await _f(40)
		var parts: Array = []
		for s in strikes:
			if not is_instance_valid(s):
				continue
			var nd := 99999.0
			for e in foes:
				if is_instance_valid(e):
					nd = minf(nd, (s as Node2D).global_position.distance_to(e.global_position))
			parts.append("(düşmana %.0f px, başlangıca %.0f px, güç %.2f)" % [nd, (s as Node2D).global_position.distance_to(start), float(s.strength)])
		_p("yildirim %s: şimşek=%d %s" % ["tam şarj" if full else "kısa şarj", strikes.size(), " ".join(parts)])
		await _idle_check("yildirim/" + ("tam" if full else "kisa"))
	get_tree().node_added.disconnect(on_add)
