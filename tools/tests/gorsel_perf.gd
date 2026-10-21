extends Node
## v38 görüntü / GPU başarım ölçümü (Ayarlar._ready "--gpu_perf" ile ekler; başka test bayraklarıyla birleşir).
##   godot --path . -- --gpu_perf --pencere=2560x1440 --derinlik=5 --tohum=3 --bekle=5 --olcum_sn=10 --gpu_faz=2
##   (--otomatik / --vahset / --yurt ile birlikte: sahne kendi akışında oynar, ölçüm pencereleri ardışık)
## Her faz için tek satır "gpu_perf:" yazar: kare süresi ort / %95 / en kötü (ms, CPU duvar saati), GPU süresi
## (kök görüntü alanı, RenderingServer ölçümü), FPS, 2D çizim çağrısı / öğe / ilkel sayıları, doku ve toplam video belleği,
## görünür ışık (gölgeli) sayısı. Ayrıca açılış: ilk kare (motor başlangıcından ms) ve bölüm kurulum kareleri.
## Ölçüm boyunca dikey eşitleme kapalı ve kare sınırı yok (gerçek iş yükü); ayar kaydedilmez. --gpu_perf=<dosya> satırları
## dosyaya da ekler.

var _out := ""
var _wait := 5.0
var _dur := 10.0
var _phases := 1
var _vp_rid: RID
var _last_level: Object = null
var _builds: Array = []


func _ready() -> void:
	process_mode = Node.PROCESS_MODE_ALWAYS
	for a in OS.get_cmdline_user_args():
		var s := String(a)
		if s.begins_with("--gpu_perf="):
			_out = s.trim_prefix("--gpu_perf=")
		elif s.begins_with("--bekle="):
			_wait = maxf(0.1, float(s.trim_prefix("--bekle=")))
		elif s.begins_with("--olcum_sn="):
			_dur = maxf(1.0, float(s.trim_prefix("--olcum_sn=")))
		elif s.begins_with("--gpu_faz="):
			_phases = maxi(1, int(s.trim_prefix("--gpu_faz=")))
	DisplayServer.window_set_vsync_mode(DisplayServer.VSYNC_DISABLED)
	Engine.max_fps = 0
	_vp_rid = get_viewport().get_viewport_rid()
	RenderingServer.viewport_set_measure_render_time(_vp_rid, true)
	_run()


func _log(line: String) -> void:
	print(line)
	if _out != "":
		var f := FileAccess.open(_out, FileAccess.READ_WRITE if FileAccess.file_exists(_out) else FileAccess.WRITE)
		if f:
			f.seek_end()
			f.store_line(line)


func _level() -> Object:
	var m := get_tree().current_scene
	return m.get("level") if m else null


func _run() -> void:
	await RenderingServer.frame_post_draw
	_log("gpu_perf: ilk_kare=%d ms pencere=%s surucu=%s/%s gpu=%s hd=%d" % [Time.get_ticks_msec(), str(get_tree().root.size),
		RenderingServer.get_current_rendering_driver_name(), RenderingServer.get_current_rendering_method(),
		RenderingServer.get_video_adapter_name(), Ayarlar.hd_active])
	_last_level = _level()
	var t_end := Time.get_ticks_usec() + int(_wait * 1e6)
	var last := Time.get_ticks_usec()
	while Time.get_ticks_usec() < t_end:
		await RenderingServer.frame_post_draw
		last = _track(last)
	for ph in _phases:
		var times: Array = []
		var gpu: Array = []
		var dc := 0.0
		var items := 0.0
		var prims := 0.0
		var t0 := Time.get_ticks_usec()
		last = t0
		while float(Time.get_ticks_usec() - t0) / 1e6 < _dur:
			await RenderingServer.frame_post_draw
			var now := Time.get_ticks_usec()
			times.append(float(now - last) / 1000.0)
			last = _track(last)
			gpu.append(RenderingServer.viewport_get_measured_render_time_gpu(_vp_rid))
			dc += get_viewport().get_render_info(Viewport.RENDER_INFO_TYPE_CANVAS, Viewport.RENDER_INFO_DRAW_CALLS_IN_FRAME)
			items += get_viewport().get_render_info(Viewport.RENDER_INFO_TYPE_CANVAS, Viewport.RENDER_INFO_OBJECTS_IN_FRAME)
			prims += get_viewport().get_render_info(Viewport.RENDER_INFO_TYPE_CANVAS, Viewport.RENDER_INFO_PRIMITIVES_IN_FRAME)
		var n := maxf(1.0, times.size())
		var st := _stats(times)
		var gs := _stats(gpu)
		var lights := _lights()
		var lv := _level()
		var bio := ""
		if lv:
			var bd: Dictionary = lv.get("biome") if lv.get("biome") is Dictionary else {}
			bio = "yurt" if lv.get("hub") else "%s/%d" % [str(bd.get("id", "?")), int(Game.run.get("depth", 0))]
		_log("gpu_perf: faz=%d sahne=%s kare=%d ort=%.2fms p95=%.2fms en_kotu=%.2fms fps=%.1f gpu_ort=%.2fms gpu_p95=%.2fms cizim=%.0f oge=%.0f ilkel=%.0f doku_vram=%.0fMB toplam_vram=%.0fMB isik=%d golgeli=%d hd_doku=%d hd_yukleme=%.2fsn" % [
			ph, bio, times.size(), st[0], st[1], st[2], 1000.0 / maxf(0.01, st[0]), gs[0], gs[1], dc / n, items / n, prims / n,
			RenderingServer.get_rendering_info(RenderingServer.RENDERING_INFO_TEXTURE_MEM_USED) / 1048576.0,
			RenderingServer.get_rendering_info(RenderingServer.RENDERING_INFO_VIDEO_MEM_USED) / 1048576.0, lights[0], lights[1],
			int(Data.get("_pack_hits")), float(Data.get("_pack_usec")) / 1e6])
	if OS.get_cmdline_user_args().has("--gpu_doku"):
		_dump_textures()
	if not _builds.is_empty():
		_log("gpu_perf: bolum_kurulum_kareleri=%s ms" % str(_builds))
	_log("gpu_perf: bitti")
	get_tree().quit()


