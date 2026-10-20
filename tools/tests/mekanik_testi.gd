extends Node
## v12 mekanik testi: godot --headless --path . --quit-after 6000 -- --mekanik [--derinlik=N]
## v34: -- --mekanik --zipla --boss: zıplama / tutunma / Kahraman İnişi ölçümü (tools/tests/zipla_testi.gd)
## v25 tehlike çukuru (tek vuruş + sektirme / güvenli zemine dönüş), Don (her arketip), Usul ızgarası, Ad Koyma töreni.

var main: Node


func _ready() -> void:
	process_mode = Node.PROCESS_MODE_ALWAYS
	_run.call_deferred()


func _wait(s: float) -> void:
	await get_tree().create_timer(s, true, true).timeout


func _p(s: String) -> void:
	print("[mekanik] ", s)


func _pit(lv: Node) -> Vector2i:
	## İlk tehlike çukuru (diken / zehir / lav; buz değil): üst satırı, sol dudağı katı zemin
	if lv.haz_kind == "buz":
		return Vector2i(-1, -1)
	for x in range(20, lv.W - 20):
		for y in range(4, lv.H - 2):
			if lv.cell(x, y) == 3 and lv.cell(x, y - 1) != 3 and lv.cell(x - 1, y) != 3:
				return Vector2i(x, y)
	return Vector2i(-1, -1)


func _tuzak(lv: Node, pl: Node) -> void:
	## v25 tehlike çukuru: ilk temasta TEK vuruş + yukarı / geldiği yana sektirme, içinde sürekli hasar yok;
	## 1,6 sn içinde yeniden düşen hasarsız son güvenli zemine döner; yaratık da bir kez vurulup kenara sektirilir.
	var c := _pit(lv)
	if c.x < 0:
		_p("tuzak: bu bölümde tehlike çukuru yok (%s)" % lv.haz_kind)
		return
	var TS: int = lv.TS
	for e in get_tree().get_nodes_in_group("dusman"):
		if is_instance_valid(e) and e.global_position.distance_to(Vector2(c.x * TS, c.y * TS)) < 700.0:
			e.remove_from_group("dusman")
			e.queue_free()
	# önce çukurun solundaki güvenli zeminde dur
	var lx: int = c.x - 3
	pl.global_position = Vector2(lx * TS + 12, lv.surface_y(lx) * TS - 1)
	pl.velocity = Vector2.ZERO
	pl.inv_t = 0.0
	Game.run["hp"] = float(Game.run["max_hp"])
	await _wait(0.4)
	var safe0: Vector2 = pl._haz_safe
	var hp0 := float(Game.run["hp"])
	pl.global_position = Vector2(c.x * TS + 12, (c.y + 1) * TS - 1)
	pl.velocity = Vector2.ZERO
	await _wait(0.06)
	var hp1 := float(Game.run["hp"])
	_p("tuzak %s ilk temas: hasar=%.0f (azami canın %%%.0f) sektirme vy=%.0f vx=%.0f güvenli=%s" % [lv.haz_kind, hp0 - hp1, 100.0 * (hp0 - hp1) / float(Game.run["max_hp"]), pl.velocity.y, pl.velocity.x, str(safe0.round())])
	await _wait(1.1)
	var hp2 := float(Game.run["hp"])
	var in_haz: bool = lv.hazard_at(pl.global_position + Vector2(0, 2)) != "" or lv.hazard_at(pl.global_position + Vector2(0, -4)) != ""
	_p("tuzak 1,1 sn sonra: ek hasar=%.0f (0 olmalı) zemin=%s çukurda=%s x=%d" % [hp1 - hp2, str(pl.is_on_floor()), str(in_haz), int(pl.global_position.x / TS)])
	# ikinci düşüş (1,6 sn içinde): hasarsız güvenli zemine
	pl.inv_t = 0.0
	pl._haz_t = 0.0
	pl._haz_last = Game.clock()
	pl.global_position = Vector2(c.x * TS + 12, (c.y + 1) * TS - 1)
	pl.velocity = Vector2.ZERO
	await _wait(0.06)
	var hp3 := float(Game.run["hp"])
	_p("tuzak ikinci düşüş: hasar=%.0f (0 olmalı) güvenli_zemine=%s" % [hp2 - hp3, str(pl.global_position.distance_to(pl._haz_safe) < 6.0)])
	# yaratık çukura itilirse
	await _wait(1.0)
	var e2: Enemy = lv.spawn_enemy("kara_boru" if Data.enemy_def("kara_boru").size() > 0 else "cor", Vector2(c.x * TS + 12, (c.y + 1) * TS - 1))
	e2.cd = 99.0
	await _wait(0.05)
	var ehp0: float = e2.max_hp
	await _wait(1.4)
	if is_instance_valid(e2) and not e2.dead:
		var ein: bool = lv.hazard_at(e2.global_position + Vector2(0, 2)) != "" or lv.hazard_at(e2.global_position + Vector2(0, -4)) != ""
		_p("tuzak yaratık: hasar=%.0f (azami canın %%%.0f, tek vuruş) çukurda=%s" % [ehp0 - e2.hp, 100.0 * (ehp0 - e2.hp) / ehp0, str(ein)])
		e2.remove_from_group("dusman")
		e2.queue_free()
	else:
		_p("tuzak yaratık: çukurda öldü")


