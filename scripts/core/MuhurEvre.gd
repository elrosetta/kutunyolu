class_name MuhurEvre
extends Node2D
## v44 Mühür yolu, Beşinci Mühür kuralı "Zincir Evresi": boss canının %40'ına inince Erlik'in zincirini çağırır.
## Bossun yapay zekâsına dokunmaz; arenada ayrı bir düğüm olarak bossun canını izler ve yeni bir hamle ekler:
##   * Evreye giriş: boss kükrer (kara mürekkep halkası, sarsıntı, "<AD> · ZİNCİR EVRESİ" yazısı), saldırganlığı %15 artar.
##   * Zincir yağmuru: her ZAMAN sn'de oyuncunun bulunduğu yere ve bir yanına (evre ilerledikçe iki yanına) önce yerde
##     kızıl bir uyarı çizgisi + gökten sarkan ince zincir gölgesi (HAZIR sn, okunur), sonra ağır kara zincir iner:
##     altında kalan oyuncu bossun vuruşunun %80'i kadar hasar alır. Yuvarlanma / yana kaçış kurtarır.
## Dünya uzayında çizilir (Level'in çocuğu; z bossun önünde).

const ZAMAN := 3.4
const HAZIR := 0.85
const INIS := 0.16
const KAL := 0.5
const GEN := 22.0

var level: Node
var boss: Node
var esik := 0.4
var etkin := false
var _t := 0.0
var _sonraki := 1.2
var _vuruslar: Array = []    # [x, taban_y, t0 (hazırlık başı)]
var inen := 0                # test: inen zincir sayısı
var isabet := 0              # test


static func kur(lv: Node, b: Node, k: float) -> MuhurEvre:
	var m := MuhurEvre.new()
	m.level = lv
	m.boss = b
	m.esik = k
	m.z_index = 30
	m.name = "MuhurEvre"
	b.set_meta("muhur_evre", m)
	lv.add_child(m)
	return m


func _physics_process(delta: float) -> void:
	if boss == null or not is_instance_valid(boss) or bool(boss.dead):
		if _vuruslar.is_empty():
			queue_free()
			return
	elif not etkin and float(boss.hp) <= float(boss.max_hp) * esik:
		_basla()
	_t += delta
	if etkin and boss != null and is_instance_valid(boss) and not bool(boss.dead):
		_sonraki -= delta
		if _sonraki <= 0.0:
			_sonraki = ZAMAN * (0.85 if float(boss.hp) < float(boss.max_hp) * esik * 0.5 else 1.0)
			_yagmur()
	for v in _vuruslar.duplicate():
		var u: float = _t - float(v[2])
		if u >= HAZIR and not bool(v[3]):
			v[3] = true
			_in(v)
		if u >= HAZIR + INIS + KAL:
			_vuruslar.erase(v)
	queue_redraw()


func _basla() -> void:
	etkin = true
	_sonraki = 1.0
	if "_aggr" in boss:
		boss._aggr *= 1.15
	var c: Vector2 = boss.center()
	var ad := String(boss.def.get("name", "")) if "def" in boss else ""
	FX.text(c + Vector2(0, -float(boss.size.y) * 0.5 - 50), "%s · ZİNCİR EVRESİ" % Sinema.buyuk(ad), Color(1.0, 0.45, 0.3), 13)
	FX.ring(c, 120, Color(0.2, 0.05, 0.08), 0.7)
	FX.ring(c, 70, Color(1.0, 0.4, 0.25), 0.5)
	Game.shake_dir(0.6, Vector2.DOWN)
	Game.slowmo(0.35, 0.4)
	Ses.play("sin_erlik", -4.0)
	Ses.play("bag_zincir", -2.0)


func _yagmur() -> void:
	var pl: Node = level.player if level else null
	if pl == null or bool(pl.dead):
		return
	var px: float = pl.global_position.x
	var xs := [px]
	var yan := 1.0 if randf() < 0.5 else -1.0
	xs.append(px + yan * 74.0)
	if float(boss.hp) < float(boss.max_hp) * esik * 0.5:
		xs.append(px - yan * 74.0)
	for x in xs:
		var gy := _taban(float(x))
		_vuruslar.append([float(x), gy, _t, false])
	Ses.play("bag_zincir", -8.0, 0.8)


func _taban(x: float) -> float:
	if level.has_method("surface_y"):
		var tx := int(floor(x / 24.0))
		return float(level.surface_y(tx)) * 24.0
	return float(level.player.global_position.y)


