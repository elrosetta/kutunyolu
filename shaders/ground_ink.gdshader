// Stil v2 "mürekkep" zemini (yalnızca --stil=v2, tools/artgen/otuken_ink_ground.py).
// Karo atlası iki dokudur: TEXTURE = boyalı sanat (ot bandı, mürekkep konturu, kayalar), NORMAL_TEXTURE yuvasında
// taşınan maske (R = toprak kaplaması, G = kenar gölgesi). Kaplama olan yerde dünya koordinatından okunan dikişsiz
// toprak dokusu görünür, sanat onun üstüne biner. Her şey doğrusal süzgeç + mipmap: kenarlar yumuşak, piksel yok.
// Işık: boyalı dokular ışığı zaten içerir; 2D ışıklar (ay, çıralar) yumuşak ve kısık eklenir, 3 bant yok.
shader_type canvas_item;

uniform sampler2D soil_tex : source_color, filter_linear_mipmap, repeat_enable;
uniform float soil_density = 2.0;
uniform sampler2D depth_tex : filter_linear;
// çayır: zeminin üst karolarında dünya uzayı ot dokusu; top_tex = yüzeyden dikey derinlik (0 yüzey, 1 = 4 karo)
uniform sampler2D meadow_tex : source_color, filter_linear_mipmap, repeat_enable;
uniform sampler2D top_tex : filter_linear;
uniform float meadow_depth = 0.55;
uniform float meadow_on = 1.0;
uniform vec2 map_size_px = vec2(5520.0, 1056.0);
uniform vec4 deep_color : source_color = vec4(0.06, 0.06, 0.08, 1.0);
uniform float deep_amount : hint_range(0.0, 1.0) = 0.8;
// ay (yönlü ışık) ve noktasal ışıkların katkı çarpanları
uniform float moon_gain : hint_range(0.0, 2.0) = 0.6;
uniform float point_gain : hint_range(0.0, 2.0) = 1.0;
// ışıyan damarlar (Şahmeran kristal, Tamu lav; yalnızca emit_gain > 0 olan biyomlar): dünya uzayı, toprakla aynı ızgara.
// emit_pulse = (genlik, hız): damarlar yavaşça nabız atar, faz dünya konumuna göre kayar.
uniform sampler2D soil_e : source_color, filter_linear_mipmap, repeat_enable, hint_default_black;
uniform float emit_gain = 0.0;
uniform vec2 emit_pulse = vec2(0.25, 1.2);

varying vec2 world_pos;
varying vec4 vcol;
// v38: dünya uzayı UV'leri dünya konumunun doğrusal işlevi: köşede hesaplanıp aradeğerlenir (sonuç aynı, piksel başına
// textureSize / bölme yok)
varying vec2 suv;
varying vec2 muv;
varying vec2 duv;

void vertex() {
	world_pos = (MODEL_MATRIX * vec4(VERTEX, 0.0, 1.0)).xy;
	vcol = COLOR;
	suv = world_pos * soil_density / vec2(textureSize(soil_tex, 0));
	muv = world_pos * soil_density / vec2(textureSize(meadow_tex, 0));
	duv = world_pos / map_size_px;
}

void fragment() {
	vec4 art = texture(TEXTURE, UV);
	vec4 mk = texture(NORMAL_TEXTURE, UV);
	float cov = mk.r;
	vec3 s = texture(soil_tex, suv).rgb;
	float d = texture(depth_tex, duv).r;
	if (meadow_on > 0.5) {
		float td = texture(top_tex, duv).r;
		vec3 mdw = texture(meadow_tex, muv).rgb;
		// ot yüzeyde ay ışığında, aşağı indikçe gölgeye girer
		mdw *= mix(1.0, 0.5, smoothstep(0.0, meadow_depth, td));
		s = mix(s, mdw, 1.0 - smoothstep(meadow_depth * 0.45, meadow_depth, td));
	}
	s *= 1.0 - mk.g * 0.8;
	s = mix(s, deep_color.rgb, smoothstep(0.0, 1.0, d) * deep_amount);
	float a = art.a + cov * (1.0 - art.a);
	vec3 pm = art.rgb * art.a + s * cov * (1.0 - art.a);
	if (emit_gain > 0.0) {
		vec4 e = texture(soil_e, suv);
		float ph = TIME * emit_pulse.y + world_pos.x * 0.004 + world_pos.y * 0.007;
		float k = emit_gain * (1.0 - emit_pulse.x + emit_pulse.x * sin(ph)) * (1.0 - 0.75 * d) * (1.0 - mk.g * 0.5);
		pm += e.rgb * e.a * k * cov * (1.0 - art.a);
	}
	COLOR = vec4(pm / max(a, 1e-4), a) * vcol;
	// düz normal (maske normal haritası DEĞİL); üst yüzeyler hafif yukarı bakar
	NORMAL_MAP = vec3(0.5, 0.62, 0.92);
}

void light() {
	float ndl = clamp(dot(NORMAL, LIGHT_DIRECTION), 0.0, 1.0);
	float g = LIGHT_IS_DIRECTIONAL ? moon_gain : point_gain;
	LIGHT = vec4(COLOR.rgb * LIGHT_COLOR.rgb * LIGHT_ENERGY * (0.45 + 0.55 * ndl) * g, LIGHT_COLOR.a);
}
