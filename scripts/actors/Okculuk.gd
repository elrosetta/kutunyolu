class_name Okculuk
extends RefCounted
## v19 Okçuluk: Dead Cells esinli uzak dövüş (yay). Player.gd yalnızca girdi noktalarından çağırır; durum burada.
##
## His (Dead Cells yayları: Quick Bow, Multiple-nocks, Marksman's Bow, Nerves of Steel, Heavy Crossbow):
##   * dokunuş = ok: tuşa basıp hemen bırakmak da atar (en kısa gerilme "min" dolunca); seri basış seri atış
##   * basılı tut: çabuk yay (Akıncı) kendiliğinden yineleyerek atar; gerilen yaylar dolup bırakılmayı bekler
##   * oklar çok hızlı (650-1100 px/sn, neredeyse anında), yalnızca ağır / yarım gerilmiş oklar hafifçe düşer
##   * dikey hedef yardımı: öndeki en yakın düşmana ±26° içinde kendiliğinden nişan (yerçekimi düşüşü hesaba katılır)
##   * gerilirken yürünür (yaya göre %40-85 hız), havada atılır; yuvarlanma gerilmeyi keser, bekleme kısa
##   * yakın dövüş basışı gerilmeyi keser: yeterince gerildiyse ok o anda çıkar ("çabuk atış"), saldırı aynı karede
##   * saldırının toparlanmasında yay basışı saldırıyı keser (FLOW.buf_sec); bekleme sırasındaki basış kaybolmaz
## Yeni mekanikler:
##   TAM BIRAKIŞ   gerilen yaylarda yay dolduğu an açılan dar pencere (0,1 sn): o anda bırakılan ok kesin kritik,
##                 +1 delme, hızlı; yay ucunda daralan halka pencereyi önceden haber verir, dolunca parıltı
##   OK SÖKME      isabet eden son ok düşmana saplı kalır (en çok 5, 6 sn). Saplı oku olan düşmana yakın dövüş
##                 vuruşu okları söker: ok başına +%30 hasar, kanama, 3+ okta kesin kritik, yay beklemesi sıfırlanır
##                 ve bir "hazır ok" kazanılır
##   OK TOPLAMA    ıskalanan oklar duvara / zemine saplanır (6 sn), ölen düşmandaki saplı oklar yere dökülür;
##                 üstünden geçince toplanır: "hazır ok" (en çok 3) — sıradaki atış anında dolu ve tam bırakış sayılır
##   KARTAL SÜZÜLÜŞÜ  havada gerilirken düşüş yavaşlar (hava başına 0,55 sn); havadaki ilk atış küçük bir sıçrama verir
##   CEPHANE (v25, Dead Cells'in sınırlı oklu yayları)  tek oklu yaylar (Türk, Akıncı) sınırsız ama biraz yavaş; çok
##                 oklu / alevli yaylar (Sağanak, Tufan, Od Okları) "ammo" atış hakkıyla: atış başına bir hak, atış
##                 yokken kendiliğinden dolar, yerden toplanan / sökülen ok anında bir hak; boşken kuru tık + ipucu

## Yay profilleri (sn, px/sn, rad). [a, b] çiftleri: [en kısa bırakış, tam gerilme] arasında doğrusal.
##   draw tam gerilme · min en kısa bırakış · rec atış sonrası kilit · auto basılı tutunca kendiliğinden yineler
##   spd hız · grav yerçekimi · move gerilirken yürüme oranı · spread yelpaze yarı açısı · kb itme · dmg hasar çarpanı
##   perfect tam bırakış penceresi (0: yok) · close bu uzaklığın altında "dipten" kesin kritik (0: yok)
##   recoil atışta geri tepme (px/sn) · var ok sprite türü · pal isabet mürekkep paleti · core iz çekirdek rengi
##   ammo v25 [atış hakkı, bir hakkın dolma süresi sn] ([0, 0]: sınırsız)
const PROF := {
	# Kemankeş yayı (Marksman's Bow + Nerves of Steel): gerilen, delen, tam bırakışla kritik
	"turk_yayi": {"draw": 0.52, "min": 0.06, "rec": 0.2, "auto": false, "spd": [640.0, 1100.0], "grav": [420.0, 0.0],
		"move": 0.6, "spread": [0.0, 0.0], "kb": [50.0, 120.0], "dmg": [0.45, 1.0], "perfect": 0.11, "close": 0.0,
		"recoil": 0.0, "var": "normal", "pal": 9, "core": Color(1.0, 0.92, 0.74), "ammo": [0, 0.0]},
	# Çabuk yay (Quick Bow): basılı tut = seri atış (v25: ~3,4 ok/sn), yuvarlanırken atar, geri çekilirken kritik
	"akinci_yayi": {"draw": 0.16, "min": 0.05, "rec": 0.11, "auto": true, "spd": [980.0, 1050.0], "grav": [0.0, 0.0],
		"move": 0.85, "spread": [0.0, 0.0], "kb": [35.0, 45.0], "dmg": [0.5, 0.55], "perfect": 0.0, "close": 0.0,
		"recoil": 0.0, "var": "kizil", "pal": 0, "core": Color(1.0, 0.45, 0.35), "ammo": [0, 0.0]},
	# Çok gezli yay (Multiple-nocks): yelpaze; gerildikçe yelpaze daralır; dipten (80 px) kritik
	"saganak_yayi": {"draw": 0.3, "min": 0.08, "rec": 0.2, "auto": false, "spd": [720.0, 960.0], "grav": [260.0, 60.0],
		"move": 0.6, "spread": [0.34, 0.12], "kb": [50.0, 80.0], "dmg": [0.45, 0.65], "perfect": 0.1, "close": 80.0,
		"recoil": 40.0, "var": "sel", "pal": 2, "core": Color(0.62, 0.88, 1.0), "ammo": [8, 1.5]},
	# Od okları: alev bırakan oklar; yanan düşmana kritik
	"od_oklari": {"draw": 0.32, "min": 0.08, "rec": 0.18, "auto": false, "spd": [700.0, 940.0], "grav": [300.0, 60.0],
		"move": 0.65, "spread": [0.0, 0.0], "kb": [50.0, 80.0], "dmg": [0.55, 1.0], "perfect": 0.1, "close": 0.0,
		"recoil": 0.0, "var": "od", "pal": 1, "core": Color(1.0, 0.68, 0.3), "ammo": [10, 1.2]},
	# Ağır yelpaze (Heavy Crossbow): geniş saçma, büyük itme, geri tepme; dipten (90 px) kritik
	"tufan_yayi": {"draw": 0.5, "min": 0.13, "rec": 0.32, "auto": false, "spd": [680.0, 900.0], "grav": [300.0, 140.0],
		"move": 0.4, "spread": [0.42, 0.2], "kb": [120.0, 200.0], "dmg": [0.4, 0.6], "perfect": 0.1, "close": 90.0,
		"recoil": 130.0, "var": "sel", "pal": 2, "core": Color(0.55, 0.95, 1.0), "ammo": [6, 2.0]},
}

