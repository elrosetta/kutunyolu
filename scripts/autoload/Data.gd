extends Node
## Veri ve görsel önbelleği: JSON verileri, sprite meta bilgisi, CanvasTexture'lar (renk + normal map).

var items: Dictionary = {}
var world: Dictionary = {}
var story: Dictionary = {}
var weapon_meta: Dictionary = {}
var decor_meta: Dictionary = {}
var tile_meta: Dictionary = {}
var weapon_tex: CanvasTexture
var weapon_glow: Texture2D
var _sprites: Dictionary = {}
var _decor: Dictionary = {}


## Doku paketi (2K / 4K): assets_hd/x2 ya da x4 altında aynı göreli yolla, temel dokunun 2 / 4 katı
## çözünürlükte yeniden çizilmiş renk dokuları. manifest.json temel boyutları tutar; yüklenen büyük doku
## ImageTexture.set_size_override ile temel boyutta raporlanır: bölgeler, kareler ve çizim boyu değişmez,
## yalnızca ayrıntı artar. Normal ve parlama haritaları temel çözünürlükte kalır.
var pack := 1
var _pack_dir := ""
var _pack_manifest: Dictionary = {}
var _tex_cache: Dictionary = {}


func _init_pack() -> void:
	pack = Ayarlar.pack_scale()
	Ayarlar.lock_pack()
	if pack <= 1:
		return
	_pack_dir = "res://assets_hd/x%d/" % pack
	_pack_manifest = load_json(_pack_dir + "manifest.json") if FileAccess.file_exists(_pack_dir + "manifest.json") else {}
	if _pack_manifest.is_empty():
		push_warning("Doku paketi x%d bulunamadı; standart dokular kullanılıyor" % pack)
		pack = 1


func tex(path: String) -> Texture2D:
	## Renk dokusu: paket etkinse ve bu doku pakette varsa yüksek çözünürlüklü sürüm (temel boyutta raporlanır)
	if _tex_cache.has(path):
		return _tex_cache[path]
	var t: Texture2D = null
	if pack > 1:
		var rel := path.trim_prefix("res://assets/")
		if _pack_manifest.has(rel) and ResourceLoader.exists(_pack_dir + rel):
			var big: Texture2D = load(_pack_dir + rel)
			var it := ImageTexture.create_from_image(big.get_image())
			var bs: Array = _pack_manifest[rel]
			it.set_size_override(Vector2i(int(bs[0]), int(bs[1])))
			t = it
	if t == null:
		t = load(path)
	_tex_cache[path] = t
	return t


func tex_full(path: String) -> Texture2D:
	## Paket dokusunu GERÇEK boyutunda döndürür (boyut geçersiz kılma yok). TileSet geçersiz kılmayı yok
	## saydığı için karo atlasları bununla yüklenir ve karo boyu paket çarpanıyla büyütülür.
	if pack_has(path):
		return load(_pack_dir + path.trim_prefix("res://assets/"))
	return load(path)


func pack_has(path: String) -> bool:
	return pack > 1 and _pack_manifest.has(path.trim_prefix("res://assets/"))


var _weapon_img: Image


func weapon_image() -> Image:
	## Silah atlasının TEMEL görüntüsü (bölge çözümlemesi için; paketten bağımsız)
	if _weapon_img == null:
		var bt: Texture2D = load("res://assets/weapons/weapons.png")
		_weapon_img = bt.get_image()
		if _weapon_img.is_compressed():
			_weapon_img.decompress()
	return _weapon_img


## Görsel stil (deneme): -- --stil=v2 ile bir varlığın "_v2" adlı sürümü varsa o yüklenir, yoksa v1 kalır
## (bengu -> bengu_v2, bengu_kol -> bengu_kol_v2, otuken karoları -> otuken_v2, otuken_3_mid -> otuken_3_mid_v2).
## v2 sanatı: tools/artgen/style_v2.py, export_v2.py. v1 dosyaları olduğu gibi durur.
var stil := "v1"


func stil_id(id: String, probe: String) -> String:
	## probe: kimliğin yerine geçeceği "%s" içeren yol, ör. "res://assets/sprites/%s.json"
	if stil == "v1":
		return id
	var alt := "%s_%s" % [id, stil]
	var pth := probe % alt
	if ResourceLoader.exists(pth) or FileAccess.file_exists(pth):
		return alt
	return id


func _ready() -> void:
	for arg in OS.get_cmdline_user_args():
		if String(arg).begins_with("--stil="):
			stil = String(arg).trim_prefix("--stil=")
	_init_pack()
	items = load_json("res://data/items.json")
	world = load_json("res://data/world.json")
	story = load_json("res://data/story.json")
	weapon_meta = load_json("res://assets/weapons/weapons.json")
	# silah atlası doku yoğunluğu (weapons.json "texel"): 2 = hücre 128x80, oyunda 1/2 ölçekle çizilir, dünya boyu aynı
	weapon_texel = float(weapon_meta.get("texel", 1.0))
	decor_meta = load_json("res://assets/decor/decor.json")
	tile_meta = load_json("res://assets/tiles/otuken.json")
	weapon_tex = canvas_tex("res://assets/weapons/weapons.png", "res://assets/weapons/weapons_n.png")
	weapon_glow = load("res://assets/weapons/weapons_e.png")
	_load_weapon_stil()
	# piksel yazı tipi (tools/artgen/pixfont.py): 13 = 1x, 26 = 2x, 39 = 3x; yalnızca tam sayı ölçek
	pixel_font = load("res://assets/ui/pixel.fnt")
	if pixel_font:
		pixel_font.fixed_size_scale_mode = TextServer.FIXED_SIZE_SCALE_INTEGER_ONLY
		pixel_font.antialiasing = TextServer.FONT_ANTIALIASING_NONE
	else:
		push_error("Piksel yazı tipi yüklenemedi")


