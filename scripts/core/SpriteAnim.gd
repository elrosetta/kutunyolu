class_name SpriteAnim
extends Node2D
## JSON meta ile çalışan sprite animasyonu. Renk + normal map (CanvasTexture) ve ayrı bir
## parlama katmanı (ışıktan etkilenmeyen, toplamalı) kullanır. Kareler bir atlas satırındadır.

signal finished(anim_name: String)

var meta: Dictionary
var base: Sprite2D
var glow: Sprite2D
var mat: ShaderMaterial
var anim := ""
var frame := 0
var speed := 1.0
var manual := false
var facing := 1
var texel := 1.0  # doku yoğunluğu (meta "texel"): 1.5 = 1.5x piksel; sprite 1/texel ölçekle çizilir, dünya boyu aynı
var shadow: GroundShadow  # sahibin (get_parent) ayaklarının altındaki temas gölgesi
var _t := 0.0
## v29 yönetmen (docs/v29/enemy_anim_json.md): açıkken play / show_frame yalnızca yapay zekânın İSTEĞİNİ kaydeder
## (req, req_frame); gösterilecek kareyi sahibi (Enemy._anim_tick) drive / drive_loop ile seçer.
var director := false
var req := ""
var req_frame := -1      # show_frame isteği (-1: play isteği)
var req_restart := false
var dspeed := 1.0        # yönetmenin hız çarpanı (adım kilidi; speed'den bağımsız: donma speed = 0 ile durur)


func setup(sprite_name: String) -> void:
	meta = Data.sprite(sprite_name)
	texel = float(meta.get("texel", 1.0))
	base = Sprite2D.new()
	base.texture = meta["tex"]
	base.region_enabled = true
	base.centered = false
	mat = ShaderMaterial.new()
	mat.shader = Data.INK_SHADER  # mürekkep-cel: doğrusal süzgeç + mipmap, düz ışık
	base.material = mat
	add_child(base)
	if meta.get("glow_tex") != null:
		glow = Sprite2D.new()
		glow.texture = meta["glow_tex"]
		glow.texture_filter = CanvasItem.TEXTURE_FILTER_LINEAR_WITH_MIPMAPS
		glow.region_enabled = true
		glow.centered = false
		var gm := CanvasItemMaterial.new()
		gm.blend_mode = CanvasItemMaterial.BLEND_MODE_ADD
		gm.light_mode = CanvasItemMaterial.LIGHT_MODE_UNSHADED
		glow.material = gm
		glow.self_modulate = Color(1.6, 1.6, 1.6)
		add_child(glow)
	set_facing(1)
	play(meta["anims"].keys()[0])
	_attach_shadow()


func _attach_shadow() -> void:
	## Temas gölgesi sahibin (oyuncu, düşman, boss, NPC, kılık, ruh kurdu) ilk çocuğu olur.
	## Genişlik: sahibin çarpışma boyu (size) varsa ondan, yoksa kare genişliğinden (meta "shadow_w" ile ezilebilir).
	## Görünürlük/alfa bu SpriteAnim'den izlenir; genişlik bu düğümün ölçeğiyle çarpılır (seçkin, ezilme/esneme).
	var host := get_parent() as Node2D
	if host == null or shadow != null:
		return
	var cell: Array = meta["cell"]
	var w := float(meta.get("shadow_w", float(cell[0]) / texel * 0.25))
	var sz = host.get("size")
	if sz is Vector2:
		w = maxf(8.0, (sz as Vector2).x * 0.9)
	shadow = GroundShadow.attach(host, w, self, self)


func has_anim(n: String) -> bool:
	return meta["anims"].has(n)


func play(n: String, restart := false) -> void:
	if not has_anim(n):
		return
	if director:
		if n != req or req_frame >= 0 or restart:
			req_restart = req_restart or restart or n != req
		req = n
		req_frame = -1
		return
	_play(n, restart)


func _play(n: String, restart := false) -> void:
	if n == anim and not restart:
		return
	anim = n
	frame = 0
	_t = 0.0
	manual = false
	_apply()


func show_frame(n: String, f: int) -> void:
	## Saldırı gibi zamanlaması kodla yönetilen animasyonlar için doğrudan kare seçimi.
	if not has_anim(n):
		return
	if director:
		req = n
		req_frame = f
		return
	drive(n, f)


func drive(n: String, f: int) -> void:
	## v29: yönetmenin doğrudan kare seçimi (director açıkken de çalışır)
	if not has_anim(n):
		return
	anim = n
	manual = true
	frame = clampi(f, 0, int(meta["anims"][n]["frames"]) - 1)
	_apply()


func drive_loop(n: String, sp := 1.0, restart := false) -> void:
	## v29: yönetmenin döngü oynatması (kendi fps'iyle, dspeed çarpanıyla)
	if not has_anim(n):
		return
	dspeed = sp
	if n != anim or manual or restart:
		_play(n, true)


func frame_rect(n: String, f: int) -> Array:
	## v29: bir karenin [doku, bölge] çifti (ceset ölüm karelerini oynatır; sayfalı sayfalar dahil)
	var a: Dictionary = meta["anims"][n]
	var cell: Array = meta["cell"]
	var row := int(a["row"])
	var col := clampi(f, 0, int(a["frames"]) - 1)
	var tex: Texture2D = meta["tex"]
	if a.has("page"):
		var fc := maxi(1, int(a.get("cols", 9999)))
		row += col / fc
		col = col % fc
		if meta.has("page_texs"):
			tex = meta["page_texs"][mini(int(a["page"]), (meta["page_texs"] as Array).size() - 1)]
	elif meta.has("page_texs"):
		var pr := maxi(1, int(meta.get("page_rows", 9999)))
		var pg := mini(row / pr, (meta["page_texs"] as Array).size() - 1)
		row -= pg * pr
		tex = meta["page_texs"][pg]
	return [tex, Rect2(col * float(cell[0]), float(row) * float(cell[1]), float(cell[0]), float(cell[1]))]


