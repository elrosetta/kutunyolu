extends SceneTree
## Bölüm üretimi tuzak testi: her stil ve birçok tohum için üretir, kalan çıkmaz (tuzak) hücreleri sayar.
## Kullanım: godot --headless --path . --script res://tools/tests/tuzak_testi.gd


func _init() -> void:
	var W := 230
	var H := 44
	var total_fix := 0
	var bad := 0
	var t0 := Time.get_ticks_msec()
	for style in ["orman", "ucurum", "magara", "harabe", "bozkir", "kuyu"]:
		for seed in range(1, 13):
			var rng := RandomNumberGenerator.new()
			rng.seed = seed * 7919 + style.length()
			var r := LevelGen.generate(rng, W, H, 3, [style])
			var left := LevelGen.traps(LevelGen._haz_as_air(r["grid"]), W, H, r["heights"])
			var ok := LevelGen._reachable(r["grid"], W, H, r["heights"])
			total_fix += int(r.get("trapfix", 0))
			if not left.is_empty() or not ok:
				bad += 1
				print("KÖTÜ stil=%s tohum=%d kalan_tuzak=%d gecilebilir=%s" % [style, seed, left.size(), str(ok)])
	print("tuzak testi: düzeltme=%d kötü=%d süre=%d ms" % [total_fix, bad, Time.get_ticks_msec() - t0])
	quit()
