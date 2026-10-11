# Öğrenci Açıklamalarının Soru Bağlamına Duyarlı Anlamsal Değerlendirilmesi: Türkçe Veri Uyarlaması ve Diller Arası Karşılaştırmalı Analiz

**TEKNOFEST 2242 — Eğitim Alanı | Araştırma Projesi Raporu (gelecek uygun çağrı için bilimsel taslak)**

- **Önerilen tematik alan:** E-Öğrenme; ayrıca Yapay Zekâ / Makine Öğrenmesi uygulamaları.
- **Proje yürütücüsü / ekip / kurum / danışman:** Başvuru sahibi tarafından doğrulanıp doldurulacak. Uydurma kimlik veya kurum yazılmadı.
- **Araştırma kayıt tarihi:** 11 Ekim 2026.
- **Araştırma statüsü:** P0/P1/T1–T4 çevrimdışı yazılım ve keşifsel veri deneyleri tamamlandı. Türkçe insan doğrulaması yapılmadı; doğal Türkçe öğrenci verisi üzerinde dış geçerlilik değerlendirmesi yapılmadı.
- **Yarışma statüsü:** **2026'nın 6 Nisan başvuru ve 24 Nisan rapor teslim tarihleri geçmiştir. Bu metin 2026 dönemine gönderilmiş resmî bir başvuru değildir.** Yeni çağrının koşulları ilan edildiğinde yeniden uyarlanmalıdır.
- **Biçim notu:** 2026 TÜBİTAK 2242 rehberinin *Özet; 1. Giriş; 2. Yöntem ve Teknikler; 3. Bulgular; 4. Sonuç ve Tartışma; 5. Öneriler; 6. Kaynaklar; 7. Ekler* düzeni izlenmiştir. Markdown sayfa düzenini ve **resmî DOCX şablonunun** tipografisini tek başına sağlamaz; teslim öncesi güncel resmî şablona yerleştirilerek 2–20 sayfalık PDF teslim şartı ayrıca doğrulanmalıdır.

## İÇİNDEKİLER

1. GİRİŞ — amaç, özgünlük, araştırma soruları
2. YÖNTEM VE TEKNİKLER — veri, modeller, bölme, çeviri ve kalite denetimi, istatistik, iş planı
3. BULGULAR — İngilizce ablasyon, Türkçe QA, T4 karşılaştırması, sınıf bazlı F1
4. SONUÇ VE TARTIŞMA — araştırma cevapları, eğitimsel sınır, özgün katkı
5. ÖNERİLER — bağımsız dış doğrulama kapıları
6. KAYNAKLAR
7. EKLER VE YENİDEN ÜRETİLEBİLİRLİK

**Tablolar listesi:** Tablo 1 — SciEntsBank bölümleri; Tablo 2 — B0–B3 modelleri; Tablo 2A — gerçek iş-zaman çizelgesi; Tablo 3 — İngilizce Test-UQ; Tablo 4 — Türkçe QA; Tablo 5 — üç varyant Macro-F1; Tablo 6 — eşlenik sürüm farkları; Tablo 7 — B2 sınıf F1; Tablo 8 — B1 sınıf F1; Tablo 9 — bilimsel/teknik kabul kapıları.

**Şekiller listesi:** Şekil 1 — metinsel araştırma işlem zinciri.

**Kısaltmalar:** B0–B3 = sözlüksel başlangıç/ablasyon koşulları; CI/GA = güven aralığı; EN = İngilizce; TR = Türkçe; TF-IDF = terim sıklığı–ters belge sıklığı; LR = lojistik regresyon; QA = otomatik kalite denetimi; SHA-256 = dosya bütünlüğü özeti; P0/P1/T1–T4 = araştırma iş paketleri; Test-UQ = testte eğitimin görmediği soru kümeleri.

*Bu Markdown dosyasında sayfa numaraları bulunmaz. Kapak, içindekiler ve listelerin sayfa numaraları resmî DOCX şablonundan PDF'ye son dönüşüm sırasında belirlenmelidir.*

## ÖZET