func frame_count(n: String) -> int:
	return int(meta["anims"][n]["frames"]) if has_anim(n) else 1


func set_facing(dir: int) -> void:
	facing = 1 if dir >= 0 else -1
	var cell: Array = meta["cell"]
	var org: Array = meta["origin"]
	var x := -float(org[0]) if facing > 0 else -(float(cell[0]) - float(org[0]))
	base.flip_h = facing < 0
	base.scale = Vector2.ONE / texel
	base.position = Vector2(x, -float(org[1])) / texel
	if glow:
		glow.flip_h = base.flip_h
		glow.scale = base.scale * _glow_k()
		glow.position = base.position


func _glow_k() -> float:
	## Işıma sayfası çözünürlüğü (json "glow_scale": 2 = yarım boy ışıma sayfası; export_boss_ink.py). Yoksa 1.
	return float(meta.get("glow_scale", 1.0))


var _flash_on := false
static var _ortak_t := -9.0   # v31: ortak flaş penceresinin başı
static var _ortak_n := 0      # v31: pencerede başlayan flaş sayısı
var _flash_k := 1.0
var _flash_at := -9.0


func set_flash(v: float) -> void:
	## v22: art arda gelen darbe flaşları söner — 0,4 sn içinde yeniden başlayan flaş bir öncekinin %55'i (en az %20);
	## ilk flaş da tam beyaz değil (0,45). Vuruş donmasında flaş gerçek zamanda uzar; hızlı kombolarda düşman bembeyaz
	## siluete dönüp okunmaz oluyordu.
	if v > 0.05 and not _flash_on:
		var now := Time.get_ticks_msec() / 1000.0
		_flash_k = maxf(0.2, _flash_k * 0.55) if now - _flash_at < 0.4 else 0.45
		_flash_at = now
		# v31 çok hedef: aynı 0,15 sn içinde başlayan flaşlar paylaşılır — 2. düşman ×0,7, 3. ×0,5, sonrakiler ×0,35
		# (savaş sanatı / bitiriş birden çok düşmana değince ekran beyaz silüet yığınına dönmesin)
		if now - _ortak_t > 0.15:
			_ortak_t = now
			_ortak_n = 0
		_ortak_n += 1
		_flash_k *= 1.0 if _ortak_n <= 1 else (0.7 if _ortak_n == 2 else (0.5 if _ortak_n == 3 else 0.35))
	_flash_on = v > 0.05
	mat.set_shader_parameter("flash", v * _flash_k)


func set_tint(c: Color) -> void:
	mat.set_shader_parameter("tint", c)


func _process(delta: float) -> void:
	if anim == "" or manual:
		return
	var a: Dictionary = meta["anims"][anim]
	_t += delta * float(a["fps"]) * speed * dspeed
	while _t >= 1.0:
		_t -= 1.0
		frame += 1
		if frame >= int(a["frames"]):
			if a["loop"]:
				frame = 0
			else:
				frame = int(a["frames"]) - 1
				_t = 0.0
				_apply()
				finished.emit(anim)
				return
	_apply()


func _apply() -> void:
	var a: Dictionary = meta["anims"][anim]
	var cell: Array = meta["cell"]
	var row := int(a["row"])
	var col := frame
	if a.has("page"):
		# animasyon başına sayfa + sarmalı satır (tools/artgen/export_boss_ink.py; dev boss kareleri): kareler "cols"
		# sütunda bir alt satıra geçer, "row" sayfadaki ilk satır
		var fc := maxi(1, int(a.get("cols", 9999)))
		row += frame / fc
		col = frame % fc
		var pg2 := int(a["page"])
		if meta.has("page_texs"):
			pg2 = mini(pg2, (meta["page_texs"] as Array).size() - 1)
			base.texture = meta["page_texs"][pg2]
			if glow and meta["page_glows"][pg2] != null:
				glow.texture = meta["page_glows"][pg2]
	elif meta.has("page_texs"):
		# sayfalı sayfa: satırın sayfası (Data.sprite); kopyalar (hayalet, ceset, vuruş karesi) base.texture'ı izler
		var pr := maxi(1, int(meta.get("page_rows", 9999)))
		var pg := mini(row / pr, (meta["page_texs"] as Array).size() - 1)
		row -= pg * pr
		base.texture = meta["page_texs"][pg]
		if glow and meta["page_glows"][pg] != null:
			glow.texture = meta["page_glows"][pg]
	var r := Rect2(col * float(cell[0]), float(row) * float(cell[1]), float(cell[0]), float(cell[1]))
	base.region_rect = r
	if glow:
		var gk := _glow_k()
		glow.region_rect = Rect2(r.position / gk, r.size / gk)


func anchor(key: String) -> Variant:
	## Ayak noktasına göre çapa konumu (yöne göre aynalanmış); yoksa null.
	var a: Dictionary = meta["anims"][anim]
	var data: Array = a["data"]
	if frame >= data.size():
		return null
	var d: Dictionary = data[frame]
	if not d.has(key):
		return null
	return Vector2(float(d[key][0]) * facing, float(d[key][1]))


func anchor_angle(key: String) -> float:
	var a: Dictionary = meta["anims"][anim]
	var data: Array = a["data"]
	if frame >= data.size():
		return 0.0
	var d: Dictionary = data[frame]
	var ang := float(d.get(key, 0.0))
	return ang if facing > 0 else PI - ang
