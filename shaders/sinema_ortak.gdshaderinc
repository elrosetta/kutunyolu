// v43 sinematik motoru (Sinema.gd): katman gölgelendiricilerinin ortak parçası (sinema_katman / sinema_isik).
//  * blur: odak dışı katman için disk bulanıklığı (dokunun piksel biriminde; 13 dokunuş Poisson diski)
//  * sway: rüzgâr salınımı (dokunun alt kenarı sabit, tepeye doğru artar; ağaç tepesi, çaput, ot)
//  * reveal: mürekkep belirmesi; reveal_mode 0 = kâğıda emilen leke (koyu önce), 1 = soldan sağa yazılış (fırça yazısı),
//    2 = çember boyunca çiziliş (enso; radial_a0 başlangıç açısı)
uniform float blur = 0.0;
uniform float sway = 0.0;
uniform float sway_freq = 0.7;
uniform float seed = 0.0;
uniform float reveal = 1.0;
uniform int reveal_mode = 0;
uniform float radial_a0 = -2.4;
uniform vec4 tint : source_color = vec4(1.0);

float s43_hash(vec2 p) {
	p = fract(p * vec2(123.34, 456.21) + seed);
	p += dot(p, p + 45.32);
	return fract(p.x * p.y);
}

float s43_noise(vec2 p) {
	vec2 i = floor(p);
	vec2 f = fract(p);
	f = f * f * (3.0 - 2.0 * f);
	return mix(mix(s43_hash(i), s43_hash(i + vec2(1.0, 0.0)), f.x), mix(s43_hash(i + vec2(0.0, 1.0)), s43_hash(i + vec2(1.0, 1.0)), f.x), f.y);
}

vec2 s43_sway_uv(vec2 uv, vec2 px) {
	if (sway <= 0.001) {
		return uv;
	}
	float k = pow(clamp(1.0 - uv.y, 0.0, 1.0), 1.6);
	float w = sin(TIME * sway_freq + seed * 3.0 + uv.y * 2.5) + 0.35 * sin(TIME * sway_freq * 2.7 + uv.x * 11.0 + uv.y * 7.0);
	return uv - vec2(w * sway * k * px.x, 0.0);
}

// disk bulanıklığı dokunuşları (TEXTURE yerleşiği işleve geçirilemediği için örnekleme gölgelendiricinin kendisinde)
const vec3 S43_DISK[12] = vec3[](vec3(-0.326, -0.406, 0.08), vec3(-0.840, -0.074, 0.08), vec3(-0.696, 0.457, 0.08), vec3(-0.203, 0.621, 0.08),
	vec3(0.962, -0.195, 0.08), vec3(0.473, -0.480, 0.08), vec3(0.519, 0.767, 0.08), vec3(0.185, -0.893, 0.08),
	vec3(0.507, 0.064, 0.06), vec3(0.896, 0.412, 0.06), vec3(-0.322, -0.933, 0.06), vec3(-0.792, -0.598, 0.06));

// mürekkep belirme maskesi: x = görünürlük (0..1), y = ıslak kenar
vec2 s43_reveal(vec2 uv, float lum) {
	if (reveal >= 0.999) {
		return vec2(1.0, 0.0);
	}
	float n = s43_noise(uv * vec2(7.0, 4.0)) * 0.62 + s43_noise(uv * vec2(26.0, 15.0) + 11.0) * 0.28 + s43_noise(uv * vec2(77.0, 44.0) + 3.0) * 0.1;
	float v;
	if (reveal_mode == 1) {
		v = reveal * 1.3 - uv.x - n * 0.18 + 0.02;
	} else if (reveal_mode == 2) {
		vec2 d = uv - vec2(0.5);
		float a = atan(d.y, d.x) - radial_a0;
		a = mod(a + 12.566, 6.2832) / 6.2832;
		v = reveal * 1.15 - a - n * 0.06 + 0.02;
	} else {
		float dark = clamp(1.0 - lum * 1.15, 0.0, 1.0);
		v = reveal * 1.45 - 0.37 - n * 0.55 + dark * 0.32;
	}
	float m = smoothstep(-0.05, 0.05, v);
	float rim = smoothstep(-0.05, 0.0, v) * (1.0 - smoothstep(0.01, 0.1, v));
	return vec2(m, rim);
}
