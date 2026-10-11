# TEKNOFEST 2242 — Eğitim Kategorisi | StudentContextNLP

> **Durum:** GELECEK ÇAĞRIYA HAZIRLIK TASLAĞI. 2026 başvuruları kapanmıştır; 2027 yarışma takvimi ve resmî rapor şablonu henüz teyit edilmemiştir. Bu belge 2026 2242 rehberiyle uyumlu bir çalışma planıdır, resmî başvuru formu değildir. P0 ve ilk gerçek İngilizce B0–B3 Test-UQ sonuçları 10 Ekim 2026'da araştırmacının Windows ortamında üretildi. Türkçe 10.804 aday kaydın yerel çevirisi tamamlandı; insan doğrulaması ve S1/S2 sonuçları henüz yoktur.

**Türkçe başlık:** Öğrenci Açıklamalarının Soru Bağlamına Duyarlı Anlamsal Değerlendirilmesi: Türkçe Veri Uyarlaması ve Diller Arası Karşılaştırmalı Analiz.

**Ana alan:** Eğitim. **Önerilen tematik alan:** E-Öğrenme (yeni çağrıda doğrulanacak). Teknik yaklaşım: makine öğrenmesi / doğal dil işleme.

## Araştırma problemi
Soru metnini öğrenci açıklamasına eklemek, eğitim sırasında hiç görülmemiş soruların dört sınıflı anlamsal değerlendirmesinde Macro-F1 skorunu değiştiriyor mu?

**Birincil fark:** ΔQ = Macro-F1(B2, Test-UQ) − Macro-F1(B1, Test-UQ). H0: ΔQ=0; H1: ΔQ≠0.

**İkincil araştırma sorusu (v0.2):** Makine çevirisinin öğrenci açıklamasındaki doğru/eksik/çelişkili/diğer etiketini ve bilimsel hatanın niteliğini koruma oranı nedir? İngilizce ve aktarılmış Türkçe örneklerde bağlam kazancı nasıl değişir? Bu fark tek başına dilin nedensel etkisi değildir.

## Tasarım
- **Veri:** SciEntsBank, train + test_ua + test_uq + test_ud. P0 aşamasında şema, etiket, tekrarlar, çelişkiler, normalize soru çakışmaları ve SHA-256 denetlenir.
- **Türetilmiş dört sınıf:** Correct, Incomplete, Contradictory, Other (= irrelevant + non_domain). Kaynak beşli etiketler de saklanır.
- **B0:** çoğunluk sınıfı; **B1:** yalnız açıklama, TF-IDF + Logistic Regression; **B2:** açıklama+soru, TF-IDF + LR; **B3:** yalnız soru, TF-IDF + LR.
- **S1/S2:** dondurulmuş yerel MiniLM temsilleriyle yalnız açıklama / açıklama+soru ve eğitilen Logistic Regression.
- **Değerlendirme:** train içi question-grouped validation; bağımsız birincil Test-UQ; ikincil Test-UA/Test-UD; Macro-F1, sınıf F1, confusion matrix, soru kümeli eşleştirilmiş bootstrap, CPU maliyeti.
- **Etik/teknik:** API key, LLM API, uzaktan inference, büyük LLM eğitimi, RAG veya ajan yoktur. Gizli referans yanıtı ana modelin girdisi değildir. Sentetik test skorları bilimsel sonuç olarak gösterilmez.

## Türkçe uyarlama (v0.2) — özgünlük ve sınır

- Tam 4 splitin tüm satırlarına uygulanabilir offline EN→TR çeviri motoru, model ve veri SHA-256 izlenebilirliği.
- Özgün öğrenci hataları düzeltilemez; kaynak ve hedef metinler birlikte saklanır.
- Tüm otomatik etiket aktarımı **UNVERIFIED_TRANSFER**; insan doğrulaması olmadan Türkçe altın standart veya bilimsel skor ilan edilemez.
- **T3.0 örneklemi oluşturuldu:** 240 kayıt; her splitten 60 ve her sınıftan 60, örneklemin 73 satırı sezgisel bayraklı. İki bağımsız değerlendirici için [etiket körü iki aşamalı protokol](../docs/TR_REVIEW_PROTOCOL_T3.md) tanımlandı; insan etiketleri hâlâ bekliyor.
- İlk İngilizce baseline dondurulur; Türkçe sonuçlara yalnız kalite kapısından sonra geçilir. Çevrilmiş İngilizce öğrenci yanıtları, doğal olarak Türkçe yazılmış yanıtları temsil etmez.
- v0.2'nin gerçek yerel EN→TR aday çevirisi 10.804/10.804 satırda tamamlandı; 2.823 kayıt sezgisel kalite incelemesi için işaretlendi. İnsan doğrulaması henüz yapılmadı.

