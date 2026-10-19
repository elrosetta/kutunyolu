extends Node
## v19 yay / okçuluk testi (betikli girdi; Input.action_press ile oyuncunun kendi yolundan sürer):
##   godot --headless --path . --quit-after 99999 -- --yay --boss            (düz arena, ölçüm)
##   godot --path . -- --yay --boss --pencere=1920x1080 --yay_goruntu=C:/mutlak/klasor   (ekran görüntüleri)
## Her yay için: dokunuş→atış→isabet gecikmesi, tam bırakış (pencerede bırak), geç bırakış, basılı tutma (Akıncı:
## seri atış), 10 Hz seri basış, saldırı vuruşunda yay basışı (ara bellek), gerilirken saldırı (çabuk atış),
## gerilirken yuvarlanma, saplanan ok + yakın dövüşle sökme, yere düşen / saplanan oku toplama, havada süzülüş,
## takılı kalan durum. Çıktı: "[yay] ..." satırları + "[yay] OZET ..." + "[yay] TAKILMA=n".
## v25 cephane: çok oklu yayda haklar biter (boşken kuru tık, ok çıkmaz), atmazken dolar (ilk hak süresi), yerden
## toplanan ok anında bir hak; tek oklu yaylar sınırsız. "[yay] CEPHANE ..." satırları + "[yay] CEPHANE_HATA=n".
## Görüntüler (v25): unsur başına ok izi (iz_<unsur>), cephane imleri, cirit izi, Gök Asası / Gök Gürlemesi.

var main: Node
var lv: Node
var pl: Player
var spot := Vector2.ZERO
var stuck := 0
var shots_dir := ""
var cephane_hata := 0

const BOWS := ["turk_yayi", "akinci_yayi", "saganak_yayi", "od_oklari", "tufan_yayi"]
const ACTS := ["saldiri1", "saldiri2", "zipla", "yuvarlan", "sag", "sol", "yukari", "asagi", "techizat1", "techizat2", "sise", "kut"]


func _ready() -> void:
	process_mode = Node.PROCESS_MODE_ALWAYS
	for arg in OS.get_cmdline_user_args():
		if String(arg).begins_with("--yay_goruntu="):
			shots_dir = String(arg).trim_prefix("--yay_goruntu=")
	_run.call_deferred()


func _p(s: String) -> void:
	print("[yay] ", s)


func _f(n := 1) -> void:
	for i in n:
		await get_tree().physics_frame
		_tick()


func _tick() -> void:
	if pl == null:
		return
	Game.run["hp"] = float(Game.run["max_hp"])
	for e in get_tree().get_nodes_in_group("dusman"):
		if is_instance_valid(e) and not e.dead:
			e.cd = 99.0
			if not e.has_meta("olebilir"):
				e.hp = maxf(e.hp, 1.0)


func _release_all() -> void:
	for a in ACTS:
		Input.action_release(a)


func _tap(a: String, frames := 2) -> void:
	Input.action_press(a)
	await _f(frames)
	Input.action_release(a)


func _until(cond: Callable, max_f := 120) -> int:
	for n in max_f:
		await _f()
		if cond.call():
			return n
	return -1


func _ms(fr: int) -> String:
	return "yok" if fr < 0 else "%d kare (%d ms)" % [fr, int(round(fr * 1000.0 / 60.0))]


func _find_spot() -> Vector2:
	if "boss" in lv and lv.boss != null and is_instance_valid(lv.boss):
		lv.boss.remove_from_group("dusman")
		lv.boss.queue_free()
		lv.boss = null
		return Vector2(28 * Level.TS + 12, lv.surface_y(28) * Level.TS - 1)
	for x in range(20, Level.W - 30):
		var y0: int = lv.surface_y(x)
		var ok := true
		for dx in range(-7, 16):
			if lv.surface_y(x + dx) != y0:
				ok = false
				break
		if ok:
			return Vector2(x * Level.TS + 12, y0 * Level.TS - 1)
	return Vector2(40 * Level.TS + 12, lv.surface_y(40) * Level.TS - 1)


func _clear() -> void:
	for e in get_tree().get_nodes_in_group("dusman"):
		e.remove_from_group("dusman")
		e.queue_free()
	for c in lv.proj_root.get_children():
		c.queue_free()


