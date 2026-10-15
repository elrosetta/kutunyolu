// Zemin: karolardaki ANAHTAR renkli toprak pikselleri, dünya koordinatından okunan dikişsiz
// toprak dokusuyla değiştirilir (karo tekrarı görünmez). Derinlik dokusu yüzeyden uzaklaştıkça
// toprağı yumuşakça karartır. Işıklandırma Dead Cells tarzı 3 bantlıdır.
// soil_density: dünya pikseli başına doku pikseli (1.5 → 1080p'de her doku pikseli 2x2 ekran pikseli),
// karo atlası da aynı yoğunlukta üretilir, böylece iki ızgara üst üste oturur.
shader_type canvas_item;

#include "res://shaders/aapix.gdshaderinc"

uniform sampler2D soil_tex : filter_nearest, repeat_enable;
uniform sampler2D soil_n : filter_nearest, repeat_enable;
// isteğe bağlı ışıma dokusu (lav damarları, kristaller): siyah = ışımaz
uniform sampler2D soil_e : filter_nearest, repeat_enable, hint_default_black;
uniform float soil_density = 1.0;
uniform float emis_gain = 3.2;
// karo atlasındaki kırmızı anahtar (lav çatlağı / ışıyan yosun) bu renkte ışır; siyahsa toprak sayılır
uniform vec4 glow_col : source_color = vec4(0.0, 0.0, 0.0, 1.0);
uniform sampler2D depth_tex : filter_linear;
uniform vec2 map_size_px = vec2(5520.0, 1056.0);
uniform vec4 deep_color : source_color = vec4(0.04, 0.03, 0.06, 1.0);
uniform float deep_amount : hint_range(0.0, 1.0) = 0.85;
uniform float band_hi = 0.62;
uniform float band_lo = 0.20;
// karo üstündeki "lit" anahtarlı pikseller yukarı bakan normal alır: aydan ince bir ışık çizgisi düşer
uniform float top_tilt : hint_range(0.0, 1.0) = 0.6;
uniform float spec_band : hint_range(0.0, 1.0) = 0.92;
uniform float spec_gain : hint_range(0.0, 1.0) = 0.12;

varying vec2 world_pos;
varying vec4 vcol;

void vertex() {
	world_pos = (MODEL_MATRIX * vec4(VERTEX, 0.0, 1.0)).xy;
	vcol = COLOR;
}

void fragment() {
	vec4 c = texture(TEXTURE, UV);
	vec3 k_soil = vec3(1.0, 0.0, 1.0);
	// Anahtarlar yalnızca 0/1 bileşenli: HDR'de sRGB→doğrusal dönüşümünden etkilenmez.
	vec3 k_shade = vec3(0.0, 1.0, 1.0);
	vec3 k_lit = vec3(1.0, 1.0, 0.0);
	vec3 k_edge = vec3(0.0, 0.0, 1.0);
	vec3 k_glow = vec3(1.0, 0.0, 0.0);
	float is_soil = step(distance(c.rgb, k_soil), 0.06);
	float is_shade = step(distance(c.rgb, k_shade), 0.06);
	float is_lit = step(distance(c.rgb, k_lit), 0.06);
	float is_edge = step(distance(c.rgb, k_edge), 0.06);
	float is_glow = step(distance(c.rgb, k_glow), 0.06);
	float has_glow = step(0.001, dot(glow_col.rgb, vec3(1.0)));
	is_soil = max(is_soil, is_glow * (1.0 - has_glow));
	float any_soil = max(max(is_soil, is_edge), max(is_shade, is_lit));
	vec2 suv = (floor(world_pos * soil_density) + 0.5) / vec2(textureSize(soil_tex, 0));
	if (any_soil > 0.5 && c.a > 0.5) {
		// keskin-kenar yumuşatmalı: kamera kayarken toprak taneleri titremez
		vec3 s = aa_sample_wrap(soil_tex, world_pos * soil_density).rgb;
		vec3 e = texture(soil_e, suv).rgb;
		s *= mix(1.0, 0.6, is_shade);
		s *= mix(1.0, 0.38, is_edge);
		s = mix(s, min(s * 1.22 + vec3(0.03, 0.02, 0.0), vec3(1.0)), is_lit);
		float d = texture(depth_tex, world_pos / map_size_px).r;
		s = mix(s, deep_color.rgb, smoothstep(0.0, 1.0, d) * deep_amount);
		// ışıyan damarlar derinlikte de sönmez (yalnızca hafifçe kısılır)
		s += e * emis_gain * (1.0 - 0.45 * d);
		c.rgb = s;
		// zemin üstü (lit) pikselleri yukarı eğ: yukarıdan gelen ay ışığı üst bandı/parlamayı burada yakalar,
		// aşağıdaki çıralar yakalamaz (haritada +Y aşağı: yukarı bakan normal = yeşil kanal > 0.5)
		NORMAL_MAP = mix(texture(soil_n, suv).rgb, vec3(0.5, 0.5 + 0.45 * top_tilt, 1.0 - 0.4 * top_tilt), is_lit);
	} else if (is_glow * has_glow > 0.5 && c.a > 0.5) {
		c.rgb = glow_col.rgb * emis_gain * 0.7;
		NORMAL_MAP = vec3(0.5, 0.5, 1.0);
	} else {
		if (c.a > 0.0) {
			AA_TEX(TEXTURE, UV, c);
		}
		NORMAL_MAP = texture(NORMAL_TEXTURE, UV).rgb;
	}
	// Not: Godot 4'te COLOR zaten doku × köşe rengi; burada yalnızca köşe rengiyle (modulate) çarpılır.
	COLOR = c * vcol;
}

void light() {
	float ndl = dot(NORMAL, LIGHT_DIRECTION);
	float b = ndl > band_hi ? 1.0 : (ndl > band_lo ? 0.62 : 0.28);
	vec3 lit = COLOR.rgb * b;
	// hafif parlama bandı: ışığa tam bakan toprak taneleri ve karo üstleri bir tık açılır
	lit += step(spec_band, ndl) * spec_gain * (lit + vec3(0.4));
	LIGHT = vec4(lit * LIGHT_COLOR.rgb * LIGHT_ENERGY, LIGHT_COLOR.a);
}
