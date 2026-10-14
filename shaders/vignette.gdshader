// Kenarları hafifçe karartan, köşeleri mora çeken vinyet.
shader_type canvas_item;

uniform float strength : hint_range(0.0, 1.0) = 0.55;
uniform vec4 edge_color : source_color = vec4(0.06, 0.03, 0.12, 1.0);

void fragment() {
	vec2 d = (UV - vec2(0.5)) * vec2(1.0, 0.75);
	float v = smoothstep(0.28, 0.72, length(d) * 1.25);
	COLOR = vec4(edge_color.rgb, v * strength);
}
