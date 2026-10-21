# Bu dosya boş kalabilir.
#
# ARAŞTIR: Python'da bir klasörde neden __init__.py olur? "package" ve "module"
# arasındaki fark ne? `py -m uvicorn api.main:app` komutunun "api.main"
# diyebilmesi bu dosyayla nasıl ilişkili?
#
# CEVAP:
#   - Module tek bir .py dosyasıdır (main.py). Package, module'leri bir arada
#     tutan klasördür. __init__.py klasörü "normal package" yapar; package ilk
#     import edildiğinde bu dosya çalışır.
#   - Python 3.3'ten beri __init__.py olmayan klasör de "namespace package"
#     olarak import edilebilir. Yine de dosyanın olması niyeti açık eder ve
#     pytest gibi araçların klasörü doğru tanımasını sağlar.
#   - `api.main` = api package'ı içindeki main module'ü (api/main.py). Komutu
#     kök dizinde (lol-data/) çalıştırdığın için Python api/ klasörünü orada
#     bulur ve noktalı yolu klasör/dosya olarak çözer.
