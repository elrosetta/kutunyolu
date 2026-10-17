extends Node
## v20 unsur testi (Unsur.gd): her unsuru birkaç silah sınıfına takar, kukla düşmanlara vurur, tetiklenme sayılarını ve
## unsurun getirdiği ek hasarı yazar; pencereli çalıştırılırsa iz / tetiklenme / ağır silah tozu çekimleri alır.
##   godot --headless --path . -- --unsur [--unsur_silah=alp_kilici,dag_cekici] [--unsur_tur=12]
##   godot --path . -- --pencere=1920x1080 --unsur --anlik=C:/abs/klasor [--unsur_cekim=iz,toz,tetik]
## Çıktı: "[unsur] ..." satırları; sonunda "[unsur] OZET" ve "[unsur] HATA=n".

var main: Node
var lv: Node
var pl: Node
var spot := Vector2.ZERO
var weapons: Array = ["alp_kilici", "dag_cekici", "ikiz_bicak", "kargi", "kement", "teber"]
var rounds := 10
var shots: Array = ["iz", "tetik", "toz"]
var _snap_dir := ""
var _errors := 0
var _dummies: Array = []


func _ready() -> void:
	process_mode = Node.PROCESS_MODE_ALWAYS
	for arg in OS.get_cmdline_user_args():
		var a := String(arg)
		if a.begins_with("--unsur_silah="):
			weapons = Array(a.trim_prefix("--unsur_silah=").split(","))
		elif a.begins_with("--unsur_tur="):
			rounds = int(a.trim_prefix("--unsur_tur="))
		elif a.begins_with("--unsur_cekim="):
			shots = Array(a.trim_prefix("--unsur_cekim=").split(","))
		elif a.begins_with("--anlik="):
			_snap_dir = a.trim_prefix("--anlik=")
	if DisplayServer.get_name() == "headless":
		_snap_dir = ""
	_run.call_deferred()


func _p(s: String) -> void:
	print("[unsur] " + s)


func _f(n := 1) -> void:
	for i in n:
		await get_tree().physics_frame
		_tick()


func _wait(s: float) -> void:
	await _f(maxi(1, int(round(s * 60.0))))


func _tick() -> void:
	if pl == null:
		return
	Game.run["hp"] = float(Game.run["max_hp"])
	pl.inv_t = maxf(float(pl.inv_t), 0.2)
	for i in _dummies.size():
		var e = _dummies[i]
		if is_instance_valid(e) and not e.dead:
			e.global_position.x = spot.x + 30.0 + 22.0 * i
			e.velocity.x = 0.0
			e.cd = 99.0


func _snap(tag: String) -> void:
	if _snap_dir == "":
		return
	await RenderingServer.frame_post_draw
	var img := get_viewport().get_texture().get_image()
	if get_viewport().use_hdr_2d:
		if img.get_format() != Image.FORMAT_RGBA8 and img.get_format() != Image.FORMAT_RGB8:
			img.convert(Image.FORMAT_RGBA8)
		img.linear_to_srgb()
	var out := "%s/%s.png" % [_snap_dir, tag]
	img.save_png(out)
	_p("anlik %s" % out)


func _find_spot() -> Vector2:
	if "boss" in lv and lv.boss != null and is_instance_valid(lv.boss):
		lv.boss.remove_from_group("dusman")
		lv.boss.queue_free()
		lv.boss = null
		return Vector2(33 * Level.TS + 12, lv.surface_y(33) * Level.TS - 1)
	for x in range(20, Level.W - 30):
		var y0: int = lv.surface_y(x)
		var ok := true
		for dx in range(-8, 9):
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


func _clear() -> void:
	for e in get_tree().get_nodes_in_group("dusman"):
		e.remove_from_group("dusman")
		e.queue_free()
	_dummies.clear()


