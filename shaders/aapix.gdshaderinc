// Keskin ama kenar yumuşatmalı piksel örnekleme ("AA nearest"). Doku pikselleri ekran pikseline tam sayı
// oranla oturmadığında (1,5x yoğunluklu Bengü/karolar 1080p'de 1,33 ekran pikseli, dönen silahlar) en yakın
// komşu örneklemesi bazı pikselleri 1, bazılarını 2 ekran pikseli çizer; kamera kaydıkça bu desen değişir ve
// doku "titrer". Burada her doku pikseli keskin kalır, yalnızca sınırları tek ekran pikseli içinde karışır.
// texelFetch ile elle çift doğrusal: düğümün doku süzgecinden bağımsız. Önceden çarpılmış alfa (koyu saçak yok).

// TEXTURE yerleşiği fonksiyona verilemiyor: koordinat/ağırlık burada, dört texelFetch gövdede (AA_TEX makrosu).
void aa_coords(vec2 uv, ivec2 isz, out ivec2 i0, out vec2 f) {
	vec2 px = uv * vec2(isz) - 0.5;
	vec2 fw = max(fwidth(px), vec2(1e-4));
	vec2 b = floor(px);
	f = clamp((px - b - 0.5) / fw + 0.5, 0.0, 1.0);
	i0 = ivec2(b);
}

vec4 aa_pm(vec4 c) {
	return vec4(c.rgb * c.a, c.a);
}

vec4 aa_combine(vec4 c00, vec4 c10, vec4 c01, vec4 c11, vec2 f) {
	vec4 r = mix(mix(aa_pm(c00), aa_pm(c10), f.x), mix(aa_pm(c01), aa_pm(c11), f.x), f.y);
	return vec4(r.rgb / max(r.a, 1e-4), r.a);
}

// Kullanım: vec4 c; AA_TEX(TEXTURE, UV, c);
#define AA_TEX(T, U, OUT) { ivec2 aa_sz = textureSize(T, 0); ivec2 aa_i; vec2 aa_f; aa_coords(U, aa_sz, aa_i, aa_f); ivec2 aa_m = aa_sz - ivec2(1); OUT = aa_combine(texelFetch(T, clamp(aa_i, ivec2(0), aa_m), 0), texelFetch(T, clamp(aa_i + ivec2(1, 0), ivec2(0), aa_m), 0), texelFetch(T, clamp(aa_i + ivec2(0, 1), ivec2(0), aa_m), 0), texelFetch(T, clamp(aa_i + ivec2(1, 1), ivec2(0), aa_m), 0), aa_f); }

// Döşenen (repeat) dokular için: dünya koordinatından okunan toprak dokusu
vec4 aa_fetch_wrap(sampler2D tex, ivec2 p, ivec2 sz) {
	vec4 c = texelFetch(tex, ((p % sz) + sz) % sz, 0);
	return vec4(c.rgb * c.a, c.a);
}

vec4 aa_sample_wrap(sampler2D tex, vec2 px_in) {
	// px_in: doku pikseli biriminde konum (piksel merkezi = tam sayı + 0,5)
	ivec2 isz = textureSize(tex, 0);
	vec2 px = px_in - 0.5;
	vec2 fw = max(fwidth(px), vec2(1e-4));
	vec2 b = floor(px);
	vec2 f = clamp((px - b - 0.5) / fw + 0.5, 0.0, 1.0);
	ivec2 i0 = ivec2(b);
	vec4 r = mix(mix(aa_fetch_wrap(tex, i0, isz), aa_fetch_wrap(tex, i0 + ivec2(1, 0), isz), f.x),
			mix(aa_fetch_wrap(tex, i0 + ivec2(0, 1), isz), aa_fetch_wrap(tex, i0 + ivec2(1, 1), isz), f.x), f.y);
	return vec4(r.rgb / max(r.a, 1e-4), r.a);
}
