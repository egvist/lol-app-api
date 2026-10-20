# Boş kalabilir.
#
# Bu klasördeki her dosya bir APIRouter tanımlar. Router'ın görevi:
#   1. HTTP parametrelerini almak ve doğrulamak (path, query)
#   2. Depends(get_conn) ile bağlantı almak
#   3. repositories/ fonksiyonlarını çağırmak
#   4. Sonuç yoksa HTTPException(404) fırlatmak
#   5. Sonucu schemas/ modeli olarak döndürmek (response_model)
# Router'larda SQL YAZILMAZ.
