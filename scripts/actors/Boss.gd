class_name Boss
extends Enemy
## v23 bosslar: her biri adım dizileriyle (_seq) yazılmış çok evreli hamle takımı. Ortak kurallar:
##   * Boşta beklemek yok: hamle arası 0,3-0,8 sn; arada bir sonraki hamlenin menziline yürür / geri çekilir.
##   * Bütün hamleler süper zırhlı: vuruşlar hamleyi kesmez, geri itmez; sersemletme / dondurma / kök bossu kilitlemez
##     (dondurma 8 sn'de bir 0,5 sn). Karşı vuruş ("!" hazırlığa isabet) yalnız kritik.
##   * Boss duruşu (b_poise): her isabet duruş hasarı biriktirir (kritik, ağır silah, sersemletme daha çok); dolunca
##     SENDELER (1,8 sn, ×1,25 hasar, HUD'da "duruş kırık"), sonra 9 sn birikmez. Ayrıca hamleye özgü açık pencereler
##     (Tepegöz'ün duvara çarpınca açılan gözü ×2, Şahmeran'ın yere saplanan başı ×1,5, iniş toparlanmaları).
##   * Evre geçişi %66 / %33'te yeni hamleler ekler; %15'in altında ÖFKE (daha sık, daha kısa uyarı; uyarı en az 0,28 sn).
##   * Yanlış yerde durmak cezalandırılır: platformda / arkada / uzakta / kıpırtısız oyuncuya özel hamleler.
## Hamle takımları ve evreleri: docs/TASARIM.md "v23: yapay zeka ve boss mekanikleri".

signal phase_changed(p: int)

var phase := 1
var next_move := ""
var shadow_done := false
var intro_t := 1.6
var move_log: Dictionary = {}
var klon := false            # Kara Börü Han'ın gölge sahte kopyası (tek vuruşta dağılır)
var partner := false         # Kara Börü Han'ın 3. evre gölge eşi (kısıtlı hamle takımı)
var enraged := false
var b_poise := 0.0
var _poise_cd := 0.0
var _poise_idle := 0.0
var _close_t := 0.0        # oyuncunun dibinde kaldığı süre (yakın cezalandırıcı "nova" hamlesini çağırır)     # son duruş hasarından beri geçen süre (2 sn sonra söner)
var vuln_t := 0.0
var vuln_k := 1.0
var untouch := false
var _q: Array = []
var _step: Dictionary = {}
var _hit_once := false
var _cool: Dictionary = {}
var _last_moves: Array = []
var _plan := ""
var _plan_t := 0.0
var _fight_t := 0.0
var _cc_cd := 0.0
var _beam2: Isin
var _gust_dir := 0.0
var _gust_f := 0.0
var _rec_t := 0.4
var _klon_t := 0.0
var _land_k := 1.0
var _bosslog := false
var _tint_cm: CanvasModulate
var _tint_base := Color(1, 1, 1)
# v29: tam gövde animasyonu — hamle adımının evresine kare eşlemesi (docs/TASARIM.md "v29: boss animasyonları")
var _vz: Dictionary = {}     # etkin eşleme: an, f0, f1, lp (döngü başı), m (kip), t (adım süresi), e (geçen)
var _vrec: Array = []        # son hamlenin toparlanma bölümü [an, f0, f1] (hamle sonrası "recover" bekleyişine yayılır)

const RENK := {"kara_boru_han": Color(1.0, 0.3, 0.5), "tepegoz": Color(1.0, 0.75, 0.35), "sahmeran_ana": Color(0.5, 1.0, 0.5),
	"yelbegen": Color(0.6, 0.9, 1.0), "erlik_han": Color(1.0, 0.45, 0.2)}
const EVRE_ADI := {"kara_boru_han": ["", "BOZGUN UYANIYOR", "GÖLGE AYRILIYOR"], "tepegoz": ["", "GÖZÜ KIZARIYOR", "DAĞ GİBİ ÖFKE"],
	"sahmeran_ana": ["", "ZEHİR KABARIYOR", "KRALİÇENİN ÖFKESİ"], "yelbegen": ["", "ÜÇ BAŞ UYANIYOR", "KAF FIRTINASI"],
	"erlik_han": ["", "TAMU KAYNIYOR", "ERLİK'İN GAZABI"]}
const KUKREME := {"kara_boru_han": "uluma", "tepegoz": "agac_olum", "sahmeran_ana": "hayalet_olum", "yelbegen": "uluma", "erlik_han": "kut_donusum"}
const SEQ_STATES := ["windup", "act", "air", "cling", "hold", "vuln", "dash", "hide"]
## boss zırhı: açık pencereler (sendeleme, açık göz / saplanan baş) dışında alınan hasar çarpanı. Sendelemede tam
## hasar ×1,25 (broken_t): pencereyi kollamak savaşı belirgin kısaltır.
const ZIRH := {"kara_boru_han": 0.75, "tepegoz": 0.75, "sahmeran_ana": 0.68, "yelbegen": 0.75, "erlik_han": 0.7}
## v29 animasyon adı öneki (sprite json'unda "<önek>_<hamle>" satırları; v1 sprite'ında yoksa eski adlara düşülür)
const V29_ON := {"kara_boru_han": "kbh", "tepegoz": "tg", "sahmeran_ana": "sh", "yelbegen": "yb", "erlik_han": "er"}


func _ready() -> void:
	super._ready()
	is_boss = true
	elite = false
	_label.text = String(def.get("name", "KARA BÖRÜ HAN")).to_upper()
	_label.visible = false
	state = "intro"
	if not _v_show(_an("roar"), "a", 0):
		anim.play("howl" if kind == "kara_boru_han" else "rage")
	aggro = true
	cd = 0.8
	_bosslog = OS.get_cmdline_user_args().has("--bosslog")
	if level:
		level.add_light(Vector2(0, -size.y * 0.6), _col(), 260.0, 1.1, self)


func _exit_tree() -> void:
	# stil v2 dev boss sayfaları koşu boyunca önbellekte birikmesin (beşi birden ~240 MB VRAM); gölge kopya değil, asıl boss
	if anim and Data.is_linear(anim.meta) and not get_meta("golge", false):
		Data.forget_sprite(sprite_kind)
	if is_instance_valid(_beam2):
		_beam2.queue_free()
	if _tint_cm and is_instance_valid(_tint_cm):
		_tint_cm.color = _tint_base


func _col() -> Color:
	return RENK.get(kind, Color(1.0, 0.3, 0.5))


# ================================================================== hasar, duruş, sersemletme
func take_hit(d: float, opts: Dictionary) -> bool:
	if dead:
		return false
	if untouch and not decoy:
		if Engine.get_physics_frames() % 8 == 0:
			FX.text(center() + Vector2(0, -size.y * 0.5), "erişilmez", Color(0.8, 0.75, 0.9), 7)
		return false
	if vuln_t > 0.0:
		d *= vuln_k
	elif state != "sendele":
		d *= float(ZIRH.get(kind, 1.0))
	var v0 := velocity
	var fr := freeze_t
	var crit: bool = opts.get("crit", false) or opts.get("force_crit", false)
	var pz := float(opts.get("poise", 0.6 if float(opts.get("kb", 0.0)) > 0.0 else 0.15))
	pz += (1.0 if crit else 0.0) + (1.5 if opts.get("heavy", false) else 0.0) + float(opts.get("stun", 0.0)) * 1.5
	var r := super.take_hit(d, opts)
	# boss sarsılmaz, geri itilmez, kilitlenmez
	hurt_t = 0.0
	stun_t = 0.0
	root_t = 0.0
	if not (state in ["sendele", "vuln"]):
		velocity = v0
	if freeze_t > fr:
		if _cc_cd <= 0.0:
			freeze_t = minf(freeze_t, 0.5)
			_cc_cd = 8.0
		else:
			freeze_t = fr
	if not dead and not decoy:
		_add_poise(pz)
	return r


func stun(t: float) -> void:
	## Boss: sersemletme duruşa eklenir. Kavramadan (Tepegöz) kurtulan oyuncu bossu sendeletir.
	if state == "hold":
		_drop_grab(Vector2(-facing * 160.0, -200.0))
		_stagger(1.2, "KURTULDUN!")
		return
	if not (state in ["sendele", "vuln"]):
		_add_poise(t * 3.0)


func _add_poise(p: float) -> void:
	if _poise_cd > 0.0 or state in ["sendele", "vuln", "intro"] or klon:
		return
	b_poise += p * (0.75 if state in SEQ_STATES else 1.0)
	_poise_idle = 0.0
	if b_poise >= _poise_max():
		_stagger(1.8, "SENDELEDİ!")


func _poise_max() -> float:
	return 30.0 + 6.0 * phase


func _stagger(t: float, txt: String) -> void:
	## Duruşu kırıldı: hamle kesilir, t sn açık (×1,25 hasar: broken_t), sonra 9 sn duruş birikmez
	_clear_move()
	if _bosslog:
		print("BOSS %s faz=%d %s t=%.1f" % [kind, phase, txt, _fight_t])
	b_poise = 0.0
	_poise_cd = 9.0 + t
	state = "sendele"
	st = t
	broken_t = t
	sa_t = 0.0
	velocity.x = 0.0
	if not _v_begin(_an("stagger"), "a", "map", t, "sendele", "-"):
		anim.play("hurt" if anim.has_anim("hurt") else "idle", true)
	FX.text(center() + Vector2(0, -size.y * 0.5 - 20.0), txt, Color(1.0, 0.8, 0.45), 10)
	InkFX.ring(center(), 30.0 + size.y * 0.2, 9, 0.35)
	FX.ring(center(), 40.0 + size.y * 0.25, Color(1.0, 0.85, 0.45), 0.35)
	Game.slowmo(0.4, 0.2)
	Game.shake(4.0)
	Ses.play("darbe_kunt", -2.0, 0.7)


func _clear_move() -> void:
	_q.clear()
	_step = {}
	_vz = {}
	_vrec = []
	contact = false
	untouch = false
	flying = false
	anim.modulate.a = 1.0 if not klon else anim.modulate.a
	if is_instance_valid(_beam2):
		_beam2.queue_free()
	_beam2 = null
	_gust_f = 0.0
	if grab_target and is_instance_valid(grab_target):
		_drop_grab(Vector2(-facing * 120.0, -160.0))


func _drop_grab(v: Vector2) -> void:
	if grab_target and is_instance_valid(grab_target) and grab_target.grabbed_by == self:
		grab_target.release_grab(v)
	grab_target = null


func _die(dir := 1.0, kb := 100.0, crit := false) -> void:
	_clear_move()
	if get_meta("golge", false):
		FX.anim("void_implosion", center(), 0.0, 1.4 if not klon else 0.8, Color(0.6, 0.3, 0.9))
		FX.soul(center(), Color(0.7, 0.4, 1.0), 24 if not klon else 8)
		dead = true
		remove_from_group("dusman")
		queue_free()
		return
	# asıl boss ölünce çağrılanlar ve gölge eş dağılır
	for e in get_tree().get_nodes_in_group("dusman"):
		if e != self and is_instance_valid(e) and not e.dead and (e.get_meta("v23_cagri", false) or e.get_meta("golge", false)):
			e._die(0.0, 0.0, false)
	_v29_death()
	super._die(dir, kb, crit)


# ================================================================== adım dizisi motoru
func _w(t: float, a := "windup", glyph := "!", hint := "", go := Callable()) -> Dictionary:
	## hazırlık adımı (uyarı): "!" ya da "!!" (yakalama / ağır), isteğe bağlı ipucu yazısı (ZIPLA!, YUVARLAN!...)
	return {"s": "windup", "t": t, "a": a, "g": glyph, "h": hint, "go": go}


func _a(t: float, s := "act", a := "", go := Callable(), tick := Callable(), until := Callable()) -> Dictionary:
	return {"s": s, "t": t, "a": a, "go": go, "tick": tick, "until": until}


func _seq(mv: String, steps: Array) -> void:
	next_move = mv
	move_log[mv] = int(move_log.get(mv, 0)) + 1
	_last_moves.push_front(mv)
	if _last_moves.size() > 3:
		_last_moves.pop_back()
	if _bosslog and not klon:
		print("BOSS %s faz=%d hamle=%s can=%d/%d t=%.1f" % [kind, phase, mv, int(hp), int(max_hp), _fight_t])
	_q = steps.duplicate()
	_next_step()


func _next_step() -> void:
	if _q.is_empty():
		_step = {}
		state = "recover"
		st = _rec_t
		contact = false
		flying = false
		untouch = false
		# v29: toparlanma bölümü hamle sonrası bekleyişe yayılır (yoksa durgun)
		_vz = {}
		if not _vrec.is_empty():
			_v_set(String(_vrec[0]), int(_vrec[1]), int(_vrec[2]), -1, "map", _rec_t)
		return
	_step = _q.pop_front()
	_hit_once = false
	var s := String(_step.get("s", "act"))
	var t := float(_step.get("t", 0.3))
	if s == "windup":
		t = maxf(0.28, t * (0.92 if phase >= 3 else 1.0) * (0.85 if enraged else 1.0)) if t > 0.28 else t
		state = "windup"
		st = t
		var g := String(_step.get("g", "!"))
		warn.text = g
		warn.label_settings.font_color = Color(1.0, 0.62, 0.12) if g == "!!" else Color(1.0, 0.35, 0.25)
		warn.position = Vector2(-8.0 if g == "!!" else -4.0, -size.y - 26.0)
		_windup_sfx()
		var h := String(_step.get("h", ""))
		if h != "" and not klon:
			FX.text(center() + Vector2(0, -size.y * 0.5 - 34.0), h, Color(1.0, 0.85, 0.55), 9)
	else:
		state = s
		st = t
	var a := String(_step.get("a", ""))
	var vs: Array = _step.get("v", [])
	if vs.is_empty() or not _v_begin(String(vs[0]), String(vs[1]), String(vs[2]), t, s, String(vs[3])):
		_vz = {}
		_vrec = []
		if a != "" and anim.has_anim(a):
			anim.play(a, true)
		elif _bosslog and not klon:
			print("BOSS %s ANIM EKSIK adim=%s a=%s v=%s" % [kind, s, a, str(vs)])
	var go: Callable = _step.get("go", Callable())
	if go.is_valid():
		go.call()


func _run_step(delta: float) -> void:
	st -= delta
	var tick: Callable = _step.get("tick", Callable())
	if tick.is_valid():
		tick.call(delta)
	if _step.is_empty():
		return   # tick hamleyi kesti (sendeleme vb.)
	var done := st <= 0.0
	var until: Callable = _step.get("until", Callable())
	if until.is_valid() and until.call():
		done = true
	if done:
		_next_step()