## T3 otomatik kalite ön taraması (11 Ekim 2026)

Araştırmacının yüklediği 240 kör çeviri örneği asistan ortamında [çevrimdışı QA modülü](../audit_translation_quality.py) ile tarandı. 47 yüksek, 61 orta öncelikli **şüpheli çeviri adayı** işaretlendi; 132 kayıt kuralca işaretlenmedi. Toplam 210 hücre bazlı kural bulgusu üretildi. Bu sayıların **hiçbiri doğrulanmış yanlış çeviri adedi, hata oranı veya otomatik doğruluk kanıtı değildir**. Bazı örneklerde açık sözcük anlamı kaymaları görüldü (ör. `bulb` → `otobüs`; `calcite` → `analiz`).

İki bağımsız insan değerlendiriciyle kappa çalışması kullanıcı tercihiyle şu aşamada **yapılmıyor**. Çalışma yönteminde bu bölümün adı **otomatik destekli niteliksel çeviri hata analizi** olarak değiştirildi. Çeviri kaynaklarından aktarılan etiketler yine `UNVERIFIED_TRANSFER` durumunda; Türkçe altın standart yoktur. Ayrıntılı bilimsel sınırlar: [T3 otomatik QA protokolü](../docs/TR_AUTOMATED_QA_T3.md). Türkçe model kıyaslamaları yapılırsa bunlar yalnızca projeksiyon etiketli **exploratory proxy** deneyler olarak raporlanacaktır.

## P1 bulguları — 10 Ekim 2026 gerçek SciEntsBank Test-UQ

**Kaynak:** Araştırmacının Windows'ta çalıştırdığı `train_lexical.py` terminal çıktısı. Ham veriler ve tahmin kayıtları yerelde saklanmaktadır; GitHub Actions gerçek veri deneyini çalıştırmadı. `reports/P0_DECISION.md` ile uyarıların koşullu kabulü kaydedildi. Test-UQ: 733 öğrenci yanıtı ve 15 görülmemiş soru.

| Baseline | Test-UQ Macro-F1 |
|---|---:|
| B0 — çoğunluk sınıfı | 0.145551 |
| **B1 — yalnız açıklama** | **0.295023** |
| B2 — açıklama + soru | 0.240599 |
| B3 — yalnız soru | 0.170172 |

Önceden tanımlanan ana fark **B2−B1 = −0.054424** (−5,44 yüzde puan); soru kümesi bazlı eşleştirilmiş bootstrap yüzdelik **%95 GA [−0.102546; −0.006910]**, 1.000 tekrar, 15 küme. Bu sonuç, kullanılan **TF-IDF + Logistic Regression temsilinde soru eklemenin fayda yerine ölçülebilir düşüş getirdiğini** gösteriyor. Bağlamın tüm NLP modellerinde zararlı olduğunu veya çeviri sonrası sonucun aynı olacağını iddia etmiyoruz.

Denetim sırasında özgün train'de **6 çelişkili yanıt üçlüsü / 15 satır**, Test-UD'de **1 üçlü / 6 satır** görüldü; Test-UA'da train ile 24 ortak normalize üçlü vardır; Test-UQ'da train ile ortak soru ve ortak üçlü yoktur. Başlangıç veri kümeleri değiştirilmemiştir. Tek bir bootstrap yöntemi, tekrarlar ve 15 soru kümesi nedeniyle genelleme gücü sınırlıdır. Bunların tamamı değerlendirmede açıkça belirtilmelidir.

**Araştırma sonraki adımı:** [T2 gerçek çeviri kaydı](T2_REAL_TR_TRANSLATION_2026-10-10.md) ve tamamlanan T3.0 örneklemesi sonrasında 240 kayıtta iki bağımsız değerlendiricinin kör anlam/bilimsel yanılgı incelemesi, ardından etiket korunumu denetimi. Aktarılan etiketler insan kontrolü olmadan Türkçe altın standart sayılmayacaktır.

## 2026 jüri değerlendirme ölçütlerine kanıt eşlemesi

| Ölçüt | Bu araştırmada jüriye gösterilecek kanıt | Mevcut durum |
|---|---|---|
| Özgünlük/Yenilikçilik | Bağlam ablasyonu, yalnız soru kontrolü, literatürle kontrollü karşılaştırma | İngilizce B0–B3 ölçüldü; TR deneyleri bekleniyor |
| Yöntem ve Süreç | Soru gruplu validation, P0 denetimi, yeniden üretim kaydı | P0 koşullu kabul, B0–B3 yerel ölçüm, CI sentetik PASS |
| Uygulanabilirlik/Kullanılabilirlik | CPU'da gerçek model, süre ölçümü ve çevrimdışı inference | CPU'da B0–B3 eğitildi; gerçek süre analizi ve Türkçe bekleniyor |
| Katma Değer/Yaygın Etki | Yerel Türkçe uyarlama ve uzman etiket kalite incelemesi | Kullanıcı/eğitim etkisi henüz ölçülmedi |

