// Dead Cells tarzı ışıklandırma: 2D ışıkların katkısını 3 sert banda nicele.
// Normal map CanvasTexture'dan otomatik gelir; burada sadece renk ve ışık işlenir.
shader_type canvas_item;

uniform float band_hi : hint_range(0.0, 1.0) = 0.62;
uniform float band_lo : hint_range(0.0, 1.0) = 0.20;
uniform float flash : hint_range(0.0, 1.0) = 0.0;
uniform vec4 flash_color : source_color = vec4(1.0, 0.97, 0.9, 1.0);
uniform vec4 tint : source_color = vec4(1.0, 1.0, 1.0, 1.0);

void fragment() {
	// Godot 4'te COLOR zaten doku × köşe rengi (modulate) olarak gelir.
	vec4 c = COLOR * tint;
	c.rgb = mix(c.rgb, flash_color.rgb, flash);
	COLOR = c;
}

void light() {
	float ndl = dot(NORMAL, LIGHT_DIRECTION);
	float b = ndl > band_hi ? 1.0 : (ndl > band_lo ? 0.62 : 0.28);
	LIGHT = vec4(COLOR.rgb * LIGHT_COLOR.rgb * LIGHT_ENERGY * b, LIGHT_COLOR.a);
}
