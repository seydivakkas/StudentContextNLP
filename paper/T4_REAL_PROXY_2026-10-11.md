# T4 — Gerçek SciEntsBank Test-UQ EN/TR v0.2/TR v0.2.1 Keşifsel Sözlüksel Proxy Sonuçları

**Tarih:** 11 Ekim 2026. **Kanıt:** araştırmacının kendi Windows makinesinde çalıştırdığı `run_t4_proxy_lexical.py` terminal çıktısı. Özgün veri ve satır düzeyinde tahminler GitHub'da **yoktur**; GitHub CI yalnız sentetik regresyon ve yazılım güvenlik testlerini doğrulamıştır.

**Protokol:** [T4 kilitli karşılaştırma](../docs/TR_T4_PROXY_LEXICAL_PROTOCOL.md). Çalışan kod: [run_t4_proxy_lexical.py](../run_t4_proxy_lexical.py). Test-UQ **733 kayıt / 15 İngilizce normalize soru kümesi**. Başlangıçtaki beş özgün İngilizce etiketten sabit dört sınıfa aktarım: Correct, Incomplete, Contradictory, Other. Bu etiketler **Türkçe insan gold etiketi değildir**.

## Gerçek Windows çalışması ve temel sonuçlar

**Yazılım kabulü:** 71/71 sentetik regresyon testi PASS, üç varyantın train-grouped validation ve tüm üç değerlendirme bölümü tamamlandı. İngilizce P1 önceki skorları altı ondalıkta yeniden elde edildi. Tüm kaynak manifesti SHA denetimleri PASS, Test-UQ hiperparametre seçimi yapılmadı, eski veri/model dosyaları değiştirilmedi.

| Model | EN Macro-F1 | TR v0.2 Macro-F1 | TR v0.2.1 Macro-F1 |
|---|---:|---:|---:|
| B0 — çoğunluk | 0,145551 | 0,145551 | 0,145551 |
| B1 — yalnız öğrenci | 0,295023 | 0,265198 | 0,263115 |
| B2 — öğrenci + soru | 0,240599 | 0,274505 | 0,285392 |
| B3 — yalnız soru | 0,170172 | 0,149603 | 0,160710 |
| **B2−B1** | **−0,054424** | **+0,009307** | **+0,022277** |

**Dondurulmuş hiperparametreler:** EN B1 C=1, B2 C=10, B3 C=10; TR v0.2 B1 C=10, B2 C=10, B3 C=10; TR v0.2.1 aynı C=10/10/10 (TR v0.2 train-validation seçiminden). Test-UQ üzerinde yeni C seçimi yoktur.

**Gözlenen farklar (yuvarlanmış tablo üzerinden):** TR v0.2.1−v0.2 B2 **+0,010887**, B1 **−0,002083**, B3 **+0,011107**, B0 **0,000000**. Bağlam girdisinin kazancı v0.2'de **+0,009307**, v0.2.1'de **+0,022277**. Bu özel TF-IDF+LogisticRegression koşulunda İngilizce B2−B1 negatif iken Türkçe proxy koşullarında pozitiftir. Dilsel doğruluk veya genellenebilir bağlam etkisi konusunda nedensel yorum yapılamaz.

**Farkların farkı:** `[MacroF1(B2)−MacroF1(B1)](TR v0.2.1) − [MacroF1(B2)−MacroF1(B1)](TR v0.2)` = **+0,012970134720524773**. 15 özgün İngilizce soru kümesine göre eşlenik, 1000 tekrarlı, sabit `seed=20261009` bootstrap **tanımlayıcı %95 percentile aralığı**: **[0,0000448260933499839; 0,026609468785013725]**. Alt sınır pratik olarak sıfıra çok yakındır; küçük kümeler, önceki deneylerle aynı Test-UQ ve keşifsel analiz nedeniyle bu sonucu kesin istatistiksel doğrulama, güçlü anlamlılık, müdahale etkisi veya genel Türkçe performans artışı olarak raporlamıyoruz.

