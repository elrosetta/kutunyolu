class_name Unsur
extends RefCounted
## v20 Unsur sistemi: yerden alınan silahın ruhu. ItemGen düşen silaha (yakın, yay, fırlatma) bir unsur yuvarlar:
##   od        (ateş)        tutuşturur; yanan düşmana +%10; zincir bitirişi yerde yanan mürekkep gölü bırakır
##   ayaz      (buz)         ayaz yükü biriktirir (yavaşlatır) → 4 yükte donar; donmuşa vuruş kırar (kesin kritik + kıymık)
##   yildirim  (şimşek)      hedefin başına gökten şimşek indirir, yakındaki iki düşmana sıçrar (kısa sersemletme)
##   kam       (şaman ruhu)  töz damgası (+%10 hasar alır; damgalı ölünce can + Kut, ruh zerresi), ruh kurdu yankısı
##   yersu     (Yer-Su)      kök dolar (yerinde tutar), diken zehri; zincir bitirişi yaprak şifası
## Unsur yalnızca rastgele malzemeyle yuvarlanan (yani düşen) eşyaya gelir; başlangıç / test eşyaları sade kalır.
## Olasılıklar silah hızıyla (yavaş silah vuruş başına daha olası), unsur gücüyle (nadirlik) ölçeklenir; bosslarda yarıya
## iner, süreler yarıya iner, donma ve kök bosslarda yoktur (ayaz yükü bossta "buz kırığı" ek hasarına dönüşür).
## Bağlantılar: ItemGen.roll (yuvarlama, ad, açıklama), Player._deal (before_hit / after_hit), Enemy._tick_status (tick),
## InkTrail (palet + unsur zerreleri), HUD / Pickup (glyph, aura), Player._update_weapon_visual (bıçak ışıması).

const IDS := ["od", "ayaz", "yildirim", "kam", "yersu"]
## ad, sıfat (eşya adı), tür, renk (sRGB), mürekkep paleti (InkFX.PALETTES), nadirliğe göre ağırlık
const DEF := {
	"od": {"ad": "Od", "sifat": "Alazlı", "tur": "ateş", "renk": Color(1.0, 0.52, 0.16), "pal": 1, "w": [30, 28, 26, 24]},
	"ayaz": {"ad": "Ayaz", "sifat": "Ayazlı", "tur": "buz", "renk": Color(0.55, 0.86, 1.0), "pal": 2, "w": [28, 26, 24, 22]},
	"yildirim": {"ad": "Yıldırım", "sifat": "Şimşekli", "tur": "şimşek", "renk": Color(0.6, 0.72, 1.0), "pal": 5, "w": [12, 17, 21, 24]},
	"kam": {"ad": "Kam", "sifat": "Tözlü", "tur": "şaman ruhu", "renk": Color(0.66, 0.55, 1.0), "pal": 10, "w": [6, 11, 15, 19]},
	"yersu": {"ad": "Yer-Su", "sifat": "Köklü", "tur": "doğa gücü", "renk": Color(0.55, 0.88, 0.36), "pal": 11, "w": [24, 24, 22, 20]},
}
## Unsur gelme olasılığı (nadirliğe göre: sıradan, nadir, destansı, efsanevi); tema silahı +0,25
const CHANCE := [0.3, 0.5, 0.7, 0.9]
## Unsur gücü (nadirliğe göre); yuvarlamada ×0,92-1,08
const POWER := [1.0, 1.1, 1.22, 1.35]
const KINDS := ["slash", "heavy", "thrust", "dual", "whip", "bow", "throw"]
## Tema silahları: unsur gelirse %80 kendi unsuru
const BIAS := {"od_kamcisi": "od", "kor_cekici": "od", "od_oklari": "od", "ayaz_kilici": "ayaz", "yildirim_kilici": "yildirim",
	"tufan_yayi": "yildirim", "ruh_kilici": "kam", "erlik_tirpani": "kam", "kartal_tuyleri": "kam", "yilan_kilici": "yersu",
	"kayin_asasi": "yersu", "ruzgar_kilici": "ayaz"}
## Malzeme eğilimi: unsur gelirse %45 malzemenin unsuru
const MAT_BIAS := {"od_tasi": "od", "ayaz": "ayaz", "gok_demiri": "yildirim", "ruh": "kam", "yesim": "yersu"}

## Denge (taban değerler; olasılık = taban × güç × hız katsayısı × boss 0,5). Belgede tablo: docs/TASARIM.md v20.
const N := {
	"od_p": 0.2, "od_burn": 3.0, "od_bonus": 0.1, "od_pool_r": 30.0, "od_pool_t": 2.2, "od_pool_dps": 0.12, "od_pool_cd": 1.4,
	"ayaz_p": 0.45, "ayaz_max": 4, "ayaz_t": 3.5, "ayaz_slow": 0.08, "ayaz_freeze": 1.3, "ayaz_freeze_el": 0.9,
	"ayaz_shatter": 1.25, "ayaz_shard": 0.3, "ayaz_shard_r": 56.0, "ayaz_boss": 1.35,
	"yil_p": 0.13, "yil_dmg": 0.8, "yil_stun": 0.35, "yil_chain": 2, "yil_chain_r": 110.0, "yil_chain_dmg": 0.4, "yil_cd": 0.45,
	"kam_p": 0.3, "kam_mark": 5.0, "kam_bonus": 0.1, "kam_echo_p": 0.12, "kam_echo": 0.5, "kam_heal": 0.03, "kam_kut": 10.0, "kam_yer": 1.5,
	"yer_root_p": 0.14, "yer_root": 1.1, "yer_root_el": 0.65, "yer_poison_p": 0.3, "yer_heal": 0.015, "yer_heal_cd": 2.5,
	"boss_p": 0.5, "boss_t": 0.5,
}

## test sayaçları (--unsur): olay adı -> sayı, "hasar_<unsur>" -> unsurun verdiği ek hasar
static var stats: Dictionary = {}
static var _pl_cd: Dictionary = {}
## test (--unsur çekimi): >= 0 ise tüm olasılıklar bu değer (1 = her vuruşta tetikler)
static var force_p := -1.0