func _then(mv: String, steps: Array) -> void:
	## zincir: mevcut dizinin sonuna başka hamle ekle (kombo)
	move_log[mv] = int(move_log.get(mv, 0)) + 1
	if _bosslog and not klon:
		print("BOSS %s faz=%d zincir=%s" % [kind, phase, mv])
	_q.append_array(steps)


# ================================================================== v29 animasyon eşlemesi
## Boss sprite'ının (stil v2) her hamlesi kendi tam gövde satırını taşır; satırın json'undaki "v29": {"seg": {ad: [ilk,
## son, döngü başı]}} evre bölümleri adımlara eşlenir (tools/artgen/<boss>_v29.py). Kipler: "wu" hazırlık (kareler
## uyarı süresinin ilk %75'ine yavaşlayarak yayılır, derin pozda bekler, son kare = fırlama anı son 0,08 sn), "map"
## adım süresine eşit yayılım (temas karesi vuruş anında, eylem adımının başında açılır), "fast" ilk %60'a yayılıp son
## karede durur, "ol" bir kez oynayıp döngü başından döner (fps), "loop" döngü, "air" dikey hıza göre (yükseliş / tepe /
## düşüş), "hold" tek kare. AI zamanları, vuruş kutuları ve adım süreleri DEĞİŞMEZ: yalnızca hangi karenin gösterileceği.
func _an(x: String) -> String:
	return String(V29_ON.get(kind, "")) + "_" + x


func _v(step: Dictionary, an: String, seg: String, mode := "", rec := "") -> Dictionary:
	## adıma v29 eşlemesi ekle: an satırının seg bölümü; rec "-" = hamle sonrası toparlanma bölümü kullanılmaz
	step["v"] = [_an(an), seg, mode, rec]
	return step


func _seg(an: String, sg: String) -> Array:
	if anim == null or not anim.has_anim(an):
		return []
	var v: Variant = (anim.meta["anims"][an] as Dictionary).get("v29", null)
	if not (v is Dictionary) or not (v as Dictionary).has("seg") or not (v["seg"] as Dictionary).has(sg):
		return []
	var r: Array = v["seg"][sg]
	return [int(r[0]), int(r[1]), int(r[2]) if r.size() > 2 else -1]


func _v_set(an: String, f0: int, f1: int, lp: int, m: String, t: float) -> void:
	_vz = {"an": an, "f0": f0, "f1": f1, "lp": lp, "m": m, "t": maxf(0.01, t), "e": 0.0}
	_v_apply()


func _v_begin(an: String, sg: String, mode: String, t: float, s: String, rec := "") -> bool:
	var r := _seg(an, sg)
	if r.is_empty():
		return false
	var m := mode
	if m == "":
		m = "wu" if s == "windup" else ("ol" if int(r[2]) >= 0 else "map")
	_v_set(an, int(r[0]), int(r[1]), int(r[2]), m, t)
	# toparlanma: bu satırın 'r' bölümü (adımın kendisi 'r' ise son karesi tutulur)
	_vrec = []
	if rec != "-":
		if sg == "r":
			_vrec = [an, int(r[1]), int(r[1])]
		else:
			var rr := _seg(an, "r")
			if not rr.is_empty():
				_vrec = [an, int(rr[0]), int(rr[1])]
	return true


func _v_show(an: String, sg: String, k: int) -> bool:
	## bölümün k. karesini doğrudan göster (eşleme kurmadan: giriş, gölge kopya bekleyişi)
	var r := _seg(an, sg)
	if r.is_empty():
		return false
	anim.show_frame(an, clampi(int(r[0]) + k, int(r[0]), int(r[1])))
	return true


func _v_tick(delta: float) -> void:
	if _vz.is_empty():
		return
	_vz["e"] = float(_vz["e"]) + delta
	_v_apply()


func _v_apply() -> void:
	var an := String(_vz["an"])
	if anim == null or not anim.has_anim(an):
		_vz = {}
		return
	var f0 := int(_vz["f0"])
	var f1 := int(_vz["f1"])
	var n := f1 - f0 + 1
	var t := float(_vz["t"])
	var e := float(_vz["e"])
	var u := clampf(1.0 - st / t, 0.0, 1.0)
	var fps := float(anim.meta["anims"][an]["fps"])
	var f := f0
	match String(_vz["m"]):
		"wu":
			if n >= 3 and st <= minf(0.08, t * 0.25):
				f = f1
			else:
				var k := n - 1 if n >= 3 else n
				f = f0 + mini(k - 1, int(sqrt(clampf(u / 0.75, 0.0, 1.0)) * k))
		"map":
			f = f0 + mini(n - 1, int(u * n))
		"fast":
			f = f0 + mini(n - 1, int(clampf(u / 0.6, 0.0, 1.0) * n))
		"loop":
			f = f0 + int(e * fps) % n
		"ol":
			var lp := int(_vz["lp"])
			var i := int(e * fps)
			if lp < f0 or f0 + i < lp:
				f = mini(f1, f0 + i)
			else:
				f = lp + (f0 + i - lp) % (f1 - lp + 1)
		"air":
			var vy := velocity.y
			f = f0 if vy < -140.0 else (f0 + 1 if vy < 140.0 else f0 + 2)
			if e < 0.06:
				f = f0
			f = mini(f, f1)
		_:
			f = f0
	anim.show_frame(an, f)


func _v29_death() -> void:
	## Ölüm sırası: ayrı bir düğümde (boss düğümü hemen silinir; oyun akışı ve ödüller aynı) ölüm satırı oynar, son
	## karede bekler, sonra kül olup söner. Uçan ceset (FX.corpse) bu boss için gösterilmez.
	var an := _an("death")
	if anim == null or not anim.has_anim(an) or FX.root == null:
		return
	var host := Node2D.new()
	FX.root.add_child(host)
	host.global_position = global_position
	host.z_index = z_index
	var sa := SpriteAnim.new()
	host.add_child(sa)
	sa.setup(sprite_kind)
	sa.scale = base_scale
	sa.set_facing(facing)
	sa.show_frame(an, 0)
	var n := sa.frame_count(an)
	var fps := float(anim.meta["anims"][an]["fps"])
	var fx_c := _col()
	var dir := facing
	var tw := host.create_tween()
	tw.tween_method(func(x: float) -> void: sa.show_frame(an, int(x)), 0.0, float(n) - 0.01, float(n) / fps)
	tw.tween_callback(func() -> void:
		Game.shake(4.0)
		FX.dust(host.global_position + Vector2(dir * 40.0, 0.0), Vector2.UP, 14, 0.5))
	tw.tween_interval(1.4)
	tw.tween_callback(func() -> void:
		FX.smoke(host.global_position + Vector2(0, -40), 6, 0.9, Color(0.3, 0.28, 0.34, 0.5))
		FX.soul(host.global_position + Vector2(0, -50), fx_c, 30))
	tw.tween_property(sa, "modulate", Color(0.2, 0.15, 0.25, 0.0), 1.3)
	tw.tween_callback(host.queue_free)
	anim.base.texture = null   # uçan ceset ve darbe karesi silueti yerine yukarıdaki ölüm sırası
	if anim.glow:
		anim.glow.visible = false


# ================================================================== yardımcılar
func _pl() -> Node:
	return level.player if level and level.player and not level.player.dead else null


func _px() -> float:
	var p := _pl()
	return float(p.global_position.x) if p else global_position.x


func _floor_y() -> float:
	return float(level.surface_y(int(floor(global_position.x / Level.TS)), int(floor(global_position.y / Level.TS)) - 2) * Level.TS)


func _arena_x(x: float) -> float:
	return clampf(x, 4.0 * Level.TS + size.x * 0.5, 82.0 * Level.TS - size.x * 0.5)


func _face_p() -> void:
	var p := _pl()
	if p:
		_face(p.center() - center())


func _box(w: float, h: float, off := 0.0, both := false) -> Rect2:
	if both:
		return Rect2(global_position.x - w, global_position.y - h, w * 2.0, h)
	return Rect2(global_position.x + (off if facing > 0 else -off - w), global_position.y - h, w, h)


func _hit(r: Rect2, k: float, push := Vector2.ZERO) -> bool:
	var p := _pl()
	if p == null or not r.intersects(p.hurt_rect()):
		return false
	var ok: bool = p.take_hit(dmg * k, self)
	if ok and push != Vector2.ZERO and p.has_method("shove"):
		var sx := signf(p.global_position.x - global_position.x)
		if sx == 0.0:
			sx = float(facing)
		p.shove(Vector2(push.x * sx, push.y))
	return ok


func _hit_tick(r: Rect2, k: float, push := Vector2.ZERO) -> void:
	## çok karelik vuruş kutusu: adım boyunca bir kez vurur
	if not _hit_once and _hit(r, k, push):
		_hit_once = true


func _leap_v(tx: float, peak: float) -> Vector2:
	## yerçekimi 1100 ile peak yükseklikte, tx'e inecek hız (düşüş hızı 540'ta kesilir: peak ≤ 130)
	var g := 1100.0
	var vy := -sqrt(2.0 * g * peak)
	var t := 2.0 * absf(vy) / g
	var vx := clampf((_arena_x(tx) - global_position.x) / t, -900.0, 900.0)
	return Vector2(vx, vy)


func _shoot(k: String, pos: Vector2, vel: Vector2, dk := 0.6, grav := -1.0, homing := 0.0, life := 3.5) -> Projectile:
	var p := Projectile.new()
	p.team = "e"
	p.kind = k
	p.damage = dmg * dk
	p.source = self
	p.position = pos
	p.velocity = vel
	p.gravity = grav if grav >= 0.0 else (0.0 if k == "spore" else (380.0 if k in ["stone_big", "ice", "stone"] else 120.0))
	p.homing = homing
	p.life = life
	p.trail_col = Color(_col(), 0.6)
	level.add_projectile(p)
	return p


func _lob(k: String, from: Vector2, tx: float, t: float, dk := 0.6, grav := 420.0) -> Projectile:
	## tx'e t sn'de düşecek yay atışı (iniş yeri önceden işaretlenir)
	var gy := float(level.surface_y(int(floor(tx / Level.TS)), int(floor(global_position.y / Level.TS)) - 2) * Level.TS) - 4.0
	var v := Vector2((tx - from.x) / t, (gy - from.y) / t - 0.5 * grav * t)
	level.telegraph_ground(Vector2(tx, gy), t)
	return _shoot(k, from, v, dk, grav)


func _ground_wave(sgn: int, spd := 280.0, dk := 0.7, col := Color(-1, 0, 0)) -> void:
	var p := Projectile.new()
	p.team = "e"
	p.kind = "ground_wave"
	p.damage = dmg * dk
	p.source = self
	p.position = Vector2(global_position.x + sgn * (size.x * 0.6), global_position.y - 14.0)
	p.velocity = Vector2(sgn * spd, 0)
	p.life = 3.0
	p.set_meta("col", _col() if col.r < 0.0 else col)
	level.add_projectile(p)


func _drop_from_sky(x: float, k: String, delay: float, dk := 0.6) -> void:
	## gökten düşen (işaretli): delay sn sonra x'in 300 px üstünden aşağı
	var gy := float(level.surface_y(int(floor(x / Level.TS)), int(floor(global_position.y / Level.TS)) - 2) * Level.TS)
	level.telegraph_ground(Vector2(x, gy), delay + 0.45)
	get_tree().create_timer(delay).timeout.connect(_sky_drop.bind(x, gy, k, dk))


func _sky_drop(x: float, gy: float, k: String, dk: float) -> void:
	if dead or level == null:
		return
	_shoot(k, Vector2(x, gy - 300.0), Vector2(0, 520.0), dk, 300.0)


func _spawn_add(k: String, pos: Vector2, hp_k := 0.5) -> Enemy:
	var e: Enemy = level.spawn_enemy(k, pos)
	e.aggro = true
	e.max_hp *= hp_k
	e.hp = e.max_hp
	e.set_meta("v23_cagri", true)
	FX.anim("smoke_puff", e.center(), 0.0, 0.9, _col(), false)
	FX.ring(e.center(), 24, _col(), 0.3)
	return e


func _adds_alive() -> int:
	var n := 0
	for e in get_tree().get_nodes_in_group("dusman"):
		if is_instance_valid(e) and not e.dead and e.get_meta("v23_cagri", false):
			n += 1
	return n


func _shake_land(pw: float) -> void:
	vis_scale = Vector2(1.3, 0.75)
	Game.shake(4.0 + 4.0 * pw)
	Game.kick(Vector2.DOWN, 3.0 + 4.0 * pw)
	Ses.play("sarsinti_buyuk" if pw > 0.6 else "sarsinti", -2.0, 0.8)
	FX.ground_slam(global_position, facing, 1.0 + pw, _col(), false, false, false)


func _player_high() -> bool:
	var p := _pl()
	return p != null and float(p.global_position.y) < _floor_y() - 60.0


func _dist_x() -> float:
	return absf(_px() - global_position.x)


func _ready_move(mv: String) -> bool:
	return float(_cool.get(mv, 0.0)) <= 0.0


func _set_cool(mv: String, t: float) -> void:
	_cool[mv] = t


