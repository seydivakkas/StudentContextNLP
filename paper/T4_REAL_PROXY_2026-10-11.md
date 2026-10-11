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
| **P1 tam `1e-8` eşleşme kararı** | **PASS — gerçek Windows `audit_t4_results.py` kontrolü** |
| Satır-düzeyi veri GitHub'a eklendi mi? | Hayır |

**PowerShell görüntüleme ayrıntısı artık çözüldü:** Önceki betikte `-8` olarak yazılan değer bir property-parsing sorunudur; ayrı salt-okunur denetim aracının gerçek Windows çıktısı `Tolerance 1e-8: True` ve `T4 METRIC AUDIT PASS` olarak kaydedildi. İngilizce P1'in karşılaştırılabilirlik kabulü tamamlandı.

## T4 metrik kabulü — gerçek Windows salt-okunur yeniden hesaplama

**İkinci mühendislik kabulü:** 76/76 regresyon testi **PASS**. `audit_t4_results.py` 36 adet 4×4 karışıklık matrisindeki TP/FP/FN sayılarını, Macro/Weighted F1, Accuracy ve dört sınıfın Precision/Recall/F1 değerlerini yeniden hesaplayıp mevcut T4 sonuçlarıyla karşılaştırdı; **PASS**. İngilizce P1 Test-UQ Macro-F1 sonuçlarının orijinal kayıttaki karşılıkları `1e-8` hassasiyette eşleşti: **True**. Toplu raporlar araştırmacının yerel `reports/tr_t4_metric_audit_v01/` klasöründe. `No human gold` durumu korunur.

### Test-UQ özgün dört sınıf destekleri

| Kaynak etiket aktarımı | Test-UQ kayıt sayısı |
|---|---:|
| Correct | 301 |
| Incomplete | 175 |
| Contradictory | 64 |
| Other | 193 |
| **Toplam** | **733** |

### Sınıf bazında B2 F1 — aynı Test-UQ örnekleri

| Sınıf | EN B2 | TR v0.2 B2 | TR v0.2.1 B2 | v0.2.1 − v0.2 |
|---|---:|---:|---:|---:|
| Correct | 0,487395 | 0,548303 | 0,553806 | +0,005503 |
| Incomplete | 0,123223 | 0,152466 | 0,180258 | +0,027791 |
| Contradictory | 0,041667 | 0,082645 | 0,085470 | +0,002825 |
| Other | 0,310112 | 0,314607 | 0,322034 | +0,007427 |
| **Macro-F1** | **0,240599** | **0,274505** | **0,285392** | **+0,010887** |

TR v0.2.1'de B2 Macro-F1 farkının en büyük sınıf katkısı *Incomplete* sınıfındadır (+0,027791 sınıf-F1). *Contradictory* sınıfında B2 F1 hâlâ **0,085470**; bu sınıfta yakalama performansı düşüktür ve teknik QA azalışına rağmen veri semantiğinin korunması/güvenilir pedagojik değerlendirme kanıtı değildir.

### B1 sınıf bazlı F1 (karşılaştırma için)

| Sınıf | EN B1 | TR v0.2 B1 | TR v0.2.1 B1 |
|---|---:|---:|---:|
| Correct | 0,480000 | 0,435352 | 0,437908 |
| Incomplete | 0,237705 | 0,277966 | 0,271186 |
| Contradictory | 0,127660 | 0,036364 | 0,036697 |
| Other | 0,334728 | 0,311111 | 0,306667 |
| **Macro-F1** | **0,295023** | **0,265198** | **0,263115** |

### Eşlenik soru-kümesi bootstrap — v0.2.1 − v0.2

| Model | Macro-F1 farkı | Tanımlayıcı %95 aralık | 15 küme / 1.000 bootstrap |
|---|---:|---|---|
| B0 | 0,000000 | [0,000000; 0,000000] | Evet |
| B1 | −0,002083 | [−0,008982; +0,005187] | Evet |
| B2 | +0,010887 | [−0,000945; +0,021446] | Evet |
| B3 | +0,011107 | [0,000000; +0,039529] | Evet |

B2 tek-model aralığı **sıfırı içermektedir**; B3 alt sınırı **sıfırdır**. Birincil `(B2−B1)_(v0.2.1)−(B2−B1)_(v0.2)` = **+0,01297013**, aralık **[+0,00004483; +0,02660947]**; alt sınır neredeyse sıfırdır ve Test-UQ'nun önceki araştırma aşamalarında tekrar kullanılmış olması nedeniyle yalnızca keşifsel/tanımlayıcı olarak sunulur. Bu sonuçlar çoklu inceleme, küçük soru-kümesi sayısı ve aktarılmış etiket sorununu çözmez.

**Yeniden çalıştırma notu:** İlk Windows denetimi `T4 METRIK DENETIMI PASS` ile sonuçlandı; aynı komutun ikinci kez çalıştırılması `reports/tr_t4_metric_audit_v01` zaten bulunduğu için **bilerek durdu**. Bu bir QA başarısızlığı değildir ve raporlar silinmemelidir.

## Zorunlu bilimsel sınırlamalar

- Bu **keşifsel, aktarılmış etiketli sözlüksel proxy** deneydir; insan değerlendirmesi, Türkçe gold etiket, Cohen kappa veya Türkçe öğrenci doğal dağılımında doğrulama yapılmadı.
- Çeviri düzeltmelerinin önceki QA kural uyarılarını azaltması **doğru anlam korunduğu** veya sınıflandırmanın bilimsel olarak iyileştiği anlamına gelmez.
- Yalnız 15 Test-UQ soru kümesi vardır; soru düzeyinde korelasyon ve özgün veri etiket çelişkileri bulunmaktadır.
- İngilizce ve Türkçe sonuçlar aynı veri/etikete rağmen dil temsili, eğitim metni ve çeviri kalitesi bakımından farklıdır. İngilizce B1−B2 farkı Türkçedeki B1−B2 farkının nedensel karşılığı olarak yorumlanmaz.
- Test-UQ önceki P1 ve T3 aşamalarında kullanılmıştır. Sonuçlara bakarak yeni sözlüksel kural seçmek, çeviri revizyonu yapmak veya C ayarlamak test uyarlama yanlılığı yaratır; bunlar sonraki bağımsız değerlendirmeye bırakılmalıdır.
- B0–B3 **referans yanıtını model girdisi olarak kullanmaz**; v0.2.1'deki 376 referans çevirisi değişiminin bu modeller üzerinde doğrudan girdi etkisi yoktur.
- T4'ün 36 adet 4×4 confusion matrix aritmetiği ve sınıf bazlı precision, recall, F1 değerleri gerçek Windows üzerinde yeniden hesaplanarak doğrulandı. Özetler yerelde `reports/tr_t4_metric_audit_v01/` altında, toplu sonuçları aşağıdadır.

## Bir sonraki mühendislik kapısı

T4'ün *sözlüksel proxy* karşılaştırması, 36 confusion matrix ile İngilizce P1 tekrarlanabilirlik kontrolü bakımından **tamamlandı**. Sonuçlara bakarak ek çeviri düzeltmesi veya test üzerinde hiperparametre seçimi **yapılmamalıdır**. Bir sonraki araştırma kapısı, ayrılmış bağımsız dış doğrulama planı ve test-uyarlama yanlılığının açıkça raporlanmasıdır; bu iş yapılmadan Türkçe gerçek eğitimsel geçerlilik iddia edilmez.
