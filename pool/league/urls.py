from .views import *

urlpatterns = SeasonCRUDL().as_urlpatterns() + \
              TeamCRUDL().as_urlpatterns() + \
              PlayerCRUDL().as_urlpatterns() + \
              MatchCRUDL().as_urlpatterns()

