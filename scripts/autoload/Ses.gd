extends Node
## Ses yöneticisi: efekt havuzu (varyant seçimi, perde oynaması, aynı anda tekrar sınırı), döngü sesleri
## (şarj, ateş) ve çapraz geçişli müzik. Dosyalar `assets/audio` altında prosedürel üretilir (tools/audiogen).

const SFX_DIR := "res://assets/audio/sfx/"
const MUSIC_DIR := "res://assets/audio/music/"
const POOL := 24

var _streams: Dictionary = {}
var _variants: Dictionary = {}  # önek -> [ad, ad...]
var _pool: Array = []
var _loops: Dictionary = {}
var _music_a: AudioStreamPlayer
var _music_b: AudioStreamPlayer
var _music_cur := ""
var _music_fade := 0.0
var _last_play: Dictionary = {}
var sfx_db := 0.0
var music_db := -6.0
var _bus_sfx := "SFX"
var _bus_music := "Muzik"


func _ready() -> void:
	process_mode = Node.PROCESS_MODE_ALWAYS
	_setup_buses()
	_load_all()
	for i in POOL:
		var p := AudioStreamPlayer.new()
		p.bus = _bus_sfx
		add_child(p)
		_pool.append(p)
	_music_a = AudioStreamPlayer.new()
	_music_b = AudioStreamPlayer.new()
	for m in [_music_a, _music_b]:
		m.bus = _bus_music
		add_child(m)
	set_volumes(float(Game.meta.get("ses_sfx", 1.0)), float(Game.meta.get("ses_muzik", 0.8)))


func _setup_buses() -> void:
	for b in [_bus_sfx, _bus_music]:
		if AudioServer.get_bus_index(b) < 0:
			AudioServer.add_bus()
			AudioServer.set_bus_name(AudioServer.bus_count - 1, b)
			AudioServer.set_bus_send(AudioServer.bus_count - 1, "Master")


func _load_all() -> void:
	var d := DirAccess.open(SFX_DIR)
	if d == null:
		push_warning("Ses: efekt klasörü yok")
		return
	d.list_dir_begin()
	var f := d.get_next()
	while f != "":
		if f.ends_with(".wav"):
			var name := f.trim_suffix(".wav")
			var st: AudioStream = load(SFX_DIR + f)
			if st:
				if name.ends_with("_dongu") and st is AudioStreamWAV:
					(st as AudioStreamWAV).loop_mode = AudioStreamWAV.LOOP_FORWARD
					(st as AudioStreamWAV).loop_end = (st as AudioStreamWAV).data.size() / 2
				_streams[name] = st
				var m := name.rfind("_")
				if m > 0 and name.substr(m + 1).is_valid_int():
					var pre := name.substr(0, m)
					if not _variants.has(pre):
						_variants[pre] = []
					_variants[pre].append(name)
		f = d.get_next()


func set_volumes(sfx: float, music: float) -> void:
	sfx_db = linear_to_db(clampf(sfx, 0.0, 1.0))
	music_db = linear_to_db(clampf(music, 0.0, 1.0)) - 4.0
	AudioServer.set_bus_volume_db(AudioServer.get_bus_index(_bus_sfx), sfx_db)
	AudioServer.set_bus_volume_db(AudioServer.get_bus_index(_bus_music), music_db)


func has(name: String) -> bool:
	return _streams.has(name) or _variants.has(name)


func play(name: String, vol_db := 0.0, pitch := 1.0, pitch_var := 0.06, min_gap := 0.03) -> AudioStreamPlayer:
	## Adı verilen efekti çalar; "savur_hafif" gibi bir önek verilirse varyantlardan rastgele seçer.
	var key := name
	if not _streams.has(key):
		if _variants.has(name):
			var vs: Array = _variants[name]
			key = vs[randi() % vs.size()]
		else:
			return null
	var now := Time.get_ticks_msec() / 1000.0
	if now - float(_last_play.get(name, -1.0)) < min_gap:
		return null
	_last_play[name] = now
	var p := _free_player()
	if p == null:
		return null
	p.stream = _streams[key]
	p.volume_db = vol_db
	p.pitch_scale = pitch * (1.0 + randf_range(-pitch_var, pitch_var))
	p.play()
	return p


func _free_player() -> AudioStreamPlayer:
	var oldest: AudioStreamPlayer = null
	var oldest_pos := -1.0
	for p in _pool:
		if not p.playing:
			return p
		if p.get_playback_position() > oldest_pos:
			oldest_pos = p.get_playback_position()
			oldest = p
	return oldest


func loop_start(id: String, name: String, vol_db := -6.0, pitch := 1.0) -> void:
	## Sürekli ses (şarj uğultusu, ateş çıtırtısı); aynı id ile tekrar çağrılınca yeniden başlamaz.
	if _loops.has(id) and is_instance_valid(_loops[id]):
		return
	if not _streams.has(name):
		return
	var p := AudioStreamPlayer.new()
	p.bus = _bus_sfx
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


func music(track: String, fade := 1.5) -> void:
	## Çapraz geçişli müzik; aynı parça çalıyorsa dokunmaz.
	if track == _music_cur:
		return
	var path := MUSIC_DIR + track + ".wav"
	if not ResourceLoader.exists(path):
		return
	var st: AudioStream = load(path)
	if st is AudioStreamWAV:
		(st as AudioStreamWAV).loop_mode = AudioStreamWAV.LOOP_FORWARD
		(st as AudioStreamWAV).loop_end = (st as AudioStreamWAV).data.size() / 2
	_music_cur = track
	var outp := _music_a if _music_a.playing else _music_b
	var inp := _music_b if outp == _music_a else _music_a
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