func _run() -> void:
	if OS.get_cmdline_user_args().has("--zipla"):
		# v34: zıplama / tutunma / Kahraman İnişi ölçümü (tools/tests/zipla_testi.gd; --boss arenası)
		var zt: Node = load("res://tools/tests/zipla_testi.gd").new()
		zt.set("main", main)
		add_child(zt)
		return
	await _wait(0.5)
	var lv: Node = main.level
	var pl: Node = lv.player
	# ---- v25: Üç Âlem kaldırıldı (T eylemi yok, gök / hayalet çarpışma katmanı yok); tehlike çukuru sektirmesi
	_p("v25 alem_yok: eylem=%s maske=%d" % [str(InputMap.has_action("alem")), pl.collision_mask])
	await _tuzak(lv, pl)
	# ---- don: her arketip
	for k in ["kara_boru", "bekci", "tosbaga", "kurgan_atlisi", "dev_cocugu", "kaf_kartali", "kurgan_okcusu"]:
		if Data.enemy_def(k).is_empty():
			continue
		pl.inv_t = 99.0
		# v22: düşmanlar daha sert; yakalanma / tehlike karosu (dokunulmazlığı aşar) testi öldürüp yeniden başlatmasın
		for e in get_tree().get_nodes_in_group("dusman"):
			if e.global_position.distance_to(pl.global_position) < 400.0:
				e.cd = 99.0
		Game.run["hp"] = float(Game.run["max_hp"])
		pl.gain_don(k)
		pl._begin_don()
		await _wait(0.2)
		Input.action_press("saldiri1")
		await _wait(0.05)
		Input.action_release("saldiri1")
		await _wait(0.6)
		Input.action_press("saldiri2")
		await _wait(0.05)
		Input.action_release("saldiri2")
		await _wait(0.6)
		if is_instance_valid(pl.don):
			_p("don %s: arketip=%s aktif=%s kalan=%.1f" % [k, pl.don.arch, pl.don_on, pl.don.t])
			pl.don.t = 0.01
		else:
			# v23 yapay zekâ: düşman cd yok sayıp vurursa don erken biter (test hatası değil, form zaten kapandı)
			_p("don %s: erken bitti (aktif=%s)" % [k, pl.don_on])
		await _wait(0.1)
	_p("don bitti: aktif=%s gövde_görünür=%s" % [pl.don_on, pl.anim.visible])
	# ---- usul
	var hits := 0
	for i in 40:
		var u := Ses.usul_now()
		if i == 0:
			_p("usul: %s" % str(u))
		if not u.is_empty() and absf(float(u["d"])) < 0.085:
			hits += 1
		await _wait(0.05)
	_p("usul penceresine düşen örnek=%d/40" % hits)
	# ---- ad koyma
	Adlar.deed("basat", pl.center())
	Adlar.deed("segrek", pl.center())
	_p("bekleyen=%s" % str(Adlar.pending()))
	main._ad_toreni()
	_p("tören: mod=%s ad=%s kazanıldı=%s" % [main.hud.mode, main.hud.ad_id, Adlar.earned("basat")])
	await _wait(1.5)
	main._ad_toreni()
	_p("ikinci tören: ad=%s bekleyen=%s başlık=%s" % [main.hud.ad_id, str(Adlar.pending()), Adlar.title()])
	main._start_play()
	_p("BITTI")
