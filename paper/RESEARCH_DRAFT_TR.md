# StudentContextNLP v0.1/v0.2 — Gerçek Araştırma Kaydı

**Sabit proje başlığı:** Öğrenci Açıklamalarının Soru Bağlamına Duyarlı Anlamsal Değerlendirilmesi: Türkçe Veri Uyarlaması ve Diller Arası Karşılaştırmalı Analiz.

**Yarışma hedefi:** TEKNOFEST 2242 Eğitim kategorisi, gelecek çağrı değerlendirmesine hazırlık. Bu belge nihai yarışma raporu değildir.

## Araştırma soruları

1. Soru metni eklenmesi, görülmemiş soru kümeleri üzerinde dört sınıflı Macro-F1'i değiştiriyor mu?
2. v0.2'de İngilizceden Türkçeye aktarım, öğrenci açıklamasının anlamını ve özgün hatalı yanıt/etiket niteliğini hangi sıklıkla koruyor? İki dilde soru bağlamı ablasyonu nasıl farklılaşıyor?

**Birincil ön kayıtlı deney:** Δ = Macro-F1(B2, Test-UQ) − Macro-F1(B1, Test-UQ). H0: Δ=0; H1: Δ≠0. Bir eğitim müdahalesinin nedensel etkisi değildir.

## Modeller

| ID | Girdi | Temsil / öğrenici |
|---|---|---|
| B0 | Metin özelliği yok | Majority class |
| B1 | Yalnız öğrenci açıklaması | Kelime + karakter TF-IDF; Logistic Regression |
| B2 | Açıklama ve soru birlikte | Aynı TF-IDF tasarımı; Logistic Regression |
| B3 | Yalnız soru | Aynı TF-IDF tasarımı; Logistic Regression |
| S1 | Yalnız açıklama | Yerel dondurulmuş MiniLM + Logistic Regression |
| S2 | Açıklama + soru | Yerel dondurulmuş MiniLM + Logistic Regression |

Sabit veri: SciEntsBank (İngilizce), 4 türetilmiş sınıf: Correct, Incomplete, Contradictory, Other. Yalnız eğitim verisinde soru gruplu validation ve C∈{0.1,1,10}; birincil Test-UQ; ikincil Test-UA ve Test-UD. Referans açıklama hiçbir ana sınıflandırıcının girdisi değildir.

## P0 — Gerçek veri incelemesi

**Kaynak:** Kullanıcının 10 Ekim 2026 tarihli Windows çıktıları; ham veri, SHA-256 değerleri, eğitim artefaktları yalnız yerel makinede tutuluyor. GitHub bu veri dosyalarını kendi başına yeniden çalıştırmadı.

- Dört Parquet dosyasının SHA-256 değerleri indirilen dosya manifestiyle kullanıcının yerel Python kontrolünde uyuştu.
- 10.804 satır, tüm bölümlerde 195 benzersiz normalize soru, resmi dağılımlarla eşleşen beşli sınıf sayıları.
- **P0 status: PASS_WITH_WARNINGS, fatal=0.** Train: altısı da dört sınıfa aktarıldığında süren 6 çelişkili üçlü / 15 satır. Test-UD: 1 çelişkili üçlü / 6 satır. Test-UA: train ile 24 ortak normalize üçlü.
- **Test-UQ train ortak soru=0, ortak üçlü=0;** 15 soru kümesi ve 733 öğrenci açıklaması. Test-UQ içinde 30 ilave tekrar kaydı.
- Araştırmacı yerelde `reports/P0_DECISION.md` yazıp uyarıları kaydetti; ana deneyde hiçbir etiket değiştirilmedi. Daha sonra etiket çatışması / yinelenen satır duyarlılık analizi planlanmıştır.
- Ayrıntılar: [P0 gerçek veri denetimi](P0_REAL_DATA_AUDIT_2026-10-10.md).

## P1 — Gerçek SciEntsBank Test-UQ sonuçları (10 Ekim 2026)

**Kanıt türü:** Kullanıcı, gerçek yerel `train_lexical.py` çıktısını aktardı; `results/lexical/baseline_results.json`, `selection_before_test.json` ve tahmin dosyaları GitHub'a yüklenmedi. Dolayısıyla sayılar *kullanıcının yerel deney raporudur*, GitHub CI'nin doğruladığı bilimsel skorlar değildir.

| Model | Test-UQ Macro-F1 |
|---|---:|
| B0 — Çoğunluk sınıfı | 0.1455512572533849 |
| B1 — Açıklama | 0.2950231314934188 |
| B2 — Açıklama+soru | 0.2405991832538969 |
| B3 — Soru | 0.17017237841165606 |