static func _roll(p: float) -> bool:
	return randf() < (force_p if force_p >= 0.0 else p)


static func valid(u: String) -> bool:
	return DEF.has(u)


static func of(it: Dictionary) -> String:
	var u := String(it.get("unsur", ""))
	return u if DEF.has(u) else ""


static func color(u: String) -> Color:
	return DEF[u]["renk"] if DEF.has(u) else Color(1, 1, 1)


static func pal(u: String) -> int:
	return int(DEF[u]["pal"]) if DEF.has(u) else 0


static func _stat(k: String, v := 1.0) -> void:
	stats[k] = float(stats.get(k, 0.0)) + v


# ------------------------------------------------------------------ yuvarlama (ItemGen)
static func roll_into(it: Dictionary, base: Dictionary, rng: RandomNumberGenerator) -> void:
	## Düşen eşyaya unsur: nadirlikle artan olasılık, tema silahı / malzeme eğilimi, nadir unsurlar yüksek nadirlikte.
	if String(base.get("cat", it.get("cat", ""))) != "weapons" or not (String(base.get("kind", "")) in KINDS):
		return
	var rar := clampi(int(it.get("rarity", 0)), 0, 3)
	var id := String(it.get("id", ""))
	var p: float = CHANCE[rar] + (0.25 if BIAS.has(id) else 0.0)
	if rng.randf() >= p:
		return
	var u := ""
	if BIAS.has(id) and rng.randf() < 0.8:
		u = BIAS[id]
	elif MAT_BIAS.has(String(it.get("material", ""))) and rng.randf() < 0.45:
		u = MAT_BIAS[String(it["material"])]
	else:
		var tot := 0.0
		for k in IDS:
			tot += float(DEF[k]["w"][rar])
		var r := rng.randf() * tot
		for k in IDS:
			r -= float(DEF[k]["w"][rar])
			if r <= 0.0:
				u = k
				break
		if u == "":
			u = IDS[IDS.size() - 1]
	apply(it, u, POWER[rar] * rng.randf_range(0.92, 1.08))


static func apply(it: Dictionary, u: String, g := -1.0) -> void:
	## Eşyaya unsur ver (test / ödül): ad yeniden kurulur.
	if not DEF.has(u):
		it.erase("unsur")
		it.erase("unsur_g")
		return
	it["unsur"] = u
	it["unsur_g"] = g if g > 0.0 else POWER[clampi(int(it.get("rarity", 0)), 0, 3)]
	if it.has("name_base") and it.has("material"):
		it["name"] = ItemGen.item_name(it)


static func name_adj(it: Dictionary) -> String:
	var u := of(it)
	return (String(DEF[u]["sifat"]) + " ") if u != "" else ""


const MARK := "◈ "


static func describe(it: Dictionary) -> Array:
	## Eşya kartı satırları (MARK ile başlar: HUD unsur renginde boyar)
	var u := of(it)
	if u == "":
		return []
	var g := float(it.get("unsur_g", 1.0))
	var sk := g * speed_k(it)
	var pc := func(k: String) -> String: return ItemGen.fmt(minf(95.0, float(N[k]) * sk * 100.0))
	var head := MARK + "Unsur: %s (%s)" % [DEF[u]["ad"], DEF[u]["tur"]]
	match u:
		"od":
			return [head, "  %%%s tutuşturur; yanana +%%%d hasar; bitiriş alev gölü" % [pc.call("od_p"), int(N["od_bonus"] * 100.0)]]
		"ayaz":
			return [head, "  %%%s ayaz yükü (yavaşlatır); %d yükte donar, donmuşu kırar" % [pc.call("ayaz_p"), int(N["ayaz_max"])]]
		"yildirim":
			return [head, "  %%%s başına şimşek iner, %d düşmana sıçrar" % [pc.call("yil_p"), int(N["yil_chain"])]]
		"kam":
			return [head, "  %%%s töz damgası (ölünce can + Kut); %%%s ruh kurdu yankısı" % [pc.call("kam_p"), pc.call("kam_echo_p")]]
		"yersu":
			return [head, "  %%%s kök dolar, %%%s diken zehri; bitiriş yaprak şifası" % [pc.call("yer_root_p"), pc.call("yer_poison_p")]]
	return [head]


static func speed_k(it: Dictionary) -> float:
	## Vuruş başına olasılık katsayısı: yavaş (ağır) silah ×1,6'ya kadar, hızlı hançer ×0,55'e kadar (saniyedeki
	## tetiklenme sayısı silahlar arasında yakın kalır)
	var aps := maxf(0.3, float(it.get("aps", 2.0)))
	return clampf(pow(2.0 / aps, 0.6), 0.55, 1.6)


# ------------------------------------------------------------------ dövüş (Player._deal)
static func _st(e: Node) -> Dictionary:
	if not e.has_meta("unsur"):
		e.set_meta("unsur", {})
	return e.get_meta("unsur")


static func _base(it: Dictionary) -> float:
	return float(it.get("dmg", 10.0)) * Game.item_mult(it)


static func before_hit(pl: Node, e: Node, it: Dictionary, opts: Dictionary, d: float) -> float:
	## Hasar uygulanmadan hemen önce (kritik hesaplandıktan sonra): yanana ek, donmuşu kırma, damgalıya ek, boss buz kırığı
	var u := of(it)
	if u == "" or opts.get("unsur_proc", false) or not is_instance_valid(e) or e.dead:
		return d
	var d0 := d
	match u:
		"od":
			if e.burn_t > 0.0:
				d *= 1.0 + float(N["od_bonus"])
		"ayaz":
			var s := _st(e)
			if e.freeze_t > 0.0 and not e.is_boss:
				# kırılma: donmuş düşmana vuruş kesin kritik + ek; buz kıymıkları çevreye (after_hit)
				d *= float(N["ayaz_shatter"])
				if not opts.get("crit", false):
					d *= float(it.get("crit_mult", 1.9)) + ItemGen.aff(it, "krit_hasar") / 100.0
					opts["crit"] = true
					opts["crit_done"] = true
				e.freeze_t = 0.0
				s["shatter"] = true
			elif e.is_boss and int(s.get("chill", 0)) >= int(N["ayaz_max"]):
				d *= float(N["ayaz_boss"])
				s["chill"] = 0
				s["boss_break"] = true
		"kam":
			if float(_st(e).get("mark_t", 0.0)) > 0.0:
				d *= 1.0 + float(N["kam_bonus"])
	if d > d0:
		_stat("hasar_" + u, d - d0)
	return d


