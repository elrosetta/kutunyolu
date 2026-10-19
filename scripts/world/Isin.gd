class_name Isin
extends Node2D
## v23 ışın / bağ çizgisi (düşman ve boss hamleleri). Sahibi her kare origin / tip (ya da aim) verir.
##   goz    Tepegöz'ün göz ışını: önce ince titreşen nişan çizgisi (charge 0..1), sonra kalın kızıl ışın (on: hasar)
##   bag    Erlik'in Kızı'nın büyü bağı (mor, dalgalı; hasarsız: çekmeyi sahibi yapar)
##   ayaz   Yelbegen'in ayaz soluğu (buz mavisi geniş huzme)
##   zincir Erlik Han'ın kara zinciri (halkalı)

var level: Node
var source: Node
var kind := "goz"
var origin := Vector2.ZERO
var tip := Vector2.ZERO
var on := false
var charge := 0.0
var dmg := 0.0
var width := 12.0
var hits := 0          # oyuncuya kaç kez değdi (sahibi okur)
var follow: Callable   # v25: her kare origin'i veren çağrı (Tepegöz'ün göz çapası); hazırlıkta / duraklamada da gözü izler
var target := Vector2.INF   # v25: follow varken ışının hedef noktası (origin oynadıkça yeniden nişan alınır)
var reach := 900.0
var _t := 0.0


func _ready() -> void:
	z_index = 24
	InkDraw.prep(self)
	var m := CanvasItemMaterial.new()
	m.light_mode = CanvasItemMaterial.LIGHT_MODE_UNSHADED
	if kind in ["goz", "ayaz"]:
		m.blend_mode = CanvasItemMaterial.BLEND_MODE_ADD
	material = m


func aim(ang: float, length: float) -> void:
	## origin'den ang yönünde length boyunca; ilk katı karoda durur (ışın zemine çarpar)
	var d := Vector2.from_angle(ang)
	var l := 0.0
	while l < length:
		if level and level.solid_at(origin + d * l):
			break
		l += 8.0
	tip = origin + d * l


func touches(r: Rect2) -> bool:
	var seg := tip - origin
	var n := int(seg.length() / 6.0) + 1
	var g := r.grow(width * 0.35)
	for i in n + 1:
		if g.has_point(origin + seg * (float(i) / n)):
			return true
	return false


func _process(delta: float) -> void:
	_t += delta
	if follow.is_valid():
		origin = follow.call()
		if target != Vector2.INF:
			aim((target - origin).angle(), reach)
	if on and dmg > 0.0 and level and level.player:
		var pl: Node = level.player
		if not pl.dead and touches(pl.hurt_rect()):
			if pl.take_hit(dmg, source if is_instance_valid(source) else null):
				hits += 1
	if on and Engine.get_process_frames() % 3 == 0 and kind in ["goz", "ayaz"]:
		if kind == "goz":
			FX.sparks(tip, (origin - tip).normalized(), Color(1.0, 0.6, 0.3), 3, 160.0)
			if Engine.get_process_frames() % 9 == 0:
				FX.smoke(tip, 1, 0.3, Color(0.3, 0.2, 0.18, 0.5))
		else:
			FX.frost(tip, 1)
	queue_redraw()


func _draw() -> void:
	var o := to_local(origin)
	var t := to_local(tip)
	if o.distance_to(t) < 2.0:
		return
	match kind:
		"goz", "ayaz":
			var hot := Color(1.0, 0.35, 0.18) if kind == "goz" else Color(0.55, 0.85, 1.0)
			var core := Color(1.0, 0.92, 0.75) if kind == "goz" else Color(0.95, 1.0, 1.0)
			if not on:
				var flick := 0.5 + 0.5 * float(int(_t * 20.0) % 2)
				InkDraw.line(self, PackedVector2Array([o, t]), 2.0 + 2.0 * charge, 1.0, Color(hot, (0.35 + 0.4 * charge) * flick))
				InkDraw.soft(self, o, 6.0 + 10.0 * charge, Color(hot, 0.5 * charge))
				return
			var wob := 1.0 + 0.12 * sin(_t * 40.0)
			InkDraw.line(self, PackedVector2Array([o, t]), width * 2.2 * wob, width * 1.6, Color(hot, 0.28))
			InkDraw.line(self, PackedVector2Array([o, t]), width * wob, width * 0.75, Color(hot, 0.85))
			InkDraw.line(self, PackedVector2Array([o, t]), width * 0.38, width * 0.3, Color(core, 0.95))
			InkDraw.soft(self, o, width * 1.4, Color(core, 0.7))
			InkDraw.soft(self, t, width * 1.8 * wob, Color(hot, 0.6))
		"bag":
			var pts := PackedVector2Array()
			var seg := t - o
			var nrm := Vector2(-seg.y, seg.x).normalized()
			var n := maxi(6, int(seg.length() / 10.0))
			for i in n + 1:
				var k := float(i) / n
				pts.append(o + seg * k + nrm * sin(k * 12.0 - _t * 14.0) * 5.0 * sin(k * PI))
			var a := 0.85 if on else 0.35
			InkDraw.line(self, pts, 5.0, 3.0, Color(0.75, 0.2, 0.65, 0.4 * a))
			InkDraw.line(self, pts, 2.4, 1.4, Color(1.0, 0.55, 0.95, a))
			InkDraw.soft(self, t, 8.0, Color(0.9, 0.4, 0.85, 0.5 * a))
		"zincir":
			var seg2 := t - o
			var n2 := maxi(2, int(seg2.length() / 9.0))
			InkDraw.line(self, PackedVector2Array([o, t]), 3.0, 2.0, Color(0.1, 0.06, 0.06, 0.9))
			for i in n2 + 1:
				var p := o + seg2 * (float(i) / n2)
				InkDraw.ring(self, p, 4.0, 2.6, Color(0.25, 0.16, 0.14, 0.95), seg2.angle() + (PI * 0.5 if i % 2 == 0 else 0.0))
			InkDraw.soft(self, t, 9.0, Color(1.0, 0.45, 0.15, 0.6))
			InkDraw.star(self, t, 6.0, _t * 3.0, Color(1.0, 0.6, 0.3, 0.9))