- **Ön kayıtlı Δ(B2−B1): −0.0544239482395219** (−5,44 Macro-F1 yüzde puanı).
- **%95 tanımlayıcı, eşleştirilmiş soru-kümesi bootstrap yüzdelik aralığı:** [−0.10254558393043693, −0.006910099256588127]; **15 soru kümesi**, **1.000** bootstrap yinelemesi.
- **Yorum:** Bu *özel TF-IDF + LR temsilinde* soru metninin eklenmesi, görülmemiş sorularda performansı düşürdü. Bu, soru bağlamının genel olarak faydasız olduğunu veya başka modellerde de aynı sonucun alınacağını kanıtlamaz. B3 düşüklüğü, sorunun tek başına yeterli bir kestirim girdisi olmadığını bu deneyde destekler.
- **Sınırlılıklar:** Sadece 15 bağımsız soru; 30 Test-UQ tekrar kaydı; train etiket çelişkileri; Other heterojen sınıfı; sınıf dengesizlikleri. Tek bootstrap yöntemi ve bu küçük soru sayısı, güçlü genelleme/istatistiksel kesinlik iddiasına yetmez.
- **Araştırmanın devamı:** Per-class F1/karışıklık matrisi, tekrar/çelişki duyarlılık analizi, validasyon skorları, CPU maliyeti. Bu analizlerde resmi Test-UQ'ya göre yeniden hiperparametre seçimi **yapılmayacak**.

## P2 — Türkçe veri uyarlaması: 10.804 aday çeviri tamamlandı (10 Ekim 2026)

Araştırmacının Windows bilgisayarında, yerel Argos EN→TR modeliyle dört SciEntsBank bölümünün tamamı (10.804/10.804) **makine çevirisi adayı** olarak üretildi. Kurulu model SHA-256'sı `2d553a00880a0c21dea5b1c375535659e6bf18c9bf2ce9847c2a2fd2ff50316a` olarak kaydedildi. Kaynak/hedef kayıt sırası, `id` ve özgün etiketler 4/4 splitte eşleşti.

| Bölüm | Aday satır | Otomatik kalite uyarısı bulunan satır |
|---|---:|---:|
| Train | 4.969 | 1.315 |
| Test-UA | 540 | 153 |
| Test-UQ | 733 | 258 |
| Test-UD | 4.562 | 1.097 |
| **Toplam** | **10.804** | **2.823 (%26,1)** |

Çeviri statüsü **`FULL_CANDIDATE / UNVERIFIED_MACHINE_TRANSLATION`** ve aktarılan etiketler **`UNVERIFIED_TRANSFER`** olarak korundu. Uyarılar anlamsal hata kanıtı veya çevirinin güvenilirlik oranı değildir. Ayrıntılı üretim ve bilimsel sınır raporu: [T2 çeviri kaydı](T2_REAL_TR_TRANSLATION_2026-10-10.md).

**T3.0 (11 Ekim 2026) tamamlandı:** Araştırmacı `seed=20261010` ile **240 benzersiz satırlık** örneklem üretti, her bir splitten 60 ve her türetilmiş sınıftan 60 örnek alındı. Örneklemde **73 otomatik kalite bayraklı** aday bulunmaktadır. `review_A.csv`, `review_B.csv`, `review_manifest.json` yerel makinede oluşturuldu; iki bağımsız insanın inceleme yanıtları henüz yoktur. Sınıfa/kalite bayrağına kör aşama-1 formları üretmek için `prepare_blinded_reviews.py` ve [iki aşamalı protokol](../docs/TR_REVIEW_PROTOCOL_T3.md) eklendi. T3 insan doğrulaması bitmeden Türkçe altın standart veya bilimsel Türkçe Macro-F1 ilan edilmez.

## T3-AUTO — İnsan değerlendirmesi olmadan yerel çeviri hata ön taraması (11 Ekim 2026)

**Protokol güncellemesi:** Araştırmacı şu aşamada gerçek iki bağımsız insanın değerlendirmesini istemiyor; bu nedenle **T3-HUMAN = NOT_PERFORMED**. Bunun yerine İngilizce–Türkçe kaynak/aday çiftleri için asistan destekli niteliksel inceleme ve tamamen çevrimdışı deterministik kontrol motoru eklendi: [TR_AUTOMATED_QA_T3.md](../docs/TR_AUTOMATED_QA_T3.md). Veri/etiket kaydı ve orijinal A/B dosyaları değişmedi.