const WANT_T := 0.2           # bekleme / yuvarlanma sırasında yapılan basış bu kadar saklanır (v22: 0,45 → 0,2)
const STUCK_MAX := 5
const STUCK_LIFE := 6.0
const HAZIR_MAX := 3
const HOVER_T := 0.55
const HOVER_VY := 50.0
const AIM_RANGE := 380.0
const AIM_CONE := 0.46
const AMMO_WAIT := 0.45       # v25: atıştan sonra cephane dolumu bu kadar bekler (gerilirken de durur)
const KURU_IPUCU := 2.5       # boş tık ipucu yazısı en sık bu kadar sn'de bir

var p: Player
var hazir := 0                   # hazır ok (toplanan / sökülen): sıradaki atış anında dolu + tam bırakış
var _want := false               # bekleyen yay basışı
var _want_t := 0.0
var _released := false           # bu gerilmede tuş bırakıldı mı (dokunuş: en kısa gerilmede atılır)
var _fresh := true               # gerilme yeni basışla mı başladı (otomatik yinelemede yön değişmez)
var _full_fx := false
var _ring_fx := false
var _perfect_armed := false      # hazır ok: bu gerilme tam bırakış sayılır
var _hover := HOVER_T
var _air_pop := true
var _stuck: Dictionary = {}      # örnek kimliği -> {e, n, t, spr: [], pos}
var _pips: Node2D
var tilt := 0.0                  # görsel nişan eğimi (rad, + aşağı): kol, yay ve yaydaki ok hedefe döner
## v25 cephane (çok oklu yaylar): HUD yuvanın altında mürekkep ok imleri çizer (ammo / ammo_max, ammo_k dolum)
var ammo := 0
var ammo_max := 0
var ammo_pop := 0.0              # HUD: hak kazanınca / boş tıkta imler kısa süre sıçrar
var ammo_bos := 0.0              # HUD: boş tıkta imler kızarır
var _ammo_key := ""              # cephanesi tutulan yay (başka yay kuşanınca dolu başlar)
var _ammo_regen := 0.0
var _ammo_wait := 0.0
var _kuru_t := -99.0
## test / ölçüm (tools/tests/yay_testi.gd)
var stats := {"fire": 0, "perfect": 0, "sokme": 0, "toplama": 0, "saplanma": 0, "isabet": 0, "dokunus": 0, "cabuk": 0,
	"last_fire_t": -1.0, "last_hit_t": -1.0, "last_charge": 0.0, "suzulus": 0.0, "kuru": 0, "dolum": 0}


func _init(player: Player) -> void:
	p = player


## v20 saldırı hızı: Player._hiz_tick her kare yazar (1 = taban). Gerilme, en kısa bırakış ve atış kilidi bununla
## çarpılır (Player.HIZ.yay oranında); tam bırakış penceresi aynı kalır (beceri penceresi kısalmasın).
static var hiz_k := 1.0
static var _hiz_cache: Dictionary = {}


static func prof(it: Dictionary) -> Dictionary:
	var pr: Dictionary = PROF.get(String(it.get("id", "")), PROF["turk_yayi"])
	if absf(hiz_k - 1.0) < 0.001:
		return pr
	var key := "%s|%.3f" % [String(it.get("id", "")), hiz_k]
	if not _hiz_cache.has(key):
		if _hiz_cache.size() > 64:
			_hiz_cache.clear()
		var q := pr.duplicate()
		q["draw"] = maxf(0.05, float(pr["draw"]) * hiz_k)
		q["min"] = maxf(0.033, float(pr["min"]) * hiz_k) if float(pr["min"]) > 0.033 else float(pr["min"])
		q["rec"] = maxf(0.05, float(pr["rec"]) * hiz_k)
		_hiz_cache[key] = q
	return _hiz_cache[key]


static func ammo_of(it: Dictionary) -> int:
	## v25: yayın atış hakkı (0: sınırsız)
	if it.get("kind", "") != "bow":
		return 0
	return int((PROF.get(String(it.get("id", "")), PROF["turk_yayi"]) as Dictionary).get("ammo", [0, 0.0])[0])


static func ammo_regen_of(it: Dictionary) -> float:
	return float((PROF.get(String(it.get("id", "")), PROF["turk_yayi"]) as Dictionary).get("ammo", [0, 0.0])[1])


static func kart_tur(it: Dictionary) -> float:
	## v25 kart: tam güçte (kritiksiz: tam bırakış penceresinden sonra) bir atış turu, sn
	var pr := prof(it)
	return float(pr["draw"]) + float(pr["perfect"]) + float(pr["rec"]) + 2.0 / 60.0


