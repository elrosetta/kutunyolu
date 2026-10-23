class_name OtagIc
extends Control
## v42 otağ içi: açık otağa W ile girilince oyun durur, otağın içi (otag_v2 "otag_ic": kerege kafesi, uuk sırıkları,
## tündükten ay ışığı, asılı kilimler, ocak) ve ödül sandığı görünür. Sandık 0,6 sn'de açılır, ödül satırları sırayla
## belirir; W / Boşluk / Esc ile çıkılır: ödül otağın kapısına düşer (eşya / tomar / parşömen), altın ve Kut doğrudan
## eklenir (Level.otag_odul_ver). Kendi CanvasLayer'ında (Level kurar); HUD "otag" kipinde duraklatma menüsü çizmez.

var level: Node
var otag: Node
var odul: Dictionary = {}
var _t := 0.0
var _kapandi := false
var _hud_once := "play"


func _ready() -> void:
	process_mode = Node.PROCESS_MODE_ALWAYS
	position = Vector2.ZERO
	size = get_viewport_rect().size
	mouse_filter = Control.MOUSE_FILTER_IGNORE
	InkDraw.prep(self)
	var m: Node = level.get_parent() if level else null
	if m and m.get("hud") != null:
		_hud_once = String(m.hud.mode)
		m.hud.mode = "otag"
	get_tree().paused = true
	Ses.play("otag_ac", -2.0, 1.0, 0.02)


func _process(delta: float) -> void:
	var t0 := _t
	_t += delta
	if t0 < 0.6 and _t >= 0.6:
		Ses.play("otag_odul", -2.0, 1.0, 0.02)
	var m: Node = level.get_parent() if level else null
	if _t > 1.6 and m != null and bool(m.get("auto_test")):
		kapat()   # bot (--otomatik): otağdan kendiliğinden çıkar
		return
	if _t > 1.0 and (Input.is_action_just_pressed("etkiles") or Input.is_action_just_pressed("zipla") or Input.is_action_just_pressed("duraklat")):
		kapat()
	queue_redraw()


func kapat() -> void:
	if _kapandi:
		return
	_kapandi = true
	get_tree().paused = false
	var m: Node = level.get_parent() if level else null
	if m and m.get("hud") != null:
		m.hud.mode = _hud_once if _hud_once != "otag" else "play"
	if level and is_instance_valid(otag):
		level.otag_odul_ver(otag, odul)
		print("[otag] ÇIKIŞ %s ödül: %s" % [String(otag.tur), ", ".join(satirlar().map(func(l: Array) -> String: return String(l[0])))])
	Ses.play("ui_kapa", -6.0)
	var cl := get_parent()
	if cl is CanvasLayer:
		cl.queue_free()
	else:
		queue_free()


func satirlar() -> Array:
	## [metin, renk] ödül satırları
	var out: Array = []
	var gold := Color(1.0, 0.85, 0.45)
	if int(odul.get("altin", 0)) > 0:
		out.append(["+%d altın" % int(odul["altin"]), gold])
	if int(odul.get("kut", 0)) > 0:
		out.append(["+%d Kut" % int(odul["kut"]), Color(0.55, 1.0, 0.95)])
	if int(odul.get("tomar", 0)) > 0:
		out.append(["Kut Tomarı", Color(1.0, 0.78, 0.45)])
	if String(odul.get("parsomen", "")) != "":
		out.append(["Parşömen: " + String(Data.find_item(String(odul["parsomen"])).get("name", odul["parsomen"])), Color(0.9, 0.86, 0.7)])
	var rars: Array = Data.items["rarities"]
	for it in odul.get("items", []):
		var r: Dictionary = rars[clampi(int(it.get("rarity", 0)), 0, rars.size() - 1)]
		out.append(["%s  (%s)" % [String(it.get("name", "")), String(r["name"])], Color(String(r["color"]))])
	return out