var pixel_font: FontFile
var weapon_texel := 1.0


func wscale() -> float:
	## Silah sprite'ının oyun içi ölçeği (1 / doku yoğunluğu)
	return 1.0 / weapon_texel
var _icon_cache: Dictionary = {}


func weapon_icon_rect(item_id: String, mat_id: String) -> Rect2:
	## Silah karesinin dolu bölgesi (arayüz simgeleri için sıkı kırpma); önbellekli.
	var key := item_id + "/" + mat_id
	if _icon_cache.has(key):
		return _icon_cache[key]
	var reg := weapon_region(item_id, mat_id)
	var r := reg
	var img: Image = weapon_image()
	if img:
		var used := img.get_region(Rect2i(reg)).get_used_rect()
		if used.size.x > 0:
			r = Rect2(reg.position + Vector2(used.position), Vector2(used.size))
	_icon_cache[key] = r
	return r


func load_json(path: String) -> Dictionary:
	var f := FileAccess.open(path, FileAccess.READ)
	if f == null:
		push_error("JSON açılamadı: %s" % path)
		return {}
	var parsed: Variant = JSON.parse_string(f.get_as_text())
	if parsed == null or not (parsed is Dictionary):
		push_error("JSON çözümlenemedi: %s" % path)
		return {}
	return parsed


func canvas_tex(diffuse: String, normal: String) -> CanvasTexture:
	var ct := CanvasTexture.new()
	ct.diffuse_texture = tex(diffuse)
	if ResourceLoader.exists(normal):
		ct.normal_texture = load(normal)
	ct.texture_filter = CanvasItem.TEXTURE_FILTER_NEAREST
	return ct


func sprite(sprite_name: String) -> Dictionary:
	if _sprites.has(sprite_name):
		return _sprites[sprite_name]
	var sid := stil_id(sprite_name, "res://assets/sprites/%s.json")
	var meta := load_json("res://assets/sprites/%s.json" % sid)
	meta["tex"] = canvas_tex("res://assets/sprites/%s.png" % sid, "res://assets/sprites/%s_n.png" % sid)
	if is_linear(meta):
		(meta["tex"] as CanvasTexture).texture_filter = CanvasItem.TEXTURE_FILTER_LINEAR_WITH_MIPMAPS
	var gp := "res://assets/sprites/%s_e.png" % sid
	meta["glow_tex"] = load(gp) if ResourceLoader.exists(gp) else null
	# sayfalı sayfa (tools/artgen/export_ink.py, json "pages" > 1): satırlar sırayla <ad>.png, <ad>_p1.png ... dokularına
	# bölünür (her biri en çok 4096 px). "page_texs"/"page_glows" sayfa dokuları; SpriteAnim satırın sayfasını seçer.
	var pages := int(meta.get("pages", 1))
	if pages > 1:
		var texs: Array = [meta["tex"]]
		var glows: Array = [meta["glow_tex"]]
		for k in range(1, pages):
			var pid := "%s_p%d" % [sid, k]
			var ct := canvas_tex("res://assets/sprites/%s.png" % pid, "")
			if is_linear(meta):
				ct.texture_filter = CanvasItem.TEXTURE_FILTER_LINEAR_WITH_MIPMAPS
			texs.append(ct)
			var gpk := "res://assets/sprites/%s_e.png" % pid
			glows.append(load(gpk) if ResourceLoader.exists(gpk) else null)
		meta["page_texs"] = texs
		meta["page_glows"] = glows
	_sprites[sprite_name] = meta
	return meta


func forget_sprite(sprite_name: String) -> void:
	## Büyük sprite sayfalarını (stil v2 bosslar, 20-55 MB VRAM) önbellekten bırakır; dokular son kullanıcısıyla
	## (sahne düğümleri, ceset kopyası) birlikte serbest kalır. Yeniden istenirse diskten yüklenir.
	if not _sprites.has(sprite_name):
		return
	var sid := stil_id(sprite_name, "res://assets/sprites/%s.json")
	_sprites.erase(sprite_name)
	var base := "res://assets/sprites/%s" % sid
	for k in _tex_cache.keys():
		var ks := String(k)
		if ks == base + ".png" or ks.begins_with(base + "_p"):
			_tex_cache.erase(k)


