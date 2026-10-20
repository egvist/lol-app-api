# player_html.txt içinden çıkarılabilecek bilgiler

## İncelemenin kapsamı

Dosya 296.483.965 bayt ve 2.850 adet `URL:` başlıklı sayfa bölümü içeriyor. Bu sayı benzersiz oyuncu sayısı değildir. Her bölümde profil URL’si ve HTML body bulunuyor. İnceleme; dosya genelinde alan taraması, Sajator profilinin ayrıntılı incelenmesi ve canlı oyun içeren bir sayfanın kontrolüne dayanıyor. Her alanın her oyuncuda dolu olduğu varsayılmamalı.

**En önemli bulgu:** Body yalnızca görünen HTML’den oluşmuyor. İçindeki `window.__LOLPROSGG__` script’i yapılandırılmış uygulama verisini taşıyor. En kapsamlı çıkarım için bu veri kullanılmalı; HTML öğeleri tamamlayıcı kaynak olabilir.

## 1. Oyuncu profili

| Bilgi | Kaynak / alan | Dosyadan örnek veya açıklama |
|---|---|---|
| Profil URL’si ve slug | Bölüm başındaki `URL:`, script `slug`, `routePath` | `https://lolpros.gg/player/sajator`, `sajator` |
| LOLPros profil UUID’si | `state.profile.profile.uuid` | Oyuncu profilini eşlemek için; Riot hesap kimliği değildir |
| Oyuncunun görünen adı | `.profile-details h1.name`, script `name` | Sajator |
| Ülke ve ülke kodu | `.profile-details .keypoints`, bayrak `title` / `fi-*`; script `country` | Czech Republic / CZ |
| Ek ülkeler | Script `other_countries` | Liste doluysa ek ülke bilgileri |
| Pozisyon | Profil keypoint’i, `league_player.position` | Mid; script’te kod biçiminde olabilir |
| Staff bilgisi | Script `staff`; ilgili rol ikonlarının `aria-label` değerleri | Varsa koç, analist, yönetici vb. bilgiler |
| Ligler | Profil `.league-logo`, script `leagues[]` | Prime League; UUID, slug, kısaltma, sunucular, logo verisi |
| Profil görseli | `.profile-details img.summoner-icon` | Profil ikonu URL’si; gerçek oyuncu fotoğrafı olduğu varsayılmaz |
| LOLPros sıralamaları | `.player-rankings .ranking-row`; script `rankings` | Sajator: global 51, pozisyonda 24, ülkede 3, ülke + pozisyonda 3 |
| Oyun durumu | Script `league_player.in_game`, canlı oyun sekmesi | Kaydın alındığı andaki durum |

Sıralamalar LOLPros’un kendi liste kapsamındadır; Riot sunucusunun tüm oyuncularını kapsayan resmi sıralama olarak yorumlanmamalı.

## 2. Sosyal ve dış bağlantılar

Profil içindeki `.profile-details .social-media a` öğelerinden platform, URL ve kullanıcı adı çıkarılabilir. Script’te karşılığı `social_media` alanıdır.

Dosyada Twitter/X, Twitch, Instagram, Facebook, Leaguepedia (`lol.fandom.com`) ve Games of Legends (`gol.gg`) bağlantıları bulunuyor. Script’te Discord gibi ek sosyal alanlar da var; yalnızca dolu alanlar alınmalı. `gamesoflegends` değeri örneğin `3258` gibi dış site profil ID’si olabilir.

Sajator örneği: Twitter `Sajator`, Twitch `sajatorcz`, Leaguepedia `Sajator`, Games of Legends profil ID’si `3258`.

**Kapsam önemli:** Footer’daki Discord, PayPal, e-posta ve site ekibine ait sosyal bağlantılar oyuncuya ait değildir. Tüm body içindeki bağlantıları doğrudan oyuncunun sosyal hesapları olarak toplamayın. `//` ile başlayan adresler HTTPS ile; `/` ile başlayan adresler LOLPros alan adı ile tamamlanabilir.