# ================================================================== yapay zekâ döngüsü
func _ai_custom(delta: float, player: Node, to_p: Vector2, dist: float) -> void:
	_fight_t += delta
	_poise_idle += delta
	if _poise_idle > 2.0:
		b_poise = maxf(0.0, b_poise - 4.0 * delta)
	_poise_cd -= delta
	_cc_cd -= delta
	if vuln_t > 0.0:
		vuln_t -= delta
		if vuln_t <= 0.0:
			vuln_k = 1.0
	for k in _cool.keys():
		_cool[k] = float(_cool[k]) - delta
	if player and not player.dead and absf(to_p.x) < size.x * 0.5 + 60.0 and absf(to_p.y) < size.y:
		_close_t += delta
	else:
		_close_t = maxf(0.0, _close_t - delta * 0.5)
	if _gust_f != 0.0:
		_apply_gust(delta)
	if klon:
		_klon_ai(delta)
		return
	var hpk := hp / max_hp
	var new_phase := 1 if hpk > 0.66 else (2 if hpk > 0.33 else 3)
	if partner:
		new_phase = 1
	if new_phase > phase and state != "intro":
		phase = new_phase
		_enter_phase()
		return
	if not enraged and hpk < 0.15 and not partner:
		enraged = true
		FX.text(center() + Vector2(0, -size.y - 40.0), "ÖFKE!", Color(1.0, 0.4, 0.3), 12)
		Ses.play(String(KUKREME.get(kind, "uluma")), -2.0, 0.6)
		Game.shake(5.0)
	match state:
		"intro":
			velocity.x = 0.0
			intro_t -= delta
			var ra := _seg(_an("roar"), "a")
			if not ra.is_empty():
				var rn := int(ra[1]) - int(ra[0]) + 1
				anim.show_frame(_an("roar"), int(ra[0]) + mini(rn - 1, int(clampf(1.0 - intro_t / 1.6, 0.0, 1.0) * rn)))
			else:
				anim.play("howl" if kind == "kara_boru_han" else "rage")
			if Engine.get_physics_frames() % 10 == 0:
				FX.ring(center(), 60 + 20 * (1.6 - intro_t), Color(_col(), 0.5), 0.35)
			if intro_t <= 0.0:
				state = "chase"
				cd = 0.25
				Ses.play(String(KUKREME.get(kind, "uluma")), 0.0, 0.7)
				Game.shake(5.0)
		"sendele":
			velocity.x = move_toward(velocity.x, 0.0, 900 * delta)
			st -= delta
			if Engine.get_physics_frames() % 8 == 0:
				FX.burst(center() + Vector2(0, -size.y * 0.4), Color(1.0, 0.95, 0.6), 1, 40, 0.5, 0.16, -20, true)
			if st <= 0.0:
				broken_t = 0.0
				state = "chase"
				cd = 0.15
				_vz = {}
		"recover":
			velocity.x = move_toward(velocity.x, 0.0, 900 * delta)
			if _vz.is_empty():
				_pa(["idle"])
			st -= delta
			if st <= 0.0:
				state = "chase"
				cd = _gap()
				_vz = {}
				_vrec = []
		"chase", "idle":
			state = "chase"
			_vz = {}
			_stalk(delta, player, to_p, dist)
		_:
			if not _step.is_empty():
				_run_step(delta)
			else:
				state = "chase"
	_v_tick(delta)
	if phase >= 3 and Engine.get_physics_frames() % 8 == 0 and not partner:
		FX.burst(center() + Vector2(randf_range(-size.x * 0.5, size.x * 0.5), randf_range(-size.y * 0.5, size.y * 0.3)), _col(), 1, 30, 0.6, 0.18, -60, true)


func _gap() -> float:
	## hamle arası: kısa (boşta bekleme yok); evre ve öfkeyle kısalır
	return randf_range(0.3, 0.75) / (1.0 + 0.2 * (phase - 1)) * (0.65 if enraged else 1.0)


func _stalk(delta: float, player: Node, to_p: Vector2, _dist: float) -> void:
	## Hamle arası: bir sonraki hamleyi seç, menziline yürü / geri çekil, menzile girince (ya da 1,1 sn sonra) başlat
	if player == null or player.dead:
		velocity.x = move_toward(velocity.x, 0.0, 600 * delta)
		_pa(["idle"])
		return
	if _plan == "":
		_plan = _choose()
		_plan_t = 0.0
	_plan_t += delta
	var rg := _range_of(_plan)
	var gap := absf(to_p.x)
	var side := _side_of(player)
	var tx := global_position.x
	if gap < rg.x:
		tx = float(player.global_position.x) + side * rg.x
	elif gap > rg.y:
		tx = float(player.global_position.x) + side * rg.y
	else:
		# menzildeyken de durmaz: bandın içinde salınır (dolanır, yaklaşıp uzaklaşır)
		var ph := 0.5 + 0.5 * sin(_fight_t * 2.4 + float(get_instance_id() % 7))
		tx = float(player.global_position.x) + side * lerpf(rg.x, minf(rg.y, rg.x + 160.0), ph)
	var spd := speed * (1.0 + 0.2 * (phase - 1)) * (1.2 if enraged else 1.0)
	var dx := _arena_x(tx) - global_position.x
	var want := 0.0
	if absf(dx) > 8.0:
		want = signf(dx) * spd
	velocity.x = move_toward(velocity.x, want, 900 * delta)
	_face(to_p)
	var loco: Array = ["idle"]
	if absf(velocity.x) > 12.0:
		loco = ["run", "walk"]
		# v29: Kara Börü Han bandın içinde salınırken sinsi yürür (walk), menzile koşarken dörtnala kalkar (run)
		if kind == "kara_boru_han" and anim.has_anim("walk") and absf(dx) < 70.0:
			loco = ["walk"]
	_pa(loco)
	if absf(velocity.x) > 12.0 and anim.anim == "walk":
		anim.speed = clampf(absf(velocity.x) / maxf(1.0, speed), 0.7, 1.6)
		if Engine.get_physics_frames() % 18 == 0 and is_on_floor() and size.y > 100.0:
			Game.shake(1.0)
			FX.dust(global_position + Vector2(facing * 14, 0), Vector2(-facing, -0.4), 3, 0.34)
	else:
		anim.speed = 1.0
	if cd <= 0.0 and ((gap >= rg.x - 10.0 and gap <= rg.y + 10.0) or _plan_t > 1.1):
		var mv := _plan
		_plan = ""
		anim.speed = 1.0
		velocity.x = 0.0
		_face(to_p)
		_start(mv)


func _pick(w: Dictionary) -> String:
	## ağırlıklı seçim: bekleme süresindekiler düşer, son hamleler cezalı (aynısı art arda gelmez). Oyuncu 1,2 sn'den
	## uzun süre dibinde kalırsa (ezbere vuruyorsa) yakın cezalandırıcı "nova" öne geçer.
	if _close_t > (0.8 if kind == "yelbegen" else 1.2) and not partner and _ready_move("nova"):
		w["nova"] = 7.0
	var tot := 0.0
	var opts: Array = []
	for k in w.keys():
		var v := float(w[k])
		if v <= 0.0 or not _ready_move(String(k)):
			continue
		if _last_moves.size() > 0 and _last_moves[0] == k:
			continue
		if String(k) in _last_moves:
			v *= 0.5
		opts.append([k, v])
		tot += v
	if opts.is_empty():
		return String(w.keys()[0])
	var r := randf() * tot
	for o in opts:
		r -= float(o[1])
		if r <= 0.0:
			return String(o[0])
	return String(opts[-1][0])


func _choose() -> String:
	match kind:
		"kara_boru_han":
			return _kbh_choose()
		"tepegoz":
			return _tg_choose()
		"sahmeran_ana":
			return _sh_choose()
		"yelbegen":
			return _yb_choose()
		"erlik_han":
			return _er_choose()
	return "x"


func _range_of(mv: String) -> Vector2:
	## hamlenin istediği yatay uzaklık (min, max)
	var r: Dictionary = {
		"pounce": Vector2(120, 330), "rush": Vector2(150, 420), "flurry": Vector2(0, 110), "howl": Vector2(140, 900),
		"wall_dive": Vector2(0, 900), "crystals": Vector2(160, 500), "shadows": Vector2(0, 900),
		"slam": Vector2(30, 135), "boulder": Vector2(200, 700), "stomp": Vector2(0, 600), "grab": Vector2(20, 120),
		"beam": Vector2(160, 520), "charge": Vector2(200, 900), "quake": Vector2(0, 900),
		"spit": Vector2(150, 480), "tail": Vector2(0, 170), "lunge": Vector2(110, 300), "snakes": Vector2(140, 900),
		"drip": Vector2(0, 900), "gaze": Vector2(120, 450), "venom": Vector2(120, 600),
		"club": Vector2(20, 140), "gust": Vector2(60, 400), "heads": Vector2(160, 520), "breath": Vector2(30, 220),
		"icicles": Vector2(0, 900), "blizzard": Vector2(0, 900), "leap_ice": Vector2(140, 500),
		"chain": Vector2(90, 300), "firewave": Vector2(0, 500), "fireballs": Vector2(180, 560), "scythe": Vector2(20, 130),
		"nova": Vector2(0, 900), "pillars": Vector2(120, 700), "souls": Vector2(120, 900), "walls": Vector2(0, 900), "tamu_seli": Vector2(0, 900), "gate": Vector2(0, 900)}
	return r.get(mv, Vector2(0, 400))


func _start(mv: String) -> void:
	if mv == "nova":
		_set_cool("nova", 4.0)
		_close_t = 0.0
		_rec_t = 0.35
		_seq("nova", [_v(_w(0.42, "howl" if kind == "kara_boru_han" else "rage", "!!", ""), "nova", "w"),
			_v(_a(0.45, "act", "slam" if kind != "sahmeran_ana" else "strike", _nova), "nova", "s")])
		return
	match kind:
		"kara_boru_han":
			_kbh_start(mv)
		"tepegoz":
			_tg_start(mv)
		"sahmeran_ana":
			_sh_start(mv)
		"yelbegen":
			_yb_start(mv)
		"erlik_han":
			_er_start(mv)
	if state == "chase":
		cd = 0.2


func _enter_phase() -> void:
	_clear_move()
	phase_changed.emit(phase)
	var col := _col()
	Game.slowmo(0.35, 0.45)
	Game.shake(7.0)
	FX.ring(center(), 150, col, 0.6)
	FX.flash_light(center(), col, 360.0, 2.2, 0.5)
	Ses.play(String(KUKREME.get(kind, "uluma")), 0.0, 0.65)
	var names: Array = EVRE_ADI.get(kind, ["", "", ""])
	FX.text(center() + Vector2(0, -size.y - 30), String(names[phase - 1]), col.lightened(0.3), 12)
	if level and level.has_method("flash_white"):
		level.flash_white(0.2)
	b_poise = 0.0
	# evre geçişi: kükreme şok dalgası (yakındaki oyuncu itilir), sonra hemen yeni evre hamlesi
	_seq("evre", [_v(_a(0.9, "act", "howl" if kind == "kara_boru_han" else "rage", _phase_roar), "roar", "a", "map")])
	_rec_t = 0.25
	if kind == "kara_boru_han" and phase == 3 and not shadow_done:
		shadow_done = true
		_spawn_partner()


func _nova() -> void:
	## Yakın cezalandırıcı: dibindeki oyuncuyu iten zırhlı şok halkası (her bossa kendi biçimi)
	var r := size.x * 0.5 + 90.0
	FX.ring(center(), r, _col(), 0.35)
	FX.ring(global_position + Vector2(0, -6), r, Color(_col(), 0.7), 0.3, 0.3)
	Game.shake(5.0)
	_hit(_box(r, size.y + 20.0, 0.0, true), 0.8, Vector2(340.0, -240.0))
	match kind:
		"kara_boru_han":
			Ses.play("uluma", -2.0, 0.9)
		"tepegoz":
			_shake_land(0.6)
		"sahmeran_ana":
			FX.slash(global_position + Vector2(0, -16), 1, -0.6, 0.6, r, 10.0, _col(), 0.2)
			FX.slash(global_position + Vector2(0, -16), -1, -0.6, 0.6, r, 10.0, _col(), 0.2)
			Ses.play("savur_dev", -3.0, 1.1)
		"yelbegen":
			for sg in [-1, 1]:
				Tehlike.spawn(level, "buz", Vector2(global_position.x + sg * (size.x * 0.5 + 40.0), global_position.y), 30.0, 0.05, 0.5, dmg * 0.4, self)
			Ses.play("buz_kir" if Ses.has("buz_kir") else "darbe_tas", -4.0, 0.9)
		"erlik_han":
			for sg in [-1, 1]:
				Tehlike.spawn(level, "ates", Vector2(global_position.x + sg * (size.x * 0.5 + 45.0), global_position.y), 40.0, 0.0, 1.4, dmg * 0.3, self)
			Ses.play("kut_donusum", -3.0, 0.8)


func _phase_roar() -> void:
	var p := _pl()
	if p and absf(float(p.global_position.x) - global_position.x) < 170.0 and p.has_method("shove"):
		p.shove(Vector2(signf(float(p.global_position.x) - global_position.x) * 320.0, -200.0))
	FX.ring(center(), 120, _col(), 0.45)


# ================================================================== KARA BÖRÜ HAN
## 1: sıçrayış zinciri (son sıçrayış gecikmeli), yer yaran hamle (şeritli, içinden yuvarlan), pençe yağmuru (3 hızlı +
##    gecikmeli ağır), uluma (ruh tazıları). 2: + duvardan pike (duvara tırmanır, işaretli yere dalar, iki yer dalgası),
##    bozgun kristalleri, ikili hamle. 3: + gölge oyunu (iki sahte kopya + asıl), gölge eş; ÖFKE: daha uzun zincirler.
func _kbh_choose() -> String:
	var d := _dist_x()
	var w := {"pounce": 3.0, "rush": 2.2, "flurry": 3.5 if d < 160.0 else 0.8, "howl": 1.4 if _adds_alive() < 2 and not partner else 0.0}
	if phase >= 2 and not partner:
		w["wall_dive"] = 1.6
		w["crystals"] = 1.4
	if phase >= 3 and not partner:
		w["shadows"] = 2.0
	if _player_high():
		w["pounce"] = 4.0
		w["flurry"] = 0.0
		w["rush"] = 0.4
		if w.has("wall_dive"):
			w["wall_dive"] = 3.0
	if _pl_still > 1.5:
		w["rush"] = float(w["rush"]) + 2.0
	return _pick(w)


