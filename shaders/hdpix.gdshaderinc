// HD doku paketleri: piksel sanatını Scale2x (2K) ya da Scale4x (4K) kurallarıyla, çizim anında büyütür.
// Önceden 2x/4x üretilmiş dokularla birebir aynı sonucu verir; ek dosya ve ek video belleği gerektirmez.
// Kural (Scale2x / EPX): bir doku pikseli 2x2 alt piksele bölünür; köşedeki iki komşu aynı renkse ve
// karşı komşulardan farklıysa alt piksel o komşunun rengini alır. Böylece merdiven köşegenler yumuşar,
// palet korunur (yeni renk üretilmez, bulanıklık olmaz). Scale4x = Scale2x'in Scale2x'i.
// hd_level: 0 kapalı, 1 = 2K paketi (Scale2x), 2 = 4K paketi (Scale4x). Ayarlar.gd genel parametreyi yazar.
//
// Kullanım (Godot yerleşik TEXTURE'ın fonksiyonlara aktarılmasına izin vermediği için örnekler makroyla alınır):
//   vec4 c = texture(TEXTURE, UV);
//   if (hd_level > 0) { HD_SAMPLE(c, TEXTURE, UV, TEXTURE_PIXEL_SIZE); }

global uniform int hd_level;

// 13 örnek: merkez çevresinde yarıçapı 2 olan elmas
// 0:(0,0) 1:(0,-1) 2:(1,0) 3:(-1,0) 4:(0,1) 5:(0,-2) 6:(2,0) 7:(-2,0) 8:(0,2) 9:(1,-1) 10:(-1,-1) 11:(1,1) 12:(-1,1)
#define HD_TX(tex, T, px, ox, oy) texture(tex, (T + vec2(float(ox), float(oy)) + 0.5) * px)
#define HD_SAMPLE(outc, tex, uv, px) { vec2 hdT = floor((uv) / (px)); vec2 hds = (uv) / (px) - hdT; vec4 hdn[13]; hdn[0] = HD_TX(tex, hdT, px, 0, 0); hdn[1] = HD_TX(tex, hdT, px, 0, -1); hdn[2] = HD_TX(tex, hdT, px, 1, 0); hdn[3] = HD_TX(tex, hdT, px, -1, 0); hdn[4] = HD_TX(tex, hdT, px, 0, 1); if (hd_level > 1) { hdn[5] = HD_TX(tex, hdT, px, 0, -2); hdn[6] = HD_TX(tex, hdT, px, 2, 0); hdn[7] = HD_TX(tex, hdT, px, -2, 0); hdn[8] = HD_TX(tex, hdT, px, 0, 2); hdn[9] = HD_TX(tex, hdT, px, 1, -1); hdn[10] = HD_TX(tex, hdT, px, -1, -1); hdn[11] = HD_TX(tex, hdT, px, 1, 1); hdn[12] = HD_TX(tex, hdT, px, -1, 1); } outc = hd_resolve(hdn, hds); }

bool hd_eq(vec4 a, vec4 b) {
	if (a.a < 0.02 && b.a < 0.02) {
		return true;
	}
	vec4 d = abs(a - b);
	return max(max(d.r, d.g), max(d.b, d.a)) < 0.015;
}

vec4 hd_at(vec4 n[13], ivec2 o) {
	if (o == ivec2(0, 0)) return n[0];
	if (o == ivec2(0, -1)) return n[1];
	if (o == ivec2(1, 0)) return n[2];
	if (o == ivec2(-1, 0)) return n[3];
	if (o == ivec2(0, 1)) return n[4];
	if (o == ivec2(0, -2)) return n[5];
	if (o == ivec2(2, 0)) return n[6];
	if (o == ivec2(-2, 0)) return n[7];
	if (o == ivec2(0, 2)) return n[8];
	if (o == ivec2(1, -1)) return n[9];
	if (o == ivec2(-1, -1)) return n[10];
	if (o == ivec2(1, 1)) return n[11];
	return n[12];
}

// P merkez; A yukarı, B sağ, C sol, D aşağı; q alt piksel (0/1, 0/1)
vec4 hd_s2x(vec4 P, vec4 A, vec4 B, vec4 C, vec4 D, ivec2 q) {
	if (q.x == 0 && q.y == 0) {
		return (hd_eq(C, A) && !hd_eq(C, D) && !hd_eq(A, B)) ? A : P;
	}
	if (q.x == 1 && q.y == 0) {
		return (hd_eq(A, B) && !hd_eq(A, C) && !hd_eq(B, D)) ? B : P;
	}
	if (q.x == 0 && q.y == 1) {
		return (hd_eq(D, C) && !hd_eq(D, B) && !hd_eq(C, A)) ? C : P;
	}
	return (hd_eq(B, D) && !hd_eq(B, A) && !hd_eq(D, C)) ? D : P;
}

// o göreli doku pikselinin q alt pikseli (Scale2x)
vec4 hd_sub2(vec4 n[13], ivec2 o, ivec2 q) {
	return hd_s2x(hd_at(n, o), hd_at(n, o + ivec2(0, -1)), hd_at(n, o + ivec2(1, 0)), hd_at(n, o + ivec2(-1, 0)), hd_at(n, o + ivec2(0, 1)), q);
}

// 2x ızgarasında g alt pikseli (g = 2*o + q; merkez doku pikseli o = 0)
vec4 hd_g2(vec4 n[13], ivec2 g) {
	ivec2 o = ivec2(floor(vec2(g) * 0.5));
	return hd_sub2(n, o, g - o * 2);
}

vec4 hd_resolve(vec4 n[13], vec2 s) {
	if (hd_level == 1) {
		return hd_sub2(n, ivec2(0, 0), ivec2(min(s * 2.0, vec2(1.0))));
	}
	// Scale4x: 2x ızgarasındaki alt piksel ve dört komşusu, sonra onlara Scale2x
	ivec2 q4 = ivec2(min(s * 4.0, vec2(3.0)));
	ivec2 g = q4 / 2;
	ivec2 qq = q4 - g * 2;
	return hd_s2x(hd_g2(n, g), hd_g2(n, g + ivec2(0, -1)), hd_g2(n, g + ivec2(1, 0)), hd_g2(n, g + ivec2(-1, 0)), hd_g2(n, g + ivec2(0, 1)), qq);
}