Bu dört ölçüt **2026 çağrı metninden** alınmıştır; ölçütlerin 2027'de aynı kalacağı varsayılmayacaktır.

## 2026 yarışma rehberindeki rapor bölümleri

1. Giriş: amaç, eğitim değeri, literatür ve özgünlük sınırları.
2. Yöntem ve Teknikler: veri, modeller, deney protokolü, değerlendirme, iş-zaman çizelgesi.
3. Bulgular: **Gerçek SciEntsBank P0 ve İngilizce B0–B3 Test-UQ sonuçları aşağıda raporlandı.** S1/S2 ve Türkçe deneyler bekliyor.
4. Sonuç ve Tartışma: yalnız deneylerden sonra yazılacak; kısıtlar açıkça ifade edilecek.
5. Öneriler: Doğal Türkçe öğrenci yanıtlarıyla bağımsız v0.3 genelleme doğrulaması.
6. Kaynaklar: SciEntsBank/SemEval, Sentence-BERT, yarışma resmî rehberi.
7. Ekler: doğrulanmış kod sürümü, deney konfigürasyonu, gerçek test artefaktları.

**2242 2026 koşulları:** Ön lisans/lisans statüsü başvuru esnasında sürmeli; en çok beş öğrenci; danışman isteğe bağlı. Özette 150–300 kelime, proje raporu PDF biçiminde 2–20 sayfa istenmişti; kod ek belge olarak sunulur. Önceden yarışmaya sunulmuş ya da aynı fikrin başka yarışmaya başvurusu gibi hususların uygunluğu yeni çağrıda tekrar doğrulanmalıdır.

**Özgünlük beyanı:** Dünyada ilk öğrenci cevabı sınıflandırma yöntemi iddia edilmiyor. Katkı, bağlam ablasyonu + yalnız-soru kontrolü + bağımsız soru genellemesi + tamamen yerel CPU tekrarlanabilirliğinin bir arada deneyle değerlendirilmesidir. Yayımlanabilirlik ve yarışma başarısı henüz kanıtlanmamıştır.

## Adım adım teknik kapılar

| Kapı | Kanıt | Durum |
|---|---|---|
| C1 | GitHub kod + sentetik CI | PASS (9 Ekim 2026 CI) |
| P0 | Dört gerçek Parquet dosyası + yerel SHA-256 doğrulaması ve koşullu uyarı kaydı | PASS_WITH_WARNINGS; yerel raporda koşullu kabul |
| P1 | B0–B3 gerçek Macro-F1 + ΔQ + %95 GA | Yerel Windows deneyinde tamamlandı; bağımsız yeniden çalışma beklenebilir |
| P2 | S1–S2 gerçek MiniLM koşulları, CPU maliyeti | BEKLENİYOR |
| P3 | Son rapor, görseller, sunum / başvuru kanıtları | BEKLENİYOR |
| T1 | Doğrudan Argos EN→TR model kurulumu ve model SHA-256 | PASS: yerel model, SHA-256 kaydı |
| T2 | Dört gerçek veri splitinde %100 aday çeviri ve denetim manifesti | PASS: 10.804/10.804 aday, 4/4 satır/etiket kontrolü |
| T3 | 240 kayıt üzerinden otomatik destekli çeviri kalite ön taraması; insan uzmanlık doğrulaması ayrı | T3-AUTO: 240/240 tarandı, 108 inceleme adayı; T3-HUMAN NOT_PERFORMED, kappa üretilmeyecek |
| T4 | Kalite eşiğine bağlı Türkçe gerçek benchmark ve dil karşılaştırması | BEKLENİYOR |

## Kaynaklar
- [2242 TEKNOFEST yarışma sayfası](https://www.teknofest.org/tr/yarismalar/universite-ogrencileri-arastirma-proje-yarismalari/)
- [2026 proje rehberi (PDF)](https://cdn.teknofest.org/media/upload/userFormUpload/2242_%C3%BCniversite_proje_rehberi_2025-2026_OBW7i.pdf)
- [TÜBİTAK 2242 çağrı bilgisi](https://tubitak.gov.tr/en/competitions/2242-university-students-research-project-competitions)
- [SciEntsBank](https://huggingface.co/datasets/nkazi/SciEntsBank)
- [SemEval-2013 Task 7](https://aclanthology.org/S13-2045/)

Not: Proje yarışmasında kullanıcıya dönük uygulama şartı varsayılmamalı; geçerli yeni çağrının alan, tema ve belge koşulları esas alınacaktır.