func _dummy(n: int, boss := false) -> void:
	for i in n:
		var e: Node = lv.spawn_enemy("kara_boru", spot + Vector2(30.0 + 22.0 * i, 0))
		e.max_hp = 1.0e7
		e.hp = 1.0e7
		e.dmg = 0.0
		e.cd = 99.0
		e.aggro = false
		e.facing = -1
		e.is_boss = boss
		e.speed = 0.0
		_dummies.append(e)


func _equip(w: String, u: String) -> Dictionary:
	var it: Dictionary = ItemGen.roll(w, 1, "demir", 1, "")
	Unsur.apply(it, u, 1.1)
	Game.run["slots"]["melee"] = it
	Game.run["slots"]["second"] = ItemGen.roll("turk_yayi", 1, "demir", 0)   # tek yakın silah: saldırı tuşu bu silahı kullanır
	pl.on_equip()
	pl.mel_slot = "melee"
	return it


func _reset_pl() -> void:
	Input.action_release("saldiri1")
	pl.global_position = spot
	pl.velocity = Vector2.ZERO
	pl.facing = 1
	pl.since_atk = 9.0
	pl.last_step = -1
	pl.combo_break("")


func _chain(presses := 3) -> void:
	for k in presses:
		pl.facing = 1
		Input.action_press("saldiri1")
		await _f(4)
		Input.action_release("saldiri1")
		await _wait(0.4)


func _dmg_total() -> float:
	var s := 0.0
	for e in _dummies:
		if is_instance_valid(e):
			s += 1.0e7 - float(e.hp)
	return s