Asistanın kullanıcı tarafından yüklenen 240 farklı kayıt üzerinde yerel tarama çıktısı:

| Denetim | Kayıt |
|---|---:|
| Yüksek öncelikli şüpheli | 47 |
| Orta öncelikli şüpheli | 61 |
| Kuralca işaretlenmeyen | 132 |
| **İnceleme adayı toplamı** | **108/240** |
| Hücre düzeyi kural tetiklenmesi | 210 |

Tespit edilen somut hata türlerine örnekler: `calcite` → `analiz`, `bulb` → `otobüs`, `nail` → `tırnak`, `pots` → `tencere`, `solid` → `sağlam`, `fogged up` → `parlak`, `square` → `meydan okuyorlar`. Bu örnekler kaynak metinlerle karşılaştırılarak incelendi; toplu 108 adedin tamamı doğrulanmış yanlış çeviri **değildir**. Sistem kural kaçırabilir (false negative) ve yanlış alarm verebilir (false positive). **Doğruluk oranı, iki uzman arası Cohen kappa veya Türkçe gold etiket iddia edilmiyor.**

İnsan kalite doğrulaması olmadan **T4'te** elde edilecek Türkçe karşılaştırmalar yalnız *projected-label exploratory proxy experiment* şeklinde sunulabilir; bağımsız Türkçe öğrenci verisinde doğrulama olarak sunulamaz.

### T3-AUTO v0.2 — Yeni bilimsel anlam koruma kontrolleri

Önceki 108/240 sonuçları **v0.1**, aynı 240 yerel yükleme üzerinde asistan tarafından yeniden çalıştırılan ek olumsuz kavram/birim kontrolleri ise **v0.2** sürümüdür. Güncel v0.2 ön tarama: **112/240 aday**, **53 HIGH**, **59 MEDIUM**, **128 kuralca işaretlenmeyen** ve **220 hücre-kural tetiklenmesi**. Yeni kurallar `SATURATION_POLARITY_REVERSED` (ör. *saturated→doymamış*) ve `MILLILITER_AS_LITER` (ör. *100 milliliters→100 litre*) için toplam 10 ek alan bulgusu üretti. Tekrarlanan soru/cevaplar nedeniyle bu sayı 10 bağımsız hata örneği anlamına gelmez.

Ayrı `propose_translation_corrections.py` aracı yalnız **etiketsiz, geri alınabilir kavram düzeltme önerileri** oluşturur; kaynak veriye, makine çevirisine veya insan inceleme formuna yazmaz. **Hiçbir satır otomatik düzeltilmedi, hiçbir insan değerlendirici/altın standart kararı üretilmedi.** Güncel çıktılar kullanıcının kendi Windows bilgisayarında tekrar çalıştırılmayı bekliyor. Ayrıntılar: [T3-AUTO protokolü](../docs/TR_AUTOMATED_QA_T3.md).

### T3-AUTO v0.3 — Kaynak kavrama göre gruplanmış örnek ve tam veri tarama motoru

Asistan, kullanıcı tarafından yüklenen **aynı 240 kör İngilizce–Türkçe çifti** üzerinde v0.2 kurallarını yeniden çalıştırıp kaynak kavramı bazında sınıflandırdı. Olumsuzluk: **56 tetiklenme / 54 ayrı kayıt / 37 ayrı alan–kaynak–hedef çift**; İngilizce kalan terimler: **41 / 23 / 22**; `bulb`: **21 / 11 / 8**; sayılar: **17 / 17 / 10**; `solid`: **11 / 10 / 7**; `calcite`: **10 / 3 / 7**; mililitre/litre: **8 / 8 / 6**. Bunlar insan tarafından doğrulanmış hata adedi veya gerçek çeviri hata oranı değildir.

Yeni `audit_translation_corpus.py` modülü tüm **10.804** kayıt için orijinal Parquet/SHA ve çeviri manifestlerini denetleyip aynı kontrolleri soru, referans ve öğrenci açıklamasında çalıştırır; kaynak kavramı/grup/tekrar sayımlarını birbirinden ayırır. Tam veri denetimi araştırmacının Windows sisteminde **11 Ekim 2026'da tamamlandı**. Ayrıntılı yöntem ve kullanım: [T3 tam korpus QA](../docs/TR_FULL_CORPUS_QA_T3.md). İlk sentetik tam-kapsam regresyon testleri GitHub CI'de PASS; bu bir gerçek veri doğrulaması değildir.

### T3-AUTO tam gerçek korpus taraması — 11 Ekim 2026