Fen bilimleri eğitiminde kısa öğrenci açıklamalarının otomatik değerlendirilmesi, bir yanıtın yalnızca sözcüklerinden değil, yanıtlandığı sorunun bağlamından da etkilenebilir. Bu araştırmada soru metni eklemenin açıklama sınıflandırmasına katkısı ve İngilizce kaynak verinin Türkçeye çevrilmesi sırasında oluşan değişikliklerin sözlüksel modellere yansıması incelenmiştir. SciEntsBank veri kümesinin dört bölümündeki 10.804 kayıt kullanılmış, özgün beş sınıf tanımlı dört sınıfa dönüştürülmüştür. Çevrimdışı çalışan çoğunluk sınıfı ve TF-IDF ile lojistik regresyon temelli dört temel model karşılaştırılmıştır. Birincil değerlendirmede, eğitim bölümünde görülmeyen sorulardan oluşan 733 yanıtlık Test-UQ kullanılmıştır. İngilizcede yalnız öğrenci açıklaması modeli 0,295023, açıklama ve soru modeli 0,240599 Macro-F1 üretmiştir. İngilizceden Türkçeye yerel olarak çevrilen bütün kayıtlar kaynak kimlikleriyle korunmuş, otomatik kalite kuralları ve kanıta bağlı düzeltme önerileri uygulanmıştır. Türkçe ilk sürümde soru içeren modelin Macro-F1 değeri 0,274505, ayrı bir düzeltilmiş aday sürümde 0,285392 bulunmuştur. İkinci Türkçe sürümde 34 seçili tam-metin düzeltmesi 1.604 kaydı etkilemiş, 10.804 satırın tamamı korunmuştur. Sonuçlar dört sınıfın hata dağılımı ve soru kümelerine göre eşlenik yeniden örnekleme ile incelenmiştir. Veri bütünlüğü ve metrik aritmetiği yerel testlerle doğrulanmıştır. Bununla birlikte Türkçe etiketler İngilizce kaynaktan aktarılmıştır; bağımsız insan doğrulaması ve doğal Türkçe öğrenci yanıtları bulunmadığından sonuçlar yalnız keşifsel araştırma bulgularıdır.

**Anahtar kelimeler:** Öğrenci yanıtı değerlendirme; soru bağlamı; Türkçe veri uyarlaması; doğal dil işleme; çevrimdışı makine öğrenmesi.

## 1. GİRİŞ

### 1.1. Projenin amacı ve önemi

Kısa yanıtlı fen sorularının ölçme ve değerlendirmesinde, bir öğrenci açıklamasının tam anlamı sorulan soruyla ilişkili olabilir. Yalnız öğrenci metnini kullanan bir sınıflandırıcı ile açıklamaya soru metnini de ekleyen bir sınıflandırıcının hangi koşullarda ayrıştığı, veri sızıntısı ve sınıf dengesizliği denetlenerek araştırılmalıdır. SciEntsBank/SemEval-2013 Task 7, öğrenci yanıtlarının açıklama temelli değerlendirilmesi için yerleşik bir araştırma bağlamı sunar (Dzikovska vd., 2013).

Bu projede temel soru şudur: **Eğitimde görülmemiş soru kümelerinde, öğrenci açıklamasına soru metninin eklenmesi dört sınıflı Macro-F1'i nasıl değiştirir?** İkinci soru, aynı sabit İngilizce kaynak ve aktarılan etiketler kullanıldığında, yerel Türkçe makine çevirisinin ve kanıtla izlenen çeviri revizyonlarının gözlenen sözlüksel model ölçümlerini nasıl değiştirdiğidir. Bu iki soru **öğrenmenin veya pedagojik müdahalenin nedensel etkisi** sorusu değildir.

### 1.2. Özgünlük unsuru ve literatürdeki yeri

Araştırmanın **yeni bir sınıflandırıcı mimarisi icat ettiği iddia edilmemektedir**. Katkısı, aşağıdaki mühendislik ve araştırma kararlarının birlikte açık biçimde izlenmesidir: (i) yalnız açıklama / açıklama+soru / yalnız soru ablasyonu; (ii) **özgün İngilizce soru kümelerine göre** tutulmuş ayrık Test-UQ ve eğitim-içi doğrulama; (iii) orijinal beş etiketin korunup analize özel dört sınıfa dönüşümün belgelenmesi; (iv) tamamen yerel EN→TR çeviri, bilimsel kavram odaklı otomatik kalite taraması ve değişmez SHA-256 kanıtları; (v) hatalı görünen metnin genel sözcük değişimiyle değil **kaynak–hedef tam eşleşmesine dayalı ayrı sürümde** düzeltilmesi; (vi) diller arasında eşlenik soru-kümesi değerlendirmesi; (vii) olumsuz ve belirsiz sonuçların da raporlanması.

Öğrenci değerlendirmesi, makine çevirisi ve anlamsal temsiller literatürde vardır; araştırma mevcut yöntemlerin kontrollü, yinelenebilir karşılaştırmasını önerir. Dondurulmuş anlamsal gömme tabanlı S1/S2 seçenekleri kod/protokol düzeyindedir, **gerçek karşılaştırmalı S1/S2 skoru bu raporda bulunmamaktadır** (Reimers ve Gurevych, 2019).

### 1.3. İlgili teknoloji ve eğitim alanları

Başlıca alanlar eğitim teknolojileri, e-öğrenme, doğal dil işleme, makine öğrenmesi, deneysel yazılım mühendisliği ve veri bütünlüğüdür. Ön çalışma yalnız araştırma prototipi ve metrik üretmiştir; sınıfta uygulama, öğretmen kararını ikame etme, öğrenciye otomatik not verme veya öğrenme kazanımını artırma doğrulaması yapılmamıştır.

### 1.4. Araştırma soruları ve kapsam