static func kart_hiz(it: Dictionary) -> float:
	## v25 kart SnH: saniyede taban hasarın kaç katı (ok sayısı x tam gerilme çarpanı x yelpaze payı / tur). Cephaneli
	## yayda bu patlama (dolu cephane) değeridir; sürekli atışta dolum hızı sınırlar
	var pr := prof(it)
	var mech := String(it.get("mech_id", ""))
	var n := int(it.get("mech_v", 3)) if mech == "yelpaze" else 1
	var k := float(pr["dmg"][1]) * (0.85 if n > 1 else 1.0) * float(n)
	if mech == "part_atisi":
		k *= 1.0 + float(it.get("mech_v", 0.0)) / 100.0
	return k / kart_tur(it)


func _ammo_sync() -> void:
	var it := _bow()
	var key := "" if it.is_empty() else "%s|%s|%.2f" % [String(it.get("id", "")), String(it.get("name", "")), float(it.get("dmg", 0.0))]
	if key == _ammo_key:
		return
	_ammo_key = key
	ammo_max = ammo_of(it) if not it.is_empty() else 0
	ammo = ammo_max
	_ammo_regen = 0.0
	_ammo_wait = 0.0


func ammo_fill() -> void:
	_ammo_sync()
	ammo = ammo_max


func ammo_k() -> float:
	## HUD: sıradaki hakkın dolum oranı (0..1)
	var it := _bow()
	if ammo_max <= 0 or ammo >= ammo_max or it.is_empty():
		return 0.0
	return clampf(_ammo_regen / maxf(0.05, ammo_regen_of(it)), 0.0, 1.0)


func ammo_add(n: int) -> void:
	_ammo_sync()
	if ammo_max <= 0 or n <= 0:
		return
	ammo = mini(ammo_max, ammo + n)
	ammo_pop = 0.22


func _ammo_tick(delta: float) -> void:
	_ammo_sync()
	ammo_pop = maxf(0.0, ammo_pop - delta)
	ammo_bos = maxf(0.0, ammo_bos - delta)
	if ammo_max <= 0 or ammo >= ammo_max:
		_ammo_regen = 0.0
		return
	if p.aim_t >= 0.0:
		return
	_ammo_wait -= delta
	if _ammo_wait > 0.0:
		return
	_ammo_regen += delta
	var rt := ammo_regen_of(_bow())
	if rt > 0.0 and _ammo_regen >= rt:
		_ammo_regen -= rt
		ammo = mini(ammo_max, ammo + 1)
		ammo_pop = 0.18
		stats["dolum"] = int(stats["dolum"]) + 1
		if ammo >= ammo_max:
			Ses.play("yay_ger", -16.0, 1.5, 0.04, 0.05)


func _kuru(it: Dictionary) -> void:
	## Boş tık: cephane bitti — kiriş boşa çarpar, imler kızarır; ipucu yazısı seyrek
	_want = false
	p.sec_buf = 0.0
	p.cd[p.sec_slot] = 0.22
	p.cd_max[p.sec_slot] = 0.22
	stats["kuru"] = int(stats["kuru"]) + 1
	ammo_bos = 0.35
	ammo_pop = 0.2
	Ses.play("yay_birak", -13.0, 1.9, 0.05, 0.05)
	Ses.play("ui_iptal", -14.0, 1.5, 0.05, 0.05)
	p.vis_scale = Vector2(0.97, 1.02)
	var now := Game.clock()
	if now - _kuru_t >= KURU_IPUCU:
		_kuru_t = now
		var rt := ammo_regen_of(it)
		FX.text(p.center() + Vector2(0, -44), "ok bitti · yerdeki okları topla", Color(1.0, 0.62, 0.5), 7)
		if rt > 0.0:
			FX.text(p.center() + Vector2(0, -34), "atmazsan %s sn'de bir ok dolar" % ItemGen.fmt(rt), Color(0.85, 0.8, 0.72), 6)


func _bow() -> Dictionary:
	var it := p.slot(p.sec_slot)
	return it if it.get("kind", "") == "bow" else {}


func draw_time() -> float:
	var it := _bow()
	return float(prof(it)["draw"]) if not it.is_empty() else 0.4


func pull() -> float:
	## 0..1 gerilme (görsel ve hasar)
	if p.aim_t < 0.0:
		return 0.0
	return clampf(p.aim_t / draw_time(), 0.0, 1.0)


func in_perfect() -> bool:
	## tam bırakış penceresi açık mı (yay ucunda parıltı)
	var it := _bow()
	if it.is_empty() or p.aim_t < 0.0:
		return false
	var pr := prof(it)
	var w := float(pr["perfect"])
	if w <= 0.0:
		return false
	var d := float(pr["draw"])
	return p.aim_t >= d - 0.017 and p.aim_t <= d + w


func ring_k() -> float:
	## tam bırakış halkası: dolmadan önceki son 0,18 sn'de 1 -> 0 daralır; yoksa -1
	var it := _bow()
	if it.is_empty() or p.aim_t < 0.0 or float(prof(it)["perfect"]) <= 0.0:
		return -1.0
	var d := float(prof(it)["draw"])
	var lead := minf(0.18, d * 0.6)
	if p.aim_t < d - lead or p.aim_t >= d:
		return -1.0
	return (d - p.aim_t) / lead


func move_k() -> float:
	var it := _bow()
	return float(prof(it)["move"]) if not it.is_empty() else 0.3