static func after_hit(pl: Node, e: Node, it: Dictionary, opts: Dictionary, d: float, killed: bool) -> void:
	var u := of(it)
	if u == "" or opts.get("unsur_proc", false) or not is_instance_valid(e):
		return
	_stat("isabet_" + u)
	var boss: bool = e.is_boss
	var big: bool = opts.get("last", false) or opts.get("heavy", false)
	var sk := float(it.get("unsur_g", 1.0)) * speed_k(it) * (float(N["boss_p"]) if boss else 1.0)
	var tk := float(N["boss_t"]) if boss else 1.0
	var now := Game.clock()
	var hp: Vector2 = e.center()
	match u:
		"od":
			if not killed and _roll(float(N["od_p"]) * sk * (1.3 if big else 1.0)):
				var fresh: bool = e.burn_t <= 0.0
				_stat("od_yanma_sn", maxf(0.0, float(N["od_burn"]) * tk - maxf(e.burn_t, 0.0)))
				e.burn_t = maxf(e.burn_t, float(N["od_burn"]) * tk)
				_stat("od_tutusma")
				if fresh:
					fx_ignite(hp)
			if opts.get("last", false) and pl.is_on_floor() and now >= float(_pl_cd.get("od_pool", -9.0)) and pl.level:
				_pl_cd["od_pool"] = now + float(N["od_pool_cd"])
				pl.level.fire_pool(Vector2(e.global_position.x, pl.global_position.y), float(N["od_pool_r"]), float(N["od_pool_t"]), _base(it) * float(N["od_pool_dps"]) * 2.0)
				_stat("od_gol")
		"ayaz":
			var s := _st(e)
			if s.get("shatter", false):
				s.erase("shatter")
				_stat("ayaz_kirilma")
				fx_shatter(hp)
				for o in pl.get_tree().get_nodes_in_group("dusman"):
					if o != e and is_instance_valid(o) and not o.dead and o.center().distance_to(hp) < float(N["ayaz_shard_r"]):
						_proc(pl, o, it, _base(it) * float(N["ayaz_shard"]), {"kb": 90.0, "dir": signf(o.center().x - hp.x)}, "ayaz")
				_chill_end(e, s)
			elif s.get("boss_break", false):
				s.erase("boss_break")
				_stat("ayaz_kirilma")
				fx_shatter(hp)
				_chill_end(e, s)
			elif not killed and e.freeze_t <= 0.0 and _roll(float(N["ayaz_p"]) * sk):
				var n := mini(int(N["ayaz_max"]), int(s.get("chill", 0)) + (2 if big else 1))
				_chill_set(e, s, n)
				_stat("ayaz_yuk")
				FX.frost(hp, 2)
				if n >= int(N["ayaz_max"]) and not boss:
					e.freeze_t = maxf(e.freeze_t, float(N["ayaz_freeze_el"] if e.elite else N["ayaz_freeze"]))
					_chill_end(e, s)
					_stat("ayaz_donma")
					fx_freeze(hp)
		"yildirim":
			var s2 := _st(e)
			if not killed and now >= float(s2.get("bolt_cd", -9.0)) and _roll(float(N["yil_p"]) * sk * (1.5 if big else 1.0)):
				s2["bolt_cd"] = now + float(N["yil_cd"])
				bolt(pl, e, it)
		"kam":
			var s3 := _st(e)
			var yk := float(N["kam_yer"]) if String(pl.get("realm")) == "yer" else 1.0
			if killed:
				if float(s3.get("mark_t", 0.0)) > 0.0:
					_kam_reward(pl, e)
			else:
				if _roll(float(N["kam_p"]) * sk * yk):
					if float(s3.get("mark_t", 0.0)) <= 0.0:
						_stat("kam_damga")
						fx_mark(hp)
					s3["mark_t"] = float(N["kam_mark"]) * tk
					_aura(e)
				if _roll(float(N["kam_echo_p"]) * sk * yk):
					_kam_echo(pl, e, it)
		"yersu":
			if not killed:
				if not boss and _roll(float(N["yer_root_p"]) * sk):
					var rt := float(N["yer_root_el"] if e.elite else N["yer_root"])
					e.root_t = maxf(e.root_t, rt)
					_st(e)["root_max"] = rt
					_aura(e)
					_stat("yersu_kok")
					fx_roots(e.global_position)
				if _roll(float(N["yer_poison_p"]) * sk):
					e.poison = mini(5, int(e.poison) + 1)
					e.poison_t = 4.0
					_stat("yersu_zehir")
			if opts.get("last", false) and now >= float(_pl_cd.get("yer_heal", -9.0)):
				_pl_cd["yer_heal"] = now + float(N["yer_heal_cd"])
				var hv := float(pl.max_hp()) * float(N["yer_heal"]) + 1.0
				pl.heal(hv)
				_stat("yersu_sifa", hv)
				fx_leaf_heal(pl.center())


static func _proc(pl: Node, e: Node, it: Dictionary, dmg: float, opts: Dictionary, u: String) -> bool:
	## Unsurun kendi vuruşu: _deal çarpanları yok (taban hasar × eşya ölçeği), unsur yeniden tetiklenmez
	if not is_instance_valid(e) or e.dead:
		return false
	var o := {"unsur_proc": true, "sfx_done": true, "feel_done": true, "kb": 0.0, "dir": 1.0, "poise": 0.3}
	o.merge(opts, true)
	var killed: bool = e.take_hit(dmg, o)
	_stat("hasar_" + u, dmg)
	if is_instance_valid(pl):
		pl.add_kut(dmg * 0.1)
	if killed and float(_st(e).get("mark_t", 0.0)) > 0.0:
		_kam_reward(pl, e)
	return killed