## Stil v2 mürekkep-cel sprite'ları (tools/artgen/inkkit.py; json "filter": "linear"): kenar yumuşatmalı çizim,
## doğrusal süzgeç + mipmap ile ve ink_char.gdshader ile çizilir (piksel-AA ve 3 bantlı toon ışığı yok).
## CanvasTexture süzgeci onu kullanan her düğüme (hayalet, ceset, vuruş karesi) geçer.
const INK_SHADER: Shader = preload("res://shaders/ink_char.gdshader")


static func is_linear(meta: Dictionary) -> bool:
	return String(meta.get("filter", "")) == "linear"


func decor(decor_name: String) -> Dictionary:
	if _decor.has(decor_name):
		return _decor[decor_name]
	var d: Dictionary = decor_meta.get(decor_name, {}).duplicate()
	d["tex"] = canvas_tex("res://assets/decor/%s.png" % decor_name, "res://assets/decor/%s_n.png" % decor_name)
	var gp := "res://assets/decor/%s_e.png" % decor_name
	d["glow_tex"] = load(gp) if ResourceLoader.exists(gp) else null
	_decor[decor_name] = d
	return d


func find_item(id: String) -> Dictionary:
	for cat in ["weapons", "shields", "gadgets"]:
		for it in items[cat]:
			if it["id"] == id:
				var d: Dictionary = it.duplicate(true)
				d["cat"] = cat
				return d
	return {}


func material_def(id: String) -> Dictionary:
	for m in items["materials"]:
		if m["id"] == id:
			return m
	return items["materials"][0]


func has_weapon_sprite(item_id: String) -> bool:
	return weapon_meta.has("items") and weapon_meta["items"].has(item_id)


func weapon_region(item_id: String, mat_id: String) -> Rect2:
	var cell: Array = weapon_meta["cell"]
	var row := int(weapon_meta["items"][item_id]["row"])
	var col: int = weapon_meta["materials"].find(mat_id)
	if col < 0:
		col = 0
	return Rect2(col * cell[0], row * cell[1], cell[0], cell[1])


func weapon_pivot(item_id: String) -> Vector2:
	var p: Array = weapon_meta["items"][item_id]["pivot"]
	return Vector2(p[0], p[1])


## Stil v2 mürekkep-cel silah atlası (tools/artgen/weapons_ink.py): weapons_<stil>.json + sayfalar
## (weapons_<stil>_<n>.png). Eşya başına sıkı kırpma, pivot kırpma içinde; doğrusal süzgeç + mipmap.
## Arayüz simgeleri (PixUI) v1 piksel atlasında kalır; dünyadaki silah sprite'ları weapon_sprite() kullanır.
var weapon_stil: Dictionary = {}
var _wst_pages: Array = []
var _wst_imgs: Dictionary = {}
var _wspr_cache: Dictionary = {}


func _load_weapon_stil() -> void:
	if stil == "v1":
		return
	var jp := "res://assets/weapons/weapons_%s.json" % stil
	if not FileAccess.file_exists(jp):
		return
	weapon_stil = load_json(jp)
	for pg in weapon_stil.get("pages", []):
		var ct := CanvasTexture.new()
		ct.diffuse_texture = load("res://assets/weapons/%s" % pg)
		ct.texture_filter = CanvasItem.TEXTURE_FILTER_LINEAR_WITH_MIPMAPS
		_wst_pages.append(ct)


func weapon_sprite(item_id: String, mat_id: String) -> Dictionary:
	## Dünyadaki silah sprite'ı: {tex, region, pivot, scale, linear, page}. Stil atlasında varsa o (v2), yoksa v1.
	var key := item_id + "/" + mat_id
	if _wspr_cache.has(key):
		return _wspr_cache[key]
	var d := {}
	var its: Dictionary = weapon_stil.get("items", {})
	if its.has(item_id) and not _wst_pages.is_empty():
		var e: Dictionary = its[item_id]
		var ms: Dictionary = e["m"]
		var m: Array = ms.get(mat_id, ms.values()[0])
		var sz: Array = e["size"]
		var pv: Array = e["pivot"]
		d = {"tex": _wst_pages[int(m[0])], "region": Rect2(float(m[1]), float(m[2]), float(sz[0]), float(sz[1])),
			"pivot": Vector2(float(pv[0]), float(pv[1])), "scale": 1.0 / float(weapon_stil.get("texel", 4.0)),
			"linear": true, "page": int(m[0])}
	else:
		d = {"tex": weapon_tex, "region": weapon_region(item_id, mat_id), "pivot": weapon_pivot(item_id), "scale": wscale(),
			"linear": false, "page": -1}
	_wspr_cache[key] = d
	return d


func weapon_sprite_image(d: Dictionary) -> Image:
	## weapon_sprite() sözlüğünün doku görüntüsü (yay uçları gibi piksel taramaları için)
	var p := int(d.get("page", -1))
	if p < 0:
		return weapon_image()
	if not _wst_imgs.has(p):
		var img: Image = (_wst_pages[p] as CanvasTexture).diffuse_texture.get_image()
		if img.is_compressed():
			img.decompress()
		_wst_imgs[p] = img
	return _wst_imgs[p]


func enemy_def(id: String) -> Dictionary:
	for e in world["enemies"]:
		if e["id"] == id:
			return e
	return {}
