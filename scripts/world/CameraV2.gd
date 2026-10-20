class_name CameraV2
extends Camera2D
## Stil v2 (mürekkep) kamerası: yakın çekim (stil_v2.json "camera_zoom", biyoma göre 1,65-1,75; v19'a dek 2,0: Bengü
## 1080p'de ~195 px, ekranın ~%18'i). v1 kamerası (oyuncunun çocuğu, Player._look_ahead) hiç değişmez.
## Çerçeve sabitleri 2,0 yakınlık için yazıldı (REF_ZOOM); taban yakınlık farklıysa öncü kayma, ayak yüksekliği,
## zıplama penceresi ve düşüş bakışı aynı EKRAN oranında kalsın diye REF_ZOOM / taban ile ölçeklenir.
##
## Oyuncunun çocuğu DEĞİL (Level'ın çocuğu): hedefi her kare kendisi kurar, Camera2D'nin konum yumuşatması sönümler.
##  * İleri bakış: baktığın / koştuğun yöne yumuşak öncü kayma (saldırı sırasında donar ki vuruş anında ekran kaymasın).
##  * Dikey: yerdeyken ayaklar ekranın ~%69'unda (zemin ve yakındaki düşmanlar görünür); zıplamada kamera hemen
##    yükselmez (pencere), hızlı düşüşte aşağı bakar (iniş yeri görünür), yere inince yumuşakça yeniden oturur.
##  * İlgi: yakındaki uyanık düşman arkadaysa öncü kayma kısalır, kavga ekranda kalır.
##  * Boss arenası: boss ile oyuncu aynı karede kalsın diye yakınlık düşer (fit, en az MIN_FIT), merkez ikisinin arasına
##    kayar; boss'un boyu da sığar. Game._process taban yakınlığı + zoom_punch'ı yazar; bu düğüm (process_priority 100) aynısını fit ile çarparak yeniden yazar.

const LEAD := 58.0            # dünya birimi; 2,0 yakınlıkta yarım genişlik 240
const LEAD_VEL := 0.07        # hızla ek öncü (koşu/sprint)
const LEAD_RATE := 2.4        # öncü kaymanın üstel yaklaşma hızı (1/sn)
const FEET_UP := 50.0         # yerdeyken kamera merkezi ayakların bu kadar üstünde
const WIN_UP := 64.0          # zıplarken kamera bu yükseklikten sonra izler
const WIN_DOWN := 18.0
const FALL_LOOK := 54.0       # hızlı düşüşte aşağı bakış
const MIN_FIT := 0.62
const REF_ZOOM := 2.0         # yukarıdaki dünya birimi sabitlerinin yazıldığı taban yakınlık

var level: Node
var player: Node2D
## boss sığdırma çarpanı (1 = taban yakınlık); ParallaxBG/ForegroundV2 kaydırma hızını bununla ölçer
var fit := 1.0
var _lead := 0.0
var _anchor_y := 0.0
var _look_y := 0.0
var _boss_x := 0.0
var _ready_done := false
var _last_p := Vector2.ZERO


func _ready() -> void:
	process_priority = 100   # Game (autoload) yakınlığı yazdıktan sonra
	position_smoothing_enabled = true
	position_smoothing_speed = 6.0
	limit_smoothed = true
	process_mode = Node.PROCESS_MODE_ALWAYS


func snap() -> void:
	## Işınlanma / bölüm başı: öncü ve dikey çapa sıfırlanır, yumuşatma atlanır
	if player == null:
		return
	_anchor_y = player.global_position.y
	_lead = float(player.get("facing")) * LEAD * _zk()
	_look_y = 0.0
	global_position = _target()
	reset_smoothing()
	_ready_done = true


func _zk() -> float:
	## çerçeve ölçeği: daha uzak kamerada (küçük yakınlık) dünya birimi sabitleri aynı ekran oranına büyür
	return REF_ZOOM / maxf(0.5, Game.base_zoom)


func _target() -> Vector2:
	var p := player.global_position
	return Vector2(p.x + _lead, _anchor_y - FEET_UP * _zk() + _look_y)


func _process(delta: float) -> void:
	if Prof.on:
		var t0 := Time.get_ticks_usec()
		_process_ic(delta)
		Prof.ekle(&"kamera", t0)
		return
	_process_ic(delta)


