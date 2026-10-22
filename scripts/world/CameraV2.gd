class_name CameraV2
extends Camera2D
## Stil v2 (mürekkep) kamerası: yakın çekim (stil_v2.json "camera_zoom", biyoma göre 1,65-1,75; v19'a dek 2,0: Bengü
## 1080p'de ~195 px, ekranın ~%18'i). v1 kamerası (oyuncunun çocuğu, Player._look_ahead) hiç değişmez.
## Çerçeve sabitleri 2,0 yakınlık için yazıldı (REF_ZOOM); taban yakınlık farklıysa öncü kayma, ayak yüksekliği,
## zıplama penceresi ve düşüş bakışı aynı EKRAN oranında kalsın diye REF_ZOOM / taban ile ölçeklenir.
##
## Oyuncunun çocuğu DEĞİL (Level'ın çocuğu): hedefi her kare kendisi kurar, Camera2D'nin konum yumuşatması sönümler.
##  * İleri bakış: baktığın / koştuğun yöne yumuşak öncü kayma (saldırı sırasında donar ki vuruş anında ekran kaymasın).
##    v40: üstel yaklaşma yerine kritik sönümlü yay (SmoothDamp): dönüşte öncü sıçramaz, yavaşça savrulur.
##  * Dikey: yerdeyken ayaklar ekranın ~%69'unda (zemin ve yakındaki düşmanlar görünür); zıplamada kamera hemen
##    yükselmez (pencere), hızlı düşüşte aşağı bakar (iniş yeri görünür), yere inince yumuşakça yeniden oturur.
##    v40: sert inişte kısa bir çöküş (landing dip: düşüş hızıyla 2-7 birim, 0,25 sn'de toparlanır).
##  * İlgi: yakındaki uyanık düşman arkadaysa öncü kayma kısalır, kavga ekranda kalır.
##  * v40 boşta nefes: oyuncu ~1,5 sn kıpırdamayınca kamera çok yavaş, belli belirsiz süzülür (el kamerası değil,
##    "canlı" çerçeve); ilk harekette söner.
##  * Boss arenası: boss ile oyuncu aynı karede kalsın diye yakınlık düşer (fit, en az MIN_FIT), merkez ikisinin arasına
##    kayar; boss'un boyu da sığar. Game._process taban yakınlığı + zoom_punch'ı yazar; bu düğüm (process_priority 100) aynısını fit ile çarparak yeniden yazar.
##    v40 boss girişi (boss_intro): arena kurulunca kamera 2,2 sn boyunca kükreyen boss'a doğru süzülür, geniş açılır,
##    oyuncuya döner (tanıtım çekimi). Oyuncu bu sırada oynayabilir.
##  * v40 ölüm (olum): yavaşça yaklaşır (1,10x), öncü kayma söner; duraklatmada da sürer.

const LEAD := 58.0            # dünya birimi; 2,0 yakınlıkta yarım genişlik 240
const LEAD_VEL := 0.07        # hızla ek öncü (koşu/sprint)
const LEAD_SMOOTH := 0.42     # v40: öncü kaymanın yay yumuşatma süresi (sn; SmoothDamp)
const FEET_UP := 50.0         # yerdeyken kamera merkezi ayakların bu kadar üstünde
const WIN_UP := 64.0          # zıplarken kamera bu yükseklikten sonra izler
const WIN_DOWN := 18.0
const FALL_LOOK := 54.0       # hızlı düşüşte aşağı bakış
const MIN_FIT := 0.62
const REF_ZOOM := 2.0         # yukarıdaki dünya birimi sabitlerinin yazıldığı taban yakınlık
const IDLE_WAIT := 1.4        # v40: bu kadar hareketsizlikten sonra nefes başlar
const IDLE_AMP := Vector2(2.4, 1.5)   # v40: nefes genliği (dünya birimi, 2,0 yakınlıkta)
const DIP_MAX := 7.0          # v40: iniş çöküşü üst sınırı (dünya birimi)
const INTRO_T := 2.2          # v40: boss tanıtım süresi (sn)

var level: Node
var player: Node2D
## boss sığdırma çarpanı (1 = taban yakınlık); ParallaxBG/ForegroundV2 kaydırma hızını bununla ölçer
var fit := 1.0
var _lead := 0.0
var _lead_v := 0.0
var _anchor_y := 0.0
var _look_y := 0.0
var _boss_x := 0.0
var _ready_done := false
var _last_p := Vector2.ZERO
var _idle_t := 0.0
var _idle_k := 0.0
var _breath_t := 0.0
var _dip := 0.0
var _was_floor := true
var _last_vy := 0.0
var _intro_t := 0.0
var _olum_k := 0.0
var _olum := false


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
	_lead_v = 0.0
	_look_y = 0.0
	_dip = 0.0
	_idle_t = 0.0
	_idle_k = 0.0
	global_position = _target()
	reset_smoothing()
	_ready_done = true


func boss_intro() -> void:
	## v40: arena başı tanıtım çekimi (bkz. sınıf notu)
	_intro_t = INTRO_T