# ------------------------------------------------------------------ her kare (Player._physics_process başı)
func process(delta: float) -> void:
	if p.roll_t <= 0.0:
		_want_t -= delta   # v22: yuvarlanırken basış erimez (yuvarlanma biter bitmez ok; kısalan WANT_T yetişmiyordu)
	if _want_t <= 0.0:
		_want = false
	if p.is_on_floor():
		_hover = HOVER_T
		_air_pop = true
	var it := _bow()
	# v25: gerilme sürerken aynı basış yeniden sayılmaz (çabuk yayda tek dokunuş iki ok atıyordu)
	if not it.is_empty() and p.sec_act != "" and Input.is_action_just_pressed(p.sec_act) and p.aim_t < 0.0:
		_want = true
		_want_t = WANT_T
		# vuruş anında / ağır savuruşta basıldıysa: toparlanma başlayınca saldırıyı kessin (ara bellek erimesin)
		if not p.atk.is_empty():
			p.sec_buf = maxf(p.sec_buf, float(Player.FLOW["buf_sec"]))
	if not p.atk.is_empty() and p.atk.get("phase", "") == "rec" and _want and p.melee_buf <= 0.0:
		p.sec_buf = maxf(p.sec_buf, 0.05)
	# görsel nişan: gerilirken hedef yardımının açısına yumuşakça döner
	var want_tilt := 0.0
	if p.aim_t >= 0.0 and not it.is_empty():
		var pr := prof(it)
		var k := pull()
		var o := p.center() + Vector2(p.facing * 10, -9)
		want_tilt = _aim_angle(o, lerpf(float(pr["spd"][0]), float(pr["spd"][1]), k), lerpf(float(pr["grav"][0]), float(pr["grav"][1]), k))
	tilt = lerpf(tilt, clampf(want_tilt, -0.42, 0.42), 1.0 - exp(-22.0 * delta))
	_stuck_tick(delta)
	_ammo_tick(delta)
	_pips_tick()


# ------------------------------------------------------------------ girdi (saldırı yokken; Player'ın eski yay bloğu)
func tick(delta: float, it: Dictionary, sec_press: bool) -> void:
	var pr := prof(it)
	var held: bool = p.sec_act != "" and Input.is_action_pressed(p.sec_act)
	if sec_press:
		p.sec_buf = 0.0
		if p.aim_t < 0.0:
			_want = true
			_want_t = WANT_T
	if p.aim_t < 0.0:
		var auto_go: bool = bool(pr["auto"]) and held and not _fresh_needed()
		if (_want or auto_go) and p.cd[p.sec_slot] <= 0.0:
			_ammo_sync()
			if ammo_max > 0 and ammo <= 0 and hazir <= 0:
				_kuru(it)   # v25: cephane bitti (hazır ok — yerden toplanan — yine atılır)
				return
			_begin(it, pr, _want)
		else:
			return
	else:
		p.aim_t += delta
	if not held:
		_released = true
	var d := float(pr["draw"])
	# dolma anı: ses, parıltı, gövde flaşı (tam bırakış penceresi açılır)
	if p.aim_t >= d and not _full_fx:
		_full_fx = true
		if not bool(pr["auto"]):
			Ses.play("yay_dolu", -7.0 if float(pr["perfect"]) > 0.0 else -9.0, 1.08)
			p.anim.set_flash(0.3)
			p.get_tree().create_timer(0.045).timeout.connect(func() -> void:
				if is_instance_valid(p):
					p.anim.set_flash(0.0))
			_glint(it)
	# havada gerilme: Kartal Süzülüşü
	if not p.is_on_floor() and _hover > 0.0 and p.velocity.y > HOVER_VY:
		_hover -= delta
		stats["suzulus"] = float(stats["suzulus"]) + delta
		p.velocity.y = HOVER_VY
	elif not p.is_on_floor() and _hover > 0.0 and p.velocity.y > -40.0:
		_hover -= delta * 0.5
		p.velocity.y = minf(p.velocity.y, HOVER_VY)
	# atış
	var mn := float(pr["min"])
	if bool(pr["auto"]):
		if p.aim_t >= d or (_released and p.aim_t >= mn):
			fire(clampf(p.aim_t / d, 0.0, 1.0))
	elif _released and p.aim_t >= mn:
		fire(clampf(p.aim_t / d, 0.0, 1.0))


func _fresh_needed() -> bool:
	## otomatik yineleme yalnızca yayın kendi basışıyla başlayan seride (saldırı / yuvarlanma sonrası yeni basış ister)
	return _fresh


func _begin(it: Dictionary, pr: Dictionary, pressed: bool) -> void:
	var held: bool = p.sec_act != "" and Input.is_action_pressed(p.sec_act)
	_want = false
	_released = not held
	_full_fx = false
	_perfect_armed = false
	if pressed:
		_fresh = false
		var dir := Input.get_axis("sol", "sag")
		if dir != 0.0:
			p.facing = int(signf(dir))
		# v22: önde kimse yokken arkadakine kendiliğinden dönme kalktı (oyuncu kendisi döner); dikey nişan yardımı sürer
	p.aim_t = 0.0
	if hazir > 0:
		hazir -= 1
		_perfect_armed = true
		p.aim_t = float(pr["draw"]) - 0.016 if float(pr["perfect"]) > 0.0 else float(pr["draw"])
		Ses.play("yay_ger", -6.0, 1.25)
	else:
		Ses.play("yay_ger", -9.0 if bool(pr["auto"]) else -7.0, 1.2 if bool(pr["auto"]) else 1.0, 0.08)
	p.anim.set_facing(p.facing)


func _valid_target(e: Node) -> bool:
	if not is_instance_valid(e) or e.dead:
		return false
	if "_hidden" in e and e._hidden:
		return false
	return true


# ------------------------------------------------------------------ kesişmeler
func melee_interrupt() -> void:
	## Gerilirken yakın dövüş basışı: gerilme bırakılır, saldırı ara bellekten aynı karede başlar (girdi kaybı yok).
	## v22: "çabuk atış" kalktı — saldırı tuşu oku kendiliğinden fırlatmaz (ok yalnızca yay tuşu bırakılınca çıkar).
	if p.aim_t < 0.0:
		return
	p.aim_t = -1.0
	_want = false
	_fresh = true


