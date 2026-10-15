extends Node
## Ses yöneticisi (v9): çalışma anında kurulan veri yolları (SFX, Ambience, Music, UI -> Master sıkıştırıcı + sert sınırlayıcı),
## biyoma göre yankı (`set_biome`), ses başına eşzamanlılık sınırı ve en eski sesi çalma (voice stealing), art arda aynı
## dosyayı çalmayan varyant seçimi, küçük perde ve ses oynaması, isteğe bağlı 2B konumlu çalma (kameraya göre sağ-sol),
## menü/duraklatma kısması (`menu_duck`), düşük can kalp atışı + boğuklaşma (`low_hp`), biyom ortam döngüleri ve çapraz
## geçişli müzik. Dosyalar `assets/audio` altında üretilir (tools/audiogen/export_audio.py).
## v13 darbe hiyerarşisi: `hit(tier, pos, kind)` (0 hafif / 1 ağır / 2 kritik / 3 öldürücü; "tas"/"metal" yüzeyi),
## `boom(pos, size)` (kademeli patlama; büyük / ekran dışı uzak), `thunder(pos, delay)` (çatırtı hemen, gök gürlemesi
## zaman ölçeğinden bağımsız sayaçla sonra). Ağır/kritik/öldürücü dosyaların başında 30-45 ms bas ön-yankı vardır
## (`assets/audio/sfx/sfx.json` "onset"); vuruş duraklamasıyla aynı karede tetiklenince geçiş darbe karesine oturur.

const SFX_DIR := "res://assets/audio/sfx/"
const MUSIC_DIR := "res://assets/audio/music/"
const POOL := 24
const POOL_2D := 16

const BUS_SFX := "SFX"
const BUS_AMB := "Ambience"
const BUS_MUSIC := "Music"
const BUS_UI := "UI"

## Arayüz veri yoluna giden sesler: menüde de net kalır, yankı ve kısma almaz.
const UI_PREFIXES := ["ui_", "npc_", "esya_kusan", "esya_degis", "tilsim", "seviye", "acilis", "ors", "kut_banka", "kalp_"]

## Eşzamanlılık sınırı: önce tam ad, sonra aile (ilk "_" öncesi) aranır; dolunca aynı gruptaki en eski ses kesilir.
const LIMITS := {
	"adim": 2, "inis": 1, "zipla": 1, "yuvarlan": 1, "altin": 4, "kut_tane": 4, "ui_gez": 2, "ui_sec": 2,
	"savur": 3, "darbe": 5, "darbe_kritik": 2, "ok_vurus": 3, "ok_ucus": 3, "dusman_hazirlik": 3, "hazirlik": 3,
	"patlama": 3, "sarsinti": 2, "olum_vurus": 2, "simsek_catirti": 2, "gok_gurleme": 2,
}
const DEFAULT_LIMIT := 3

## Biyom akustiği: yankı odası, sönüm (yüksek = karanlık), ıslak oran, ön gecikme (ms). Ortam döngüsü "ortam_<id>_dongu".
const BIOME_FX := {
	"otuken": {"room": 0.45, "damp": 0.55, "wet": 0.09, "pre": 20.0, "spread": 0.8},
	"bozkir": {"room": 0.15, "damp": 0.7, "wet": 0.03, "pre": 10.0, "spread": 0.5},
	"sahmeran": {"room": 0.88, "damp": 0.3, "wet": 0.24, "pre": 55.0, "spread": 1.0},
	"kaf": {"room": 0.7, "damp": 0.25, "wet": 0.13, "pre": 90.0, "spread": 1.0},
	"tamu": {"room": 0.75, "damp": 0.9, "wet": 0.17, "pre": 35.0, "spread": 0.9},
	"yurt": {"room": 0.35, "damp": 0.6, "wet": 0.08, "pre": 12.0, "spread": 0.7},
	"baslik": {"room": 0.6, "damp": 0.5, "wet": 0.1, "pre": 30.0, "spread": 0.8},
}

