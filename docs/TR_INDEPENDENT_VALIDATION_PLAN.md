# StudentContextNLP — Test-UQ'dan Bağımsız Doğrulama ve Bilimsel Kabul Protokolü

**Durum:** Önceden dondurulacak ileri araştırma planı. **Henüz uygulanmadı; sonuç, gold veri, insan değerlendirmesi veya yeni test başarısı içermez.** 11 Ekim 2026 tarihli P1/T4 sonuçları bu planın yöntemsel motivasyonudur, **daha fazla model veya çeviri seçimi için kullanılmayacaktır**.

**Bağlantılı proje raporu:** [TEKNOFEST 2242 Eğitim rapor taslağı](../paper/TEKNOFEST_2242_EGITIM_RAPORU_TR.md). **Sabit önceki deney:** [T4 gerçek Windows sonuçları](../paper/T4_REAL_PROXY_2026-10-11.md).

## 1. Neden yeni doğrulama gerekiyor?

T4 Test-UQ yalnız **733 kayıt / 15 özgün İngilizce soru kümesi** içeriyor; bu bölüm üzerinde daha önce P1, T3 ve T4 aşamalarında tekrar sonuç incelendi. Bazı Türkçe ifadeler AI_DRAFT önerileriyle revize edildi; etiketler **İngilizce özgünden aktarıldı**, doğal Türkçe öğrencilerinden bağımsız olarak doğrulanmadı. Bu nedenle güven aralığı dar görünse bile veri-uyarlama etkisini gerçek Türkçe performans veya pedagojik geçerlilik gibi yorumlamak doğru değildir.

Dört farklı kanıt sınıfı ayrı tutulacak:

1. **S1 — Yazılım bütünlüğü (etiket gerekmez):** Hash, satır/alan/provenans, sürümlü değişiklik, deterministik test ve sızıntı engelleri.
2. **S2 — Çeviri tutarlılığı incelemesi (etiket gerekmez):** Sayısal birim/olumsuzlama denetimleri ve tekrar eden kaynak–hedef eşleşmeleri; yanlış alarm oranı bilinmez, semantik doğruluğa eşitlenmez.
3. **S3 — Bağımsız değerlendirme (gerçek referans etiketleri gerekir):** Yeni, görülmemiş sorular ve doğal Türkçe açıklamalarla sınıf bazlı Macro-F1 ve hata profili.
4. **S4 — Sınıf içi eğitimsel fayda (ayrı izinli saha çalışması gerekir):** Öğretmen-kullanıcı etkileşimi ve öğrenme kazanımı; şu an **proje kapsamı dışında**.

