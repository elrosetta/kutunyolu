// Dead Cells tarzı ışıklandırma: 2D ışıkların katkısını 3 sert banda nicele.
// Normal map CanvasTexture'dan otomatik gelir; burada sadece renk ve ışık işlenir.
// Hacim hissi için iki ek basamak (varsayılanlarla açık, kod değişikliği gerekmez):
//   parlama bandı : ışığa tam bakan pikseller (ndl > spec_band) bir tık açılır, beyaza çalar
//   kenar ışığı   : normal map'te siluete yatık (NORMAL.z < rim_edge) ve ışığa dönük pikseller
//                   ince bir çizgi gibi yanar; gövdeyi arka plandan koparır, "kâğıt" hissini kırar
shader_type canvas_item;

#include "res://shaders/aapix.gdshaderinc"

// pixel_aa: 1 = keskin-kenar yumuşatmalı örnekleme (titreme yok), 0 = eski en yakın komşu
uniform float pixel_aa : hint_range(0.0, 1.0) = 1.0;
varying vec4 vcol;

void vertex() {
	vcol = COLOR;
}

uniform float band_hi : hint_range(0.0, 1.0) = 0.62;
uniform float band_lo : hint_range(0.0, 1.0) = 0.20;
uniform float flash : hint_range(0.0, 1.0) = 0.0;
uniform vec4 flash_color : source_color = vec4(1.0, 0.97, 0.9, 1.0);
uniform vec4 tint : source_color = vec4(1.0, 1.0, 1.0, 1.0);
uniform float spec_band : hint_range(0.0, 1.0) = 0.92;
uniform float spec_gain : hint_range(0.0, 1.0) = 0.15;
uniform vec4 spec_tint : source_color = vec4(1.0, 0.98, 0.92, 1.0);
uniform float rim_edge : hint_range(0.0, 1.0) = 0.9;
uniform float rim_facing : hint_range(-1.0, 1.0) = 0.35;
uniform float rim_gain : hint_range(0.0, 1.0) = 0.3;
// ay gölgesi (GroundShadow, Level.moon_occluded): yönlü ışığın (ay) bu payı kesilir; noktasal ışıklar etkilenmez
uniform float moon_shade : hint_range(0.0, 1.0) = 0.0;

void fragment() {
	// Godot 4'te COLOR zaten doku × köşe rengi (modulate) olarak gelir.
	vec4 c = COLOR * tint;
	if (pixel_aa > 0.5) {
		AA_TEX(TEXTURE, UV, c);
		c = c * vcol * tint;
	}
	c.rgb = mix(c.rgb, flash_color.rgb, flash);
	COLOR = c;
}

void light() {
	float ndl = dot(NORMAL, LIGHT_DIRECTION);
	float b = ndl > band_hi ? 1.0 : (ndl > band_lo ? 0.62 : 0.28);
	vec3 lit = COLOR.rgb * b;
	// parlama: +spec_gain parlaklık, açık renge çalar
	float spec = step(spec_band, ndl);
	lit += spec * spec_gain * (lit + spec_tint.rgb * 0.5);
	// kenar ışığı: siluete yatık normal + ışık yönüne dönük
	vec2 nxy = NORMAL.xy;
	float nlen = max(length(nxy), 1e-4);
	float ldir = dot(nxy / nlen, normalize(LIGHT_DIRECTION.xy + vec2(1e-4, 0.0)));
	float rim = step(NORMAL.z, rim_edge) * step(rim_facing, ldir);
	lit += rim * rim_gain * mix(COLOR.rgb, vec3(1.0), 0.6);
	if (LIGHT_IS_DIRECTIONAL) {
		lit *= 1.0 - moon_shade;
	}
	LIGHT = vec4(lit * LIGHT_COLOR.rgb * LIGHT_ENERGY, LIGHT_COLOR.a);
}