- **AS1 / birincil:** İngilizce Test-UQ'da \(\Delta_{\mathrm{context}} = F1_{\mathrm{macro}}(B2)-F1_{\mathrm{macro}}(B1)\) nedir?
- **AS2 / keşifsel:** Türkçe v0.2 ve v0.2.1 adayları için aynı farkın yönü ve büyüklüğü nedir?
- **AS3 / keşifsel:** \(\Delta_{\mathrm{TR\,v0.2.1}}-\Delta_{\mathrm{TR\,v0.2}}\) değeri ve özgün İngilizce soru kümeleriyle eşlenik bootstrap aralığı nedir?
- **AS4 / yazılım denetimi:** Sürümler arasında kaynak metin, etiket, bölüm ayrımı ve uygulanan tam eşleşmeli düzeltmeler değişmez kanıtla doğrulanabiliyor mu?

## 2. YÖNTEM VE TEKNİKLER

### 2.1. Veri kümesi ve kaynak bütünlüğü

Kullanılan veri **SciEntsBank**'tir; yerel dosyalar sabit kaynak revizyonu ve SHA-256 manifestleriyle indirilmiş ve denetlenmiştir. Her kayıtta soru, referans yanıt, öğrenci yanıtı, kimlik ve özgün etiket alanları bulunmaktadır.

**Tablo 1. Gerçek kaynak veri bölümleri ve P0 denetimi**

| Bölüm | Satır | Benzersiz normalize İngilizce soru | Rol |
|---|---:|---:|---|
| Train | 4.969 | 135 | Eğitim ve eğitim-içi soru gruplu doğrulama |
| Test-UA | 540 | 135 | İkincil değerlendirme |
| Test-UQ | 733 | 15 | Birincil: görülmemiş sorular |
| Test-UD | 4.562 | 45 | İkincil: farklı alan/sorular |
| **Toplam** | **10.804** | **195 farklı soru (bölümler arası birleşim)** | |

P0 denetimi **PASS_WITH_WARNINGS** olarak sonuçlanmıştır: özgün beş etiket üzerinde train'de 6 çelişkili normalize yanıt üçlüsü (15 satır), Test-UD'de 1 üçlü (6 satır), Test-UA ile train arasında 24 ortak normalize soru+referans+yanıt üçlüsü vardır. Test-UQ ve train arasında normalize soru örtüşmesi **0** bulunmuştur. Test-UQ'nun kendi içinde 30 fazla yinelenen üçlü kaydı vardır. Çelişkili kaynak etiketlere müdahale edilmemiştir. Bu bulgular özgün kaynağa ilişkin koşullu kabul kayıtlarıdır; kalite sorununun giderildiği anlamına gelmez.

