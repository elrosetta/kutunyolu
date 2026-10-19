extends Node
## v23 yapay zekâ denetimi (düz boss arenasında, tek tek):
##   godot --headless --path . --fixed-fps 60 --quit-after 400000 -- --zeka [--derinlik=3] [--zeka_tur=kara_boru,cor]
##   godot --headless --path . --fixed-fps 60 --quit-after 400000 -- --zeka --boss=tepegoz [--zeka_oldur]
## Yaratık başına iki sahne:
##   PASIF (20 sn): oyuncu hiç kıpırdamaz, yaratık 150 px ötede uyanık doğar. ilk = ilk saldırı hazırlığına (ya da
##     ilk hasara) kadar geçen süre; hamle = saldırı başlangıcı sayısı (10 sn'ye ölçekli); hasar = oyuncuya verilen
##     toplam hasar (30 sn'ye ölçekli, oyuncunun azami canı yüzdesi olarak da).
##   EZME (20 sn; 10 sn'ye ölçekli): oyuncu dibine girip 8 karede bir saldırır (bot gibi). hamle/10sn = yaratığın başlattığı saldırı;
##     kilit = yaratığın sarsılmış / sersem / kalkanı düşmüş / havaya fırlatılmış olduğu karelerin payı; hasar = oyuncuya.
## Bosslarda: PASIF 30 sn (hamle kullanımı, boşta kalma payı = hareketsiz chase/idle/recover + kilit), EZME 20 sn,
## --zeka_oldur ile ÖLDÜR (beklenen donanımlı basit dövüşçü; can sınırsız, alınan hasar azami can katı olarak).
## Çıktı: "[zeka] ..." satırları, sonda "[zeka] TABLO" ve "[zeka] BITTI".

var main: Node
var lv: Node
var pl: Player
var spot := Vector2.ZERO
var _boss_id := ""
var _rows: Array = []
var _last_log: Dictionary = {}

const KINDS := ["kara_boru", "sicrayan_tazi", "yek", "kirkayak", "ayaz_kurdu", "cor", "kara_kus_yavrusu", "kan_yarasasi",
	"agac_iyesi", "dev_cocugu", "tozkoparan", "su_iyesi", "balbal", "arcura", "kurgan_okcusu", "isilti_bocegi", "erlik_kizi",
	"surale", "karakoncolos", "kurgan_bekcisi", "al_atli", "tas_kertenkele", "tosbaga"]
const ACTS := ["saldiri1", "saldiri2", "zipla", "yuvarlan", "sag", "sol", "yukari", "asagi"]
const ATK_STATES := ["windup", "dive", "charge", "spin", "grab", "swoop"]


func _ready() -> void:
	process_mode = Node.PROCESS_MODE_ALWAYS
	# ölçüm mühürsüz (kayıtlı Kut Mührü seçimi sonuçları değiştirmesin); --zeka_muhur=N ile değiştirilir
	Zorluk.set_muhur(int(_arg("--zeka_muhur", "0")))
	for a in OS.get_cmdline_user_args():
		if String(a).begins_with("--boss="):
			_boss_id = String(a).trim_prefix("--boss=")
		elif String(a) == "--boss":
			_boss_id = "kara_boru_han"
	_run.call_deferred()


func _p(s: String) -> void:
	print("[zeka] ", s)


func _arg(k: String, def := "") -> String:
	for a in OS.get_cmdline_user_args():
		if String(a).begins_with(k + "="):
			return String(a).trim_prefix(k + "=")
	return def


func _release_all() -> void:
	for a in ACTS:
		Input.action_release(a)


func _fresh(bid: String) -> void:
	## düz boss arenası kur; bid boşsa boss kaldırılır
	main._build_boss(bid if bid != "" else "kara_boru_han")
	await get_tree().physics_frame
	await get_tree().physics_frame
	lv = main.level
	pl = lv.player
	if bid == "":
		if lv.boss != null and is_instance_valid(lv.boss):
			lv.boss.remove_from_group("dusman")
			lv.boss.queue_free()
			lv.boss = null
	spot = Vector2(30 * Level.TS + 12, lv.surface_y(30) * Level.TS - 1)
	Game.run["max_hp"] = 100000.0
	Game.run["hp"] = 100000.0
	pl.global_position = spot
	pl.velocity = Vector2.ZERO
	pl.facing = 1
	for i in 10:
		await get_tree().physics_frame