func roll_tick() -> void:
	## Yuvarlanırken: Akıncı Yayı (part atışı) yuvarlanmadan ok atar; diğerlerinde basış yuvarlanma bitince çıkar
	var it := _bow()
	if it.is_empty() or p.sec_act == "":
		return
	_fresh = true
	if Input.is_action_just_pressed(p.sec_act) and it.get("mech_id", "") == "part_atisi" and p.cd[p.sec_slot] <= 0.0:
		_want = false
		p.sec_buf = 0.0
		fire(0.8)


# ------------------------------------------------------------------ atış
func fire(charge: float) -> void:
	var it := _bow()
	if it.is_empty() or p.level == null:
		p.aim_t = -1.0
		return
	var pr := prof(it)
	var mech: String = it.get("mech_id", "")
	var perfect := _perfect_armed or (float(pr["perfect"]) > 0.0 and in_perfect())
	_perfect_armed = false
	if perfect:
		charge = 1.0
	var full := charge >= 0.98
	var on_beat := p._usul_press()
	# v25 cephane: atış başına bir hak (cephane bitmişken hazır okla atılan ok bedava)
	_ammo_sync()
	if ammo_max > 0:
		ammo = maxi(0, ammo - 1)
		_ammo_wait = AMMO_WAIT
	var uns := "altin" if perfect else Unsur.of(it)
	if uns == "" and mech == "alev_oku":
		uns = "od"
	var n := int(it.get("mech_v", 3)) if mech == "yelpaze" else 1
	var spread := lerpf(float(pr["spread"][0]), float(pr["spread"][1]), charge)
	var spd := lerpf(float(pr["spd"][0]), float(pr["spd"][1]), charge) * (1.1 if perfect else 1.0)
	var grav := lerpf(float(pr["grav"][0]), float(pr["grav"][1]), charge)
	var kb := lerpf(float(pr["kb"][0]), float(pr["kb"][1]), charge)
	var dmg_k := lerpf(float(pr["dmg"][0]), float(pr["dmg"][1]), charge)
	var origin := p.arm_root.to_global(p._bow_nock + Vector2(p.facing * 12, 0)) if p._bow_nock_ok else p.global_position + Vector2(p.facing * 10, -30)
	if not p.level.solid_at(origin) and p.level.solid_at(origin + Vector2(p.facing * 4, 0)):
		origin.x -= p.facing * 6.0
	var aim := _aim_angle(origin, spd, grav)
	var pierce := 0
	if mech == "kemankes" and full:
		pierce = int(it.get("mech_v", 1))
	elif mech == "yelpaze" and full:
		pierce = 1
	if perfect:
		pierce += 1
	if Adlar.earned("bamsi_beyrek"):
		pierce += 1
	var close := float(pr["close"])
	var src := p.center()
	var face := p.facing
	var shot := {"dipten": false}   # atış başına ortak: yelpazede "dipten!" yazısı bir kez
	for i in n:
		var o := Ok.new()
		o.team = "p"
		o.okc = self
		o.position = origin
		var a := aim
		if n > 1:
			a += lerpf(-spread, spread, float(i) / float(n - 1))
		o.velocity = Vector2(cos(a) * float(face), sin(a)) * spd
		o.gravity = grav
		o.pierce = pierce
		o.life = 1.6
		o.arrow_variant = "altin" if perfect else String(pr["var"])
		o.fx_kind = "od" if mech == "alev_oku" else ("altin" if perfect else "")
		o.trail_col = Color(1, 1, 1, 0.9)
		o.unsur = uns
		o.iz_w = 0.5 if perfect else (0.42 if full else 0.34)   # v25: çok ince iz (1080p'de ~2,3-3,4 px)
		o.ink_pal = 9 if perfect else int(pr["pal"])
		o.big = perfect or kb >= 150.0
		var arrow_dmg := float(it["dmg"]) * dmg_k * (0.85 if n > 1 else 1.0)
		o.on_hit = func(e: Node) -> Dictionary:
			return _arrow_hit(e, it, arrow_dmg, kb, face, perfect, on_beat, close, src, o, shot)
		p.level.add_projectile(o)
	if mech == "alev_oku":
		FX.fire(origin, 3, 0.26)
	# geri bildirim
	p.cd[p.sec_slot] = float(pr["rec"])
	p.cd_max[p.sec_slot] = maxf(0.05, float(pr["rec"]) + float(pr["draw"]))
	p.vis_scale = Vector2(0.94, 1.04) if kb < 150.0 else Vector2(0.88, 1.08)
	p.bow_rel_t = Player.BOW_REL
	SanatAnim.kiris(p, it)   # v27: kiriş şaklaması
	p.aim_t = -1.0
	_full_fx = false
	var heavy_bow := float(pr["recoil"]) >= 100.0
	Ses.play("yay_birak_tam" if ((full and not bool(pr["auto"])) or perfect) else "yay_birak", -3.0 if not heavy_bow else -1.0, (0.9 if heavy_bow else 1.0) + 0.1 * charge + (0.12 if bool(pr["auto"]) else 0.0), 0.06, 0.02)
	Ses.play("ok_ucus", -12.0, 0.9 + 0.25 * charge, 0.08, 0.03, p.center())
	if float(pr["recoil"]) > 0.0:
		p.velocity.x -= float(face) * float(pr["recoil"]) * (0.5 + 0.5 * charge)
		Game.kick(Vector2(-face, 0), 2.0 + 2.0 * charge)
	if not p.is_on_floor() and _air_pop:
		_air_pop = false
		p.velocity.y = minf(p.velocity.y, -70.0)
	_muzzle_fx(origin, Vector2(cos(aim) * float(face), sin(aim)), int(pr["pal"]), charge, perfect, n)
	if perfect:
		_perfect_fx(origin, face)
	elif full and not bool(pr["auto"]):
		Game.kick(Vector2(-face, 0), 2.0)
	stats["fire"] = int(stats["fire"]) + 1
	stats["last_fire_t"] = Game.clock()
	stats["last_charge"] = charge
	if perfect:
		stats["perfect"] = int(stats["perfect"]) + 1