## 3. Oyuncuya bağlı LoL hesapları

HTML’de `.accounts-list .account` hesap listesini, `.--selected` ise açık hesabı gösterir. Script’te `state.profile.profile.league_player.accounts[]` ve `state.profile.league.accounts[]` bulunur; `state.profile.league.account` seçili hesaptır.

| Bilgi | Script alanı / HTML kaynağı | Açıklama |
|---|---|---|
| LOLPros hesap UUID’si | `uuid` | Profil UUID’sinden ayrı hesap kimliği |
| Sunucu | `server`, profil `servers` | Hesap bazında alınmalı; ülke ya da tagline’dan tahmin edilmemeli |
| Tam Riot ID | `summoner_name`, `.account .summoner-name` | `SAJAT0R#20311` |
| Game name / tagline | `gamename`, `tagline` | `SAJAT0R` / `20311`; script ayrı alanlar sunuyor |
| PUUID alanı | `encrypted_puuid` | Dosyada mevcut; Riot API’de kullanılabilirliği ayrıca doğrulanmalı |
| Profil ikonu | `profile_icon_id`, hesap ikonunun `src` değeri | Örneğin `29`; görsel URL’si de alınabilir |
| Seçili hesap | `league.account`, `.account.--selected` | Görünen rank kartlarının hangi hesaba ait olduğunu belirler |
| OP.GG bağlantısı | `#current-elo a.--opgg` | Seçili hesabın dış profil bağlantısı; URL sunucu bilgisi de içerir |

Sajator’un HTML hesap listesi: `SAJAT0R#20311`, `sajator21#zubri`, `sajat2004rCZLPYT#ZUBRI`.

## 4. Mevcut rank, peak ve sezon kayıtları

Her hesap için script’te `rank`, `peak` ve `seasons[]` alanları bulunabilir. HTML’de `#current-elo` ve `#peak-elo` yalnızca açık hesabın bilgilerini gösterir.

- Tier: `tier` / `.rank` (örneğin Challenger; script kodu `00_challenger` olabilir).
- Division: `division`; düşük tier’lerde rank ayrımını koruyun.
- LP: `league_points` / `.league-points`.
- Galibiyet ve mağlubiyet: `wins`, `losses` / `.games .wins`, `.games .losses`.
- Rank kayıt zamanı: `created_at`; HTML’de `time` daha kısa tarih gösterebilir.
- LOLPros sıralama skoru: `score`. LP ile aynı alan değildir.
- Sezon: `seasons[].id`; sezon sonu kaydı `end`, sezon peak kaydı `peak`.
- Toplam maç ve kazanma oranı: wins + losses ve wins / toplam maç üzerinden hesaplanabilir. Toplam sıfırsa oran boş bırakılmalı. HTML oranı yuvarlanmış olabilir.

Sajator’un seçili hesabında mevcut rank Challenger **3028 LP**, **493 galibiyet / 370 mağlubiyet (%57)**; peak Challenger **3258 LP**, **425 / 307 (%58)**. Peak, sitenin açıklamasına göre LOLPros’ta kaydedilmiş en yüksek rank’tır; oyuncunun tüm kariyerinin kesin zirvesi olduğu varsayılmaz.

## 5. Rank / LP zaman serisi

**Günlük/tarihli rank geçmişi çıkarılabilir.** HTML’de `#rank-history` tarih aralığını gösterir; `canvas#line-chart` sayısal veriyi kendi içinde saklamaz. Ancak body içindeki script’te `state.profile.league.rankings[]` grafiğin kayıtlarını içeriyor.

Her kayıttan `created_at`, `tier`, `division`, `league_points`, `score`, `wins`, `losses` ve `season` alınabilir.

Doğrudan görülen örnek kayıt: `2026-08-25T06:23:50+00:00`, **3158 LP**, **458 galibiyet**, **337 mağlubiyet**, `score: 7158` (Sajator).