func _run() -> void:
	await get_tree().physics_frame
	await get_tree().physics_frame
	var cek := _arg("--zeka_cekim")
	if cek != "":
		DirAccess.make_dir_recursive_absolute(cek)
		if _boss_id != "":
			await _boss_cekim(_boss_id, cek)
		else:
			await _mob_cekim(cek)
		_p("BITTI")
		get_tree().quit()
		return
	if _boss_id != "":
		await _boss_suite(_boss_id)
	else:
		await _mob_suite()
	_p("BITTI")
	get_tree().quit()


# ================================================================== yaratıklar
func _mob_suite() -> void:
	var kinds: Array = KINDS
	var only := _arg("--zeka_tur")
	if only != "":
		kinds = only.split(",")
	_p("derinlik=%d" % int(Game.run.get("depth", 1)))
	for k in kinds:
		var a: Dictionary = await _mob_case(String(k), "pasif", 20.0)
		var b: Dictionary = await _mob_case(String(k), "ezme", 20.0)
		var row := "%-16s ai=%-12s | ilk=%5.2f sn hamle/10sn=%4.1f hasar/30sn=%4d | EZME hamle/10sn=%4.1f kilit=%3d%% hasar/10sn=%4d vuruş=%d çarpışma=%d karşı=%d" % [k, a["ai"],
			a["first"], a["atk"] * 10.0 / 20.0, int(a["dmg"] * 30.0 / 20.0), b["atk"] * 0.5, int(b["lock"] * 100.0), int(b["dmg"] * 0.5), int(b["hits"] * 0.5), b["clash"], b["counter"]]
		if OS.get_cmdline_user_args().has("--zeka_oldur"):
			# v26: gerçek canla öldürme (derinliğin beklenen donanımı, ezen oyuncu): süre, vuruş, alınan hasar
			var o: Dictionary = await _mob_case(String(k), "oldur", 45.0)
			row += " | OLDUR süre=%4.1f sn vuruş=%d can=%d alınan=%d (%.0f%% can) kritik=%d/%d öldü=%s" % [o["kill_t"], o["hits"], int(o["ehp0"]), int(o["dmg"]), 100.0 * o["dmg"] / maxf(1.0, o["ref_hp"]), o["krit"], o["isabet"], str(o["killed"])]
		_p(row)
		_rows.append(row)
	_p("TABLO")
	for r in _rows:
		_p("  " + r)