func _aim_angle(origin: Vector2, spd: float, grav: float) -> float:
	## Dikey hedef yardımı: öndeki en yakın düşman. Nişan noktası gövde kutusunun okun yüksekliğine en yakın yeri
	## (düz atış zaten değiyorsa açı 0); koni yakında geniş (alçak kurt dibinde de vurulsun), uzakta dar.
	## Yerçekimi düşüşü kadar yukarı.
	var best := 0.0
	var best_s := INF
	var best_d := 0.0
	for e in p.get_tree().get_nodes_in_group("dusman"):
		if not _valid_target(e):
			continue
		var r: Rect2 = e.hurt_rect()
		var tx := r.get_center().x
		if (tx - origin.x) * float(p.facing) < 4.0 and not r.has_point(origin):
			continue
		var ty := clampf(origin.y, r.position.y + minf(4.0, r.size.y * 0.3), r.end.y - minf(4.0, r.size.y * 0.3))
		var d := Vector2(tx, ty) - origin
		var dist := d.length()
		if dist > AIM_RANGE:
			continue
		var a := atan2(d.y, maxf(absf(d.x), 1.0))
		var cone := lerpf(1.1, AIM_CONE, clampf((dist - 30.0) / 140.0, 0.0, 1.0))
		if absf(a) > cone:
			continue
		var s := dist + absf(a) * 160.0
		if s < best_s:
			best_s = s
			best = a
			best_d = dist
	if best_s < INF and grav > 0.0:
		best -= grav * best_d / (2.0 * spd * spd)
	return clampf(best, -1.1, 1.1)


func _arrow_hit(e: Node, it: Dictionary, dmg: float, kb: float, face: int, perfect: bool, on_beat: bool, close: float, _src: Vector2, o: Ok, shot: Dictionary) -> Dictionary:
	var mech: String = it.get("mech_id", "")
	var opts := {"kb": kb, "dir": signf(o.velocity.x) if absf(o.velocity.x) > 1.0 else float(face), "ok": true, "usul_ok": on_beat}
	# kemankeş: _deal'de "full" kesin kritik -> artık yalnız tam bırakış; yelpaze dolu kritik yerine dipten kritik
	opts["full"] = perfect if mech == "kemankes" else false
	if perfect:
		opts["force_crit"] = true
		opts["krit_neden"] = "yay_tam"   # v23 kritik ölçümü (Player.krit_say)
	var near: bool = close > 0.0 and e.center().distance_to(p.center()) <= close
	if near:
		opts["force_crit"] = true
		opts["krit_neden"] = "yay_dipten"
		if not shot["dipten"]:
			shot["dipten"] = true
			FX.text(e.center() + Vector2(0, -30), "dipten!", Color(0.7, 0.92, 1.0), 7)
	if kb >= 150.0:
		opts["stagger"] = true
	var hp0: float = e.hp
	p._deal(e, dmg, it, opts)
	if mech == "alev_oku" and p.level:
		p.level.fire_pool(e.global_position, 22.0, float(it.get("mech_v", 2.0)), 2.0)
	stats["isabet"] = int(stats["isabet"]) + 1
	stats["last_hit_t"] = Game.clock()
	var crit: bool = opts.get("crit", false)
	if crit and not opts.get("feel_done", false):
		Game.kick(Vector2(face, 0), 2.5)
	return {"crit": crit, "killed": not is_instance_valid(e) or e.dead, "dmg": hp0 - (e.hp if is_instance_valid(e) else 0.0)}


func on_pierce(_e: Node, _o: Ok) -> void:
	pass


# ------------------------------------------------------------------ saplı oklar (ok sökme)
func stick(e: Node, o: Ok, at: Vector2) -> void:
	if not is_instance_valid(e) or e.dead:
		return
	var key := e.get_instance_id()
	var r: Dictionary = _stuck.get(key, {"e": e, "n": 0, "t": 0.0, "spr": [], "pos": e.global_position, "lvl": p.level.get_instance_id() if p.level else 0})
	r["n"] = mini(STUCK_MAX, int(r["n"]) + 1)
	r["t"] = STUCK_LIFE
	var spr := _stuck_sprite(o)
	if spr:
		var sprs: Array = r["spr"]
		if sprs.size() >= STUCK_MAX:
			var old: Variant = sprs.pop_front()
			if is_instance_valid(old):
				(old as Node).queue_free()
		e.add_child(spr)
		# aynı yere saplanan oklar üst üste binmesin: enine birkaç birim, açıda biraz sapma
		var hd := o.velocity.normalized()
		spr.global_position = at + Vector2(-hd.y, hd.x) * randf_range(-3.0, 3.0) - hd * randf_range(0.0, 2.0)
		spr.global_rotation = o.velocity.angle() + randf_range(-0.18, 0.18)
		spr.z_index = 5
		sprs.append(spr)
	_stuck[key] = r
	stats["saplanma"] = int(stats["saplanma"]) + 1


func _stuck_sprite(o: Ok) -> Node2D:
	## Saplı ok görseli: v2 mürekkep ok sprite'ı (uçtan kısaltılmış: gövdenin içinde), v1 piksel ok karesi
	if o.ink_spr:
		var s := o.ink_spr.duplicate() as Sprite2D
		s.modulate = Color(1.15, 1.1, 1.05)   # karanlık gövdede okunsun
		s.material = SusV2.flat_mat()
		# uç gövdenin içinde: bölge kuyruktan pivotun biraz ötesine kırpılır (temrenin görünmesin)
		var r := s.region_rect
		var cut := minf(r.size.x, -s.offset.x + 10.0)
		s.region_rect = Rect2(r.position, Vector2(cut, r.size.y))
		var g := s.get_node_or_null("glow") as Sprite2D
		if g:
			g.region_rect = s.region_rect
		return s
	return null


