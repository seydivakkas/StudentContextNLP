# TEKNOFEST 2242 — Eğitim Kategorisi | StudentContextNLP

> **Durum:** GELECEK ÇAĞRIYA HAZIRLIK TASLAĞI. 2026 başvuruları kapanmıştır; 2027 yarışma takvimi ve resmî rapor şablonu henüz teyit edilmemiştir. Bu belge 2026 2242 rehberiyle uyumlu bir çalışma planıdır, resmî başvuru formu değildir. Gerçek SciEntsBank sonuçları henüz yoktur.

**Türkçe başlık:** Öğrenci Açıklamalarındaki Anlamsal Tutarsızlıkların Sınıflandırılmasında Soru Bağlamının Etkisi.

**Ana alan:** Eğitim. **Önerilen tematik alan:** E-Öğrenme (yeni çağrıda doğrulanacak). Teknik yaklaşım: makine öğrenmesi / doğal dil işleme.

## Araştırma problemi
Soru metnini öğrenci açıklamasına eklemek, eğitim sırasında hiç görülmemiş soruların dört sınıflı anlamsal değerlendirmesinde Macro-F1 skorunu değiştiriyor mu?

**Birincil fark:** ΔQ = Macro-F1(B2, Test-UQ) − Macro-F1(B1, Test-UQ). H0: ΔQ=0; H1: ΔQ≠0.

## Tasarım
- **Veri:** SciEntsBank, train + test_ua + test_uq + test_ud. P0 aşamasında şema, etiket, tekrarlar, çelişkiler, normalize soru çakışmaları ve SHA-256 denetlenir.
- **Türetilmiş dört sınıf:** Correct, Incomplete, Contradictory, Other (= irrelevant + non_domain). Kaynak beşli etiketler de saklanır.
- **B0:** çoğunluk sınıfı; **B1:** yalnız açıklama, TF-IDF + Logistic Regression; **B2:** açıklama+soru, TF-IDF + LR; **B3:** yalnız soru, TF-IDF + LR.
- **S1/S2:** dondurulmuş yerel MiniLM temsilleriyle yalnız açıklama / açıklama+soru ve eğitilen Logistic Regression.
- **Değerlendirme:** train içi question-grouped validation; bağımsız birincil Test-UQ; ikincil Test-UA/Test-UD; Macro-F1, sınıf F1, confusion matrix, soru kümeli eşleştirilmiş bootstrap, CPU maliyeti.
- **Etik/teknik:** API key, LLM API, uzaktan inference, büyük LLM eğitimi, RAG veya ajan yoktur. Gizli referans yanıtı ana modelin girdisi değildir. Sentetik test skorları bilimsel sonuç olarak gösterilmez.

## 2026 yarışma rehberindeki rapor bölümleri

1. Giriş: amaç, eğitim değeri, literatür ve özgünlük sınırları.
2. Yöntem ve Teknikler: veri, modeller, deney protokolü, değerlendirme, iş-zaman çizelgesi.
3. Bulgular: **GERÇEK VERİ DENEYLERİ BEKLENİYOR**. Buraya P0 ve gerçek B0–S2 sonuçları eklenecek.
4. Sonuç ve Tartışma: yalnız deneylerden sonra yazılacak; kısıtlar açıkça ifade edilecek.
5. Öneriler: Türkçe gerçek öğrenci açıklamalarıyla v0.2.
6. Kaynaklar: SciEntsBank/SemEval, Sentence-BERT, yarışma resmî rehberi.
7. Ekler: doğrulanmış kod sürümü, deney konfigürasyonu, gerçek test artefaktları.

**2242 2026 koşulları:** Ön lisans/lisans statüsü başvuru esnasında sürmeli; en çok beş öğrenci; danışman isteğe bağlı. Özette 150–300 kelime, proje raporu PDF biçiminde 2–20 sayfa istenmişti; kod ek belge olarak sunulur. Önceden yarışmaya sunulmuş ya da aynı fikrin başka yarışmaya başvurusu gibi hususların uygunluğu yeni çağrıda tekrar doğrulanmalıdır.

**Özgünlük beyanı:** Dünyada ilk öğrenci cevabı sınıflandırma yöntemi iddia edilmiyor. Katkı, bağlam ablasyonu + yalnız-soru kontrolü + bağımsız soru genellemesi + tamamen yerel CPU tekrarlanabilirliğinin bir arada deneyle değerlendirilmesidir. Yayımlanabilirlik ve yarışma başarısı henüz kanıtlanmamıştır.

## Adım adım teknik kapılar

| Kapı | Kanıt | Durum |
|---|---|---|
| C1 | GitHub kod + sentetik CI | PASS (9 Ekim 2026 CI) |
| P0 | Dört gerçek Parquet dosyası + `reports/P0_audit.md` | BEKLENİYOR |
| P1 | B0–B3 gerçek Macro-F1 + ΔQ + %95 GA | BEKLENİYOR |
| P2 | S1–S2 gerçek MiniLM koşulları, CPU maliyeti | BEKLENİYOR |
| P3 | Son rapor, görseller, sunum / başvuru kanıtları | BEKLENİYOR |

## Kaynaklar
- [2242 TEKNOFEST yarışma sayfası](https://www.teknofest.org/tr/yarismalar/universite-ogrencileri-arastirma-proje-yarismalari/)
- [2026 proje rehberi (PDF)](https://cdn.teknofest.org/media/upload/userFormUpload/2242_%C3%BCniversite_proje_rehberi_2025-2026_OBW7i.pdf)
- [TÜBİTAK 2242 çağrı bilgisi](https://tubitak.gov.tr/en/competitions/2242-university-students-research-project-competitions)
- [SciEntsBank](https://huggingface.co/datasets/nkazi/SciEntsBank)
- [SemEval-2013 Task 7](https://aclanthology.org/S13-2045/)

Not: Proje yarışmasında kullanıcıya dönük uygulama şartı varsayılmamalı; geçerli yeni çağrının alan, tema ve belge koşulları esas alınacaktır.