var _streams: Dictionary = {}
var _variants: Dictionary = {}  # önek -> [ad, ad...]
var _last_key: Dictionary = {}  # önek -> son çalınan dosya (art arda tekrar yok)
var _pool: Array = []
var _pool2d: Array = []
var _loops: Dictionary = {}
var _music_a: AudioStreamPlayer
var _music_b: AudioStreamPlayer
var _music_cur := ""
var _amb_a: AudioStreamPlayer
var _amb_b: AudioStreamPlayer
var _amb_cur := ""
var _heart: AudioStreamPlayer
var _music_fade := 0.0
var _last_play: Dictionary = {}
var sfx_db := 0.0
var music_db := -6.0
var biome := ""
var _bus_sfx := BUS_SFX
var _bus_music := BUS_MUSIC

# karıştırma durumu (gerçek zamanla yumuşatılır; vuruş duraklaması/ağır çekimden etkilenmez)
var _menu := false
var _hp_k := 0.0
var _duck := 0.0  # menü (müzik dahil)
var _pduck := 0.0  # duraklatma ya da menü (efekt + ortam)
var _hp_s := 0.0
var _wet := 0.0
var _wet_target := 0.0
var _last_us := 0

var _fx_reverb: AudioEffectReverb
var _fx_lp_sfx: AudioEffectLowPassFilter
var _fx_lp_amb: AudioEffectLowPassFilter
var _fx_lp_music: AudioEffectLowPassFilter
var _lp_idx := {}  # veri yolu adı -> alçak geçiren efekt sırası


func _ready() -> void:
	process_mode = Node.PROCESS_MODE_ALWAYS
	_setup_buses()
	_load_all()
	for i in POOL:
		var p := AudioStreamPlayer.new()
		p.bus = _bus_sfx
		add_child(p)
		_pool.append(p)
	for i in POOL_2D:
		var q := AudioStreamPlayer2D.new()
		q.bus = _bus_sfx
		q.max_distance = 1400.0
		q.attenuation = 1.0
		q.panning_strength = 0.6
		add_child(q)
		_pool2d.append(q)
	_music_a = AudioStreamPlayer.new()
	_music_b = AudioStreamPlayer.new()
	for m in [_music_a, _music_b]:
		m.bus = _bus_music
		add_child(m)
	_amb_a = AudioStreamPlayer.new()
	_amb_b = AudioStreamPlayer.new()
	for m in [_amb_a, _amb_b]:
		m.bus = BUS_AMB
		add_child(m)
	_heart = AudioStreamPlayer.new()
	_heart.bus = BUS_UI
	add_child(_heart)
	_last_us = Time.get_ticks_usec()
	set_volumes(float(Game.meta.get("ses_sfx", 1.0)), float(Game.meta.get("ses_muzik", 0.8)))
	set_biome("baslik")


# ------------------------------------------------------------------ veri yolları
func _ensure_bus(bus_name: String) -> int:
	var idx := AudioServer.get_bus_index(bus_name)
	if idx < 0:
		AudioServer.add_bus()
		idx = AudioServer.bus_count - 1
		AudioServer.set_bus_name(idx, bus_name)
	AudioServer.set_bus_send(idx, "Master")
	while AudioServer.get_bus_effect_count(idx) > 0:
		AudioServer.remove_bus_effect(idx, 0)
	return idx


func _setup_buses() -> void:
	## Master: yapıştırıcı sıkıştırıcı + sert sınırlayıcı (üst üste binen vuruşlar kırpılmaz).
	var mi := 0
	while AudioServer.get_bus_effect_count(mi) > 0:
		AudioServer.remove_bus_effect(mi, 0)
	var glue := AudioEffectCompressor.new()
	glue.threshold = -8.0
	glue.ratio = 2.5
	glue.attack_us = 1500.0
	glue.release_ms = 120.0
	AudioServer.add_bus_effect(mi, glue)
	var lim := AudioEffectHardLimiter.new()
	lim.ceiling_db = -0.5
	lim.release = 0.08
	AudioServer.add_bus_effect(mi, lim)
	# SFX: tepe denetimi -> biyom yankısı -> boğuklaştırıcı (menü / düşük can)
	var si := _ensure_bus(BUS_SFX)
	var comp := AudioEffectCompressor.new()
	comp.threshold = -14.0
	comp.ratio = 3.0
	comp.attack_us = 2000.0
	comp.release_ms = 150.0
	AudioServer.add_bus_effect(si, comp)
	_fx_reverb = AudioEffectReverb.new()
	_fx_reverb.dry = 1.0
	_fx_reverb.wet = 0.0
	_fx_reverb.hipass = 0.25
	AudioServer.add_bus_effect(si, _fx_reverb)
	_fx_lp_sfx = _add_lowpass(si, BUS_SFX)
	# Ortam: yalnızca boğuklaştırıcı
	var ai := _ensure_bus(BUS_AMB)
	_fx_lp_amb = _add_lowpass(ai, BUS_AMB)
	# Müzik: büyük vuruşlarda hafifçe çekilir (SFX yan zincir), menüde boğuklaşır
	var mu := _ensure_bus(BUS_MUSIC)
	var duckc := AudioEffectCompressor.new()
	duckc.threshold = -18.0
	duckc.ratio = 1.8
	duckc.attack_us = 2000.0
	duckc.release_ms = 300.0
	duckc.sidechain = StringName(BUS_SFX)
	AudioServer.add_bus_effect(mu, duckc)
	_fx_lp_music = _add_lowpass(mu, BUS_MUSIC)
	_ensure_bus(BUS_UI)