func _process_ic(delta: float) -> void:
	if player == null or not is_instance_valid(player):
		return
	if not _ready_done or player.global_position.distance_to(_last_p) > 220.0:
		snap()   # ışınlanma (bölüm başı, test sahnesi, çukurdan dönüş)
	_last_p = player.global_position
	var rd := delta / maxf(0.05, Engine.time_scale)   # ağır çekim / vuruş donmasında kamera kendi hızında
	var p := player.global_position
	var vel: Vector2 = player.get("velocity") if player.get("velocity") != null else Vector2.ZERO
	var facing := float(player.get("facing")) if player.get("facing") != null else 1.0
	var on_floor: bool = player.is_on_floor() if player.has_method("is_on_floor") else true
	var attacking := false
	var atk = player.get("atk")
	if atk is Dictionary and not (atk as Dictionary).is_empty():
		attacking = true
	# --- yatay öncü
	var zk := _zk()
	var tl := (facing * LEAD + clampf(vel.x, -260.0, 260.0) * LEAD_VEL) * zk
	tl += _attention(p)
	if attacking:
		tl = _lead
	_lead = lerpf(_lead, tl, 1.0 - exp(-LEAD_RATE * rd))
	# --- dikey çapa: yerde ayaklara oturur; havada pencere dışına çıkınca izler
	if on_floor:
		_anchor_y = lerpf(_anchor_y, p.y, 1.0 - exp(-9.0 * rd))
	else:
		if p.y < _anchor_y - WIN_UP * zk:
			_anchor_y = p.y + WIN_UP * zk
		elif p.y > _anchor_y + WIN_DOWN * zk:
			_anchor_y = p.y - WIN_DOWN * zk
	var ly := 0.0
	if not on_floor and vel.y > 240.0:
		ly = clampf((vel.y - 240.0) / 260.0, 0.0, 1.0) * FALL_LOOK * zk
	_look_y = lerpf(_look_y, ly, 1.0 - exp(-(3.0 if ly > _look_y else 5.0) * rd))
	var t := _target()
	# --- boss: ikisi de karede kalsın
	var want_fit := 1.0
	var boss: Node2D = level.get("boss") if level != null else null
	if boss != null and is_instance_valid(boss) and not bool(boss.get("dead")):
		var vp := get_viewport().get_visible_rect().size
		var base := maxf(0.1, Game.base_zoom)
		var bsz: Vector2 = boss.get("size") if boss.get("size") is Vector2 else Vector2(48, 64)
		var bh := bsz.y * 1.5
		var banim = boss.get("anim")
		if banim is SpriteAnim:
			var cell: Array = (banim as SpriteAnim).meta.get("cell", [0, 0])
			bh = maxf(bh, float(cell[1]) / (banim as SpriteAnim).texel * 0.8)
		var dx := absf(boss.global_position.x - p.x) + bsz.x * 0.5 + 90.0
		var zx := vp.x / maxf(1.0, dx * 1.15)
		var zy := vp.y / maxf(1.0, bh + 120.0)
		var need := minf(zx, zy) / base
		# boss uzaktaysa (en geniş çerçeveye bile sığmıyorsa) normal yakın kamera; menzile girince yumuşakça açılır
		want_fit = clampf(need, MIN_FIT, 1.0) if need >= MIN_FIT * 0.8 else 1.0
		_boss_x = lerpf(_boss_x, boss.global_position.x, 1.0 - exp(-4.0 * rd))
		if fit < 0.999:
			# merkez oyuncu ile boss arasına (oyuncuya yakın) kayar; oyuncu ekranın iç yarısında kalır
			var k := clampf((1.0 - fit) / (1.0 - MIN_FIT), 0.0, 1.0)
			t.x = lerpf(t.x, (p.x + _boss_x) * 0.5, 0.8 * k)
			var half_w := vp.x * 0.5 / (base * fit)
			t.x = clampf(t.x, p.x - half_w * 0.5, p.x + half_w * 0.5)
			t.y -= (1.0 / fit - 1.0) * 40.0
	fit = lerpf(fit, want_fit, 1.0 - exp(-1.8 * rd))
	zoom = Vector2.ONE * Game.base_zoom * (1.0 + float(Game.get("_zoom"))) * fit
	global_position = t


func _attention(p: Vector2) -> float:
	## Yakındaki (arkadaki) en yakın uyanık düşman: öncü kaymayı ona doğru kısaltır
	var best := 9999.0
	var bdx := 0.0
	for e in get_tree().get_nodes_in_group("dusman"):
		var en := e as Node2D
		if en == null or bool(en.get("dead")):
			continue
		var d := en.global_position - p
		if absf(d.y) > 140.0:
			continue
		var ad := absf(d.x)
		if ad < best and ad < 230.0:
			best = ad
			bdx = d.x
	if best > 9000.0:
		return 0.0
	return clampf(bdx, -150.0, 150.0) * 0.32
