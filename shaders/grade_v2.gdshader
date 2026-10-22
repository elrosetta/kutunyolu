// Stil v2 renk derecelendirme + vinyet (yalnızca --stil=v2 ortamında, vignette.gdshader yerine).
// Sahnenin kendisini (ekran dokusu) okur: gölgeleri mora, orta tonları teal-yeşile çeker, hafif doygunluk düşüşü ve
// yumuşak S eğrisi; kenarlar mor-siyaha kararır (Shinobi: Art of Vengeance referansının sisli, buğulu havası).
// "hurt" parametresi vignette.gdshader ile aynı (Level.flash_red kenardan kırmızı nabız).
//
// v40 "ışık ve renk cilası": film derecelendirme sırası (ASC CDL benzeri lift / gamma / gain, üç tonlu ayrık tonlama:
// gölge / orta / açık, canlılık), ekran uzayı sis bandı (mist: alçak pus, oyuncunun ayak çizgisinin altına Level yazar,
// yavaş sürüklenen gürültüyle; koyuları kaldırır, açıkları bırakır), biçimlendirilebilir vinyet (vig_in / vig_out /
// vig_round), çok ince canlı film tanesi (açıklarda azalır), yalnızca vuruşta renk sapması (ca: Level.flash_red),
// ölüm derecesi (death: doygunluk gider, soğur, vinyet daralır). Hepsi tek geçiş; ek doku okuması yalnızca ca > 0 iken.
shader_type canvas_item;

uniform sampler2D screen_tex : hint_screen_texture, filter_linear;
uniform float strength : hint_range(0.0, 1.0) = 0.5;
uniform vec4 edge_color : source_color = vec4(0.07, 0.03, 0.08, 1.0);
uniform float hurt : hint_range(0.0, 1.0) = 0.0;
uniform vec4 hurt_color : source_color = vec4(0.55, 0.02, 0.04, 1.0);
uniform float amount : hint_range(0.0, 1.0) = 1.0;
uniform float saturation = 0.9;
uniform float contrast = 1.06;
uniform vec3 shadow_tint = vec3(0.92, 0.82, 1.0);
uniform vec3 mid_tint = vec3(0.95, 1.04, 1.0);
uniform vec3 lift = vec3(0.012, 0.02, 0.022);
// ısı dalgası (Tamu): ekran UV'si yatayda kıvrılır, alta doğru güçlenir; 0 = kapalı (Ötüken, Şahmeran)
uniform float heat = 0.0;
// v38: bantlaşma önleyici titreşim genliği (sRGB, 1 / 255 = bir 8 bit adım); 0 = kapalı
uniform float dither = 0.0039;
// ---- v40
uniform vec3 gamma = vec3(1.0);          // orta ton eğrisi (kanal başına; >1 aydınlatır)
uniform vec3 gain = vec3(1.0);           // açık uç çarpanı (kanal başına)
uniform vec3 high_tint = vec3(1.0);      // açık tonların rengi (ayrık tonlamanın üst ucu)
uniform float high_k : hint_range(0.0, 1.0) = 0.0;
uniform float vibrance : hint_range(-1.0, 1.0) = 0.0;   // az doygun renkleri çok doygunlardan çok canlandırır
uniform float vig_in = 0.32;             // vinyetin başladığı yarıçap
uniform float vig_out = 0.8;             // tam koyuluğa ulaştığı yarıçap
uniform float vig_round = 0.75;          // dikey sıkıştırma (1 = daire, <1 ekran oranına yakın oval)
uniform float grain : hint_range(0.0, 0.1) = 0.0;       // film tanesi genliği (sRGB)
uniform float mist : hint_range(0.0, 1.0) = 0.0;        // sis bandı gücü
uniform vec3 mist_color = vec3(0.4, 0.46, 0.44);
uniform float mist_y = 0.66;             // sisin ekranda yoğunlaştığı yükseklik (0 üst, 1 alt); Level her kare yazar
uniform float mist_soft = 0.3;           // bandın yumuşaklığı (ekran yüksekliği birimi)
uniform float mist_drift = 1.0;          // sürüklenme hızı
uniform float ca : hint_range(0.0, 4.0) = 0.0;          // renk sapması (ekran pikseli; yalnızca vuruş nabzında)
uniform float death : hint_range(0.0, 1.0) = 0.0;       // ölüm derecesi

float hash21(vec2 p) {
	p = fract(p * vec2(123.34, 456.21));
	p += dot(p, p + 45.32);
	return fract(p.x * p.y);
}

float vnoise(vec2 p) {
	// iki boyutlu değer gürültüsü (ALU; doku yok)
	vec2 i = floor(p);
	vec2 f = fract(p);
	f = f * f * (3.0 - 2.0 * f);
	float a = hash21(i);
	float b = hash21(i + vec2(1.0, 0.0));
	float c = hash21(i + vec2(0.0, 1.0));
	float d = hash21(i + vec2(1.0, 1.0));
	return mix(mix(a, b, f.x), mix(c, d, f.x), f.y);
}