func _add_lowpass(idx: int, bus_name: String) -> AudioEffectLowPassFilter:
	var lpf := AudioEffectLowPassFilter.new()
	lpf.cutoff_hz = 20000.0
	lpf.resonance = 0.5
	AudioServer.add_bus_effect(idx, lpf)
	var e := AudioServer.get_bus_effect_count(idx) - 1
	_lp_idx[bus_name] = e
	AudioServer.set_bus_effect_enabled(idx, e, false)
	return lpf


func _load_all() -> void:
	var d := DirAccess.open(SFX_DIR)
	if d == null:
		push_warning("Ses: efekt klasörü yok")
		return
	d.list_dir_begin()
	var f := d.get_next()
	while f != "":
		# dışa aktarılmış oyunda dosyalar ".wav.import" / ".wav.remap" olarak listelenebilir
		var fname := f.trim_suffix(".import").trim_suffix(".remap")
		if fname.ends_with(".wav") and not _streams.has(fname.trim_suffix(".wav")):
			var name := fname.trim_suffix(".wav")
			var st: AudioStream = load(SFX_DIR + fname)
			if st:
				if name.ends_with("_dongu"):
					_make_loop(st)
				_streams[name] = st
				var m := name.rfind("_")
				if m > 0 and name.substr(m + 1).is_valid_int():
					var pre := name.substr(0, m)
					if not _variants.has(pre):
						_variants[pre] = []
					_variants[pre].append(name)
		f = d.get_next()


func _make_loop(st: AudioStream) -> void:
	## Döngü sonu kare sayısı: sıkıştırılmış (QOA) verinin bayt sayısı kare sayısı değildir; süre x örnekleme hızı kullanılır.
	if st is AudioStreamWAV:
		var w := st as AudioStreamWAV
		w.loop_mode = AudioStreamWAV.LOOP_FORWARD
		w.loop_begin = 0
		w.loop_end = int(floor(w.get_length() * float(w.mix_rate)))


func set_volumes(sfx: float, music: float) -> void:
	sfx_db = linear_to_db(clampf(sfx, 0.0, 1.0))
	music_db = linear_to_db(clampf(music, 0.0, 1.0)) - 4.0
	_apply_mix()


# ------------------------------------------------------------------ efektler
func has(name: String) -> bool:
	return _streams.has(name) or _variants.has(name)