func _kbh_start(mv: String) -> void:
	_rec_t = 0.32
	match mv:
		"pounce":
			var n := (2 if phase == 1 else 3) + (1 if enraged else 0)
			var steps: Array = []
			for i in n:
				var last := i == n - 1 and n > 1
				var wt := 0.45 if i == 0 else (0.62 if last else 0.22)   # son sıçrayış gecikmeli: ritmi bozar
				steps.append(_v(_w(wt, "windup", "!", "", _face_p), "pounce", "w"))
				steps.append(_v(_a(1.2, "air", "leap", _kbh_pounce_go, _kbh_air_tick, _landed), "pounce", "a", "air"))
				steps.append(_v(_a(0.1 if not last else 0.35, "act", "idle", _kbh_land.bind(0.6 if phase >= 2 else 0.3)), "pounce", "s"))
			_seq("pounce", steps)
			if phase >= 2 and randf() < 0.35:
				_then("rush", _kbh_rush_steps(false))
			elif randf() < 0.6:
				_q.append(_v(_a(0.9, "air", "leap", _kbh_backleap, _kbh_air_tick, _landed), "back", "a", "air"))
		"rush":
			_seq("rush", _kbh_rush_steps(phase >= 2))
			if _dist_x() < 260.0 and randf() < 0.4:
				_then("flurry", _kbh_flurry_steps())
		"flurry":
			_seq("flurry", _kbh_flurry_steps())
			if randf() < 0.65:
				_q.append(_v(_a(0.9, "air", "leap", _kbh_backleap, _kbh_air_tick, _landed), "back", "a", "air"))
		"howl":
			_set_cool("howl", 12.0)
			_seq("howl", [_v(_a(0.9, "air", "leap", _kbh_backleap, _kbh_air_tick, _landed), "back", "a", "air"),
				_v(_w(0.5, "howl", "!", ""), "howl", "w"), _v(_a(1.0, "act", "howl", _kbh_howl), "howl", "a")])
		"wall_dive":
			_set_cool("wall_dive", 7.0)
			_rec_t = 0.75   # iniş açığı
			_seq("wall_dive", [_v(_w(0.4, "windup", "!", ""), "pounce", "w"),
				_v(_a(1.6, "air", "leap", _kbh_to_wall, _kbh_air_tick, _kbh_at_wall), "pounce", "a", "air"),
				_v(_a(0.7, "cling", "howl", _kbh_cling), "wall", "c"), _v(_a(1.2, "air", "slam", _kbh_dive, _kbh_dive_tick, _landed), "wall", "d", "loop"),
				_v(_a(0.1, "act", "slam", _kbh_dive_land), "wall", "s")])
		"crystals":
			_set_cool("crystals", 6.0)
			_seq("crystals", [_v(_w(0.5, "rage", "!", ""), "crys", "w"), _v(_a(0.35, "act", "rage", _kbh_crystals.bind(0)), "crys", "a"),
				_v(_a(0.35, "act", "rage", _kbh_crystals.bind(1)), "crys", "a"), _v(_a(0.35, "act", "rage", _kbh_crystals.bind(2)), "crys", "a")])
		"shadows":
			_set_cool("shadows", 11.0)
			_rec_t = 0.8
			_seq("shadows", [_v(_w(0.45, "howl", "!", "GÖLGELER!"), "howl", "w"), _v(_a(0.5, "hide", "idle", _kbh_vanish), "pounce", "w", "hold"),
				_v(_a(1.25, "hide", "idle", _kbh_clones), "pounce", "w", "hold"), _v(_a(0.1, "hide", "idle", _kbh_emerge), "pounce", "w", "hold"),
				_v(_w(0.4, "windup", "!", "", _face_p), "pounce", "w"),
				_v(_a(1.2, "air", "leap", _kbh_pounce_go, _kbh_air_tick, _landed), "pounce", "a", "air"),
				_v(_a(0.1, "act", "idle", _kbh_land.bind(0.6)), "pounce", "s")])
		_:
			_seq("pounce", [_v(_w(0.45), "pounce", "w"), _v(_a(1.2, "air", "leap", _kbh_pounce_go, _kbh_air_tick, _landed), "pounce", "a", "air")])


func _landed() -> bool:
	return is_on_floor() and st < float(_step.get("t", 1.0)) - 0.15


func _kbh_air_tick(_delta: float) -> void:
	if Engine.get_physics_frames() % 2 == 0:
		FX.ghost(anim.base, Color(0.8, 0.2, 0.5, 0.35), 0.2)


func _kbh_pounce_go() -> void:
	var p := _pl()
	var tx := _px() + (float(p.velocity.x) * 0.35 if p else 0.0)
	velocity = _leap_v(tx, 95.0 if not _player_high() else 150.0)
	if _player_high() and p:
		velocity.y = -sqrt(2.0 * 1100.0 * maxf(150.0, _floor_y() - float(p.global_position.y) + 70.0))
	contact = true
	contact_k = 0.65
	_did_hit = false
	vis_scale = Vector2(0.8, 1.25)
	FX.dust(global_position, Vector2(-facing, -0.5), 8, 0.36)
	Ses.play("sicrayis", -2.0, 0.7)


func _kbh_land(pw: float) -> void:
	contact = false
	velocity.x *= 0.2
	_shake_land(pw * 0.6)
	if pw >= 0.5:
		# 2. evreden: inişte yakına kısa şok
		var p := _pl()
		if p and absf(float(p.global_position.x) - global_position.x) < 80.0 and p.is_on_floor():
			_hit(_box(80.0, 40.0, 0.0, true), 0.5, Vector2(220.0, -160.0))


func _kbh_rush_steps(double: bool) -> Array:
	var s: Array = [_v(_w(0.55, "windup", "!", "", _kbh_lane), "rush", "w"),
		_v(_a(0.9, "dash", "run", _kbh_rush_go, _kbh_rush_tick, _kbh_rush_end), "rush", "d"), _v(_a(0.35, "act", "idle", _kbh_skid), "rush", "k")]
	if double:
		s += [_v(_w(0.35, "windup", "!", "", _kbh_lane), "rush", "w"),
			_v(_a(0.9, "dash", "run", _kbh_rush_go, _kbh_rush_tick, _kbh_rush_end), "rush", "d"), _v(_a(0.45, "act", "idle", _kbh_skid), "rush", "k")]
	return s


func _kbh_lane() -> void:
	_face_p()
	var tx := _arena_x(_px() + facing * 260.0)
	var mid := (global_position.x + tx) * 0.5
	Tehlike.spawn(level, "serit", Vector2(mid, global_position.y), absf(tx - global_position.x) * 0.5, 0.55, 0.05, 0.0, self)
	set_meta("rush_x", tx)


func _kbh_rush_go() -> void:
	contact = true
	contact_k = 1.0
	_did_hit = false
	velocity.x = facing * 720.0
	Ses.play("savur_dev", -3.0, 0.8)
	FX.dust(global_position, Vector2(-facing, -0.4), 8, 0.34)


func _kbh_rush_tick(_delta: float) -> void:
	velocity.x = facing * 720.0
	if Engine.get_physics_frames() % 2 == 0:
		FX.ghost(anim.base, Color(0.9, 0.2, 0.4, 0.35), 0.18)
		FX.streak(global_position + Vector2(-facing * 40, -6), global_position + Vector2(-facing * 110, -6), Color(0.9, 0.3, 0.45, 0.7), 0.25)


func _kbh_rush_end() -> bool:
	var tx := float(get_meta("rush_x", global_position.x))
	return (facing > 0 and global_position.x >= tx) or (facing < 0 and global_position.x <= tx) or is_on_wall()


func _kbh_skid() -> void:
	contact = false
	velocity.x = facing * 160.0
	FX.dust(global_position, Vector2(-facing, -0.3), 10, 0.36)


func _kbh_flurry_steps() -> Array:
	return [_v(_w(0.35, "windup", "!", "", _face_p), "flurry", "w"), _v(_a(0.13, "act", "slam", _kbh_swipe.bind(0.6, false)), "flurry", "a"),
		_v(_a(0.13, "act", "leap", _kbh_swipe.bind(0.6, false)), "flurry", "b"), _v(_a(0.13, "act", "slam", _kbh_swipe.bind(0.6, false)), "flurry", "a"),
		_v(_w(0.55, "windup", "!", "", _face_p), "flurry", "W"), _v(_a(0.4, "act", "slam", _kbh_swipe.bind(1.3, true)), "flurry", "S")]


func _kbh_swipe(k: float, big: bool) -> void:
	velocity.x = facing * (90.0 if not big else 200.0)
	var w := 120.0 if not big else 150.0
	FX.slash(global_position + Vector2(facing * 30, -40), facing, -2.2 if big else -1.6, 0.9, 50.0 if big else 40.0, 10.0 if big else 7.0, Color(1.0, 0.4, 0.55), 0.16)
	Ses.play("savur_dev" if big else "savur_bicak", -4.0, 0.9 if big else 1.1)
	if big:
		Game.shake(3.0)
	_hit(_box(w, 72.0, -20.0), k, Vector2(320.0, -200.0) if big else Vector2(120.0, -60.0))


func _kbh_backleap() -> void:
	var side := _side_of(_pl()) if _pl() else -float(facing)
	velocity = _leap_v(global_position.x + side * 200.0, 70.0)
	FX.dust(global_position, Vector2.UP, 6, 0.3)


func _kbh_howl() -> void:
	_face_p()
	Ses.play("uluma", 0.0, 0.75)
	FX.anim("hush_lock", center() + Vector2(facing * 24, -16), 0.0, 2.0, Color(1.0, 0.35, 0.5))
	FX.ring(center(), 120, Color(1.0, 0.35, 0.5, 0.6), 0.4)
	Game.shake(4.0)
	var p := _pl()
	if p and absf(float(p.global_position.x) - global_position.x) < 130.0:
		_hit(_box(130.0, 120.0, 0.0, true), 0.3, Vector2(260.0, -180.0))
	var n := mini(3 - _adds_alive(), 2 if phase < 3 else 3)
	for i in n:
		var e := _spawn_add("kara_boru", Vector2(_arena_x(global_position.x - facing * (60 + i * 40)), global_position.y - 20.0), 0.45)
		e.anim.modulate = Color(0.8, 0.6, 1.0, 0.85)
		e.flank = i % 2


func _kbh_to_wall() -> void:
	# en yakın arena duvarına (ya da oyuncudan uzak yana) sıçrar ve tutunur
	var lx := 4.0 * Level.TS + size.x * 0.5
	var rx := 82.0 * Level.TS - size.x * 0.5
	var wx := lx if absf(global_position.x - lx) < absf(global_position.x - rx) else rx
	set_meta("wall_x", wx)
	velocity = Vector2(clampf((wx - global_position.x) / 0.7, -1100.0, 1100.0), -560.0)
	facing = 1 if wx < global_position.x else -1
	FX.dust(global_position, Vector2.UP, 8, 0.36)
	Ses.play("sicrayis", -2.0, 0.6)


func _kbh_at_wall() -> bool:
	var wx := float(get_meta("wall_x", global_position.x))
	return absf(global_position.x - wx) < 20.0 or is_on_wall()


func _kbh_cling() -> void:
	flying = true
	velocity = Vector2.ZERO
	facing = 1 if global_position.x < 43.0 * Level.TS else -1
	var p := _pl()
	var tx := _px() + (float(p.velocity.x) * 0.3 if p else 0.0)
	set_meta("dive_x", tx)
	level.telegraph_ground(Vector2(tx, _floor_y()), 1.1)
	FX.text(center() + Vector2(0, -size.y), "!", Color(1.0, 0.35, 0.25), 14)
	Ses.play("uluma", -6.0, 1.1)


func _kbh_dive() -> void:
	flying = false
	var tx := float(get_meta("dive_x", _px()))
	var gy := _floor_y()
	var to := Vector2(tx, gy) - global_position
	velocity = to.normalized() * 820.0
	contact = true
	contact_k = 1.4
	_did_hit = false
	Ses.play("savur_dev", -2.0, 0.6)


func _kbh_dive_tick(_delta: float) -> void:
	var tx := float(get_meta("dive_x", _px()))
	var to := Vector2(tx, _floor_y() + 40.0) - global_position
	velocity = to.normalized() * 820.0
	if Engine.get_physics_frames() % 2 == 0:
		FX.ghost(anim.base, Color(0.9, 0.2, 0.5, 0.4), 0.2)


func _kbh_dive_land() -> void:
	contact = false
	velocity = Vector2.ZERO
	_shake_land(1.0)
	_hit(_box(100.0, 50.0, 0.0, true), 1.0, Vector2(300.0, -240.0))
	_ground_wave(-1, 300.0, 0.6)
	_ground_wave(1, 300.0, 0.6)


func _kbh_crystals(i: int) -> void:
	Ses.play("kut_donusum", -8.0, 1.3)
	var px := _px()
	var n := 3 + phase
	for k in n:
		var tx := px + (k - (n - 1) * 0.5) * 70.0 + (35.0 if i % 2 == 1 else 0.0)
		var p := _lob("stone_big", center() + Vector2(-facing * 10, -30), _arena_x(tx), 0.85, 0.5, 600.0)
		p.trail_col = Color(1.0, 0.3, 0.7, 0.7)
	FX.burst(center() + Vector2(-facing * 10, -30), Color(1.0, 0.4, 0.8), 8, 80, 0.4, 0.16, -40, true)


func _kbh_vanish() -> void:
	untouch = true
	var tw := create_tween()
	tw.tween_property(anim, "modulate:a", 0.08, 0.35)
	FX.anim("smoke_puff", center(), 0.0, 1.2, Color(0.4, 0.2, 0.5), false)
	Ses.play("hayalet_olum", -6.0, 0.6)


func _kbh_clones() -> void:
	# iki sahte kopya oyuncunun iki yanında belirir, sırayla sıçrar; asıl üçüncü olarak gelir
	var px := _px()
	var sides := [-1.0, 1.0]
	sides.shuffle()
	for i in 2:
		var x := _arena_x(px + float(sides[i]) * 260.0)
		var g: Enemy = level.spawn_enemy("kara_boru_han", Vector2(x, global_position.y))
		g.set_meta("golge", true)
		if g is Boss:
			var b := g as Boss
			b.klon = true
			b.decoy = true
			b.hp = 1.0
			b.max_hp = 1.0
			b.dmg = dmg * 0.7
			b.state = "hide"
			b._klon_t = 0.25 + i * 0.45
			b.anim.modulate = Color(0.45, 0.25, 0.7, 0.0)
			b.intro_t = 0.0
	# asıl kopyaların arkasında, üçüncü yandan
	set_meta("emerge_x", _arena_x(px + (randf_range(-1, 1) * 60.0) + (180.0 if randf() < 0.5 else -180.0)))


func _kbh_emerge() -> void:
	global_position.x = float(get_meta("emerge_x", global_position.x))
	untouch = false
	var tw := create_tween()
	tw.tween_property(anim, "modulate:a", 1.0, 0.2)
	FX.anim("void_implosion", center(), 0.0, 1.0, Color(0.6, 0.3, 0.9))
	_face_p()


func _klon_ai(delta: float) -> void:
	## gölge sahte kopya: belirir, "!" ile sıçrar, inince dağılır (tek vuruşta da dağılır)
	match state:
		"hide":
			_klon_t -= delta
			velocity.x = 0.0
			if not _v_show(_an("pounce"), "w", 1):
				anim.play("windup")
			anim.modulate.a = clampf(0.6 - _klon_t, 0.0, 0.6)
			_face_p()
			if _klon_t <= 0.0:
				_seq("klon", [_v(_w(0.4, "windup", "!", "", _face_p), "pounce", "w"),
					_v(_a(1.2, "air", "leap", _kbh_pounce_go, _kbh_air_tick, _landed), "pounce", "a", "air")])
		"recover", "chase", "intro":
			FX.anim("smoke_puff", center(), 0.0, 0.9, Color(0.5, 0.3, 0.7), false)
			dead = true
			remove_from_group("dusman")
			queue_free()
		_:
			if not _step.is_empty():
				_run_step(delta)
				_v_tick(delta)