Bu seriyle LP değişimi, dönemsel minimum/maksimum, rank geçişleri ve kayıtlar arası maç farkları hesaplanabilir. Kayıtlar aynı aralıklarla gelmeyebilir; olmayan günlere veri uydurulmamalı. Seri seçili hesaba bağlanmalı; tüm hesapların geçmiş serisinin yüklendiği varsayılmamalı. Sayaç farkları sezon sıfırlamaları dikkate alınarak yorumlanmalı.

## 6. Hesap adı geçmişi

- HTML: `#summoner-names .summoner-name` içinde ad ve `time`.
- Script: Her hesabın `summoner_names[]` listesinde `name` ve tam zaman damgalı `created_at`.
- Script, seçili olmayan hesapların ad geçmişini de taşıyabiliyor.

Sajator’un seçili hesabında `SAJAT0R#20311` ve `karakoram2727#V8x3` mevcut. İsim kayıt zamanı, kullanıcının Riot’ta isim değiştirdiği kesin an olarak yorumlanmamalı; sitenin kaydettiği zamandır.

## 7. Takımlar, kadrolar ve takım geçmişi

HTML’de `.team-members`, `.team-staff`, `.team-previous-members`, `.previous-team`, `.member`, `.team-link` gibi öğeler; script’te `teams`, `previous_teams` ve üyelik nesneleri bulunuyor.

Çıkarılabilecekler:

- Mevcut ve geçmiş takımların adı, slug’ı, LOLPros URL’si, UUID ve logo verisi.
- Takım üyelerinin adı, profil bağlantısı/UUID’si, ülkesi, pozisyonu ve üyelik rolü (oyuncu, yedek, staff).
- Üyelik kimliği (`uuid`) ve mevcut üyelik göstergesi (`current`).
- Katılım/ayrılma tarihleri: `join_date`, `leave_date`, Unix karşılıkları `join_timestamp`, `leave_timestamp`.
- HTML tarihleri için `time[title]`: görünen `Oct 2025` metni yerine `27/10/2025` gibi tam tarih bulunabilir.
- Mevcut kadrodaki üyelerin gösterilen rank, division ve LP bilgileri.
- Ayrılmış takım üyeleri ve staff listeleri.

Sajator örneğinde mevcut takım **TeamOrangeGaming**; geçmiş takımlar arasında EXILE esports, Team Heretics Academy, Barça eSports, eSuba ve Inside Games bulunuyor. Mevcut takımdaki Sajator üyeliği için katılım tarihi **17/01/2026**.

**Oyuncunun kendi geçmişi ile tüm kadro geçmişini ayırın:** Geçmiş takım kartında listelenen herkes incelenen oyuncu değildir. Oyuncunun o takımdaki tarihlerine ulaşmak için profil UUID’sini/slug’ını ilgili üye kaydıyla eşleyin. Aynı kadroda görünmek, tarih aralıkları çakışmadan birlikte oynandığını kanıtlamaz.

## 8. Canlı oyun verisi (yalnızca mevcutsa)

Bazı sayfalarda `section#live-game` yalnızca `Summoner not in game` gösterirken bazıları oyun detaylarını içeriyor.

Canlı oyun içeren HTML’den şunlar çıkarılabilir:

- Oyun modu, harita ve kaydedildiği anda gösterilen oyun süresi (`.game-infos`). İncelenen örnek: `5v5 Ranked Solo | Summoner's Rift | 25:08`.
- Mavi/kırmızı takım ve takım başına banlanan şampiyonlar (`.team-header`, `.bans .ban img[alt]`).
- Katılımcı Riot ID’leri, varsa LOLPros oyuncu profili, ülke, rol ve takım bilgisi.
- Seçilen şampiyon (`.summoner .champion img[alt]`).
- Sihirdar büyüleri (`.summoner-spells img[alt]`).
- Ana rün ve ikincil rün ağacı (`.main-rune`, `.secondary-rune`); örneğin Lethal Tempo / Resolve.
- Katılımcı rank, LP, winrate ve toplam maç göstergeleri.
- LOLPros’a kayıtlı olmayan katılımcı göstergesi.