func _in(v: Array) -> void:
	inen += 1
	var x := float(v[0])
	var gy := float(v[1])
	FX.burst(Vector2(x, gy - 4), Color(0.25, 0.2, 0.22), 14, 120, 0.4, 0.2, -120, false)
	Game.shake_dir(0.22, Vector2.DOWN)
	Ses.play("darbe_metal", -6.0, 0.7)
	var pl: Node = level.player
	if pl != null and not bool(pl.dead) and absf(pl.global_position.x - x) < GEN and pl.global_position.y > gy - 140.0:
		if pl.take_hit(float(boss.dmg) * 0.8 if is_instance_valid(boss) else 20.0, boss if is_instance_valid(boss) else null):
			isabet += 1


func _draw() -> void:
	if etkin and boss != null and is_instance_valid(boss) and not bool(boss.dead):
		# evre imi: gökten inen iki zincir bossun omuzlarına bağlı, salınır (Erlik'in tasması)
		var bc: Vector2 = boss.center()
		var h := float(boss.size.y)
		for s in [-1.0, 1.0]:
			var sal := sin(_t * 1.3 + s) * 10.0
			var omuz := bc + Vector2(s * float(boss.size.x) * 0.35, -h * 0.28)
			_zincir_ab(omuz + Vector2(s * 70.0 + sal, -420.0), omuz, Color(0.14, 0.1, 0.12, 0.92))
		draw_circle(bc, h * 0.62, Color(0.5, 0.05, 0.05, 0.07 + 0.04 * sin(_t * 3.0)))
	for v in _vuruslar:
		var x := float(v[0])
		var gy := float(v[1])
		var u: float = _t - float(v[2])
		var top := gy - 420.0
		if u < HAZIR:
			var k := u / HAZIR
			# yerde kızıl uyarı (genişleyen fırça), gökten sarkan ince zincir gölgesi
			draw_line(Vector2(x - GEN * (0.4 + 0.6 * k), gy - 1), Vector2(x + GEN * (0.4 + 0.6 * k), gy - 1), Color(1.0, 0.25, 0.15, 0.4 + 0.5 * k), 3.0, true)
			draw_line(Vector2(x, top), Vector2(x, gy), Color(0.9, 0.2, 0.15, 0.08 + 0.18 * k), 1.0 + 3.0 * k, true)
			_zincir(x, top, top + (gy - top) * 0.18 * k, Color(0.12, 0.1, 0.12, 0.35 + 0.4 * k))
		else:
			var w := clampf((u - HAZIR) / INIS, 0.0, 1.0)
			var a := 1.0 - clampf((u - HAZIR - INIS) / KAL, 0.0, 1.0)
			_zincir(x, top, top + (gy - top) * w, Color(0.1, 0.08, 0.1, a))
			if w >= 1.0:
				draw_circle(Vector2(x, gy - 3), 10.0 * a + 4.0, Color(1.0, 0.45, 0.2, 0.35 * a))


func _zincir(x: float, y0: float, y1: float, col: Color) -> void:
	_zincir_ab(Vector2(x, y0), Vector2(x, y1), col)


func _zincir_ab(a: Vector2, b: Vector2, col: Color) -> void:
	## a'dan b'ye halka halka zincir: kalın kara mürekkep halkalar (dönüşümlü yüz / yan), kemik rengi parıltı, kor kenarı;
	## açık gökte de koyu yerde de okunur
	var d := b - a
	var L := d.length()
	if L < 1.0:
		return
	var u := d / L
	var n := Vector2(-u.y, u.x)
	var ink := Color(0.03, 0.02, 0.03, col.a)
	var bone := Color(0.85, 0.78, 0.68, col.a * 0.8)
	var kor := Color(1.0, 0.4, 0.2, col.a * 0.5)
	var s := 0.0
	var i := 0
	while s < L:
		var c := a + u * (s + 8.0)
		if i % 2 == 0:
			var pts := PackedVector2Array()
			for k in 13:
				var t := TAU * float(k) / 12.0
				pts.append(c + u * cos(t) * 9.0 + n * sin(t) * 6.0)
			draw_polyline(pts, ink, 5.0, true)
			draw_polyline(pts, col.lerp(kor, 0.35), 2.5, true)
			draw_line(c - n * 4.5 + u * -4.0, c - n * 5.5 + u * 3.0, bone, 1.2, true)
		else:
			draw_line(c - u * 8.0, c + u * 8.0, ink, 6.0, true)
			draw_line(c - u * 7.0, c + u * 7.0, col.lerp(kor, 0.2), 3.0, true)
			draw_line(c - u * 5.0 - n * 1.2, c + u * 3.0 - n * 1.2, bone, 1.0, true)
		s += 14.0
		i += 1