static func _chill_set(e: Node, s: Dictionary, n: int) -> void:
	if not s.has("spd0"):
		s["spd0"] = float(e.speed)
	s["chill"] = n
	s["chill_t"] = float(N["ayaz_t"])
	e.speed = float(s["spd0"]) * (1.0 - float(N["ayaz_slow"]) * n * (float(N["boss_t"]) if e.is_boss else 1.0))
	_aura(e)


static func _chill_end(e: Node, s: Dictionary) -> void:
	s["chill"] = 0
	s["chill_t"] = 0.0
	if s.has("spd0"):
		e.speed = float(s["spd0"])
		s.erase("spd0")


static func tick(e: Node, delta: float) -> void:
	## Enemy._tick_status'tan (yalnızca unsur durumu olan düşmanda)
	var s: Dictionary = e.get_meta("unsur")
	if int(s.get("chill", 0)) > 0:
		s["chill_t"] = float(s["chill_t"]) - delta
		if float(s["chill_t"]) <= 0.0:
			_chill_end(e, s)
		elif Engine.get_physics_frames() % 18 == 0:
			FX.frost(e.center() + Vector2(0, 6), 1)
	if float(s.get("mark_t", 0.0)) > 0.0:
		s["mark_t"] = float(s["mark_t"]) - delta


static func _kam_reward(pl: Node, e: Node) -> void:
	var s := _st(e)
	if s.get("rewarded", false):
		return
	s["rewarded"] = true
	s["mark_t"] = 0.0
	_stat("kam_odul")
	var w := Wisp.new()
	w.pl = pl
	w.heal = float(pl.max_hp()) * float(N["kam_heal"])
	w.kut = float(N["kam_kut"])
	w.position = e.center()
	if FX.root:
		FX.root.add_child(w)


static func _kam_echo(pl: Node, e: Node, it: Dictionary) -> void:
	## Ruh kurdu yankısı: kısa gecikmeyle hayalet pençe aynı hedefe (vuruşun %50'si)
	_stat("kam_yanki")
	var tree: SceneTree = pl.get_tree()
	var dir := signf(e.center().x - pl.center().x)
	if dir == 0.0:
		dir = 1.0
	# düğümleri değil kimliklerini yakala: gecikmede düşman silinmiş olabilir
	var eid := e.get_instance_id()
	var pid := pl.get_instance_id()
	var go := func() -> void:
		var e2 = instance_from_id(eid)
		var p2 = instance_from_id(pid)
		if e2 == null or p2 == null or not is_instance_valid(e2) or e2.dead:
			return
		_kam_echo_hit(p2, e2, it, dir)
	tree.create_timer(0.16, false).timeout.connect(go)


static func _kam_echo_hit(pl: Node, e: Node, it: Dictionary, dir: float) -> void:
	var c: Vector2 = e.center()
	InkFX.hit("claw", c, Vector2(dir, -0.4), 10, 2, 1.3)
	InkTrail.auto_arc(c + Vector2(-dir * 4.0, -4.0), 30.0, -2.0, 0.6, 0.08, 10, int(dir), false)
	FX.soul(c, Color(0.7, 0.6, 1.0), 6)
	Ses.play("savur_ruh", -6.0, 1.25, 0.08)
	_proc(pl, e, it, _base(it) * float(N["kam_echo"]), {"kb": 60.0, "dir": dir}, "kam")


static func bolt(pl: Node, e: Node, it: Dictionary) -> void:
	## Gökten şimşek: hedefin başına iner (ana vuruş + sersemletme), en yakın iki düşmana sıçrar
	_stat("yildirim_simsek")
	var c: Vector2 = e.center()
	var top := c + Vector2(randf_range(-26.0, 26.0), -190.0)
	fx_bolt(top, c + Vector2(0, -2))
	Ses.play("simsek_catirti" if Ses.has("simsek_catirti") else "yildirim", -5.0, randf_range(1.05, 1.25), 0.06, 0.08)
	_proc(pl, e, it, _base(it) * float(N["yil_dmg"]), {"stun": float(N["yil_stun"]), "kb": 40.0, "dir": signf(c.x - pl.center().x)}, "yildirim")
	var near: Array = []
	for o in pl.get_tree().get_nodes_in_group("dusman"):
		if o != e and is_instance_valid(o) and not o.dead and o.center().distance_to(c) < float(N["yil_chain_r"]):
			near.append(o)
	near.sort_custom(func(a: Node, b: Node) -> bool: return a.center().distance_to(c) < b.center().distance_to(c))
	var prev := c
	for i in mini(int(N["yil_chain"]), near.size()):
		var o: Node = near[i]
		var oc: Vector2 = o.center()
		FX.lightning(prev, oc, Color(0.62, 0.78, 1.0))
		InkFX.hit("spark", oc, (oc - prev).normalized(), 5, 1, 0.9)
		_proc(pl, o, it, _base(it) * float(N["yil_chain_dmg"]), {"stun": 0.2, "kb": 30.0, "dir": signf(oc.x - prev.x)}, "yildirim")
		_stat("yildirim_sicrama")
		prev = oc


# ------------------------------------------------------------------ vuruş efektleri (stil v2 mürekkep; v1'de de çalışır)
static func fx_ignite(c: Vector2) -> void:
	FX.fire(c, 7, 0.36, 7.0)
	InkFX.hit("magic", c, Vector2.UP, 1, 1, 0.9)
	var p := parca(c, true)
	if p:
		for k in 7:
			p.add("alev", c + Vector2(randf_range(-7, 7), randf_range(-2, 6)), Vector2(randf_range(-30, 30), randf_range(-120, -60)), Vector2(5, 10) * randf_range(0.8, 1.3), randf_range(0.35, 0.55), Color(1.0, 0.62, 0.22), -160.0)
	Ses.play("buyu", -9.0, 1.4, 0.1, 0.1)