func _reset(bow: String, melee := "alp_kilici") -> void:
	_release_all()
	_clear()
	Game.run["slots"]["melee"] = ItemGen.roll(melee, 1, "demir", 0)
	Game.run["slots"]["second"] = ItemGen.roll(bow, 1, "demir", 0)
	pl.on_equip()
	pl.global_position = spot
	pl.velocity = Vector2.ZERO
	pl.facing = 1
	pl.roll_t = 0.0
	pl.roll_cd = 0.0
	pl.hurt_t = 0.0
	pl.inv_t = 0.0
	pl.melee_buf = 0.0
	pl.sec_buf = 0.0
	pl.jump_buf = 0.0
	pl.combo_break("")
	pl.okc.hazir = 0
	for k in pl.cd.keys():
		pl.cd[k] = 0.0
	pl.okc.ammo_fill()
	await _f(20)


func _enemy(dx: float, kind := "kara_boru", dy := 0.0) -> Enemy:
	var e: Enemy = lv.spawn_enemy(kind, spot + Vector2(dx, dy))
	e.max_hp = 99999.0
	e.hp = 99999.0
	e.speed = 0.0
	e.cd = 99.0
	e.aggro = false
	e.facing = -1 if dx > 0 else 1
	return e


func _st(k: String) -> int:
	return int(pl.okc.stats[k])


func _idle_check(tag: String) -> void:
	_release_all()
	await _f(60)
	# v26: vuruş duraklaması / ağır çekim dipleri GERÇEK zamanla söner (Game.clock); --fixed-fps 60 headless koşu gerçek
	# zamandan hızlı aktığında 60 kare dibin sonuna yetmeyebiliyordu (kalıcı takılma değil). En çok 0,8 sn gerçek zaman bekle.
	var t_end := Time.get_ticks_msec() + 800
	while absf(Engine.time_scale - 1.0) > 0.01 and Time.get_ticks_msec() < t_end:
		await _f(1)
	var bad: Array = []
	if not pl.atk.is_empty():
		bad.append("atk")
	if pl.aim_t >= 0.0:
		bad.append("aim")
	if pl.roll_t > 0.0:
		bad.append("roll")
	if absf(Engine.time_scale - 1.0) > 0.01:
		bad.append("time_scale=%.2f" % Engine.time_scale)
	if not bad.is_empty():
		stuck += 1
		_p("TAKILDI %s: %s" % [tag, ", ".join(bad)])


func _shot(name: String) -> void:
	if shots_dir == "":
		return
	await RenderingServer.frame_post_draw
	var img := get_viewport().get_texture().get_image()
	var path := shots_dir.path_join(name + ".png")
	img.save_png(path)
	_p("görüntü %s" % path)