func _mob_case(kind: String, mode: String, dur: float) -> Dictionary:
	var ref_hp := 100.0
	if mode == "oldur":
		ref_hp = _loadout_for(Zorluk.derinlik())
	await _fresh("")
	if mode == "oldur":
		pl.on_equip()
	_release_all()
	var e: Enemy = lv.spawn_enemy(kind, spot + Vector2(150.0, 0.0))
	e.aggro = true
	e.cd = 0.6
	if mode == "ezme":
		e.max_hp = 1.0e7
		e.hp = 1.0e7
	await get_tree().physics_frame
	var t := 0.0
	var first := -1.0
	var atk := 0
	var lock_t := 0.0
	var dmg := 0.0
	var hits := 0
	var prev_state := String(e.state)
	var hp_prev := float(Game.run["hp"])
	var ehp := e.hp
	var f := 0
	var c0 := int(pl.v19_stats.get("carpisma", 0))
	var k0 := int(pl.v19_stats.get("karsi", 0))
	var killed := false
	var ehp0 := e.max_hp
	var ks0: Dictionary = Player.krit_say.duplicate()
	while t < dur:
		if mode == "oldur" and (not is_instance_valid(e) or e.dead):
			killed = true
			break
		if not is_instance_valid(e) or e.dead:
			# kamikaze vb. kendini yok etti: yeniden doğur (sayım sürer)
			e = lv.spawn_enemy(kind, spot + Vector2(150.0, 0.0))
			e.aggro = true
			if mode == "ezme":
				e.max_hp = 1.0e7
				e.hp = 1.0e7
			ehp = e.hp
			prev_state = String(e.state)
		_release_all()
		if mode in ["ezme", "oldur"] and not pl.dead:
			var dx: float = e.global_position.x - pl.global_position.x
			if pl.atk.is_empty() and pl.roll_t <= 0.0 and absf(dx) > 2.0:
				pl.facing = int(signf(dx))
			if absf(dx) > 40.0:
				Input.action_press("sag" if dx > 0.0 else "sol")
			if f % 8 == 0:
				Input.action_press("saldiri1")
		await get_tree().physics_frame
		f += 1
		var dt := get_physics_process_delta_time() * Engine.time_scale
		t += dt
		if not is_instance_valid(e):
			continue
		var s := String(e.state)
		if OS.get_cmdline_user_args().has("--zeka_iz") and s != prev_state:
			print("[iz] t=%.2f %s -> %s mv=%s dx=%.0f sa=%.2f hurt=%.2f stun=%.2f pl_inv=%.2f pl_roll=%.2f pl_atk=%s" % [t, prev_state, s, str(e.get_meta("move", "")), e.global_position.x - pl.global_position.x, e.sa_t, e.hurt_t, e.stun_t, pl.inv_t, pl.roll_t, str(pl.atk.get("phase", "-"))])
		if s != prev_state and s in ATK_STATES and not (prev_state in ATK_STATES):
			atk += 1
			if first < 0.0:
				first = t
		prev_state = s
		if e.hurt_t > 0.0 or e.stun_t > 0.0 or e.state == "stagger" or e.launch_t > 0.0 or e.freeze_t > 0.0:
			lock_t += dt
		var hp_now := float(Game.run["hp"])
		if OS.get_cmdline_user_args().has("--zeka_iz") and (hp_now != hp_prev or pl.inv_t > 0.75):
			print("[iz] hp %.1f -> %.1f inv=%.2f" % [hp_prev, hp_now, pl.inv_t])
		if hp_now < hp_prev:
			dmg += hp_prev - hp_now
			if first < 0.0:
				first = t
		Game.run["hp"] = 100000.0
		hp_prev = 100000.0
		if e.hp < ehp:
			hits += 1
		ehp = e.hp
	_release_all()
	var ai_name := String(e.ai) if is_instance_valid(e) else "?"
	for o in get_tree().get_nodes_in_group("dusman"):
		o.remove_from_group("dusman")
		o.queue_free()
	return {"ai": ai_name, "first": first if first >= 0.0 else 99.0, "atk": float(atk), "lock": lock_t / maxf(0.01, dur), "dmg": dmg, "hits": hits,
		"clash": int(pl.v19_stats.get("carpisma", 0)) - c0, "counter": int(pl.v19_stats.get("karsi", 0)) - k0,
		"killed": killed, "kill_t": t, "ref_hp": ref_hp, "ehp0": ehp0,
		"krit": int(Player.krit_say["sans"]) + int(Player.krit_say["kosul"]) + int(Player.krit_say["kesin"]) - int(ks0["sans"]) - int(ks0["kosul"]) - int(ks0["kesin"]),
		"isabet": int(Player.krit_say["isabet"]) - int(ks0["isabet"])}


# ================================================================== bosslar
func _boss_suite(bid: String) -> void:
	var a: Dictionary = await _boss_case(bid, "pasif", 30.0)
	var b: Dictionary = await _boss_case(bid, "ezme", 20.0)
	_p("BOSS %s PASIF 30sn: ilk=%.2f sn hamle=%d (10 sn'de %.1f) boşta=%d%% hasar=%d (oyuncu can %d'nin %.1f katı) hamleler=%s" % [bid,
		a["first"], a["atk"], a["atk"] / 3.0, int(a["idle"] * 100.0), int(a["dmg"]), int(a["ref_hp"]), a["dmg"] / maxf(1.0, a["ref_hp"]), str(a["moves"])])
	_p("BOSS %s EZME 20sn: hamle=%d kilit=%d%% boşta=%d%% hasar=%d hamleler=%s" % [bid, b["atk"], int(b["lock"] * 100.0), int(b["idle"] * 100.0), int(b["dmg"]), str(b["moves"])])
	if OS.get_cmdline_user_args().has("--zeka_oldur"):
		for m in ["oldur", "iyi"]:
			var c: Dictionary = await _boss_case(bid, m, 300.0)
			_p("BOSS %s %s: süre=%.1f sn öldü=%s evre=%d alınan hasar=%d (azami canın %.1f katı) kilit=%d%% boşta=%d%% erişim=%d%% sendele=%d açık=%d hamleler=%s hasar_kaynağı=%s" % [bid,
				"OLDUR (ezen bot)" if m == "oldur" else "IYI (kaçan bot)", c["t"], str(c["killed"]), c["phase"], int(c["dmg"]), c["dmg"] / maxf(1.0, c["ref_hp"]),
				int(c["lock"] * 100.0), int(c["idle"] * 100.0), int(c["reach"] * 100.0), c["stag"], c["vuln"], str(c["log"]), str(c["by_move"])])