func _spawn_partner() -> void:
	## 3. evre: gölge eş (canın %12'si; yalnızca sıçrayış / hamle / pençe yağmuru)
	var g: Enemy = level.spawn_enemy("kara_boru_han", Vector2(_arena_x(global_position.x - facing * 120.0), global_position.y))
	g.set_meta("golge", true)
	g.hp = max_hp * 0.12
	g.max_hp = g.hp
	g.dmg = dmg * 0.6
	g.anim.modulate = Color(0.5, 0.3, 0.8, 0.65)
	if g is Boss:
		var b := g as Boss
		b.partner = true
		b.state = "chase"
		b.intro_t = 0.0
		b.shadow_done = true
		b.cd = 1.5
		b.speed *= 1.1
	FX.anim("void_implosion", g.center(), 0.0, 1.6, Color(0.6, 0.3, 0.9))
	Ses.play("hayalet_olum", -4.0, 0.6)


# ================================================================== TEPEGÖZ
## 1: gürz çakışı (önünde kor çatlak bırakır), kaya atışı (işaretli; parçalanır), yer tepme (iki yana şok dalgası:
##    zıpla), kavrama ("!!": yuvarlan; yakalarsa sıkar ve fırlatır, 4 basışla kurtulursan sendeler).
## 2: + göz ışını (yerde sürünen ışın: üstünden zıpla / içinden yuvarlan), hücum (duvara çarparsa GÖZ AÇIK: 2,6 sn
##    ×2 hasar), ikili çakış / ikili tepme. 3: + dağ sarsıntısı (ortaya sıçrar, tavandan kaya yağar), çapraz tarama,
##    üçlü tepme, kombolar.
func _tg_choose() -> String:
	var d := _dist_x()
	var w := {"slam": 3.0 if d < 200.0 else 0.6, "boulder": 2.2 if d > 180.0 else 0.6, "stomp": 2.0, "grab": 2.4 if d < 170.0 else 0.0}
	if phase >= 2:
		w["beam"] = 2.4
		w["charge"] = 1.8 if d > 180.0 else 0.6
	if phase >= 3:
		w["quake"] = 1.6
	if _player_high():
		w["boulder"] = 3.5
		w["grab"] = 0.0
		w["slam"] = 0.0
		if phase >= 2:
			w["beam"] = 3.0
	if _pl_still > 1.5:
		w["boulder"] = float(w["boulder"]) + 2.0
	return _pick(w)


func _tg_start(mv: String) -> void:
	_rec_t = 0.35
	match mv:
		"slam":
			var steps: Array = [_v(_w(0.75, "windup", "!", "", _face_p), "slam", "w"), _v(_a(0.5, "act", "slam", _tg_slam), "slam", "s")]
			if phase >= 2:
				steps += [_v(_w(0.42, "windup", "!", "", _face_p), "slam", "w"), _v(_a(0.55, "act", "slam", _tg_slam), "slam", "s")]
			_seq("slam", steps)
			if phase >= 3 and randf() < 0.5:
				_then("stomp", _tg_stomp_steps(1))
		"boulder":
			var n := 1 if phase == 1 else (2 if phase == 2 else 3)
			var steps2: Array = []
			for i in n:
				steps2 += [_v(_w(0.6 if i == 0 else 0.38, "cast", "!", "", _face_p), "throw", "w"), _v(_a(0.3, "act", "strike", _tg_throw), "throw", "s")]
			_seq("boulder", steps2)
		"stomp":
			_seq("stomp", _tg_stomp_steps(1 if phase == 1 else (2 if phase == 2 else 3)))
		"grab":
			_set_cool("grab", 6.0)
			_seq("grab", [_v(_w(0.55, "windup", "!!", "YUVARLAN!", _face_p), "grab", "w"),
				_v(_a(0.3, "act", "strike", _tg_reach, _tg_reach_tick, _tg_caught), "grab", "s"),
				_v(_a(0.01, "act", "strike", _tg_grab_after), "grab", "s", "hold")])
		"beam":
			_set_cool("beam", 5.0)
			var dir := 1 if randf() < 0.5 else -1
			if phase >= 3:
				_seq("beam", [_v(_w(0.9, "cast", "!", "ZIPLA!", _tg_beam_charge.bind(dir)), "beam", "w"),
					_v(_a(1.1, "act", "cast", _tg_beam_on, _tg_beam_tick.bind(dir)), "beam", "a"),
					_v(_a(0.2, "act", "cast", _tg_beam_pause), "beam", "a", "hold"), _v(_a(1.1, "act", "cast", _tg_beam_on, _tg_beam_tick.bind(-dir)), "beam", "a"),
					_v(_a(0.1, "act", "idle", _tg_beam_off), "beam", "r")])
			else:
				_seq("beam", [_v(_w(0.9, "cast", "!", "ZIPLA!", _tg_beam_charge.bind(dir)), "beam", "w"),
					_v(_a(1.1, "act", "cast", _tg_beam_on, _tg_beam_tick.bind(dir)), "beam", "a"), _v(_a(0.1, "act", "idle", _tg_beam_off), "beam", "r")])
		"charge":
			_set_cool("charge", 6.0)
			_rec_t = 0.6
			_seq("charge", [_v(_w(0.7, "windup", "!", "", _tg_lane), "charge", "w"),
				_v(_a(3.0, "dash", "walk", _tg_charge_go, _tg_charge_tick, _tg_charge_end), "charge", "d"),
				_v(_a(0.01, "act", "idle", _tg_charge_after), "charge", "r")])
		"quake":
			_set_cool("quake", 10.0)
			_rec_t = 0.7
			_seq("quake", [_v(_w(0.6, "windup", "!", ""), "quake", "w"), _v(_a(1.5, "air", "slam", _tg_quake_jump, Callable(), _landed), "quake", "a", "air"),
				_v(_a(0.6, "act", "slam", _tg_quake_land), "quake", "s")])
		_:
			_seq("slam", [_v(_w(0.75), "slam", "w"), _v(_a(0.5, "act", "slam", _tg_slam), "slam", "s")])


func _tg_slam() -> void:
	velocity.x = facing * 60.0
	_shake_land(0.8)
	FX.slash_sprite("arc_heavy", center() + Vector2(facing * 50, -10), 0.2 * facing, Vector2(2.2 * facing, 2.2), _col())
	_hit(_box(135.0, size.y, -10.0), 1.3, Vector2(300.0, -220.0))
	var cx := global_position.x + facing * 110.0
	Tehlike.spawn(level, "catlak", Vector2(cx, global_position.y), 75.0, 0.45, 3.0, dmg * 0.35, self)


func _tg_throw() -> void:
	var p := _pl()
	var tx := _px() + (float(p.velocity.x) * 0.5 if p else 0.0)
	var pr := _lob("stone_big", center() + Vector2(facing * 30, -size.y * 0.45), _arena_x(tx), 0.9, 0.8, 380.0)
	pr.on_explode = Boss._shatter_cb(level, dmg * 0.4, self)
	pr.life = 3.0
	Ses.play("savur_dev", -3.0, 0.6)


static func _shatter_cb(lv: Node, d: float, src: Node) -> Callable:
	## kaya yere çarpınca dört parçaya bölünür (statik: boss ölse de güvenli)
	return func(pos: Vector2) -> void:
		if not is_instance_valid(lv):
			return
		FX.dust(pos, Vector2.UP, 10, 0.4)
		FX.burst(pos, Color(0.7, 0.62, 0.5), 10, 120, 0.4, 0.2, 400)
		Game.shake(2.5)
		for k in 4:
			var p := Projectile.new()
			p.team = "e"
			p.kind = "stone"
			p.damage = d
			p.source = src if is_instance_valid(src) else null
			p.position = pos + Vector2(0, -10)
			p.velocity = Vector2((-1.5 + k) * 110.0, -220.0 - absf(-1.5 + k) * 40.0)
			p.gravity = 600.0
			p.life = 1.6
			lv.add_projectile(p)


func _tg_stomp_steps(n: int) -> Array:
	var s: Array = []
	for i in n:
		s += [_v(_w(0.55 if i == 0 else 0.4, "windup", "!", "ZIPLA!" if i == 0 else ""), "stomp", "w"), _v(_a(0.35, "act", "slam", _tg_stomp), "stomp", "s")]
	return s


func _tg_stomp() -> void:
	_shake_land(0.7)
	_hit(_box(70.0, 40.0, 0.0, true), 0.8, Vector2(240.0, -200.0))
	_ground_wave(-1, 300.0, 0.7)
	_ground_wave(1, 300.0, 0.7)


func _tg_reach() -> void:
	velocity.x = facing * 260.0
	Ses.play("savur_dev", -4.0, 0.7)


func _tg_reach_tick(_delta: float) -> void:
	velocity.x = move_toward(velocity.x, 0.0, 900 * _dt)
	var p := _pl()
	if p and grab_target == null and _box(150.0, size.y * 0.75, -10.0).intersects(p.hurt_rect()) and p.grabbed_by == null and float(p.inv_t) <= 0.0 and float(p.roll_t) <= 0.0:
		p.get_grabbed(self)
		grab_target = p
		FX.anim("tether_catch", p.center(), 0.0, 1.2, Color(1.0, 0.8, 0.5))
		FX.text(center() + Vector2(0, -size.y - 10.0), "YAKALANDIN! (4 kez bas)", Color(1.0, 0.8, 0.4), 9)


func _tg_caught() -> bool:
	return grab_target != null


func _tg_grab_after() -> void:
	if grab_target != null:
		_q = [_v(_a(1.4, "hold", "cast", Callable(), _tg_hold_tick), "grab", "h"), _v(_a(0.35, "act", "strike", _tg_throw_player), "grab", "t", "", "-")]
	else:
		_rec_t = 0.9   # ıskaladı: uzun açık
		_q = []


func _tg_hold_tick(_delta: float) -> void:
	velocity.x = 0.0
	if grab_target == null or not is_instance_valid(grab_target) or grab_target.grabbed_by != self:
		grab_target = null
		_q = []
		st = 0.0
		return
	grab_target.global_position = global_position + Vector2(facing * 40.0, -size.y * 0.62)
	var sq := float(get_meta("sq", 0.25)) - _dt
	if sq <= 0.0:
		sq = 0.35
		grab_target.take_hit(dmg * 0.35, self, null, true)
		vis_scale = Vector2(1.06, 0.95)
		Game.shake(1.5)
	set_meta("sq", sq)


func _tg_throw_player() -> void:
	if grab_target and is_instance_valid(grab_target) and grab_target.grabbed_by == self:
		var g := grab_target
		_drop_grab(Vector2(facing * 420.0, -260.0))
		g.take_hit(dmg * 0.6, self, null, true)
		Game.shake(4.0)
		Ses.play("savur_dev", -2.0, 0.6)
	grab_target = null


func _tg_eye() -> Vector2:
	## v25: gözün dünya konumu sprite'ın kare başına "eye" çapasından (tools/artgen/goz_capasi.py, ışıma sayfasındaki göz
	## parıltısından ölçülür): yöne göre aynalanır, görsel ölçek (ezilme / esneme, seçkin) ve eğilme açısıyla döner. Eskiden
	## gövde boyunun %67'si tahmin ediliyordu ve ışın alakasız bir yerden çıkıyordu. Çapa yoksa eski tahmin.
	var a: Variant = anim.anchor("eye") if anim else null
	if a == null:
		return global_position + Vector2(facing * 30.0, -size.y * 0.67)
	return global_position + ((a as Vector2) * anim.scale).rotated(anim.rotation)


func _tg_beam_charge(dir: int) -> void:
	# dir 1: ışın ayağının dibinden uzağa sürünür; -1: uzaktan ayağına doğru gelir
	_face_p()
	if is_instance_valid(_beam2):
		_beam2.queue_free()
	_beam2 = Isin.new()
	_beam2.kind = "goz"
	_beam2.level = level
	_beam2.source = self
	_beam2.dmg = dmg * 0.55
	_beam2.width = 13.0
	_beam2.follow = _tg_eye   # v25: ışın her karede gözden çıkar (cast karelerinde göz oynar)
	level.fx_root.add_child(_beam2)
	set_meta("bx", 40.0 if dir > 0 else 520.0)
	_beam_aim(float(get_meta("bx")))
	FX.flash_light(_tg_eye(), Color(1.0, 0.3, 0.2), 160.0, 2.0, 0.9)
	Ses.play("buyu", -4.0, 0.6)


func _beam_aim(bx: float) -> void:
	if not is_instance_valid(_beam2):
		return
	_beam2.origin = _tg_eye()
	var target := Vector2(global_position.x + facing * bx, _floor_y() + 6.0)
	_beam2.target = target
	_beam2.aim((target - _beam2.origin).angle(), 900.0)


func _tg_beam_on() -> void:
	if is_instance_valid(_beam2):
		_beam2.on = true
		_beam2.charge = 1.0
	Ses.play("kut_donusum", -4.0, 0.7)
	Game.shake(2.0)


func _tg_beam_tick(delta: float, dir: int) -> void:
	if not is_instance_valid(_beam2):
		return
	if _beam2.on:
		var bx := float(get_meta("bx", 40.0)) + dir * 460.0 * delta
		set_meta("bx", clampf(bx, 30.0, 600.0))
		_beam_aim(float(get_meta("bx")))
		if Engine.get_physics_frames() % 5 == 0:
			Tehlike.spawn(level, "ates", _beam2.tip, 10.0, 0.0, 0.5, dmg * 0.2, self)
	else:
		_beam2.charge = clampf(_beam2.charge + delta / 0.9, 0.0, 1.0)
		_beam_aim(float(get_meta("bx", 40.0)))


func _tg_beam_pause() -> void:
	if is_instance_valid(_beam2):
		_beam2.on = false


func _tg_beam_off() -> void:
	if is_instance_valid(_beam2):
		_beam2.queue_free()
	_beam2 = null


func _tg_lane() -> void:
	_face_p()
	var wx := 82.0 * Level.TS if facing > 0 else 4.0 * Level.TS
	Tehlike.spawn(level, "serit", Vector2((global_position.x + wx) * 0.5, global_position.y), absf(wx - global_position.x) * 0.5, 0.7, 0.05, 0.0, self)


