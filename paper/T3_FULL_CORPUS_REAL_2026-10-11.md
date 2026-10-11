# T3-AUTO v0.3 — 10.804 Kayıtlı Gerçek Windows Tam Tarama Kanıtı

> **Kaynak:** Araştırmacının 11 Ekim 2026 tarihli Windows PowerShell çıktısı (`audit_translation_corpus.py`, `reports/tr_auto_full_v01`). Bu belge gerçek kullanıcı çalıştırmasının **agregat bildirimidir**; özgün öğrenci metinleri, üretilen tam CSV ve SHA-256 manifestleri kullanıcı bilgisayarındadır. GitHub CI kendi başına gerçek SciEntsBank metinlerini yeniden taramamıştır.

## Ön koşullar ve yazılım doğrulaması

- Geliştirme dalı: `feature/tr-v0.2-offline-adaptation`
- Yerel sentetik/yazılım regresyon testleri: **49/49 PASS, 7.45 saniye**
- P0 sabit kaynak revizyonu, dört Parquet veri dosyası ve Türkçe hedef dosyalarının SHA-256'sı `audit_translation_corpus.py` tarafından doğrulandı; komut hata vermeden tamamlandı.
- Orijinal `id`, beşli `label`, İngilizce soru/referans/öğrenci yanıtı her satırda eşleştirildi. Dört split toplamı **10.804/10.804**.
- Önceden dondurulmuş 240 kayıtlık gerçek T3-AUTO v0.2 örneklem raporu `frozen_sample_recheck.total_flags==220` ile tekrar uyumlu bulundu.
- Kaynaklara/çeviri dosyalarına otomatik müdahale: **0**.

## Tam gerçek veri üzerinde ilk QA sonuçları

| Split | Kayıt | HIGH (benzersiz satır) | MEDIUM (yalnız orta öncelik) | Kuralla işaretlenmeyen | Kural tetiklenmesi |
|---|---:|---:|---:|---:|---:|
| train | 4.969 | 983 | 1.139 | 2.847 | 4.140 |
| test_ua | 540 | 118 | 121 | 301 | 485 |
| test_uq | 733 | 53 | 243 | 437 | 457 |
| test_ud | 4.562 | 776 | 775 | 3.011 | 2.330 |
| **TOPLAM** | **10.804** | **1.930** | **2.278** | **6.596** | **7.412** |

**4.208 satır** en az bir otomatik uyarı taşıyor; bu bir *yanlış çeviri oranı* değildir. **6.596** işaretsiz satırın da doğru olduğu ispatlanmış değildir. `HIGH` ifadesi kural önceliğidir, istatistiksel doğrulama ya da kalibre edilmiş hata olasılığı değildir.

**Kaynak bilimsel kavram: 28**, aynı `rule + metin alanı + kaynak/hedef kanıtı` birden fazla satırda görülen grup: **155**. Bunlar yeni sürümde üretilecek `concept+field+source/target` kök neden kümelerinin sayısıyla birebir aynı kabul edilmemeli; gruplanma anahtarları farklıdır.

## En yaygın kaynak kavram adayları

| Kavram | Kural tetiklenmesi | Ayrı satır | Ayrı metin alanı/kaynak/hedef |
|---|---:|---:|---:|
| negation | 2.081 | 1.952 | 576 |
| english_lexeme | 800 | 461 | 136 |
| bulb | 655 | 306 | 81 |
| numbers | 536 | 517 | 53 |
| evaporate | 502 | 358 | 127 |
| solid | 467 | 378 | 87 |
| milliliter | 397 | 391 | 66 |
| slope | 346 | 283 | 23 |
| calcite | 305 | 120 | 67 |
| exclusivity | 242 | 242 | 5 |
| plant_pot | 201 | 197 | 6 |
| fogged_glass | 200 | 200 | 2 |

Kural sayısını kaynakta düzeltilmesi gereken cümle sayısı sanmak hatalıdır. Özellikle `exclusivity` için **242 kayıt yalnız 5 farklı eşleşmeye**, `fogged_glass` için **200 kayıt yalnız 2 farklı eşleşmeye** dayanıyor. Bu, tekrarlanan kaynak soru/referans çevirilerinin önce **kök neden** olarak incelenmesini önerir, fakat otomatik hata doğrulaması değildir.

## Mühendislik devam paketi: Kök neden önceliklendirme

`prioritize_translation_issues.py` tam tarama sonuçlarını:

1. **(concept, field, source_en, target_tr)** anahtarına göre gruplayarak tekrarları birleştirir; birden çok kural aynı metni işaretliyorsa tek kanıt kümesinde gösterir.
2. Birim/olumsuz fiziksel kavram tersine dönüşü `P1_SCIENTIFIC_POLARITY_OR_UNITS`, belirli yanlış teknik karşılıklar `P2_SPECIFIC_TECHNICAL_TERM`, diğer genel kural şüphelerini `P3_SURFACE_HEURISTIC` olarak ayırır. Bunlar mühendislik sırası, doğruluk olasılığı **değil**.
3. `full_qa_summary.json` içindeki kaynak dosya SHA-256'sını, tüm kural/toplam/split sayımlarını ve kayıt düzeyi HIGH/MEDIUM sayılarını denetler.
4. Sonuçları **yeni, yerel `reports/tr_auto_priority_v01/`** klasörüne yazar; özgün veri, Türkçe aday veri veya A/B formlarını değiştirmez.

| Dosya | İşlev |
|---|---|
| `root_cause_clusters.csv` | Kaynak metin, çeviri, örüntü SHA-256, alan, kural kümeleri, etkilenen satır ve split sayıları — **yerel kalmalı** |
| `concept_priority.csv` | Bilimsel kavramın farklı hata örüntüleri ve öncelik sınıfı |
| `root_cause_summary.md` | Kaynak metin içermeyen toplulaştırılmış araştırma özeti |
| `root_cause_manifest.json` | Girdi ve çıktı SHA-256, sayaçlar ve güven sınırları |

**Gerçek 10.804 kayıtlık kök neden raporu henüz üretilmedi;** yalnız tam kural taraması gerçek Windows ortamında PASS. Yeni önceliklendirme modülünün sentetik birim testleri eklendi.

## Bilimsel sınır

T3-HUMAN **NOT_PERFORMED**, Cohen kappa veya insan doğrulanmış kalite oranı **YOK**. T3-AUTO yalnız kaynak metne dayalı denetlenebilir şüphe ve önceliklendirme çıktısı üretir. `UNVERIFIED_TRANSFER` etiketleri Türkçe gold değildir. Türkçe modeller değerlendirilecekse sonuçlar **keşifsel aktarılmış-etiket proxy** olarak açıkça ayrılacaktır.
