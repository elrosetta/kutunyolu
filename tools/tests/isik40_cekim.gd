extends Node
## v40 ışık / renk çekim aracı (Ayarlar._ready "--isik40=<klasör>" ile eklenir; başsız değil):
##   godot --path . -- --isik40=C:/mutlak/klasor [--isik40_sahne=biyom,yurt,konak,boss,isin,olum,gecis] [--pencere=1920x1080]
##     [--doku=2] [--isik40_tohum=N] [--isik40_on=once]
## Her sahne için aynı tohum ve aynı kare: <klasör>/<ön ek>_<sahne>.png. Önce / sonra karşılaştırması: tools/tests/isik40_sayfa.py.
##   biyom : 1-10. derinlik (her biyomun iki derinliği), giriş ve bölüm ortası (ikinci Kut Taşı'nın yanı)
##   yurt  : Ulu Kayın yurdu · konak: Ötüken / Şahmeran / Tamu konağı · boss: 3 arena (tanıtım çekiminin 3 karesi)
##   isin  : ışınlanma çözülmesi (kapanış, varış, açılış t<0,5, son) · olum: ölüm derecesi (0,3 / 0,9 / 1,6 / 2,2 sn)
##   gecis : bölüm başı mürekkep perdesi (perde t < 0,97 / 0,62 / 0,28: zamana değil perdenin evresine bağlı)

var main: Node
var out_dir := ""
var on_ek := "sonra"
var sahneler: Array = ["biyom", "yurt", "konak", "boss", "isin", "olum", "gecis"]
var tohum := 7


func _ready() -> void:
	process_mode = Node.PROCESS_MODE_ALWAYS
	for a in OS.get_cmdline_user_args():
		var s := String(a)
		if s.begins_with("--isik40="):
			out_dir = s.trim_prefix("--isik40=")
		elif s.begins_with("--isik40_sahne="):
			sahneler = Array(s.trim_prefix("--isik40_sahne=").split(","))
		elif s.begins_with("--isik40_tohum="):
			tohum = int(s.trim_prefix("--isik40_tohum="))
		elif s.begins_with("--isik40_on="):
			on_ek = s.trim_prefix("--isik40_on=")
	DirAccess.make_dir_recursive_absolute(out_dir)
	_run.call_deferred()


func _p(s: String) -> void:
	print("[isik40] ", s)


func _bekle(sn: float) -> void:
	await get_tree().create_timer(sn, true, false, true).timeout


func _cek(ad: String) -> void:
	await RenderingServer.frame_post_draw
	var img := get_viewport().get_texture().get_image()
	if get_viewport().use_hdr_2d:
		if img.get_format() != Image.FORMAT_RGBA8 and img.get_format() != Image.FORMAT_RGB8:
			img.convert(Image.FORMAT_RGBA8)
		img.linear_to_srgb()
	var path := "%s/%s_%s.png" % [out_dir, on_ek, ad]
	img.save_png(path)
	_p("çekim %s %s" % [path.get_file(), str(img.get_size())])


func _perde_bekle() -> void:
	## bölüm başı perdesi (Perde) tamamen açılana dek bekle (yükleme takılmasında perde bekler; kare belirlenimci kalsın)
	while Perde._inst != null and is_instance_valid(Perde._inst) and Perde._inst.rect.visible:
		await get_tree().process_frame


func _perde_t_bekle(esik: float) -> void:
	## perde t bu eşiğin altına inene dek bekle (geçiş kareleri zamana değil perdenin evresine bağlı: takılmadan bağımsız)
	while Perde._inst != null and is_instance_valid(Perde._inst) and Perde._inst.t > esik:
		await get_tree().process_frame


func _main() -> Node:
	if main == null:
		main = get_tree().root.get_node_or_null("Main")
	if main == null:
		for c in get_tree().root.get_children():
			if c.get("hud") != null and c.has_method("_build_level"):
				main = c
	return main


func _bolum(d: int) -> Node:
	Game.run["depth"] = d
	Game.run["tier"] = Zorluk.kademe(d)
	Game.run["hp"] = float(Game.run.get("max_hp", 100.0))
	var m := _main()
	if m.level:
		m.level.queue_free()
	var lv := Level.new()
	lv.process_mode = Node.PROCESS_MODE_PAUSABLE
	m.add_child(lv)
	m.level = lv
	lv.build(tohum * 100 + d)
	lv.harita_requested.connect(m._harita_ac)
	lv.player_died.connect(m._on_died)
	m.hud.level = lv
	m.rehber.reset(lv)
	m._start_play()
	return lv


