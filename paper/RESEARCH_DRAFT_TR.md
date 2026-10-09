# StudentContextNLP v0.1 — Akademik çalışma durumu

**Türkçe başlık:** Öğrenci Açıklamalarındaki Anlamsal ve Bağlamsal Tutarsızlıkların Sınıflandırılmasında Soru Bağlamının Etkisi.

**İngilizce başlık:** The Effect of Question Context on Classifying Semantic Inconsistencies in Student Explanations.

> **SONUÇ DURUMU: BEKLENİYOR.** Kaynak kodu ve sentetik GitHub CI testi vardır. Gerçek SciEntsBank veri denetimi, model eğitimi ve bilimsel skorlar henüz gerçekleştirilmemiştir.

## Araştırma sorusu

Öğrenci açıklamasına soru bağlamı eklemek, yeni sorulara genellemede dört sınıflı Macro-F1 performansını değiştirir mi?

- Birincil karşılaştırma: Δ_Q = Macro-F1(B2, Test-UQ) − Macro-F1(B1, Test-UQ).
- İkincil karşılaştırma: S2−S1 (yerel, dondurulmuş MiniLM).
- H0: Δ_Q=0; H1: Δ_Q≠0. Model girdisi ablasyonudur; öğrencide öğrenme etkisi değildir.

## Deney matrisi

| ID | Girdi | Model |
|---|---|---|
| B0 | Özellik yok | Majority class |
| B1 | Yalnız açıklama | TF-IDF + Logistic Regression |
| B2 | Açıklama + soru | TF-IDF + Logistic Regression |
| B3 | Yalnız soru | TF-IDF + Logistic Regression |
| S1 | Yalnız açıklama | Yerel MiniLM embedding + Logistic Regression |
| S2 | Açıklama + soru | Yerel MiniLM embedding + Logistic Regression |

Veri: SciEntsBank, beş özgün sınıftan dört türetilmiş sınıfa dönüşüm. Train içinde soru gruplarıyla validation; birincil bağımsız test: Test-UQ. İkincil: Test-UA, Test-UD. Soru kümelerine dayalı eşleştirilmiş bootstrap güven aralığı, sınıf bazlı F1 ve hata analizi.

## Gerçek sonuçlar için kilitli alanlar

| Sonuç | Değer |
|---|---|
| P0 veri denetimi | BEKLENİYOR |
| Test-UQ B1 Macro-F1 | BEKLENİYOR |
| Test-UQ B2 Macro-F1 | BEKLENİYOR |
| Δ_Q ve %95 GA | BEKLENİYOR |
| S1/S2 sonuçları | BEKLENİYOR |
| Etiket, tekrar ve sızıntı uyarıları | BEKLENİYOR |

**Gerçek olmayan demo skorları bilimsel sonuç sayılmaz.** Kaynak dosyalar ve model ağırlıkları repoya eklenmeyecek. API key / LLM API / bulut inference / büyük model eğitimi olmayacak.

## Çalışmanın sınırları

Sınıflandırılan etiket öğrencinin kalıcı zihinsel yanlış kavramasının kanıtı değildir. Other kategorisi iki heterojen etiketi birleştirir. Referans cevap ana model girdisinde yoktur. Fen/İngilizce veri sonuçları Türkçe veya diğer derslere otomatik genellenmez. Türkçe etiketli veriyle eğitim v0.2 ayrı çalışmasıdır.

## Yarışma hedefi — TEKNOFEST 2242 Eğitim

- **Ana yarışma:** 2242 Üniversite Öğrencileri Araştırma Proje Yarışmaları, **Eğitim** kategorisi. Bu, 2209-A gibi araştırma destek başvurusu değildir.
- **Durum:** 2026 yarışması tamamlandı. Yeni dönem (muhtemel 2027) takvim ve uygunluk koşulları açıklanana kadar hazırlanacak materyaller yalnız taslaktır.
- **Başvuru araştırma raporu:** `paper/COMPETITION_2242_EDUCATION_TR.md`. Resmî 2026 rehberinde özet 150–300 kelime, PDF raporu 2–20 sayfa, yazılım kodu ek olarak öngörülmüştür. Yeni yıl rehberiyle teyit gereklidir.
- **Ön koşullar:** Gerçek SciEntsBank P0 denetimi, B0–B3 sonuçları ve doğrulanmış model karşılaştırması olmadan nihai yarışma raporu hazırlanmış sayılmaz.
- **Gelecek:** Türkçe veri ile v0.2 ayrı araştırma uzantısı; mevcut sonuçları varmış gibi göstermeyeceğiz.

## Kaynaklar

1. Dzikovska vd., 2013, SemEval Task 7 — https://aclanthology.org/S13-2045/
2. Reimers & Gurevych, 2019, Sentence-BERT — https://aclanthology.org/D19-1410/
3. SciEntsBank veri kartı — https://huggingface.co/datasets/nkazi/SciEntsBank
4. TÜBİTAK 2209-A 2026 — https://tubitak.gov.tr/tr/burslar/lisans-onlisans/destek-programlari/2209-universite-ogrencileri-arastirma-projeleri-destekleme-programi

**Sonraki tek teknik görev:** Windows üzerinde depo/test ortamını çalıştırmak, ardından P0 gerçek veri indirmesi ve audit çıktısını incelemek.
