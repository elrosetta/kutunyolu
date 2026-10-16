// Stil v2 mürekkep vuruş efektleri (scripts/core/InkFX.gd): patlama yıldızı, fırça dokunuşu, kesik izi, kritik
// damgası, yer sıçrantısı, ensō. Atlas (assets/fx/ink/ink_fx.png, tools/artgen/inkfx.py) veri taşır:
//   R işaretli uzaklık (0,5 kenar)  G koyu mürekkep / sıcak çekirdek  B çizim sırası  A erime gürültüsü
// Köşe verisi (COLOR.rgb HDR 2D'de doğrusala çevrildiği için yalnızca UV ve COLOR.a):
//   UV.x = atlas_u + 2 x biçem (0 renkli sıçrantı, 1 mürekkep damgası, 2 sıcak kesik, 3 soluk/kuru)
//   UV.y = atlas_v + 2 x açılış (0..63: çizim sırası eşiği)
//   COLOR.a = erime (0 tam .. 1 yok)
shader_type canvas_item;
render_mode blend_premul_alpha, unshaded;

uniform sampler2D atlas : filter_linear_mipmap, repeat_disable;
uniform vec3 c_ink = vec3(0.004, 0.001, 0.002);
uniform vec3 c_core = vec3(0.16, 0.003, 0.006);
uniform vec3 c_body = vec3(0.78, 0.012, 0.006);
uniform vec3 c_rim = vec3(1.0, 0.16, 0.02);
uniform vec3 c_hot = vec3(1.0, 0.86, 0.62);
uniform float hot_gain = 2.4;
uniform float glow_gain = 0.5;

void fragment() {
	float var_f = floor(UV.x * 0.5);
	float q = floor(UV.y * 0.5);
	vec2 uv = vec2(UV.x - var_f * 2.0, UV.y - q * 2.0);
	float reveal = q / 63.0;
	float diss = clamp(COLOR.a, 0.0, 1.0);
	vec4 d = texture(atlas, uv);
	float sdf = d.r;
	// açılış: sıra alanı eşiğin altında kalan kısım görünür (patlama merkezden dışa, kesik bir uçtan öbürüne)
	float rv = smoothstep(d.b - 0.035, d.b + 0.005, reveal * 1.04);
	float front = 1.0 - smoothstep(0.0, 0.18, reveal * 1.04 - d.b);   // açılış cephesinin hemen arkası
	// erime: eşik yükselir (şekil incelir, gürültüyle parçalanır); taze cephede mürekkep bir tık kalın
	float th = 0.5 + diss * (0.16 + 0.32 * d.a) + (d.a - 0.5) * 0.05 - front * 0.03 * (1.0 - diss);
	float w = fwidth(sdf) * 0.8 + 0.004;
	float a = smoothstep(th - w, th + w, sdf) * rv;
	float inner = smoothstep(0.5, 0.64, sdf);
	vec3 col;
	float fresh = 1.0 - smoothstep(0.0, 0.35, diss);
	if (var_f < 0.5) {
		col = mix(c_rim, c_body, inner);
		col = mix(col, c_core, smoothstep(0.62, 0.9, sdf) * 0.5);
		col = mix(col, c_ink, clamp(d.g * 0.6, 0.0, 1.0));
		col = mix(col, c_hot * hot_gain, front * fresh * (1.0 - d.g) * 0.8);
	} else if (var_f < 1.5) {
		// mürekkep damgası: koyu (paletin mürekkebi siyaha yakın), ince renkli kenar, uçlarda koyu kızıl
		col = mix(c_rim * 1.2, c_ink * 0.3, smoothstep(0.5, 0.56, sdf));
		col = mix(col, c_core * 0.8, (1.0 - d.g) * inner * 0.55);
	} else if (var_f < 2.5) {
		col = mix(c_rim, c_body, inner * 0.6);
		col = mix(col, c_hot * hot_gain * 1.2, clamp(d.g * 1.4, 0.0, 1.0) * fresh);
		col = mix(col, c_rim * 1.3, d.g * (1.0 - fresh));
	} else {
		col = mix(c_rim, c_body, inner);
		a *= 0.55;
	}
	// ışıma: şeklin hemen dışında, taze iken (toplamalı)
	float halo = smoothstep(0.3, 0.49, sdf) * (1.0 - smoothstep(0.49, 0.55, sdf)) * rv;
	float g = var_f > 0.5 && var_f < 1.5 ? 0.35 : 1.0;
	vec3 add = mix(c_rim, c_hot, 0.3) * glow_gain * g * halo * fresh * fresh;
	COLOR = vec4(col * a + add * (1.0 - a), a);
}