func _run() -> void:
	await get_tree().create_timer(0.6).timeout
	lv = main.level
	pl = lv.player
	spot = _find_spot()
	_p("arena=%s stil=%s" % [str(spot), Data.STIL])
	if shots_dir != "":
		await _goruntuler()
		get_tree().quit()
		return
	if OS.get_cmdline_user_args().has("--yay_cephane"):
		await _cephane()
		_p("CEPHANE_HATA=%d" % cephane_hata)
		get_tree().quit()
		return
	var sum := ""
	for b in BOWS:
		var pr: Dictionary = Okculuk.prof({"id": b})
		# ---- dokunuş: basış -> atış -> isabet (150 px)
		await _reset(b)
		var e := _enemy(150.0)
		await _f(4)
		var f0 := _st("fire")
		var h0 := _st("isabet")
		Input.action_press("saldiri2")
		var t_fire := -1
		for i in 60:
			await _f()
			if i == 1:
				Input.action_release("saldiri2")
			if _st("fire") > f0:
				t_fire = i
				break
		Input.action_release("saldiri2")
		var t_hit := await _until(func() -> bool: return _st("isabet") > h0, 60)
		_p("%s: dokunuş→atış=%s atış→isabet(150px)=%s şarj=%.2f" % [b, _ms(t_fire + 1), _ms(t_hit + 1), float(pl.okc.stats["last_charge"])])
		sum += "%s dokunuş=%dms " % [b, int((t_fire + 1) * 1000.0 / 60.0)]
		# ---- basılı tut
		await _reset(b)
		e = _enemy(150.0)
		await _f(4)
		if bool(pr["auto"]):
			f0 = _st("fire")
			Input.action_press("saldiri2")
			await _f(60)
			Input.action_release("saldiri2")
			await _f(20)
			var n_auto := _st("fire") - f0
			_p("%s: 1 sn basılı tut → %d ok (seri atış)" % [b, n_auto])
			sum += "seri=%d/sn " % n_auto
		else:
			f0 = _st("fire")
			var p0 := _st("perfect")
			Input.action_press("saldiri2")
			var t_full := await _until(func() -> bool: return pl.okc.in_perfect(), 90)
			Input.action_release("saldiri2")
			await _until(func() -> bool: return _st("fire") > f0, 30)
			var perf_ok := _st("perfect") > p0
			await _f(30)
			_p("%s: basış→tam gerilme=%s, pencerede bırak → tam_bırakış=%s, isabet kritik hasar=%d" % [b, _ms(t_full + 1), "EVET" if perf_ok else "hayır", int(99999.0 - e.hp)])
			# geç bırakış: pencereden sonra
			await _reset(b)
			f0 = _st("fire")
			p0 = _st("perfect")
			Input.action_press("saldiri2")
			await _f(int((float(pr["draw"]) + float(pr["perfect"]) + 0.25) * 60.0))
			Input.action_release("saldiri2")
			await _until(func() -> bool: return _st("fire") > f0, 30)
			_p("%s: geç bırakış → atış=%s tam_bırakış=%s (beklenen: hayır)" % [b, "EVET" if _st("fire") > f0 else "YOK", "EVET" if _st("perfect") > p0 else "hayır"])
			sum += "tam=%s " % ("ok" if perf_ok else "YOK")
		await _idle_check(b + "/tut")
		# ---- 10 Hz seri basış, 1,2 sn
		await _reset(b)
		f0 = _st("fire")
		for i in 12:
			await _tap("saldiri2", 2)
			await _f(4)
		await _f(40)
		var n_tap := _st("fire") - f0
		_p("%s: 12 basış (10 Hz) → %d ok" % [b, n_tap])
		sum += "seri_bas=%d/12 | " % n_tap
		await _idle_check(b + "/seri")
	# ---------------------------------------------------------------- akış
	var b0 := "turk_yayi"
	# saldırının vuruş anında yay basışı -> toparlanmada keser, ok çıkar
	await _reset(b0)
	var f1 := _st("fire")
	await _tap("saldiri1", 2)
	await _until(func() -> bool: return pl.atk.get("phase", "") == "act", 60)
	await _tap("saldiri2", 2)
	var bw := await _until(func() -> bool: return _st("fire") > f1, 60)
	_p("akış: vuruş anında yay dokunuşu → %s sonra ok" % _ms(bw))
	await _idle_check("akis/vurus_yay")
	# gerilirken saldırı: 0,2 sn gerilmiş -> saldırı aynı karede; v22: ok kendiliğinden çıkmaz (çabuk atış kalktı)
	await _reset(b0)
	f1 = _st("fire")
	Input.action_press("saldiri2")
	await _f(12)
	await _tap("saldiri1", 2)
	var ma := await _until(func() -> bool: return not pl.atk.is_empty(), 30)
	Input.action_release("saldiri2")
	await _f(30)
	_p("akış: gerilirken saldırı → saldırı %s sonra, kendiliğinden ok=%s (v22 beklenen: hayır)" % [_ms(ma), "EVET" if _st("fire") > f1 else "hayır"])
	await _idle_check("akis/ger_saldiri")
	# gerilirken yuvarlanma
	await _reset(b0)
	Input.action_press("saldiri2")
	await _f(8)
	await _tap("yuvarlan", 2)
	var rl := await _until(func() -> bool: return pl.roll_t > 0.0, 30)
	Input.action_release("saldiri2")
	_p("akış: gerilirken yuvarlan → %s, gerilme bırakıldı=%s" % [_ms(rl), "EVET" if pl.aim_t < 0.0 else "HAYIR"])
	await _idle_check("akis/ger_yuv")
	# yuvarlanırken basılan yay: yuvarlanma bitince ok (kaybolmaz)
	await _reset(b0)
	f1 = _st("fire")
	await _tap("yuvarlan", 2)
	await _f(4)
	await _tap("saldiri2", 2)
	var ry := await _until(func() -> bool: return _st("fire") > f1, 60)
	_p("akış: yuvarlanırken yay dokunuşu → %s sonra ok" % _ms(ry))
	await _idle_check("akis/yuv_yay")
	# Akıncı: yuvarlanırken atış
	await _reset("akinci_yayi")
	f1 = _st("fire")
	await _tap("yuvarlan", 2)
	await _f(3)
	await _tap("saldiri2", 2)
	_p("akış: Akıncı yuvarlanırken atış=%s (yuvarlanma sürüyor=%s)" % ["EVET" if _st("fire") > f1 else "hayır", str(pl.roll_t > 0.0)])
	await _idle_check("akis/akinci_yuv")
	# ---------------------------------------------------------------- ok sökme
	await _reset(b0)
	var foe := _enemy(46.0)
	await _f(4)
	for i in 3:
		await _tap("saldiri2", 2)
		await _f(16)
	await _f(10)
	var n_stuck := pl.okc.stuck_n(foe)
	var hz0 := pl.okc.hazir
	var s0 := _st("sokme")
	var hp_before := foe.hp
	await _tap("saldiri1", 2)
	await _until(func() -> bool: return pl.atk.is_empty(), 90)
	_p("ok sökme: saplı ok=%d → sökme=%s hazır_ok %d→%d, vuruş hasarı=%d" % [n_stuck, "EVET" if _st("sokme") > s0 else "HAYIR", hz0, pl.okc.hazir, int(hp_before - foe.hp)])
	# hazır ok: sıradaki atış anında tam bırakış
	var p1 := _st("perfect")
	f1 = _st("fire")
	await _f(10)
	await _tap("saldiri2", 2)
	var hf := await _until(func() -> bool: return _st("fire") > f1, 30)
	_p("hazır ok: dokunuş → %s sonra ok, tam_bırakış=%s" % [_ms(hf), "EVET" if _st("perfect") > p1 else "HAYIR"])
	await _idle_check("sokme")
	# ---------------------------------------------------------------- ok toplama: ölen düşmandaki oklar dökülür
	await _reset(b0)
	var victim := _enemy(70.0)
	victim.set_meta("olebilir", true)
	await _f(4)
	for i in 2:
		await _tap("saldiri2", 2)
		await _f(14)
	await _f(6)
	var ns := pl.okc.stuck_n(victim)
	victim.hp = 1.0
	victim.max_hp = 20.0
	await _tap("saldiri2", 2)
	await _f(50)
	var t0 := _st("toplama")
	Input.action_press("sag")
	var pk := await _until(func() -> bool: return _st("toplama") > t0, 150)
	Input.action_release("sag")
	await _f(80)
	_p("ok toplama: ölen düşmanda saplı=%d → toplanan=%d (ilk %s), hazır_ok=%d" % [ns, _st("toplama") - t0, _ms(pk), pl.okc.hazir])
	# ıskalanan ok yere saplanır ve toplanır
	await _reset(b0)
	t0 = _st("toplama")
	pl.facing = 1
	await _tap("saldiri2", 2)  # dokunuş: yarım güçte ok, yere düşer
	await _f(70)
	var grounded := 0
	for c in lv.proj_root.get_children():
		if c is Ok and c._state == 1:
			grounded += 1
	Input.action_press("sag")
	var pk2 := await _until(func() -> bool: return _st("toplama") > t0, 200)
	Input.action_release("sag")
	_p("ok toplama: ıskalanan ok yerde=%d, yürüyerek toplandı=%s" % [grounded, _ms(pk2)])
	await _idle_check("toplama")
	# ---------------------------------------------------------------- havada süzülüş
	await _reset(b0)
	await _tap("zipla", 4)
	await _until(func() -> bool: return pl.velocity.y > 0.0, 60)
	var vy_free := 0.0
	await _f(10)
	vy_free = pl.velocity.y
	await _until(func() -> bool: return pl.is_on_floor(), 120)
	await _f(10)
	await _tap("zipla", 4)
	await _until(func() -> bool: return pl.velocity.y > 0.0, 60)
	Input.action_press("saldiri2")
	var vmax := 0.0
	for i in 10:
		await _f()
		vmax = maxf(vmax, pl.velocity.y)
	Input.action_release("saldiri2")
	await _f(40)
	_p("süzülüş: tepe+10 kare düşüş hızı serbest=%d px/sn, gerilirken en çok=%d px/sn" % [int(vy_free), int(vmax)])
	await _idle_check("suzulus")
	await _cephane()
	_p("OZET " + sum)
	_p("TAKILMA=%d" % stuck)
	_p("CEPHANE_HATA=%d" % cephane_hata)
	_release_all()
	get_tree().quit()


