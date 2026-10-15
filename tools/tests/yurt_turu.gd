extends Node
## Yurt turu: godot --path . --quit-after 900 -- --yurt --yurt-tur
## Bengü'yü girişten sağa yürütür; her NPC'nin yanında kısa durur ("E" balonu görünür mü), Kut Kapısı'na
## varınca çıkar. Hareketin hiçbir süs tarafından kesilmediğini doğrular; --write-movie ile kamera kaydı alınır.

var level: Node
var _t := 0.0
var _stop_t := 0.0
var _seen := {}
var _last_x := 0.0
var _stuck := 0.0


func _ready() -> void:
	process_mode = Node.PROCESS_MODE_ALWAYS
	print("[yurt] tur başladı")


func _unpause() -> void:
	# Main başlık ekranını yurt kurulduktan sonra açar: ilk karelerde oyuna geç
	var m := level.get_parent()
	if m and m.get("hud"):
		m.hud.mode = "play"
	get_tree().paused = false


func _process(delta: float) -> void:
	_t += delta
	var pl: Node2D = level.player
	if _t < 0.6:
		_unpause()
		return
	if pl == null:
		return
	for n in level.npcs:
		if n.near and not _seen.has(n.id):
			_seen[n.id] = true
			_stop_t = 1.6
			print("[yurt] %s yanında (x=%.0f)" % [n.id, pl.global_position.x])
	if level._done:
		Input.action_release("sag")
		print("[yurt] Kut Kapısı'na varıldı t=%.1f görülen=%s" % [_t, str(_seen.keys())])
		get_tree().quit()
		set_process(false)
		return
	if _stop_t > 0.0:
		_stop_t -= delta
		Input.action_release("sag")
		return
	Input.action_press("sag")
	if absf(pl.global_position.x - _last_x) < 0.5:
		_stuck += delta
		# basamak: kısa bir zıplama (oyuncunun yapacağı gibi)
		if _stuck > 0.2 and _stuck < 0.3:
			Input.action_press("zipla")
		else:
			Input.action_release("zipla")
		if _stuck > 2.5:
			print("[yurt] HATA: takıldı x=%.0f y=%.0f" % [pl.global_position.x, pl.global_position.y])
			get_tree().quit()
	else:
		_stuck = 0.0
		Input.action_release("zipla")
	_last_x = pl.global_position.x