func _loadout_for(d: int) -> float:
	## Main._bot_loadout ile aynı varsayım: o kademenin Nadir Alp Kılıcı + derinlik başına ~2,5 tılsım
	var s := 2.5 * float(d - 1)
	var o := {"kurt": int(round(s * 0.6)), "ayi": int(round(s * 0.25)), "kartal": int(round(s * 0.15))}
	Game.run["ongun"] = o
	var hp := 100.0
	for i in int(o["kurt"]) + int(o["kartal"]):
		hp *= 1.06
	for i in int(o["ayi"]):
		hp *= 1.15
	Game.run["tier"] = maxi(0, d - 1)
	Game.run["slots"]["melee"] = ItemGen.roll("alp_kilici", maxi(0, d - 1), "demir", 1, "")
	return hp


func _boss_case(bid: String, mode: String, dur: float) -> Dictionary:
	var d := Zorluk.boss_derinlik(bid)
	var ref_hp := _loadout_for(d)
	await _fresh(bid)
	pl.on_equip()
	_release_all()
	var b: Enemy = lv.boss
	var t := 0.0
	var first := -1.0
	var atk := 0
	var lock_t := 0.0
	var idle_t := 0.0
	var dmg := 0.0
	var moves: Dictionary = {}
	var prev_state := String(b.state)
	var hp_prev := float(Game.run["hp"])
	var f := 0
	var killed := false
	var roll_seen: Dictionary = {}
	var reach_t := 0.0
	var by_move: Dictionary = {}
	var stag := 0
	var vul := 0
	while t < dur:
		if b == null or not is_instance_valid(b) or b.dead:
			killed = true
			break
		_release_all()
		if mode != "pasif" and not pl.dead:
			var dx: float = b.global_position.x - pl.global_position.x
			var gap: float = absf(dx) - b.size.x * 0.5
			if pl.atk.is_empty() and pl.roll_t <= 0.0 and absf(dx) > 2.0:
				pl.facing = int(signf(dx))
			if mode == "oldur":
				# basit dövüşçü: hazırlıkta yarı yarıya yuvarlanır (her hazırlıkta bir kez karar), yaklaşır, vurur
				var key: int = int(b.get_meta("v23_wid", 0))
				if b.state == "windup" and not roll_seen.has(key) and gap < 160.0:
					roll_seen[key] = true
					if randf() < 0.5:
						Input.action_press("yuvarlan")
				if gap > 26.0:
					Input.action_press("sag" if dx > 0.0 else "sol")
				if f % 97 == 0:
					Input.action_press("zipla")
			elif mode == "iyi":
				# iyi oyuncu: hazırlığın sonunda (son 0,2 sn) uzağa yuvarlanır, tehlikede saldırmaz, geri çekilir,
				# yer dalgasının / alçak tehlikenin üstünden zıplar, açıkta (toparlanma / sendeleme) vurur
				var key2: int = int(b.get_meta("v23_wid", 0))
				var away := "sol" if dx > 0.0 else "sag"
				var danger: bool = b.state == "windup" or (b.state in ["dash", "air"] and gap < 200.0)
				if b.state == "windup" and float(b.st) < 0.2 and not roll_seen.has(key2) and gap < 260.0:
					roll_seen[key2] = true
					if randf() < 0.85:
						Input.action_press(away)
						Input.action_press("yuvarlan")
				elif danger and gap < 140.0:
					Input.action_press(away)
				elif gap > 26.0:
					Input.action_press("sag" if dx > 0.0 else "sol")
				for pr in lv.proj_root.get_children():
					if pr is Projectile and pr.team == "e" and absf(pr.global_position.x - pl.global_position.x) < 70.0 							and absf(pr.global_position.y - pl.center().y) < 40.0 and signf(pr.velocity.x) == signf(pl.global_position.x - pr.global_position.x):
						Input.action_press("zipla")
						break
				if not danger and f % 8 == 0 and gap < 70.0:
					Input.action_press("saldiri1")
			else:
				if gap > 26.0:
					Input.action_press("sag" if dx > 0.0 else "sol")
			if mode != "iyi" and f % 8 == 0 and gap < 70.0:
				Input.action_press("saldiri1")
		await get_tree().physics_frame
		f += 1
		var dt := get_physics_process_delta_time() * Engine.time_scale
		t += dt
		if b == null or not is_instance_valid(b) or b.dead:
			killed = true
			break
		_last_log = b.get("move_log") if "move_log" in b else {}
		var s := String(b.state)
		if s != prev_state and s == "windup":
			atk += 1
			b.set_meta("v23_wid", atk)
			var mv := String(b.get("next_move")) if "next_move" in b else "?"
			moves[mv] = int(moves.get(mv, 0)) + 1
			if first < 0.0:
				first = t
		if s != prev_state and s == "sendele":
			stag += 1
		if s != prev_state and s == "vuln":
			vul += 1
		prev_state = s
		if pl and absf(b.global_position.x - pl.global_position.x) - b.size.x * 0.5 < 60.0 and absf(b.center().y - pl.center().y) < b.size.y * 0.5 + 30.0 and not ("untouch" in b and b.untouch):
			reach_t += dt
		var locked: bool = b.hurt_t > 0.0 or b.stun_t > 0.0 or b.freeze_t > 0.0 or b.root_t > 0.0
		if locked:
			lock_t += dt
		if locked or (s in ["idle", "chase", "recover"] and absf(b.velocity.x) < 15.0):
			idle_t += dt
		var hp_now := float(Game.run["hp"])
		if hp_now < hp_prev:
			dmg += hp_prev - hp_now
			var mk := String(b.get("next_move")) if "next_move" in b else "?"
			by_move[mk] = int(by_move.get(mk, 0)) + int(hp_prev - hp_now)
			if first < 0.0:
				first = t
		Game.run["hp"] = 100000.0
		hp_prev = 100000.0
	_release_all()
	var ph := int(b.get("phase")) if (b != null and is_instance_valid(b)) else 3
	for o in get_tree().get_nodes_in_group("dusman"):
		o.remove_from_group("dusman")
		o.queue_free()
	return {"first": first if first >= 0.0 else 99.0, "atk": atk, "lock": lock_t / maxf(0.01, t), "idle": idle_t / maxf(0.01, t),
		"dmg": dmg, "moves": moves, "t": t, "killed": killed, "phase": ph, "ref_hp": ref_hp, "reach": reach_t / maxf(0.01, t), "by_move": by_move, "stag": stag, "vuln": vul,
		"log": (b.get("move_log") if (b != null and is_instance_valid(b)) else _last_log)}