static func fx_freeze(c: Vector2) -> void:
	FX.anim("frost_nova", c, 0.0, 0.9, Color(0.7, 0.9, 1.0))
	FX.frost(c, 8)
	InkFX.ring(c, 26.0, 2, 0.34)
	Ses.play("donma", -4.0, 1.0, 0.06, 0.1)


static func fx_shatter(c: Vector2) -> void:
	InkFX.hit("magic", c, Vector2.UP, 2, 2, 1.4)
	var p := parca(c, false)
	if p:
		for k in 12:
			var a := randf() * TAU
			var v := Vector2.from_angle(a) * randf_range(90.0, 230.0) + Vector2(0, -60)
			p.add("kivilcim", c, v, Vector2(3.0, 10.0) * randf_range(0.7, 1.4), randf_range(0.45, 0.7), Color(0.78, 0.94, 1.0), 520.0, true)
	FX.frost(c, 10)
	FX.flash_light(c, Color(0.6, 0.85, 1.0), 90.0, 1.2, 0.16)
	Ses.play("darbe_donuk" if Ses.has("darbe_donuk") else "ors", -2.0, 1.25, 0.08)
	Game.shake_dir(0.18, Vector2(0, 1))


static func fx_bolt(top: Vector2, at: Vector2) -> void:
	FX.lightning(top, at, Color(0.72, 0.84, 1.0))
	FX.lightning(top + Vector2(randf_range(-10, 10), 0), at, Color(0.55, 0.7, 1.0))
	InkFX.hit("spark", at, Vector2.UP, 5, 2, 1.25)
	InkFX.ring(at + Vector2(0, 6), 22.0, 5, 0.24, 0.35)
	FX.flash_light(at, Color(0.6, 0.75, 1.0), 140.0, 2.0, 0.14)
	FX.sparks(at, Vector2.UP, Color(0.75, 0.85, 1.0), 8, 220.0)
	Game.shake_dir(0.22, Vector2.DOWN)


static func fx_mark(c: Vector2) -> void:
	InkFX.ring(c, 18.0, 10, 0.3)
	FX.soul(c, Color(0.7, 0.6, 1.0), 5)


static func fx_roots(feet: Vector2) -> void:
	FX.burst(feet, Color(0.35, 0.5, 0.2), 8, 110, 0.45, 0.2, 380)
	var p := parca(feet, false)
	if p:
		for k in 5:
			p.add("yaprak", feet + Vector2(randf_range(-8, 8), -4), Vector2(randf_range(-60, 60), randf_range(-150, -80)), Vector2(6, 6), randf_range(0.6, 0.9), Color(0.42, 0.7, 0.26), 260.0, true)
	Ses.play("agac_inilti" if Ses.has("agac_inilti") else "darbe_kunt", -12.0, 1.4, 0.1, 0.15)


static func fx_leaf_heal(c: Vector2) -> void:
	var p := parca(c, false)
	if p:
		for k in 10:
			var a := randf() * TAU
			p.add("yaprak", c + Vector2.from_angle(a) * 16.0, Vector2.from_angle(a + PI * 0.5) * 60.0 + Vector2(0, -30), Vector2(6, 6) * randf_range(0.8, 1.2), randf_range(0.7, 1.0), Color(0.5, 0.85, 0.3), -20.0, true)
	FX.text(c + Vector2(0, -26), "yaprak şifası", Color(0.6, 0.95, 0.45), 7)
	FX.flash_light(c, Color(0.6, 1.0, 0.5), 60.0, 0.9, 0.2)


# ------------------------------------------------------------------ düğümler
static func parca(pos: Vector2, additive: bool) -> Parca:
	if FX.root == null:
		return null
	var p := Parca.new()
	p.additive = additive
	FX.root.add_child(p)
	return p


class Parca extends Node2D:
	## Mürekkep parçacık kümesi (assets/fx/ink_p dokuları, kenar yumuşatmalı dörtgenler). Tek düğüm, kısa ömür.
	var additive := false
	var _ps: Array = []   # [doku, konum, hız, boy, ömür, yaş, renk, yerçekimi, döner mi, açı, açısal hız]

	func _ready() -> void:
		z_index = 62
		top_level = true
		InkDraw.prep(self)
		var m := CanvasItemMaterial.new()
		m.light_mode = CanvasItemMaterial.LIGHT_MODE_UNSHADED
		if additive:
			m.blend_mode = CanvasItemMaterial.BLEND_MODE_ADD
		material = m

	func add(tex: String, p: Vector2, v: Vector2, sz: Vector2, life: float, col: Color, grav := 0.0, spin := false) -> void:
		_ps.append([tex, p, v, sz, life, 0.0, col, grav, spin, randf() * TAU, randf_range(-9.0, 9.0)])

	func _process(delta: float) -> void:
		var alive := false
		for q in _ps:
			q[5] = float(q[5]) + delta
			if float(q[5]) < float(q[4]):
				alive = true
			var v: Vector2 = q[2]
			v = v * maxf(0.0, 1.0 - 2.4 * delta) + Vector2(0, float(q[7]) * delta)
			if String(q[0]) == "yaprak":
				v.x += sin(float(q[5]) * 9.0 + float(q[9])) * 160.0 * delta
			q[2] = v
			q[1] = (q[1] as Vector2) + v * delta
			q[9] = float(q[9]) + float(q[10]) * delta
		if not alive:
			queue_free()
			return
		queue_redraw()

	func _draw() -> void:
		for q in _ps:
			var k := float(q[5]) / float(q[4])
			if k >= 1.0:
				continue
			var col: Color = q[6]
			col.a *= 1.0 - k * k
			var sz: Vector2 = q[3]
			var v: Vector2 = q[2]
			var ang: float = float(q[9]) if q[8] else (v.angle() + PI * 0.5 if v.length() > 2.0 else 0.0)
			match String(q[0]):
				"alev":
					InkDraw.flame(self, q[1], sz.x * (1.0 - 0.5 * k), sz.y * (1.0 - 0.4 * k), col, sin(float(q[9]) * 3.0) * 0.4)
				_:
					InkDraw.quad(self, String(q[0]), q[1], sz * (1.0 - 0.3 * k), ang, col)