func play(name: String, vol_db := 0.0, pitch := 1.0, pitch_var := 0.06, min_gap := 0.03, pos := Vector2.INF, vol_var := 1.5) -> Node:
	## Adı verilen efekti çalar. Önek varyantları varsa ("darbe_kunt" -> darbe_kunt_1..3) art arda aynısı gelmeyecek biçimde
	## onlardan seçer, yoksa tam adı çalar. pos verilirse (dünya konumu) kameraya göre sağ-sol ve uzaklıkla çalar.
	var key := ""
	if _variants.has(name):
		var vs: Array = _variants[name]
		var i := randi() % vs.size()
		if vs.size() > 1 and vs[i] == _last_key.get(name, ""):
			i = (i + 1 + randi() % (vs.size() - 1)) % vs.size()
		key = vs[i]
		_last_key[name] = key
	elif _streams.has(name):
		key = name
	else:
		return null
	var now := Time.get_ticks_msec() / 1000.0
	if now - float(_last_play.get(name, -1.0)) < min_gap:
		return null
	_last_play[name] = now
	var bus := _bus_for(name)
	var group := _group_for(name)
	var use2d: bool = pos.is_finite() and bus == BUS_SFX and get_viewport().get_camera_2d() != null
	var p: Node = _voice_for(group, use2d)
	if p == null:
		return null
	var vol := vol_db + randf_range(-0.5, 0.5) * vol_var
	var pit := maxf(0.05, pitch * (1.0 + randf_range(-pitch_var, pitch_var)))
	p.set_meta("g", group)
	p.set_meta("t", Time.get_ticks_msec())
	if p is AudioStreamPlayer2D:
		var q := p as AudioStreamPlayer2D
		q.stop()
		q.bus = bus
		q.stream = _streams[key]
		q.volume_db = vol
		q.pitch_scale = pit
		q.global_position = pos
		q.play()
	else:
		var a := p as AudioStreamPlayer
		a.stop()
		a.bus = bus
		a.stream = _streams[key]
		a.volume_db = vol
		a.pitch_scale = pit
		a.play()
	return p


func play_at(name: String, pos: Vector2, vol_db := 0.0, pitch := 1.0, pitch_var := 0.06, min_gap := 0.03) -> Node:
	## Konumlu kısayol: Ses.play_at("darbe_et", e.center()).
	return play(name, vol_db, pitch, pitch_var, min_gap, pos)


# ------------------------------------------------------------------ v13: darbe hiyerarşisi, patlama, yıldırım
## Kademe -> ses adı, yedek ad (dosya yoksa), ses farkı (dB) ve perde oynaması. 0 hafif, 1 ağır, 2 kritik, 3 öldürücü.
## Dosyalar zaten kademeye göre daha sıcak masterlanmıştır; buradaki fark merdiveni belirginleştirir.
const HIT_TIERS := [
	{"name": "darbe_hafif", "alt": "darbe_et", "db": -3.0, "pv": 0.05},
	{"name": "darbe_agir", "alt": "darbe_kunt", "db": -1.0, "pv": 0.04},
	{"name": "darbe_kritik", "alt": "darbe_kritik", "db": 0.5, "pv": 0.03},
	{"name": "olum_vurus", "alt": "darbe_kritik", "db": 1.5, "pv": 0.025},
]
## Yüzey -> ses: kademe 0..2'de kademe sesinin yerine geçer (öldürücü vuruş her zaman olum_vurus).
const HIT_KIND := {"tas": "darbe_donuk", "kalkan": "darbe_donuk", "metal": "darbe_metal"}
## Ekran dışı patlama eşiği: kameraya uzaklık > görünür alanın yarı köşegeni x bu kat.
const FAR_K := 1.15


func hit(tier: int, pos := Vector2.INF, kind := "") -> Node:
	## Darbe hiyerarşisi: tier 0 hafif / 1 ağır / 2 kritik / 3 öldürücü; kind "tas" ("kalkan") -> darbe_donuk, "metal" -> darbe_metal.
	## Kademeye göre ses farkı ve küçük rastgele perde. Vuruş duraklaması (Game.hitstop) ile aynı karede çağrılır: hafifte geçiş
	## t=0'da, ağır/kritik/öldürücüde 30-45 ms bas ön-yankıdan sonra gelir (duraklamanın içine düşer).
	var t: int = clampi(tier, 0, HIT_TIERS.size() - 1)
	var d: Dictionary = HIT_TIERS[t]
	var name: String = d["name"]
	var vol: float = float(d["db"])
	if t < 3 and HIT_KIND.has(kind):
		name = HIT_KIND[kind]
		vol = -2.0 + 1.0 * t
	if not has(name):
		name = d["alt"]
	return play(name, vol, 1.0, float(d["pv"]), 0.02, pos, 1.0)