func olum() -> void:
	## v40: ölüm kamerası (yavaş yaklaşma; Level.on_player_died çağırır)
	_olum = true


func _zk() -> float:
	## çerçeve ölçeği: daha uzak kamerada (küçük yakınlık) dünya birimi sabitleri aynı ekran oranına büyür
	return REF_ZOOM / maxf(0.5, Game.base_zoom)


func _target() -> Vector2:
	var p := player.global_position
	return Vector2(p.x + _lead, _anchor_y - FEET_UP * _zk() + _look_y + _dip)


static func _smooth_damp(cur: float, target: float, vel: Array, smooth: float, dt: float) -> float:
	## Kritik sönümlü yay (Unity SmoothDamp): sıçramasız, aşmasız yaklaşma; vel[0] hız durumu
	var omega := 2.0 / maxf(0.0001, smooth)
	var x := omega * dt
	var e := 1.0 / (1.0 + x + 0.48 * x * x + 0.235 * x * x * x)
	var ch := cur - target
	var tmp := (float(vel[0]) + omega * ch) * dt
	vel[0] = (float(vel[0]) - omega * tmp) * e
	return target + (ch + tmp) * e


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
	# --- yatay öncü (v40: kritik sönümlü yay)
	var zk := _zk()
	var tl := (facing * LEAD + clampf(vel.x, -260.0, 260.0) * LEAD_VEL) * zk
	tl += _attention(p)
	if attacking:
		tl = _lead
	if _olum:
		tl = 0.0
	var lv := [_lead_v]
	_lead = _smooth_damp(_lead, tl, lv, LEAD_SMOOTH if not attacking else 0.12, rd)
	_lead_v = float(lv[0])
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
	# --- v40 iniş çöküşü: hızlı düşüşten yere değince kamera kısa bir an aşağı çöker, yumuşakça toparlanır
	if on_floor and not _was_floor and _last_vy > 260.0:
		_dip = clampf((_last_vy - 260.0) / 420.0, 0.0, 1.0) * DIP_MAX * zk * (0.5 + 0.5 * Game.fx_scale)
	_dip = lerpf(_dip, 0.0, 1.0 - exp(-8.0 * rd))
	_was_floor = on_floor
	_last_vy = vel.y
	# --- v40 boşta nefes
	var still := on_floor and vel.length() < 6.0 and not attacking and _intro_t <= 0.0
	_idle_t = (_idle_t + rd) if still else 0.0
	var want_k := clampf((_idle_t - IDLE_WAIT) / 1.6, 0.0, 1.0)
	_idle_k = lerpf(_idle_k, want_k, 1.0 - exp(-(1.2 if want_k > _idle_k else 4.0) * rd))
	_breath_t += rd
	var t := _target()
	if _idle_k > 0.001:
		t += Vector2(sin(_breath_t * 0.46) * IDLE_AMP.x, sin(_breath_t * 0.31 + 1.2) * IDLE_AMP.y) * zk * _idle_k
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
		if _intro_t > 0.0:
			# v40 tanıtım: kamera boss'a doğru süzülür (yarıya dek), geniş açılır, sonra oyuncuya döner
			_intro_t -= rd
			var u := 1.0 - clampf(_intro_t / INTRO_T, 0.0, 1.0)
			var k := sin(u * PI)   # 0 → 1 → 0 (yumuşak gidiş-dönüş)
			k = k * k * (3.0 - 2.0 * k)
			var half_w0 := vp.x * 0.5 / base
			var bx := clampf(boss.global_position.x, p.x - half_w0 * 1.6, p.x + half_w0 * 1.6)
			t.x = lerpf(t.x, lerpf(p.x, bx, 0.62), k)
			t.y -= k * 26.0 * zk
			want_fit = minf(want_fit, lerpf(1.0, 0.8, k))
		elif fit < 0.999:
			# merkez oyuncu ile boss arasına (oyuncuya yakın) kayar; oyuncu ekranın iç yarısında kalır
			var k := clampf((1.0 - fit) / (1.0 - MIN_FIT), 0.0, 1.0)
			t.x = lerpf(t.x, (p.x + _boss_x) * 0.5, 0.8 * k)
			var half_w := vp.x * 0.5 / (base * fit)
			t.x = clampf(t.x, p.x - half_w * 0.5, p.x + half_w * 0.5)
			t.y -= (1.0 / fit - 1.0) * 40.0
	else:
		_intro_t = 0.0
	fit = lerpf(fit, want_fit, 1.0 - exp(-(2.6 if _intro_t > 0.0 else 1.8) * rd))
	# --- v40 ölüm: yavaş yaklaşma (1,10x; 2 sn), duraklatmada da sürer
	if _olum:
		_olum_k = lerpf(_olum_k, 1.0, 1.0 - exp(-0.9 * rd))
	zoom = Vector2.ONE * Game.base_zoom * (1.0 + float(Game.get("_zoom"))) * fit * (1.0 + 0.1 * _olum_k)
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