func stuck_n(e: Node) -> int:
	if e == null or not is_instance_valid(e):
		return 0
	return int(_stuck.get(e.get_instance_id(), {}).get("n", 0))


func melee_rip(e: Node, _it: Dictionary, opts: Dictionary) -> float:
	## Yakın dövüş vuruşu saplı okları söker: hasar çarpanı döner (Player._deal)
	if e == null or not is_instance_valid(e):
		return 1.0
	var key := e.get_instance_id()
	if not _stuck.has(key):
		return 1.0
	var r: Dictionary = _stuck[key]
	var n := int(r["n"])
	_stuck.erase(key)
	if n <= 0:
		return 1.0
	var c: Vector2 = e.center()
	for s in r["spr"]:
		if is_instance_valid(s):
			_fly_out(s as Node2D, c)
	if n >= 3:
		opts["force_crit"] = true
		opts["krit_neden"] = "ok_sokme"
	if "bleed" in e:
		e.bleed = mini(5, int(e.bleed) + n)
		e.bleed_t = 4.0
	hazir = mini(HAZIR_MAX, hazir + 1)
	ammo_add(1)   # v25: sökülen ok bir atış hakkı
	var it := _bow()
	if not it.is_empty():
		p.cd[p.sec_slot] = 0.0
	Ses.play("sapla", -2.0, 1.15, 0.05, 0.02)
	Ses.play("darbe_delme", -5.0, 0.85, 0.05, 0.02)
	Game.hitstop(0.025)
	FX.text(c + Vector2(0, -40), "OK SÖKÜLDÜ" + (" ×%d" % n if n > 1 else ""), Color(1.0, 0.55, 0.4), 8 + mini(n, 3))
	var fx := InkFX.spawn(0, c, 59)
	if fx:
		fx.el("drops", Vector2.ZERO, randf() * TAU, Vector2.ONE * (34.0 + 6.0 * n), InkFX.V_STAMP, 0.0, 0.06, 0.08, 0.42)
		fx.el("claw", Vector2.ZERO, randf_range(-0.5, 0.5), Vector2.ONE * (30.0 + 4.0 * n), InkFX.V_CUT, 0.0, 0.03, 0.06, 0.24)
	stats["sokme"] = int(stats["sokme"]) + 1
	return 1.0 + 0.3 * float(n)


func _fly_out(s: Node2D, c: Vector2) -> void:
	## sökülen ok: düşmandan geriye fırlar, döner ve söner
	var g := s.global_position
	var rot := s.global_rotation
	if FX.root:
		s.reparent(FX.root)
	s.global_position = g
	s.global_rotation = rot
	var away := (g - c).normalized() if g.distance_to(c) > 0.5 else Vector2.from_angle(rot + PI)
	away = (away + Vector2(0, -0.8)).normalized()
	var tw := s.create_tween()
	tw.set_parallel(true)
	tw.tween_property(s, "global_position", g + away * 26.0 + Vector2(0, 6), 0.32).set_trans(Tween.TRANS_QUAD).set_ease(Tween.EASE_OUT)
	tw.tween_property(s, "global_rotation", rot + randf_range(2.0, 4.0) * (1.0 if randf() < 0.5 else -1.0), 0.32)
	tw.tween_property(s, "modulate:a", 0.0, 0.2).set_delay(0.14)
	tw.chain().tween_callback(s.queue_free)


func _stuck_tick(delta: float) -> void:
	if _stuck.is_empty():
		return
	for key in _stuck.keys():
		var r: Dictionary = _stuck[key]
		var e: Variant = r["e"]
		var alive: bool = is_instance_valid(e) and not (e as Node).is_queued_for_deletion() and not e.dead
		if alive:
			r["pos"] = (e as Node2D).global_position
			r["t"] = float(r["t"]) - delta
			if float(r["t"]) <= 0.0:
				for s in r["spr"]:
					if is_instance_valid(s):
						var tw := (s as Node).create_tween()
						tw.tween_property(s, "modulate:a", 0.0, 0.3)
						tw.tween_callback((s as Node).queue_free)
				_stuck.erase(key)
			continue
		# düşman öldü: saplı oklar yere dökülür (toplanabilir); bölüm değiştiyse dökülmez
		if p.level and int(r.get("lvl", 0)) == p.level.get_instance_id():
			_drop(r["pos"] as Vector2, mini(3, int(r["n"])))
		_stuck.erase(key)


func _drop(at: Vector2, n: int) -> void:
	if p.level == null:
		return
	var it := _bow()
	var vr := String(prof(it)["var"]) if not it.is_empty() else "normal"
	for i in n:
		var o := Ok.new()
		o.team = "p"
		o.okc = self
		o.harmless = true
		o.position = at + Vector2(randf_range(-6, 6), -18.0 - i * 3.0)
		o.velocity = Vector2(randf_range(-70, 70), randf_range(-190, -120))
		o.gravity = 700.0
		o.life = 3.0
		o.arrow_variant = vr
		p.level.add_projectile(o)


func on_pickup(o: Ok) -> void:
	hazir = mini(HAZIR_MAX, hazir + 1)
	ammo_add(1)   # v25: toplanan ok cephaneli yayda anında bir atış hakkı
	stats["toplama"] = int(stats["toplama"]) + 1
	var at := o.global_position
	Ses.play("esya", -10.0, 1.6, 0.05, 0.04)
	Ses.play("yay_ger", -14.0, 1.4, 0.05, 0.04)
	FX.text(p.center() + Vector2(0, -36), "+OK" + (" (%d)" % hazir if hazir > 1 else ""), Color(1.0, 0.9, 0.6), 7)
	InkFX.ring(at, 10.0, 9, 0.22)
	if _pips:
		_pips.set_meta("pop", 0.2)