void fragment() {
	vec2 suv = SCREEN_UV;
	if (heat > 0.0) {
		float k = heat * smoothstep(0.15, 1.0, suv.y);
		suv.x += sin(suv.y * 90.0 + TIME * 3.1) * k + sin(suv.y * 37.0 - TIME * 1.7 + suv.x * 9.0) * k * 0.6;
	}
	vec3 lin;
	if (ca > 0.001) {
		// vuruş nabzı: kırmızı ve mavi kanallar merkezden dışa doğru ayrışır (mercek sapması), kenarda daha çok
		vec2 dir = (suv - vec2(0.5)) * SCREEN_PIXEL_SIZE * ca * 2.2;
		lin.r = texture(screen_tex, suv + dir).r;
		lin.g = texture(screen_tex, suv).g;
		lin.b = texture(screen_tex, suv - dir).b;
	} else {
		lin = texture(screen_tex, suv).rgb;
	}
	vec3 c = pow(max(lin, vec3(0.0)), vec3(1.0 / 2.2));
	vec3 g = c;
	// --- lift / gamma / gain (ASC CDL sırası; lift yalnızca koyulara biner)
	g = g * gain + lift * (1.0 - g);
	g = pow(max(g, vec3(0.0)), vec3(1.0) / max(gamma, vec3(0.05)));
	// --- doygunluk ve canlılık
	float l = dot(g, vec3(0.299, 0.587, 0.114));
	float sat_px = max(max(g.r, g.g), g.b) - min(min(g.r, g.g), g.b);
	float s_k = saturation + vibrance * (1.0 - clamp(sat_px * 2.0, 0.0, 1.0));
	g = mix(vec3(l), g, s_k);
	// --- ayrık tonlama: koyular (shadow_tint), ortalar (mid_tint), açıklar (high_tint)
	float sh = 1.0 - smoothstep(0.0, 0.42, l);
	float md = smoothstep(0.15, 0.5, l) * (1.0 - smoothstep(0.6, 0.95, l));
	float hi = smoothstep(0.55, 0.95, l);
	g *= mix(vec3(1.0), shadow_tint, sh * 0.6);
	g *= mix(vec3(1.0), mid_tint, md);
	g *= mix(vec3(1.0), high_tint, hi * high_k);
	// --- karşıtlık (S eğrisi, orta gri çevresinde)
	g = (g - 0.5) * contrast + 0.5;
	// --- sis bandı: alçak pus; koyuları kaldırır, açıkları hemen hiç bozmaz (ışık kaynakları sisin içinden parlar)
	if (mist > 0.001) {
		float t = TIME * 0.05 * mist_drift;
		// tek oktav değer gürültüsü + gürültüyle bükülen ince sinüs dalgası (ikinci oktav yerine: yarı maliyet, aynı his)
		float n = vnoise(vec2(UV.x * 3.0 + t, UV.y * 2.2 - t * 0.4));
		n = n * 0.7 + 0.3 * (0.5 + 0.5 * sin(UV.x * 23.0 - t * 9.0 + n * 6.0));
		float band = smoothstep(mist_y - mist_soft, mist_y + mist_soft * 0.35, UV.y);
		float m = mist * band * (0.55 + 0.45 * n) * (1.0 - smoothstep(0.35, 0.95, l));
		g = mix(g, mist_color, clamp(m, 0.0, 0.6));
	}
	g = mix(c, g, amount);
	// --- ölüm: renk çekilir, soğur, kararır (Perde.olum sürer)
	if (death > 0.001) {
		float dl = dot(g, vec3(0.299, 0.587, 0.114));
		vec3 cold = vec3(dl) * vec3(0.62, 0.66, 0.78) + vec3(0.015, 0.0, 0.03);
		g = mix(g, cold, death * 0.85);
	}
	// --- vinyet (ekran oranına göre oval; ölümde daralır)
	vec2 d = (UV - vec2(0.5)) * vec2(1.0, vig_round);
	float r = length(d) * 1.25;
	float vi = vig_in - death * 0.14;
	float vo = vig_out - death * 0.12;
	float v = smoothstep(vi, vo, r) * min(1.0, strength + death * 0.35);
	g = mix(g, edge_color.rgb, v);
	float h = smoothstep(0.38, 0.8, r) * hurt;
	g = mix(g, hurt_color.rgb, clamp(h * 1.4, 0.0, 0.85));
	// --- film tanesi: çok ince, canlı (her kare değişir), açıklarda azalır
	vec2 fc = FRAGCOORD.xy;
	if (grain > 0.0001) {
		float gn = hash21(fc + vec2(fract(TIME * 7.31) * 311.0, fract(TIME * 3.17) * 173.0)) - 0.5;
		g += gn * grain * (1.0 - smoothstep(0.3, 0.9, l));
	}
	// v38 titreşim (dither): HDR 2D tampon ekrana 8 bit yazılırken koyu sis / pus / gök gradyanlarında bantlaşma
	// olmasın; iki kaydırılmış "interleaved gradient noise" toplamı = üçgen dağılım, ±1 / 255 (görünmez tane)
	float n1 = fract(52.9829189 * fract(dot(fc, vec2(0.06711056, 0.00583715))));
	float n2 = fract(52.9829189 * fract(dot(fc + vec2(47.0, 17.0), vec2(0.06711056, 0.00583715))));
	g += (n1 + n2 - 1.0) * dither;
	COLOR = vec4(pow(max(g, vec3(0.0)), vec3(2.2)), 1.0);
}