# ================================================================== çekim (headless değil): -- --zeka --zeka_cekim=C:/mutlak/klasor [--boss=..]
## Her hamleyi sırayla zorlar; uyarı anında, vuruş anında ve sonrasında 1920x1080 kare kaydeder.
const CEKIM := {
	"kara_boru_han": [["pounce", 1], ["rush", 1], ["flurry", 1], ["howl", 1], ["wall_dive", 2], ["crystals", 2], ["shadows", 3]],
	"tepegoz": [["slam", 1], ["boulder", 1], ["stomp", 1], ["grab", 1], ["beam", 2], ["charge", 2], ["quake", 3]],
	"sahmeran": [["spit", 1], ["tail", 1], ["lunge", 1], ["snakes", 2], ["drip", 2], ["gaze", 3], ["venom", 3]],
	"yelbegen": [["club", 1], ["gust", 1], ["heads", 1], ["breath", 2], ["icicles", 2], ["blizzard", 3], ["leap_ice", 3]],
	"erlik_han": [["chain", 1], ["firewave", 1], ["fireballs", 1], ["scythe", 1], ["pillars", 2], ["walls", 2], ["tamu_seli", 3]]}


func _snap(path: String) -> void:
	await RenderingServer.frame_post_draw
	var img := get_viewport().get_texture().get_image()
	if img:
		img.save_png(path)
		_p("kare: " + path)