class Wisp extends Node2D:
	## Töz damgalı düşman ölünce çıkan ruh zerresi: oyuncuya süzülür, değince can + Kut verir
	var pl: Node
	var heal := 0.0
	var kut := 0.0
	var _t := 0.0
	var _v := Vector2(0, -90)

	func _ready() -> void:
		z_index = 63
		top_level = true
		InkDraw.prep(self)
		var m := CanvasItemMaterial.new()
		m.light_mode = CanvasItemMaterial.LIGHT_MODE_UNSHADED
		m.blend_mode = CanvasItemMaterial.BLEND_MODE_ADD
		material = m
		_v = Vector2(randf_range(-60, 60), -110)

	func _process(delta: float) -> void:
		_t += delta
		if pl == null or not is_instance_valid(pl) or _t > 3.0:
			queue_free()
			return
		var to: Vector2 = pl.center() - global_position
		var acc := to.normalized() * (380.0 + 700.0 * _t)
		_v = (_v + acc * delta) * maxf(0.0, 1.0 - 2.0 * delta)
		global_position += _v * delta
		if to.length() < 10.0 and _t > 0.2:
			pl.heal(heal)
			pl.add_kut(kut)
			FX.soul(pl.center(), Color(0.7, 0.62, 1.0), 8)
			FX.text(pl.center() + Vector2(0, -28), "töz", Color(0.78, 0.7, 1.0), 7)
			Ses.play("ruh_kusu" if Ses.has("ruh_kusu") else "kut_tane", -6.0, 1.2)
			queue_free()
			return
		queue_redraw()

	func _draw() -> void:
		var pulse := 1.0 + 0.2 * sin(_t * 20.0)
		InkDraw.soft(self, Vector2.ZERO, 9.0 * pulse, Color(0.45, 0.35, 1.0, 0.45))
		InkDraw.soft(self, Vector2.ZERO, 4.0, Color(0.9, 0.85, 1.0, 0.9))
		var tail := -_v.normalized() * minf(_v.length() * 0.06, 16.0)
		InkDraw.stroke(self, Vector2.ZERO, tail, 5.0, Color(0.55, 0.45, 1.0, 0.6))


static func _aura(e: Node) -> void:
	for ch in e.get_children():
		if ch is Aura:
			return
	var a := Aura.new()
	a.host = e
	e.add_child(a)


class Aura extends Node2D:
	## Düşman üstünde unsur durumu: ayaz yükü (ayakta buz kristalleri), töz damgası (başın üstünde ruh gözü),
	## kök (ayaklara dolanan kökler). Durum kalmayınca kendini siler.
	var host: Node
	var _t := 0.0

	func _ready() -> void:
		z_index = 3
		InkDraw.prep(self)

	func _process(delta: float) -> void:
		_t += delta
		if host == null or not is_instance_valid(host) or host.dead or not host.has_meta("unsur"):
			queue_free()
			return
		var s: Dictionary = host.get_meta("unsur")
		if int(s.get("chill", 0)) <= 0 and float(s.get("mark_t", 0.0)) <= 0.0 and host.root_t <= 0.0:
			queue_free()
			return
		queue_redraw()

	func _draw() -> void:
		var s: Dictionary = host.get_meta("unsur")
		var sz: Vector2 = host.size
		var n := int(s.get("chill", 0))
		if n > 0:
			# ayaz: ayaklarda buz kabuğu ve yükle büyüyen kristaller
			var a := clampf(float(s.get("chill_t", 0.0)) / 0.6, 0.0, 1.0)
			InkDraw.ellipse(self, Vector2(0, -1), sz.x * 0.75, 4.0 + n, Color(0.55, 0.85, 1.0, 0.32 * a))
			for i in n * 2:
				var x := (float(i) / float(maxi(1, n * 2 - 1)) - 0.5) * sz.x * 0.9
				var h := (5.0 + 3.0 * n) * (0.6 + 0.4 * absf(sin(float(i) * 2.3)))
				var c := Vector2(x, -h * 0.4)
				InkDraw.quad(self, "kivilcim", c, Vector2(3.4, h), (x / sz.x) * 0.9, Color(0.82, 0.95, 1.0, 0.9 * a))
				InkDraw.quad(self, "kivilcim", c, Vector2(1.2, h * 0.8), (x / sz.x) * 0.9, Color(1.0, 1.0, 1.0, 0.8 * a))
		var mk := float(s.get("mark_t", 0.0))
		if mk > 0.0:
			# töz damgası: başın üstünde dönen ruh gözü (çift halka + göz bebeği), son saniyede yanıp söner
			var a2 := clampf(mk / 0.8, 0.0, 1.0) * (0.75 + 0.25 * sin(_t * 8.0))
			var c2 := Vector2(0, -sz.y - 14.0 + sin(_t * 3.0) * 1.5)
			InkDraw.soft(self, c2, 8.0, Color(0.45, 0.35, 1.0, 0.35 * a2))
			Unsur.glyph(self, "kam", c2, 9.0, Color(0.78, 0.7, 1.0, a2), _t)
		if host.root_t > 0.0:
			# kök: ayaklara dolanan iki kıvrık kök + diken
			var rm := maxf(0.2, float(s.get("root_max", 1.0)))
			var g := clampf(host.root_t / rm * 3.0, 0.0, 1.0)
			for side: int in [-1, 1]:
				var pts := PackedVector2Array()
				for i in 7:
					var k := float(i) / 6.0
					pts.append(Vector2(side * (sz.x * 0.55 - k * sz.x * 0.5) + sin(k * 7.0 + float(side)) * 3.0, -k * 16.0 * g))
				InkDraw.line(self, pts, 4.0, 1.2, Color(0.16, 0.12, 0.06, 0.95))
				InkDraw.line(self, pts, 2.4, 0.6, Color(0.42, 0.62, 0.22, 0.95))
				InkDraw.quad(self, "yaprak", pts[4] + Vector2(side * 3.0, 0), Vector2(6, 6) * g, float(side) * 0.8, Color(0.5, 0.82, 0.3, 0.95))