func _ch(ok: bool, s: String) -> void:
	if not ok:
		cephane_hata += 1
	_p("CEPHANE %s %s" % ["tamam" if ok else "HATA", s])


func _cephane() -> void:
	## v25 cephane denetimi
	# ---- çok oklu yay: haklar biter, boşken kuru tık
	for b in ["saganak_yayi", "tufan_yayi", "od_oklari"]:
		await _reset(b)
		var mx := pl.okc.ammo_max
		var f0 := _st("fire")
		var k0 := _st("kuru")
		var pr: Dictionary = Okculuk.prof({"id": b})
		var wait_f := int((float(pr["rec"]) + 0.05) * 60.0) + 2
		for i in mx + 2:
			await _tap("saldiri2", 2)
			await _f(wait_f + 10)
		var fired := _st("fire") - f0
		_ch(mx > 0 and fired == mx and pl.okc.ammo == 0 and _st("kuru") > k0,
			"%s: hak=%d, %d basışta atış=%d, kalan=%d, kuru tık=%d" % [b, mx, mx + 2, fired, pl.okc.ammo, _st("kuru") - k0])
		# ---- atmazken dolar
		var t_reg := await _until(func() -> bool: return pl.okc.ammo >= 1, 300)
		var rt := Okculuk.ammo_regen_of({"id": b, "kind": "bow"})
		_ch(t_reg >= 0 and t_reg / 60.0 <= rt + Okculuk.AMMO_WAIT + 0.1, "%s: boşken ilk hak %s sonra doldu (dolum %.1f sn + bekleme)" % [b, _ms(t_reg + 1), rt])
		await _idle_check(b + "/cephane")
	# ---- yerdeki ok anında bir hak
	await _reset("saganak_yayi")
	pl.okc.ammo = 1
	pl.facing = 1
	var t0 := _st("toplama")
	await _tap("saldiri2", 2)   # dokunuş: yarım güçte yelpaze, oklar yere saplanır
	await _f(50)
	pl.okc.ammo = 0
	pl.okc._ammo_wait = 99.0    # dolum dursun: artış yalnızca toplamadan gelsin
	Input.action_press("sag")
	var gain := 0
	for i in 200:
		var a0 := pl.okc.ammo
		await _f()
		if _st("toplama") > t0:
			gain = pl.okc.ammo - a0
			break
	Input.action_release("sag")
	pl.okc._ammo_wait = 0.0
	_ch(_st("toplama") > t0 and gain >= 1, "toplama: yerdeki ok toplandı=%s, hak +%d (hazır ok=%d)" % [str(_st("toplama") > t0), gain, pl.okc.hazir])
	# boşken hazır okla atış yine çıkar
	pl.okc.ammo = 0
	var f1 := _st("fire")
	await _f(20)
	await _tap("saldiri2", 2)
	await _f(30)
	_ch(pl.okc.hazir == 0 or _st("fire") > f1, "boş cephane + hazır ok: atış=%s" % str(_st("fire") > f1))
	await _idle_check("cephane/toplama")
	# ---- tek oklu yaylar sınırsız
	for b in ["turk_yayi", "akinci_yayi"]:
		await _reset(b)
		var f2 := _st("fire")
		var k2 := _st("kuru")
		for i in 16:
			await _tap("saldiri2", 2)
			await _f(22)
		_ch(pl.okc.ammo_max == 0 and _st("fire") - f2 == 16 and _st("kuru") == k2, "%s: sınırsız (hak=%d), 16 basış → %d ok, kuru tık=%d" % [b, pl.okc.ammo_max, _st("fire") - f2, _st("kuru") - k2])
		await _idle_check(b + "/sinirsiz")


