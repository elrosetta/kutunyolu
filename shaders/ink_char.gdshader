// Stil v2 "mürekkep-cel" karakter gölgelendiricisi (tools/artgen/inkkit.py ile çizilen sprite'lar; json "filter": "linear").
// Cel gölgesi, kontur ve kenar ışığı dokunun içinde çizili: toon_light'ın normal haritasından 3 bantlı nicelemesi
// bu çizimle çatışır (düz yüzey tek banda düşer, gölge iki kez uygulanır). Burada ışık yalnızca renk ve şiddet taşır:
// her ışık dokuyu düz olarak aydınlatır (ay için light_k, noktasal ışıklarda dokunun kendi düşüşü), sahne gölgesi
// (moon_shade) ve vuruş parlaması/ton (flash, tint) toon_light ile aynı adlarla çalışır.
// Örnekleme: düğümün/CanvasTexture'ın süzgeci (doğrusal + mipmap); piksel-AA yolu yok.
shader_type canvas_item;

uniform float flash : hint_range(0.0, 1.0) = 0.0;
uniform vec4 flash_color : source_color = vec4(1.0, 0.97, 0.9, 1.0);
uniform vec4 tint : source_color = vec4(1.0, 1.0, 1.0, 1.0);
// ay gölgesi (GroundShadow, Level.moon_occluded): yönlü ışığın bu payı kesilir
uniform float moon_shade : hint_range(0.0, 1.0) = 0.0;
// yönlü ışık (ay) katkı çarpanı: toon_light'ın ortalama bandına (~0.8) denk
uniform float light_k : hint_range(0.0, 2.0) = 0.85;
// noktasal ışık katkı çarpanı (ocak, çıra, Kut)
uniform float point_k : hint_range(0.0, 2.0) = 0.9;

void fragment() {
	vec4 c = COLOR * tint;
	c.rgb = mix(c.rgb, flash_color.rgb, flash);
	COLOR = c;
}

void light() {
	vec3 lit = COLOR.rgb * LIGHT_COLOR.rgb * LIGHT_ENERGY;
	if (LIGHT_IS_DIRECTIONAL) {
		lit *= light_k * (1.0 - moon_shade);
	} else {
		lit *= point_k;
	}
	LIGHT = vec4(lit, LIGHT_COLOR.a);
}
