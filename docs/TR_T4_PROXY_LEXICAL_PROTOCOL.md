# T4 — Çevrimdışı İngilizce/Türkçe B0–B3 karşılaştırmalı projected-label proxy protokolü

**Tarih:** 11 Ekim 2026. **Durum:** Yazılım geliştirildi ve sentetik regresyon testleri eklendi; gerçek Windows model skorları **henüz hesaplanmadı**. Bu belge yayımlanacak sonuç iddiası değildir.

## T3-AUTO v0.2.1 kabulü ve T4 ön denetimi — gerçek Windows

Araştırmacının Windows çalıştırması: **66/66 yazılım testi PASS**, T3-AUTO ön-denetim PASS. Sürüm dosyaları/etiketler orijinal kaynakları koruyor. 10.804 kaynak satırda 1.604 farklı kaydın toplam **1.748 Türkçe alanı** değişti.

| Bölüm | Soru değişimi | Referans değişimi | Öğrenci yanıtı değişimi | Ayrı değişen kayıt |
|---|---:|---:|---:|---:|
| train | 565 | 248 | 5 | 779 |
| test_ua | 64 | 28 | 1 | 88 |
| test_uq | 40 | 0 | 0 | 40 |
| test_ud | 697 | 100 | 0 | 697 |
| **Toplam** | **1.366** | **376** | **6** | **1.604** |

**Aynı kaydın birden çok metin alanı değişebilir; alan sayıları ayrı kayıt sayıları değildir.**

T3-AUTO öncelik geçişi: **610 HIGH→MEDIUM**, **784 HIGH→UNFLAGGED**, **210 HIGH→HIGH** (düzenlenmiş toplam 1.604). Hiç düzenlenmeyen 9.200 satırın önceliği değişmedi. Bu kural öncelik geçişleri gerçek çeviri doğruluğuna eşit değildir.

Test-UQ 733 kayıt / 15 İngilizce soru kümesi. v0.2.1 yalnız 40 soruyu değiştirmiştir; Türkçe öğrenci yanıtları Test-UQ'da birebir aynıdır. **Ancak eğitimde 5 öğrenci yanıtı farklı olduğundan B1 çıktıları aynı olma zorunluluğu yoktur.** Referans metinleri B0–B3 model girdisi değildir. Test-UQ değiştirilmiş alanların 40'ı da sorudur; 31'i orijinal doğru, 5'i çelişkili, 2'si kısmen doğru, 2'si ilgisiz özgün etiketlidir. Bunlar orijinal İngilizce etiketlerin aktarımıdır, Türkçe gold sınıfları değildir.

## Sabit deney

[run_t4_proxy_lexical.py](../run_t4_proxy_lexical.py), **mevcut [train_lexical.py](../train_lexical.py)** model ailelerini aynen yeniden kullanır:

| Model | Girdi | Algoritma |
|---|---|---|
| B0 | Çoğunluk sınıfı | `DummyClassifier(most_frequent)` |
| B1 | Öğrenci açıklaması | Kelime 1–2 + karakter 3–5 TF-IDF; Logistic Regression |
| B2 | Öğrenci + soru | Aynı vektörleştirme ve Logistic Regression |
| B3 | Soru | Aynı vektörleştirme ve Logistic Regression |

**Varyantlar:** `en` özgün İngilizce; `tr_v0_2` yerel Argos çevirisi; `tr_v0_2_1` kaynak kanıtına bağlı AI_DRAFT keşifsel düzeltme. Tümü **aynı satır sırası, `id` ve beş özgün İngilizce etiketten türetilen dört sınıfı** korur. `Correct/Incomplete/Contradictory/Other` etiketi İngilizce kaynak veri aktarımıdır, Türkçe gold değil.

- **Hiperparametre:** `C ∈ {0.1, 1, 10}`; EN ve TR v0.2'de tek, sabit **yalnız train içindeki** `GroupShuffleSplit(test_size=0.25, seed=20261009)`; soruların **özgün İngilizce normalize metniyle** gruplama. TR v0.2.1, TR v0.2 için train validation'da belirlenmiş C'yi aynen kullanır; böylece v0.2→v0.2.1 farkına yeniden hiperparametre seçimi karışmaz.
- **Evaluation:** Test-UQ ön kayıtlı birincil (733 kayıt, 15 bağımsız İngilizce soru kümesi); Test-UA ve Test-UD ikincil. Normalleştirilmiş İngilizce soru düzeyinde train/Test-UQ ve train/Test-UD örtüşmesi varsa fail-closed.
- **Birincil gösterge:** `Δ_context = MacroF1(B2) - MacroF1(B1)` (her varyant için). Ayrıca Türkçe v0.2.1−v0.2 her B modeli ve **difference of differences** `[Δ_context(v0.2.1) − Δ_context(v0.2)]`, **eşleşmiş İngilizce soru kümelerine göre bootstrap 1.000 iterasyon**, seed 20261009, tanımlayıcı %95 percentile güven aralığı.
- **Kontrol:** İngilizce Test-UQ B0–B3 metrikleri, mevcut `results/lexical/baseline_results.json` varsa karşılaştırılır; birebir sayı uyuşmazlığı raporlanır ama sonucu saklamak için susturulmaz.
- **Rapor:** Macro-F1, weighted-F1, accuracy, sınıf bazlı F1, confusion matrix, seçilen C, seçimin test skorundan **önce** saklanması; sadece toplulaştırılmış değerler. Yerel modelleme **CPU/sklearn**, ağ/API/LLM/agent/RAG yok.

### Çalıştırma (Windows)

```powershell
.\.venv\Scripts\python.exe run_t4_proxy_lexical.py --original-dir data/raw --tr-02 data/tr_v0_2 --tr-021 data/tr_v0_2_1 --comparison reports/tr_compare_v021 --out results/t4_proxy_v021 --allow-p0-warnings
```

**Beklenen çıktı:**

- `results/t4_proxy_v021/selection_before_test.json` — soru gruplu eğitim/doğrulama, sabit C ve validasyon sonucu
- `results/t4_proxy_v021/t4_proxy_results.json` — Test-UA/UQ/UD tüm B0–B3 ölçümleri, dört sınıf dağılımı, %95 grup bootstrap CI, QA manifestleri
- `results/t4_proxy_v021/t4_proxy_summary.md` — Test-UQ sonuç tablosu, farkların yorum sınırlaması

Bu çıktı **önceki P1 İngilizce model/rapor klasörüne yazmaz**, kişisel öğrenci metni veya satır-düzeyi tahminleri GitHub'a yüklemez. Çalışma başarısız olursa `results/t4_proxy_v021.part/` inceleme için korunur; sessizce silinmez.

## Bilimsel sınırlar ve sonraki karar

**T4 ölçümü Türkçe performans doğrulaması değildir.** Aynı orijinal İngilizce sınıflar makine çevirisi adaylarına aktarılmıştır; T3-HUMAN yapılmamış, akademik gold etiket yoktur. QA uyarıları 7.412→4.926 düşse de anlamsal sadakat otomatik ispatlanamaz. Macro-F1 farkları bu **belirli sözlüksel temsil, etiket aktarımı ve 15 Test-UQ soru kümesi** ile sınırlıdır; eğitimsel nedensellik iddia edilmez. Yalnız Test-UQ performansına bakarak yeni hiperparametre/kurallar seçilmez. Önce üç varyantın çıktıları ve soru-kümesi güven aralıkları ayrı araştırma raporuna işlenir.
