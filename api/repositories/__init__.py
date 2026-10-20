# Boş kalabilir.
#
# Bu klasördeki her dosya bir kaynağın (players, accounts, ...) SQL sorgularını
# tutar. Buradaki fonksiyonlar:
#   - parametre olarak bir psycopg bağlantısı (conn) + filtre değerleri alır,
#   - SQL çalıştırır,
#   - dict / dict listesi / None döndürür.
# FastAPI'yi, HTTPException'ı, Request'i BİLMEZLER. Bu yüzden ileride bir CLI
# script'inden de çağrılabilirler.
