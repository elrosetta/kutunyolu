class_name ZamanliKapi
extends Node2D
## v32 zamanlı kapı (Dead Cells'in zamanlı kapıları gibi): çıkmaz ödül odasının girişi; bölüm başından `sure` saniye
## sonra oyuncu odanın dışındaysa kapanır (4 karolık geçit katı olur: Level.set_solid). Oyuncu süresinde içeri
## girdiyse kapı hep açık kalır (ödül kazanıldı). Çizim: iki yanda taş söve, üstte kum saati tamgası ve kalan süre;
## kapanınca mürekkep demir parmaklıklar.

var level: Node
var cell := Vector2i.ZERO    # kapı sütunu (x) ve taban satırı (y); geçit y-4..y-1
var sure := 90.0
var ic_yon := 1              # ödül odası kapının hangi yanında (+1: sağ, -1: sol)
var oda := Rect2i()          # ödül odasının iç alanı (karo): oyuncu buradaysa "içeride"
var acik := true
var kazanildi := false
var _t := 0.0
var _kapanma := 0.0


func _ready() -> void:
	z_index = 4
	InkDraw.prep(self)


func kalan() -> float:
	return maxf(0.0, sure - float(Game.run.get("bolum_sure", 0.0)))


func etiket() -> String:
	if not acik:
		return "Kapalı"
	if kazanildi:
		return "Açık"
	return "%d sn" % int(ceil(kalan()))


func _physics_process(delta: float) -> void:
	_t += delta
	_kapanma = maxf(0.0, _kapanma - delta)
	if level == null or level.player == null:
		return
	var TS: int = level.TS
	var pc := Vector2i(int(floor(level.player.global_position.x / TS)), int(floor((level.player.global_position.y - 4.0) / TS)))
	var inside: bool = oda.has_point(pc) and (pc.x - cell.x) * ic_yon > 0
	if acik and not kazanildi and inside:
		kazanildi = true
		FX.text(global_position + Vector2(0, -70), "Zamanında yetiştin!", Color(1.0, 0.85, 0.45), 9)
	if acik and not kazanildi and kalan() <= 0.0 and not inside:
		_kapat()
	if Engine.get_process_frames() % 3 == 0:
		queue_redraw()


func _kapat() -> void:
	acik = false
	_kapanma = 0.6
	for y in range(cell.y - 4, cell.y):
		level.set_solid(cell.x, y)
	FX.dust(global_position + Vector2(12, -2), Vector2.UP, 10, 0.4)
	Game.shake(2.0)
	Ses.play("kapi", -4.0, 0.7)


func _draw() -> void:
	var TS: float = float(level.TS) if level else 24.0
	var top := -4.0 * TS
	var ink := Color(0.08, 0.06, 0.08)
	# söve: iki yanda ince taş direk, üstte kiriş
	InkDraw.stroke(self, Vector2(-3, 0), Vector2(-3, top - 4), 4.0, ink)
	InkDraw.stroke(self, Vector2(TS + 3, 0), Vector2(TS + 3, top - 4), 4.0, ink)
	InkDraw.stroke(self, Vector2(-8, top - 4), Vector2(TS + 8, top - 4), 5.0, ink)
	var col := Color(1.0, 0.85, 0.45) if acik else Color(0.55, 0.5, 0.5)
	# kum saati tamgası (kirişin üstünde)
	var c := Vector2(TS * 0.5, top - 14)
	draw_line(c + Vector2(-5, -6), c + Vector2(5, -6), col, 1.4, true)
	draw_line(c + Vector2(-5, 6), c + Vector2(5, 6), col, 1.4, true)
	draw_line(c + Vector2(-4, -6), c + Vector2(4, 6), col, 1.2, true)
	draw_line(c + Vector2(4, -6), c + Vector2(-4, 6), col, 1.2, true)
	if acik and not kazanildi:
		var kl := kalan()
		var k := clampf(kl / sure, 0.0, 1.0)
		draw_line(c + Vector2(-8, 11), c + Vector2(-8 + 16.0 * k, 11), col, 2.0, true)
		if kl < 15.0:
			InkDraw.soft(self, c, 10.0, Color(1.0, 0.4, 0.3, 0.3 + 0.3 * sin(_t * 8.0)), 0)
	elif kazanildi:
		InkDraw.soft(self, c, 9.0, Color(1.0, 0.85, 0.45, 0.25 + 0.1 * sin(_t * 2.0)), 1)
	if not acik:
		# demir parmaklıklar (karolar katı; bu yalnızca görsel)
		var kk := 1.0 - _kapanma / 0.6
		for i in 4:
			var x := 3.0 + i * (TS - 6.0) / 3.0
			InkDraw.stroke(self, Vector2(x, top - 2), Vector2(x, top + (2.0 - top) * kk), 2.4, Color(0.2, 0.17, 0.18))
		InkDraw.stroke(self, Vector2(-2, top * 0.5), Vector2(TS + 2, top * 0.5), 2.0, Color(0.2, 0.17, 0.18))
