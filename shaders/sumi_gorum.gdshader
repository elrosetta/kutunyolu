// v42 hikâye sineması: sumi-e paneli kâğıda emilen mürekkep gibi belirir (Sinema.gd, Gorum.gd).
// reveal 0 → 1: önce koyu mürekkep (darbe gövdeleri), sonra yıkamalar, en son boş kâğıt; sınır gürültüyle bükülür ve
// sınırın hemen içinde mürekkep bir an koyulaşır (ıslak kenar). Saydam dokularda (görüm silüeti) alfa da aynı maskeyle
// söner; "dissolve" > 0 ise silüet kenardan duman gibi dağılır.
shader_type canvas_item;
render_mode blend_add;
// v42: sumi_panel.gdshader ile aynı; toplamalı karışım (Gorum.gd: Gün Ana silüeti ışık gibi parlar)

uniform float reveal : hint_range(0.0, 1.0) = 1.0;
uniform float edge_dark : hint_range(0.0, 1.0) = 0.35;
uniform vec2 noise_scale = vec2(7.0, 4.0);
uniform float seed = 0.0;
uniform float dissolve : hint_range(0.0, 1.0) = 0.0;
uniform vec4 tint : source_color = vec4(1.0);

float hash21(vec2 p) {
	p = fract(p * vec2(123.34, 456.21) + seed);
	p += dot(p, p + 45.32);
	return fract(p.x * p.y);
}

float vnoise(vec2 p) {
	vec2 i = floor(p);
	vec2 f = fract(p);
	f = f * f * (3.0 - 2.0 * f);
	float a = hash21(i);
	float b = hash21(i + vec2(1.0, 0.0));
	float c = hash21(i + vec2(0.0, 1.0));
	float d = hash21(i + vec2(1.0, 1.0));
	return mix(mix(a, b, f.x), mix(c, d, f.x), f.y);
}

void fragment() {
	vec4 mod_c = COLOR;   // öğe modülasyonu (modulate / self_modulate)
	vec4 t = texture(TEXTURE, UV);
	float lum = dot(t.rgb, vec3(0.299, 0.587, 0.114));
	float dark = clamp(1.0 - lum * 1.15, 0.0, 1.0);
	float n = vnoise(UV * noise_scale) * 0.62 + vnoise(UV * noise_scale * 3.7 + 11.0) * 0.28 + vnoise(UV * noise_scale * 11.0 + 3.0) * 0.1;
	float v = reveal * 1.45 - 0.22 - n * 0.55 + dark * 0.32;
	float e = 0.15;
	float m = smoothstep(e - 0.06, e + 0.06, v);
	// ıslak kenar: sınırın içinde ince koyu bant
	float rim = smoothstep(e - 0.06, e, v) * (1.0 - smoothstep(e + 0.01, e + 0.12, v));
	vec3 col = t.rgb * (1.0 - rim * edge_dark);
	float a = t.a * m;
	if (dissolve > 0.001) {
		float dn = vnoise(UV * noise_scale * 2.3 + vec2(0.0, TIME * 0.4));
		a *= smoothstep(dissolve - 0.1, dissolve + 0.1, dn * 0.85 + (1.0 - abs(UV.x - 0.5) * 2.0) * 0.15);
	}
	COLOR = vec4(col, a) * tint * mod_c;
}