func boom(pos := Vector2.INF, size := 1.0, vol_db := 0.0) -> Node:
	## Kademeli patlama (tık -> 15 ms sonra alt bas -> moloz): size >= 1.5 -> patlama_buyuk; konum kameradan uzaksa (ekran dışı)
	## patlama_uzak; yoksa patlama_1..3. Küçük patlamalar biraz ince (perde 1/sqrt(size)).
	var name := "patlama"
	var pit := 1.0
	if size >= 1.5 and has("patlama_buyuk"):
		name = "patlama_buyuk"
	else:
		pit = clampf(1.0 / sqrt(maxf(size, 0.3)), 0.8, 1.3)
	if pos.is_finite() and _is_far(pos) and has("patlama_uzak"):
		name = "patlama_uzak"
		pit = 1.0
	return play(name, vol_db, pit, 0.04, 0.03, pos, 1.0)


func thunder(pos := Vector2.INF, delay := 0.1, vol_db := 0.0) -> Node:
	## Yıldırım: beyaz karede simsek_catirti hemen; gok_gurleme `delay` sn sonra, zaman ölçeğinden bağımsız sayaçla (vuruş
	## duraklaması / ağır çekim gürlemeyi geciktirmez). Ön ipucu için: loop_start("simsek", "simsek_sizirti_dongu", -12.0) / loop_stop.
	var p := play("simsek_catirti", vol_db, 1.0, 0.03, 0.02, pos, 1.0)
	if not has("gok_gurleme"):
		return p
	var roll := func() -> void:
		play("gok_gurleme", vol_db - 1.0, 1.0, 0.05, 0.05, pos, 1.5)
	if delay <= 0.0:
		roll.call()
	else:
		get_tree().create_timer(delay, true, false, true).timeout.connect(roll)
	return p


func _is_far(pos: Vector2) -> bool:
	## Konum ekranın görünür alanının dışında mı (kamera merkezine uzaklık > yarı köşegen x FAR_K)?
	var cam := get_viewport().get_camera_2d()
	if cam == null:
		return false
	var half: Vector2 = get_viewport().get_visible_rect().size * 0.5 / cam.zoom
	return pos.distance_to(cam.get_screen_center_position()) > half.length() * FAR_K


func _bus_for(name: String) -> String:
	if name.begins_with("ortam_"):
		return BUS_AMB
	for pre in UI_PREFIXES:
		if name.begins_with(pre):
			return BUS_UI
	return BUS_SFX


func _group_for(name: String) -> String:
	if LIMITS.has(name):
		return name
	var fam := name.get_slice("_", 0)
	if LIMITS.has(fam):
		return fam
	return name


func _voice_for(group: String, use2d: bool) -> Node:
	## Grup sınırı doluysa grubun en eski sesi; değilse boş ses; hiç boş yoksa havuzun en eskisi.
	var limit: int = LIMITS.get(group, DEFAULT_LIMIT)
	var busy := 0
	var oldest_g: Node = null
	var oldest_g_t := 0
	for pool in [_pool, _pool2d]:
		for p in pool:
			if p.playing and String(p.get_meta("g", "")) == group:
				busy += 1
				var t: int = p.get_meta("t", 0)
				if oldest_g == null or t < oldest_g_t:
					oldest_g = p
					oldest_g_t = t
	if busy >= limit and oldest_g != null and (oldest_g is AudioStreamPlayer2D) == use2d:
		return oldest_g
	if busy >= limit and oldest_g != null:
		oldest_g.call("stop")
	var pool2: Array = _pool2d if use2d else _pool
	var oldest: Node = null
	var oldest_t := 0
	for p in pool2:
		if not p.playing:
			return p
		var t2: int = p.get_meta("t", 0)
		if oldest == null or t2 < oldest_t:
			oldest = p
			oldest_t = t2
	return oldest


# ------------------------------------------------------------------ döngüler
func loop_start(id: String, name: String, vol_db := -6.0, pitch := 1.0) -> void:
	## Sürekli ses (şarj uğultusu, ateş çıtırtısı); aynı id ile tekrar çağrılınca yeniden başlamaz.
	if _loops.has(id) and is_instance_valid(_loops[id]):
		return
	if not _streams.has(name):
		return
	var p := AudioStreamPlayer.new()
	p.bus = _bus_for(name)
	p.stream = _streams[name]
	p.volume_db = vol_db
	p.pitch_scale = pitch
	add_child(p)
	p.play()
	_loops[id] = p


func loop_pitch(id: String, pitch: float) -> void:
	if _loops.has(id) and is_instance_valid(_loops[id]):
		_loops[id].pitch_scale = pitch