func _tg_charge_go() -> void:
	contact = true
	contact_k = 1.3
	_did_hit = false
	set_meta("hit_player", false)
	Ses.play("savur_dev", -2.0, 0.6)
	FX.ring(center(), 40, _col(), 0.3)


func _tg_charge_tick(_delta: float) -> void:
	velocity.x = move_toward(velocity.x, facing * 470.0, 1600 * _dt)
	anim.speed = 2.2
	if Engine.get_physics_frames() % 2 == 0:
		FX.ghost(anim.base, Color(_col(), 0.3), 0.18)
		FX.dust(global_position + Vector2(-facing * 20, 0), Vector2(-facing, -0.4), 2, 0.3)
	if Engine.get_physics_frames() % 12 == 0:
		Game.shake(1.5)
	if _did_hit:
		set_meta("hit_player", true)


func _tg_charge_end() -> bool:
	return is_on_wall() or (bool(get_meta("hit_player", false)) and st < 2.6)


func _tg_charge_after() -> void:
	anim.speed = 1.0
	contact = false
	velocity.x = 0.0
	if is_on_wall() and not bool(get_meta("hit_player", false)):
		# duvara çarptı: GÖZ AÇIK (ceza penceresi, ×2 hasar)
		Game.shake(8.0)
		Game.hitstop(0.06)
		FX.impact_sprite("blunt", global_position + Vector2(facing * size.x * 0.5, -size.y * 0.5), Vector2(facing, 0), _col(), 1.8)
		Ses.play("darbe_cekic", -1.0, 0.7)
		FX.text(center() + Vector2(0, -size.y * 0.5 - 30.0), "GÖZ AÇIK!", Color(1.0, 0.9, 0.5), 11)
		velocity.x = -facing * 120.0
		vuln_t = 2.6
		vuln_k = 2.0
		broken_t = 2.6
		if _bosslog:
			print("BOSS %s faz=%d GÖZ AÇIK t=%.1f" % [kind, phase, _fight_t])
		_q = [_v(_a(2.6, "vuln", "hurt", Callable(), _tg_vuln_tick), "dazed", "v"), _v(_w(0.35, "rage", "!", ""), "dazed", "w"),
			_v(_a(0.4, "act", "rage", _tg_rise_roar), "roar", "a", "fast")]


func _tg_vuln_tick(_delta: float) -> void:
	velocity.x = move_toward(velocity.x, 0.0, 400 * _dt)
	if Engine.get_physics_frames() % 6 == 0:
		FX.burst(_tg_eye(), Color(1.0, 0.95, 0.6), 2, 40, 0.4, 0.16, -20, true)
		FX.ring(_tg_eye(), 12.0, Color(1.0, 0.85, 0.4, 0.8), 0.15)


func _tg_rise_roar() -> void:
	broken_t = 0.0
	Ses.play("agac_olum", -2.0, 0.6)
	FX.ring(center(), 100, _col(), 0.4)
	_hit(_box(100.0, size.y, 0.0, true), 0.4, Vector2(300.0, -200.0))


func _tg_quake_jump() -> void:
	velocity = _leap_v(43.0 * Level.TS, 125.0)
	sa_t = 2.0
	FX.dust(global_position, Vector2.UP, 12, 0.42)
	Ses.play("sicrayis", -2.0, 0.5)


func _tg_quake_land() -> void:
	_shake_land(1.0)
	_hit(_box(110.0, 60.0, 0.0, true), 1.2, Vector2(320.0, -260.0))
	_ground_wave(-1, 320.0, 0.7)
	_ground_wave(1, 320.0, 0.7)
	var px := _px()
	for i in 6:
		var x := _arena_x(px + (i - 2.5) * 95.0 + randf_range(-20, 20))
		_drop_from_sky(x, "stone_big", 0.5 + i * 0.18, 0.7)


# ================================================================== ŞAHMERAN ANA
## 1: zehir tükürüğü (üç yay; inişte zehir gölü), kuyruk süpürmesi (alçak: zıpla), sokma (çöreklenir, uzun atılış;
##    ıskalarsa başı 0,8 sn yere saplanır: ×1,5). 2: + yılan sürüsü, mağara yıkımı (kuyruk tavana: sıralı damla
##    yağmuru), sokma → kuyruk kombosu. 3: + taşlaştıran bakış ("ARKANI DÖN!": bakana dönük olan taşlaşır, ardından
##    sokma), zehir pınarı (duranın altından sırayla fışkıran göller); ÖFKE: beşli tükürük, ikili sokma.
func _sh_choose() -> String:
	var d := _dist_x()
	var w := {"spit": 2.4 if d > 140.0 else 0.8, "tail": 3.0 if d < 180.0 else 0.4, "lunge": 2.6 if d > 90.0 else 1.0}
	if phase >= 2:
		w["snakes"] = 1.4 if _adds_alive() < 3 else 0.0
		w["drip"] = 1.6
	if phase >= 3:
		w["gaze"] = 1.8
		w["venom"] = 1.8
	if _player_high():
		w["spit"] = 3.5
		w["tail"] = 0.0
		if phase >= 2:
			w["drip"] = 3.0
	if _pl_still > 1.2 and phase >= 3:
		w["venom"] = float(w["venom"]) + 3.0
	return _pick(w)


func _sh_start(mv: String) -> void:
	_rec_t = 0.32
	match mv:
		"spit":
			_seq("spit", [_v(_w(0.55, "cast", "!", "", _face_p), "spit", "w"), _v(_a(0.5, "act", "cast", _sh_spit), "spit", "s")])
		"tail":
			var steps: Array = [_v(_w(0.6, "windup", "!", "ZIPLA!", _sh_rattle), "tail", "w"), _v(_a(0.45, "act", "strike", _sh_tail), "tail", "s")]
			_seq("tail", steps)
		"lunge":
			var steps2 := _sh_lunge_steps()
			if enraged:
				steps2 += _sh_lunge_steps()
			_seq("lunge", steps2)
			if phase >= 2 and randf() < 0.45:
				_then("tail", [_v(_w(0.4, "windup", "!", "ZIPLA!", _sh_rattle), "tail", "w"), _v(_a(0.45, "act", "strike", _sh_tail), "tail", "s")])
		"snakes":
			_set_cool("snakes", 14.0)
			_seq("snakes", [_v(_w(0.6, "rage", "!", ""), "snakes", "w"), _v(_a(0.7, "act", "rage", _sh_snakes), "snakes", "a")])
		"drip":
			_set_cool("drip", 8.0)
			_seq("drip", [_v(_w(0.6, "strike", "!", "TAVAN!"), "drip", "w"), _v(_a(0.9, "act", "slam", _sh_drip), "drip", "s")])
		"gaze":
			_set_cool("gaze", 9.0)
			_seq("gaze", [_v(_w(1.0, "cast", "!!", "ARKANI DÖN!", _sh_gaze_charge), "gaze", "w"), _v(_a(0.25, "act", "cast", _sh_gaze_fire), "gaze", "s")])
		"venom":
			_set_cool("venom", 8.0)
			_seq("venom", [_v(_w(0.5, "cast", "!", ""), "venom", "w"), _v(_a(0.45, "act", "cast", _sh_venom), "venom", "a"),
				_v(_a(0.45, "act", "cast", _sh_venom), "venom", "a"), _v(_a(0.45, "act", "cast", _sh_venom), "venom", "a"),
				_v(_a(0.45, "act", "cast", _sh_venom), "venom", "a")])
		_:
			_seq("spit", [_v(_w(0.55), "spit", "w"), _v(_a(0.5, "act", "cast", _sh_spit), "spit", "s")])


func _sh_spit() -> void:
	var px := _px()
	var n := 3 if not enraged else 5
	var mouth := center() + Vector2(facing * 26, -size.y * 0.35)
	for k in n:
		var tx := _arena_x(px + (k - (n - 1) * 0.5) * 85.0)
		var p := _lob("spore", mouth, tx, 0.8, 0.5, 460.0)
		p.homing = 0.0
		p.trail_col = Color(0.5, 1.0, 0.35, 0.7)
		p.on_explode = Boss._pool_cb(level, dmg * 0.3, self)
	Ses.play("buyu", -4.0, 1.2)
	FX.anim("acid_splash", mouth, 0.0, 0.6, Color(0.6, 1.0, 0.4))


static func _pool_cb(lv: Node, d: float, src: Node) -> Callable:
	return func(pos: Vector2) -> void:
		if is_instance_valid(lv):
			Tehlike.spawn(lv, "zehir", pos, 40.0, 0.2, 4.0, d, src if is_instance_valid(src) else null)


func _sh_rattle() -> void:
	_face_p()
	FX.dust(global_position + Vector2(-facing * 40, 0), Vector2(-facing, -0.5), 8, 0.3, Color(0.5, 0.7, 0.4, 0.6))
	Ses.play("sarsinti", -8.0, 1.6)


func _sh_tail() -> void:
	velocity.x = facing * 80.0
	FX.slash(global_position + Vector2(0, -16), facing, -0.5, 0.5, 120.0, 9.0, Color(0.5, 1.0, 0.5), 0.2)
	FX.slash(global_position + Vector2(0, -16), -facing, -0.5, 0.5, 90.0, 9.0, Color(0.5, 1.0, 0.5), 0.2)
	FX.dust(global_position + Vector2(facing * 80, 0), Vector2(facing, -0.3), 10, 0.36)
	Ses.play("savur_dev", -3.0, 1.0)
	# alçak süpürme: önde 210, arkada 120 px, yerden 34 px (zıplayan geçer)
	var r := Rect2(global_position.x - (120.0 if facing > 0 else 210.0), global_position.y - 34.0, 330.0, 34.0)
	_hit(r, 1.0, Vector2(280.0, -200.0))


func _sh_lunge_steps() -> Array:
	return [_v(_w(0.55, "windup", "!", "", _sh_coil), "lunge", "w"), _v(_a(0.28, "dash", "strike", _sh_lunge_go, _sh_lunge_tick), "lunge", "d"),
		_v(_a(0.01, "act", "strike", _sh_lunge_after), "lunge", "x", "hold")]


func _sh_coil() -> void:
	_face_p()
	vis_scale = Vector2(1.2, 0.8)


func _sh_lunge_go() -> void:
	contact = true
	contact_k = 1.1
	_did_hit = false
	velocity.x = facing * 1050.0
	Ses.play("isirik", -2.0, 0.6)


func _sh_lunge_tick(_delta: float) -> void:
	velocity.x = facing * 1050.0
	if Engine.get_physics_frames() % 2 == 0:
		FX.ghost(anim.base, Color(0.5, 1.0, 0.5, 0.35), 0.18)


func _sh_lunge_after() -> void:
	contact = false
	velocity.x = facing * 60.0
	if not _did_hit:
		# ıskaladı: başı yere saplandı (ceza penceresi)
		vuln_t = 0.8
		vuln_k = 1.5
		FX.dust(global_position + Vector2(facing * 40, 0), Vector2.UP, 8, 0.34)
		FX.text(center() + Vector2(0, -size.y * 0.5 - 20.0), "saplandı!", Color(0.8, 1.0, 0.6), 8)
		_q.push_front(_v(_a(0.8, "vuln", "hurt"), "lunge", "v"))


func _sh_snakes() -> void:
	Ses.play("hayalet_olum", -4.0, 0.9)
	var n := mini(4 - _adds_alive(), 3)
	for i in n:
		var e := _spawn_add("kirkayak", Vector2(_arena_x(global_position.x + (i - 1) * 70.0), global_position.y - 10.0), 0.5)
		e.anim.modulate = Color(0.6, 1.0, 0.55, 1.0)
		e.flank = i % 2


func _sh_drip() -> void:
	_shake_land(0.6)
	var px := _px()
	var dir := 1.0 if randf() < 0.5 else -1.0
	for i in 7:
		var x := _arena_x(px + dir * (i - 3) * 75.0)
		_drop_from_sky(x, "stone", 0.35 + i * 0.16, 0.7)


func _sh_gaze_charge() -> void:
	_face_p()
	FX.flash_light(center() + Vector2(facing * 20, -size.y * 0.35), Color(0.6, 1.0, 0.5), 200.0, 2.0, 1.0)
	FX.ring(center() + Vector2(facing * 20, -size.y * 0.35), 30.0, Color(0.7, 1.0, 0.6, 0.8), 1.0)


func _sh_gaze_fire() -> void:
	var p := _pl()
	FX.ring(center(), 260.0, Color(0.6, 1.0, 0.5, 0.6), 0.4)
	Ses.play("kut_donusum", -2.0, 1.3)
	if p == null:
		return
	var looking: bool = int(p.facing) == int(signf(global_position.x - float(p.global_position.x)))
	if looking and float(p.roll_t) <= 0.0 and float(p.inv_t) <= 0.0 and absf(float(p.global_position.x) - global_position.x) < 520.0:
		# taşlaştı: kısa süre kıpırdayamaz; Şahmeran hemen sokar
		p.hurt_t = maxf(float(p.hurt_t), 1.1)
		p.velocity = Vector2.ZERO
		FX.text(p.center() + Vector2(0, -36), "TAŞLAŞTIN!", Color(0.75, 0.8, 0.7), 10)
		FX.anim("frost_nova", p.center(), 0.0, 0.8, Color(0.7, 0.75, 0.65))
		_q = _sh_lunge_steps()
	else:
		FX.text(p.center() + Vector2(0, -36), "bakmadın", Color(0.85, 1.0, 0.8), 8)


func _sh_venom() -> void:
	var p := _pl()
	var x := _px() + (float(p.velocity.x) * 0.25 if p else 0.0)
	Tehlike.spawn(level, "zehir", Vector2(_arena_x(x), global_position.y), 38.0, 0.55, 2.2, dmg * 0.35, self)
	Ses.play("buyu", -9.0, 1.4)


