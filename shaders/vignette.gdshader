// Kenarları hafifçe karartan, köşeleri mora çeken vinyet.
shader_type canvas_item;

uniform float strength : hint_range(0.0, 1.0) = 0.55;
uniform vec4 edge_color : source_color = vec4(0.06, 0.03, 0.12, 1.0);
// hasar: kenarlardan içeri kısa kırmızı nabız (tüm ekranı boyamaz; ortadaki dövüş okunur kalır)
uniform float hurt : hint_range(0.0, 1.0) = 0.0;
uniform vec4 hurt_color : source_color = vec4(0.55, 0.02, 0.04, 1.0);

void fragment() {
	vec2 d = (UV - vec2(0.5)) * vec2(1.0, 0.75);
	float r = length(d) * 1.25;
	float v = smoothstep(0.28, 0.72, r);
	float h = smoothstep(0.38, 0.8, r) * hurt;
	vec3 col = mix(edge_color.rgb, hurt_color.rgb, clamp(h * 2.0, 0.0, 1.0));
	COLOR = vec4(col, max(v * strength, h * 0.7));
}
