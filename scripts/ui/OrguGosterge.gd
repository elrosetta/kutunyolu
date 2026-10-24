class_name OrguGosterge
extends RefCounted
## v43 Gün Örgüleri göstergesi: beş fırça çemberi (Al / Ak / Gök / Sarı / Altın, Hikaye.ORGU_SIRA). Alınan örgü kendi
## renginde nefes alır, alınmayan boş çember (kâğıt rengi ince iz). Duraklatma ve tam ekran haritada sürekli (sağ üst),
## oyun HUD'unda yalnızca ilerleme değişince birkaç saniye (bildir) — tepede ortada belirip söner.

const HUD_SURE := 6.0

static var _degisim_ms := -100000
static var _yeni := -1


static func bildir(sira: int) -> void:
	## Örgü alındı (Main / örgü sahnesi sonrası): HUD'da gösterge belirir, yeni yuva parlar
	_degisim_ms = Time.get_ticks_msec()
	_yeni = sira


static func gecen() -> float:
	return float(Time.get_ticks_msec() - _degisim_ms) / 1000.0


static func ciz(ci: CanvasItem, merkez: Vector2, olcek := 1.0, a := 1.0, yazi := true) -> void:
	var t := float(Time.get_ticks_msec()) / 1000.0
	var enso := InkUI.tex("enso")
	var gap := 22.0 * olcek
	var r := 8.0 * olcek
	# ardında yumuşak mürekkep yıkaması
	var band := InkUI.tex("band")
	if band:
		ci.draw_texture_rect(band, Rect2(merkez - Vector2(gap * 3.2, r * 2.4), Vector2(gap * 6.4, r * (4.8 if not yazi else 6.6))), false, Color(InkUI.INK, 0.55 * a))
	var g := gecen()
	for i in 5:
		var bid: String = Hikaye.ORGU_SIRA[i]
		var c := merkez + Vector2((i - 2) * gap, 0.0)
		var col := Hikaye.orgu_renk(bid)
		var var_ := Hikaye.parca_var(bid)
		if enso:
			ci.draw_texture_rect(enso, Rect2(c - Vector2(r, r) * 1.45, Vector2(r, r) * 2.9), false, Color(InkUI.INK, 0.9 * a))
			ci.draw_texture_rect(enso, Rect2(c - Vector2(r, r) * 1.25, Vector2(r, r) * 2.5), false, Color(InkUI.BONE, (0.55 if var_ else 0.28) * a))
		if var_:
			var nef := 0.85 + 0.15 * sin(t * 2.2 + i * 1.3)
			var puls := 1.0
			if i == _yeni and g < 2.5:
				puls = 1.0 + 0.6 * clampf(1.0 - g / 2.5, 0.0, 1.0)
				ci.draw_arc(c, r * (1.2 + g * 1.6), 0.0, TAU, 32, Color(col, a * clampf(1.0 - g / 2.5, 0.0, 1.0)), 1.5 * olcek, true)
			ci.draw_circle(c, r * 1.5 * nef * puls, Color(col, 0.16 * a), true, -1.0, true)
			ci.draw_circle(c, r * 0.72 * puls, Color(col, 0.9 * a), true, -1.0, true)
			# örgü dokusu: iki ters kama
			ci.draw_line(c + Vector2(-r * 0.35, -r * 0.3), c + Vector2(r * 0.1, r * 0.05), Color(col.darkened(0.5), 0.7 * a), maxf(1.0, olcek), true)
			ci.draw_line(c + Vector2(r * 0.35, -r * 0.05), c + Vector2(-r * 0.1, r * 0.35), Color(col.darkened(0.5), 0.7 * a), maxf(1.0, olcek), true)
			ci.draw_circle(c + Vector2(-r * 0.2, -r * 0.25), r * 0.18, Color(1, 1, 1, 0.5 * a), true, -1.0, true)
	if yazi:
		var f := InkUI.font("caps")
		var s := "GÜN ÖRGÜLERİ  %d / 5" % Hikaye.parca_sayi() if not Hikaye.safak() else "TAN SÖKTÜ"
		var fs := int(maxf(8.0, 8.0 * olcek))
		var w := f.get_string_size(s, HORIZONTAL_ALIGNMENT_LEFT, -1, fs).x
		ci.draw_string(f, Vector2(merkez.x - w * 0.5, merkez.y + r * 2.6 + fs * 0.5), s, HORIZONTAL_ALIGNMENT_LEFT, -1, fs, Color(1.0, 0.86, 0.55, 0.85 * a))


static func hud(ci: CanvasItem, vp: Vector2) -> void:
	## Oyun HUD'u: ilerleme değişince tepede ortada birkaç saniye
	var g := gecen()
	if g > HUD_SURE:
		return
	var a := clampf(minf(g / 0.5, (HUD_SURE - g) / 1.0), 0.0, 1.0)
	ciz(ci, Vector2(vp.x * 0.5, 30.0 + (1.0 - a) * -10.0), 1.1, a, true)
