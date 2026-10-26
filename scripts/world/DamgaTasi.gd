class_name DamgaTasi
extends NPC
## v44 Damga Taşı: konakta Bengisu Usta'nın tezgâhı ile Demirci arasında dikili taş. Yüzündeki çerçevede sunulan üç
## tamga sırayla parlar (bu konakta Damga alındıysa vurulan tamga sabit, soluk). Yakınken W: Damga ekranı
## (Main._on_npc("damga") → DerinlikUI). Etkileşim NPC gibi (Level.npcs, nearest_npc).

const TEX := "res://assets/ui/ink/damga_tasi.png"
const BOY := Vector2(48, 80)

var _spr: Sprite2D
var _isik: PointLight2D


static func kur(lv: Node, tx: float) -> DamgaTasi:
	var d := DamgaTasi.new()
	d.id = "damga"
	d.display_name = "Damga Taşı"
	d.level = lv
	d.position = lv._hub_px(tx, 0.0)
	lv.actors.add_child(d)
	lv.npcs.append(d)
	return d


func _ready() -> void:
	z_index = 2
	process_mode = Node.PROCESS_MODE_ALWAYS
	_spr = Sprite2D.new()
	_spr.texture = Data.tex(TEX)
	_spr.centered = false
	_spr.texture_filter = CanvasItem.TEXTURE_FILTER_LINEAR_WITH_MIPMAPS
	if _spr.texture:
		_spr.scale = BOY / _spr.texture.get_size()
	_spr.position = Vector2(-BOY.x * 0.5, -BOY.y + 2.0)
	_spr.show_behind_parent = true
	add_child(_spr)
	if level:
		_isik = level.add_light(Vector2(0, -50), Color(1.0, 0.75, 0.4), 120.0, 0.6, self)


func talk() -> void:
	talk_t = 0.6


func _process(delta: float) -> void:
	_t += delta
	talk_t -= delta
	var paused := get_tree().paused
	if paused == _yazi:
		_yazi = not paused
	var pl: Node = level.player if level else null
	if pl and not paused:
		near = absf(pl.global_position.x - global_position.x) < 30.0 and absf(pl.global_position.y - global_position.y) < 40.0
	if _isik:
		_isik.energy = 0.45 + 0.2 * sin(_t * 2.2) + (0.5 if near else 0.0)
	queue_redraw()


func _tamga_simdi() -> String:
	if Damga.secildi():
		var a: Array = Damga.etkin()
		return String(a[-1]) if not a.is_empty() else ""
	var tk: Array = Damga.teklif()
	if tk.is_empty():
		return ""
	return String(tk[int(_t / 1.6) % tk.size()])


func _draw() -> void:
	# taşın çerçevesinde parlayan tamga (toplamalı değil: mürekkep-cel; parıltı halkası ve kor)
	var id := _tamga_simdi()
	var c := Vector2(0, -BOY.y + 2.0 + BOY.y * 0.38)
	if id != "":
		var col := Damga.renk(id)
		var k := 0.6 + 0.4 * sin(_t * 3.0) if not Damga.secildi() else 0.35
		var fade := fposmod(_t, 1.6) / 1.6
		var a := clampf(minf(fade * 5.0, (1.0 - fade) * 5.0), 0.0, 1.0) if not Damga.secildi() else 1.0
		draw_circle(c, 13.0, Color(col, 0.16 * k * a))
		DerinlikUI.tamga(self, id, c, 17.0, Color(col.lightened(0.25), (0.75 + 0.25 * k) * a))
	if not _yazi:
		return
	PixUI.text(self, Vector2(-80, -101), display_name, PixUI.TEXT, 1, HORIZONTAL_ALIGNMENT_CENTER, 160, 2)
	if not Damga.secildi() and not Game.run.is_empty():
		var by := roundf(-114.0 + sin(_t * 4.0) * 2.0)
		PixUI.text(self, Vector2(-80, by), "üç tamga bekliyor", InkUI.GOLD, 1, HORIZONTAL_ALIGNMENT_CENTER, 160, 2)
	if near:
		var y := roundf(-128.0 + sin(_t * 5.0) * 2.0)
		PixUI.key_cap(self, Vector2(-5, y), HUD.KEY_ETKILES)