func _tp(pl: Node, cell: Vector2i) -> void:
	pl.global_position = Vector2(cell.x * Level.TS + Level.TS / 2.0, (cell.y + 1) * Level.TS - 1.0)
	pl.velocity = Vector2.ZERO


func _sakin(lv: Node) -> void:
	## düşmanlar durağan ve oyuncuya saldırmasın (kare belirlenimci kalsın): uykuda bırakılır
	for e in get_tree().get_nodes_in_group("dusman"):
		if is_instance_valid(e) and e != lv.get("boss"):
			e.set("aggro", false)
			e.set("ai_t", 99.0)


func _run() -> void:
	await _bekle(0.5)
	var m := _main()
	if m == null:
		_p("Main bulunamadı")
		get_tree().quit()
		return
	for s in sahneler:
		match String(s):
			"biyom":
				for d in [1, 2, 3, 4, 5, 6, 7, 8, 9, 10]:
					var lv := _bolum(d)
					_sakin(lv)
					await _bekle(1.6)
					await _perde_bekle()
					await _cek("d%02d_giris" % d)
					if lv.harita != null and lv.harita.tasi.size() >= 2:
						_tp(lv.player, lv.harita.tasi[1]["cell"] + Vector2i(-1, 0))
						lv.player.facing = 1
						await _bekle(1.4)
						await _cek("d%02d_orta" % d)
			"yurt":
				m._build_hub()
				m._start_play()
				await _bekle(1.6)
				await _perde_bekle()
				await _cek("yurt")
				m.level.player.global_position.x = 50.0 * Level.TS
				await _bekle(1.4)
				await _cek("yurt_otag")
			"konak":
				for d in [2, 6, 10]:
					Game.run["depth"] = d
					Game.run["tier"] = Zorluk.kademe(d)
					m._build_konak()
					m._start_play()
					await _bekle(1.6)
					await _perde_bekle()
					await _cek("konak_d%02d" % d)
			"boss":
				for bid in ["kara_boru_han", "sahmeran", "erlik_han"]:
					Game.run["depth"] = {"kara_boru_han": 2, "tepegoz": 4, "sahmeran": 6, "yelbegen": 8, "erlik_han": 10}.get(bid, 2)
					Game.run["tier"] = Zorluk.kademe(int(Game.run["depth"]))
					m._build_boss(bid)
					m._start_play()
					await _bekle(0.35)
					await _perde_bekle()
					await _cek("boss_%s_a" % bid)
					await _bekle(0.8)
					await _cek("boss_%s_b" % bid)
					await _bekle(1.6)
					await _cek("boss_%s_c" % bid)
					# boss oyuncuya yaklaşınca sığdırma çerçevesi
					if m.level.boss and is_instance_valid(m.level.boss):
						m.level.boss.global_position.x = m.level.player.global_position.x + 260.0
						await _bekle(1.6)
						await _cek("boss_%s_d" % bid)
			"isin":
				var lv := _bolum(1)
				_sakin(lv)
				await _bekle(0.6)
				await _perde_bekle()
				var pl: Node = lv.player
				for i in mini(2, lv.tasi.size()):
					lv.tasi[i].kesfet(true)
				_tp(pl, lv.harita.tasi[1]["cell"] + Vector2i(1, 0))
				await _bekle(0.8)
				if lv.isinlan(0):
					await _bekle(lv.ISIN_SURE - 0.1)
					await _cek("isin_kapanis")
					await _bekle(0.13)
					await _cek("isin_varis")
					await _perde_t_bekle(0.5)
					await _cek("isin_acilis")
					await _perde_bekle()
					await _bekle(0.4)
					await _cek("isin_son")
			"olum":
				var lv := _bolum(3)
				_sakin(lv)
				await _bekle(1.2)
				await _perde_bekle()
				var pl: Node = lv.player
				pl.inv_t = 0.0
				Game.run["hp"] = 1.0
				pl.take_hit(999.0, null, null, true)
				await _bekle(0.3)
				await _cek("olum_a")
				await _bekle(0.6)
				await _cek("olum_b")
				await _bekle(0.7)
				await _cek("olum_c")
				await _bekle(0.6)
				await _cek("olum_d")
				get_tree().paused = false
			"gecis":
				var lv := _bolum(5)
				_sakin(lv)
				await _perde_t_bekle(0.97)
				await _cek("gecis_a")
				await _perde_t_bekle(0.62)
				await _cek("gecis_b")
				await _perde_t_bekle(0.28)
				await _cek("gecis_c")
	_p("BITTI %s" % out_dir)
	get_tree().quit()
