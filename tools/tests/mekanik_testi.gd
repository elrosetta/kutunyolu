extends Node
## v12 mekanik testi: godot --headless --path . --quit-after 6000 -- --mekanik [--derinlik=N]
## Üç Âlem (gök bulutu, ruh taşı, gizli oda, dönüş), Don (her arketip), Usul ızgarası, Ad Koyma töreni.

var main: Node


func _ready() -> void:
	process_mode = Node.PROCESS_MODE_ALWAYS
	_run.call_deferred()


func _wait(s: float) -> void:
	await get_tree().create_timer(s, true, true).timeout


func _p(s: String) -> void:
	print("[mekanik] ", s)


func _run() -> void:
	await _wait(0.5)
	var lv: Node = main.level
	var pl: Node = lv.player
	var al: Alem = lv.alem
	_p("odalar=%d bulut=%d kus=%d tas=%d" % [al.rooms.size(), al.clouds.size(), al.birds.size(), al.slabs.size()])
	# ---- gök
	pl.kam = 100.0
	pl._enter_realm("gok")
	await _wait(0.3)
	_p("gok: realm=%s maske_gok=%s maske_hayalet=%s" % [pl.realm, pl.get_collision_mask_value(5), pl.get_collision_mask_value(6)])
	if not al.clouds.is_empty():
		var c: Vector2 = al.clouds[0]["pos"]
		pl.global_position = c + Vector2(0, -30)
		pl.velocity = Vector2.ZERO
		await _wait(0.8)
		_p("bulut üstü: hedef_y=%.0f oyuncu_y=%.0f zemin=%s" % [c.y, pl.global_position.y, pl.is_on_floor()])
	pl._exit_realm(false, 0.016)
	await _wait(0.2)
	_p("dönüş: realm='%s'" % pl.realm)
	# ---- yeraltı + gizli oda
	if not al.rooms.is_empty():
		var r: Dictionary = al.rooms[0]
		var door: Rect2 = r["door"]
		pl.global_position = Vector2(door.get_center().x, door.position.y - 1)
		pl.velocity = Vector2.ZERO
		await _wait(0.6)
		_p("taş üstü (bu dünya): y=%.0f kapak_y=%.0f zemin=%s" % [pl.global_position.y, door.position.y, pl.is_on_floor()])
		pl.kam = 100.0
		pl._enter_realm("yer")
		await _wait(1.0)
		var rm: Rect2 = r["room"]
		_p("yeraltı: y=%.0f oda=[%.0f..%.0f] odada=%s" % [pl.global_position.y, rm.position.y, rm.end.y, rm.grow(4).has_point(pl.global_position)])
		var spirits := 0
		for e in get_tree().get_nodes_in_group("dusman"):
			if e.realm == "yer":
				spirits += 1
		_p("gölge ruh=%d" % spirits)
		pl._exit_realm(false, 0.016)
		await _wait(0.4)
		_p("oda çıkışı: realm='%s' y=%.0f (kapak üstü %.0f) zemin=%s" % [pl.realm, pl.global_position.y, door.position.y, pl.is_on_floor()])
	# ---- don: her arketip
	for k in ["kara_boru", "bekci", "tosbaga", "kurgan_atlisi", "dev_cocugu", "kaf_kartali", "kurgan_okcusu"]:
		if Data.enemy_def(k).is_empty():
			continue
		pl.inv_t = 99.0
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
		_p("don %s: arketip=%s aktif=%s kalan=%.1f" % [k, pl.don.arch, pl.don_on, pl.don.t])
		pl.don.t = 0.01
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