# ------------------------------------------------------------------ simge (HUD yuvası, eşya kartı, yerdeki eşya)
static func glyph(ci: CanvasItem, u: String, c: Vector2, s: float, col: Color, t := 0.0) -> void:
	## Unsur simgesi, kenar yumuşatmalı çizgi / çokgen: od alev, ayaz kar tanesi, yıldırım şimşek, kam ruh gözü, yersu yaprak
	var ink := Color(0.06, 0.05, 0.08, col.a * 0.9)
	match u:
		"od":
			# alev: altta yuvarlak karın, iki yandan içe kıvrılıp sivrilen uç; içte sarı-beyaz küçük alev
			var pts := _flame_pts(c, s)
			_poly(ci, pts, ink, 1.6)
			ci.draw_colored_polygon(pts, col)
			ci.draw_colored_polygon(_flame_pts(c + Vector2(0, s * 0.32), s * 0.5), Color(1.0, 0.93, 0.62, col.a))
		"ayaz":
			for i in 3:
				var d := Vector2.from_angle(float(i) * PI / 3.0 + PI * 0.5) * s
				ci.draw_line(c - d, c + d, ink, 3.2, true)
			for i in 3:
				var d := Vector2.from_angle(float(i) * PI / 3.0 + PI * 0.5) * s
				ci.draw_line(c - d, c + d, col, 1.6, true)
				for sg: float in [-1.0, 1.0]:
					var b := c + d * 0.55 * sg
					var o := d.normalized().rotated(0.7) * s * 0.3
					var o2 := d.normalized().rotated(-0.7) * s * 0.3
					ci.draw_line(b, b + o * sg, col, 1.3, true)
					ci.draw_line(b, b + o2 * sg, col, 1.3, true)
		"yildirim":
			var pts2 := PackedVector2Array([c + Vector2(0.15, -1.0) * s, c + Vector2(-0.5, 0.1) * s, c + Vector2(-0.02, 0.1) * s,
				c + Vector2(-0.2, 1.0) * s, c + Vector2(0.5, -0.18) * s, c + Vector2(0.04, -0.18) * s, c + Vector2(0.3, -1.0) * s])
			_poly(ci, pts2, ink, 1.6)
			ci.draw_colored_polygon(pts2, col)
		"kam":
			# ruh gözü: badem göz + bebek, çevresinde dönen iki yay
			var eye := PackedVector2Array()
			for i in 20:
				var a := float(i) / 20.0 * TAU
				eye.append(c + Vector2(cos(a) * s * 0.85, sin(a) * s * 0.42 * (1.0 if sin(a) > 0.0 else 0.9)))
			_poly(ci, eye, ink, 1.6)
			ci.draw_colored_polygon(eye, Color(col, col.a * 0.55))
			ci.draw_circle(c, s * 0.3, col, true, -1.0, true)
			ci.draw_circle(c, s * 0.13, Color(0.08, 0.05, 0.16, col.a), true, -1.0, true)
			ci.draw_arc(c, s * 1.05, t * 2.0, t * 2.0 + 1.6, 12, col, 1.3, true)
			ci.draw_arc(c, s * 1.05, t * 2.0 + PI, t * 2.0 + PI + 1.6, 12, col, 1.3, true)
		"yersu":
			var leaf := PackedVector2Array()
			for i in 17:
				var k := float(i) / 16.0
				var a := k * TAU
				leaf.append(c + Vector2(sin(a) * s * 0.5 * (1.0 - 0.3 * cos(a)), -cos(a) * s).rotated(0.5))
			_poly(ci, leaf, ink, 1.6)
			ci.draw_colored_polygon(leaf, col)
			ci.draw_line(c + Vector2(0, s * 1.1).rotated(0.5), c + Vector2(0, -s * 0.7).rotated(0.5), Color(0.1, 0.2, 0.05, col.a), 1.2, true)


static func _flame_pts(c: Vector2, s: float) -> PackedVector2Array:
	var pts := PackedVector2Array()
	for i in 13:
		var ang := lerpf(-PI * 0.12, PI * 1.12, float(i) / 12.0)
		pts.append(c + Vector2(cos(ang) * 0.62, 0.3 + sin(ang) * 0.58) * s)
	# sol kenardan uca, uçtan sağ kenara (hafif S kıvrımı)
	pts.append(c + Vector2(-0.5, -0.35) * s)
	pts.append(c + Vector2(-0.18, -0.8) * s)
	pts.append(c + Vector2(0.08, -1.12) * s)
	pts.append(c + Vector2(0.22, -0.62) * s)
	pts.append(c + Vector2(0.58, -0.12) * s)
	return pts


static func _poly(ci: CanvasItem, pts: PackedVector2Array, col: Color, w: float) -> void:
	var cl := pts.duplicate()
	cl.append(pts[0])
	ci.draw_polyline(cl, col, w * 2.0, true)


static func slot_badge(ci: CanvasItem, r: Rect2, it: Dictionary, t := 0.0) -> void:
	## HUD yuvası: köşede unsur simgesi + alta unsur renginde ince yıkama
	var u := of(it)
	if u == "":
		return
	var col := color(u)
	# altta ince unsur yıkaması (yuvanın alt üçte biri; yukarı doğru söner)
	var h := r.size.y * 0.38
	var y0 := r.end.y - 3.0 - h
	var a0 := 0.16 + 0.05 * sin(t * 3.0)
	ci.draw_polygon(PackedVector2Array([Vector2(r.position.x + 3, y0), Vector2(r.end.x - 3, y0), Vector2(r.end.x - 3, r.end.y - 3), Vector2(r.position.x + 3, r.end.y - 3)]),
		PackedColorArray([Color(col, 0.0), Color(col, 0.0), Color(col, a0), Color(col, a0)]))
	var c := r.position + Vector2(r.size.x - 5.0, 6.0)
	ci.draw_circle(c, 6.2, Color(0.05, 0.04, 0.07, 0.92), true, -1.0, true)
	ci.draw_arc(c, 6.2, 0.0, TAU, 24, Color(col, 0.9), 1.0, true)
	glyph(ci, u, c, 3.8, col, t)