# ------------------------------------------------------------------ mürekkep geri bildirimleri
func _glint(_it: Dictionary) -> void:
	## yay doldu: ok ucunda mürekkep parıltısı (tam bırakış penceresi açıldı)
	if not p._bow_nock_ok:
		return
	var tip := p.arm_root.to_global(p._bow_nock + Vector2(p.facing * 20, 0))
	# v31: ok ucunda altın iğne yıldızı + daralan ince kuru halka (silah atlası)
	var n := InkFX.spawn(9, tip, 60, true)
	if n:
		n.el("glint", Vector2.ZERO, randf_range(-0.15, 0.15), Vector2(18.0, 12.0), InkFX.V_CUT, 0.0, 0.02, 0.05, 0.16)
		n.el("ring_thin", Vector2.ZERO, randf() * TAU, Vector2.ONE * 15.0, InkFX.V_DRY, 0.0, 0.05, 0.0, 0.16)


func _muzzle_fx(at: Vector2, dir: Vector2, pal: int, charge: float, perfect: bool, n: int) -> void:
	# v31 bırakış patlaması (silah atlası): tek karelik iğne parlaması + öne açılan kısa fırça telleri yelpazesi (kiriş
	# şaklamasının mürekkebi, soluk ve çok kısa); yelpazede geniş, tam gerilmede uzun
	var fx := InkFX.spawn(9 if perfect else pal, at + dir * 4.0, 57, true)
	if fx == null:
		return
	var L := 22.0 + 18.0 * charge + (6.0 if n > 1 else 0.0)
	var fl := 1.0 if randf() < 0.5 else -1.0
	fx.el("flash", dir * 3.0, dir.angle(), Vector2(L * 0.9, L * 0.42), InkFX.V_CUT, 0.0, 0.001, 0.03, 0.06)
	fx.el("cut_thin", dir * L * 0.4, dir.angle(), Vector2(L, L * (0.07 if n == 1 else 0.12) * fl), InkFX.V_CUT, 0.0, 0.025, 0.03, 0.13)
	fx.el("release", dir * 2.0, dir.angle(), Vector2(1.0, (0.8 if n == 1 else 1.2) * fl) * (11.0 + 7.0 * charge + (4.0 if n > 1 else 0.0)), InkFX.V_DRY, 0.0, 0.02, 0.02, 0.11)


func _perfect_fx(at: Vector2, face: int) -> void:
	## Tam bırakış: kısa duraklama, altın mürekkep halkası, yazı, gövde flaşı
	Game.hitstop(0.035)
	Game.kick(Vector2(-face, 0), 3.5)
	Game.rumble(0.25, 0.4, 0.08)
	FX.text(p.center() + Vector2(0, -46), "TAM BIRAKIŞ", Color(1.0, 0.86, 0.42), 9)
	Ses.play("yay_dolu", -4.0, 1.5, 0.02, 0.02)
	var fx := InkFX.spawn(9, at, 59)
	if fx:
		fx.el("enso", Vector2.ZERO, randf() * TAU, Vector2.ONE * 30.0, InkFX.V_STAMP, 0.0, 0.06, 0.08, 0.32)
		fx.el("shard", Vector2.ZERO, randf_range(-0.2, 0.2), Vector2.ONE * 26.0, InkFX.V_CUT, 0.0, 0.025, 0.05, 0.18)
	p.anim.set_flash(0.45)
	p.get_tree().create_timer(0.05).timeout.connect(func() -> void:
		if is_instance_valid(p):
			p.anim.set_flash(0.0))


# ------------------------------------------------------------------ hazır ok göstergesi (baş üstünde küçük oklar)
func _pips_tick() -> void:
	var show := hazir > 0 and not _bow().is_empty() and not p.dead and p.wolf_t <= 0.0 and not p.don_on
	if _pips == null:
		if not show:
			return
		_pips = OkPips.new()
		_pips.okc = self
		p.add_child(_pips)
	_pips.visible = show
	if show:
		_pips.queue_redraw()


class OkPips extends Node2D:
	## Hazır ok göstergesi: başın üstünde 1-3 küçük, eğik mürekkep ok (kenar yumuşatmalı çizgiler)
	var okc: Okculuk

	func _ready() -> void:
		z_index = 30
		position = Vector2(0, -52)

	func _draw() -> void:
		var n := okc.hazir
		var pop := float(get_meta("pop", 0.0))
		if pop > 0.0:
			set_meta("pop", maxf(0.0, pop - get_process_delta_time()))
		var k := 1.0 + pop * 1.5
		var ink := Color(0.05, 0.035, 0.04, 0.95)
		var core := Color(1.0, 0.88, 0.55)
		for i in n:
			var x := (float(i) - float(n - 1) * 0.5) * 5.0
			var a := Vector2(x - 1.8, 3.2) * k
			var b := Vector2(x + 1.8, -3.2) * k
			var hd := (b - a).normalized()
			var nr := Vector2(-hd.y, hd.x)
			draw_line(a, b, ink, 1.3, true)
			draw_line(a, b, core, 0.5, true)
			var head := PackedVector2Array([b + hd * 1.4, b - hd * 1.2 + nr * 1.1, b - hd * 1.2 - nr * 1.1, b + hd * 1.4])
			draw_polyline(head, ink, 0.8, true)
			draw_line(a, a + (-hd + nr) * 1.3, ink, 0.7, true)
			draw_line(a, a + (-hd - nr) * 1.3, ink, 0.7, true)
