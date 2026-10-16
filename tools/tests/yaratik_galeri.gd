extends Node
## Yaratık galerisi: seçili düşmanları oyuncunun önüne dikip her pozu (boşta, hareket, saldırı uyarısı, saldırı,
## yaralanma) oyun içinde çeker. Stil v2 yaratık çizimlerini 1080p'de denetlemek için.
##   godot --path . --resolution 1920x1080 -- --stil=v2 --derinlik=1 --yaratik=cor,agac_iyesi --yaratik_cikti=C:/x/klasor
## Her düşman için <klasor>/<kimlik>_<poz>.png (düşman çevresinden 1:1 kırpım, 720x600) ve <kimlik>_tam.png (1080p kare).
## AI kapatılır (set_physics_process(false)); kare SpriteAnim.show_frame ile seçilir.

var main: Node
var kinds: Array = ["cor", "agac_iyesi", "balbal", "arcura"]
var out_dir := "user://galeri"
const CROP := Vector2i(720, 600)
## sprite kimliğine göre pozlar: [ad, animasyon, kare]
const POSES := {
	"cor": [["bosta", "idle", 0], ["hareket", "idle", 3], ["uyari", "attack", 0], ["saldiri", "attack", 1], ["yara", "hurt", 0]],
	"agac_iyesi": [["bosta", "idle", 0], ["hareket", "walk", 1], ["uyari", "windup", 1], ["saldiri", "slam", 0], ["yara", "hurt", 0]],
	"balbal": [["uyku", "dormant", 0], ["bosta", "idle", 0], ["hareket", "hop", 2], ["uyari", "windup", 1], ["saldiri", "strike", 0]],
	"arcura": [["bosta", "idle", 0], ["hareket", "run", 1], ["uyari", "cast", 0], ["saldiri", "cast", 1], ["yara", "hurt", 0]],
}


func _ready() -> void:
	process_mode = Node.PROCESS_MODE_ALWAYS
	for arg in OS.get_cmdline_user_args():
		var a := String(arg)
		if a.begins_with("--yaratik="):
			kinds = Array(a.trim_prefix("--yaratik=").split(","))
		elif a.begins_with("--yaratik_cikti="):
			out_dir = a.trim_prefix("--yaratik_cikti=")
	DirAccess.make_dir_recursive_absolute(out_dir)
	_run.call_deferred()


func _wait(s: float) -> void:
	await get_tree().create_timer(s, true, false, false).timeout


func _clear() -> void:
	for e in get_tree().get_nodes_in_group("dusman"):
		e.queue_free()


func _grab() -> Image:
	await RenderingServer.frame_post_draw
	var img := get_viewport().get_texture().get_image()
	if get_viewport().use_hdr_2d:
		if img.get_format() != Image.FORMAT_RGBA8 and img.get_format() != Image.FORMAT_RGB8:
			img.convert(Image.FORMAT_RGBA8)
		img.linear_to_srgb()
	return img


func _screen(n: Node2D) -> Vector2:
	var vp := n.get_viewport()
	return n.get_global_transform_with_canvas().origin * (Vector2(vp.get_window().size) / vp.get_visible_rect().size)


func _run() -> void:
	await _wait(4.5)  # bölüm başlık kartı geçsin
	var pl: Node2D = main.level.player
	pl.set_physics_process(false)
	for k in kinds:
		_clear()
		await _wait(0.1)
		var e: Enemy = main.level.spawn_enemy(k, pl.global_position + Vector2(118, 0), false)
		if e == null:
			continue
		e.set_physics_process(false)
		e.set_process(false)
		if e.flying:
			e.position.y = pl.global_position.y - 30
		else:
			e.position.y = pl.global_position.y
		e.facing = -1
		e.anim.set_facing(-1)
		e.hp = 1.0e6
		e.max_hp = 1.0e6
		var poses: Array = POSES.get(e.sprite_kind, POSES["cor"])
		for ps in poses:
			e.anim.show_frame(String(ps[1]), int(ps[2]))
			await _wait(0.35)
			var img := await _grab()
			var c := _screen(e) + Vector2(0, -150)
			var r := Rect2i(Vector2i(c) - CROP / 2, CROP)
			r = r.intersection(Rect2i(Vector2i.ZERO, img.get_size()))
			img.get_region(r).save_png("%s/%s_%s.png" % [out_dir, k, ps[0]])
			if ps[0] == "bosta":
				img.save_png("%s/%s_tam.png" % [out_dir, k])
			print("[galeri] %s %s %s:%d" % [k, ps[0], ps[1], ps[2]])
	print("[galeri] bitti")
	get_tree().quit()
