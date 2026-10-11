# T3-AUTO — İnsan incelemesi olmadan çevrimdışı çeviri kalite ön taraması

**Durum:** 11 Ekim 2026, 240 satırlık T3.0/T3.1 örneklemi üzerinde gerçek kaynak/aday çeviri çiftleri kullanılarak çalıştırılmış kural tabanlı tarama. Bu çalışma iki bağımsız insan değerlendirmesinin yerini tuttuğu iddiasında değildir.

## Araştırma kararı ve kullanılan sınırlı yöntem

Araştırmacı henüz iki bağımsız insan değerlendiricinin incelemesini istemiyor. Bu nedenle **T3-HUMAN: NOT_PERFORMED** olarak kayıt altına alınır; otomatik tarama **T3-AUTO: COMPLETED (TRIAGE ONLY)** olarak ayrı takip edilir. İnsan değerlendirici diye sahte satır işaretlemesi veya Cohen kappa üretilmeyecek. T4'te Türkçe makineyle aktarılmış etiketlere dayalı modeller çalıştırılırsa bunlar **exploratory projected-label proxy results**, Türkçe gold benchmark değil, olarak raporlanmalıdır.

Kod: [audit_translation_quality.py](../audit_translation_quality.py), testler: [test_translation_quality_heuristics.py](../tests/test_translation_quality_heuristics.py). Çalışma ağ/API anahtarı/model indirmesi gerektirmez. Orijinal `review_A.csv`, `review_B.csv`, `review_A_blind.csv`, `review_B_blind.csv` dosyalarına yazmaz; yeni çıktı klasörüne yazar.

## Araştırmacının yüklediği gerçek 240 kayıt üzerinde asistan ortamında hesaplanan sayılar

| Ölçüm | Sayı |
|---|---:|
| İşlenen kaynak–çeviri kaydı | 240 |
| Yüksek öncelikli aday | 47 |
| Orta öncelikli aday | 61 |
| İşaretlenmeyen satır | 132 |
| İnceleme için işaretlenen toplam satır | **108** |
| Hücre düzeyinde kural tetiklenmesi | **210** |

**ÖNEMLİ:** Bu sayılar *hatalı çevrilmiş kayıt sayısı, çeviri doğruluk oranı ya da sistem hassasiyet/duyarlılık sonucu değildir*. Aynı kayıt üzerinde soru+referans+öğrenci açıklaması arasında birden fazla tetikleyici bulunabilir. Etiketli ground truth olmadan precision, recall, false negative oranı hesaplanamaz. Otomatik işaretlenmeyen kayıtlar da anlam kayması içerebilir.

**Yüzeysel kontroller:** yanlış/eksik bilimsel terminoloji (calcite→analiz, bulb→otobüs, nail→tırnak, pot→tencere, solid→sağlam, store food→mağaza yemeği, skinny→cilt, evaporate→tahliye, no slope→göçücü, square→meydan okuma), sayılar, olumsuzlama, kısıtlama, karşılaştırma, parça halinde İngilizce kalmış sözcükler ve olağandışı uzunluk. İngilizce–Türkçe serbest ifade ve morfoloji nedeniyle **yanlış alarmlar kaçınılmazdır**, özellikle sayıların yazıyla ifade edildiği çevirilerde.

**Denetim kanıtları yerel kalır:** `translation_flags.csv` (kaynak ve hedef alan + gerekçe), `review_queue.csv` (240 kayıt sıralaması), `qa_summary.json`, `qa_summary.md`. 14 örneğin metin düzeyinde inceleme notları da yalnız çalışma paketinde tutulur; öğrenci açıklamaları ve kimlikleri GitHub'a yüklenmez.

## Tek parça Windows çalıştırması

```powershell
& {
    $ErrorActionPreference = "Stop"
    Set-Location "C:\Users\seydieryilmaz\StudentContextNLP"
    git pull --ff-only origin feature/tr-v0.2-offline-adaptation
    if ($LASTEXITCODE -ne 0) { throw "Git guncellemesi basarisiz." }

    $py = ".\.venv\Scripts\python.exe"
    if (-not (Test-Path $py)) { throw "Python sanal ortami bulunamadi." }

    & $py audit_translation_quality.py `
        --input reports/tr_review/blind_stage1/review_A_blind.csv `
        --out reports/tr_auto_qa_v01
    if ($LASTEXITCODE -ne 0) { throw "Otomatik QA incelemesi basarisiz." }
}
```

Aynı çıktı klasöründe rapor zaten varsa script **üzerine yazmaz**, farklı `--out` klasörü verilir.

## Kabul ayrımı

| Kapı | Durum |
|---|---|
| T2 gerçek EN→TR aday çeviri 10.804/10.804 | PASS (yerel Windows) |
| T3.0 örnekleme, 240/240 | PASS (yerel Windows) |
| T3.1 A/B kör form hazırlanması | PASS (yerel Windows) |
| T3-AUTO deterministik QA tarama | TAMAMLANDI (asistan ortamında 240/240 aday tarandı), Windows tekrar denemesi bekleniyor |
| T3-HUMAN iki bağımsız insan incelemesi/kappa | NOT_PERFORMED |
| T4 Türkçe etiketli bilimsel altın standart performansı | NOT_CLAIMED; yalnız exploratory pseudo/proxy-label karşılaştırma yapılabilir |

Herhangi bir metni düzeltirken **öğrencinin özgün bilimsel hatasını düzeltmeyin**; yalnız kaynak yanıtı doğru temsil eden çeviriyle değiştirmek amaçlanmalı ve eski sürüm, kural, kanıt ve SHA özetleri korunmalıdır.
