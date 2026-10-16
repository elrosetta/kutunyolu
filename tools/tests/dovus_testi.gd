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


func _ms(fr: int) -> String:
	return "yok" if fr < 0 else "%d kare (%d ms)" % [fr, int(round(fr * 1000.0 / 60.0))]


func _run() -> void:
	await get_tree().create_timer(0.6).timeout
	lv = main.level
	pl = lv.player
	spot = _find_spot()
	_p("arena=%s stil=%s" % [str(spot), "v2" if OS.get_cmdline_user_args().has("--stil=v2") else "v1"])
	if OS.get_cmdline_user_args().has("--klip"):
		await _klip()
		get_tree().quit()
		return
	var sum := {}
	# ---------------------------------------------------------------- 1) gecikme, kilit, ara bellek (her silah)
	for w in WEAPONS:
		await _reset(w)
		Input.action_press("saldiri1")
		var l_start := await _until(func() -> bool: return not pl.atk.is_empty(), 30)
		Input.action_release("saldiri1")
		var l_strike := await _until(func() -> bool: return pl.atk.get("phase", "") == "act", 120)
		var l_rec := await _until(func() -> bool: return pl.atk.is_empty() or pl.atk.get("phase", "") == "rec", 120)
		var l_end := await _until(func() -> bool: return pl.atk.is_empty(), 120)
		var strike_total := l_start + 1 + l_strike + 1
		var cancel_total := strike_total + l_rec + 1
		_p("%s: basış→saldırı=%s basış→vuruş=%s basış→iptal_edilebilir=%s kuyruk=%s" % [w, _ms(l_start), _ms(strike_total), _ms(cancel_total), _ms(l_end + 1)])
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