func _run() -> void:
	await get_tree().create_timer(0.6).timeout
	main.hud.mode = "play"
	get_tree().paused = false
	lv = main.level
	pl = lv.player
	spot = _find_spot()
	_p("arena=%s biyom=%s" % [str(spot), String(lv.biome.get("id", "?"))])
	# ------------------------------------------------ 1) yuvarlama: dağılım ve adlar
	ItemGen.rng.seed = 2026
	var cnt := {}
	var named := 0
	for i in 600:
		var it: Dictionary = ItemGen.random_drop(2)
		var u := Unsur.of(it)
		cnt[u if u != "" else "sade"] = int(cnt.get(u if u != "" else "sade", 0)) + 1
		if u != "" and String(it["name"]).begins_with(String(Unsur.DEF[u]["sifat"])) == false and String(it["name"]).find(String(Unsur.DEF[u]["sifat"])) < 0:
			_errors += 1
		elif u != "":
			named += 1
	_p("yuvarlama 600 düşüş (kademe 2): %s; adlı=%d" % [str(cnt), named])
	var ex: Dictionary = ItemGen.roll("od_kamcisi", 3, "", 3)
	_p("örnek: %s | %s" % [ex["name"], " / ".join(ItemGen.describe(ex))])
	var plain: Dictionary = ItemGen.roll("alp_kilici", 0, "demir", 0)
	if Unsur.of(plain) != "":
		_errors += 1
		_p("HATA: açık malzemeli (başlangıç) eşyaya unsur geldi")
	# ------------------------------------------------ 2) dövüş: tetiklenme ve ek hasar
	var summary: Array = []
	for w in weapons:
		var base_dmg := -1.0
		for u in ["", "od", "ayaz", "yildirim", "kam", "yersu"]:
			_clear()
			_reset_pl()
			_equip(w, u)
			await _f(10)
			_dummy(3)
			await _f(6)
			Unsur.stats.clear()
			for r in rounds:
				await _chain(3)
				await _wait(0.35)
			await _wait(0.6)
			var tot := _dmg_total()
			var diag: Array = []
			for e in _dummies:
				diag.append("yok" if not is_instance_valid(e) else ("ölü" if e.dead else "%d@%d,%d" % [int(1.0e7 - float(e.hp)), int(e.global_position.x), int(e.global_position.y)]))
			_p("  kuklalar: %s oyuncu=%s" % [", ".join(diag), str(pl.global_position)])
			if u == "":
				base_dmg = tot
				_p("%s sade toplam=%d" % [w, int(tot)])
				continue
			var keys := Unsur.stats.keys()
			keys.sort()
			var parts: Array = []
			for k in keys:
				parts.append("%s=%s" % [k, ItemGen.fmt(float(Unsur.stats[k]))])
			# unsura bağlanan hasar: unsur vuruşları + ek çarpanlar (hasar_<u>) + süreğen hasar tahmini (yanma 6/sn,
			# zehir yükü başına ~2,8/sn x 4 sn). Toplamlar silah rastlantısıyla (usul, kritik) ±%20 oynar; oran daha güvenilir.
			var tier := float(Game.run.get("tier", 0))
			var dot := float(Unsur.stats.get("od_yanma_sn", 0.0)) * 6.0 * (1.0 + 0.6 * tier) + float(Unsur.stats.get("yersu_zehir", 0.0)) * 2.8 * 4.0 * (1.0 + 0.6 * tier) * 0.5
			var ek := float(Unsur.stats.get("hasar_" + u, 0.0)) + dot
			var gain := ek / maxf(1.0, tot - ek) * 100.0
			_p("%s %s toplam=%d unsur_payi=%+.0f%% (süreğen~%d) %s" % [w, u, int(tot), gain, int(dot), " ".join(parts)])
			summary.append([w, u, gain, float(Unsur.stats.get("isabet_" + u, 0.0))])
			if rounds > 0 and float(Unsur.stats.get("isabet_" + u, 0.0)) <= 0.0:
				_errors += 1
				_p("HATA: %s %s hiç isabet yok" % [w, u])
	# ------------------------------------------------ 3) boss azaltması (aynı silah, boss bayraklı kukla)
	for u in ["od", "yildirim", "yersu"]:
		var rates: Array = []
		for boss in [false, true]:
			_clear()
			_reset_pl()
			_equip("alp_kilici", u)
			await _f(8)
			_dummy(1, boss)
			await _f(4)
			Unsur.stats.clear()
			for r in 8:
				await _chain(3)
				await _wait(0.3)
			var ev := 0.0
			for k in Unsur.stats.keys():
				# yalnızca olasılıkla tetiklenen olaylar (süre / şifa / bitiriş gölü / sıçrama sayılmaz)
				if String(k) in ["od_tutusma", "ayaz_yuk", "yildirim_simsek", "kam_damga", "kam_yanki", "yersu_kok", "yersu_zehir"]:
					ev += float(Unsur.stats[k])
			rates.append(ev / maxf(1.0, float(Unsur.stats.get("isabet_" + u, 1.0))))
		_p("boss %s olay/isabet normal=%.2f boss=%.2f" % [u, rates[0], rates[1]])
		if lv.boss == null and float(rates[1]) > float(rates[0]) + 0.15:
			_p("UYARI: boss oranı normalden yüksek (%s)" % u)
	var g_sum := {}
	for s in summary:
		g_sum[s[1]] = float(g_sum.get(s[1], 0.0)) + float(s[2]) / float(weapons.size())
	_p("OZET ortalama ek hasar: %s" % str(g_sum))
	# ------------------------------------------------ 4) çekimler (pencereli)
	if _snap_dir != "":
		await _shots()
	_clear()
	_p("HATA=%d" % _errors)
	get_tree().quit()


