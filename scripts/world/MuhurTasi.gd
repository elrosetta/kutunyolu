class_name MuhurTasi
extends NPC
## v44 Mühür Taşı (yurt, Kut Kapısı'nın solunda): kırık güneş sunağının üstünde beş yuvalı taş. Erlik'in zincirinden
## kalan her halka Umay'ın elinde bir Kut Mührü olur ve bir yuvaya basılır (mühür açıldı); o mühürde Erlik yenilince
## mühür altın kenar alır ve parlar (zafer). Seçili mührün yuvasından Kut Kapısı'na doğru ince bir ışık akar.
## W: mühür seçim ekranı (MuhurUI; Main._on_npc "muhur_tasi"). Yeni mühür açıldıysa (meta muhur_toren) yurda ilk
## girişte tören: mühür gökten süzülüp yuvasına oturur, mürekkep sıçrar, Umay konuşur.
## NPC'den türer (Level.nearest_npc / npc_requested yolu aynı); sprite yok, kendini çizer.

const YUVA_R := 6.5
var yuva_merkez: Array = []     # dünya yerel (düğüme göre) yuva merkezleri
var toren := -1                 # oynayan tören (mühür no)
var toren_t := 0.0
var toren_bitti := false        # test
var _sunak: Sprite2D
var _isik: PointLight2D


static func kur(lv: Node, tx: float) -> MuhurTasi:
	var m := MuhurTasi.new()
	m.id = "muhur_tasi"
	m.display_name = "Mühür Taşı"
	m.level = lv
	m.position = lv._hub_px(tx, 0.0)
	lv.actors.add_child(m)
	lv.npcs.append(m)
	m._sunak = lv._hub_prop("gun_sunagi", tx, -3)
	return m


func _ready() -> void:
	z_index = 2
	process_mode = Node.PROCESS_MODE_ALWAYS
	# beş yuva: dikili taşın yüzünde, güneş ışını gibi açılan yay (soldan sağa I..V)
	for i in 5:
		var a := lerpf(deg_to_rad(198.0), deg_to_rad(342.0), float(i) / 4.0)
		yuva_merkez.append(Vector2(0, -62) + Vector2.from_angle(a) * 27.0)
	if level:
		_isik = level.add_light(Vector2(0, -56), Color(1.0, 0.6, 0.4), 120.0, 0.45, self)
	var bekleyen := int(Game.meta.get("muhur_toren", -1))
	if bekleyen >= 1 and bekleyen <= Zorluk.muhur_acik():
		toren = bekleyen
		toren_t = -1.2   # yurt perdesi açılsın
	soz = _soz()


func _soz() -> String:
	if Zorluk.muhur_acik() <= 0:
		return MuhurYolu.satir("tas_bos", int(Game.meta.get("runs", 0)))
	return MuhurYolu.satir("tas", int(Game.meta.get("runs", 0)))


func talk() -> void:
	talk_t = 0.6
	Ses.play("sin_muhur", -8.0, 1.2)


func _process(delta: float) -> void:
	_t += delta
	talk_t -= delta
	var paused := get_tree().paused
	if paused == _yazi:
		_yazi = not paused
	if toren >= 1 and not paused:
		toren_t += delta
		if toren_t >= 0.0 and toren_t - delta < 0.0:
			Ses.play("sin_parilti", -6.0)
		if toren_t >= 1.4 and toren_t - delta < 1.4:
			_oturdu()
		if toren_t >= 3.2:
			toren = -1
			toren_bitti = true
	var pl: Node = level.player if level else null
	if pl and not paused:
		near = absf(pl.global_position.x - global_position.x) < 34.0 and absf(pl.global_position.y - global_position.y) < 44.0
	if _isik:
		_isik.energy = 0.35 + 0.08 * Zorluk.muhur_acik() + 0.1 * sin(_t * 1.7)
	queue_redraw()


func _oturdu() -> void:
	var c: Vector2 = global_position + yuva_merkez[clampi(toren - 1, 0, 4)]
	var col := MuhurYolu.renk(toren)
	FX.ring(c, 40, col, 0.6)
	FX.soul(c, col, 26)
	FX.flash_light(c, col, 220.0, 1.6, 0.5)
	Game.shake(2.0)
	Ses.play("sin_muhur", -2.0)
	Game.meta["muhur_toren"] = -1
	Game.save_meta()
	Gorum.konus("Umay Ana", MuhurYolu.umay_sozu(toren), Color(0.62, 0.9, 0.86), 5.5)