func _goruntuler() -> void:
	## Ekran görüntüleri (pencereli çalıştır): tam gerilme + halka, tam bırakış anı, uçuş izi, saplı oklar, Tufan yelpazesi
	await _goruntuler_v25()
	await _reset("turk_yayi")
	_enemy(130.0)
	_enemy(190.0, "kara_boru", -40.0)
	await _f(20)
	Input.action_press("saldiri2")
	var d := float(Okculuk.prof({"id": "turk_yayi"})["draw"])
	await _f(int((d - 0.07) * 60.0))
	await _shot("yay_halka")
	await _until(func() -> bool: return pl.okc.in_perfect(), 30)
	await _f(1)
	await _shot("yay_tam")
	Input.action_release("saldiri2")
	await _f(2)
	await _shot("yay_birakis")
	await _f(2)
	await _shot("yay_ucus")
	for i in 3:
		await _f(12)
		await _tap("saldiri2", 2)
	await _f(50)
	await _shot("yay_sapli")
	await _reset("akinci_yayi")
	_enemy(160.0)
	await _f(10)
	Input.action_press("saldiri2")
	Input.action_press("sag")
	await _f(28)
	await _shot("akinci_seri")
	Input.action_release("saldiri2")
	Input.action_release("sag")
	await _reset("tufan_yayi")
	_enemy(80.0)
	await _f(10)
	Input.action_press("saldiri2")
	await _f(int(float(Okculuk.prof({"id": "tufan_yayi"})["draw"]) * 60.0) + 2)
	await _shot("tufan_gerili")
	Input.action_release("saldiri2")
	await _f(3)
	await _shot("tufan_yelpaze")
	await _f(30)
	await _reset("od_oklari")
	await _tap("zipla", 4)
	await _f(14)
	Input.action_press("saldiri2")
	await _f(12)
	await _shot("od_havada")
	Input.action_release("saldiri2")
	await _f(4)
	await _shot("od_ucus")
	await _f(30)