Bu bilgiler yalnızca kaydedilmiş anı temsil eder. `no-game`, yüklenme ve hata durumları birbirinden ayrılmalı. Canlı oyun katılımcılarının bilgileri doğrudan profil sahibine yazılmamalı. HTML’de bir şampiyonla görünen Unranked satırın gerçek Riot ID içerdiği varsayılmamalı.

## 9. Türetilmiş bilgiler

Kaynak alanlar yeterliyse hesap sayısı, kullanılan sunucular, toplam maç, hesap bazlı winrate, LP trendi, isim geçmişi sayısı, takım geçmişi sayısı ve takımda kalma süresi hesaplanabilir. Takım üyelerinin tarih aralıkları kesiştirilerek olası birlikte bulunma dönemleri belirlenebilir.

Bu sonuçlar kaynak veriden hesaplanan alanlar olarak işaretlenmeli; eksik tarihlerle kesin süre veya eksik LP serisiyle kesin aktivite sonucu üretilmemeli.

## 10. Çıkarım yöntemi ve sınırlar

1. Dosyayı satır başındaki `URL:` başlıklarına göre sayfalara ayırın; her veriyi kaynak URL ile ilişkilendirin.
2. Body’deki `window.__LOLPROSGG__` atamasını ayrıştırın. Bu **JSON değil**, parametrelerle sıkıştırılmış bir JavaScript IIFE’sidir. Örneğin `server:q` veya `tier:e` gerçek değeri değil değişken referansını gösterir; fonksiyon parametreleri ve sondaki argümanlar çözülmelidir.
3. Harici HTML’yi ve script’i doğrudan normal uygulama sürecinde `eval` ile çalıştırmayın. Bir JavaScript parser’ı ile izin verilen veri ifadelerini çözmek tercih edilir.
4. `state.profile.profile`, `state.profile.league.accounts`, `state.profile.league.account` ve `state.profile.league.rankings` içindeki dolu kayıtları esas alın. Çeviri sözlüklerindeki aynı adlı anahtarlar oyuncu verisi değildir.
5. HTML’den çıkarmada semantik sınıflar ve bölüm kapsamları kullanın; değişebilen `data-v-*` değerlerine bağlanmayın. Gizli sekmeler de veri içerebilir; aynı zamanda mobil/masaüstü tekrarları tekilleştirilmelidir.
6. Oyuncu, hesap, takım üyeliği, takım kadrosu ve canlı oyun katılımcısını ayrı varlıklar olarak tutun. Aynı isim farklı profil veya hesapları gösterebilir.
7. Eksik değerleri `null`/boş olarak koruyun; varsayılan sıfır, Unranked veya takım yok sonucuna çevirmeyin.
8. ISO zaman damgalarını ve saat dilimini koruyun. HTML’deki kısa gün/ay metinlerine mevcut yılı eklemeyin. `created_at` alanını scrape zamanı sanmayın.

Bu incelemede gerçek ad, doğum tarihi, yaş, maç sonrası KDA, CS, hasar, eşya dizilimi veya eksiksiz maç geçmişi için oyuncuya ait doğrulanmış kayıt bulunmadı. Dış profil bağlantılarının olması o sitelerdeki bilgilerin bu dosyada bulunduğu anlamına gelmez. Rank serisinden tek tek maç sonuçları veya maç ID’leri çıkarılamaz. PUUID alanı ise script’te gerçekten mevcuttur; uygulamadaki Riot senkronizasyonunda kullanmadan önce doğrulanmalıdır.

## Önerilen veri grupları

`players`, `accounts`, `account_ranks`, `account_seasons`, `rank_history`, `account_name_history`, `social_links`, `leagues`, `teams`, `team_memberships` ve varsa `live_game_snapshots` / `live_game_participants`.

Her kayıtta kaynak profil URL’si ve verinin ilgili olduğu profil/hesap/üyelik kimliği tutulmalı. Böylece hesap rank’ı ile kadro kartındaki rank veya oyuncunun kendi geçmişi ile takım arkadaşlarının geçmişi karışmaz.
