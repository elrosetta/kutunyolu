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
	var gp := "res://assets/sprites/%s_e.png" % sid
	meta["glow_tex"] = load(gp) if ResourceLoader.exists(gp) else null
	_sprites[sprite_name] = meta
	return meta


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


func enemy_def(id: String) -> Dictionary:
	for e in world["enemies"]:
		if e["id"] == id:
			return e
	return {}