func _track(last: int) -> int:
	## bölüm değiştiyse o karenin süresi (bölüm kurulumu + ilk dokuların yüklenmesi) kaydedilir
	var now := Time.get_ticks_usec()
	var lv := _level()
	if lv != _last_level:
		_last_level = lv
		_builds.append(snappedf(float(now - last) / 1000.0, 0.1))
	return now


func _stats(a: Array) -> Array:
	if a.is_empty():
		return [0.0, 0.0, 0.0]
	var s := a.duplicate()
	s.sort()
	var avg := 0.0
	for x in s:
		avg += float(x)
	avg /= s.size()
	return [avg, float(s[int(s.size() * 0.95)]), float(s[-1])]


func _lights() -> Array:
	var n := 0
	var sh := 0
	var stack: Array = [get_tree().root]
	while not stack.is_empty():
		var nd: Node = stack.pop_back()
		if nd is Light2D and (nd as Light2D).is_visible_in_tree() and (nd as Light2D).enabled:
			n += 1
			if (nd as Light2D).shadow_enabled:
				sh += 1
		stack.append_array(nd.get_children())
	return [n, sh]



func _dump_textures() -> void:
	## --gpu_doku: sahnedeki düğümlerin ve Data önbelleğinin kullandığı benzersiz dokular (yol, boyut); VRAM tahmini
	## araç tarafında (.import sıkıştırmasına göre)
	var seen := {}
	var stack: Array = [get_tree().root]
	var add := func(t: Variant) -> void:
		if t is CanvasTexture:
			t = (t as CanvasTexture).diffuse_texture
		if t is Texture2D and not seen.has(t):
			seen[t] = true
	while not stack.is_empty():
		var nd: Node = stack.pop_back()
		for prop in ["texture", "texture_normal", "normal_map"]:
			if prop in nd:
				add.call(nd.get(prop))
		if nd is CanvasItem and (nd as CanvasItem).material is ShaderMaterial:
			var sm := (nd as CanvasItem).material as ShaderMaterial
			if sm.shader:
				for u in sm.shader.get_shader_uniform_list():
					add.call(sm.get_shader_parameter(u["name"]))
		if nd is TileMapLayer and (nd as TileMapLayer).tile_set:
			var ts := (nd as TileMapLayer).tile_set
			for i in ts.get_source_count():
				var src := ts.get_source(ts.get_source_id(i))
				if src is TileSetAtlasSource:
					add.call((src as TileSetAtlasSource).texture)
		stack.append_array(nd.get_children())
	for t in (Data.get("_tex_cache") as Dictionary).values():
		add.call(t)
	for t in seen:
		var tx := t as Texture2D
		var nm := tx.resource_path if tx.resource_path != "" else "img:" + tx.resource_name
		_log("gpu_doku: %s %dx%d" % [nm, tx.get_width(), tx.get_height()])
	_log("gpu_doku_sayi: %d" % seen.size())