func loop_stop(id: String) -> void:
	if _loops.has(id) and is_instance_valid(_loops[id]):
		var p: AudioStreamPlayer = _loops[id]
		var tw := create_tween()
		tw.tween_property(p, "volume_db", -40.0, 0.12)
		tw.tween_callback(p.queue_free)
	_loops.erase(id)


# ------------------------------------------------------------------ müzik ve ortam
var alem_mix := ""  # v12: "yer" -> müzik boğuklaşır
var _usul: Dictionary = {}
var _usul_loaded := false


func usul_now() -> Dictionary:
	## Usul Vuruşu: çalan parçanın usul ızgarasında şu an. d = en yakın usul vuruşuna uzaklık (sn, + geç / - erken),
	## strong = ölçünün ilk vuruşu (düm), k = ölçü içindeki konum 0..1, starts = vuruşların ölçü içi konumları.
	if not _usul_loaded:
		_usul_loaded = true
		var f := FileAccess.open("res://assets/audio/music/usul.json", FileAccess.READ)
		if f:
			var v: Variant = JSON.parse_string(f.get_as_text())
			if v is Dictionary:
				_usul = v
	if _music_cur == "" or not _usul.has(_music_cur) or _music_cur == "baslik":
		return {}
	var p: AudioStreamPlayer = null
	for m in [_music_a, _music_b]:
		if m.playing and (p == null or m.volume_db > p.volume_db):
			p = m
	if p == null:
		return {}
	var u: Dictionary = _usul[_music_cur]
	var step := float(u["step"])
	var groups: Array = u["groups"]
	var bar := 0.0
	var starts: Array = []
	for g in groups:
		starts.append(bar)
		bar += float(g) * step
	var pos := p.get_playback_position() + AudioServer.get_time_since_last_mix() - AudioServer.get_output_latency()
	var t := fposmod(pos, bar)
	var best := 1e9
	var strong := false
	for i in starts.size() + 1:
		var s: float = bar if i == starts.size() else float(starts[i])
		var d := t - s
		if absf(d) < absf(best):
			best = d
			strong = (i == 0 or i == starts.size())
	var ks: Array = []
	for s in starts:
		ks.append(float(s) / bar)
	return {"d": best, "strong": strong, "k": t / bar, "starts": ks, "bar": bar}


func music(track: String, fade := 1.5) -> void:
	## Çapraz geçişli müzik; aynı parça çalıyorsa dokunmaz. Parça bir biyom adıysa yankı ve ortam da ona geçer.
	if BIOME_FX.has(track):
		set_biome(track)
	if track == _music_cur:
		return
	var path := MUSIC_DIR + track + ".wav"
	if not ResourceLoader.exists(path):
		return
	var st: AudioStream = load(path)
	_make_loop(st)
	_music_cur = track
	_crossfade(_music_a, _music_b, st, fade)


func _crossfade(pa: AudioStreamPlayer, pb: AudioStreamPlayer, st: AudioStream, fade: float) -> void:
	var outp := pa if pa.playing else pb
	var inp := pb if outp == pa else pa
	inp.stream = st
	inp.volume_db = -30.0
	inp.play()
	var tw := create_tween().set_parallel(true)
	tw.tween_property(inp, "volume_db", 0.0, fade)
	if outp.playing:
		tw.tween_property(outp, "volume_db", -30.0, fade)
		tw.chain().tween_callback(outp.stop)


func music_stop(fade := 1.0) -> void:
	_music_cur = ""
	for m in [_music_a, _music_b]:
		if m.playing:
			var tw := create_tween()
			tw.tween_property(m, "volume_db", -30.0, fade)
			tw.tween_callback(m.stop)


func ambience(name: String, fade := 2.0) -> void:
	## Ortam döngüsü (rüzgâr, damla, çıtırtı); "" ya da olmayan ad çalanı söndürür.
	if name == _amb_cur:
		return
	_amb_cur = name
	if name == "" or not _streams.has(name):
		_amb_cur = ""
		for m in [_amb_a, _amb_b]:
			if m.playing:
				var tw := create_tween()
				tw.tween_property(m, "volume_db", -40.0, fade)
				tw.tween_callback(m.stop)
		return
	_crossfade(_amb_a, _amb_b, _streams[name], fade)