func _draw() -> void:
	var vp := get_viewport_rect().size
	var s := vp.y / 360.0
	var a := clampf(_t / 0.35, 0.0, 1.0)
	draw_rect(Rect2(Vector2.ZERO, vp), Color(0.02, 0.015, 0.03, 0.82 * a))
	var tur := String(otag.tur) if is_instance_valid(otag) else "cabuk"
	var col: Color = Sinav.RENK.get(tur, Color(1, 0.85, 0.45))
	# otağ içi resmi
	var r := Otag.region("otag_ic")
	var pw := 400.0 * s
	var ph := pw * (r.size.y / maxf(1.0, r.size.x))
	var pr := Rect2((vp.x - pw) * 0.5, 34.0 * s + (1.0 - a) * 10.0 * s, pw, ph)
	if Otag.tex() != null:
		draw_texture_rect_region(Otag.tex(), pr, r, Color(1, 1, 1, a))
	# ince mürekkep çerçeve
	for i in 4:
		var e := pr.grow(-1.0 * s + i * 0.6 * s)
		draw_rect(e, Color(0.05, 0.04, 0.05, 0.9 * a), false, 1.5 * s)
	draw_rect(pr.grow(3.0 * s), Color(col, 0.55 * a), false, 1.2 * s)
	# sandık (açılır)
	var sn := "sandik_acik" if _t >= 0.6 else "sandik_kapali"
	var sr := Otag.region(sn)
	var sh := 58.0 * s
	var sw := sh * sr.size.x / maxf(1.0, sr.size.y)
	var sc := Vector2(pr.position.x + pr.size.x * 0.63, pr.end.y - 14.0 * s)
	var bob := 0.0 if _t >= 0.6 else sin(_t * 40.0) * 1.2 * s * clampf((_t - 0.3) / 0.3, 0.0, 1.0)
	if Otag.tex() != null:
		if _t >= 0.6:
			var gk := clampf((_t - 0.6) / 0.4, 0.0, 1.0)
			InkDraw.soft(self, sc + Vector2(0, -sh * 0.55), sh * 0.55, Color(1.0, 0.7, 0.3, 0.35 * gk))
		draw_texture_rect_region(Otag.tex(), Rect2(sc + Vector2(-sw * 0.5 + bob, -sh), Vector2(sw, sh)), sr, Color(1, 1, 1, a))
	# başlık
	var fc := InkUI.font("caps")
	var fb := InkUI.font("body")
	var title := InkHUD.tr_upper(Sinav.AD.get(tur, "") + (" Otağı" if tur != "han" else ""))
	var ts := int(round(16 * s))
	var tw := fc.get_string_size(title, HORIZONTAL_ALIGNMENT_LEFT, -1, ts).x
	Otag.ui_draw(self, "ui_muhur", Vector2((vp.x - tw) * 0.5 - 18.0 * s, 22.0 * s), 18.0 * s, Color(col, a))
	Otag.ui_draw(self, "ui_tamga_" + tur, Vector2((vp.x - tw) * 0.5 - 18.0 * s, 22.0 * s), 12.0 * s, Color(0.12, 0.08, 0.06, a))
	InkUI.draw_str(self, Vector2((vp.x - tw) * 0.5, 28.0 * s), title, fc, ts, Color(col, a), 2)
	# ödül satırları (sandık açılınca sırayla)
	var ls := satirlar()
	var y := pr.end.y + 22.0 * s
	var fsz := int(round(11 * s))
	for i in ls.size():
		var la := clampf((_t - 0.75 - i * 0.18) / 0.25, 0.0, 1.0)
		if la <= 0.0:
			continue
		var txt := String(ls[i][0])
		var w := fb.get_string_size(txt, HORIZONTAL_ALIGNMENT_LEFT, -1, fsz).x
		InkUI.draw_str(self, Vector2((vp.x - w) * 0.5, y + (1.0 - la) * 6.0 * s), txt, fb, fsz, Color(ls[i][1], la), 2)
		y += 15.0 * s
	if _t > 1.0:
		var h := "W / Boşluk: ödülü al ve otağdan çık"
		var hw := fb.get_string_size(h, HORIZONTAL_ALIGNMENT_LEFT, -1, int(round(9 * s))).x
		InkUI.draw_str(self, Vector2((vp.x - hw) * 0.5, vp.y - 12.0 * s), h, fb, int(round(9 * s)), Color(0.85, 0.8, 0.7, 0.55 + 0.3 * sin(_t * 3.0)), 1)
