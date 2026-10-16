extends Node
## Mürekkep fırçası laboratuvarı (stil v2 savuruş izi ve vuruş efektleri çekimi):
##   godot --path . --write-movie C:/x/f.png --fixed-fps 30 --quit-after 900 -- --stil=v2 --firca[=silah1,silah2:malzeme,...]
##   [--firca_bos] (düşmansız: yalnız iz) [--firca_adim=zincir,agir,ozel] (sıra)
## Her silahta: 3 vuruşluk zincir (son vuruş bitiriş), basılı tutulan ağır saldırı, savuşturma + kusursuz kaçış süsü.
## Çıktıda "[firca] silah adım kare=N" satırları kareleri bulmak için.

var main: Node
var weapons: Array = ["alp_kilici", "dag_cekici", "kargi", "ikiz_bicak", "kement", "erlik_tirpani", "ayaz_kilici", "od_kamcisi"]
var with_enemy := true


func _ready() -> void:
	process_mode = Node.PROCESS_MODE_ALWAYS
	for arg in OS.get_cmdline_user_args():
		var a := String(arg)
		if a.begins_with("--firca="):
			weapons = Array(a.trim_prefix("--firca=").split(","))
		elif a == "--firca_bos":
			with_enemy = false
	_run.call_deferred()


func _wait(s: float) -> void:
	await get_tree().create_timer(s, true, false, false).timeout


func _p(s: String) -> void:
	var sp := Vector2.ZERO
	if main and main.level and main.level.player:
		var pl: Node2D = main.level.player
		var vp := pl.get_viewport()
		sp = pl.get_global_transform_with_canvas().origin * (Vector2(vp.get_window().size) / vp.get_visible_rect().size)
	print("[firca] %s kare=%d ekran=%d,%d" % [s, Engine.get_frames_drawn(), int(sp.x), int(sp.y)])


func _clear_enemies() -> void:
	for e in get_tree().get_nodes_in_group("dusman"):
		e.queue_free()


func _spawn(pl: Node, dx: float) -> void:
	var en: Node = main.level.spawn_enemy("kara_boru", pl.global_position + Vector2(dx, 0), false)
	if en:
		en.set_physics_process(false)
		en.facing = -1
		en.anim.set_facing(-1)
		if "hp" in en:
			en.hp = 1.0e6
		if "max_hp" in en:
			en.max_hp = 1.0e6


func _run() -> void:
	await _wait(1.2)
	var pl: Node = main.level.player
	var x0: float = pl.global_position.x
	for w in weapons:
		var parts := String(w).split(":")
		var id := parts[0]
		var mat := parts[1] if parts.size() > 1 else "demir"
		_clear_enemies()
		pl.global_position.x = x0
		pl.velocity = Vector2.ZERO
		pl.facing = 1
		Game.run["slots"]["melee"] = ItemGen.roll(id, 1, mat, 0)
		pl.on_equip()
		await _wait(0.25)
		if with_enemy:
			_spawn(pl, 36.0)
		await _wait(0.2)
		for k in 3:
			pl.facing = 1
			_p("%s zincir%d" % [id, k + 1])
			Input.action_press("saldiri1")
			await _wait(0.06)
			Input.action_release("saldiri1")
			await _wait(0.42)
		await _wait(0.5)
		pl.facing = 1
		_p("%s agir" % id)
		Input.action_press("saldiri1")
		await _wait(0.85)
		Input.action_release("saldiri1")
		_p("%s agir_birak" % id)
		await _wait(1.0)
	_clear_enemies()
	_p("savustur")
	if pl.has_method("_parry"):
		pl._parry({}, null, null)
	await _wait(0.8)
	_p("kusursuz")
	if pl.has_method("_perfect_dodge"):
		pl._perfect_dodge(null)
	await _wait(1.2)
	_p("bitti")