Araştırmacının Windows ortamında **49/49** yazılım regresyon testi geçti; İngilizce ve Türkçe kaynak manifestlerinin SHA-256 ve 240 donmuş örnek eşleştirmesi doğrulandı. Toplam **10.804/10.804** satır tarandı: **1.930 HIGH**, **2.278 MEDIUM** uyarılı kayıt, **6.596 kuralca işaretlenmeyen** kayıt ve toplam **7.412** metin alanı/kural bulgusu.

Farklı kaynak kavram: **28**. Tekrarlanan kural/metin kanıt grubu: **155**. En sık kavramlar: olumsuzluk 2.081 tetiklenme / 1.952 farklı kayıt / 576 farklı alan–metin; `bulb` 655 / 306 / 81; mililitre 397 / 391 / 66; eğim 346 / 283 / 23. Bu sayılar doğrulanmış çeviri hataları değildir ve toplandıklarında tekil hatalı satır sayısını vermez. Gerekçeli tam gerçek veri kaydı: [T3_FULL_CORPUS_REAL_2026-10-11.md](T3_FULL_CORPUS_REAL_2026-10-11.md).

Bunu izleyen `prioritize_translation_issues.py` kök neden modülü, tekrar eden kural tetiklenmelerini **kavram/alan/kaynak–hedef metin** anahtarına göre birleştirir; anlam tersine dönüşü, özgül yanlış terim ve diğer yüzeysel şüpheleri ayrı sıraya koyar. Tam 10.804 satırın bu yeni önceliklendirme aşaması henüz Windows üzerinde çalıştırılmadı. **T3-HUMAN yapılmadı, altın standart ve insan uyumu iddiası yoktur.**

### T3-AUTO v0.4 — Gerçek tekrar grupları ve v0.2.1 tasarım kapısı (11 Ekim 2026)

Araştırmacının Windows çıktısında **53/53 regresyon testi PASS**, tam 10.804 kayıt/7.412 kural bulgusundan **1.460 kavram+alan+kaynak/hedef kök neden adayı** ve 147 tekrar eden küme hesaplandı; **28 farklı kavram**, otomatik değiştirilen satır **0**. Mililitre kavramı 391 ayrı kayıt/66 farklı metin eşleşmesi; doygunluk 39 kayıt/2 eşleşme. Bunlar kesin hata sayıları değil, tekrar içeren şüpheli çeviri kümeleridir. Kaynak kümelemeye ilişkin bilimsel öncelik, gerçek hata olasılığı olarak yorumlanmayacaktır. [Gerçek tam veri kaydı](T3_FULL_CORPUS_REAL_2026-10-11.md).

**v0.2.1 hazırlığı (kod tamamlandı, gerçek veri henüz oluşturulmadı):** [Sürümleme ve düzeltme kanıt protokolü](../docs/TR_PATCH_LAYER_V021.md) geliştirildi. `prepare_translation_patch_plan.py` P1/P2 tekrar eden kaynak metin eşleşmeleri için **boş düzeltme şablonu** üretir; `apply_translation_patch_plan.py` yalnız `APPLY_EXPLORATORY` olarak açıkça belirlenmiş, tam metin + gerekçeli, SHA kanıtı ile eşleşen önerileri *yeni* `data/tr_v0_2_1/` aday sürümünde uygulayabilir. AI önerileri `AI_DRAFT` statüsünde kalır, gold veya iki insanın değerlendirmesi değildir. Henüz gerçek v0.2.1 metni değiştirilmedi; P1 İngilizce baseline etkilenmedi.

### T3-AUTO v0.5 — Gerçek Windows kök neden patch-plan kabulü (11 Ekim 2026)

Araştırmacının Windows ortamında **58/58 regresyon testi PASS**, `reports/tr_patch_plan_v021` içinde **39 uygun tekrarlanan P1/P2 kümesinden 37 tekil düzeltme plan adayı** üretildi. `milliliter` kavramında 7, `solid` 10, `bulb` 7, `evaporate` 4, `fogged_glass` 2, `plant_pot` 2 ve diğer kavramlarda adaylar bulunuyor. En büyük tekil plan adayı kaynak soru çevirisi 100 kaydı ilgilendiriyor. **Bu adaylar doğrulanmış çeviri hataları değildir**; `decision=PENDING` ve düzeltme metni boş, uygulanan değişiklik 0. Hiçbir insan uzman değerlendirmesi ya da Türkçe gold etiketi üretilmedi. [v0.2.1 öneri/uygulama protokolü](../docs/TR_PATCH_LAYER_V021.md).