func _frames(n: int) -> void:
	for i in n:
		await get_tree().physics_frame


func _boss_cekim(bid: String, dir: String) -> void:
	await _fresh(bid)
	var b = lv.boss
	await _frames(110)
	for mp in CEKIM.get(bid, []):
		var mv := String(mp[0])
		var ph := int(mp[1])
		if b == null or not is_instance_valid(b):
			break
		b.phase = ph
		b.hp = b.max_hp * [0.95, 0.55, 0.22][ph - 1]
		var w := 0
		while String(b.state) != "chase" and w < 400:
			await _frames(1)
			w += 1
		# oyuncuyu hamleye uygun mesafeye koy
		var rg: Vector2 = b.call("_range_of", mv)
		var want := clampf((rg.x + rg.y) * 0.5, 90.0, 300.0)
		pl.global_position = Vector2(b.global_position.x - b.facing * want, pl.global_position.y)
		if pl.global_position.x < 6 * Level.TS or pl.global_position.x > 80 * Level.TS:
			pl.global_position.x = b.global_position.x + b.facing * want
		pl.facing = int(signf(b.global_position.x - pl.global_position.x))
		await _frames(2)
		b._face(pl.center() - b.center())
		b.call("_start", mv)
		await _frames(8)
		await _snap(dir.path_join("%s_%s_1uyari.png" % [bid, mv]))
		w = 0
		while String(b.state) == "windup" and w < 200:
			await _frames(1)
			w += 1
		await _frames(5)
		await _snap(dir.path_join("%s_%s_2vurus.png" % [bid, mv]))
		await _frames(22)
		await _snap(dir.path_join("%s_%s_3sonra.png" % [bid, mv]))
		w = 0
		while not (String(b.state) in ["chase", "recover"]) and w < 600:
			await _frames(1)
			w += 1
			if w % 45 == 0:
				await _snap(dir.path_join("%s_%s_4_%d.png" % [bid, mv, w]))
		Game.run["hp"] = 100000.0
		for o in get_tree().get_nodes_in_group("dusman"):
			if o != b:
				o.remove_from_group("dusman")
				o.queue_free()
		await _frames(30)


const MOB_CEKIM := ["kara_boru", "agac_iyesi", "su_iyesi", "tozkoparan", "isilti_bocegi", "erlik_kizi", "kurgan_bekcisi", "kara_kus_yavrusu"]


func _mob_cekim(dir: String) -> void:
	for k in MOB_CEKIM:
		await _fresh("")
		var e: Enemy = lv.spawn_enemy(k, spot + Vector2(130.0, 0.0))
		e.aggro = true
		e.cd = 0.4
		var shots := 0
		var prev := ""
		var t := 0
		while shots < 3 and t < 900:
			await _frames(1)
			t += 1
			Game.run["hp"] = 100000.0
			if not is_instance_valid(e):
				break
			var s := String(e.state)
			if s != prev and s == "windup":
				await _frames(6)
				await _snap(dir.path_join("mob_%s_%d_uyari.png" % [k, shots]))
				var w := 0
				while is_instance_valid(e) and String(e.state) == "windup" and w < 120:
					await _frames(1)
					w += 1
				await _frames(6)
				await _snap(dir.path_join("mob_%s_%d_vurus.png" % [k, shots]))
				shots += 1
			prev = s if is_instance_valid(e) else ""
		# bir de ezme: tepki (geri sıçrama / zırhlı intikam)
		if is_instance_valid(e):
			e.max_hp = 1.0e6
			e.hp = 1.0e6
			for i in 120:
				_release_all()
				var dx: float = e.global_position.x - pl.global_position.x
				pl.facing = int(signf(dx)) if absf(dx) > 2.0 else pl.facing
				if absf(dx) > 40.0:
					Input.action_press("sag" if dx > 0.0 else "sol")
				if i % 8 == 0:
					Input.action_press("saldiri1")
				await _frames(1)
				if i == 70:
					await _snap(dir.path_join("mob_%s_tepki.png" % k))
			_release_all()
		for o in get_tree().get_nodes_in_group("dusman"):
			o.remove_from_group("dusman")
			o.queue_free()