func _draw() -> void:
	var acik := Zorluk.muhur_acik()
	var secili := Zorluk.muhur_secili()
	# dikili taş (bitig taşı gibi): sunağın üstünde, sivri başlı; mürekkep kontur, ay yanı açık, gölge yanı koyu
	var pts := PackedVector2Array([Vector2(-34, -24), Vector2(-36, -70), Vector2(-24, -94), Vector2(0, -104), Vector2(24, -94), Vector2(36, -70), Vector2(34, -24)])
	draw_colored_polygon(pts, Color(0.2, 0.19, 0.23, 1.0))
	draw_colored_polygon(PackedVector2Array([Vector2(4, -24), Vector2(4, -102), Vector2(24, -94), Vector2(36, -70), Vector2(34, -24)]), Color(0.13, 0.12, 0.16, 1.0))
	var kenar := pts.duplicate()
	kenar.append(pts[0])
	draw_polyline(kenar, Color(0.03, 0.02, 0.05, 1.0), 2.5, true)
	draw_line(Vector2(-33, -66), Vector2(-22, -90), Color(0.75, 0.78, 0.9, 0.35), 1.2, true)
	# yazıt çizgileri ve Kut tamgası (taşın alt yüzü)
	for k in 3:
		draw_line(Vector2(-22, -40 + k * 5), Vector2(22, -40 + k * 5), Color(0.6, 0.5, 0.35, 0.28), 1.0, true)
	InkUI.tamga(self, 1, Vector2(0, -60), 10.0, Color(0.85, 0.7, 0.45, 0.3 + 0.06 * acik))
	for i in 5:
		var n := i + 1
		var c: Vector2 = yuva_merkez[i]
		var col := MuhurYolu.renk(n)
		var dolu := n <= acik and not (toren == n and toren_t < 1.4)
		# yuva oyuğu
		draw_circle(c, YUVA_R + 1.5, Color(0.02, 0.015, 0.03, 0.95))
		draw_arc(c, YUVA_R + 1.5, 0, TAU, 20, Color(0.5, 0.42, 0.32, 0.6), 1.0, true)
		if dolu:
			var zafer := MuhurYolu.zafer_var(n)
			var nef := 0.5 + 0.5 * sin(_t * 2.0 + i)
			draw_circle(c, YUVA_R + 3.5, Color(col.darkened(0.3), 0.08 + 0.06 * nef))
			InkUI.seal_round(self, c, YUVA_R * 2.1, col.darkened(0.42), float(i) * 0.7)
			_roma(c, n, Color(0.08, 0.04, 0.03, 0.9))
			if zafer:
				draw_arc(c, YUVA_R + 2.0, 0, TAU, 24, Color(0.85, 0.66, 0.3, 0.55 + 0.2 * nef), 1.0, true)
			if n == secili:
				# seçili mühür: yuvadan göğe ince ışık
				draw_arc(c, YUVA_R + 4.0, _t, _t + PI * 1.4, 16, Color(col, 0.85), 1.2, true)
		elif n == acik + 1:
			# kazanılacak sıradaki yuva: soluk nabız
			draw_arc(c, YUVA_R - 1.0, 0, TAU, 20, Color(col, 0.18 + 0.15 * sin(_t * 3.0)), 1.2, true)
	if toren >= 1 and toren_t >= 0.0 and toren_t < 1.4:
		# tören: mühür gökten süzülür, dönerek yuvasına iner
		var u := clampf(toren_t / 1.4, 0.0, 1.0)
		var e := u * u * (3.0 - 2.0 * u)
		var hedef: Vector2 = yuva_merkez[clampi(toren - 1, 0, 4)]
		var p := hedef + Vector2(sin(u * 9.0) * 14.0 * (1.0 - u), -150.0 * (1.0 - e))
		var col2 := MuhurYolu.renk(toren)
		draw_circle(p, 26.0 * (1.0 - u) + 10.0, Color(col2, 0.12))
		InkUI.seal_round(self, p, YUVA_R * 2.2 * (1.6 - 0.6 * e), col2, u * 6.0)
	elif toren >= 1 and toren_t >= 1.4:
		var k := clampf((toren_t - 1.4) / 1.8, 0.0, 1.0)
		var hedef2: Vector2 = yuva_merkez[clampi(toren - 1, 0, 4)]
		draw_arc(hedef2, YUVA_R + 4.0 + 50.0 * k, 0, TAU, 32, Color(MuhurYolu.renk(toren), 1.0 - k), 2.0, true)
	if not _yazi:
		return
	PixUI.text(self, Vector2(-80, -126), display_name, PixUI.TEXT, 1, HORIZONTAL_ALIGNMENT_CENTER, 160, 2)
	if acik > 0:
		PixUI.text(self, Vector2(-80, -115), "%s · %d / 5" % [MuhurYolu.ad(secili), acik], Color(MuhurYolu.renk(secili).lerp(PixUI.TEXT, 0.4), 0.9), 1, HORIZONTAL_ALIGNMENT_CENTER, 160, 2)
	if near:
		var y := roundf(-142.0 + sin(_t * 5.0) * 2.0)
		PixUI.key_cap(self, Vector2(-5, y), HUD.KEY_ETKILES)
		if soz != "":
			PixUI.text(self, Vector2(-110, y - 14.0), "«%s»" % soz, Color(PixUI.TEXT, 0.85), 1, HORIZONTAL_ALIGNMENT_CENTER, 220, 2)


func _roma(c: Vector2, n: int, col: Color) -> void:
	var f: Font = InkUI.font("caps")
	var s: String = MuhurYolu.ROMA[n]
	var w := f.get_string_size(s, HORIZONTAL_ALIGNMENT_LEFT, -1, 6).x
	draw_string(f, c + Vector2(-w * 0.5, 2.2), s, HORIZONTAL_ALIGNMENT_LEFT, -1, 6, col)