func _goruntuler_v25() -> void:
	## v25: unsur başına ok izi (uzak hedefe yarım gerilmiş ok, uçarken), cephane imleri, cirit izi, Gök Asası
	for u in ["", "od", "ayaz", "yildirim", "kam", "yersu"]:
		await _reset("turk_yayi")
		var it: Dictionary = Game.run["slots"]["second"]
		Unsur.apply(it, u)
		pl.on_equip()
		_enemy(330.0)
		await _f(10)
		Input.action_press("saldiri2")
		await _f(14)
		Input.action_release("saldiri2")
		await _f(7)
		await _shot("iz_" + (u if u != "" else "sade"))
		await _f(30)
	# tam bırakış izi (altın)
	await _reset("turk_yayi")
	_enemy(330.0)
	await _f(10)
	Input.action_press("saldiri2")
	await _until(func() -> bool: return pl.okc.in_perfect(), 60)
	Input.action_release("saldiri2")
	await _f(6)
	await _shot("iz_altin")
	await _f(30)
	# Tufan yelpazesi (yıldırım unsurlu) + cephane imleri
	await _reset("tufan_yayi")
	Unsur.apply(Game.run["slots"]["second"], "yildirim")
	pl.on_equip()
	_enemy(260.0)
	await _f(10)
	for i in 2:
		await _tap("saldiri2", 2)
		await _f(36)
	Input.action_press("saldiri2")
	await _f(int(float(Okculuk.prof({"id": "tufan_yayi"})["draw"]) * 60.0) + 12)
	Input.action_release("saldiri2")
	await _f(6)
	await _shot("tufan_iz_cephane")
	await _f(40)
	# boş cephane: kuru tık
	pl.okc.ammo = 0
	await _tap("saldiri2", 2)
	await _f(8)
	await _shot("cephane_bos")
	await _f(30)
	# cirit izi
	await _reset("cirit")
	Unsur.apply(Game.run["slots"]["second"], "od")
	pl.on_equip()
	_enemy(240.0)
	await _f(10)
	await _tap("saldiri2", 2)
	await _f(12)
	await _shot("cirit_iz")
	await _f(40)
	# Gök Asası: zincir ve Gök Gürlemesi
	await _reset("gok_asasi")
	_enemy(110.0)
	_enemy(190.0)
	_enemy(260.0, "kara_boru", -30.0)
	await _f(10)
	await _tap("saldiri2", 2)
	await _f(3)
	await _shot("gok_asasi")
	for i in 3:
		await _f(60)
		await _tap("saldiri2", 2)
	await _f(3)
	await _shot("gok_gurlemesi")
	await _f(40)