**Etiket dönüşümü:** Kaynaktaki beş sınıf silinmemiştir. \`correct\`→Correct; \`partially_correct_incomplete\`→Incomplete; \`contradictory\`→Contradictory; \`irrelevant\` ve \`non_domain\`→Other şeklinde yalnız dört sınıflı değerlendirme hedefi oluşturulmuştur. Türkçe kayıtlar aynı **İngilizce kaynak etiketini** devralır (\`UNVERIFIED_TRANSFER\`); Türkçe gold değildir.

### 2.2. Modeller ve veri girdi ablasyonu

**Tablo 2. Sabit sözlüksel model koşulları**

| Koşul | Özellik girdisi | Öğrenici |
|---|---|---|
| B0 | Metin kullanılmaz | Çoğunluk sınıfı |
| B1 | Öğrenci açıklaması | Kelime 1–2-gram ve \`char_wb\` 3–5-gram TF-IDF + Logistic Regression |
| B2 | Öğrenci açıklaması + soru | Aynı özellik ailesi + Logistic Regression |
| B3 | Yalnız soru | Aynı özellik ailesi + Logistic Regression |

Dört koşulda **referans cevap model girdisi değildir**. Soru içeren modelleri öğrenci açıklamasıyla birlikte sınamak için B3 özellikle bir *question-only shortcut control* işlevi görür. Seçilen öğrenici ve özellikler scikit-learn ile yerelde uygulanmıştır (Pedregosa vd., 2011).

### 2.3. Eğitim–test ayrımı ve hiperparametre protokolü

Eğitim bölümü içinde normalize **özgün İngilizce soru** ile \`GroupShuffleSplit(test_size=0.25, seed=20261009)\` kullanılmıştır. Eğitim/doğrulama arasında aynı soru kümesi yoktur. Lojistik regresyon düzenlileştirme parametresi \`C\` yalnız **{0,1; 1; 10}** adaylarından eğitim-içi doğrulama Macro-F1 ile seçilmiş, sonra tüm train bölümünde yeniden eğitilmiştir.

T4'te üç varyant ayrı değerlendirilmiştir: İngilizce kaynak (\`en\`), yerel ham Türkçe aday (\`tr_v0_2\`) ve kanıta bağlı düzeltilmiş keşifsel Türkçe aday (\`tr_v0_2_1\`). Bütün varyantlar aynı satır kimliklerini ve **İngilizce soru kümesi anahtarlarını** paylaşmaktadır. Türkçe v0.2.1'in C değerleri **v0.2 eğitim doğrulamasındaki seçimden dondurulmuştur**; Test-UQ üzerinde hiperparametre ayarlanmamıştır. Test-UQ önceden ana değerlendirme bölümü olarak tanımlanmıştır; Test-UA/UD sonuçları yerelde ikincil analize alınmıştır, ancak bu metinde sayısal sonuçları sunulmadığı için uydurulmamıştır.

### 2.4. Türkçe uyarlama, otomatik kalite denetimi ve sürümleme

Dört kaynak bölümündeki **10.804/10.804** satır, yerel Argos EN→TR modeli kullanılarak çevrimdışı aday metinler olarak üretilmiştir; 10.804 satırın İngilizce kaynağı, kimliği ve özgün etiketi korunmuştur. Argos kurulum paketinin SHA-256 değeri yerel manifestte kaydedilmiştir. Model API, bulut üzerinden çıkarım ve internet bağlantılı servis kullanılmamıştır.

İlk çevirilerde bilimsel kavram hatası şüphelerini incelemek için 240 satırlık **bölüm/sınıf bakımından dengeli, ancak nüfus hata prevalansı için olasılıksal olmayan** örneklem oluşturulmuştur. Sonra tüm korpus üzerinde deterministik kurallar uygulanmıştır. Örnek kural konuları: *bulb*→araç adı, *milliliters*→litre, *saturated*→doymamış, *calcite*→analiz, olumsuzluk ve sayı uyumsuzluğu. **Her işaret, doğrulanmış hata değil, yanlış alarm da verebilen inceleme adayıdır.**

Tam kaynak/hedef/alan eşleşmelerinden 1.460 farklı kök neden **adayı** türetilmiş, 39 tekrar eden yüksek öncelikli teknik/birim kümesinden çakışan metinler ayrıştırılarak **37 düzeltme şablonu** hazırlanmıştır. Ayrı \`AI_DRAFT\` incelemesi sonunda **34** tam metin önerisi \`APPLY_EXPLORATORY\`, **3** belirsiz örnek \`PENDING\` kalmıştır. Yalnız açıkça seçilmiş metinler yeni \`data/tr_v0_2_1/\` klasörüne uygulanmış; \`data/tr_v0_2/\` değiştirilmemiştir. Her değişiklikte satır sayısı, tam kaynak+önceki çeviri eşleşmesi ve SHA-256 kanıtı korunmuştur.

**Üç kritik durum ayrı tutulmuştur:** (i) kaynak İngilizce etiketin aktarımı ≠ Türkçe gold; (ii) heuristik QA uyarısının azalması ≠ gerçek anlamsal hata azalması; (iii) AI_DRAFT önerisinin makine tarafından uygulanabilir olması ≠ bağımsız uzman doğrulaması.

### 2.5. Metrikler, belirsizlik ve yazılım kabulü

Birincil ölçüm **dört sınıfın sabit sırada Macro-F1 ortalaması** olarak tanımlanmıştır. Ayrıca sınıf bazlı precision/recall/F1, confusion matrix, weighted F1 ve accuracy hesaplanmıştır. Test-UQ'da öğrenci yanıtlarının aynı bilim sorusunda gruplanması nedeniyle belirsizlik aralıkları satır düzeyinde değil, **15 normalize özgün İngilizce soru kümesinin eşlenik bootstrap yeniden örneklemesi** (1.000 tekrar; seed=20261009; percentile %95) ile elde edilmiştir. Küme sayısının küçük olması güven aralığının bilimsel gücünü sınırlar.

Yerel Windows çalıştırmasında **76/76 yazılım regresyon testi PASS**, İngilizce önceki P1 sonucu **1e−8 toleransta birebir yeniden üretim PASS**, **36 dört sınıflı karışıklık matrisinin** Macro/Weighted F1 ve sınıf F1 aritmetiği **PASS** bildirilmiştir. Bu bir metrik yazılım tutarlılığı denetimidir; Türkçe anlamsal doğruluk değerlendirmesi değildir. Doğrudan gerçek performans ölçümleri araştırmacının yerel raporlarıdır; GitHub CI, ham SciEntsBank dosyalarını kendi başına yeniden çalıştırmaz.

### 2.6. Gerçekleşen iş akışı ve veri güvenliği

**Şekil 1 (metinsel işlem zinciri).**

\`Kaynak SciEntsBank + SHA → P0 etiketsel/tekrar denetimi → B0–B3 EN P1 → yerel EN→TR v0.2 → tam QA + kavram kök nedeni → sürümlü AI_DRAFT v0.2.1 → veri etki analizi → kilitli T4 B0–B3 → salt-okunur metrik kabulü\`

Geliştirme ortamı Windows/Python, scikit-learn ve çevrimdışı çeviri bileşenleridir. Kaynak ve düzeltilmiş öğrenci metinleri, satır bazlı öneriler, çeviri CSV'leri, ikili model dosyaları ve satır düzeyi tahminler **yerel bilgisayarda tutulmuştur**; kamuya açık depoda kod, sentetik test, toplu sonuç ve bilimsel sınırlama belgeleri bulunmaktadır. Ölçülmemiş CPU gecikmesi veya model maliyeti rapora eklenmemiştir.

### 2.7. Tamamlanan iş-zaman çizelgesi ve açık araştırma işleri

2026 yarışma rapor teslim tarihi Nisan ayında sona ermiş olduğundan aşağıdaki çizelge **gelecek bir yarışma başvurusunun gerçekleştirilmiş takvimi gibi değil, projenin gerçek araştırma kronolojisi** olarak verilmektedir.

**Tablo 2A. Gerçek ilerleme kronolojisi ve ileri çalışma durumu**

| İş paketi | 9 Ekim 2026 | 10 Ekim 2026 | 11 Ekim 2026 | Mevcut durum |
|---|:---:|:---:|:---:|---|
| C0/C1: Kod, sentetik regresyon, CI | ● | ● | ● | Güncel 76 test PASS |
| P0: Veri dosyaları, tekrar/etiket çelişkileri |  | ● |  | PASS_WITH_WARNINGS |
| P1: İngilizce B0–B3 Test-UQ |  | ● | ✓ yeniden kabul | PASS |
| T1/T2: Yerel EN→TR tam aday çeviri |  | ● |  | Aday üretimi PASS |
| T3-AUTO: Tam QA/kök neden/AI_DRAFT |  |  | ● | Yazılım PASS; insan gold yok |
| T4: Üç varyant ve sınıf metrik QA |  |  | ● | Teknik PASS, keşifsel |
| V2–V4: Yeni bağımsız soru/etiket/dış test |  |  |  | NOT_STARTED / BLOCKED |
| S1/S2: Dondurulmuş anlamsal encoder gerçek sonuçları |  |  |  | RAPORLANMADI |

*● = tarihte çalıştırılan iş; ✓ = yeniden üretilebilirlik doğrulaması. Bu takvimde boş hücre başarısızlık anlamına gelmez; gerçek tamamlanma kanıtı olmayan iş paketleri tamamlanmış gibi gösterilmez.*

## 3. BULGULAR

### 3.1. İngilizce Test-UQ bağlam ablasyonu

**Tablo 3. Özgün İngilizce Test-UQ, dört sınıflı Macro-F1 (733 kayıt)**

| Model | Macro-F1 |
|---|---:|
| B0 — çoğunluk sınıfı | 0,145551 |
| **B1 — yalnız açıklama** | **0,295023** |
| B2 — açıklama+soru | 0,240599 |
| B3 — yalnız soru | 0,170172 |

Önceden tanımlanan **B2−B1 = −0,0544239482**; 15 İngilizce soru kümesiyle tanımlayıcı %95 bootstrap aralığı **[−0,102545584; −0,006910099]**. Dolayısıyla belirli sözlüksel TF-IDF temsilinde bağlam eklemek bu Test-UQ skorunu düşürmüştür; sonuç farklı anlamsal modellerin aynı davranacağı anlamına gelmez.

### 3.2. Tam Türkçe kalite denetimi ve revizyonun kapsamı

**Tablo 4. Türkçe çevrimdışı aday QA kural çıktıları**

| Ölçüm | TR v0.2 | TR v0.2.1 |
|---|---:|---:|
| Satır sayısı | 10.804 | 10.804 |
| HIGH uyarılı kayıt | 1.930 | 536 |
| MEDIUM uyarılı kayıt | 2.278 | 2.888 |
| İşaretlenmeyen kayıt | 6.596 | 7.380 |
| Alan düzeyi kural tetiklenmesi | 7.412 | 4.926 |

Yeni sürüme **34 ayrı tam kaynak–hedef eşleşme önerisi** uygulanmıştır; **1.604 farklı kayıt / 1.748 Türkçe alan örneği** değişmiştir. Alanların **1.366'sı soru**, **376'sı referans yanıt**, yalnız **6'sı öğrenci yanıtıdır**. Test-UQ'da yalnız **40 sorunun çevirisi** değişmiş; bu bölümde referans ve öğrenci metni alanları değiştirilmemiştir. Kural tetiklenmeleri **2.486 (%33,54)** azalmıştır; bu, **çeviri hata oranı veya anlamsal sadakat doğruluk oranı değildir**.

### 3.3. Üç varyant için kilitli T4 Test-UQ karşılaştırması

**Tablo 5. Test-UQ Macro-F1 — aynı özgün İngilizce etiketler / 15 soru kümesi**

| Girdi/Model | İngilizce | Türkçe v0.2 | Türkçe v0.2.1 |
|---|---:|---:|---:|
| B0 | 0,145551 | 0,145551 | 0,145551 |
| B1 — öğrenci | **0,295023** | 0,265198 | 0,263115 |
| B2 — öğrenci+soru | 0,240599 | 0,274505 | **0,285392** |
| B3 — soru | 0,170172 | 0,149603 | 0,160710 |
| **B2−B1** | **−0,054424** | **+0,009307** | **+0,022277** |

**Tablo 6. Eşlenik Test-UQ TR v0.2.1−TR v0.2 Macro-F1 farkları**

| Model | Nokta farkı | %95 tanımlayıcı soru-kümesi bootstrap aralığı |
|---|---:|---|
| B0 | 0,000000 | [0,000000; 0,000000] |
| B1 | −0,002083 | [−0,008982; +0,005187] |
| B2 | +0,010887 | [−0,000945; +0,021446] |
| B3 | +0,011107 | [0,000000; +0,039529] |

**Bağlam farklarının farkı**, \`(B2−B1)_(v0.2.1) − (B2−B1)_(v0.2)\`, **+0,0129701347**; eşlenik %95 percentile aralığı **[+0,0000448261; +0,0266094688]**. Tekil B2 farkının aralığı **sıfırı içermektedir**; B3 aralığının alt sınırı sıfırdır. Bağlam farklarının farkında alt sınır sıfıra çok yakındır; 15 soru kümesi ve daha önce incelenmiş Test-UQ üzerinden kuvvetli istatistiksel doğrulama ilan edilemez.

### 3.4. Sınıf bazlı değerlendirme ve başarısızlık profili

**Tablo 7. Test-UQ B2 sınıf F1; 4 sınıfın destekleri sırasıyla 301 / 175 / 64 / 193**

| Sınıf | EN B2 | TR v0.2 B2 | TR v0.2.1 B2 |
|---|---:|---:|---:|
| Correct (301) | 0,487395 | 0,548303 | 0,553806 |
| Incomplete (175) | 0,123223 | 0,152466 | 0,180258 |
| Contradictory (64) | 0,041667 | 0,082645 | **0,085470** |
| Other (193) | 0,310112 | 0,314607 | 0,322034 |
| **Macro-F1** | **0,240599** | **0,274505** | **0,285392** |

Türkçe B2 v0.2.1−v0.2 F1 sınıf farkları: **Incomplete +0,027791**, Correct +0,005503, Contradictory +0,002825, Other +0,007427. En büyük gözlenen sınıf düzeyi artış *Incomplete* üzerindedir. Ancak *Contradictory* sınıfındaki **0,085470** F1, çelişkili bilimsel açıklamaların bu sözlüksel yöntemle yeterli güvenilirlikte ayrıştırılamadığını gösteren önemli bir zayıflıktır. Bu metrik “öğrenci yanılgısı doğru teşhis edildi” iddiasını desteklemez.

**Tablo 8. Test-UQ B1 sınıf F1**

| Sınıf | İngilizce | TR v0.2 | TR v0.2.1 |
|---|---:|---:|---:|
| Correct | 0,480000 | 0,435352 | 0,437908 |
| Incomplete | 0,237705 | 0,277966 | 0,271186 |
| Contradictory | 0,127660 | 0,036364 | 0,036697 |
| Other | 0,334728 | 0,311111 | 0,306667 |
| **Macro-F1** | **0,295023** | **0,265198** | **0,263115** |

B2'nin bazı sınıflarda artması, aynı veri üzerinde B1'in artacağı anlamına gelmez. Özellikle Türkçe B1 Contradictory F1 **0,036697** ve B2 Contradictory F1 **0,085470** olduğundan iki model de bu sınıfta zayıftır. Hangi öğrenci yanlışının korunduğu, satır düzeyinde *bağımsız anlam doğrulaması olmadan* söylenemez.

### 3.5. Mühendislik kabulü ile bilimsel geçerliliğin ayrımı

**Tablo 9. Durum kararları**

| Kapı | Karar | Dayanak |
|---|---|---|
| P0 kaynak bütünlüğü | **PASS_WITH_WARNINGS** | 7 çelişkili üçlü / 21 satır ve tekrar kayıtları belgelendi |
| P1 İngilizce B0–B3 | **Teknik PASS** | Önceden tanımlı Test-UQ sonuçları ve soru-kümesi GA |
| T2 yerel tam çeviri | **Yazılım PASS** | 10.804/10.804 aday, kimlik/etiket/SHA |
| T3-AUTO | **Yazılım PASS; anlam doğruluğu ölçülmedi** | Kaynak kanıtlı 34 öneri, ayrı v0.2.1 |
| T4 sözlüksel proxy | **Teknik PASS, keşifsel** | 76/76 test; P1 1e−8; 36 confusion matrix PASS |
| T3-HUMAN / doğal Türkçe gold | **NOT_PERFORMED** | Bağımsız Türkçe doğruluk etiketi ve görüş birliği yok |
| Öğretmen/kullanıcı kabulü ve eğitim etkisi | **NOT_PERFORMED** | Pilot, süreç/kazanım ölçümü ve uygulama değerlendirmesi yok |
| Dondurulmuş MiniLM S1/S2 gerçek sonuçları | **RAPORLANMADI** | Ölçülmüş gerçek karşılaştırmalı skor kanıtı yok |

## 4. SONUÇ VE TARTIŞMA

### 4.1. Araştırma sorularına cevap

**AS1:** Sabit İngilizce Test-UQ sözlüksel deneyinde soru bağlamının eklenmesi B1'e kıyasla Macro-F1'i **0,054424** azaltmıştır. Bu yalnız sözlüksel bir temsili ve görülmemiş soru bölümünü kapsar.

**AS2:** Aktarılmış İngilizce etiketlerle yapılan keşifsel Türkçe karşılaştırmada B2−B1 farkı v0.2 için **+0,009307**, v0.2.1 için **+0,022277** bulunmuştur. İngilizce ve Türkçe farkların farklı işaretli olması tek başına “dil etkisi” kanıtı değildir; çeviri, sözcük dağılımı ve eğitim koşulları birlikte değişmiştir.

**AS3:** TR v0.2.1 için bağlam-kazancı farklarının farkı **+0,012970** hesaplanmış, fakat aralığın sıfıra çok yakın olması ve sınırlı bağımsız soru kümesi nedeniyle sonuç keşifsel tutulmuştur. B2'nin kendi sürüm farkı için %95 aralık sıfırı içermektedir.

**AS4:** Satır/split/kimlik/etiket bütünlüğü, 34 seçili tam eşleşme, eski dosyaların korunması, önceki İngilizce metriklerin tam tekrarı ve 36 confusion matrix aritmetiği başarıyla doğrulanmıştır. Bu, *yazılım doğruluğunu ve deney izlenebilirliğini* destekler; öğrencilerin bilişsel durumlarını ölçen bir sistemin geçerlilik kanıtı değildir.

### 4.2. Eğitimde kullanılabilirlik, uygulanabilirlik ve sınır

Çevrimdışı Python/CPU hattı kurum içi mahremiyet ve tekrar çalıştırılabilirlik için elverişli bir **araştırma prototipi** ortaya koymuştur. Herhangi bir öğretim kurumunda canlı ölçme/değerlendirme pilotu, erişilebilirlik/kullanılabilirlik testi, güvenlik tehdit modeli, veri saklama etkisi, gerçek işlem maliyeti veya öğretmenle kıyaslanmış doğruluk **ölçülmüş olarak ileri sürülmemektedir**.

Temel bilimsel riskler: (a) İngilizce sınıfların makine çevirisi üzerinden Türkçeye aktarılması; (b) çeviri hataları ve orijinal öğrenci yanılgısının istemeden düzeltilmesi olasılığı; (c) P0'da görülen çelişkili/tekrarlanan kayıtlar; (d) Test-UA'da eğitimle ortak üçlüler; (e) sadece 15 Test-UQ soru kümesi; (f) önceki proje aşamalarında Test-UQ sonuçlarının tekrar incelenmiş olması ve analiz uyarlama yanlılığı; (g) Other sınıfının heterojenliği; (h) Contradictory F1 düşüklüğü. Bu nedenle **öğrenciye otomatik not verme veya öğretmen yerine değerlendirme yapma kullanımına hazır kabul edilmemelidir**.

### 4.3. Araştırmanın özgün katkısının net sınırı

Ortaya konulan çıktı yeni bir yapay zekâ modelinin üstünlüğü değil, **kanıt zinciri ve koşullu araştırma kararlarıyla sürdürülmüş, tamamen çevrimdışı, dil karşılaştırmalı bir kısa-yanıt değerlendirme deney sistemidir**. Sonuçlar İngilizce sözlüksel ablasyonda bağlamın otomatik fayda üretmediğini; keşifsel Türkçe sözlüksel deneyde ise bağlam farkının ters işaretli olabileceğini göstermiştir. Gerçek Türkçe genellemesi, çeviri semantiğinin doğrulanması ve eğitim uygulamasının etkisi henüz açık araştırma konularıdır.

## 5. ÖNERİLER

Bu aşamada **mevcut Test-UQ üzerinde yeni model, kelime kuralı, çeviri onarımı veya C seçimi yapılmamalıdır**. Tamamlanan P1/T4 sürümleri, tohumlar, veri ve model manifestleri, çıktı SHA-256'ları, sınıf eşlemesi, soruya göre gruplama politikası ve ölçüm tanımları dondurulmalıdır.

**Bağımsız değerlendirme kapısı** [ayrı protokolde](../docs/TR_INDEPENDENT_VALIDATION_PLAN.md) geliştirilmiştir. Önce dış veriyi görmeden adayların ve karar kurallarının dondurulması; sonra özgün İngilizce sorularla örtüşmeyen yeni soru kümeleri ve ayrı toplanmış doğal Türkçe öğrenci yanıtları üzerinde kapsam, mahremiyet, etiketleme kökeni ve sınıf bazlı ölçümlerle doğrulama önerilir. Bağımsız Türkçe gold etiketi sağlanamıyorsa yalnız **etiketsiz bütünlük/çeviri tutarlılığı kontrolleri** yapılabilir; Macro-F1'in “gerçek Türkçe doğruluğu” olarak raporlanması mümkün değildir.

Bağımsız yeni veride de Contradictory sınıfı için performans yetersiz kalırsa sonuç **HOLD** olmalı; bu sınıf üzerinde yanlış güven oluşturabilecek otomatik not verme işlevi açılmamalıdır. Bu işlem, kullanıcıdan bağımsız insan değerlendirmesi gerektiren yeni bir çalışmayı zorunlu uygulama adımı yapmaz: mevcut yazılımın bakım ve tekrarlanabilirlik çalışmaları çevrimdışı otomatik testlerle sürdürülebilir, ancak gold-geçerlilik iddiası beklemelidir.

## 6. KAYNAKLAR

- Dzikovska, M. O., Nielsen, R. D., Brew, C., Leacock, C., Giampiccolo, D., Bentivogli, L., Clark, P., Dagan, I. ve Dang, H. T. (2013). SemEval-2013 Task 7: The Joint Student Response Analysis and 8th Recognizing Textual Entailment Challenge. *Second Joint Conference on Lexical and Computational Semantics (SEM), Volume 2*, 263–274. https://aclanthology.org/S13-2045/
- Pedregosa, F., Varoquaux, G., Gramfort, A., Michel, V., Thirion, B., Grisel, O., … Duchesnay, É. (2011). Scikit-learn: Machine learning in Python. *Journal of Machine Learning Research, 12*, 2825–2830. https://jmlr.org/papers/v12/pedregosa11a.html
- Reimers, N. ve Gurevych, I. (2019). Sentence-BERT: Sentence embeddings using Siamese BERT-networks. *Proceedings of EMNLP-IJCNLP*, 3982–3992. https://aclanthology.org/D19-1410/
- TÜBİTAK-BİDEB. (2026). *2242 Üniversite Öğrencileri Araştırma Proje Yarışmaları Proje Rehberi (2025–2026)*. https://cdn.teknofest.org/media/upload/userFormUpload/2242_%C3%BCniversite_proje_rehberi_2025-2026_OBW7i.pdf
- TÜBİTAK. (2026). *2242 — Üniversite Öğrencileri Araştırma Proje Yarışmaları, proje raporu yükleme ve 2026 kuralları*. https://tubitak.gov.tr/en/competitions/2242-university-students-research-project-competitions
- TEKNOFEST. (2026). *Üniversite Öğrencileri Araştırma Proje Yarışmaları — kategori, yarışma dokümanları ve 2026 takvimi*. https://teknofest.org/tr/yarismalar/universite-ogrencileri-arastirma-proje-yarismalari/
- *SciEntsBank veri kümesi; nkazi/SciEntsBank yayını*. (t.y.). https://huggingface.co/datasets/nkazi/SciEntsBank

## 7. EKLER VE YENİDEN ÜRETİLEBİLİRLİK

**Ek A — Açık kaynak kod / yöntem bağlantıları (yalnız teknik metaveri):** [StudentContextNLP GitHub geliştirme dalı](https://github.com/seydivakkas/StudentContextNLP/tree/feature/tr-v0.2-offline-adaptation), [kaynak P0 raporu](P0_REAL_DATA_AUDIT_2026-10-10.md), [T2 tam çeviri kaydı](T2_REAL_TR_TRANSLATION_2026-10-10.md), [T3 tam tarama](T3_FULL_CORPUS_REAL_2026-10-11.md), [T4 gerçek skorlar/sınıf bazlı QA](T4_REAL_PROXY_2026-10-11.md), [T4 soru-kümesi protokolü](../docs/TR_T4_PROXY_LEXICAL_PROTOCOL.md).

**Ek B — Önemli yerel, yayımlanmamış artefaktlar:** \`data/raw/\`, \`data/tr_v0_2/\`, \`data/tr_v0_2_1/\`, \`reports/tr_auto_full_v01/\`, \`reports/tr_patch_plan_v021_ai_draft/\`, \`reports/tr_compare_v021/\`, \`reports/tr_impact_v021/\`, \`results/lexical/baseline_results.json\`, \`results/t4_proxy_v021/t4_proxy_results.json\`, \`reports/tr_t4_metric_audit_v01/\`. Bunların **kaynak kişisel/öğrenci metinleri, satır kayıtları ve lisans durumu değerlendirilmeden GitHub'a veya yarışma sistemine tam veri olarak yüklenmesi uygun kabul edilmez**. İzinli ve lisans uyumlu kod/araç kanıtları ayrıca paketlenebilir.

**Ek C — Doğrulama kontrol listesi:** sabit SciEntsBank kaynak revizyonu ve SHA-256, beşli→dörtlü etiket haritası, Train–Test-UQ İngilizce soru ayrımı, 10.804 satır bütünlüğü, 34 kanıtlı AI_DRAFT düzeltmesi ve 3 bekleyen aday, 76/76 sentetik test kabulü, 36 confusion matrix aritmetiği, P1 tam 1e−8 tekrarı, T3-HUMAN=NOT_PERFORMED, 15 soru-kümesi bootstrap, Türkçe gold iddiası yok.

**Ek D — Uygunluk:** TÜBİTAK 2026 rehberinde rapor özeti **150–300 kelime**, 3–6 anahtar kelime, giriş/yöntem/bulgular/sonuç/öneriler/kaynaklar/ekler düzeni ve APA 6.0 kaynakça yaklaşımı belirtilmektedir. Geçerli yeni çağrı ilan edildiğinde **resmî şablonun son sürümü, başvuru uygunluğu, etik izin ve rapor PDF uzunluğu** ayrıca kontrol edilmelidir. Bu dosya tamamlanmış **bilimsel içerik taslağıdır**, sisteme gönderilmiş veya şablonu birebir doldurulmuş resmî başvuru dosyası değildir.