# ================================================================== YELBEGEN
## 1: gürz savuruşu, yel üfürüğü (2,2 sn seni duvara iter; rüzgârla buz parçaları gelir: zıpla), üç baş (sırayla buz
##    parçası, üçlü yelpaze, inişte buz dikeni). 2: + ayaz soluğu (önünde yere sürünen huzme, arkasında buz dikenleri),
##    saçak yağmuru + üfürük kombosu. 3: + Kaf fırtınası (rüzgâr yön değiştirir, buz yağar, başlar ateş eder), buzlu
##    sıçrayış; ÖFKE: beş baş atışı.
func _yb_choose() -> String:
	var d := _dist_x()
	var w := {"club": (5.0 if d < 120.0 else 3.0) if d < 170.0 else 0.4, "gust": 1.0, "heads": 1.8 if d > 140.0 else 0.3}
	if phase >= 2:
		w["breath"] = 2.4 if d < 260.0 else 0.6
		w["icicles"] = 1.6
	if phase >= 3:
		w["blizzard"] = 1.6
		w["leap_ice"] = 1.8
	if _player_high():
		w["heads"] = 3.5
		w["club"] = 0.0
		if phase >= 2:
			w["icicles"] = 3.0
	if _pl_still > 1.5:
		w["heads"] = float(w["heads"]) + 2.0
	return _pick(w)


func _yb_start(mv: String) -> void:
	_rec_t = 0.35
	match mv:
		"club":
			var steps: Array = [_v(_w(0.65, "windup", "!", "", _face_p), "club", "w"), _v(_a(0.45, "act", "strike", _yb_club), "club", "s")]
			if (phase >= 2 and randf() < 0.5) or _dist_x() < 120.0:
				steps += [_v(_w(0.4, "windup", "!", "", _face_p), "club", "w"), _v(_a(0.45, "act", "strike", _yb_club), "club", "s")]
			_seq("club", steps)
		"gust":
			_set_cool("gust", 9.0)
			_seq("gust", [_v(_w(0.6, "cast", "!", "DİREN!", _face_p), "gust", "w"), _v(_a(2.2, "act", "cast", _yb_gust_on, _yb_gust_tick), "gust", "a"),
				_v(_a(0.1, "act", "idle", _yb_gust_off), "gust", "r")])
		"heads":
			var n := 3 if not enraged else 5
			var steps2: Array = [_v(_w(0.5, "cast", "!", "", _face_p), "heads", "w")]
			for i in n:
				steps2.append(_v(_a(0.42, "act", "cast", _yb_head.bind(i % 3)), "heads", ["b", "c", "f"][i % 3]))
			_seq("heads", steps2)
		"breath":
			_set_cool("breath", 6.0)
			_seq("breath", [_v(_w(0.8, "windup", "!", "", _yb_breath_charge), "breath", "w"), _v(_a(1.2, "act", "cast", _yb_breath_on, _yb_breath_tick), "breath", "a"),
				_v(_a(0.1, "act", "idle", _tg_beam_off), "breath", "r")])
		"icicles":
			_set_cool("icicles", 8.0)
			var st2: Array = [_v(_w(0.55, "rage", "!", ""), "icicles", "w"), _v(_a(0.6, "act", "rage", _yb_icicles), "icicles", "s")]
			if randf() < 0.6:
				st2 += [_v(_w(0.4, "cast", "!", "DİREN!", _face_p), "gust", "w"), _v(_a(1.6, "act", "cast", _yb_gust_on, _yb_gust_tick), "gust", "a"),
					_v(_a(0.1, "act", "idle", _yb_gust_off), "gust", "r")]
			_seq("icicles", st2)
		"blizzard":
			_set_cool("blizzard", 14.0)
			_seq("blizzard", [_v(_w(0.7, "rage", "!", "KAF FIRTINASI!"), "blizzard", "w"), _v(_a(4.2, "act", "cast", _yb_storm_on, _yb_storm_tick), "blizzard", "a"),
				_v(_a(0.1, "act", "idle", _yb_gust_off), "blizzard", "r")])
		"leap_ice":
			_set_cool("leap_ice", 5.0)
			_rec_t = 0.65
			_seq("leap_ice", [_v(_w(0.55, "windup", "!", "", _face_p), "leap", "w"), _v(_a(1.5, "air", "slam", _yb_leap, Callable(), _landed), "leap", "a", "air"),
				_v(_a(0.5, "act", "slam", _yb_leap_land), "leap", "s")])
		_:
			_seq("club", [_v(_w(0.65), "club", "w"), _v(_a(0.45, "act", "strike", _yb_club), "club", "s")])


func _yb_club() -> void:
	velocity.x = facing * 140.0
	FX.slash_sprite("arc_heavy", center() + Vector2(facing * 40, -10), 0.2 * facing, Vector2(2.4 * facing, 2.4), _col())
	FX.dust(global_position + Vector2(facing * 80, 0), Vector2(facing, -0.5), 8, 0.36)
	Ses.play("savur_dev", -1.0, 0.75)
	Game.shake(4.0)
	_hit(_box(140.0, size.y, -10.0), 1.2, Vector2(300.0, -200.0))


func _yb_gust_on() -> void:
	var p := _pl()
	_gust_dir = signf(float(p.global_position.x) - global_position.x) if p else float(facing)
	if _gust_dir == 0.0:
		_gust_dir = float(facing)
	_gust_f = 125.0
	var g := Ruzgar.new()
	g.dir = _gust_dir
	g.life = float(_step.get("t", 2.0))
	g.level = level
	level.fx_root.add_child(g)
	Ses.play("ruzgar" if Ses.has("ruzgar") else "buyu", -2.0, 0.6)


func _yb_gust_tick(delta: float) -> void:
	# rüzgârla buz parçaları, okunur düzende: alçak (üstünden zıpla), alçak, yüksek (altında dur, zıplama)
	var gt := float(get_meta("gt", 0.3)) - delta
	if gt <= 0.0:
		gt = 0.5
		var n := int(get_meta("gn", 0))
		set_meta("gn", n + 1)
		var y := _floor_y() - (10.0 if n % 3 != 2 else 50.0)
		var x0 := global_position.x + _gust_dir * 30.0
		_shoot("ice", Vector2(x0, y), Vector2(_gust_dir * 300.0, 0.0), 0.4, 0.0, 0.0, 3.0)
	set_meta("gt", gt)


func _yb_gust_off() -> void:
	_gust_f = 0.0


func _apply_gust(delta: float) -> void:
	var p := _pl()
	if p and p.grabbed_by == null:
		p.move_and_collide(Vector2(_gust_dir * _gust_f * delta, 0.0))


func _yb_head(i: int) -> void:
	var p := _pl()
	var heads := [Vector2(-18, -size.y * 0.95), Vector2(0, -size.y * 1.02), Vector2(18, -size.y * 0.95)]
	var hp0: Vector2 = global_position + Vector2(facing * float(heads[i].x), float(heads[i].y))
	FX.flash_light(hp0, _col(), 90.0, 1.6, 0.18)
	FX.ring(hp0, 10.0, Color(0.8, 0.95, 1.0, 0.8), 0.15)
	Ses.play("buyu", -6.0, 0.9 + i * 0.15)
	if p == null:
		return
	var aim: Vector2 = p.center() + Vector2(float(p.velocity.x) * 0.25, 0.0) - hp0
	match i:
		0:
			_shoot("ice", hp0, aim.normalized() * 340.0, 0.6, 0.0)
		1:
			for s in [-0.2, 0.2]:
				_shoot("ice", hp0, aim.normalized().rotated(float(s)) * 280.0, 0.45, 0.0)
		_:
			var pr := _lob("ice", hp0, _arena_x(float(p.global_position.x)), 0.8, 0.5, 420.0)
			pr.on_explode = Boss._spike_cb(level, dmg * 0.6, self)


static func _spike_cb(lv: Node, d: float, src: Node) -> Callable:
	return func(pos: Vector2) -> void:
		if is_instance_valid(lv):
			Tehlike.spawn(lv, "buz", pos, 34.0, 0.3, 0.6, d, src if is_instance_valid(src) else null)


func _yb_breath_charge() -> void:
	_face_p()
	if is_instance_valid(_beam2):
		_beam2.queue_free()
	_beam2 = Isin.new()
	_beam2.kind = "ayaz"
	_beam2.level = level
	_beam2.source = self
	_beam2.dmg = dmg * 0.4
	_beam2.width = 22.0
	level.fx_root.add_child(_beam2)
	set_meta("bx", 30.0)
	_yb_breath_aim()


func _yb_breath_aim() -> void:
	if not is_instance_valid(_beam2):
		return
	_beam2.origin = global_position + Vector2(facing * 14.0, -size.y * 0.95)
	var target := Vector2(global_position.x + facing * float(get_meta("bx", 30.0)), _floor_y() + 6.0)
	_beam2.aim((target - _beam2.origin).angle(), 700.0)


func _yb_breath_on() -> void:
	if is_instance_valid(_beam2):
		_beam2.on = true
	Ses.play("buz_kir" if Ses.has("buz_kir") else "buyu", -4.0, 0.7)


func _yb_breath_tick(delta: float) -> void:
	if not is_instance_valid(_beam2):
		return
	if _beam2.on:
		set_meta("bx", minf(300.0, float(get_meta("bx", 30.0)) + 230.0 * delta))
		if Engine.get_physics_frames() % 12 == 0:
			Tehlike.spawn(level, "buz", _beam2.tip, 22.0, 0.35, 0.8, dmg * 0.5, self)
	else:
		_beam2.charge = clampf(_beam2.charge + delta / 0.8, 0.0, 1.0)
	_yb_breath_aim()


func _yb_icicles() -> void:
	_shake_land(0.5)
	var px := _px()
	for i in 8:
		var x := _arena_x(px + (i - 3.5) * 70.0 + randf_range(-15, 15))
		_drop_from_sky(x, "ice", 0.4 + (i % 4) * 0.18 + (0.5 if i >= 4 else 0.0), 0.6)


func _yb_storm_on() -> void:
	_gust_dir = 1.0 if randf() < 0.5 else -1.0
	_gust_f = 120.0
	set_meta("storm_t", 1.3)
	var g := Ruzgar.new()
	g.dir = _gust_dir
	g.life = 1.3
	g.level = level
	g.snow = true
	level.fx_root.add_child(g)


func _yb_storm_tick(delta: float) -> void:
	var t := float(get_meta("storm_t", 1.3)) - delta
	if t <= 0.0:
		t = 1.3
		_gust_dir = -_gust_dir
		FX.text(center() + Vector2(0, -size.y - 20.0), "→" if _gust_dir > 0 else "←", Color(0.85, 0.95, 1.0), 12)
		var g := Ruzgar.new()
		g.dir = _gust_dir
		g.life = 1.3
		g.level = level
		g.snow = true
		level.fx_root.add_child(g)
	set_meta("storm_t", t)
	if Engine.get_physics_frames() % 18 == 0:
		_drop_from_sky(_arena_x(_px() + randf_range(-140, 140)), "ice", 0.35, 0.5)
	if Engine.get_physics_frames() % 50 == 25:
		_yb_head(randi() % 2)


func _yb_leap() -> void:
	var p := _pl()
	velocity = _leap_v(_px() + (float(p.velocity.x) * 0.4 if p else 0.0), 120.0)
	sa_t = 1.8
	contact = true
	contact_k = 1.2
	_did_hit = false
	FX.dust(global_position, Vector2.UP, 10, 0.4)


func _yb_leap_land() -> void:
	contact = false
	_shake_land(0.9)
	_hit(_box(90.0, 50.0, 0.0, true), 1.0, Vector2(300.0, -220.0))
	for s in [-1, 1]:
		for k in 3:
			Tehlike.spawn(level, "buz", Vector2(global_position.x + s * (70.0 + k * 60.0), global_position.y), 22.0, 0.15 + k * 0.15, 0.6, dmg * 0.55, self)


# ================================================================== ERLİK HAN
## 1: kara zincir (değerse seni çeker, ardından yukarı savuruş), ateş dalgası (iki yana; inişte kor), Tamu ateşi
##    (yelpaze yay ateş topu), tırpan savuruşu. 2: + kor sütunları (duran oyuncunun yerinde sırayla), kayıp ruhlar,
##    daralan Tamu (kenarlardan içeri yürüyen alev duvarı). 3: + TAMU SELİ (v25; eski adı Âlem kayması): zemin lav olur,
##    üç taş platform güvenli; sonra gök kapanır, platformlara kor yağar: aşağı in. ÖFKE: ikili zincir.
func _er_choose() -> String:
	var d := _dist_x()
	var w := {"chain": 2.6 if d > 80.0 else 0.8, "firewave": 2.0, "fireballs": 2.2 if d > 160.0 else 0.8, "scythe": 3.0 if d < 160.0 else 0.3,
		"gate": 1.8 if phase == 1 else 2.4}
	if phase >= 2:
		w["pillars"] = 2.2
		w["souls"] = 1.2 if _adds_alive() < 3 else 0.0
		w["walls"] = 1.0
	if phase >= 3:
		w["tamu_seli"] = 1.8
	if _player_high():
		w["fireballs"] = 3.0
		w["scythe"] = 0.0
		if phase >= 2:
			w["pillars"] = 3.0
	if _pl_still > 1.2 and phase >= 2:
		w["pillars"] = float(w["pillars"]) + 3.0
	return _pick(w)


