// Kenarları hafifçe karartan, köşeleri mora çeken vinyet (Işık ve parlama "Az" düzeyi: derecelendirme kapalıyken).
shader_type canvas_item;

uniform float strength : hint_range(0.0, 1.0) = 0.55;
uniform vec4 edge_color : source_color = vec4(0.06, 0.03, 0.12, 1.0);
// hasar: kenarlardan içeri kısa kırmızı nabız (tüm ekranı boyamaz; ortadaki dövüş okunur kalır)
uniform float hurt : hint_range(0.0, 1.0) = 0.0;
uniform vec4 hurt_color : source_color = vec4(0.55, 0.02, 0.04, 1.0);
// v40 ölüm: vinyet daralıp koyulaşır, soğuk bir perde iner (grade_v2 "death" ile aynı ad; Perde.olum sürer)
uniform float death : hint_range(0.0, 1.0) = 0.0;

void fragment() {
	vec2 d = (UV - vec2(0.5)) * vec2(1.0, 0.75);
	float r = length(d) * 1.25;
	float v = smoothstep(0.28 - death * 0.14, 0.72 - death * 0.1, r);
	float h = smoothstep(0.38, 0.8, r) * hurt;
	vec3 col = mix(edge_color.rgb, hurt_color.rgb, clamp(h * 2.0, 0.0, 1.0));
	col = mix(col, vec3(0.02, 0.015, 0.04), death * 0.6);
	float a = max(v * min(1.0, strength + death * 0.4), h * 0.7);
	a = max(a, death * 0.3);
	COLOR = vec4(col, a);
}