static func pickup_aura(ci: CanvasItem, it: Dictionary, t: float) -> void:
	## Yerdeki eşya: unsur renginde nabız gibi atan yıkama + unsura özgü zerreler + simge
	var u := of(it)
	if u == "":
		return
	var col := color(u)
	var pulse := 0.5 + 0.5 * sin(t * 3.2)
	InkDraw.soft(ci, Vector2(0, -6), 15.0 + 2.0 * pulse, Color(col, 0.18 + 0.08 * pulse))
	for k in 4:
		var ph := fmod(t * 0.7 + float(k) * 0.25, 1.0)
		var x := sin(float(k) * 2.1 + t * 1.3) * 12.0
		var a := sin(ph * PI) * 0.85
		match u:
			"od":
				InkDraw.flame(ci, Vector2(x, 2.0 - ph * 22.0), 3.0, 7.0 * (1.0 - ph * 0.5), Color(1.0, 0.6, 0.2, a), sin(t * 5.0 + k) * 0.4)
			"ayaz":
				InkDraw.star(ci, Vector2(x, -22.0 + ph * 20.0), 3.0, t * 2.0 + k, Color(0.85, 0.96, 1.0, a))
			"yildirim":
				if fmod(t * 7.0 + float(k) * 1.7, 3.0) < 0.6:
					var p0 := Vector2(x, -18.0 + float(k) * 4.0)
					var pts := PackedVector2Array([p0, p0 + Vector2(4, 5), p0 + Vector2(-2, 9), p0 + Vector2(3, 14)])
					InkDraw.line(ci, pts, 2.2, 0.6, Color(0.75, 0.85, 1.0, 0.95))
			"kam":
				InkDraw.cloud(ci, Vector2(x * 0.8, 0.0 - ph * 24.0), 4.0 + ph * 3.0, Color(0.55, 0.45, 1.0, a * 0.55), k)
			"yersu":
				InkDraw.quad(ci, "yaprak", Vector2(x, -24.0 + ph * 26.0), Vector2(5, 5), t * 3.0 + float(k), Color(0.5, 0.85, 0.3, a))
	glyph(ci, u, Vector2(0, -30.0 + sin(t * 2.0) * 1.5), 4.5, Color(col.lightened(0.2), 0.95), t)


# ------------------------------------------------------------------ silah ışıması (oyuncunun elindeki bıçak)
static func weapon_glow(host: Node2D, it: Dictionary, h: Vector2, bd: Vector2, R: float, show: bool) -> void:
	## Player._update_weapon_visual: bıçak boyunca unsur ışıması (alt düğüm, kendi çizer)
	var g: BladeGlow = null
	for ch in host.get_children():
		if ch is BladeGlow:
			g = ch
			break
	var u := of(it) if show else ""
	if u == "" or it.get("kind", "") == "bow":
		if g:
			g.visible = false
		return
	if g == null:
		g = BladeGlow.new()
		host.add_child(g)
	g.visible = true
	g.u = u
	g.a = h + bd.normalized() * R * 0.28
	g.b = h + bd.normalized() * R * 0.98


class BladeGlow extends Node2D:
	var u := ""
	var a := Vector2.ZERO
	var b := Vector2.ZERO
	var _t := 0.0

	func _ready() -> void:
		z_index = 2
		InkDraw.prep(self)
		var m := CanvasItemMaterial.new()
		m.blend_mode = CanvasItemMaterial.BLEND_MODE_ADD
		m.light_mode = CanvasItemMaterial.LIGHT_MODE_UNSHADED
		material = m

	func _process(delta: float) -> void:
		_t += delta
		if visible:
			queue_redraw()

	func _draw() -> void:
		var col := Unsur.color(u)
		var d := b - a
		var L := d.length()
		if L < 1.0:
			return
		var n := d / L
		var o := n.orthogonal()
		var fl := 0.8 + 0.2 * sin(_t * 23.0)
		InkDraw.stroke(self, b, a, 7.0 * fl, Color(col, 0.28))
		InkDraw.stroke(self, b, a, 2.6, Color(col.lightened(0.4), 0.45))
		for k in 3:
			var ph := fmod(_t * 2.2 + float(k) * 0.33, 1.0)
			var p := a + d * (0.25 + 0.7 * fmod(float(k) * 0.37 + _t * 0.4, 1.0))
			match u:
				"od":
					InkDraw.flame(self, p, 2.6, 6.0 * (1.0 - ph), Color(1.0, 0.6, 0.2, 0.7 * (1.0 - ph)), sin(_t * 9.0 + k) * 0.5)
				"ayaz":
					InkDraw.star(self, p + o * sin(_t * 4.0 + k) * 2.0, 2.4 * (1.0 - ph), _t * 3.0, Color(0.9, 0.97, 1.0, 0.8 * (1.0 - ph)))
				"yildirim":
					if fmod(_t * 11.0 + float(k) * 2.3, 2.0) < 0.5:
						var q := PackedVector2Array([p, p + o * 3.0 + n * 2.0, p - o * 2.0 + n * 5.0, p + o * 2.5 + n * 8.0])
						InkDraw.line(self, q, 1.8, 0.5, Color(0.8, 0.9, 1.0, 0.95))
				"kam":
					InkDraw.cloud(self, p - n * ph * 6.0 + Vector2(0, -ph * 8.0), 2.5 + 2.0 * ph, Color(0.5, 0.4, 1.0, 0.45 * (1.0 - ph)), k)
				"yersu":
					InkDraw.quad(self, "yaprak", p + o * 3.0 * sin(_t * 3.0 + k), Vector2(3.5, 3.5) * (1.0 - 0.5 * ph), _t * 2.0 + k, Color(0.55, 0.9, 0.35, 0.7 * (1.0 - ph)))