### SciEntsBank-TR v0.2.1 — AI_DRAFT uygulama ve tam-korpus karşılaştırmalı kalite kapısı (11 Ekim 2026)

Araştırmacının yüklediği 37 P1/P2 kaynak–hedef çeviri adayından oluşturulan özel `AI_DRAFT` paketinde 34 açık `APPLY_EXPLORATORY`, 3 belirsiz `PENDING` önerisi vardır. Özgün donmuş düzeltme planı, veri v0.2 korpusu, A/B insan değerlendirme dosyaları değiştirilmez. Bu araştırma kapsamında **insan doğrulaması, gerçek Türkçe gold veri veya Cohen kappa bulunmamaktadır**.

Yeni çevrimdışı kod (`import_ai_draft_patch.py`, `compare_translation_versions.py`): (1) ZIP içindeki özel metinleri GitHub'a koymadan manifest SHA-256, 37 değişmez kanıt alanı ve 34/3 karar kontrolü ile ayrı bir yerel AI_DRAFT planı üretir; (2) mevcut `apply_translation_patch_plan.py` yalnız kanıta bağlı, tam cümle ve açık gerekçeli önerilerle **ayrı** `data/tr_v0_2_1/` oluşturmayı dener; (3) yeni ve eski 10.804 satırın üç metin alanında 7.412 özgün QA kural bulgusunu yeniden üretme, İngilizce kaynak/`id`/etiket değişmezliği, birebir uygulama kanıtı ve eklenen yüksek öncelikli uyarı denetimleri çalıştırır. Sonuçlar `reports/tr_compare_v021/` altında yalnız yerel tutulur. [Uygulama/kabul protokolü](../docs/TR_V021_REAL_DRAFT_APPLY_COMPARE.md).

**Gerçek 10.804 satırlık v0.2.1 uygulaması ve karşılaştırmalı QA, araştırmacının Windows bilgisayarında 11 Ekim 2026'da çalıştırıldı; teknik kapı PASS.** 64/64 yazılım regresyon testi, AI_DRAFT SHA ve tüm orijinal kaynakların SHA bütünlüğü PASS. 34 tam eşleşme önerisi yeni sürümde uygulandı, 3 belirsiz aday bekletildi; 1.604 farklı kaydın 1.748 Türkçe alan örneği değişti. Toplam heuristik kural tetiklenmesi **7.412→4.926** (−2.486; −%33,54), yeni HIGH kural regresyonu **0**. Bu, çeviri semantiğinin doğruluğunun bağımsız kabulü değildir. **Orijinal İngilizce kaynak/etiketler ve eski v0.2 aday veri değişmedi; `UNVERIFIED_TRANSFER` korunur.** Teknik sınırlar ve splitler: [gerçek v0.2.1 karşılaştırma kabulü](../docs/TR_V021_REAL_DRAFT_APPLY_COMPARE.md).

## Araştırma etiği ve yeniden üretilebilirlik

- Sentetik smoke sonuçları akademik tabloya alınmaz. API anahtarı, LLM API, bulut model inference, RAG, agent, büyük dil modeli fine-tuning yoktur.
- Ham metinler, kaynak Parquet dosyaları, çeviri cache'leri, model ağırlıkları ve öğrenci satırı düzeyindeki tahminler GitHub'a konmaz; GitHub'da yalnız kaynak kod, toplu istatistik ve araştırma kayıtları.
- SciEntsBank kaynak verisi beş etiketlidir; dört-sınıf yeniden eşleştirmesi özgün etiketi yok etmez. Veri lisansı ve çeviri model lisansı ayrı değerlendirilmelidir.

## Kaynaklar

1. Dzikovska vd. (2013), SemEval Task 7 — https://aclanthology.org/S13-2045/
2. Reimers & Gurevych (2019), Sentence-BERT — https://aclanthology.org/D19-1410/
3. SciEntsBank dataset — https://huggingface.co/datasets/nkazi/SciEntsBank
4. TEKNOFEST 2242 — https://www.teknofest.org/tr/yarismalar/universite-ogrencileri-arastirma-proje-yarismalari/

**Sonraki teknik görev:** v0.2 ve v0.2.1 gerçek kayıtlarında değişiklik/kural dağılımı analizi; ardından aynı veri bölümleri ve sabit sınıf eşlemesiyle Test-UQ üzerinde İngilizce/Türkçe B0–B3 karşılaştırmalı *exploratory projected-label proxy* deneyleri. Q-gruplu güven aralığı ve veri sızıntısı denetimleri zorunlu. T3-HUMAN `NOT_PERFORMED`; Türkçe gold etiketi iddia edilmez.