**Kullanıcı bağımsız insan değerlendirmesi yapmak istemediği sürece yazılım mühendisliği S1/S2 üzerinden sürdürülebilir. S3 ve S4 iddiaları ise \`NOT_EVALUATED\` olarak kalır.** İnsan etiketlerinin var olmadığı yerde otomatik çeviri kıyaslaması, öğretmen gold kararı yerine geçirilmeyecek.

## 2. Dondurulacak araştırma nesneleri

Dış veri toplanmadan, etiketleri görülmeden veya başka bir test skoruna bakılmadan aşağıdakiler için ayrı **salt-okunur, SHA-256 imzalı protokol manifesti** üretilecek:

| Nesne | Dondurulacak alanlar | Değiştirme politikası |
|---|---|---|
| P0 İngilizce kaynak | 4 özgün dosya, normalizasyon, label mapping, soru kümesi | Sabit; çelişkiler ayrı analiz |
| T2 Türkçe ham aday | v0.2 çeviri paket/model hash'i, CSV manifestleri | Orijinali değiştirme |
| T3-AUTO öneri | 37 tam eşleşme; 34 APPLY_EXPLORATORY, 3 PENDING | Kaynak/öneri kanıtı dondurulmuş |
| T3-AUTO düzeltilmiş aday | v0.2.1 split hash'leri, patch audit | Sabit; yeni düzeltme gerekiyorsa yeni sürüm |
| T4 sözlüksel model seçimi | B0–B3 özellikleri; C; seed=20261009; EN soru grupları | Test verisinden yeniden seçim yok |
| Metrik protokolü | Dört sınıf sırası, Macro-F1, sınıf F1, soru-kümeli bootstrap | Dış test sonuçlarını görmeden sabitle |
| Kapsam ve açıklama | Data license/consent, P0 uyarıları, no gold, no causal inference | Asla geriye dönük gizleme |

Önceki Test-UQ'ya dayanan B2/B1 karşılaştırmaları **keşifsel tarihsel sonuç** olarak saklanır; ön kayıtlı bağımsız test gibi yeniden etiketlenmez.

## 3. Yeni bağımsız test kohortu — örnekleme sınırı

Önerilen veri kaynağı, mevcut SciEntsBank testlerinden veya onların yalnız çevirisinden kopyalanmayan **yeni fen soruları ve doğal Türkçe kısa öğrenci açıklamalarıdır**. Bir sorunun parafrazı, aynı fen şablonunun birebir devamı veya kaynak referansın yeniden yazımı *yeni bağımsız soru* kabul edilmeyecek.

- Soru toplama ve soru kimliği: her kavramsal soru \`question_group_id\` ile gruplanır; aynı soru/metin varyantları aynı gruba alınır. Eğitim, model geliştirme, kalite ön tarama, konu seçimi, kontrol ve dış test soruları ayrık tutulur.
- **Bölüm sızıntısı:** Normalize Türkçe/İngilizce soru, referans ve öğrenci yanıtının yakın yinelenenleri için önceden seçilmiş eşiklerle benzerlik taraması; belirsizler \`OVERLAP_REVIEW_PENDING\`. Test sonuçlarıyla eşik ayarlanmaz.
- **Örneklem planı:** Kaç soru/yanıt toplanacağı, soru başına gözlem sayısı ve hedef güven aralığı genişliği **veri görülmeden güç/duyarlılık simülasyonu** ile kesinleştirilecek; mevcut projede buna ilişkin doğrulanmış örneklem büyüklüğü yoktur. Bu nedenle belirli bir N'nin yeterli olduğu **iddia edilmez**.
- **Sınıf dengesi:** Correct, Incomplete, Contradictory, Other sınıfları örneklem tasarımında önceden hedeflenir; gerçek sınıf dağılımı ile denge örneklemesi arasındaki fark ağırlıklar ve ham tabloyla raporlanır.
- **Mahremiyet ve izin:** Öğrenci açıklamaları yeniden toplanacaksa veri kaynağı izni, kurum süreçleri ve gerekliyse veli/katılımcı onamı, gizlilik ve saklama koşulları tamamlanmadan veri toplanmaz; kimlik bilgileri erişime kapalı tutulur. Verilerin GitHub'a aktarılacağı varsayılmaz.

Yeni materyal zaten erişilebilir bir lisanslı veri kümesinden alınırsa lisans, gerçek dil kökeni ve önceki Test-UQ ile örtüşme ayrıca denetlenir. **Türkçeye makine çevrilmiş İngilizce test, doğal Türkçe öğrencilerden toplanmış veri yerine geçmez.**

## 4. Referans etiket, ölçüm ve kabul

**S1/S2 (insan etiket gerektirmeyen) kabul:** SHA-256 ve manifestlerin doğrulanması; yinelenen soru/cevap sızıntısında fail-closed; aynı kodun tekrar çalıştırılabilirliği; kaynak etiket/yanıt değişmezliği; tüm QA uyarılarının **hipotez** olarak saklanması. Bu kapının PASS olması gold veya pedagojik kabul anlamına gelmez.

**S3 (gerçek sınıflandırma geçerliliği) için zorunlu ön koşul:** Her yeni yanıtın özgün Türkçe içeriğine ilişkin referans etiketin **modelden ve otomatik çeviri önerisinden bağımsız bir değerlendirme prosedürüyle** belirlenmesi. Uygulanabilir bir tasarım, konu yeterliği olan bağımsız değerlendiricilerce kör etiketleme ve önceden tanımlı anlaşmazlık çözümüdür. Ancak bu bir **gelecek araştırma önerisidir**; henüz kimse değerlendirme yapmadı, kappa ölçülmedi ve kullanıcı onayı olmadan insan çalışma paketi başlatılmayacak. Güvenilir doğruluk etiketi olmaksızın S3'in Macro-F1 değerini hesaplamak **yasaktır**.

S3 mümkün olursa, ilk dondurulmuş paket açılmadan şu ölçüler ilan edilecek:

- **Birincil metrik:** dört sınıf sabit-sıralı Macro-F1, *her yeni doğal Türkçe yanıtın bağımsız referans sınıfına karşı*.
- **Karşılaştırmalar:** B1 vs B2; B0; B3. Türkçe v0.2.1 sürümünün eğitim verisi sabit; Test-UQ'dan yeni tuning yok.
- **Birincil belirsizlik:** yeni \`question_group_id\` kümeleri üzerinde eşlenik yüzde 95 bootstrap; küme sayısı, etkili örneklem, tüm sınıf destekleri raporlanacak.
- **İkincil:** sınıf bazlı precision/recall/F1, confusion matrix, accuracy, weighted F1; özellikle Contradictory yanlış negatifleri. Eğer referans yanıt mevcutsa öğrencinin özgün fen yanılgısının etiketiyle *görüş ayrılığı* ayrı izlenecek.
- **Tekrarlama ve uyarılar:** çift anlamlı soru, eksiltili öğrenci yanıtı, yanlış bilimsel referans yanıtı, tekrarlar/label çelişkileri ve karakter/dil kaymaları için ayrık analiz.
- **Değerlendirme kararı:** Kullanım güvenliği, Contradictory geri çağırımı, sınıf dengesizlikleri ve CI genişliği için *önceden* kararlaştırılmış eşikler olmadıkça otomatik “geçti / notlandırmaya hazır” denmeyecek. Eşikler bu çalışmadaki Test-UQ skorları üzerinden seçilmez.

**S4:** Öğrenci öğrenmesi, öğretmen iş yükü, yanlış yönlendirme ve kullanıcı deneyimi, ayrı etik ve eğitim araştırması gerektirir. S3 başarılı olsa bile S4 tamamlanmış sayılmaz.

## 5. Sorun analizi ve başarısızlık şeması

Bağımsız test başlatılırsa her hata en az şu ayrı kodlarla ele alınmalı; bir kayıtta birden fazla sorun bulunabilir:

| Kod | Açıklama | Ölçüm önceliği |
|---|---|---|
| \`SOURCE_LABEL_CONFLICT\` | Aynı kaynak üçlü için çelişkili sınıf | P0 tekrarı, hata hassasiyeti |
| \`TRANSLATION_POLARITY\` | Türkçede olumsuzlama/doygunluk gibi anlam tersine dönüşü | Özgün bilimsel yanılgı korunumu |
| \`UNIT_SCALE\` | mL/L gibi 1000 kat ölçü birimi olası kayması | Sayı/birim semantiği |
| \`TECHNICAL_TERM\` | *bulb*, *calcite*, *solid*, *evaporate* bağlam kayması | Bağlamlı terminoloji |
| \`SHORT_ANSWER_AMBIGUITY\` | “Store food.” türünde eksiltili kısa yanıt | Belirsiz/PENDING |
| \`QUESTION_SHORTCUT\` | Modelin öğrenciyi okumadan soru kalıbından yanıt kestirmesi | B3 kontrolü |
| \`RARE_CLASS_FAILURE\` | Contradictory gibi düşük F1/düşük destek | Yanlış güven/adalet |
| \`SPLIT_OR_NEAR_DUPLICATE\` | Eski eğitim/test sorusunun aynısı/yakını | Veri sızıntısı |
| \`GOLD_NOT_AVAILABLE\` | Referans etiketi yok veya doğrulanmamış | S3 blokajı |

**Raporlama:** Kategori bazında ayrı *hata adedi*, *etkilenen soru kümesi*, *doğrulanmış etiketli örnek* ve *kural tarafından şüpheli işaretlenen kayıt* farklı kolonlar olarak verilmelidir. Çelişkili bilimsel açıklamayı geriye dönük “doğru cevap”a dönüştüren otomatik düzeltme göz ardı edilmemelidir.

## 6. Dış doğrulama öncesi karar ağacı

\`\`\`text
Yeniden üretilebilir kod + v0.2/v0.2.1 hash'leri korundu mu?
  HAYIR -> HOLD; yalnız kaynak bütünlüğü / kod onarımı
  EVET  -> Model, sınıf eşlemesi, C, metrik, gruplama, eşik protokolü DONDUR
           |
           Yeni sorulara / kaynak yanıtlarına erişim ve izin mevcut mu?
             HAYIR -> S1/S2 üzerinde kal; bağımsız doğruluk iddiası YOK
             EVET  -> Soru sızıntısı taraması ve bağımsız dış test ayrımı
                      |
                      Doğal Türkçe örneklerde bağımsız etiketler var mı?
                        HAYIR -> S1/S2 otomatik denetim; S3 NOT_EVALUATED
                        EVET  -> Kilitli modelleri bir kez dış testte değerlendir
                                 |
                                 Sınıf başına F1/Recall, CI, yanlış negatif,
                                 soru kümeleri ve hata şemasını raporla.
                                 Sonuca bakarak yeniden tuning yapma.
\`\`\`

## 7. İş paketleri ve ilerleme kanıtı

| Kapı | Girdi | Çıktı | Durum |
|---|---|---|---|
| V0 — T4 deneyin dondurulması | Kaynak/candidate manifestleri, İngilizce ve T4 metrik JSON | SHA-256'lı sürüm/protokol | **Protokol hazırlanmış, ayrı freeze dosyası henüz üretilmedi** |
| V1 — S1/S2 otomatik tekrarlanabilirlik | Yerel SciEntsBank, önceki scriptler | Aynı sayımlar, hash, CI ve kod testleri | T4'te önceki denetim PASS; yeni bağımsız kontrol **yapılmadı** |
| V2 — Bağımsız kaynak/soru belirleme | Yeni lisanslı/izinli Türkçe veri | Soruların sızıntısız manifesti | **NOT_STARTED** |
| V3 — Türkçe bağımsız referans etiketi | Yeni doğal Türkçe yanıtlar ve gerekli onaylar | Etiket kökeni ve anlaşmazlık kaydı | **NOT_PERFORMED** |
| V4 — Dış test ve hata analizi | Kilitli model + V2/V3 | Yeni Macro-F1, sınıf F1, soru kümesi CI | **BLOCKED_BY_V2_V3** |
| V5 — Eğitim ortamı değerlendirmesi | V4 geçerli, izinli pilot | Kullanılabilirlik ve eğitim etkisi | **OUT_OF_CURRENT_SCOPE** |

## 8. Sonuç ve kullanım politikası

Bu plan, mevcut **TEKNOFEST araştırma raporunun ileri değerlendirme bölümüdür**, T4'e eklenmiş gerçek bir sonuç değildir. İleride yeni test kullanılacaksa her protokol değişikliği tarihlendirilmeli, SHA-256 ile dondurulmalı, geçmiş Test-UQ ile karıştırılmamalı ve **önceden test sonuçlarına bakılmış olma gerçeği açıkça beyan edilmelidir**.

**Teknik geliştirmeyi sürdürmek için bağımsız insan etiketlerini zorunlu tutmuyoruz; ancak bunlar olmadan “Türkçe doğru yanılgı tespiti”, “güvenilir otomatik notlandırma”, “öğrenme etkisi” veya “gerçek Türkçe gold Macro-F1” kabulü yapmıyoruz.**

*Kaynaklar ve proje kanıtı:* [ana yarışma raporu](../paper/TEKNOFEST_2242_EGITIM_RAPORU_TR.md), [T4 araştırma kaydı](../paper/T4_REAL_PROXY_2026-10-11.md), [P0 bütünlük denetimi](../paper/P0_REAL_DATA_AUDIT_2026-10-10.md), [2026 TÜBİTAK 2242 Proje Rehberi](https://cdn.teknofest.org/media/upload/userFormUpload/2242_%C3%BCniversite_proje_rehberi_2025-2026_OBW7i.pdf).