func _er_start(mv: String) -> void:
	_rec_t = 0.35
	match mv:
		"chain":
			var steps := _er_chain_steps()
			if enraged:
				steps += _er_chain_steps()
			_seq("chain", steps)
		"firewave":
			var s2: Array = [_v(_w(0.6, "windup", "!", "ZIPLA!", _face_p), "wave", "w"), _v(_a(0.5, "act", "slam", _er_wave), "wave", "s")]
			if phase >= 2:
				s2 += [_v(_w(0.4, "windup", "!", ""), "wave", "w"), _v(_a(0.5, "act", "slam", _er_wave), "wave", "s")]
			_seq("firewave", s2)
		"fireballs":
			_seq("fireballs", [_v(_w(0.55, "cast", "!", "", _face_p), "fireballs", "w"), _v(_a(0.6, "act", "cast", _er_fireballs), "fireballs", "s")])
		"scythe":
			_seq("scythe", [_v(_w(0.6, "windup", "!", "", _face_p), "scythe", "w"), _v(_a(0.4, "act", "strike", _er_scythe.bind(1.2)), "scythe", "s"),
				_v(_w(0.32, "windup", "!", "", _face_p), "scythe", "W"), _v(_a(0.45, "act", "strike", _er_scythe.bind(1.0)), "scythe", "S")])
		"pillars":
			_set_cool("pillars", 7.0)
			var s3: Array = [_v(_w(0.5, "cast", "!", ""), "pillars", "w")]
			for i in 6:
				s3.append(_v(_a(0.32, "act", "cast", _er_pillar), "pillars", "a"))
			_seq("pillars", s3)
		"gate":
			_set_cool("gate", 4.5)
			_seq("gate", [_v(_w(0.4, "cast", "!", ""), "gate", "w"), _v(_a(0.5, "hide", "cast", _er_sink), "gate", "k"),
				_v(_a(0.45, "hide", "idle", _er_gate_pick), "gate", "h", "hold"), _v(_a(0.4, "act", "rage", _er_rise), "gate", "e")])
			if randf() < 0.6:
				if randf() < 0.5:
					_then("scythe", [_v(_w(0.4, "windup", "!", "", _face_p), "scythe", "w"), _v(_a(0.45, "act", "strike", _er_scythe.bind(1.1)), "scythe", "s")])
				else:
					_then("firewave", [_v(_w(0.45, "windup", "!", "ZIPLA!", _face_p), "wave", "w"), _v(_a(0.5, "act", "slam", _er_wave), "wave", "s")])
		"souls":
			_set_cool("souls", 14.0)
			_seq("souls", [_v(_w(0.6, "rage", "!", ""), "souls", "w"), _v(_a(0.7, "act", "rage", _er_souls), "souls", "a")])
		"walls":
			_set_cool("walls", 16.0)
			_seq("walls", [_v(_w(0.6, "rage", "!", "TAMU DARALIYOR!"), "walls", "w"), _v(_a(0.5, "act", "rage", _er_walls), "walls", "s")])
		"tamu_seli":
			_set_cool("tamu_seli", 14.0)
			_rec_t = 0.6
			_seq("tamu_seli", [_v(_w(1.4, "rage", "!!", "TAMU TAŞIYOR — PLATFORMLARA ÇIK!", _er_sel_warn), "seli", "w"),
				_v(_a(4.5, "act", "cast", _er_lava_on, _er_lava_tick), "seli", "L"),
				_v(_w(1.0, "cast", "!!", "KOR YAĞIYOR — AŞAĞI İN!", _er_sky_warn), "seli", "V"), _v(_a(2.6, "act", "cast", _er_sky_on, _er_sky_tick), "seli", "K"),
				_v(_a(0.1, "act", "idle", _er_sel_end), "seli", "r")])
		_:
			_seq("scythe", [_v(_w(0.6), "scythe", "w"), _v(_a(0.4, "act", "strike", _er_scythe.bind(1.2)), "scythe", "s")])


func _er_sink() -> void:
	## Tamu kapısı: yere batar (erişilmez), oyuncunun öbür yanında kor halkasıyla yükselir
	untouch = true
	var tw := create_tween()
	tw.tween_property(anim, "modulate:a", 0.08, 0.35)
	FX.fire(global_position, 14, 0.5, 30.0)
	FX.ring(global_position + Vector2(0, -6), 50.0, Color(1.0, 0.5, 0.2, 0.8), 0.4, 0.35)
	Ses.play("kut_donusum", -6.0, 0.6)


func _er_gate_pick() -> void:
	var px := _px()
	var side := -_side_of(_pl()) if _pl() else float(facing)
	var nx := _arena_x(px + side * 210.0)
	if absf(nx - px) < 120.0:
		nx = _arena_x(px - side * 210.0)
	set_meta("gate_x", nx)
	Tehlike.spawn(level, "ates", Vector2(nx, global_position.y), 34.0, 0.0, 0.45, 0.0, self)
	level.telegraph_ground(Vector2(nx, global_position.y), 0.45)


func _er_rise() -> void:
	global_position.x = float(get_meta("gate_x", global_position.x))
	untouch = false
	var tw := create_tween()
	tw.tween_property(anim, "modulate:a", 1.0, 0.15)
	_face_p()
	FX.fire(global_position, 16, 0.5, 26.0)
	FX.ring(center(), 80.0, _col(), 0.35)
	Game.shake(4.0)
	Ses.play("sarsinti", -4.0, 0.8)
	_hit(_box(80.0, size.y, 0.0, true), 0.7, Vector2(260.0, -220.0))


func _er_chain_steps() -> Array:
	return [_v(_w(0.55, "windup", "!", "", _face_p), "chain", "w"), _v(_a(0.5, "act", "strike", _er_chain_go, _er_chain_tick, _er_chain_caught), "chain", "s", "fast"),
		_v(_a(0.01, "act", "strike", _er_chain_after), "chain", "s", "hold")]


func _er_hand() -> Vector2:
	return global_position + Vector2(facing * 26.0, -size.y * 0.55)


func _er_chain_go() -> void:
	if is_instance_valid(_beam2):
		_beam2.queue_free()
	_beam2 = Isin.new()
	_beam2.kind = "zincir"
	_beam2.level = level
	_beam2.source = self
	level.fx_root.add_child(_beam2)
	_beam2.origin = _er_hand()
	_beam2.tip = _beam2.origin
	set_meta("cl", 0.0)
	var p := _pl()
	set_meta("cy", float(p.center().y) if p else _er_hand().y)
	set_meta("caught", false)
	Ses.play("savur_kamci" if Ses.has("savur_kamci") else "savur_bicak", -3.0, 0.7)


func _er_chain_tick(delta: float) -> void:
	if not is_instance_valid(_beam2):
		return
	var cl := minf(330.0, float(get_meta("cl", 0.0)) + 1300.0 * delta)
	set_meta("cl", cl)
	_beam2.origin = _er_hand()
	var aim := Vector2(facing * cl, float(get_meta("cy")) - _beam2.origin.y).limit_length(cl)
	_beam2.tip = _beam2.origin + aim
	var p := _pl()
	if p and _beam2.touches(p.hurt_rect()) and float(p.roll_t) <= 0.0 and p.grabbed_by == null:
		if p.take_hit(dmg * 0.7, self):
			set_meta("caught", true)


func _er_chain_caught() -> bool:
	return bool(get_meta("caught", false))


func _er_chain_after() -> void:
	if bool(get_meta("caught", false)):
		# çek, sonra yukarı savur
		_q = [_v(_a(0.3, "act", "strike", Callable(), _er_pull_tick), "chain", "p"), _v(_w(0.18, "windup", "!", ""), "chain", "u"),
			_v(_a(0.4, "act", "strike", _er_scythe.bind(1.0)), "chain", "U"), _v(_a(0.01, "act", "idle", _tg_beam_off), "chain", "U", "hold")]
	else:
		_q = [_v(_a(0.25, "act", "idle", Callable(), _er_retract_tick), "chain", "m"), _v(_a(0.01, "act", "idle", _tg_beam_off), "chain", "m", "hold")]


func _er_pull_tick(delta: float) -> void:
	var p := _pl()
	if p and p.grabbed_by == null:
		var tx := global_position.x + facing * 50.0
		p.move_and_collide(Vector2(clampf(tx - float(p.global_position.x), -900.0 * delta, 900.0 * delta), 0.0))
		if is_instance_valid(_beam2):
			_beam2.origin = _er_hand()
			_beam2.tip = p.center()


func _er_retract_tick(delta: float) -> void:
	if is_instance_valid(_beam2):
		_beam2.origin = _er_hand()
		_beam2.tip = _beam2.tip.lerp(_beam2.origin, clampf(10.0 * delta, 0.0, 1.0))


func _er_scythe(k: float) -> void:
	velocity.x = facing * 150.0
	FX.slash_sprite("arc_heavy", center() + Vector2(facing * 40, -10), 0.2 * facing, Vector2(2.2 * facing, 2.2), _col())
	Ses.play("savur_dev", -2.0, 0.7)
	Game.shake(3.5)
	_hit(_box(130.0, size.y, -10.0), k, Vector2(280.0, -260.0))


func _er_wave() -> void:
	_shake_land(0.7)
	_hit(_box(size.x * 0.5 + 40.0, 50.0, 0.0, true), 0.8, Vector2(260.0, -200.0))
	FX.anim("earth_rupture", global_position + Vector2(facing * 30, 0), 0.0, 1.4, _col(), false)
	_ground_wave(-1, 290.0, 0.7)
	_ground_wave(1, 290.0, 0.7)
	for s in [-1, 1]:
		Tehlike.spawn(level, "ates", Vector2(global_position.x + s * 90.0, global_position.y), 26.0, 0.25, 1.6, dmg * 0.3, self)


func _er_fireballs() -> void:
	var p := _pl()
	var hand := _er_hand()
	var n := 3 + phase * 2
	var px := _px()
	for k in n:
		var tx := _arena_x(px + (k - (n - 1) * 0.5) * 60.0 + (float(p.velocity.x) * 0.3 if p else 0.0))
		var pr := _lob("fireball", hand, tx, 0.75 + absf(k - (n - 1) * 0.5) * 0.06, 0.55, 300.0)
		pr.on_explode = Boss._fire_cb(level, dmg * 0.25, self)
	Ses.play("buyu", -2.0, 0.7)
	FX.flash_light(hand, _col(), 140.0, 1.6, 0.2)


static func _fire_cb(lv: Node, d: float, src: Node) -> Callable:
	return func(pos: Vector2) -> void:
		if is_instance_valid(lv):
			FX.fire(pos, 8, 0.4, 6.0)
			Tehlike.spawn(lv, "ates", pos, 18.0, 0.0, 1.2, d, src if is_instance_valid(src) else null)


func _er_pillar() -> void:
	var p := _pl()
	var x := _px() + (float(p.velocity.x) * 0.3 if p else 0.0)
	Tehlike.spawn(level, "sutun", Vector2(_arena_x(x), global_position.y), 22.0, 0.6, 0.45, dmg * 0.8, self)


func _er_souls() -> void:
	Ses.play("kut_donusum", -4.0, 0.9)
	var n := mini(4 - _adds_alive(), 3)
	for i in n:
		var e := _spawn_add("kayip_ruh", Vector2(_arena_x(global_position.x + (i - 1) * 80.0), global_position.y - 90.0), 0.6)
		e.flank = i % 2


func _er_walls() -> void:
	# kenarlardan içeri yürüyen alev duvarı: 6 sn içinde arena ortadaki ~520 px'e daralır, sonra söner
	var lx := 4.0 * Level.TS
	var rx := 82.0 * Level.TS
	var cx := clampf(_px(), lx + 300.0, rx - 300.0)
	for i in 8:
		var k := float(i) / 7.0
		var xl := lerpf(lx + 40.0, cx - 270.0, k)
		var xr := lerpf(rx - 40.0, cx + 270.0, k)
		var dl := 0.4 + i * 0.55
		Tehlike.spawn(level, "ates", Vector2(xl, global_position.y), 46.0, dl, 7.0 - dl, dmg * 0.35, self)
		Tehlike.spawn(level, "ates", Vector2(xr, global_position.y), 46.0, dl, 7.0 - dl, dmg * 0.35, self)


func _er_tint(c: Color, t: float) -> void:
	if _tint_cm == null:
		for ch in level.get_children():
			if ch is CanvasModulate:
				_tint_cm = ch
				_tint_base = ch.color
				break
	if _tint_cm:
		var tw := _tint_cm.create_tween()
		tw.tween_property(_tint_cm, "color", c, t)


func _er_platforms() -> Array:
	return [Vector2(24.0 * Level.TS, 25.0 * Level.TS), Vector2(44.0 * Level.TS, 25.0 * Level.TS), Vector2(64.0 * Level.TS, 25.0 * Level.TS)]


func _er_sel_warn() -> void:
	_er_tint(_tint_base_safe() * Color(1.4, 0.55, 0.45), 1.2)
	Ses.play("tamu_seli" if Ses.has("tamu_seli") else "kut_donusum", -2.0, 0.7)
	FX.anim("spectral_bloom", global_position, 0.0, 2.0, Color(1.0, 0.4, 0.2))
	for pp in _er_platforms():
		FX.ring(pp + Vector2(0, -6), 50.0, Color(1.0, 0.9, 0.5, 0.8), 1.2, 0.35)
		FX.flash_light(pp + Vector2(0, -10), Color(1.0, 0.9, 0.55), 160.0, 1.6, 1.4)
	var lx := 4.0 * Level.TS
	var rx := 82.0 * Level.TS
	Tehlike.spawn(level, "serit", Vector2((lx + rx) * 0.5, global_position.y), (rx - lx) * 0.5, 1.4, 0.05, 0.0, self)


func _tint_base_safe() -> Color:
	if _tint_cm == null:
		for ch in level.get_children():
			if ch is CanvasModulate:
				_tint_cm = ch
				_tint_base = ch.color
				break
	return _tint_base


func _er_lava_on() -> void:
	var lx := 4.0 * Level.TS
	var rx := 82.0 * Level.TS
	var n := 8
	for i in n:
		var w2 := (rx - lx) / n
		Tehlike.spawn(level, "lav", Vector2(lx + w2 * (i + 0.5), global_position.y), w2 * 0.5 + 2.0, 0.0, 4.5, dmg * 0.35, self)
	Game.shake(5.0)
	for pp in _er_platforms():
		FX.flash_light(pp + Vector2(0, -10), Color(1.0, 0.9, 0.55), 150.0, 1.4, 4.5)


func _er_lava_tick(_delta: float) -> void:
	# lavda dururken platformlara ateş topu
	if Engine.get_physics_frames() % 40 == 0:
		var p := _pl()
		if p:
			_lob("fireball", _er_hand(), _arena_x(float(p.global_position.x)), 0.7, 0.5, 300.0)
	if Engine.get_physics_frames() % 10 == 0:
		for pp in _er_platforms():
			FX.burst(pp + Vector2(randf_range(-40, 40), -4), Color(1.0, 0.9, 0.5), 1, 20, 0.5, 0.14, -30, true)


func _er_sky_warn() -> void:
	_er_tint(_tint_base_safe() * Color(0.8, 0.75, 1.25), 0.9)
	for pp in _er_platforms():
		Tehlike.spawn(level, "serit", pp, 56.0, 1.0, 0.05, 0.0, self, false)


func _er_sky_on() -> void:
	Game.shake(3.0)


func _er_sky_tick(_delta: float) -> void:
	if Engine.get_physics_frames() % 14 == 0:
		var pp: Vector2 = _er_platforms()[randi() % 3]
		var x := pp.x + randf_range(-50.0, 50.0)
		_shoot("fireball", Vector2(x, pp.y - 320.0), Vector2(0.0, 520.0), 0.6, 300.0)
		level.telegraph_ground(Vector2(x, pp.y), 0.5)
	if Engine.get_physics_frames() % 30 == 0:
		var p := _pl()
		if p and not _player_high():
			_shoot("fireball", _er_hand(), (p.center() - _er_hand()).normalized() * 220.0, 0.45, 0.0)


func _er_sel_end() -> void:
	_er_tint(_tint_base_safe(), 0.8)