## Veri ve deney bütünlüğü

| Ölçüm | Windows kaydı |
|---|---|
| Orijinal veri | 10.804 kayıt, 4 split, değişmeden saklandı |
| v0.2.1 düzeltme kapsamı | 34 AI_DRAFT tam-metin eşleşmesi; 1604 farklı kaydın 1748 Türkçe alan örneği |
| Test-UQ Türkçe v0.2.1 değişiklikleri | Yalnız 40 soru metni; öğrenci ve referans değişimi 0 |
| İngilizce kaynak ve özgün etiketler | SHA ve birebir alan karşılaştırma PASS |
| Türkçe etiket kökeni | `UNVERIFIED_TRANSFER` |
| P1 Test-UQ tekrar skorları | Altı ondalıkta önceki kayıtla uyumlu |
| **P1 tam `1e-8` eşleşme kararı** | **HENÜZ ÇIKTIDAN DOĞRULANAMADI** |
| Satır-düzeyi veri GitHub'a eklendi mi? | Hayır |

**Windows PowerShell sunum hatası:** `Write-Host "Skorlar 1e-8 toleransta uyumlu: $($e.all_within_1e-8)"` benzeri bir ifade `-8` aritmetik bileşeni olarak çözümleyebilir; kullanıcı günlüğündeki `-8` **modelin uyuşmadığı anlamına gelmez**. Gerçek boole değerini `$($e.'all_within_1e-8')` ile okumak gerekiyor. Bilimsel kabul tamamlanırken bu alan yeniden doğrulanmalı.

## Zorunlu bilimsel sınırlamalar

- Bu **keşifsel, aktarılmış etiketli sözlüksel proxy** deneydir; insan değerlendirmesi, Türkçe gold etiket, Cohen kappa veya Türkçe öğrenci doğal dağılımında doğrulama yapılmadı.
- Çeviri düzeltmelerinin önceki QA kural uyarılarını azaltması **doğru anlam korunduğu** veya sınıflandırmanın bilimsel olarak iyileştiği anlamına gelmez.
- Yalnız 15 Test-UQ soru kümesi vardır; soru düzeyinde korelasyon ve özgün veri etiket çelişkileri bulunmaktadır.
- İngilizce ve Türkçe sonuçlar aynı veri/etikete rağmen dil temsili, eğitim metni ve çeviri kalitesi bakımından farklıdır. İngilizce B1−B2 farkı Türkçedeki B1−B2 farkının nedensel karşılığı olarak yorumlanmaz.
- Test-UQ önceki P1 ve T3 aşamalarında kullanılmıştır. Sonuçlara bakarak yeni sözlüksel kural seçmek, çeviri revizyonu yapmak veya C ayarlamak test uyarlama yanlılığı yaratır; bunlar sonraki bağımsız değerlendirmeye bırakılmalıdır.
- B0–B3 **referans yanıtını model girdisi olarak kullanmaz**; v0.2.1'deki 376 referans çevirisi değişiminin bu modeller üzerinde doğrudan girdi etkisi yoktur.
- T4'te per-class F1 ve confusion matrix yerel `results/t4_proxy_v021/t4_proxy_results.json` içinde mevcuttur; henüz bağımsız toplulaştırılmış araştırma tablosuyla kabul edilmedi.

## Bir sonraki mühendislik kapısı

Yeni eğitim veya test hiperparametre araması yapmadan, **salt-okunur T4 metrik denetimi**: İngilizce P1 `1e-8` tam yeniden üretimi, orijinal etiket sırası, macro-F1'in confusion matrix ve per-class değerleriyle aritmetik eşleşmesi, v0.2.1−v0.2 B1–B3 farklarının **eşlenik soru-kümesi aralıkları** ve Test-UQ etiket sınıflarının kırılımını yerelde raporla. Ardından dil/çeviri sınırlamalarıyla araştırma tablosunu kesinleştir; insan gold'u olmayan sistem için kabul **EXPLORATORY ONLY**.