func set_biome(id: String) -> void:
	## Biyom akustiği: yankı odası/ıslaklığı ve ortam döngüsü. Ses.music(biyom) bunu kendisi çağırır.
	var b: Dictionary = BIOME_FX.get(id, BIOME_FX["otuken"])
	biome = id
	if _fx_reverb:
		_fx_reverb.room_size = float(b["room"])
		_fx_reverb.damping = float(b["damp"])
		_fx_reverb.predelay_msec = float(b["pre"])
		_fx_reverb.spread = float(b["spread"])
	_wet_target = float(b["wet"])
	ambience("ortam_%s_dongu" % id)


# ------------------------------------------------------------------ menü, düşük can
func menu_duck(on: bool) -> void:
	## Menü/panel açıkken oyun sesleri ve müzik kısılır ve boğuklaşır (arayüz sesleri net kalır).
	## Ağaç duraklatıldığında (get_tree().paused) efekt ve ortam kendiliğinden kısılır; müzik yalnızca bununla.
	_menu = on


func low_hp(k: float) -> void:
	## 0 = sağlıklı, 1 = ölüm eşiği. Kalp atışı yükselir/hızlanır, oyun sesleri boğuklaşır. Her karede çağrılabilir.
	_hp_k = clampf(k, 0.0, 1.0)


func _process(_delta: float) -> void:
	var now := Time.get_ticks_usec()
	var dt := clampf(float(now - _last_us) / 1000000.0, 0.0, 0.1)
	_last_us = now
	var paused := get_tree().paused
	_duck = move_toward(_duck, 1.0 if _menu else 0.0, dt * 4.0)
	_pduck = move_toward(_pduck, 1.0 if (_menu or paused) else 0.0, dt * 4.0)
	_hp_s = move_toward(_hp_s, _hp_k, dt * 1.5)
	_wet = move_toward(_wet, _wet_target, dt * 0.25)
	_apply_mix()
	_update_heart()


func _cut(k: float, low: float) -> float:
	## 0 -> 20 kHz, 1 -> low (logaritmik)
	return 20000.0 * pow(low / 20000.0, clampf(k, 0.0, 1.0))


func _set_lp(bus_name: String, fx: AudioEffectLowPassFilter, cutoff: float) -> void:
	if fx == null:
		return
	var idx := AudioServer.get_bus_index(bus_name)
	if idx < 0:
		return
	fx.cutoff_hz = cutoff
	AudioServer.set_bus_effect_enabled(idx, int(_lp_idx.get(bus_name, 0)), cutoff < 18000.0)


func _apply_mix() -> void:
	var hp := _hp_s * _hp_s
	var c_sfx := minf(_cut(_pduck, 1100.0), _cut(hp, 1800.0))
	var c_mus := minf(_cut(_duck, 900.0), _cut(hp, 3500.0))
	if alem_mix == "yer":
		c_mus = minf(c_mus, 1300.0)
	_set_lp(BUS_SFX, _fx_lp_sfx, c_sfx)
	_set_lp(BUS_AMB, _fx_lp_amb, c_sfx)
	_set_lp(BUS_MUSIC, _fx_lp_music, c_mus)
	if _fx_reverb:
		_fx_reverb.wet = _wet
	_bus_vol(BUS_SFX, sfx_db - 6.0 * _pduck - 2.0 * hp)
	_bus_vol(BUS_AMB, sfx_db - 2.0 - 10.0 * _pduck - 3.0 * hp)
	_bus_vol(BUS_MUSIC, music_db - 6.0 * _duck - 4.0 * hp)
	_bus_vol(BUS_UI, sfx_db)


func _bus_vol(bus_name: String, db: float) -> void:
	var idx := AudioServer.get_bus_index(bus_name)
	if idx >= 0:
		AudioServer.set_bus_volume_db(idx, maxf(db, -80.0))


func _update_heart() -> void:
	if _heart == null:
		return
	var k := _hp_s * (1.0 - 0.6 * _pduck)
	if k < 0.03:
		if _heart.playing:
			_heart.stop()
		return
	if not _heart.playing:
		if not _streams.has("kalp_dongu"):
			return
		_heart.stream = _streams["kalp_dongu"]
		_heart.play()
	_heart.volume_db = lerpf(-28.0, -3.0, k)
	_heart.pitch_scale = lerpf(0.85, 1.4, _hp_s)