func _shots() -> void:
	# iz: düşmansız, tetiklenme yok (yalnızca savuruş izi ve unsur zerreleri)
	if "iz" in shots:
		Unsur.force_p = 0.0
		var pairs := [["alp_kilici", ""], ["alp_kilici", "od"], ["alp_kilici", "ayaz"], ["alp_kilici", "yildirim"], ["alp_kilici", "kam"],
			["alp_kilici", "yersu"], ["dag_cekici", ""], ["dag_cekici", "od"], ["dag_cekici", "yildirim"], ["ikiz_bicak", ""],
			["ikiz_bicak", "ayaz"], ["kargi", ""], ["kargi", "kam"], ["kement", ""], ["kement", "yersu"], ["teber", ""], ["teber", "od"]]
		for pr in pairs:
			await _shoot(pr[0], pr[1], 0, "iz")
	# tetik: kuklalara vurulur, her vuruşta unsur tetiklenir (şimşek, donma / kırılma, tutuşma, töz, kök)
	if "tetik" in shots:
		Unsur.force_p = 1.0
		for pr in [["alp_kilici", "od"], ["alp_kilici", "ayaz"], ["alp_kilici", "yildirim"], ["alp_kilici", "kam"], ["alp_kilici", "yersu"], ["dag_cekici", "ayaz"]]:
			await _shoot(pr[0], pr[1], 2, "tetik")
	Unsur.force_p = -1.0
	# yer: beş unsurlu silah yerde (hale, zerreler, simge, ışık) + oyuncu ortadakinin yanında (eşya kartı)
	if "yer" in shots:
		_clear()
		_reset_pl()
		_equip("alp_kilici", "kam")
		await _f(10)
		var ws := ["kor_cekici", "ayaz_kilici", "yildirim_kilici", "ruh_kilici", "yilan_kilici"]
		var us := ["od", "ayaz", "yildirim", "kam", "yersu"]
		for i in 5:
			var it: Dictionary = ItemGen.roll(ws[i], 2, "", 2)
			Unsur.apply(it, us[i], 1.22)
			lv.drop_item(it, spot + Vector2(-70.0 + 42.0 * i, -14.0), true)
		pl.global_position = spot + Vector2(-8.0, 0)
		await _wait(1.6)
		await _snap("yer_unsurlar")
		await _wait(0.4)
		await _snap("yer_unsurlar_2")
	if "toz" in shots:
		for w in ["dag_cekici", "gurz", "kor_cekici", "ulu_kilic"]:
			_clear()
			_reset_pl()
			_equip(w, "")
			await _f(20)
			# basılı ağır saldırı (çakma)
			pl.facing = 1
			Input.action_press("saldiri1")
			await _wait(0.85)
			Input.action_release("saldiri1")
			# çakma bayrağı kurulur (vuruş başı), sonra baş yere değdiği karede düşer: toz o karede doğar
			var n := 0
			while n < 90 and not (not pl.atk.is_empty() and pl.atk.get("gslam", false)):
				await _f()
				n += 1
			while n < 150 and not pl.atk.is_empty() and pl.atk.get("gslam", false):
				await _f()
				n += 1
			_p("toz %s temas kare=%d" % [w, n])
			for d in [1, 6, 14, 26, 40]:
				await _f(1 if d == 1 else (d - [1, 6, 14, 26, 40][[1, 6, 14, 26, 40].find(d) - 1]))
				await _snap("toz_%s_%s_%02d" % [String(lv.biome.get("id", "")), w, d])
			await _wait(1.2)


func _shoot(w: String, u: String, n_dummy: int, kind: String) -> void:
	_clear()
	_reset_pl()
	_equip(w, u)
	await _f(12)
	if n_dummy > 0:
		_dummy(n_dummy)
	await _f(30)
	var tag := "%s_%s_%s" % [kind, u if u != "" else "sade", w]
	for k in 3:
		pl.facing = 1
		Input.action_press("saldiri1")
		await _f(4)
		Input.action_release("saldiri1")
		await _until_contact(40)
		await _f(3)
		await _snap("%s_%d_a" % [tag, k + 1])
		await _f(5)
		await _snap("%s_%d_b" % [tag, k + 1])
		await _wait(0.3)
	await _wait(0.4)


func _until_contact(max_f: int) -> void:
	for n in max_f:
		await _f()
		if not pl.atk.is_empty() and pl.atk.get("phase", "") == "act":
			return
